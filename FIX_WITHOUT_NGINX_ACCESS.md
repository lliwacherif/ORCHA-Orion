# Options to Fix 405 Error Without Nginx Access

## The Problem
- Nginx is blocking POST requests to `/api/v1/orcha/doc-check`
- Returns 405 Not Allowed before request reaches FastAPI
- You cannot modify nginx configuration

## What I've Done

### ✅ Added OPTIONS Handler
I added this to `app/api/v1/endpoints.py`:

```python
@router.options("/orcha/doc-check")
async def orcha_doc_check_options():
    """Handle CORS preflight requests for doc-check endpoint."""
    return {"status": "ok"}
```

This **might** help if nginx is blocking due to missing CORS preflight support.

**To deploy this fix:**
```bash
git add app/api/v1/endpoints.py
git commit -m "Add OPTIONS handler for doc-check CORS preflight"
git push

# Then on VPS:
git pull
sudo systemctl restart orcha  # Or however you restart your service
```

## Other Options (If OPTIONS Handler Doesn't Work)

### Option 1: Contact VPS Administrator

**If someone else manages nginx, send them this:**

> Subject: Nginx Configuration Needed for Document Upload API
>
> Hi,
>
> Our FastAPI application at `aura-orcha.vaeerdia.com` has an endpoint for document verification that's being blocked by nginx with a 405 error.
>
> **Endpoint:** POST `/api/v1/orcha/doc-check`
> **Issue:** Nginx returns 405 Not Allowed before the request reaches our application
>
> **Required nginx config changes:**
>
> Please add these settings to `/etc/nginx/sites-available/orcha`:
>
> ```nginx
> server {
>     # ... existing config ...
>     
>     # Add these settings:
>     client_max_body_size 20M;
>     proxy_connect_timeout 120s;
>     proxy_send_timeout 120s;
>     proxy_read_timeout 120s;
>     
>     location / {
>         # ... existing proxy_pass settings ...
>         
>         # Add these:
>         proxy_buffering off;
>         proxy_request_buffering off;
>     }
> }
> ```
>
> Then reload: `sudo nginx -t && sudo systemctl reload nginx`
>
> This will allow POST requests with file uploads to reach our FastAPI application.

### Option 2: Use Different Port (Bypass Nginx)

Run FastAPI on a port NOT behind nginx:

**On your VPS:**

1. **Edit your systemd service or run command:**
```bash
# Change port from 8000 to 8080
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

2. **Open firewall:**
```bash
sudo ufw allow 8080/tcp
```

3. **Update external app to use:**
```
http://aura-orcha.vaeerdia.com:8080/api/v1/orcha/doc-check
```

**⚠️ Downsides:**
- No SSL/HTTPS (unless you configure it in FastAPI)
- No nginx rate limiting
- Port 8080 must be exposed in firewall
- Direct exposure to internet (less secure)

### Option 3: Use Ngrok/Cloudflare Tunnel (Temporary Testing)

If you just need to test quickly:

**On your VPS:**
```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz

# Run tunnel to your FastAPI
./ngrok http 8000
```

This gives you a public URL like `https://xxxx.ngrok.io` that bypasses nginx.

### Option 4: Ask Hosting Provider

If you're on managed hosting (DigitalOcean, AWS, etc.):

1. Open a support ticket
2. Say: "My nginx reverse proxy is blocking POST requests, can you help me update the config?"
3. Attach the `nginx_orcha.conf` file from this repo

## Recommended Approach

**Try this order:**

1. ✅ **Deploy the OPTIONS handler** (already done) - Push to VPS and test
2. If still fails → **Contact whoever manages nginx** (Option 1)
3. If no nginx access at all → **Use different port** (Option 2)
4. For quick testing only → **Use ngrok** (Option 3)

## Testing After Each Fix

```bash
# From your local machine or anywhere:
curl -v -X POST https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check \
  -F "file=@test.txt" \
  -F "label=passport"
```

**Success looks like:**
```
HTTP/1.1 200 OK
...
{"success": true/false, "message": "...", "data": {...}}
```

**Still failing looks like:**
```
HTTP/1.1 405 Not Allowed
<html><h1>405 Not Allowed</h1></html>
```

## Who to Contact

**Need nginx access? Contact:**
- Your DevOps team
- Your VPS provider support
- Whoever set up the server initially
- System administrator

**Tell them:** "I need to update nginx config to allow POST requests with file uploads to `/api/v1/orcha/doc-check`"

## Next Steps

1. **Push the OPTIONS handler fix:**
   ```bash
   git add -A
   git commit -m "Add OPTIONS handler for doc-check + nginx config docs"
   git push
   ```

2. **On your VPS:**
   ```bash
   cd /opt/orcha  # Or wherever your app is
   git pull
   sudo systemctl restart orcha
   ```

3. **Test the endpoint**

4. **If still 405** → Contact nginx administrator or use Option 2 (different port)
