"""
Quick test script for engine_runner
Run: python test_quick.py
"""

import asyncio
import json
from pathlib import Path
from src.core.engine_runner import run_engine


async def main():
    # Find sample audio
    # audio_file = Path("data/l2arctic_spontaneous/L2A_001.wav")
    audio_file = Path("data/ielts_part_2/ielts7.wav")
    # audio_file = Path("samples/sample6.flac")

    if not audio_file.exists():
        print(f"[ERROR] Audio File Not Found")
        return
    
    print(f"[INFO] Loading: {audio_file.name} ({audio_file.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # Read audio bytes
    with open(audio_file, "rb") as f:
        audio_bytes = f.read()
    
    # Run analysis
    try:
        print("\n[START] Starting analysis (this may take 1-2 minutes)...\n")
        
        result = await run_engine(
            audio_bytes=audio_bytes,
            context="conversational",
            use_llm=True,  # Disable LLM for faster testing
            filename=audio_file.name
        )
        
        # Display results
        print("\n" + "="*70)
        print("[OK] ANALYSIS COMPLETE")
        print("="*70)
        
        # Export final report to JSON
        output_path = Path("outputs") / f"final_report_{audio_file.stem}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[EXPORTED] Final report saved to: {output_path}\n")
        
        # Transcript
        transcript = result['transcript']
        print(f"\n[TRANSCRIPT]:\n{transcript}\n")
        
        # Band scores
        print(f"[IELTS BAND SCORES]:")
        print(f"   Overall Band: {result['band_scores']['overall_band']}")
        print(f"\n   Criterion Bands:")
        for criterion, band in result['band_scores']['criterion_bands'].items():
            print(f"     • {criterion}: {band}")
        
        # Feedback
        if result['band_scores']['feedback']:
            print(f"\n[FEEDBACK]:")
            for criterion, feedback in result['band_scores']['feedback'].items():
                print(f"   {criterion}:")
                print(f"     {feedback}\n")
        
        # Statistics
        print(f"[STATISTICS]:")
        stats = result['statistics']
        print(f"   • Duration: {result['metadata']['audio_duration_sec']}s")
        print(f"   • Total words: {stats['total_words_transcribed']}")
        print(f"   • Content words: {stats['content_words']}")
        print(f"   • Filler words: {stats['filler_words_detected']}")
        print(f"   • Filler percentage: {stats['filler_percentage']}%")
        print(f"   • Monotone: {'Yes' if stats['is_monotone'] else 'No'}")
        
        # Fluency metrics
        fluency = result['fluency_analysis']
        if fluency:
            print(f"\n[FLUENCY METRICS]:")
            if 'wpm' in fluency:
                print(f"   • Words per minute: {fluency['wpm']}")
            if 'long_pauses_per_min' in fluency:
                print(f"   • Long pauses per minute: {fluency['long_pauses_per_min']}")
            if 'pause_variability' in fluency:
                print(f"   • Pause variability: {fluency['pause_variability']}")
        
        # Speech quality
        quality = result['speech_quality']
        print(f"\n[SPEECH QUALITY]:")
        print(f"   • Mean word confidence: {quality['mean_word_confidence']:.3f}")
        print(f"   • Low confidence ratio: {quality['low_confidence_ratio']:.3f}")
        print(f"   • Monotone detected: {quality['is_monotone']}")
        
        # LLM analysis
        if result.get('llm_analysis'):
            print(f"\n[LLM ANALYSIS AVAILABLE]")
        else:
            print(f"\n[TIP] Run with use_llm=True for semantic analysis (slower)")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
