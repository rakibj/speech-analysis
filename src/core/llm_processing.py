from pydantic import BaseModel, Field, ValidationError as PydanticValidationError
from typing import List, Literal, Optional, Dict, Any
from openai import OpenAI
import json
import os
from difflib import SequenceMatcher
from src.utils.exceptions import LLMAPIError, LLMValidationError, ConfigurationError
from src.utils.logging_config import logger


# ======================================================
# Span definition
# ======================================================

class Span(BaseModel):
    text: str
    label: Literal[
        # Grammar
        "meaning_blocking_grammar_error",
        "grammar_error",

        # Lexical
        "word_choice_error",
        "advanced_vocabulary",
        "idiomatic_or_collocational_use",

        # Discourse
        "coherence_break",
        "clause_completion_issue",

        # Syntax
        "complex_structure",

        # Paraphrase
        "successful_paraphrase",
        "failed_paraphrase",

        # Register
        "register_mismatch",
    ]


# ======================================================
# Timestamped Span (with audio location)
# ======================================================

class SpanWithTimestamp(BaseModel):
    """Span with audio timestamp information."""
    text: str
    label: str
    start_sec: float
    end_sec: float
    timestamp_mmss: str
    
    class Config:
        frozen = False


# ======================================================
# LLM OUTPUT SCHEMA (IMPORTANT CHANGES)
# ======================================================

class LLMSpeechAnnotations(BaseModel):
    # Global judgments (now GRADED, not binary)
    topic_relevance: bool

    listener_effort_level: Literal["low", "medium", "high"]
    flow_control_level: Literal["stable", "mixed", "unstable"]

    overall_clarity_score: Literal[1, 2, 3, 4, 5]

    cascading_grammar_failure: bool

    # Discourse
    coherence_breaks: List[Span]
    clause_completion_issues: List[Span]

    # Lexical
    word_choice_errors: List[Span]
    advanced_vocabulary: List[Span]
    idiomatic_or_collocational_use: List[Span]

    # Grammar
    grammar_errors: List[Span]
    meaning_blocking_grammar_errors: List[Span]

    # Syntax
    complex_structures_attempted: List[Span]
    complex_structures_accurate: List[Span]

    # Paraphrase
    successful_paraphrase: List[Span]
    failed_paraphrase: List[Span]

    # Register
    register_mismatch: List[Span]


# ======================================================
# SYSTEM PROMPT (CRITICAL FIX)
# ======================================================

SYSTEM_PROMPT = """
You are an IELTS examiner-style annotation engine.

Your task:
- Annotate spans AND provide graded judgments.
- Be precise but NOT overly conservative.
- When evidence is reasonable, ANNOTATE.
- ACTIVELY SEEK advanced vocabulary and idiomatic use - don't omit them.

IMPORTANT BEHAVIOR CHANGE:
- If rewording is present, annotate paraphrase.
- If vocabulary is more precise/sophisticated than casual speech, annotate advanced_vocabulary.
- If vocabulary demonstrates natural language use beyond basic learner English, annotate.
- Use MEDIUM confidence when unsure, not omission.

GLOBAL JUDGMENTS:
- topic_relevance: 
  TRUE = speaker stays on topic or slightly tangential but related
  FALSE = off-topic rambling, random insertions unrelated to subject
  (Slight relevance is OK - mark TRUE)

- listener_effort_level:
  low    = effortless to follow (speech is coherent, connected)
  medium = occasional effort needed (some jumps or unclear transitions)
  high   = frequent effort required (scattered ideas, hard to track flow)
  (Use HIGH to penalize babblers and random idiom inserters)

- flow_control_level:
  stable   = consistent pacing, smooth transitions
  mixed    = uneven pacing but ideas are connected
  unstable = erratic flow, abrupt changes, no clear thread
  (Use UNSTABLE to catch gaming attempts)

- overall_clarity_score (1–5):
  5 = extremely clear, effortless
  3 = generally clear, some strain
  1 = hard to follow
  (Lower this if topic_relevance=FALSE or random idiom insertions detected)

ADVANCED VOCABULARY GUIDELINES (be GENEROUS):
- Academic/formal words: methodology, facilitate, leverage, emphasize, demonstrate, analyze
- Precise descriptors: meticulous, pragmatic, intricate, nuanced, eloquent
- Sophisticated expressions: "coincided with", "in hindsight", "nonetheless"
- Domain-specific terms: algorithm, paradigm, sustainable, reciprocal
- Adverbs of manner/degree: substantially, inherently, predominantly
- ANY word more advanced than basic learner English (not simple/common)

IDIOMATIC USE GUIDELINES (CONTEXT MATTERS):
- Annotate natural collocations IF CONTEXTUALLY APPROPRIATE: "came back", "set aside", "take for granted"
- Phrasal verbs IF USED MEANINGFULLY: "take on", "bring about", "shed light on"
- Common expressions IF NATURALLY USED: "in a nutshell", "on second thought"
- Figurative language IF RELEVANT TO TOPIC: "between a rock and a hard place", "silver lining"
- Expressions beyond word-by-word translation ONLY IF CONTEXTUALLY FITTING
- CRITICAL: Do NOT annotate random idiom insertion. If 3+ idioms appear disconnected from speech flow, mark as "register_mismatch" instead
- CRITICAL: If topic_relevance=FALSE or flow_control_level=unstable, penalize any idiom annotations

SPAN RULES:
- Shortest possible span
- Do not duplicate spans
- Prefer recall over extreme precision
- Do NOT annotate filler words as errors

LABEL PRECEDENCE (highest → lowest):
1. Meaning Blocking Grammar Error
2. Grammar Error
3. Failed Paraphrase
4. Word Choice Error
5. Coherence Break
6. Clause Completion Issue
7. Complex Structure
8. Successful Paraphrase
9. Idiomatic or Collocational Use
10. Advanced Vocabulary

CRITICAL: When you identify any sophisticated vocabulary or natural expression use, ALWAYS annotate it. 
This is measured in IELTS scoring - examiners actively listen for vocabulary range.

Return ONLY valid JSON.
"""


# ======================================================
# EXTRACTION
# ======================================================

def extract_llm_annotations(
    raw_transcript: str,
    speech_context: str = "conversational",
    context_metadata: dict = None
) -> LLMSpeechAnnotations:
    """
    Extract LLM-based speech annotations from transcript.
    
    Args:
        raw_transcript: Full transcript text
        speech_context: Context (conversational, narrative, ielts, etc)
        context_metadata: Optional metadata dict (e.g., {"topic": "family", "cue_card": "..."})
        
    Returns:
        LLMSpeechAnnotations object with parsed annotations
        
    Raises:
        ConfigurationError: If OpenAI API key is missing
        LLMAPIError: If OpenAI API call fails
        LLMValidationError: If response schema is invalid
    """
    # Validate API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ConfigurationError(
            "OpenAI API key not found. Set OPENAI_API_KEY environment variable.",
            {"environment_var": "OPENAI_API_KEY"}
        )
    
    # Validate transcript
    if not raw_transcript or not raw_transcript.strip():
        raise LLMValidationError(
            "Empty transcript provided to LLM",
            {"transcript_length": len(raw_transcript) if raw_transcript else 0}
        )
    
    try:
        client = OpenAI(api_key=api_key)
        
        payload = {
            "raw_transcript": raw_transcript,
            "speech_context": speech_context,
        }
        
        # Add context metadata if provided
        if context_metadata:
            payload["context_metadata"] = context_metadata
        
        logger.info(f"Extracting LLM annotations (context: {speech_context}, metadata: {context_metadata})")
        
        response = client.responses.parse(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            temperature=0.0,
            top_p=1.0,
            text_format=LLMSpeechAnnotations,
        )
        
        logger.info("LLM annotation extraction successful")
        return response.output_parsed
    except PydanticValidationError as e:
        raise LLMValidationError(
            f"LLM response validation failed: {str(e)}",
            {"validation_errors": str(e)}
        )
    except Exception as e:
        error_msg = str(e)
        if "API" in error_msg or "OpenAI" in error_msg:
            raise LLMAPIError(
                f"OpenAI API call failed: {error_msg}",
                {"error": error_msg, "model": "gpt-4o-mini"}
            )
        else:
            raise LLMAPIError(
                f"Unexpected error during LLM annotation: {error_msg}",
                {"error": error_msg}
            )


# ======================================================
# AGGREGATION (COMPATIBLE WITH EXISTING SCORER)
# ======================================================

def aggregate_llm_metrics(llm: LLMSpeechAnnotations) -> Dict[str, Any]:
    """
    Aggregate LLM annotations into metrics dictionary.
    
    Args:
        llm: LLMSpeechAnnotations object
        
    Returns:
        Dictionary of aggregated metrics for band scoring
    """
    grammar_errors = len(llm.grammar_errors)
    meaning_blocking = len(llm.meaning_blocking_grammar_errors)

    meaning_blocking_ratio = (
        meaning_blocking / grammar_errors if grammar_errors else 0.0
    )

    paraphrase_attempts = (
        len(llm.successful_paraphrase) + len(llm.failed_paraphrase)
    )

    paraphrase_success_ratio = (
        len(llm.successful_paraphrase) / paraphrase_attempts
        if paraphrase_attempts > 0 else None
    )

    complex_accuracy_ratio = (
        len(llm.complex_structures_accurate) /
        len(llm.complex_structures_attempted)
        if llm.complex_structures_attempted else None
    )

    return {
        # Relevance
        "topic_relevance": llm.topic_relevance,

        # NEW graded controls (mapped later)
        "listener_effort_high": llm.listener_effort_level == "high",
        "flow_instability_present": llm.flow_control_level == "unstable",
        "overall_clarity_score": llm.overall_clarity_score,

        # Coherence
        "coherence_break_count": len(llm.coherence_breaks),
        "clause_completion_issue_count": len(llm.clause_completion_issues),

        # Lexical
        "word_choice_error_count": len(llm.word_choice_errors),
        "advanced_vocabulary_count": len(llm.advanced_vocabulary),
        "idiomatic_collocation_count": len(llm.idiomatic_or_collocational_use),

        # Grammar
        "grammar_error_count": grammar_errors,
        "meaning_blocking_error_ratio": round(meaning_blocking_ratio, 3),
        "cascading_grammar_failure": llm.cascading_grammar_failure,

        # Syntax
        "complex_structures_attempted": len(llm.complex_structures_attempted),
        "complex_structure_accuracy_ratio": complex_accuracy_ratio,

        # Paraphrase
        "successful_paraphrase_count": len(llm.successful_paraphrase),
        "failed_paraphrase_count": len(llm.failed_paraphrase),
        "paraphrase_success_ratio": paraphrase_success_ratio,

        # Register
        "register_mismatch_count": len(llm.register_mismatch),
    }


# ======================================================
# SPAN-TO-TIMESTAMP MAPPING
# ======================================================

def find_span_in_transcript(
    transcript: str,
    span_text: str,
    fuzzy: bool = True,
    threshold: float = 0.8
) -> Optional[int]:
    """
    Find span text position in transcript using fuzzy matching.
    
    Args:
        transcript: Full transcript text (lowercase)
        span_text: Span text to find (lowercase)
        fuzzy: Whether to use fuzzy matching
        threshold: Similarity threshold for fuzzy match (0.0-1.0)
        
    Returns:
        Character index of span start, or None if not found
    """
    # Try exact match first
    idx = transcript.find(span_text)
    if idx != -1:
        return idx
    
    if not fuzzy:
        return None
    
    # Fuzzy matching using sliding window
    span_len = len(span_text)
    best_match_idx = None
    best_score = threshold
    
    for i in range(len(transcript) - span_len + 1):
        window = transcript[i:i + span_len]
        ratio = SequenceMatcher(None, window, span_text).ratio()
        
        if ratio > best_score:
            best_score = ratio
            best_match_idx = i
    
    return best_match_idx


def get_word_index_at_position(
    word_timestamps: List[Dict],
    char_position: int,
    transcript_prefix: str
) -> Optional[int]:
    """
    Find word index that contains the character position.
    
    Args:
        word_timestamps: List of word timestamp dicts
        char_position: Character position in transcript
        transcript_prefix: The transcript up to this point (for validation)
        
    Returns:
        Index in word_timestamps list, or None if not found
    """
    char_count = 0
    
    for i, word_data in enumerate(word_timestamps):
        word_text = word_data.get("word", "")
        word_len = len(word_text)
        
        if char_count <= char_position < char_count + word_len:
            return i
        
        # Add space between words
        char_count += word_len + 1
    
    return None


def map_spans_to_timestamps(
    transcript: str,
    spans: List[Span],
    word_timestamps: List[Dict]
) -> List[SpanWithTimestamp]:
    """
    Map LLM span text to audio timestamps.
    
    Args:
        transcript: Full transcript text
        spans: List of Span objects from LLM
        word_timestamps: List of word timestamp dicts from audio_analysis
        
    Returns:
        List of SpanWithTimestamp objects with audio locations
    """
    timestamped_spans = []
    transcript_lower = transcript.lower()
    
    for span in spans:
        span_text = span.text.lower().strip()
        
        # Find span position in transcript
        start_idx = find_span_in_transcript(
            transcript_lower,
            span_text,
            fuzzy=True,
            threshold=0.75
        )
        
        if start_idx is None:
            logger.debug(f"Could not locate span: {span.text}")
            continue
        
        # Find corresponding word indices
        word_start_idx = get_word_index_at_position(
            word_timestamps,
            start_idx,
            transcript[:start_idx]
        )
        
        if word_start_idx is None:
            logger.debug(f"Could not map span to word timestamps: {span.text}")
            continue
        
        # Count words in span
        span_word_count = len(span_text.split())
        word_end_idx = min(
            word_start_idx + span_word_count - 1,
            len(word_timestamps) - 1
        )
        
        # Get timestamps
        start_time = word_timestamps[word_start_idx].get("start", 0.0)
        end_time = word_timestamps[word_end_idx].get("end", start_time)
        
        # Convert to MM:SS format
        start_min, start_sec = divmod(int(start_time), 60)
        end_min, end_sec = divmod(int(end_time), 60)
        timestamp_mmss = f"{start_min}:{start_sec:02d}-{end_min}:{end_sec:02d}"
        
        timestamped_spans.append(SpanWithTimestamp(
            text=span.text,
            label=span.label,
            start_sec=round(start_time, 2),
            end_sec=round(end_time, 2),
            timestamp_mmss=timestamp_mmss
        ))
    
    return sorted(timestamped_spans, key=lambda x: x.start_sec)
