"""
app/security/rate_limiter.py
─────────────────────────────
Redis-based sliding window rate limiter.
Falls back gracefully if Redis is unavailable.
"""

import logging
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# Try to import redis — graceful fallback for dev without Redis
try:
    import redis.asyncio as redis
    _redis_client = None

    async def _get_redis():
        global _redis_client
        if _redis_client is None:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return _redis_client

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available — rate limiting disabled.")


class RateLimiter:
    def __init__(
        self,
        max_requests: int = None,
        window_seconds: int = None,
    ):
        self.max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        self.window = window_seconds or settings.RATE_LIMIT_WINDOW

    async def check(self, identifier: str) -> None:
        """
        Check rate limit for identifier (IP address or API key).
        Raises HTTP 429 if limit exceeded.
        """
        if not REDIS_AVAILABLE:
            return  # Skip if Redis not configured

        try:
            r = await _get_redis()
            key = f"venkatgpt:rl:{identifier}"
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, self.window)
            if count > self.max_requests:
                logger.warning(f"Rate limit exceeded for {identifier}")
                raise HTTPException(
                    status_code=429,
                    detail=(
                        f"Too many requests. You can send {self.max_requests} "
                        f"messages per {self.window} seconds."
                    ),
                    headers={"Retry-After": str(self.window)},
                )
        except HTTPException:
            raise
        except Exception as e:
            # Don't block requests if Redis has issues
            logger.warning(f"Rate limiter Redis error: {e}")
