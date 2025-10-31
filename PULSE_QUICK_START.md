# Pulse Feature - Quick Start

## 🎯 What is Pulse?

**Daily AI-powered summary** of each user's conversations. Analyzes the last 10 conversations every 24 hours to extract:
- 🔹 Main topics
- 📋 Important reminders  
- 💡 Insights and ideas
- 🕒 Overall context

## 🚀 Quick Setup (5 Minutes)

### Backend

```bash
# 1. Run database migration
python migrate_add_pulse.py

# 2. Restart server
python -m uvicorn app.main:app --reload --port 8000

# 3. Test it works
curl http://localhost:8000/api/v1/pulse/1
```

### Frontend

```jsx
// 1. Add pulse icon to navigation
import { Activity } from 'lucide-react';

<button onClick={() => setShowPulse(true)}>
  <Activity /> Pulse
</button>

// 2. Fetch pulse when clicked
const fetchPulse = async () => {
  const response = await fetch(`/api/v1/pulse/${userId}`);
  const data = await response.json();
  setPulse(data.pulse.content);
};

// 3. Display in modal/panel
<div className="pulse-display">
  {pulse.split('\n').map(line => <p>{line}</p>)}
</div>
```

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/pulse/{user_id}` | Get current pulse (auto-generates if missing) |
| `POST /api/v1/pulse/{user_id}/regenerate` | Force regenerate pulse |

## 📁 Files Modified/Created

### Created
- `app/services/pulse_service.py` - Generation logic
- `app/tasks/pulse_scheduler.py` - Auto-scheduler
- `migrate_add_pulse.py` - Database setup
- `FRONTEND_PULSE_GUIDE.md` - React examples

### Modified  
- `app/db/models.py` - Added Pulse model
- `app/api/v1/endpoints.py` - Added 2 endpoints
- `app/main.py` - Integrated scheduler

## 🔄 How It Works

1. **First Access**: User clicks pulse icon → Auto-generates (30-60s)
2. **Auto-Update**: Scheduler regenerates every 24 hours
3. **Manual Refresh**: User can force regenerate anytime
4. **Storage**: One pulse per user (overwrites daily)

## 📋 Complete Guides

- **Backend Setup**: See `PULSE_FEATURE_SETUP.md`
- **Frontend Integration**: See `FRONTEND_PULSE_GUIDE.md`

## ✅ Verify It Works

```bash
# 1. Check scheduler started
# Look for these in server logs:
✅ Pulse scheduler started
✅ Pulse checker started

# 2. Generate first pulse
curl http://localhost:8000/api/v1/pulse/1

# 3. Check database
SELECT * FROM pulses WHERE user_id = 1;

# 4. View in frontend
Click Pulse icon → Should see AI summary
```

## 🎨 Example Pulse Output

```
🧭 Daily Pulse — 2025-10-27

🔹 Main Topics:
- Insurance claim processing discussions
- Document analysis workflows
- Health data privacy concerns

📋 Important Actions / Reminders:
- Follow up on pending claim #1234
- Review updated compliance guidelines
- Schedule team meeting for Friday

💭 Insights & Ideas:
- User exploring automated document classification
- Interest in improving claim processing speed
- Focus on HIPAA compliance requirements

🕒 Summary Context:
User's day focused on insurance operations with emphasis on
efficiency and regulatory compliance.
```

## 🐛 Common Issues

**Pulse not generating?**
- Check LM Studio is running
- Verify user has conversations
- Look at server logs for errors

**Takes too long?**
- Reduce from 10 to 5 conversations in `pulse_service.py`
- Increase timeout from 120 to 180 seconds

**Scheduler not running?**
- Restart server
- Check `main.py` imports are correct
- Look for "Pulse scheduler started" in logs

## 🎉 Done!

Your Pulse feature is now ready. Each user gets personalized daily insights automatically!
