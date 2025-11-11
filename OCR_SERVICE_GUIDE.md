# OCR Service Implementation Guide

## Overview
This guide will help you build the OCR service that works with ORCHA. The OCR service will receive base64-encoded images from ORCHA, extract text using OCR technology, and return the extracted text.

---

## Architecture

```
Frontend → ORCHA (POST /api/v1/orcha/ocr/extract) → OCR Service (POST /extract) → ORCHA → Frontend
```

**Flow:**
1. Frontend sends image (base64) to ORCHA endpoint `/api/v1/orcha/ocr/extract`
2. ORCHA forwards the image to OCR service at `/extract`
3. OCR service processes the image and extracts text
4. OCR service returns extracted text with metadata
5. ORCHA returns the text to frontend for display

---

## Requirements

### Python Dependencies
```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
paddleocr>=2.7.0
paddlepaddle>=2.5.0  # or paddlepaddle-gpu for GPU support
opencv-python>=4.8.0
pillow>=10.0.0
python-multipart>=0.0.6
pydantic>=2.0.0
```

### System Requirements
- Python 3.8+
- Sufficient RAM (2GB+ recommended)
- Optional: CUDA-compatible GPU for faster processing

---

## OCR Service Implementation

### 1. Project Structure
```
ocr-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── ocr_engine.py
├── requirements.txt
└── README.md
```

### 2. Configuration (`app/config.py`)

```python
# app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # OCR settings
    OCR_USE_GPU: bool = False  # Set to True if you have CUDA GPU
    OCR_LANGUAGE: str = "en"   # Supported: en, ch, fr, german, korean, japan
    
    # Performance settings
    OCR_USE_ANGLE_CLS: bool = True  # Enable text direction classification
    OCR_DET_LIMIT_SIDE_LEN: int = 960  # Detection model input size limit
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3. OCR Engine (`app/ocr_engine.py`)

```python
# app/ocr_engine.py
from paddleocr import PaddleOCR
from app.config import settings
import base64
import io
from PIL import Image
import numpy as np
from typing import Dict, Any, List

class OCREngine:
    def __init__(self):
        """Initialize PaddleOCR engine."""
        self.ocr = PaddleOCR(
            use_angle_cls=settings.OCR_USE_ANGLE_CLS,
            lang=settings.OCR_LANGUAGE,
            use_gpu=settings.OCR_USE_GPU,
            det_limit_side_len=settings.OCR_DET_LIMIT_SIDE_LEN,
            show_log=False  # Disable verbose logging
        )
    
    def decode_base64_image(self, base64_string: str) -> np.ndarray:
        """Decode base64 string to image array."""
        # Remove data URI prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64 to bytes
        img_bytes = base64.b64decode(base64_string)
        
        # Convert to PIL Image
        img = Image.open(io.BytesIO(img_bytes))
        
        # Convert to RGB if needed (handle RGBA, grayscale, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(img)
        
        return img_array
    
    def extract_text(self, image_data: str, mode: str = "auto") -> Dict[str, Any]:
        """
        Extract text from base64 encoded image.
        
        Args:
            image_data: Base64 encoded image string
            mode: OCR mode (auto, fast, accurate)
                  - auto: balanced speed and accuracy
                  - fast: faster processing, lower accuracy
                  - accurate: slower processing, higher accuracy
        
        Returns:
            dict: {
                "status": "success",
                "text": "extracted text",
                "confidence": 0.95,
                "metadata": {
                    "total_lines": 10,
                    "detection_boxes": [...],
                    "avg_confidence": 0.95
                }
            }
        """
        try:
            # Decode image
            img_array = self.decode_base64_image(image_data)
            
            # Adjust OCR parameters based on mode
            if mode == "fast":
                # Use faster but less accurate settings
                det_limit_side_len = 640
            elif mode == "accurate":
                # Use more accurate but slower settings
                det_limit_side_len = 1280
            else:  # auto
                det_limit_side_len = settings.OCR_DET_LIMIT_SIDE_LEN
            
            # Perform OCR
            result = self.ocr.ocr(img_array, cls=settings.OCR_USE_ANGLE_CLS)
            
            if not result or not result[0]:
                return {
                    "status": "success",
                    "text": "",
                    "confidence": 0.0,
                    "metadata": {
                        "total_lines": 0,
                        "message": "No text detected in image"
                    }
                }
            
            # Extract text and confidence from results
            extracted_lines = []
            confidences = []
            detection_boxes = []
            
            for line in result[0]:
                if line:
                    # line structure: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)]
                    box = line[0]
                    text_info = line[1]
                    text = text_info[0]
                    confidence = text_info[1]
                    
                    extracted_lines.append(text)
                    confidences.append(confidence)
                    detection_boxes.append({
                        "box": box,
                        "text": text,
                        "confidence": confidence
                    })
            
            # Combine all text
            full_text = "\n".join(extracted_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                "status": "success",
                "text": full_text,
                "confidence": round(avg_confidence, 3),
                "metadata": {
                    "total_lines": len(extracted_lines),
                    "detection_boxes": detection_boxes,
                    "avg_confidence": round(avg_confidence, 3),
                    "mode": mode
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "text": "",
                "confidence": 0.0,
                "metadata": {
                    "error": str(e)
                }
            }

# Global OCR engine instance
ocr_engine = OCREngine()
```

### 4. Main Application (`app/main.py`)

```python
# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
from app.config import settings
from app.ocr_engine import ocr_engine

app = FastAPI(
    title="OCR Service",
    description="Text extraction service using PaddleOCR",
    version="1.0.0"
)

class OCRExtractRequest(BaseModel):
    image_data: str  # Base64 encoded image
    filename: Optional[str] = "image"
    mode: Optional[str] = "auto"  # auto, fast, accurate

class OCRExtractResponse(BaseModel):
    status: str
    text: str
    confidence: float
    metadata: dict

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "OCR Service",
        "status": "running",
        "version": "1.0.0",
        "ocr_engine": "PaddleOCR",
        "language": settings.OCR_LANGUAGE,
        "gpu_enabled": settings.OCR_USE_GPU
    }

@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "ocr_engine": "initialized",
        "settings": {
            "language": settings.OCR_LANGUAGE,
            "use_gpu": settings.OCR_USE_GPU,
            "use_angle_cls": settings.OCR_USE_ANGLE_CLS
        }
    }

@app.post("/extract", response_model=OCRExtractResponse)
async def extract_text(request: OCRExtractRequest):
    """
    Extract text from base64 encoded image.
    
    Args:
        request: OCRExtractRequest containing image_data, filename, and mode
    
    Returns:
        OCRExtractResponse with extracted text and metadata
    """
    if not request.image_data:
        raise HTTPException(status_code=400, detail="image_data is required")
    
    # Validate mode
    valid_modes = ["auto", "fast", "accurate"]
    if request.mode not in valid_modes:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid mode. Must be one of: {', '.join(valid_modes)}"
        )
    
    try:
        # Extract text using OCR engine
        result = ocr_engine.extract_text(
            image_data=request.image_data,
            mode=request.mode
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["metadata"].get("error", "OCR processing failed"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True  # Set to False in production
    )
```

### 5. Requirements File

```txt
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
paddleocr==2.7.0.3
paddlepaddle==2.5.2
opencv-python==4.8.1.78
pillow==10.1.0
python-multipart==0.0.6
pydantic==2.5.0
numpy==1.24.3
```

---

## Deployment

### Option 1: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Option 2: Production with Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

### Option 3: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8001

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

Build and run:
```bash
docker build -t ocr-service .
docker run -p 8001:8001 ocr-service
```

---

## Testing

### Test with cURL

```bash
# Test health check
curl http://localhost:8001/health

# Test OCR extraction (with base64 image)
curl -X POST http://localhost:8001/extract \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "filename": "test.png",
    "mode": "auto"
  }'
```

### Test with Python

```python
import requests
import base64

# Read and encode image
with open("test_image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Send request
response = requests.post(
    "http://localhost:8001/extract",
    json={
        "image_data": image_data,
        "filename": "test_image.jpg",
        "mode": "auto"
    }
)

print(response.json())
```

---

## Configuration for ORCHA

Make sure ORCHA's `app/config.py` has the correct OCR service URL:

```python
# In ORCHA's app/config.py
OCR_SERVICE_URL: str = "http://localhost:8001"  # or your OCR service URL
```

---

## Performance Optimization

### 1. GPU Acceleration
If you have a CUDA-compatible GPU:
```bash
# Install GPU version
pip uninstall paddlepaddle
pip install paddlepaddle-gpu
```

Update `.env`:
```
OCR_USE_GPU=true
```

### 2. Batch Processing
For multiple images, you can modify the engine to support batch processing.

### 3. Caching
Consider adding Redis caching for frequently processed images.

---

## Troubleshooting

### Issue: Low accuracy
- Solution: Use `mode="accurate"` or increase `OCR_DET_LIMIT_SIDE_LEN`

### Issue: Slow processing
- Solution: Use `mode="fast"` or enable GPU acceleration

### Issue: Memory issues
- Solution: Reduce `OCR_DET_LIMIT_SIDE_LEN` or process smaller images

### Issue: Wrong language detection
- Solution: Set `OCR_LANGUAGE` to the correct language code

---

## API Reference

### POST `/extract`

**Request:**
```json
{
  "image_data": "base64EncodedImageString",
  "filename": "document.jpg",
  "mode": "auto"
}
```

**Response:**
```json
{
  "status": "success",
  "text": "Extracted text from the image\nLine 2\nLine 3",
  "confidence": 0.957,
  "metadata": {
    "total_lines": 3,
    "detection_boxes": [
      {
        "box": [[10, 10], [100, 10], [100, 30], [10, 30]],
        "text": "Extracted text from the image",
        "confidence": 0.98
      }
    ],
    "avg_confidence": 0.957,
    "mode": "auto"
  }
}
```

---

## Next Steps

1. Deploy the OCR service on your preferred platform
2. Update ORCHA's configuration with your OCR service URL
3. Test the integration using the Frontend OCR Guide
4. Monitor performance and adjust settings as needed

For frontend implementation, see `FRONTEND_OCR_GUIDE.md`.























