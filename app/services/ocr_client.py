# app/services/ocr_client.py
import httpx
from app.config import settings
from typing import Optional

async def call_ocr(file_uri: str, mode: str = "auto", timeout: int = None):
    """
    Call OCR service with a file URI.
    Legacy method for URI-based OCR.
    """
    timeout = timeout or settings.OCR_TIMEOUT
    url = f"{settings.OCR_SERVICE_URL.rstrip('/')}/ocr"
    payload = {"file_uri": file_uri, "mode": mode}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()

async def extract_text_from_image(image_data: str, filename: str = "image", language: str = "en", timeout: int = None):
    """
    Call OCR service with base64 encoded image data.
    
    Args:
        image_data: Base64 encoded image string
        filename: Original filename (for metadata)
        language: Language code (en, fr, ar, ch, etc.)
        timeout: Request timeout in seconds
    
    Returns:
        dict: OCR response containing extracted text and metadata
              {
                  "success": True,
                  "text": "extracted text",
                  "lines_count": 10,
                  "message": "Text extracted successfully"
              }
    """
    import base64
    import io
    
    timeout = timeout or settings.OCR_TIMEOUT
    url = f"{settings.OCR_SERVICE_URL.rstrip('/')}/extract-text"
    
    try:
        # Convert base64 to bytes
        if ',' in image_data:
            image_data = image_data.split(',')[1]  # Remove data URL prefix
        
        image_bytes = base64.b64decode(image_data)
        
        # Prepare multipart form data
        files = {"file": (filename, io.BytesIO(image_bytes), "image/jpeg")}
        data = {"lang": language}
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, files=files, data=data)
            r.raise_for_status()
            return r.json()
            
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "lines_count": 0,
            "message": f"Error: {str(e)}"
        }
