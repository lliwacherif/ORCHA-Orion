# Doc-Check Endpoint: POST to PUT Migration Summary

## What Was Changed

### 1. **HTTP Method Changed: POST → PUT**
   - **Endpoint**: `/api/v1/orcha/doc-check`
   - **Old Method**: POST
   - **New Method**: PUT
   - **Reason**: Nginx reverse proxy was blocking POST requests with 405 error

### 2. **Files Modified**

#### Code Changes:
- ✅ `app/api/v1/endpoints.py`
  - Changed `@router.post("/orcha/doc-check")` to `@router.put("/orcha/doc-check")`
  - Added `@router.options("/orcha/doc-check")` for CORS preflight support

#### Documentation Updates:
- ✅ `DOC_CHECK_API_GUIDE-V2.md`
  - Updated endpoint specification: POST → PUT
  - Updated all curl examples
  - Updated JavaScript/Node.js examples
  - Updated Python examples
  - Updated PHP examples
  - Added warning note about PUT method workaround

- ✅ `VPS_DEPLOYMENT.md`
  - Enhanced nginx configuration with proper POST/PUT handling
  - Added file upload size limits
  - Added timeouts for long-running requests

#### New Files:
- ✅ `nginx_orcha.conf` - Complete nginx configuration template
- ✅ `FIX_405_ERROR.md` - Detailed diagnosis and nginx fix guide
- ✅ `FIX_WITHOUT_NGINX_ACCESS.md` - Alternative solutions when nginx cannot be modified

## Git Information

- **Branch**: `feature/doc-check-endpoint`
- **Commit**: `80fe905` - "Fix 405 error: Change doc-check endpoint from POST to PUT method"
- **Remote**: GitLab - http://192.168.1.49/vaerdia-solution/artificial-intelligence/aura-ai/aura-backend.git

## External App Changes Required

The external application needs to update its API call from:

### Before (POST):
```javascript
fetch('https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check', {
  method: 'POST',
  body: formData
})
```

### After (PUT):
```javascript
fetch('https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check', {
  method: 'PUT',
  body: formData
})
```

### curl Before:
```bash
curl -X POST https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@document.pdf" \
  -F "label=passport"
```

### curl After:
```bash
curl -X PUT https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@document.pdf" \
  -F "label=passport"
```

## Deployment Steps

### On VPS:

1. **Pull the changes:**
   ```bash
   cd /opt/orcha  # Or your app directory
   git fetch origin
   git checkout feature/doc-check-endpoint
   git pull origin feature/doc-check-endpoint
   ```

2. **Restart the application:**
   ```bash
   sudo systemctl restart orcha
   # OR if using other method:
   # pkill -f uvicorn
   # uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

3. **Verify the change:**
   ```bash
   curl -X PUT https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
     -F "file=@test.txt" \
     -F "label=passport"
   ```

   Should return `200 OK` instead of `405 Not Allowed`

## Testing

### Test 1: Local Test
```bash
curl -X PUT http://localhost:8000/api/v1/orcha/doc-check \
  -F "file=@test.txt" \
  -F "label=passport"
```

### Test 2: Production Test
```bash
curl -X PUT https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@test.pdf" \
  -F "label=passport"
```

### Expected Response:
```json
{
  "success": true,
  "message": "document valide",
  "data": {
    "Res_validation": "VALID: ..."
  }
}
```

## Why PUT Instead of POST?

- **Root Cause**: Nginx reverse proxy was blocking POST requests with 405 error
- **Investigation**: FastAPI app was correctly configured, CORS was open, no auth required
- **Diagnosis**: Error came from nginx (response showed "nginx/1.08.0 (Ubuntu)")
- **Solution**: Changed to PUT method as a workaround since you cannot modify nginx config
- **Alternative**: If nginx can be modified in the future, you can change back to POST and update nginx config as documented in `FIX_405_ERROR.md`

## Important Notes

1. ⚠️ **External apps must update their requests to use PUT instead of POST**
2. ✅ All functionality remains the same - only the HTTP method changed
3. ✅ CORS is still properly configured (`allow_origins=["*"]`)
4. ✅ No authentication required (as designed)
5. ✅ OPTIONS endpoint added for CORS preflight support
6. 📝 If nginx is ever updated with proper config, we can revert to POST

## Next Steps

1. ✅ Deploy to VPS (pull from `feature/doc-check-endpoint` branch)
2. ✅ Restart the application
3. ✅ Test the endpoint with PUT method
4. ✅ Notify external app developers to change their API calls from POST to PUT
5. ✅ Verify external app can now successfully call the endpoint

## Rollback Plan

If issues occur:

```bash
git checkout main  # or previous stable branch
sudo systemctl restart orcha
```

Then investigate nginx configuration as documented in `FIX_405_ERROR.md`.

---

**Status**: ✅ Ready for deployment
**Date**: 2025-11-19
**Author**: AI Assistant
