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
    matchScore: int = Field(description="A score between 75 and 99 indicating fit based on the user's master profile")
    description: str = Field(description="A concise 2-sentence summary of the job requirements")

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

        # Step 1: Pull live remote software dev jobs from LinkedIn
        linkedin_jobs = []
        try:
            query = urllib.parse.quote(q)
            loc = f"&location={urllib.parse.quote(l)}" if l else ""
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={query}{loc}&start={start}"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            job_lis = soup.find_all("li")[:25]  # Take top 25
            
            def fetch_job_details(j):
                title_elem = j.find("h3")
                company_elem = j.find("h4")
                loc_elem = j.find("span", class_="job-search-card__location")
                a_tag = j.find("a", class_="base-card__full-link")
                
                if not (title_elem and company_elem and a_tag):
                    return None
                    
                job_url = a_tag["href"]
                    
                return {
                    "title": title_elem.text.strip(),
                    "company": company_elem.text.strip(),
                    "location": loc_elem.text.strip() if loc_elem else "Unknown",
                    "url": job_url,
                    "description_snippet": "Full description available on posting."
                }

            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                results = list(executor.map(fetch_job_details, job_lis))
                linkedin_jobs = [res for res in results if res is not None]
        except Exception as e:
            print("LinkedIn scrape failed:", e)

        if not linkedin_jobs:
            raise Exception("No jobs found from LinkedIn.")

        if not client:
            raise HTTPException(status_code=500, detail="OpenAI client not initialized.")

        role_target = q if q else "Job Seeker"
        
        # Step 2: Pass through highly rigorous AI Anti-Scam Filter
        system_instruction = f"""
        You are a strict, world-class Anti-Scam Analyst for a premium job board. 
        Your ONLY goal is to protect users from fake jobs, ghost jobs, MLMs, unpaid internships, "pay-to-work" schemes, and severely underpaid roles.
        You will receive a list of raw job postings scraped directly from LinkedIn.

        Rules:
        1. Discard ANY job that mentions unpaid, equity-only, or "investment required".
        2. Discard ANY job that looks like a ghost job (too generic, lack of real requirements).
        3. Discard ANY job from known spammy recruitment agencies if it looks fake or lacks a real company.
        4. For the jobs that PASS the filter, write a highly structured, beautiful 3-sentence summary of the role.
        5. Generate a 'matchScore' between 50 and 99 based on how well it fits a '{role_target}'. DO NOT discard legitimate jobs simply because they are in a different industry or don't match the tech sector.
        """

        prompt = f"Raw Scraped Jobs: {json.dumps(linkedin_jobs, indent=2)}"

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
            "jobs": (admin_jobs if start == 0 else []) + [j.model_dump() for j in filtered_jobs]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

class InterviewQuestionsResult(BaseModel):
    questions: List[str]

@app.get("/api/interview-questions")
async def get_interview_questions(role: str = "Software Engineer"):
    if not client:
        return {"status": "error", "message": "OpenAI client not configured."}
    
    system_instruction = "You are a ruthless technical interviewer from a top-tier tech company. The user is interviewing for the role provided. Generate exactly 5 extremely difficult, highly-specific behavioral and technical interview questions for this specific role. Do NOT give generic questions. Make them situational and challenging."
    
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

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "GetHired Engine is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
