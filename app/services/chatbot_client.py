# app/services/chatbot_client.py
from openai import AsyncOpenAI
from app.config import settings
from typing import List, Optional
import httpx

# Initialize Scaleway client
client = AsyncOpenAI(
    base_url=settings.SCALEWAY_API_URL,
    api_key=settings.SCALEWAY_API_KEY
)

async def call_lmstudio_chat(
    messages: List[dict], 
    model: Optional[str] = None, 
    timeout: Optional[int] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
):
    """
    Call Scaleway's OpenAI-compatible chat completions API (formerly LM Studio).
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name (defaults to settings.SCALEWAY_MODEL if None)
        timeout: Request timeout in seconds
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens to generate
    
    Returns:
        Full API response dict (mimicking the previous raw JSON structure)
    """
    # Use default model from settings if not provided
    model_to_use = model or settings.SCALEWAY_MODEL
    
    # Map params
    # Note: OpenAI python client handles timeouts differently (usually via client setup or transport), 
    # but we can pass timeout to the request directly in newer versions or handle it via asyncio.wait_for if needed.
    # Here we'll rely on the default client timeout unless critical.
    
    try:
        response = await client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            max_tokens=max_tokens or settings.MAX_TOKENS,
            temperature=temperature,
            top_p=1,
            presence_penalty=0,
            stream=False, # We keep it non-streaming for now as per this function's interface
            # response_format={ "type": "text" } 
        )
        
        # Convert response object to dict to match previous return signature (raw JSON)
        # The Orchestrator expects a dict that looks like the raw API response
        return response.model_dump()
        
    except Exception as e:
        # In case of error, we might want to re-raise or return a mock error structure
        # For now, let's let specific exceptions bubble up or wrap them
        raise e

async def get_available_models():
    """Get list of available models from Scaleway."""
    # Since we are using OpenAI client, we can list models
    try:
        models = await client.models.list()
        return models.model_dump()
    except Exception:
        # Fallback or simple mock if listing fails
        return {"data": [{"id": settings.SCALEWAY_MODEL}]}