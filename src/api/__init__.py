"""FastAPI routes for audio analysis."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import tempfile
from pathlib import Path

from src.models import (
    AudioAnalysisRequest,
    AudioAnalysisResponse,
    HealthResponse,
    SpeechContextEnum,
)
from src.services import AnalysisService
from src.utils.logging_config import logger
from src.utils.exceptions import AudioNotFoundError, AudioFormatError, AudioDurationError

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        message="API is running"
    )


@router.post("/analyze", response_model=AudioAnalysisResponse)
async def analyze_audio(request: AudioAnalysisRequest):
    """
    Analyze speech fluency from audio file.
    
    Args:
        request: Audio analysis request with audio path and context
        
    Returns:
        Complete analysis results with scores and metrics
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        logger.info(f"Received analysis request for: {request.audio_path}")
        
        result = await AnalysisService.analyze_speech(
            audio_path=request.audio_path,
            speech_context=request.speech_context,
            device=request.device
        )
        
        return AudioAnalysisResponse(**result)
    
    except (AudioNotFoundError, FileNotFoundError) as e:
        logger.error(f"Audio file not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Audio file not found: {str(e)}")
    
    except AudioFormatError as e:
        logger.error(f"Invalid audio format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid audio format: {str(e)}")
    
    except AudioDurationError as e:
        logger.error(f"Audio too short: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Audio too short: {str(e)}")
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze-upload", response_model=AudioAnalysisResponse)
async def analyze_audio_upload(
    file: UploadFile = File(...),
    speech_context: SpeechContextEnum = Form(default=SpeechContextEnum.CONVERSATIONAL),
    device: str = Form(default="cpu")
):
    """
    Analyze speech fluency from uploaded audio file.
    
    Args:
        file: Audio file to analyze
        speech_context: Context of the speech
        device: Device to run on
        
    Returns:
        Complete analysis results
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        logger.info(f"Received upload request for: {file.filename}")
        
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            result = await AnalysisService.analyze_speech(
                audio_path=tmp_path,
                speech_context=speech_context,
                device=device
            )
            
            return AudioAnalysisResponse(**result)
        
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)
    
    except (AudioNotFoundError, FileNotFoundError) as e:
        logger.error(f"Audio file error: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Audio error: {str(e)}")
    
    except AudioFormatError as e:
        logger.error(f"Invalid audio format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid audio format: {str(e)}")
    
    except AudioDurationError as e:
        logger.error(f"Audio too short: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Audio too short: {str(e)}")
    
    except Exception as e:
        logger.error(f"Upload analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
