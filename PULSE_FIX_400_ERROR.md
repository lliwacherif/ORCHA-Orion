# Pulse 400 Error - Fix Applied

## Problem

When clicking the Pulse icon, frontend showed:
```
An error occurred while fetching your pulse
```

Backend logs showed:
```
Client error '400 Bad Request' for url 'http://192.168.1.37:1234/v1/chat/completions'
```

## Root Cause

The pulse generation was sending **too much text** to LM Studio:
- Analyzing 10 conversations with all messages
- Long messages not truncated
- No total context limit
- Could easily exceed model's token limit (~4000-8000 tokens)

## Fixes Applied

### 1. ✅ Reduced Conversation Count
```python
# Before: Analyzed last 10 conversations
.limit(10)

# After: Analyze last 5 conversations
.limit(5)
```

### 2. ✅ Added Message Truncation
```python
MAX_MESSAGE_LENGTH = 300  # Truncate individual messages
content = msg.content[:MAX_MESSAGE_LENGTH]
if len(msg.content) > MAX_MESSAGE_LENGTH:
    content += "... (truncated)"
```

### 3. ✅ Added Total Context Limit
```python
MAX_TOTAL_LENGTH = 4000  # Conservative limit to avoid 400 errors

if len(conversations_text) > MAX_TOTAL_LENGTH:
    conversations_text += "\n... (Additional conversations truncated)\n"
    break
```

### 4. ✅ Better Error Handling
```python
try:
    response = await call_lmstudio_chat(messages, timeout=120)
except Exception as llm_error:
    if "400" in str(llm_error):
        logger.error(f"Context size was {len(conversations_text)} chars")
        return "Pulse generation failed: Context too large."
    raise
```

### 5. ✅ Added Context Size Logging
```python
logger.info(f"📊 Context size: {len(conversations_text)} chars (~{len(conversations_text)//4} tokens)")
```

## Files Modified

- `app/services/pulse_service.py` - Added all fixes above

## Testing

### 1. Run Test Script
```bash
python test_pulse_generation.py 1
```

This will:
- Check if user has conversations
- Show context size
- Generate pulse
- Test API endpoint

### 2. Check Logs
Look for these in server logs:
```
📊 Context size: 2340 characters (~585 tokens)  # Should be under 4000
✅ Pulse generated successfully (1234 chars)
```

### 3. Try Frontend Again
Click the Pulse icon - should now work without 400 error.

## Configuration

You can adjust these limits in `pulse_service.py`:

```python
# Line 49: Number of conversations to analyze
.limit(5)  # Increase to 7 or 8 if needed

# Line 70-71: Context limits
MAX_MESSAGE_LENGTH = 300   # Individual message max
MAX_TOTAL_LENGTH = 4000    # Total context max
```

**⚠️ Warning:** If you increase these too much, you'll get 400 errors again.

## How to Adjust for Your Model

Different models have different context limits:

| Model | Max Tokens | Recommended MAX_TOTAL_LENGTH |
|-------|------------|------------------------------|
| Llama 3 8B | 8192 | 4000 chars |
| Llama 3 70B | 8192 | 6000 chars |
| GPT-4 | 8192 | 6000 chars |
| Claude | 100k | 20000 chars |

**Formula:** 1 token ≈ 4 characters (English text)

## Troubleshooting

### Still Getting 400 Errors?

1. **Check model context limit:**
   ```bash
   # In LM Studio, check model info
   # Look for "context_length" or "n_ctx"
   ```

2. **Reduce limits more:**
   ```python
   MAX_MESSAGE_LENGTH = 200  # Even shorter
   MAX_TOTAL_LENGTH = 2000   # Even smaller
   ```

3. **Check model is loaded:**
   - Open LM Studio
   - Ensure a model is selected and loaded
   - Test with a simple request first

### Empty Pulse?

User might not have enough conversations:
```sql
SELECT COUNT(*) FROM conversations WHERE user_id = 1 AND is_active = true;
```

Need at least 1-2 conversations with several messages.

### Takes Too Long?

Reduce timeout or conversation count:
```python
timeout=60  # 1 minute instead of 2
.limit(3)   # Only 3 conversations
```

## Success Indicators

After the fix, you should see:

✅ **Frontend:** Pulse displays correctly  
✅ **Logs:** No 400 errors  
✅ **Logs:** Shows context size under 4000 chars  
✅ **Response:** Comes back in 30-60 seconds  

## Summary

**Before:**
- ❌ 400 Bad Request errors
- ❌ Sending 10+ conversations
- ❌ No truncation
- ❌ Could send 20k+ characters

**After:**
- ✅ 200 OK responses
- ✅ Only 5 conversations
- ✅ Messages truncated at 300 chars
- ✅ Total limited to 4000 chars
- ✅ Better error messages
- ✅ Detailed logging

The pulse feature should now work reliably! 🎉
