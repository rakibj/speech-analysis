#!/usr/bin/env python3
"""Re-run analysis on test files with fixed pronunciation confidence"""
import json
import asyncio
from pathlib import Path
from src.core.analyzer_raw import analyze_speech

async def main():
    data_dir = Path("data/ielts_part_2")
    output_dir = Path("outputs/audio_analysis")
    band_dir = Path("outputs/band_results")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    band_dir.mkdir(parents=True, exist_ok=True)
    
    wav_files = sorted(data_dir.rglob("*.wav"))
    
    print(f"Found {len(wav_files)} audio files")
    print("=" * 70)
    
    for idx, wav_path in enumerate(wav_files, 1):
        print(f"\n[{idx}/{len(wav_files)}] Analyzing: {wav_path.name}")
        
        try:
            # Run raw analysis with fixed confidence extraction
            result = await analyze_speech(str(wav_path), "conversational", "cpu")
            
            # Wrap in expected structure
            analysis_wrapper = {
                "raw_analysis": result
            }
            
            # Save raw analysis
            analysis_file = output_dir / f"{wav_path.stem}.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_wrapper, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Analysis saved")
            print(f"    Mean word confidence: {result.get('mean_word_confidence', 'N/A'):.3f}")
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Analysis complete!")

if __name__ == "__main__":
    asyncio.run(main())
