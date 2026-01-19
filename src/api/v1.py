"""RapidAPI-specific routes (v1)."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends, Query
from typing import Optional
import tempfile
from pathlib import Path
import uuid

from src.models.auth import AuthContext
from src.auth.middleware import get_rapidapi_auth
from src.models import SpeechContextEnum
from src.services import AnalysisService
from src.core.job_queue import JobQueue
from src.services.response_builder import build_response
from src.utils.logging_config import logger
from src.utils.exceptions import AudioNotFoundError, AudioFormatError, AudioDurationError

router = APIRouter()
job_queue = JobQueue()  # Singleton job tracker


@router.get("/health")
async def health_check(auth: AuthContext = Depends(get_rapidapi_auth)):
    """Health check endpoint - requires valid RapidAPI key and signature."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "message": "RapidAPI endpoint is running"
    }


@router.post("/analyze")
async def analyze_audio_rapidapi(
    file: UploadFile = File(...),
    speech_context: SpeechContextEnum = Form(default=SpeechContextEnum.CONVERSATIONAL),
    device: str = Form(default="cpu"),
    background_tasks: BackgroundTasks = None,
    auth: AuthContext = Depends(get_rapidapi_auth)
):
    """
    Analyze speech fluency from uploaded audio file (ASYNC).
    RapidAPI endpoint.
    
    Returns immediately with job_id. Poll /result/{job_id} for results.
    
    Args:
        file: Audio file to analyze
        speech_context: Context of the speech
        device: Device to run on ("cpu" or "cuda")
        auth: RapidAPI authentication context
        
    Returns:
        job_id: Unique identifier to poll for results
        status: Always "queued"
        message: Instructions for polling
    """
    job_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[RapidAPI] Received analysis request: {job_id} for {file.filename}")
    except Exception as e:
        logger.error(f"Failed to log request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal error")
    
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    # Create job entry with API key ownership tracking
    job_queue.create_job(job_id, file.filename, api_key_hash=auth.key_hash)
    
    # Queue analysis as background task
    background_tasks.add_task(
        _process_analysis_rapidapi,
        job_id=job_id,
        tmp_path=tmp_path,
        speech_context=speech_context,
        device=device
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Analysis started. Poll /api/v1/result/{job_id} for results"
    }


@router.get("/result/{job_id}")
async def get_result_rapidapi(
    job_id: str,
    detail: Optional[str] = Query(None, description="Optional: 'feedback' or 'full'"),
    auth: AuthContext = Depends(get_rapidapi_auth)
):
    """
    Poll for analysis results.
    RapidAPI endpoint.
    
    Args:
        job_id: The job ID returned from /analyze endpoint
        detail: Optional detail level ('feedback' or 'full')
        auth: RapidAPI authentication context
        
    Returns:
        status="processing": Still running, poll again in a few seconds
        status="completed": Analysis done, results in 'data' field
        status="error": Analysis failed, error message in 'detail' field
    """
    # Verify job ownership
    if not job_queue.verify_job_ownership(job_id, auth.key_hash):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or access denied")
    
    status, data = job_queue.get_status(job_id)
    
    if status == "notfound":
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Build tiered response
    response = build_response(
        job_id=job_id,
        status=status,
        raw_analysis=data if status == "completed" else None,
        detail=detail,
        error=data if status == "error" else None
    )
    
    return response


# ============================================================================
# Background processing function (NOT an endpoint)
# ============================================================================

async def _process_analysis_rapidapi(job_id: str, tmp_path: str, speech_context: str, device: str):
    """
    Background task to process audio analysis.
    Runs in the background without blocking the HTTP request.
    """
    try:
        logger.info(f"[Job {job_id}] Starting analysis...")
        
        # Call the main analysis service
        result = await AnalysisService.analyze_speech(
            audio_path=tmp_path,
            speech_context=speech_context,
            device=device
        )
        
        # Store result as-is (engine_runner returns raw analysis dict)
        job_queue.set_result(job_id, result)
        logger.info(f"[Job {job_id}] Analysis completed successfully")
    
    except (AudioNotFoundError, FileNotFoundError) as e:
        error_msg = f"Audio file not found: {str(e)}"
        logger.error(f"[Job {job_id}] {error_msg}")
        job_queue.set_error(job_id, error_msg)
    
    except AudioFormatError as e:
        error_msg = f"Invalid audio format: {str(e)}"
        logger.error(f"[Job {job_id}] {error_msg}")
        job_queue.set_error(job_id, error_msg)
    
    except AudioDurationError as e:
        error_msg = f"Audio too short: {str(e)}"
        logger.error(f"[Job {job_id}] {error_msg}")
        job_queue.set_error(job_id, error_msg)
    
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error(f"[Job {job_id}] {error_msg}", exc_info=True)
        job_queue.set_error(job_id, error_msg)
    
    finally:
        # Always clean up temp file
        Path(tmp_path).unlink(missing_ok=True)
        logger.info(f"[Job {job_id}] Cleaned up temporary file")
