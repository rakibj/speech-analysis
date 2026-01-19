"""Context parser for speech analysis context strings.

Supports various context formats:
- "conversational" - General conversation
- "ielts" - IELTS Speaking (topic-based)
- "ielts[topic: ..., cue_card: ...]" - IELTS with metadata
- "custom[...]" - Custom context with metadata

Extracts base_type and metadata for flexible context handling.
"""

import re
from typing import Dict, Any, Tuple
from src.utils.logging_config import setup_logging

logger = setup_logging(level="INFO")


def parse_context(context_str: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse context string into base type and metadata.
    
    Args:
        context_str: Context string (e.g., "ielts[topic: Speaking about family, cue_card: Part 2]")
    
    Returns:
        Tuple of (base_type, metadata_dict)
        - base_type: "conversational", "ielts", "narrative", "presentation", "interview", or "custom"
        - metadata_dict: Dictionary of extracted metadata (topic, cue_card, etc.)
    
    Examples:
        "conversational" → ("conversational", {})
        "ielts" → ("ielts", {})
        "ielts[topic: family, cue_card: Describe someone]" → 
            ("ielts", {"topic": "family", "cue_card": "Describe someone"})
        "custom[speech_type: presentation, formality: high]" →
            ("custom", {"speech_type": "presentation", "formality": "high"})
    """
    
    context_str = context_str.strip()
    metadata = {}
    
    # Check if context has metadata in brackets: "base_type[key1: val1, key2: val2]"
    match = re.match(r'^(\w+)\s*\[(.*)\]$', context_str)
    
    if match:
        base_type = match.group(1).lower()
        metadata_str = match.group(2)
        
        # Parse key: value pairs
        pairs = metadata_str.split(',')
        for pair in pairs:
            pair = pair.strip()
            if ':' in pair:
                key, value = pair.split(':', 1)
                metadata[key.strip().lower()] = value.strip()
    else:
        # Simple context without metadata
        base_type = context_str.lower()
    
    # Normalize base types
    valid_types = {"conversational", "ielts", "narrative", "presentation", "interview", "custom"}
    if base_type not in valid_types:
        logger.warning(f"Unknown context type '{base_type}', defaulting to 'conversational'")
        base_type = "conversational"
    
    return base_type, metadata


def format_context_for_llm(base_type: str, metadata: Dict[str, Any]) -> str:
    """
    Format context information for LLM analysis.
    
    Helps LLM understand the speech context for better annotations
    (e.g., topic relevance checks for IELTS).
    
    Args:
        base_type: Context type (ielts, conversational, etc.)
        metadata: Context metadata (topic, cue_card, etc.)
    
    Returns:
        Formatted string for LLM consumption
    """
    
    if base_type == "ielts":
        parts = ["IELTS Speaking Test"]
        if "topic" in metadata:
            parts.append(f"Topic: {metadata['topic']}")
        if "cue_card" in metadata:
            parts.append(f"Cue Card: {metadata['cue_card']}")
        if "part" in metadata:
            parts.append(f"Part: {metadata['part']}")
        return " | ".join(parts)
    
    elif base_type == "custom":
        if metadata:
            pairs = [f"{k}: {v}" for k, v in metadata.items()]
            return " | ".join(pairs)
        return "Custom Speech Context"
    
    else:
        return f"{base_type.capitalize()} Speech"


def get_tolerance_config(base_type: str) -> Dict[str, float]:
    """
    Get tolerance configuration for context type.
    
    Args:
        base_type: Context type
    
    Returns:
        Dictionary with pause_tolerance and pause_variability_tolerance
    """
    from src.utils.config import CONTEXT_CONFIG
    
    if base_type in CONTEXT_CONFIG:
        config = CONTEXT_CONFIG[base_type]
        return {
            "pause_tolerance": config.get("pause_tolerance", 1.0),
            "pause_variability_tolerance": config.get("pause_variability_tolerance", 1.0),
        }
    
    # Default to conversational
    config = CONTEXT_CONFIG.get("conversational", {})
    return {
        "pause_tolerance": config.get("pause_tolerance", 1.0),
        "pause_variability_tolerance": config.get("pause_variability_tolerance", 1.0),
    }


if __name__ == "__main__":
    # Test examples
    test_cases = [
        "conversational",
        "ielts",
        "ielts[topic: family, cue_card: Describe someone important to you]",
        "ielts[topic: travel, part: 2]",
        "custom[speech_type: podcast, formality: medium]",
    ]
    
    for test in test_cases:
        base_type, metadata = parse_context(test)
        llm_format = format_context_for_llm(base_type, metadata)
        print(f"Input:    {test}")
        print(f"Base:     {base_type}")
        print(f"Metadata: {metadata}")
        print(f"LLM:      {llm_format}")
        print()
