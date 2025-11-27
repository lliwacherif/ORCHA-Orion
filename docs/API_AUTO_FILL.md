# Auto-Fill API Documentation

## Endpoint Overview

The **Auto-Fill API** is a public endpoint designed to scan ID documents (ID Cards or Passports) and automatically extract personal information for form auto-completion.

---

## Endpoint Details

| Property       | Value                                          |
|----------------|------------------------------------------------|
| **URL**        | `https://aura-orcha.vaeerdia.com/api/v1/orcha/auto-fill` |
| **Method**     | `PUT`                                          |
| **Auth**       | None (Public/Open)                             |
| **Content-Type** | `multipart/form-data`                        |

---

## Request

### Form Data Parameters

| Parameter | Type   | Required | Description                                      |
|-----------|--------|----------|--------------------------------------------------|
| `file`    | File   | Yes      | ID document file (PDF or image PNG/JPG)          |

### Supported File Types

- **PDF** (`.pdf`)
- **JPEG** (`.jpg`, `.jpeg`)
- **PNG** (`.png`)

---

## Processing Flow

```
┌─────────────────┐
│  Upload File    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Detect Type    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌───────┐
│  PDF  │  │ Image │
└───┬───┘  └───┬───┘
    │          │
    ▼          ▼
┌─────────┐  ┌─────────┐
│ Extract │  │   OCR   │
│  Text   │  │ Extract │
└────┬────┘  └────┬────┘
     │            │
     └─────┬──────┘
           │
           ▼
    ┌─────────────┐
    │     LLM     │
    │  Analysis   │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   Extract   │
    │   4 Fields  │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   Return    │
    │   Response  │
    └─────────────┘
```

### Detailed Flow:

1. **PDF Files**: Converted to Base64 and text is extracted directly, then sent to the LLM for analysis.
2. **Image Files**: Processed through OCR service first to extract raw text, then the text is sent to the LLM.

---

## Response

### Success Response

```json
{
    "success": true,
    "message": "",
    "data": {
        "id": null,
        "is_vip": 0,
        "language": "",
        "fid": null,
        "org_id": null,
        "is_group": 0,
        "employer_id": null,
        "fullname": "",
        "gender": "M",
        "firstname": "John",
        "lastname": "Doe",
        "maidenname": "",
        "birth_date": "1990-01-15",
        "birth_place": "",
        "birth_country_code": "",
        "nationality": "",
        "nationality_2": null,
        "nationality_3": null,
        "email": null,
        "tel_1": "",
        "tel_2": "",
        "def_address_id": null,
        "def_bank_account_id": null,
        "adr": "",
        "adr_2": "",
        "zipcode": "",
        "city": "",
        "country_code": "",
        "bank_name": null,
        "bank_iban": "",
        "bank_bic": "",
        "lifecycle": null,
        "is_hr": 0,
        "staff_number": "",
        "created_at": null,
        "updated_at": null,
        "created_by": null,
        "updated_by": null,
        "deleted_at": null,
        "origin": null,
        "source_id": null,
        "reference": "",
        "social_sec_number": "",
        "citizen_id": null,
        "family_number": "",
        "type_account": null,
        "agency_name": null,
        "agency_code": null,
        "bank_country_code": null,
        "bank_contact": null,
        "agency_adress": null,
        "control_key": null,
        "bank_identifier_code": null,
        "bank_branch_code": null,
        "account_number": null,
        "rib_key": null,
        "rib": null,
        "bank_country": null,
        "bank_start_date": null,
        "bank_end_date": null,
        "locked_by": null,
        "locked_at": null,
        "identity_doc": null,
        "batchId": null,
        "childrens_count_by_type": [],
        "addresses": [],
        "banks": [],
        "moral": null,
        "childrens": [],
        "update": {
            "by": "",
            "at": null
        }
    }
}
```

### Extracted Fields

| Field        | Type   | Description                              |
|--------------|--------|------------------------------------------|
| `gender`     | String | `"M"` (Male) or `"F"` (Female) or `null` |
| `firstname`  | String | First name extracted from document       |
| `lastname`   | String | Last name extracted from document        |
| `birth_date` | String | Birth date (format varies by document)   |

### Failure Response

When the document cannot be processed or is invalid:

```json
{
    "success": false,
    "message": "Document seems to be unvalid",
    "data": {
        "id": null,
        "gender": null,
        "firstname": "",
        "lastname": "",
        "birth_date": null,
        ... // all other fields as null/empty
    }
}
```

---

## Example Usage

### cURL

```bash
curl -X PUT \
  https://aura-orcha.vaeerdia.com/api/v1/orcha/auto-fill \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/path/to/id_card.jpg'
```

### JavaScript (Fetch)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('https://aura-orcha.vaeerdia.com/api/v1/orcha/auto-fill', {
    method: 'PUT',
    body: formData
});

const result = await response.json();

if (result.success) {
    console.log('Extracted data:', {
        gender: result.data.gender,
        firstname: result.data.firstname,
        lastname: result.data.lastname,
        birth_date: result.data.birth_date
    });
} else {
    console.error('Failed:', result.message);
}
```

### Python (requests)

```python
import requests

url = "https://aura-orcha.vaeerdia.com/api/v1/orcha/auto-fill"

with open("id_card.pdf", "rb") as f:
    files = {"file": ("id_card.pdf", f, "application/pdf")}
    response = requests.put(url, files=files)

result = response.json()

if result["success"]:
    print(f"Gender: {result['data']['gender']}")
    print(f"First Name: {result['data']['firstname']}")
    print(f"Last Name: {result['data']['lastname']}")
    print(f"Birth Date: {result['data']['birth_date']}")
else:
    print(f"Error: {result['message']}")
```

---

## Error Scenarios

| Scenario                  | `success` | `message`                                           |
|---------------------------|-----------|-----------------------------------------------------|
| Invalid/unreadable doc    | `false`   | `"Document seems to be unvalid"`                    |
| Unsupported file type     | `false`   | `"Unsupported file type. Please upload PDF or image (PNG/JPG)."` |
| OCR failure               | `false`   | `"Document seems to be unvalid"`                    |
| Empty/corrupted file      | `false`   | `"Document seems to be unvalid"`                    |
| Server error              | `false`   | `"Error processing document: {error details}"`      |

---

## CORS Support

This endpoint supports Cross-Origin Resource Sharing (CORS) for browser-based applications:

- **Allowed Origins**: `*` (all origins)
- **Allowed Methods**: `GET, POST, PUT, DELETE, OPTIONS`
- **Allowed Headers**: `*` (all headers)

---

## Rate Limits

This is a public endpoint with no authentication. Consider implementing rate limiting in production to prevent abuse.

---

## Notes

- The endpoint uses AI-powered text extraction and analysis
- Processing time may vary depending on document complexity (typically 2-10 seconds)
- For best results, ensure the uploaded document is clear and readable
- The API handles both scanned documents and digital PDF files

