# app/api/v1/voice.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
from app.services.voice_service import voice_service
# from app.services.orchestrator import handle_chat_request # Orchestrator might not be available or fully set up yet in this environment context, but kept as per request if needed. 
# Checking imports, orchestrator seems to be in app/services/orchestrator.py
from app.services.orchestrator import handle_chat_request
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import shutil
import os
import tempfile
import subprocess
import traceback
from app.utils.logging import logger

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives an audio file, transcribes it using Whisper,
    and returns the text and AI response.
    
    Supported formats: webm, mp3, wav, flac, ogg, m4a
    """
    if request:
        request.state.db_session = db
    
    temp_file_path = None
    converted_file_path = None
    final_file_path = None
    
    try:
        # 1. Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        if request and hasattr(request.state, "trace_id"):
            tid = request.state.trace_id
        else:
            tid = "voice_api"
            
        logger.info(f"Saved temp audio file to {temp_file_path}", extra={"trace_id": tid})
        
        # 2. Convert to MP3 using FFmpeg (Scaleway supports: flac, mp3, wav, ogg)
        # We only convert if it's NOT one of the supported formats, or just always convert to be safe/consistent?
        # The request says "Convert to MP3 using FFmpeg".
        converted_file_path = temp_file_path + ".mp3"
        
        try:
            logger.info("Converting audio to MP3 using ffmpeg...", extra={"trace_id": tid})
            
            # Determine ffmpeg path
            ffmpeg_cmd = _get_ffmpeg_path()
            
            # Check if input is already a supported format to potentially skip conversion if ffmpeg fails? 
            # But Scaleway might have strict requirements. Let's try conversion.
            
            command = [
                ffmpeg_cmd, 
                "-y",                    # Overwrite output
                "-i", temp_file_path,    # Input file
                "-vn",                   # Disable video
                "-ac", "1",              # Mono audio
                "-f", "mp3",             # Output format
                converted_file_path
            ]
            
            process = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
            
            logger.info(f"Conversion successful: {converted_file_path}", extra={"trace_id": tid})
            final_file_path = converted_file_path
            
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            error_msg = e.stderr.decode() if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
            logger.error(f"FFMPEG conversion failed or not found: {error_msg}", extra={"trace_id": tid})
            
            # If conversion failed, trying to use the original file if it looks compatible
            if suffix.lower() in [".mp3", ".wav", ".flac", ".ogg"]:
                logger.info(f"FFmpeg failed, but file format {suffix} might be supported directly. Trying original file.", extra={"trace_id": tid})
                final_file_path = temp_file_path
            else:
                 # If it was webm or something else, we really needed that conversion.
                return {
                    "status": "error",
                    "error": "Audio processing error",
                    "message": "Could not process audio. FFmpeg might be missing or the file format is invalid."
                }

        # 3. Transcribe using VoiceService
        if not final_file_path:
             raise HTTPException(status_code=500, detail="Failed to prepare audio file for transcription.")

        transcribed_text = voice_service.transcribe(final_file_path)
        logger.info(f"Transcribed Text: {transcribed_text}", extra={"trace_id": tid})
        
        if not transcribed_text:
            return {
                "status": "success",
                "transcription": "",
                "response": "I couldn't hear anything. Please try again."
            }
        
        # 4. Process with Orchestrator
        user_id = str(settings.DEFAULT_WIDGET_USER_ID) # Use constant or from auth
        
        chat_payload = {
            "user_id": user_id, 
            "message": transcribed_text,
            "use_rag": False,
            "use_pro_mode": False
        }
        
        # We need to ensure orchestrator is ready for this.
        chat_response = await handle_chat_request(chat_payload, request)
        response_text = chat_response.get("message", "")
        
        return {
            "status": "success",
            "transcription": transcribed_text,
            "response": response_text,
            "conversation_id": chat_response.get("conversation_id")
        }
        
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Voice processing error: {e}\nTraceback: {tb}", extra={"trace_id": "voice_api_error"})
        if "Invalid file format" in str(e):
            raise HTTPException(status_code=400, detail="Invalid audio format.")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temp files
        # We need to make sure we don't hold locks if possible, but OS remove should handle it if closed.
        # TempFile context manager usually deletes on close if delete=True, but we used delete=False.
        for path in [temp_file_path, converted_file_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {path}: {e}", extra={"trace_id": tid})

def _get_ffmpeg_path() -> str:
    """Determine the correct FFmpeg path for the current OS."""
    # Windows: Check local binary in app/bin
    if os.name == 'nt':
        local_ffmpeg = os.path.join(os.getcwd(), "app", "bin", "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            logger.info(f"Using local ffmpeg: {local_ffmpeg}", extra={"trace_id": "ffmpeg_check"})
            return local_ffmpeg
    
    # Check system path (works for both Linux and valid Windows PATH)
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        logger.info(f"Using system ffmpeg at: {system_ffmpeg}", extra={"trace_id": "ffmpeg_check"})
        return system_ffmpeg
        
    # Linux fallbacks
    if os.name != 'nt':
        common_paths = [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/snap/bin/ffmpeg",
            "/bin/ffmpeg"
        ]
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"Found ffmpeg at: {path}", extra={"trace_id": "ffmpeg_check"})
                return path
    
    logger.warning("ffmpeg not found, using default 'ffmpeg' command", extra={"trace_id": "ffmpeg_check"})
    return "ffmpeg"
