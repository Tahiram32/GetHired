from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Header, Depends
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
from pydantic import BaseModel, Field, field_validator, ValidationError
import logging
logger = logging.getLogger('api')
from typing import List, Optional, Any

app = FastAPI(title="GetHired API")

class SerpApiJobValidator(BaseModel):
    title: Optional[str] = Field(default="Unknown Title")
    company_name: Optional[str] = Field(default="Unknown Company")
    location: Optional[str] = Field(default="Location not listed")
    description: Optional[str] = Field(default="No description available.")
    share_link: Optional[str] = Field(default="")
    job_highlights: Optional[List[Any]] = Field(default_factory=list)

    @field_validator('description', mode='before')
    @classmethod
    def clean_description(cls, v: Any) -> str:
        if not v:
            return "No description available."
        return str(v).strip()



import threading
import signal
from fastapi import Request



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

class SkillGap(BaseModel):
    skill_name: str = Field(..., description="The specific hard skill missing")
    importance: str = Field(..., description="High/Medium/Low based on frequency in target roles")
    reasoning: str = Field(..., description="Brief, one-sentence evidence from user's rejected roles")

class CoachingInsight(BaseModel):
    summary: str = Field(..., description="A 1-sentence takeaway of the user's current status")
    gaps: List[SkillGap] = Field(..., description="List of actionable technical gaps")
    recommendation: str = Field(..., description="The single most important action for this weekend")

class CoachingRequest(BaseModel):
    aspirational_baseline: Optional[str] = None

class ResumeRewrite(BaseModel):
    original_bullet: str = Field(..., description="The original bullet point from the resume")
    suggested_rewrite: str = Field(..., description="The optimized bullet point incorporating the skill gap")
    skill_addressed: str = Field(..., description="The skill this rewrite addresses")
    reasoning: str = Field(..., description="Why this rewrite is better for ATS")

class ResumeOptimizationResponse(BaseModel):
    rewrites: List[ResumeRewrite] = Field(..., description="List of suggested bullet point rewrites")
    general_advice: str = Field(..., description="Overall advice for tailoring the resume to the target role")

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
    order_index: int = 0


class ColumnOrderUpdate(BaseModel):
    column_id: int
    job_ids: List[int]

@app.post("/api/kanban/update-column-order")
async def update_column_order(payloads: List[ColumnOrderUpdate]):
    with Session(engine) as session:
        # 1. Single Flattened Read
        all_job_ids = []
        for p in payloads:
            all_job_ids.extend(p.job_ids)
            
        jobs = session.exec(select(TrackerJob).where(TrackerJob.id.in_(all_job_ids))).all()
        
        # 2. In-Memory Map
        job_map = {job.id: job for job in jobs}
        
        # 3. In-Memory Bulk Update
        for payload in payloads:
            for index, job_id in enumerate(payload.job_ids):
                if job_id in job_map:
                    job_map[job_id].column_id = payload.column_id
                    job_map[job_id].order_index = index
                
        # 4. Single Atomic Write
        session.commit()
    return {"status": "success"}


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


load_dotenv()

from time import time
from collections import defaultdict
from fastapi import Request, Depends

RATE_LIMIT = 10
RATE_LIMIT_WINDOW = 3600
ip_requests = defaultdict(list)

def check_rate_limit(request: Request):
    ip = request.client.host
    now = time()
    ip_requests[ip] = [t for t in ip_requests[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(ip_requests[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    ip_requests[ip].append(now)

def get_openai_client():
    api_key = os.getenv("MASTER_OPENAI_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    return OpenAI(api_key=api_key)

def get_serpapi_key():
    api_key = os.getenv("MASTER_SERPAPI_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="SerpAPI key not configured")
    return api_key

class SettingsUpdate(BaseModel):
    openai_key: Optional[str] = None
    serpapi_key: Optional[str] = None

@app.get("/api/config")
async def get_config_alias():
    keys = get_keys()
    return {
        "has_openai": bool(keys.get("openai_key")),
        "has_serpapi": bool(keys.get("serpapi_key"))
    }

@app.post("/api/config")
async def update_config_alias(settings: SettingsUpdate):
    keys = get_keys()
    
    if settings.openai_key:
        try:
            temp_client = OpenAI(api_key=settings.openai_key)
            temp_client.models.list()
            keys["openai_key"] = settings.openai_key
        except openai.AuthenticationError:
            raise HTTPException(status_code=401, detail="Invalid API Key. Please double check your OpenAI key.")
        except openai.RateLimitError:
            raise HTTPException(status_code=429, detail="API Quota Exceeded. Please ensure you have added a $5 minimum balance to your OpenAI account.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    if settings.serpapi_key:
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

@app.post("/api/analysis/skill-gap")
async def analyze_skill_gap(payload: CoachingRequest):
    with Session(engine) as session:
        rejected_col = session.exec(select(KanbanColumn).where(KanbanColumn.name == "Rejected")).first()
        if not rejected_col:
            raise HTTPException(status_code=400, detail="Rejected column not found")
            
        rejected_jobs = session.exec(select(TrackerJob).where(TrackerJob.column_id == rejected_col.id)).all()
        if not rejected_jobs:
            return CoachingInsight(summary="You have no rejected jobs yet. Keep applying!", gaps=[], recommendation="Apply to more jobs.")

        interview_col = session.exec(select(KanbanColumn).where(KanbanColumn.name == "Interviewing")).first()
        interview_jobs = []
        if interview_col:
            interview_jobs = session.exec(select(TrackerJob).where(TrackerJob.column_id == interview_col.id)).all()

    rejected_texts = "\n\n".join([j.description for j in rejected_jobs])
    interview_texts = "\n\n".join([j.description for j in interview_jobs]) if interview_jobs else ""
    
    baseline = payload.aspirational_baseline if payload.aspirational_baseline else ""

    if not interview_texts and not baseline:
         raise HTTPException(status_code=400, detail="We need either some jobs in the Interviewing column or an Aspirational Baseline to compare your rejections against.")

    if len(rejected_texts) < 200:
        return CoachingInsight(
            summary="These job descriptions lack sufficient detail for a meaningful analysis.",
            gaps=[],
            recommendation="Save jobs with more detailed requirement sections to get actionable insights."
        )

    prompt = f"""You are an expert career coach performing a differential analysis.
You must compare the requirements of the jobs where the user was rejected against the roles they are actively interviewing for (or their target aspirational baseline).
You must completely ignore 'Nice to Have', 'Bonus', or 'Preferred Qualifications' sections. You must only extract hard skills from sentences that use absolute terminology like 'Must have', 'Required', 'X+ years of experience in', or 'Minimum qualifications'.

[REJECTED JOB DESCRIPTIONS]
{rejected_texts}
"""
    if interview_texts:
        prompt += f"\n[INTERVIEWING JOB DESCRIPTIONS]\n{interview_texts}\n"
    if baseline:
        prompt += f"\n[ASPIRATIONAL BASELINE ROLE]\n{baseline}\n"

    try:
        response = get_openai_client().beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a career coach. Return the JSON object following the strict schema."},
                {"role": "user", "content": prompt}
            ],
            response_format=CoachingInsight
        )
        return response.choices[0].message.parsed
    except Exception as e:
        logger.error(f"Failed to generate coaching insight: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate coaching insight")

@app.post("/api/resume/optimize")
async def optimize_resume(req: Request, _=Depends(check_rate_limit), file: UploadFile = File(...), skill_gaps: str = Form(...)):
    try:
        with pdfplumber.open(file.file) as pdf:
            resume_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    except Exception as e:
        logger.error(f"Failed to read PDF: {e}")
        raise HTTPException(status_code=400, detail="Failed to parse PDF resume. Please ensure it is a valid text-based PDF.")
        
    if not resume_text or len(resume_text.strip()) < 100:
        raise HTTPException(status_code=400, detail="Could not extract sufficient text from the PDF. Is it an image-based scan?")
        
    prompt = f"""You are an expert technical recruiter and ATS optimization specialist.
The user has provided their current resume and a list of identified 'Skill Gaps' for their target role.
Your goal is to suggest rewrites for specific bullet points in their resume to naturally incorporate these missing skills.
If the user's experience suggests they possess the foundational knowledge, reframe their existing bullets to explicitly use the missing ATS keywords. Do not fabricate entire jobs, but heavily optimize the phrasing.

HUMANITY SCORE FILTER:
You must strictly limit the use of adjectives. Do NOT use corporate buzzwords or executive puffery (e.g., "synergized", "architected high-scale mission-critical infrastructure"). Prioritize strong, simple active verbs. Every suggested rewrite MUST be 25 words or less. Keep it punchy, human-readable, and honest.

[IDENTIFIED SKILL GAPS]
{skill_gaps}

[USER RESUME]
{resume_text}
"""
    try:
        response = get_openai_client().beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a resume optimizer. Return the JSON object following the strict schema."},
                {"role": "user", "content": prompt}
            ],
            response_format=ResumeOptimizationResponse
        )
        return response.choices[0].message.parsed
    except Exception as e:
        logger.error(f"Failed to generate resume optimization: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize resume.")

@app.get("/api/jobs")
async def get_live_jobs(request: Request, q: str = "", l: str = "", start: int = 0, _=Depends(check_rate_limit)):
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
            
            serpapi_key = get_serpapi_key()

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
                try:
                    # The Anti-Corruption Layer: Normalize unstructured Google JSON into strongly-typed variables
                    validated_job = SerpApiJobValidator(**item)
                except ValidationError as ve:
                    logger.warning(f"Dropped malformed job due to missing critical fields: {ve}")
                    continue
                    
                title = validated_job.title
                company = validated_job.company_name
                loc = validated_job.location
                desc = validated_job.description
                url_link = validated_job.share_link
                
                # Use SerpAPI's native pre-cleaned highlights to save OpenAI tokens
                highlights = validated_job.job_highlights
                if highlights:
                    # Pass the structured array directly as a string to avoid token-heavy fluff
                    snippet = str(highlights)
                    api_jobs.append({
                        "title": title,
                        "company": company,
                        "location": loc,
                        "url": url_link,
                        "description_snippet": snippet
                    })
                else:
                    # Transparency Badge Fix: Skip AI filter entirely to prevent false-positive deletion
                    unverified_jobs.append(Job(
                        title=title,
                        company=company,
                        location=loc,
                        url=url_link,
                        description=desc,
                        is_unverified=True
                    ))
            
            api_jobs = api_jobs[:15]
            unverified_jobs = unverified_jobs[:5]
        except HTTPException as he:
            if he.status_code == 400 and "SerpAPI key" in he.detail:
                return {"status": "error", "code": "MISSING_SERPAPI_KEY", "message": "Action Required: SerpAPI Key Missing. Please enter your key below to unlock the job feed."}
            else:
                print("HTTPException during SerpAPI:", he)
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
async def get_interview_questions(req: Request, role: str = "Software Engineer", _=Depends(check_rate_limit)):

    
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

init_db()
