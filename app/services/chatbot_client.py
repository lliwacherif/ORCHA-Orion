# app/services/chatbot_client.py
import httpx
from app.config import settings
from typing import List, Optional

async def call_lmstudio_chat(
    messages: List[dict], 
    model: Optional[str] = None, 
    timeout: Optional[int] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
):
    """
    Call LM Studio's OpenAI-compatible chat completions API.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name (if None, LM Studio uses the loaded model)
        timeout: Request timeout in seconds
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens to generate
    
    Returns:
        Full API response from LM Studio
    """
    timeout = timeout or settings.LM_TIMEOUT
    url = f"{settings.LMSTUDIO_URL.rstrip('/')}/v1/chat/completions"
    
    payload = {
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    
    # Only add optional fields if provided
    if model:
        payload["model"] = model
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()

async def get_available_models():
    """Get list of available models from LM Studio."""
    url = f"{settings.LMSTUDIO_URL.rstrip('/')}/v1/models"
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()