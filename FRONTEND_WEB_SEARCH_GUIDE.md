# Frontend Implementation Guide: Web Search Feature

## Overview
The web search feature allows users to search the internet using Google Custom Search API, with results automatically refined by the LLM for a clean, summarized response. The API provides 100 free queries per day.

## Backend Endpoint

**URL**: `POST /api/v1/orcha/search`

### Request Format
```json
{
  "user_id": "123",
  "query": "Who won the F1 race last weekend?",
  "max_results": 5,           // Optional, default: 5
  "conversation_id": 456,     // Optional, to maintain context
  "tenant_id": "tenant_123"   // Optional
}
```

### Response Format
```json
{
  "status": "ok",
  "message": "LLM-refined answer based on search results...",
  "conversation_id": 456,
  "search_query": "Who won the F1 race last weekend?",
  "raw_search_results": "Here are the search results:\n\nResult 1:...",
  "results_count": 5,
  "token_usage": {
    "current_usage": 1500,
    "reset_at": "2025-11-12T10:00:00Z"
  },
  "model_response": {...}
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Error message",
  "error_type": "ExceptionType",
  "message": "User-friendly error message",
  "conversation_id": null
}
```

## Frontend Implementation Steps

### 1. Add Search Mode Toggle
Add a button or toggle in your chat interface to activate "Search Mode":

```javascript
const [searchMode, setSearchMode] = useState(false);

// UI Toggle
<button 
  onClick={() => setSearchMode(!searchMode)}
  className={searchMode ? 'active' : ''}
>
  🔍 Search Mode {searchMode ? 'ON' : 'OFF'}
</button>
```

### 2. Update Message Send Function
Modify your message sending logic to route to the search endpoint when search mode is active:

```javascript
const sendMessage = async (message) => {
  try {
    const endpoint = searchMode 
      ? '/api/v1/orcha/search'   // Search endpoint
      : '/api/v1/orcha/chat';     // Regular chat endpoint
    
    const payload = searchMode 
      ? {
          user_id: currentUserId,
          query: message,
          max_results: 5,
          conversation_id: currentConversationId,
          tenant_id: tenantId
        }
      : {
          user_id: currentUserId,
          message: message,
          conversation_id: currentConversationId,
          tenant_id: tenantId,
          use_rag: ragEnabled
        };
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(payload)
    });
    
    const data = await response.json();
    
    if (data.status === 'ok') {
      // Display the LLM-refined message
      displayMessage('assistant', data.message);
      
      // Optionally show search metadata
      if (searchMode) {
        console.log('Search query:', data.search_query);
        console.log('Results count:', data.results_count);
      }
      
      // Update conversation ID if needed
      setCurrentConversationId(data.conversation_id);
    } else {
      // Handle error
      showError(data.message || data.error);
    }
    
  } catch (error) {
    console.error('Error sending message:', error);
    showError('Failed to send message. Please try again.');
  }
};
```

### 3. Visual Indicators (Optional but Recommended)
Add visual feedback to show when search mode is active:

```javascript
// Show search indicator in input field
<div className="chat-input-wrapper">
  {searchMode && (
    <span className="search-indicator">
      🔍 Searching the web...
    </span>
  )}
  <input 
    type="text"
    placeholder={searchMode 
      ? "Search the internet..." 
      : "Type your message..."}
    value={inputMessage}
    onChange={(e) => setInputMessage(e.target.value)}
  />
  <button onClick={handleSend}>Send</button>
</div>
```

### 4. Display Search Results (Optional)
If you want to show raw search results alongside the refined answer:

```javascript
const displaySearchResults = (data) => {
  return (
    <div className="search-response">
      <div className="refined-answer">
        <h4>Answer:</h4>
        <p>{data.message}</p>
      </div>
      
      {/* Optional: Show raw results */}
      {showRawResults && (
        <details>
          <summary>View Raw Search Results</summary>
          <pre>{data.raw_search_results}</pre>
        </details>
      )}
      
      {/* Show metadata */}
      <div className="search-metadata">
        <small>
          🔍 Searched: {data.search_query} | 
          📊 {data.results_count} results
        </small>
      </div>
    </div>
  );
};
```

### 5. Example React Component
Complete example with search mode:

```javascript
import React, { useState } from 'react';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [searchMode, setSearchMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  
  const API_BASE_URL = process.env.REACT_APP_API_URL;
  const userId = localStorage.getItem('userId');
  const authToken = localStorage.getItem('authToken');
  
  const sendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    // Add user message to UI
    const userMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    try {
      const endpoint = searchMode 
        ? '/api/v1/orcha/search'
        : '/api/v1/orcha/chat';
      
      const payload = searchMode
        ? {
            user_id: userId,
            query: inputMessage,
            max_results: 5,
            conversation_id: conversationId
          }
        : {
            user_id: userId,
            message: inputMessage,
            conversation_id: conversationId
          };
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(payload)
      });
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        // Add assistant response
        const assistantMessage = {
          role: 'assistant',
          content: data.message,
          isSearchResult: searchMode,
          searchQuery: data.search_query,
          resultsCount: data.results_count
        };
        setMessages(prev => [...prev, assistantMessage]);
        
        // Update conversation ID
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }
      } else {
        // Add error message
        setMessages(prev => [...prev, {
          role: 'error',
          content: data.message || 'An error occurred'
        }]);
      }
      
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'error',
        content: 'Failed to send message. Please try again.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="chat-interface">
      {/* Search mode toggle */}
      <div className="chat-controls">
        <button
          onClick={() => setSearchMode(!searchMode)}
          className={`search-toggle ${searchMode ? 'active' : ''}`}
        >
          🔍 Search Mode: {searchMode ? 'ON' : 'OFF'}
        </button>
      </div>
      
      {/* Messages display */}
      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">{msg.content}</div>
            {msg.isSearchResult && (
              <div className="search-badge">
                🔍 Web Search: {msg.resultsCount} results
              </div>
            )}
          </div>
        ))}
        {isLoading && <div className="loading">Thinking...</div>}
      </div>
      
      {/* Input area */}
      <div className="input-area">
        {searchMode && (
          <div className="search-indicator">
            🔍 Searching the web
          </div>
        )}
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder={searchMode 
            ? "Search the internet..." 
            : "Type your message..."}
          disabled={isLoading}
        />
        <button 
          onClick={sendMessage}
          disabled={isLoading || !inputMessage.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
```

## Key Points

1. **Automatic Refinement**: The backend automatically sends search results to the LLM for refinement, so you always get a clean, summarized response.

2. **Conversation Context**: Include `conversation_id` to maintain conversation context across search queries.

3. **Token Tracking**: Search queries consume tokens. The response includes token usage information in `token_usage` field.

4. **Error Handling**: Always check `data.status` - it will be either `"ok"` or `"error"`.

5. **User Experience**: 
   - Show loading indicators during search
   - Display search mode status clearly
   - Optionally show search metadata (query, result count)
   - Consider adding a badge/icon to distinguish search results from regular chat

## Styling Suggestions (CSS)

```css
.search-toggle {
  padding: 8px 16px;
  border: 2px solid #ccc;
  border-radius: 20px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
}

.search-toggle.active {
  background: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.search-indicator {
  display: inline-block;
  padding: 4px 8px;
  background: #e3f2fd;
  border-radius: 4px;
  font-size: 12px;
  color: #1976d2;
  margin-bottom: 8px;
}

.search-badge {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 3px;
  display: inline-block;
}

.message.assistant .search-badge {
  background: #e8f5e9;
  color: #2e7d32;
}
```

## Testing

Test the feature with these sample queries:
- "Who won the F1 race last weekend?"
- "What are the latest developments in AI?"
- "Current Bitcoin price"
- "Recent news about climate change"

## Notes

- The search uses Google Custom Search API
- 100 free queries per day (quota limit)
- Results are limited to 5 by default (configurable, max 10 per request)
- LLM refinement ensures clean, contextual responses
- All searches are logged in the conversation history
- Token usage is tracked automatically
- Error messages inform users if quota is exceeded

