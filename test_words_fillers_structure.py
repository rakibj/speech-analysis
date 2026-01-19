"""Test script to show the new timestamped_words and timestamped_fillers structure."""
import json
import asyncio
from pathlib import Path

# Load one of the existing raw analyses to extract word and filler timestamps
async def demo_structure():
    # Try to load an existing analysis that has the raw data
    from src.core.analyzer_raw import analyze_speech as analyze_speech_raw
    
    # Load existing final report to understand structure
    report_path = Path("outputs/final_report_ielts7.json")
    if report_path.exists():
        with open(report_path) as f:
            existing = json.load(f)
            print("Current final_report keys:", list(existing.keys()))
    
    # Check if any band results have the structure we need
    band_results_path = Path("outputs/band_results")
    if band_results_path.exists():
        files = sorted(band_results_path.glob("*.json"))[:1]
        for file in files:
            print(f"\n=== Examining {file.name} ===")
            with open(file) as f:
                data = json.load(f)
            
            if "raw_analysis" in data:
                raw = data["raw_analysis"]
                timestamps = raw.get("timestamps", {})
                
                # Show word timestamps structure
                words = timestamps.get("words_timestamps_raw", [])
                if words:
                    print(f"\n✓ Found {len(words)} timestamped words")
                    print(f"  Sample word entries:")
                    for w in words[:3]:
                        print(f"    {w}")
                
                # Show filler timestamps structure  
                fillers = timestamps.get("filler_timestamps", [])
                if fillers:
                    print(f"\n✓ Found {len(fillers)} timestamped fillers")
                    print(f"  Sample filler entries:")
                    for f in fillers[:5]:
                        print(f"    {f}")
                else:
                    print("\n  No filler_timestamps found")

if __name__ == "__main__":
    asyncio.run(demo_structure())
