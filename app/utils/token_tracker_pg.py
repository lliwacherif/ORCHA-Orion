# app/utils/token_tracker_pg.py
"""
PostgreSQL-based token tracking (replaces Redis version).
Tracks token usage per user with 24-hour rolling window.
"""
from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import TokenUsage

class PostgreSQLTokenTracker:
    """Track token usage using PostgreSQL database."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def increment_tokens(
        self, 
        user_id: int, 
        tokens_used: int,
        logger = None
    ) -> Dict[str, any]:
        """
        Increment token count for a user and return current usage.
        Automatically resets after 24 hours.
        
        Args:
            user_id: User ID (integer from users table)
            tokens_used: Number of tokens to add
            logger: Optional logger for debugging
        
        Returns:
            Dict with current_usage, tokens_added, reset_at, tracking_enabled
        """
        try:
            # Fetch existing record
            result = await self.db.execute(
                select(TokenUsage).where(TokenUsage.user_id == user_id)
            )
            usage_record = result.scalar_one_or_none()
            
            now = datetime.utcnow()
            
            # If no record or reset time passed, create/reset
            if usage_record is None or now >= usage_record.reset_at:
                reset_at = now + timedelta(hours=24)
                
                if usage_record is None:
                    # Create new record
                    usage_record = TokenUsage(
                        user_id=user_id,
                        total_tokens=tokens_used,
                        reset_at=reset_at,
                        last_updated=now
                    )
                    self.db.add(usage_record)
                    if logger:
                        logger.info(f"🎯 Started new 24h tracking window for user {user_id}")
                else:
                    # Reset existing record
                    usage_record.total_tokens = tokens_used
                    usage_record.reset_at = reset_at
                    usage_record.last_updated = now
                    if logger:
                        logger.info(f"🔄 Reset token tracking for user {user_id}")
                
                await self.db.commit()
                await self.db.refresh(usage_record)
                
                return {
                    "current_usage": tokens_used,
                    "tokens_added": tokens_used,
                    "reset_at": reset_at.isoformat(),
                    "tracking_enabled": True,
                    "time_until_reset": str(reset_at - now)
                }
            
            else:
                # Increment existing usage
                old_usage = usage_record.total_tokens
                usage_record.total_tokens += tokens_used
                usage_record.last_updated = now
                
                await self.db.commit()
                await self.db.refresh(usage_record)
                
                if logger:
                    logger.info(f"📊 User {user_id}: {old_usage} → {usage_record.total_tokens} tokens (+{tokens_used})")
                
                return {
                    "current_usage": usage_record.total_tokens,
                    "tokens_added": tokens_used,
                    "reset_at": usage_record.reset_at.isoformat(),
                    "tracking_enabled": True,
                    "time_until_reset": str(usage_record.reset_at - now)
                }
        
        except Exception as e:
            if logger:
                logger.error(f"❌ Token tracking failed for user {user_id}: {e}")
            # Gracefully fail - don't break the request
            return {
                "current_usage": 0,
                "tokens_added": tokens_used,
                "reset_at": None,
                "tracking_enabled": False,
                "error": str(e)
            }
    
    async def get_usage(self, user_id: int) -> Dict[str, any]:
        """
        Get current token usage for a user without incrementing.
        
        Returns:
            Dict with current_usage, reset_at
        """
        try:
            result = await self.db.execute(
                select(TokenUsage).where(TokenUsage.user_id == user_id)
            )
            usage_record = result.scalar_one_or_none()
            
            if usage_record is None:
                return {
                    "current_usage": 0,
                    "reset_at": None,
                    "tracking_enabled": True
                }
            
            now = datetime.utcnow()
            
            # Check if expired
            if now >= usage_record.reset_at:
                return {
                    "current_usage": 0,
                    "reset_at": None,
                    "tracking_enabled": True,
                    "note": "Usage window expired, will reset on next use"
                }
            
            return {
                "current_usage": usage_record.total_tokens,
                "reset_at": usage_record.reset_at.isoformat(),
                "tracking_enabled": True,
                "time_until_reset": str(usage_record.reset_at - now)
            }
        
        except Exception as e:
            return {
                "current_usage": 0,
                "reset_at": None,
                "tracking_enabled": False,
                "error": str(e)
            }
    
    async def reset_user(self, user_id: int) -> bool:
        """
        Manually reset a user's token count.
        Useful for admin operations or testing.
        """
        try:
            result = await self.db.execute(
                select(TokenUsage).where(TokenUsage.user_id == user_id)
            )
            usage_record = result.scalar_one_or_none()
            
            if usage_record:
                await self.db.delete(usage_record)
                await self.db.commit()
            
            return True
        except Exception:
            return False
























