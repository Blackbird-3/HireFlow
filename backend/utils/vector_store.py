import os
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Initialize the embedding model
embedding_model = OllamaEmbeddings(model="nomic-embed-text:latest")

# Directory for persistent storage
PERSIST_DIR = "./chroma_db"

# Initialize Chroma vector store with embedding function
vectorstore = Chroma(
    collection_name="cv_collection",
    embedding_function=embedding_model,
    persist_directory=PERSIST_DIR
)

# Text splitter for long documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

def add_cv_to_vector_store(candidate_id: str,candidate_name: str , cv_text: str) -> None:
    """
    Add a CV to the vector store for semantic search
    
    Args:
        candidate_id: Unique identifier for the candidate
        cv_text: Text content of the CV
    """
    # Split text into chunks
    texts = text_splitter.split_text(cv_text)
    
    # Generate chunk IDs
    chunk_ids = [f"{candidate_id}_chunk_{i}" for i in range(len(texts))]
    
    # Metadata for each chunk
    metadatas = [{"candidate_id": candidate_id, "candidate_name": candidate_name, "chunk_index": i} for i in range(len(texts))]
    
    # Add to vector store
    vectorstore.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=chunk_ids
    )

def search_similar_cvs(job_description: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for CVs similar to a job description using RAG
    
    Args:
        job_description: Job description text
        top_k: Number of top results to return
        
    Returns:
        List of document objects with metadata
    """
    # Perform similarity search with the retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold", 
        search_kwargs={"score_threshold": 0.3, "k": top_k}
    )
    
    # Get the documents
    results = retriever.invoke(job_description)
    print(f"Found {len(results)} similar CVs.")
    print(f"Results: {results}")
    return results
    # Aggregate scores per candidate
    # candidate_scores = {}
    # candidate_names = {}
    
    # for doc, score in results:
    #     candidate_id = doc.metadata.get("candidate_id")
    #     candidate_name = doc.metadata.get("candidate_name", "Unknown")
        
    #     if candidate_id in candidate_scores:
    #         candidate_scores[candidate_id].append(score)
    #     else:
    #         candidate_scores[candidate_id] = [score]
    #         candidate_names[candidate_id] = candidate_name
    
    # # Compute average score per candidate
    # candidates = [
    #     {
    #         "candidate_id": candidate_id,
    #         "name": candidate_names.get(candidate_id, "Unknown"),
    #         "email": "N/A",  # We could fetch this from the database if needed
    #         "match_score": 1.0 - min(1.0, sum(scores) / len(scores) / 30.0),  # Convert distance to similarity score
    #         "matching_skills": []  # Placeholder for skills
    #     }
    #     for candidate_id, scores in candidate_scores.items()
    # ]

    # # Sort by match score (higher is better)
    # candidates.sort(key=lambda x: x["match_score"], reverse=True)

    # Limit to top_k candidates
    # return candidates[:top_k]