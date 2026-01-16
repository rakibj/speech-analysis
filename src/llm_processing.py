from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import List, Literal
from openai import OpenAI
import json

NonNegativeInt = Annotated[int, Field(ge=0)]
Ratio01 = Annotated[float, Field(ge=0.0, le=1.0)]

class Span(BaseModel):
    text: str
    label: Literal[
        "meaning_blocking_grammar_error",
        "grammar_error",
        "word_choice_error",
        "coherence_break",
        "complex_structure",
        "advanced_vocabulary",
    ]

class LLMSpeechAnnotations(BaseModel):
    topic_relevance: bool

    coherence_breaks: List[Span]

    word_choice_errors: List[Span]
    advanced_vocabulary: List[Span]

    complex_structures_attempted: List[Span]
    complex_structures_accurate: List[Span]

    grammar_errors: List[Span]
    meaning_blocking_grammar_errors: List[Span]

system_prompt = """
You are a deterministic annotation engine for spoken English evaluation.

Your task:
- Identify and MARK spans in the transcript.
- Do NOT compute totals, counts, or ratios.
- Do NOT explain reasoning.
- Do NOT infer intent beyond the transcript.
- If unsure, DO NOT annotate the span.

STRICT RULES:
- Annotate ONLY what is clearly present.
- If uncertain, omit the annotation.
- Use the LOWEST reasonable interpretation.
- Return ONLY valid JSON matching the schema.
- No markdown. No comments. No extra keys.

DEFINITIONS:
- coherence_breaks: Moments where the speaker abandons an idea or makes an illogical jump.
- topic_relevance: True if the response addresses the prompt.
- word_choice_errors: Incorrect or inappropriate word choice (not grammar).
- advanced_vocabulary: Correctly used higher-level words (Band 7+).
- complex_structures_attempted: Attempts at conditionals, relatives, passives, modals, subordination.
- complex_structures_accurate: Subset of attempted structures that are correct.
- grammar_errors: Any grammatical error.
- meaning_blocking_grammar_errors: Meaning-blocking grammar errors are ONLY those that: Make the sentence unintelligible OR Change the core meaning OR Prevent understanding without rereading. Number agreement errors alone are NOT meaning-blocking. Preposition redundancy alone is NOT meaning-blocking.


SPAN RULES:
- Each span must be ATOMIC.
- Do NOT merge multiple issues into one span.
- A span must be the shortest phrase that independently shows the issue.
- Never include conjunctions like "and then", "so", "because" unless required.
- If a span qualifies for multiple labels, assign ONLY the highest-precedence label.
- Do NOT duplicate spans across categories.

LABEL PRECEDENCE (highest → lowest):
1. Meaning Blocking Grammar Error
2. Grammar Error
3. Word Choice Error
4. Coherence Break
5. Complex Structure
6. Advanced Vocabulary

IMPORTANT:
- A span must include the exact text excerpt from the transcript.
- Do NOT include timestamps or character offsets.
- The text must appear verbatim in the transcript.
- If unsure whether something qualifies, do NOT annotate it.
"""

def extract_llm_annotations(raw_transcript: str, speech_context: str = "conversational") -> LLMSpeechAnnotations:
    
    context = {
        "raw_transcript": raw_transcript,
        "speech_context": speech_context,
    }

    prompt_text = json.dumps(
        context,
        ensure_ascii=False,
        indent=2
    )

    client = OpenAI()
    prompt_text = json.dumps(context, ensure_ascii=False)
    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_text},
        ],
        temperature=0.0,      # 🔒 critical
        top_p=1.0,            # 🔒 critical
        text_format=LLMSpeechAnnotations,
    )

    llm_result: LLMSpeechAnnotations = response.output_parsed

    return llm_result

def aggregate_llm_metrics(llm_result) -> dict:
    """
    Convert span-based LLM annotations into scalar metrics.
    """

    grammar_error_count = len(llm_result.grammar_errors)
    meaning_blocking_count = len(llm_result.meaning_blocking_grammar_errors)

    meaning_blocking_error_ratio = (
        meaning_blocking_count / grammar_error_count
        if grammar_error_count > 0
        else 0.0
    )

    return {
        "coherence_breaks": len(llm_result.coherence_breaks),
        "topic_relevance": llm_result.topic_relevance,

        "word_choice_errors": len(llm_result.word_choice_errors),
        "advanced_vocabulary_count": len(llm_result.advanced_vocabulary),

        "complex_structures_attempted": len(llm_result.complex_structures_attempted),
        "complex_structures_accurate": len(llm_result.complex_structures_accurate),

        "grammar_errors": grammar_error_count,
        "meaning_blocking_error_ratio": round(meaning_blocking_error_ratio, 3),
    }

def analyze_llm_metrics(
    raw_transcript: str,
    speech_context: str = "conversational"
) -> dict:
    """
    Analyze speech using LLM and return aggregated metrics.
    """
    llm_result = extract_llm_annotations(raw_transcript, speech_context)
    llm_metrics = aggregate_llm_metrics(llm_result)
    return llm_metrics