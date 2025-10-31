# Token Tracking - Frontend Guide

## Overview

The backend automatically tracks token usage per user with a 24-hour rolling reset. Every chat response includes token usage information.

---

## Response Format

When you call `/api/v1/orcha/chat`, you'll get this response:

```json
{
  "status": "ok",
  "message": "Assistant's response...",
  "token_usage": {
    "current_usage": 1523,
    "tokens_added": 245,
    "reset_at": "2025-10-23T14:30:00",
    "tracking_enabled": true
  }
}
```

**Fields:**
- `current_usage` - Total tokens used in the last 24 hours
- `tokens_added` - Tokens consumed by this chat request
- `reset_at` - ISO timestamp when usage resets
- `tracking_enabled` - Whether tracking is active (requires Redis)

---

## API Endpoints

### 1. Chat (with token tracking)
**POST** `/api/v1/orcha/chat`

Returns token usage automatically in each response.

### 2. Get Current Usage
**GET** `/api/v1/tokens/usage/{user_id}`

```javascript
const response = await fetch('http://localhost:8000/api/v1/tokens/usage/user123');
const data = await response.json();
// { "status": "ok", "current_usage": 1523, "reset_at": "...", ... }
```

### 3. Reset Usage (Admin)
**POST** `/api/v1/tokens/reset/{user_id}`

```javascript
await fetch('http://localhost:8000/api/v1/tokens/reset/user123', { method: 'POST' });
```

---

## Implementation Example

```jsx
import React, { useState } from 'react';

function ChatInterface({ userId }) {
  const [messages, setMessages] = useState([]);
  const [tokenUsage, setTokenUsage] = useState(null);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    const response = await fetch('http://localhost:8000/api/v1/orcha/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        message: input,
        use_rag: false
      })
    });

    const data = await response.json();
    
    if (data.status === 'ok') {
      // Add message to chat
      setMessages([...messages, { role: 'assistant', content: data.message }]);
      
      // Update token usage
      if (data.token_usage) {
        setTokenUsage(data.token_usage);
      }
    }
    
    setInput('');
  };

  return (
    <div>
      {/* Display token usage */}
      {tokenUsage?.tracking_enabled && (
        <div className="token-display">
          🪙 {tokenUsage.current_usage.toLocaleString()} tokens used
          {tokenUsage.tokens_added > 0 && ` (+${tokenUsage.tokens_added})`}
        </div>
      )}

      {/* Chat messages */}
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i}>{msg.content}</div>
        ))}
      </div>

      {/* Input */}
      <input value={input} onChange={e => setInput(e.target.value)} />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}
```

---

## Important Notes

1. **Automatic Tracking**: Token usage is tracked automatically - no extra code needed
2. **24-Hour Window**: Resets 24 hours after first use (not at midnight)
3. **Always Check**: Verify `tracking_enabled` is `true` before displaying usage
4. **Graceful Fallback**: If Redis is down, `tracking_enabled` will be `false`

---

## Quick Test

```bash
# Send a chat
curl -X POST http://localhost:8000/api/v1/orcha/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Hello"}'

# Check usage
curl http://localhost:8000/api/v1/tokens/usage/test
```

