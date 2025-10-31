# Pulse Feature - Complete Setup Guide

## 🎯 Overview

The **Pulse** feature is an AI-powered daily summary system that analyzes each user's conversations and generates insightful summaries every 24 hours.

### What It Does

- 📊 Analyzes last **10 conversations** per user
- 🤖 Uses LLM to extract key topics, reminders, and insights
- 💾 Stores one pulse per user (overwrites daily)
- ⏰ Auto-regenerates every 24 hours
- 🔄 Manual refresh available anytime

## 📁 Files Created/Modified

### New Files
```
app/
  db/
    models.py                    # ✅ Added Pulse model
  services/
    pulse_service.py             # ✅ NEW - Pulse generation logic
  tasks/
    pulse_scheduler.py           # ✅ NEW - Auto-generation scheduler
  main.py                        # ✅ Modified - Added scheduler startup
  api/v1/endpoints.py            # ✅ Modified - Added pulse endpoints

migrate_add_pulse.py             # ✅ NEW - Database migration
FRONTEND_PULSE_GUIDE.md          # ✅ NEW - Frontend integration
PULSE_FEATURE_SETUP.md           # ✅ NEW - This file
```

## 🔧 Setup Instructions

### Step 1: Run Database Migration

```bash
python migrate_add_pulse.py
```

This creates the `pulses` table in your database.

**Table Schema:**
```sql
CREATE TABLE pulses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    conversations_analyzed INTEGER DEFAULT 0,
    messages_analyzed INTEGER DEFAULT 0,
    next_generation TIMESTAMP NOT NULL
);
```

### Step 2: Restart Your Backend Server

Stop and restart your FastAPI server to load the new code:

```bash
# Stop current server (Ctrl+C)

# Restart
python -m uvicorn app.main:app --reload --port 8000
```

**You should see:**
```
✅ Pulse scheduler started
✅ Pulse checker started
```

### Step 3: Test the API

#### Get Pulse (generates on first access)
```bash
curl http://localhost:8000/api/v1/pulse/1
```

**Expected Response:**
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

#### Manually Regenerate Pulse
```bash
curl -X POST http://localhost:8000/api/v1/pulse/1/regenerate
```

## 🏗️ Architecture

### Database Model (Pulse)

```python
class Pulse(Base):
    id: int                          # Primary key
    user_id: int                     # Foreign key to users (unique)
    content: str                     # AI-generated summary
    generated_at: datetime           # When generated
    conversations_analyzed: int      # Stats
    messages_analyzed: int           # Stats
    next_generation: datetime        # When to regenerate
```

### Relationships
- `User.pulse` → One-to-one with Pulse
- `Pulse.user` → Back reference to User

### Service Functions

```python
# pulse_service.py

async def generate_pulse_for_user(user_id, db_session)
    # Analyzes last 10 conversations
    # Calls LLM with special prompt
    # Returns pulse content string

async def update_user_pulse(user_id, db_session)
    # Generates and saves/updates pulse
    # Returns True/False

async def get_user_pulse(user_id, db_session)
    # Retrieves current pulse
    # Returns dict or None
```

### Scheduler Tasks

```python
# pulse_scheduler.py

async def pulse_scheduler_loop()
    # Runs every 24 hours
    # Generates pulses for ALL users

async def pulse_checker_loop()
    # Runs every hour
    # Catches missed generations
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pulse/{user_id}` | GET | Get current pulse (generates if missing) |
| `/api/v1/pulse/{user_id}/regenerate` | POST | Manually regenerate pulse |

## 🔄 How It Works

### First-Time Generation

1. User clicks Pulse icon in frontend
2. Frontend calls `GET /api/v1/pulse/1`
3. Backend finds no pulse exists
4. Automatically generates pulse (30-60 seconds)
5. Returns generated pulse
6. Saves to database

### Automatic Daily Updates

1. Scheduler runs every 24 hours (background task)
2. Gets all active users
3. For each user:
   - Fetches last 10 conversations
   - Extracts all messages
   - Sends to LLM with prompt
   - Saves/overwrites pulse
4. Sets `next_generation` to +24 hours

### Manual Regeneration

1. User clicks refresh icon
2. Frontend calls `POST /api/v1/pulse/1/regenerate`
3. Backend immediately generates new pulse
4. Overwrites existing pulse
5. Returns updated pulse

## 📝 AI Prompt

The system uses this prompt to generate pulses:

```
Your task is to generate out of all these chats that follows a daily Pulse,
a concise, structured summary that captures only the most relevant and
meaningful information from these chats.

Focus on identifying:
✅ Key topics and recurring themes.
📌 Important reminders, tasks, or follow-ups the user mentioned.
💡 Useful insights, ideas, or decisions made.
🚫 Ignore irrelevant small talk or casual conversations.

Output format:
🧭 Daily Pulse — [Date]
🔹 Main Topics:
- ...
📋 Important Actions / Reminders:
- ...
💭 Insights & Ideas:
- ...
🕒 Summary Context:
(Brief sentence describing the overall tone or focus of the user's day)

If you think that there is nothing important you just answer by
"Nothing important for now."
```

## 🎨 Frontend Integration

See `FRONTEND_PULSE_GUIDE.md` for complete React implementation with:
- Pulse icon component
- Modal with pulse display
- Refresh functionality
- Styling examples

**Quick Example:**
```jsx
import { Activity } from 'lucide-react';

<button onClick={() => fetchPulse(userId)}>
  <Activity /> View Pulse
</button>
```

## ⚙️ Configuration

### Scheduler Timing

Edit `app/tasks/pulse_scheduler.py` to change timing:

```python
# Generate every 12 hours instead of 24
await asyncio.sleep(12 * 60 * 60)

# Check every 30 minutes instead of 1 hour
await asyncio.sleep(30 * 60)
```

### Conversation Limit

Edit `app/services/pulse_service.py` to analyze more/fewer conversations:

```python
# Analyze last 20 conversations instead of 10
.limit(20)
```

### LLM Timeout

Edit `app/services/pulse_service.py`:

```python
# Increase timeout to 3 minutes
response = await call_lmstudio_chat(messages, timeout=180)
```

## 🐛 Troubleshooting

### Pulse Not Generating

**Check:**
1. LM Studio is running: `http://192.168.1.37:1234`
2. User has conversations: `SELECT * FROM conversations WHERE user_id = 1`
3. Database migration ran: `SELECT * FROM pulses`
4. Server logs for errors

**Debug Command:**
```python
# In Python shell
from app.db.database import AsyncSessionLocal
from app.services.pulse_service import update_user_pulse

async def test():
    async with AsyncSessionLocal() as db:
        result = await update_user_pulse(1, db)
        print(f"Result: {result}")

import asyncio
asyncio.run(test())
```

### Scheduler Not Running

Check server startup logs:
```
✅ Pulse scheduler started  # Should see this
✅ Pulse checker started    # Should see this
```

If not shown, check `app/main.py` imports.

### Generation Takes Too Long

Reduce analyzed conversations or increase timeout:
```python
# pulse_service.py
.limit(5)  # Analyze only 5 conversations
timeout=180  # 3 minutes timeout
```

### Empty Pulse Content

User might not have enough conversation data yet:
- Check conversation count
- Verify messages exist
- Try manual regeneration

## 📊 Monitoring

### Check Pulse Status

```python
from app.db.database import AsyncSessionLocal
from sqlalchemy import select
from app.db.models import Pulse

async def check_pulses():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Pulse))
        pulses = result.scalars().all()
        for p in pulses:
            print(f"User {p.user_id}: {p.generated_at}, next: {p.next_generation}")

import asyncio
asyncio.run(check_pulses())
```

### View Logs

```bash
# Server logs show pulse generation
🔄 Generating pulse for user 1
Found 10 conversations for user 1
Analyzing 45 messages from 10 conversations
✅ Pulse generated successfully (1234 chars)
💾 Pulse saved for user 1. Next generation at 2025-10-28 15:00:00
```

## 🚀 Production Considerations

### 1. Performance

- Consider using Celery/Redis for background tasks
- Cache pulse data if accessed frequently
- Limit conversation analysis per user

### 2. Scaling

- Run scheduler on dedicated worker
- Use message queue for pulse generation
- Database indexes on `user_id` and `next_generation`

### 3. Monitoring

- Track generation failures
- Alert on long generation times
- Monitor LLM API availability

### 4. User Experience

- Show loading state during generation
- Display progress indicator
- Cache frontend pulse data

## ✅ Success Checklist

- [ ] Database migration completed
- [ ] Server restarted with scheduler running
- [ ] API endpoints accessible
- [ ] First pulse generated successfully
- [ ] Frontend pulse icon added
- [ ] Modal displays pulse correctly
- [ ] Refresh button works
- [ ] Scheduler logs showing 24h countdown

## 🎉 Feature Complete!

You now have a fully functional Pulse system that:
- ✅ Auto-generates daily summaries
- ✅ Analyzes conversations intelligently
- ✅ Stores per-user insights
- ✅ Provides REST API access
- ✅ Includes frontend integration
- ✅ Runs background scheduler

**Next Steps:**
- Integrate with frontend UI
- Customize pulse prompt for your needs
- Add user notifications for new pulses
- Enhance with more analytics
