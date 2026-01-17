from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from openai import OpenAI
import json


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

IMPORTANT BEHAVIOR CHANGE:
- If rewording is present, annotate paraphrase.
- If vocabulary is more precise than casual speech, annotate advanced_vocabulary.
- Use MEDIUM confidence when unsure, not omission.

GLOBAL JUDGMENTS:
- listener_effort_level:
  low    = effortless to follow
  medium = occasional effort
  high   = frequent effort / reprocessing

- flow_control_level:
  stable   = consistent pacing
  mixed    = uneven but manageable
  unstable = erratic / broken rhythm

- overall_clarity_score (1–5):
  5 = extremely clear, effortless
  3 = generally clear, some strain
  1 = hard to follow

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

Return ONLY valid JSON.
"""


# ======================================================
# EXTRACTION
# ======================================================

def extract_llm_annotations(
    raw_transcript: str,
    speech_context: str = "conversational"
) -> LLMSpeechAnnotations:

    client = OpenAI()

    payload = {
        "raw_transcript": raw_transcript,
        "speech_context": speech_context,
    }

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

    return response.output_parsed


# ======================================================
# AGGREGATION (COMPATIBLE WITH EXISTING SCORER)
# ======================================================

def aggregate_llm_metrics(llm: LLMSpeechAnnotations) -> dict:
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
