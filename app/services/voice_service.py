# app/services/voice_service.py
import os
from openai import OpenAI
from app.config import settings
from app.utils.logging import logger

class VoiceService:
    _instance = None
    client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoiceService, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance
    
    def _initialize_client(self):
        """Initialize the OpenAI client for Scaleway."""
        try:
            logger.info("Initializing Scaleway Whisper client...", extra={"trace_id": "startup"})
            self.client = OpenAI(
                base_url=settings.SCALEWAY_API_URL,
                api_key=settings.SCALEWAY_API_KEY
            )
            logger.info("✅ Scaleway Whisper client initialized", extra={"trace_id": "startup"})
        except Exception as e:
            logger.error(f"❌ Failed to initialize Scaleway client: {e}", extra={"trace_id": "startup"})
            self.client = None

    def transcribe(self, file_path: str, language: str = "fr") -> str:
        """
        Transcribe audio file to text using Scaleway Whisper API.
        
        Args:
            file_path: Path to the audio file (mp3, wav, flac, etc.)
            language: Language code (default: "fr" for French)
            
        Returns:
            Transcribed text string
        """
        if not self.client:
            self._initialize_client()
            if not self.client:
                raise RuntimeError("Scaleway client is not initialized")
        
        try:
            logger.info(f"Transcribing file: {file_path}", extra={"trace_id": "voice_service"})
            
            # Verify file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            with open(file_path, 'rb') as f:
                transcript = self.client.audio.transcriptions.create(
                    model=settings.WHISPER_MODEL_SIZE,
                    file=f,
                    prompt="Tu es un assistant utile.",  # Context prompt
                    language=language
                )
            
            transcribed_text = transcript.text
            logger.info(f"Transcription successful: {transcribed_text[:50]}...", extra={"trace_id": "voice_service"})
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Scaleway Transcription error: {e}", extra={"trace_id": "voice_service"})
            raise e

# Global singleton instance
voice_service = VoiceService()
