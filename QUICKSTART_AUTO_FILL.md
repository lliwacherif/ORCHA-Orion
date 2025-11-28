# Quick Start - Auto-Fill API v2

Get started with the refactored auto-fill endpoint in 5 minutes.

---

## What Changed?

The `/api/v1/orcha/auto-fill` endpoint now:
- ✅ Accepts **any fields** you want to extract (not just 4 hardcoded fields)
- ✅ Returns **only the requested fields** (no 80+ field response)
- ✅ Works with **any document type** (no strict validation)

---

## 1. Test with Python (Fastest)

```bash
# Install requests if needed
pip install requests

# Test with a document
python test_auto_fill_v2.py path/to/your/document.pdf
```

---

## 2. Test with cURL

```bash
curl -X PUT http://localhost:8000/api/v1/orcha/auto-fill \
  -F 'file=@document.pdf' \
  -F 'fields=[{"field_name":"firstname","field_type":"string"},{"field_name":"lastname","field_type":"string"},{"field_name":"birth_date","field_type":"date"}]'
```

---

## 3. Basic Python Example

```python
import requests
import json

# Define fields to extract
fields = [
    {"field_name": "firstname", "field_type": "string"},
    {"field_name": "lastname", "field_type": "string"},
    {"field_name": "birth_date", "field_type": "date"}
]

# Send request
with open("document.pdf", "rb") as f:
    response = requests.put(
        "http://localhost:8000/api/v1/orcha/auto-fill",
        files={"file": f},
        data={"fields": json.dumps(fields)}
    )

result = response.json()
print(result)
```

---

## 4. Understanding the Response

### Success (Data Found)
```json
{
  "success": true,
  "message": "success",
  "data": {
    "firstname": "John",
    "lastname": "Doe",
    "birth_date": "1990-01-15"
  }
}
```

### Invalid/Unreadable Document
```json
{
  "success": true,
  "message": "invalid doc",
  "data": {
    "firstname": null,
    "lastname": null,
    "birth_date": null
  }
}
```

### API Error
```json
{
  "success": false,
  "message": "Error: Invalid fields parameter",
  "data": {}
}
```

---

## 5. Common Use Cases

### Extract Identity Info
```python
fields = [
    {"field_name": "firstname", "field_type": "string"},
    {"field_name": "lastname", "field_type": "string"},
    {"field_name": "birth_date", "field_type": "date"},
    {"field_name": "nationality", "field_type": "string"}
]
```

### Extract Invoice Info
```python
fields = [
    {"field_name": "invoice_number", "field_type": "string"},
    {"field_name": "invoice_date", "field_type": "date"},
    {"field_name": "total_amount", "field_type": "number"},
    {"field_name": "vendor_name", "field_type": "string"}
]
```

### Extract Address Info
```python
fields = [
    {"field_name": "street_address", "field_type": "string"},
    {"field_name": "city", "field_type": "string"},
    {"field_name": "postal_code", "field_type": "string"},
    {"field_name": "country", "field_type": "string"}
]
```

---

## 6. Migration from Old API

### Old Code (v1)
```python
# Only worked with 4 hardcoded fields
response = requests.put(url, files={"file": file})
```

### New Code (v2)
```python
# Specify any fields you want
fields = [
    {"field_name": "firstname", "field_type": "string"},
    {"field_name": "lastname", "field_type": "string"}
]
response = requests.put(url, files={"file": file}, data={"fields": json.dumps(fields)})
```

---

## 7. Troubleshooting

### "Invalid fields parameter"
- Check that `fields` is a valid JSON array
- Each field must have `field_name`

### "Unsupported file type"
- Only PDF and images (PNG, JPG, JPEG) are supported

### "invalid doc" message
- Document is empty, unreadable, or contains no text
- Try with a clearer scan/document

### Connection Error
- Check that the ORCHA server is running
- Verify the API URL is correct

---

## 8. Next Steps

📖 **Full Documentation**: `docs/AUTO_FILL_API_V2.md`  
💻 **Code Examples**: `docs/AUTO_FILL_CODE_EXAMPLES.md`  
📝 **Complete Summary**: `REFACTOR_SUMMARY.md`  
🧪 **Test Script**: `test_auto_fill_v2.py`

---

## Need Help?

Contact the ORCHA development team or check the documentation files above.

**Happy extracting! 🚀**

