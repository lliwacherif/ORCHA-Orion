# app/tasks/pulse_scheduler.py
"""
Pulse Scheduler - Automatically generates daily pulses for all active users.
This runs as a background task every 24 hours.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import User, Pulse
from app.services.pulse_service import update_user_pulse

logger = logging.getLogger(__name__)


async def generate_pulses_for_all_users():
    """
    Generate pulses for all active users.
    This is called by the scheduler every 24 hours.
    """
    logger.info("🔄 Starting pulse generation for all users")
    
    async with AsyncSessionLocal() as db_session:
        try:
            # Get all active users
            result = await db_session.execute(
                select(User).where(User.is_active == True)
            )
            users = result.scalars().all()
            
            logger.info(f"Found {len(users)} active users")
            
            success_count = 0
            fail_count = 0
            
            for user in users:
                try:
                    logger.info(f"Generating pulse for user {user.id} ({user.username})")
                    success = await update_user_pulse(user.id, db_session)
                    
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to generate pulse for user {user.id}: {e}")
                    fail_count += 1
            
            logger.info(f"✅ Pulse generation complete: {success_count} succeeded, {fail_count} failed")
            
        except Exception as e:
            logger.error(f"Failed to generate pulses: {e}")
            import traceback
            logger.error(traceback.format_exc())


async def check_and_generate_due_pulses():
    """
    Check for users whose pulses are due for regeneration and update them.
    This can run more frequently to catch any missed generations.
    """
    logger.info("🔍 Checking for due pulse generations")
    
    async with AsyncSessionLocal() as db_session:
        try:
            now = datetime.utcnow()
            
            # Get pulses that are due for regeneration
            result = await db_session.execute(
                select(Pulse).where(Pulse.next_generation <= now)
            )
            due_pulses = result.scalars().all()
            
            if not due_pulses:
                logger.info("No pulses due for regeneration")
                return
            
            logger.info(f"Found {len(due_pulses)} pulses due for regeneration")
            
            for pulse in due_pulses:
                try:
                    logger.info(f"Regenerating pulse for user {pulse.user_id}")
                    await update_user_pulse(pulse.user_id, db_session)
                except Exception as e:
                    logger.error(f"Failed to regenerate pulse for user {pulse.user_id}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to check due pulses: {e}")


async def pulse_scheduler_loop():
    """
    Main scheduler loop that runs continuously.
    Generates pulses every 24 hours.
    """
    logger.info("🚀 Pulse scheduler started")
    
    while True:
        try:
            # Generate pulses for all users
            await generate_pulses_for_all_users()
            
            # Wait 24 hours before next generation
            logger.info("😴 Sleeping for 24 hours until next pulse generation")
            await asyncio.sleep(24 * 60 * 60)  # 24 hours
            
        except Exception as e:
            logger.error(f"Error in pulse scheduler loop: {e}")
            # Wait 1 hour before retrying on error
            await asyncio.sleep(60 * 60)


async def pulse_checker_loop():
    """
    Checker loop that runs every hour to catch any missed pulse generations.
    """
    logger.info("🔍 Pulse checker started")
    
    # Wait 5 minutes before first check (to let main scheduler run first)
    await asyncio.sleep(5 * 60)
    
    while True:
        try:
            await check_and_generate_due_pulses()
            
            # Check every hour
            await asyncio.sleep(60 * 60)
            
        except Exception as e:
            logger.error(f"Error in pulse checker loop: {e}")
            await asyncio.sleep(60 * 60)


# Export the scheduler functions
__all__ = [
    "generate_pulses_for_all_users",
    "check_and_generate_due_pulses",
    "pulse_scheduler_loop",
    "pulse_checker_loop"
]
