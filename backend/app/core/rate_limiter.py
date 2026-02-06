"""
Beagle Rate Limiter Module
Request rate limiting using SlowAPI
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings


def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    Uses user ID if authenticated, otherwise IP address.
    """
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user:
        return f"user:{user.user_id}"
    
    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["100/minute"],
    storage_uri=settings.redis_url,
    strategy="fixed-window"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded: {exc.detail}",
                "retry_after": getattr(exc, "retry_after", 60)
            }
        },
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))}
    )


# Rate limit decorators for different endpoints
def limit_execute():
    """Rate limit for code execution: 10/minute"""
    return limiter.limit(settings.rate_limit_execute)


def limit_chat():
    """Rate limit for chat messages: 30/minute"""
    return limiter.limit(settings.rate_limit_chat)


def limit_upload():
    """Rate limit for file uploads: 5/minute"""
    return limiter.limit(settings.rate_limit_upload)
