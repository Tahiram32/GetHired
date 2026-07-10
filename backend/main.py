from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import os
import json
import requests
import urllib.parse
import concurrent.futures
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

app = FastAPI(title="GetHired API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up OpenAI Client
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

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

        response = client.beta.chat.completions.parse(
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
            response = client.chat.completions.create(
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
    
            response = client.beta.chat.completions.parse(
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

class InterviewQuestionsResult(BaseModel):
    questions: List[str]

@app.get("/api/interview-questions")
async def get_interview_questions(role: str = "Software Engineer"):
    if not client:
        return {"status": "error", "message": "OpenAI client not configured."}
    
    system_instruction = "You are a strict, professional hiring manager. Generate exactly 5 short, realistic interview questions for the provided role. Real interviews are dynamic back-and-forths, not massive paragraphs. Keep each question to a single sentence or two. Make them situational and challenging."
    
    try:
        response = client.beta.chat.completions.parse(
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
    You are a strict, professional hiring manager. The user will provide an interview question and their text-based answer.
    Analyze the substance of their answer. Provide harsh but constructive feedback focusing on the content, clarity, and completeness.
    Do NOT comment on tone, pacing, or audio/video quality, as this is a text-based exercise.
    Advise them on how to improve their answer, for example by using the STAR method (Situation, Task, Action, Result) if they forgot to give specific examples.
    Keep your feedback concise, actionable, and in the voice of a hiring manager.
    """
    
    try:
        response = client.beta.chat.completions.parse(
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
        response = client.beta.chat.completions.parse(
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
