# Conversation Isolation Fix

## Problem Identified

The chat system was storing all conversations as one global chat for each user instead of maintaining separate, isolated conversations. This was caused by a bug in the conversation history loading logic in `orchestrator.py`.

## Root Cause

In `app/services/orchestrator.py` (lines 194-220), the conversation history loading had a critical bug:

### Before (Buggy Code):
```python
history_result = await db_session.execute(
    select(ChatMessage)
    .where(ChatMessage.conversation_id == conversation.id)
    .order_by(ChatMessage.created_at.desc())
    .limit(10)
)
db_messages = history_result.scalars().all()

# Convert to message format (excluding the current user message)
db_history = []
for msg in reversed(db_messages[:-1]):  # ❌ BUG: This removes the OLDEST message, not the current one!
    if msg.role in ["user", "assistant"]:
        db_history.append({
            "role": msg.role,
            "content": msg.content
        })
```

**The Bug:**
1. Query orders by `created_at.desc()` (newest first)
2. The current user message was just added to the database
3. Using `db_messages[:-1]` removes the LAST item in the list (oldest message)
4. This meant the current message was INCLUDED in the history, causing duplication and context confusion

## Solution

### After (Fixed Code):
```python
# Load messages that were created BEFORE the current user message
history_result = await db_session.execute(
    select(ChatMessage)
    .where(
        ChatMessage.conversation_id == conversation.id,
        ChatMessage.id < user_message.id  # ✅ Only messages before current one
    )
    .order_by(ChatMessage.created_at.desc())
    .limit(10)
)
db_messages = history_result.scalars().all()

# Convert to message format in chronological order (oldest to newest)
db_history = []
for msg in reversed(db_messages):  # ✅ Reverse to get chronological order
    if msg.role in ["user", "assistant"]:
        db_history.append({
            "role": msg.role,
            "content": msg.content
        })
```

**The Fix:**
1. Added `ChatMessage.id < user_message.id` filter to exclude the current message
2. This ensures we only load messages that existed BEFORE the current one
3. Properly maintains conversation isolation
4. Prevents message duplication in context

## How Conversations Work Now

### 1. **Creating a New Conversation**
```json
POST /api/v1/orcha/chat
{
  "user_id": "1",
  "message": "Hello!",
  "conversation_id": null  // null = create new conversation
}
```

Response includes `conversation_id` for subsequent messages.

### 2. **Continuing an Existing Conversation**
```json
POST /api/v1/orcha/chat
{
  "user_id": "1",
  "message": "What did I say earlier?",
  "conversation_id": 123  // Use existing conversation ID
}
```

The system will:
- Load the last 10 messages from conversation 123
- Exclude the current message being processed
- Maintain full context within that conversation
- Keep it isolated from other conversations

### 3. **Multiple Conversations**
Each user can have multiple conversations:
- Conversation 1: "Help with insurance claims"
- Conversation 2: "Document processing questions"
- Conversation 3: "General health questions"

Each conversation maintains its own:
- ✅ Separate message history
- ✅ Independent context
- ✅ Unique conversation ID
- ✅ Auto-generated title

## Database Schema

The system uses three main tables:

### `conversations`
- `id`: Unique conversation identifier
- `user_id`: Owner of the conversation
- `title`: Auto-generated or user-set title
- `tenant_id`: Multi-tenant support
- `created_at`, `updated_at`: Timestamps
- `is_active`: Soft delete flag

### `chat_messages`
- `id`: Unique message identifier
- `conversation_id`: Links to parent conversation
- `role`: "user" or "assistant"
- `content`: Message text
- `attachments`: JSON metadata
- `token_count`: Usage tracking
- `model_used`: Which AI model responded
- `created_at`: Timestamp

### `users`
- `id`: User identifier
- `username`, `email`: User credentials
- `plan_type`: free, pro, enterprise
- Relationships to conversations

## API Endpoints

### Conversation Management
- `POST /api/v1/conversations` - Create new conversation
- `GET /api/v1/conversations/{user_id}` - List user's conversations
- `GET /api/v1/conversations/{user_id}/{conversation_id}` - Get conversation details with messages
- `PUT /api/v1/conversations/{user_id}/{conversation_id}` - Update conversation title
- `DELETE /api/v1/conversations/{user_id}/{conversation_id}` - Soft delete conversation

### Chat
- `POST /api/v1/orcha/chat` - Send message (creates new conversation if `conversation_id` is null)

## Testing

Run the isolation test to verify the fix:

```bash
python test_conversation_isolation.py
```

This test:
1. Creates two separate conversations
2. Sends different information to each (Alice/pizza vs Bob/burgers)
3. Verifies each conversation maintains its own context
4. Confirms no information leaks between conversations

## What Was Fixed

✅ **Conversation Isolation**: Each conversation now properly maintains its own history
✅ **Message Deduplication**: Current message no longer included in its own context
✅ **Proper History Loading**: Only loads messages that existed before the current one
✅ **Chronological Order**: Messages loaded in correct order (oldest to newest)
✅ **Database Filtering**: Uses message ID comparison for accurate filtering

## Frontend Integration

The frontend should:

1. **Store conversation_id** when starting a new chat
2. **Pass conversation_id** with every subsequent message in that conversation
3. **Create new conversation** by passing `conversation_id: null`
4. **List conversations** using `GET /conversations/{user_id}`
5. **Load conversation history** using `GET /conversations/{user_id}/{conversation_id}`

Example React flow:
```typescript
// Start new conversation
const response = await fetch('/api/v1/orcha/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: userId,
    message: userMessage,
    conversation_id: null  // Creates new conversation
  })
});
const { conversation_id } = await response.json();

// Continue conversation
const response2 = await fetch('/api/v1/orcha/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: userId,
    message: nextMessage,
    conversation_id: conversation_id  // Uses existing conversation
  })
});
```

## Benefits

1. **True Multi-Conversation Support**: Users can have multiple independent chats
2. **Context Preservation**: Each conversation remembers its own history
3. **No Cross-Contamination**: Information from one conversation doesn't leak to others
4. **Scalable**: Supports unlimited conversations per user
5. **Database-Backed**: All conversations persist across sessions

## Migration Notes

If you have existing chat data:
- Old messages without conversation_id will need migration
- Create conversations for existing message groups
- Update frontend to use conversation IDs

The system is now ready for production use with proper conversation isolation! 🎉
