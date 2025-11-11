# 🧠 Frontend Memory Integration Guide

## Overview

This guide explains how to integrate the **User Memory** feature into your frontend application. The memory system stores AI-extracted personal information and preferences about users, which can be displayed in the UI to show what the AI "remembers" about them.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Response Formats](#response-formats)
- [Implementation Examples](#implementation-examples)
- [UI Components](#ui-components)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Quick Start

### Base URL
```
http://localhost:8000/api/v1
```

### Available Endpoints
1. **GET /memory/{user_id}** - Retrieve user's memory
2. **POST /memory** - Save/update user's memory (typically automated)

---

## API Endpoints

### 1. Get User Memory

Retrieve the stored memory for a specific user.

**Endpoint:** `GET /api/v1/memory/{user_id}`

**Example Request:**
```javascript
const userId = 123;

fetch(`http://localhost:8000/api/v1/memory/${userId}`, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

**Success Response (Memory Exists):**
```json
{
  "status": "ok",
  "memory": {
    "content": "User prefers formal communication. Works in the insurance industry specializing in risk assessment. Interested in AI applications for document processing. Based in Paris, France. Prefers responses in French when discussing technical topics.",
    "created_at": "2025-11-01T10:30:00",
    "updated_at": "2025-11-04T14:22:15"
  }
}
```

**Success Response (No Memory):**
```json
{
  "status": "ok",
  "memory": null
}
```

**Error Response:**
```json
{
  "detail": "User not found"
}
```

### 2. Save/Update User Memory

> ⚠️ **Note:** This endpoint is typically called automatically by the backend orchestrator during chat interactions. You usually don't need to call this from the frontend unless you're building an admin interface.

**Endpoint:** `POST /api/v1/memory`

**Request Body:**
```json
{
  "user_id": 123,
  "content": "User prefers formal communication. Works in insurance..."
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Memory saved successfully"
}
```

---

## Response Formats

### Memory Object Structure

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | The AI-extracted memory content |
| `created_at` | string (ISO 8601) | When the memory was first created |
| `updated_at` | string (ISO 8601) | When the memory was last updated |

### Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process the memory data |
| 404 | User not found | Show error message |
| 500 | Server error | Show error and retry option |

---

## Implementation Examples

### React/TypeScript Example

#### 1. Define TypeScript Interfaces

```typescript
// types/memory.ts
export interface UserMemory {
  content: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryResponse {
  status: string;
  memory: UserMemory | null;
}
```

#### 2. Create Memory Service

```typescript
// services/memoryService.ts
import { MemoryResponse, UserMemory } from '../types/memory';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export class MemoryService {
  /**
   * Fetch user's stored memory
   */
  static async getUserMemory(userId: number): Promise<UserMemory | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/memory/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          console.warn('User not found');
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: MemoryResponse = await response.json();
      return data.memory;
    } catch (error) {
      console.error('Error fetching user memory:', error);
      throw error;
    }
  }

  /**
   * Format memory content for display (optional helper)
   */
  static formatMemoryForDisplay(memory: UserMemory): string[] {
    // Split memory content into bullet points if it's formatted with periods
    return memory.content
      .split('. ')
      .filter(item => item.trim().length > 0)
      .map(item => item.trim().replace(/\.$/, ''));
  }

  /**
   * Check if memory needs updating (based on last update time)
   */
  static isMemoryStale(memory: UserMemory, hoursSince: number = 24): boolean {
    const updatedAt = new Date(memory.updated_at);
    const now = new Date();
    const hoursDiff = (now.getTime() - updatedAt.getTime()) / (1000 * 60 * 60);
    return hoursDiff >= hoursSince;
  }
}
```

#### 3. React Component - Memory Display

```typescript
// components/MemoryPanel.tsx
import React, { useEffect, useState } from 'react';
import { MemoryService } from '../services/memoryService';
import { UserMemory } from '../types/memory';

interface MemoryPanelProps {
  userId: number;
}

export const MemoryPanel: React.FC<MemoryPanelProps> = ({ userId }) => {
  const [memory, setMemory] = useState<UserMemory | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMemory();
  }, [userId]);

  const loadMemory = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await MemoryService.getUserMemory(userId);
      setMemory(data);
    } catch (err) {
      setError('Failed to load memory. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="memory-panel loading">
        <div className="spinner"></div>
        <p>Loading memory...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="memory-panel error">
        <p className="error-message">{error}</p>
        <button onClick={loadMemory}>Retry</button>
      </div>
    );
  }

  if (!memory) {
    return (
      <div className="memory-panel empty">
        <p>No memory stored yet. Start chatting to build your profile!</p>
      </div>
    );
  }

  const memoryItems = MemoryService.formatMemoryForDisplay(memory);
  const isStale = MemoryService.isMemoryStale(memory);

  return (
    <div className="memory-panel">
      <div className="memory-header">
        <h3>🧠 What I Remember About You</h3>
        {isStale && (
          <span className="stale-badge">Updated {formatDate(memory.updated_at)}</span>
        )}
      </div>

      <div className="memory-content">
        <ul className="memory-list">
          {memoryItems.map((item, index) => (
            <li key={index} className="memory-item">
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="memory-footer">
        <small className="text-muted">
          Last updated: {formatDate(memory.updated_at)}
        </small>
      </div>
    </div>
  );
};
```

#### 4. React Component - Compact Memory Badge

```typescript
// components/MemoryBadge.tsx
import React, { useEffect, useState } from 'react';
import { MemoryService } from '../services/memoryService';
import { UserMemory } from '../types/memory';

interface MemoryBadgeProps {
  userId: number;
  onClick?: () => void;
}

export const MemoryBadge: React.FC<MemoryBadgeProps> = ({ userId, onClick }) => {
  const [memory, setMemory] = useState<UserMemory | null>(null);
  const [hasMemory, setHasMemory] = useState<boolean>(false);

  useEffect(() => {
    loadMemory();
  }, [userId]);

  const loadMemory = async () => {
    try {
      const data = await MemoryService.getUserMemory(userId);
      setMemory(data);
      setHasMemory(data !== null);
    } catch (err) {
      console.error('Failed to load memory badge:', err);
    }
  };

  if (!hasMemory) {
    return null;
  }

  return (
    <button 
      className="memory-badge" 
      onClick={onClick}
      title="View what the AI remembers about you"
    >
      <span className="badge-icon">🧠</span>
      <span className="badge-text">Memory Active</span>
    </button>
  );
};
```

### Vanilla JavaScript Example

```javascript
// memoryManager.js
class MemoryManager {
  constructor(apiBaseUrl = 'http://localhost:8000/api/v1') {
    this.apiBaseUrl = apiBaseUrl;
  }

  async getUserMemory(userId) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/memory/${userId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.memory;
    } catch (error) {
      console.error('Error fetching memory:', error);
      throw error;
    }
  }

  renderMemory(memory, containerId) {
    const container = document.getElementById(containerId);
    
    if (!memory) {
      container.innerHTML = `
        <div class="empty-state">
          <p>No memory stored yet.</p>
        </div>
      `;
      return;
    }

    const items = memory.content
      .split('. ')
      .filter(item => item.trim())
      .map(item => `<li>${item.trim()}</li>`)
      .join('');

    container.innerHTML = `
      <div class="memory-panel">
        <h3>🧠 What I Remember About You</h3>
        <ul class="memory-list">
          ${items}
        </ul>
        <small>Last updated: ${new Date(memory.updated_at).toLocaleString()}</small>
      </div>
    `;
  }
}

// Usage
const memoryManager = new MemoryManager();
const userId = 123;

memoryManager.getUserMemory(userId)
  .then(memory => {
    memoryManager.renderMemory(memory, 'memory-container');
  })
  .catch(error => {
    console.error('Failed to load memory:', error);
  });
```

---

## UI Components

### Suggested UI Placements

1. **Sidebar Panel** - Dedicated memory section showing full details
2. **User Profile Page** - Display memory alongside user information
3. **Chat Interface Header** - Small badge indicating memory is active
4. **Settings Page** - View and manage (delete) memory data

### CSS Example

```css
/* Memory Panel Styles */
.memory-panel {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.memory-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.stale-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.memory-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.memory-item {
  background: rgba(255, 255, 255, 0.1);
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  backdrop-filter: blur(10px);
}

.memory-item:last-child {
  margin-bottom: 0;
}

.memory-footer {
  margin-top: 16px;
  text-align: center;
  opacity: 0.8;
}

.memory-footer small {
  font-size: 12px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  opacity: 0.7;
}

/* Loading State */
.memory-panel.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.spinner {
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Memory Badge (compact) */
.memory-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 20px;
  padding: 6px 12px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.memory-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.badge-icon {
  font-size: 16px;
}
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| 404 User not found | Invalid user_id | Verify user exists in system |
| 500 Server error | Database connection issue | Check backend logs, retry |
| Network error | Backend not running | Ensure backend is running on port 8000 |
| null memory | No memory created yet | Normal - user needs to chat more |

### Error Handling Pattern

```typescript
async function loadMemoryWithErrorHandling(userId: number) {
  try {
    const memory = await MemoryService.getUserMemory(userId);
    
    if (!memory) {
      // Not an error - just no memory yet
      showEmptyState();
      return;
    }
    
    displayMemory(memory);
    
  } catch (error: any) {
    if (error.message.includes('404')) {
      showError('User not found. Please log in again.');
    } else if (error.message.includes('500')) {
      showError('Server error. Please try again later.');
    } else {
      showError('Failed to load memory. Check your connection.');
    }
    
    // Log for debugging
    console.error('Memory load error:', error);
  }
}
```

---

## Best Practices

### 1. **Caching Strategy**

```typescript
// Cache memory data to reduce API calls
class MemoryCacheService {
  private static cache = new Map<number, { data: UserMemory | null, timestamp: number }>();
  private static CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  static async getMemory(userId: number): Promise<UserMemory | null> {
    const cached = this.cache.get(userId);
    
    if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
      return cached.data;
    }

    const memory = await MemoryService.getUserMemory(userId);
    this.cache.set(userId, { data: memory, timestamp: Date.now() });
    return memory;
  }

  static invalidate(userId: number) {
    this.cache.delete(userId);
  }
}
```

### 2. **Refresh Memory After Chat**

```typescript
// After sending a message, refresh memory if it might have been updated
async function handleMessageSent(userId: number) {
  // ... send message logic ...
  
  // Invalidate cache and refresh memory display
  MemoryCacheService.invalidate(userId);
  
  // Wait a moment for backend to process
  setTimeout(async () => {
    const updatedMemory = await MemoryCacheService.getMemory(userId);
    updateMemoryDisplay(updatedMemory);
  }, 2000);
}
```

### 3. **Privacy Considerations**

```typescript
// Add option to view/clear memory
async function clearUserMemory(userId: number) {
  const confirmed = confirm(
    'Are you sure you want to clear your memory? ' +
    'The AI will forget all personalized information about you.'
  );
  
  if (!confirmed) return;
  
  // You might need to implement a DELETE endpoint for this
  // For now, you can update with empty content
  await fetch(`http://localhost:8000/api/v1/memory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      content: '' // Empty content
    })
  });
  
  MemoryCacheService.invalidate(userId);
}
```

### 4. **Polling for Updates**

```typescript
// Optional: Poll for memory updates during active session
class MemoryPoller {
  private intervalId: number | null = null;
  private readonly POLL_INTERVAL = 60000; // 1 minute

  start(userId: number, onUpdate: (memory: UserMemory | null) => void) {
    this.intervalId = window.setInterval(async () => {
      try {
        MemoryCacheService.invalidate(userId);
        const memory = await MemoryCacheService.getMemory(userId);
        onUpdate(memory);
      } catch (error) {
        console.error('Error polling memory:', error);
      }
    }, this.POLL_INTERVAL);
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}

// Usage
const poller = new MemoryPoller();
poller.start(userId, (memory) => {
  updateMemoryDisplay(memory);
});

// Don't forget to stop when component unmounts
// poller.stop();
```

---

## Testing

### Test the Integration

1. **Verify Backend is Running:**
```bash
# The backend should be running on port 8000
curl http://localhost:8000/api/v1/memory/1
```

2. **Test with Browser Console:**
```javascript
// Open browser console and run:
fetch('http://localhost:8000/api/v1/memory/1')
  .then(r => r.json())
  .then(console.log);
```

3. **Expected Responses:**
   - First call (no memory): `{ status: "ok", memory: null }`
   - After chatting: `{ status: "ok", memory: { content: "...", ... } }`

---

## Complete Integration Checklist

- [ ] Add TypeScript types/interfaces for memory data
- [ ] Create memory service with API calls
- [ ] Implement memory display component
- [ ] Add error handling and loading states
- [ ] Style the memory panel/badge
- [ ] Implement caching strategy
- [ ] Add memory refresh after chat interactions
- [ ] Test with real user data
- [ ] Add privacy controls (view/clear memory)
- [ ] Document for your team

---

## Troubleshooting

### Memory not showing up?
1. Verify user has had at least one chat conversation
2. Check backend logs for memory extraction
3. Verify the user_id is correct
4. Check network tab for 200 OK response

### Memory not updating?
1. Clear frontend cache
2. Check if memory was actually extracted (backend logs)
3. Verify the update timestamp is changing

### CORS errors?
1. Ensure backend CORS settings allow your frontend origin
2. Check `app/main.py` for CORS configuration

---

## Next Steps

- Integrate memory display into your chat UI
- Add visual indicators when memory is being updated
- Consider adding memory highlights in conversations
- Build admin tools to manage user memories
- Add analytics to track memory usage

---

**Need Help?** Check the backend implementation in:
- `app/api/v1/endpoints.py` (lines 616-728) - Memory endpoints
- `app/db/models.py` (lines 111-123) - UserMemory model
- `app/services/orchestrator.py` - Memory extraction logic

Happy coding! 🚀




