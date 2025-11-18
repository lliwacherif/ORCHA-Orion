# ORCHA Chat v2 API

Concise reference for iframe/external partners who call the lightweight chat endpoint.

## Endpoint
- **Method:** `POST`
- **URL:** `/api/v1/orcha/chat-v2`

## Request Body
```json
{
  "text": "Your user prompt",
  "conversation_id": 123,      // optional, keep history
  "user_id": 42,               // optional, defaults to Settings.DEFAULT_WIDGET_USER_ID
  "tenant_id": "partner_xyz",  // optional, defaults to Settings.DEFAULT_WIDGET_TENANT_ID
  "use_rag": false             // optional, true forces retrieval
}
```

Minimum requirement is `text`. Provide `conversation_id` from the previous response to maintain the thread.

## Response Body
```json
{
  "success": true,
  "message": "",
  "data": {
    "text": "LLM answer",
    "conversation_id": 123,
    "contexts": []              // present only when RAG is used
  }
}
```
- `success=false` indicates backend failure; reason is in `message`.  
- `data.text` always carries the assistant output (even on error if partial text exists).  
- `conversation_id` is stable per user thread—cache it client-side.

## Notes
- Same orchestrator logic as `/orcha/chat`, but without attachments or advanced payloads.  
- Returns 200 OK for handled errors; check `success` before rendering.  
- Tenant defaults (`Settings.DEFAULT_WIDGET_*`) can be overridden per partner for analytics and rate control.

