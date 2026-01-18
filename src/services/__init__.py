"""Service layer for audio analysis orchestration."""
import asyncio
import pandas as pd
from typing import Dict, Any
from pathlib import Path

from src.audio import (
    load_audio,
    transcribe_verbatim_fillers,
    align_words_whisperx,
    extract_words_dataframe,
    extract_segments_dataframe,
    mark_filler_words,
    mark_filler_segments,
    get_content_words,
    detect_fillers_wav2vec,
    detect_fillers_whisper,
    merge_filler_detections,
    group_stutters,
)
from src.utils.config import CORE_FILLERS
from src.core.fluency_metrics import analyze_fluency
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
        
        Args:
            audio_path: Path to audio file
            speech_context: Context of the speech (conversational, narrative, presentation, interview)
            device: Device to run on (cpu or cuda)
            
        Returns:
            Dictionary with complete analysis results
        """
        logger.info(f"Starting analysis for: {audio_path}")
        
        # Validate audio file exists
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print(f"Analyzing audio: {audio_path}")
        print(f"Context: {speech_context}")
        
        # Step 1: Verbatim transcription (source of truth)
        print("\n[1/5] Transcribing with Whisper (verbatim)...")
        verbatim_result = await asyncio.to_thread(
            transcribe_verbatim_fillers, audio_path, device=device
        )
        
        # Extract words and segments
        df_words = extract_words_dataframe(verbatim_result)
        df_segments = extract_segments_dataframe(verbatim_result)
        
        # Check for empty transcription
        if df_segments.empty:
            logger.warning(f"No speech detected in {audio_path}")
            return AnalysisService._empty_response()
        
        total_duration = float(df_segments.iloc[-1]["end"])
        print(f"  Duration: {total_duration:.2f}s")
        print(f"  Words: {len(df_words)}")
        
        # Step 2: Mark fillers in words and segments
        print("\n[2/5] Marking filler words...")
        df_words = mark_filler_words(df_words, CORE_FILLERS)
        df_segments = mark_filler_segments(df_segments, CORE_FILLERS)
        
        filler_count = df_words['is_filler'].sum()
        print(f"  Marked: {filler_count} filler words")
        
        # Get content-only words
        df_content_words = get_content_words(df_words)
        print(f"  Content words: {len(df_content_words)}")
        
        # Step 3: Align words with WhisperX
        print("\n[3/5] Aligning words with WhisperX...")
        audio, _ = await asyncio.to_thread(load_audio, audio_path)
        df_aligned_words = await asyncio.to_thread(
            align_words_whisperx, verbatim_result["segments"], audio, device=device
        )
        print(f"  Aligned: {len(df_aligned_words)} words")
        
        # Step 4: Detect fillers with Wav2Vec2
        print("\n[4/5] Detecting subtle fillers with Wav2Vec2...")
        df_wav2vec_fillers = await asyncio.to_thread(
            detect_fillers_wav2vec, audio_path, df_aligned_words
        )
        
        # Extract Whisper-detected fillers
        df_whisper_fillers = df_words[df_words['is_filler']].copy()
        df_whisper_fillers['type'] = 'filler'
        df_whisper_fillers['text'] = df_whisper_fillers['word'].str.lower()
        df_whisper_fillers['style'] = 'clear'
        df_whisper_fillers = df_whisper_fillers[['type', 'text', 'start', 'end', 'duration', 'style']]
        
        # Merge detections
        df_merged_fillers = merge_filler_detections(df_whisper_fillers, df_wav2vec_fillers)
        df_final_fillers = group_stutters(df_merged_fillers)
        print(f"  Total events: {len(df_final_fillers)}")
        
        # Step 5: Calculate fluency metrics
        print("\n[5/5] Calculating fluency score...")
        analysis = analyze_fluency(
            df_words,
            df_content_words,
            df_segments,
            df_final_fillers,
            total_duration,
            speech_context
        )
        
        if analysis["verdict"]["fluency_score"] is not None:
            print(f"\n✓ Fluency Score: {analysis['verdict']['fluency_score']}/100")
            print(f"✓ Readiness: {analysis['verdict']['readiness']}")
        else:
            print(f"\n✗ {analysis['verdict']['readiness']}")
        
        # Build final response
        final_response = {
            **analysis,
            "word_timestamps": df_words.to_dict(orient="records"),
            "content_words": df_content_words.to_dict(orient="records"),
            "segment_timestamps": df_segments.to_dict(orient="records"),
            "filler_events": df_final_fillers.to_dict(orient="records"),
            "statistics": {
                "total_words_transcribed": len(df_words),
                "content_words": len(df_content_words),
                "filler_words_detected": int(filler_count),
                "filler_percentage": round(
                    100 * filler_count / len(df_words), 2
                ) if len(df_words) > 0 else 0,
            }
        }
        
        logger.info(f"Analysis completed successfully for {audio_path}")
        return final_response
    
    @staticmethod
    def _empty_response() -> Dict[str, Any]:
        """Return empty response when no speech is detected."""
        return {
            "verdict": {"fluency_score": None, "readiness": "no_speech_detected"},
            "benchmarking": None,
            "normalized_metrics": None,
            "opinions": None,
            "word_timestamps": [],
            "content_words": [],
            "segment_timestamps": [],
            "filler_events": [],
            "statistics": {
                "total_words_transcribed": 0,
                "content_words": 0,
                "filler_words_detected": 0,
                "filler_percentage": 0,
            }
        }
