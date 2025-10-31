# app/utils/token_tracker.py
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Optional, Dict

class TokenTracker:
    """
    Track token usage per user with 24-hour reset window.
    Uses Redis with expiring keys for automatic cleanup.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def _get_user_key(self, user_id: str) -> str:
        """Generate Redis key for user token tracking."""
        return f"token_usage:{user_id}"
    
    def _get_reset_time_key(self, user_id: str) -> str:
        """Generate Redis key for tracking reset timestamp."""
        return f"token_reset:{user_id}"
    
    async def increment_tokens(
        self, 
        user_id: str, 
        tokens_used: int,
        logger = None
    ) -> Dict[str, any]:
        """
        Increment token count for a user and return current usage.
        Automatically resets after 24 hours.
        
        Args:
            user_id: Unique user identifier
            tokens_used: Number of tokens to add
            logger: Optional logger for debugging
        
        Returns:
            Dict with current_usage, tokens_added, reset_at, limit_remaining
        """
        if not self.redis:
            # If Redis is not available, return dummy data
            return {
                "current_usage": 0,
                "tokens_added": tokens_used,
                "reset_at": None,
                "tracking_enabled": False
            }
        
        user_key = self._get_user_key(user_id)
        reset_key = self._get_reset_time_key(user_id)
        
        try:
            # Check if user has existing tracking
            current_usage = await self.redis.get(user_key)
            reset_time = await self.redis.get(reset_key)
            
            now = datetime.utcnow()
            
            # If no existing data or reset time passed, initialize new 24h window
            if current_usage is None or reset_time is None:
                # Start new tracking window
                current_usage = 0
                reset_at = now + timedelta(hours=24)
                
                # Set reset time (stored as ISO string)
                await self.redis.set(
                    reset_key, 
                    reset_at.isoformat(),
                    ex=86400  # Expire in 24 hours
                )
                
                if logger:
                    logger.info(f"🎯 Started new 24h tracking window for user {user_id}")
            else:
                current_usage = int(current_usage)
                reset_at = datetime.fromisoformat(reset_time.decode('utf-8'))
                
                # Check if reset time has passed (edge case if Redis didn't expire)
                if now >= reset_at:
                    current_usage = 0
                    reset_at = now + timedelta(hours=24)
                    await self.redis.set(
                        reset_key,
                        reset_at.isoformat(),
                        ex=86400
                    )
                    if logger:
                        logger.info(f"🔄 Reset token tracking for user {user_id}")
            
            # Increment usage
            new_usage = current_usage + tokens_used
            
            # Store new usage with same expiry as reset key (24h)
            await self.redis.set(
                user_key,
                new_usage,
                ex=86400  # Expire in 24 hours
            )
            
            if logger:
                logger.info(f"📊 User {user_id}: {current_usage} → {new_usage} tokens (+{tokens_used})")
            
            return {
                "current_usage": new_usage,
                "tokens_added": tokens_used,
                "reset_at": reset_at.isoformat(),
                "tracking_enabled": True,
                "time_until_reset": str(reset_at - now)
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
    
    async def get_usage(self, user_id: str) -> Dict[str, any]:
        """
        Get current token usage for a user without incrementing.
        
        Returns:
            Dict with current_usage, reset_at
        """
        if not self.redis:
            return {
                "current_usage": 0,
                "reset_at": None,
                "tracking_enabled": False
            }
        
        user_key = self._get_user_key(user_id)
        reset_key = self._get_reset_time_key(user_id)
        
        try:
            current_usage = await self.redis.get(user_key)
            reset_time = await self.redis.get(reset_key)
            
            if current_usage is None:
                return {
                    "current_usage": 0,
                    "reset_at": None,
                    "tracking_enabled": True
                }
            
            reset_at = datetime.fromisoformat(reset_time.decode('utf-8')) if reset_time else None
            now = datetime.utcnow()
            
            return {
                "current_usage": int(current_usage),
                "reset_at": reset_at.isoformat() if reset_at else None,
                "tracking_enabled": True,
                "time_until_reset": str(reset_at - now) if reset_at else None
            }
            
        except Exception as e:
            return {
                "current_usage": 0,
                "reset_at": None,
                "tracking_enabled": False,
                "error": str(e)
            }
    
    async def reset_user(self, user_id: str) -> bool:
        """
        Manually reset a user's token count.
        Useful for admin operations or testing.
        """
        if not self.redis:
            return False
        
        user_key = self._get_user_key(user_id)
        reset_key = self._get_reset_time_key(user_id)
        
        try:
            await self.redis.delete(user_key)
            await self.redis.delete(reset_key)
            return True
        except Exception:
            return False


