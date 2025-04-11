# HireFlow - AI-Powered Recruitment System

HireFlow is a multi-agent AI system that automates and enhances the job screening and candidate matching process.

## Features

- **Job Description Analysis**: Automatically extracts key requirements, skills, and qualifications from job descriptions
- **CV/Resume Processing**: Analyzes candidate CVs to extract structured information
- **Intelligent Matching**: Calculates match scores between candidates and job positions
- **Automated Interview Scheduling**: Generates professional interview request emails for top candidates

## System Architecture

HireFlow uses a multi-agent framework powered by LangGraph:

1. **Job Summarizer Agent**: Analyzes job descriptions to extract key requirements
2. **CV Analyzer Agent**: Extracts structured data from candidate resumes
3. **Matcher Agent**: Calculates match scores between jobs and candidates
4. **Email Generator Agent**: Creates professional interview request emails

## Tech Stack

- **Backend**: FastAPI
- **Database**: SQLite
- **AI Framework**: LangChain
- **LLM**: Ollama (llama3.2:1b)
- **Vector Store**: ChromaDB
- **Frontend**: Streamlit

## Getting Started

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) with llama3.2:1b model installed

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/hireflow.git
   cd hireflow
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make sure Ollama is running with the llama3.2:1b model, nomic-embed-text for embedding:
   ```
   ollama run llama3.2:1b
   ollama pull nomic-embed-text
   ```

4. Start the API server:
   ```
   uvicorn app:app --reload
   ```

5. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

- `POST /jobs` - Create a new job listing
- `POST /candidates` - Upload a candidate's CV
- `POST /matchcv` - Match candidates with a job position
- `POST /interview-requests` - Generate and send interview requests
- `GET /jobs` - List all jobs
- `GET /candidates` - List all candidates



## License

This project is licensed under the MIT License - see the LICENSE file for details.