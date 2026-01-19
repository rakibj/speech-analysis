#!/usr/bin/env python3
"""
Determinism Analysis - Test if scoring is consistent across multiple runs.

Runs band scoring multiple times on the same audio_analysis data
and checks for variance in results.
"""

import json
from pathlib import Path
from src.core.ielts_band_scorer import IELTSBandScorer

# Mock LLM metrics that would normally come from the LLM
# Using the same mock metrics for each run to isolate non-LLM variance
MOCK_LLM_METRICS = {
    "topic_relevance": True,
    "listener_effort_high": False,
    "flow_instability_present": False,
    "overall_clarity_score": 4,
    "register_mismatch_count": 0,
    "advanced_vocabulary_count": 5,
    "idiomatic_collocation_count": 2,
    "word_choice_error_count": 0,
    "grammar_error_count": 2,
    "coherence_break_count": 0,
}


def analyze_file_multiple_times(file_path: str, runs: int = 10) -> dict:
    """
    Analyze the same audio_analysis file multiple times and collect results.
    
    Args:
        file_path: Path to audio_analysis JSON file
        runs: Number of times to run scoring
        
    Returns:
        dict with results and statistics
    """
    with open(file_path) as f:
        data = json.load(f)
    
    transcript = data.get("raw_analysis", {}).get("raw_transcript", "")
    metrics = data.get("raw_analysis", {})
    
    if not transcript or not metrics:
        return {"error": "Invalid data format"}
    
    # Run scoring multiple times
    results = []
    scorer = IELTSBandScorer()
    
    print(f"\nAnalyzing: {Path(file_path).name}")
    print(f"Transcript length: {len(transcript)} chars")
    print(f"Running {runs} times...\n")
    
    for run in range(runs):
        try:
            result = scorer.score_overall_with_feedback(
                metrics,
                transcript,
                MOCK_LLM_METRICS
            )
            results.append(result)
            print(f"  Run {run+1}: Overall {result['overall_band']}, "
                  f"Lex {result['criterion_bands']['lexical_resource']}, "
                  f"Pron {result['criterion_bands']['pronunciation']}")
        except Exception as e:
            print(f"  Run {run+1}: ERROR - {e}")
            return {"error": str(e)}
    
    # Analyze variance
    overall_scores = [r["overall_band"] for r in results]
    lex_scores = [r["criterion_bands"]["lexical_resource"] for r in results]
    pron_scores = [r["criterion_bands"]["pronunciation"] for r in results]
    fluency_scores = [r["criterion_bands"]["fluency_coherence"] for r in results]
    grammar_scores = [r["criterion_bands"]["grammatical_range_accuracy"] for r in results]
    
    # Check consistency
    overall_unique = len(set(overall_scores))
    lex_unique = len(set(lex_scores))
    pron_unique = len(set(pron_scores))
    fluency_unique = len(set(fluency_scores))
    grammar_unique = len(set(grammar_scores))
    
    analysis = {
        "file": Path(file_path).name,
        "runs": runs,
        "deterministic": overall_unique == 1,  # True if all runs identical
        "scores": {
            "overall": {
                "values": overall_scores,
                "unique_count": overall_unique,
                "min": min(overall_scores),
                "max": max(overall_scores),
                "range": max(overall_scores) - min(overall_scores),
            },
            "lexical": {
                "values": lex_scores,
                "unique_count": lex_unique,
                "min": min(lex_scores),
                "max": max(lex_scores),
                "range": max(lex_scores) - min(lex_scores),
            },
            "pronunciation": {
                "values": pron_scores,
                "unique_count": pron_unique,
                "min": min(pron_scores),
                "max": max(pron_scores),
                "range": max(pron_scores) - min(pron_scores),
            },
            "fluency": {
                "values": fluency_scores,
                "unique_count": fluency_unique,
                "min": min(fluency_scores),
                "max": max(fluency_scores),
                "range": max(fluency_scores) - min(fluency_scores),
            },
            "grammar": {
                "values": grammar_scores,
                "unique_count": grammar_unique,
                "min": min(grammar_scores),
                "max": max(grammar_scores),
                "range": max(grammar_scores) - min(grammar_scores),
            },
        }
    }
    
    return analysis


def main():
    """Run determinism analysis on all audio_analysis files."""
    print("=" * 70)
    print("DETERMINISM ANALYSIS - BAND SCORING CONSISTENCY")
    print("=" * 70)
    print("\nTesting if the same input always produces the same output")
    print("Using mock LLM metrics (fixed) to isolate non-LLM variance\n")
    
    audio_analysis_dir = Path("outputs/audio_analysis")
    
    # Get all JSON files
    json_files = sorted(audio_analysis_dir.glob("*.json"))
    
    # Filter to only the main band files (not test files)
    main_files = [
        f for f in json_files
        if f.name.startswith("ielts") and not f.name.startswith("test_")
    ]
    
    all_results = []
    
    for json_file in main_files:
        analysis = analyze_file_multiple_times(str(json_file), runs=10)
        all_results.append(analysis)
    
    # Summary
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    deterministic_count = sum(1 for r in all_results if r.get("deterministic"))
    total_count = len(all_results)
    
    print(f"\nDeterministic files: {deterministic_count}/{total_count}")
    
    print("\n[OVERALL BAND]")
    for result in all_results:
        det_status = "[DETERMINISTIC]" if result.get("deterministic") else "[VARIES]"
        overall = result["scores"]["overall"]
        print(f"  {det_status} {result['file']:30s} "
              f"Range: {overall['min']:.1f}-{overall['max']:.1f} "
              f"({overall['range']:.1f}) "
              f"Unique values: {overall['unique_count']}")
    
    print("\n[LEXICAL RESOURCE]")
    for result in all_results:
        lex = result["scores"]["lexical"]
        print(f"  {result['file']:30s} "
              f"Range: {lex['min']:.1f}-{lex['max']:.1f} "
              f"({lex['range']:.1f}) "
              f"Unique values: {lex['unique_count']}")
    
    print("\n[PRONUNCIATION]")
    for result in all_results:
        pron = result["scores"]["pronunciation"]
        print(f"  {result['file']:30s} "
              f"Range: {pron['min']:.1f}-{pron['max']:.1f} "
              f"({pron['range']:.1f}) "
              f"Unique values: {pron['unique_count']}")
    
    print("\n[FLUENCY/COHERENCE]")
    for result in all_results:
        flu = result["scores"]["fluency"]
        print(f"  {result['file']:30s} "
              f"Range: {flu['min']:.1f}-{flu['max']:.1f} "
              f"({flu['range']:.1f}) "
              f"Unique values: {flu['unique_count']}")
    
    print("\n[GRAMMAR/ACCURACY]")
    for result in all_results:
        gram = result["scores"]["grammar"]
        print(f"  {result['file']:30s} "
              f"Range: {gram['min']:.1f}-{gram['max']:.1f} "
              f"({gram['range']:.1f}) "
              f"Unique values: {gram['unique_count']}")
    
    # Analysis
    print("\n\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Check if fully deterministic
    if deterministic_count == total_count:
        print("\n[FULLY DETERMINISTIC]")
        print("✓ All scoring is perfectly deterministic")
        print("✓ Same input always produces identical output")
        print("✓ No randomness in metrics calculation or scoring logic")
        print("\nConclusion: Scoring system is 100% reproducible")
    else:
        print(f"\n[PARTIALLY DETERMINISTIC]")
        print(f"✗ {deterministic_count}/{total_count} files are fully deterministic")
        print(f"✗ {total_count - deterministic_count} files show variance")
        
        # Identify sources
        print("\nVariance detected in:")
        for result in all_results:
            if not result.get("deterministic"):
                print(f"  - {result['file']}")
                for criterion, scores in result["scores"].items():
                    if scores["range"] > 0:
                        print(f"    * {criterion}: varies by {scores['range']:.1f} "
                              f"({scores['unique_count']} unique values)")
    
    # Determinism sources
    print("\n\nPotential Sources of Non-Determinism:")
    print("  1. Floating-point rounding (0.0-0.5 band increments)")
    print("  2. Metrics calculation variance (if speech processing uses randomness)")
    print("  3. LLM output variance (if real LLM used instead of mock)")
    print("  4. Threshold boundary effects (scores near thresholds)")
    print("\nCurrent Test: Using fixed mock LLM metrics")
    print("  - Isolated to metrics calculation and scoring logic only")
    print("  - LLM variance excluded from this test")
    
    return 0 if deterministic_count == total_count else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
