"""
Demonstration of the new context system for speech analysis.

The context parameter now supports rich semantic information about the speech,
especially for IELTS speaking tests with topics and cue cards.
"""

import sys
sys.path.insert(0, '.')

from src.utils.context_parser import parse_context, format_context_for_llm

def demo_basic_context():
    """Demo: Basic context types."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Context Types (Backward Compatible)")
    print("=" * 70)
    
    contexts = [
        "conversational",
        "narrative",
        "presentation",
        "interview",
    ]
    
    for ctx in contexts:
        base_type, metadata = parse_context(ctx)
        llm_format = format_context_for_llm(base_type, metadata)
        print(f"\nInput: '{ctx}'")
        print(f"  → Base type: {base_type}")
        print(f"  → Metadata: {metadata if metadata else '(empty)'}")
        print(f"  → For LLM: {llm_format}")

def demo_ielts_context():
    """Demo: IELTS-specific context with topics and cue cards."""
    print("\n" + "=" * 70)
    print("DEMO 2: IELTS Speaking Context with Topics & Cue Cards")
    print("=" * 70)
    
    ielts_contexts = [
        "ielts",  # Simple IELTS
        "ielts[topic: family]",  # With topic
        "ielts[topic: family, part: 2]",  # With topic and part
        'ielts[topic: family, cue_card: Describe someone important to you, part: 2]',  # Full
        "ielts[topic: travel, cue_card: Describe a memorable trip you took]",
    ]
    
    for ctx in ielts_contexts:
        base_type, metadata = parse_context(ctx)
        llm_format = format_context_for_llm(base_type, metadata)
        print(f"\nInput: '{ctx}'")
        print(f"  → Base type: {base_type}")
        print(f"  → Metadata: {metadata if metadata else '(empty)'}")
        print(f"  → For LLM: {llm_format}")
        print(f"  → Use case: LLM will check topic relevance to: {metadata.get('topic', 'any topic')}")

def demo_custom_context():
    """Demo: Custom context for other speech types."""
    print("\n" + "=" * 70)
    print("DEMO 3: Custom Context for Other Use Cases")
    print("=" * 70)
    
    custom_contexts = [
        "custom[speech_type: podcast, formality: casual, audience: tech-savvy]",
        "custom[speech_type: interview, position: senior engineer, company: tech startup]",
        "custom[speech_type: presentation, domain: machine learning, duration: 10min]",
    ]
    
    for ctx in custom_contexts:
        base_type, metadata = parse_context(ctx)
        llm_format = format_context_for_llm(base_type, metadata)
        print(f"\nInput: '{ctx}'")
        print(f"  → Base type: {base_type}")
        print(f"  → Metadata: {metadata}")
        print(f"  → For LLM: {llm_format}")

def demo_usage_in_engine():
    """Demo: How to use new context in the engine."""
    print("\n" + "=" * 70)
    print("DEMO 4: Using New Context in Engine")
    print("=" * 70)
    
    print("""
import asyncio
from src.core.engine_runner import run_engine

# Example 1: Regular conversational speech
result = await run_engine(
    audio_bytes=audio_data,
    context="conversational",
    use_llm=True
)

# Example 2: IELTS speaking test with specific topic
result = await run_engine(
    audio_bytes=audio_data,
    context="ielts[topic: family, part: 2, cue_card: Describe an important person]",
    use_llm=True
)
# LLM will check if speaker is addressing the family topic

# Example 3: Podcast with specific metadata
result = await run_engine(
    audio_bytes=audio_data,
    context="custom[speech_type: podcast, topic: AI trends]",
    use_llm=True
)

# Example 4: Interview (stricter fluency standards)
result = await run_engine(
    audio_bytes=audio_data,
    context="interview",  # Uses stricter pause tolerances
    use_llm=True
)
""")

def demo_use_cases():
    """Demo: Real-world use cases."""
    print("\n" + "=" * 70)
    print("DEMO 5: Real-World Use Cases")
    print("=" * 70)
    
    use_cases = {
        "IELTS Speaking Test": {
            "context": "ielts[topic: technology, cue_card: Describe a piece of technology you use]",
            "why": "Enables topic relevance checking; soft relevance OK for IELTS",
        },
        "English Interview": {
            "context": "interview",
            "why": "Uses strict pause tolerances; rapid speech expected",
        },
        "Storytelling/Narrative": {
            "context": "narrative",
            "why": "Allows longer pauses between thoughts; more relaxed timing",
        },
        "Conference Presentation": {
            "context": "presentation",
            "why": "Medium pause tolerance; structured delivery expected",
        },
        "YouTube Video": {
            "context": "custom[speech_type: video, formality: casual, audience: general]",
            "why": "Flexible standards; context info for future analysis",
        },
    }
    
    for use_case, info in use_cases.items():
        print(f"\n{use_case}:")
        print(f"  Context: {info['context']}")
        print(f"  Benefit: {info['why']}")

def main():
    print("\n" + "=" * 70)
    print("CONTEXT SYSTEM DEMONSTRATION")
    print("=" * 70)
    
    demo_basic_context()
    demo_ielts_context()
    demo_custom_context()
    demo_usage_in_engine()
    demo_use_cases()
    
    print("\n" + "=" * 70)
    print("KEY FEATURES")
    print("=" * 70)
    print("""
✓ Backward Compatible
  - Old context names still work: conversational, narrative, presentation, interview
  - No breaking changes to existing code

✓ IELTS Specific
  - New format: ielts[topic: X, cue_card: Y, part: Z]
  - Enables soft topic relevance checking
  - Metadata passed to LLM for smarter analysis

✓ Flexible & Extensible
  - Custom format: custom[key1: val1, key2: val2]
  - Any metadata can be specified
  - Passed to LLM for context-aware analysis

✓ Semantic Rich
  - Context describes the speech semantic context, not just delivery style
  - Enables better error detection and feedback
  - Improves LLM understanding of speaker intent
""")
    
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
