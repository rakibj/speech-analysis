# src/audio/processing.py
"""Audio loading and transcription utilities with error handling."""
import os
import soundfile as sf
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Set, Any
from src.utils.config import CORE_FILLERS, FILLER_PATTERNS
from src.utils.exceptions import (
    AudioNotFoundError,
    AudioFormatError,
    AudioDurationError,
    TranscriptionError,
    ModelLoadError,
    NoSpeechDetectedError,
    DeviceError,
)
from src.utils.logging_config import logger


MIN_AUDIO_DURATION_SEC = 5.0


def load_audio(path: str) -> Tuple[np.ndarray, int]:
    """
    Load audio file and convert to mono 16kHz.
    
    Args:
        path: Path to audio file
        
    Returns:
        Tuple of (audio_array, sample_rate)
        
    Raises:
        AudioNotFoundError: If file doesn't exist
        AudioFormatError: If file cannot be read
    """
    audio_path = Path(path)
    
    # Validate file exists
    if not audio_path.exists():
        raise AudioNotFoundError(
            f"Audio file not found: {path}",
            {"file_path": str(audio_path)}
        )
    
    try:
        audio, sr = sf.read(str(audio_path), dtype="float32")
    except Exception as e:
        raise AudioFormatError(
            f"Failed to read audio file: {str(e)}",
            {"file_path": str(audio_path), "error": str(e)}
        )
    
    # Convert stereo to mono
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    
    # Resample to 16kHz if needed
    if sr != 16000:
        try:
            import torch
            import torchaudio
            audio_tensor = torch.from_numpy(audio)
            audio = torchaudio.functional.resample(
                audio_tensor, sr, 16000
            ).numpy()
            sr = 16000
        except Exception as e:
            raise AudioFormatError(
                f"Failed to resample audio: {str(e)}",
                {"original_sample_rate": sr, "target_sample_rate": 16000}
            )
    
    # Validate audio duration
    duration = len(audio) / sr
    if duration < MIN_AUDIO_DURATION_SEC:
        raise AudioDurationError(
            f"Audio duration {duration:.2f}s is less than minimum {MIN_AUDIO_DURATION_SEC}s",
            {"duration": duration, "minimum_required": MIN_AUDIO_DURATION_SEC}
        )
    
    logger.info(f"Loaded audio: {duration:.2f}s at {sr}Hz")
    return audio, sr


def transcribe_with_whisper(
    audio_path: str,
    model_name: str = "base",
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Transcribe audio using Whisper with word timestamps.
    
    Args:
        audio_path: Path to audio file
        model_name: Whisper model size (tiny, base, small, medium, large)
        device: Device to run on ('cpu' or 'cuda')
        
    Returns:
        Dictionary with segments and word-level timestamps
        
    Raises:
        ModelLoadError: If Whisper model fails to load
        TranscriptionError: If transcription fails
        DeviceError: If device is unavailable
    """
    # Validate device availability
    try:
        import torch
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            device = "cpu"
    except Exception:
        device = "cpu"
    
    # Load model
    try:
        import whisper
        # Use cache directory from environment or default
        cache_dir = os.getenv("WHISPER_DOWNLOAD_ROOT", None)
        model = whisper.load_model(model_name, device=device, download_root=cache_dir)
        logger.info(f"Loaded Whisper model: {model_name} on {device}")
    except Exception as e:
        raise ModelLoadError(
            f"Failed to load Whisper model {model_name}: {str(e)}",
            {"model": model_name, "device": device, "error": str(e)}
        )
    
    # Transcribe
    try:
        result = model.transcribe(
            audio_path,
            task="transcribe",
            word_timestamps=True,
            fp16=False,
            language="en"
        )
        logger.info(f"Transcription completed: {len(result.get('segments', []))} segments")
        return result
    except Exception as e:
        raise TranscriptionError(
            f"Transcription failed: {str(e)}",
            {"audio_path": audio_path, "model": model_name, "error": str(e)}
        )


def transcribe_verbatim_fillers(
    audio_path: str,
    model_name: str = "base",
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Transcribe with explicit focus on capturing filler words.
    
    Args:
        audio_path: Path to audio file
        model_name: Whisper model size
        device: Device to run on
        
    Returns:
        Dictionary with verbatim transcription including fillers
        
    Raises:
        ModelLoadError: If model fails to load
        TranscriptionError: If transcription fails
    """
    # Validate device
    try:
        import torch
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            device = "cpu"
    except Exception:
        device = "cpu"
    
    try:
        import whisper
        import torch
        # Use cache directory from environment or default
        cache_dir = os.getenv("WHISPER_DOWNLOAD_ROOT", None)
        # Workaround for meta tensor issue: load on CPU first, then move to target device
        try:
            model = whisper.load_model(model_name, device="cpu", download_root=cache_dir)
            if device != "cpu":
                model = model.to_empty(device=device)
        except Exception:
            # Fallback: try loading directly with device parameter
            model = whisper.load_model(model_name, device=device, download_root=cache_dir)
    except Exception as e:
        raise ModelLoadError(
            f"Failed to load Whisper model: {str(e)}",
            {"model": model_name, "device": device}
        )
    
    try:
        result = model.transcribe(
            audio_path,
            task="transcribe",
            temperature=0,
            word_timestamps=(device != "cpu"),  # Disable on CPU due to timing hook issues
            condition_on_previous_text=False,
            initial_prompt=(
                "Transcribe verbatim. Include filler words like um, uh, er, "
                "false starts, repetitions, and hesitations."
            ),
            fp16=False,
            language="en"
        )
        return result
    except Exception as e:
        raise TranscriptionError(
            f"Verbatim transcription failed: {str(e)}",
            {"audio_path": audio_path, "error": str(e)}
        )


def align_words_whisperx(
    segments: list,
    audio: np.ndarray,
    language_code: str = "en",
    device: str = None
) -> pd.DataFrame:
    """
    Align word timestamps using WhisperX for better accuracy.
    
    Args:
        segments: Whisper transcription segments
        audio: Audio array
        language_code: Language code for alignment model
        device: Device to run on (auto-detected if None)
        
    Returns:
        DataFrame with aligned word timestamps
        
    Raises:
        ModelLoadError: If alignment model fails to load
    """
    if device is None:
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"
    
    # Validate device
    try:
        import torch
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            device = "cpu"
    except Exception:
        device = "cpu"
    
    try:
        import whisperx
        align_model, metadata = whisperx.load_align_model(
            language_code=language_code,
            device=device
        )
        logger.info(f"Loaded WhisperX alignment model for {language_code}")
    except Exception as e:
        raise ModelLoadError(
            f"Failed to load alignment model: {str(e)}",
            {"language": language_code, "device": device}
        )
    
    try:
        import whisperx
        aligned = whisperx.align(
            segments,
            align_model,
            metadata,
            audio,
            device
        )
    except Exception as e:
        raise TranscriptionError(
            f"Word alignment failed: {str(e)}",
            {"error": str(e)}
        )
    
    aligned_words = []
    for seg in aligned["segments"]:
        for w in seg.get("words", []):
            if w["start"] is not None and w["end"] is not None:
                aligned_words.append({
                    "word": w["word"].strip().lower(),
                    "start": float(w["start"]),
                    "end": float(w["end"])
                })
    
    if not aligned_words:
        raise NoSpeechDetectedError(
            "No words detected in aligned segments",
            {"segments_processed": len(aligned.get('segments', []))}
        )
    
    df = pd.DataFrame(aligned_words)
    return df.sort_values("start").reset_index(drop=True)


def extract_words_dataframe(result: Dict[str, Any]) -> pd.DataFrame:
    """
    Extract word-level data from Whisper result.
    
    Args:
        result: Whisper transcription result
        
    Returns:
        DataFrame with word timestamps and confidence scores
        
    Raises:
        NoSpeechDetectedError: If no words are found
    """
    words = []
    for seg in result["segments"]:
        # Skip if words not available (e.g., when word_timestamps=False)
        if "words" not in seg:
            continue
        for w in seg["words"]:
            words.append({
                "word": w["word"].strip(),
                "start": float(w["start"]),
                "end": float(w["end"]),
                "duration": float(w["end"] - w["start"]),
                "confidence": float(w["probability"])
            })
    
    if not words:
        # Create DataFrame from segments if word-level data unavailable
        segments = result.get("segments", [])
        if segments:
            words_from_segments = []
            for seg in segments:
                text = seg.get("text", "").strip()
                if text:
                    # Split into words and create entries with segment timing
                    seg_words = text.split()
                    if seg_words:
                        word_duration = (seg.get("end", 0) - seg.get("start", 0)) / len(seg_words)
                        for i, word in enumerate(seg_words):
                            words_from_segments.append({
                                "word": word,
                                "start": seg.get("start", 0) + i * word_duration,
                                "end": seg.get("start", 0) + (i + 1) * word_duration,
                                "duration": word_duration,
                                "confidence": seg.get("confidence", 1.0)
                            })
            if words_from_segments:
                return pd.DataFrame(words_from_segments)
        
        raise NoSpeechDetectedError(
            "No words extracted from transcription",
            {"segments": len(result.get('segments', []))}
        )
    
    return pd.DataFrame(words)


def extract_segments_dataframe(result: Dict[str, Any]) -> pd.DataFrame:
    """
    Extract segment-level data from Whisper result.
    
    Args:
        result: Whisper transcription result
        
    Returns:
        DataFrame with segment timestamps and average confidence
    """
    segments = []
    for seg in result["segments"]:
        # Handle missing word-level data (when word_timestamps=False)
        if "words" in seg and len(seg["words"]) > 0:
            avg_confidence = sum(
                [float(w["probability"]) for w in seg["words"]]
            ) / len(seg["words"])
        else:
            # Use segment-level confidence if available, else default to 1.0
            avg_confidence = float(seg.get("confidence", 1.0))
        
        segments.append({
            "text": seg["text"].strip(),
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "duration": float(seg["end"] - seg["start"]),
            "avg_word_confidence": avg_confidence
        })
    
    return pd.DataFrame(segments)
