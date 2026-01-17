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

from src.analyzer_old import analyze_speech


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

## analyze_band.py

```python
# analyze_band.py

# analyze_band.py
import sys
from pathlib import Path
from src.analyzer_raw import analyze_speech
from src.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.ielts_band_scorer import IELTSBandScorer
from datetime import datetime

PROJECT_ROOT = Path.cwd().parent
sys.path.insert(0, str(PROJECT_ROOT))

def build_analysis(
    result: dict,
    llm_metrics: dict,
) -> dict:
    # ---- Lexical density ----
    total_words = result["statistics"]["total_words_transcribed"]
    content_words = result["statistics"]["content_words"]

    # ---- Word confidence metrics ----
    confidences = [
        w["confidence"]
        for w in result["timestamps"]["words_timestamps_raw"]
        if w.get("confidence") is not None
    ]

    mean_word_confidence = (
        sum(confidences) / len(confidences) if confidences else 0.0
    )

    low_confidence_ratio = (
        sum(1 for c in confidences if c < 0.7) / len(confidences)
        if confidences else 0.0
    )


    return {
        "metadata": {
            "audio_duration_sec": round(result["audio_duration_sec"], 2),
            "speaking_time_sec": round(result["speaking_time_sec"], 2),
            "total_words_transcribed": total_words,
            "content_word_count": content_words,
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
        },
        "fluency_coherence": {
            "pauses": {
                "pause_frequency_per_min": result.get("pause_frequency"),
                "long_pause_rate": result["long_pauses_per_min"],
                "pause_variability": float(result["pause_variability"]),
            },
            "rate": {
                "speech_rate_wpm": float(result["wpm"]),
                "speech_rate_variability": float(result["speech_rate_variability"]),
            },
            "disfluency": {
                "filler_frequency_per_min": float(result["fillers_per_min"]),
                "stutter_frequency_per_min": float(result["stutters_per_min"]),
                "repetition_rate": float(result["repetition_ratio"]),
            },
            "coherence": {
                "coherence_breaks": llm_metrics["coherence_breaks"],
                "topic_relevance": llm_metrics["topic_relevance"],
            },
        },
        "lexical_resource": {
            "breadth": {
                "unique_word_count": int(
                    round(result["vocab_richness"] * content_words)
                ),
                "lexical_diversity": float(result["vocab_richness"]),
                "lexical_density": round(result["lexical_density"], 3),
                "most_frequent_word_ratio": float(result["repetition_ratio"]),
            },
            "quality": {
                "word_choice_errors": llm_metrics["word_choice_errors"],
                "advanced_vocabulary_count": llm_metrics["advanced_vocabulary_count"],
            },
        },
        "grammatical_range_accuracy": {
            "complexity": {
                "mean_utterance_length": float(result["mean_utterance_length"]),
                "complex_structures_attempted": llm_metrics["complex_structures_attempted"],
                "complex_structures_accurate": llm_metrics["complex_structures_accurate"],
            },
            "accuracy": {
                "grammar_errors": llm_metrics["grammar_errors"],
                "meaning_blocking_error_ratio": llm_metrics["meaning_blocking_error_ratio"],
            },
        },
        "pronunciation": {
            "intelligibility": {
                "mean_word_confidence": round(mean_word_confidence, 3),
                "low_confidence_ratio": round(low_confidence_ratio, 3),
            },
            "prosody": {
                "monotone_detected": result["statistics"]["is_monotone"],
            },
        },
        "raw_data": {
            "word_timestamps": result["timestamps"]["words_timestamps_raw"],
            "pause_events": result.get("pause_events", []),
            "filler_events": result["timestamps"]["filler_timestamps"],
            "stutter_events": result.get("stutter_events", []),
        },
    }

async def analyze_band_from_audio(audio_path: str) -> dict:
    """Analyze speech and score IELTS band."""
    result = await analyze_speech(audio_path)
    llm_result = extract_llm_annotations(result["raw_transcript"])
    llm_metrics = aggregate_llm_metrics(llm_result)
    scorer = IELTSBandScorer()
    analysis = build_analysis(result, llm_metrics)
    band_scores = scorer.score(analysis)
    report = {"band_scores": band_scores, "analysis": analysis}
    return report


async def analyze_band_from_analysis(raw_analysis: dict, llm_metrics: dict) -> dict:
    """Analyze speech and score IELTS band."""
    scorer = IELTSBandScorer()
    analysis = build_analysis(raw_analysis, llm_metrics)
    band_scores = scorer.score(analysis)
    report = {"band_scores": band_scores, "analysis": analysis}
    return report
```

## analyzer_old.py

```python
# analyzer_old.py

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

# src/analyzer_raw.py
"""Main fluency analysis orchestrator."""
import asyncio
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
    detect_phonemes_wav2vec,
    detect_fillers_whisper,
    merge_filler_detections,
    group_stutters,
)
from .metrics import calculate_normalized_metrics
from src.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.prosody_extraction import is_monotone_speech

# Load environment variables
load_dotenv()

# Set pandas display options
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", 0)


def generate_transcript_raw(
    df_words_raw: pd.DataFrame,
) -> str:
    if df_words_raw.empty:
        return ""
    return " ".join(df_words_raw["text"].astype(str))

def combine_words_and_fillers(
    df_words_raw: pd.DataFrame,
    df_final_fillers: pd.DataFrame
) -> pd.DataFrame:
    """
    Combine transcribed words and disfluency events into a single chronological token stream.
    
    Each row represents a spoken token (word or disfluency) with:
      - 'start', 'end', 'text'
      - 'source': 'whisper' or 'wav2vec'
      - 'type': 'word', 'filler', or 'stutter'
    
    Only non-empty, valid tokens are included.
    """
    tokens = []

    # Add Whisper words
    if not df_words_raw.empty:
        for _, row in df_words_raw.iterrows():
            word = str(row.get("word", "")).strip()
            if word and not pd.isna(row.get("start")):
                tokens.append({
                    "start": float(row["start"]),
                    "end": float(row["end"]),
                    "text": word,
                    "source": "whisper",
                    "type": "word"
                })

    # Add Wav2Vec2 fillers/stutters (only if they have non-empty 'text')
    if not df_final_fillers.empty:
        for _, row in df_final_fillers.iterrows():
            text = row.get("text", "")
            if pd.isna(text):
                text = ""
            else:
                text = str(text).strip()
            
            if text and "start" in row and "end" in row:
                tokens.append({
                    "start": float(row["start"]),
                    "end": float(row["end"]),
                    "text": text,
                    "source": "wav2vec",
                    "type": row.get("type", "filler")  # 'filler' or 'stutter'
                })

    if not tokens:
        return pd.DataFrame(columns=["start", "end", "text", "source", "type"])

    # Sort by start time
    tokens_sorted = sorted(tokens, key=lambda x: x["start"])
    
    # Convert to DataFrame
    df_combined = pd.DataFrame(tokens_sorted)
    
    # Optional: reset index
    df_combined.reset_index(drop=True, inplace=True)
    
    return df_combined

async def analyze_speech(
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
    transcribe_verbatim_fillers_task = asyncio.to_thread(transcribe_verbatim_fillers, str(audio_path), device=device)
    is_monotone_speech_task = asyncio.to_thread(is_monotone_speech, audio_path)
    detect_phonemes_wav2vec_task = asyncio.to_thread(detect_phonemes_wav2vec, audio_path)

    verbatim_result, is_monotone, df_wav2vec = await asyncio.gather(
        transcribe_verbatim_fillers_task,
        is_monotone_speech_task,    
        detect_phonemes_wav2vec_task
    )

    # Extract words and segments
    df_words_whisper_raw = extract_words_dataframe(verbatim_result)
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
    print(f"  Words: {len(df_words_whisper_raw)}")
    
    # Step 2: Mark fillers in words and segments
    print("\n[2/5] Marking filler words...")
    df_words_whisper_raw = mark_filler_words(df_words_whisper_raw, CORE_FILLERS)
    df_segments = mark_filler_segments(df_segments, CORE_FILLERS)
    
    filler_count = df_words_whisper_raw['is_filler'].sum()
    print(f"  Marked: {filler_count} filler words")
    
    # Get content-only words
    df_words_content = get_content_words(df_words_whisper_raw)
    print(f"  Content words: {len(df_words_content)}")

    
    # Step 3: Align words with WhisperX
    print("\n[3/5] Aligning words with WhisperX...")
    audio, _ = load_audio(audio_path)
    df_aligned_words = align_words_whisperx(verbatim_result["segments"], audio, device=device)
    print(f"  Aligned: {len(df_aligned_words)} words")
    
    # Step 4: Detect fillers with Wav2Vec2
    print("\n[4/5] Detecting subtle fillers with Wav2Vec2...")
    df_wav2vec_fillers = detect_fillers_wav2vec(df_wav2vec, df_aligned_words)
    
    # Extract Whisper-detected fillers (already marked in df_words)
    df_whisper_fillers = df_words_whisper_raw[df_words_whisper_raw['is_filler']].copy()
    df_whisper_fillers['type'] = 'filler'
    df_whisper_fillers['text'] = df_whisper_fillers['word'].str.lower()
    df_whisper_fillers['style'] = 'clear'  # Add style column
    df_whisper_fillers = df_whisper_fillers[['type', 'text', 'start', 'end', 'duration', 'style']]
    
    # Merge detections
    df_merged_fillers = merge_filler_detections(df_whisper_fillers, df_wav2vec_fillers)
    df_final_fillers = group_stutters(df_merged_fillers)
    print(f"  Total events: {len(df_final_fillers)}")

    df_words_raw = combine_words_and_fillers(df_words_whisper_raw, df_final_fillers)
    transcript_raw = generate_transcript_raw(df_words_raw)
    print(f"  Transcript: {transcript_raw}")
    
    print("\n[5/5] Calculating raw score...")
    normalized_metrics = calculate_normalized_metrics(
        df_words_asr=df_words_whisper_raw,      # ✅ full ASR words (with fillers)
        df_words_content=df_words_content,       # ✅ content-only
        df_segments=df_segments,
        df_fillers=df_final_fillers,
        total_duration=total_duration,
        # df_tokens_enriched=df_tokens_enriched  # optional, not used yet
    )
    
    # Build response with multiple word views
    response = {
        "raw_transcript": transcript_raw,
        **normalized_metrics,
        # Statistics
        "statistics": {
            "total_words_transcribed": len(df_words_whisper_raw),
            "content_words": len(df_words_content),
            "filler_words_detected": filler_count,
            "filler_percentage": round(100 * filler_count / len(df_words_whisper_raw), 2) if len(df_words_whisper_raw) > 0 else 0,
            "is_monotone": is_monotone
        }, 
        "timestamps": {
            # Complete timeline with filler markers
            "words_timestamps_raw": df_words_whisper_raw.to_dict(orient="records"),
            
            # Content words only (for clean display)
            "words_timestamps_cleaned": df_words_content.to_dict(orient="records"),
            
            # Segments with filler flags
            "segment_timestamps": df_segments.to_dict(orient="records"),
            
            # Detected filler events (including stutters)
            "filler_timestamps": df_final_fillers.to_dict(orient="records"),
        }
    }
    
    return response


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: fluency-analyze <audio_file> [context]")
        print("Contexts: conversational (default), narrative, presentation, interview")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    speech_context = sys.argv[2] if len(sys.argv) > 2 else "conversational"
    
    result = asyncio.run(analyze_speech(audio_path, speech_context))
    
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
    df_wav2vec: pd.DataFrame,
    aligned_words: pd.DataFrame
) -> pd.DataFrame:
    """
    Detect fillers and stutters using Wav2Vec2 phoneme detection.
    
    Args:
        df_wav2vec: wav to vec phoneme events
        aligned_words: DataFrame with aligned word timestamps
        
    Returns:
        DataFrame with detected filler/stutter events
    """
    # Get phoneme-level events
    
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

## ielts_band_scorer.py

```python
# ielts_band_scorer.py

"""
IELTS Band Scorer v3.0 - Super Accurate Production System
===========================================================

Philosophy: Simulate experienced IELTS examiner judgment through multi-layered
scoring with qualitative gates and quantitative metrics.

Key Innovations:
1. Three-stage scoring (base → deductions → gates)
2. Sophistication-based lexical scoring (not just diversity)
3. Prosody-dominant pronunciation assessment
4. Complex structure inventory tracking
5. Error severity classification
6. Statistical calibration to match real-world distributions

Target Accuracy: 90%+ correlation with human examiners (±0.5 bands)
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from collections import Counter
import re


class IELTSBandScorer :
    """
    Production-grade IELTS Speaking scorer with examiner-like judgment.
    """
    
    # ========================================================================
    # CONFIGURATION - EXAMINER-CALIBRATED THRESHOLDS
    # ========================================================================
    
    # Minimum sample requirements
    MIN_DURATION_SEC = 30
    MIN_CONTENT_WORDS = 50
    MIN_SPEAKING_TIME_SEC = 25
    
    # Fluency & Coherence thresholds
    FLUENCY_WPM_VERY_SLOW = 60
    FLUENCY_WPM_SLOW = 75
    FLUENCY_WPM_HESITANT = 90
    FLUENCY_WPM_COMFORTABLE = 120
    FLUENCY_WPM_RUSHED = 200
    
    FLUENCY_LONG_PAUSE_SEVERE = 3.0
    FLUENCY_LONG_PAUSE_FREQUENT = 2.0
    FLUENCY_LONG_PAUSE_NOTICEABLE = 1.0
    FLUENCY_LONG_PAUSE_MINIMAL = 0.5
    
    FLUENCY_FILLER_EXCESSIVE = 6.0
    FLUENCY_FILLER_FREQUENT = 4.0
    FLUENCY_FILLER_SOME = 2.0
    FLUENCY_FILLER_MINIMAL = 1.0
    
    FLUENCY_REPETITION_EXCESSIVE = 0.15
    FLUENCY_REPETITION_FREQUENT = 0.08
    FLUENCY_REPETITION_SOME = 0.04
    FLUENCY_REPETITION_MINIMAL = 0.02
    
    # Lexical Resource thresholds
    LEXICAL_DIVERSITY_VERY_LIMITED = 0.35
    LEXICAL_DIVERSITY_LIMITED = 0.45
    LEXICAL_DIVERSITY_ADEQUATE = 0.55
    LEXICAL_DIVERSITY_GOOD = 0.65
    
    LEXICAL_ERROR_RATE_FREQUENT = 5.0
    LEXICAL_ERROR_RATE_SOME = 3.0
    LEXICAL_ERROR_RATE_OCCASIONAL = 1.5
    LEXICAL_ERROR_RATE_RARE = 0.5
    
    # Grammar thresholds
    GRAMMAR_MLU_VERY_SIMPLE = 7
    GRAMMAR_MLU_SIMPLE = 9
    GRAMMAR_MLU_MODERATE = 11
    GRAMMAR_MLU_COMPLEX = 13
    
    GRAMMAR_ERROR_RATE_FREQUENT = 8.0
    GRAMMAR_ERROR_RATE_NOTICEABLE = 5.0
    GRAMMAR_ERROR_RATE_SOME = 3.0
    GRAMMAR_ERROR_RATE_OCCASIONAL = 1.5
    
    GRAMMAR_COMPLEX_ACC_VERY_POOR = 0.3
    GRAMMAR_COMPLEX_ACC_POOR = 0.5
    GRAMMAR_COMPLEX_ACC_WEAK = 0.7
    GRAMMAR_COMPLEX_ACC_GOOD = 0.85
    GRAMMAR_COMPLEX_ACC_EXCELLENT = 0.90
    
    GRAMMAR_BLOCKING_FREQUENT = 0.3
    GRAMMAR_BLOCKING_SOME = 0.2
    GRAMMAR_BLOCKING_OCCASIONAL = 0.1
    
    # Pronunciation thresholds
    PRONUN_INTELLIGIBILITY_POOR = 0.6
    PRONUN_INTELLIGIBILITY_FAIR = 0.7
    PRONUN_INTELLIGIBILITY_GOOD = 0.8
    PRONUN_INTELLIGIBILITY_VERY_GOOD = 0.9
    PRONUN_INTELLIGIBILITY_EXCELLENT = 0.95
    
    # Statistical calibration targets
    STAT_BAND_8_PLUS_MAX_PCT = 5.0
    STAT_BAND_9_MAX_PCT = 1.0
    
    def __init__(self):
        """Initialize scorer with supporting resources"""
        self.score_history = []
        
        # Idiomatic expressions database (expanded)
        self.IDIOMS = {
            'once in a blue moon', 'butterflies in my stomach', 'break the ice',
            'hit the nail on the head', 'under the weather', 'spill the beans',
            'cost an arm and a leg', 'piece of cake', 'let the cat out of the bag',
            'burn the midnight oil', 'pull someone\'s leg', 'the ball is in your court',
            'on the same page', 'get cold feet', 'a blessing in disguise',
            'actions speak louder than words', 'at the drop of a hat', 'back to square one',
            'barking up the wrong tree', 'beat around the bush', 'bite the bullet',
            'break a leg', 'call it a day', 'cut corners', 'face the music',
            'get the ball rolling', 'hit the books', 'in the nick of time',
            'jump on the bandwagon', 'kill two birds with one stone', 'miss the boat',
            'no pain no gain', 'on thin ice', 'pull yourself together', 'read between the lines',
            'the best of both worlds', 'time flies', 'up in arms', 'when pigs fly'
        }
        
        # Common collocations (verb + noun)
        self.COLLOCATIONS = {
            'make': ['decision', 'choice', 'mistake', 'progress', 'effort', 'appointment'],
            'take': ['break', 'chance', 'time', 'opportunity', 'responsibility', 'action'],
            'have': ['look', 'chat', 'discussion', 'argument', 'conversation', 'meeting'],
            'do': ['homework', 'research', 'favor', 'damage', 'harm', 'business'],
            'give': ['advice', 'feedback', 'presentation', 'speech', 'hand', 'permission'],
            'pay': ['attention', 'compliment', 'price', 'fine', 'tribute', 'respect'],
            'catch': ['cold', 'bus', 'train', 'attention', 'breath', 'glimpse'],
            'keep': ['promise', 'secret', 'record', 'eye', 'mind', 'track']
        }
        
        # Academic Word List (sample - top 50 families)
        self.AWL = {
            'analysis', 'approach', 'area', 'assess', 'assume', 'authority', 'available',
            'benefit', 'concept', 'consistent', 'constitutional', 'context', 'contract',
            'create', 'data', 'define', 'derive', 'distribute', 'economy', 'environment',
            'establish', 'estimate', 'evident', 'export', 'factor', 'finance', 'formula',
            'function', 'identify', 'income', 'indicate', 'individual', 'interpret',
            'involve', 'issue', 'labor', 'legal', 'legislate', 'major', 'method',
            'occur', 'percent', 'period', 'policy', 'principle', 'proceed', 'process',
            'require', 'research', 'respond', 'role', 'section', 'sector', 'significant',
            'similar', 'source', 'specific', 'structure', 'theory', 'vary'
        }
        
        # Phrasal verbs
        self.PHRASAL_VERBS = {
            'come across', 'come up with', 'carry out', 'find out', 'figure out',
            'get along', 'get over', 'give up', 'go on', 'look after', 'look for',
            'look into', 'make up', 'pick up', 'put off', 'put up with', 'run into',
            'set up', 'take off', 'turn down', 'turn up', 'work out'
        }
        
        # Simple overused words to penalize
        self.BASIC_WORDS = {
            'thing', 'stuff', 'get', 'make', 'do', 'put', 'take',
            'good', 'bad', 'big', 'small', 'nice', 'very', 'really'
        }
    
    # ========================================================================
    # MAIN ENTRY POINT
    # ========================================================================
    
    def score(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main scoring function.
        
        Args:
            analysis_data: Dictionary containing:
                - metadata
                - fluency_coherence
                - lexical_resource
                - grammatical_range_accuracy
                - pronunciation
                - raw_transcript (optional)
        
        Returns:
            Dictionary with overall_band, criterion_bands, feedback, diagnostics
        """
        
        # Step 1: Validate input
        is_valid, reason = self._validate_input(analysis_data)
        if not is_valid:
            return {
                'overall_band': None,
                'criterion_bands': None,
                'feedback_summary': f'Insufficient data: {reason}',
                'validation_failed': True
            }
        
        metadata = analysis_data['metadata']
        transcript = analysis_data.get('raw_transcript', '').lower()
        
        # Step 2: Enhanced feature extraction
        enhanced_features = self._enhance_features(analysis_data, transcript)
        
        # Step 3: Score each criterion with diagnostics
        fluency_result = self._score_fluency_coherence(
            analysis_data['fluency_coherence'],
            metadata
        )
        
        lexical_result = self._score_lexical_resource(
            analysis_data['lexical_resource'],
            enhanced_features['lexical'],
            metadata,
            transcript
        )
        
        grammar_result = self._score_grammatical_range_accuracy(
            analysis_data['grammatical_range_accuracy'],
            metadata
        )
        
        pronunciation_result = self._score_pronunciation(
            analysis_data['pronunciation'],
            enhanced_features['pronunciation'],
            metadata
        )
        
        # Step 4: Calculate overall band
        criterion_bands = {
            'fluency_coherence': fluency_result['score'],
            'lexical_resource': lexical_result['score'],
            'grammatical_range_accuracy': grammar_result['score'],
            'pronunciation': pronunciation_result['score']
        }
        
        overall_band = self._calculate_overall_band(
            criterion_bands,
            metadata
        )
        
        # Step 5: Generate detailed feedback
        feedback = self._generate_feedback(
            criterion_bands,
            overall_band,
            {
                'fluency': fluency_result,
                'lexical': lexical_result,
                'grammar': grammar_result,
                'pronunciation': pronunciation_result
            }
        )
        
        # Record for statistical calibration
        self.score_history.append(overall_band)
        
        return {
            'overall_band': overall_band,
            'criterion_bands': criterion_bands,
            'feedback_summary': feedback['summary'],
            'detailed_diagnostics': {
                'fluency': fluency_result,
                'lexical': lexical_result,
                'grammar': grammar_result,
                'pronunciation': pronunciation_result
            },
            'strengths': feedback['strengths'],
            'areas_for_improvement': feedback['improvements']
        }
    
    # ========================================================================
    # INPUT VALIDATION
    # ========================================================================
    
    def _validate_input(self, data: Dict) -> Tuple[bool, str]:
        """Validate minimum sample requirements"""
        
        metadata = data.get('metadata', {})
        
        # Check duration
        duration = metadata.get('audio_duration_sec', 0)
        if duration < self.MIN_DURATION_SEC:
            return False, f"Duration {duration}s < {self.MIN_DURATION_SEC}s required"
        
        # Check content words
        content_words = metadata.get('content_word_count', 0)
        if content_words < self.MIN_CONTENT_WORDS:
            return False, f"Only {content_words} words < {self.MIN_CONTENT_WORDS} required"
        
        # Check speaking time
        speaking_time = metadata.get('speaking_time_sec', 0)
        if speaking_time < self.MIN_SPEAKING_TIME_SEC:
            return False, f"Speaking time {speaking_time}s < {self.MIN_SPEAKING_TIME_SEC}s"
        
        # Check required fields
        required = ['fluency_coherence', 'lexical_resource', 
                   'grammatical_range_accuracy', 'pronunciation']
        for field in required:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        return True, ""
    
    # ========================================================================
    # FEATURE ENHANCEMENT
    # ========================================================================
    
    def _enhance_features(self, data: Dict, transcript: str) -> Dict:
        """Extract additional features not in base analysis"""
        
        enhanced = {
            'lexical': self._enhance_lexical_features(
                data['lexical_resource'], 
                transcript,
                data['metadata']['content_word_count']
            ),
            'pronunciation': self._enhance_pronunciation_features(
                data['pronunciation']
            )
        }
        
        return enhanced
    
    def _enhance_lexical_features(self, lexical: Dict, transcript: str, word_count: int) -> Dict:
        """Deep lexical analysis"""
        
        words = transcript.lower().split()
        
        # Detect idiomatic expressions
        idiom_count = 0
        found_idioms = []
        for idiom in self.IDIOMS:
            if idiom in transcript:
                idiom_count += 1
                found_idioms.append(idiom)
        
        # Check collocation accuracy
        collocation_correct = 0
        collocation_total = 0
        for verb, nouns in self.COLLOCATIONS.items():
            for noun in nouns:
                pattern = f"{verb}.*{noun}"
                if re.search(pattern, transcript):
                    collocation_total += 1
                    collocation_correct += 1  # Simplified - assume correct if found
        
        # Count Academic Word List coverage
        awl_count = sum(1 for word in words if any(awl in word for awl in self.AWL))
        
        # Count phrasal verbs
        phrasal_count = sum(1 for pv in self.PHRASAL_VERBS if pv in transcript)
        
        # Count basic word overuse
        basic_overuse = sum(words.count(word) for word in self.BASIC_WORDS)
        
        # Calculate sophistication score (0-10)
        sophistication = 0.0
        sophistication += min(3.0, idiom_count * 0.5)  # Idioms: max 3 pts
        sophistication += min(2.0, (collocation_correct / max(1, collocation_total)) * 2)  # Collocations: max 2 pts
        sophistication += min(2.0, awl_count * 0.2)  # AWL: max 2 pts
        sophistication += min(1.0, phrasal_count * 0.25)  # Phrasal verbs: max 1 pt
        sophistication += min(2.0, (word_count / 100) * 0.5)  # Length bonus: max 2 pts
        
        return {
            'idiomatic_expressions': {
                'count': idiom_count,
                'examples': found_idioms
            },
            'collocation_accuracy': {
                'correct': collocation_correct,
                'total': collocation_total
            },
            'academic_word_list_coverage': awl_count,
            'phrasal_verbs': {
                'count': phrasal_count
            },
            'basic_word_overuse': basic_overuse,
            'sophistication_score': sophistication
        }
    
    def _enhance_pronunciation_features(self, pronunciation: Dict) -> Dict:
        """Calculate prosody score from available features"""
        
        # Use monotone detection as primary prosody indicator
        monotone = pronunciation.get('prosody', {}).get('monotone_detected', True)
        
        # Estimate prosody quality
        if monotone:
            prosody_score = 0.4  # Poor prosody
        else:
            # Use confidence metrics as proxy for prosodic quality
            conf = pronunciation['intelligibility']['mean_word_confidence']
            prosody_score = min(0.8, conf * 0.9)  # Good but not native-like
        
        return {
            'prosody_quality_score': prosody_score,
            'has_natural_intonation': not monotone
        }
    
    # ========================================================================
    # CRITERION SCORERS
    # ========================================================================
    
    def _score_fluency_coherence(self, fluency: Dict, metadata: Dict) -> Dict:
        """
        Three-stage fluency scoring: base → deductions → gates
        """
        
        base_score = 9.0
        deductions = []
        gates = []
        
        # Extract metrics
        wpm = fluency['rate']['speech_rate_wpm']
        long_pauses = fluency['pauses']['long_pause_rate']
        pause_freq = fluency['pauses']['pause_frequency_per_min']
        fillers = fluency['disfluency']['filler_frequency_per_min']
        repetition = fluency['disfluency']['repetition_rate']
        coherence_breaks = fluency['coherence']['coherence_breaks']
        topic_relevant = fluency['coherence']['topic_relevance']
        
        # ============ STAGE 1: DEDUCTIONS ============
        
        # Speech rate
        if wpm < self.FLUENCY_WPM_VERY_SLOW:
            deductions.append(('speech_too_slow', 3.0))
        elif wpm < self.FLUENCY_WPM_SLOW:
            deductions.append(('speech_slow', 2.0))
        elif wpm < self.FLUENCY_WPM_HESITANT:
            deductions.append(('speech_hesitant', 1.0))
        elif wpm > self.FLUENCY_WPM_RUSHED:
            deductions.append(('speech_rushed', 0.5))
        
        # Long pauses
        if long_pauses > self.FLUENCY_LONG_PAUSE_SEVERE:
            deductions.append(('excessive_pausing', 2.5))
        elif long_pauses > self.FLUENCY_LONG_PAUSE_FREQUENT:
            deductions.append(('frequent_pausing', 1.5))
        elif long_pauses > self.FLUENCY_LONG_PAUSE_NOTICEABLE:
            deductions.append(('noticeable_pausing', 0.5))
        
        # Fillers
        if fillers > self.FLUENCY_FILLER_EXCESSIVE:
            deductions.append(('excessive_fillers', 2.5))
        elif fillers > self.FLUENCY_FILLER_FREQUENT:
            deductions.append(('frequent_fillers', 1.5))
        elif fillers > self.FLUENCY_FILLER_SOME:
            deductions.append(('some_fillers', 0.5))
        
        # Repetition
        if repetition > self.FLUENCY_REPETITION_EXCESSIVE:
            deductions.append(('excessive_repetition', 2.0))
        elif repetition > self.FLUENCY_REPETITION_FREQUENT:
            deductions.append(('frequent_repetition', 1.0))
        elif repetition > self.FLUENCY_REPETITION_SOME:
            deductions.append(('some_repetition', 0.3))
        
        # Coherence
        if not topic_relevant:
            deductions.append(('off_topic', 3.0))
        
        if coherence_breaks >= 3:
            deductions.append(('severe_coherence_loss', 2.5))
        elif coherence_breaks == 2:
            deductions.append(('moderate_coherence_loss', 1.5))
        elif coherence_breaks == 1:
            deductions.append(('minor_coherence_loss', 0.5))
        
        # Apply deductions
        for reason, amount in deductions:
            base_score -= amount
        
        # ============ STAGE 2: HARD GATES ============
        
        # Gate 1: Band 1 = no communication possible
        if not topic_relevant or wpm < 30:
            gates.append(('no_communication', 1.5))
        
        # Gate 2: Band 3 ceiling
        if wpm < self.FLUENCY_WPM_VERY_SLOW and coherence_breaks >= 2:
            gates.append(('very_limited_communication', 3.5))
        
        # Gate 3: Band 5 ceiling - must avoid this unfair penalty
        # Only apply if BOTH conditions severe
        if coherence_breaks >= 3 and fillers > self.FLUENCY_FILLER_EXCESSIVE:
            gates.append(('unstable_fluency', 5.5))
        
        # Gate 4: Band 7 ceiling
        if long_pauses > self.FLUENCY_LONG_PAUSE_NOTICEABLE or fillers > self.FLUENCY_FILLER_SOME:
            gates.append(('lacks_native_fluency', 7.5))
        
        # Apply strictest gate
        if gates:
            gated_score = min(g[1] for g in gates)
            base_score = min(base_score, gated_score)
        
        # ============ STAGE 3: POSITIVE INDICATORS ============
        
        # Band 8-9 requires excellence across all metrics
        if base_score >= 8.0:
            if not (wpm >= self.FLUENCY_WPM_COMFORTABLE and 
                   long_pauses < self.FLUENCY_LONG_PAUSE_MINIMAL and
                   fillers < self.FLUENCY_FILLER_MINIMAL and
                   repetition < self.FLUENCY_REPETITION_MINIMAL):
                base_score = min(base_score, 7.5)
        
        final_score = self._round(base_score)
        
        return {
            'score': final_score,
            'deductions': deductions,
            'gates': gates,
            'metrics': {
                'wpm': wpm,
                'long_pauses': long_pauses,
                'fillers': fillers,
                'repetition': repetition,
                'coherence_breaks': coherence_breaks
            }
        }
    
    def _score_lexical_resource(self, lexical: Dict, enhanced: Dict, 
                                metadata: Dict, transcript: str) -> Dict:
        """
        Three-stage lexical scoring with sophistication emphasis
        """
        
        base_score = 9.0
        deductions = []
        gates = []
        
        word_count = metadata['content_word_count']
        sophistication = enhanced['sophistication_score']
        
        # ============ STAGE 1: DEDUCTIONS ============
        
        # Diversity (necessary but not sufficient)
        diversity = lexical['breadth']['lexical_diversity']
        if diversity < self.LEXICAL_DIVERSITY_VERY_LIMITED:
            deductions.append(('very_limited_range', 3.0))
        elif diversity < self.LEXICAL_DIVERSITY_LIMITED:
            deductions.append(('limited_range', 2.0))
        elif diversity < self.LEXICAL_DIVERSITY_ADEQUATE:
            deductions.append(('adequate_range', 1.0))
        
        # Basic word overuse
        basic_overuse = enhanced['basic_word_overuse']
        if basic_overuse > 20:
            deductions.append(('excessive_basic_vocab', 2.0))
        elif basic_overuse > 10:
            deductions.append(('noticeable_basic_vocab', 1.0))
        
        # Word choice errors
        error_rate = (lexical['quality']['word_choice_errors'] / word_count) * 100
        if error_rate > self.LEXICAL_ERROR_RATE_FREQUENT:
            deductions.append(('frequent_word_errors', 2.5))
        elif error_rate > self.LEXICAL_ERROR_RATE_SOME:
            deductions.append(('some_word_errors', 1.5))
        elif error_rate > self.LEXICAL_ERROR_RATE_OCCASIONAL:
            deductions.append(('occasional_word_errors', 0.5))
        
        # Apply deductions
        for reason, amount in deductions:
            base_score -= amount
        
        # ============ STAGE 2: HARD GATES (CRITICAL) ============
        
        # Gate 1: No sophistication = max Band 5.5
        if sophistication < 3.0:
            gates.append(('no_sophistication', 5.5))
        
        # Gate 2: No idiomatic usage = max Band 6.5
        if enhanced['idiomatic_expressions']['count'] == 0:
            gates.append(('no_idiomatic_usage', 6.5))
        
        # Gate 3: Poor collocations = max Band 6.0
        if enhanced['collocation_accuracy']['total'] > 0:
            col_acc = (enhanced['collocation_accuracy']['correct'] / 
                      enhanced['collocation_accuracy']['total'])
            if col_acc < 0.6:
                gates.append(('poor_collocations', 6.0))
        
        # Gate 4: No advanced vocabulary = max Band 5.5
        if lexical['quality']['advanced_vocabulary_count'] == 0 and word_count >= 80:
            gates.append(('no_advanced_vocabulary', 5.5))
        
        # Gate 5: Band 7+ requires AWL coverage
        if enhanced['academic_word_list_coverage'] < 2 and base_score >= 7.0:
            gates.append(('insufficient_academic_vocab', 6.5))
        
        # Gate 6: Band 7+ requires phrasal verbs
        if enhanced['phrasal_verbs']['count'] == 0 and base_score >= 7.0:
            gates.append(('no_phrasal_verbs', 6.5))
        
        # Apply strictest gate
        if gates:
            gated_score = min(g[1] for g in gates)
            base_score = min(base_score, gated_score)
        
        # ============ STAGE 3: POSITIVE INDICATORS ============
        
        # Band 8-9 requires exceptional sophistication
        if base_score >= 8.0:
            if not (sophistication >= 7.0 and
                   enhanced['idiomatic_expressions']['count'] >= 2 and
                   error_rate < 1.0):
                base_score = min(base_score, 7.5)
        
        final_score = self._round(base_score)
        
        return {
            'score': final_score,
            'deductions': deductions,
            'gates': gates,
            'sophistication_score': sophistication,
            'metrics': {
                'diversity': diversity,
                'idioms': enhanced['idiomatic_expressions']['count'],
                'awl_coverage': enhanced['academic_word_list_coverage'],
                'phrasal_verbs': enhanced['phrasal_verbs']['count'],
                'error_rate': error_rate
            }
        }
    
    def _score_grammatical_range_accuracy(self, grammar: Dict, metadata: Dict) -> Dict:
        """
        Three-stage grammar scoring with complex structure focus
        """
        
        base_score = 9.0
        deductions = []
        gates = []
        
        word_count = metadata['content_word_count']
        
        # Calculate metrics
        mlu = grammar['complexity']['mean_utterance_length']
        complex_attempted = grammar['complexity']['complex_structures_attempted']
        complex_accurate = grammar['complexity']['complex_structures_accurate']
        total_errors = grammar['accuracy']['grammar_errors']
        blocking_ratio = grammar['accuracy']['meaning_blocking_error_ratio']
        
        complex_acc_rate = (complex_accurate / complex_attempted 
                           if complex_attempted > 0 else 0)
        error_rate = (total_errors / word_count) * 100 if word_count > 0 else 100
        
        # Count structure range (types attempted)
        structure_range = 1 if complex_attempted > 0 else 0
        if complex_attempted >= 2:
            structure_range = 2
        if complex_attempted >= 4:
            structure_range = 3
        
        # ============ STAGE 1: DEDUCTIONS ============
        
        # Utterance length
        if mlu < self.GRAMMAR_MLU_VERY_SIMPLE:
            deductions.append(('very_simple_sentences', 3.0))
        elif mlu < self.GRAMMAR_MLU_SIMPLE:
            deductions.append(('simple_sentences', 2.0))
        elif mlu < self.GRAMMAR_MLU_MODERATE:
            deductions.append(('moderate_complexity', 1.0))
        
        # Structure range
        if structure_range < 2:
            deductions.append(('very_limited_range', 2.5))
        elif structure_range < 3:
            deductions.append(('limited_range', 1.0))
        
        # Error rate
        if error_rate > self.GRAMMAR_ERROR_RATE_FREQUENT:
            deductions.append(('frequent_errors', 3.0))
        elif error_rate > self.GRAMMAR_ERROR_RATE_NOTICEABLE:
            deductions.append(('noticeable_errors', 2.0))
        elif error_rate > self.GRAMMAR_ERROR_RATE_SOME:
            deductions.append(('some_errors', 1.0))
        elif error_rate > self.GRAMMAR_ERROR_RATE_OCCASIONAL:
            deductions.append(('occasional_errors', 0.5))
        
        # Complex accuracy
        if complex_acc_rate < self.GRAMMAR_COMPLEX_ACC_VERY_POOR:
            deductions.append(('very_poor_complex_control', 3.5))
        elif complex_acc_rate < self.GRAMMAR_COMPLEX_ACC_POOR:
            deductions.append(('poor_complex_control', 2.5))
        elif complex_acc_rate < self.GRAMMAR_COMPLEX_ACC_WEAK:
            deductions.append(('weak_complex_control', 1.5))
        elif complex_acc_rate < self.GRAMMAR_COMPLEX_ACC_GOOD:
            deductions.append(('developing_complex_control', 0.5))
        
        # Blocking errors
        if blocking_ratio > self.GRAMMAR_BLOCKING_FREQUENT:
            deductions.append(('frequent_blocking_errors', 3.0))
        elif blocking_ratio > self.GRAMMAR_BLOCKING_SOME:
            deductions.append(('some_blocking_errors', 2.0))
        elif blocking_ratio > self.GRAMMAR_BLOCKING_OCCASIONAL:
            deductions.append(('occasional_blocking_errors', 1.0))
        
        # Apply deductions
        for reason, amount in deductions:
            base_score -= amount
        
        # ============ STAGE 2: HARD GATES ============
        
        # Gate 1: Zero accuracy on complex = max Band 4.5
        if complex_attempted > 0 and complex_acc_rate == 0:
            gates.append(('no_complex_control', 4.5))
        
        # Gate 2: No complex attempted = max Band 5.0
        if complex_attempted == 0:
            gates.append(('no_complex_attempted', 5.0))
        
        # Gate 3: Frequent blocking = max Band 5.5
        if blocking_ratio > 0.25:
            gates.append(('communication_breakdown', 5.5))
        
        # Gate 4: Very limited range = max Band 6.0
        if structure_range < 2:
            gates.append(('insufficient_range', 6.0))
        
        # Gate 5: Band 7+ requires 75%+ complex accuracy
        if complex_acc_rate < 0.75 and base_score >= 7.0:
            gates.append(('insufficient_complex_accuracy', 6.5))
        
        # Gate 6: Band 8+ requires 90%+ complex accuracy
        if complex_acc_rate < 0.90 and base_score >= 8.0:
            gates.append(('not_band_8_accuracy', 7.5))
        
        # Apply strictest gate
        if gates:
            gated_score = min(g[1] for g in gates)
            base_score = min(base_score, gated_score)
        
        # ============ STAGE 3: POSITIVE INDICATORS ============
        
        # Band 8-9 requires excellence
        if base_score >= 8.0:
            if not (complex_acc_rate >= 0.90 and 
                   error_rate < 2.0 and
                   structure_range >= 3):
                base_score = min(base_score, 7.5)
        
        final_score = self._round(base_score)
        
        return {
            'score': final_score,
            'deductions': deductions,
            'gates': gates,
            'metrics': {
                'mlu': mlu,
                'complex_accuracy': complex_acc_rate,
                'error_rate': error_rate,
                'blocking_ratio': blocking_ratio,
                'structure_range': structure_range
            }
        }
    
    def _score_pronunciation(self, pronunciation: Dict, enhanced: Dict, 
                            metadata: Dict) -> Dict:
        """
        Three-stage pronunciation scoring with prosody emphasis
        """
        
        base_score = 9.0
        deductions = []
        gates = []
        
        # Extract metrics
        word_conf = pronunciation['intelligibility']['mean_word_confidence']
        low_conf_ratio = pronunciation['intelligibility']['low_confidence_ratio']
        prosody_quality = enhanced['prosody_quality_score']
        monotone = pronunciation['prosody']['monotone_detected']
        
        # Calculate intelligibility (40% segmental, 60% prosody)
        segmental_score = word_conf * 0.7 + (1 - low_conf_ratio) * 0.3
        intelligibility = segmental_score * 0.4 + prosody_quality * 0.6
        
        # ============ STAGE 1: DEDUCTIONS ============
        
        # Intelligibility-based deductions
        if intelligibility < 0.5:
            deductions.append(('very_difficult_to_understand', 4.0))
        elif intelligibility < 0.65:
            deductions.append(('difficult_to_understand', 3.0))
        elif intelligibility < 0.75:
            deductions.append(('requires_effort', 2.0))
        elif intelligibility < 0.85:
            deductions.append(('noticeable_accent', 1.0))
        elif intelligibility < 0.92:
            deductions.append(('slight_accent', 0.5))
        
        # Prosody-specific deductions
        if monotone:
            deductions.append(('monotone_delivery', 1.5))
        
        if prosody_quality < 0.5:
            deductions.append(('unnatural_rhythm', 1.0))
        
        # Apply deductions
        for reason, amount in deductions:
            base_score -= amount
        
        # ============ STAGE 2: HARD GATES ============
        
        # Gate 1: Poor intelligibility = Band 4
        if intelligibility < self.PRONUN_INTELLIGIBILITY_POOR:
            gates.append(('poor_intelligibility', 4.0))
        
        # Gate 2: Monotone = max Band 6.0
        if monotone:
            gates.append(('no_prosodic_variation', 6.0))
        
        # Gate 3: Band 7+ requires good prosody
        if prosody_quality < 0.70 and base_score >= 7.0:
            gates.append(('insufficient_prosody', 6.5))
        
        # Gate 4: Band 8+ requires excellent prosody
        if prosody_quality < 0.85 and base_score >= 8.0:
            gates.append(('not_native_like', 7.5))
        
        # Gate 5: Band 9 requires near-perfect
        if (prosody_quality < 0.95 or word_conf < 0.95) and base_score >= 9.0:
            gates.append(('not_band_9_quality', 8.5))
        
        # Apply strictest gate
        if gates:
            gated_score = min(g[1] for g in gates)
            base_score = min(base_score, gated_score)
        
        # ============ STAGE 3: POSITIVE INDICATORS ============
        
        # Band 8-9 requires excellence
        if base_score >= 8.0:
            if not (intelligibility >= 0.92 and 
                   prosody_quality >= 0.85 and
                   not monotone):
                base_score = min(base_score, 7.5)
        
        final_score = self._round(base_score)
        
        return {
            'score': final_score,
            'deductions': deductions,
            'gates': gates,
            'metrics': {
                'word_confidence': word_conf,
                'low_conf_ratio': low_conf_ratio,
                'intelligibility': intelligibility,
                'prosody_quality': prosody_quality,
                'monotone': monotone
            }
        }
    
    # ========================================================================
    # OVERALL BAND CALCULATION
    # ========================================================================
    
    def _calculate_overall_band(self, criterion_bands: Dict[str, float], 
                                metadata: Dict) -> float:
        """
        Calculate overall band with weakness penalties and validation
        """
        
        scores = list(criterion_bands.values())
        avg = np.mean(scores)
        min_score = min(scores)
        max_score = max(scores)
        gap = max_score - min_score
        
        # ============ STAGE 1: WEAKNESS PENALTIES ============
        
        overall = avg
        
        # Large gap penalty
        if gap >= 2.0:
            overall = min_score * 0.4 + avg * 0.6
        elif gap >= 1.5:
            overall = min_score * 0.3 + avg * 0.7
        
        # Multiple weak areas compound
        weak_count = sum(1 for s in scores if s <= 5.0)
        if weak_count >= 2:
            overall = min(overall, 5.0)
        elif weak_count == 1:
            overall = min(overall, 6.0)
        
        # ============ STAGE 2: HARD CEILINGS ============
        
        ceilings = []
        
        # Fluency below 5.0 = max overall 6.0
        if criterion_bands['fluency_coherence'] < 5.0:
            ceilings.append(('fluency_barrier', 6.0))
        
        # Grammar below 5.0 = max overall 5.5
        if criterion_bands['grammatical_range_accuracy'] < 5.0:
            ceilings.append(('grammar_barrier', 5.5))
        
        # Any criterion <= 4.0 = max overall 5.0
        if min_score <= 4.0:
            ceilings.append(('severe_weakness', 5.0))
        
        # Lexical weak + others strong = cap at 7.0
        if criterion_bands['lexical_resource'] <= 6.0 and max_score >= 8.0:
            ceilings.append(('lexical_bottleneck', 7.0))
        
        # Apply strictest ceiling
        if ceilings:
            overall = min(overall, min(c[1] for c in ceilings))
        
        # ============ STAGE 3: STATISTICAL CALIBRATION ============
        
        overall = self._apply_statistical_calibration(overall, criterion_bands)
        
        # ============ STAGE 4: VALIDATION ============
        
        # Overall cannot exceed best criterion by more than 0.5
        if overall > max_score + 0.5:
            overall = max_score + 0.5
        
        # Overall should not be below worst criterion by more than 1.0
        if overall < min_score - 1.0:
            overall = min_score - 1.0
        
        return self._round(overall)
    
    def _apply_statistical_calibration(self, overall: float, 
                                       criterion_bands: Dict) -> float:
        """
        Ensure realistic score distribution matching real IELTS data
        """
        
        if len(self.score_history) < 100:
            return overall  # Need more data
        
        # Check Band 8+ percentage
        band_8_plus = sum(1 for s in self.score_history if s >= 8.0)
        band_8_plus_pct = (band_8_plus / len(self.score_history)) * 100
        
        if band_8_plus_pct > self.STAT_BAND_8_PLUS_MAX_PCT:
            # Too many high scores - apply stricter criteria
            if overall >= 8.0:
                # Verify all criteria at 7.5+
                if not all(s >= 7.5 for s in criterion_bands.values()):
                    overall = min(overall, 7.5)
        
        # Check Band 9 percentage
        band_9 = sum(1 for s in self.score_history if s >= 9.0)
        band_9_pct = (band_9 / len(self.score_history)) * 100
        
        if band_9_pct > self.STAT_BAND_9_MAX_PCT:
            # Band 9 should be extremely rare
            if overall >= 9.0:
                overall = min(overall, 8.5)
        
        return overall
    
    # ========================================================================
    # FEEDBACK GENERATION
    # ========================================================================
    
    def _generate_feedback(self, criterion_bands: Dict, overall_band: float,
                          diagnostics: Dict) -> Dict:
        """Generate detailed feedback for test-taker"""
        
        sorted_criteria = sorted(criterion_bands.items(), key=lambda x: x[1])
        weakest = sorted_criteria[0]
        strongest = sorted_criteria[-1]
        
        # Summary
        summary = f"Overall Band: {overall_band}\n"
        summary += f"Weakest: {weakest[0].replace('_', ' ').title()} ({weakest[1]})\n"
        summary += f"Strongest: {strongest[0].replace('_', ' ').title()} ({strongest[1]})"
        
        # Identify strengths
        strengths = []
        for criterion, score in criterion_bands.items():
            if score >= 7.0:
                strengths.append(f"{criterion.replace('_', ' ').title()}: {score}")
        
        # Identify areas for improvement with specific advice
        improvements = []
        
        # Fluency
        if criterion_bands['fluency_coherence'] < 7.0:
            fluency_diag = diagnostics['fluency']
            advice = []
            if fluency_diag['metrics']['wpm'] < 90:
                advice.append("Increase speaking speed through practice")
            if fluency_diag['metrics']['long_pauses'] > 1.0:
                advice.append("Reduce long pauses by preparing ideas in advance")
            if fluency_diag['metrics']['fillers'] > 2.0:
                advice.append("Replace fillers (um, uh) with brief pauses")
            if fluency_diag['metrics']['coherence_breaks'] > 0:
                advice.append("Use linking words to maintain coherence")
            
            if advice:
                improvements.append({
                    'criterion': 'Fluency & Coherence',
                    'current_band': criterion_bands['fluency_coherence'],
                    'suggestions': advice
                })
        
        # Lexical
        if criterion_bands['lexical_resource'] < 7.0:
            lexical_diag = diagnostics['lexical']
            advice = []
            if lexical_diag['sophistication_score'] < 5.0:
                advice.append("Learn and use more idiomatic expressions")
            if lexical_diag['metrics']['idioms'] == 0:
                advice.append("Incorporate common idioms naturally")
            if lexical_diag['metrics']['awl_coverage'] < 3:
                advice.append("Build academic vocabulary for abstract topics")
            if lexical_diag['metrics']['phrasal_verbs'] == 0:
                advice.append("Use phrasal verbs for natural expression")
            
            if advice:
                improvements.append({
                    'criterion': 'Lexical Resource',
                    'current_band': criterion_bands['lexical_resource'],
                    'suggestions': advice
                })
        
        # Grammar
        if criterion_bands['grammatical_range_accuracy'] < 7.0:
            grammar_diag = diagnostics['grammar']
            advice = []
            if grammar_diag['metrics']['complex_accuracy'] < 0.75:
                advice.append("Practice complex structures until automatic")
            if grammar_diag['metrics']['structure_range'] < 3:
                advice.append("Expand range: conditionals, relative clauses, passives")
            if grammar_diag['metrics']['error_rate'] > 3.0:
                advice.append("Focus on accuracy in common structures")
            
            if advice:
                improvements.append({
                    'criterion': 'Grammatical Range & Accuracy',
                    'current_band': criterion_bands['grammatical_range_accuracy'],
                    'suggestions': advice
                })
        
        # Pronunciation
        if criterion_bands['pronunciation'] < 7.0:
            pronun_diag = diagnostics['pronunciation']
            advice = []
            if pronun_diag['metrics']['monotone']:
                advice.append("Practice intonation patterns (rising/falling)")
            if pronun_diag['metrics']['prosody_quality'] < 0.7:
                advice.append("Work on sentence stress and rhythm")
            if pronun_diag['metrics']['intelligibility'] < 0.85:
                advice.append("Focus on problematic sounds with minimal pairs")
            
            if advice:
                improvements.append({
                    'criterion': 'Pronunciation',
                    'current_band': criterion_bands['pronunciation'],
                    'suggestions': advice
                })
        
        return {
            'summary': summary,
            'strengths': strengths,
            'improvements': improvements
        }
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    @staticmethod
    def _round(score: float) -> float:
        """Round to nearest 0.5"""
        return round(score * 2) / 2


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import json
    import sys
    
    print("=" * 70)
    print("IELTS Band Scorer v3.0 - Super Accurate Production System")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        # Load from file
        filename = sys.argv[1]
        try:
            with open(filename) as f:
                analysis_data = json.load(f)
            
            # Extract analysis portion if wrapped in results
            if 'analysis' in analysis_data:
                analysis_data = analysis_data['analysis']
            
            scorer = IELTSBandScorerV3()
            result = scorer.score(analysis_data)
            
            print("\n" + "=" * 70)
            print("SCORING RESULTS")
            print("=" * 70)
            
            if result.get('validation_failed'):
                print(f"\n❌ {result['feedback_summary']}")
            else:
                print(f"\n🎯 Overall Band Score: {result['overall_band']}")
                print("\n📊 Criterion Scores:")
                for criterion, score in result['criterion_bands'].items():
                    criterion_name = criterion.replace('_', ' ').title()
                    print(f"   • {criterion_name:.<40} {score}")
                
                print(f"\n📝 Feedback:")
                print(result['feedback_summary'])
                
                if result.get('strengths'):
                    print(f"\n✅ Strengths:")
                    for strength in result['strengths']:
                        print(f"   • {strength}")
                
                if result.get('areas_for_improvement'):
                    print(f"\n📈 Areas for Improvement:")
                    for area in result['areas_for_improvement']:
                        print(f"\n   {area['criterion']} (Current: Band {area['current_band']})")
                        for suggestion in area['suggestions']:
                            print(f"      - {suggestion}")
                
                # Detailed diagnostics
                if '--verbose' in sys.argv:
                    print("\n" + "=" * 70)
                    print("DETAILED DIAGNOSTICS")
                    print("=" * 70)
                    
                    for criterion, diag in result['detailed_diagnostics'].items():
                        print(f"\n{criterion.upper()}:")
                        print(f"  Score: {diag['score']}")
                        
                        if diag.get('deductions'):
                            print(f"  Deductions:")
                            for reason, amount in diag['deductions']:
                                print(f"    - {reason}: -{amount}")
                        
                        if diag.get('gates'):
                            print(f"  Gates Applied:")
                            for reason, cap in diag['gates']:
                                print(f"    - {reason}: capped at {cap}")
                        
                        if diag.get('metrics'):
                            print(f"  Key Metrics:")
                            for metric, value in diag['metrics'].items():
                                if isinstance(value, float):
                                    print(f"    - {metric}: {value:.3f}")
                                else:
                                    print(f"    - {metric}: {value}")
        
        except FileNotFoundError:
            print(f"\n❌ Error: File '{filename}' not found")
        except json.JSONDecodeError:
            print(f"\n❌ Error: Invalid JSON in '{filename}'")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    else:
        print("\nUsage: python ielts_scorer_v3.py <analysis_file.json> [--verbose]")
        print("\nExample:")
        print("  python ielts_scorer_v3.py L2A_003.json")
        print("  python ielts_scorer_v3.py L2A_003.json --verbose")
        print("\nThe analysis file should contain IELTS speaking analysis data with:")
        print("  - metadata (duration, word counts)")
        print("  - fluency_coherence metrics")
        print("  - lexical_resource metrics")
        print("  - grammatical_range_accuracy metrics")
        print("  - pronunciation metrics")
        print("  - raw_transcript (optional but recommended)")
```

## llm_processing.py

```python
# llm_processing.py

from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import List, Literal
from openai import OpenAI
import json

NonNegativeInt = Annotated[int, Field(ge=0)]
Ratio01 = Annotated[float, Field(ge=0.0, le=1.0)]

class Span(BaseModel):
    text: str
    label: Literal[
        "meaning_blocking_grammar_error",
        "grammar_error",
        "word_choice_error",
        "coherence_break",
        "complex_structure",
        "advanced_vocabulary",
    ]

class LLMSpeechAnnotations(BaseModel):
    topic_relevance: bool

    coherence_breaks: List[Span]

    word_choice_errors: List[Span]
    advanced_vocabulary: List[Span]

    complex_structures_attempted: List[Span]
    complex_structures_accurate: List[Span]

    grammar_errors: List[Span]
    meaning_blocking_grammar_errors: List[Span]

system_prompt = """
You are a deterministic annotation engine for spoken English evaluation.

Your task:
- Identify and MARK spans in the transcript.
- Do NOT compute totals, counts, or ratios.
- Do NOT explain reasoning.
- Do NOT infer intent beyond the transcript.
- If unsure, DO NOT annotate the span.

STRICT RULES:
- Annotate ONLY what is clearly present.
- If uncertain, omit the annotation.
- Use the LOWEST reasonable interpretation.
- Return ONLY valid JSON matching the schema.
- No markdown. No comments. No extra keys.

DEFINITIONS:
- coherence_breaks: Moments where the speaker abandons an idea or makes an illogical jump.
- topic_relevance: True if the response addresses the prompt.
- word_choice_errors: Incorrect or inappropriate word choice (not grammar).
- advanced_vocabulary: Correctly used higher-level words (Band 7+).
- complex_structures_attempted: Attempts at conditionals, relatives, passives, modals, subordination.
- complex_structures_accurate: Subset of attempted structures that are correct.
- grammar_errors: Any grammatical error.
- meaning_blocking_grammar_errors: Meaning-blocking grammar errors are ONLY those that: Make the sentence unintelligible OR Change the core meaning OR Prevent understanding without rereading. Number agreement errors alone are NOT meaning-blocking. Preposition redundancy alone is NOT meaning-blocking.


SPAN RULES:
- Each span must be ATOMIC.
- Do NOT merge multiple issues into one span.
- A span must be the shortest phrase that independently shows the issue.
- Never include conjunctions like "and then", "so", "because" unless required.
- If a span qualifies for multiple labels, assign ONLY the highest-precedence label.
- Do NOT duplicate spans across categories.

LABEL PRECEDENCE (highest → lowest):
1. Meaning Blocking Grammar Error
2. Grammar Error
3. Word Choice Error
4. Coherence Break
5. Complex Structure
6. Advanced Vocabulary

IMPORTANT:
- A span must include the exact text excerpt from the transcript.
- Do NOT include timestamps or character offsets.
- The text must appear verbatim in the transcript.
- If unsure whether something qualifies, do NOT annotate it.
"""

def extract_llm_annotations(raw_transcript: str, speech_context: str = "conversational") -> LLMSpeechAnnotations:
    
    context = {
        "raw_transcript": raw_transcript,
        "speech_context": speech_context,
    }

    prompt_text = json.dumps(
        context,
        ensure_ascii=False,
        indent=2
    )

    client = OpenAI()
    prompt_text = json.dumps(context, ensure_ascii=False)
    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_text},
        ],
        temperature=0.0,      # 🔒 critical
        top_p=1.0,            # 🔒 critical
        text_format=LLMSpeechAnnotations,
    )

    llm_result: LLMSpeechAnnotations = response.output_parsed

    return llm_result

def aggregate_llm_metrics(llm_result) -> dict:
    """
    Convert span-based LLM annotations into scalar metrics.
    """

    grammar_error_count = len(llm_result.grammar_errors)
    meaning_blocking_count = len(llm_result.meaning_blocking_grammar_errors)

    meaning_blocking_error_ratio = (
        meaning_blocking_count / grammar_error_count
        if grammar_error_count > 0
        else 0.0
    )

    return {
        "coherence_breaks": len(llm_result.coherence_breaks),
        "topic_relevance": llm_result.topic_relevance,

        "word_choice_errors": len(llm_result.word_choice_errors),
        "advanced_vocabulary_count": len(llm_result.advanced_vocabulary),

        "complex_structures_attempted": len(llm_result.complex_structures_attempted),
        "complex_structures_accurate": len(llm_result.complex_structures_accurate),

        "grammar_errors": grammar_error_count,
        "meaning_blocking_error_ratio": round(meaning_blocking_error_ratio, 3),
    }

def analyze_llm_metrics(
    raw_transcript: str,
    speech_context: str = "conversational"
) -> dict:
    """
    Analyze speech using LLM and return aggregated metrics.
    """
    llm_result = extract_llm_annotations(raw_transcript, speech_context)
    llm_metrics = aggregate_llm_metrics(llm_result)
    return llm_metrics
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
    if df_words.empty:
        return wpms
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
    if fillers.empty:
        return False
    for _, f in fillers.iterrows():
        if start < f["end"] + tol and end > f["start"] - tol:
            return True
    return False


def utterance_lengths(df_words_asr, pause_threshold=0.5):
    """Compute utterance lengths using clean ASR word timeline."""
    if df_words_asr.empty:
        return []
    lengths = []
    count = 0
    n = len(df_words_asr)
    for i in range(n):
        count += 1
        if i == n - 1:
            lengths.append(count)
        else:
            gap = df_words_asr.iloc[i + 1]["start"] - df_words_asr.iloc[i]["end"]
            if gap > pause_threshold:
                lengths.append(count)
                count = 0
    return lengths


def calculate_normalized_metrics(
    df_words_asr: pd.DataFrame,
    df_words_content: pd.DataFrame,
    df_segments: pd.DataFrame,
    df_fillers: pd.DataFrame,
    total_duration: float,
    df_tokens_enriched: pd.DataFrame = None  # Optional: for future use only
) -> dict:
    """
    Calculate normalized fluency metrics.
    
    Args:
        df_words_asr: Full ASR word timeline (includes transcribed fillers like 'um', 'uh').
                      Used for pause detection, utterance segmentation, and confidence metrics.
        df_words_content: Content words only (fillers removed).
                          Used for lexical and rate metrics.
        df_segments: Segment-level timestamps from ASR.
        df_fillers: Unified disfluency events (fillers + stutters from all sources).
        total_duration: Total audio duration in seconds.
        df_tokens_enriched: Optional enriched token stream (ASR + acoustic fillers).
                            Currently unused — reserved for future advanced metrics.
        
    Returns:
        Dictionary of normalized metrics
    """
    if total_duration <= 0:
        total_duration = 0.1  # avoid division by zero

    duration_min = max(total_duration / 60.0, 0.5)

    # === Lexical & Rate Metrics (use content words only) ===
    words_per_minute = (len(df_words_content) * 60) / total_duration

    if len(df_words_content) == 0:
        vocab_richness = 0.0
        repetition_ratio = 0.0
        words_clean_nostopwords = pd.Series([], dtype="object")
    else:
        words_clean = df_words_content["word"].str.lower()
        vocab_richness = words_clean.nunique() / len(words_clean)
        words_clean_nostopwords = words_clean[~words_clean.isin(STOPWORDS)]
        if len(words_clean_nostopwords) > 0:
            repetition_ratio = (
                words_clean_nostopwords.value_counts().iloc[0] / len(words_clean_nostopwords)
            )
        else:
            repetition_ratio = 0.0

    # === Disfluency Metrics (use df_fillers) ===
    filler_events = df_fillers[df_fillers["type"] == "filler"]
    stutter_events = df_fillers[df_fillers["type"] == "stutter"]

    fillers_per_min = (
        filler_events["duration"].apply(filler_weight).sum() / duration_min
        if not filler_events.empty else 0.0
    )

    stutters_per_min = len(stutter_events) / duration_min

    # === Pause & Prosody Metrics (use df_words_asr + df_fillers) ===
    pause_durations = []
    if not df_words_asr.empty:
        for i in range(1, len(df_words_asr)):
            gap_start = df_words_asr.iloc[i - 1]["end"]
            gap_end = df_words_asr.iloc[i]["start"]
            gap = gap_end - gap_start
            if gap > 0.3 and not overlaps_filler(gap_start, gap_end, df_fillers):
                pause_durations.append(gap)

    pause_durations = pd.Series(pause_durations, dtype="float")

    long_pauses = pause_durations[pause_durations > 1.0]
    very_long_pauses = pause_durations[pause_durations > 2.0]

    long_pauses_per_min = len(long_pauses) / duration_min
    very_long_pauses_per_min = len(very_long_pauses) / duration_min
    pause_time_ratio = pause_durations.sum() / total_duration if not pause_durations.empty else 0.0
    pause_variability = pause_durations.std() if len(pause_durations) > 5 else 0.0
    pause_frequency = len(pause_durations) / duration_min

    # === Utterance Metrics ===
    utt_lengths = utterance_lengths(df_words_asr)
    mean_utterance_length = np.mean(utt_lengths) if utt_lengths else 0.0

    # === Confidence Metrics (use df_words_asr) ===
    if "confidence" in df_words_asr.columns and not df_words_asr.empty:
        valid_confs = df_words_asr["confidence"].dropna()
        if len(valid_confs) > 0:
            mean_word_confidence = valid_confs.mean()
            low_confidence_ratio = (valid_confs < 0.7).sum() / len(valid_confs)
        else:
            mean_word_confidence = 0.0
            low_confidence_ratio = 0.0
    else:
        mean_word_confidence = 0.0
        low_confidence_ratio = 0.0

    # === Derived Metrics ===
    lexical_density = (
        len(words_clean_nostopwords) / len(df_words_asr)
        if len(df_words_asr) > 0 else 0.0
    )

    wpm_rolling = rolling_wpm(df_words_content)
    speech_rate_variability = (
        np.std(wpm_rolling) / np.mean(wpm_rolling) if len(wpm_rolling) > 3 else 0.0
    )

    # Note: pause_after_filler_rate is buggy (uses undefined gap_start) — disabled for now
    pause_after_filler_rate = 0.0

    speaking_time_sec = total_duration - pause_durations.sum()

    return {
        "wpm": round(words_per_minute, 2),
        "unique_word_count": int(round(vocab_richness * len(df_words_content))) if len(df_words_content) > 0 else 0,
        "fillers_per_min": round(fillers_per_min, 2),
        "stutters_per_min": round(stutters_per_min, 2),
        "long_pauses_per_min": round(long_pauses_per_min, 2),
        "very_long_pauses_per_min": round(very_long_pauses_per_min, 2),
        "pause_frequency": round(pause_frequency, 2),
        "pause_time_ratio": round(pause_time_ratio, 3),
        "pause_variability": round(pause_variability, 3) if not np.isnan(pause_variability) else 0.0,
        "vocab_richness": round(vocab_richness, 3),
        "repetition_ratio": round(repetition_ratio, 3),
        "speech_rate_variability": round(speech_rate_variability, 3),
        "mean_utterance_length": round(mean_utterance_length, 2),
        "pause_after_filler_rate": round(pause_after_filler_rate, 3),
        "mean_word_confidence": round(mean_word_confidence, 3),
        "low_confidence_ratio": round(low_confidence_ratio, 3),
        "lexical_density": round(lexical_density, 3),
        "audio_duration_sec": round(total_duration, 2),
        "speaking_time_sec": round(speaking_time_sec, 2),
    }
```

## prosody_extraction.py

```python
# prosody_extraction.py

import numpy as np
import librosa
from pathlib import Path
import sys

PROJECT_ROOT = Path.cwd().parent
sys.path.insert(0, str(PROJECT_ROOT))


def prosody_variation_robust(audio_path: str, hop_length: int = 256) -> float:
    """
    Robust prosody variation using:
      - YIN for speed
      - IQR-based outlier removal
      - Median absolute deviation (MAD) as variation metric
    """
    y, sr = librosa.load(audio_path, sr=None)
    
    # Estimate F0 with YIN (faster than PYIN)
    f0 = librosa.yin(
        y,
        fmin=librosa.note_to_hz('C2'),   # 65 Hz
        fmax=librosa.note_to_hz('C6'),   # 1046 Hz (reduce max to avoid harmonics)
        sr=sr,
        hop_length=hop_length
    )
    
    # Remove unvoiced frames (YIN returns 0 for unvoiced)
    voiced_f0 = f0[f0 > 0]
    
    if len(voiced_f0) < 10:  # Need min frames
        return 0.0

    # Remove outliers using IQR (keeps only plausible F0)
    q25, q75 = np.percentile(voiced_f0, [25, 75])
    iqr = q75 - q25
    lower_bound = q25 - 1.5 * iqr
    upper_bound = q75 + 1.5 * iqr
    filtered_f0 = voiced_f0[(voiced_f0 >= lower_bound) & (voiced_f0 <= upper_bound)]
    
    if len(filtered_f0) == 0:
        return 0.0
        
    # Use MAD (robust to outliers) instead of std
    # Convert to Hz-scale MAD: MAD ≈ 0.6745 * σ for normal dist, but we care about relative variation
    mad = np.median(np.abs(filtered_f0 - np.median(filtered_f0)))
    return float(mad)


def monotone_detected(prosody_var: float, threshold: float = 20.0) -> bool:
    """Detect monotone speech based on F0 std (in Hz)."""
    return prosody_var < threshold


# Example usage
def is_monotone_speech(audio_file: str) -> None:
    prosody_var = prosody_variation_robust(audio_file, hop_length=512)  # try 1024 for even faster
    monotone = monotone_detected(prosody_var)

    print(f"Prosody Variation (F0 std): {prosody_var:.2f} Hz")
    print(f"Monotone Detected: {monotone}")

    return monotone
```

