"""
Experiment: Combined LLM Call vs Separate Calls
================================================

This script tests whether combining LLM band scoring and annotations into a single call
produces the same quality results while saving time.

Tests on pre-analyzed audio files and compares with existing band results.

Run: python test_combined_llm_experiment.py
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from src.utils.logging_config import logger

# Load environment variables (including OPENAI_API_KEY)
load_dotenv()

# Enable UTF-8 output on Windows
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.core.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.core.ielts_band_scorer import score_ielts_speaking


async def combined_llm_analysis(
    transcript: str,
    metrics: Dict[str, Any],
    speech_context: str = "conversational"
) -> Dict:
    """
    EXPERIMENT: Combined LLM call that returns both band scores and annotations.
    
    Currently the code makes 2 separate calls:
    1. extract_llm_annotations() → annotations + grammar/vocab feedback
    2. score_ielts_speaking(use_llm=True) → band scores
    
    This combines them into a single call to see if we get equivalent results.
    """
    from openai import AsyncOpenAI
    import json
    import os
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = AsyncOpenAI(api_key=api_key)
    
    # Prepare a comprehensive prompt
    system_prompt = """You are an IELTS speaking assessor. 
    
    Analyze the transcript considering the provided metrics.
    Return BOTH band scores AND detailed annotations in JSON format.
    
    Be consistent: if transcript shows complex grammar, band score should reflect it.
    """
    
    user_prompt = f"""
    TRANSCRIPT:
    {transcript}
    
    METRICS PROVIDED:
    - Speech rate: {metrics.get('wpm', 'N/A')} WPM
    - Pause frequency: {metrics.get('pause_frequency', 'N/A')} per minute
    - Mean word confidence: {metrics.get('mean_word_confidence', 'N/A')}
    - Filler percentage: {metrics.get('filler_percentage', 'N/A')}%
    - Vocabulary diversity: {metrics.get('type_token_ratio', 'N/A')}
    - Repetition ratio: {metrics.get('repetition_ratio', 'N/A')}
    
    Analyze and return valid JSON with:
    {{
        "band_scores": {{
            "fluency_coherence": <6.0-9.0>,
            "pronunciation": <6.0-9.0>,
            "lexical_resource": <6.0-9.0>,
            "grammatical_range_accuracy": <6.0-9.0>,
            "overall_score": <6.0-9.0>
        }},
        "annotations": {{
            "grammar_errors": [list of found errors],
            "grammar_error_count": <number>,
            "word_choice_errors": [list of errors],
            "word_choice_error_count": <number>,
            "advanced_vocabulary_count": <number>,
            "topic_relevance": <true/false>,
            "coherence_breaks": <number>,
            "listener_effort_high": <true/false>,
            "flow_instability_present": <true/false>,
            "overall_clarity_score": <1-5>,
            "cascading_grammar_failure": <true/false>
        }},
        "confidence": <0.5-0.95>,
        "reasoning": "Brief explanation of band scores"
    }}
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse response
        content = response.choices[0].message.content
        
        # Try to extract JSON from the content
        # Sometimes LLM wraps it in markdown code blocks
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        else:
            json_str = content
        
        result = json.loads(json_str)
        return result
    
    except Exception as e:
        logger.error(f"Combined LLM call failed: {str(e)}")
        return {}


async def run_experiment():
    """Run the experiment comparing separate vs combined LLM calls."""
    
    print("\n" + "="*80)
    print("EXPERIMENT: Combined LLM Call Analysis")
    print("="*80)
    
    # Paths
    audio_analysis_dir = Path("outputs/audio_analysis")
    band_results_dir = Path("outputs/band_results")
    
    # Files to test
    test_files = [
        "ielts5.5.json",
        "ielts7.json",
        "ielts8.5.json",
    ]
    
    results_comparison = []
    
    for filename in test_files:
        print(f"\n{'─'*80}")
        print(f"Testing: {filename}")
        print(f"{'─'*80}")
        
        # Load audio analysis (raw metrics + transcript)
        audio_file = audio_analysis_dir / filename
        if not audio_file.exists():
            print(f"⚠ Audio analysis file not found: {audio_file}")
            continue
        
        with open(audio_file, 'r', encoding='utf-8') as f:
            audio_data = json.load(f)
        
        # Load existing band results (baseline)
        band_file = band_results_dir / filename
        if not band_file.exists():
            print(f"⚠ Band results file not found: {band_file}")
            continue
        
        with open(band_file, 'r', encoding='utf-8') as f:
            baseline_results = json.load(f)
        
        # Extract transcript and metrics
        transcript = audio_data.get('raw_analysis', {}).get('raw_transcript', '')
        metrics = {k: v for k, v in audio_data.get('raw_analysis', {}).items() 
                   if k not in ['raw_transcript', 'timestamps', 'fluency_analysis', 'statistics']}
        
        print(f"\nTranscript length: {len(transcript)} chars")
        print(f"Metrics available: {len(metrics)}")
        
        # Get baseline band scores
        baseline_bands = baseline_results.get('band_scores', {}).get('criterion_bands', {})
        baseline_overall = baseline_results.get('band_scores', {}).get('overall_band')
        
        print(f"\n[BASELINE - Existing Results]")
        print(f"  Overall Band: {baseline_overall}")
        for criterion, band in baseline_bands.items():
            print(f"    {criterion}: {band}")
        
        # Run combined LLM analysis
        print(f"\n[EXPERIMENT - Combined LLM Call]")
        print(f"  Running combined LLM analysis...")
        
        combined_result = await combined_llm_analysis(transcript, metrics)
        
        if not combined_result:
            print(f"  ✗ Combined LLM call failed")
            continue
        
        combined_bands = combined_result.get('band_scores', {})
        combined_overall = combined_bands.get('overall_score')
        
        print(f"  Overall Band: {combined_overall}")
        for criterion in ['fluency_coherence', 'pronunciation', 'lexical_resource', 'grammatical_range_accuracy']:
            score = combined_bands.get(criterion)
            print(f"    {criterion}: {score}")
        
        # Calculate differences
        print(f"\n[COMPARISON - Baseline vs Combined]")
        differences = {}
        
        if baseline_overall and combined_overall:
            diff = abs(baseline_overall - combined_overall)
            differences['overall'] = diff
            print(f"  Overall Band Difference: {diff:.2f}")
            print(f"    Baseline: {baseline_overall} → Combined: {combined_overall}")
        
        for criterion in ['fluency_coherence', 'pronunciation', 'lexical_resource', 'grammatical_range_accuracy']:
            baseline_val = baseline_bands.get(criterion)
            combined_val = combined_bands.get(criterion)
            
            if baseline_val is not None and combined_val is not None:
                diff = abs(baseline_val - combined_val)
                differences[criterion] = diff
                status = "✓" if diff <= 0.5 else "⚠" if diff <= 1.0 else "✗"
                print(f"  {status} {criterion}: diff={diff:.2f} ({baseline_val} → {combined_val})")
        
        # Annotations comparison
        print(f"\n[ANNOTATIONS - Combined LLM]")
        annotations = combined_result.get('annotations', {})
        print(f"  Grammar error count: {annotations.get('grammar_error_count', 'N/A')}")
        print(f"  Word choice error count: {annotations.get('word_choice_error_count', 'N/A')}")
        print(f"  Advanced vocabulary count: {annotations.get('advanced_vocabulary_count', 'N/A')}")
        print(f"  Topic relevance: {annotations.get('topic_relevance', 'N/A')}")
        print(f"  Coherence breaks: {annotations.get('coherence_breaks', 'N/A')}")
        print(f"  Listener effort high: {annotations.get('listener_effort_high', 'N/A')}")
        print(f"  Clarity score: {annotations.get('overall_clarity_score', 'N/A')}/5")
        
        # Summary
        results_comparison.append({
            "file": filename,
            "baseline_overall": baseline_overall,
            "combined_overall": combined_overall,
            "overall_diff": differences.get('overall', None),
            "criterion_diffs": {k: v for k, v in differences.items() if k != 'overall'},
            "annotations_quality": "available" if annotations else "missing"
        })
        
        # Wait between API calls
        await asyncio.sleep(2)
    
    # Final Report
    print(f"\n\n{'='*80}")
    print("EXPERIMENT SUMMARY")
    print(f"{'='*80}")
    
    print(f"\nResults Comparison ({len(results_comparison)} files tested):")
    
    total_diff = 0
    count = 0
    
    for result in results_comparison:
        print(f"\n{result['file']}:")
        print(f"  Overall Band: {result['baseline_overall']} → {result['combined_overall']}")
        if result['overall_diff'] is not None:
            print(f"  Difference: {result['overall_diff']:.2f}")
            total_diff += result['overall_diff']
            count += 1
        print(f"  Criterion max diff: {max(result['criterion_diffs'].values()) if result['criterion_diffs'] else 'N/A'}")
        print(f"  Annotations: {result['annotations_quality']}")
    
    if count > 0:
        avg_diff = total_diff / count
        print(f"\n{'─'*80}")
        print(f"Average Band Difference: {avg_diff:.2f}")
        
        if avg_diff <= 0.25:
            print("✓ EXCELLENT: Results are nearly identical. Combined LLM call is viable!")
        elif avg_diff <= 0.5:
            print("✓ GOOD: Results are very similar. Combined call maintains quality.")
        elif avg_diff <= 1.0:
            print("⚠ ACCEPTABLE: Results differ slightly but within acceptable range.")
        else:
            print("✗ CAUTION: Results differ significantly. May need refinement.")
    
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS:")
    print(f"{'='*80}")
    print("""
1. If average difference <= 0.5: Use combined LLM call in production
   - Saves 5-8 seconds per request (50% faster)
   - Maintains quality equivalence
   
2. If average difference > 0.5: Refine the combined prompt
   - May need better context
   - May need adjusted temperature/model
   
3. Always validate on larger dataset
   - Current test: 3 samples
   - Full validation: 20-30 samples
    """)
    
    return results_comparison


if __name__ == "__main__":
    results = asyncio.run(run_experiment())
