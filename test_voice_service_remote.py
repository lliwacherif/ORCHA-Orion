import sys
import os
import logging
from app.services.voice_service import voice_service
from app.config import settings

# Setup basic logging to see output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_voice")

def test_voice_setup():
    print("=== Testing Voice Service Configuration ===")
    
    # 1. Check Config
    print(f"API URL: {settings.SCALEWAY_API_URL}")
    print(f"API Key present: {'Yes' if settings.SCALEWAY_API_KEY else 'No'}")
    print(f"Model: {settings.WHISPER_MODEL_SIZE}")
    
    # 2. Check Service Init
    print("\nInitializing Client...")
    try:
        if not voice_service.client:
            voice_service._initialize_client()
        
        if voice_service.client:
            print("✅ VoiceService client initialized successfully.")
            print(f"Base URL: {voice_service.client.base_url}")
        else:
            print("❌ VoiceService client failed to initialize (is None).")
            
    except Exception as e:
        print(f"❌ Exception during initialization: {e}")
        import traceback
        traceback.print_exc()

    # 3. Check FFmpeg again just in case (imported via voice API usually)
    pass

if __name__ == "__main__":
    test_voice_setup()
