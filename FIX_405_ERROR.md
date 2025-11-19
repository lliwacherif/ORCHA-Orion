# 405 Error Fix for `/api/v1/orcha/doc-check` Endpoint

## Problem Diagnosis

The **405 Not Allowed** error is **NOT** caused by:
- ❌ Missing authentication (the endpoint is correctly configured without auth)
- ❌ Wrong HTTP method (the endpoint is correctly defined as `@router.post`)
- ❌ FastAPI configuration issues

The error **IS** caused by:
- ✅ **Nginx reverse proxy configuration**

The error message shows `nginx/1.18.0 (Ubuntu)`, confirming that nginx is returning the 405 error **before the request even reaches your FastAPI application**.

---

## Root Cause

Your current nginx configuration likely has one or more of these issues:

1. **Missing HTTP method allowlist** - Nginx may not be configured to allow POST requests
2. **Request body size limit** - Default nginx `client_max_body_size` is 1MB, which is too small for document uploads
3. **Missing proxy headers** - Required headers may not be forwarded to FastAPI
4. **Timeout configuration** - OCR processing can take 10-60 seconds, default timeouts may be too short

---

## Solution

### Step 1: Update Nginx Configuration

SSH into your VPS and edit the nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/orcha
```

Replace the content with the configuration from `nginx_orcha.conf` file (see the file in your project root).

**Key changes needed:**

1. **Allow POST method explicitly:**
```nginx
if ($request_method !~ ^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)$ ) {
    return 405;
}
```

2. **Increase upload size limit:**
```nginx
client_max_body_size 20M;  # Allow up to 20MB documents
```

3. **Increase timeouts for long-running OCR:**
```nginx
proxy_connect_timeout 120s;
proxy_send_timeout 120s;
proxy_read_timeout 120s;
```

4. **Disable request buffering for file uploads:**
```nginx
proxy_buffering off;
proxy_request_buffering off;
```

### Step 2: Test Configuration

```bash
# Test nginx syntax
sudo nginx -t
```

You should see:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Step 3: Reload Nginx

```bash
# Reload nginx to apply changes (no downtime)
sudo systemctl reload nginx

# OR restart nginx (brief downtime)
sudo systemctl restart nginx
```

### Step 4: Verify the Fix

Test the endpoint from your local machine:

```bash
python test_post_doc_check.py
```

Or use curl:

```bash
curl -X POST https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@test_document.pdf" \
  -F "label=passport"
```

You should now get a **200 OK** response instead of **405 Not Allowed**.

---

## Verification Checklist

After applying the fix, verify:

- [ ] Nginx config test passes: `sudo nginx -t`
- [ ] Nginx reloaded successfully: `sudo systemctl reload nginx`
- [ ] POST requests are accepted (no 405 error)
- [ ] Files up to 20MB can be uploaded
- [ ] OCR processing completes without timeout (may take 10-60 seconds)
- [ ] Response contains `{"success": true/false, "message": "...", "data": {...}}`

---

## Common Issues After Configuration Change

### Issue: Still getting 405 error

**Solution:**
```bash
# Check if nginx actually reloaded
sudo systemctl status nginx

# Force restart if reload didn't work
sudo systemctl restart nginx

# Check nginx error logs
sudo tail -f /var/log/nginx/orcha_error.log
```

### Issue: 413 Entity Too Large

**Solution:** Increase `client_max_body_size` in nginx config:
```nginx
client_max_body_size 50M;  # Adjust as needed
```

### Issue: 504 Gateway Timeout

**Solution:** Increase proxy timeouts:
```nginx
proxy_connect_timeout 180s;
proxy_send_timeout 180s;
proxy_read_timeout 180s;
```

---

## How to Apply These Changes on Your VPS

### Option 1: Manual Update (Recommended for Production)

1. **SSH into your VPS:**
```bash
ssh your-user@aura-orcha.vaeerdia.com
```

2. **Backup current config:**
```bash
sudo cp /etc/nginx/sites-available/orcha /etc/nginx/sites-available/orcha.backup
```

3. **Edit the config:**
```bash
sudo nano /etc/nginx/sites-available/orcha
```

4. **Paste the new configuration** (from `nginx_orcha.conf`)

5. **Test and reload:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Option 2: Quick Deploy Script

Create this script on your VPS:

```bash
#!/bin/bash
# deploy_nginx_fix.sh

# Backup current config
sudo cp /etc/nginx/sites-available/orcha /etc/nginx/sites-available/orcha.backup.$(date +%Y%m%d_%H%M%S)

# Download new config (if you have it in a repo or transfer it)
# sudo curl -o /etc/nginx/sites-available/orcha https://your-repo/nginx_orcha.conf
# OR manually copy the content

# Test configuration
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx config is valid, reloading..."
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx config test failed! Rolling back..."
    sudo cp /etc/nginx/sites-available/orcha.backup /etc/nginx/sites-available/orcha
    exit 1
fi
```

---

## Testing the Endpoint

### Test 1: Simple Text File (Quick Test)

```bash
echo "Test passport document" > test.txt
curl -X POST https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@test.txt" \
  -F "label=passport"
```

### Test 2: Real PDF Document

```bash
curl -X POST https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@passport.pdf" \
  -F "label=passport"
```

### Test 3: Image Document

```bash
curl -X POST https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@id_card.jpg" \
  -F "label=cin"
```

---

## Why Was There No Authentication?

You were **correct** - this endpoint does **NOT** require authentication. Looking at the code:

```python
@router.post("/orcha/doc-check")
async def orcha_doc_check(
    file: UploadFile = File(...),
    label: str = Form(...),
    request: Request = None
):
    # No Depends(get_current_user) here!
    # This endpoint is public by design
```

Compare this to authenticated endpoints which have `Depends(get_current_user)`:

```python
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    # This requires authentication
```

The `/api/v1/orcha/doc-check` endpoint is **intentionally public** for partner integrations, as documented in `DOC_CHECK_API_GUIDE-V2.md`.

---

## Next Steps

1. **Apply the nginx configuration fix** on your VPS
2. **Test the endpoint** with the provided test scripts
3. **Update your external app** to retry the request (it should now work)
4. **Monitor nginx logs** to ensure everything is working:
   ```bash
   sudo tail -f /var/log/nginx/orcha_access.log
   sudo tail -f /var/log/nginx/orcha_error.log
   ```

---

## Summary

| Issue | Cause | Solution |
|-------|-------|----------|
| 405 Not Allowed | Nginx blocking POST requests | Update nginx config to allow POST method |
| — | Small upload size limit | Set `client_max_body_size 20M` |
| — | Request body buffering | Set `proxy_request_buffering off` |
| — | Short timeouts | Increase proxy timeouts to 120s+ |

**The FastAPI application is correctly configured. The issue is purely in the nginx reverse proxy layer.**
