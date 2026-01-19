"""
Debug script to inspect LLM findings for a specific audio file
"""
import json
import sys
from pathlib import Path

# Setup project path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.llm_processing import extract_llm_annotations, aggregate_llm_metrics
from src.utils.logging_config import setup_logging

logger = setup_logging(level="INFO")

def debug_llm_analysis(audio_file: str):
    """Debug LLM annotations for a specific file."""
    
    audio_analysis_dir = Path(PROJECT_ROOT) / "outputs" / "audio_analysis"
    audio_path = audio_analysis_dir / f"{audio_file}.json"
    
    # Load audio analysis
    with open(audio_path, 'r') as f:
        audio_data = json.load(f)
    
    raw_analysis = audio_data.get("raw_analysis", {})
    transcript = raw_analysis.get("raw_transcript", "")
    
    print(f"\n{'='*70}")
    print(f"LLM ANALYSIS DEBUG: {audio_file}")
    print(f"{'='*70}\n")
    
    print(f"Transcript preview:\n{transcript[:500]}...\n")
    
    # Run LLM analysis
    print("Running LLM extraction...")
    llm_annotations = extract_llm_annotations(transcript)
    llm_metrics = aggregate_llm_metrics(llm_annotations)
    
    print("\nLLM RESULTS:")
    print(f"  Advanced Vocabulary Count: {llm_metrics.get('advanced_vocabulary_count', 0)}")
    print(f"  Idiomatic Collocation Count: {llm_metrics.get('idiomatic_collocation_count', 0)}")
    print(f"  Word Choice Errors: {llm_metrics.get('word_choice_error_count', 0)}")
    print(f"  Grammar Errors: {llm_metrics.get('grammar_error_count', 0)}")
    
    # Show advanced vocabulary examples
    if llm_annotations.advanced_vocabulary:
        print(f"\n  Advanced Vocabulary Examples:")
        for item in llm_annotations.advanced_vocabulary[:5]:
            print(f"    - '{item.text}'")
    else:
        print(f"\n  Advanced Vocabulary: NONE DETECTED")
    
    # Show idiomatic examples
    if llm_annotations.idiomatic_or_collocational_use:
        print(f"\n  Idiomatic/Collocational Examples:")
        for item in llm_annotations.idiomatic_or_collocational_use[:5]:
            print(f"    - '{item.text}'")
    else:
        print(f"\n  Idiomatic Use: NONE DETECTED")
    
    # Show word choice errors
    if llm_annotations.word_choice_errors:
        print(f"\n  Word Choice Errors:")
        for item in llm_annotations.word_choice_errors[:5]:
            print(f"    - '{item.text}'")
    else:
        print(f"\n  Word Choice Errors: NONE DETECTED")

if __name__ == "__main__":
    # Debug the top-band speakers to understand why lexical isn't high
    for file in ["ielts9", "ielts8.5", "ielts8-8.5", "ielts7"]:
        try:
            debug_llm_analysis(file)
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
