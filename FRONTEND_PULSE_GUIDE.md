# Frontend Pulse Integration Guide

## Overview

The **Pulse** feature provides users with an AI-generated daily summary of their conversations. It analyzes the last 10 conversations and extracts:
- 🔹 Main topics and recurring themes
- 📋 Important reminders and tasks
- 💭 Insights and ideas
- 🕒 Overall context and tone

## Backend API Endpoints

### 1. Get User's Pulse
```http
GET /api/v1/pulse/{user_id}
```

**Response:**
```json
{
  "status": "ok",
  "pulse": {
    "content": "🧭 Daily Pulse — 2025-10-27\n🔹 Main Topics:\n- ...",
    "generated_at": "2025-10-27T15:00:00",
    "next_generation": "2025-10-28T15:00:00",
    "conversations_analyzed": 10,
    "messages_analyzed": 45
  }
}
```

### 2. Manually Regenerate Pulse
```http
POST /api/v1/pulse/{user_id}/regenerate
```

**Response:**
```json
{
  "status": "ok",
  "message": "Pulse regenerated successfully",
  "pulse": {
    "content": "...",
    "generated_at": "2025-10-27T15:30:00",
    ...
  }
}
```

## Frontend Implementation

### Step 1: Add Pulse Icon to UI

Add a pulse/activity icon to your navigation or header:

```jsx
// Example with Lucide React icons
import { Activity } from 'lucide-react';

function NavigationBar() {
  const [showPulse, setShowPulse] = useState(false);
  
  return (
    <nav>
      {/* Other nav items */}
      
      {/* Pulse Icon Button */}
      <button 
        onClick={() => setShowPulse(true)}
        className="pulse-button"
        title="View Daily Pulse"
      >
        <Activity className="w-6 h-6" />
        <span className="badge">Pulse</span>
      </button>
    </nav>
  );
}
```

### Step 2: Create Pulse Component

Create a component to fetch and display the pulse:

```jsx
// components/PulseModal.jsx
import { useState, useEffect } from 'react';
import { Activity, X, RefreshCw } from 'lucide-react';

function PulseModal({ userId, isOpen, onClose }) {
  const [pulse, setPulse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  // Fetch pulse when modal opens
  useEffect(() => {
    if (isOpen && userId) {
      fetchPulse();
    }
  }, [isOpen, userId]);

  const fetchPulse = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/pulse/${userId}`);
      const data = await response.json();
      
      if (data.status === 'ok') {
        setPulse(data.pulse);
      } else {
        console.error('Failed to fetch pulse:', data);
      }
    } catch (error) {
      console.error('Error fetching pulse:', error);
    } finally {
      setLoading(false);
    }
  };

  const regeneratePulse = async () => {
    setRegenerating(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/pulse/${userId}/regenerate`,
        { method: 'POST' }
      );
      const data = await response.json();
      
      if (data.status === 'ok') {
        setPulse(data.pulse);
      } else {
        console.error('Failed to regenerate pulse:', data);
      }
    } catch (error) {
      console.error('Error regenerating pulse:', error);
    } finally {
      setRegenerating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="pulse-modal-overlay" onClick={onClose}>
      <div className="pulse-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="pulse-header">
          <div className="pulse-title">
            <Activity className="w-6 h-6" />
            <h2>Your Daily Pulse</h2>
          </div>
          <div className="pulse-actions">
            <button 
              onClick={regeneratePulse} 
              disabled={regenerating}
              title="Regenerate Pulse"
            >
              <RefreshCw className={`w-5 h-5 ${regenerating ? 'animate-spin' : ''}`} />
            </button>
            <button onClick={onClose}>
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="pulse-content">
          {loading ? (
            <div className="pulse-loading">
              <div className="spinner"></div>
              <p>Analyzing your conversations...</p>
            </div>
          ) : pulse ? (
            <>
              <div className="pulse-text">
                {/* Render the pulse content with proper formatting */}
                {pulse.content.split('\n').map((line, idx) => (
                  <p key={idx}>{line}</p>
                ))}
              </div>
              
              <div className="pulse-meta">
                <div className="meta-item">
                  <span className="meta-label">Generated:</span>
                  <span>{new Date(pulse.generated_at).toLocaleString()}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Conversations analyzed:</span>
                  <span>{pulse.conversations_analyzed}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Messages analyzed:</span>
                  <span>{pulse.messages_analyzed}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Next update:</span>
                  <span>{new Date(pulse.next_generation).toLocaleString()}</span>
                </div>
              </div>
            </>
          ) : (
            <p>No pulse data available</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default PulseModal;
```

### Step 3: Add Styling (CSS)

```css
/* PulseModal.css */
.pulse-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.pulse-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.pulse-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.pulse-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pulse-title h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.pulse-actions {
  display: flex;
  gap: 10px;
}

.pulse-actions button {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  color: white;
  transition: background 0.2s;
}

.pulse-actions button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.pulse-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pulse-content {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.pulse-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.pulse-text {
  line-height: 1.8;
  font-size: 15px;
  color: #374151;
}

.pulse-text p {
  margin: 8px 0;
  white-space: pre-wrap;
}

.pulse-meta {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.meta-item span:last-child {
  font-size: 14px;
  color: #111827;
  font-weight: 500;
}

/* Pulse button styling */
.pulse-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: transform 0.2s, box-shadow 0.2s;
}

.pulse-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.pulse-button .badge {
  font-size: 14px;
}
```

### Step 4: Use in Your App

```jsx
// App.jsx or your main component
import { useState } from 'react';
import PulseModal from './components/PulseModal';

function App() {
  const [showPulse, setShowPulse] = useState(false);
  const userId = 1; // Get from your auth context

  return (
    <div className="app">
      {/* Your app content */}
      
      {/* Pulse Modal */}
      <PulseModal
        userId={userId}
        isOpen={showPulse}
        onClose={() => setShowPulse(false)}
      />
      
      {/* Pulse Button */}
      <button 
        className="pulse-button"
        onClick={() => setShowPulse(true)}
      >
        <Activity />
        View Pulse
      </button>
    </div>
  );
}
```

## Quick Start Checklist

- [ ] Run database migration: `python migrate_add_pulse.py`
- [ ] Install Lucide icons: `npm install lucide-react`
- [ ] Create `PulseModal` component
- [ ] Add pulse button to your navigation
- [ ] Test by clicking the pulse icon
- [ ] (Optional) Add notification badge when pulse updates

## Features

### Auto-Generation
- Pulses auto-generate every 24 hours
- First pulse generates when user clicks the icon
- Analyzes last 10 conversations

### Manual Regeneration
- Users can click refresh icon to regenerate
- Useful for getting updated insights during the day

### Smart Content
The AI analyzes conversations for:
- ✅ Key topics and recurring themes
- 📌 Important reminders and tasks
- 💡 Insights and ideas
- 🚫 Filters out small talk

## API Testing

Test the endpoints with cURL:

```bash
# Get pulse
curl http://localhost:8000/api/v1/pulse/1

# Regenerate pulse
curl -X POST http://localhost:8000/api/v1/pulse/1/regenerate
```

## Notes

1. **First Time Use**: When user first clicks pulse, it will generate (may take ~30 seconds)
2. **24-Hour Updates**: Pulses automatically regenerate every 24 hours
3. **Performance**: Analyzing 10 conversations typically takes 30-60 seconds
4. **Storage**: Only one pulse per user (overwrites previous)

## Troubleshooting

**Pulse not generating?**
- Check that LM Studio is running
- Verify user has conversations
- Check server logs for errors

**Takes too long?**
- Reduce conversation limit in `pulse_service.py`
- Increase LLM timeout if needed

**Empty pulse?**
- User may not have enough conversations yet
- System will show "Nothing important for now"
