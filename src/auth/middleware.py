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


async def get_rapidapi_auth(request: Request) -> AuthContext:
    """
    FastAPI dependency for RapidAPI request validation.
    
    IMPORTANT: This trusts that RapidAPI Gateway has already validated the subscriber.
    If a request reaches us with RapidAPI headers, the subscription is valid.
    
    RapidAPI Gateway injects:
    - x-rapidapi-proxy-secret: Proxy secret from subscription
    - x-rapidapi-user: Username of subscriber
    - x-mashape-user: Legacy format for username
    
    We just check that these headers exist (meaning it came through RapidAPI).
    
    Usage:
        @router.post("/analyze")
        async def analyze(auth: AuthContext = Depends(get_rapidapi_auth)):
            ...
    """
    from src.utils.logging_config import logger
    
    # Read headers (RapidAPI sends these for ANY valid subscriber)
    x_rapidapi_proxy_secret = request.headers.get("x-rapidapi-proxy-secret")
    x_rapidapi_user = request.headers.get("x-rapidapi-user") or request.headers.get("x-mashape-user")
    
    logger.info(f"[RapidAPI Auth] Request from user: {x_rapidapi_user}")
    
    # Validate that request came through RapidAPI gateway
    # If these headers exist, RapidAPI already validated the subscription
    if not x_rapidapi_proxy_secret:
        logger.error("[RapidAPI Auth] FAILED: Not from RapidAPI Gateway (missing x-rapidapi-proxy-secret)")
        raise HTTPException(status_code=401, detail="Invalid RapidAPI request")
    
    if not x_rapidapi_user:
        logger.error("[RapidAPI Auth] FAILED: Missing RapidAPI user information")
        raise HTTPException(status_code=401, detail="Invalid RapidAPI user")
    
    # Create auth context - trust RapidAPI's validation
    auth = AuthContext(
        api_key=x_rapidapi_proxy_secret,
        key_hash=x_rapidapi_proxy_secret,
        owner_type="rapidapi",
        owner_id=x_rapidapi_user
    )
    
    logger.info(f"[RapidAPI Auth] SUCCESS: Authenticated {x_rapidapi_user}")
    return auth
