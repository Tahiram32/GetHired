from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import os
import json
import stat
import subprocess
import getpass
import requests
import urllib.parse
import concurrent.futures
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import openai
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(title="GetHired API")

import threading
import signal
from fastapi import Request

import secrets
SHUTDOWN_TOKEN = secrets.token_hex(32)
SHUTDOWN_TOKEN_FILE = os.path.join(get_app_dir(), "shutdown.token")
with open(SHUTDOWN_TOKEN_FILE, "w") as f:
    f.write(SHUTDOWN_TOKEN)

if platform.system() == "Windows":
    try:
        import getpass
        subprocess.run(['icacls', SHUTDOWN_TOKEN_FILE, '/inheritance:r', '/grant:r', f'{getpass.getuser()}:F'], check=False, capture_output=True)
    except Exception:
        pass
else:
    import stat
    os.chmod(SHUTDOWN_TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)

@app.post("/api/shutdown")
async def shutdown_server(request: Request, x_shutdown_token: str = Header(None)):
    if request.client.host not in ["127.0.0.1", "localhost", "::1"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if x_shutdown_token != SHUTDOWN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    def kill_server():
        import time
        time.sleep(0.5)
        if platform.system() == "Windows":
            os.kill(os.getpid(), signal.SIGINT)
        else:
            os.kill(os.getpid(), signal.SIGTERM)
            
    threading.Thread(target=kill_server).start()
    return {"status": "shutting down"}


import platform
import json
import stat
import subprocess
import getpass

def get_app_dir():
    system = platform.system()
    if system == "Windows":
        base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
        app_dir = os.path.join(base_dir, "GetHired")
    elif system == "Darwin":
        app_dir = os.path.expanduser("~/Library/Application Support/GetHired")
    else:
        app_dir = os.path.expanduser("~/.local/share/GetHired")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

CONFIG_FILE = os.path.join(get_app_dir(), "config.json")
DB_FILE = os.path.join(get_app_dir(), "gethired.db")

from sqlmodel import create_engine, SQLModel, Session, Field, select
from sqlalchemy import event
from sqlalchemy.engine import Engine
from typing import Optional

sqlite_url = f"sqlite:///{DB_FILE}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class KanbanColumn(SQLModel, table=True):
    __tablename__ = "kanban_columns"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    order_index: int

class TrackerJob(SQLModel, table=True):
    __tablename__ = "tracker_jobs"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    company: str
    location: str
    url: Optional[str] = None
    description: str
    is_unverified: bool = False
    column_id: int = Field(foreign_key="kanban_columns.id")

def init_db():
    SQLModel.metadata.create_all(engine)
    keys = get_keys()
    if not keys.get("has_seeded_defaults", False):
        with Session(engine) as session:
            defaults = [
                KanbanColumn(name="Saved", order_index=0),
                KanbanColumn(name="Applied", order_index=1),
                KanbanColumn(name="Interviewing", order_index=2),
                KanbanColumn(name="Offer", order_index=3),
                KanbanColumn(name="Rejected", order_index=4)
            ]
            session.add_all(defaults)
            session.commit()
            
            keys["has_seeded_defaults"] = True
            with open(CONFIG_FILE, "w") as f:
                json.dump(keys, f)

init_db()


def get_keys():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def get_openai_client():
    keys = get_keys()
    api_key = keys.get("openai_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    return OpenAI(api_key=api_key)

def get_serpapi_key():
    keys = get_keys()
    api_key = keys.get("serpapi_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="SerpAPI key not configured")
    return api_key

class SettingsUpdate(BaseModel):
    openai_key: str
    serpapi_key: str

@app.get("/api/settings")
async def get_settings():
    keys = get_keys()
    return {
        "has_openai": bool(keys.get("openai_key")),
        "has_serpapi": bool(keys.get("serpapi_key"))
    }

@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    try:
        temp_client = OpenAI(api_key=settings.openai_key)
        temp_client.models.list()
    except openai.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid API Key. Please double check your OpenAI key.")
    except openai.RateLimitError:
        raise HTTPException(status_code=429, detail="API Quota Exceeded. Please ensure you have added a $5 minimum balance to your OpenAI account.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    keys = get_keys()
    keys["openai_key"] = settings.openai_key
    keys["serpapi_key"] = settings.serpapi_key
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(keys, f)
        
    if platform.system() == "Windows":
        try:
            username = getpass.getuser()
            subprocess.run(['icacls', CONFIG_FILE, '/inheritance:r', '/grant:r', f'{username}:F'], check=False, capture_output=True)
        except Exception as e:
            print(f"Warning: Could not set strict Windows permissions: {e}")
    else:
        os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)
        
    return {"status": "success"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AtsResult(BaseModel):
    ats_match_score: int = Field(description="The projected ATS match score between 0 and 100")
    tailored_bullets: list[str] = Field(description="The rewritten resume bullets matching the job description")

class Job(BaseModel):
    title: str
    company: str
    location: str
    url: str | None = Field(None, description="The URL to the actual job application")
    description: str = Field(description="A concise 2-sentence summary of the job requirements")
    is_unverified: bool = False

class JobFilterResult(BaseModel):
    verified_jobs: list[Job] = Field(description="List of verified, non-scam jobs")

@app.post("/api/tailor-resume")
async def tailor_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        # Step 1: Auto-Scrape Job URL if provided instead of text
        if job_description.startswith("http://") or job_description.startswith("https://"):
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                res = requests.get(job_description, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")
                # Attempt to extract all textual content and strip excessive whitespace
                job_description = soup.get_text(separator="\n", strip=True)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Could not scrape job URL: {str(e)}")

        # Step 2: Extract text from the uploaded PDF
        extracted_text = ""
        with pdfplumber.open(resume.file) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"

        if not client:
            raise HTTPException(status_code=500, detail="OpenAI client not initialized. Check OPENAI_API_KEY.")

        # Step 2: Use OpenAI to tailor the resume
        system_instruction = """
        You are an empathetic, high-conversion career coach and ATS optimization expert. 
        Your job is to read the user's base resume and the target job description. 
        You will extract the most relevant achievements from the resume and rewrite them 
        into powerful, impact-driven bullet points that naturally include the keywords 
        found in the job description.
        
        CRITICAL RULE: DO NOT hallucinate or lie. You must only use facts present in the base resume. 
        If they do not have a skill, do not pretend they do. Focus on transferable skills and framing.
        """

        prompt = f"""
        Base Resume:
        {extracted_text}
        
        Target Job Description:
        {job_description}
        
        Analyze the match and provide a JSON response with 'ats_match_score' and 'tailored_bullets'.
        """

        response = get_openai_client().beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            response_format=AtsResult,
            temperature=0.3
        )
        
        result_data = response.choices[0].message.parsed

        return {
            "status": "success",
            "message": "Resume successfully tailored for ATS.",
            "original_text_preview": extracted_text[:200] + "...",
            "tailored_bullets": result_data.tailored_bullets,
            "ats_match_score": result_data.ats_match_score
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/admin/job")
async def post_admin_job(job: Job):
    """Admin endpoint to manually post a highly-vetted job to the global feed."""
    try:
        # Use AI to automatically fix formatting if it's a clumped copy-paste
        if client:
            system_instruction = "You are a professional technical recruiter. The user will provide a messy, clumped job description. Format it into beautiful, easy-to-read sections (e.g. The Role, Responsibilities, Requirements, Compensation) using clear spacing and bullet points (-). Do NOT use markdown bolding (**) or headers (##). Just use plain text with actual newline characters to separate sections."
            response = get_openai_client().chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": job.description}
                ],
                temperature=0.3
            )
            job.description = response.choices[0].message.content.strip()

        db_path = "jobs_db.json"
        if os.path.exists(db_path):
            with open(db_path, "r") as f:
                jobs_db = json.load(f)
        else:
            jobs_db = []
            
        jobs_db.append(job.model_dump())
        
        with open(db_path, "w") as f:
            json.dump(jobs_db, f, indent=4)
            
        return {"status": "success", "message": "Job successfully added to the global feed!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/jobs")
async def get_live_jobs(q: str = "", l: str = "", start: int = 0):
    """
    Pulls live jobs from the global Admin JSON DB, plus an open API (Remotive), and passes them through an AI Scam-Filter.
    """
    try:
        # Load Admin Jobs First
        admin_jobs = []
        db_path = "jobs_db.json"
        if os.path.exists(db_path):
            with open(db_path, "r") as f:
                admin_jobs = json.load(f)

        # Step 1: Pull live jobs from SerpAPI Google Jobs
        api_jobs = []
        unverified_jobs = []
        try:
            query = q.lower().strip()
            location = l.lower().strip()
            
            # Backend Safety Net: Reject empty location requests
            if not location:
                return {"status": "error", "message": "Backend Error: A valid Location parameter is strictly required."}
            
            # Backend Safety Net: Reject empty role requests to prevent low-quality spam
            if not query:
                return {"status": "error", "message": "Backend Error: A valid Role parameter is strictly required."}
            
            serpapi_key = os.getenv("SERPAPI_KEY")
            if not serpapi_key:
                raise Exception("SERPAPI_KEY is not configured in the environment.")

            url = "https://serpapi.com/search.json"
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "start": start,
                "api_key": serpapi_key
            }
            
            res = requests.get(url, params=params, timeout=15)
            data = res.json()
            
            for item in data.get("jobs_results", []):
                title = item.get("title", "")
                company = item.get("company_name", "")
                loc = item.get("location", "")
                desc = item.get("description", "")
                
                # Use SerpAPI's native pre-cleaned highlights to save OpenAI tokens
                highlights = item.get("job_highlights", [])
                if highlights:
                    # Pass the structured array directly as a string to avoid token-heavy fluff
                    snippet = str(highlights)
                    api_jobs.append({
                        "title": title,
                        "company": company,
                        "location": loc,
                        "url": item.get("share_link", ""),
                        "description_snippet": snippet
                    })
                else:
                    # Transparency Badge Fix: Skip AI filter entirely to prevent false-positive deletion
                    unverified_jobs.append(Job(
                        title=title,
                        company=company,
                        location=loc,
                        url=item.get("share_link", ""),
                        description=desc,
                        is_unverified=True
                    ))
            
            api_jobs = api_jobs[:15]
            unverified_jobs = unverified_jobs[:5]
        except Exception as e:
            print("SerpAPI failed:", e)

        if not api_jobs and not unverified_jobs:
            raise Exception("No active jobs found matching your criteria.")

        if not client:
            raise HTTPException(status_code=500, detail="OpenAI client not initialized.")

        filtered_jobs = []
        
        if api_jobs:
            # Step 2: Pass structured jobs through highly rigorous AI Anti-Scam Filter
            system_instruction = f"""
            You are a strict, world-class Anti-Scam Analyst for a premium job board. 
            Your ONLY goal is to protect users from fake jobs, ghost jobs, MLMs, unpaid internships, "pay-to-work" schemes, and severely underpaid roles.
            You will receive a list of raw job postings scraped from public APIs.
    
            Rules:
            1. Discard ANY job that mentions unpaid, equity-only, or "investment required".
            2. Discard ANY job that looks like a ghost job (too generic, lack of real requirements).
            3. Discard ANY job from known spammy recruitment agencies if it looks fake or lacks a real company.
            4. For the jobs that PASS the filter, write a highly structured, beautiful 3-sentence summary of the role.
            """
    
            prompt = f"Raw Scraped Jobs: {json.dumps(api_jobs, indent=2)}"
    
            response = get_openai_client().beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                response_format=JobFilterResult,
                temperature=0.2
            )
            
            filtered_jobs = response.choices[0].message.parsed.verified_jobs

        return {
            "status": "success",
            "jobs": (admin_jobs if start == 0 else []) + [j.model_dump() for j in filtered_jobs] + [j.model_dump() for j in unverified_jobs]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

class QuestionObj(BaseModel):
    question: str
    hint: str

class InterviewQuestionsResult(BaseModel):
    questions: List[QuestionObj]

@app.get("/api/interview-questions")
async def get_interview_questions(role: str = "Software Engineer"):
    if not client:
        return {"status": "error", "message": "OpenAI client not configured."}
    
    system_instruction = "You are a strict, professional hiring manager. Generate exactly 5 short, realistic interview questions for the provided role, along with a 1-sentence hint for each to help a candidate who gets stuck. Real interviews are dynamic back-and-forths. Keep each question to a single sentence or two. Make them situational and challenging."
    
    try:
        response = get_openai_client().beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Role: {role}"}
            ],
            response_format=InterviewQuestionsResult,
            temperature=0.7
        )
        return {
            "status": "success",
            "questions": response.choices[0].message.parsed.questions
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


class InterviewFeedbackResult(BaseModel):
    feedback: str

@app.post("/api/interview-feedback")
async def get_interview_feedback(question: str = Form(...), answer: str = Form(...)):
    if not client:
        return {"status": "error", "message": "OpenAI client not configured."}
    
    system_instruction = """
    You are an expert, supportive Career Coach providing a post-answer coaching moment. The user will provide an interview question and their text-based answer.
    Critique their answer focusing on content, clarity, and completeness in a supportive but highly analytical tone.
    CRITICAL RULE (Critique + Exemplar): You MUST explicitly rewrite their answer using the STAR method (Situation, Task, Action, Result) so they can see exactly how the structure should look. Show them the Gold Standard answer.
    Do NOT comment on tone, pacing, or audio/video quality.
    """
    
    try:
        response = get_openai_client().beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Question: {question}\n\nAnswer: {answer}"}
            ],
            response_format=InterviewFeedbackResult,
            temperature=0.7
        )
        return {
            "status": "success",
            "feedback": response.choices[0].message.parsed.feedback
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}



class InterviewScorecardResult(BaseModel):
    top_strength: str
    biggest_blind_spot: str
    summary: str

@app.post("/api/interview-scorecard")
async def generate_interview_scorecard(session_data: str = Form(...)):
    if not client:
        return {"status": "error", "message": "OpenAI client not configured."}
    
    system_instruction = """
    You are an expert career coach reviewing a completed 5-question interview session.
    You will receive a JSON string containing the questions, the user's answers, and the hiring manager's feedback.
    Generate a Post-Interview Scorecard.
    Identify their Top Strength (1 sentence).
    Identify their Biggest Blind Spot (e.g., "You consistently fail to quantify your impact in your answers" - 1 sentence).
    Provide a short coaching summary (2-3 sentences).
    """
    try:
        response = get_openai_client().beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": session_data}
            ],
            response_format=InterviewScorecardResult,
            temperature=0.7
        )
        parsed = response.choices[0].message.parsed
        return {
            "status": "success",
            "top_strength": parsed.top_strength,
            "biggest_blind_spot": parsed.biggest_blind_spot,
            "summary": parsed.summary
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

class CounterOfferResult(BaseModel):
    script: str

@app.post("/api/fair-pay")
async def generate_counter_offer(offer_details: str = Form(...)):
    if not client:
        return {"status": "error", "message": "OpenAI client not configured."}
    
    system_instruction = """
    You are an expert career coach and salary negotiation advocate. The user will provide the details of a job offer they received, including what they are unhappy with or what the market average is. 
    Draft a highly professional, respectful, and persuasive counter-offer email script for them. 
    
    CRITICAL TONE RULES:
    1. NEVER sound like an AI. Do not use robotic phrases like "I hope this email finds you well", "delve into", "dynamic landscape", or "underscores".
    2. Write like a highly competent, respectful human professional. Keep sentences relatively short and punchy.
    3. Be confident but not arrogant. Frame the request collaboratively (e.g., "I am very excited to join, but I was hoping we could look at the base salary...").
    4. Only output the email script itself. Do not include any meta-commentary.
    """
    try:
        response = get_openai_client().beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": offer_details}
            ],
            response_format=CounterOfferResult,
            temperature=0.5
        )
        return {
            "status": "success",
            "script": response.choices[0].message.parsed.script
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "GetHired Engine is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
