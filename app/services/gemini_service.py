# app/services/gemini_service.py
"""
Google Gemini 2.5 API integration for Pro Mode.
Uses the new google-genai SDK for Gemini 2.5 Flash model.
"""

from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from app.config import settings

# Get API key and model from settings (loaded from .env)
GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_MODEL = settings.GEMINI_MODEL

# Initialize the Gemini client
_client = genai.Client(api_key=GEMINI_API_KEY)


class GeminiServiceError(Exception):
    """Custom exception for Gemini service errors"""
    pass


class GeminiRateLimitError(GeminiServiceError):
    """Exception raised when hitting Gemini rate limit"""
    pass


class GeminiSafetyError(GeminiServiceError):
    """Exception raised when content is blocked by safety filters"""
    pass


def _convert_messages_to_gemini_format(messages: List[Dict[str, str]]) -> tuple[List[types.Content], Optional[str]]:
    """
    Convert OpenAI-style messages to Gemini 2.5 format.
    
    OpenAI format:
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, ...]
    
    Gemini 2.5 format:
        [types.Content(role="user", parts=[types.Part.from_text(...)]), ...]
    
    Note: Gemini doesn't have a "system" role - we extract it separately.
    
    Args:
        messages: List of OpenAI-format message dicts
    
    Returns:
        Tuple of (gemini_contents, system_instruction)
    """
    formatted_contents = []
    system_instruction = None
    
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        if role == "system":
            # Extract system instruction for separate handling
            system_instruction = content
        elif role == "user":
            formatted_contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=content)]
                )
            )
        elif role == "assistant":
            # OpenAI "assistant" -> Gemini "model"
            formatted_contents.append(
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=content)]
                )
            )
    
    return formatted_contents, system_instruction


async def call_gemini_chat(
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Call Google Gemini 2.5 API with chat messages.
    
    Args:
        messages: List of message dicts with 'role' and 'content' (OpenAI format)
                  Example: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        max_tokens: Maximum tokens to generate (default: 1024)
        temperature: Sampling temperature (default: 0.7)
        timeout: Request timeout in seconds (default: 60)
    
    Returns:
        Dict with response data in OpenAI-compatible format:
        {
            "choices": [{"message": {"role": "assistant", "content": "..."}}],
            "usage": {"prompt_tokens": ..., "completion_tokens": ..., "total_tokens": ...},
            "model": "gemini-2.5-flash"
        }
    
    Raises:
        GeminiRateLimitError: If hitting the rate limit
        GeminiSafetyError: If content is blocked by safety filters
        GeminiServiceError: For other API errors
    """
    
    if not messages:
        raise GeminiServiceError("messages parameter is required")
    
    # Use defaults if not specified
    max_tokens = max_tokens or 1024
    temperature = temperature or 0.7
    
    try:
        # Convert messages to Gemini 2.5 format
        formatted_contents, system_instruction = _convert_messages_to_gemini_format(messages)
        
        # Configure generation parameters
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Add system instruction if provided
        if system_instruction:
            config.system_instruction = system_instruction
        
        # Call the Gemini 2.5 API
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=formatted_contents,
            config=config
        )
        
        # Extract the response text
        assistant_message = response.text if response.text else ""
        
        # Estimate token usage (Gemini doesn't always provide exact counts)
        prompt_tokens = sum(len(msg.get("content", "")) // 4 for msg in messages)
        completion_tokens = len(assistant_message) // 4
        
        # Build OpenAI-compatible response
        result = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": assistant_message
                    }
                }
            ],
            "model": GEMINI_MODEL,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }
        
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for rate limit errors
        if any(keyword in error_msg for keyword in ["rate limit", "quota", "429", "resource exhausted"]):
            raise GeminiRateLimitError(
                "Pro Mode is currently busy (rate limit reached). Please try again in a moment."
            )
        
        # Check for safety/content filter errors
        if any(keyword in error_msg for keyword in ["safety", "blocked", "harmful", "dangerous"]):
            raise GeminiSafetyError(
                "Your request was blocked by content safety filters. Please rephrase your message."
            )
        
        # Check for API key errors
        if any(keyword in error_msg for keyword in ["api key", "invalid", "unauthorized", "401", "403"]):
            raise GeminiServiceError("Pro Mode API authentication failed. Please contact support.")
        
        # Check for model not found errors
        if any(keyword in error_msg for keyword in ["not found", "404", "model"]):
            raise GeminiServiceError(f"Model not available: {GEMINI_MODEL}. Please contact support.")
        
        # Generic error with details
        print(f"❌ Pro Mode (Gemini) Error: {e}")
        raise GeminiServiceError(f"Pro Mode API error: {str(e)}")


async def test_gemini_connection() -> bool:
    """
    Test the Gemini API connection with a simple message.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        test_messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        response = await call_gemini_chat(test_messages, max_tokens=10, timeout=10)
        
        return bool(response.get("choices"))
    
    except Exception:
        return False
