# app/api/v1/endpoints.py
from fastapi import APIRouter, Request, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Union
import base64
from app.services.orchestrator import (
    handle_chat_request,
    handle_ocr_request,
    handle_ocr_extract,
    handle_rag_query,
    handle_ingest_request,
    handle_predict_request,
    handle_web_search_request,
)
from app.services.chatbot_client import get_available_models
from app.utils.token_tracker_pg import PostgreSQLTokenTracker
from app.services.pulse_service import get_user_pulse, update_user_pulse
from app.db.database import get_db
from app.db.models import User, Conversation, ChatMessage, UserMemory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from app.config import settings

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
    use_pro_mode: Optional[bool] = False  # Enable AURA Pro (Gemini 2.5)
    conversation_history: Optional[List[Message]] = Field(default_factory=list)
    conversation_id: Optional[int] = None  # New: Link to existing conversation

class ChatV2Request(BaseModel):
    text: str = Field(..., min_length=1, description="User message to send to ORCHA")
    user_id: Optional[int] = Field(
        default=None,
        description="Existing ORCHA user ID. Defaults to settings.DEFAULT_WIDGET_USER_ID."
    )
    tenant_id: Optional[str] = Field(
        default=None,
        description="Optional tenant identifier. Defaults to settings.DEFAULT_WIDGET_TENANT_ID."
    )
    conversation_id: Optional[int] = Field(
        default=None,
        description="Resume an existing conversation if provided."
    )
    use_rag: Optional[bool] = Field(
        default=False,
        description="Set true to force Retrieval-Augmented responses."
    )

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

# DocCheckRequest removed - using File upload instead

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

class WebSearchRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    query: str
    max_results: Optional[int] = 5
    conversation_id: Optional[int] = None

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

class SaveMemoryRequest(BaseModel):
    user_id: int
    content: str
    title: Optional[str] = None
    conversation_id: Optional[int] = None
    source: Optional[str] = "manual"
    tags: Optional[List[str]] = None

class MemoryResponse(BaseModel):
    id: int
    content: str
    title: Optional[str]
    conversation_id: Optional[int]
    source: str
    tags: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

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

@router.post("/orcha/chat-v2")
async def orcha_chat_v2(req: ChatV2Request, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Lightweight chat endpoint tailored for the external iframe widget.
    Accepts only plain text (plus optional identifiers) and returns a normalized payload:
    {
        "success": true,
        "message": "",
        "data": {
            "text": "...",
            "conversation_id": 123
        }
    }
    """
    request.state.db_session = db

    resolved_user_id = req.user_id or settings.DEFAULT_WIDGET_USER_ID
    resolved_tenant_id = req.tenant_id or settings.DEFAULT_WIDGET_TENANT_ID

    chat_payload = {
        "user_id": str(resolved_user_id),
        "tenant_id": resolved_tenant_id,
        "message": req.text,
        "attachments": [],
        "use_rag": req.use_rag,
        "conversation_history": [],
        "conversation_id": req.conversation_id,
    }

    result = await handle_chat_request(chat_payload, request)
    success = result.get("status") == "ok"

    data = {
        "text": result.get("message", ""),
        "conversation_id": result.get("conversation_id"),
    }

    if success:
        if result.get("contexts"):
            data["contexts"] = result["contexts"]
        return {
            "success": True,
            "message": "",
            "data": data,
        }

    error_message = result.get("error") or result.get("message") or "Unable to process chat request."
    return {
        "success": False,
        "message": error_message,
        "data": data,
    }

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

@router.post("/orcha/search")
async def orcha_web_search(req: WebSearchRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Perform a web search and get LLM-refined results.
    
    Request:
    {
        "user_id": "123",
        "query": "Who won the F1 race last weekend?",
        "max_results": 5,  // optional, default: 5
        "conversation_id": 456  // optional, to maintain conversation context
    }
    
    Response:
    {
        "status": "ok",
        "message": "LLM-refined answer based on search results",
        "conversation_id": 456,
        "search_query": "Who won the F1 race last weekend?",
        "raw_search_results": "Here are the search results...",
        "results_count": 5,
        "token_usage": {...}
    }
    """
    # Attach database session to request state for orchestrator
    request.state.db_session = db
    result = await handle_web_search_request(req.dict(), request)
    return result

# Helper function to create CORS-friendly responses
def _create_cors_response(content: dict, status_code: int = 200):
    """Create a JSONResponse with explicit CORS headers to prevent nginx from blocking."""
    from fastapi.responses import JSONResponse
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(content=content, status_code=status_code, headers=headers)

# OPTIONS handler for CORS preflight (fix CORS errors with nginx)
@router.options("/orcha/doc-check")
async def orcha_doc_check_options():
    """Handle CORS preflight requests for doc-check endpoint."""
    from fastapi.responses import Response
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Max-Age": "86400",  # 24 hours
    }
    
    return Response(status_code=200, headers=headers)

@router.options("/orcha/auto-fill")
async def orcha_auto_fill_options():
    """Handle CORS preflight requests for auto-fill endpoint."""
    from fastapi.responses import Response
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Max-Age": "86400",  # 24 hours
    }
    
    return Response(status_code=200, headers=headers)

# Default empty response structure for auto-fill
def _get_empty_autofill_response(success: bool = True, message: str = "") -> dict:
    """Return the standard auto-fill response structure with empty/null data."""
    return {
        "success": success,
        "message": message,
        "data": {
            "id": None,
            "is_vip": 0,
            "language": "",
            "fid": None,
            "org_id": None,
            "is_group": 0,
            "employer_id": None,
            "fullname": "",
            "gender": None,
            "firstname": "",
            "lastname": "",
            "maidenname": "",
            "birth_date": None,
            "birth_place": "",
            "birth_country_code": "",
            "nationality": "",
            "nationality_2": None,
            "nationality_3": None,
            "email": None,
            "tel_1": "",
            "tel_2": "",
            "def_address_id": None,
            "def_bank_account_id": None,
            "adr": "",
            "adr_2": "",
            "zipcode": "",
            "city": "",
            "country_code": "",
            "bank_name": None,
            "bank_iban": "",
            "bank_bic": "",
            "lifecycle": None,
            "is_hr": 0,
            "staff_number": "",
            "created_at": None,
            "updated_at": None,
            "created_by": None,
            "updated_by": None,
            "deleted_at": None,
            "origin": None,
            "source_id": None,
            "reference": "",
            "social_sec_number": "",
            "citizen_id": None,
            "family_number": "",
            "type_account": None,
            "agency_name": None,
            "agency_code": None,
            "bank_country_code": None,
            "bank_contact": None,
            "agency_adress": None,
            "control_key": None,
            "bank_identifier_code": None,
            "bank_branch_code": None,
            "account_number": None,
            "rib_key": None,
            "rib": None,
            "bank_country": None,
            "bank_start_date": None,
            "bank_end_date": None,
            "locked_by": None,
            "locked_at": None,
            "identity_doc": None,
            "batchId": None,
            "childrens_count_by_type": [],
            "addresses": [],
            "banks": [],
            "moral": None,
            "childrens": [],
            "update": {
                "by": "",
                "at": None
            }
        }
    }

def _parse_llm_autofill_response(llm_response: str) -> dict:
    """
    Parse LLM response to extract gender, firstname, lastname, birth_date.
    
    Expected format: "response is: {gender_value}, {firstname_value}, {lastname_value}, {birth_date_value}"
    Or: "Document seems to be unvalid"
    
    Returns:
        dict with extracted values or None if invalid
    """
    import re
    
    if not llm_response:
        return None
    
    # Check for invalid document response
    if "document seems to be unvalid" in llm_response.lower():
        return None
    
    # Try to extract values from the expected format
    # Pattern: "response is: value1, value2, value3, value4"
    pattern = r"response\s+is\s*:\s*(.+)"
    match = re.search(pattern, llm_response, re.IGNORECASE)
    
    if not match:
        return None
    
    values_str = match.group(1).strip()
    
    # Split by comma and clean up
    values = [v.strip() for v in values_str.split(",")]
    
    if len(values) < 4:
        return None
    
    # Map values to fields
    gender_raw = values[0].strip().lower()
    firstname = values[1].strip()
    lastname = values[2].strip()
    birth_date = values[3].strip()
    
    # Normalize gender to expected format (M/F or null)
    gender = None
    if gender_raw in ["m", "male", "homme", "masculin"]:
        gender = "M"
    elif gender_raw in ["f", "female", "femme", "féminin", "feminin"]:
        gender = "F"
    
    # Validate birth_date format (should be a date-like string)
    # Accept various formats: YYYY-MM-DD, DD/MM/YYYY, etc.
    if birth_date and birth_date.lower() in ["n/a", "na", "none", "null", ""]:
        birth_date = None
    
    return {
        "gender": gender,
        "firstname": firstname if firstname and firstname.lower() not in ["n/a", "na", "none", "null"] else "",
        "lastname": lastname if lastname and lastname.lower() not in ["n/a", "na", "none", "null"] else "",
        "birth_date": birth_date
    }

@router.put("/orcha/auto-fill")
async def orcha_auto_fill(
    file: UploadFile = File(..., description="ID document file (PDF or image PNG/JPG)"),
    request: Request = None
):
    """
    Public endpoint to scan ID documents (ID Card or Passport) and extract personal information.
    No authentication required - designed for external application integrations.
    
    Accepts documents via multipart/form-data and extracts:
    - gender
    - firstname
    - lastname
    - birth_date
    
    Form Data:
    - file: Document file (PDF or image PNG/JPG)
    
    Processing Flow:
    - PDF files: Converted to Base64 and sent directly to the LLM for analysis
    - Image files: Processed through OCR first, then the extracted text is sent to LLM
    
    Response:
    {
        "success": true,
        "message": "",
        "data": {
            "gender": "M" or "F",
            "firstname": "John",
            "lastname": "Doe",
            "birth_date": "1990-01-15",
            ... (other fields as null/empty)
        }
    }
    """
    from app.utils.pdf_utils import extract_pdf_text
    from app.services.ocr_client import extract_text_from_image
    from app.services.chatbot_client import call_lmstudio_chat
    
    logger = getattr(request.state, "logger", None) if request else None
    
    # LLM System Prompt for ID document extraction
    LLM_SYSTEM_PROMPT = """Take this content of a document, analyse it and extract from it these 4 things only: "gender", "firstname", "lastname", "birth_date".

If valid, answer back in this specific format: "response is: {gender_value}, {firstname_value}, {lastname_value}, {birth_date_value}"

If you find nothing or the document is unclear, answer exactly: "Document seems to be unvalid\""""
    
    try:
        # Step 1: Read file and detect MIME type
        file_content = await file.read()
        filename = file.filename or "document"
        content_type = file.content_type or "application/octet-stream"
        
        if logger:
            logger.info(f"[AUTO-FILL] Received file: {filename}, type: {content_type}")
        
        # Convert to base64 for processing
        document_data_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Step 2: Process based on file type
        content_for_llm = ""
        is_pdf = content_type == "application/pdf" or filename.lower().endswith('.pdf')
        is_image = content_type.startswith("image/") or filename.lower().endswith(('.png', '.jpg', '.jpeg'))
        
        if not is_pdf and not is_image:
            # Unsupported file type
            if logger:
                logger.warning(f"[AUTO-FILL] Unsupported file type: {content_type}")
            response = _get_empty_autofill_response(success=False, message="Unsupported file type. Please upload PDF or image (PNG/JPG).")
            return _create_cors_response(response)
        
        if is_pdf:
            # PDF: Send Base64 directly to LLM (for vision processing)
            if logger:
                logger.info(f"[AUTO-FILL] Processing PDF: {filename}")
            
            # Extract text from PDF for LLM analysis
            extracted_text = extract_pdf_text(document_data_base64)
            
            if not extracted_text or len(extracted_text) < 10:
                if logger:
                    logger.warning(f"[AUTO-FILL] PDF appears empty or unreadable: {filename}")
                response = _get_empty_autofill_response(success=False, message="Document seems to be unvalid")
                return _create_cors_response(response)
            
            content_for_llm = extracted_text
            if logger:
                logger.info(f"[AUTO-FILL] Extracted {len(extracted_text)} characters from PDF")
        
        elif is_image:
            # Image: Send to OCR first, then to LLM
            if logger:
                logger.info(f"[AUTO-FILL] Processing image via OCR: {filename}")
            
            ocr_result = await extract_text_from_image(
                image_data=document_data_base64,
                filename=filename,
                language="en"  # Default to English for ID documents
            )
            
            if not ocr_result.get("success"):
                error_msg = ocr_result.get("message", "OCR failed")
                if logger:
                    logger.error(f"[AUTO-FILL] OCR failed: {error_msg}")
                response = _get_empty_autofill_response(success=False, message="Document seems to be unvalid")
                return _create_cors_response(response)
            
            extracted_text = ocr_result.get("text", "")
            
            if not extracted_text or len(extracted_text) < 10:
                if logger:
                    logger.warning(f"[AUTO-FILL] OCR returned insufficient text: {len(extracted_text)} chars")
                response = _get_empty_autofill_response(success=False, message="Document seems to be unvalid")
                return _create_cors_response(response)
            
            content_for_llm = extracted_text
            if logger:
                logger.info(f"[AUTO-FILL] OCR extracted {len(extracted_text)} characters")
        
        # Step 3: Send to LLM for extraction
        messages = [
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": f"Document content:\n\n{content_for_llm[:4000]}"}  # Limit to 4000 chars
        ]
        
        if logger:
            logger.info(f"[AUTO-FILL] Sending to LLM for extraction")
        
        llm_response = await call_lmstudio_chat(
            messages,
            model=None,
            max_tokens=200,  # Brief response expected
            timeout=60
        )
        
        # Extract LLM response text
        llm_text = ""
        if llm_response.get("choices") and len(llm_response["choices"]) > 0:
            llm_text = llm_response["choices"][0].get("message", {}).get("content", "")
        
        if logger:
            logger.info(f"[AUTO-FILL] LLM response: {llm_text[:200]}")
        
        # Step 4: Parse LLM response
        parsed = _parse_llm_autofill_response(llm_text)
        
        if not parsed:
            # LLM couldn't extract data or returned invalid document
            if logger:
                logger.warning(f"[AUTO-FILL] Failed to parse LLM response or invalid document")
            response = _get_empty_autofill_response(success=False, message="Document seems to be unvalid")
            return _create_cors_response(response)
        
        # Step 5: Build success response with extracted data
        response = _get_empty_autofill_response(success=True, message="")
        response["data"]["gender"] = parsed["gender"]
        response["data"]["firstname"] = parsed["firstname"]
        response["data"]["lastname"] = parsed["lastname"]
        response["data"]["birth_date"] = parsed["birth_date"]
        
        if logger:
            logger.info(f"[AUTO-FILL] Successfully extracted: gender={parsed['gender']}, firstname={parsed['firstname']}, lastname={parsed['lastname']}, birth_date={parsed['birth_date']}")
        
        return _create_cors_response(response)
        
    except Exception as e:
        error_msg = str(e)
        if logger:
            logger.error(f"[AUTO-FILL] Error: {error_msg}")
        
        response = _get_empty_autofill_response(success=False, message=f"Error processing document: {error_msg}")
        return _create_cors_response(response)

@router.put("/orcha/doc-check")
async def orcha_doc_check(
    file: UploadFile = File(..., description="Document file (PDF or image)"),
    label: str = Form(..., description="Document type label (e.g., passport, cin, driver_license)"),
    lang: str = Form(default="fr", description="Response language: 'en' or 'fr' (default: fr)"),
    request: Request = None
):
    """
    Document verification endpoint for external applications.
    No authentication required - designed for partner integrations.
    
    Accepts documents (PDF or images) via multipart/form-data and validates their authenticity.
    Returns validation result with brief explanation.
    
    Form Data:
    - file: Document file (PDF or image)
    - label: What the document is (e.g., "passport", "cin", "driver_license")
    - lang: Response language - "en" or "fr" (default: "fr")
    
    Response:
    {
        "success": true,  // API execution status (true = worked, false = error)
        "valid": true,    // Document validity (true = valid, false = invalid)
        "message": "API request processed successfully",
        "data": {
            "Res_validation": "Detailed validation result..."
        }
    }
    """
    from app.utils.pdf_utils import extract_pdf_text
    from app.services.ocr_client import extract_text_from_image
    from app.services.chatbot_client import call_lmstudio_chat
    
    SUPPORTED_OCR_LANGUAGES = {
        "en", "fr", "ar", "ch", "es", "de", "it", "pt", "ru", "ja", "ko"
    }
    
    logger = getattr(request.state, "logger", None) if request else None
    
    # Normalize language parameter
    lang = lang.lower() if lang else "fr"
    if lang not in ["en", "fr"]:
        lang = "fr"  # Default to French if invalid
    
    try:
        # Step 1: Read file and detect MIME type
        file_content = await file.read()
        filename = file.filename or "document"
        content_type = file.content_type or "application/octet-stream"
        
        if logger:
            logger.info(f"[DOC-CHECK] Received file: {filename}, type: {content_type}, label: {label}, lang: {lang}")
        
        # Convert to base64 for processing
        document_data_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Step 2: Extract text from document
        extracted_text = ""
        
        if content_type == "application/pdf" or filename.lower().endswith('.pdf'):
            # PDF: Extract text directly
            if logger:
                logger.info(f"[DOC-CHECK] Extracting text from PDF: {filename}")
            extracted_text = extract_pdf_text(document_data_base64)
            if logger:
                logger.info(f"[DOC-CHECK] Extracted {len(extracted_text)} characters from PDF")
        
        elif content_type.startswith("image/") or filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            # Image: Use OCR
            if logger:
                logger.info(f"[DOC-CHECK] Extracting text from image via OCR: {filename}")
            
            ocr_language = lang if lang in SUPPORTED_OCR_LANGUAGES else "en"
            if ocr_language != lang and logger:
                logger.warning(f"[DOC-CHECK] Unsupported OCR language '{lang}', falling back to '{ocr_language}'")
            
            ocr_result = await extract_text_from_image(
                image_data=document_data_base64,
                filename=filename,
                language=ocr_language
            )
            
            if ocr_result.get("success"):
                extracted_text = ocr_result.get("text", "")
                if logger:
                    logger.info(f"[DOC-CHECK] OCR extracted {len(extracted_text)} characters")
            else:
                # API failed (OCR error) - return success=False
                error_msg = f"Unable to extract text from image: {ocr_result.get('message', 'OCR failed')}"
                return _create_cors_response({
                    "success": False,
                    "valid": False,
                    "message": "invalid document" if lang == "en" else "document non valide",
                    "data": {
                        "Res_validation": error_msg
                    }
                })
        else:
            # Unsupported file type - API worked but file is invalid
            error_msg = f"Unsupported document type: {content_type}. Please upload PDF or image files."
            return _create_cors_response({
                "success": False,
                "valid": False,
                "message": "invalid document" if lang == "en" else "document non valide",
                "data": {
                    "Res_validation": error_msg
                }
            })
        
        if not extracted_text or len(extracted_text) < 10:
            # Document is unreadable - API worked but document is invalid
            error_msg = "Document appears to be empty or unreadable. No text could be extracted." if lang == "en" else "Le document semble vide ou illisible. Aucun texte n'a pu être extrait."
            return _create_cors_response({
                "success": True,  # API worked
                "valid": False,   # But document is invalid
                "message": "invalid document" if lang == "en" else "document non valide",
                "data": {
                    "Res_validation": error_msg
                }
            })
        
        # Step 3: Build specialized validation prompt based on label and language
        label_lower = label.lower()
        
        # Language instruction for the model
        if lang == "en":
            language_instruction = "Respond in English."
        else:
            language_instruction = "Répondez en français."
        
        # Build prompt with label injected and language preference
        system_prompt = f"""You are a document verification expert specializing in {label} validation.
Analyze the extracted text from a {label} document and verify its authenticity.

Check for:
- Document structure and completeness specific to {label}
- Presence of mandatory fields for {label}
- Valid identification numbers and formats
- Issuing authority and authenticity markers
- Valid dates (issue date, expiry date if applicable)
- Personal information consistency
- Any signs of tampering or inconsistency

Respond briefly (2-3 sentences maximum) with:
1. VALID or INVALID determination
2. Key reason(s) for your assessment
3. Any missing or suspicious elements if invalid

Be concise and professional.
{language_instruction}"""
        
        # Step 4: Call LLM for validation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Validate this {label} document:\n\n{extracted_text[:4000]}"}
        ]
        
        if logger:
            logger.info(f"[DOC-CHECK] Sending to LLM for validation: {label} (language: {lang})")
        
        llm_response = await call_lmstudio_chat(
            messages,
            model=None,
            max_tokens=300,  # Brief response
            timeout=60
        )
        
        validation_result = ""
        if llm_response.get("choices") and len(llm_response["choices"]) > 0:
            validation_result = llm_response["choices"][0].get("message", {}).get("content", "")
        
        if not validation_result:
            # LLM service unavailable - API failed
            error_msg = "Validation service unavailable. Please try again." if lang == "en" else "Service de validation indisponible. Veuillez réessayer."
            return _create_cors_response({
                "success": False,
                "valid": False,
                "message": "invalid document" if lang == "en" else "document non valide",
                "data": {
                    "Res_validation": error_msg
                }
            })
        
        # Step 5: Determine if document is valid based on LLM response
        validation_lower = validation_result.lower()
        
        # Check for invalid keywords first (more specific)
        # Check both English and French keywords regardless of lang setting
        if "invalid" in validation_lower or "invalide" in validation_lower:
            is_valid = False
        # Only if no invalid markers, check for valid keywords
        elif "valid" in validation_lower or "valide" in validation_lower:
            is_valid = True
        else:
            # If neither found, assume invalid for safety
            is_valid = False
        
        if logger:
            logger.info(f"[DOC-CHECK] Validation complete: {'VALID' if is_valid else 'INVALID'}")
        
        # API worked successfully - return result with document validity
        return _create_cors_response({
            "success": True,  # API worked
            "valid": is_valid,  # Document validity
            "message": ("valid document" if is_valid else "invalid document") if lang == "en" else ("document valide" if is_valid else "document non valide"),
            "data": {
                "Res_validation": validation_result
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        if logger:
            logger.error(f"[DOC-CHECK] Error: {error_msg}")
        
        # API failed due to exception
        return _create_cors_response({
            "success": False,
            "valid": False,
            "message": "invalid document" if lang == "en" else "document non valide",
            "data": {
                "Res_validation": f"Error during validation: {error_msg}"
            }
        })

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


# ===== MEMORY ENDPOINTS =====

@router.post("/memory")
async def save_memory(req: SaveMemoryRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new memory entry for a user.
    Supports multiple memories per user for complete history tracking.
    
    Request:
    {
        "user_id": 123,
        "content": "User prefers formal communication, works in insurance...",
        "title": "Communication preferences",  // optional
        "conversation_id": 456,  // optional - link to source conversation
        "source": "auto_extraction",  // optional - manual, auto_extraction, import
        "tags": ["preferences", "communication"]  // optional - categorization
    }
    
    Response:
    {
        "status": "ok",
        "message": "Memory saved successfully",
        "memory_id": 789
    }
    """
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == req.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify conversation exists if provided (skip validation if None)
        if req.conversation_id is not None:
            conv_result = await db.execute(
                select(Conversation).where(Conversation.id == req.conversation_id)
            )
            conversation = conv_result.scalar_one_or_none()
            if not conversation:
                # Don't fail - just set conversation_id to None
                # This prevents errors if frontend sends invalid conversation_id
                req.conversation_id = None
        
        # Create new memory entry (always creates new, never updates)
        memory = UserMemory(
            user_id=req.user_id,
            content=req.content,
            title=req.title,
            conversation_id=req.conversation_id,
            source=req.source or "manual",
            tags=req.tags,
            is_active=True
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        
        return {
            "status": "ok",
            "message": "Memory saved successfully",
            "memory_id": memory.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        # Log the actual error for debugging
        print(f"[ERROR] Failed to save memory: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save memory: {str(e)}")


@router.get("/memory/{user_id}")
async def get_memories(
    user_id: int, 
    limit: int = 50,
    offset: int = 0,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all memories for a user (paginated).
    
    Query Parameters:
    - limit: Maximum number of memories to return (default: 50)
    - offset: Number of memories to skip (default: 0)
    - include_inactive: Include soft-deleted memories (default: false)
    
    Response:
    {
        "status": "ok",
        "memories": [
            {
                "id": 1,
                "content": "User prefers...",
                "title": "Communication preferences",
                "conversation_id": 123,
                "source": "auto_extraction",
                "tags": ["preferences"],
                "is_active": true,
                "created_at": "2025-01-01T10:00:00",
                "updated_at": "2025-01-02T15:30:00"
            }
        ],
        "total": 10,
        "limit": 50,
        "offset": 0
    }
    """
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build query
        query = select(UserMemory).where(UserMemory.user_id == user_id)
        
        if not include_inactive:
            query = query.where(UserMemory.is_active == True)
        
        # Get total count
        count_result = await db.execute(
            select(UserMemory).where(
                UserMemory.user_id == user_id,
                UserMemory.is_active == True if not include_inactive else True
            )
        )
        total = len(count_result.scalars().all())
        
        # Get paginated memories (most recent first)
        query = query.order_by(desc(UserMemory.created_at)).limit(limit).offset(offset)
        result = await db.execute(query)
        memories = result.scalars().all()
        
        return {
            "status": "ok",
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "title": m.title,
                    "conversation_id": m.conversation_id,
                    "source": m.source,
                    "tags": m.tags,
                    "is_active": m.is_active,
                    "created_at": m.created_at.isoformat(),
                    "updated_at": m.updated_at.isoformat()
                }
                for m in memories
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/detail/{memory_id}")
async def get_memory_by_id(memory_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific memory by its ID.
    
    Response:
    {
        "status": "ok",
        "memory": {
            "id": 1,
            "user_id": 123,
            "content": "User prefers...",
            "title": "Communication preferences",
            "conversation_id": 456,
            "source": "auto_extraction",
            "tags": ["preferences"],
            "is_active": true,
            "created_at": "2025-01-01T10:00:00",
            "updated_at": "2025-01-02T15:30:00"
        }
    }
    """
    try:
        result = await db.execute(select(UserMemory).where(UserMemory.id == memory_id))
        memory = result.scalar_one_or_none()
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {
            "status": "ok",
            "memory": {
                "id": memory.id,
                "user_id": memory.user_id,
                "content": memory.content,
                "title": memory.title,
                "conversation_id": memory.conversation_id,
                "source": memory.source,
                "tags": memory.tags,
                "is_active": memory.is_active,
                "created_at": memory.created_at.isoformat(),
                "updated_at": memory.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: int, db: AsyncSession = Depends(get_db)):
    """
    Soft delete a memory (sets is_active to False).
    
    Response:
    {
        "status": "ok",
        "message": "Memory deleted successfully"
    }
    """
    try:
        result = await db.execute(select(UserMemory).where(UserMemory.id == memory_id))
        memory = result.scalar_one_or_none()
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Soft delete
        memory.is_active = False
        memory.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "status": "ok",
            "message": "Memory deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/memory/{memory_id}")
async def update_memory(
    memory_id: int,
    content: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing memory.
    
    Request Body (all fields optional):
    {
        "content": "Updated content...",
        "title": "Updated title",
        "tags": ["updated", "tags"]
    }
    
    Response:
    {
        "status": "ok",
        "message": "Memory updated successfully"
    }
    """
    try:
        result = await db.execute(select(UserMemory).where(UserMemory.id == memory_id))
        memory = result.scalar_one_or_none()
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Update fields if provided
        if content is not None:
            memory.content = content
        if title is not None:
            memory.title = title
        if tags is not None:
            memory.tags = tags
        
        memory.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "status": "ok",
            "message": "Memory updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


