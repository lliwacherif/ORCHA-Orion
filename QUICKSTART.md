# Quick Start Guide

## What Changed

I've configured ORCHA to work with your LM Studio server and optimized the API responses for React consumption.

### Changes Made:

1. **Updated LM Studio URL** (`app/config.py`)
   - Changed from `localhost:1234` to `192.168.1.37:1234`
   - Now points to your remote LM Studio server

2. **Enhanced Chat Client** (`app/services/chatbot_client.py`)
   - Improved OpenAI-compatible API integration
   - Added support for temperature and max_tokens parameters
   - Added `get_available_models()` function to list available models

3. **Optimized Chat Response** (`app/services/orchestrator.py`)
   - **Clean response format for React:**
     ```json
     {
       "status": "ok",
       "message": "Assistant's response here",
       "contexts": [...],  // Only if RAG is used
       "model_response": {...}  // Full response for debugging
     }
     ```
   - The `message` field contains the clean text to display in your UI
   - No need to dig through nested `choices[0].message.content`

4. **Added Models Endpoint** (`app/api/v1/endpoints.py`)
   - New endpoint: `GET /api/v1/models`
   - Returns available models from LM Studio
   - Useful for showing model selection in your UI

5. **Cleaned Up Duplicates**
   - Removed `app/api/tasks/worker.py` (duplicate)
   - Removed `app/utils/middleware.py` (duplicate)

## Testing the Setup

### Step 1: Test LM Studio Connection

Run the test script to verify everything works:

```bash
python test_lmstudio.py
```

This will test:
- ✅ Connection to LM Studio at `192.168.1.37:1234`
- ✅ Models endpoint (`GET /v1/models`)
- ✅ Chat endpoint (`POST /v1/chat/completions`)
- ✅ ORCHA API integration

### Step 2: Start ORCHA Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:
- Local: `http://localhost:8000`
- Network: `http://<your-ip>:8000`

### Step 3: Test the Chat Endpoint

Using curl:

```bash
curl -X POST http://localhost:8000/api/v1/orcha/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello! How are you today?",
    "use_rag": false
  }'
```

Expected response:

```json
{
  "status": "ok",
  "message": "Hello! I'm doing well, thank you for asking. How can I assist you today?",
  "contexts": null,
  "model_response": {
    "id": "chatcmpl-xxx",
    "choices": [...]
  }
}
```

### Step 4: Test with RAG (if RAG service is running)

```bash
curl -X POST http://localhost:8000/api/v1/orcha/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "What are the company policies?",
    "use_rag": true
  }'
```

## API Documentation

See the complete API documentation in the main README or use:

```bash
# Start server and visit:
http://localhost:8000/docs
```

FastAPI automatically generates interactive documentation (Swagger UI).

## React Integration

For building your React UI, refer to **REACT_INTEGRATION.md** which includes:

- ✅ Complete React component examples
- ✅ API response format documentation
- ✅ Error handling best practices
- ✅ TypeScript interfaces
- ✅ React Query examples

### Quick React Example:

```jsx
const sendChat = async (message) => {
  const response = await fetch('http://localhost:8000/api/v1/orcha/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: 'user123',
      message: message,
      use_rag: false
    })
  });
  
  const data = await response.json();
  
  if (data.status === 'ok') {
    // Display data.message in your chat UI
    console.log('AI Response:', data.message);
  }
};
```

## Available Endpoints

### Main Endpoints:
- `POST /api/v1/orcha/chat` - Chat with LLM (with optional RAG)
- `POST /api/v1/orcha/route` - Intelligent routing
- `GET /api/v1/models` - List available models ⭐ NEW
- `POST /api/v1/orcha/rag/query` - Search documents
- `POST /api/v1/orcha/ingest` - Add documents to RAG
- `POST /api/v1/orcha/ocr` - Process documents with OCR

### Interactive Docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### LM Studio Connection Failed

**Problem:** Cannot connect to `192.168.1.37:1234`

**Solutions:**
1. Verify LM Studio is running on that machine
2. Check that a model is loaded in LM Studio
3. Verify the IP address is correct
4. Check firewall settings
5. Test direct connection: `curl http://192.168.1.37:1234/v1/models`

### ORCHA Returns Error

**Problem:** `{"status": "error", "error": "..."}`

**Common causes:**
1. LM Studio not responding (check LM Studio logs)
2. Model is loading (wait and retry)
3. Timeout exceeded (increase `LM_TIMEOUT` in config)
4. Network issues

### Redis Connection Failed

**Problem:** Redis not available

**Solution:**
```bash
# Install Redis
# Windows: Use WSL or download Redis for Windows
# Mac: brew install redis
# Linux: sudo apt install redis-server

# Start Redis
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

**Note:** ORCHA will continue working without Redis, but OCR job queuing won't work.

## Configuration

You can customize settings via environment variables or `.env` file:

```env
# .env
LMSTUDIO_URL=http://192.168.1.37:1234
LM_TIMEOUT=60
REDIS_URL=redis://localhost:6379/0
OCR_SERVICE_URL=http://localhost:8001
RAG_SERVICE_URL=http://localhost:8002
RAG_TIMEOUT=5
OCR_TIMEOUT=30
```

Then restart the server.

## Next Steps

1. ✅ Test LM Studio connection (`python test_lmstudio.py`)
2. ✅ Start ORCHA server (`uvicorn app.main:app --reload`)
3. ✅ Test API endpoints (use curl or Postman)
4. ✅ Build React UI (refer to `REACT_INTEGRATION.md`)
5. ✅ (Optional) Set up OCR service
6. ✅ (Optional) Set up RAG service

## Support

If you encounter issues:
1. Check the test script output
2. Review server logs
3. Verify all services are running
4. Check the `/docs` endpoint for API details

---

**Your ORCHA API is now configured and ready for your React interface! 🚀**

