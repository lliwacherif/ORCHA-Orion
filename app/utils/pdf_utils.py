# app/utils/pdf_utils.py
import base64
import io
import PyPDF2
from typing import Optional


def extract_pdf_text(base64_data: str) -> str:
    """
    Extract text from a base64-encoded PDF file.
    
    Args:
        base64_data: Base64 string (the 'data' field from attachment)
    
    Returns:
        Extracted text from all PDF pages
    
    Raises:
        Exception: If PDF cannot be decoded or read
    """
    try:
        # Decode base64 to bytes
        file_bytes = base64.b64decode(base64_data)
        
        # Create a file-like object
        pdf_file = io.BytesIO(file_bytes)
        
        # Read PDF
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {page_num} ---\n{page_text}"
        
        return text
    except Exception as e:
        raise Exception(f"Failed to extract PDF text: {str(e)}")


def is_valid_pdf_base64(base64_data: str) -> bool:
    """
    Check if a base64 string represents a valid PDF file.
    
    Args:
        base64_data: Base64 string to validate
    
    Returns:
        True if valid PDF, False otherwise
    """
    try:
        file_bytes = base64.b64decode(base64_data)
        # Check PDF magic bytes (should start with %PDF)
        return file_bytes.startswith(b'%PDF')
    except Exception:
        return False

