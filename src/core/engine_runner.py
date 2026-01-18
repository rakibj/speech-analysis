"""
Engine Runner - Wrapper for engine.analyze_speech with audio bytes input

Handles:
- Saving audio bytes to temporary file
- Running analysis pipeline
- Returning structured results
"""

import asyncio
import tempfile
import json
from pathlib import Path
from typing import Dict, Optional
import traceback

from src.core.engine import analyze_speech
from src.utils.logging_config import setup_logging
from src.utils.exceptions import SpeechAnalysisError

logger = setup_logging(level="INFO")


async def run_engine(
    audio_bytes: bytes,
    context: str = "conversational",
    device: str = "cpu",
    use_llm: bool = True,
    filename: str = "audio.wav"
) -> Dict:
    """
    Run comprehensive speech analysis on audio bytes.
    
    Saves audio bytes to temporary file and runs analysis pipeline.
    
    Args:
        audio_bytes: Raw audio data as bytes (WAV, MP3, etc.)
        context: Speech context ('conversational', 'narrative', 'presentation', 'interview')
        device: Computation device ('cpu' or 'cuda')
        use_llm: Whether to use LLM for semantic analysis (default: True)
        filename: Original filename (for reference, default: 'audio.wav')
        
    Returns:
        dict with complete analysis report including:
            - metadata: audio info
            - transcript: speech transcript
            - fluency_analysis: fluency metrics
            - pronunciation: clarity and prosody
            - band_scores: IELTS band scoring
            - feedback: user-facing feedback
            - statistics: speech statistics
            - llm_analysis: LLM semantic analysis (if enabled)
            
    Raises:
        SpeechAnalysisError: If analysis fails
        ValueError: If audio_bytes is empty or invalid
        
    Example:
        result = await run_engine(
            audio_bytes=b'...',
            context='conversational',
            use_llm=True
        )
        print(f"Band Score: {result['band_scores']['overall_band']}")
        print(f"Transcript: {result['transcript']}")
    """
    
    # Validate input
    if not isinstance(audio_bytes, bytes) or len(audio_bytes) == 0:
        raise ValueError("audio_bytes must be non-empty bytes object")
    
    logger.info(f"run_engine called with {len(audio_bytes)} bytes, filename: {filename}")
    
    temp_file = None
    try:
        # =============================================
        # CREATE TEMPORARY FILE
        # =============================================
        # Use wav extension for proper format handling
        file_ext = Path(filename).suffix if Path(filename).suffix else ".wav"
        
        temp_file = tempfile.NamedTemporaryFile(
            suffix=file_ext,
            delete=False
        )
        temp_path = temp_file.name
        
        # Write audio bytes to temp file
        temp_file.write(audio_bytes)
        temp_file.flush()
        temp_file.close()
        
        logger.info(f"Audio saved to temp file: {temp_path}")
        
        # =============================================
        # RUN ANALYSIS
        # =============================================
        logger.info(f"Starting analysis with context='{context}', use_llm={use_llm}")
        
        result = await analyze_speech(
            audio_path=temp_path,
            context=context,
            device=device,
            use_llm=use_llm
        )
        
        logger.info("[OK] Analysis complete")
        
        return result
        
    except SpeechAnalysisError as e:
        logger.error(f"Analysis error: {e.message}")
        raise
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.debug(traceback.format_exc())
        raise SpeechAnalysisError(
            "Engine execution failed",
            str(e)
        )
        
    finally:
        # =============================================
        # CLEANUP
        # =============================================
        if temp_file:
            try:
                Path(temp_path).unlink(missing_ok=True)
                logger.debug(f"Cleaned up temp file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {str(e)}")


def run_engine_sync(
    audio_bytes: bytes,
    context: str = "conversational",
    device: str = "cpu",
    use_llm: bool = True,
    filename: str = "audio.wav"
) -> Dict:
    """
    Synchronous wrapper for run_engine (for non-async contexts).
    
    Args:
        Same as run_engine
        
    Returns:
        Same as run_engine
        
    Example:
        result = run_engine_sync(audio_bytes=b'...', context='conversational')
    """
    return asyncio.run(run_engine(audio_bytes, context, device, use_llm, filename))
