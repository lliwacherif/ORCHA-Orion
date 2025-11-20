# Doc-Check API Changelog

## Branch: `feature/doc-check-lang-support`

### Changes Made

#### 1. **Language Support**
- Added `lang` parameter to the endpoint (default: `"fr"`)
- Accepts `"en"` or `"fr"` values
- Model responds in **French by default**
- Model follows the language specified in the `lang` parameter

#### 2. **Improved Response Structure**
- **`success`**: Indicates if the API call executed successfully (true/false)
- **`valid`**: NEW field indicating if the document is valid (true/false)
- **`message`**: Shows document validity status (as before)
- **`data.Res_validation`**: Model's detailed explanation (unchanged)

### API Usage

**Endpoint**: `PUT /api/v1/orcha/doc-check`

**Form Data**:
```
file: <document file> (PDF or image)
label: <document type> (e.g., "passport", "cin", "driver_license")
lang: <language> (optional, "en" or "fr", default: "fr")
```

### Response Examples

#### Valid Document (French - default):
```json
{
    "success": true,
    "valid": true,
    "message": "document valide",
    "data": {
        "Res_validation": "Document VALIDE. Toutes les informations nécessaires sont présentes..."
    }
}
```

#### Valid Document (English):
```json
{
    "success": true,
    "valid": true,
    "message": "valid document",
    "data": {
        "Res_validation": "Document VALID. All necessary information is present..."
    }
}
```

#### Invalid Document (French):
```json
{
    "success": true,
    "valid": false,
    "message": "document non valide",
    "data": {
        "Res_validation": "Document INVALIDE. Champs manquants..."
    }
}
```

#### API Error (e.g., OCR service down):
```json
{
    "success": false,
    "valid": false,
    "message": "document non valide",
    "data": {
        "Res_validation": "Unable to extract text from image: OCR service error..."
    }
}
```

### Backward Compatibility

- Existing integrations that don't send `lang` parameter will get French responses by default
- The `message` field continues to show document validity as before
- The `data.Res_validation` format is unchanged

### Migration Notes

**For external applications**:
1. Check the `valid` field for document validity (recommended)
2. The `success` field now indicates API execution status
3. Add `lang=en` if you need English responses

### Testing

The changes are already deployed on the development server. Test with:

```bash
curl -X PUT "http://localhost:8000/api/v1/orcha/doc-check" \
  -F "file=@test_document.jpg" \
  -F "label=passport" \
  -F "lang=en"
```

---
**Date**: 2025-11-20  
**Author**: Automated via Antigravity  
**GitLab Branch**: feature/doc-check-lang-support
