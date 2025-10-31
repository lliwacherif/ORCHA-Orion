# ORCHA Setup Instructions

## ✅ What Was Implemented

1. **User Authentication System** (Register/Login with JWT)
2. **Token Usage Tracking** (PostgreSQL-based, 24-hour rolling window)
3. **Database Models** (Users + TokenUsage tables)
4. **Complete API Endpoints** (Auth + Chat + Token tracking)

---

## 🚀 Setup Steps

### 1. Install New Dependencies
```powershell
pip install -r requirements.txt
```

This installs:
- `passlib[bcrypt]` - Password hashing
- `python-jose[cryptography]` - JWT tokens
- `python-multipart` - Form data support

### 2. Initialize Database
```powershell
python init_database.py
```

**Or use:**
```powershell
python -m app.db.init_db
```

**What this does:**
- Creates `orcha_db` database
- Creates `users` table
- Creates `token_usage` table

**Expected output:**
```
🔧 Initializing database...
✅ Database 'orcha_db' created successfully!
✅ All tables created successfully!
✅ Database initialization complete!
```

### 3. Start the Server
```powershell
uvicorn app.main:app --reload
```

Server will start on: `http://localhost:8000`

### 4. Verify Setup
Open your browser: `http://localhost:8000/docs`

You should see new endpoints:
- `/api/v1/auth/register`
- `/api/v1/auth/login`
- `/api/v1/auth/me`
- `/api/v1/orcha/chat` (updated with PostgreSQL tracking)
- `/api/v1/tokens/usage/{user_id}`

---

## 🧪 Quick Test

### Test in PowerShell:

```powershell
# 1. Register a user
$registerBody = @{
    username = "testuser"
    email = "test@test.com"
    password = "password123"
    full_name = "Test User"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" -Method Post -Body $registerBody -ContentType "application/json"

# Save token
$token = $response.access_token
$userId = $response.user.id

Write-Host "User ID: $userId"
Write-Host "Token: $token"

# 2. Send a chat message
$chatBody = @{
    user_id = $userId
    message = "Hello, this is a test!"
    use_rag = $false
} | ConvertTo-Json

$chatResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/orcha/chat" -Method Post -Body $chatBody -ContentType "application/json"

Write-Host "Token Usage:"
$chatResponse.token_usage | ConvertTo-Json

# 3. Check token usage
$usageResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tokens/usage/$userId" -Method Get

Write-Host "Current Usage:"
$usageResponse | ConvertTo-Json
```

---

## 📋 Important Changes

### 1. **user_id is now INTEGER**
**Before:** `"user_id": "user123"` (string)  
**Now:** `"user_id": 1` (integer from database)

### 2. **No More Redis Required**
Token tracking now uses PostgreSQL instead of Redis.

### 3. **Authentication Available**
Frontend can now:
- Register users
- Login users
- Get user profile
- Use JWT tokens for authenticated requests

---

## 📁 New Files Created

```
app/
├── api/v1/
│   └── auth.py                    # Auth endpoints (register, login, me)
├── db/
│   ├── models.py                  # Database models (User, TokenUsage)
│   ├── database.py                # Database connection
│   └── init_db.py                 # Database initialization script
├── utils/
│   ├── auth.py                    # Auth utilities (JWT, password hashing)
│   └── token_tracker_pg.py        # PostgreSQL token tracker
└── config.py                      # Updated with JWT settings

AUTH_SETUP_GUIDE.md                # Complete API documentation
SETUP_INSTRUCTIONS.md              # This file
```

---

## 🔧 Configuration

Current settings in `app/config.py`:

```python
DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/orcha_db"
JWT_SECRET_KEY = "your-secret-key-change-in-production-min-32-chars"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
```

**⚠️ IMPORTANT:** Change `JWT_SECRET_KEY` in production!

---

## 📖 Documentation

See `AUTH_SETUP_GUIDE.md` for:
- Complete API reference
- Frontend integration examples
- Testing examples
- Troubleshooting

---

## ✅ Next Steps for Frontend

1. Update chat requests to use numeric `user_id`
2. Implement register/login UI
3. Store JWT token in localStorage
4. Send token in Authorization header for protected routes
5. Display token usage in user dashboard

---

## 🎯 Summary

**You now have:**
✅ Full user authentication (register, login, JWT)  
✅ User profiles stored in PostgreSQL  
✅ Token tracking in PostgreSQL (no Redis needed)  
✅ 24-hour rolling token usage limits  
✅ Complete API documentation  

**Ready to use!** Just run the 3 setup steps above! 🚀

