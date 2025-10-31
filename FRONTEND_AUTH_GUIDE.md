# Frontend Authentication Guide

Complete guide for implementing user registration, login, and session management.

---

## 🔑 Overview

Your backend now supports:
- ✅ User registration
- ✅ User login with JWT tokens
- ✅ Authenticated sessions
- ✅ User profiles

---

## 📋 API Endpoints

### 1. Register New User
**POST** `/api/v1/auth/register`

**Request:**
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
    "created_at": "2025-10-22T14:30:00"
  }
}
```

### 2. Login
**POST** `/api/v1/auth/login`

**Request:**
```json
{
  "username": "john_doe",
  "password": "password123"
}
```

**Response:** Same as registration

### 3. Get Current User
**GET** `/api/v1/auth/me`

**Headers:** `Authorization: Bearer {your_token}`

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "plan_type": "free",
  "created_at": "2025-10-22T14:30:00"
}
```

---

## 🎨 React Implementation

### Complete Authentication Context

```jsx
// contexts/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_BASE = 'http://localhost:8000/api/v1';

  // Load user from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  // Register new user
  const register = async (username, email, password, fullName = '') => {
    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          email,
          password,
          full_name: fullName
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }

      const data = await response.json();
      
      // Save to state and localStorage
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      return { success: true, user: data.user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  // Login existing user
  const login = async (username, password) => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      
      // Save to state and localStorage
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      return { success: true, user: data.user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  // Logout
  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  // Refresh user data
  const refreshUser = async () => {
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to refresh user');

      const userData = await response.json();
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (error) {
      console.error('Failed to refresh user:', error);
      logout(); // Token might be expired
    }
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token,
    register,
    login,
    logout,
    refreshUser
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Wrap Your App

```jsx
// App.jsx
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <AuthProvider>
      <YourAppContent />
    </AuthProvider>
  );
}
```

---

## 📝 Registration Form

```jsx
// components/RegisterForm.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

function RegisterForm() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    fullName: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await register(
      formData.username,
      formData.email,
      formData.password,
      formData.fullName
    );

    setLoading(false);

    if (result.success) {
      navigate('/dashboard'); // Redirect after successful registration
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="register-form">
      <h2>Create Account</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
            minLength={3}
            placeholder="Choose a username"
          />
        </div>

        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            placeholder="your@email.com"
          />
        </div>

        <div className="form-group">
          <label>Full Name</label>
          <input
            type="text"
            name="fullName"
            value={formData.fullName}
            onChange={handleChange}
            placeholder="John Doe (optional)"
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={6}
            placeholder="At least 6 characters"
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Creating account...' : 'Register'}
        </button>
      </form>

      <p className="form-footer">
        Already have an account? <a href="/login">Login here</a>
      </p>
    </div>
  );
}

export default RegisterForm;
```

---

## 🔐 Login Form

```jsx
// components/LoginForm.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password);

    setLoading(false);

    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="login-form">
      <h2>Welcome Back</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            placeholder="Enter your username"
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="Enter your password"
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>

      <p className="form-footer">
        Don't have an account? <a href="/register">Register here</a>
      </p>
    </div>
  );
}

export default LoginForm;
```

---

## 👤 User Profile Display

```jsx
// components/UserProfile.jsx
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

function UserProfile() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="user-profile">
      <div className="profile-header">
        <div className="avatar">
          {user.full_name ? user.full_name.charAt(0) : user.username.charAt(0)}
        </div>
        <div className="user-info">
          <h3>{user.full_name || user.username}</h3>
          <p className="username">@{user.username}</p>
          <p className="email">{user.email}</p>
          <span className="plan-badge">{user.plan_type}</span>
        </div>
      </div>

      <div className="profile-stats">
        <div className="stat">
          <span className="label">Member Since</span>
          <span className="value">
            {new Date(user.created_at).toLocaleDateString()}
          </span>
        </div>
        <div className="stat">
          <span className="label">Status</span>
          <span className="value">
            {user.is_active ? '✅ Active' : '❌ Inactive'}
          </span>
        </div>
      </div>

      <button onClick={logout} className="logout-button">
        Logout
      </button>
    </div>
  );
}

export default UserProfile;
```

---

## 🔒 Protected Route Component

```jsx
// components/ProtectedRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
```

**Usage:**
```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
```

---

## 💬 Using Chat with Authenticated User

```jsx
// components/ChatInterface.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

function ChatInterface() {
  const { user, token } = useAuth();
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim() || !user) return;

    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/orcha/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Optional: include token if you want server-side auth check
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: user.id,  // ← Use numeric user ID
          message: message,
          use_rag: false,
          conversation_history: messages.slice(-4)
        })
      });

      const data = await response.json();

      if (data.status === 'ok') {
        setMessages([
          ...messages,
          { role: 'user', content: message },
          { role: 'assistant', content: data.message }
        ]);

        // Display token usage if available
        if (data.token_usage) {
          console.log('Tokens used:', data.token_usage);
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
    }

    setLoading(false);
    setMessage('');
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>

      <div className="input-area">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
```

---

## 🎨 CSS Styles

```css
/* Auth Forms */
.register-form, .login-form {
  max-width: 400px;
  margin: 50px auto;
  padding: 30px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.register-form h2, .login-form h2 {
  margin-bottom: 20px;
  text-align: center;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #555;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

button[type="submit"] {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

button[type="submit"]:hover {
  transform: translateY(-2px);
}

button[type="submit"]:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 10px;
  border-radius: 5px;
  margin-bottom: 15px;
  text-align: center;
}

.form-footer {
  margin-top: 20px;
  text-align: center;
  color: #666;
}

.form-footer a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

/* User Profile */
.user-profile {
  max-width: 500px;
  margin: 30px auto;
  padding: 30px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.profile-header {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 32px;
  font-weight: bold;
}

.user-info h3 {
  margin: 0 0 5px 0;
  color: #333;
}

.username {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.email {
  margin: 5px 0;
  color: #888;
  font-size: 14px;
}

.plan-badge {
  display: inline-block;
  padding: 4px 12px;
  background: #e0e7ff;
  color: #4c51bf;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.profile-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.stat {
  text-align: center;
  padding: 15px;
  background: #f7fafc;
  border-radius: 8px;
}

.stat .label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.stat .value {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.logout-button {
  width: 100%;
  padding: 12px;
  background: #f56565;
  color: white;
  border: none;
  border-radius: 5px;
  font-weight: 600;
  cursor: pointer;
}

.logout-button:hover {
  background: #e53e3e;
}
```

---

## 🔄 Complete Authentication Flow

```
1. User visits site
   ↓
2. Click "Register" or "Login"
   ↓
3. Fill form and submit
   ↓
4. Backend validates and returns JWT token + user data
   ↓
5. Frontend saves token and user to localStorage
   ↓
6. User is redirected to dashboard
   ↓
7. All chat requests use user.id (numeric)
   ↓
8. Token is sent with authenticated requests
```

---

## ✅ Checklist

- [ ] Install AuthContext in your app
- [ ] Create Register page
- [ ] Create Login page
- [ ] Create User Profile component
- [ ] Add ProtectedRoute wrapper
- [ ] Update chat to use `user.id` (number)
- [ ] Test registration flow
- [ ] Test login flow
- [ ] Test token persistence (refresh page)
- [ ] Test logout

---

## 🧪 Testing

```javascript
// Test registration
const result = await register('testuser', 'test@test.com', 'password123', 'Test User');
console.log(result); // { success: true, user: {...} }

// Test login
const loginResult = await login('testuser', 'password123');
console.log(loginResult); // { success: true, user: {...} }

// Check current user
console.log(user); // { id: 1, username: 'testuser', ... }

// Use in chat
sendChat(user.id, 'Hello!'); // user.id is a number
```

---

## 📝 Important Notes

1. **User ID is numeric** - Use `user.id` (not username) for chat requests
2. **Token expires in 24 hours** - Users need to re-login after that
3. **Token stored in localStorage** - Persists across page refreshes
4. **Logout clears everything** - Removes token and user data
5. **Protected routes** - Redirect to login if not authenticated

---

Happy coding! 🚀






