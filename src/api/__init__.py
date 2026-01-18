"""FastAPI routes for audio analysis."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional
import tempfile
from pathlib import Path
import uuid

from src.models import (
    AudioAnalysisRequest,
    AudioAnalysisResponse,
    HealthResponse,
    SpeechContextEnum,
)
from src.services import AnalysisService
from src.core.job_queue import JobQueue
from src.utils.logging_config import logger
from src.utils.exceptions import AudioNotFoundError, AudioFormatError, AudioDurationError

router = APIRouter()
job_queue = JobQueue()  # Singleton job tracker


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        message="API is running"
    )


@router.post("/analyze")
async def analyze_audio_upload(
    file: UploadFile = File(...),
    speech_context: SpeechContextEnum = Form(default=SpeechContextEnum.CONVERSATIONAL),
    device: str = Form(default="cpu"),
    background_tasks: BackgroundTasks = None
):
    """
    Analyze speech fluency from uploaded audio file (ASYNC).
    
    Returns immediately with job_id. Poll /result/{job_id} for results.
    
    Args:
        file: Audio file to analyze
        speech_context: Context of the speech
        device: Device to run on ("cpu" or "cuda")
        
    Returns:
        job_id: Unique identifier to poll for results
        status: Always "queued"
        message: Instructions for polling
    """
    job_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Received analysis request: {job_id} for {file.filename}")
    except Exception as e:
        logger.error(f"Failed to log request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal error")
    
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    # Create job entry BEFORE queueing
    job_queue.create_job(job_id, file.filename)
    
    # Queue analysis as background task
    background_tasks.add_task(
        _process_analysis,
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
async def get_result(job_id: str):
    """
    Poll for analysis results.
    
    Args:
        job_id: The job ID returned from /analyze endpoint
        
    Returns:
        status="processing": Still running, poll again in a few seconds
        status="completed": Analysis done, results in 'data' field
        status="error": Analysis failed, error message in 'detail' field
        status="notfound": Job ID doesn't exist
    """
    status, data = job_queue.get_status(job_id)
    
    if status == "processing":
        return {"status": "processing", "job_id": job_id, "message": "Analysis in progress..."}
    
    elif status == "completed":
        return {"status": "completed", "job_id": job_id, "data": data}
    
    elif status == "error":
        return {"status": "error", "job_id": job_id, "detail": data}
    
    else:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


# ============================================================================
# Background processing function (NOT an endpoint)
# ============================================================================

async def _process_analysis(job_id: str, tmp_path: str, speech_context: str, device: str):
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
        
        # Convert result to response model
        analysis_response = AudioAnalysisResponse(**result)
        
        # Store result in job queue
        job_queue.set_result(job_id, analysis_response)
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
