# app/api/v1/endpoints.py
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Union
from app.services.orchestrator import (
    handle_chat_request,
    handle_ocr_request,
    handle_ocr_extract,
    handle_rag_query,
    handle_ingest_request,
    handle_predict_request,
)
from app.services.chatbot_client import get_available_models
from app.utils.token_tracker_pg import PostgreSQLTokenTracker
from app.services.pulse_service import get_user_pulse, update_user_pulse
from app.db.database import get_db
from app.db.models import User, Conversation, ChatMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

router = APIRouter()

class Attachment(BaseModel):
    uri: str
    type: Optional[str] = None
    filename: Optional[str] = None
    data: Optional[str] = None  # Base64 encoded file content
    size: Optional[int] = None

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    message: str
    attachments: Optional[List[Attachment]] = Field(default_factory=list)
    use_rag: Optional[bool] = False
    conversation_history: Optional[List[Message]] = Field(default_factory=list)
    conversation_id: Optional[int] = None  # New: Link to existing conversation

class OCRRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    file_uri: str
    mode: Optional[str] = "auto"

class OCRExtractRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    image_data: str  # Base64 encoded image
    filename: Optional[str] = "image"
    language: Optional[str] = "en"  # en, fr, ar, ch, etc.

class RAGQuery(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    query: str
    k: Optional[int] = 8
    rerank: Optional[bool] = True

class IngestRequest(BaseModel):
    source: str
    uri: str
    metadata: Optional[dict] = None

class PredictRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    features: dict

class RouteRequest(BaseModel):
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    message: Optional[str] = ""
    attachments: Optional[List[Attachment]] = Field(default_factory=list)
    use_rag: Optional[bool] = False

class RouteDecision(BaseModel):
    endpoint: str
    reason: str
    prepared_payload: dict

# New models for conversation management
class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int

class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: int
    role: str
    content: str
    attachments: Optional[Any] = None  # Can be list, dict, or None (JSON field)
    token_count: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime

class ConversationDetailResponse(BaseModel):
    id: int
    title: Optional[str]
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse]

class CreateConversationRequest(BaseModel):
    user_id: int
    title: Optional[str] = None
    tenant_id: Optional[str] = None

class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None

@router.post("/orcha/route")
async def orcha_route(req: RouteRequest, request: Request) -> RouteDecision:
    """Return which endpoint to call next based on message/attachments.

    Heuristics:
    - If attachments present or message hints OCR -> suggest /orcha/ocr
    - If message hints ingest -> suggest /orcha/ingest (requires source/uri)
    - If message hints RAG/search -> suggest /orcha/rag/query
    - Else default to /orcha/chat
    """
    text = (req.message or "").lower()
    has_attachments = bool(req.attachments)

    def serialize_attachments():
        return [a.dict() for a in (req.attachments or [])]

    if has_attachments or any(k in text for k in ["scan", "ocr", "extract text", "read file"]):
        payload = {
            "user_id": req.user_id or "anonymous",
            "tenant_id": req.tenant_id,
            "file_uri": (req.attachments[0].uri if has_attachments else ""),
            "mode": "auto",
        }
        return RouteDecision(endpoint="/api/v1/orcha/ocr", reason="attachments or OCR intent detected", prepared_payload=payload)

    if any(k in text for k in ["ingest", "index", "add document", "load dataset"]):
        payload = {
            "source": "user",
            "uri": "",  # caller should fill
            "metadata": {"requested_by": req.user_id or "anonymous"},
        }
        return RouteDecision(endpoint="/api/v1/orcha/ingest", reason="ingest intent detected", prepared_payload=payload)

    if req.use_rag or any(k in text for k in ["rag", "search", "retrieve", "context"]):
        payload = {
            "user_id": req.user_id or "anonymous",
            "tenant_id": req.tenant_id,
            "query": req.message or "",
            "k": 8,
            "rerank": True,
        }
        return RouteDecision(endpoint="/api/v1/orcha/rag/query", reason="RAG intent detected", prepared_payload=payload)

    # default: chat
    payload = {
        "user_id": req.user_id or "anonymous",
        "tenant_id": req.tenant_id,
        "message": req.message or "",
        "attachments": serialize_attachments(),
        "use_rag": req.use_rag,
    }
    return RouteDecision(endpoint="/api/v1/orcha/chat", reason="default to chat", prepared_payload=payload)

@router.post("/orcha/chat")
async def orcha_chat(req: ChatRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Attach database session to request state for orchestrator
    request.state.db_session = db
    result = await handle_chat_request(req.dict(), request)
    return result

@router.post("/orcha/ocr")
async def orcha_ocr(req: OCRRequest, request: Request):
    result = await handle_ocr_request(req.dict(), request)
    return result

@router.post("/orcha/ocr/extract")
async def orcha_ocr_extract(req: OCRExtractRequest, request: Request):
    """
    Extract text from image using OCR.
    Accepts base64 encoded image data and returns extracted text immediately.
    
    Request:
    {
        "user_id": "user123",
        "image_data": "base64EncodedImageString",
        "filename": "document.jpg",
        "language": "en"  // en, fr, ar, ch, es, de, it, pt, ru, ja, ko
    }
    
    Response:
    {
        "status": "success",
        "extracted_text": "Text extracted from image",
        "lines_count": 15,
        "message": "Text extracted successfully",
        "filename": "document.jpg",
        "language": "en"
    }
    """
    result = await handle_ocr_extract(req.dict(), request)
    return result

@router.post("/orcha/rag/query")
async def orcha_rag_query(req: RAGQuery, request: Request):
    result = await handle_rag_query(req.dict(), request)
    return result

@router.post("/orcha/ingest")
async def orcha_ingest(req: IngestRequest, request: Request):
    result = await handle_ingest_request(req.dict(), request)
    return result

@router.post("/orcha/predict")
async def orcha_predict(req: PredictRequest, request: Request):
    result = await handle_predict_request(req.dict(), request)
    return result

@router.get("/models")
async def list_models():
    """Get available models from LM Studio."""
    try:
        models = await get_available_models()
        return {"status": "ok", "models": models}
    except Exception as e:
        return {"status": "error", "error": str(e), "models": None}

@router.get("/tokens/usage/{user_id}")
async def get_token_usage(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get current token usage for a user (24-hour window)."""
    try:
        tracker = PostgreSQLTokenTracker(db)
        usage_info = await tracker.get_usage(user_id)
        
        return {
            "status": "ok",
            "user_id": user_id,
            **usage_info
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/tokens/reset/{user_id}")
async def reset_token_usage(user_id: int, db: AsyncSession = Depends(get_db)):
    """Manually reset token usage for a user (admin function)."""
    try:
        tracker = PostgreSQLTokenTracker(db)
        success = await tracker.reset_user(user_id)
        
        if success:
            return {
                "status": "ok",
                "message": f"Token usage reset for user {user_id}"
            }
        else:
            return {
                "status": "error",
                "error": "Failed to reset token usage"
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ===== CONVERSATION MANAGEMENT ENDPOINTS =====

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    req: CreateConversationRequest, 
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation for a user."""
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == req.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create conversation
        conversation = Conversation(
            user_id=req.user_id,
            title=req.title,
            tenant_id=req.tenant_id
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            tenant_id=conversation.tenant_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{user_id}", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: int, 
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations for a user."""
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get conversations with message count
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.is_active == True)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        conversations = result.scalars().all()
        
        # Get message counts for each conversation
        conversation_responses = []
        for conv in conversations:
            message_count_result = await db.execute(
                select(ChatMessage).where(ChatMessage.conversation_id == conv.id)
            )
            message_count = len(message_count_result.scalars().all())
            
            conversation_responses.append(ConversationResponse(
                id=conv.id,
                title=conv.title,
                tenant_id=conv.tenant_id,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=message_count
            ))
        
        return conversation_responses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{user_id}/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    user_id: int,
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed conversation with all messages."""
    import traceback
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get conversation
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_active == True
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        messages_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at)
        )
        messages = messages_result.scalars().all()
        
        message_responses = []
        for msg in messages:
            try:
                message_responses.append(ChatMessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    attachments=msg.attachments,
                    token_count=msg.token_count,
                    model_used=msg.model_used,
                    created_at=msg.created_at
                ))
            except Exception as msg_error:
                print(f"❌ Error serializing message {msg.id}: {msg_error}")
                print(f"   Message data: id={msg.id}, role={msg.role}, attachments type={type(msg.attachments)}")
                print(f"   Attachments value: {msg.attachments}")
                traceback.print_exc()
                raise
        
        return ConversationDetailResponse(
            id=conversation.id,
            title=conversation.title,
            tenant_id=conversation.tenant_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_responses
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_conversation_detail: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/conversations/{user_id}/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    user_id: int,
    conversation_id: int,
    req: UpdateConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update conversation title."""
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get conversation
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_active == True
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Update conversation
        if req.title is not None:
            conversation.title = req.title
            conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(conversation)
        
        # Get message count
        message_count_result = await db.execute(
            select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        )
        message_count = len(message_count_result.scalars().all())
        
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            tenant_id=conversation.tenant_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=message_count
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{user_id}/{conversation_id}")
async def delete_conversation(
    user_id: int,
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a conversation."""
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get conversation
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_active == True
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Soft delete
        conversation.is_active = False
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"status": "ok", "message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ===== PULSE ENDPOINTS =====

@router.get("/pulse/{user_id}")
async def get_pulse(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get the current daily pulse for a user.
    
    Returns the AI-generated summary of the user's conversations.
    If no pulse exists, it will be generated on first access.
    """
    try:
        # Try to get existing pulse
        pulse_data = await get_user_pulse(user_id, db)
        
        if not pulse_data:
            # No pulse exists, generate one now
            success = await update_user_pulse(user_id, db)
            
            if not success:
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to generate pulse. Please try again later."
                )
            
            # Get the newly generated pulse
            pulse_data = await get_user_pulse(user_id, db)
            
            if not pulse_data:
                raise HTTPException(
                    status_code=500,
                    detail="Pulse generation failed unexpectedly"
                )
        
        return {
            "status": "ok",
            "pulse": pulse_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pulse/{user_id}/regenerate")
async def regenerate_pulse(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Manually trigger pulse regeneration for a user.
    
    This will analyze the last 10 conversations and generate a new pulse.
    Useful for testing or when user wants to refresh their pulse.
    """
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate new pulse
        success = await update_user_pulse(user_id, db)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to regenerate pulse"
            )
        
        # Get the regenerated pulse
        pulse_data = await get_user_pulse(user_id, db)
        
        return {
            "status": "ok",
            "message": "Pulse regenerated successfully",
            "pulse": pulse_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


