# app/services/orchestrator.py
from typing import Dict, Any, List
import traceback
from app.services.chatbot_client import call_lmstudio_chat
from app.services.rag_client import rag_query, rag_ingest
from app.tasks.worker import enqueue_ocr_job
from app.config import settings
from app.utils.pdf_utils import extract_pdf_text
from app.utils.token_tracker_pg import PostgreSQLTokenTracker
from app.db.database import get_db
from app.db.models import Conversation, ChatMessage, User
from sqlalchemy import select
from datetime import datetime

def has_vision_attachments(attachments: List) -> tuple[bool, List[Dict[str, Any]]]:
    """
    Check if attachments contain images suitable for vision processing.
    
    Returns:
        tuple: (has_images: bool, vision_attachments: List[Dict])
               vision_attachments contain {"data": base64_str, "type": mime_type, "filename": str}
    """
    vision_images = []
    if not attachments:
        return False, []
    
    for a in attachments:
        if not isinstance(a, dict):
            continue
        
        attachment_type = a.get("type", "")
        attachment_data = a.get("data")
        
        # Check if it's an image with base64 data (suitable for vision)
        if attachment_type and attachment_type.startswith("image/") and attachment_data:
            vision_images.append({
                "data": attachment_data,
                "type": attachment_type,
                "filename": a.get("filename", "image")
            })
    
    return len(vision_images) > 0, vision_images

async def handle_chat_request(payload: Dict[str, Any], request):
    """
    payload: { user_id, tenant_id, message, attachments[], use_rag, conversation_id }
    request: FastAPI Request for trace/logging access
    
    Smart flow:
    - If attachments with base64 data (PDFs) -> Extract text and add to prompt
    - If attachments with URI -> OCR + Ingest to RAG + Answer with RAG context
    - If use_rag=True -> Query RAG + Answer with context
    - Otherwise -> Direct chat with LLM
    - Store all messages in database
    """
    logger = getattr(request.state, "logger", None)
    user_id = payload.get("user_id")
    message = payload.get("message", "")
    attachments = payload.get("attachments") or []
    use_rag = payload.get("use_rag", False)
    conversation_history = payload.get("conversation_history") or []  # Last N messages for context
    conversation_id = payload.get("conversation_id")  # Optional: existing conversation
    tenant_id = payload.get("tenant_id")
    ingested_docs = []  # Track ingested documents

    # Get database session
    db_session = getattr(request.state, 'db_session', None)
    if not db_session:
        logger.error("No database session available")
        return {"status": "error", "error": "Database session not available"}

    # Convert user_id to int for database operations
    user_id_int = int(user_id) if isinstance(user_id, str) else user_id

    # Get or create conversation
    conversation = None
    conversation_title = None  # Cache title to avoid lazy loads
    if conversation_id:
        # Use existing conversation
        conv_result = await db_session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id_int,
                Conversation.is_active == True
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found for user {user_id_int}")
        else:
            # Cache the title value to avoid lazy load issues later
            await db_session.refresh(conversation)
            conversation_title = conversation.title
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=user_id_int,
            tenant_id=tenant_id,
            title=None  # Will be auto-generated from first message
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)
        conversation_title = None  # New conversation has no title yet
        logger.info(f"Created new conversation {conversation.id} for user {user_id_int}")

    # Store user message in database
    user_message = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=message,
        attachments=attachments if attachments else None,
        created_at=datetime.utcnow()
    )
    db_session.add(user_message)
    await db_session.commit()
    await db_session.refresh(user_message)

    # 1) Check for vision attachments first
    has_vision, vision_images = has_vision_attachments(attachments)
    
    # 2) Process attachments - extract text from PDFs or use OCR for images
    pdf_content = ""  # Store extracted PDF text for direct inclusion in prompt
    
    if attachments:
        if logger:
            logger.info(f"Processing {len(attachments)} attachment(s)")
        
        from app.services.ocr_client import call_ocr
        
        # Process each attachment
        for a in attachments:
            uri = a.get("uri") if isinstance(a, dict) else a
            attachment_type = a.get("type") if isinstance(a, dict) else None
            attachment_data = a.get("data") if isinstance(a, dict) else None
            filename = a.get("filename", "unknown") if isinstance(a, dict) else "unknown"
            
            # Check if attachment has base64 data (new flow)
            if attachment_data:
                if logger:
                    logger.info(f"📎 Processing attachment with base64 data: {filename}")
                
                # Handle PDF files with direct text extraction
                if attachment_type == "application/pdf":
                    try:
                        if logger:
                            logger.info(f"📄 Extracting text from PDF: {filename}")
                        
                        # Extract text from PDF
                        pdf_text = extract_pdf_text(attachment_data)
                        
                        if logger:
                            logger.info(f"✅ Extracted {len(pdf_text)} characters from {filename}")
                        
                        # Add to PDF content for direct inclusion in prompt
                        pdf_content += f"\n\n=== Document: {filename} ===\n"
                        pdf_content += pdf_text
                        pdf_content += f"\n=== End of {filename} ===\n"
                        
                    except Exception as e:
                        if logger:
                            logger.error(f"❌ Error extracting PDF {filename}: {e}")
                        # Continue with other attachments
                        continue
                
                # Handle images - skip processing if using vision mode
                elif attachment_type and attachment_type.startswith("image/"):
                    if has_vision:
                        if logger:
                            logger.info(f"🖼️ Image attachment detected: {filename} (will be processed by vision model)")
                        # Skip individual processing - will be handled by vision API
                    else:
                        if logger:
                            logger.info(f"🖼️ Image attachment detected: {filename} (OCR not yet implemented for base64 images)")
                        # TODO: Add OCR support for base64 image data if needed
                
            # Fallback to URI-based OCR flow (legacy/external attachments)
            elif uri:
                try:
                    # Step 1: Extract text via OCR 
                    if logger:
                        logger.info(f"Extracting text from URI: {uri}")
                    ocr_result = await call_ocr(uri, mode="auto")
                    
                    # Step 2: Ingest extracted text into RAG
                    if logger:
                        logger.info(f"Ingesting {uri} into RAG")
                    ingest_result = await rag_ingest(
                        source=f"attachment_{user_id}",
                        uri=uri,
                        metadata={
                            "user_id": user_id,
                            "original_message": message,
                            "type": attachment_type or "unknown",
                            "ocr_result": ocr_result  # Store OCR metadata
                        }
                    )
                    ingested_docs.append(ingest_result)
                    if logger:
                        logger.info(f"Successfully ingested {uri}")
                    
                    # For URI-based attachments, enable RAG
                    use_rag = True
                    
                except Exception as e:
                    if logger:
                        logger.error(f"Failed to process attachment {uri}: {e}")
                    # Continue with other attachments even if one fails
                    continue

    # 3) if use_rag -> query RAG first to collect contexts
    contexts = None
    if use_rag:
        try:
            rag_resp = await rag_query(message, k=8, rerank=True)
            contexts = rag_resp.get("contexts") or rag_resp.get("results") or []
            if logger:
                logger.info(f"RAG returned {len(contexts)} contexts")
        except Exception as e:
            if logger:
                logger.info(f"RAG query failed: {e}")

    # 4) build messages for LLM
    # Detect if this is a memory extraction request
    is_memory_request = message.strip().startswith("Based on my recent messages, extract and remember")
    
    if is_memory_request:
        # Use unrestricted system prompt for memory extraction
        system_prompt = "You are a helpful AI assistant. Carefully analyze the user's conversation history and extract key information they want you to remember. Be thorough and accurate in identifying personal details, preferences, and important facts."
        if logger:
            logger.info("🧠 Memory extraction request detected - using unrestricted system prompt")
    else:
        # Use insurance/finance-focused prompt for regular chat
        system_prompt = "You are AURA, an advanced assistant for insurance and finance. Provide precise, professional insights on health insurance, FinTech, risk management, and compliant financial advice. Refuse general topics and redirect to relevant contexts. Stay factual, concise, and analytical."
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add RAG context if available
    if contexts:
        # attach top contexts to the prompt in a safe, truncated way
        ctx_text = "\n\n=== SOURCES ===\n"
        for i, c in enumerate(contexts[:4]):
            src = c.get("source") or c.get("doc_id") or f"context_{i}"
            txt = c.get("text") or c.get("chunk") or c.get("content") or ""
            ctx_text += f"[{src}] {txt[:800]}\n\n"
        messages.append({"role": "system", "content": ctx_text})
    
    # Get conversation history from database (last 10 messages for context)
    # IMPORTANT: Only load history BEFORE the current user message to avoid including it
    if not conversation_history:  # Only use DB history if frontend didn't provide it
        try:
            # Load messages that were created BEFORE the current user message
            # This ensures we don't include the message we just added above
            history_result = await db_session.execute(
                select(ChatMessage)
                .where(
                    ChatMessage.conversation_id == conversation.id,
                    ChatMessage.id < user_message.id  # Only messages before current one
                )
                .order_by(ChatMessage.created_at.desc())
                .limit(10)
            )
            db_messages = history_result.scalars().all()
            
            # Convert to message format in chronological order (oldest to newest)
            db_history = []
            for msg in reversed(db_messages):  # Reverse to get chronological order
                if msg.role in ["user", "assistant"]:
                    db_history.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            if db_history:
                if logger:
                    logger.info(f"Including {len(db_history)} previous messages from conversation {conversation.id}")
                conversation_history = db_history
        except Exception as e:
            if logger:
                logger.warning(f"Failed to load conversation history: {e}")
    
    # Add conversation history for context
    if conversation_history:
        if logger:
            logger.info(f"Including {len(conversation_history)} previous messages for context")
        # Validate and add history messages
        for hist_msg in conversation_history:
            if isinstance(hist_msg, dict) and "role" in hist_msg and "content" in hist_msg:
                # Only allow user and assistant roles in history
                if hist_msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": hist_msg["role"],
                        "content": hist_msg["content"]
                    })
    
    # Build enhanced message with PDF content if available
    if pdf_content:
        # Prepend PDF content to user's message
        enhanced_message = f"""The user has attached a document with the following content:

{pdf_content}

User's question: {message}

Please answer the user's question based on the document content above."""
        
        if logger:
            logger.info(f"Enhanced message with PDF content ({len(pdf_content)} chars)")
    else:
        # No PDF attached, use original message
        enhanced_message = message
    
    # Add current user message with vision support
    if has_vision:
        # Format message for LM Studio vision API
        if logger:
            logger.info(f"🎨 Formatting message for vision API with {len(vision_images)} image(s)")
        
        # Build content array with text and images
        content = [{"type": "text", "text": enhanced_message}]
        
        # Add each image in vision format
        for img in vision_images:
            # Ensure base64 data doesn't have data URL prefix
            base64_data = img["data"]
            if base64_data.startswith("data:"):
                # Strip the data URL prefix if present
                base64_data = base64_data.split(",", 1)[1] if "," in base64_data else base64_data
            
            # Determine image format from MIME type
            img_format = img["type"].split("/")[1] if "/" in img["type"] else "jpeg"
            
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{img_format};base64,{base64_data}"
                }
            })
            
            if logger:
                logger.info(f"  📷 Added image: {img['filename']} (format: {img_format})")
        
        messages.append({"role": "user", "content": content})
    else:
        # Standard text-only message
        messages.append({"role": "user", "content": enhanced_message})

    # 5) call LM Studio with vision support if needed
    try:
        if logger:
            logger.info(f"Calling LM Studio with {len(messages)} messages")
        
        # Use vision model if images are present
        model_to_use = settings.LMSTUDIO_VISION_MODEL if has_vision else None
        max_tokens = 1024 if has_vision else None  # Limit tokens for vision requests
        
        if has_vision and logger:
            logger.info(f"🎨 Using vision model: {model_to_use}")
            logger.info(f"🎨 Vision mode active: sending {len(vision_images)} image(s)")
            # Log message structure for debugging
            last_msg = messages[-1] if messages else None
            if last_msg and isinstance(last_msg.get("content"), list):
                logger.info(f"🎨 Message content is array with {len(last_msg['content'])} items")
                for i, item in enumerate(last_msg['content']):
                    if item.get('type') == 'image_url':
                        img_url = item.get('image_url', {}).get('url', '')
                        logger.info(f"🎨   Item {i}: image (url length: {len(img_url)} chars)")
                    else:
                        logger.info(f"🎨   Item {i}: {item.get('type', 'unknown')}")
        
        resp = await call_lmstudio_chat(
            messages, 
            model=model_to_use,
            max_tokens=max_tokens,
            timeout=settings.LM_TIMEOUT
        )
        
        if logger:
            logger.info(f"LM Studio response received successfully")
            logger.debug(f"Response keys: {resp.keys() if isinstance(resp, dict) else 'Not a dict'}")
        
        # Validate response structure
        if not isinstance(resp, dict):
            raise ValueError(f"LM Studio returned non-dict response: {type(resp)}")
        
        if "choices" not in resp:
            raise ValueError(f"LM Studio response missing 'choices' field. Keys: {list(resp.keys())}")
        
        # Extract the assistant's message for clean React consumption
        assistant_message = ""
        total_tokens = 0
        if resp.get("choices") and len(resp["choices"]) > 0:
            message_obj = resp["choices"][0].get("message", {})
            assistant_message = message_obj.get("content", "")
            
            if logger:
                logger.info(f"✅ Extracted message length: {len(assistant_message)} chars")
                if "usage" in resp:
                    usage = resp["usage"]
                    total_tokens = usage.get('total_tokens', 0)
                    logger.info(f"📊 Tokens - Prompt: {usage.get('prompt_tokens')}, Completion: {usage.get('completion_tokens')}, Total: {total_tokens}")
        
        # Fallback if message is empty
        if not assistant_message:
            assistant_message = "I apologize, but I couldn't generate a proper response. Please try again."
            if logger:
                logger.warning("LM returned empty message")
        
        # Store assistant message in database
        assistant_message_db = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_message,
            token_count=total_tokens,
            model_used=resp.get("model", "unknown"),
            rag_contexts_used=contexts if contexts else None,
            created_at=datetime.utcnow()
        )
        db_session.add(assistant_message_db)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        # Auto-generate conversation title from first user message if not set
        # Use cached conversation_title to avoid lazy load issues
        if not conversation_title:
            # Count messages in this conversation to check if it's the first exchange
            message_count_result = await db_session.execute(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation.id)                                                                                                                                                                                                                                                                                                     
            )
            message_count = len(message_count_result.scalars().all())
            
            # Only set title on first exchange (2 messages: 1 user + 1 assistant)
            if message_count <= 2:
                # Generate title from first user message (truncated)
                title = message[:50] + "..." if len(message) > 50 else message
                conversation.title = title
                conversation_title = title  # Update cached value
                if logger:
                    logger.info(f"Auto-generated conversation title: {title}")
        
        await db_session.commit()
        await db_session.refresh(assistant_message_db)

        # Track token usage for this user (24-hour rolling window)
        token_usage_info = {}
        if total_tokens > 0 and user_id:
            try:
                tracker = PostgreSQLTokenTracker(db_session)
                # Convert user_id to int if it's a string
                user_id_int = int(user_id) if isinstance(user_id, str) else user_id
                token_usage_info = await tracker.increment_tokens(
                    user_id=user_id_int,
                    tokens_used=total_tokens,
                    logger=logger
                )
                if logger:
                    logger.info(f"💳 Token usage updated: {token_usage_info.get('current_usage')} total (resets at {token_usage_info.get('reset_at')})")
            except Exception as e:
                if logger:
                    logger.warning(f"Token tracking failed (non-fatal): {e}")
        
        # Return clean response for React UI
        result = {
            "status": "ok",
            "message": assistant_message,
            "conversation_id": conversation.id,  # Return conversation ID for frontend
            "contexts": contexts if contexts else [],
            "model_response": resp,  # Full response for debugging
            "token_usage": token_usage_info  # Add token tracking info
        }
        
        # Add attachment info if any were processed
        if attachments:
            result["attachments_processed"] = len(attachments)
            result["ingested_documents"] = len(ingested_docs)
            if pdf_content:
                result["pdf_text_length"] = len(pdf_content)
        
        if logger:
            logger.info(f"Returning result with status: {result['status']}")
            logger.info(f"📤 Response preview: message length={len(result['message'])}, conversation_id={result['conversation_id']}")
            logger.info(f"📤 Full response keys: {list(result.keys())}")
        
        return result
        
    except Exception as e:
        # Log full traceback for debugging
        error_traceback = traceback.format_exc()
        if logger:
            logger.error(f"LM call failed with exception: {e}")
            logger.error(f"Full traceback:\n{error_traceback}")
        else:
            # Fallback to print if logger not available
            print(f"ERROR: {e}")
            print(error_traceback)
        
        # Store error message in database if conversation exists
        if conversation:
            try:
                error_message_db = ChatMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    content="Sorry, I encountered an error processing your request. Please try again.",
                    error_message=str(e),
                    created_at=datetime.utcnow()
                )
                db_session.add(error_message_db)
                conversation.updated_at = datetime.utcnow()
                await db_session.commit()
            except Exception as db_error:
                if logger:
                    logger.error(f"Failed to store error message: {db_error}")
        
        # Return error but keep the system alive
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Sorry, I encountered an error processing your request. Please try again.",
            "conversation_id": conversation.id if conversation else None
        }

async def handle_ocr_request(payload: Dict[str, Any], request):
    """
    payload: {user_id, tenant_id, file_uri, mode}
    We only enqueue the OCR job and return job id
    """
    redis = request.app.state.redis
    job_id = await enqueue_ocr_job(redis, payload.get("file_uri"), user_id=payload.get("user_id"), tenant_id=payload.get("tenant_id"))
    return {"status": "ocr_queued", "job_id": job_id}

async def handle_ocr_extract(payload: Dict[str, Any], request):
    """
    Direct OCR text extraction from base64 image data.
    
    payload: {
        user_id: str,
        tenant_id: str (optional),
        image_data: str (base64 encoded),
        filename: str (optional),
        language: str (en|fr|ar|ch|etc, default: en)
    }
    
    Returns extracted text immediately without queueing.
    """
    logger = getattr(request.state, "logger", None)
    
    image_data = payload.get("image_data")
    filename = payload.get("filename", "image")
    language = payload.get("language", "en")
    user_id = payload.get("user_id")
    
    if not image_data:
        return {
            "status": "error",
            "error": "image_data is required"
        }
    
    try:
        if logger:
            logger.info(f"🖼️ Processing OCR extraction for {filename} (language: {language})")
        
        # Import here to avoid circular dependency
        from app.services.ocr_client import extract_text_from_image
        
        # Call OCR service
        ocr_result = await extract_text_from_image(
            image_data=image_data,
            filename=filename,
            language=language
        )
        
        if logger:
            logger.info(f"✅ OCR extraction completed for {filename}")
            if ocr_result.get("success") and ocr_result.get("text"):
                logger.info(f"📝 Extracted {len(ocr_result['text'])} characters")
        
        # Check if OCR was successful
        if ocr_result.get("success"):
            return {
                "status": "success",
                "extracted_text": ocr_result.get("text", ""),
                "lines_count": ocr_result.get("lines_count", 0),
                "message": ocr_result.get("message", "Text extracted successfully"),
                "filename": filename,
                "language": language
            }
        else:
            # OCR service returned an error
            error_msg = ocr_result.get("message", "OCR extraction failed")
            if logger:
                logger.error(f"❌ OCR service error for {filename}: {error_msg}")
            
            return {
                "status": "error",
                "error": error_msg,
                "filename": filename
            }
        
    except Exception as e:
        error_msg = str(e)
        if logger:
            logger.error(f"❌ OCR extraction failed for {filename}: {error_msg}")
            logger.error(traceback.format_exc())
        
        return {
            "status": "error",
            "error": error_msg,
            "filename": filename
        }

async def handle_rag_query(payload: Dict[str, Any], request):
    """
    payload: {user_id, tenant_id, query, k, rerank}
    """
    try:
        resp = await rag_query(payload.get("query", ""), k=payload.get("k", 8), rerank=payload.get("rerank", True))
        return {"status": "ok", "result": resp}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def handle_ingest_request(payload: Dict[str, Any], request):
    """
    payload: {source, uri, metadata}
    Enqueue or call rag_ingest directly
    """
    try:
        resp = await rag_ingest(payload.get("source"), payload.get("uri"), payload.get("metadata"))
        return {"status": "ok", "result": resp}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def handle_predict_request(payload: Dict[str, Any], request):
    # stub predictive model: echo features + fake score
    features = payload.get("features", {})
    # naive scoring: count numeric features (placeholder)
    score = sum(1 for v in features.values() if isinstance(v, (int, float)))
    reasons = ["stub: numeric feature count"]
    return {"status": "ok", "score": float(score), "reasons": reasons}
