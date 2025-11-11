# Frontend Memory API Fix Guide

## Problem: 500 Error on POST /api/v1/memory

**Symptom:** 
```
POST /api/v1/memory -> 500 Internal Server Error
```

**Cause:** The API schema changed to support memory history. Your frontend is likely sending the old format.

---

## ✅ Solution: Update Frontend POST Request

### OLD Format (No Longer Works)
```typescript
// ❌ OLD - This causes 500 error
const response = await fetch('/api/v1/memory', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 1,
    content: "Memory content here"
  })
});
```

### NEW Format (Required)
```typescript
// ✅ NEW - This works with memory history
const response = await fetch('/api/v1/memory', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 1,
    content: "Memory content here",
    title: "Memory Title",              // OPTIONAL but recommended
    conversation_id: 123,                // OPTIONAL - link to conversation
    source: "auto_extraction",           // OPTIONAL - default: "manual"
    tags: ["preferences", "personal"]    // OPTIONAL - for categorization
  })
});

const data = await response.json();
if (data.status === "ok") {
  console.log("Memory saved with ID:", data.memory_id);
}
```

---

## 📋 API Request Schema

### Required Fields:
- `user_id` (integer) - The user's ID
- `content` (string) - The memory content

### Optional Fields:
- `title` (string | null) - Short title/summary
- `conversation_id` (integer | null) - Link to source conversation
- `source` (string) - Origin of memory
  - `"manual"` (default)
  - `"auto_extraction"`
  - `"import"`
  - `"legacy"`
- `tags` (array of strings | null) - Categorization tags

---

## 🔧 Complete Frontend Integration Examples

### Example 1: Basic Memory Save (Minimum Fields)
```typescript
async function saveMemory(userId: number, content: string) {
  try {
    const response = await fetch('/api/v1/memory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        content: content,
        // All other fields are optional and will use defaults
      })
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('Failed to save memory:', error);
      return null;
    }

    const data = await response.json();
    return data.memory_id;
  } catch (error) {
    console.error('Error saving memory:', error);
    return null;
  }
}

// Usage
const memoryId = await saveMemory(1, "User prefers formal communication");
```

### Example 2: Full Memory Save (With All Fields)
```typescript
async function saveFullMemory(
  userId: number,
  content: string,
  title?: string,
  conversationId?: number,
  tags?: string[]
) {
  try {
    const payload: any = {
      user_id: userId,
      content: content,
      source: "auto_extraction"  // Indicate this was AI-generated
    };

    // Add optional fields if provided
    if (title) payload.title = title;
    if (conversationId) payload.conversation_id = conversationId;
    if (tags && tags.length > 0) payload.tags = tags;

    const response = await fetch('/api/v1/memory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Memory saved:', data.memory_id);
    return data.memory_id;
    
  } catch (error) {
    console.error('❌ Failed to save memory:', error);
    throw error;
  }
}

// Usage
const memoryId = await saveFullMemory(
  1,                                    // userId
  "User prefers formal communication",  // content
  "Communication Preferences",          // title
  456,                                  // conversationId
  ["preferences", "style"]              // tags
);
```

### Example 3: React Component Integration
```typescript
import React, { useState } from 'react';

interface MemorySaveProps {
  userId: number;
  conversationId?: number;
  onMemorySaved?: (memoryId: number) => void;
}

export const MemorySaveButton: React.FC<MemorySaveProps> = ({ 
  userId, 
  conversationId,
  onMemorySaved 
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSaveMemory = async (aiGeneratedContent: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          content: aiGeneratedContent,
          title: "Auto-generated memory",
          conversation_id: conversationId,
          source: "auto_extraction",
          tags: ["auto"]
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save memory');
      }

      const data = await response.json();
      
      if (data.status === "ok") {
        console.log('Memory saved successfully:', data.memory_id);
        onMemorySaved?.(data.memory_id);
      } else {
        throw new Error('Unexpected response format');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error saving memory:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button 
        onClick={() => handleSaveMemory("Example memory content")}
        disabled={loading}
      >
        {loading ? 'Saving...' : 'Save Memory'}
      </button>
      {error && <div className="error">{error}</div>}
    </div>
  );
};
```

---

## 📥 GET Memory API (Also Changed)

### OLD Response Format:
```json
{
  "status": "ok",
  "memory": {
    "content": "...",
    "created_at": "...",
    "updated_at": "..."
  }
}
```

### NEW Response Format:
```json
{
  "status": "ok",
  "memories": [
    {
      "id": 1,
      "content": "...",
      "title": "...",
      "conversation_id": 123,
      "source": "auto_extraction",
      "tags": ["preferences"],
      "is_active": true,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

### Update Frontend GET Request:
```typescript
// ❌ OLD
const response = await fetch(`/api/v1/memory/${userId}`);
const data = await response.json();
const memory = data.memory;  // Single object

// ✅ NEW
const response = await fetch(`/api/v1/memory/${userId}?limit=50`);
const data = await response.json();
const memories = data.memories;  // Array of objects
const total = data.total;
```

---

## 🐛 Debugging Steps

### 1. Check Server Logs for Detailed Error
Look for the actual error message in your terminal. The 500 error should show:
```
[ERROR] Failed to save memory: <detailed error>
Traceback (most recent call last):
  ...
```

### 2. Test API with curl
```bash
# Test basic POST
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "content": "Test memory content"
  }'

# Test with all fields
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "content": "Test memory",
    "title": "Test",
    "source": "manual",
    "tags": ["test"]
  }'
```

### 3. Check Browser DevTools
In your browser's Network tab:
- Click on the failed `/api/v1/memory` request
- Check the **Request Payload** - what is your frontend sending?
- Check the **Response** - what error message did you get?

### 4. Common Issues

**Issue:** `user_id` sent as string instead of integer
```typescript
// ❌ Wrong
body: JSON.stringify({ user_id: "1", ... })

// ✅ Correct
body: JSON.stringify({ user_id: 1, ... })
```

**Issue:** Invalid `conversation_id` (doesn't exist)
```typescript
// Make sure conversation exists first
const conv = await fetch(`/api/v1/conversations/${conversationId}`);
if (conv.ok) {
  // Then save memory with this conversation_id
}
```

**Issue:** Tags not array
```typescript
// ❌ Wrong
body: JSON.stringify({ tags: "preferences" })

// ✅ Correct
body: JSON.stringify({ tags: ["preferences"] })
```

---

## ✅ Quick Fix Checklist

1. [ ] Update POST request to include at minimum `user_id` and `content`
2. [ ] Ensure `user_id` is sent as **integer**, not string
3. [ ] If sending `tags`, ensure it's an **array of strings**
4. [ ] If sending `conversation_id`, ensure it's a valid **integer** (conversation exists)
5. [ ] Update GET response handler to expect `memories` **array**, not single `memory` object
6. [ ] Check server terminal logs for actual error message
7. [ ] Test with minimal payload first (just user_id and content)

---

## 🔄 Migration Path for Existing Frontend

### Step 1: Update Memory Save Function
```typescript
// Find your existing saveMemory function and update it:

// BEFORE
async function saveMemory(userId: string, content: string) {
  const response = await fetch('/api/v1/memory', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, content })
  });
  return await response.json();
}

// AFTER
async function saveMemory(
  userId: number,  // Changed to number
  content: string,
  options?: {      // Added optional parameters
    title?: string;
    conversationId?: number;
    tags?: string[];
  }
) {
  const payload: any = {
    user_id: userId,
    content: content,
    source: "auto_extraction"
  };
  
  if (options?.title) payload.title = options.title;
  if (options?.conversationId) payload.conversation_id = options.conversationId;
  if (options?.tags) payload.tags = options.tags;

  const response = await fetch('/api/v1/memory', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to save memory: ${response.status}`);
  }
  
  return await response.json();
}
```

### Step 2: Update Memory Load Function
```typescript
// BEFORE
async function loadMemory(userId: string) {
  const response = await fetch(`/api/v1/memory/${userId}`);
  const data = await response.json();
  return data.memory;  // Single object
}

// AFTER
async function loadMemories(userId: number, limit: number = 50) {
  const response = await fetch(`/api/v1/memory/${userId}?limit=${limit}`);
  const data = await response.json();
  return {
    memories: data.memories,  // Array
    total: data.total
  };
}
```

---

## 📞 Need More Help?

If you're still getting 500 errors:

1. **Share the server logs** - Look for the full error traceback
2. **Share your frontend code** - The exact fetch request
3. **Test with curl** - Does the command above work?

The most common issue is sending `user_id` as a string instead of integer. Check that first!

---

## 🎯 Summary

**The Fix:**
```typescript
// Just ensure your POST includes these MINIMUM fields:
{
  "user_id": 1,          // INTEGER (not string!)
  "content": "..."       // STRING
}

// Everything else is optional
```

**Test it:**
```bash
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "content": "Test"}'
```

If this works in curl but fails in your frontend, the issue is in your frontend code sending wrong data types or format.

