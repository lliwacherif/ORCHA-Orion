# app/api/v1/admin.py
"""
Admin Dashboard API - Secure admin endpoints for user management and statistics.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, List

from app.db.database import get_db
from app.db.models import Admin, User, Conversation, ChatMessage
from app.config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ============================================================================
# Pydantic Models
# ============================================================================

class AdminLogin(BaseModel):
    username: str
    password: str


class AdminCredentialsUpdate(BaseModel):
    current_password: str
    new_username: Optional[str] = None
    new_password: Optional[str] = None


class AdminResponse(BaseModel):
    id: int
    username: str
    created_at: str


class UserStats(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    job_title: Optional[str]
    is_active: bool
    plan_type: str
    created_at: Optional[str]
    conversation_count: int
    message_count: int
    last_activity: Optional[str]


class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_conversations: int
    total_messages: int


class UsersResponse(BaseModel):
    users: List[UserStats]
    stats: DashboardStats


# ============================================================================
# Helper Functions
# ============================================================================

def create_admin_token(admin_id: int, username: str) -> str:
    """Create a JWT token for admin authentication."""
    expire = datetime.utcnow() + timedelta(hours=settings.ADMIN_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(admin_id),
        "username": username,
        "exp": expire,
        "type": "admin"
    }
    return jwt.encode(payload, settings.ADMIN_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Admin:
    """Dependency to verify admin JWT token and return the admin user."""
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.ADMIN_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        admin_id = int(payload.get("sub"))
        
        # Verify this is an admin token
        if payload.get("type") != "admin":
            raise credentials_exception
        
        # Fetch admin from database
        result = await db.execute(select(Admin).where(Admin.id == admin_id))
        admin = result.scalar_one_or_none()
        
        if not admin:
            raise credentials_exception
        
        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account is disabled"
            )
        
        return admin
        
    except JWTError:
        raise credentials_exception


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.post("/login")
async def admin_login(request: AdminLogin, db: AsyncSession = Depends(get_db)):
    """
    Admin login endpoint.
    Returns JWT token for authenticated admin sessions.
    
    Default credentials: admin / admin
    """
    # Find admin by username
    result = await db.execute(select(Admin).where(Admin.username == request.username))
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not pwd_context.verify(request.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if admin is active
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is disabled"
        )
    
    # Create token
    token = create_admin_token(admin.id, admin.username)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "created_at": admin.created_at.isoformat()
        }
    }


@router.get("/me")
async def get_current_admin(admin: Admin = Depends(verify_admin_token)):
    """
    Get current admin information.
    Requires admin authentication.
    """
    return {
        "id": admin.id,
        "username": admin.username,
        "created_at": admin.created_at.isoformat()
    }


@router.get("/users", response_model=UsersResponse)
async def get_all_users(
    admin: Admin = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users with their statistics.
    Returns user list with conversation/message counts and overall dashboard stats.
    """
    # Query users with conversation and message counts using the view
    try:
        result = await db.execute(text("SELECT * FROM admin_user_stats"))
        rows = result.fetchall()
        
        users = []
        for row in rows:
            users.append({
                "id": row.id,
                "username": row.username,
                "email": row.email,
                "full_name": row.full_name,
                "job_title": row.job_title,
                "is_active": row.is_active,
                "plan_type": row.plan_type,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "conversation_count": row.conversation_count or 0,
                "message_count": row.message_count or 0,
                "last_activity": row.last_activity.isoformat() if row.last_activity else None
            })
    except Exception:
        # Fallback if view doesn't exist - use direct query
        users_result = await db.execute(select(User))
        all_users = users_result.scalars().all()
        
        users = []
        for user in all_users:
            # Count conversations
            conv_result = await db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.user_id == user.id)
                .where(Conversation.is_active == True)
            )
            conversation_count = conv_result.scalar() or 0
            
            # Count messages
            msg_result = await db.execute(
                select(func.count(ChatMessage.id))
                .join(Conversation, ChatMessage.conversation_id == Conversation.id)
                .where(Conversation.user_id == user.id)
            )
            message_count = msg_result.scalar() or 0
            
            # Get last activity
            last_activity_result = await db.execute(
                select(func.max(ChatMessage.created_at))
                .join(Conversation, ChatMessage.conversation_id == Conversation.id)
                .where(Conversation.user_id == user.id)
            )
            last_activity = last_activity_result.scalar()
            
            users.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "job_title": user.job_title,
                "is_active": user.is_active,
                "plan_type": user.plan_type,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "conversation_count": conversation_count,
                "message_count": message_count,
                "last_activity": last_activity.isoformat() if last_activity else None
            })
    
    # Get overall stats
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0
    
    total_conversations_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.is_active == True)
    )
    total_conversations = total_conversations_result.scalar() or 0
    
    total_messages_result = await db.execute(select(func.count(ChatMessage.id)))
    total_messages = total_messages_result.scalar() or 0
    
    return {
        "users": users,
        "stats": {
            "total_users": total_users,
            "active_users": active_users,
            "total_conversations": total_conversations,
            "total_messages": total_messages
        }
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: Admin = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user account (soft delete - marks as inactive).
    """
    # Find user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete - mark as inactive
    user.is_active = False
    await db.commit()
    
    return {"status": "ok", "message": "User deleted successfully"}


@router.put("/credentials")
async def update_admin_credentials(
    request: AdminCredentialsUpdate,
    admin: Admin = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Update admin username and/or password.
    Requires current password for verification.
    """
    # Verify current password
    if not pwd_context.verify(request.current_password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update username if provided
    if request.new_username:
        # Check if username is already taken by another admin
        existing = await db.execute(
            select(Admin)
            .where(Admin.username == request.new_username)
            .where(Admin.id != admin.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        admin.username = request.new_username
    
    # Update password if provided
    if request.new_password:
        admin.hashed_password = pwd_context.hash(request.new_password)
    
    await db.commit()
    
    return {"status": "ok", "message": "Credentials updated successfully"}

