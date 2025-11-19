# Document Verification API - `/api/v1/orcha/doc-check`

## Overview

Public API endpoint for automated document verification. Accepts identity documents (passports, national IDs, driver's licenses) in PDF or image format, extracts text, and validates authenticity using AI-powered analysis.

**Base URL**: `https://aura.vaeerdia.com`  
**Endpoint**: `POST /api/v1/orcha/doc-check`  
**Authentication**: None required (public API for partner integrations)

---

## Request Format

### Headers
```
Content-Type: application/json
```

### Request Body

```json
{
  "document_data": "base64_encoded_document_string",
  "document_type": "passport",
  "mime_type": "application/pdf",
  "filename": "passport.pdf"
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document_data` | string | Yes | Base64-encoded document content |
| `document_type` | string | Yes | Type of document: `passport`, `cin`, `id_card`, `national_id`, `driver_license`, `driving_license` |
| `mime_type` | string | No | Document MIME type. Default: `application/pdf`<br>Supported: `application/pdf`, `image/png`, `image/jpeg`, `image/jpg` |
| `filename` | string | No | Original filename (for logging). Default: `document` |

---

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "document valide",
  "data": {
    "Res_validation": "VALID: Passport contains all mandatory fields including valid passport number, issue/expiry dates, and proper MRZ format. Document structure is consistent with standard international passport format."
  }
}
```

### Failure Response

```json
{
  "success": false,
  "message": "document non valide",
  "data": {
    "Res_validation": "INVALID: Missing expiry date field. Passport number format appears incorrect for stated issuing country. MRZ checksum validation failed."
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | `true` if document is valid, `false` if invalid |
| `message` | string | `"document valide"` or `"document non valide"` |
| `data.Res_validation` | string | Detailed validation result with reasoning (2-3 sentences) |

---

## How It Works

### Processing Flow

1. **Document Reception**
   - API receives base64-encoded document with metadata
   - Validates MIME type and document type

2. **Text Extraction**
   - **PDF Documents**: Direct text extraction using PDF parser
   - **Image Documents**: OCR processing to extract text from image
   - Validates that text was successfully extracted (minimum 10 characters)

3. **Specialized Validation**
   - System selects validation prompt based on `document_type`
   - Each document type has specialized criteria:
     - **Passport**: Checks passport number, MRZ, dates, issuing country
     - **CIN/ID Card**: Checks ID number, issuing authority, personal info
     - **Driver's License**: Checks license number, categories, validity dates

4. **LLM Analysis**
   - Extracted text sent to AI model with specialized prompt
   - Model analyzes document structure, completeness, and consistency
   - Returns brief validation result (2-3 sentences max)

5. **Response Generation**
   - Determines `success` status based on LLM response
   - Returns standardized response format

---

## Usage Examples

### Example 1: Validating a Passport (PDF)

```bash
curl -X POST https://aura.vaeerdia.com/api/v1/orcha/doc-check \
  -H "Content-Type: application/json" \
  -d '{
    "document_data": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC...",
    "document_type": "passport",
    "mime_type": "application/pdf",
    "filename": "passport.pdf"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "document valide",
  "data": {
    "Res_validation": "VALID: Passport number P123456789 follows correct format, all mandatory fields present including valid MRZ. Issue date (2020-01-15) and expiry date (2030-01-15) are valid."
  }
}
```

### Example 2: Validating a National ID (Image)

```bash
curl -X POST https://aura.vaeerdia.com/api/v1/orcha/doc-check \
  -H "Content-Type: application/json" \
  -d '{
    "document_data": "iVBORw0KGgoAAAANSUhEUgAA...",
    "document_type": "cin",
    "mime_type": "image/jpeg",
    "filename": "cin.jpg"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "document valide",
  "data": {
    "Res_validation": "VALID: National ID number format is correct, issuing authority clearly stated, all personal information fields are present and consistent."
  }
}
```

### Example 3: Invalid Document

```bash
curl -X POST https://aura.vaeerdia.com/api/v1/orcha/doc-check \
  -H "Content-Type: application/json" \
  -d '{
    "document_data": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC...",
    "document_type": "passport",
    "mime_type": "application/pdf",
    "filename": "suspicious_passport.pdf"
  }'
```

**Response:**
```json
{
  "success": false,
  "message": "document non valide",
  "data": {
    "Res_validation": "INVALID: Passport number format does not match any known country format. Expiry date is missing. MRZ appears to be incomplete or corrupted."
  }
}
```

---

## Supported Document Types

| Type | Value | Description |
|------|-------|-------------|
| Passport | `passport` | International passports |
| National ID | `cin`, `id_card`, `national_id` | National identity cards |
| Driver's License | `driver_license`, `driving_license` | Driving permits |

---

## Supported File Formats

- **PDF**: `application/pdf`
- **PNG**: `image/png`
- **JPEG**: `image/jpeg`, `image/jpg`

---

## Error Handling

### Empty Document
```json
{
  "success": false,
  "message": "document non valide",
  "data": {
    "Res_validation": "Document appears to be empty or unreadable. No text could be extracted."
  }
}
```

### Unsupported Format
```json
{
  "success": false,
  "message": "document non valide",
  "data": {
    "Res_validation": "Unsupported document type: application/msword"
  }
}
```

### OCR Failure
```json
{
  "success": false,
  "message": "document non valide",
  "data": {
    "Res_validation": "Unable to extract text from image: OCR service unavailable"
  }
}
```

---

## Integration Guide

### JavaScript/Node.js

```javascript
const fs = require('fs');

async function verifyDocument(filePath, documentType) {
  // Read file and convert to base64
  const fileBuffer = fs.readFileSync(filePath);
  const base64Doc = fileBuffer.toString('base64');
  
  // Determine MIME type
  const mimeType = filePath.endsWith('.pdf') 
    ? 'application/pdf' 
    : 'image/jpeg';
  
  const response = await fetch('https://aura.vaeerdia.com/api/v1/orcha/doc-check', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      document_data: base64Doc,
      document_type: documentType,
      mime_type: mimeType,
      filename: filePath.split('/').pop()
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    console.log('Document is valid:', result.data.Res_validation);
  } else {
    console.log('Document is invalid:', result.data.Res_validation);
  }
  
  return result;
}

// Usage
verifyDocument('./passport.pdf', 'passport');
```

### Python

```python
import base64
import requests

def verify_document(file_path, document_type):
    # Read and encode file
    with open(file_path, 'rb') as f:
        document_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Determine MIME type
    mime_type = 'application/pdf' if file_path.endswith('.pdf') else 'image/jpeg'
    
    response = requests.post(
        'https://aura.vaeerdia.com/api/v1/orcha/doc-check',
        json={
            'document_data': document_data,
            'document_type': document_type,
            'mime_type': mime_type,
            'filename': file_path.split('/')[-1]
        }
    )
    
    result = response.json()
    
    if result['success']:
        print(f"Valid: {result['data']['Res_validation']}")
    else:
        print(f"Invalid: {result['data']['Res_validation']}")
    
    return result

# Usage
verify_document('./passport.pdf', 'passport')
```

---

## Best Practices

1. **File Size**: Keep documents under 10MB for optimal processing
2. **Image Quality**: For images, ensure minimum 300 DPI for accurate OCR
3. **Document Type**: Always specify the correct `document_type` for accurate validation
4. **Error Handling**: Always check the `success` field before processing results
5. **Retry Logic**: Implement retry with exponential backoff for network errors

---

## Rate Limiting

Currently no rate limits enforced. For production use, implement client-side rate limiting:
- Recommended: Max 60 requests per minute per client
- Batch processing: Process documents in batches of 10-20

---

## Support

For technical support or integration assistance:
- **Email**: support@vaeerdia.com
- **API Documentation**: `https://aura.vaeerdia.com/docs`
- **Status**: Check service status at `https://aura.vaeerdia.com/health`

---

## Technical Notes

- **Processing Time**: 3-10 seconds per document (PDF: 3-5s, Images: 5-10s)
- **Maximum Document Size**: 10MB
- **Text Extraction Limit**: First 4000 characters analyzed
- **AI Model**: Specialized document verification model with domain expertise
- **OCR Service**: PaddleOCR with multi-language support

---

## Changelog

**Version 1.0** (Current)
- Initial release
- Support for passport, CIN, and driver's license validation
- PDF and image format support
- Brief validation responses (2-3 sentences)

