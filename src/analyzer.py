# src/analyzer.py
"""Main fluency analysis orchestrator."""
import pandas as pd
from dotenv import load_dotenv

from .audio_processing import (
    load_audio,
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
from .metrics import analyze_fluency


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
    
    Args:
        audio_path: Path to audio file
        speech_context: Type of speech ('conversational', 'narrative', 'presentation', 'interview')
        device: Device to run models on ('cpu' or 'cuda')
        
    Returns:
        Dictionary containing:
        - verdict: fluency_score and readiness
        - benchmarking: percentile, target_score, score_gap, practice_hours
        - normalized_metrics: all computed metrics
        - opinions: primary_issues and action_plan
        - word_timestamps: word-level timing data
        - segment_timestamps: segment-level timing data
        - filler_events: detected fillers and stutters
        - aligned_words: WhisperX aligned words
    """
    print(f"Analyzing audio: {audio_path}")
    print(f"Context: {speech_context}")
    
    # Step 1: Load and transcribe audio
    print("\n[1/6] Transcribing with Whisper...")
    result = transcribe_with_whisper(audio_path, device=device)
    df_words = extract_words_dataframe(result)
    df_segments = extract_segments_dataframe(result)
    
    total_duration = float(df_segments.iloc[-1]["end"])
    print(f"  Duration: {total_duration:.2f}s")
    print(f"  Words: {len(df_words)}")
    
    # Step 2: Align words with WhisperX
    print("\n[2/6] Aligning words with WhisperX...")
    audio, _ = load_audio(audio_path)
    df_aligned_words = align_words_whisperx(result["segments"], audio, device=device)
    print(f"  Aligned: {len(df_aligned_words)} words")
    
    # Step 3: Detect fillers with Wav2Vec2
    print("\n[3/6] Detecting fillers with Wav2Vec2...")
    df_wav2vec_fillers = detect_fillers_wav2vec(audio_path, df_aligned_words)
    print(f"  Detected: {len(df_wav2vec_fillers)} events")
    
    # Step 4: Detect fillers with Whisper verbatim
    print("\n[4/6] Detecting fillers with Whisper (verbatim)...")
    verbatim_result = transcribe_verbatim_fillers(audio_path, device=device)
    df_whisper_fillers = detect_fillers_whisper(verbatim_result)
    print(f"  Detected: {len(df_whisper_fillers)} fillers")
    
    # Step 5: Merge and group detections
    print("\n[5/6] Merging detections...")
    df_merged_fillers = merge_filler_detections(df_whisper_fillers, df_wav2vec_fillers)
    df_final_fillers = group_stutters(df_merged_fillers)
    print(f"  Total events: {len(df_final_fillers)}")
    
    # Step 6: Calculate fluency metrics and score
    print("\n[6/6] Calculating fluency score...")
    analysis = analyze_fluency(
        df_words,
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
    
    # Build complete response
    final_response = {
        **analysis,
        "word_timestamps": df_words.to_dict(orient="records"),
        "segment_timestamps": df_segments.to_dict(orient="records"),
        "filler_events": df_final_fillers.to_dict(orient="records"),
        "aligned_words": df_aligned_words.to_dict(orient="records"),
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