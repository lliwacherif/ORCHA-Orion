# Authentication & Token Tracking Setup Guide

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database
```bash
python app/db/init_db.py
```

This will:
- Create the `orcha_db` database
- Create `users` table
- Create `token_usage` table

### Step 3: Start Server
```bash
uvicorn app.main:app --reload
```

---

## 📋 API Endpoints

### Authentication Endpoints

#### 1. Register New User
**POST** `/api/v1/auth/register`

```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "plan_type": "free",
    "created_at": "2025-10-22T..."
  }
}
```

#### 2. Login
**POST** `/api/v1/auth/login`

```json
{
  "username": "john_doe",
  "password": "password123"
}
```

**Response:** Same as register

#### 3. Get Current User
**GET** `/api/v1/auth/me`

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "plan_type": "free",
  "created_at": "2025-10-22T..."
}
```

---

### Chat with Token Tracking

**POST** `/api/v1/orcha/chat`

```json
{
  "user_id": 1,
  "message": "Hello!",
  "use_rag": false
}
```

**Note:** `user_id` is now an **integer** (from users table), not a string.

**Response:**
```json
{
  "status": "ok",
  "message": "Hello! How can I help you?",
  "token_usage": {
    "current_usage": 245,
    "tokens_added": 245,
    "reset_at": "2025-10-23T14:30:00",
    "tracking_enabled": true
  }
}
```

---

### Token Usage Endpoints

#### Get Usage
**GET** `/api/v1/tokens/usage/{user_id}`

```
GET /api/v1/tokens/usage/1
```

#### Reset Usage (Admin)
**POST** `/api/v1/tokens/reset/{user_id}`

```
POST /api/v1/tokens/reset/1
```

---

## 🔐 Frontend Integration

### 1. Register/Login Flow

```javascript
// Register
const response = await fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'john_doe',
    email: 'john@example.com',
    password: 'password123',
    full_name: 'John Doe'
  })
});

const data = await response.json();
// Save token to localStorage
localStorage.setItem('token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

### 2. Use Token in Requests

```javascript
// Get current user
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/api/v1/auth/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const user = await response.json();
```

### 3. Send Chat with User ID

```javascript
const user = JSON.parse(localStorage.getItem('user'));

const response = await fetch('http://localhost:8000/api/v1/orcha/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: user.id,  // ← Use numeric user ID from login
    message: 'Hello!',
    use_rag: false
  })
});

const data = await response.json();
console.log('Token usage:', data.token_usage);
```

---

## 📊 Database Schema

### Users Table
```sql
- id (INTEGER, PRIMARY KEY)
- username (VARCHAR(50), UNIQUE)
- email (VARCHAR(100), UNIQUE)
- hashed_password (VARCHAR(255))
- full_name (VARCHAR(100))
- is_active (BOOLEAN, default TRUE)
- is_superuser (BOOLEAN, default FALSE)
- plan_type (VARCHAR(20), default 'free')
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

### Token Usage Table
```sql
- user_id (INTEGER, PRIMARY KEY, references users.id)
- total_tokens (BIGINT)
- reset_at (TIMESTAMP)
- last_updated (TIMESTAMP)
```

---

## 🧪 Testing

### Test with curl

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@test.com", "password": "test123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123"}'

# Get current user (use token from login)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Send chat
curl -X POST http://localhost:8000/api/v1/orcha/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "message": "Hello!", "use_rag": false}'
```

---

## ⚙️ Configuration

Edit `app/config.py` or create `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:1234@localhost:5432/orcha_db
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24
```

---

## 🔧 Troubleshooting

### Database connection error?
- Make sure PostgreSQL 17 is running
- Check password is correct in config
- Run `python app/db/init_db.py` to create database

### Import errors?
- Run `pip install -r requirements.txt` again

### Token not working?
- Check token is in `Authorization: Bearer {token}` header
- Check token hasn't expired (24 hours)
- Re-login to get fresh token

---

## 📝 Important Notes

1. **User ID is now INTEGER** - Changed from string to integer (database primary key)
2. **Token tracking uses PostgreSQL** - No Redis needed anymore
3. **JWT tokens expire in 24 hours** - Configurable in settings
4. **Passwords are hashed** - Never stored in plain text
5. **24-hour rolling window** - Token usage resets 24h after first use

---

## 🎯 Next Steps

1. ✅ Initialize database
2. ✅ Test register/login
3. ✅ Update frontend to use JWT tokens
4. ✅ Use numeric user_id in chat requests
5. ✅ Display token usage in UI






