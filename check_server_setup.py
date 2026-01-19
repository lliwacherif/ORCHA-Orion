import os
import sys
import shutil
import logging
import asyncio
from sqlalchemy import text
from app.db.database import engine

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_setup")

async def check_ffmpeg():
    print("-" * 20)
    print("Checking FFmpeg...")
    
    # Check PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"✅ FFmpeg found in PATH at: {ffmpeg_path}")
    else:
        print("⚠️ FFmpeg NOT found in PATH")
        
    # Check common paths
    common_paths = [
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/snap/bin/ffmpeg",
        "/bin/ffmpeg"
    ]
    found_alt = False
    for path in common_paths:
        if os.path.exists(path):
            print(f"✅ FFmpeg found at common path: {path}")
            found_alt = True
    
    if not ffmpeg_path and not found_alt:
        print("❌ FFmpeg NOT found anywhere standard.")
        
    # Test execution
    try:
        import subprocess
        cmd = ffmpeg_path if ffmpeg_path else "ffmpeg"
        result = subprocess.run([cmd, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print("✅ FFmpeg execution successful")
            print(result.stdout.decode().split('\n')[0])
        else:
            print(f"❌ FFmpeg execution failed with code {result.returncode}")
    except Exception as e:
        print(f"❌ Failed to execute ffmpeg: {e}")

async def check_db_column():
    print("-" * 20)
    print("Checking Database Metadata...")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='job_title'"
            ))
            col = result.fetchone()
            if col:
                print("✅ Column 'job_title' exists in 'users' table.")
            else:
                print("❌ Column 'job_title' MISSING in 'users' table.")
                print("   -> You MUST run: python migrate_add_user_job_title.py")
    except Exception as e:
        print(f"❌ Database check failed: {e}")

def check_logging():
    print("-" * 20)
    print("Checking Logging...")
    try:
        # Import the app logging config
        from app.utils.logging import logger as app_logger
        app_logger.info("Test log with trace_id", extra={"trace_id": "TEST"})
        app_logger.info("Test log WITHOUT trace_id") # Should pass if filter works
        print("✅ Logging configuration appears safe.")
    except Exception as e:
        print(f"❌ Logging configuration is crashing: {e}")

async def main():
    print("=== Server Setup Diagnostic ===")
    await check_ffmpeg()
    await check_db_column()
    check_logging()
    print("-" * 20)
    print("Diagnostic complete.")

if __name__ == "__main__":
    asyncio.run(main())
