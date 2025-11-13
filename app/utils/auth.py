"""
Authentication and Authorization Utilities
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.utils.config import get_settings
import logging

logger = logging.getLogger(__name__)

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    settings = get_settings()

    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return api_key


async def get_optional_api_key(api_key: str = Security(api_key_header)) -> str | None:
    """
    Optional API key verification
    Returns None if no key provided or invalid
    """
    try:
        return await verify_api_key(api_key)
    except HTTPException:
        return None
