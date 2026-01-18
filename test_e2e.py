"""
Test script to verify end-to-end speech analysis pipeline.
Processes one audio file through full analysis -> band scoring.
"""
import sys
import json
from pathlib import Path
import asyncio

# Setup path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.logging_config import setup_logging
from src.exceptions import SpeechAnalysisError
from src.analyzer_raw import analyze_speech
from src.analyze_band import analyze_band_from_analysis
from src.rubric_from_metrics import generate_constraints

logger = setup_logging(level="INFO")


async def test_e2e_pipeline():
    """Run end-to-end test with one audio file."""
    
    # Find a test audio file
    test_audio = PROJECT_ROOT / "data" / "ielts_part_2" / "ielts5-5.5.wav"
    
    if not test_audio.exists():
        logger.error(f"Test audio file not found: {test_audio}")
        return False
    
    logger.info("=" * 60)
    logger.info("STARTING END-TO-END PIPELINE TEST")
    logger.info("=" * 60)
    logger.info(f"Test audio: {test_audio.name}")
    logger.info(f"Audio size: {test_audio.stat().st_size / 1024 / 1024:.2f} MB")
    
    try:
        # Stage 1: Audio Analysis
        logger.info("\n[Stage 1] Running speech analysis...")
        result = await analyze_speech(test_audio)
        
        if result is None:
            logger.error("Analysis returned None")
            return False
        
        # Check that result has expected fields
        if "raw_transcript" not in result:
            logger.error("Analysis missing 'raw_transcript'")
            return False
        
        logger.info(f"[SUCCESS] Analysis complete")
        logger.info(f"  Transcript: {result.get('raw_transcript', '')[:100]}...")
        logger.info(f"  Total words: {result.get('statistics', {}).get('total_words_transcribed', 'N/A')}")
        logger.info(f"  Content words: {result.get('statistics', {}).get('content_words', 'N/A')}")
        logger.info(f"  Duration: {result.get('audio_duration_sec', 'N/A')} seconds")
        
        # Stage 2: Band Scoring
        logger.info("\n[Stage 2] Running IELTS band scoring...")
        band_result = await analyze_band_from_analysis(result)
        
        if band_result is None:
            logger.error("Band scoring returned None")
            return False
        
        if "band_scores" not in band_result:
            logger.error("Band result missing 'band_scores'")
            return False
        
        band_scores = band_result["band_scores"]
        
        logger.info(f"[SUCCESS] Band scoring complete")
        logger.info(f"  Overall Band: {band_scores.get('overall_band')}")
        logger.info(f"  Fluency & Coherence: {band_scores.get('criterion_bands', {}).get('fluency_coherence')}")
        logger.info(f"  Pronunciation: {band_scores.get('criterion_bands', {}).get('pronunciation')}")
        logger.info(f"  Lexical Resource: {band_scores.get('criterion_bands', {}).get('lexical_resource')}")
        logger.info(f"  Grammar: {band_scores.get('criterion_bands', {}).get('grammatical_range_accuracy')}")
        
        # Verify output structure
        if not band_scores.get("feedback"):
            logger.error("Band result missing 'feedback'")
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("[SUCCESS] END-TO-END TEST PASSED")
        logger.info("=" * 60)
        logger.info("\nSample feedback:")
        for criterion, comment in band_scores["feedback"].items():
            if criterion != "overall_recommendation":
                logger.info(f"  {criterion}: {comment[:80]}...")
        
        return True
        
    except SpeechAnalysisError as e:
        logger.error(f"❌ Speech analysis error: {e.message}")
        logger.error(f"   Details: {e.details}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(test_e2e_pipeline())
    sys.exit(0 if success else 1)
