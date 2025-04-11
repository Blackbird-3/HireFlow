from typing import List
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class EmailGeneratorAgent:
    def __init__(self):
        # Initialize Ollama LLM
        self.llm = Ollama(model="llama3.2:1b")
        
        # Create prompt template for email generation
        self.prompt_template = PromptTemplate(
            input_variables=["candidate_name", "job_title", "proposed_dates", "interview_format"],
            template="""
            Write a professional email to invite a candidate for a job interview.
            
            Candidate Name: {candidate_name}
            Job Title: {job_title}
            Proposed Interview Dates: {proposed_dates}
            Interview Format: {interview_format}
            
            The email should be concise, professional, and include:
            1. A greeting that includes the candidate's name
            2. The purpose of the email (invitation to interview)
            3. Brief mention of the job position
            4. Proposed interview dates and format
            5. A request for the candidate to confirm their availability
            6. A professional closing
            
            Do not include any placeholder text like [Company Name] or [Recruiter Name].
            Use "HireFlow Recruitment Team" as the sender.
            """
        )
        
        # Create the chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
    def generate_interview_request(self, candidate_name: str, job_title: str, proposed_dates: List[str], interview_format: str) -> str:
        """
        Generate an interview request email
        """
        # Format the proposed dates for the template
        dates_formatted = ", ".join(proposed_dates)
        
        # Execute the chain
        try:
            email_content = self.chain.run(
                candidate_name=candidate_name,
                job_title=job_title,
                proposed_dates=dates_formatted,
                interview_format=interview_format
            )
            return email_content
        except Exception as e:
            # Fallback for any errors
            print(f"Error in email generation: {str(e)}")
            
            # Return a default email template
            return f"""
            Subject: Interview Invitation: {job_title} Position
            
            Dear {candidate_name},
            
            We are pleased to invite you for an interview for the {job_title} position. Your qualifications and experience have impressed our team, and we would like to learn more about you.
            
            Interview Details:
            - Format: {interview_format}
            - Proposed Dates: {dates_formatted}
            
            Please let us know which date and time works best for you, and we will confirm the details.
            
            We look forward to speaking with you!
            
            Best regards,
            
            HireFlow Recruitment Team
            """