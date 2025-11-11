# Image Routing to Gemma Model - Implementation Guide

## Overview

This guide documents the implementation of automatic image attachment routing to the Gemma multimodal model in LM Studio.

## Implementation Summary

### ✅ What Was Implemented

The system now automatically detects image attachments and routes them to the Gemma model (running in LM Studio) for vision processing, while text-only messages continue to use the default gpt-oss20b model.

### Key Features

1. **Automatic Image Detection**
   - Detects images via `attachment.type == "image"`
   - Detects images via `attachment.mime` starting with `"image/"`
   - Supports both `base64` and `data` fields (frontend flexibility)

2. **Smart Routing**
   - **Images present** → Routes to Gemma model (`google/gemma-3-12b`)
   - **Text only** → Routes to default model (gpt-oss20b)

3. **Multiple Images Support**
   - Handles single or multiple images in one request
   - Each image is included in the multimodal payload

4. **Empty Text Handling**
   - If `message.text` is empty but image present
   - Automatically uses wrapper text: `"User provided image; analyze it"`

---

## Configuration

### Updated Files

#### 1. `app/config.py`
Added Gemma model configuration:

```python
GEMMA_MODEL: str = "google/gemma-3-12b"  # Gemma model in LM Studio for multimodal
```

**Environment Variable Support:**
You can override this in `.env`:
```env
GEMMA_MODEL=google/gemma-3-12b
```

---

## Code Changes

### 1. Image Detection (`app/services/orchestrator.py`)

**Function:** `has_vision_attachments(attachments: List) -> tuple[bool, List[Dict]]`

**Detection Logic:**
```python
# Check type field OR mime field for image detection
is_image = (attachment_type == "image" or 
           attachment_type.startswith("image/") or 
           mime_type.startswith("image/"))

# Frontend sends base64 in "base64" field, fallback to "data"
attachment_data = a.get("base64") or a.get("data")
```

**Returns:**
- `has_images` (bool): True if any images found
- `vision_images` (List): List of dicts with `{"base64": str, "type": str, "filename": str}`

### 2. Routing Logic (`app/services/orchestrator.py`)

**When Images Detected:**
```python
if has_vision:
    # Build multimodal content array
    text_content = enhanced_message if enhanced_message.strip() else "User provided image; analyze it"
    
    content = [{"type": "text", "text": text_content}]
    
    # Add each image
    for img in vision_images:
        base64_data = img["base64"]
        # Strip data URL prefix if present
        if base64_data.startswith("data:"):
            base64_data = base64_data.split(",", 1)[1]
        
        img_format = img["type"].split("/")[1] if "/" in img["type"] else "jpeg"
        
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{img_format};base64,{base64_data}"
            }
        })
    
    messages.append({"role": "user", "content": content})
    
    # Route to Gemma
    resp = await call_lmstudio_chat(
        messages, 
        model=settings.GEMMA_MODEL,  # Use Gemma for images
        max_tokens=2048,
        timeout=settings.LM_TIMEOUT
    )
```

**When Text Only:**
```python
else:
    # Standard text message
    messages.append({"role": "user", "content": enhanced_message})
    
    # Route to default model
    resp = await call_lmstudio_chat(
        messages, 
        model=None,  # Use default loaded model (gpt-oss20b)
        timeout=settings.LM_TIMEOUT
    )
```

---

## Frontend Integration

### Expected Payload Format

The frontend should send attachments in this format:

#### Option 1: Using `type` field
```json
{
  "message": "What's in this image?",
  "attachments": [
    {
      "type": "image",
      "base64": "iVBORw0KGgoAAAANS...",
      "filename": "photo.jpg"
    }
  ]
}
```

#### Option 2: Using `mime` field
```json
{
  "message": "Analyze this",
  "attachments": [
    {
      "type": "file",
      "mime": "image/jpeg",
      "base64": "iVBORw0KGgoAAAANS...",
      "filename": "photo.jpg"
    }
  ]
}
```

#### Option 3: Multiple images
```json
{
  "message": "Compare these images",
  "attachments": [
    {
      "type": "image",
      "mime": "image/jpeg",
      "base64": "...",
      "filename": "image1.jpg"
    },
    {
      "type": "image",
      "mime": "image/png",
      "base64": "...",
      "filename": "image2.png"
    }
  ]
}
```

#### Option 4: Empty text with image
```json
{
  "message": "",
  "attachments": [
    {
      "type": "image",
      "base64": "...",
      "filename": "photo.jpg"
    }
  ]
}
```
*Backend automatically adds: "User provided image; analyze it"*

---

## Response Format

### With Images (Vision Processing)

```json
{
  "status": "ok",
  "message": "The image shows...",
  "conversation_id": 123,
  "model_response": { ... },
  "token_usage": { ... },
  "attachments_processed": 1,
  "vision_processed": true,
  "images_count": 1,
  "model_used": "google/gemma-3-12b",
  "image_filenames": ["photo.jpg"]
}
```

### Text Only (Standard Processing)

```json
{
  "status": "ok",
  "message": "Here's my response...",
  "conversation_id": 123,
  "model_response": { ... },
  "token_usage": { ... }
}
```

---

## Logging

### What to Look For

When an image is processed, you'll see these log entries:

```
🎨 Routing to Gemma model in LM Studio with 1 image(s)
🎨 Model: google/gemma-3-12b
  📷 Image 1: photo.jpg (image/jpeg)
  📷 Added image to content: photo.jpg (format: jpeg)
✅ Gemma response received
```

For text-only:
```
📝 Routing to LM Studio (text-only) with 5 messages
```

---

## Testing

### Manual Test Steps

1. **Load Gemma in LM Studio**
   - Open LM Studio
   - Load the `google/gemma-3-12b` model
   - Ensure it's running on the configured port (default: 1234)

2. **Send Test Request via Frontend**
   ```javascript
   const formData = {
     message: "What do you see?",
     attachments: [{
       type: "image",
       mime: "image/jpeg",
       base64: "<base64-image-data>",
       filename: "test.jpg"
     }]
   };
   
   const response = await fetch('/api/v1/chat', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify(formData)
   });
   ```

3. **Check Response**
   - Should contain `"vision_processed": true`
   - Should contain `"model_used": "google/gemma-3-12b"`
   - Should have vision-based response

### Automated Test

Run the test script:
```bash
python test_image_routing.py
```

Tests:
- ✅ Image detection with `type="image"`
- ✅ Image detection with `mime="image/*"`
- ✅ Multiple images
- ✅ Text-only (no false positives)
- ✅ Mixed attachments (PDF + Image)
- ✅ Legacy `data` field support

---

## Troubleshooting

### Issue: Images not being detected

**Check:**
1. Attachment has `type="image"` OR `mime` starting with `"image/"`
2. Attachment has `base64` or `data` field with actual base64 data
3. Check logs for "🖼️ Image attachment detected" message

### Issue: Routing to wrong model

**Check:**
1. `has_vision` is True (check logs)
2. `GEMMA_MODEL` is set correctly in config
3. Gemma model is loaded in LM Studio

### Issue: Empty response

**Check:**
1. Gemma model is actually loaded and running in LM Studio
2. Check LM Studio console for errors
3. Verify base64 data is valid image format
4. Check timeout settings (multimodal may need more time)

### Issue: Base64 format errors

**Check:**
1. Base64 data doesn't have data URL prefix already
   - ❌ `"data:image/jpeg;base64,iVBORw..."`
   - ✅ `"iVBORw..."`
   - System automatically strips prefix if present

---

## Architecture Diagram

```
Frontend
   │
   │ Sends: { message, attachments[] }
   │
   ▼
Orchestrator (handle_chat_request)
   │
   ├─► has_vision_attachments()
   │   └─► Detects: type=="image" OR mime startsWith "image/"
   │
   ├─► If images found:
   │   │
   │   ├─► Build multimodal content array
   │   │   ├─► Text: message or "User provided image; analyze it"
   │   │   └─► Images: [{"type": "image_url", "image_url": {...}}]
   │   │
   │   └─► call_lmstudio_chat(
   │         model=GEMMA_MODEL,  ← google/gemma-3-12b
   │         messages=[..., {"role": "user", "content": [text, images]}]
   │       )
   │
   └─► If text only:
       │
       └─► call_lmstudio_chat(
             model=None,  ← Default gpt-oss20b
             messages=[..., {"role": "user", "content": text}]
           )
```

---

## Future Enhancements

### Potential Improvements

1. **OCR for Images**
   - Add OCR fallback if vision model unavailable
   - Extract text from images for RAG ingestion

2. **Image Validation**
   - Validate image size before processing
   - Compress large images automatically

3. **Model Selection**
   - Allow frontend to specify vision model
   - Support multiple vision models (Gemma, LLaVA, etc.)

4. **Caching**
   - Cache vision results for identical images
   - Reduce redundant processing

5. **Metadata Extraction**
   - Extract EXIF data from images
   - Include in context for better responses

---

## API Reference

### `has_vision_attachments(attachments: List)`

**Parameters:**
- `attachments` (List): List of attachment dictionaries

**Returns:**
- `tuple[bool, List[Dict]]`: (has_images, vision_attachments)

**Example:**
```python
attachments = [{"type": "image", "base64": "...", "filename": "test.jpg"}]
has_images, vision_images = has_vision_attachments(attachments)
# has_images = True
# vision_images = [{"base64": "...", "type": "image", "filename": "test.jpg"}]
```

---

## Configuration Summary

### Environment Variables

Add to `.env` file:
```env
# Gemma Model Configuration
GEMMA_MODEL=google/gemma-3-12b

# LM Studio Configuration
LMSTUDIO_URL=http://192.168.1.37:1234
LM_TIMEOUT=500
```

### Database Schema

No database changes required. Existing `ChatMessage` model tracks:
- `model_used`: Records which model processed the message
- `attachments`: Stores attachment metadata (JSON)

---

## Success Criteria

✅ **Implementation Complete When:**

1. Image attachments are automatically detected
2. Images route to Gemma model in LM Studio
3. Text-only routes to default model (gpt-oss20b)
4. Multiple images are supported
5. Empty text with image uses wrapper text
6. Response includes vision processing metadata
7. Logs show correct routing decisions
8. Frontend receives vision-processed responses

---

## Support

For issues or questions:
1. Check logs for routing decisions
2. Verify Gemma is loaded in LM Studio
3. Test with `test_image_routing.py`
4. Review this guide's troubleshooting section

---

**Implementation Date:** November 3, 2025  
**Status:** ✅ Complete and Ready for Testing















