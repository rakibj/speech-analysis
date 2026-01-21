# src/analyzer_raw.py
"""Main fluency analysis orchestrator."""
import asyncio
import pandas as pd
from dotenv import load_dotenv

from .fluency_metrics import analyze_fluency
from .metrics import calculate_normalized_metrics

from src.audio.processing import (
    CORE_FILLERS,
    load_audio,
    transcribe_with_whisper,
    transcribe_verbatim_fillers,
    align_words_whisperx,
    extract_words_dataframe,
    extract_segments_dataframe,
)
from src.audio.filler_detection import (
    get_content_words,
    mark_filler_segments,
    mark_filler_words,
    detect_fillers_wav2vec,
    detect_phonemes_wav2vec,
    detect_fillers_whisper,
    merge_filler_detections,
    group_stutters,
)
from src.core.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.core.prosody_extraction import is_monotone_speech

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
    return " ".join(df_words_raw["word"].astype(str))

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
    
    # Merge WhisperX confidence back into Whisper words
    # Match by word position/timing and update confidence from aligned data
    if not df_aligned_words.empty and 'confidence' in df_aligned_words.columns:
        # Merge on approximate timing (within 10ms tolerance)
        for idx, row in df_words_whisper_raw.iterrows():
            # Find matching aligned word (by timing proximity)
            matching = df_aligned_words[
                (df_aligned_words['start'] >= row['start'] - 0.01) &
                (df_aligned_words['start'] <= row['start'] + 0.01)
            ]
            if not matching.empty:
                # Use the first match (should be unique)
                df_words_whisper_raw.at[idx, 'confidence'] = matching.iloc[0]['confidence']
        print(f"  Updated confidence for {(df_words_whisper_raw['confidence'] > 0.5).sum()} words from WhisperX")
    
    # Step 4: Detect fillers with Wav2Vec2
    print("\n[4/5] Detecting subtle fillers with Wav2Vec2...")
    df_wav2vec_fillers = detect_fillers_wav2vec(audio_path, df_aligned_words)
    
    # Extract Whisper-detected fillers (already marked in df_words)
    df_whisper_fillers = df_words_whisper_raw[df_words_whisper_raw['is_filler']].copy()
    df_whisper_fillers['type'] = 'filler'
    df_whisper_fillers['text'] = df_whisper_fillers['word'].str.lower()
    df_whisper_fillers['style'] = 'clear'  # Add style column
    # Keep word column for output, select all relevant columns
    df_whisper_fillers = df_whisper_fillers[['word', 'type', 'text', 'start', 'end', 'duration', 'style', 'confidence']]
    
    # Merge detections
    df_merged_fillers = merge_filler_detections(df_whisper_fillers, df_wav2vec_fillers)
    df_final_fillers = group_stutters(df_merged_fillers)
    print(f"  Total events: {len(df_final_fillers)}")

    df_words_raw = combine_words_and_fillers(df_words_whisper_raw, df_final_fillers)
    transcript_raw = generate_transcript_raw(df_words_whisper_raw)
    # transcript_raw = generate_transcript_raw(df_words_raw)
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

    fluency_analysis = analyze_fluency(
        df_words_whisper_raw,          # Full timeline (with is_filler column)
        df_words_content,  # Content words only (for WPM)
        df_segments,
        df_final_fillers,
        total_duration,
        speech_context
    )
    
    # Build response with multiple word views
    response = {
        "raw_transcript": transcript_raw,
        "fluency_analysis": fluency_analysis,
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