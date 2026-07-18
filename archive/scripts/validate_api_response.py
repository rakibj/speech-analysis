#!/usr/bin/env python3
"""
Comprehensive validation of API response structure and data accuracy.
Checks that all fields are present, correct type, and data is consistent.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

def validate_response(response: Dict[str, Any]) -> List[Tuple[str, bool, str]]:
    """
    Validate API response structure and data.
    Returns list of (check_name, passed, message) tuples.
    """
    results = []
    
    # =====================================================================
    # METADATA VALIDATION
    # =====================================================================
    
    # Check required metadata fields
    required_meta = ["job_id", "status", "engine_version"]
    for field in required_meta:
        exists = field in response
        results.append((f"Metadata: {field} exists", exists, f"{field}: {response.get(field)}"))
    
    # =====================================================================
    # BAND SCORES VALIDATION
    # =====================================================================
    
    overall = response.get("overall_band")
    criterion_bands = response.get("criterion_bands", {})
    
    # Check band scores are in valid range [5.0, 9.0]
    if overall:
        in_range = 5.0 <= overall <= 9.0
        results.append((f"Band Score: overall_band in [5.0, 9.0]", in_range, f"Value: {overall}"))
    
    # Check criterion bands exist and are valid
    required_criteria = ["fluency_coherence", "pronunciation", "lexical_resource", "grammatical_range_accuracy"]
    for criterion in required_criteria:
        exists = criterion in criterion_bands
        value = criterion_bands.get(criterion)
        if value:
            in_range = 5.0 <= value <= 9.0
            results.append((f"Band Score: {criterion} exists and in range", exists and in_range, f"Value: {value}"))
        else:
            results.append((f"Band Score: {criterion} exists and in range", False, "Missing or invalid"))
    
    # Check overall band = average of criteria (with rounding to 0.5)
    if criterion_bands and all(criterion_bands.get(c) for c in required_criteria):
        avg = sum(criterion_bands.get(c, 0) for c in required_criteria) / 4
        # Round to nearest 0.5
        rounded_avg = round(avg * 2) / 2
        matches = overall == rounded_avg
        results.append((f"Band Score: overall = avg(criteria)", matches, f"Overall: {overall}, Avg: {avg}, Rounded: {rounded_avg}"))
    
    # =====================================================================
    # DESCRIPTORS VALIDATION
    # =====================================================================
    
    descriptors = response.get("descriptors")
    criterion_descriptors = response.get("criterion_descriptors")
    
    # Check descriptors exist
    results.append((f"Descriptors: overall exists", descriptors is not None, f"Type: {type(descriptors)}"))
    results.append((f"Descriptors: criterion_descriptors exists", criterion_descriptors is not None, f"Type: {type(criterion_descriptors)}"))
    
    # Check criterion descriptors for all criteria
    if criterion_descriptors:
        for criterion in required_criteria:
            has_desc = criterion in criterion_descriptors
            desc = criterion_descriptors.get(criterion, "")
            is_str = isinstance(desc, str)
            not_empty = len(str(desc).strip()) > 0
            results.append((f"Descriptors: {criterion} is non-empty string", has_desc and is_str and not_empty, f"Value: {desc[:50]}..."))
    
    # =====================================================================
    # CONFIDENCE VALIDATION
    # =====================================================================
    
    confidence = response.get("confidence", {})
    
    if confidence:
        overall_conf = confidence.get("overall_confidence")
        if overall_conf is not None:
            in_range = 0.0 <= overall_conf <= 1.0
            results.append((f"Confidence: overall_confidence in [0.0, 1.0]", in_range, f"Value: {overall_conf}"))
        
        factor_breakdown = confidence.get("factor_breakdown", {})
        expected_factors = ["duration", "audio_clarity", "llm_consistency", "boundary_proximity", "gaming_detection", "criterion_coherence"]
        for factor in expected_factors:
            exists = factor in factor_breakdown
            results.append((f"Confidence: {factor} breakdown exists", exists, f"Present: {exists}"))
    
    # =====================================================================
    # STATISTICS VALIDATION
    # =====================================================================
    
    statistics = response.get("statistics", {})
    
    if statistics:
        # Check required statistics fields
        stat_fields = {
            "total_words_transcribed": (int, "≥0"),
            "content_words": (int, "≥0"),
            "filler_words_detected": (int, "≥0"),
            "filler_percentage": (float, "[0,100]"),
            "is_monotone": (bool, "true/false"),
        }
        
        for field, (expected_type, constraint) in stat_fields.items():
            exists = field in statistics
            if exists:
                value = statistics[field]
                correct_type = isinstance(value, expected_type)
                results.append((f"Statistics: {field} ({expected_type.__name__})", correct_type, f"Value: {value}"))
            else:
                results.append((f"Statistics: {field} exists", False, f"Missing"))
        
        # Validate filler_percentage calculation
        total = statistics.get("total_words_transcribed", 0)
        fillers = statistics.get("filler_words_detected", 0)
        filler_pct = statistics.get("filler_percentage", 0)
        if total > 0:
            expected_pct = round(100 * fillers / total, 2)
            matches = abs(filler_pct - expected_pct) < 0.01
            results.append((f"Statistics: filler_percentage calculation", matches, f"Expected: {expected_pct}, Got: {filler_pct}"))
    
    # =====================================================================
    # NORMALIZED METRICS VALIDATION
    # =====================================================================
    
    norm_metrics = response.get("normalized_metrics", {})
    
    if norm_metrics:
        metric_fields = {
            "wpm": (float, ">0"),
            "long_pauses_per_min": (float, "≥0"),
            "fillers_per_min": (float, "≥0"),
            "pause_variability": (float, "≥0"),
            "speech_rate_variability": (float, "≥0"),
            "vocab_richness": (float, "[0,1]"),
            "type_token_ratio": (float, "[0,1]"),
            "repetition_ratio": (float, "[0,1]"),
            "mean_utterance_length": (float, ">0"),
        }
        
        for field, (expected_type, constraint) in metric_fields.items():
            exists = field in norm_metrics
            if exists:
                value = norm_metrics[field]
                correct_type = isinstance(value, expected_type)
                results.append((f"Normalized Metrics: {field} ({expected_type.__name__})", correct_type, f"Value: {value}"))
            else:
                results.append((f"Normalized Metrics: {field} exists", False, "Missing"))
        
        # Check for removed invalid fields
        invalid_fields = ["articulationrate"]
        for field in invalid_fields:
            not_present = field not in norm_metrics
            results.append((f"Normalized Metrics: {field} NOT present", not_present, f"Present: {field in norm_metrics}"))
    
    # =====================================================================
    # TRANSCRIPT & FEEDBACK VALIDATION
    # =====================================================================
    
    transcript = response.get("transcript")
    grammar_errors = response.get("grammar_errors")
    word_choice_errors = response.get("word_choice_errors")
    fluency_notes = response.get("fluency_notes")
    
    results.append((f"Transcript: exists and non-empty", transcript and len(str(transcript)) > 0, f"Length: {len(str(transcript)) if transcript else 0}"))
    results.append((f"Grammar Errors: exists", grammar_errors is not None, f"Type: {type(grammar_errors)}"))
    results.append((f"Word Choice Errors: exists", word_choice_errors is not None, f"Type: {type(word_choice_errors)}"))
    results.append((f"Fluency Notes: exists", fluency_notes is not None, f"Type: {type(fluency_notes)}"))
    
    # =====================================================================
    # WORD TIMESTAMPS VALIDATION
    # =====================================================================
    
    word_timestamps = response.get("word_timestamps", [])
    
    if word_timestamps:
        # Check structure
        is_list = isinstance(word_timestamps, list)
        results.append((f"Word Timestamps: is list", is_list, f"Type: {type(word_timestamps)}"))
        
        # Sample validation of first few entries
        if len(word_timestamps) > 0:
            for i, entry in enumerate(word_timestamps[:3]):
                has_word = "word" in entry
                has_type = "type" in entry
                has_start = "start_sec" in entry
                has_end = "end_sec" in entry
                all_fields = has_word and has_type and has_start and has_end
                
                word = entry.get("word", "")
                ts_type = entry.get("type", "")
                start = entry.get("start_sec", 0)
                end = entry.get("end_sec", 0)
                
                # Check timestamps are reasonable
                valid_timing = start >= 0 and end >= start
                valid_type = ts_type in ["content", "filler"]
                
                results.append((f"Word Timestamps[{i}]: all fields present and valid", all_fields and valid_timing and valid_type, f"Word: {word}, Type: {ts_type}, Time: [{start}, {end}]"))
    
    # =====================================================================
    # LLM ANALYSIS VALIDATION
    # =====================================================================
    
    llm_analysis = response.get("llm_analysis", {})
    
    if llm_analysis:
        llm_fields = [
            "topic_relevance",
            "grammar_error_count",
            "word_choice_error_count",
            "advanced_vocabulary_count",
            "coherence_break_count",
        ]
        
        for field in llm_fields:
            exists = field in llm_analysis
            value = llm_analysis.get(field)
            results.append((f"LLM Analysis: {field} exists", exists, f"Value: {value}"))
    
    # =====================================================================
    # SPEECH QUALITY VALIDATION
    # =====================================================================
    
    speech_quality = response.get("speech_quality", {})
    
    if speech_quality:
        sq_fields = {
            "mean_word_confidence": (float, "[0,1]"),
            "low_confidence_ratio": (float, "[0,1]"),
            "is_monotone": (bool, "true/false"),
        }
        
        for field, (expected_type, constraint) in sq_fields.items():
            exists = field in speech_quality
            if exists:
                value = speech_quality[field]
                correct_type = isinstance(value, expected_type)
                results.append((f"Speech Quality: {field} ({expected_type.__name__})", correct_type, f"Value: {value}"))
            else:
                results.append((f"Speech Quality: {field} exists", False, "Missing"))
    
    return results


def print_validation_report(results: List[Tuple[str, bool, str]]):
    """Print formatted validation report."""
    print("\n" + "="*100)
    print("API RESPONSE VALIDATION REPORT")
    print("="*100 + "\n")
    
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    
    print(f"SUMMARY: {passed}/{total} checks passed ({100*passed/total:.1f}%)\n")
    
    print("DETAILED RESULTS:\n")
    
    for check, passed, message in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {check:<55} | {message}")
    
    print("\n" + "="*100)
    
    failed = [c for c, p, _ in results if not p]
    if failed:
        print(f"\nFAILED CHECKS ({len(failed)}):")
        for check in failed:
            print(f"  - {check}")
    
    print("="*100 + "\n")


def main():
    """Run validation on API response example."""
    # Load example response
    example_file = Path("outputs/band_results/ielts5-5.5.json")
    
    if not example_file.exists():
        print(f"Error: Example file not found: {example_file}")
        return
    
    with open(example_file) as f:
        data = json.load(f)
    
    # Extract the raw_analysis if wrapped
    if "raw_analysis" in data:
        response = data["raw_analysis"]
    elif "band_scores" in data and "overall_band" not in data:
        # Wrapped in band_scores - use the parent
        response = data
    else:
        response = data
    
    # Run validation
    results = validate_response(response)
    print_validation_report(results)


if __name__ == "__main__":
    main()
