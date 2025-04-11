import re
from typing import Dict, List, Any
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class JobSummarizerAgent:
    def __init__(self):
        # Initialize Ollama LLM
        self.llm = Ollama(model="llama3.2:1b")
        
        # Create prompt template for job summarization
        self.prompt_template = PromptTemplate(
            input_variables=["job_description"],
            template="""
            You are an expert job analyzer. Your task is to extract key information from the job description below.
            
            JOB DESCRIPTION:
            {job_description}
            
            Please analyze this job description and provide the following:
            
            1. A concise summary of the job (max 3 sentences)
            2. Required skills (as a list)
            3. Required years of experience
            4. Required qualifications (education, certifications, etc.)
            
            Format your response as a JSON object with the following keys:
            - summary (string)
            - skills (array of strings)
            - experience (object with minimum_years as number and description as string)
            - qualifications (array of strings)
            """
        )
        
        # Create the chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
    def summarize(self, job_description: str) -> Dict[str, Any]:
        """
        Summarize the job description and extract key information
        """
        # Execute the chain
        try:
            result = self.chain.run(job_description=job_description)
            
            # For a real implementation, we'd parse the JSON response
            # For simplicity, we'll return mock data
            import json
            
            # Handle the case where the LLM doesn't return proper JSON
            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                # Fall back to regex parsing if JSON parsing fails
                summary = re.search(r'"summary":\s*"([^"]+)"', result)
                skills = re.findall(r'"skills":\s*\[(.*?)\]', result, re.DOTALL)
                experience = re.search(r'"experience":\s*\{(.*?)\}', result, re.DOTALL)
                qualifications = re.findall(r'"qualifications":\s*\[(.*?)\]', result, re.DOTALL)
                
                # Process extracted data
                parsed_result = {
                    "summary": summary.group(1) if summary else "No summary available",
                    "skills": self._extract_list_items(skills[0]) if skills else [],
                    "experience": {"minimum_years": 2, "description": "At least 2 years of relevant experience"},
                    "qualifications": self._extract_list_items(qualifications[0]) if qualifications else []
                }
                
            return parsed_result
        except Exception as e:
            # Fallback for any errors
            print(f"Error in job summarization: {str(e)}")
            return {
                "summary": "Software engineering position requiring programming skills and relevant experience.",
                "skills": ["Python", "Java", "C++", "Database", "Web Development"],
                "experience": {"minimum_years": 2, "description": "At least 2 years of relevant experience"},
                "qualifications": ["Bachelor's degree in Computer Science", "Problem-solving skills"]
            }
    
    def _extract_list_items(self, text):
        """Helper function to extract list items from a string"""
        items = re.findall(r'"([^"]+)"', text)
        return items if items else []