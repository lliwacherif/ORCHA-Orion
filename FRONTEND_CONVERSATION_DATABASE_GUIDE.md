# Frontend Integration Guide: Database-Backed Conversations

This guide explains how to integrate with the new database-backed conversation system in ORCHA. All user chats and conversations are now stored in PostgreSQL, providing persistent conversation history across sessions.

## Overview

The system now supports:
- **Persistent conversations** stored in PostgreSQL
- **Conversation management** (create, read, update, delete)
- **Message history** automatically loaded from database
- **Multi-tenant support** with tenant_id
- **Token tracking** per conversation
- **Auto-generated conversation titles**

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

## 1. Conversation Management

### Create New Conversation
```http
POST /conversations
Content-Type: application/json

{
  "user_id": 1,
  "title": "Optional conversation title",
  "tenant_id": "optional_tenant_id"
}
```

**Response:**
```json
{
  "id": 123,
  "title": "Optional conversation title",
  "tenant_id": "optional_tenant_id",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "message_count": 0
}
```

### Get User's Conversations
```http
GET /conversations/{user_id}?limit=50&offset=0
```

**Response:**
```json
[
  {
    "id": 123,
    "title": "How to process insurance claims",
    "tenant_id": "company_abc",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "message_count": 8
  },
  {
    "id": 122,
    "title": "Document analysis help",
    "tenant_id": "company_abc",
    "created_at": "2024-01-15T09:15:00Z",
    "updated_at": "2024-01-15T09:20:00Z",
    "message_count": 4
  }
]
```

### Get Conversation Details (with messages)
```http
GET /conversations/{user_id}/{conversation_id}
```

**Response:**
```json
{
  "id": 123,
  "title": "How to process insurance claims",
  "tenant_id": "company_abc",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "messages": [
    {
      "id": 1001,
      "role": "user",
      "content": "How do I process a health insurance claim?",
      "attachments": null,
      "token_count": null,
      "model_used": null,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 1002,
      "role": "assistant",
      "content": "To process a health insurance claim, you need to...",
      "attachments": null,
      "token_count": 150,
      "model_used": "llama-3.1-8b",
      "created_at": "2024-01-15T10:30:05Z"
    }
  ]
}
```

### Update Conversation Title
```http
PUT /conversations/{user_id}/{conversation_id}
Content-Type: application/json

{
  "title": "New conversation title"
}
```

### Delete Conversation (Soft Delete)
```http
DELETE /conversations/{user_id}/{conversation_id}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Conversation deleted successfully"
}
```

## 2. Chat Integration

### Send Message to Existing Conversation
```http
POST /orcha/chat
Content-Type: application/json

{
  "user_id": "1",
  "tenant_id": "company_abc",
  "message": "Can you help me with document processing?",
  "conversation_id": 123,
  "attachments": [],
  "use_rag": false,
  "conversation_history": []
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "I'd be happy to help you with document processing...",
  "conversation_id": 123,
  "contexts": [],
  "token_usage": {
    "current_usage": 150,
    "reset_at": "2024-01-16T10:30:00Z"
  }
}
```

### Start New Conversation
```http
POST /orcha/chat
Content-Type: application/json

{
  "user_id": "1",
  "tenant_id": "company_abc",
  "message": "Hello, I need help with insurance claims",
  "conversation_id": null,
  "attachments": [],
  "use_rag": false,
  "conversation_history": []
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Hello! I'm here to help you with insurance claims...",
  "conversation_id": 124,
  "contexts": [],
  "token_usage": {
    "current_usage": 200,
    "reset_at": "2024-01-16T10:30:00Z"
  }
}
```

## 3. Frontend Implementation Examples

### React Hook for Conversation Management

```typescript
import { useState, useEffect } from 'react';

interface Conversation {
  id: number;
  title: string | null;
  tenant_id: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface ChatMessage {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments: any;
  token_count: number | null;
  model_used: string | null;
  created_at: string;
}

export const useConversations = (userId: number) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/conversations/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch conversations');
      const data = await response.json();
      setConversations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const createConversation = async (title?: string, tenantId?: string) => {
    try {
      const response = await fetch('/api/v1/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          title,
          tenant_id: tenantId
        })
      });
      if (!response.ok) throw new Error('Failed to create conversation');
      const newConversation = await response.json();
      setConversations(prev => [newConversation, ...prev]);
      return newConversation;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const deleteConversation = async (conversationId: number) => {
    try {
      const response = await fetch(`/api/v1/conversations/${userId}/${conversationId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete conversation');
      setConversations(prev => prev.filter(c => c.id !== conversationId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [userId]);

  return {
    conversations,
    loading,
    error,
    fetchConversations,
    createConversation,
    deleteConversation
  };
};
```

### React Hook for Chat Messages

```typescript
import { useState, useEffect } from 'react';

export const useChatMessages = (userId: number, conversationId: number | null) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMessages = async () => {
    if (!conversationId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/conversations/${userId}/${conversationId}`);
      if (!response.ok) throw new Error('Failed to fetch messages');
      const data = await response.json();
      setMessages(data.messages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (
    message: string,
    attachments: any[] = [],
    useRag: boolean = false,
    tenantId?: string
  ) => {
    try {
      const response = await fetch('/api/v1/orcha/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId.toString(),
          tenant_id: tenantId,
          message,
          conversation_id: conversationId,
          attachments,
          use_rag: useRag,
          conversation_history: [] // Let backend load from database
        })
      });

      if (!response.ok) throw new Error('Failed to send message');
      const result = await response.json();

      if (result.status === 'ok') {
        // Add user message
        const userMessage: ChatMessage = {
          id: Date.now(), // Temporary ID
          role: 'user',
          content: message,
          attachments: attachments.length > 0 ? attachments : null,
          token_count: null,
          model_used: null,
          created_at: new Date().toISOString()
        };

        // Add assistant message
        const assistantMessage: ChatMessage = {
          id: Date.now() + 1, // Temporary ID
          role: 'assistant',
          content: result.message,
          attachments: null,
          token_count: result.token_usage?.current_usage || null,
          model_used: 'llama-3.1-8b',
          created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage, assistantMessage]);
        
        // Return conversation ID if this was a new conversation
        return result.conversation_id;
      } else {
        throw new Error(result.error || 'Chat request failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  useEffect(() => {
    fetchMessages();
  }, [conversationId]);

  return {
    messages,
    loading,
    error,
    sendMessage,
    fetchMessages
  };
};
```

### React Component Example

```typescript
import React, { useState } from 'react';
import { useConversations } from './hooks/useConversations';
import { useChatMessages } from './hooks/useChatMessages';

interface ChatInterfaceProps {
  userId: number;
  tenantId?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ userId, tenantId }) => {
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messageInput, setMessageInput] = useState('');
  
  const {
    conversations,
    loading: conversationsLoading,
    createConversation,
    deleteConversation
  } = useConversations(userId);

  const {
    messages,
    loading: messagesLoading,
    sendMessage
  } = useChatMessages(userId, currentConversationId);

  const handleSendMessage = async () => {
    if (!messageInput.trim()) return;

    try {
      let conversationId = currentConversationId;
      
      // If no current conversation, create one
      if (!conversationId) {
        const newConversation = await createConversation(undefined, tenantId);
        conversationId = newConversation.id;
        setCurrentConversationId(conversationId);
      }

      await sendMessage(messageInput, [], false, tenantId);
      setMessageInput('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConversation = await createConversation(undefined, tenantId);
      setCurrentConversationId(newConversation.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (conversationId: number) => {
    setCurrentConversationId(conversationId);
  };

  return (
    <div className="chat-interface">
      {/* Sidebar with conversations */}
      <div className="conversations-sidebar">
        <button onClick={handleNewConversation} className="new-chat-btn">
          + New Chat
        </button>
        
        {conversationsLoading ? (
          <div>Loading conversations...</div>
        ) : (
          <div className="conversations-list">
            {conversations.map(conv => (
              <div
                key={conv.id}
                className={`conversation-item ${currentConversationId === conv.id ? 'active' : ''}`}
                onClick={() => handleSelectConversation(conv.id)}
              >
                <div className="conversation-title">
                  {conv.title || 'Untitled Conversation'}
                </div>
                <div className="conversation-meta">
                  {conv.message_count} messages • {new Date(conv.updated_at).toLocaleDateString()}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                    if (currentConversationId === conv.id) {
                      setCurrentConversationId(null);
                    }
                  }}
                  className="delete-btn"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Chat area */}
      <div className="chat-area">
        {messagesLoading ? (
          <div>Loading messages...</div>
        ) : (
          <div className="messages-container">
            {messages.map(msg => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-content">{msg.content}</div>
                <div className="message-meta">
                  {msg.created_at} {msg.token_count && `• ${msg.token_count} tokens`}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="message-input">
          <input
            type="text"
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type your message..."
          />
          <button onClick={handleSendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
};
```

## 4. Key Implementation Notes

### Conversation Flow
1. **New Chat**: Don't provide `conversation_id` in chat request
2. **Existing Chat**: Always provide `conversation_id` to continue conversation
3. **Auto-title**: Backend auto-generates titles from first user message
4. **History**: Backend automatically loads conversation history from database

### Error Handling
- Always check `status` field in responses
- Handle network errors gracefully
- Show user-friendly error messages

### Performance Tips
- Use pagination for conversation lists (`limit`/`offset`)
- Load conversation details only when needed
- Cache conversations locally for better UX

### Token Tracking
- Each response includes `token_usage` information
- Track usage per user for billing/limits
- Reset happens every 24 hours

## 5. Migration from Browser Storage

If you're migrating from browser-based conversation storage:

1. **Create conversations** for existing browser data
2. **Import messages** using the conversation endpoints
3. **Update UI** to use conversation IDs instead of local storage keys
4. **Remove** browser storage code

## 6. Testing

Test the integration with these scenarios:
- Create new conversation
- Send messages to existing conversation
- Load conversation history
- Update conversation title
- Delete conversation
- Handle network errors
- Test with multiple users/tenants

## 7. Security Notes

- Always validate `user_id` on frontend
- Use HTTPS in production
- Implement proper authentication
- Validate file uploads for attachments
- Rate limit chat requests

This system provides a robust, scalable foundation for persistent conversations with full database backing.



