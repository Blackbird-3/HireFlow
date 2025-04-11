import streamlit as st
import requests
import pandas as pd
import json
import matplotlib.pyplot as plt
import time
from datetime import datetime
import os
import io

# Constants
API_URL = "http://localhost:8000"  # Update if your FastAPI backend is running elsewhere

# Set page configuration
st.set_page_config(
    page_title="HireFlow - AI Recruitment System",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Helper functions
def upload_job_description(title, description):
    """Upload a job description to the API"""
    response = requests.post(
        f"{API_URL}/jobs",
        json={"title": title, "description": description}
    )
    return response.json() if response.status_code == 200 else None

def upload_candidate_cv(file, name, email):
    """Upload a candidate CV to the API"""
    files = {"file": (file.name, file, "application/pdf")}
    data = {"candidate_name": name, "candidate_email": email}
    response = requests.post(f"{API_URL}/candidates", files=files, data=data)
    return response.json() if response.status_code == 200 else None

def get_jobs():
    """Get all jobs from the API"""
    response = requests.get(f"{API_URL}/jobs")
    return response.json() if response.status_code == 200 else []

def get_candidates():
    """Get all candidates from the API"""
    response = requests.get(f"{API_URL}/candidates")
    return response.json() if response.status_code == 200 else []

def match_candidates(job_id, threshold=0.3):
    """Match candidates to a job using RAG"""
    response = requests.post(
        f"{API_URL}/matchcv", 
        params={"job_id": job_id, "threshold": threshold}
    )
    
    if response.status_code == 200:
        # The response now contains Document objects with metadata
        return response.json()
    else:
        st.error(f"Error matching candidates: {response.text}")
        return []

def send_interview_request(candidate_id, job_id, proposed_dates, interview_format):
    """Send an interview request"""
    data = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "proposed_dates": proposed_dates,
        "interview_format": interview_format
    }
    response = requests.post(f"{API_URL}/interview-requests", json=data)
    return response.json() if response.status_code == 200 else None

def api_health_check():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_URL}/jobs", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Initialize session state
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = api_health_check()
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'candidates' not in st.session_state:
    st.session_state.candidates = []
if 'current_matches' not in st.session_state:
    st.session_state.current_matches = []
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

# Sidebar for navigation
st.sidebar.title("HireFlow 👔")
st.sidebar.caption("AI-Powered Recruitment System")

# API connection indicator
api_status = "✅ Connected" if st.session_state.api_connected else "❌ Disconnected"
st.sidebar.info(f"API Status: {api_status}")

# Refresh data button
if st.sidebar.button("↻ Refresh Data"):
    st.session_state.api_connected = api_health_check()
    if st.session_state.api_connected:
        st.session_state.jobs = get_jobs()
        st.session_state.candidates = get_candidates()
        st.toast("Data refreshed successfully!", icon="✅")
    else:
        st.toast("Failed to connect to API. Is the backend running?", icon="❌")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Jobs", "Candidates", "Matching", "Interview Requests"],
    key="navigation",
    index=["Dashboard", "Jobs", "Candidates", "Matching", "Interview Requests"].index(st.session_state.page)
)

# Update the current page in session state
st.session_state.page = page

# Dashboard
if page == "Dashboard":
    st.title("HireFlow Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Jobs", len(st.session_state.jobs))
        st.metric("Total Candidates", len(st.session_state.candidates))
    
    with col2:
        # Placeholder for a chart
        if len(st.session_state.jobs) > 0 and len(st.session_state.candidates) > 0:
            st.subheader("Candidates per Job")
            fig, ax = plt.subplots()
            match_counts = [len(match_candidates(job["id"])) for job in st.session_state.jobs]
            ax.bar([job["title"] for job in st.session_state.jobs], match_counts)
            ax.set_xticklabels([job["title"] for job in st.session_state.jobs], rotation=45, ha='right')
            ax.set_ylabel("Candidate Matches")
            st.pyplot(fig)
        else:
            st.info("Add jobs and candidates to see analytics")
    
    st.subheader("Quick Actions")
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        if st.button("➕ Add New Job"):
            st.session_state.page = "Jobs"
            st.rerun()
    
    with quick_col2:
        if st.button("➕ Add New Candidate"):
            st.session_state.page = "Candidates"
            st.rerun()
    
    with quick_col3:
        if st.button("🔍 Match Candidates"):
            st.session_state.page = "Matching"
            st.rerun()
    
    st.subheader("Recent Activities")
    # In a real app, you would fetch actual activity data
    st.table(pd.DataFrame({
        "Time": [datetime.now().strftime("%H:%M:%S")],
        "Activity": ["System initialized"]
    }))

# Jobs page
elif page == "Jobs":
    st.title("Job Management")
    
    # Refresh jobs
    if st.session_state.api_connected:
        st.session_state.jobs = get_jobs()
    
    # Create tabs for viewing and adding jobs
    job_tab1, job_tab2, job_tab3 = st.tabs(["View Jobs", "Add Job", "Import Jobs"])
    
    # View jobs
    with job_tab1:
        if not st.session_state.jobs:
            st.info("No jobs found. Add a new job to get started.")
        else:
            for job in st.session_state.jobs:
                with st.expander(f"{job['title']}"):
                    st.write(f"**Job ID:** {job['id']}")
                    st.write(f"**Summary:** {job['summary']}")
                    
                    # Actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Match Candidates", key=f"match_{job['id']}"):
                            st.session_state.current_job_id = job['id']
                            st.session_state.page = "Matching"
                            st.rerun()
                    with col2:
                        if st.button("Delete", key=f"delete_{job['id']}"):
                            st.error("Delete functionality not implemented yet")
    
    # Add job
    with job_tab2:
        st.subheader("Add a New Job")
        
        job_title = st.text_input("Job Title")
        job_description = st.text_area("Job Description", height=300)
        
        if st.button("Submit Job"):
            if job_title and job_description:
                with st.spinner("Processing job description..."):
                    result = upload_job_description(job_title, job_description)
                    
                if result:
                    st.success(f"Job '{job_title}' added successfully!")
                    # Refresh jobs list
                    st.session_state.jobs = get_jobs()
                else:
                    st.error("Failed to add job. Please check the API connection.")
            else:
                st.warning("Please fill in both job title and description.")
    
    # Import jobs
    with job_tab3:
        st.subheader("Import Jobs from CSV")
        
        # File upload
        uploaded_file = st.file_uploader("Upload a CSV file with job data", type="csv")
        
        if uploaded_file is not None:
            # Read CSV
            try:
                df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
                st.dataframe(df.head())
                
                if "Job Title" in df.columns and "Job Description" in df.columns:
                    if st.button("Import Jobs"):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Process each job
                        for i, row in df.iterrows():
                            progress = (i + 1) / len(df)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing job {i+1} of {len(df)}: {row['Job Title']}")

                            # Upload job
                            result = upload_job_description(row['Job Title'], row['Job Description'])
                            time.sleep(0.5)

                        status_text.text("Import completed!")
                        st.session_state.jobs = get_jobs()
                        st.success(f"Successfully imported {len(df)} jobs.")
                else:
                    st.error("CSV file must contain 'Job Title' and 'Job Description' columns.")
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")

# Candidates page
elif page == "Candidates":
    st.title("Candidate Management")
    
    # Refresh candidates
    if st.session_state.api_connected:
        st.session_state.candidates = get_candidates()
    
    # Create tabs for viewing and adding candidates
    cand_tab1, cand_tab2 = st.tabs(["View Candidates", "Add Candidate"])
    
    # View candidates
    with cand_tab1:
        if not st.session_state.candidates:
            st.info("No candidates found. Add a new candidate to get started.")
        else:
            for candidate in st.session_state.candidates:
                with st.expander(f"{candidate['name']} "):
                    st.write(f"**Candidate ID:** {candidate['id']}")
                    
                    # Actions
                    col1, col2 = st.columns(2)
                    # with col1:
                    #     if st.button("View Details", key=f"view_{candidate['id']}"):
                    #         st.info("Detail view not implemented yet")
                    with col1:
                        if st.button("Delete", key=f"delete_cand_{candidate['id']}"):
                            st.error("Delete functionality not implemented yet")
    
    # Add candidate
    with cand_tab2:
        st.subheader("Add a New Candidate")
        
        candidate_name = st.text_input("Full Name")
        candidate_email = st.text_input("Email Address")
        
        uploaded_cv = st.file_uploader("Upload CV (PDF)", type="pdf")
        
        if st.button("Submit Candidate"):
            if candidate_name and candidate_email and uploaded_cv:
                with st.spinner("Processing CV..."):
                    # Create a copy of the uploaded file
                    cv_file = io.BytesIO(uploaded_cv.getvalue())
                    cv_file.name = uploaded_cv.name
                    
                    result = upload_candidate_cv(cv_file, candidate_name, candidate_email)
                    
                if result:
                    st.success(f"Candidate '{candidate_name}' added successfully!")
                    # Refresh candidates list
                    st.session_state.candidates = get_candidates()
                else:
                    st.error("Failed to add candidate. Please check the API connection.")
            else:
                st.warning("Please fill in all fields and upload a CV.")

# Matching page
elif page == "Matching":
    st.title("Candidate-Job Matching")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Job selection
        st.subheader("Select Job")
        job_options = {job["title"]: job["id"] for job in st.session_state.jobs}
        
        if not job_options:
            st.warning("No jobs available. Please add jobs first.")
            selected_job_id = None
        else:
            if 'current_job_id' in st.session_state:
                # Find the title for the current job ID
                current_job_title = next((job["title"] for job in st.session_state.jobs 
                                        if job["id"] == st.session_state.current_job_id), 
                                        list(job_options.keys())[0])
            else:
                current_job_title = list(job_options.keys())[0]
                
            selected_job_title = st.selectbox("Job", options=list(job_options.keys()), 
                                             index=list(job_options.keys()).index(current_job_title))
            selected_job_id = job_options[selected_job_title]
    
    with col2:
        # Matching threshold
        st.subheader("Threshold Settings")
        threshold = st.slider("Minimum Match Score", min_value=0.0, max_value=1.0, value=0.7, step=0.05, 
                             help="Lower values will include more candidates with lower match scores")
    
    # Run matching
    if selected_job_id and st.button("Run Matching"):
        with st.spinner("Matching candidates..."):
            matches = match_candidates(selected_job_id, threshold)
            st.session_state.current_matches = matches
    
    # Display matches
    if 'current_matches' in st.session_state and st.session_state.current_matches:
        st.subheader(f"Matches: {len(st.session_state.current_matches)} candidates")
        
        # Create a dataframe for better display
        match_data = []
        for match in st.session_state.current_matches:
            # Handle matching skills display
            matching_skills = match.get("matching_skills", [])
            skill_display = ", ".join(matching_skills[:3])
            if len(matching_skills) > 3:
                skill_display += f" + {len(matching_skills) - 3} more"
                
            match_data.append({
                "Name": match.get("name", "Unknown"),
                "Email": match.get("email", "N/A"),
                "Match Score": f"{match.get('match_score', 0):.2f}",
                "Matching Skills": skill_display
            })
        
        df_matches = pd.DataFrame(match_data)
        st.dataframe(df_matches)
        
        # Visualize match scores
        st.subheader("Match Score Distribution")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Sort by match score for better visualization
        sorted_matches = sorted(st.session_state.current_matches, 
                                key=lambda x: x.get("match_score", 0), 
                                reverse=True)
        
        names = [m.get("name", f"Candidate {i}") for i, m in enumerate(sorted_matches)]
        scores = [m.get("match_score", 0) for m in sorted_matches]
        
        bars = ax.bar(names, scores, color='#4CAF50')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.set_ylabel("Match Score")
        ax.set_ylim(0, 1)
        ax.set_title("Candidate Match Scores")
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig)
        
        # Display detailed candidate information in expandable sections
        st.subheader("Candidate Details")
        for match in sorted_matches:
            with st.expander(f"{match.get('name', 'Unknown')} - {match.get('match_score', 0):.2f} match"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Matching Skills")
                    if match.get("matching_skills"):
                        for skill in match.get("matching_skills"):
                            st.markdown(f"- {skill}")
                    else:
                        st.markdown("No specific skills extracted")
                
                with col2:
                    # Additional candidate information could be displayed here
                    st.subheader("Contact")
                    st.markdown(f"**Email:** {match.get('email', 'N/A')}")
                    
                    # If there's a CV document link, add it here
                    if "cv_document" in match:
                        st.markdown(f"**CV Document:** [View]({match['cv_document']})")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View Full Resume", key=f"view_{match.get('candidate_id')}"):
                        st.info("Resume view functionality to be implemented")
                
                with col2:
                    if st.button("Schedule Interview", key=f"interview_{match.get('candidate_id')}"):
                        st.session_state.interview_job_id = selected_job_id
                        st.session_state.interview_candidate_id = match.get("candidate_id")
                        st.session_state.page = "Interview Requests"
                        st.rerun()
        
        # Select candidate for interview
        st.subheader("Schedule Interview")
        candidate_options = {
            f"{match.get('name', 'Unknown')} ({match.get('match_score', 0):.2f})": match.get("candidate_id") 
            for match in st.session_state.current_matches
        }
        
        if candidate_options:
            selected_candidate = st.selectbox("Select Candidate", options=list(candidate_options.keys()))
            selected_candidate_id = candidate_options[selected_candidate]
            
            if st.button("Schedule Interview"):
                st.session_state.interview_job_id = selected_job_id
                st.session_state.interview_candidate_id = selected_candidate_id
                st.session_state.page = "Interview Requests"
                st.rerun()
        else:
            st.info("No candidates matched the criteria")
    elif st.session_state.get('current_matches') == []:
        st.info("No candidates matched the selected criteria. Try lowering the threshold.")
        
        
# Interview Requests page
elif page == "Interview Requests":
    st.title("Interview Request Management")
    
    # Check if we have a candidate and job selected
    if ('interview_candidate_id' in st.session_state and 
        'interview_job_id' in st.session_state):
        
        # Get candidate and job details
        candidate_id = st.session_state.interview_candidate_id
        job_id = st.session_state.interview_job_id
        
        # Find candidate name
        candidate_name = next((c["name"] for c in st.session_state.candidates 
                              if c["id"] == candidate_id), "Unknown")
        
        # Find job title
        job_title = next((j["title"] for j in st.session_state.jobs 
                         if j["id"] == job_id), "Unknown")
        
        st.subheader(f"Schedule Interview: {candidate_name} for {job_title}")
        
        # Interview details
        col1, col2 = st.columns(2)
        
        with col1:
            interview_format = st.selectbox(
                "Interview Format",
                ["Remote Video Call", "Phone Interview", "In-Person", "Technical Assessment"]
            )
        
        with col2:
            date_options = []
            for i in range(5):  # Next 5 business days
                date = datetime.now() + pd.Timedelta(days=i+1)
                if date.weekday() < 5:  # Monday to Friday
                    date_options.append(date.strftime("%Y-%m-%d"))
            
            proposed_dates = st.multiselect(
                "Proposed Dates",
                options=date_options,
                default=date_options[:2]
            )
        
        if st.button("Generate Interview Request"):
            if proposed_dates:
                with st.spinner("Generating interview request..."):
                    result = send_interview_request(
                        candidate_id,
                        job_id,
                        proposed_dates,
                        interview_format
                    )
                
                if result:
                    st.success("Interview request generated successfully!")
                    
                    # Display the email
                    st.subheader("Email Preview")
                    st.code(result["email_content"], language="text")
                    
                    # Option to download
                    email_content_bytes = result["email_content"].encode()
                    st.download_button(
                        label="Download Email",
                        data=email_content_bytes,
                        file_name=f"interview_request_{candidate_name.replace(' ', '_')}.txt",
                        mime="text/plain"
                    )
                else:
                    st.error("Failed to generate interview request. Please check the API connection.")
            else:
                st.warning("Please select at least one proposed date.")
    else:
        st.info("Select a candidate from the Matching page to schedule an interview.")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("HireFlow - AI-Powered Recruitment System")
st.sidebar.caption("Hackathon Project")