import os
import requests
import json
import time
from pathlib import Path
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("demo_workflow")

# Constants
API_URL = "http://localhost:8000"
SAMPLE_DATA_DIR = "sample_data"

# Sample job descriptions
SAMPLE_JOBS = [
    {
        "title": "Senior Python Developer",
        "description": """
        We are looking for a Senior Python Developer to join our growing team. 
        
        Responsibilities:
        - Design, develop, and maintain Python applications
        - Lead development of new features and product improvements
        - Mentor junior developers and review code
        - Participate in architectural decisions
        - Troubleshoot and debug applications
        
        Requirements:
        - 5+ years of experience with Python
        - Strong knowledge of web frameworks like Django or FastAPI
        - Experience with RESTful APIs and microservices architecture
        - Familiarity with databases (SQL and NoSQL)
        - Knowledge of container technologies like Docker
        - Experience with version control systems (Git)
        - Strong problem-solving skills and attention to detail
        
        Bonus Qualifications:
        - Experience with machine learning libraries (TensorFlow, PyTorch)
        - DevOps experience with CI/CD pipelines
        - Knowledge of cloud services (AWS, GCP, Azure)
        - Open-source contributions
        
        Benefits:
        - Competitive salary and equity options
        - Remote-friendly work environment
        - Professional development budget
        - Health, dental, and vision insurance
        - 401(k) matching
        """
    },
    {
        "title": "Data Scientist",
        "description": """
        Join our data science team to help uncover insights from our growing datasets.
        
        Responsibilities:
        - Design and implement statistical models to analyze complex data
        - Create data visualizations and dashboards
        - Collaborate with product and engineering teams
        - Communicate findings and recommendations to stakeholders
        - Develop and maintain data pipelines
        
        Requirements:
        - Master's or PhD in Statistics, Computer Science, or related field
        - 3+ years of experience in data science
        - Strong programming skills in Python and R
        - Experience with machine learning frameworks
        - Knowledge of SQL and NoSQL databases
        - Familiarity with data visualization tools
        - Excellent communication skills
        
        Preferred Qualifications:
        - Experience with large-scale data processing
        - Knowledge of deep learning frameworks (TensorFlow, PyTorch)
        - Experience with NLP and computer vision
        - Cloud platform experience (AWS, GCP, Azure)
        
        Benefits:
        - Flexible work arrangements
        - Collaborative and innovative team
        - Continuous learning opportunities
        - Competitive compensation package
        """
    },
    {
        "title": "UX/UI Designer",
        "description": """
        We're seeking a talented UX/UI Designer to create beautiful, intuitive interfaces for our products.
        
        Responsibilities:
        - Create user-centered designs by understanding business requirements and user feedback
        - Create user flows, wireframes, prototypes and mockups
        - Design UI elements and tools such as navigation menus, search boxes, tabs, and widgets
        - Develop UX design solutions that meet or exceed business goals and requirements
        - Adjust designs based on user feedback and testing results
        - Present and defend designs and key deliverables to peers and executives
        
        Requirements:
        - Bachelor's degree in Design, HCI, or equivalent experience
        - 3+ years of UX/UI design experience for digital products or services
        - Proficiency in design tools (Figma, Sketch, Adobe XD)
        - Strong portfolio demonstrating UI design skills
        - Understanding of user research and usability principles
        - Knowledge of HTML, CSS, and JavaScript basics
        - Excellent communication and presentation skills
        
        Nice to Have:
        - Experience with design systems
        - Knowledge of accessibility standards
        - Animation and interaction design experience
        - Experience with mobile-first and responsive design
        
        Benefits:
        - Creative work environment
        - Design conferences and workshops
        - Latest design tools and resources
        - Collaborative team structure
        """
    }
]

# Sample CV texts (simplified for demo purposes)
SAMPLE_CVS = [
    {
        "name": "Alex Johnson",
        "email": "alex.johnson@example.com",
        "content": """
        ALEX JOHNSON
        alex.johnson@example.com | (123) 456-7890 | github.com/alexj
        
        SUMMARY
        Senior Python Developer with 7 years of experience building scalable web applications and microservices.
        Expertise in Django, FastAPI, and cloud infrastructure with AWS.
        
        SKILLS
        - Languages: Python, JavaScript, SQL
        - Frameworks: Django, FastAPI, Flask, React
        - Databases: PostgreSQL, MongoDB, Redis
        - Tools: Docker, Kubernetes, Git, CI/CD (Jenkins, GitHub Actions)
        - Cloud: AWS (EC2, S3, Lambda, RDS), Google Cloud Platform
        
        EXPERIENCE
        
        Senior Backend Developer | TechCorp Inc. | 2021-Present
        - Led team of 5 developers building a high-throughput API platform using FastAPI
        - Redesigned database schema resulting in 40% performance improvement
        - Implemented CI/CD pipeline reducing deployment time by 60%
        - Mentored junior developers and conducted code reviews
        
        Python Developer | DataSolutions | 2018-2021
        - Developed Django applications serving 100K+ daily active users
        - Created RESTful APIs integrated with third-party services
        - Optimized query performance through database indexing and caching
        - Implemented authentication and authorization systems
        
        Junior Developer | WebStart | 2016-2018
        - Built and maintained web applications using Flask and React
        - Developed automated testing suites with pytest
        - Collaborated with UX/UI team on frontend implementations
        
        EDUCATION
        B.S. Computer Science, University of Washington, 2016
        
        CERTIFICATIONS
        - AWS Certified Developer
        - MongoDB Certified Developer
        """
    },
    {
        "name": "Sarah Chen",
        "email": "sarah.chen@example.com",
        "content": """
        SARAH CHEN, Ph.D.
        sarah.chen@example.com | (987) 654-3210 | github.com/sarahc
        
        SUMMARY
        Data Scientist with Ph.D. in Applied Mathematics and 4 years of industry experience.
        Specialist in machine learning, statistical modeling, and big data analytics.
        
        SKILLS
        - Languages: Python, R, SQL
        - Libraries: scikit-learn, TensorFlow, PyTorch, Pandas, NumPy
        - Big Data: Spark, Hadoop
        - Visualization: Matplotlib, Seaborn, Tableau
        - Cloud: AWS, Google Cloud
        
        EXPERIENCE
        
        Senior Data Scientist | AnalyticsPro | 2022-Present
        - Developed predictive models improving customer retention by 25%
        - Built real-time recommendation system processing 10M+ daily events
        - Created NLP pipeline for sentiment analysis achieving 92% accuracy
        - Led team of 3 data scientists on time-series forecasting project
        
        Data Scientist | TechInnovate | 2020-2022
        - Implemented computer vision algorithms for product quality control
        - Designed A/B testing framework for product features
        - Created interactive dashboards for business stakeholders
        - Optimized machine learning models for production deployment
        
        Research Assistant | Stanford University | 2018-2020
        - Published 3 papers on neural networks in top conferences
        - Developed algorithms for analyzing genomic sequence data
        - Collaborated on interdisciplinary research projects
        
        EDUCATION
        Ph.D. Applied Mathematics, Stanford University, 2020
        M.S. Statistics, University of Michigan, 2017
        B.S. Mathematics, UCLA, 2015
        
        PUBLICATIONS
        - "Advancements in Neural Network Architectures," NeurIPS 2020
        - "Statistical Models for Genomic Data," ICML 2019
        """
    },
    {
        "name": "Michael Rodriguez",
        "email": "michael.rodriguez@example.com",
        "content": """
        MICHAEL RODRIGUEZ
        michael.rodriguez@example.com | (555) 123-4567 | behance.net/michaelr
        
        SUMMARY
        Creative UX/UI Designer with 5 years of experience designing intuitive interfaces for web and mobile applications.
        Passionate about user-centered design and creating visually appealing experiences.
        
        SKILLS
        - Design Tools: Figma, Sketch, Adobe XD, Photoshop, Illustrator
        - Prototyping: InVision, Principle, Framer
        - Frontend: HTML, CSS, JavaScript (basic)
        - Research: User interviews, usability testing, A/B testing
        - Other: Design systems, accessibility standards, animation
        
        EXPERIENCE
        
        Senior UI/UX Designer | DesignWorks | 2021-Present
        - Led redesign of e-commerce platform resulting in 35% increase in conversion
        - Created comprehensive design system used across 10+ products
        - Conducted user research and usability testing for key features
        - Collaborated with development team on implementation details
        
        UX Designer | CreativeApps | 2019-2021
        - Designed mobile applications for iOS and Android
        - Created interactive prototypes for client presentations
        - Implemented user feedback resulting in improved satisfaction scores
        - Contributed to company design guidelines
        
        Junior Designer | WebSolutions | 2017-2019
        - Designed landing pages and marketing materials
        - Created wireframes and mockups for web applications
        - Participated in brainstorming sessions and design critiques
        
        EDUCATION
        B.A. Graphic Design, Rhode Island School of Design, 2017
        
        CERTIFICATIONS
        - Google UX Design Professional Certificate
        - Interaction Design Foundation UX Certificate
        """
    }
]

def ensure_sample_data_dir():
    """Ensure sample data directory exists"""
    sample_dir = Path(SAMPLE_DATA_DIR)
    if not sample_dir.exists():
        sample_dir.mkdir(parents=True)
        logger.info(f"Created sample data directory: {sample_dir}")
    
    # Create CVs directory
    cv_dir = sample_dir / "cvs"
    if not cv_dir.exists():
        cv_dir.mkdir(parents=True)
        logger.info(f"Created CVs directory: {cv_dir}")
    
    return sample_dir, cv_dir

def create_sample_cvs(cv_dir):
    """Create sample CV PDF files (simulated for the demo)"""
    cv_paths = []
    
    for i, cv_data in enumerate(SAMPLE_CVS):
        # In a real demo, you would generate actual PDFs
        # Here we'll just create text files with .pdf extension for simplicity
        filename = f"{cv_data['name'].replace(' ', '_')}.pdf"
        file_path = cv_dir / filename
        
        with open(file_path, 'w') as f:
            f.write(cv_data['content'])
        
        logger.info(f"Created sample CV: {filename}")
        cv_paths.append((file_path, cv_data['name'], cv_data['email']))
    
    return cv_paths

def check_api_running():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_URL}/jobs", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def upload_job(title, description):
    """Upload a job to the API"""
    response = requests.post(
        f"{API_URL}/jobs",
        json={"title": title, "description": description}
    )
    
    if response.status_code == 200:
        job_data = response.json()
        logger.info(f"Uploaded job: {title} (ID: {job_data['job_id']})")
        return job_data
    else:
        logger.error(f"Failed to upload job: {title} - {response.status_code}")
        return None

def upload_candidate(cv_path, name, email):
    """Upload a candidate CV to the API"""
    with open(cv_path, 'rb') as f:
        files = {"file": (cv_path.name, f, "application/pdf")}
        data = {"candidate_name": name, "candidate_email": email}
        
        response = requests.post(f"{API_URL}/candidates", files=files, data=data)
        
        if response.status_code == 200:
            candidate_data = response.json()
            logger.info(f"Uploaded candidate: {name} (ID: {candidate_data['candidate_id']})")
            return candidate_data
        else:
            logger.error(f"Failed to upload candidate: {name} - {response.status_code}")
            return None

def match_candidates(job_id, threshold=0.7):
    """Match candidates to a job"""
    response = requests.post(f"{API_URL}/match", params={"job_id": job_id, "threshold": threshold})
    
    if response.status_code == 200:
        matches = response.json()
        logger.info(f"Found {len(matches)} matches for job ID: {job_id}")
        return matches
    else:
        logger.error(f"Failed to match candidates for job ID: {job_id} - {response.status_code}")
        return []

def send_interview_request(candidate_id, job_id):
    """Send an interview request"""
    # Generate some sample dates
    from datetime import datetime, timedelta
    today = datetime.now()
    proposed_dates = [
        (today + timedelta(days=i+1)).strftime("%Y-%m-%d")
        for i in range(3)
    ]
    
    data = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "proposed_dates": proposed_dates,
        "interview_format": "Remote Video Call"
    }
    
    response = requests.post(f"{API_URL}/interview-requests", json=data)
    
    if response.status_code == 200:
        request_data = response.json()
        logger.info(f"Sent interview request (ID: {request_data['request_id']})")
        return request_data
    else:
        logger.error(f"Failed to send interview request - {response.status_code}")
        return None

def run_demo():
    """Run the complete demo workflow"""
    logger.info("Starting HireFlow demo workflow")
    
    # Check if API is running
    if not check_api_running():
        logger.error("API is not running. Please start the FastAPI backend first.")
        return False
    
    # Ensure sample data directories exist
    sample_dir, cv_dir = ensure_sample_data_dir()
    
    # Create sample CVs
    cv_paths = create_sample_cvs(cv_dir)
    
    # Upload sample jobs
    job_data_list = []
    for job in SAMPLE_JOBS:
        job_data = upload_job(job["title"], job["description"])
        if job_data:
            job_data_list.append(job_data)
            # Add a small delay to prevent overwhelming the API
            time.sleep(1)
    
    if not job_data_list:
        logger.error("Failed to upload any jobs. Aborting demo.")
        return False
    
    # Upload sample candidates
    candidate_data_list = []
    for cv_path, name, email in cv_paths:
        candidate_data = upload_candidate(cv_path, name, email)
        if candidate_data:
            candidate_data_list.append(candidate_data)
            # Add a small delay to prevent overwhelming the API
            time.sleep(1)
    
    if not candidate_data_list:
        logger.error("Failed to upload any candidates. Aborting demo.")
        return False
    
    # Run matching for each job
    for job_data in job_data_list:
        logger.info(f"Running matching for job: {job_data['title']}")
        matches = match_candidates(job_data['job_id'])
        
        # For the first job with matches, send an interview request
        if matches and not any("interview_sent" in job_data for job_data in job_data_list):
            # Get the highest scoring candidate
            best_match = matches[0]
            
            logger.info(f"Sending interview request to {best_match['name']} for {job_data['title']}")
            interview_data = send_interview_request(best_match['candidate_id'], job_data['job_id'])
            
            if interview_data:
                job_data["interview_sent"] = True
                # Display the email content
                logger.info("Interview request email:")
                print("\n" + "="*60 + "\n")
                print(interview_data["email_content"])
                print("\n" + "="*60 + "\n")
    
    logger.info("Demo workflow completed successfully")
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="HireFlow Demo Workflow")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    
    args = parser.parse_args()
    
    global API_URL
    API_URL = args.api_url
    
    run_demo()

if __name__ == "__main__":
    main()