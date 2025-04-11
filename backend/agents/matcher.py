from typing import Dict, List, Any
import numpy as np

class MatcherAgent:
    def __init__(self):
        # Define weights for different matching criteria
        self.weights = {
            "skills": 0.5,
            "experience": 0.3,
            "education": 0.2
        }
    
    def calculate_match(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """
        Calculate the match score between a job and a candidate
        
        Args:
            job: Job data including skills, experience, qualifications
            candidate: Candidate data including skills, experience, education
            
        Returns:
            float: Match score between 0 and 1
        """
        # Calculate skills match
        skills_match = self._calculate_skills_match(job["skills"], candidate["skills"])
        
        # Calculate experience match
        experience_match = self._calculate_experience_match(
            job.get("experience", {}), 
            candidate.get("experience", [])
        )
        
        # Calculate education match
        education_match = self._calculate_education_match(
            job.get("qualifications", []), 
            candidate.get("education", [])
        )
        
        # Calculate weighted score
        total_score = (
            skills_match * self.weights["skills"] +
            experience_match * self.weights["experience"] +
            education_match * self.weights["education"]
        )
        
        return round(total_score, 2)
    
    def _calculate_skills_match(self, job_skills: List[str], candidate_skills: List[str]) -> float:
        """Calculate the match between required skills and candidate skills"""
        if not job_skills or not candidate_skills:
            return 0.0
        
        # Normalize skills (lower case)
        job_skills_norm = [skill.lower() for skill in job_skills]
        candidate_skills_norm = [skill.lower() for skill in candidate_skills]
        
        # Count matched skills
        matched_skills = [skill for skill in candidate_skills_norm if any(job_skill in skill for job_skill in job_skills_norm)]
        
        # Calculate score
        return len(matched_skills) / len(job_skills) if job_skills else 0.0
    
    def _calculate_experience_match(self, job_experience: Dict[str, Any], candidate_experience: List[Dict[str, Any]]) -> float:
        """Calculate the match between required experience and candidate experience"""
        # This is a simplified implementation
        # In a real system, we'd use NLP to match job titles and responsibilities
        
        if not job_experience or not candidate_experience:
            return 0.5  # Neutral score if missing data
        
        # Extract required years if available
        required_years = job_experience.get("minimum_years", 0)
        
        # Calculate candidate's total years of experience
        # In a real implementation, we'd parse the dates properly
        candidate_years = len(candidate_experience)  # Simplified: each job is 1 year
        
        # Calculate score based on years
        if candidate_years >= required_years:
            return 1.0
        elif required_years == 0:
            return 0.5
        else:
            return candidate_years / required_years
    
    def _calculate_education_match(self, job_qualifications: List[str], candidate_education: List[Dict[str, Any]]) -> float:
        """Calculate the match between required qualifications and candidate education"""
        if not job_qualifications or not candidate_education:
            return 0.5  # Neutral score if missing data
        
        # Extract education levels from qualifications
        education_keywords = {
            "bachelor": ["bachelor", "bs", "ba", "undergraduate", "college"],
            "master": ["master", "ms", "ma", "graduate"],
            "phd": ["phd", "doctorate", "doctoral"]
        }
        
        # Find required education level
        required_level = "none"
        for qual in job_qualifications:
            qual_lower = qual.lower()
            for level, keywords in education_keywords.items():
                if any(keyword in qual_lower for keyword in keywords):
                    required_level = level
                    break
            if required_level != "none":
                break
        
        # Find candidate's highest education level
        candidate_level = "none"
        for edu in candidate_education:
            degree_lower = edu.get("degree", "").lower()
            for level, keywords in education_keywords.items():
                if any(keyword in degree_lower for keyword in keywords):
                    if level == "phd" or (level == "master" and candidate_level != "phd") or (level == "bachelor" and candidate_level == "none"):
                        candidate_level = level
            
        # Score based on education level
        education_scores = {
            "none": 0.0,
            "bachelor": 0.7,
            "master": 0.9,
            "phd": 1.0
        }
        
        education_requirements = {
            "none": ["none", "bachelor", "master", "phd"],
            "bachelor": ["bachelor", "master", "phd"],
            "master": ["master", "phd"],
            "phd": ["phd"]
        }
        
        # Check if candidate meets the education requirement
        if candidate_level in education_requirements.get(required_level, []):
            return 1.0
        else:
            return education_scores.get(candidate_level, 0.0)
    
    def get_matching_skills(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> List[str]:
        """Get the list of skills that match between the job and the candidate"""
        job_skills_norm = [skill.lower() for skill in job["skills"]]
        candidate_skills_norm = [skill.lower() for skill in candidate["skills"]]
        
        matched_skills = []
        for candidate_skill in candidate["skills"]:
            if any(job_skill in candidate_skill.lower() for job_skill in job_skills_norm):
                matched_skills.append(candidate_skill)
                
        return matched_skills