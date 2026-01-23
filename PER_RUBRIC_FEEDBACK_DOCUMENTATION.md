# Per-Rubric Feedback Documentation

## Overview

The API now returns detailed, structured feedback for each IELTS speaking criterion. Each rubric feedback clearly shows:

1. **Strengths** - What the speaker is doing well
2. **Weaknesses** - Areas that need improvement
3. **Suggestions** - Actionable tips to improve
4. **Overall Assessment** - Summary and next band recommendations

## Feedback Structure

### Response Example

```json
{
  "feedback": {
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
        "Use a thesaurus and corpus (e.g., English Corpora) to check word usage",
        "Learn 10-15 new advanced words/phrases per week",
        "Study idiomatic expressions in context"
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
        "Focus on tense consistency and subject-verb agreement",
        "Study one complex structure per week (e.g., subordinate clauses)",
        "Record yourself and check for grammatical accuracy",
        "Practice combining simple sentences into complex ones"
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
}
```

## Field Descriptions

### Per-Rubric Feedback Object

#### `fluency_coherence`

**Criterion:** Fluency & Coherence

**What's evaluated:**

- Ability to speak at length without excessive hesitation
- Logical flow and connection between ideas
- Use of transition words and discourse markers
- Coherence and lack of "listener effort"

**Strengths Examples (what looks good):**

- "Excellent fluency - speech flows naturally"
- "Able to sustain speech with minimal pauses"
- "Ideas are logically connected"
- "Demonstrates willingness to keep speaking"

**Weaknesses Examples (what needs work):**

- "Coherence breaks detected (2) - ideas not always clearly connected"
- "Speech flow is inconsistent - difficulty finding words"
- "Frequent long pauses (2.8/min) - prepare answers more thoroughly"
- "Excessive repetition (ratio: 0.12) - vary your vocabulary and structures"

**Suggestions (how to improve):**

- Use transition words (furthermore, in addition, however)
- Practice organizing thoughts before speaking
- Record yourself and listen for natural flow
- Practice extended speaking on various topics

#### `pronunciation`

**Criterion:** Pronunciation

**What's evaluated:**

- Individual sound articulation (phoneme accuracy)
- Word stress and sentence stress
- Intonation and rhythm
- Overall intelligibility/word clarity

**Strengths Examples:**

- "Clear pronunciation - easily understood"
- "Consistent phonological control"
- "Natural stress and intonation patterns"

**Weaknesses Examples:**

- "Low word clarity (35% unclear words) - mispronunciation of certain words"
- "Average word clarity is low (65%) - enunciation needs work"
- "Lack of intonation variation - speech sounds monotone"
- "Pronunciation issues make speech difficult to understand"

**Suggestions:**

- Focus on articulation - speak more clearly and deliberately
- Record yourself and compare with native speaker pronunciation
- Practice varying pitch and stress - listen to English music and podcasts
- Use pronunciation apps (Forvo, Google Translate)

#### `lexical_resource`

**Criterion:** Lexical Resource

**What's evaluated:**

- Range of vocabulary (variety of words used)
- Use of advanced/sophisticated vocabulary
- Idiomatic expressions and collocations
- Appropriate word choice and word form accuracy
- Avoiding repetition and using paraphrase

**Strengths Examples:**

- "Wide and flexible vocabulary range"
- "Uses 8 advanced vocabulary items effectively"
- "Employs 3 idiomatic expressions naturally"
- "Good vocabulary diversity"

**Weaknesses Examples:**

- "Word choice errors (4) - using wrong words or wrong connotation"
- "Limited use of advanced vocabulary"
- "Excessive repetition of the same words"
- "Does not use idiomatic expressions or collocations"

**Suggestions:**

- Learn precise word meanings and usage contexts
- Use a thesaurus and corpus to check word usage
- Learn 10-15 new advanced words/phrases per week
- Study idiomatic expressions in context
- Paraphrase - express the same idea using different words

#### `grammatical_range_accuracy`

**Criterion:** Grammatical Range & Accuracy

**What's evaluated:**

- Variety of grammatical structures (simple, complex, compound)
- Accuracy of tense usage
- Agreement (subject-verb, article, etc.)
- Appropriate use of subordination
- Overall grammatical control

**Strengths Examples:**

- "Excellent grammatical control"
- "Wide range of structures used accurately"
- "Good control of various grammatical structures"
- "Manages basic and some complex structures"

**Weaknesses Examples:**

- "Grammar errors found (5) - affects clarity at times"
- "Grammar errors compound - meaning becomes unclear"
- "Complex structures attempted but often inaccurate"
- "Limited range of grammatical structures"
- "Primarily uses simple sentences - limited complexity"

**Suggestions:**

- Review common grammar errors identified in speech
- Focus on tense consistency and subject-verb agreement
- Practice using complex structures (relative clauses, conditionals)
- Start with written practice, then transfer to speaking
- Study one complex structure per week
- Practice combining simple sentences into complex ones

### Overall Assessment

#### `summary`

Band-specific summary of overall performance:

- **Band 8.0+:** "You demonstrate strong command of English with fluent delivery, varied vocabulary, and excellent grammatical control."
- **Band 7.0+:** "You show good English proficiency with generally fluent speech, adequate range of vocabulary and structures."
- **Band 6.0+:** "You have adequate English skills to discuss topics with some range and generally clear communication."
- **Band 5.5+:** "You can manage basic conversation but need improvement in fluency, vocabulary range, and grammatical accuracy."
- **Below 5.5:** "You have some English ability but need significant improvement in fluency, vocabulary, and grammar."

#### `next_band_tips`

Specific actionable advice to reach the next band level:

**Structure:**

- `focus`: Which criterion to prioritize
- `action`: Specific steps to take

**Example:**

```json
{
  "focus": "Improve grammar range and accuracy to reach band 7.5",
  "action": "Master complex sentence structures and ensure accurate tense and agreement."
}
```

## Data-Driven Feedback

All feedback is backed by actual metrics:

### Fluency & Coherence Metrics

- WPM (words per minute) - speech rate
- Pause frequency and duration
- Coherence break count (from LLM analysis)
- Flow stability assessment
- Long pause frequency

### Pronunciation Metrics

- Mean word confidence (0-1 scale)
- Low confidence word ratio (%)
- Monotone detection
- Articulation clarity

### Lexical Resource Metrics

- Advanced vocabulary count (from LLM)
- Idiomatic expression count
- Word choice error count
- Vocabulary richness ratio

### Grammar Metrics

- Total grammar error count
- Complex structure accuracy ratio
- Cascading failure detection
- Range assessment

## Response Integration

### When Feedback is Included

The `feedback` field is included in these response tiers:

1. **Default Response** (no detail parameter): ❌ Not included
2. **Feedback Response** (`detail=feedback`): ✅ Included
3. **Full Response** (`detail=full`): ✅ Included

### Example API Request

```bash
# Get feedback tier response
curl https://api.example.com/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "audio_file": "audio.wav",
    "detail": "feedback"
  }'
```

### Example API Response

```json
{
  "job_id": "job_12345",
  "status": "completed",
  "overall_band": 7.0,
  "criterion_bands": {
    "fluency_coherence": 7.0,
    "pronunciation": 7.5,
    "lexical_resource": 7.0,
    "grammatical_range_accuracy": 6.5
  },
  "feedback": {
    "fluency_coherence": { ... },
    "pronunciation": { ... },
    "lexical_resource": { ... },
    "grammatical_range_accuracy": { ... },
    "overall": { ... }
  }
}
```

## Implementation Details

### Where Feedback is Generated

**File:** `src/core/ielts_band_scorer.py`

**Method:** `IELTSBandScorer._build_feedback()`

This method:

1. Takes subscores (band levels), metrics, and LLM analysis as input
2. Generates strengths based on positive indicators
3. Identifies weaknesses from metric thresholds
4. Provides suggestions tailored to band level and weaknesses
5. Returns structured feedback dict

### Key Thresholds

**Fluency & Coherence:**

- WPM < 80: Slow speech rate flagged
- Long pauses > 2.5/min: Flagged for lower bands
- Coherence breaks > 0: Always flagged

**Pronunciation:**

- Low confidence ratio > 0.3: Clarity issue flagged
- Monotone detection: Intonation issue flagged
- Mean confidence < 0.75: Clarity concerns

**Lexical Resource:**

- Word choice errors > 0: Flagged with count
- Advanced vocabulary = 0 + band >= 6: Under-utilization flagged
- Vocabulary richness < 0.4: Repetition flagged

**Grammar:**

- Grammar errors > 0: Flagged with count
- Complex accuracy < 0.7: Structure issues flagged
- Cascading failure: Meaning-affecting errors flagged

## Frontend Integration

### Displaying Feedback

Recommended frontend structure:

```javascript
// Fluency & Coherence feedback
<div class="criterion">
  <h3>
    {feedback.fluency_coherence.criterion} (Band{" "}
    {feedback.fluency_coherence.band})
  </h3>

  <div class="strengths">
    <h4>What's Good ✓</h4>
    <ul>
      {feedback.fluency_coherence.strengths.map((s) => (
        <li>{s}</li>
      ))}
    </ul>
  </div>

  <div class="weaknesses">
    <h4>Areas for Improvement</h4>
    <ul>
      {feedback.fluency_coherence.weaknesses.map((w) => (
        <li>{w}</li>
      ))}
    </ul>
  </div>

  <div class="suggestions">
    <h4>How to Improve</h4>
    <ol>
      {feedback.fluency_coherence.suggestions.map((s) => (
        <li>{s}</li>
      ))}
    </ol>
  </div>
</div>
```

## Examples by Performance Level

### Band 8.0+ (Excellent)

- Multiple strengths across all criteria
- Minimal weaknesses (mostly about perfecting already-good skills)
- Suggestions focus on advanced refinement
- Next band tips about maintaining excellence

### Band 7.0 (Good)

- Clear strengths in strong areas
- Some weaknesses in weaker criteria
- Balanced suggestions (maintain strengths, improve weaknesses)
- Next band tips about reaching 7.5 or 8.0

### Band 6.0 (Adequate)

- Fewer strengths overall
- Multiple weaknesses in each criterion
- More suggestions for improvement
- Next band tips about reaching 6.5 or 7.0

### Band 5.5 (Pass)

- Few or no strengths
- Multiple weaknesses in most criteria
- Extensive suggestions needed
- Next band tips emphasize foundational improvements

### Below Band 5.5

- Minimal strengths
- Significant weaknesses across all criteria
- Suggestions focus on basic skills
- Clear guidance on what needs most urgent attention
