# Source Code Dump (src)

## __init__.py

```python
# __init__.py

# Speech analysis package
"""Speech fluency analysis toolkit."""
```

## analyze_audio.py

```python
# analyze_audio.py

# src/analyze_audio.py
#!/usr/bin/env python3
"""
Command-line tool for analyzing speech fluency.

Usage:
    python scripts/analyze_audio.py sample4.flac
    python scripts/analyze_audio.py sample4.flac conversational
    python scripts/analyze_audio.py sample4.flac presentation
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.analyzer import analyze_speech


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    audio_path = sys.argv[1]
    speech_context = sys.argv[2] if len(sys.argv) > 2 else "conversational"
    output_json = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Validate audio file exists
    if not Path(audio_path).exists():
        print(f"Error: Audio file not found: {audio_path}")
        sys.exit(1)
    
    # Run analysis
    result = analyze_speech(audio_path, speech_context)
    
    # Save to JSON if requested
    if output_json:
        with open(output_json, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Results saved to: {output_json}")
    
    return result


if __name__ == "__main__":
    main()
```

## analyzer.py

```python
# analyzer.py

# src/analyzer.py
"""Main fluency analysis orchestrator."""
import pandas as pd
from dotenv import load_dotenv

from .audio_processing import (
    CORE_FILLERS,
    get_content_words,
    load_audio,
    mark_filler_segments,
    mark_filler_words,
    transcribe_with_whisper,
    transcribe_verbatim_fillers,
    align_words_whisperx,
    extract_words_dataframe,
    extract_segments_dataframe,
)
from .disfluency_detection import (
    detect_fillers_wav2vec,
    detect_fillers_whisper,
    merge_filler_detections,
    group_stutters,
)
from .fluency_metrics import analyze_fluency
from .config import VALID_CONTEXTS


# Load environment variables
load_dotenv()

# Set pandas display options
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", 0)


def analyze_speech(
    audio_path: str,
    speech_context: str = "conversational",
    device: str = "cpu"
) -> dict:
    """
    Analyze speech fluency from audio file.
    """
    print(f"Analyzing audio: {audio_path}")
    print(f"Context: {speech_context}")
    
    # Step 1: Verbatim transcription (source of truth)
    print("\n[1/5] Transcribing with Whisper (verbatim)...")
    verbatim_result = transcribe_verbatim_fillers(audio_path, device=device)
    
    # Extract words and segments
    df_words = extract_words_dataframe(verbatim_result)
    df_segments = extract_segments_dataframe(verbatim_result)
    
    # Check for empty transcription
    if df_segments.empty:
        print("\n✗ Error: No speech detected in audio")
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
                "total_words": 0,
                "content_words": 0,
                "filler_words": 0,
                "filler_percentage": 0,
            }
        }
    
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
    audio, _ = load_audio(audio_path)
    df_aligned_words = align_words_whisperx(verbatim_result["segments"], audio, device=device)
    print(f"  Aligned: {len(df_aligned_words)} words")
    
    # Step 4: Detect fillers with Wav2Vec2
    print("\n[4/5] Detecting subtle fillers with Wav2Vec2...")
    df_wav2vec_fillers = detect_fillers_wav2vec(audio_path, df_aligned_words)
    
    # Extract Whisper-detected fillers (already marked in df_words)
    df_whisper_fillers = df_words[df_words['is_filler']].copy()
    df_whisper_fillers['type'] = 'filler'
    df_whisper_fillers['text'] = df_whisper_fillers['word'].str.lower()
    df_whisper_fillers['style'] = 'clear'  # Add style column
    df_whisper_fillers = df_whisper_fillers[['type', 'text', 'start', 'end', 'duration', 'style']]
    
    # Merge detections
    df_merged_fillers = merge_filler_detections(df_whisper_fillers, df_wav2vec_fillers)
    df_final_fillers = group_stutters(df_merged_fillers)
    print(f"  Total events: {len(df_final_fillers)}")
    
    # Step 5: Calculate fluency metrics
    print("\n[5/5] Calculating fluency score...")
    analysis = analyze_fluency(
        df_words,          # Full timeline (with is_filler column)
        df_content_words,  # Content words only (for WPM)
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
    
    # Build response with multiple word views
    final_response = {
        **analysis,
        
        # Complete timeline with filler markers
        "word_timestamps": df_words.to_dict(orient="records"),
        
        # Content words only (for clean display)
        "content_words": df_content_words.to_dict(orient="records"),
        
        # Segments with filler flags
        "segment_timestamps": df_segments.to_dict(orient="records"),
        
        # Detected filler events (including stutters)
        "filler_events": df_final_fillers.to_dict(orient="records"),
        
        # Statistics
        "statistics": {
            "total_words_transcribed": len(df_words),
            "content_words": len(df_content_words),
            "filler_words_detected": filler_count,
            "filler_percentage": round(100 * filler_count / len(df_words), 2) if len(df_words) > 0 else 0,
        }
    }
    
    return final_response


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: fluency-analyze <audio_file> [context]")
        print("Contexts: conversational (default), narrative, presentation, interview")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    speech_context = sys.argv[2] if len(sys.argv) > 2 else "conversational"
    
    result = analyze_speech(audio_path, speech_context)
    
    # Print summary
    print("\n" + "="*60)
    print("FLUENCY ANALYSIS SUMMARY")
    print("="*60)
    
    if result["verdict"]["fluency_score"] is not None:
        print(f"\nScore: {result['verdict']['fluency_score']}/100")
        print(f"Readiness: {result['verdict']['readiness']}")
        print(f"Percentile: {result['benchmarking']['percentile']}th")
        
        if result["opinions"]["primary_issues"]:
            print("\nTop Issues:")
            for issue in result["opinions"]["primary_issues"][:3]:
                print(f"  • [{issue['severity'].upper()}] {issue['issue']}")
                print(f"    {issue['root_cause']}")
        
        if result["opinions"]["action_plan"]:
            print("\nAction Plan:")
            for action in result["opinions"]["action_plan"]:
                print(f"  {action['priority']}. {action['instruction']}")
                print(f"     Expected gain: +{action['expected_score_gain']} points")
    else:
        print(f"\nStatus: {result['verdict']['readiness']}")
        print("Minimum 5 seconds of audio required for analysis.")


if __name__ == "__main__":
    main()
```

## analyzer_raw.py

```python
# analyzer_raw.py

# src/analyzer.py
"""Main fluency analysis orchestrator."""
import pandas as pd
from dotenv import load_dotenv

from .audio_processing import (
    CORE_FILLERS,
    get_content_words,
    load_audio,
    mark_filler_segments,
    mark_filler_words,
    transcribe_with_whisper,
    transcribe_verbatim_fillers,
    align_words_whisperx,
    extract_words_dataframe,
    extract_segments_dataframe,
)
from .disfluency_detection import (
    detect_fillers_wav2vec,
    detect_fillers_whisper,
    merge_filler_detections,
    group_stutters,
)
from .metrics import calculate_normalized_metrics


# Load environment variables
load_dotenv()

# Set pandas display options
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", 0)


def analyze_speech(
    audio_path: str,
    speech_context: str = "conversational",
    device: str = "cpu"
) -> dict:
    """
    Analyze speech fluency from audio file.
    """
    print(f"Analyzing audio: {audio_path}")
    print(f"Context: {speech_context}")
    
    # Step 1: Verbatim transcription (source of truth)
    print("\n[1/5] Transcribing with Whisper (verbatim)...")
    verbatim_result = transcribe_verbatim_fillers(audio_path, device=device)
    
    # Extract words and segments
    df_words = extract_words_dataframe(verbatim_result)
    df_segments = extract_segments_dataframe(verbatim_result)
    
    # Check for empty transcription
    if df_segments.empty:
        print("\n✗ Error: No speech detected in audio")
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
                "total_words": 0,
                "content_words": 0,
                "filler_words": 0,
                "filler_percentage": 0,
            }
        }
    
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
    audio, _ = load_audio(audio_path)
    df_aligned_words = align_words_whisperx(verbatim_result["segments"], audio, device=device)
    print(f"  Aligned: {len(df_aligned_words)} words")
    
    # Step 4: Detect fillers with Wav2Vec2
    print("\n[4/5] Detecting subtle fillers with Wav2Vec2...")
    df_wav2vec_fillers = detect_fillers_wav2vec(audio_path, df_aligned_words)
    
    # Extract Whisper-detected fillers (already marked in df_words)
    df_whisper_fillers = df_words[df_words['is_filler']].copy()
    df_whisper_fillers['type'] = 'filler'
    df_whisper_fillers['text'] = df_whisper_fillers['word'].str.lower()
    df_whisper_fillers['style'] = 'clear'  # Add style column
    df_whisper_fillers = df_whisper_fillers[['type', 'text', 'start', 'end', 'duration', 'style']]
    
    # Merge detections
    df_merged_fillers = merge_filler_detections(df_whisper_fillers, df_wav2vec_fillers)
    df_final_fillers = group_stutters(df_merged_fillers)
    print(f"  Total events: {len(df_final_fillers)}")
    
    print("\n[5/5] Calculating raw score...")
    normalized_metrics = calculate_normalized_metrics(
        df_words_raw=df_words,
        df_words_cleaned=df_content_words,
        df_segments=df_segments,
        df_fillers=df_final_fillers,
        total_duration=total_duration
    )
    
    # Build response with multiple word views
    final_response = {
        **normalized_metrics,
        # Statistics
        "statistics": {
            "total_words_transcribed": len(df_words),
            "content_words": len(df_content_words),
            "filler_words_detected": filler_count,
            "filler_percentage": round(100 * filler_count / len(df_words), 2) if len(df_words) > 0 else 0,
        }, 
        "timestamps": {
            # Complete timeline with filler markers
            "words_timestamps_raw": df_words.to_dict(orient="records"),
            
            # Content words only (for clean display)
            "words_timestamps_cleaned": df_content_words.to_dict(orient="records"),
            
            # Segments with filler flags
            "segment_timestamps": df_segments.to_dict(orient="records"),
            
            # Detected filler events (including stutters)
            "filler_timestamps": df_final_fillers.to_dict(orient="records"),
        }
    }
    
    return final_response


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: fluency-analyze <audio_file> [context]")
        print("Contexts: conversational (default), narrative, presentation, interview")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    speech_context = sys.argv[2] if len(sys.argv) > 2 else "conversational"
    
    result = analyze_speech(audio_path, speech_context)
    
    # Print summary
    print("\n" + "="*60)
    print("FLUENCY ANALYSIS SUMMARY")
    print("="*60)
    
    if result["verdict"]["fluency_score"] is not None:
        print(f"\nScore: {result['verdict']['fluency_score']}/100")
        print(f"Readiness: {result['verdict']['readiness']}")
        print(f"Percentile: {result['benchmarking']['percentile']}th")
        
        if result["opinions"]["primary_issues"]:
            print("\nTop Issues:")
            for issue in result["opinions"]["primary_issues"][:3]:
                print(f"  • [{issue['severity'].upper()}] {issue['issue']}")
                print(f"    {issue['root_cause']}")
        
        if result["opinions"]["action_plan"]:
            print("\nAction Plan:")
            for action in result["opinions"]["action_plan"]:
                print(f"  {action['priority']}. {action['instruction']}")
                print(f"     Expected gain: +{action['expected_score_gain']} points")
    else:
        print(f"\nStatus: {result['verdict']['readiness']}")
        print("Minimum 5 seconds of audio required for analysis.")


if __name__ == "__main__":
    main()
```

## audio_processing.py

```python
# audio_processing.py

# src/audio_processing.py
"""Audio loading and transcription utilities."""
import torch
import torchaudio
import soundfile as sf
import whisper
import whisperx
import pandas as pd
from typing import Tuple
from .config import CORE_FILLERS, FILLER_PATTERNS


def load_audio(path: str) -> Tuple[any, int]:
    """
    Load audio file and convert to mono 16kHz.
    
    Args:
        path: Path to audio file
        
    Returns:
        Tuple of (audio_array, sample_rate)
    """
    audio, sr = sf.read(path, dtype="float32")
    
    # Convert stereo to mono
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    
    # Resample to 16kHz if needed
    if sr != 16000:
        audio_tensor = torch.from_numpy(audio)
        audio = torchaudio.functional.resample(
            audio_tensor, sr, 16000
        ).numpy()
        sr = 16000
    
    return audio, sr


def transcribe_with_whisper(
    audio_path: str,
    model_name: str = "base",
    device: str = "cpu"
) -> dict:
    """
    Transcribe audio using Whisper with word timestamps.
    
    Args:
        audio_path: Path to audio file
        model_name: Whisper model size
        device: Device to run on ('cpu' or 'cuda')
        
    Returns:
        Dictionary with segments and word-level timestamps
    """
    model = whisper.load_model(model_name, device=device)
    
    result = model.transcribe(
        audio_path,
        task="transcribe",
        word_timestamps=True,
        fp16=False,
        language="en"
    )
    
    return result


def transcribe_verbatim_fillers(
    audio_path: str,
    model_name: str = "base",
    device: str = "cpu"
) -> dict:
    """
    Transcribe with explicit focus on capturing filler words.
    
    Args:
        audio_path: Path to audio file
        model_name: Whisper model size
        device: Device to run on
        
    Returns:
        Dictionary with verbatim transcription including fillers
    """
    model = whisper.load_model(model_name, device=device)
    
    result = model.transcribe(
        audio_path,
        task="transcribe",
        temperature=0,
        word_timestamps=True,
        condition_on_previous_text=False,
        initial_prompt=(
            "Transcribe verbatim. Include filler words like um, uh, er, "
            "false starts, repetitions, and hesitations."
        ),
        fp16=False,
        language="en"
    )
    
    return result


def align_words_whisperx(
    segments: list,
    audio: any,
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
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    align_model, metadata = whisperx.load_align_model(
        language_code=language_code,
        device=device
    )
    
    aligned = whisperx.align(
        segments,
        align_model,
        metadata,
        audio,
        device
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
    
    df = pd.DataFrame(aligned_words)
    return df.sort_values("start").reset_index(drop=True)


def extract_words_dataframe(result: dict) -> pd.DataFrame:
    """
    Extract word-level data from Whisper result.
    
    Args:
        result: Whisper transcription result
        
    Returns:
        DataFrame with word timestamps and confidence scores
    """
    words = []
    for seg in result["segments"]:
        for w in seg["words"]:
            words.append({
                "word": w["word"].strip(),
                "start": float(w["start"]),
                "end": float(w["end"]),
                "duration": float(w["end"] - w["start"]),
                "confidence": float(w["probability"])
            })
    
    return pd.DataFrame(words)



def extract_segments_dataframe(result: dict) -> pd.DataFrame:
    """
    Extract segment-level data from Whisper result.
    
    Args:
        result: Whisper transcription result
        
    Returns:
        DataFrame with segment timestamps and average confidence
    """
    segments = []
    for seg in result["segments"]:
        # Handle empty word list
        if len(seg["words"]) > 0:
            avg_confidence = sum(
                [float(w["probability"]) for w in seg["words"]]
            ) / len(seg["words"])
        else:
            avg_confidence = 0.0
        
        segments.append({
            "text": seg["text"].strip(),
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "duration": float(seg["end"] - seg["start"]),
            "avg_word_confidence": avg_confidence
        })
    
    return pd.DataFrame(segments)
# Add to audio_processing.py or create a new utility file

import re
import pandas as pd
from typing import Set


def normalize_word(word: str) -> str:
    """
    Normalize a word for filler detection.
    
    - Strips punctuation
    - Converts to lowercase
    - Removes extra whitespace
    
    Args:
        word: Raw word string from transcription
        
    Returns:
        Normalized word string
    """
    # Remove leading/trailing punctuation and whitespace
    word = re.sub(r'^[^\w]+|[^\w]+$', '', word.lower().strip())
    
    # Collapse multiple spaces
    word = re.sub(r'\s+', ' ', word)
    
    return word


def is_filler_word(
    word: str,
    filler_set: Set[str] = CORE_FILLERS,
    include_pattern_match: bool = True
) -> bool:
    """
    Determine if a word is a filler with high confidence.
    
    Args:
        word: Word to check
        filler_set: Set of known filler words
        include_pattern_match: Also check regex patterns for variations
        
    Returns:
        True if word is a filler
    """
    normalized = normalize_word(word)
    
    if not normalized:
        return False
    
    # Direct lookup in filler set
    if normalized in filler_set:
        return True
    
    # Pattern matching for variations
    if include_pattern_match:
        # Repeated vowels: uhhhhh, ummmm, ahhhhh
        if re.fullmatch(r'[uea]h{2,}', normalized):
            return True
        if re.fullmatch(r'[ume]{2,}', normalized):
            return True
        
        # Elongated nasals: mmmmm, nnnn
        if re.fullmatch(r'[mn]{2,}', normalized):
            return True
        
        # Um/uh variants with extra letters
        if re.fullmatch(r'u+h*m+', normalized):  # um, umm, uhhm
            return True
        if re.fullmatch(r'u+h+', normalized):  # uh, uhh, uhhh
            return True
        if re.fullmatch(r'e+r+m*', normalized):  # er, err, erm
            return True
    
    return False


def mark_filler_words(
    df_words: pd.DataFrame,
    filler_set: Set[str] = CORE_FILLERS,
    word_column: str = 'word'
) -> pd.DataFrame:
    """
    Add 'is_filler' column to word DataFrame.
    
    Args:
        df_words: DataFrame with word timestamps
        filler_set: Set of filler words to detect
        word_column: Name of column containing words
        
    Returns:
        DataFrame with added 'is_filler' column
    """
    df = df_words.copy()
    
    df['is_filler'] = df[word_column].apply(
        lambda w: is_filler_word(w, filler_set)
    )
    
    return df


def get_content_words(df_words: pd.DataFrame) -> pd.DataFrame:
    """
    Extract only content words (non-fillers).
    
    Args:
        df_words: DataFrame with 'is_filler' column
        
    Returns:
        Filtered DataFrame with only content words
    """
    if 'is_filler' not in df_words.columns:
        raise ValueError("DataFrame must have 'is_filler' column. Run mark_filler_words() first.")
    
    return df_words[~df_words['is_filler']].copy().reset_index(drop=True)


def segment_contains_filler(segment_text: str, filler_set: Set[str] = CORE_FILLERS) -> bool:
    """
    Check if a segment contains any filler words.
    
    Args:
        segment_text: Full segment text
        filler_set: Set of filler words
        
    Returns:
        True if segment contains fillers
    """
    words = segment_text.lower().split()
    return any(is_filler_word(w, filler_set) for w in words)


def mark_filler_segments(
    df_segments: pd.DataFrame,
    filler_set: Set[str] = CORE_FILLERS,
    text_column: str = 'text'
) -> pd.DataFrame:
    """
    Add 'contains_filler' column to segment DataFrame.
    
    Args:
        df_segments: DataFrame with segment timestamps
        filler_set: Set of filler words to detect
        text_column: Name of column containing segment text
        
    Returns:
        DataFrame with added 'contains_filler' column
    """
    df = df_segments.copy()
    
    df['contains_filler'] = df[text_column].apply(
        lambda text: segment_contains_filler(text, filler_set)
    )
    
    return df


if __name__ == "__main__":
    # Quick test
    audio_path = "sample4.flac"
    result = transcribe_with_whisper(audio_path)
    df_words = extract_words_dataframe(result)
    print(f"Transcribed {len(df_words)} words")
    print(df_words.head())
```

## config.py

```python
# config.py

"""
config.py

Central configuration file for the speech fluency analysis system.

This file defines:
- Detection thresholds (fillers, pauses, stutters)
- Scoring weights and limits
- Context-specific tolerances (conversation vs presentation)
- Readiness criteria and benchmarking assumptions

⚠️ IMPORTANT:
- All numeric values here directly affect scores and verdicts.
- Changing values WILL change user-facing results.
- Treat this file as product policy, not just engineering config.
"""

VALID_CONTEXTS = {"conversational", "narrative", "presentation", "interview"}

STOPWORDS = {
    # ------------------------------------------------------------------
    # Articles & determiners (no lexical choice signal)
    # ------------------------------------------------------------------
    "a", "an", "the",
    "this", "that", "these", "those",

    # ------------------------------------------------------------------
    # Personal pronouns (unavoidable repetition in speech)
    # ------------------------------------------------------------------
    "i", "me", "my", "mine", "myself",
    "you", "your", "yours", "yourself",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",

    # ------------------------------------------------------------------
    # Auxiliary & copular verbs (grammatical scaffolding)
    # ------------------------------------------------------------------
    "am", "is", "are", "was", "were",
    "be", "been", "being",

    # ------------------------------------------------------------------
    # Modal verbs (high frequency, low lexical information)
    # ------------------------------------------------------------------
    "can", "could", "may", "might",
    "must", "shall", "should",
    "will", "would",

    # ------------------------------------------------------------------
    # Function verbs (do/have — repetition is not lexical weakness)
    # ------------------------------------------------------------------
    "do", "does", "did", "done", "doing",
    "have", "has", "had", "having",

    # ------------------------------------------------------------------
    # Prepositions (mandatory grammar glue)
    # ------------------------------------------------------------------
    "to", "of", "in", "on", "at", "for", "with",
    "about", "from", "by", "into", "onto",
    "over", "under", "after", "before",
    "between", "among", "through", "during",
    "without", "within", "against", "around",
    "towards", "upon",

    # ------------------------------------------------------------------
    # Conjunctions & subordinators (structural, not lexical)
    # ------------------------------------------------------------------
    "and", "but", "or", "so", "yet",
    "because", "although", "though", "while",
    "if", "unless", "until", "since",

    # ------------------------------------------------------------------
    # Relative & complementizers (clause formation)
    # ------------------------------------------------------------------
    "that", "which", "who", "whom", "whose",
    "where", "when",

    # ------------------------------------------------------------------
    # Quantifiers & generalizers (very common, vague)
    # ------------------------------------------------------------------
    "some", "any", "many", "much",
    "few", "little", "more", "most",
    "less", "least", "all", "both",
    "either", "neither", "each", "every",
    "enough",

    # ------------------------------------------------------------------
    # Negation & polarity (grammatical necessity)
    # ------------------------------------------------------------------
    "not", "no", "nor", "never",
    "none", "nothing", "nobody", "nowhere",

    # ------------------------------------------------------------------
    # Existentials & placeholders (low semantic value)
    # ------------------------------------------------------------------
    "there", "here",
    "something", "anything", "everything",
    "someone", "anyone", "everyone",
    "somewhere", "anywhere", "everywhere",

    # ------------------------------------------------------------------
    # Spoken fillers & discourse glue (NOT lexical choice)
    # ------------------------------------------------------------------
    "uh", "um", "erm", "ah", "eh", "hmm",
    "like",           # filler usage (IELTS-relevant)
    "well", "okay", "ok", "right",
    "you know", "i mean",
    "kind of", "sort of",
    "basically", "actually", "literally",

    # ------------------------------------------------------------------
    # Temporal / sequencing glue (narrative structure, not vocabulary)
    # ------------------------------------------------------------------
    "then", "now", "today", "yesterday", "tomorrow",
    "later", "first", "second", "third", "next", "finally",
}

# ============================================================
# FILLER & STUTTER DETECTION CONFIGURATION
# ============================================================

FILLER_PATTERNS = {
    # Basic fillers
    'um', 'umm', 'ummm', 'uhm', 'uhhmm',
    'uh', 'uhh', 'uhhh', 'er', 'err', 'errr',
    'ah', 'ahh', 'ahhh', 'eh', 'ehh', 'ehhh',
    
    # British/formal variants
    'erm', 'errm', 'errmm',
    
    # Elongated versions
    'uuuh', 'uuum', 'aaah', 'mmm', 'hmm', 'hmmm',
    
}
FILLER_REGEX = r"^(um+|uh+|erm+|er+|ah+|eh+|mmm+|hmm+)$"
FILLER_IGNORE_MAX = 0.10     # <100ms → ignore
FILLER_LIGHT_MAX = 0.30      # 100–300ms → light
# More conservative set (exclude discourse markers)
CORE_FILLERS = {
    'um', 'umm', 'ummm', 'uhm', 'uhhmm',
    'uh', 'uhh', 'uhhh', 'er', 'err', 'errr',
    'ah', 'ahh', 'ahhh', 'eh', 'ehh', 'ehhh',
    'erm', 'errm', 'errmm',
    'uuuh', 'uuum', 'aaah', 'mmm', 'hmm', 'hmmm',
}


# Mapping from raw phoneme labels (from wav2vec / CTC output)
# to normalized human-readable filler text.
#
# Example:
#   raw phoneme "MM" or "NN" → perceived as "um"
FILLER_MAP = {
    "A": "uh",
    "E": "uh",
    "U": "uh",
    "M": "um",
    "N": "um",
    "MM": "um",
    "NN": "um",
}

# Maximum allowed gap (in seconds) between a filler/stutter
# and the next word start to still consider it word-initial.
#
# Used to avoid falsely classifying normal word onsets as fillers.
WORD_ONSET_WINDOW = 0.12  # seconds

# Minimum duration (in seconds) for a sound to be considered
# a meaningful filler rather than noise or articulation artifact.
MIN_FILLER_DURATION = 0.02  # seconds

# Set of consonants that can form stutters when rapidly repeated.
# Example: "t-t-today", "b-b-but"
STUTTER_CONSONANTS = set("BCDFGHJKLPQRSTVWXYZ")


# ============================================================
# MINIMUM ANALYSIS REQUIREMENTS
# ============================================================

# Minimum audio duration required to produce a valid fluency score.
# Shorter samples are rejected as statistically unreliable.
MIN_ANALYSIS_DURATION_SEC = 5.0


# ============================================================
# SPEECH RATE (WORDS PER MINUTE) THRESHOLDS
# ============================================================

# Below this WPM, speech is considered unnaturally slow.
WPM_TOO_SLOW = 70

# Below this WPM, speech begins to feel hesitant or labored.
WPM_SLOW_THRESHOLD = 110

# Upper bound of the optimal WPM range for clarity.
WPM_OPTIMAL_MAX = 170

# Range over which excessively fast speech is penalized.
# Beyond WPM_OPTIMAL_MAX, score decays linearly over this range.
WPM_FAST_DECAY_RANGE = 120


# ============================================================
# PAUSE BEHAVIOR LIMITS
# ============================================================

# Maximum acceptable number of long pauses (>1s) per minute
# before pause structure is penalized.
MAX_LONG_PAUSES_PER_MIN = 4.0

# If pause subscore drops below this threshold,
# it is treated as a structural fluency blocker.
PAUSE_SCORE_BLOCK_THRESHOLD = 0.6


# ============================================================
# FILLER DEPENDENCY LIMITS
# ============================================================

# Maximum acceptable number of fillers per minute (weighted by duration)
# before fluency is penalized.
MAX_FILLERS_PER_MIN = 6.0

# If filler subscore drops below this threshold,
# it is treated as a structural fluency blocker.
FILLER_SCORE_BLOCK_THRESHOLD = 0.6


# ============================================================
# RHYTHMIC STABILITY LIMITS
# ============================================================

# Baseline acceptable standard deviation of pause durations.
# Higher values indicate erratic speech rhythm.
BASE_PAUSE_VARIABILITY = 0.7

# Below this stability score, speech rhythm is flagged as unstable.
STABILITY_SCORE_WARN_THRESHOLD = 0.6


# ============================================================
# LEXICAL QUALITY LIMITS
# ============================================================

# Below this lexical subscore, vocabulary usage is considered weak
# (high repetition, low diversity).
LEXICAL_LOW_THRESHOLD = 0.5


# ============================================================
# SCORING WEIGHTS (MUST SUM TO 1.0)
# ============================================================

# Contribution of pause structure to final fluency score.
WEIGHT_PAUSE = 0.30

# Contribution of filler dependency to final fluency score.
WEIGHT_FILLER = 0.25

# Contribution of rhythmic stability to final fluency score.
WEIGHT_STABILITY = 0.20

# Contribution of speech rate (WPM) to final fluency score.
WEIGHT_SPEECH_RATE = 0.15

# Contribution of lexical richness and repetition avoidance.
WEIGHT_LEXICAL = 0.10


# ============================================================
# READINESS & DECISION THRESHOLDS
# ============================================================

# Minimum audio duration required to consider a speaker
# "ready" for high-stakes evaluation (e.g. IELTS simulation).
MIN_SAMPLE_DURATION_SEC = 30

# Minimum fluency score required to be classified as "ready".
READY_SCORE_THRESHOLD = 80


# ============================================================
# BENCHMARKING & PRACTICE ESTIMATION
# ============================================================

# Target fluency score representing strong readiness.
BENCHMARK_TARGET_SCORE = 80

# Estimated guided practice hours required to improve fluency
# by one point on the 0–100 scale.
PRACTICE_HOURS_PER_POINT = 0.6


# ============================================================
# CONTEXT-SPECIFIC TOLERANCE CONFIGURATION
# ============================================================

# Different speaking contexts tolerate pauses and rhythm
# differently. These multipliers adjust scoring sensitivity.
#
# Example:
#   Narrative speech allows longer pauses than interviews.
CONTEXT_CONFIG = {
    "conversational": {
        "pause_tolerance": 1.0,
        "pause_variability_tolerance": 1.0,
    },
    "narrative": {
        "pause_tolerance": 1.4,
        "pause_variability_tolerance": 1.3,
    },
    "presentation": {
        "pause_tolerance": 1.2,
        "pause_variability_tolerance": 1.1,
    },
    "interview": {
        "pause_tolerance": 0.9,
        "pause_variability_tolerance": 0.9,
    },
}


# ============================================================
# LOW-LEVEL DETECTION PARAMETERS
# ============================================================

# Maximum gap (in seconds) between repeated stutter sounds
# to be grouped into a single stutter event.
GROUP_GAP_SEC = 0.15

# Time resolution (in seconds) per wav2vec token frame.
# Used to convert token indices to timestamps.
FRAME_SEC = 0.02  # 20 ms per frame


# ============================================================
# ACTION PLAN INSTRUCTIONS
# ============================================================

# Mapping from detected issue identifiers to
# human-readable corrective instructions.
INSTRUCTIONS = {
    "hesitation_structure": (
        "Pause only after completing full clauses or ideas."
    ),
    "filler_dependency": (
        "Replace filler words with silent pauses under 300 ms."
    ),
    "delivery_instability": (
        "Practice steady pacing using metronome or rhythm drills."
    ),
    "delivery_pacing": (
        "Reduce speaking speed slightly while maintaining energy."
    ),
    "lexical_simplicity": (
        "Actively substitute repeated words during rehearsal."
    ),
}
```

## disfluency_detection.py

```python
# disfluency_detection.py

# src/disfluency_detection.py
"""Disfluency detection: fillers, stutters, and hesitations."""
import re
import torch
import torchaudio
import soundfile as sf
import pandas as pd
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from typing import Tuple

from .config import (
    FILLER_MAP,
    FILLER_REGEX,
    WORD_ONSET_WINDOW,
    MIN_FILLER_DURATION,
    STUTTER_CONSONANTS,
    GROUP_GAP_SEC,
    FRAME_SEC,
)


# ==============================
# WAV2VEC2 PHONEME DETECTION
# ==============================

def detect_phonemes_wav2vec(audio_path: str) -> pd.DataFrame:
    """
    Detect phoneme-level events using Wav2Vec2.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        DataFrame with phoneme events (label, start, end, duration)
    """
    processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-large-960h")
    wav2vec = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-large-960h")
    wav2vec.eval()
    
    # Load audio
    waveform, sr = sf.read(audio_path, dtype="float32")
    
    # Convert stereo to mono
    if waveform.ndim == 2:
        waveform = waveform.mean(axis=1)
    
    waveform = torch.from_numpy(waveform)
    
    # Resample to 16kHz if needed
    if sr != 16000:
        waveform = torchaudio.functional.resample(waveform, sr, 16000)
        sr = 16000
    
    # Prepare input
    inputs = processor(
        waveform.squeeze(),
        sampling_rate=16000,
        return_tensors="pt",
    )
    
    # Forward pass
    with torch.no_grad():
        logits = wav2vec(**inputs).logits
    
    # Get predicted tokens
    predicted_ids = torch.argmax(logits, dim=-1)[0]
    tokens = processor.tokenizer.convert_ids_to_tokens(predicted_ids.tolist())
    
    # Convert tokens to events
    events = []
    current = None
    
    for i, tok in enumerate(tokens):
        t = i * FRAME_SEC
        
        if tok == '<pad>':
            if current:
                current["end"] = t
                events.append(current)
                current = None
            continue
        
        if current and current["label"] == tok:
            continue
        
        if current:
            current["end"] = t
            events.append(current)
        
        current = {"label": tok, "start": t}
    
    if current:
        current["end"] = t
        events.append(current)
    
    df = pd.DataFrame(events)
    if df.empty:
        return df
    
    df["duration"] = df["end"] - df["start"]
    df["labels"] = df["label"]
    
    # Merge adjacent same-label events
    df = merge_adjacent_events(df)
    
    return df


def merge_adjacent_events(df: pd.DataFrame, max_gap: float = 0.05) -> pd.DataFrame:
    """Merge adjacent events with the same label."""
    if df.empty:
        return df
    
    merged = []
    current = None
    
    for _, row in df.sort_values("start").iterrows():
        if current is None:
            current = row.to_dict()
            continue
        
        same_label = row["labels"] == current["labels"]
        close = row["start"] - current["end"] <= max_gap
        
        if same_label and close:
            current["end"] = row["end"]
            current["duration"] = current["end"] - current["start"]
        else:
            merged.append(current)
            current = row.to_dict()
    
    if current:
        merged.append(current)
    
    return pd.DataFrame(merged)


# ==============================
# FILLER/STUTTER CLASSIFICATION
# ==============================

def overlaps_any_word_relaxed(
    start: float,
    end: float,
    words: pd.DataFrame,
    tol_before: float = 0.02,
    tol_after: float = 0.02
) -> bool:
    """Check if time range overlaps any word."""
    for _, w in words.iterrows():
        if start < w["end"] + tol_after and end > w["start"] - tol_before:
            return True
    return False


def is_word_initial_candidate(
    row: pd.Series,
    word_starts: pd.DataFrame,
    max_lead: float = WORD_ONSET_WINDOW
) -> bool:
    """Check if event is immediately before a word start."""
    end = row["end"]
    upcoming = word_starts[
        (word_starts["start"] >= end) &
        ((word_starts["start"] - end) <= max_lead)
    ]
    return not upcoming.empty


def looks_like_filler(norm: str, duration: float) -> bool:
    """Check if normalized label looks like a filler sound."""
    if duration < MIN_FILLER_DURATION:
        return False
    
    # Vowel hesitations (uh, ah, eh)
    if re.fullmatch(r"[AEIOUH]+", norm):
        return True
    
    # Nasal hums (mm, nn)
    if re.fullmatch(r"M+|N+", norm):
        return True
    
    return False


def should_suppress_word_initial(row: pd.Series) -> bool:
    """Check if word-initial sound should be suppressed."""
    label = row["labels"].upper()
    norm = re.sub(r"(.)\1+", r"\1", label)
    
    # Never suppress filler-shaped sounds
    if looks_like_filler(norm, row["duration"]):
        return False
    
    # Suppress only ultra-short junk
    return row["duration"] < 0.03


def classify_non_word_event(row: pd.Series) -> dict:
    """Classify a non-word phoneme event as filler or stutter."""
    label = row["labels"].upper()
    duration = row["duration"]
    norm = re.sub(r"(.)\1+", r"\1", label)
    
    # Fillers
    if looks_like_filler(norm, duration):
        return {
            "type": "filler",
            "raw_label": label,
            "text": FILLER_MAP.get(norm, "uh"),
        }
    
    # Stutters
    if (
        norm in STUTTER_CONSONANTS
        and norm not in FILLER_MAP
        and duration < 0.15
    ):
        return {
            "type": "stutter",
            "raw_label": label,
            "text": norm.lower(),
        }
    
    return None


def detect_fillers_wav2vec(
    audio_path: str,
    aligned_words: pd.DataFrame
) -> pd.DataFrame:
    """
    Detect fillers and stutters using Wav2Vec2 phoneme detection.
    
    Args:
        audio_path: Path to audio file
        aligned_words: DataFrame with aligned word timestamps
        
    Returns:
        DataFrame with detected filler/stutter events
    """
    # Get phoneme-level events
    df_wav2vec = detect_phonemes_wav2vec(audio_path)
    
    if df_wav2vec.empty:
        return pd.DataFrame()
    
    # Filter out word overlaps
    df_wav2vec["overlaps_word"] = df_wav2vec.apply(
        lambda r: overlaps_any_word_relaxed(r["start"], r["end"], aligned_words),
        axis=1
    )
    
    df_non_word = df_wav2vec.loc[~df_wav2vec["overlaps_word"]].copy()
    
    # Handle word-initial sounds
    word_starts = aligned_words[["start"]].copy()
    
    df_non_word["is_word_initial"] = df_non_word.apply(
        lambda r: is_word_initial_candidate(r, word_starts),
        axis=1
    )
    
    df_non_word["suppress"] = df_non_word.apply(
        lambda r: r["is_word_initial"] and should_suppress_word_initial(r),
        axis=1
    )
    
    df_non_word = df_non_word.loc[~df_non_word["suppress"]].reset_index(drop=True)
    
    # Merge micro events
    df_non_word = merge_adjacent_events(df_non_word, max_gap=0.05)
    
    # Classify events
    converted = []
    for _, row in df_non_word.iterrows():
        result = classify_non_word_event(row)
        if result:
            converted.append({
                "type": result["type"],
                "text": result["text"],
                "raw_label": result["raw_label"],
                "start": row["start"],
                "end": row["end"],
                "duration": row["duration"],
            })
    
    return pd.DataFrame(converted)


# ==============================
# WHISPER FILLER DETECTION
# ==============================

def detect_fillers_whisper(verbatim_result: dict) -> pd.DataFrame:
    """
    Extract filler words from verbatim Whisper transcription.
    
    Args:
        verbatim_result: Whisper transcription result with verbatim prompt
        
    Returns:
        DataFrame with detected filler words
    """
    
    def normalize_whisper_token(token: str) -> str:
        token = token.lower().strip()
        return re.sub(r"^[^\w]+|[^\w]+$", "", token)
    
    whisper_fillers = []
    
    for seg in verbatim_result.get("segments", []):
        for w in seg.get("words", []):
            norm = normalize_whisper_token(w["word"])
            if norm and FILLER_REGEX.match(norm):
                whisper_fillers.append({
                    "style": "clear",
                    "type": "filler",
                    "text": norm,
                    "raw_label": w["word"],
                    "start": float(w["start"]),
                    "end": float(w["end"]),
                    "duration": float(w["end"] - w["start"]),
                    "confidence": float(w["probability"]),
                })
    
    return pd.DataFrame(whisper_fillers)


# ==============================
# MERGE & GROUP DETECTIONS
# ==============================

def overlaps_time(
    a_start: float,
    a_end: float,
    b_start: float,
    b_end: float,
    tol: float = 0.05
) -> bool:
    """Check if two time ranges overlap."""
    return (a_start < b_end + tol) and (a_end > b_start - tol)


def merge_filler_detections(
    df_whisper: pd.DataFrame,
    df_wav2vec: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge Whisper and Wav2Vec2 filler detections.
    Prioritizes Whisper (clear speech), backfills with Wav2Vec2 (subtle).
    
    Args:
        df_whisper: Fillers detected by Whisper
        df_wav2vec: Fillers detected by Wav2Vec2
        
    Returns:
        Combined DataFrame with all filler events
    """
    final_fillers = []
    
    # Add all Whisper detections first
    for _, wf in df_whisper.iterrows():
        final_fillers.append(wf.to_dict())
    
    # Add Wav2Vec2 detections that don't overlap
    for _, row in df_wav2vec.iterrows():
        duplicate = False
        
        for af in final_fillers:
            if overlaps_time(row["start"], row["end"], af["start"], af["end"]):
                duplicate = True
                break
        
        if not duplicate:
            entry = row.to_dict()
            entry["style"] = "subtle"
            final_fillers.append(entry)
    
    df = pd.DataFrame(final_fillers)
    
    if not df.empty:
        df = df.sort_values("start").reset_index(drop=True)
    
    return df


def group_stutters(df_fillers: pd.DataFrame) -> pd.DataFrame:
    """
    Group consecutive stutter repetitions.
    
    Args:
        df_fillers: DataFrame with all filler/stutter events
        
    Returns:
        DataFrame with stutters grouped by repetition
    """
    df_stutters = df_fillers[df_fillers["type"] == "stutter"].copy()
    df_other = df_fillers[df_fillers["type"] != "stutter"].copy()
    
    if df_stutters.empty:
        return df_fillers
    
    grouped = []
    current = None
    
    for _, row in df_stutters.sort_values("start").iterrows():
        if current is None:
            current = row.to_dict()
            current["count"] = 1
            continue
        
        same_sound = row["raw_label"] == current["raw_label"]
        close_in_time = row["start"] - current["end"] <= GROUP_GAP_SEC
        
        if same_sound and close_in_time:
            current["end"] = row["end"]
            current["duration"] = current["end"] - current["start"]
            current["count"] += 1
        else:
            grouped.append(current)
            current = row.to_dict()
            current["count"] = 1
    
    if current:
        grouped.append(current)
    
    df_grouped_stutters = pd.DataFrame(grouped)
    
    # Combine with other events
    df_final = (
        pd.concat([df_other, df_grouped_stutters], ignore_index=True)
        .sort_values("start")
        .reset_index(drop=True)
    )
    
    # Filter out very short single stutters
    df_final = df_final[
        ~(
            (df_final["type"] == "stutter") &
            (df_final["count"].fillna(1) < 2) &
            (df_final["duration"] < 0.15)
        )
    ].reset_index(drop=True)
    
    return df_final


if __name__ == "__main__":
    # Quick test
    import sys
    from .audio_processing import transcribe_with_whisper, align_words_whisperx, load_audio
    
    audio_path = "sample4.flac"
    
    # Get word alignments
    result = transcribe_with_whisper(audio_path)
    audio, _ = load_audio(audio_path)
    df_aligned = align_words_whisperx(result["segments"], audio)
    
    # Detect fillers
    df_wav2vec = detect_fillers_wav2vec(audio_path, df_aligned)
    print(f"Detected {len(df_wav2vec)} events via Wav2Vec2")
    print(df_wav2vec.head())
```

## fluency_metrics.py

```python
# fluency_metrics.py

# src/metrics.py
"""Fluency metrics calculation and scoring."""
import pandas as pd
from typing import Tuple, Dict, List

from .config import (
    WPM_TOO_SLOW,
    WPM_SLOW_THRESHOLD,
    WPM_OPTIMAL_MAX,
    WPM_FAST_DECAY_RANGE,
    MAX_LONG_PAUSES_PER_MIN,
    MAX_FILLERS_PER_MIN,
    BASE_PAUSE_VARIABILITY,
    PAUSE_SCORE_BLOCK_THRESHOLD,
    FILLER_SCORE_BLOCK_THRESHOLD,
    STABILITY_SCORE_WARN_THRESHOLD,
    LEXICAL_LOW_THRESHOLD,
    WEIGHT_PAUSE,
    WEIGHT_FILLER,
    WEIGHT_STABILITY,
    WEIGHT_SPEECH_RATE,
    WEIGHT_LEXICAL,
    MIN_ANALYSIS_DURATION_SEC,
    CONTEXT_CONFIG,
    INSTRUCTIONS,
)

def clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    return max(0.0, min(1.0, x))


def calculate_subscores(
    metrics: dict,
    context_config: dict
) -> Tuple[dict, dict]:
    """
    Calculate fluency subscores.
    
    Args:
        metrics: Normalized metrics dictionary
        context_config: Context-specific tolerance settings
        
    Returns:
        Tuple of (subscores dict, context dict)
    """
    wpm = metrics["wpm"]
    
    # Speech rate score
    if wpm < WPM_SLOW_THRESHOLD:
        speech_rate_score = clamp01(
            (wpm - WPM_TOO_SLOW) / (WPM_SLOW_THRESHOLD - WPM_TOO_SLOW)
        )
    elif wpm <= WPM_OPTIMAL_MAX:
        speech_rate_score = 1.0
    else:
        speech_rate_score = clamp01(
            1 - (wpm - WPM_OPTIMAL_MAX) / WPM_FAST_DECAY_RANGE
        )
    
    # Pause structure score
    pause_score = clamp01(
        1 - (
            metrics["long_pauses_per_min"]
            / (MAX_LONG_PAUSES_PER_MIN * context_config["pause_tolerance"])
        )
    )
    
    # Filler dependency score
    filler_score = clamp01(
        1 - (metrics["fillers_per_min"] / MAX_FILLERS_PER_MIN)
    )
    
    # Rhythmic stability score
    stability_score = clamp01(
        1 - (
            metrics["pause_variability"]
            / (BASE_PAUSE_VARIABILITY * context_config["pause_variability_tolerance"])
        )
    )
    
    # Lexical quality score
    lexical_score = clamp01(
        0.65 * metrics["vocab_richness"]
        + 0.35 * (1 - metrics["repetition_ratio"])
    )
    
    subscores = {
        "speech_rate": speech_rate_score,
        "pause": pause_score,
        "filler": filler_score,
        "stability": stability_score,
        "lexical": lexical_score,
    }
    
    return subscores, context_config

def apply_compound_penalties(subscores: dict, metrics: dict) -> float:
    """
    Penalize combinations of issues that humans perceive
    as 'loss of control', even if each metric alone is acceptable.
    """
    penalty = 0.0

    # Lost-control pattern: hesitation + instability + repetition
    if (
        subscores["filler"] < 0.75 and
        subscores["stability"] < 0.75 and
        metrics["repetition_ratio"] > 0.06
    ):
        penalty += 0.12  # ≈12 points

    # Fluent-but-annoying: smooth but filler-heavy
    if (
        subscores["pause"] > 0.8 and
        metrics["fillers_per_min"] > 3.0
    ):
        penalty += 0.08

    return penalty

def calculate_fluency_score(
    subscores: dict, metrics: dict
) -> int:
    """
    Calculate overall fluency score (0-100).
    
    Args:
        subscores: Dictionary of individual subscores
        
    Returns:
        Fluency score as integer
    """
    raw_score = (
        WEIGHT_PAUSE * subscores["pause"] +
        WEIGHT_FILLER * subscores["filler"] +
        WEIGHT_STABILITY * subscores["stability"] +
        WEIGHT_SPEECH_RATE * subscores["speech_rate"] +
        WEIGHT_LEXICAL * subscores["lexical"]
    )

    penalty = apply_compound_penalties(subscores, metrics)
    raw_score = max(0.0, raw_score - penalty)
    
    return int(round(100 * clamp01(raw_score)))

def detect_issues(
    subscores: dict,
    metrics: dict
) -> List[dict]:
    """
    Detect and categorize fluency issues.
    
    Args:
        subscores: Dictionary of subscores
        metrics: Normalized metrics
        
    Returns:
        List of issue dictionaries sorted by score impact
    """
    issues = []
    
    def issue(severity: str, issue_id: str, root_cause: str, score_impact: int):
        return {
            "issue": issue_id,
            "severity": severity,
            "root_cause": root_cause,
            "score_impact": score_impact,
        }
    
    # Structural blockers
    if subscores["pause"] < PAUSE_SCORE_BLOCK_THRESHOLD:
        issues.append(issue(
            "high",
            "hesitation_structure",
            "Pauses frequently interrupt sentence flow.",
            int((1 - subscores["pause"]) * 30),
        ))
    
    if subscores["filler"] < FILLER_SCORE_BLOCK_THRESHOLD:
        issues.append(issue(
            "high",
            "filler_dependency",
            "Fillers replace silent planning pauses.",
            int((1 - subscores["filler"]) * 25),
        ))
    
    if subscores["stability"] < STABILITY_SCORE_WARN_THRESHOLD:
        issues.append(issue(
            "medium",
            "delivery_instability",
            "Speech rhythm varies unpredictably.",
            int((1 - subscores["stability"]) * 20),
        ))
    
    # Style issues
    if subscores["speech_rate"] < 0.7:
        issues.append(issue(
            "medium",
            "delivery_pacing",
            "Speech rate deviates from optimal clarity range.",
            int((1 - subscores["speech_rate"]) * 15),
        ))
    
    if subscores["lexical"] < LEXICAL_LOW_THRESHOLD:
        issues.append(issue(
            "low",
            "lexical_simplicity",
            "Frequent reuse of common vocabulary.",
            int((1 - subscores["lexical"]) * 10),
        ))
    
    return sorted(issues, key=lambda x: x["score_impact"], reverse=True)

def determine_readiness(
    fluency_score: int,
    issues: List[dict]
) -> str:
    """
    Determine speaker readiness based on score and issues.
    
    Args:
        fluency_score: Overall fluency score
        issues: List of detected issues
        
    Returns:
        Readiness status: 'ready', 'borderline', or 'not_ready'
    """
    high_issues = [i for i in issues if i["severity"] == "high"]
    medium_issues = [i for i in issues if i["severity"] == "medium"]
    
    if len(high_issues) >= 2:
        return "not_ready"
    elif len(high_issues) == 1:
        return "borderline"
    elif len(medium_issues) >= 2:
        return "borderline"
    elif fluency_score >= 80:
        return "ready"
    else:
        return "borderline"

def calculate_benchmarking(
    fluency_score: int,
    readiness: str
) -> dict:
    """
    Calculate benchmarking metrics and practice estimates.
    
    Args:
        fluency_score: Overall fluency score
        readiness: Readiness status
        
    Returns:
        Dictionary with percentile, target, and practice hours
    """
    # Estimate percentile
    if fluency_score >= 85:
        percentile = 80
    elif fluency_score >= 75:
        percentile = 65
    elif fluency_score >= 65:
        percentile = 50
    else:
        percentile = 30
    
    # Calculate score gap
    score_gap = (
        max(0, 80 - fluency_score)
        if readiness != "ready"
        else 0
    )
    
    return {
        "percentile": percentile,
        "target_score": 80,
        "score_gap": score_gap,
        "estimated_guided_practice_hours": score_gap * 0.6,
    }

def generate_action_plan(
    issues: List[dict],
    score_gap: int
) -> List[dict]:
    """
    Generate prioritized action plan with expected gains.
    
    Args:
        issues: List of detected issues
        score_gap: Points needed to reach target
        
    Returns:
        List of action items with priorities and expected gains
    """
    action_plan = []
    
    # Normalize gains to match score gap
    max_gain = sum(i["score_impact"] for i in issues[:3]) or 1
    scale = score_gap / max_gain if score_gap > 0 else 1.0
    
    for idx, issue in enumerate(issues[:3]):
        action_plan.append({
            "priority": idx + 1,
            "focus": issue["issue"],
            "instruction": INSTRUCTIONS.get(
                issue["issue"],
                "Focus on improving this aspect."
            ),
            "expected_score_gain": int(issue["score_impact"] * scale),
        })
    
    return action_plan

def analyze_fluency(
    df_words_full: pd.DataFrame,      # CHANGED: Full timeline with is_filler column
    df_words_content: pd.DataFrame,   # NEW: Content words only (no fillers)
    df_segments: pd.DataFrame,
    df_fillers: pd.DataFrame,
    total_duration: float,
    speech_context: str = "conversational"
) -> dict:
    """
    Complete fluency analysis pipeline.
    
    Args:
        df_words_full: Complete word-level timestamps (includes fillers marked with is_filler)
        df_words_content: Content words only (fillers removed) for WPM calculation
        df_segments: Segment-level timestamps
        df_fillers: Filler/stutter events
        total_duration: Total audio duration in seconds
        speech_context: Type of speech context
        
    Returns:
        Complete analysis dictionary with verdict, metrics, and opinions
    """
    # Check minimum duration
    if total_duration < MIN_ANALYSIS_DURATION_SEC:
        return {
            "verdict": {
                "fluency_score": None,
                "readiness": "insufficient_sample",
            },
            "benchmarking": None,
            "normalized_metrics": None,
            "opinions": None,
        }
    
    # Validate context
    if speech_context not in CONTEXT_CONFIG:
        print(f"⚠️  Warning: Invalid context '{speech_context}'. Using 'conversational'.")
        speech_context = "conversational"
    
    # Get context configuration
    context_config = CONTEXT_CONFIG[speech_context]
    
    # Calculate metrics (CHANGED: pass both word DataFrames)
    metrics = calculate_normalized_metrics(
        df_words_full,      # For pause detection (full timeline)
        df_words_content,   # For WPM and lexical metrics
        df_segments,
        df_fillers,
        total_duration
    )
    
    # Calculate subscores
    subscores, _ = calculate_subscores(metrics, context_config)
    
    # Calculate fluency score
    fluency_score = calculate_fluency_score(subscores, metrics)
    
    # Detect issues
    issues = detect_issues(subscores, metrics)
    
    # Determine readiness
    readiness = determine_readiness(fluency_score, issues)
    
    # Calculate benchmarking
    benchmarking = calculate_benchmarking(fluency_score, readiness)
    
    # Generate action plan
    action_plan = generate_action_plan(issues, benchmarking["score_gap"])
    
    return {
        "verdict": {
            "fluency_score": fluency_score,
            "readiness": readiness,
        },
        "benchmarking": benchmarking,
        "normalized_metrics": metrics,
        "opinions": {
            "primary_issues": issues,
            "action_plan": action_plan,
        },
    }

if __name__ == "__main__":
    # Quick test with dummy data
    import numpy as np
    
    # Create dummy data
    df_words = pd.DataFrame({
        "word": ["hello", "world", "this", "is", "test"],
        "start": [0.0, 0.5, 1.0, 1.5, 2.0],
        "end": [0.4, 0.9, 1.4, 1.9, 2.4],
        "duration": [0.4, 0.4, 0.4, 0.4, 0.4],
        "confidence": [0.9, 0.9, 0.9, 0.9, 0.9],
    })
    
    df_segments = pd.DataFrame({
        "text": ["hello world this is test"],
        "start": [0.0],
        "end": [2.4],
        "duration": [2.4],
        "avg_word_confidence": [0.9],
    })
    
    df_fillers = pd.DataFrame({
        "type": ["filler", "stutter"],
        "text": ["uh", "t"],
        "start": [0.45, 1.45],
        "end": [0.48, 1.48],
        "duration": [0.03, 0.03],
    })
    
    result = analyze_fluency(df_words, df_segments, df_fillers, 2.4)
    print(f"Fluency Score: {result['verdict']['fluency_score']}")
    print(f"Readiness: {result['verdict']['readiness']}")
```

## metrics.py

```python
# metrics.py

# src/metrics.py
"""Fluency metrics calculation and scoring."""
import pandas as pd
import numpy as np
from .config import STOPWORDS

def clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    return max(0.0, min(1.0, x))


def filler_weight(duration: float) -> float:
    """Weight fillers by perceptual impact."""
    if duration < 0.08:
        return 0.2      # micro hesitation
    elif duration < 0.3:
        return 0.6      # subtle filler
    else:
        return 1.0      # real filler
    
def rolling_wpm(df_words, window_sec=10.0):
    wpms = []
    start_times = df_words["start"].values

    for t in start_times:
        window = df_words[
            (df_words["start"] >= t) &
            (df_words["start"] < t + window_sec)
        ]
        if len(window) > 0:
            wpms.append(len(window) * 60 / window_sec)

    return wpms



def overlaps_filler(
    start: float,
    end: float,
    fillers: pd.DataFrame,
    tol: float = 0.05
) -> bool:
    """Check if time range overlaps any filler event."""
    for _, f in fillers.iterrows():
        if start < f["end"] + tol and end > f["start"] - tol:
            return True
    return False

def utterance_lengths(df_words_raw, pause_threshold=0.5):
    lengths = []
    count = 0

    for i in range(len(df_words_raw)):
        count += 1
        if i == len(df_words_raw) - 1:
            lengths.append(count)
        else:
            gap = (
                df_words_raw.iloc[i+1]["start"]
                - df_words_raw.iloc[i]["end"]
            )
            if gap > pause_threshold:
                lengths.append(count)
                count = 0

    return lengths


def calculate_normalized_metrics(
    df_words_raw: pd.DataFrame,      # CHANGED: Full timeline
    df_words_cleaned: pd.DataFrame,   # NEW: Content words only
    df_segments: pd.DataFrame,
    df_fillers: pd.DataFrame,
    total_duration: float
) -> dict:
    """
    Calculate normalized fluency metrics.
    
    Args:
        df_words_full: Complete word timeline (includes fillers with is_filler flag)
        df_words_content: Content words only (fillers removed)
        df_segments: Segment-level timestamps
        df_fillers: Filler/stutter events
        total_duration: Total audio duration in seconds
        
    Returns:
        Dictionary of normalized metrics
    """
    duration_min = max(total_duration / 60.0, 0.5)
    
    # Words per minute - use CONTENT words only
    words_per_minute = (len(df_words_cleaned) * 60) / total_duration

    # Unique word count - use CONTENT words only
    unique_word_count = df_words_cleaned["word"].str.lower().nunique()
    
    # Filler metrics
    filler_events = df_fillers[df_fillers["type"] == "filler"]
    stutter_events = df_fillers[df_fillers["type"] == "stutter"]
    
    fillers_per_min = (
        filler_events["duration"]
        .apply(filler_weight)
        .sum()
        / duration_min
    )
    
    stutters_per_min = len(stutter_events) / duration_min
    
    # Pause detection - use FULL timeline to get accurate gaps
    pause_durations = []
    
    for i in range(1, len(df_words_raw)):
        gap_start = df_words_raw.iloc[i - 1]["end"]
        gap_end = df_words_raw.iloc[i]["start"]
        gap = gap_end - gap_start
        
        # Only count as pause if:
        # 1. Gap is significant (>0.3s)
        # 2. Gap doesn't overlap with detected filler events
        if gap > 0.3 and not overlaps_filler(gap_start, gap_end, df_fillers):
            pause_durations.append(gap)
    
    pause_durations = pd.Series(pause_durations, dtype="float")
    
    # Pause metrics
    long_pauses = pause_durations[pause_durations > 1.0]
    very_long_pauses = pause_durations[pause_durations > 2.0]
    
    long_pauses_per_min = len(long_pauses) / duration_min
    very_long_pauses_per_min = len(very_long_pauses) / duration_min
    
    pause_time_ratio = (
        pause_durations.sum() / total_duration
        if pause_durations.size > 0
        else 0.0
    )
    
    # standard deviation of puse durations, small deviation means more consistent pacing
    pause_variability = (
        pause_durations.std()
        if pause_durations.size > 5
        else 0.0
    )

    pause_frequency = len(pause_durations) / duration_min
    
    # Lexical metrics - use CONTENT words only
    if len(df_words_cleaned) == 0:
        vocab_richness = 0.0
        repetition_ratio = 0.0
    else:
        words_clean = df_words_cleaned["word"].str.lower()
        
        vocab_richness = words_clean.nunique() / len(words_clean)


    words_clean_nostopwords = (
        df_words_cleaned["word"]
        .str.lower()
        .loc[~df_words_cleaned["word"].isin(STOPWORDS)]
    )
    # what ratio of words are the most common word - higher means more repetition (speakers tend to repeat safe words)
    repetition_ratio = (
        words_clean_nostopwords.value_counts().iloc[0] / len(words_clean_nostopwords)
        if len(words_clean_nostopwords) > 0
        else 0.0
    )

    wpm_rolling = rolling_wpm(df_words_cleaned)

    # compared to mean wpm (rolling), how much does the speech rate deviate? low = consistent pacing
    # < 0.2 very steady, 0.2-0.4 moderate, >0.4 highly variable
    speech_rate_variability = (
        np.std(wpm_rolling) / np.mean(wpm_rolling) if len(wpm_rolling) > 3 else 0.0
    )

    # avg words spoken per utterance (between pauses)
    utt_lengths = utterance_lengths(df_words_raw)
    mean_utterance_length = np.mean(utt_lengths) if utt_lengths else 0.0

    pause_after_filler = 0
    total_fillers = len(filler_events)

    for _, f in filler_events.iterrows():
        for gap in pause_durations:
            if gap > 0.3 and abs(f["end"] - gap_start) < 0.2:
                pause_after_filler += 1
                break

    pause_after_filler_rate = (
        pause_after_filler / total_fillers if total_fillers > 0 else 0.0
    )

    mean_word_confidence = (
        df_words_raw["confidence"].mean()
        if "confidence" in df_words_raw.columns and len(df_words_raw) > 0
        else 0.0
    )

    low_confidence_ratio = (
        (df_words_raw["confidence"] < 0.7).sum() / len(df_words_raw)
        if "confidence" in df_words_raw.columns and len(df_words_raw) > 0
        else 0.0
    )

    lexical_density = (
        len(words_clean_nostopwords) / len(df_words_raw)
        if len(df_words_raw) > 0
        else 0.0
    )


    
    return {
        "wpm": words_per_minute,
        "unique_word_count": unique_word_count,
        "fillers_per_min": fillers_per_min,
        "stutters_per_min": stutters_per_min,
        "long_pauses_per_min": long_pauses_per_min,
        "very_long_pauses_per_min": very_long_pauses_per_min,
        "pause_frequency": pause_frequency,
        "pause_time_ratio": pause_time_ratio,
        "pause_variability": pause_variability,
        "vocab_richness": vocab_richness,
        "repetition_ratio": repetition_ratio,
        "speech_rate_variability": speech_rate_variability,
        "mean_utterance_length": mean_utterance_length,
        "pause_after_filler_rate": pause_after_filler_rate,
        "mean_word_confidence": mean_word_confidence,
        "low_confidence_ratio": low_confidence_ratio,
        "lexical_density": lexical_density,
    }
```

