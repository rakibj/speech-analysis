"""Server-side protections against abuse and resource exhaustion."""
import time
from collections import defaultdict
from fastapi import HTTPException, UploadFile, Request
from src.utils.logging_config import logger

# Configuration
MAX_FILE_SIZE_MB = 15
MAX_AUDIO_DURATION_MINUTES = 5
RATE_LIMIT_REQUESTS_PER_HOUR = 100

# In-memory rate limiter: {user_id: [timestamps]}
rate_limit_tracker = defaultdict(list)


async def validate_file_size(file: UploadFile, max_mb: int = MAX_FILE_SIZE_MB) -> None:
    """
    Validate uploaded file size before processing.
    
    Args:
        file: Uploaded file
        max_mb: Maximum size in MB
        
    Raises:
        HTTPException 413 if file too large
    """
    max_bytes = max_mb * 1024 * 1024
    
    # Get file size
    if file.size and file.size > max_bytes:
        logger.warning(f"[Protection] File too large: {file.filename} ({file.size / 1024 / 1024:.1f}MB)")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {max_mb}MB. Received: {file.size / 1024 / 1024:.1f}MB"
        )


async def validate_audio_duration(audio_path: str, max_minutes: int = MAX_AUDIO_DURATION_MINUTES) -> None:
    """
    Validate audio file duration before processing.
    
    Args:
        audio_path: Path to audio file
        max_minutes: Maximum duration in minutes
        
    Raises:
        HTTPException 400 if audio too long
    """
    try:
        import librosa
        duration = librosa.get_duration(path=audio_path)
        max_seconds = max_minutes * 60
        
        if duration > max_seconds:
            logger.warning(f"[Protection] Audio too long: {duration:.1f}s ({max_minutes}m limit)")
            raise HTTPException(
                status_code=400,
                detail=f"Audio too long. Maximum: {max_minutes} minutes. Your audio: {duration / 60:.1f} minutes"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Protection] Error checking audio duration: {str(e)}")
        # Don't fail on duration check error - just log and continue
        pass


def check_rate_limit(user_id: str, max_requests: int = RATE_LIMIT_REQUESTS_PER_HOUR) -> None:
    """
    Check rate limit for a user (requests per hour).
    
    Args:
        user_id: RapidAPI user ID
        max_requests: Maximum requests per hour
        
    Raises:
        HTTPException 429 if rate limit exceeded
    """
    current_time = time.time()
    one_hour_ago = current_time - 3600
    
    # Clean old timestamps
    rate_limit_tracker[user_id] = [
        ts for ts in rate_limit_tracker[user_id] 
        if ts > one_hour_ago
    ]
    
    # Check limit
    if len(rate_limit_tracker[user_id]) >= max_requests:
        logger.warning(f"[Protection] Rate limit exceeded for user: {user_id}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum: {max_requests} requests per hour"
        )
    
    # Record this request
    rate_limit_tracker[user_id].append(current_time)
    logger.info(f"[Protection] Rate limit: {user_id} - {len(rate_limit_tracker[user_id])}/{max_requests} requests this hour")


def enforce_rapidapi_only(request: Request) -> None:
    """
    Enforce that request came through RapidAPI Gateway.
    Prevents direct URL access to paid endpoints.
    
    Args:
        request: FastAPI request
        
    Raises:
        HTTPException 403 if not from RapidAPI
    """
    # Check for RapidAPI gateway headers
    if "x-rapidapi-proxy-secret" not in request.headers:
        logger.error("[Protection] Direct access attempt - no RapidAPI gateway headers")
        raise HTTPException(
            status_code=403,
            detail="This endpoint requires RapidAPI subscription. Direct access not allowed."
        )
