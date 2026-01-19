"""Check for score inconsistencies by re-running audio_analysis scoring."""
import json
from pathlib import Path
from src.core.ielts_band_scorer import IELTSBandScorer

def run_scoring_check():
    """Re-run scoring on all audio_analysis files and compare with band_results."""
    
    scorer = IELTSBandScorer()
    audio_dir = Path("outputs/audio_analysis")
    band_results_dir = Path("outputs/band_results")
    
    inconsistencies = []
    
    print("="*80)
    print("RE-RUNNING AUDIO ANALYSIS SCORING - CHECKING FOR INCONSISTENCIES")
    print("="*80)
    
    for audio_file in sorted(audio_dir.glob("*.json")):
        if audio_file.name.startswith("test_"):
            continue
        
        print(f"\n[{audio_file.name}]")
        
        # Load audio analysis
        with open(audio_file) as f:
            audio_data = json.load(f)
        
        raw_analysis = audio_data.get("raw_analysis", {})
        
        # Build metrics
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
        
        transcript = raw_analysis.get("raw_transcript", "")
        
        # Score
        new_result = scorer.score_overall_with_feedback(metrics, transcript, None)
        
        # Load existing band_results
        band_file = band_results_dir / audio_file.name
        if not band_file.exists():
            print(f"  ⚠️  No existing band_results file")
            continue
        
        with open(band_file) as f:
            existing_result = json.load(f)
        
        # Compare scores
        new_overall = new_result["overall_band"]
        old_overall = existing_result.get("overall_band")
        
        new_fluency = new_result["criterion_bands"]["fluency_coherence"]
        old_fluency = existing_result.get("band_scores", {}).get("fluency_coherence")
        
        new_pron = new_result["criterion_bands"]["pronunciation"]
        old_pron = existing_result.get("band_scores", {}).get("pronunciation")
        
        new_lex = new_result["criterion_bands"]["lexical_resource"]
        old_lex = existing_result.get("band_scores", {}).get("lexical_resource")
        
        new_gram = new_result["criterion_bands"]["grammatical_range_accuracy"]
        old_gram = existing_result.get("band_scores", {}).get("grammatical_range_accuracy")
        
        new_conf = new_result["confidence"]["overall_confidence"]
        old_conf = existing_result.get("confidence", {}).get("overall_confidence")
        
        # Check for differences
        has_inconsistency = False
        
        print(f"  Overall: {old_overall} → {new_overall}", end="")
        if old_overall != new_overall:
            print(f" ❌ INCONSISTENT")
            has_inconsistency = True
            inconsistencies.append({
                "file": audio_file.name,
                "criterion": "overall",
                "old": old_overall,
                "new": new_overall
            })
        else:
            print(" ✓")
        
        print(f"  Fluency: {old_fluency} → {new_fluency}", end="")
        if old_fluency != new_fluency:
            print(f" ❌ INCONSISTENT")
            has_inconsistency = True
            inconsistencies.append({
                "file": audio_file.name,
                "criterion": "fluency",
                "old": old_fluency,
                "new": new_fluency
            })
        else:
            print(" ✓")
        
        print(f"  Pronunciation: {old_pron} → {new_pron}", end="")
        if old_pron != new_pron:
            print(f" ❌ INCONSISTENT")
            has_inconsistency = True
            inconsistencies.append({
                "file": audio_file.name,
                "criterion": "pronunciation",
                "old": old_pron,
                "new": new_pron
            })
        else:
            print(" ✓")
        
        print(f"  Lexical: {old_lex} → {new_lex}", end="")
        if old_lex != new_lex:
            print(f" ❌ INCONSISTENT")
            has_inconsistency = True
            inconsistencies.append({
                "file": audio_file.name,
                "criterion": "lexical",
                "old": old_lex,
                "new": new_lex
            })
        else:
            print(" ✓")
        
        print(f"  Grammar: {old_gram} → {new_gram}", end="")
        if old_gram != new_gram:
            print(f" ❌ INCONSISTENT")
            has_inconsistency = True
            inconsistencies.append({
                "file": audio_file.name,
                "criterion": "grammar",
                "old": old_gram,
                "new": new_gram
            })
        else:
            print(" ✓")
        
        print(f"  Confidence: {old_conf} → {new_conf}", end="")
        if old_conf != new_conf:
            print(f" ❌ INCONSISTENT")
            has_inconsistency = True
            inconsistencies.append({
                "file": audio_file.name,
                "criterion": "confidence",
                "old": old_conf,
                "new": new_conf
            })
        else:
            print(" ✓")
        
        if not has_inconsistency:
            print(f"  ✅ ALL SCORES CONSISTENT")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if inconsistencies:
        print(f"\n❌ Found {len(inconsistencies)} inconsistencies:\n")
        for inc in inconsistencies:
            print(f"  {inc['file']}: {inc['criterion']}")
            print(f"    Old: {inc['old']} → New: {inc['new']}")
    else:
        print("\n✅ ALL SCORES CONSISTENT - No inconsistencies found!")
    
    return inconsistencies

if __name__ == "__main__":
    inconsistencies = run_scoring_check()
