# Document Verification API - `/api/v1/orcha/doc-check`

## Overview

Public API endpoint for automated document verification. Accepts identity documents (passports, national IDs, driver's licenses) in PDF or image format, extracts text, and validates authenticity using AI-powered analysis.

**Base URL**: `https://aura-orcha.vaeerdia.com`  
**Endpoint**: `PUT /api/v1/orcha/doc-check`  
**Authentication**: None required (public API for partner integrations)

**⚠️ Note**: This endpoint uses **PUT** instead of POST as a workaround for nginx reverse proxy limitations.

---

## Request Format

### Headers
```
Content-Type: multipart/form-data
```

### Form Data Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | Document file (PDF or image: PNG, JPEG, JPG) |
| `label` | String | Yes | What the document is (e.g., "passport", "cin", "driver_license", "id_card") |

**Note**: The external app sends the actual file (PDF or image), and ORCHA handles the base64 conversion internally.

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
   - External app sends file via multipart/form-data with `file` and `label`
   - ORCHA receives the file (PDF or image)
   - Detects MIME type automatically from file content and extension

2. **Internal Conversion**
   - ORCHA converts file to base64 internally (external app sends raw file)
   - No need for external apps to handle base64 encoding

3. **Text Extraction**
   - **PDF Documents**: Direct text extraction using PDF parser
   - **Image Documents**: OCR processing to extract text from image (PNG, JPEG, etc.)
   - Validates that text was successfully extracted (minimum 10 characters)

4. **Dynamic Validation Prompt**
   - System builds validation prompt using the `label` provided
   - The `label` is injected into the prompt to guide the AI
   - Example: If label is "passport", prompt asks AI to verify passport-specific fields

5. **LLM Analysis**
   - Extracted text sent to AI model with label-based specialized prompt
   - Model analyzes document structure, completeness, and consistency
   - Returns brief validation result (2-3 sentences max)

6. **Response Generation**
   - Determines `success` status based on LLM response
   - Returns standardized response format with validation details

---

## Usage Examples

### Example 1: Validating a Passport (PDF)

```bash
curl -X PUT https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@passport.pdf" \
  -F "label=passport"
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
curl -X POST https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@cin.jpg" \
  -F "label=cin"
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
curl -X POST https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@suspicious_passport.pdf" \
  -F "label=passport"
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

## Supported Document Types (via label)

You can use any label describing the document. Common examples:

| Label Example | Description |
|---------------|-------------|
| `passport` | International passports |
| `cin` | Carte d'Identite Nationale |
| `id_card` | National identity cards |
| `driver_license` | Driving permits |
| `residence_permit` | Residence permits |
| `birth_certificate` | Birth certificates |

**Note**: The `label` is used directly in the validation prompt, so be descriptive!

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

### JavaScript/Node.js (Browser)

```javascript
async function verifyDocument(file, label) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('label', label);
  
  const response = await fetch('https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check', {
    method: 'PUT',
    body: formData
    // Note: Don't set Content-Type header - browser sets it automatically with boundary
  });
  
  const result = await response.json();
  
  if (result.success) {
    console.log('Document is valid:', result.data.Res_validation);
  } else {
    console.log('Document is invalid:', result.data.Res_validation);
  }
  
  return result;
}

// Usage with file input
document.getElementById('uploadBtn').addEventListener('click', async () => {
  const fileInput = document.getElementById('fileInput');
  const label = document.getElementById('labelInput').value;
  
  if (fileInput.files.length > 0) {
    const result = await verifyDocument(fileInput.files[0], label);
    console.log(result);
  }
});
```

### JavaScript/Node.js (Server)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const fetch = require('node-fetch');

async function verifyDocument(filePath, label) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));
  formData.append('label', label);
  
  const response = await fetch('https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check', {
    method: 'PUT',
    body: formData
  });
  
  const result = await response.json();
  
  if (result.success) {
    console.log('Valid:', result.data.Res_validation);
  } else {
    console.log('Invalid:', result.data.Res_validation);
  }
  
  return result;
}

// Usage
verifyDocument('./passport.pdf', 'passport');
```

### Python

```python
import requests

def verify_document(file_path, label):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'label': label}
        
        response = requests.put(
            'https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check',
            files=files,
            data=data
        )
    
    result = response.json()
    
    if result['success']:
        print(f"Valid: {result['data']['Res_validation']}")
    else:
        print(f"Invalid: {result['data']['Res_validation']}")
    
    return result

# Usage
verify_document('./passport.pdf', 'passport')
verify_document('./cin.jpg', 'cin')
```

### PHP

```php
<?php
$file_path = './passport.pdf';
$label = 'passport';

$curl = curl_init();

$file = new CURLFile($file_path);
$post_data = array(
    'file' => $file,
    'label' => $label
);

curl_setopt($curl, CURLOPT_URL, 'https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check');
curl_setopt($curl, CURLOPT_CUSTOMREQUEST, 'PUT');
curl_setopt($curl, CURLOPT_POSTFIELDS, $post_data);
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);

$response = curl_exec($curl);
$result = json_decode($response, true);

if ($result['success']) {
    echo "Valid: " . $result['data']['Res_validation'];
} else {
    echo "Invalid: " . $result['data']['Res_validation'];
}

curl_close($curl);
?>
```

---

## Best Practices

1. **File Size**: Keep documents under 10MB for optimal processing
2. **Image Quality**: For images, ensure minimum 300 DPI for accurate OCR
3. **Label Field**: Use descriptive labels (e.g., "passport", "cin", "driver_license") - the label guides AI validation
4. **File Format**: Send raw files (PDF or images) - ORCHA handles base64 conversion internally
5. **Error Handling**: Always check the `success` field before processing results
6. **Retry Logic**: Implement retry with exponential backoff for network errors
7. **Content-Type**: Use `multipart/form-data` (automatically set when using FormData)

---

## Rate Limiting

Currently no rate limits enforced. For production use, implement client-side rate limiting:
- Recommended: Max 60 requests per minute per client
- Batch processing: Process documents in batches of 10-20

---

## Support

For technical support or integration assistance:
- **Email**: support@vaeerdia.com
- **API Documentation**: `https://aura-orcha.vaeerdia.com/docs`
- **Status**: Check service status at `https://aura-orcha.vaeerdia.com/health`

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

