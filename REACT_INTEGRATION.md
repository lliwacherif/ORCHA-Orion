# React Integration Guide for ORCHA API

## Quick Start

### 1. Configuration
```javascript
// config.js
export const API_BASE_URL = 'http://localhost:8000/api/v1';
```

### 2. Chat Component Example

```jsx
import { useState } from 'react';
import axios from 'axios';

const ChatComponent = () => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [useRag, setUseRag] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;

    // Add user message to chat
    const userMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/v1/orcha/chat', {
        user_id: 'user123', // Replace with actual user ID
        tenant_id: 'tenant1', // Optional
        message: message,
        attachments: [],
        use_rag: useRag
      });

      if (response.data.status === 'ok') {
        // Add assistant message to chat
        const assistantMessage = {
          role: 'assistant',
          content: response.data.message,
          contexts: response.data.contexts // For showing sources
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Handle error
        console.error('Error:', response.data.error);
        const errorMessage = {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          error: true
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Request failed:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Failed to connect to the server.',
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setMessage('');
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
            {msg.contexts && (
              <div className="sources">
                <strong>Sources:</strong>
                {msg.contexts.map((ctx, i) => (
                  <span key={i} className="source-tag">
                    {ctx.source || ctx.doc_id}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="loading">Thinking...</div>}
      </div>

      <div className="input-area">
        <label>
          <input
            type="checkbox"
            checked={useRag}
            onChange={(e) => setUseRag(e.target.checked)}
          />
          Use RAG (search documents)
        </label>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !message.trim()}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatComponent;
```

## API Response Formats

### Chat Response (Success)
```json
{
  "status": "ok",
  "message": "This is the assistant's response text that you display directly in your UI",
  "contexts": [
    {
      "source": "document-123",
      "text": "Retrieved context chunk...",
      "score": 0.95
    }
  ],
  "model_response": {
    "id": "chatcmpl-xxx",
    "object": "chat.completion",
    "created": 1234567890,
    "choices": [...]
  }
}
```

**What to display in React:**
- `message`: The main text to show as the assistant's response
- `contexts`: Optional - show as "sources" or footnotes (only present if `use_rag=true`)
- `model_response`: Keep for debugging, don't show to user

### Chat Response (Error)
```json
{
  "status": "error",
  "error": "Connection refused to LM Studio",
  "message": null
}
```

### Chat Response (OCR Queued)
```json
{
  "status": "ocr_queued",
  "jobs": ["job-id-1", "job-id-2"]
}
```

**Handle in React:** Show message like "Processing attachments... Job IDs: job-id-1, job-id-2"

## Advanced Features

### 1. File Upload with OCR

```jsx
const [file, setFile] = useState(null);

const handleFileUpload = async (file) => {
  // First, upload file to your storage and get URI
  const fileUri = await uploadFileToStorage(file);

  // Then send to ORCHA with attachment
  const response = await axios.post('http://localhost:8000/api/v1/orcha/chat', {
    user_id: 'user123',
    message: 'Please analyze this document',
    attachments: [{ uri: fileUri, type: file.type }],
    use_rag: false
  });

  if (response.data.status === 'ocr_queued') {
    // Show loading state
    console.log('OCR jobs queued:', response.data.jobs);
    // TODO: Implement polling for job status
  }
};
```

### 2. RAG Query (Search Documents)

```jsx
const searchDocuments = async (query) => {
  const response = await axios.post('http://localhost:8000/api/v1/orcha/rag/query', {
    user_id: 'user123',
    query: query,
    k: 8,
    rerank: true
  });

  if (response.data.status === 'ok') {
    return response.data.result.contexts;
  }
  return [];
};
```

### 3. Intelligent Routing

```jsx
const getRouteDecision = async (message, attachments = []) => {
  const response = await axios.post('http://localhost:8000/api/v1/orcha/route', {
    user_id: 'user123',
    message: message,
    attachments: attachments,
    use_rag: false
  });

  // response.data contains:
  // - endpoint: "/api/v1/orcha/chat" or "/api/v1/orcha/ocr" etc.
  // - reason: "default to chat"
  // - prepared_payload: {...}

  // Use this to decide which component to show or which action to take
  return response.data;
};
```

### 4. Get Available Models

```jsx
const [models, setModels] = useState([]);

useEffect(() => {
  const fetchModels = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/models');
      if (response.data.status === 'ok') {
        setModels(response.data.models.data || []);
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };
  fetchModels();
}, []);
```

## Error Handling Best Practices

```jsx
const handleApiError = (error, response) => {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    
    if (status === 503) {
      return "AI service is temporarily unavailable. Please try again.";
    } else if (status === 500) {
      return "Internal server error. Please contact support.";
    } else if (status === 400) {
      return "Invalid request. Please check your input.";
    }
  } else if (error.request) {
    // Request made but no response
    return "Cannot reach the server. Please check your connection.";
  }
  
  return "An unexpected error occurred.";
};
```

## TypeScript Interfaces (Optional)

```typescript
interface ChatRequest {
  user_id: string;
  tenant_id?: string;
  message: string;
  attachments?: Attachment[];
  use_rag?: boolean;
}

interface Attachment {
  uri: string;
  type?: string;
}

interface ChatResponse {
  status: 'ok' | 'error' | 'ocr_queued';
  message?: string;
  contexts?: Context[];
  model_response?: any;
  error?: string;
  jobs?: string[];
}

interface Context {
  source?: string;
  doc_id?: string;
  text?: string;
  chunk?: string;
  content?: string;
  score?: number;
}
```

## Testing the API

Before building your React UI, test with curl:

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/v1/orcha/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test123",
    "message": "Hello, how are you?",
    "use_rag": false
  }'

# Test with RAG
curl -X POST http://localhost:8000/api/v1/orcha/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test123",
    "message": "What are our company policies?",
    "use_rag": true
  }'

# Get available models
curl http://localhost:8000/api/v1/models
```

## React Query Example (Recommended)

Using `@tanstack/react-query` for better state management:

```jsx
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

const useChatMutation = () => {
  return useMutation({
    mutationFn: async (chatData) => {
      const response = await axios.post(
        'http://localhost:8000/api/v1/orcha/chat',
        chatData
      );
      return response.data;
    },
    onSuccess: (data) => {
      console.log('Chat response:', data);
    },
    onError: (error) => {
      console.error('Chat error:', error);
    }
  });
};

// Usage in component
const ChatComponent = () => {
  const chatMutation = useChatMutation();

  const sendMessage = (message) => {
    chatMutation.mutate({
      user_id: 'user123',
      message: message,
      use_rag: false
    });
  };

  return (
    <div>
      {chatMutation.isLoading && <div>Sending...</div>}
      {chatMutation.isError && <div>Error: {chatMutation.error.message}</div>}
      {chatMutation.isSuccess && (
        <div>Response: {chatMutation.data.message}</div>
      )}
      <button onClick={() => sendMessage('Hello')}>Send</button>
    </div>
  );
};
```

## Environment Variables for React

```env
# .env.local
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_DEFAULT_USER_ID=user123
REACT_APP_DEFAULT_TENANT_ID=tenant1
```

```jsx
// Use in code
const API_URL = process.env.REACT_APP_API_URL;
```

---

## Summary for React Developers

**Key Points:**
1. **Main endpoint:** `POST /api/v1/orcha/chat`
2. **Response field to display:** `response.data.message` (this is the AI's text)
3. **Check status:** Always check `response.data.status === 'ok'`
4. **RAG sources:** If using RAG, display `response.data.contexts` as sources
5. **Error handling:** Check for `status === 'error'` and show `response.data.error`
6. **LM Studio URL:** Pre-configured to `http://192.168.1.37:1234`

The API is now optimized for React consumption with clean, predictable response formats! 🚀

