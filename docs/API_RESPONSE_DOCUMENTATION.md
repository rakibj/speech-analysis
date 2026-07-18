# Speech Analysis API - Response Data Documentation

**Version:** 1.2  
**Last Updated:** January 24, 2026  
**Status:** Complete with `/analyze-fast` Endpoint + LLM Integration + Structured Per-Rubric Feedback

---

## 🚀 Quick Start for Frontend Developers

**New to the API?** Start here:

1. **Choose Your Endpoint:**
   - Want detailed feedback? Use `/api/direct/v1/analyze` (20-40 sec)
   - Need quick results? Use `/api/direct/v1/analyze-fast` (5-10 sec)

2. **Submit Audio:**

   ```bash
   POST /api/direct/v1/analyze
   Content-Type: multipart/form-data

   file: [audio file]
   speech_context: "conversational" (optional)
   device: "cpu" (optional)
   ```

3. **Get Job ID:** Receive `job_id` immediately

   ```json
   { "job_id": "abc-123", "status": "queued" }
   ```

4. **Poll Results:**

   ```bash
   GET /api/direct/v1/result/{job_id}?detail=feedback
   ```

5. **Display Results:** Show band scores, feedback, and metrics

**See [Endpoint Comparison](#quick-endpoint-comparison) to choose between full and fast analysis.**

---

## Table of Contents

1. [Quick Start for Frontend Developers](#-quick-start-for-frontend-developers)
2. [API Endpoints](#api-endpoints)
3. [Quick Endpoint Comparison](#quick-endpoint-comparison)
4. [Overview](#overview)
5. [Response Structure](#response-structure)
6. [Response Tiers](#response-tiers)
7. [Base Response Fields](#base-response-fields)
8. [Fast Mode Response Fields](#fast-mode-response-fields-analyzefast)
9. [Optional Feedback Tier Fields](#optional-feedback-tier-fields)
10. [Optional Full Tier Fields](#optional-full-tier-fields)
11. [Data Types & Ranges](#data-types--ranges)
12. [Integration Guide for Frontend Developers](#integration-guide-for-frontend-developers)
13. [Field Validation & Type Safety](#field-validation--type-safety)
14. [Examples](#examples)
15. [Usage Guide for Frontend](#usage-guide-for-frontend)
16. [Important Notes](#important-notes)
17. [Error Handling Guide](#error-handling-guide)
18. [Version History](#version-history)

---

## API Endpoints

### Available Endpoints

#### 1. `/api/direct/v1/analyze` (POST) - Full Analysis

**Base URL:** `http://localhost:8000/api/direct/v1/analyze`

Performs comprehensive speech analysis with all features enabled.

**Features:**

- Wav2Vec2 filler detection
- LLM semantic analysis
- Full grammatical and vocabulary assessment
- All metrics calculated

**Processing Time:** 20-40 seconds per minute of audio

**Parameters:**

- `file` (UploadFile) - Audio file to analyze [required]
- `speech_context` (SpeechContextEnum) - Type of speech [optional, default: "conversational"]
  - Values: `"conversational"`, `"narrative"`, `"presentation"`, `"interview"`
- `device` (string) - Processing device [optional, default: "cpu"]
  - Values: `"cpu"`, `"cuda"`

**Response:**

```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "message": "Analysis started. Poll /api/direct/v1/result/{job_id} for results"
}
```

Then poll `/api/direct/v1/result/{job_id}` with optional `detail` parameter:

- No parameter: Base response (fastest)
- `?detail=feedback`: Base + feedback tier
- `?detail=full`: Base + feedback + full tier

---

#### 2. `/api/direct/v1/analyze-fast` (POST) - Fast Analysis ⚡ NEW

**Base URL:** `http://localhost:8000/api/direct/v1/analyze-fast`

**⚡ FAST MODE - 5-8x speedup for quick feedback**

Lightweight variant for quick assessment with basic metrics.

**What's Skipped:**

- ❌ Wav2Vec2 filler detection (uses Whisper only)
- ❌ LLM annotations & semantic analysis
- ❌ Detailed grammatical analysis
- ❌ Vocabulary sophistication assessment

**What's Included:**

- ✅ Basic WPM calculation
- ✅ Pause frequency detection
- ✅ Word confidence metrics
- ✅ Metrics-only band scoring
- ✅ Whisper transcription

**Use Cases:**

- Quick practice feedback
- Fast progress tracking
- Initial skill assessment
- When full analysis isn't needed

**Processing Time:** 5-10 seconds per minute of audio

**Parameters:** Same as `/analyze`

- `file` (UploadFile) [required]
- `speech_context` (SpeechContextEnum) [optional]
- `device` (string) [optional]

**Response:**

```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "mode": "fast",
  "message": "Fast analysis started. Poll /api/direct/v1/result/{job_id} for results"
}
```

Same polling mechanism as full analysis. Fast response will include reduced/simplified fields.

---

#### 3. `/api/v1/analyze` (POST) - RapidAPI Full Analysis

**Base URL:** RapidAPI Gateway (https://rapidapi.com/...)

Same as direct `/analyze` but requires RapidAPI authentication and gateway headers.

Protections:

- File size limit: 15MB max
- Audio duration: 30 minutes max
- Rate limiting: 100 requests/hour per user
- RapidAPI-only enforcement

---

#### 4. Result Polling: `/api/direct/v1/result/{job_id}` (GET)

Poll for analysis results using the job_id returned from analyze endpoint.

**Parameters:**

- `job_id` (path parameter) - UUID from analyze response [required]
- `detail` (query parameter) - Response detail level [optional]
  - Values: `null` (default), `"feedback"`, `"full"`

**Responses:**

**Still Processing:**

```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "message": "Analysis in progress..."
}
```

**Completed:**

```json
{
  "job_id": "uuid-string",
  "status": "completed",
  ... (response fields based on detail parameter)
}
```

**Error:**

```json
{
  "job_id": "uuid-string",
  "status": "error",
  "error": "Error message describing what went wrong"
}
```

---

## Quick Endpoint Comparison

| Feature               | `/analyze`                           | `/analyze-fast`                   |
| --------------------- | ------------------------------------ | --------------------------------- |
| Processing Speed      | 20-40 sec/min                        | 5-10 sec/min                      |
| Speedup               | Baseline                             | 5-8x faster                       |
| LLM Analysis          | ✅ Full                              | ❌ Skipped                        |
| Filler Detection      | ✅ Wav2Vec2 (accurate)               | ⚠️ Whisper only                   |
| Grammar Analysis      | ✅ Detailed                          | ❌ None                           |
| Vocabulary Assessment | ✅ Full                              | ❌ None                           |
| Band Scoring          | ✅ Metrics + LLM                     | ✅ Metrics only                   |
| Feedback Field        | ✅ Detailed                          | ❌ Null                           |
| Confidence Score      | ✅ High reliability                  | ⚠️ Lower reliability              |
| Ideal Use Case        | Formal assessment, detailed feedback | Quick practice, progress tracking |
| Cost                  | Higher                               | Lower                             |

**TL;DR:** Use `/analyze` for detailed assessment, `/analyze-fast` for quick feedback.

---

## Overview

The Speech Analysis API returns comprehensive IELTS speaking assessment data including:

- **Band Scores** - Overall IELTS band (5.0-9.0) with criterion-specific scores
- **Confidence Metrics** - Assessment reliability and confidence scoring
- **Acoustic Analysis** - Speech metrics (WPM, pauses, variability, vocabulary richness)
- **Statistics** - Word counts, filler percentages, speech characteristics
- **LLM Analysis** - AI-powered findings (grammar errors, coherence, vocabulary)
- **Descriptors** - IELTS band descriptors aligned to actual performance
- **Structured Per-Rubric Feedback** - Clear strengths, weaknesses, and suggestions per criterion (NEW)
- **Detailed Analysis** - Granular breakdown with timestamps and detailed findings (optional tiers)

### Complete Field Availability Matrix

**Which fields are returned for each endpoint and detail level:**

| Field                                                            | Full Analyze (default) | Full + feedback | Full + full | Fast Mode |
| ---------------------------------------------------------------- | ---------------------- | --------------- | ----------- | --------- |
| **Core** (always)                                                |
| job_id, status, engine_version, scoring_config                   | ✅                     | ✅              | ✅          | ✅        |
| **Scores** (always)                                              |
| overall_band, criterion_bands                                    | ✅                     | ✅              | ✅          | ✅        |
| **Assessment** (always)                                          |
| confidence, descriptors, criterion_descriptors                   | ✅                     | ✅              | ✅          | ✅        |
| **Metrics** (always)                                             |
| statistics, normalized_metrics, speech_quality                   | ✅                     | ✅              | ✅          | ✅        |
| **LLM** (always, but null in fast)                               |
| llm_analysis                                                     | ✅                     | ✅              | ✅          | ❌ null   |
| **Feedback** (detail=feedback or full)                           |
| transcript, grammar_errors, word_choice_errors                   | ❌                     | ✅              | ✅          | ❌        |
| examiner_descriptors, fluency_notes, feedback                    | ❌                     | ✅              | ✅          | ❌        |
| **Full** (detail=full only)                                      |
| word_timestamps, filler_events, content_words                    | ❌                     | ❌              | ✅          | ❌        |
| segment_timestamps, confidence_multipliers, timestamped_feedback | ❌                     | ❌              | ✅          | ❌        |

✅ = Present with data | ❌ = Not returned | `null` = Present but always null

### Response Tiers

All responses include the **base tier** (13 fields). Additional fields are available when requested:

- **Default (no detail parameter):** Base tier only (smallest, fastest)
- **`detail=feedback`:** Base + Feedback tier (transcript, errors, notes, feedback)
- **`detail=full`:** Base + Feedback + Full tier (timestamps, detailed breakdown)

**Note on Fast Mode:** The `/analyze-fast` endpoint returns a simplified response with fewer fields. LLM-derived fields will be `null` or missing. See [Fast Mode Response Fields](#fast-mode-response-fields-analyzefast) for details.

---

## ⚠️ Current Implementation Status

### Full Analysis Mode Fields ✅

**All Fields Implemented:**

- ✅ `overall_band`, `criterion_bands` - Band scores calculated
- ✅ `confidence` - Confidence with detailed factor_breakdown
- ✅ `statistics` - Word counts and filler percentages
- ✅ `normalized_metrics` - All 9 metrics calculated
- ✅ `llm_analysis` - Complete LLM findings
- ✅ `speech_quality` - Word confidence and monotone detection
- ✅ `transcript` - Full transcription (when detail="feedback")
- ✅ `word_timestamps` - All words with timing and confidence (when detail="full")
- ✅ `grammar_errors`, `word_choice_errors` - Error counts with notes (when detail="feedback")
- ✅ `examiner_descriptors`, `fluency_notes` - Feedback generated (when detail="feedback")
- ✅ `descriptors`, `criterion_descriptors` - Extracted from scorer
- ✅ `filler_events` - Generated from word_timestamps (when detail="full")
- ✅ `segment_timestamps` - Generated by grouping words (when detail="full")
- ✅ `confidence_multipliers` - Extracted from confidence breakdown (when detail="full")
- ✅ `feedback` - NEW structured per-rubric feedback (all detail levels)
- ✅ `content_words` - Non-filler words (when detail="full")
- ✅ `engine_version` - Version string (always)
- ✅ `scoring_config` - Configuration metadata (always)

### Fields Currently Returning `null` (Documented)

The following fields are defined in the API contract but currently return `null`:

| Field          | Why Null             | Workaround                               |
| -------------- | -------------------- | ---------------------------------------- |
| `opinions`     | Not generated by LLM | Use `llm_analysis` for detailed findings |
| `benchmarking` | Not implemented      | Manual comparison required               |

### Fast Mode (`/analyze-fast`) Behavior

Fast mode skips expensive operations. Response contains:

| Field                  | Available  | Notes                              |
| ---------------------- | ---------- | ---------------------------------- |
| Base tier fields       | ✅ Yes     | All fields returned                |
| `llm_analysis`         | ❌ Null    | Not calculated in fast mode        |
| `feedback`             | ❌ Null    | Requires LLM analysis              |
| `grammar_errors`       | ❌ Null    | Requires LLM analysis              |
| `word_choice_errors`   | ❌ Null    | Requires LLM analysis              |
| `examiner_descriptors` | ❌ Null    | Requires LLM analysis              |
| `fluency_notes`        | ❌ Null    | Requires LLM analysis              |
| `filler_events`        | ⚠️ Limited | Whisper-based only (less accurate) |
| Timestamps             | ✅ Yes     | All word timestamps included       |
| `normalized_metrics`   | ✅ Yes     | Basic metrics only                 |

**Recommendation:** Use fast mode for quick feedback, full mode for detailed assessment.

---

## Response Structure

### Base Response (Always Included)

```json
{
  "job_id": "string",
  "status": "completed|processing|error",
  "engine_version": "string",
  "scoring_config": {object},
  "overall_band": 6.0,
  "criterion_bands": {object},
  "confidence": {object},
  "descriptors": {object},
  "criterion_descriptors": {object},
  "statistics": {object},
  "normalized_metrics": {object},
  "llm_analysis": {object},
  "speech_quality": {object}
}
```

### Optional Feedback Tier (When detail="feedback" or "full")

```json
{
  "transcript": "string",
  "grammar_errors": {object},
  "word_choice_errors": {object},
  "examiner_descriptors": {object},
  "fluency_notes": "string",
  "feedback": {object}
}
```

### Optional Full Tier (When detail="full")

```json
{
  "word_timestamps": [array],
  "content_words": [array],
  "segment_timestamps": [array],
  "filler_events": [array],
  "benchmarking": {object},
  "confidence_multipliers": {object},
  "timestamped_feedback": {object}
}
```

---

## Base Response Fields

### 1. `job_id` (string)

**Type:** UUID string  
**Example:** `"3c6e75c6-de7d-49de-afbb-7de1452dde2c"`

Unique identifier for the analysis job. Use this to poll for results and track analyses.

---

### 2. `status` (string)

**Type:** Enum - one of: `"processing"`, `"completed"`, `"error"`  
**Example:** `"completed"`

Current state of the analysis:

- `"processing"` - Analysis in progress, poll again in a few seconds
- `"completed"` - Analysis finished, all results available
- `"error"` - Analysis failed, check the error message

---

### 3. `engine_version` (string)

**Type:** Semantic version string  
**Example:** `"0.1.0"`

Version of the analysis engine used. Useful for debugging and tracking which engine was used for scoring.

---

### 4. `scoring_config` (object)

**Type:** Dictionary/Object  
**Example:** `{}`

Configuration metadata used during scoring. May include weighting factors, thresholds, and other scoring parameters.

---

### 5. `overall_band` (float)

**Type:** Float  
**Range:** `[5.0, 9.0]` in 0.5 increments  
**Example:** `6.0`

**The main IELTS speaking band score.** This is the headline result users care about.

Possible values: 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0

Calculation: Average of all four criterion bands, rounded to nearest 0.5

**IELTS Band Descriptors:**

- **9.0** - Expert user
- **8.5** - Very good user
- **8.0** - Good user
- **7.5** - Good user (lower)
- **7.0** - Competent user
- **6.5** - Competent user (lower)
- **6.0** - Competent user (minimal)
- **5.5** - Modest user
- **5.0** - Non-user

---

### 6. `criterion_bands` (object)

**Type:** Dictionary with 4 criteria

```json
{
  "fluency_coherence": 6,
  "pronunciation": 7,
  "lexical_resource": 6,
  "grammatical_range_accuracy": 6
}
```

**Individual band scores for each IELTS criterion.** Each is scored 5.0-9.0 independently.

#### Criterion Definitions:

**`fluency_coherence` (float, [5.0-9.0])**

- How smoothly and naturally the candidate speaks
- Ability to maintain speech without excessive pauses or repetition
- Coherence: ideas are logically connected
- Uses metric: WPM, pause frequency, repetition ratio, hesitation

**`pronunciation` (float, [5.0-9.0])**

- Clarity of word articulation
- Stress patterns and intonation
- Overall intelligibility
- Uses metric: word confidence scores, low confidence ratio

**`lexical_resource` (float, [5.0-9.0])**

- Breadth and depth of vocabulary
- Use of less common words (collocations, phrasal verbs, etc.)
- Appropriateness of word choice
- Uses metric: vocabulary richness, type-token ratio, LLM vocabulary assessment

**`grammatical_range_accuracy` (float, [5.0-9.0])**

- Range of sentence structures used
- Accuracy of grammar
- Error frequency and severity
- Uses metric: sentence complexity, error analysis by LLM

---

### 7. `confidence` (object)

**Type:** Dictionary with confidence breakdown

```json
{
  "overall_confidence": 0.44
}
```

**`overall_confidence` (float, [0.0-1.0])**

Confidence score indicating reliability of the assessment. Combines:

- Audio duration and quality
- Speech clarity (word confidence)
- LLM consistency and agreement
- Score stability across criteria

**Interpretation:**

- **0.9-1.0** - Very high confidence (excellent assessment reliability)
- **0.7-0.9** - High confidence (reliable assessment)
- **0.5-0.7** - Moderate confidence (fair assessment, some uncertainty)
- **0.3-0.5** - Low confidence (assessment should be taken cautiously)
- **0.0-0.3** - Very low confidence (unreliable, retest recommended)

---

### 8. `descriptors` (object)

**Type:** Dictionary with IELTS descriptors for the overall band

```json
{
  "fluency_coherence": "Able to keep going and demonstrates willingness...",
  "pronunciation": "Range of phonological features with variable control...",
  "lexical_resource": "Resource sufficient to discuss topics...",
  "grammatical_range_accuracy": "Mix of structures with limited flexibility..."
}
```

**IELTS band descriptors for the overall band score.** These are the official IELTS descriptions of what the overall band level means.

Each descriptor explains what a speaker at that band level is capable of.

---

### 9. `criterion_descriptors` (object)

**Type:** Dictionary with per-criterion descriptors + LLM enhancements

```json
{
  "fluency_coherence": "Able to keep going and demonstrates willingness. Coherence may be lost due to hesitation. 2 coherence breaks detected.",
  "pronunciation": "Range of phonological features with variable control. Individual words may be mispronounced. 25% of words show low confidence.",
  "lexical_resource": "Resource sufficient to discuss topics. Vocabulary use may be inappropriate. 2 word choice issues detected. 1 advanced vocabulary use noted.",
  "grammatical_range_accuracy": "Mix of structures with limited flexibility. Errors frequent but rarely impede communication. 3 grammar errors identified."
}
```

**Criterion-specific IELTS descriptors ALIGNED to each criterion's actual score (not overall).**

**Key difference from `descriptors`:** Each criterion descriptor is pulled from that criterion's band score, not the overall band. This ensures feedback is realistic and specific.

**LLM Enhancements:** Appended to the base descriptor:

- **Fluency:** Coherence break count, flow instability indicators
- **Pronunciation:** Low confidence word percentage
- **Lexical:** Word choice error count, advanced vocabulary usage count
- **Grammar:** Grammar error count, cascading error notes

**This is what shows users what ACTUALLY happened in their speech, not generic band descriptions.**

---

### 10. `statistics` (object)

**Type:** Dictionary with word/filler statistics

```json
{
  "total_words_transcribed": 163,
  "content_words": 162,
  "filler_words_detected": 1,
  "filler_percentage": 0.61,
  "is_monotone": false
}
```

**Key Statistics:**

**`total_words_transcribed` (integer)**

- Total number of words in the speech (including fillers)
- Range: 1 - unlimited

**`content_words` (integer)**

- Non-filler words spoken
- Formula: `total_words - filler_words`
- Range: 1 - total_words

**`filler_words_detected` (integer)**

- Count of fillers ("um", "uh", "like", "you know", etc.)
- Range: 0 - total_words

**`filler_percentage` (float, [0.0-100.0])**

- Percentage of speech that is fillers
- Formula: `100 * filler_words / total_words`
- **Interpretation:**
  - 0-2% - Excellent (native-like)
  - 2-5% - Good
  - 5-10% - Acceptable
  - 10-20% - Needs improvement
  - 20%+ - Significant problem

**`is_monotone` (boolean)**

- Whether speech lacks prosody/intonation variation
- `true` - Speech is monotone (flat, lacking expression)
- `false` - Normal prosody (natural intonation)

---

### 11. `normalized_metrics` (object)

**Type:** Dictionary with 9 acoustic/linguistic metrics

```json
{
  "wpm": 88.73,
  "long_pauses_per_min": 2.19,
  "fillers_per_min": 2.74,
  "pause_variability": 1.472,
  "speech_rate_variability": 0.317,
  "vocab_richness": 0.537,
  "type_token_ratio": 0.537,
  "repetition_ratio": 0.072,
  "mean_utterance_length": 9.59
}
```

**Fluency & Delivery Metrics:**

**`wpm` (float)**

- **Words Per Minute** - Speech rate
- Range: 40-200
- Interpretation:
  - 150+ - Very fast
  - 110-150 - Natural/fluent
  - 70-110 - Moderate
  - <70 - Slow, hesitant

**`long_pauses_per_min` (float)**

- **Frequency of pauses longer than 1 second**
- Range: 0-20
- Interpretation:
  - 0-1 - Excellent fluency
  - 1-2 - Good fluency
  - 2-3 - Acceptable
  - 3+ - Frequent hesitation

**`fillers_per_min` (float)**

- **Frequency of filler words per minute**
- Range: 0-20
- Interpretation:
  - 0-1 - Excellent
  - 1-3 - Good
  - 3-5 - Acceptable
  - 5+ - Excessive

**`pause_variability` (float)**

- **Standard deviation of pause durations**
- Range: 0-5
- High value (>1.2) = inconsistent pausing (nervous, unsure)
- Low value (<0.5) = consistent pausing (fluent, controlled)

**`speech_rate_variability` (float)**

- **Variability in speaking rate across utterances**
- Range: 0-2
- High value = speech rate changes significantly
- Low value = consistent delivery pace

**Vocabulary Metrics:**

**`vocab_richness` (float)**

- **Type-token ratio (unique words / total words)**
- Range: 0-1
- Interpretation:
  - 0.55+ - Rich, diverse vocabulary
  - 0.45-0.55 - Good vocabulary
  - 0.35-0.45 - Limited vocabulary
  - <0.35 - Very repetitive

**`type_token_ratio` (float)**

- **Unique words / total words ratio**
- Range: 0-1
- Same as `vocab_richness` (calculated from transcript)
- Higher = more varied vocabulary

**`repetition_ratio` (float)**

- **Frequency of repeated words**
- Range: 0-1
- Interpretation:
  - <0.05 - Low repetition (good)
  - 0.05-0.10 - Moderate repetition
  - 0.10-0.20 - High repetition (weak vocabulary)
  - > 0.20 - Excessive repetition

**`mean_utterance_length` (float)**

- **Average words per utterance**
- Range: 0-50
- Interpretation:
  - 12+ - Long, complex utterances (good range)
  - 8-12 - Moderate utterance length
  - 5-8 - Short, choppy utterances
  - <5 - Very basic structures

---

### 12. `llm_analysis` (object)

**Type:** Dictionary with LLM semantic findings

```json
{
  "grammar_error_count": 3,
  "coherence_break_count": 2,
  "word_choice_error_count": 2,
  "advanced_vocabulary_count": 1,
  "flow_instability_present": false,
  "cascading_grammar_failure": false
}
```

**LLM-Based Semantic Analysis - AI findings about speech quality:**

**`grammar_error_count` (integer)**

- Number of grammar errors identified by LLM
- Includes: tense errors, subject-verb agreement, word form errors
- 0 = No errors detected
- 1-3 = Few errors (acceptable for lower bands)
- 3+ = Multiple errors (affecting clarity)

**`coherence_break_count` (integer)**

- Number of times speech becomes incoherent or loses thread
- 0 = Logical flow throughout
- 1-2 = Minor breaks in logic
- 3+ = Significant coherence issues

**`word_choice_error_count` (integer)**

- Inappropriate or incorrect word choices
- Includes: wrong connotation, misused vocabulary
- 0 = Appropriate word choices throughout
- 1-2 = Minor misuses
- 3+ = Frequent inappropriate usage

**`advanced_vocabulary_count` (integer)**

- Uses of sophisticated, advanced vocabulary
- Shows lexical resource strength
- Higher = more impressive vocabulary

**`flow_instability_present` (boolean)**

- Whether speech flow is unstable/hesitant
- Indicates difficulty finding words or organizing thoughts

**`cascading_grammar_failure` (boolean)**

- Whether grammar errors cascade/compound, affecting meaning
- More serious than isolated grammar errors

---

### 13. `speech_quality` (object)

**Type:** Dictionary with speech clarity indicators

```json
{
  "mean_word_confidence": 0.78,
  "low_confidence_ratio": 0.25,
  "is_monotone": false
}
```

**Speech Clarity & Prosody Indicators:**

**`mean_word_confidence` (float, [0.0-1.0])**

- **Average confidence of word recognition** (Whisper model confidence)
- 0.9-1.0 = Crystal clear, easy to understand
- 0.8-0.9 = Clear with minor accent
- 0.7-0.8 = Mostly clear
- 0.6-0.7 = Some unclear words
- <0.6 = Many pronunciation issues

**`low_confidence_ratio` (float, [0.0-1.0])**

- **Percentage of words with low confidence** (confidence < 0.7)
- 0-0.15 = Excellent pronunciation
- 0.15-0.30 = Good pronunciation
- 0.30-0.50 = Acceptable pronunciation
- 0.50+ = Poor pronunciation (many unclear words)

**`is_monotone` (boolean)**

- Whether speech lacks prosody/intonation
- Affects naturalness and listener engagement
- `true` = Flat, lacking expression
- `false` = Natural intonation

---

## Optional Feedback Tier Fields

Available when `detail="feedback"` or `detail="full"`

### 1. `feedback` (object) - NEW!

**Type:** Dictionary with structured per-rubric feedback

```json
{
  "fluency_coherence": {
    "criterion": "Fluency & Coherence",
    "band": 7.0,
    "strengths": [
      "Good fluency - able to sustain speech",
      "Generally smooth delivery with minor pauses"
    ],
    "weaknesses": [],
    "suggestions": [
      "Practice extended speaking (2-3 minutes) on various topics"
    ]
  },
  "pronunciation": {
    "criterion": "Pronunciation",
    "band": 7.5,
    "strengths": [
      "Generally clear pronunciation",
      "Minor accent variations don't affect understanding"
    ],
    "weaknesses": [],
    "suggestions": []
  },
  "lexical_resource": {
    "criterion": "Lexical Resource",
    "band": 7.0,
    "strengths": [
      "Good vocabulary range",
      "Uses 8 advanced items to show sophistication",
      "Includes 3 idiomatic expressions"
    ],
    "weaknesses": [
      "Word choice errors (1) - using wrong words or wrong connotation"
    ],
    "suggestions": [
      "Learn precise word meanings and usage contexts",
      "Use a thesaurus and corpus to check word usage"
    ]
  },
  "grammatical_range_accuracy": {
    "criterion": "Grammatical Range & Accuracy",
    "band": 6.5,
    "strengths": [
      "Adequate grammatical control",
      "Manages basic and some complex structures"
    ],
    "weaknesses": ["Grammar errors found (2) - affects clarity at times"],
    "suggestions": [
      "Review common grammar errors identified in your speech",
      "Study one complex structure per week"
    ]
  },
  "overall": {
    "overall_band": 7.0,
    "summary": "You show good English proficiency with generally fluent speech, adequate range of vocabulary and structures. Focus on expanding lexical range and reducing grammatical errors.",
    "next_band_tips": {
      "focus": "Improve grammar range and accuracy to reach band 7.5",
      "action": "Master complex sentence structures and ensure accurate tense and agreement."
    }
  }
}
```

**Structured, user-friendly feedback** that clearly shows:

**Per-Criterion Feedback (fluency_coherence, pronunciation, lexical_resource, grammatical_range_accuracy):**

**`criterion` (string)**

- Display name of the criterion

**`band` (float)**

- Band score for this specific criterion (5.0-9.0)

**`strengths` (array of strings)**

- What the speaker is doing well in this area
- Positive observations with specific examples
- Backed by actual metrics and LLM analysis
- Examples: "Good fluency - able to sustain speech", "Uses 8 advanced items"

**`weaknesses` (array of strings)**

- Areas that need improvement
- Specific issues identified with counts/metrics
- Data-driven observations
- Examples: "Coherence breaks detected (3)", "Grammar errors (2)", "Low word clarity (35%)"

**`suggestions` (array of strings)**

- Actionable, specific tips for improvement
- Practical steps the speaker can take
- Prioritized for effectiveness
- Examples: "Practice extended speaking on various topics", "Learn 10-15 new advanced words/phrases per week"

**Overall Assessment:**

**`overall_band` (float)**

- Overall IELTS band score (same as top-level `overall_band`)

**`summary` (string)**

- Band-specific performance summary
- Acknowledges strengths and areas to work on
- Motivational and constructive tone
- Contextualizes the band level

**`next_band_tips` (object)**

- **`focus` (string)**: Which criterion to prioritize for next band level
- **`action` (string)**: Specific steps to take to improve

---

**Key Characteristics of Feedback:**

1. **Data-Driven** - All feedback backed by actual metrics and LLM findings
2. **Specific** - Uses numbers (error counts, percentages, item counts)
3. **Actionable** - Provides clear steps to improve
4. **Band-Aware** - Feedback varies based on performance level
5. **Balanced** - Shows both what's good and what needs work
6. **Complete** - All 4 criteria covered + overall summary

---

### 2. `transcript` (string)

**Type:** String  
**Example:** `"I think the weather today is really nice and I enjoyed walking..."`

**Full transcription of the speech** as recognized by the audio model.

---

### 3. `grammar_errors` (object)

**Type:** Object with error details

```json
{
  "count": 3,
  "severity": "high",
  "note": "Found 3 grammar error(s)"
}
```

Summary of identified grammar errors.

---

### 3. `word_choice_errors` (object)

**Type:** Object with vocabulary issue details

```json
{
  "count": 2,
  "note": "Found 2 word choice issue(s)"
}
```

Summary of inappropriate or misused vocabulary.

---

### 4. `examiner_descriptors` (object)

**Type:** Dictionary with examiner-style assessment

Detailed, structured feedback formatted like official IELTS examiner comments.

---

### 5. `fluency_notes` (string)

**Type:** String

**Example:** `"Frequent mid-sentence searches | Speech flow is unstable | High listener effort required"`

High-level fluency assessment notes extracted from LLM analysis.

---

## Optional Full Tier Fields

Available when `detail="full"`

### 1. `word_timestamps` (array)

**Type:** Array of timestamped words

```json
[
  {
    "word": "I",
    "start_sec": 0.0,
    "end_sec": 0.2,
    "duration_sec": 0.2,
    "confidence": 0.95,
    "is_filler": false
  },
  {
    "word": "think",
    "start_sec": 0.2,
    "end_sec": 0.5,
    "duration_sec": 0.3,
    "confidence": 0.92,
    "is_filler": false
  }
]
```

**Complete timeline of all spoken words with precise timing.**

**Field Descriptions:**

- `word` - The recognized word
- `start_sec` - Start time in seconds
- `end_sec` - End time in seconds
- `duration_sec` - Word duration (end - start)
- `confidence` - Recognition confidence (0.0-1.0)
- `is_filler` - Whether this is a filler word (um, uh, like, etc.)

---

### 2. `content_words` (array)

**Type:** Array of non-filler words (same structure as `word_timestamps`)

List of only content words (excluding fillers), with timestamps.

---

### 3. `segment_timestamps` (array)

**Type:** Array of larger speech segments

```json
[
  {
    "text": "I think the weather today is really nice",
    "start_sec": 0.0,
    "end_sec": 8.5,
    "duration_sec": 8.5,
    "avg_word_confidence": 0.9,
    "contains_filler": false
  }
]
```

Speech divided into logical segments/sentences with timings.

---

### 4. `filler_events` (array)

**Type:** Array of detected fillers and disfluencies

```json
[
  {
    "type": "filler",
    "text": "um",
    "start_sec": 3.2,
    "end_sec": 3.5,
    "duration_sec": 0.3,
    "confidence": 0.88
  }
]
```

Timeline of all filler words and hesitations detected.

---

### 5. `benchmarking` (object)

**Type:** Comparative performance data

Percentile rankings and comparisons to similar test-takers.

---

### 6. `confidence_multipliers` (object)

**Type:** Detailed confidence score breakdown

Components that contributed to the overall confidence score.

---

### 7. `timestamped_feedback` (object)

**Type:** Word-level quality assessment

Specific feedback tied to exact timestamps in the speech. Detailed analysis of which parts of the speech had issues.

---

## Data Types & Ranges

### Score Ranges

| Field                        | Type  | Min | Max | Increment | Example |
| ---------------------------- | ----- | --- | --- | --------- | ------- |
| `overall_band`               | float | 5.0 | 9.0 | 0.5       | 6.0     |
| `fluency_coherence`          | float | 5.0 | 9.0 | 0.5       | 6.0     |
| `pronunciation`              | float | 5.0 | 9.0 | 0.5       | 7.0     |
| `lexical_resource`           | float | 5.0 | 9.0 | 0.5       | 6.0     |
| `grammatical_range_accuracy` | float | 5.0 | 9.0 | 0.5       | 6.0     |

### Ratio/Percentage Ranges

| Field                           | Type  | Min | Max   | Interpretation                    |
| ------------------------------- | ----- | --- | ----- | --------------------------------- |
| `confidence.overall_confidence` | float | 0.0 | 1.0   | 0=uncertain, 1=certain            |
| `filler_percentage`             | float | 0.0 | 100.0 | Percent of speech that is fillers |
| `low_confidence_ratio`          | float | 0.0 | 1.0   | Ratio of unclear words            |
| `vocab_richness`                | float | 0.0 | 1.0   | Vocabulary diversity              |
| `type_token_ratio`              | float | 0.0 | 1.0   | Unique word proportion            |
| `repetition_ratio`              | float | 0.0 | 1.0   | Word repetition frequency         |

### Metric Ranges

| Field                     | Type  | Typical Min | Typical Max | Unit            |
| ------------------------- | ----- | ----------- | ----------- | --------------- |
| `wpm`                     | float | 40          | 200         | words/minute    |
| `long_pauses_per_min`     | float | 0           | 20          | pauses/minute   |
| `fillers_per_min`         | float | 0           | 20          | fillers/minute  |
| `pause_variability`       | float | 0           | 5           | std dev         |
| `speech_rate_variability` | float | 0           | 2           | std dev         |
| `mean_utterance_length`   | float | 0           | 50          | words/utterance |

### Count Fields

| Field                       | Type    | Example |
| --------------------------- | ------- | ------- |
| `total_words_transcribed`   | integer | 163     |
| `content_words`             | integer | 162     |
| `filler_words_detected`     | integer | 1       |
| `grammar_error_count`       | integer | 3       |
| `coherence_break_count`     | integer | 2       |
| `word_choice_error_count`   | integer | 2       |
| `advanced_vocabulary_count` | integer | 1       |

---

## Fast Mode Response Fields (`/analyze-fast`)

The `/analyze-fast` endpoint returns a simplified response optimized for speed. Base tier fields are always included, but LLM-dependent fields are omitted.

### Fast Mode Base Response (Always Included)

```json
{
  "job_id": "string",
  "status": "completed|processing|error",
  "engine_version": "string",
  "scoring_config": {object},
  "overall_band": 6.0,
  "criterion_bands": {object},
  "confidence": {object},
  "descriptors": {object},
  "criterion_descriptors": {object},
  "statistics": {object},
  "normalized_metrics": {object},
  "speech_quality": {object}
}
```

### Fields NOT Available in Fast Mode (Always `null`)

| Field                  | Reason                                   |
| ---------------------- | ---------------------------------------- |
| `llm_analysis`         | Skipped - expensive LLM processing       |
| `feedback`             | Depends on LLM analysis                  |
| `grammar_errors`       | Requires LLM semantic analysis           |
| `word_choice_errors`   | Requires LLM vocabulary analysis         |
| `examiner_descriptors` | Generated from LLM findings              |
| `fluency_notes`        | Generated from LLM analysis              |
| `opinions`             | Not calculated in any mode (null always) |
| `benchmarking`         | Not implemented (null always)            |

### Fields WITH Limitations in Fast Mode

**`filler_events` (when detail="full")**

- Only detected via Whisper ASR (no Wav2Vec2)
- Less accurate but faster
- May miss subtle fillers

**`normalized_metrics`**

- Calculated from Whisper output only
- Excludes LLM-based enhancements
- Basic WPM, pauses, and confidence metrics only

### Fast Mode Example Response

```json
{
  "job_id": "abc-123-def",
  "status": "completed",
  "engine_version": "0.1.0",
  "scoring_config": {},
  "overall_band": 6.0,
  "criterion_bands": {
    "fluency_coherence": 6,
    "pronunciation": 7,
    "lexical_resource": 6,
    "grammatical_range_accuracy": 6
  },
  "confidence": {
    "overall_confidence": 0.42
  },
  "descriptors": {
    "fluency_coherence": "Able to keep going and demonstrates willingness...",
    "pronunciation": "Range of phonological features with variable control...",
    "lexical_resource": "Resource sufficient to discuss topics...",
    "grammatical_range_accuracy": "Mix of structures with limited flexibility..."
  },
  "criterion_descriptors": {
    "fluency_coherence": "Able to keep going and demonstrates willingness...",
    "pronunciation": "Range of phonological features with variable control...",
    "lexical_resource": "Resource sufficient to discuss topics...",
    "grammatical_range_accuracy": "Mix of structures with limited flexibility..."
  },
  "statistics": {
    "total_words_transcribed": 163,
    "content_words": 162,
    "filler_words_detected": 0,
    "filler_percentage": 0.0,
    "is_monotone": false
  },
  "normalized_metrics": {
    "wpm": 88.73,
    "long_pauses_per_min": 2.19,
    "fillers_per_min": 0.0,
    "pause_variability": 1.472,
    "speech_rate_variability": 0.317,
    "vocab_richness": null,
    "type_token_ratio": null,
    "repetition_ratio": null,
    "mean_utterance_length": null
  },
  "speech_quality": {
    "mean_word_confidence": 0.78,
    "low_confidence_ratio": 0.25,
    "is_monotone": false
  },
  "llm_analysis": null,
  "feedback": null,
  "grammar_errors": null,
  "word_choice_errors": null,
  "examiner_descriptors": null,
  "fluency_notes": null
}
```

### When to Use Fast Mode

✅ **Use Fast Mode For:**

- Quick practice feedback (5-10 seconds per minute)
- Real-time progress tracking
- Initial skill assessment
- Mobile app analysis (bandwidth conscious)
- Classroom practice with immediate feedback
- Progress monitoring over multiple takes

❌ **Don't Use Fast Mode For:**

- Formal assessments
- Detailed feedback required
- Grammar/vocabulary analysis needed
- Professional evaluation
- Detailed per-rubric feedback

---

## Examples

**Note:** Examples with `feedback` field show responses when `detail="feedback"` or `detail="full"`. The default response (no detail parameter) does not include the `feedback` field.

### Example 1: Minimal Response (Default, No Detail Parameter)

```json
{
  "job_id": "3c6e75c6-de7d-49de-afbb-7de1452dde2c",
  "status": "completed",
  "engine_version": "0.1.0",
  "scoring_config": {},
  "overall_band": 6.0,
  "criterion_bands": {
    "fluency_coherence": 6,
    "pronunciation": 7,
    "lexical_resource": 6,
    "grammatical_range_accuracy": 6
  },
  "confidence": {
    "overall_confidence": 0.44
  },
  "descriptors": {
    "fluency_coherence": "Able to keep going and demonstrates willingness...",
    "pronunciation": "Range of phonological features with variable control...",
    "lexical_resource": "Resource sufficient to discuss topics...",
    "grammatical_range_accuracy": "Mix of structures with limited flexibility..."
  },
  "criterion_descriptors": {
    "fluency_coherence": "Able to keep going and demonstrates willingness. 2 coherence breaks detected.",
    "pronunciation": "Range of phonological features with variable control. 25% of words show low confidence.",
    "lexical_resource": "Resource sufficient to discuss topics. 2 word choice issues detected.",
    "grammatical_range_accuracy": "Mix of structures with limited flexibility. 3 grammar errors identified."
  },
  "statistics": {
    "total_words_transcribed": 163,
    "content_words": 162,
    "filler_words_detected": 1,
    "filler_percentage": 0.61,
    "is_monotone": false
  },
  "normalized_metrics": {
    "wpm": 88.73,
    "long_pauses_per_min": 2.19,
    "fillers_per_min": 2.74,
    "pause_variability": 1.472,
    "speech_rate_variability": 0.317,
    "vocab_richness": 0.537,
    "type_token_ratio": 0.537,
    "repetition_ratio": 0.072,
    "mean_utterance_length": 9.59
  },
  "llm_analysis": {
    "grammar_error_count": 3,
    "coherence_break_count": 2,
    "word_choice_error_count": 2,
    "advanced_vocabulary_count": 1,
    "flow_instability_present": false,
    "cascading_grammar_failure": false
  },
  "speech_quality": {
    "mean_word_confidence": 0.78,
    "low_confidence_ratio": 0.25,
    "is_monotone": false
  },
  "feedback": {
    "fluency_coherence": {
      "criterion": "Fluency & Coherence",
      "band": 6.0,
      "strengths": ["Able to produce extended speech"],
      "weaknesses": [
        "Noticeable pauses affecting flow",
        "2 coherence breaks detected"
      ],
      "suggestions": [
        "Practice extended speaking on various topics",
        "Use transition words to improve coherence"
      ]
    },
    "pronunciation": {
      "criterion": "Pronunciation",
      "band": 7.0,
      "strengths": ["Generally clear pronunciation"],
      "weaknesses": ["Occasional clarity issues"],
      "suggestions": ["Practice articulation and intonation"]
    },
    "lexical_resource": {
      "criterion": "Lexical Resource",
      "band": 6.0,
      "strengths": ["Adequate vocabulary range"],
      "weaknesses": ["2 word choice issues detected"],
      "suggestions": [
        "Learn precise word meanings",
        "Study 10-15 new vocabulary items per week"
      ]
    },
    "grammatical_range_accuracy": {
      "criterion": "Grammatical Range & Accuracy",
      "band": 6.0,
      "strengths": ["Basic structures demonstrated"],
      "weaknesses": ["3 grammar errors identified"],
      "suggestions": [
        "Review common grammar errors",
        "Study one complex structure per week"
      ]
    },
    "overall": {
      "overall_band": 6.0,
      "summary": "You have adequate English skills to discuss topics with some range. Work on fluency, vocabulary diversity, and grammatical accuracy.",
      "next_band_tips": {
        "focus": "Improve fluency and coherence to reach band 6.5",
        "action": "Reduce pauses and use transition words to improve flow"
      }
    }
  }
}
```

### Example 2: Processing Response

```json
{
  "job_id": "3c6e75c6-de7d-49de-afbb-7de1452dde2c",
  "status": "processing",
  "message": "Analysis in progress..."
}
```

### Example 3: Error Response

```json
{
  "job_id": "3c6e75c6-de7d-49de-afbb-7de1452dde2c",
  "status": "error",
  "error": "No speech detected in audio file"
}
```

---

## Usage Guide for Frontend

### Basic Flow

1. **Submit Analysis**
   - POST `/api/direct/v1/analyze` with audio file
   - Returns: `job_id`, `status: "queued"`

2. **Poll for Results**
   - GET `/api/direct/v1/result/{job_id}` (no detail parameter)
   - Returns: Base response (minimal, fast)

3. **Display Results**
   - Show `overall_band` prominently
   - Show `criterion_bands` as a breakdown
   - Show `statistics` for word count and filler percentage
   - Show `normalized_metrics` for detailed analysis

### Displaying Band Scores

```
Overall Band: 6.0
├─ Fluency & Coherence: 6
├─ Pronunciation: 7
├─ Lexical Resource: 6
└─ Grammar & Accuracy: 6
```

### Displaying Confidence

```
Assessment Confidence: 44% (Low)
⚠️ This assessment should be taken cautiously. Confidence affected by: [details from confidence_multipliers]
```

### Displaying Key Metrics

Show a metrics dashboard with:

- **Delivery:** WPM (88.7), Pauses (2.2/min), Fillers (2.7/min)
- **Vocabulary:** Richness (0.54), Unique words, Repetition ratio
- **Quality:** Clarity (78%), Monotone (No)

### Using Descriptors

**Show criterion_descriptors (not descriptors) for user-facing feedback.**

These are specific to the candidate's actual performance, not generic IELTS band text.

```
Pronunciation: "Range of phonological features with variable control. Individual
words may be mispronounced. 25% of words show low confidence."
```

### Requesting Full Details

When user clicks "View Detailed Analysis":

- Call: GET `/api/direct/v1/result/{job_id}?detail=full`
- Returns: All fields including timestamps, errors, benchmarking

### For Feedback Tier (detail="feedback")

Call: GET `/api/direct/v1/result/{job_id}?detail=feedback`

Use:

- `transcript` - Display full speech text
- `grammar_errors` - Highlight grammar issues
- `word_choice_errors` - Show vocabulary problems
- `fluency_notes` - Display summary notes

### For Full Tier (detail="full")

Use `word_timestamps` to build a timeline visualization:

- Display each word with confidence color-coding
- Highlight fillers in different color
- Show timing bar with pauses

---

## Integration Guide for Frontend Developers

### Handling Both Full and Fast Mode Responses

When displaying results, your frontend should handle both response types:

```javascript
// Helper function to detect response mode
function isFullMode(response) {
  return response.llm_analysis !== null && response.feedback !== null;
}

function isFastMode(response) {
  return response.llm_analysis === null && response.feedback === null;
}

// Display conditional UI based on mode
if (isFullMode(response)) {
  // Show full feedback sections
  displayFeedback(response.feedback);
  displayGrammarErrors(response.grammar_errors);
  displayAdvancedMetrics(response.normalized_metrics);
} else if (isFastMode(response)) {
  // Show basic metrics only
  displayBasicMetrics(response.statistics);
  displayBandScore(response.overall_band);
  showFastModeNotice("Fast mode - LLM analysis not included");
}
```

### Conditional Field Access

Always null-check before accessing fields that may not be available:

```javascript
// Safe field access
const feedback = response.feedback || {};
const grammarErrors = response.grammar_errors || { count: 0 };
const llmAnalysis = response.llm_analysis || null;

// Check if field exists and has data
if (llmAnalysis && llmAnalysis.grammar_error_count > 0) {
  displayGrammarWarning();
}
```

### Response Mode Detection Helper

```javascript
const ResponseMode = {
  FULL: "full",
  FEEDBACK: "feedback",
  DEFAULT: "default",
  FAST: "fast",
};

function getResponseMode(response) {
  // Check for fast mode indicators
  if (response.llm_analysis === null && response.feedback === null) {
    return ResponseMode.FAST;
  }

  // Check for detail level
  if (
    response.word_timestamps !== undefined &&
    response.word_timestamps !== null
  ) {
    return ResponseMode.FULL;
  }

  if (
    response.grammar_errors !== undefined &&
    response.grammar_errors !== null
  ) {
    return ResponseMode.FEEDBACK;
  }

  return ResponseMode.DEFAULT;
}
```

### Recommended Display Strategy

**For Dashboard/Quick View:**

```
1. Always show: overall_band, criterion_bands, statistics
2. If full mode: Add feedback section, grammar errors
3. If fast mode: Show only basic metrics
```

**For Detailed Analysis:**

```
1. Request with detail=full
2. Display all available fields
3. Show timestamps visualization
4. Display detailed feedback
```

**For Practice Mode:**

```
1. Use analyze-fast endpoint
2. Show quick feedback immediately
3. Option to run full analysis for detailed feedback
```

---

## Key Integration Points

### 1. Handling Processing Status

```javascript
async function pollForResults(jobId) {
  let attempts = 0;
  const maxAttempts = 300; // 5 minutes with 1-sec intervals

  while (attempts < maxAttempts) {
    const response = await fetch(`/api/direct/v1/result/${jobId}`);
    const data = await response.json();

    if (data.status === "completed") {
      return data;
    } else if (data.status === "error") {
      throw new Error(data.error);
    }

    // Still processing, wait and retry
    await new Promise((resolve) => setTimeout(resolve, 1000));
    attempts++;
  }

  throw new Error("Analysis timeout");
}
```

### 2. Choosing Endpoint Based on User Action

```javascript
async function analyzeAudio(file, isQuickMode = false) {
  const endpoint = isQuickMode
    ? "/api/direct/v1/analyze-fast"
    : "/api/direct/v1/analyze";

  const formData = new FormData();
  formData.append("file", file);
  formData.append("speech_context", "conversational");

  const response = await fetch(endpoint, {
    method: "POST",
    body: formData,
  });

  const { job_id } = await response.json();
  return job_id;
}
```

### 3. Requesting Full Details When Needed

```javascript
async function getDetailedResults(jobId) {
  // First request: fast default response
  let response = await fetch(`/api/direct/v1/result/${jobId}`);
  let data = await response.json();

  if (data.status === "completed") {
    // User clicked "View Details", request full tier
    response = await fetch(`/api/direct/v1/result/${jobId}?detail=full`);
    data = await response.json();
  }

  return data;
}
```

---

### 1. Criterion Descriptors Are the Source of Truth

**Don't use generic IELTS descriptors.** Use `criterion_descriptors` which:

- Are pulled from the candidate's actual criterion band
- Include LLM findings (errors, breaks, vocabulary)
- Provide specific, data-driven feedback

Example:

- **Generic:** "Able to keep going and demonstrates willingness..."
- **Specific:** "Able to keep going and demonstrates willingness. Coherence may be lost due to hesitation. 2 coherence breaks detected."

### 2. Confidence Score Matters

Always show confidence level and warn if <0.5:

```
⚠️ Low Confidence (0.44): This assessment may not be reliable.
Consider retaking the test for more accurate results.
```

### 3. Statistics Are Actionable

- **Filler %:** Shows exactly how much is filler (0.61%) - concrete metric
- **Word count:** Shows effort/length of speech
- **Monotone:** Single boolean indicator of prosody issues

### 4. Use LLM Findings in Context

- Grammar error count: How many actual mistakes
- Coherence breaks: How many times lost thread
- Vocabulary: Both word choice errors AND advanced vocabulary use

This is much more informative than generic band descriptions.

### 5. Metrics Tell the Full Story

- **WPM:** Too slow (70) vs. natural (90-110) vs. fast (150+)
- **Pause variability:** High = nervous/unsure, Low = confident
- **Vocab richness:** Direct measure of vocabulary diversity
- **Repetition ratio:** Shows if candidate is stuck repeating same words

---

## Field Validation & Type Safety

### Response Field Checklist

**Always Present (All Modes):**

- ✅ `job_id` - string
- ✅ `status` - "completed" | "processing" | "error"
- ✅ `engine_version` - string
- ✅ `scoring_config` - object
- ✅ `overall_band` - number (5.0-9.0)
- ✅ `criterion_bands` - object with 4 criteria
- ✅ `confidence` - object
- ✅ `descriptors` - object
- ✅ `criterion_descriptors` - object
- ✅ `statistics` - object
- ✅ `normalized_metrics` - object
- ✅ `llm_analysis` - object (may be null in fast mode)
- ✅ `speech_quality` - object

**Present When detail="feedback" or "full":**

- ℹ️ `transcript` - string | null
- ℹ️ `grammar_errors` - object | null
- ℹ️ `word_choice_errors` - object | null
- ℹ️ `examiner_descriptors` - array | null
- ℹ️ `fluency_notes` - string | null
- ℹ️ `feedback` - object | null

**Present When detail="full":**

- 📊 `word_timestamps` - array | null
- 📊 `content_words` - array | null
- 📊 `segment_timestamps` - array | null
- 📊 `filler_events` - array | null
- 📊 `opinions` - object | null (always null)
- 📊 `benchmarking` - object | null (always null)
- 📊 `confidence_multipliers` - object | null
- 📊 `timestamped_feedback` - object | null

### Common Validation Patterns

```javascript
// Validate band score
function isBandScoreValid(band) {
  const validBands = [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0];
  return validBands.includes(band);
}

// Validate confidence
function isConfidenceValid(confidence) {
  return typeof confidence === "number" && confidence >= 0 && confidence <= 1;
}

// Validate response completeness
function isResponseComplete(response) {
  return (
    response.status === "completed" &&
    response.overall_band !== null &&
    response.criterion_bands !== null
  );
}

// Check for fast mode limitations
function hasFastModeLimitations(response) {
  return response.llm_analysis === null || response.feedback === null;
}
```

### Safe Field Access Patterns

```javascript
// Always null-check feedback-tier fields
const feedback = response.feedback || {};
const grammarErrors = response.grammar_errors || { count: 0 };

// Check for LLM analysis availability
const hasLLMAnalysis =
  response.llm_analysis && Object.keys(response.llm_analysis).length > 0;

// Safely access nested objects
const fluencyBand = response.criterion_bands?.fluency_coherence ?? 5.0;
const confidenceScore = response.confidence?.overall_confidence ?? 0;

// Validate array fields exist before iterating
const wordTimestamps = response.word_timestamps || [];
wordTimestamps.forEach((word) => {
  // Safe iteration
});
```

---

## Important Notes

### Score Calculation Formula

```
Overall Band = round_to_0.5(
  (fluency + pronunciation + lexical + grammar) / 4
)
```

All bands use this same formula. No weighting - equal emphasis on all criteria.

### Response Tier Default Behavior

- **No detail parameter:** Returns base response only (fastest, smallest)
- **detail=feedback:** Adds transcript and feedback fields
- **detail=full:** Adds timestamps and detailed breakdown (largest)

Choose appropriate tier based on use case:

- Dashboard overview → default
- Feedback email → feedback
- Detailed analysis tool → full

### Timestamp Accuracy

Timestamps are in seconds (float format):

- 0.0 = start of audio
- 8.5 = 8.5 seconds into audio
- Precision: typically 0.01s (10ms)

### Error Codes

When `status: "error"`, the `error` field contains human-readable error message. Common errors:

- "No speech detected in audio file"
- "Audio quality too poor for analysis"
- "Analysis timeout"

---

## Error Handling Guide

### Common Error Responses

**Audio File Errors:**

```json
{
  "job_id": "uuid",
  "status": "error",
  "error": "Audio file not found: [path]"
}
```

_Action: Validate file upload, check file permissions_

```json
{
  "job_id": "uuid",
  "status": "error",
  "error": "Invalid audio format: Only .wav, .mp3, .ogg supported"
}
```

_Action: Ask user to convert audio to supported format_

**Audio Content Errors:**

```json
{
  "job_id": "uuid",
  "status": "error",
  "error": "No speech detected in audio file"
}
```

_Action: Suggest recording with clear speech_

```json
{
  "job_id": "uuid",
  "status": "error",
  "error": "Audio too short: Minimum 10 seconds required"
}
```

_Action: Ask user to record longer sample_

```json
{
  "job_id": "uuid",
  "status": "error",
  "error": "Audio quality too poor for analysis"
}
```

_Action: Suggest reducing background noise, speaking clearly_

**Processing Errors:**

```json
{
  "job_id": "uuid",
  "status": "error",
  "error": "Analysis timeout: Processing took too long"
}
```

_Action: Suggest retrying with shorter audio segment_

**Job Not Found:**

```json
{
  "status": 404,
  "detail": "Job {job_id} not found or access denied"
}
```

_Action: Job expired or invalid ID - suggest resubmitting_

### Frontend Error Handling Example

```javascript
async function analyzeWithErrorHandling(file) {
  try {
    // Submit analysis
    const submitResponse = await fetch("/api/direct/v1/analyze", {
      method: "POST",
      body: formData,
    });

    if (!submitResponse.ok) {
      throw new Error(`Submit failed: ${submitResponse.status}`);
    }

    const { job_id } = await submitResponse.json();

    // Poll for results
    let attempts = 0;
    const maxAttempts = 300; // 5 minutes

    while (attempts < maxAttempts) {
      const resultResponse = await fetch(`/api/direct/v1/result/${job_id}`);

      if (!resultResponse.ok) {
        if (resultResponse.status === 404) {
          throw new Error("Analysis job expired or not found");
        }
        throw new Error(`Status check failed: ${resultResponse.status}`);
      }

      const result = await resultResponse.json();

      if (result.status === "completed") {
        return { success: true, data: result };
      }

      if (result.status === "error") {
        return { success: false, error: result.error };
      }

      // Still processing
      await new Promise((resolve) => setTimeout(resolve, 1000));
      attempts++;
    }

    throw new Error("Analysis timeout after 5 minutes");
  } catch (error) {
    return {
      success: false,
      error: error.message,
      action: getRecoveryAction(error.message),
    };
  }
}

function getRecoveryAction(errorMessage) {
  if (errorMessage.includes("Audio")) {
    return "upload_new_file";
  }
  if (errorMessage.includes("timeout")) {
    return "use_shorter_audio";
  }
  if (errorMessage.includes("not found")) {
    return "resubmit";
  }
  return "retry";
}
```

---

## Version History

| Version | Date       | Changes                                                                                                         |
| ------- | ---------- | --------------------------------------------------------------------------------------------------------------- |
| 1.2     | 2026-01-24 | Added `/analyze-fast` endpoint documentation, fast mode response fields, and endpoint comparison table          |
| 1.1     | 2026-01-24 | Added `feedback` field: structured per-rubric feedback with strengths, weaknesses, and suggestions              |
| 1.0     | 2026-01-24 | Complete response spec with LLM integration, criterion-specific descriptors, updated statistics always included |

---

**For questions or clarifications, contact the API team.**
