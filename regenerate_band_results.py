"""
Regenerate band_results from audio_analysis JSON files.
Tests the fixed lexical scoring against known band samples.
"""
import json
import sys
from pathlib import Path
from typing import Dict

# Setup project path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.analyze_band import build_analysis
from src.core.ielts_band_scorer import score_ielts_speaking
from src.core.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.utils.logging_config import setup_logging

logger = setup_logging(level="INFO")

def regenerate_band_results():
    """Regenerate band_results from audio_analysis files."""
    
    audio_analysis_dir = Path(PROJECT_ROOT) / "outputs" / "audio_analysis"
    band_results_dir = Path(PROJECT_ROOT) / "outputs" / "band_results_fixed"
    
    # Create output directory
    band_results_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all audio_analysis files
    audio_files = sorted(audio_analysis_dir.glob("*.json"))
    
    print(f"\n{'='*70}")
    print(f"REGENERATING BAND RESULTS WITH FIXED LEXICAL SCORING")
    print(f"{'='*70}\n")
    
    results_summary = []
    
    for audio_file in audio_files:
        print(f"Processing: {audio_file.name}")
        
        try:
            # Load audio analysis
            with open(audio_file, 'r') as f:
                audio_data = json.load(f)
            
            # Extract raw_analysis
            raw_analysis = audio_data.get("raw_analysis", {})
            
            # Build analysis with metrics
            analysis = build_analysis(raw_analysis)
            
            # Get metrics for scoring
            metrics_for_scoring = analysis["metrics_for_scoring"]
            transcript = raw_analysis.get("raw_transcript", "")
            
            # Score IELTS bands
            band_scores = score_ielts_speaking(
                metrics=metrics_for_scoring,
                transcript=transcript,
                use_llm=True
            )
            
            # Build final band result
            band_result = {
                "band_scores": {
                    "overall_band": band_scores["overall_band"],
                    "criterion_bands": band_scores["criterion_bands"],
                    "descriptors": band_scores["descriptors"],
                    "feedback": band_scores["feedback"],
                },
                "analysis": {
                    "metadata": analysis["metadata"],
                    "fluency_analysis": raw_analysis.get("fluency_analysis", {}),
                    "pronunciation": analysis["pronunciation"],
                },
                "metrics": metrics_for_scoring,
            }
            
            # Save to file
            output_file = band_results_dir / audio_file.name
            with open(output_file, 'w') as f:
                json.dump(band_result, f, indent=2)
            
            # Record results
            file_prefix = audio_file.stem  # e.g., "ielts9"
            overall_band = band_scores["overall_band"]
            lexical_band = band_scores["criterion_bands"]["lexical_resource"]
            
            results_summary.append({
                "file": file_prefix,
                "overall_band": overall_band,
                "lexical_band": lexical_band,
                "fluency": band_scores["criterion_bands"]["fluency_coherence"],
                "pronunciation": band_scores["criterion_bands"]["pronunciation"],
                "grammar": band_scores["criterion_bands"]["grammatical_range_accuracy"],
                "vocab_richness": metrics_for_scoring.get("vocab_richness"),
                "lexical_density": metrics_for_scoring.get("lexical_density"),
            })
            
            print(f"  ✓ Overall: {overall_band} | Lexical: {lexical_band}")
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Print summary
    print(f"\n{'='*70}")
    print("BAND RESULTS SUMMARY")
    print(f"{'='*70}\n")
    print(f"{'File':<20} {'Overall':<10} {'Lexical':<10} {'Fluency':<10} {'Pronunciation':<15} {'Grammar':<10} {'VocabRich':<12} {'LexDense':<10}")
    print("-" * 110)
    
    for result in results_summary:
        print(
            f"{result['file']:<20} "
            f"{result['overall_band']:<10.1f} "
            f"{result['lexical_band']:<10.1f} "
            f"{result['fluency']:<10.1f} "
            f"{result['pronunciation']:<15.1f} "
            f"{result['grammar']:<10.1f} "
            f"{result['vocab_richness']:<12.3f} "
            f"{result['lexical_density']:<10.3f}"
        )
    
    print(f"\n{'='*70}")
    print(f"Files saved to: {band_results_dir}")
    print(f"{'='*70}\n")
    
    # Validation: Check if band names match generated scores
    print("VALIDATION: Checking if file names align with generated bands...\n")
    
    for result in results_summary:
        file_prefix = result["file"].lower()
        overall = result["overall_band"]
        lexical = result["lexical_band"]
        
        # Parse file prefix to expected band range
        if file_prefix == "ielts9":
            expected = (8.5, 9.0)
        elif file_prefix == "ielts8-8.5":
            expected = (8.0, 8.5)
        elif file_prefix == "ielts8.5":
            expected = (8.0, 9.0)
        elif file_prefix == "ielts8":
            expected = (7.5, 8.5)
        elif file_prefix == "ielts7-7.5":
            expected = (7.0, 7.5)
        elif file_prefix == "ielts7":
            expected = (6.5, 7.5)
        elif file_prefix == "ielts5.5":
            expected = (5.0, 6.5)
        elif file_prefix == "ielts5-5.5":
            expected = (5.0, 6.0)
        else:
            expected = (5.0, 9.0)
        
        # Check alignment
        in_range = expected[0] <= overall <= expected[1]
        status = "✓ PASS" if in_range else "✗ FAIL"
        
        print(f"{file_prefix:<15} | Expected: {expected[0]}-{expected[1]} | Got: {overall:<5.1f} | {status}")
    
    print()

if __name__ == "__main__":
    regenerate_band_results()
