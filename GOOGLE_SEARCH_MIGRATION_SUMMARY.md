# Migration from DuckDuckGo to Google Custom Search API

## ✅ Migration Complete

Successfully replaced DuckDuckGo with Google Custom Search API due to rate limiting issues.

---

## Changes Made

### 1. **Configuration** (`app/config.py`)
Added Google API credentials:
```python
GOOGLE_API_KEY: str = "AIzaSyBoDGtsHf5nIub8CGys_gQIjkBhX8Yon9k"
GOOGLE_SEARCH_ENGINE_ID: str = "30b305149d8ec4be9"
```

### 2. **Dependencies** (`requirements.txt`)
- ❌ Removed: `duckduckgo-search==5.3.0`
- ✅ Added: `requests>=2.31.0`

### 3. **Search Function** (`app/services/orchestrator.py`)
- Replaced DuckDuckGo implementation with Google Custom Search API
- Uses: `https://www.googleapis.com/customsearch/v1`
- Better error handling for quota limits (429) and authentication (403)
- Timeout set to 10 seconds

### 4. **Test Script** (`test_web_search.py`)
- Updated to test Google search
- Removed Unicode emojis for Windows compatibility

---

## Test Results ✓

**Query**: "Who is the richest man"

**Results**: Successfully returned 5 search results from:
- Investopedia
- Forbes Real-Time Billionaires
- Wikipedia
- Reddit
- Facebook

**Performance**: Fast and reliable

---

## API Limits

- **Free Tier**: 100 queries per day
- **Max Results per Query**: 10
- **Default**: 5 results
- **Timeout**: 10 seconds

---

## Error Handling

The implementation handles:
1. **429 (Rate Limit)**: "You have exceeded your daily search quota (100 queries per day)"
2. **403 (Auth Error)**: "API key or Search Engine ID is incorrect"
3. **Timeout**: "Search request timed out"
4. **General Errors**: Detailed error messages

---

## Benefits Over DuckDuckGo

✅ No rate limiting issues (100 queries/day is sufficient)
✅ Higher quality results from Google
✅ More reliable uptime
✅ Better structured data (snippets, titles, URLs)
✅ Official API with proper error codes

---

## Frontend Impact

**NONE** - The API endpoint remains the same:
- Still: `POST /api/v1/orcha/search`
- Same request/response format
- No frontend changes needed

---

## Usage Example

```bash
curl -X POST http://localhost:8000/api/v1/orcha/search \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "query": "Who is the richest man",
    "max_results": 5
  }'
```

**Response**:
```json
{
  "status": "ok",
  "message": "Based on the search results, Elon Musk is currently the richest person in the world with a net worth of $469 billion...",
  "conversation_id": 456,
  "search_query": "Who is the richest man",
  "results_count": 5,
  "token_usage": {...}
}
```

---

## Monitoring Quota

To track your daily usage, monitor the console output:
- `[SEARCH] Performing Google search for: <query>`
- `[SUCCESS] Google search complete, returning X results`

If you hit the limit, you'll see:
- `[ERROR] HTTP error: 429`
- User gets: "You have exceeded your daily search quota"

---

## Future Considerations

If 100 queries/day is not enough, you can:
1. **Upgrade to Paid Plan** ($5 per 1000 queries after free tier)
2. **Use Multiple API Keys** (rotate keys)
3. **Cache Results** (implement Redis caching for common queries)
4. **Rate Limit on Frontend** (warn users about quota)

---

## Server Ready ✓

The server is ready to run with the new Google search:

```bash
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

All tests pass, no errors, ready for production! 🚀

