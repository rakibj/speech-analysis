"""FastAPI dependency injection for authentication."""
from fastapi import Header, HTTPException, Request
from typing import Optional
from src.auth.key_manager import KeyManager
from src.models.auth import AuthContext, InvalidAPIKeyError


async def get_direct_auth(
    x_api_key: str = Header(..., description="API key for direct access")
) -> AuthContext:
    """
    FastAPI dependency for direct API key validation.
    
    Usage:
        @router.post("/analyze")
        async def analyze(auth: AuthContext = Depends(get_direct_auth)):
            ...
    """
    try:
        auth = KeyManager.validate_key(x_api_key)
        auth.owner_type = "direct"
        return auth
    except InvalidAPIKeyError as e:
        raise HTTPException(status_code=401, detail=str(e))


async def get_rapidapi_auth(
    request: Request,
    x_rapidapi_key: str = Header(..., description="RapidAPI key"),
    x_rapidapi_signature: Optional[str] = Header(None, description="RapidAPI signature"),
    x_rapidapi_user: Optional[str] = Header(None, description="RapidAPI user ID"),
) -> AuthContext:
    """
    FastAPI dependency for RapidAPI request validation.
    
    Verifies X-RapidAPI-Signature header using HMAC-SHA256.
    
    Usage:
        @router.post("/analyze")
        async def analyze(auth: AuthContext = Depends(get_rapidapi_auth)):
            ...
    """
    # Signature is REQUIRED for RapidAPI endpoints
    if not x_rapidapi_signature:
        raise HTTPException(status_code=401, detail="X-RapidAPI-Signature header is required")
    
    # Verify signature
    try:
        body = await request.body()
    except Exception:
        body = b""
    
    if not KeyManager.verify_rapidapi_signature(body, x_rapidapi_signature):
        raise HTTPException(status_code=401, detail="Invalid RapidAPI signature")
    
    # Validate the API key
    try:
        auth = KeyManager.validate_key(x_rapidapi_key)
        auth.owner_type = "rapidapi"
        auth.owner_id = x_rapidapi_user
        return auth
    except InvalidAPIKeyError as e:
        raise HTTPException(status_code=401, detail=str(e))
