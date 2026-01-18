"""Service layer for audio analysis orchestration."""
from typing import Dict, Any
from pathlib import Path

from src.core.engine_runner import run_engine
from src.utils.logging_config import logger


class AnalysisService:
    """Service for orchestrating speech analysis operations."""
    
    @staticmethod
    async def analyze_speech(
        audio_path: str,
        speech_context: str = "conversational",
        device: str = "cpu"
    ) -> Dict[str, Any]:
        """
        Analyze speech fluency from audio file.
        
        Delegates to engine_runner for actual analysis.
        
        Args:
            audio_path: Path to audio file
            speech_context: Context of the speech (conversational, narrative, presentation, interview)
            device: Device to run on (cpu or cuda)
            
        Returns:
            Dictionary with complete analysis results
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio is invalid
        """
        logger.info(f"Starting analysis for: {audio_path}")
        
        # Validate audio file exists
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Read audio bytes
        audio_bytes = audio_file.read_bytes()
        filename = audio_file.name
        
        logger.info(f"Loaded {len(audio_bytes)} bytes from {filename}")
        
        # Delegate to engine_runner for full analysis pipeline
        result = await run_engine(
            audio_bytes=audio_bytes,
            context=speech_context,
            device=device,
            use_llm=True,
            filename=filename
        )
        
        logger.info(f"Analysis completed successfully for {audio_path}")
        return result
