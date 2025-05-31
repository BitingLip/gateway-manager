"""
Authentication and dependency injection utilities
"""

from fastapi import HTTPException, Depends, Request, Header, status
from typing import Optional, Annotated
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)


async def verify_api_key_if_configured(
    request: Request,  # For logging context
    authorization: Annotated[Optional[str], Header()] = None  # Explicitly get Authorization header
):
    """
    Verify API key if configured, otherwise allow access
    """
    if settings.api_key:  # API key is configured, authentication is REQUIRED
        if not authorization:
            logger.warning("API key required, but no Authorization header provided.", url=str(request.url))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated. Authorization header is missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            scheme, credentials = authorization.split()
            if scheme.lower() != "bearer":
                logger.warning(f"Invalid authentication scheme: {scheme}. Expected Bearer.", url=str(request.url))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme. Use Bearer token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if credentials != settings.api_key:
                logger.warning("Invalid API key provided.", url=str(request.url))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError:  # Handles case where split() fails (e.g., header doesn't have a space)
            logger.warning("Malformed Authorization header. Expected 'Bearer <token>'.", url=str(request.url))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed Authorization header. Expected 'Bearer <token>'.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug("API key authentication successful.", url=str(request.url), user_provided_scheme=scheme)
        return credentials  # Or a user object if you map keys to users
    else:
        # API key is not configured, allow unauthenticated access
        logger.debug("API key not configured. Allowing unauthenticated access.", url=str(request.url))
        if authorization:  # Log if auth was sent anyway but not checked
            logger.info("Authorization header present but API key not configured; access allowed.", url=str(request.url))
        return None  # No user/credentials to return, access is granted


# This single dependency will be used by routes that need conditional auth
AUTH_DEPENDENCY = Depends(verify_api_key_if_configured)
