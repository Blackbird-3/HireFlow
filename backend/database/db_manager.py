import sqlite3
import os

DB_PATH = "hireflow.db"

def init_db():
    """Initialize the database schema if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
    -- Jobs table
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        summary TEXT,
        skills TEXT,  -- JSON array
        experience TEXT,  -- JSON array
        qualifications TEXT,  -- JSON array
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Candidates table
    CREATE TABLE IF NOT EXISTS candidates (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        cv_text TEXT NOT NULL,
        cv_filename TEXT,
        skills TEXT,  -- JSON array
        experience TEXT,  -- JSON array
        education TEXT,  -- JSON array
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Job-Candidate matches
    CREATE TABLE IF NOT EXISTS job_matches (
        job_id TEXT,
        candidate_id TEXT,
        match_score REAL,
        matched_at TIMESTAMP,
        PRIMARY KEY (job_id, candidate_id),
        FOREIGN KEY (job_id) REFERENCES jobs (id),
        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
    );
    
    -- Interview requests
    CREATE TABLE IF NOT EXISTS interview_requests (
        id TEXT PRIMARY KEY,
        candidate_id TEXT,
        job_id TEXT,
        email_content TEXT,
        proposed_dates TEXT,  -- JSON array
        interview_format TEXT,
        status TEXT,  -- pending, sent, accepted, rejected
        created_at TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates (id),
        FOREIGN KEY (job_id) REFERENCES jobs (id)
    );
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn