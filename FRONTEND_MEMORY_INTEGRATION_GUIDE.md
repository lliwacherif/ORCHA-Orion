# Frontend Memory Integration Guide

## Overview

This guide explains how to integrate the Memory Storage feature into your React frontend. The backend now stores user memories in the database and automatically includes them in chat context.

---

## Backend Implementation Summary

✅ **Database Table**: `user_memories` created  
✅ **API Endpoints**: Save and retrieve memory  
✅ **Chat Integration**: Memory automatically loaded and injected into conversations  
✅ **Migration Script**: `migrate_add_user_memory.py` ready to run  

---

## API Endpoints

### 1. Save Memory

**Endpoint**: `POST /api/v1/memory`

**Request**:
```typescript
{
  user_id: number;
  content: string;  // The AI-generated memory
}
```

**Response**:
```typescript
{
  status: "ok";
  message: "Memory saved successfully";
}
```

**Example**:
```typescript
const saveMemory = async (userId: number, memoryContent: string) => {
  const response = await fetch('/api/v1/memory', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      content: memoryContent
    })
  });
  return response.json();
};
```

---

### 2. Get Memory

**Endpoint**: `GET /api/v1/memory/{user_id}`

**Response**:
```typescript
{
  status: "ok";
  memory: {
    content: string;
    created_at: string;  // ISO 8601 format
    updated_at: string;  // ISO 8601 format
  } | null;  // null if no memory exists
}
```

**Example**:
```typescript
const getMemory = async (userId: number) => {
  const response = await fetch(`/api/v1/memory/${userId}`);
  return response.json();
};
```

---

## Frontend Implementation

### Step 1: Update Memory Component

```typescript
// components/Memory.tsx or wherever your memory feature is

const MemoryComponent = () => {
  const { user } = useAuth();
  const [memory, setMemory] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Generate memory using the chat API
  const generateMemory = async () => {
    setIsGenerating(true);
    try {
      // Use the special trigger phrase to activate memory extraction
      const response = await fetch('/api/v1/orcha/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          message: "Based on my recent messages, extract and remember key information about me",
          conversation_id: currentConversationId // Your current conversation
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        const generatedMemory = data.message;
        setMemory(generatedMemory);
        
        // Automatically save to backend
        await saveMemoryToBackend(generatedMemory);
      }
    } catch (error) {
      console.error('Failed to generate memory:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  // Save memory to backend
  const saveMemoryToBackend = async (content: string) => {
    setIsSaving(true);
    try {
      const response = await fetch('/api/v1/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          content: content
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        console.log('✅ Memory saved to database');
        // Optional: Show success toast
      }
    } catch (error) {
      console.error('Failed to save memory:', error);
      // Optional: Show error toast
    } finally {
      setIsSaving(false);
    }
  };

  // Load existing memory on component mount
  useEffect(() => {
    const loadMemory = async () => {
      try {
        const response = await fetch(`/api/v1/memory/${user.id}`);
        const data = await response.json();
        
        if (data.status === 'ok' && data.memory) {
          setMemory(data.memory.content);
          console.log('📖 Loaded existing memory from database');
        }
      } catch (error) {
        console.error('Failed to load memory:', error);
      }
    };

    if (user?.id) {
      loadMemory();
    }
  }, [user?.id]);

  return (
    <div className="memory-container">
      <button 
        onClick={generateMemory} 
        disabled={isGenerating || isSaving}
      >
        {isGenerating ? 'Generating...' : 
         isSaving ? 'Saving...' : 
         memory ? 'Regenerate Memory' : 'Generate Memory'}
      </button>
      
      {memory && (
        <div className="memory-display">
          <h3>Your Memory</h3>
          <p>{memory}</p>
          <small>
            Memory is automatically used in all conversations
          </small>
        </div>
      )}
    </div>
  );
};
```

---

### Step 2: Automatic Memory Usage

**Good News**: You don't need to do anything special in chat!

When you send a chat message, the backend automatically:
1. ✅ Loads the user's memory from database
2. ✅ Injects it into the conversation context
3. ✅ AI uses it to personalize responses

**Example Flow**:
```
User sends: "What insurance plans do you recommend?"

Backend automatically adds to context:
- System: "You are AURA..."
- System: "=== USER MEMORY === User prefers comprehensive coverage, 
          works in tech industry, has family of 4..."
- User: "What insurance plans do you recommend?"

AI responds with personalized recommendations!
```

---

### Step 3: Memory Indicator (Optional)

Show users when memory is active:

```typescript
const ChatInterface = () => {
  const { user } = useAuth();
  const [hasMemory, setHasMemory] = useState(false);

  useEffect(() => {
    const checkMemory = async () => {
      const response = await fetch(`/api/v1/memory/${user.id}`);
      const data = await response.json();
      setHasMemory(data.memory !== null);
    };
    
    checkMemory();
  }, [user.id]);

  return (
    <div>
      {hasMemory && (
        <div className="memory-badge">
          💭 Memory Active
        </div>
      )}
      {/* Rest of chat interface */}
    </div>
  );
};
```

---

## Backend Migration

Before using this feature, run the database migration:

```bash
# Run migration
python migrate_add_user_memory.py

# Verify
python migrate_add_user_memory.py --verify

# Rollback (if needed)
python migrate_add_user_memory.py --rollback
```

---

## Testing

### 1. Test Memory Generation
```typescript
// Should trigger memory extraction mode
const response = await fetch('/api/v1/orcha/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 1,
    message: "Based on my recent messages, extract and remember key information"
  })
});

// Backend logs should show:
// "🧠 Memory extraction request detected - using unrestricted system prompt"
```

### 2. Test Memory Saving
```typescript
const response = await fetch('/api/v1/memory', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 1,
    content: "User prefers formal communication..."
  })
});

// Should return: { status: "ok", message: "Memory saved successfully" }
```

### 3. Test Memory Retrieval
```typescript
const response = await fetch('/api/v1/memory/1');
// Should return: { status: "ok", memory: { content: "...", ... } }
```

### 4. Test Memory in Chat
```typescript
// After saving memory, send any chat message
const response = await fetch('/api/v1/orcha/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 1,
    message: "Hello, how can you help me?"
  })
});

// Backend logs should show:
// "💭 Loaded user memory (XXX chars)"
```

---

## How It Works

### Memory Extraction Flow

1. **User Clicks "Generate Memory"**
   - Frontend sends special trigger message
   - Message starts with: "Based on my recent messages, extract and remember"

2. **Backend Detects Special Message**
   - Orchestrator detects memory extraction request
   - Switches to unrestricted system prompt
   - Allows AI to analyze conversation freely

3. **AI Generates Memory**
   - Analyzes last 10 messages in conversation
   - Extracts personal details, preferences, context
   - Returns formatted memory summary

4. **Frontend Saves Memory**
   - Receives AI response
   - Displays to user
   - Automatically POSTs to `/api/v1/memory`

5. **Memory Stored in Database**
   - Upsert operation (update if exists, insert if new)
   - One memory per user
   - Includes timestamps

### Memory Usage Flow

1. **User Sends Chat Message**
   - Any regular message (not memory extraction)

2. **Backend Loads Memory**
   - Queries `user_memories` table
   - Loads user's memory (if exists)

3. **Memory Injected into Context**
   - Added as system message
   - Format: "=== USER MEMORY === [content]"
   - Placed after RAG context, before conversation history

4. **AI Uses Memory**
   - AI sees memory in context
   - Personalizes response based on memory
   - No frontend changes needed

---

## Memory Format Example

**Good Memory**:
```
=== USER MEMORY ===
User Profile:
- Name: John Doe
- Industry: Technology/Software
- Preferences: Prefers detailed explanations, technical language
- Context: Looking for health insurance for family of 4
- Budget: $500-800/month
- Previous Discussions: Interested in PPO plans, dental coverage important
```

**What Gets Stored**:
```json
{
  "user_id": 1,
  "content": "User Profile:\n- Name: John Doe\n- Industry: Technology...",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

## UI/UX Recommendations

### 1. Memory Button
- Place in user profile or settings
- Icon: 💭 or 🧠
- Label: "Generate Memory" or "What I Know About You"

### 2. Memory Display
- Show formatted memory content
- Include "Last updated" timestamp
- Option to regenerate

### 3. Memory Badge
- Small indicator in chat interface
- Shows memory is active
- Click to view current memory

### 4. First-Time Experience
- After user's first few messages, suggest generating memory
- Explain benefits: "Help me remember you better for personalized responses"

---

## Error Handling

```typescript
const saveMemory = async (content: string) => {
  try {
    const response = await fetch('/api/v1/memory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id, content })
    });
    
    const data = await response.json();
    
    if (data.status === 'error') {
      throw new Error(data.error || 'Failed to save memory');
    }
    
    return data;
  } catch (error) {
    console.error('Memory save error:', error);
    // Show user-friendly error
    toast.error('Failed to save memory. Please try again.');
    throw error;
  }
};
```

---

## Best Practices

1. **Automatic Saving**: Save memory immediately after generation
2. **Silent Operation**: Memory usage should be transparent to user
3. **Update Strategy**: Regenerate memory periodically (weekly?)
4. **Privacy**: Allow users to view/edit/delete their memory
5. **Loading States**: Show indicators during generation/saving
6. **Error Recovery**: Graceful fallback if memory unavailable

---

## Summary

✅ **Backend Ready**: All endpoints implemented and tested  
✅ **Database Ready**: Migration script available  
✅ **Auto-Integration**: Memory automatically used in chats  
✅ **Simple Frontend**: Just 2 API calls (save + get)  

**Your frontend just needs to:**
1. Call chat API with trigger phrase to generate
2. Save result to `/api/v1/memory`
3. Optionally show memory to user
4. Everything else is automatic!

---

## Troubleshooting

### Memory Not Saving
- Check user_id is correct integer
- Verify migration ran successfully: `SELECT * FROM user_memories;`
- Check backend logs for errors

### Memory Not Used in Chat
- Verify memory exists: `GET /api/v1/memory/{user_id}`
- Check chat logs for "💭 Loaded user memory"
- Ensure not sending memory extraction message (would skip memory load)

### Memory Not Generating
- Check message starts exactly with: "Based on my recent messages, extract and remember"
- Verify conversation has history (at least a few messages)
- Check LM Studio is running and responsive

---

## Next Steps

1. ✅ Run database migration: `python migrate_add_user_memory.py`
2. ✅ Add memory generation button to frontend
3. ✅ Test memory generation and saving
4. ✅ Test chat with memory context
5. ✅ Add memory display/management UI
6. ✅ (Optional) Add memory regeneration schedule

Happy coding! 🚀









