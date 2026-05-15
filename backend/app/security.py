"""
API security: key-based auth + rate limiter.

API_KEY env var controls access to mutating endpoints.
If unset, all requests pass (dev mode).
The limiter instance is shared via import in main.py and route files.
"""
import os
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

API_KEY: str = os.getenv("API_KEY", "")

limiter = Limiter(key_func=get_remote_address)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: str | None = Security(_api_key_header)) -> None:
    """Dependency — validates X-API-Key header on mutating endpoints.
    No-op when API_KEY env var is not set (dev / local mode)."""
    if not API_KEY:
        return  # dev mode
    if key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
