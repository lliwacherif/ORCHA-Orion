# Chat Widget Integration (chat-v2)

Use this guide to embed the lightweight ORCHA chat widget inside an external application via iframe + REST API.

## 1. Backend Contract

- **Endpoint:** `POST /api/v1/orcha/chat-v2`
- **Purpose:** Minimal chat surface for iframe clients.
- **Request Body:**
  ```json
  {
    "text": "User message",
    "conversation_id": 123,      // optional, reuse to keep history
    "user_id": 42,               // optional, defaults to settings.DEFAULT_WIDGET_USER_ID
    "tenant_id": "partner_xyz",  // optional, defaults to settings.DEFAULT_WIDGET_TENANT_ID
    "use_rag": false             // optional
  }
  ```
- **Response Body:**
  ```json
  {
    "success": true,
    "message": "",
    "data": {
      "text": "LLM response here",
      "conversation_id": 123,
      "contexts": []             // present only when RAG is triggered
    }
  }
  ```
- `success=false` keeps the same structure but returns the failure reason in `message`.

> ⚠️ Ensure `settings.DEFAULT_WIDGET_USER_ID` maps to a valid `users` row. Provide a tenant string if you need to segment analytics per partner.

## 2. Frontend Flow Inside the Iframe

1. **Bootstrap:** Load the widget script from AURA UI; expose a method such as `window.AuraChatWidget.init({ apiBaseUrl, authToken? })`.
2. **Send Message:** On user submit, POST `text` (and cached `conversation_id`) to `/api/v1/orcha/chat-v2`.
3. **Persist Conversation:** Cache the returned `conversation_id` in memory or `sessionStorage` so subsequent turns stay threaded.
4. **Render Response:** Display `data.text`. Show loading state until `success` arrives; if `success=false`, surface `message` and allow retry.
5. **Edge States:** Disable the send button while awaiting a response; optionally show typing dots using the same request promise.

## 3. Example Fetch Helper

```javascript
async function sendOrchaMessage({ text, conversationId }) {
  const response = await fetch("/api/v1/orcha/chat-v2", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, conversation_id: conversationId })
  });
  if (!response.ok) throw new Error("Network error");
  const payload = await response.json();
  if (!payload.success) throw new Error(payload.message || "Chat failed");
  return payload.data; // { text, conversation_id, contexts? }
}
```

## 4. Deployment Notes

- Expose the iframe script from AURA UI and document the single configuration parameter: the backend base URL where `/api/v1/orcha/chat-v2` lives.
- If the external app requires auth, wrap the fetch call with whatever token the app expects (e.g., signed JWT in headers).
- Monitor usage by filtering conversations with `tenant_id = settings.DEFAULT_WIDGET_TENANT_ID` or partner-specific IDs.

