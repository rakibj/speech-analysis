# How the `/analyze` Endpoint Works

## Quick Overview

When you upload an audio file to `/analyze`, the system processes your speech and returns a detailed analysis of your speaking ability across four key areas: fluency, pronunciation, vocabulary, and grammar. Results are returned with an IELTS band score and personalized feedback.

---

## The Process (What Happens Behind the Scenes)

### **Step 1: Upload & Queue (Instant)**

When you submit your audio file, the system:

- Accepts your file immediately
- Assigns it a unique job ID
- Returns the job ID so you can check results later
- Queues your analysis to start processing

**You get back:** `job_id` and a polling URL to check status

---

### **Step 2: Audio Processing**

The system prepares your audio by:

- Converting it to a standard format if needed
- Cleaning up background noise and normalizing volume
- Preparing the audio for analysis

**Duration:** A few seconds

---

### **Step 3: Speech Recognition**

The system transcribes what you said by:

- Identifying every word you spoke
- Recording the exact timing of each word
- Tracking confidence levels for each word
- Detecting filler words (um, uh, er) and disfluencies

**Duration:** 20-30 seconds for a 2-minute recording

---

### **Step 4: Fluency Analysis**

The system measures how smoothly you speak by:

- Counting speaking speed (words per minute)
- Measuring pauses and hesitations
- Tracking repetitions or false starts
- Assessing flow and coherence

**Duration:** A few seconds

---

### **Step 5: Pronunciation Assessment**

The system evaluates clarity by:

- Analyzing how clearly each word is pronounced
- Identifying mispronounced or unclear words
- Assessing rhythm and intonation patterns
- Measuring overall intelligibility

**Duration:** 10-15 seconds

---

### **Step 6: Vocabulary & Grammar Analysis**

The system examines your language use by:

- Counting unique words and vocabulary complexity
- Detecting advanced vocabulary use
- Identifying grammatical structures and accuracy
- Checking for word choice errors or awkward phrasing

**Duration:** 5-10 seconds

---

### **Step 7: Scoring & Feedback**

The system generates results by:

- Combining all measurements into four criterion scores
- Calculating an overall IELTS band score
- Generating personalized feedback on strengths and areas for improvement
- Creating a confidence rating for the score

**Duration:** A few seconds

---

## Total Processing Time

- **Short recordings (1-2 min):** 30-60 seconds
- **Medium recordings (2-5 min):** 60-120 seconds
- **Long recordings (5+ min):** 120-180 seconds

---

## Getting Your Results

### **Option 1: Poll for Results**

```
GET /api/direct/v1/result/{job_id}
```

The system returns:

- `status: "processing"` → Still analyzing, check back in a few seconds
- `status: "completed"` → Results are ready
- `status: "error"` → Analysis failed, check details

### **Option 2: Response Details**

Once completed, you receive:

- **Overall IELTS Band Score** (5.0-9.0)
- **Criterion Scores:**
  - Fluency & Coherence
  - Pronunciation
  - Lexical Resource (vocabulary)
  - Grammatical Range & Accuracy
- **Personalized Feedback** with strengths and areas to improve
- **Confidence Rating** (how reliable the score is)
- **Full Transcript** of what you said

---

## What Affects Your Score

### **Fluency & Coherence**

- How fast you speak (too slow = lower score)
- How many pauses or hesitations you have
- How many times you repeat yourself
- How naturally your speech flows

### **Pronunciation**

- How clearly you pronounce each word
- How many words sound unclear or mispronounced
- Your rhythm and intonation patterns
- Overall intelligibility to a listener

### **Lexical Resource (Vocabulary)**

- How many different words you use
- How complex and advanced your vocabulary is
- Correct use of words in context
- Appropriate word choice

### **Grammatical Range & Accuracy**

- Length and complexity of your sentences
- Variety of grammatical structures used
- Frequency and severity of grammatical errors
- Correct use of tenses, articles, and other features

---

## Important Notes

- **Audio Quality Matters:** Clear audio with minimal background noise produces more accurate results
- **Duration Matters:** Longer samples (3+ minutes) produce more reliable scores than very short samples
- **Context Affects Scoring:** The same language performance may score differently depending on the context (casual conversation vs. formal presentation)
- **Confidence Scores:** Not all results have 100% confidence. Low-confidence scores may benefit from retesting

---

## Example Results

```json
{
  "job_id": "abc-123-def",
  "status": "completed",
  "overall_band": 7.0,
  "criterion_bands": {
    "fluency_coherence": 7.5,
    "pronunciation": 7.0,
    "lexical_resource": 6.5,
    "grammatical_range_accuracy": 7.0
  },
  "confidence": {
    "overall": 0.82,
    "category": "HIGH - Reliable with minor caveats"
  },
  "feedback": {
    "strengths": [
      "Good fluency with natural pacing",
      "Clear articulation of most words"
    ],
    "improvements": [
      "Increase vocabulary complexity",
      "Expand sentence structures"
    ]
  },
  "transcript": "Hello, I'm speaking about my recent experience..."
}
```

---

## Troubleshooting

| Issue                         | Solution                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------- |
| **"Processing" for too long** | Analysis may be queued. Check again in 1-2 minutes.                                         |
| **"Error" response**          | Audio file may be too short, corrupted, or wrong format. Try again with a clear audio file. |
| **Low confidence score**      | Consider retesting with better audio quality or a longer recording.                         |
| **Lower than expected score** | Review the feedback. Audio clarity or complexity may need improvement.                      |

---

## Tips for Best Results

1. **Use Clear Audio:** Minimize background noise and speak clearly
2. **Speak Naturally:** Don't rush or artificially slow down
3. **Be Substantive:** Use full sentences and varied vocabulary
4. **Longer is Better:** 3-5 minute recordings provide more reliable scores than under 1 minute
5. **Check Feedback:** Use personalized feedback to improve for next time
