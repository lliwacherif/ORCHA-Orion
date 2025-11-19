# Complete Guide: `/api/v1/orcha/chat-v2` Endpoint

## Overview

The `/api/v1/orcha/chat-v2` endpoint is a **lightweight, simplified chat interface** designed specifically for **external integrations** such as iframe widgets, partner applications, and embedded chat interfaces. It provides a streamlined API that focuses on text-only conversations without the complexity of attachments or advanced payloads.

---

## Purpose

- **Simplified Integration**: Easier for external partners to integrate ORCHA chat
- **Iframe Widget Support**: Designed for embedding in third-party applications
- **Text-Only Focus**: Streamlined for simple Q&A without document handling
- **Normalized Response**: Consistent response format regardless of success/failure

---

## Endpoint Details

- **Method**: `POST`
- **URL**: `/api/v1/orcha/chat-v2`
- **Authentication**: Optional (uses default widget user if not provided)
- **Content-Type**: `application/json`

---

## Request Model

### ChatV2Request Schema

```python
{
    "text": str,                    # Required: User message (min 1 character)
    "user_id": int,                 # Optional: Override default widget user
    "tenant_id": str,               # Optional: Override default tenant
    "conversation_id": int,          # Optional: Resume existing conversation
    "use_rag": bool                 # Optional: Force RAG retrieval (default: false)
}
```

### Request Body Example

```json
{
  "text": "What is the coverage for dental procedures?",
  "conversation_id": 123,
  "user_id": 42,
  "tenant_id": "opencare_partner",
  "use_rag": false
}
```

### Minimal Request

```json
{
  "text": "Hello, I need help with my insurance claim"
}
```

---

## Response Model

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "",
  "data": {
    "text": "I can help you with your insurance claim. Could you provide more details about...",
    "conversation_id": 123,
    "contexts": []  // Only present when RAG is used
  }
}
```

### Error Response (200 OK with success=false)

```json
{
  "success": false,
  "message": "Error: Could not connect to LM Studio",
  "data": {
    "text": "",  // May contain partial response if available
    "conversation_id": null
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | `true` if request processed successfully, `false` otherwise |
| `message` | string | Empty on success, error message on failure |
| `data.text` | string | LLM-generated response text (always present, may be empty on error) |
| `data.conversation_id` | integer | Conversation ID for maintaining thread context |
| `data.contexts` | array | RAG contexts (only present when `use_rag=true`) |

---

## Default Configuration

The endpoint uses default values from `app/config.py`:

```python
DEFAULT_WIDGET_USER_ID: int = 1
DEFAULT_WIDGET_TENANT_ID: str = "external_widget"
```

**Important**: Ensure `DEFAULT_WIDGET_USER_ID` maps to a valid user in the `users` table.

---

## How It Works

### Internal Flow

1. **Request Received**: Endpoint receives `ChatV2Request`
2. **User Resolution**: 
   - Uses `req.user_id` if provided
   - Falls back to `settings.DEFAULT_WIDGET_USER_ID`
3. **Tenant Resolution**:
   - Uses `req.tenant_id` if provided
   - Falls back to `settings.DEFAULT_WIDGET_TENANT_ID`
4. **Payload Transformation**: Converts to standard chat payload:
   ```python
   {
       "user_id": str(resolved_user_id),
       "tenant_id": resolved_tenant_id,
       "message": req.text,
       "attachments": [],  # Always empty for v2
       "use_rag": req.use_rag,
       "conversation_history": [],  # Always empty
       "conversation_id": req.conversation_id
   }
   ```
5. **Orchestrator Call**: Passes to `handle_chat_request()` (same as `/orcha/chat`)
6. **Response Normalization**: Converts orchestrator response to v2 format:
   - Maps `status: "ok"` → `success: true`
   - Maps `status: "error"` → `success: false`
   - Extracts `message` → `data.text`
   - Preserves `conversation_id`
   - Includes `contexts` if RAG was used

---

## Key Differences from `/orcha/chat`

| Feature | `/orcha/chat` | `/orcha/chat-v2` |
|----------|---------------|------------------|
| **Attachments** | ✅ Supported | ❌ Not supported |
| **Request Format** | Complex (attachments, history) | Simple (text only) |
| **Response Format** | Variable structure | Normalized `{success, message, data}` |
| **Error Handling** | HTTP error codes | Always 200 OK, check `success` |
| **Use Case** | Full-featured chat | External widgets/partners |
| **Conversation History** | Can send full history | Auto-loaded from DB |

---

## Implementation Details

### Code Location

**File**: `app/api/v1/endpoints.py`  
**Function**: `orcha_chat_v2()` (lines 229-280)

### Key Functions Used

- `handle_chat_request()`: Core orchestrator (same as `/orcha/chat`)
- `settings.DEFAULT_WIDGET_USER_ID`: Default user fallback
- `settings.DEFAULT_WIDGET_TENANT_ID`: Default tenant fallback

---

## Usage Examples

### JavaScript/TypeScript

```javascript
async function sendChatMessage(text, conversationId = null) {
  const response = await fetch('/api/v1/orcha/chat-v2', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: text,
      conversation_id: conversationId,
      use_rag: false
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const result = await response.json();
  
  if (!result.success) {
    throw new Error(result.message || 'Chat request failed');
  }

  return result.data; // { text, conversation_id, contexts? }
}

// Usage
const data = await sendChatMessage("What is my coverage?", 123);
console.log(data.text); // LLM response
console.log(data.conversation_id); // Use for next message
```

### Python

```python
import httpx

async def send_chat_v2(text: str, conversation_id: int = None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://aura-orcha.vaeerdia.com/api/v1/orcha/chat-v2",
            json={
                "text": text,
                "conversation_id": conversation_id,
                "use_rag": False
            }
        )
        response.raise_for_status()
        result = response.json()
        
        if not result["success"]:
            raise Exception(result["message"])
        
        return result["data"]
```

### cURL

```bash
curl -X POST https://aura-orcha.vaeerdia.com/api/v1/orcha/chat-v2 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is the claim process?",
    "conversation_id": 123
  }'
```

---

## Conversation Management

### Starting a New Conversation

```json
{
  "text": "Hello, I need help"
}
// Response includes new conversation_id
```

### Continuing a Conversation

```json
{
  "text": "Tell me more about that",
  "conversation_id": 123  // From previous response
}
```

**Important**: Always cache `conversation_id` from responses to maintain context across messages.

---

## RAG Integration

### Enable RAG Retrieval

```json
{
  "text": "What documents do I need for a claim?",
  "use_rag": true
}
```

**Response includes contexts**:
```json
{
  "success": true,
  "data": {
    "text": "...",
    "conversation_id": 123,
    "contexts": [
      {
        "source": "claim_guide.pdf",
        "text": "Required documents include..."
      }
    ]
  }
}
```

---

## Error Handling

### Common Errors

1. **LM Studio Connection Failure**
   ```json
   {
     "success": false,
     "message": "Error: Could not connect to LM Studio",
     "data": { "text": "", "conversation_id": null }
   }
   ```

2. **Database Error**
   ```json
   {
     "success": false,
     "message": "Database session not available",
     "data": { "text": "", "conversation_id": null }
   }
   ```

3. **Invalid User**
   ```json
   {
     "success": false,
     "message": "User not found",
     "data": { "text": "", "conversation_id": null }
   }
   ```

### Best Practices

- **Always check `success` field** before rendering response
- **Display `message` field** to users on error
- **Retry logic**: Implement exponential backoff for transient errors
- **Timeout handling**: Set appropriate client-side timeouts (recommended: 180 seconds)

---

## Integration Checklist

- [ ] Verify `DEFAULT_WIDGET_USER_ID` exists in database
- [ ] Set appropriate `tenant_id` for analytics/rate limiting
- [ ] Implement conversation ID caching (sessionStorage/localStorage)
- [ ] Handle loading states during requests
- [ ] Display error messages from `message` field
- [ ] Configure request timeouts (180+ seconds recommended)
- [ ] Test conversation continuity with `conversation_id`
- [ ] Monitor token usage via `/api/v1/orcha/tokens/usage/{user_id}`

---

## Security Considerations

1. **Authentication**: Currently optional, but recommended for production
2. **Rate Limiting**: Implement per-tenant rate limits
3. **Input Validation**: Text is validated (min 1 character)
4. **Token Tracking**: All requests tracked for billing/analytics
5. **Tenant Isolation**: Use `tenant_id` to segment usage

---

## Monitoring & Analytics

### Track Usage by Tenant

```sql
SELECT tenant_id, COUNT(*) as message_count
FROM chat_messages
WHERE tenant_id = 'opencare_partner'
GROUP BY tenant_id;
```

### Monitor Token Consumption

```bash
GET /api/v1/orcha/tokens/usage/{user_id}
```

---

## Limitations

1. **No Attachments**: Cannot send files (use `/orcha/chat` for that)
2. **No Custom History**: Conversation history auto-loaded from DB
3. **Simplified Payload**: Less control than full `/orcha/chat` endpoint
4. **Default User**: Uses widget user if `user_id` not provided

---

## Migration from `/orcha/chat`

If migrating from `/orcha/chat` to `/orcha/chat-v2`:

1. **Remove attachments** from requests
2. **Update response handling** to check `success` field
3. **Cache conversation_id** from responses
4. **Remove conversation_history** from requests (auto-loaded)
5. **Update error handling** (always 200 OK, check `success`)

---

## Support & Documentation

- **API Documentation**: `/docs` (Swagger UI)
- **Related Guides**:
  - `API_CHAT_V2.md` - Quick reference
  - `FRONTEND_CHAT_WIDGET_GUIDE.md` - Frontend integration
- **Technical Support**: support@vaeerdia.com

---

## Summary

The `/api/v1/orcha/chat-v2` endpoint provides a **simplified, normalized interface** for external integrations. It uses the same powerful orchestrator as `/orcha/chat` but with a streamlined request/response format optimized for iframe widgets and partner applications. Always check the `success` field and cache `conversation_id` for best results.

