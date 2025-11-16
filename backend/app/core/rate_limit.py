"""
Rate limiting middleware for FastAPI.
"""
import logging
from typing import Callable
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiting(app):
    """
    Setup rate limiting middleware for FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting middleware configured")


def get_limiter():
    """
    Get limiter instance for use with @limiter.limit decorator.
    
    Returns:
        Limiter: Rate limiter instance
    """
    return limiter

