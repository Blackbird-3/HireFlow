# app.py - Main FastAPI application

import os
import uuid
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

# Import our core modules
from database.db_manager import init_db, get_db_connection
from agents.job_summarizer import JobSummarizerAgent
from agents.cv_analyzer import CVAnalyzerAgent
from agents.matcher import MatcherAgent
from agents.email_generator import EmailGeneratorAgent
from utils.pdf_parser import extract_text_from_pdf
from utils.vector_store import add_cv_to_vector_store, search_similar_cvs

app = FastAPI(title="HireFlow API", description="AI-powered recruitment system")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Pydantic models for request/response validation
class JobDescription(BaseModel):
    title: str
    description: str

class Candidate(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    cv_text: str
    cv_filename: str
    match_score: Optional[float] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    
class InterviewRequest(BaseModel):
    candidate_id: str
    job_id: str
    proposed_dates: List[str]
    interview_format: str
    
# API Endpoints
@app.post("/jobs", response_model=Dict[str, Any])
async def create_job(job: JobDescription):
    # Initialize the job summarizer agent
    summarizer = JobSummarizerAgent()
    
    # Generate summary and extract key information
    summary_result = summarizer.summarize(job.description)
    
    # Store in database
    conn = get_db_connection()
    cursor = conn.cursor()
    job_id = str(uuid.uuid4())
    
    cursor.execute(
        """
        INSERT INTO jobs (id, title, description, summary, skills, experience, qualifications)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            job.title,
            job.description,
            summary_result["summary"],
            json.dumps(summary_result["skills"]),
            json.dumps(summary_result["experience"]),
            json.dumps(summary_result["qualifications"])
        )
    )
    conn.commit()
    conn.close()
    
    return {
        "job_id": job_id,
        "title": job.title,
        "summary": summary_result["summary"],
        "skills": summary_result["skills"],
        "experience": summary_result["experience"],
        "qualifications": summary_result["qualifications"]
    }

@app.post("/candidates", response_model=Dict[str, Any])
async def upload_cv(file: UploadFile = File(...), candidate_name: str = None, candidate_email: str = None):
    # Extract text from CV
    try:
        cv_text = await extract_text_from_pdf(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process PDF: {str(e)}")
    
    # Initialize CV analyzer agent
    analyzer = CVAnalyzerAgent()
    
    # Extract information from CV
    cv_info = analyzer.analyze(cv_text)
    
    # If name not provided, use the one extracted from CV
    if not candidate_name and "name" in cv_info:
        candidate_name = cv_info["name"]
    
    # If email not provided, use the one extracted from CV
    if not candidate_email and "email" in cv_info:
        candidate_email = cv_info["email"]
    
    # Generate a candidate ID
    candidate_id = str(uuid.uuid4())
    
    # Store in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO candidates (id, name, email, cv_text, cv_filename, skills, experience, education)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            candidate_id,
            candidate_name,
            candidate_email,
            cv_text,
            file.filename,
            json.dumps(cv_info.get("skills", [])),
            json.dumps(cv_info.get("experience", [])),
            json.dumps(cv_info.get("education", []))
        )
    )
    conn.commit()
    conn.close()
    
    # Add to vector store for semantic search
    add_cv_to_vector_store(candidate_id,candidate_name, cv_text)
    
    return {
        "candidate_id": candidate_id,
        "name": candidate_name,
        "email": candidate_email,
        "skills": cv_info.get("skills", []),
        "experience": cv_info.get("experience", []),
        "education": cv_info.get("education", [])
    }

@app.post("/match", response_model=List[Dict[str, Any]])
async def match_candidates(job_id: str, threshold: float = 0.8):
    # Get job details
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    
    if not job:
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = {
        "id": job[0],
        "title": job[1],
        "description": job[2],
        "summary": job[3],
        "skills": json.loads(job[4]),
        "experience": json.loads(job[5]),
        "qualifications": json.loads(job[6])
    }
    
    # Get all candidates
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()
    conn.close()
    
    # Initialize matcher agent
    matcher = MatcherAgent()
    
    # Match each candidate against the job
    matched_candidates = []
    for candidate in candidates:
        candidate_data = {
            "id": candidate[0],
            "name": candidate[1],
            "email": candidate[2],
            "cv_text": candidate[3],
            "cv_filename": candidate[4],
            "skills": json.loads(candidate[5]),
            "experience": json.loads(candidate[6]),
            "education": json.loads(candidate[7])
        }
        
        # Calculate match score
        match_score = matcher.calculate_match(job_data, candidate_data)
        
        # Add to results if above threshold
        if match_score >= threshold:
            matched_candidates.append({
                "candidate_id": candidate_data["id"],
                "name": candidate_data["name"],
                "email": candidate_data["email"],
                "match_score": match_score,
                "matching_skills": matcher.get_matching_skills(job_data, candidate_data)
            })
    
    # Update match score in database
    conn = get_db_connection()
    cursor = conn.cursor()
    for candidate in matched_candidates:
        cursor.execute(
            "INSERT OR REPLACE INTO job_matches (job_id, candidate_id, match_score, matched_at) VALUES (?, ?, ?, ?)",
            (job_id, candidate["candidate_id"], candidate["match_score"], datetime.now().isoformat())
        )
    conn.commit()
    conn.close()
    
    # Sort by match score (highest first)
    matched_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    
    return matched_candidates

# @app.post("/matchcv")
# async def match_cand(job_id: str, threshold: float = 0.8):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
#     job = cursor.fetchone()
    
#     if not job:
#         conn.close()
#         raise HTTPException(status_code=404, detail="Job not found")
    
#     job_data = {
#         "id": job[0],
#         "title": job[1],
#         "description": job[2],
#         "summary": job[3],
#         "skills": json.loads(job[4]),
#         "experience": json.loads(job[5]),
#         "qualifications": json.loads(job[6])
#     }
    
#     # Get all candidates
#     cursor.execute("SELECT * FROM candidates")
#     candidates = cursor.fetchall()
#     conn.close()
    
#     res=search_similar_cvs(job_data["description"], top_k=5)
#     print(res)
#     return res

@app.post("/matchcv", response_model=List[Dict[str, Any]])
async def match_cv(job_id: str, threshold: float = 0.7):
    # Get job details
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    
    if not job:
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = {
        "id": job[0],
        "title": job[1],
        "description": job[2],
        "summary": job[3],
        "skills": json.loads(job[4]),
        "experience": json.loads(job[5]),
        "qualifications": json.loads(job[6])
    }
    
    # Search for similar CVs using RAG
    # The search function returns Document objects
    docs = search_similar_cvs(job_data["description"], top_k=5)
    
    # Process the retrieved documents into a consistent format
    candidate_matches = {}
    
    # Group by candidate_id to avoid duplicates
    for doc in docs:
        candidate_id = doc.metadata.get('candidate_id')
        match_score = 0.8  # Default score - in a real implementation, use doc.score
        
        if candidate_id not in candidate_matches:
            candidate_matches[candidate_id] = {
                "candidate_id": candidate_id,
                "name": doc.metadata.get('candidate_name', 'Unknown'),
                "match_score": match_score,
                "content": []
            }
        
        # Add this document's content
        candidate_matches[candidate_id]["content"].append(doc.page_content)
    
    # Convert dictionary to list
    matched_candidates = list(candidate_matches.values())
    
    # Filter by threshold
    matched_candidates = [c for c in matched_candidates if c["match_score"] >= threshold]
    
    # Get additional info for each candidate from database
    for candidate in matched_candidates:
        cursor.execute("SELECT name, email, skills FROM candidates WHERE id = ?", (candidate["candidate_id"],))
        result = cursor.fetchone()
        if result:
            candidate["name"] = result[0]
            candidate["email"] = result[1]
            
            # Extract skills from CV content or use from database
            skills = []
            for content in candidate["content"]:
                if "Skills" in content:
                    skills_section = content.split("Skills")[1].split("Certifications")[0] if "Certifications" in content else content.split("Skills")[1]
                    # Extract skills mentioned after "Skills" heading
                    skill_lines = skills_section.strip().split('\n')
                    for line in skill_lines:
                        if '-' in line:
                            skill = line.split('-')[1].strip() if len(line.split('-')) > 1 else line.strip()
                            skills.append(skill)
            
            # If no skills extracted, use from database
            if not skills and result[2]:
                skills = json.loads(result[2])
            
            candidate["matching_skills"] = skills[:5]  # Get top 5 skills
    
    # Remove the content field as it's not needed in the response
    for candidate in matched_candidates:
        if "content" in candidate:
            del candidate["content"]
    
    # Update match score in database
    for candidate in matched_candidates:
        cursor.execute(
            "INSERT OR REPLACE INTO job_matches (job_id, candidate_id, match_score, matched_at) VALUES (?, ?, ?, ?)",
            (job_id, candidate["candidate_id"], candidate["match_score"], datetime.now().isoformat())
        )
    conn.commit()
    conn.close()
    
    return matched_candidates

@app.post("/interview-requests", response_model=Dict[str, Any])
async def send_interview_request(request: InterviewRequest):
    # Get candidate and job details
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM candidates WHERE id = ?", (request.candidate_id,))
    candidate = cursor.fetchone()
    
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (request.job_id,))
    job = cursor.fetchone()
    
    if not candidate or not job:
        conn.close()
        raise HTTPException(status_code=404, detail="Candidate or job not found")
    
    candidate_data = {
        "id": candidate[0],
        "name": candidate[1],
        "email": candidate[2]
    }
    
    job_data = {
        "id": job[0],
        "title": job[1]
    }
    
    # Generate email content
    email_generator = EmailGeneratorAgent()
    email_content = email_generator.generate_interview_request(
        candidate_name=candidate_data["name"],
        job_title=job_data["title"],
        proposed_dates=request.proposed_dates,
        interview_format=request.interview_format
    )
    
    # Store in database
    request_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO interview_requests 
        (id, candidate_id, job_id, email_content, proposed_dates, interview_format, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_id,
            request.candidate_id,
            request.job_id,
            email_content,
            json.dumps(request.proposed_dates),
            request.interview_format,
            "pending",
            datetime.now().isoformat()
        )
    )
    conn.commit()
    conn.close()
    
    # In a real application, we would send the email here
    # For now, we'll just return the email content
    
    return {
        "request_id": request_id,
        "candidate_email": candidate_data["email"],
        "email_content": email_content,
        "status": "pending"
    }

@app.get("/jobs", response_model=List[Dict[str, Any]])
async def list_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, summary FROM jobs")
    jobs = cursor.fetchall()
    conn.close()
    
    return [{"id": job[0], "title": job[1], "summary": job[2]} for job in jobs]

@app.get("/candidates", response_model=List[Dict[str, Any]])
async def list_candidates():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM candidates")
    candidates = cursor.fetchall()
    conn.close()
    
    return [{"id": c[0], "name": c[1], "email": c[2]} for c in candidates]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)