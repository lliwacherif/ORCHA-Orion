# Orchestrator Architecture & Flow Diagram

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Main Components](#main-components)
3. [Function Flow Diagrams](#function-flow-diagrams)
4. [Database Models](#database-models)
5. [External Services](#external-services)
6. [Data Flow Examples](#data-flow-examples)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         ORCHA SYSTEM                             │
│                    (Orchestration Layer)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────┐
        │       FastAPI Endpoints (v1)           │
        │    app/api/v1/endpoints.py             │
        └────────────────────────────────────────┘
                │         │         │
       ┌────────┴─────┬───┴────┬────┴─────┐
       ▼              ▼        ▼          ▼
   /orcha/chat   /orcha/ocr  /orcha/rag  /orcha/ingest
       │              │         │           │
       └──────────────┴─────────┴───────────┘
                      │
                      ▼
        ┌──────────────────────────────┐
        │    Orchestrator Service      │
        │  app/services/orchestrator.py│
        └──────────────────────────────┘
                │         │
        ┌───────┴────┬────┴─────┐
        ▼            ▼          ▼
   [Database]  [External]  [Utils]
                Services
```

---

## Main Components

### 1. API Layer (`app/api/v1/endpoints.py`)

**Purpose**: Entry points for all requests

#### Endpoints:

| Endpoint | Handler Function | Purpose |
|----------|-----------------|---------|
| `POST /orcha/chat` | `orcha_chat()` | Main chat interface with AI |
| `POST /orcha/ocr` | `orcha_ocr()` | Queue OCR job (legacy) |
| `POST /orcha/ocr/extract` | `orcha_ocr_extract()` | Direct OCR text extraction |
| `POST /orcha/rag/query` | `orcha_rag_query()` | Query RAG knowledge base |
| `POST /orcha/ingest` | `orcha_ingest()` | Ingest documents to RAG |
| `POST /orcha/route` | `orcha_route()` | Smart routing decision |
| `POST /orcha/predict` | `orcha_predict()` | Prediction (stub) |
| `GET /models` | `list_models()` | Get available LLM models |
| `GET /tokens/usage/{user_id}` | `get_token_usage()` | Get user token usage |
| `POST /tokens/reset/{user_id}` | `reset_token_usage()` | Reset token usage |
| `POST /conversations` | `create_conversation()` | Create conversation |
| `GET /conversations/{user_id}` | `get_user_conversations()` | List conversations |
| `GET /conversations/{user_id}/{id}` | `get_conversation_detail()` | Get conversation details |
| `PUT /conversations/{user_id}/{id}` | `update_conversation()` | Update conversation |
| `DELETE /conversations/{user_id}/{id}` | `delete_conversation()` | Delete conversation |
| `GET /pulse/{user_id}` | `get_pulse()` | Get user's daily pulse |
| `POST /pulse/{user_id}/regenerate` | `regenerate_pulse()` | Regenerate pulse |

---

### 2. Orchestrator Layer (`app/services/orchestrator.py`)

**Purpose**: Core business logic and workflow coordination

#### Main Functions:

```
orchestrator.py
├── handle_chat_request()          ← Main chat flow
├── handle_ocr_request()           ← Queue OCR jobs
├── handle_ocr_extract()           ← Direct OCR extraction
├── handle_rag_query()             ← RAG queries
├── handle_ingest_request()        ← Ingest documents
├── handle_predict_request()       ← Predictions (stub)
└── has_vision_attachments()       ← Helper: detect vision attachments
```

---

## Function Flow Diagrams

### 🔵 1. `handle_chat_request()` - The Core Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    handle_chat_request()                         │
│                  (Main Orchestration Function)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Parse Payload  │
                    │ - user_id       │
                    │ - message       │
                    │ - attachments   │
                    │ - use_rag       │
                    │ - conversation_id│
                    └─────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   Get/Create Conversation (DB)       │
        │   - Existing: Load from DB           │
        │   - New: Create new conversation     │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   Store User Message (DB)            │
        │   ChatMessage(role="user")           │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   Check Vision Attachments           │
        │   has_vision_attachments()           │
        └──────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │ Has Images?               │
                └─────────────┬─────────────┘
                        Yes   │   No
                    ┌─────────┴─────────┐
                    ▼                   │
        ┌────────────────────┐          │
        │ Vision Mode Active │          │
        │ Prepare for LLM    │          │
        └────────────────────┘          │
                    │                   │
                    └─────────┬─────────┘
                              ▼
        ┌──────────────────────────────────────┐
        │   Process Attachments                │
        └──────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌────────────────────┐      ┌──────────────────┐
    │  PDF Attachments?  │      │ Image (URI)?     │
    │  - Extract text    │      │ - OCR Service    │
    │  - Add to prompt   │      │ - Ingest to RAG  │
    │  pdf_utils.py      │      │ - Enable RAG     │
    └────────────────────┘      └──────────────────┘
                │                           │
                └─────────────┬─────────────┘
                              ▼
                    ┌─────────────────┐
                    │   Use RAG?      │
                    └─────────────────┘
                              │
                        Yes   │   No
                    ┌─────────┴─────────┐
                    ▼                   │
        ┌────────────────────┐          │
        │ Query RAG Service  │          │
        │ rag_client.py      │          │
        │ - Get contexts     │          │
        └────────────────────┘          │
                    │                   │
                    └─────────┬─────────┘
                              ▼
        ┌──────────────────────────────────────┐
        │   Detect Memory Extraction Request   │
        │   "Based on my recent messages..."   │
        └──────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │ Memory Request?           │
                └─────────────┬─────────────┘
                        Yes   │   No
                    ┌─────────┴─────────┐
                    ▼                   ▼
        ┌────────────────────┐  ┌─────────────────┐
        │ Unrestricted       │  │ Insurance/      │
        │ System Prompt      │  │ Finance Prompt  │
        └────────────────────┘  └─────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              ▼
        ┌──────────────────────────────────────┐
        │   Build Messages Array               │
        │   1. System prompt                   │
        │   2. RAG contexts (if any)           │
        │   3. Conversation history from DB    │
        │   4. Current user message            │
        │      - Text only OR                  │
        │      - Text + Images (vision)        │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   Call LM Studio                     │
        │   chatbot_client.py                  │
        │   - Regular model OR                 │
        │   - Vision model (if images)         │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   Parse Response                     │
        │   - Extract message content          │
        │   - Extract token usage              │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   Store Assistant Message (DB)       │
        │   ChatMessage(role="assistant")      │
        │   - content, token_count, model_used │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   Update Conversation                │
        │   - timestamp                        │
        │   - auto-generate title (1st msg)    │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   Track Token Usage                  │
        │   token_tracker_pg.py                │
        │   - 24-hour rolling window           │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   Return Response                    │
        │   {                                  │
        │     status: "ok",                    │
        │     message: "...",                  │
        │     conversation_id: 123,            │
        │     contexts: [...],                 │
        │     token_usage: {...}               │
        │   }                                  │
        └──────────────────────────────────────┘
```

---

### 🟢 2. `handle_ocr_extract()` - Direct OCR Flow

```
┌─────────────────────────────────────────┐
│      handle_ocr_extract()               │
└─────────────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Parse Payload         │
    │  - image_data (base64) │
    │  - filename            │
    │  - language (en/fr/ar) │
    └────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Call OCR Service      │
    │  ocr_client.py         │
    │  extract_text_from_    │
    │  image()               │
    └────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Return Result         │
    │  {                     │
    │    status: "success",  │
    │    extracted_text: "...│
    │    lines_count: 10     │
    │  }                     │
    └────────────────────────┘
```

---

### 🟡 3. `handle_rag_query()` - RAG Query Flow

```
┌─────────────────────────────────────────┐
│       handle_rag_query()                │
└─────────────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Parse Payload         │
    │  - query (text)        │
    │  - k (results count)   │
    │  - rerank (bool)       │
    └────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Call RAG Service      │
    │  rag_client.py         │
    │  rag_query()           │
    └────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Return Contexts       │
    │  {                     │
    │    status: "ok",       │
    │    result: {           │
    │      contexts: [...]   │
    │    }                   │
    │  }                     │
    └────────────────────────┘
```

---

### 🟣 4. `handle_ingest_request()` - Document Ingestion Flow

```
┌─────────────────────────────────────────┐
│     handle_ingest_request()             │
└─────────────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Parse Payload         │
    │  - source              │
    │  - uri                 │
    │  - metadata            │
    └────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Call RAG Service      │
    │  rag_client.py         │
    │  rag_ingest()          │
    └────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Return Result         │
    │  {                     │
    │    status: "ok",       │
    │    result: {...}       │
    │  }                     │
    └────────────────────────┘
```

---

## Database Models

### Entity Relationship Diagram

```
┌──────────────────────┐
│       User           │
│──────────────────────│
│ id (PK)              │◄───────┐
│ username             │        │
│ email                │        │ One-to-Many
│ hashed_password      │        │
│ full_name            │        │
│ is_active            │        │
│ plan_type            │        │
│ created_at           │        │
│ updated_at           │        │
└──────────────────────┘        │
         │                      │
         │ One-to-One           │
         ▼                      │
┌──────────────────────┐        │
│      Pulse           │        │
│──────────────────────│        │
│ id (PK)              │        │
│ user_id (FK)         │        │
│ content              │        │
│ generated_at         │        │
│ conversations_       │        │
│   analyzed           │        │
│ messages_analyzed    │        │
│ next_generation      │        │
└──────────────────────┘        │
                                │
                                │
┌──────────────────────┐        │
│   TokenUsage         │        │
│──────────────────────│        │
│ user_id (PK, FK)     │────────┘
│ total_tokens         │
│ reset_at             │
│ last_updated         │
└──────────────────────┘


┌──────────────────────┐
│   Conversation       │
│──────────────────────│
│ id (PK)              │◄───────┐
│ user_id (FK)         │────────┤
│ title                │        │
│ tenant_id            │        │
│ created_at           │        │
│ updated_at           │        │
│ is_active            │        │
└──────────────────────┘        │
         │                      │
         │ One-to-Many          │
         ▼                      │
┌──────────────────────┐        │
│    ChatMessage       │        │
│──────────────────────│        │
│ id (PK)              │        │
│ conversation_id (FK) │────────┘
│ role                 │
│ content              │
│ attachments (JSON)   │
│ token_count          │
│ model_used           │
│ created_at           │
│ processing_time_ms   │
│ error_message        │
│ rag_contexts_used    │
└──────────────────────┘
```

---

## External Services

### Service Dependencies

```
┌────────────────────────────────────────────────────┐
│              ORCHESTRATOR                          │
└────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬────────────┐
        │           │           │            │
        ▼           ▼           ▼            ▼
┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
│LM Studio │ │RAG Service│ │OCR Svc  │ │PostgreSQL│
│(Chat AI) │ │(Vector DB)│ │(Tesseract│ │(Database)│
└──────────┘ └──────────┘ └─────────┘ └──────────┘
```

### 1. **LM Studio Service** (`chatbot_client.py`)

```python
Functions:
├── call_lmstudio_chat()
│   ├── Input: messages[], model, temp, max_tokens
│   ├── API: POST /v1/chat/completions
│   └── Output: LLM response with choices
│
└── get_available_models()
    ├── API: GET /v1/models
    └── Output: List of available models
```

**Configuration:**
- `LMSTUDIO_URL`: Base URL for LM Studio
- `LMSTUDIO_VISION_MODEL`: Model for vision tasks
- `LM_TIMEOUT`: Request timeout

---

### 2. **RAG Service** (`rag_client.py`)

```python
Functions:
├── rag_query()
│   ├── Input: query, k, rerank
│   ├── API: POST /query
│   └── Output: Relevant contexts/chunks
│
└── rag_ingest()
    ├── Input: source, uri, metadata
    ├── API: POST /ingest
    └── Output: Ingestion result
```

**Configuration:**
- `RAG_SERVICE_URL`: Base URL for RAG service
- `RAG_TIMEOUT`: Request timeout

---

### 3. **OCR Service** (`ocr_client.py`)

```python
Functions:
├── call_ocr()                    ← Legacy URI-based
│   ├── Input: file_uri, mode
│   ├── API: POST /ocr
│   └── Output: OCR result
│
└── extract_text_from_image()     ← New base64-based
    ├── Input: image_data, filename, language
    ├── API: POST /extract-text
    └── Output: Extracted text + metadata
```

**Configuration:**
- `OCR_SERVICE_URL`: Base URL for OCR service
- `OCR_TIMEOUT`: Request timeout

---

## Utility Functions

### 1. **PDF Utils** (`pdf_utils.py`)

```
extract_pdf_text(base64_data)
    │
    ├── Decode base64 → bytes
    ├── Parse with PyPDF2
    ├── Extract text from all pages
    └── Return formatted text

is_valid_pdf_base64(base64_data)
    │
    ├── Decode base64
    ├── Check magic bytes (%PDF)
    └── Return True/False
```

---

### 2. **Token Tracker** (`token_tracker_pg.py`)

```
PostgreSQLTokenTracker
    │
    ├── increment_tokens(user_id, tokens)
    │   ├── Fetch current usage from DB
    │   ├── Check if reset needed (24h)
    │   ├── Update or create record
    │   └── Return usage info
    │
    ├── get_usage(user_id)
    │   ├── Fetch record
    │   ├── Check expiration
    │   └── Return current usage
    │
    └── reset_user(user_id)
        ├── Delete usage record
        └── Return success/fail
```

---

## Data Flow Examples

### Example 1: Simple Text Chat

```
User → API → Orchestrator → LM Studio → Response
         │                       
         └─→ Database (save messages)
```

**Detailed Flow:**
1. User sends: `{"message": "Hello", "user_id": "1"}`
2. `orcha_chat()` endpoint receives request
3. `handle_chat_request()` orchestrates:
   - Create/get conversation
   - Store user message
   - Build system prompt + message
   - Call LM Studio
   - Store assistant message
   - Track tokens
4. Return response to user

---

### Example 2: Chat with PDF Attachment

```
User (PDF) → API → Orchestrator → pdf_utils → LM Studio → Response
                        │              │
                        │              └─→ Extract text
                        │
                        └─→ Database (save all)
```

**Detailed Flow:**
1. User sends: `{"message": "Summarize this", "attachments": [{type: "application/pdf", data: "base64..."}]}`
2. `handle_chat_request()` processes:
   - Detect PDF attachment
   - Extract text using `extract_pdf_text()`
   - Enhance prompt with PDF content
   - Call LM Studio with enhanced prompt
   - Store messages
3. Return summary response

---

### Example 3: Chat with Image (Vision Mode)

```
User (Image) → API → Orchestrator → LM Studio (Vision) → Response
                         │              │
                         │              └─→ Vision model
                         │
                         └─→ Database (save)
```

**Detailed Flow:**
1. User sends: `{"message": "What's in this image?", "attachments": [{type: "image/jpeg", data: "base64..."}]}`
2. `handle_chat_request()` processes:
   - Detect vision attachment via `has_vision_attachments()`
   - Format message with image_url content
   - Call LM Studio with vision model
   - Store messages
3. Return image description

---

### Example 4: Chat with RAG (URI-based Image)

```
User (URI) → API → Orchestrator → OCR Service → Extract text
                      │               │
                      │               └─→ RAG Service → Ingest
                      │
                      └─→ RAG Query → Get contexts → LM Studio → Response
```

**Detailed Flow:**
1. User sends: `{"message": "What's in this doc?", "attachments": [{uri: "https://..."}]}`
2. `handle_chat_request()` processes:
   - Call OCR service for URI
   - Ingest OCR result into RAG
   - Query RAG for contexts
   - Build prompt with RAG contexts
   - Call LM Studio
   - Store messages
3. Return answer with RAG context

---

### Example 5: OCR Text Extraction

```
User (Image) → API → Orchestrator → OCR Service → Extract → Return
```

**Detailed Flow:**
1. User sends: `{"image_data": "base64...", "language": "en"}`
2. `orcha_ocr_extract()` calls `handle_ocr_extract()`
3. `extract_text_from_image()` sends to OCR service
4. Return extracted text immediately

---

### Example 6: Memory Extraction Request

```
User → API → Orchestrator → Special System Prompt → LM Studio
         │                                               │
         └─→ Load conversation history                  │
                                                         ▼
                                                      Response
                                                   (Memory facts)
```

**Detailed Flow:**
1. User sends: `{"message": "Based on my recent messages, extract and remember my preferences"}`
2. `handle_chat_request()` detects memory request:
   - Uses unrestricted system prompt
   - Loads full conversation history
   - Calls LM Studio
   - Returns structured memory facts
3. Frontend saves to memory system

---

## Helper Functions Deep Dive

### `has_vision_attachments(attachments)`

```
Purpose: Detect if images suitable for vision processing

Flow:
├── Check if attachments exist
├── Iterate through attachments
├── Find images with base64 data
│   └── type.startsWith("image/") AND has data
└── Return (has_images: bool, vision_images: List)

Example Output:
(True, [
  {
    "data": "base64string...",
    "type": "image/jpeg",
    "filename": "photo.jpg"
  }
])
```

---

## Configuration Settings

### Environment Variables (from `app/config.py`)

```python
# LM Studio
LMSTUDIO_URL             # e.g., http://localhost:1234
LMSTUDIO_VISION_MODEL    # e.g., llava-1.5
LM_TIMEOUT               # e.g., 60 seconds

# RAG Service
RAG_SERVICE_URL          # Vector database service
RAG_TIMEOUT              # e.g., 30 seconds

# OCR Service
OCR_SERVICE_URL          # Tesseract-based service
OCR_TIMEOUT              # e.g., 60 seconds

# Database
DATABASE_URL             # PostgreSQL connection string
```

---

## Key Design Patterns

### 1. **Smart Attachment Handling**
- Base64 data → Direct processing (PDFs, images for vision)
- URI → OCR + RAG ingestion (legacy flow)

### 2. **Conversation Management**
- Auto-create conversations if not provided
- Auto-generate titles from first message
- Track all messages with metadata
- Support soft deletes

### 3. **Error Handling**
- Try-catch at every external service call
- Graceful degradation (e.g., RAG failure doesn't break chat)
- Store error messages in database
- Return structured errors to client

### 4. **Token Tracking**
- 24-hour rolling window
- PostgreSQL-based (no Redis dependency)
- Non-blocking (failures don't break requests)
- Per-user tracking

### 5. **Context Building**
- System prompt (specialized or unrestricted)
- RAG contexts (if available)
- Conversation history from DB
- Current user message (enhanced with attachments)

---

## Performance Considerations

### Database Queries
- Use `select()` with filters to minimize data load
- Paginate conversation lists (limit/offset)
- Only load necessary history (last 10 messages)
- Eager cache conversation title to avoid lazy loads

### External Services
- Configurable timeouts for all services
- Async HTTP calls (httpx.AsyncClient)
- Parallel processing where possible
- Fail gracefully on service errors

### Memory Management
- Truncate RAG contexts (first 800 chars per context)
- Limit conversation history (10 messages)
- Limit vision tokens (max_tokens=1024)
- Clean JSON serialization for API responses

---

## Testing Entry Points

Based on project structure:

```
test_conversation_system.py     → Test conversation flow
test_ocr_integration.py         → Test OCR services
test_token_tracking.py          → Test token usage
test_lmstudio.py                → Test LM Studio connection
test_db_connection.py           → Test database
```

---

## Future Enhancements

### Potential Improvements:
1. **Streaming Responses**: Support SSE for real-time LLM output
2. **Batch Processing**: Handle multiple documents at once
3. **Caching**: Redis cache for frequent RAG queries
4. **Rate Limiting**: Per-user request throttling
5. **Analytics**: Track usage patterns and model performance
6. **Multi-modal**: Support audio/video attachments
7. **Fine-tuning**: Custom model training based on user data

---

## Quick Reference: Method Interactions

```
┌──────────────────────────────────────────────────────────┐
│                   METHOD CALL TREE                        │
└──────────────────────────────────────────────────────────┘

endpoints.orcha_chat()
    └─→ orchestrator.handle_chat_request()
            ├─→ has_vision_attachments()
            ├─→ pdf_utils.extract_pdf_text()
            ├─→ ocr_client.call_ocr()
            ├─→ rag_client.rag_ingest()
            ├─→ rag_client.rag_query()
            ├─→ chatbot_client.call_lmstudio_chat()
            └─→ token_tracker_pg.increment_tokens()

endpoints.orcha_ocr_extract()
    └─→ orchestrator.handle_ocr_extract()
            └─→ ocr_client.extract_text_from_image()

endpoints.orcha_rag_query()
    └─→ orchestrator.handle_rag_query()
            └─→ rag_client.rag_query()

endpoints.orcha_ingest()
    └─→ orchestrator.handle_ingest_request()
            └─→ rag_client.rag_ingest()

endpoints.get_token_usage()
    └─→ token_tracker_pg.get_usage()

endpoints.get_user_conversations()
    └─→ Database queries (Conversation, ChatMessage)

endpoints.get_pulse()
    └─→ pulse_service.get_user_pulse()
```

---

## Summary

The Orchestrator system is a sophisticated AI chat platform that:

✅ **Manages conversations** with full history tracking  
✅ **Processes multiple attachment types** (PDFs, images, URIs)  
✅ **Integrates vision AI** for image understanding  
✅ **Uses RAG** for knowledge-enhanced responses  
✅ **Tracks token usage** per user with 24h windows  
✅ **Supports OCR** for document text extraction  
✅ **Handles errors gracefully** with fallbacks  
✅ **Stores everything** in PostgreSQL for persistence  
✅ **Provides REST API** for easy integration  

The architecture is **modular**, **extensible**, and **production-ready** with comprehensive error handling and monitoring capabilities.

---

*Generated: 2025-11-02*  
*Based on: ORCHA codebase analysis*

