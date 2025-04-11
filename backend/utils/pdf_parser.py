import io
from typing import Optional
from fastapi import UploadFile
import PyPDF2

async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Extract text content from a PDF file
    
    Args:
        file: Uploaded PDF file
        
    Returns:
        str: Extracted text content
    """
    # Read the uploaded file into memory
    content = await file.read()
    
    # Create a PDF reader object
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    
    # Extract text from all pages
    text_content = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text_content += page.extract_text() + "\n\n"
    
    # Rewind the file so it can be read again if needed
    await file.seek(0)
    
    return text_content