# Auto-Fill API v2 - Dynamic Field Extraction

## Overview

The refactored `/api/v1/orcha/auto-fill` endpoint now supports **dynamic field extraction** from documents (PDFs and images). Instead of returning a fixed set of fields, the endpoint extracts only the fields you specify in the request.

## Key Changes

### ✅ What's New
1. **Dynamic Field Selection**: Specify exactly which fields you want to extract
2. **Relaxed Validation**: No strict document type validation - extracts text regardless of document type
3. **Dynamic Response**: Returns only the fields you requested (no massive static schema)
4. **JSON-based Prompting**: LLM dynamically adjusts extraction based on your field list

### ❌ What's Removed
- Hardcoded field extraction (gender, firstname, lastname, birth_date)
- Massive static response object with 80+ fields
- Strict "valid ID/Passport" validation logic

---

## API Endpoint

### Request

**Method**: `PUT`  
**URL**: `/api/v1/orcha/auto-fill`  
**Content-Type**: `multipart/form-data`

#### Form Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Document file (PDF or image: PNG, JPG, JPEG) |
| `fields` | String (JSON) | Yes | JSON array defining which fields to extract |

#### Fields Parameter Format

```json
[
  {
    "field_name": "firstname",
    "field_type": "string"
  },
  {
    "field_name": "lastname",
    "field_type": "string"
  },
  {
    "field_name": "birth_date",
    "field_type": "date"
  },
  {
    "field_name": "nationality",
    "field_type": "string"
  }
]
```

**Note**: The `field_type` is optional and informative. The LLM will attempt to extract any field you specify.

---

### Response

#### Success Response (Data Extracted)

```json
{
  "success": true,
  "message": "success",
  "data": {
    "firstname": "John",
    "lastname": "Doe",
    "birth_date": "1990-01-15",
    "nationality": "American"
  }
}
```

#### Partial Success (Some Fields Missing)

```json
{
  "success": true,
  "message": "success",
  "data": {
    "firstname": "John",
    "lastname": "Doe",
    "birth_date": null,
    "nationality": null
  }
}
```

#### Invalid/Unreadable Document

```json
{
  "success": true,
  "message": "invalid doc",
  "data": {
    "firstname": null,
    "lastname": null,
    "birth_date": null,
    "nationality": null
  }
}
```

#### API Error

```json
{
  "success": false,
  "message": "Error processing document: <error_message>",
  "data": {}
}
```

---

## Example Usage

### Python Example

```python
import requests
import json

# Define the fields you want to extract
fields_to_extract = [
    {"field_name": "firstname", "field_type": "string"},
    {"field_name": "lastname", "field_type": "string"},
    {"field_name": "birth_date", "field_type": "date"},
    {"field_name": "nationality", "field_type": "string"}
]

# Prepare the request
url = "http://your-server.com/api/v1/orcha/auto-fill"

with open("path/to/document.pdf", "rb") as f:
    files = {
        "file": ("document.pdf", f, "application/pdf")
    }
    data = {
        "fields": json.dumps(fields_to_extract)
    }
    
    response = requests.put(url, files=files, data=data)
    result = response.json()
    
    if result["success"]:
        if result["message"] == "success":
            print("✅ Extraction successful!")
            print("Extracted data:", result["data"])
        elif result["message"] == "invalid doc":
            print("⚠️ Document is invalid or unreadable")
    else:
        print("❌ API Error:", result["message"])
```

### cURL Example

```bash
curl -X PUT http://your-server.com/api/v1/orcha/auto-fill \
  -F 'file=@/path/to/document.pdf' \
  -F 'fields=[{"field_name":"firstname","field_type":"string"},{"field_name":"lastname","field_type":"string"},{"field_name":"birth_date","field_type":"date"}]'
```

### JavaScript/Fetch Example

```javascript
const formData = new FormData();

// Add file
const fileInput = document.getElementById('fileInput');
formData.append('file', fileInput.files[0]);

// Add fields (as JSON string)
const fieldsToExtract = [
  { field_name: "firstname", field_type: "string" },
  { field_name: "lastname", field_type: "string" },
  { field_name: "birth_date", field_type: "date" },
  { field_name: "email", field_type: "string" }
];
formData.append('fields', JSON.stringify(fieldsToExtract));

// Send request
fetch('http://your-server.com/api/v1/orcha/auto-fill', {
  method: 'PUT',
  body: formData
})
  .then(response => response.json())
  .then(result => {
    if (result.success && result.message === "success") {
      console.log("✅ Extracted data:", result.data);
    } else if (result.success && result.message === "invalid doc") {
      console.log("⚠️ Document is invalid or unreadable");
    } else {
      console.error("❌ Error:", result.message);
    }
  })
  .catch(error => console.error("❌ Request failed:", error));
```

---

## Processing Flow

```
1. Receive file + fields list
   ↓
2. Extract text from document
   - PDF: Direct text extraction
   - Image: OCR processing
   ↓
3. Build dynamic LLM prompt
   - Include requested field names
   - No document validation
   ↓
4. Send to LLM for extraction
   - LLM returns JSON with requested fields
   ↓
5. Parse and return response
   - success + data if extraction worked
   - invalid doc if unreadable
   - error if API failed
```

---

## Field Examples

You can request any fields that might be present in a document:

### Identity Document Fields
```json
[
  {"field_name": "firstname", "field_type": "string"},
  {"field_name": "lastname", "field_type": "string"},
  {"field_name": "birth_date", "field_type": "date"},
  {"field_name": "birth_place", "field_type": "string"},
  {"field_name": "nationality", "field_type": "string"},
  {"field_name": "document_number", "field_type": "string"},
  {"field_name": "expiry_date", "field_type": "date"}
]
```

### Invoice Fields
```json
[
  {"field_name": "invoice_number", "field_type": "string"},
  {"field_name": "invoice_date", "field_type": "date"},
  {"field_name": "total_amount", "field_type": "number"},
  {"field_name": "vendor_name", "field_type": "string"},
  {"field_name": "tax_amount", "field_type": "number"}
]
```

### Address Fields
```json
[
  {"field_name": "street_address", "field_type": "string"},
  {"field_name": "city", "field_type": "string"},
  {"field_name": "postal_code", "field_type": "string"},
  {"field_name": "country", "field_type": "string"}
]
```

---

## Error Handling

| Scenario | Response |
|----------|----------|
| Invalid fields JSON | `{"success": false, "message": "Invalid fields parameter: ...", "data": {}}` |
| Unsupported file type | `{"success": false, "message": "Unsupported file type...", "data": {}}` |
| Empty/unreadable document | `{"success": true, "message": "invalid doc", "data": {<fields>: null}}` |
| LLM extraction failed | `{"success": true, "message": "invalid doc", "data": {<fields>: null}}` |
| API exception | `{"success": false, "message": "Error processing document: ...", "data": {}}` |

---

## Best Practices

1. **Field Naming**: Use clear, descriptive field names (e.g., `birth_date` instead of `bd`)
2. **Reasonable Field Count**: Request 3-10 fields per document for best results
3. **Field Types**: While optional, specifying `field_type` helps the LLM understand expected format
4. **Error Handling**: Always check both `success` and `message` fields in the response
5. **Document Quality**: Higher quality scans/PDFs produce better extraction results

---

## Migration Guide

### Old API (v1)
```python
# Fixed 4 fields only
response = requests.put(url, files={"file": file})
# Response had 80+ fields, most were null
```

### New API (v2)
```python
# Dynamic field selection
fields = [
    {"field_name": "firstname", "field_type": "string"},
    {"field_name": "birth_date", "field_type": "date"}
]
response = requests.put(url, files={"file": file}, data={"fields": json.dumps(fields)})
# Response only contains requested fields
```

---

## Technical Details

### LLM System Prompt (Auto-Generated)

The system dynamically generates a prompt based on your field list:

```
Analyze the provided document text. Your task is to extract the following specific fields: firstname, lastname, birth_date, nationality.

Rules:
- Do not validate if this is a real ID or Passport. Just extract the text that matches the requested fields.
- Return the result strictly as a valid JSON object.
- If a field is not found, set its value to null.
- If the document is completely unreadable or contains no text, return an empty JSON object {}.

Example output format:
{
    "firstname": "extracted_value_or_null",
    "lastname": "extracted_value_or_null"
}

Only return the JSON object, no additional text.
```

### Supported File Types
- **PDFs**: `.pdf` (text extraction via PyPDF2/pdfplumber)
- **Images**: `.png`, `.jpg`, `.jpeg` (OCR via Tesseract/Cloud OCR)

### Performance
- PDF Processing: ~1-3 seconds
- Image OCR: ~2-5 seconds
- LLM Extraction: ~2-4 seconds
- **Total**: ~5-12 seconds per document

---

## Support

For issues or questions, contact the ORCHA development team.

