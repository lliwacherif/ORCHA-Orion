# app/db/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey, JSON, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model for authentication and profiles."""
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "job_title IN ('Doctor','Lawyer','Engineer','Accountant')",
            name="ck_users_job_title_valid",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Optional: plan type for token limits
    plan_type = Column(String(20), default="free", nullable=False)  # free, pro, enterprise
    job_title = Column(String(50), nullable=False, server_default="Engineer")

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="user", cascade="all, delete-orphan")
    pulse = relationship("Pulse", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class TokenUsage(Base):
    """Token usage tracking for users (24-hour rolling window)."""
    __tablename__ = "token_usage"

    user_id = Column(Integer, primary_key=True, index=True)
    total_tokens = Column(BigInteger, default=0, nullable=False)
    reset_at = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TokenUsage(user_id={self.user_id}, total_tokens={self.total_tokens}, reset_at='{self.reset_at}')>"


class Conversation(Base):
    """Conversation model to group related chat messages."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=True)  # Auto-generated or user-set title
    tenant_id = Column(String(100), nullable=True, index=True)  # For multi-tenant support
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)  # Soft delete support
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    folder = relationship("Folder", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


class ChatMessage(Base):
    """Individual chat messages within conversations."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    attachments = Column(JSON, nullable=True)  # Store attachment metadata as JSON
    token_count = Column(Integer, nullable=True)  # Track token usage per message
    model_used = Column(String(100), nullable=True)  # Track which model was used
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Optional metadata for debugging/analytics
    processing_time_ms = Column(Integer, nullable=True)  # How long the request took
    error_message = Column(Text, nullable=True)  # Store error details if any
    rag_contexts_used = Column(JSON, nullable=True)  # Store RAG contexts that were used

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"


class Pulse(Base):
    """Daily Pulse - AI-generated summary of user's conversations and activities."""
    __tablename__ = "pulses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)  # The AI-generated pulse summary
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # When this pulse was generated
    conversations_analyzed = Column(Integer, default=0, nullable=False)  # How many conversations were analyzed
    messages_analyzed = Column(Integer, default=0, nullable=False)  # Total messages analyzed
    next_generation = Column(DateTime, nullable=False)  # When the next pulse should be generated
    
    # Relationships
    user = relationship("User", back_populates="pulse")

    def __repr__(self):
        return f"<Pulse(id={self.id}, user_id={self.user_id}, generated_at='{self.generated_at}')>"


class UserMemory(Base):
    """User Memory - AI-extracted personal information and preferences stored for context.
    Supports multiple memories per user for complete history tracking."""
    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Removed unique constraint
    content = Column(Text, nullable=False)  # The extracted memory content
    title = Column(String(200), nullable=True)  # Optional title/summary
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)  # Link to source conversation
    source = Column(String(50), default="manual", nullable=False)  # manual, auto_extraction, import, etc.
    tags = Column(JSON, nullable=True)  # Categorization tags (e.g., ["preferences", "personal"])
    is_active = Column(Boolean, default=True, nullable=False)  # Soft delete support
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
    conversation = relationship("Conversation")

    def __repr__(self):
        return f"<UserMemory(id={self.id}, user_id={self.user_id}, title='{self.title}', created_at='{self.created_at}')>"


class Folder(Base):
    """Folder model for organizing conversations."""
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="folders")
    conversations = relationship("Conversation", back_populates="folder")

    def __repr__(self):
        return f"<Folder(id={self.id}, user_id={self.user_id}, name='{self.name}')>"

#This solution is designed totally by Liwa Cherif, an advanced AI solution
#You won't be able to understand it.
