"""
Analyze pronunciation scoring across all band results
"""
import json
from pathlib import Path

def analyze_pronunciation():
    """Analyze pronunciation scores and metrics"""
    
    project_root = Path(__file__).resolve().parent
    band_results_dir = project_root / "outputs" / "band_results"
    
    print("\n" + "="*100)
    print("PRONUNCIATION SCORING ANALYSIS")
    print("="*100 + "\n")
    
    files = sorted(band_results_dir.glob("*.json"))
    
    print(f"{'File':<15} {'Pron':<8} {'Mean Conf':<12} {'Low Conf %':<12} {'Feedback':<50}")
    print("-" * 100)
    
    results = []
    
    for file in files:
        with open(file) as f:
            data = json.load(f)
        
        pron_score = data["band_scores"]["criterion_bands"]["pronunciation"]
        pron_feedback = data["band_scores"]["feedback"]["pronunciation"]
        
        mean_conf = data["metrics"].get("mean_word_confidence", 0)
        low_conf_ratio = data["metrics"].get("low_confidence_ratio", 0)
        low_conf_pct = low_conf_ratio * 100
        
        feedback_short = pron_feedback[:48] + "..." if len(pron_feedback) > 50 else pron_feedback
        
        results.append({
            "file": file.stem,
            "score": pron_score,
            "mean_conf": mean_conf,
            "low_conf_ratio": low_conf_ratio,
            "low_conf_pct": low_conf_pct,
            "feedback": pron_feedback,
        })
        
        print(f"{file.stem:<15} {pron_score:<8.1f} {mean_conf:<12.3f} {low_conf_pct:<12.1f}% {feedback_short:<50}")
    
    print("\n" + "="*100)
    print("ANALYSIS OF PRONUNCIATION CONSISTENCY")
    print("="*100 + "\n")
    
    # Expected ranges based on file names
    expected_ranges = {
        "ielts5-5.5": (5.0, 6.5),
        "ielts5.5": (5.0, 6.5),
        "ielts7-7.5": (6.5, 7.5),
        "ielts7": (6.5, 7.5),
        "ielts8-8.5": (7.5, 8.5),
        "ielts8.5": (8.0, 9.0),
        "ielts9": (8.0, 9.0),
    }
    
    print("Expected vs Actual:\n")
    issues = []
    for result in results:
        expected = expected_ranges.get(result["file"], (5.0, 9.0))
        score = result["score"]
        in_range = expected[0] <= score <= expected[1]
        
        status = "✓" if in_range else "✗"
        print(f"{status} {result['file']:<15} | Expected: {expected[0]}-{expected[1]} | Got: {score:<5.1f} | Conf: {result['mean_conf']:.3f}")
        
        if not in_range:
            issues.append({
                "file": result["file"],
                "expected": expected,
                "actual": score,
                "mean_conf": result["mean_conf"],
                "low_conf_pct": result["low_conf_pct"],
            })
    
    print("\n" + "="*100)
    print("DETAILED ISSUES & RECOMMENDATIONS")
    print("="*100 + "\n")
    
    if issues:
        for issue in issues:
            print(f"\n⚠ {issue['file']}")
            print(f"  Expected range: {issue['expected'][0]}-{issue['expected'][1]}")
            print(f"  Actual score: {issue['actual']:.1f}")
            print(f"  Mean confidence: {issue['mean_conf']:.3f}")
            print(f"  Low confidence ratio: {issue['low_conf_pct']:.1f}%")
            
            if issue['actual'] > issue['expected'][1]:
                print(f"  → Score is too HIGH by {issue['actual'] - issue['expected'][1]:.1f}")
                print(f"  → Recommendation: Consider if this speaker truly has exceptional pronunciation")
            else:
                print(f"  → Score is too LOW by {issue['expected'][0] - issue['actual']:.1f}")
                print(f"  → Recommendation: Adjust thresholds or check metrics calculation")
    else:
        print("✓ All pronunciation scores are within expected ranges!\n")
    
    print("\n" + "="*100)
    print("PRONUNCIATION THRESHOLDS REVIEW")
    print("="*100 + "\n")
    
    print("Current thresholds in ielts_band_scorer.py:\n")
    thresholds = [
        ("8.5", "mean_conf >= 0.92 AND low_conf_ratio <= 0.08"),
        ("8.0", "mean_conf >= 0.89 AND low_conf_ratio <= 0.12"),
        ("7.5", "mean_conf >= 0.85 AND low_conf_ratio <= 0.20"),
        ("7.0", "mean_conf >= 0.82 AND low_conf_ratio <= 0.30"),
        ("6.5", "mean_conf >= 0.79 AND low_conf_ratio <= 0.35"),
        ("5.5", "low_conf_ratio >= 0.35"),
    ]
    
    for band, condition in thresholds:
        print(f"  Band {band}: {condition}")
    
    print("\nData points from current results:")
    for result in sorted(results, key=lambda x: x["mean_conf"], reverse=True):
        print(f"  {result['file']:<15} → Mean: {result['mean_conf']:.3f}, Low %: {result['low_conf_pct']:>5.1f}% → Score: {result['score']:.1f}")

if __name__ == "__main__":
    analyze_pronunciation()
