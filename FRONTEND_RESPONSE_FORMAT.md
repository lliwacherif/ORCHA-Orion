# Frontend Response Format Guide

## ✅ GUARANTEED Response Format

ORCHA **always** returns this format for `/api/v1/orcha/chat`:

```typescript
interface ChatResponse {
  status: "ok" | "error";
  message: string;                    // ALWAYS a string, never null
  contexts?: Array<{                  // ALWAYS an array (empty [] if none)
    source?: string;
    text?: string;
    score?: number;
  }>;
  error?: string;                     // Only present when status === "error"
  attachments_processed?: number;     // Only if attachments were sent
  ingested_documents?: number;        // Only if attachments were sent
  model_response?: any;               // Full LM response (for debugging)
}
```

---

## 📋 Response Examples

### ✅ Success Response (Normal Chat)

```json
{
  "status": "ok",
  "message": "The Burj Khalifa is the tallest building in the world.",
  "contexts": [],
  "model_response": { ... }
}
```

**Frontend handling:**
```javascript
if (data.status === "ok") {
  displayMessage(data.message);  // ✅ Always exists
}
```

---

### ✅ Success Response (With RAG Context)

```json
{
  "status": "ok",
  "message": "According to the policy, coverage includes...",
  "contexts": [
    {
      "source": "policy-doc-123",
      "text": "Coverage details from document...",
      "score": 0.95
    }
  ],
  "model_response": { ... }
}
```

**Frontend handling:**
```javascript
if (data.status === "ok") {
  displayMessage(data.message);
  
  if (data.contexts && data.contexts.length > 0) {
    displaySources(data.contexts);
  }
}
```

---

### ✅ Success Response (With Attachments)

```json
{
  "status": "ok",
  "message": "I've analyzed your document. The policy states...",
  "contexts": [
    {
      "source": "attachment_user123",
      "text": "Content extracted from PDF..."
    }
  ],
  "attachments_processed": 1,
  "ingested_documents": 1,
  "model_response": { ... }
}
```

**Frontend handling:**
```javascript
if (data.status === "ok") {
  displayMessage(data.message);
  
  if (data.attachments_processed) {
    console.log(`Processed ${data.attachments_processed} file(s)`);
  }
}
```

---

### ❌ Error Response

```json
{
  "status": "error",
  "error": "Connection refused to LM Studio",
  "message": "Sorry, I encountered an error processing your request. Please try again."
}
```

**Frontend handling:**
```javascript
if (data.status === "error") {
  displayErrorMessage(data.message);  // User-friendly message
  console.error(data.error);          // Technical error for debugging
}
```

---

## 🔧 Recommended Frontend Code

### Complete Error Handling

```javascript
const sendMessage = async (userMessage, conversationHistory = []) => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/orcha/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'user123',
        message: userMessage,
        conversation_history: conversationHistory
      })
    });

    // Check HTTP status
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Check response format
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid response format');
    }

    if (!data.status) {
      throw new Error('Response missing status field');
    }

    if (!data.message || typeof data.message !== 'string') {
      throw new Error('Response missing or invalid message field');
    }

    // Handle based on status
    if (data.status === 'ok') {
      // ✅ Success - display the message
      addMessageToChat({
        role: 'assistant',
        content: data.message,
        contexts: data.contexts || []
      });
      
      return data;
    } else if (data.status === 'error') {
      // ❌ Error - show user-friendly message
      addMessageToChat({
        role: 'assistant',
        content: data.message,  // User-friendly error message
        error: true
      });
      
      console.error('Backend error:', data.error);
      return data;
    } else {
      throw new Error(`Unknown status: ${data.status}`);
    }

  } catch (error) {
    console.error('Request failed:', error);
    
    // Display fallback error message
    addMessageToChat({
      role: 'assistant',
      content: 'Unable to connect to the server. Please check your connection.',
      error: true
    });
    
    throw error;
  }
};
```

---

### TypeScript Version

```typescript
interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Context {
  source?: string;
  text?: string;
  score?: number;
}

interface ChatResponse {
  status: 'ok' | 'error';
  message: string;
  contexts?: Context[];
  error?: string;
  attachments_processed?: number;
  ingested_documents?: number;
  model_response?: any;
}

const sendMessage = async (
  userMessage: string,
  conversationHistory: Message[] = []
): Promise<ChatResponse> => {
  const response = await fetch('http://localhost:8000/api/v1/orcha/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: 'user123',
      message: userMessage,
      conversation_history: conversationHistory
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data: ChatResponse = await response.json();

  // Validate response
  if (!data.message) {
    throw new Error('Invalid response: missing message field');
  }

  return data;
};
```

---

## 🐛 Debugging Checklist

If you see "Received response but message format is unexpected":

### 1. Check the Console
```javascript
console.log('Full response:', data);
console.log('Status:', data.status);
console.log('Message:', data.message);
console.log('Message type:', typeof data.message);
```

### 2. Verify Fields
- ✅ `data.status` exists and is "ok" or "error"
- ✅ `data.message` exists and is a string
- ✅ `data.message` is NOT null
- ✅ `data.message` is NOT undefined
- ✅ `data.message` is NOT empty string (backend handles this now)

### 3. Check HTTP Status
```javascript
console.log('HTTP Status:', response.status);
console.log('Response OK:', response.ok);
```

### 4. Check Network Tab
- Look at the actual response in browser DevTools
- Verify Content-Type is `application/json`
- Check for CORS errors

---

## ⚠️ Common Issues & Fixes

### Issue 1: "Cannot read property 'message' of undefined"
**Cause:** Response is not being parsed as JSON
**Fix:**
```javascript
const data = await response.json();
if (!data) {
  throw new Error('Empty response');
}
```

### Issue 2: "message is null"
**Cause:** Old backend version (FIXED in latest version)
**Fix:** Update backend (already done!)

### Issue 3: "contexts is undefined"
**Cause:** Trying to map over undefined array
**Fix:**
```javascript
const contexts = data.contexts || [];
contexts.map(ctx => ...)
```

### Issue 4: CORS Error
**Cause:** Backend not allowing frontend origin
**Fix:** Check if backend is running and accessible

---

## 📊 Response Field Guarantees

| Field | Always Present | Type | Default |
|-------|---------------|------|---------|
| `status` | ✅ Yes | string | - |
| `message` | ✅ Yes | string | Never null/empty |
| `contexts` | ✅ Yes | array | `[]` if none |
| `error` | ❌ No | string | Only on errors |
| `attachments_processed` | ❌ No | number | Only with files |
| `ingested_documents` | ❌ No | number | Only with files |
| `model_response` | ✅ Yes | object | Full LM response |

---

## 🎯 Best Practices

### 1. Always Check Status First
```javascript
if (data.status === 'ok') {
  // Handle success
} else {
  // Handle error
}
```

### 2. Provide Fallback
```javascript
const message = data.message || 'No response received';
```

### 3. Handle Empty Contexts
```javascript
const contexts = Array.isArray(data.contexts) ? data.contexts : [];
```

### 4. Display User-Friendly Errors
```javascript
// ❌ Don't show technical error to user
displayMessage(data.error);

// ✅ Show friendly message
displayMessage(data.message);
console.error(data.error); // Log technical details
```

### 5. Log for Debugging
```javascript
if (data.status === 'error') {
  console.group('Chat Error');
  console.log('User message:', userMessage);
  console.log('Error:', data.error);
  console.log('Full response:', data);
  console.groupEnd();
}
```

---

## 🧪 Test Cases

### Test 1: Normal Chat
```javascript
// Send simple message
const response = await sendMessage('Hello');
console.assert(response.status === 'ok');
console.assert(typeof response.message === 'string');
console.assert(response.message.length > 0);
```

### Test 2: With History
```javascript
const history = [
  { role: 'user', content: 'First question' },
  { role: 'assistant', content: 'First answer' }
];
const response = await sendMessage('Follow-up', history);
console.assert(response.status === 'ok');
```

### Test 3: Error Handling
```javascript
// Simulate error by using wrong URL
try {
  await fetch('http://wrong-url/api/v1/orcha/chat', { ... });
} catch (error) {
  console.assert(error instanceof Error);
}
```

---

## 📱 React Component Example

```jsx
import { useState } from 'react';

const ChatComponent = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      // Get last 2 messages for context
      const history = messages.slice(-2);

      const response = await fetch('http://localhost:8000/api/v1/orcha/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'user123',
          message: input,
          conversation_history: history
        })
      });

      const data = await response.json();

      // Validate response
      if (!data || !data.message) {
        throw new Error('Invalid response format');
      }

      // Add assistant message
      const assistantMsg = {
        role: 'assistant',
        content: data.message,
        contexts: data.contexts || [],
        error: data.status === 'error'
      };

      setMessages(prev => [...prev, assistantMsg]);

    } catch (error) {
      console.error('Error:', error);
      
      // Add error message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Failed to get response. Please try again.',
        error: true
      }]);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>
            <p>{msg.content}</p>
            {msg.contexts?.length > 0 && (
              <div className="sources">
                Sources: {msg.contexts.map(c => c.source).join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        disabled={loading}
      />
      <button onClick={sendMessage} disabled={loading}>
        {loading ? 'Sending...' : 'Send'}
      </button>
    </div>
  );
};

export default ChatComponent;
```

---

## ✅ Summary

**The response ALWAYS has:**
1. ✅ `status`: "ok" or "error"
2. ✅ `message`: String (never null, never empty)
3. ✅ `contexts`: Array (empty [] if none)

**Your frontend should:**
1. ✅ Check `data.status === 'ok'`
2. ✅ Display `data.message` (always exists)
3. ✅ Handle `data.contexts || []` safely
4. ✅ Show user-friendly errors

**No more unexpected formats!** 🎉

