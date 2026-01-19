"""Regenerate band_results with confidence scores."""
import json
import os
from pathlib import Path
from src.core.ielts_band_scorer import IELTSBandScorer

def regenerate_band_results():
    """Regenerate all band_results files with confidence scores."""
    
    scorer = IELTSBandScorer()
    audio_dir = Path("outputs/audio_analysis")
    band_results_dir = Path("outputs/band_results")
    
    # Process each audio analysis file
    for audio_file in sorted(audio_dir.glob("*.json")):
        if audio_file.name.startswith("test_"):
            continue  # Skip test files for now
        
        print(f"Processing: {audio_file.name}")
        
        with open(audio_file) as f:
            audio_data = json.load(f)
        
        raw_analysis = audio_data.get("raw_analysis", {})
        
        # Build metrics dictionary
        metrics = {
            "wpm": raw_analysis.get("wpm", 0),
            "unique_word_count": raw_analysis.get("unique_word_count", 0),
            "fillers_per_min": raw_analysis.get("fillers_per_min", 0),
            "stutters_per_min": raw_analysis.get("stutters_per_min", 0),
            "long_pauses_per_min": raw_analysis.get("long_pauses_per_min", 0),
            "very_long_pauses_per_min": raw_analysis.get("very_long_pauses_per_min", 0),
            "pause_frequency": raw_analysis.get("pause_frequency", 0),
            "pause_time_ratio": raw_analysis.get("pause_time_ratio", 0),
            "pause_variability": raw_analysis.get("pause_variability", 0),
            "vocab_richness": raw_analysis.get("vocab_richness", 0),
            "repetition_ratio": raw_analysis.get("repetition_ratio", 0),
            "speech_rate_variability": raw_analysis.get("speech_rate_variability", 0),
            "mean_utterance_length": raw_analysis.get("mean_utterance_length", 0),
            "pause_after_filler_rate": raw_analysis.get("pause_after_filler_rate", 0),
            "mean_word_confidence": raw_analysis.get("mean_word_confidence", 0.9),
            "low_confidence_ratio": raw_analysis.get("low_confidence_ratio", 0),
            "lexical_density": raw_analysis.get("lexical_density", 0),
            "audio_duration_sec": raw_analysis.get("audio_duration_sec", 0),
        }
        
        # Get transcript
        transcript = raw_analysis.get("raw_transcript", "")
        
        # Score with confidence
        result = scorer.score_overall_with_feedback(metrics, transcript, None)
        
        # Create output structure
        output = {
            "filename": audio_file.name,
            "overall_band": result["overall_band"],
            "confidence": result["confidence"],
            "band_scores": result["criterion_bands"],
            "descriptors": result["descriptors"],
            "feedback": result["feedback"],
        }
        
        # Save to band_results
        output_file = band_results_dir / audio_file.name
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"  ✓ Overall: {result['overall_band']}, Confidence: {result['confidence']['overall_confidence']}")
    
    print("\n✓ All band_results files regenerated with confidence scores!")

if __name__ == "__main__":
    regenerate_band_results()
