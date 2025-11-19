# OCR Integration Flow Diagram

## Complete Data Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                   │
│                              (React Frontend)                                 │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │
                                 │ 1. User selects image
                                 │ 2. Convert to base64
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  POST /api/v1/orcha/   │
                    │     ocr/extract        │
                    │                        │
                    │  Body:                 │
                    │  - user_id             │
                    │  - image_data (base64) │
                    │  - filename            │
                    │  - mode                │
                    └───────────┬────────────┘
                                │
                                │ 3. Request received
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              ORCHA BACKEND                                    │
│                         (FastAPI - Port 8000)                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ app/api/v1/endpoints.py                                              │   │
│  │                                                                       │   │
│  │ @router.post("/orcha/ocr/extract")                                   │   │
│  │ async def orcha_ocr_extract(req: OCRExtractRequest)                  │   │
│  │     │                                                                 │   │
│  │     └─→ Validate request                                             │   │
│  │         └─→ Call handle_ocr_extract()                                │   │
│  └───────────────────────────┬───────────────────────────────────────────┘   │
│                              │                                                │
│                              ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ app/services/orchestrator.py                                         │   │
│  │                                                                       │   │
│  │ async def handle_ocr_extract(payload, request)                       │   │
│  │     │                                                                 │   │
│  │     ├─→ Extract payload data                                         │   │
│  │     ├─→ Validate image_data                                          │   │
│  │     ├─→ Log request                                                  │   │
│  │     └─→ Call extract_text_from_image()                               │   │
│  └───────────────────────────┬───────────────────────────────────────────┘   │
│                              │                                                │
│                              ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ app/services/ocr_client.py                                           │   │
│  │                                                                       │   │
│  │ async def extract_text_from_image(image_data, filename, mode)        │   │
│  │     │                                                                 │   │
│  │     ├─→ Build request payload                                        │   │
│  │     ├─→ Set timeout from config                                      │   │
│  │     └─→ POST to OCR_SERVICE_URL/extract                              │   │
│  └───────────────────────────┬───────────────────────────────────────────┘   │
│                              │                                                │
└──────────────────────────────┼────────────────────────────────────────────────┘
                               │
                               │ 4. HTTP POST request
                               │    URL: http://localhost:8001/extract
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              OCR SERVICE                                      │
│                      (FastAPI + PaddleOCR - Port 8001)                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ app/main.py                                                          │   │
│  │                                                                       │   │
│  │ @app.post("/extract")                                                │   │
│  │ async def extract_text(request: OCRExtractRequest)                   │   │
│  │     │                                                                 │   │
│  │     ├─→ Validate image_data                                          │   │
│  │     ├─→ Validate mode                                                │   │
│  │     └─→ Call ocr_engine.extract_text()                               │   │
│  └───────────────────────────┬───────────────────────────────────────────┘   │
│                              │                                                │
│                              ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ app/ocr_engine.py                                                    │   │
│  │                                                                       │   │
│  │ class OCREngine:                                                     │   │
│  │     def extract_text(image_data, mode)                               │   │
│  │         │                                                             │   │
│  │         ├─→ decode_base64_image()                                    │   │
│  │         ├─→ Apply OCR settings based on mode                         │   │
│  │         ├─→ paddleocr.ocr(image)  ← PaddleOCR processing             │   │
│  │         ├─→ Extract text lines                                       │   │
│  │         ├─→ Calculate confidence                                     │   │
│  │         └─→ Build response with metadata                             │   │
│  └───────────────────────────┬───────────────────────────────────────────┘   │
│                              │                                                │
└──────────────────────────────┼────────────────────────────────────────────────┘
                               │
                               │ 5. Return OCR result
                               │
                               ▼
                    ┌────────────────────────┐
                    │  Response:             │
                    │  {                     │
                    │    "status": "success",│
                    │    "text": "...",      │
                    │    "confidence": 0.95, │
                    │    "metadata": {...}   │
                    │  }                     │
                    └───────────┬────────────┘
                                │
                                │ 6. Forward response to frontend
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              ORCHA BACKEND                                    │
│                           (Response Formatting)                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  orchestrator.py: handle_ocr_extract()                                       │
│    │                                                                          │
│    ├─→ Add filename to response                                              │
│    ├─→ Add ocr_mode to response                                              │
│    ├─→ Log success                                                           │
│    └─→ Return formatted response                                             │
│                                                                               │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │
                                 │ 7. Final response to frontend
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                   │
│                           (React Component)                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────────────────────────────┐             │
│  │  OCRExtractor Component                                     │             │
│  │                                                              │             │
│  │  8. Receive response                                        │             │
│  │  9. Display extracted text in window                        │             │
│  │  10. Show confidence score                                  │             │
│  │  11. Show metadata (lines, mode, etc.)                      │             │
│  │  12. Provide "Copy" button                                  │             │
│  │                                                              │             │
│  │  ┌──────────────────────────────────────────────┐          │             │
│  │  │  Extracted Text Window                        │          │             │
│  │  │  ┌──────────────────────────────────────┐   │          │             │
│  │  │  │ Lines: 15 | Confidence: 95.7% | Auto │   │          │             │
│  │  │  └──────────────────────────────────────┘   │          │             │
│  │  │                                               │          │             │
│  │  │  Text extracted from image...                │          │             │
│  │  │  Line 2 of text...                           │          │             │
│  │  │  Line 3 of text...                           │          │             │
│  │  │                                               │          │             │
│  │  │  [Copy to Clipboard] [Save as TXT]           │          │             │
│  │  └──────────────────────────────────────────────┘          │             │
│  └────────────────────────────────────────────────────────────┘             │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════

## Request/Response Examples

### Request Flow:

1. Frontend → ORCHA
   POST http://localhost:8000/api/v1/orcha/ocr/extract
   Content-Type: application/json
   {
     "user_id": "user123",
     "image_data": "iVBORw0KGgoAAAANS...",  // Base64 string
     "filename": "invoice.jpg",
     "mode": "auto"
   }

2. ORCHA → OCR Service
   POST http://localhost:8001/extract
   Content-Type: application/json
   {
     "image_data": "iVBORw0KGgoAAAANS...",
     "filename": "invoice.jpg",
     "mode": "auto"
   }

### Response Flow:

1. OCR Service → ORCHA
   {
     "status": "success",
     "text": "Invoice #12345\nDate: 2024-10-23\nTotal: $150.00",
     "confidence": 0.957,
     "metadata": {
       "total_lines": 3,
       "detection_boxes": [...],
       "avg_confidence": 0.957,
       "mode": "auto"
     }
   }

2. ORCHA → Frontend
   {
     "status": "success",
     "extracted_text": "Invoice #12345\nDate: 2024-10-23\nTotal: $150.00",
     "confidence": 0.957,
     "metadata": {
       "total_lines": 3,
       "detection_boxes": [...],
       "avg_confidence": 0.957,
       "mode": "auto"
     },
     "filename": "invoice.jpg",
     "ocr_mode": "auto"
   }


═══════════════════════════════════════════════════════════════════════════════

## Error Handling Flow

┌─────────────────┐
│  Any Component  │
└────────┬────────┘
         │
         │ Error occurs
         │
         ▼
    ┌─────────┐
    │ Try/Catch│
    └────┬────┘
         │
         ├─→ Log error (if logger available)
         ├─→ Format error message
         └─→ Return error response
                 │
                 ▼
         {
           "status": "error",
           "error": "Descriptive error message",
           "filename": "document.jpg"
         }
                 │
                 ▼
         Frontend displays error to user


═══════════════════════════════════════════════════════════════════════════════

## Configuration Points

ORCHA (app/config.py):
  ├─ OCR_SERVICE_URL = "http://localhost:8001"
  └─ OCR_TIMEOUT = 60

OCR Service (app/config.py):
  ├─ HOST = "0.0.0.0"
  ├─ PORT = 8001
  ├─ OCR_USE_GPU = False
  ├─ OCR_LANGUAGE = "en"
  ├─ OCR_USE_ANGLE_CLS = True
  └─ OCR_DET_LIMIT_SIDE_LEN = 960

Frontend (.env):
  └─ REACT_APP_API_URL = "http://localhost:8000"


═══════════════════════════════════════════════════════════════════════════════

## Timing Expectations

Image Upload:          < 1 second
Base64 Conversion:     < 1 second
ORCHA Processing:      < 100ms
OCR Processing:        2-10 seconds (depends on image size and mode)
Response Formatting:   < 100ms
Frontend Display:      < 100ms

Total Time: ~2-12 seconds depending on image complexity


═══════════════════════════════════════════════════════════════════════════════

## File Locations

ORCHA Backend:
  ├─ app/api/v1/endpoints.py           ← Endpoint definition
  ├─ app/services/orchestrator.py      ← Business logic
  ├─ app/services/ocr_client.py        ← OCR service communication
  └─ app/config.py                     ← OCR service URL

OCR Service (to be created):
  ├─ app/main.py                       ← FastAPI app
  ├─ app/ocr_engine.py                 ← PaddleOCR wrapper
  ├─ app/config.py                     ← OCR settings
  └─ requirements.txt                  ← Dependencies

Frontend (to be implemented):
  ├─ components/OCRExtractor.jsx       ← Main component
  ├─ components/OCRExtractor.css       ← Styling
  └─ .env                              ← API URL


═══════════════════════════════════════════════════════════════════════════════























