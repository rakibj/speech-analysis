# Advanced Confidence & Timestamped Rubric Feedback

## 1. Additional Factors Affecting Confidence

Beyond criterion alignment, several factors can affect score reliability:

### Factor 1: Sample Duration ⏱️
```
Confidence multiplier:
- < 2 min audio: 0.70x (too short, metrics unreliable)
- 2-3 min audio: 0.85x (borderline)
- 3-5 min audio: 0.95x (good)
- > 5 min audio: 1.0x (optimal)
```

**Why:** Longer samples provide more stable measurements for WPM, pause patterns, vocabulary range.

### Factor 2: Metric Certainty (Low-Confidence Word Ratio) 🎯
```
Confidence multiplier:
- low_confidence_ratio < 0.05: 1.0x (clear audio)
- low_confidence_ratio 0.05-0.10: 0.95x (minor unclear words)
- low_confidence_ratio 0.10-0.15: 0.85x (many unclear words)
- low_confidence_ratio > 0.15: 0.70x (significant audio issues)
```

**Why:** If speech-to-text struggled (many words <0.7 confidence), pronunciation score is less reliable.

**Available in metrics:**
```json
{
  "mean_word_confidence": 0.923,
  "low_confidence_ratio": 0.086,  // ← USE THIS
  "audio_duration_sec": 122.86
}
```

### Factor 3: LLM Certainty (Span Annotation Agreement) 🤖
```
Confidence multiplier based on LLM span agreement:
- High agreement (>80% spans in same category): 1.0x
- Medium agreement (60-80% spans consistent): 0.90x
- Low agreement (<60% spans scattered): 0.75x
```

**Why:** If LLM findings don't cluster consistently (e.g., flagging 20 different error types), the assessment is less reliable.

### Factor 4: Score Proximity to Thresholds 📊
```
Confidence adjustment:
- Score far from threshold (e.g., 7.0 ± 1.0): +0.05
- Score on threshold boundary (e.g., 6.0, 7.0, 8.0 exact): -0.05
```

**Why:** Boundary scores (exactly 6.5, 7.0) are more sensitive to small changes than scores in the middle (7.2, 7.7).

### Factor 5: Gaming Detection Flags 🚩
```
Confidence reduction if:
- register_mismatch >= 2: -0.15 (forced vocabulary)
- flow_unstable = true: -0.10 (erratic pattern)
- listener_effort_high = true: -0.10 (hard to follow)
- topic_relevance = false: -0.20 (off-topic, very unreliable)
```

**Why:** When system detects gaming attempts, confidence in the score drops.

### Factor 6: Criterion Coherence (Beyond Variance) 🔗
```
Two types of incoherence:

Type A - Simple variance:
  All criteria 6.0-6.5: Coherent (low variance)

Type B - Extreme mismatch:
  Fluency 8.5, Grammar 5.5: Incoherent
  (Can speaker be fluent but not control grammar? Unlikely)
  
Confidence multiplier:
- Coherent profiles: 1.0x
- Slightly mismatched: 0.90x
- Extremely mismatched: 0.70x
```

**How to detect:**
```python
# Fluency is strongly correlated with Grammar
# If fluency=8.5 but grammar=5.5, something is off

def detect_extreme_mismatch(fluency, pron, lexical, grammar):
    """Flag physically impossible combinations."""
    if fluency > 7.5 and grammar < 6.0:
        return True  # Unlikely
    if pron > 7.5 and mean_word_confidence < 0.85:
        return True  # Inconsistent
    if lexical > 8.0 and vocab_richness < 0.4:
        return True  # Impossible
    return False
```

---

## 2. Implementing Comprehensive Confidence

### Code Structure

```python
def calculate_confidence_score(
    metrics: Dict,
    band_scores: Dict,  # {fluency, pron, lexical, grammar}
    llm_data: Dict,      # LLM annotations
    audio_analysis: Dict # Full raw analysis
) -> Dict:
    """Calculate confidence with all 6 factors."""
    
    confidence = 1.0
    factors = {}
    
    # Factor 1: Sample Duration
    duration = metrics.get("audio_duration_sec", 0)
    duration_mult = calculate_duration_multiplier(duration)
    factors["duration"] = {
        "value": duration,
        "multiplier": duration_mult,
        "reason": "Longer samples = more stable metrics"
    }
    confidence *= duration_mult
    
    # Factor 2: Low-Confidence Word Ratio
    low_conf_ratio = metrics.get("low_confidence_ratio", 0)
    certainty_mult = calculate_certainty_multiplier(low_conf_ratio)
    factors["audio_clarity"] = {
        "value": low_conf_ratio,
        "multiplier": certainty_mult,
        "reason": "High ratio = audio quality issues"
    }
    confidence *= certainty_mult
    
    # Factor 3: LLM Span Consistency
    span_consistency = calculate_span_consistency(llm_data)
    consistency_mult = calculate_consistency_multiplier(span_consistency)
    factors["llm_consistency"] = {
        "value": span_consistency,
        "multiplier": consistency_mult,
        "reason": "Scattered annotations = less reliable"
    }
    confidence *= consistency_mult
    
    # Factor 4: Score Boundary Proximity
    overall_score = band_scores["overall"]
    boundary_adj = calculate_boundary_adjustment(overall_score)
    factors["boundary_proximity"] = {
        "value": overall_score,
        "adjustment": boundary_adj,
        "reason": "Scores on .0/.5 boundaries less stable"
    }
    confidence += boundary_adj
    
    # Factor 5: Gaming Detection Penalties
    gaming_penalty = calculate_gaming_penalty(llm_data)
    factors["gaming_detection"] = {
        "penalty": gaming_penalty,
        "reason": "Gaming attempts detected"
    }
    confidence -= gaming_penalty
    
    # Factor 6: Criterion Coherence
    coherence_check = detect_extreme_mismatch(
        band_scores["fluency"],
        band_scores["pronunciation"],
        band_scores["lexical"],
        band_scores["grammar"]
    )
    coherence_adj = -0.15 if coherence_check else 0.0
    factors["criterion_coherence"] = {
        "mismatch_detected": coherence_check,
        "adjustment": coherence_adj,
        "reason": "Physically impossible criterion combination"
    }
    confidence += coherence_adj
    
    # Clamp to 0.0-1.0
    confidence = max(0.0, min(1.0, confidence))
    
    return {
        "overall_confidence": round(confidence, 2),
        "factor_breakdown": factors,
        "confidence_category": categorize_confidence(confidence),
        "recommendation": generate_confidence_recommendation(confidence)
    }

def categorize_confidence(score: float) -> str:
    """Categorize confidence for user display."""
    if score >= 0.95:
        return "VERY_HIGH - Highly reliable score"
    elif score >= 0.85:
        return "HIGH - Reliable with minor caveats"
    elif score >= 0.75:
        return "MODERATE - General reliability, some uncertainty"
    elif score >= 0.60:
        return "LOW - Significant uncertainty, review recommended"
    else:
        return "VERY_LOW - Score unreliable, retest recommended"

def generate_confidence_recommendation(score: float) -> str:
    """Generate actionable recommendation."""
    if score >= 0.90:
        return "No action needed. Score is reliable."
    elif score >= 0.80:
        return "Score is generally reliable. Consider longer sample for verification."
    elif score >= 0.70:
        return "Score has moderate reliability. Audio quality or duration may be affecting results."
    elif score >= 0.60:
        return "Low confidence. Recommend retesting with 5+ minutes of clear audio."
    else:
        return "Very low confidence. Score unreliable. Retest required with better audio conditions."
```

### Output Format

```json
{
  "overall_band": 8.0,
  "band_scores": {
    "fluency": 8.5,
    "pronunciation": 8.0,
    "lexical": 8.0,
    "grammar": 7.5
  },
  "confidence": {
    "overall": 0.92,
    "category": "VERY_HIGH - Highly reliable score",
    "factors": {
      "duration": {
        "value_sec": 122.86,
        "multiplier": 1.0,
        "impact": "Optimal sample length ✓"
      },
      "audio_clarity": {
        "low_confidence_ratio": 0.086,
        "multiplier": 0.95,
        "impact": "Minor audio quality issues"
      },
      "llm_consistency": {
        "agreement_pct": 0.88,
        "multiplier": 1.0,
        "impact": "LLM findings are consistent ✓"
      },
      "boundary_proximity": {
        "distance_from_boundary": 0.5,
        "adjustment": 0.0,
        "impact": "Score not on boundary ✓"
      },
      "gaming_detection": {
        "flags_raised": 0,
        "penalty": 0.0,
        "impact": "No gaming detected ✓"
      },
      "criterion_coherence": {
        "mismatch_detected": false,
        "adjustment": 0.0,
        "impact": "Criteria logically aligned ✓"
      }
    },
    "recommendation": "No action needed. Score is reliable."
  }
}
```

---

## 3. Timestamped Rubric-Based Feedback (SEGMENT EXTRACTION)

**YES! This is very feasible.** The LLM already extracts `Span` objects with `text`, which we can map to timestamps.

### Current LLM Output Structure

```python
class Span(BaseModel):
    text: str           # "were getting iPhones"
    label: str          # "advanced_vocabulary" | "grammar_error" | etc.
```

### Enhancement: Add Timestamp Mapping

```python
class SpanWithTimestamp(BaseModel):
    text: str
    label: str
    start_sec: float    # When this span starts
    end_sec: float      # When this span ends
    timestamp_mmss: str # Human-readable: "0:45-0:52"
```

### Implementation Approach

**Step 1: Create span-to-timestamp mapper**

```python
def map_spans_to_timestamps(
    transcript: str,
    spans: List[Span],
    word_timestamps: List[Dict]  # from words_timestamps_raw
) -> List[SpanWithTimestamp]:
    """Map LLM span text to word timestamps."""
    
    timestamped_spans = []
    
    for span in spans:
        span_text = span.text.lower().strip()
        
        # Find the span in the transcript
        # Use fuzzy matching (account for minor differences)
        start_idx = find_span_in_transcript(
            transcript.lower(),
            span_text,
            fuzzy=True
        )
        
        if start_idx is None:
            continue  # Skip if can't find
        
        # Count words in span
        span_word_count = len(span_text.split())
        
        # Find corresponding word indices in timestamp list
        # (matches based on position in transcript)
        word_start_idx = get_word_index_at_position(
            word_timestamps,
            start_idx
        )
        
        if word_start_idx is None:
            continue
        
        # Get end timestamp (word_start_idx + span_word_count)
        word_end_idx = word_start_idx + span_word_count - 1
        
        if word_end_idx >= len(word_timestamps):
            word_end_idx = len(word_timestamps) - 1
        
        start_time = word_timestamps[word_start_idx]["start"]
        end_time = word_timestamps[word_end_idx]["end"]
        
        timestamped_spans.append(SpanWithTimestamp(
            text=span.text,
            label=span.label,
            start_sec=round(start_time, 2),
            end_sec=round(end_time, 2),
            timestamp_mmss=f"{int(start_time)//60}:{int(start_time)%60:02d}-"
                          f"{int(end_time)//60}:{int(end_time)%60:02d}"
        ))
    
    return sorted(timestamped_spans, key=lambda x: x.start_sec)
```

**Step 2: Group spans by rubric category**

```python
def group_spans_by_rubric(
    timestamped_spans: List[SpanWithTimestamp]
) -> Dict[str, List[SpanWithTimestamp]]:
    """Group timestamped spans by IELTS rubric category."""
    
    grouped = {
        "grammar": [],
        "lexical": [],
        "fluency": [],
        "pronunciation": []
    }
    
    rubric_mapping = {
        # Grammar category
        "meaning_blocking_grammar_error": "grammar",
        "grammar_error": "grammar",
        "clause_completion_issue": "grammar",
        
        # Lexical category
        "advanced_vocabulary": "lexical",
        "idiomatic_or_collocational_use": "lexical",
        "word_choice_error": "lexical",
        
        # Fluency/Coherence category
        "coherence_break": "fluency",
        
        # Complex structures
        "complex_structure": "grammar",
        "complex_structures_attempted": "grammar",
        "complex_structures_accurate": "grammar",
        
        # Pronunciation (note: mostly from STT confidence)
        # (no LLM spans for pronunciation, see below)
    }
    
    for span in timestamped_spans:
        category = rubric_mapping.get(span.label, "other")
        if category in grouped:
            grouped[category].append(span)
    
    return grouped
```

**Step 3: Build rubric-specific feedback with segments**

```python
def build_rubric_feedback_with_segments(
    metrics: Dict,
    llm_data: Dict,
    word_timestamps: List[Dict],
    transcript: str
) -> Dict:
    """Generate feedback grouped by rubric with timestamped segments."""
    
    # Map LLM spans to timestamps
    timestamped_spans = map_spans_to_timestamps(
        transcript,
        llm_data["all_spans"],  # All Span objects from LLM
        word_timestamps
    )
    
    # Group by rubric category
    grouped = group_spans_by_rubric(timestamped_spans)
    
    # Also extract pronunciation issues from low-confidence words
    pronunciation_issues = extract_pronunciation_issues(
        word_timestamps,
        threshold=0.7
    )
    
    return {
        "fluency_coherence": {
            "band_score": 8.5,
            "descriptor": "Fluent with only very occasional repetition...",
            "issues": {
                "coherence_breaks": [
                    {
                        "segment": "was getting iPhones, which was ridiculous",
                        "start_sec": 15.2,
                        "end_sec": 19.8,
                        "timestamp": "0:15-0:19",
                        "issue_type": "coherence_break",
                        "description": "Abrupt topic shift without transition",
                        "feedback": "Connect ideas with transitional phrases"
                    }
                ],
                "clause_issues": [],
                "flow_notes": "Generally smooth flow with natural pauses"
            },
            "highlights": []
        },
        "pronunciation": {
            "band_score": 8.0,
            "descriptor": "Uses wide range of phonological features...",
            "issues": {
                "unclear_words": [
                    {
                        "word": "year",
                        "segment": "when I was in year six",
                        "start_sec": 5.02,
                        "end_sec": 5.18,
                        "timestamp": "0:05",
                        "confidence": 0.71,
                        "description": "Unclear pronunciation detected",
                        "feedback": "Enunciate more clearly with emphasis"
                    },
                    {
                        "word": "six",
                        "segment": "in year six",
                        "start_sec": 5.18,
                        "end_sec": 5.62,
                        "timestamp": "0:05",
                        "confidence": 0.74,
                        "description": "Slightly unclear pronunciation",
                        "feedback": "Slower enunciation would help"
                    }
                ],
                "rhythm_notes": "Overall rhythm is natural and sustained"
            },
            "highlights": []
        },
        "lexical_resource": {
            "band_score": 8.5,
            "descriptor": "Wide resource, readily used to discuss all topics...",
            "issues": {
                "word_choice_errors": [
                    {
                        "word": "retro",
                        "segment": "the phone had a call retro design",
                        "start_sec": 8.1,
                        "end_sec": 8.5,
                        "timestamp": "0:08-0:08",
                        "issue_type": "word_choice_error",
                        "description": "Incorrect word choice (should be 'cute retro')",
                        "feedback": "More careful adjective selection"
                    }
                ],
                "highlights": {
                    "advanced_vocabulary": [
                        {
                            "word": "grubby",
                            "segment": "grubby, cutting edge iPhones",
                            "start_sec": 18.5,
                            "end_sec": 19.2,
                            "timestamp": "0:18-0:19",
                            "category": "sophisticated_descriptor",
                            "feedback": "Excellent use of vivid descriptive vocabulary"
                        },
                        {
                            "word": "cutting edge",
                            "segment": "cutting edge iPhones with touch screens",
                            "start_sec": 19.2,
                            "end_sec": 22.1,
                            "timestamp": "0:19-0:22",
                            "category": "idiomatic_use",
                            "feedback": "Natural and contextually appropriate idiom"
                        },
                        {
                            "word": "aspect",
                            "segment": "I kind of missed that aspect",
                            "start_sec": 35.2,
                            "end_sec": 36.1,
                            "timestamp": "0:35-0:36",
                            "category": "sophisticated_abstract_noun",
                            "feedback": "Precise vocabulary for abstract concept"
                        }
                    ]
                }
            }
        },
        "grammatical_accuracy": {
            "band_score": 7.5,
            "descriptor": "Range of structures flexibly used...",
            "issues": {
                "grammar_errors": [
                    {
                        "segment": "And so I loved my phone so much",
                        "start_sec": 10.2,
                        "end_sec": 13.5,
                        "timestamp": "0:10-0:13",
                        "issue_type": "grammar_error",
                        "description": "Starting with 'And' is informal (minor)",
                        "severity": "low",
                        "feedback": "Avoid starting sentences with 'And' in formal speaking"
                    }
                ],
                "meaning_blocking_errors": [],
                "complex_structures": [
                    {
                        "segment": "I think that if I had my time again, I would have kept my original Nokia",
                        "start_sec": 42.1,
                        "end_sec": 47.8,
                        "timestamp": "0:42-0:47",
                        "structure_type": "conditional_past",
                        "accuracy": "accurate",
                        "feedback": "Excellent use of complex conditional structure"
                    },
                    {
                        "segment": "I kind of miss my phone because I think it was really nice to be able to focus",
                        "start_sec": 28.5,
                        "end_sec": 35.2,
                        "timestamp": "0:28-0:35",
                        "structure_type": "nested_clauses",
                        "accuracy": "accurate",
                        "feedback": "Complex sentence effectively constructed"
                    }
                ]
            }
        }
    }
```

### Output JSON Example

```json
{
  "overall_band": 8.0,
  "feedback": {
    "fluency_coherence": {
      "band": 8.5,
      "issues": [
        {
          "type": "coherence_break",
          "description": "Abrupt shift without connector",
          "segment": "was getting iPhones, which was ridiculous",
          "timestamps": {
            "start_sec": 15.2,
            "end_sec": 19.8,
            "display": "0:15-0:19"
          },
          "feedback": "Use transitional phrases like 'however', 'on the other hand'"
        }
      ]
    },
    "pronunciation": {
      "band": 8.0,
      "issues": [
        {
          "type": "unclear_word",
          "word": "year",
          "segment": "when I was in year six",
          "timestamps": {
            "start_sec": 5.02,
            "end_sec": 5.18,
            "display": "0:05"
          },
          "confidence_score": 0.71,
          "feedback": "Enunciate with more force on the vowel sound"
        }
      ]
    },
    "lexical_resource": {
      "band": 8.5,
      "issues": [
        {
          "type": "word_choice_error",
          "word": "retro",
          "segment": "the phone had a call retro design",
          "timestamps": {
            "start_sec": 8.1,
            "end_sec": 8.5,
            "display": "0:08"
          },
          "feedback": "Use 'cute retro' instead"
        }
      ],
      "highlights": [
        {
          "type": "advanced_vocabulary",
          "word": "grubby",
          "segment": "grubby, cutting edge iPhones",
          "timestamps": {
            "start_sec": 18.5,
            "end_sec": 19.2,
            "display": "0:18-0:19"
          },
          "feedback": "Excellent vivid descriptor"
        },
        {
          "type": "idiomatic_use",
          "phrase": "cutting edge",
          "segment": "cutting edge iPhones with touch screens",
          "timestamps": {
            "start_sec": 19.2,
            "end_sec": 22.1,
            "display": "0:19-0:22"
          },
          "feedback": "Natural, contextually appropriate"
        }
      ]
    },
    "grammar": {
      "band": 7.5,
      "issues": [
        {
          "type": "grammar_error",
          "segment": "And so I loved my phone so much",
          "timestamps": {
            "start_sec": 10.2,
            "end_sec": 13.5,
            "display": "0:10-0:13"
          },
          "severity": "low",
          "feedback": "Avoid sentence-initial 'And' in formal contexts"
        }
      ],
      "highlights": [
        {
          "type": "complex_structure",
          "structure": "Conditional past (if...would have)",
          "segment": "If I had my time again, I would have kept my original Nokia",
          "timestamps": {
            "start_sec": 42.1,
            "end_sec": 47.8,
            "display": "0:42-0:47"
          },
          "accuracy": "accurate",
          "feedback": "Excellent control of complex grammar"
        }
      ]
    }
  }
}
```

---

## 4. Implementation Summary

### Two-Part Implementation

**Part A: Confidence Scoring** (2-3 hours)
- Add 6 confidence factors
- Implement multipliers and adjustments
- Add to band score output
- Update band_results files

**Part B: Timestamped Rubric Feedback** (3-4 hours)
- Create span-to-timestamp mapper
- Group spans by rubric category
- Extract pronunciation issues from word confidence
- Rebuild feedback generation with segments
- Update band_results with timestamped feedback

### Files to Modify

1. `src/core/ielts_band_scorer.py`
   - Add `calculate_confidence_score()` method
   - Update `score_overall_with_feedback()` to include confidence
   - Add factor calculation helpers

2. `src/core/llm_processing.py`
   - Add `SpanWithTimestamp` Pydantic model
   - Add `map_spans_to_timestamps()` function

3. `src/core/metrics.py`
   - Add `extract_issue_timestamps()` function
   - Add span grouping logic

4. `src/core/analyze_band.py`
   - Update output to include timestamped feedback
   - Update to include confidence factor breakdown

### Benefits

✅ **Confidence Scores:**
- Users understand score reliability
- Flags borderline cases for review
- Transparent uncertainty quantification
- Gaming attempts have lower confidence

✅ **Timestamped Rubric Feedback:**
- Users can replay problem areas
- Feedback is actionable (click to hear)
- Linked directly to audio timestamps
- Professional, detailed assessment

✅ **Both Together:**
- Complete transparency into scoring
- High-quality feedback for remediation
- Production-ready system
- Maintains 100% determinism
