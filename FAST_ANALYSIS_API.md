# Fast Analysis Endpoint Documentation

## Overview

The `/analyze-fast` endpoint provides **5-8x faster** speech analysis by skipping expensive operations that require semantic understanding. Perfect for development, testing, and real-time dashboards.

**Speedup: 15-25 seconds vs 100-120 seconds for full analysis**

---

## Endpoints

### RapidAPI Version

```
POST /api/v1/analyze-fast
```

### Direct Access Version

```
POST /api/direct/v1/analyze-fast
```

---

## What's Included ✅

| Feature                     | Full Analysis           | Fast Analysis     |
| --------------------------- | ----------------------- | ----------------- |
| **Whisper Transcription**   | ✅                      | ✅                |
| **Word Confidence**         | ✅                      | ✅                |
| **Filler Detection**        | ✅ (Whisper + Wav2Vec2) | ✅ (Whisper only) |
| **WPM/Pause Metrics**       | ✅                      | ✅                |
| **Basic Band Estimate**     | ✅                      | ✅ (Metrics-only) |
| **Word Timestamps**         | ✅                      | ✅                |
| **LLM Annotations**         | ✅                      | ❌                |
| **Grammar/Vocab Feedback**  | ✅                      | ❌                |
| **Semantic Analysis**       | ✅                      | ❌                |
| **Subtle Filler Detection** | ✅ (Wav2Vec2)           | ❌                |

---

## Request Format

```bash
curl -X POST http://localhost:8000/api/direct/v1/analyze-fast \
  -F "file=@speech.wav" \
  -F "speech_context=conversational" \
  -F "device=cpu"
```

### Parameters

| Parameter        | Type   | Default        | Description                                                 |
| ---------------- | ------ | -------------- | ----------------------------------------------------------- |
| `file`           | File   | Required       | Audio file (.wav, .flac, .mp3)                              |
| `speech_context` | String | conversational | Context: conversational, narrative, presentation, interview |
| `device`         | String | cpu            | Device: cpu or cuda                                         |

---

## Response Format

### Immediate Response (Queued)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "mode": "fast",
  "message": "Fast analysis started. Poll /api/direct/v1/result/{job_id} for results"
}
```

### Poll Result (`GET /api/direct/v1/result/{job_id}`)

#### While Processing

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Analysis in progress..."
}
```

#### Completed (Without detail parameter)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "mode": "fast",
  "engine_version": "0.1.0",
  "overall_band": 6.5,
  "criterion_bands": {
    "fluency_coherence": 6.5,
    "pronunciation": 6.5,
    "lexical_resource": 6.5,
    "grammatical_range_accuracy": 6.0
  },
  "confidence": 0.72
}
```

#### Completed (With `detail=feedback`)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "mode": "fast",
  "overall_band": 6.5,
  "criterion_bands": {...},
  "confidence": 0.72,
  "transcript": "This is the complete transcript...",
  "grammar_errors": {
    "count": 0,
    "severity": "none",
    "note": "No grammar errors detected"
  },
  "word_choice_errors": {
    "count": 0,
    "advanced_vocab_used": 2,
    "note": "Word choice is appropriate"
  }
}
```

#### Error Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "error",
  "error": "Audio too short: minimum 5 seconds required"
}
```

---

## Query Parameters

### `detail` - Response Detail Level

Controls what fields are included in the completed response:

- **No parameter** (default): Basic metrics only
- **`detail=feedback`**: Add transcript, grammar/vocab feedback, fluency notes
- **`detail=full`**: Add all metrics, timestamps, and detailed analysis

---

## Polling Behavior

1. **Poll immediately after upload** - Returns `status: "queued"`
2. **Poll every 2-5 seconds** - Check for `status: "processing"`
3. **When `status: "completed"`** - Results are ready
4. **Timeout after 30 seconds** - If still processing, something may be wrong

### Example Polling Loop (Python)

```python
import time
import requests

job_id = response["job_id"]

while True:
    result = requests.get(
        f"http://localhost:8000/api/direct/v1/result/{job_id}",
        params={"detail": "feedback"}
    )

    if result["status"] == "completed":
        print("Done!", result)
        break
    elif result["status"] == "processing":
        print("Still processing...")
        time.sleep(2)
    elif result["status"] == "error":
        print("Error:", result["error"])
        break
```

---

## Use Cases

### 1. **Development & Testing**

```python
# Quick feedback during development
response = analyze_fast(audio_file)
print(f"Band: {response['overall_band']}")
print(f"WPM: {response['normalized_metrics']['speech_rate_wpm']}")
```

### 2. **Real-time Dashboard**

```python
# Fast metrics for live display
for audio in uploaded_files:
    result = analyze_fast(audio)
    dashboard.update(band=result['overall_band'],
                     wpm=result['normalized_metrics']['speech_rate_wpm'])
```

### 3. **Bulk Initial Screening**

```python
# Quick pass/fail before detailed analysis
for audio in bulk_files:
    result = analyze_fast(audio)
    if result['overall_band'] >= 7.0:
        analyze_full(audio)  # Only full analysis for high performers
```

### 4. **A/B Testing**

```python
# Compare two recordings quickly
before = analyze_fast(recording_before)
after = analyze_fast(recording_after)
improvement = after['overall_band'] - before['overall_band']
```

---

## Performance Comparison

### Full Analysis Pipeline

- Whisper transcription: ~30-40s
- WhisperX alignment: ~15-20s
- Wav2Vec2 detection: ~15-20s
- LLM annotations: ~15-20s
- **Total: 100-120 seconds**

### Fast Analysis Pipeline

- Whisper transcription: ~30-40s
- Filler detection (Whisper only): ~5s
- Metrics calculation: ~2s
- **Total: 15-25 seconds**

**Speedup: 5-8x faster** ⚡

---

## Limitations

The fast variant skips:

1. **Subtle Filler Detection** (Wav2Vec2)
   - Only detects fillers marked by Whisper
   - May miss subtle "uh/um" sounds in low-confidence regions

2. **LLM Semantic Analysis**
   - No grammar error identification
   - No vocabulary complexity assessment
   - No coherence/flow analysis
   - No register/tone evaluation

3. **Advanced Band Features**
   - Band scoring is metrics-only
   - No LLM-based semantic boost
   - ~72% confidence vs ~85% for full analysis

4. **Detailed Feedback**
   - No timestamped grammar errors
   - No word-level sophistication markers
   - No listener effort estimation

---

## When to Use

### ✅ Use Fast Analysis For:

- Development and debugging
- Testing/validation
- Quick band estimates
- Bulk screening
- Real-time dashboards
- A/B comparisons
- Performance metrics
- Integration testing

### ❌ Don't Use Fast Analysis For:

- Production scoring (use full analysis)
- Detailed feedback/coaching
- Grammar correction
- Vocabulary assessment
- Listener effort evaluation
- High-stakes assessment (exams)

---

## Rate Limiting

Fast endpoint shares rate limits with full analysis endpoint:

- **100 requests/hour per user** (RapidAPI)
- **Unlimited** (Direct access)

---

## Error Handling

### Common Errors

| Error                  | Cause             | Solution             |
| ---------------------- | ----------------- | -------------------- |
| `Audio file not found` | File path invalid | Verify file path     |
| `Audio too short`      | <5 seconds        | Provide longer audio |
| `Invalid audio format` | Unsupported codec | Use .wav/.flac/.mp3  |
| `No speech detected`   | Silent audio      | Check audio content  |

---

## Example Workflow

```python
import requests
import time

# 1. Submit audio
response = requests.post(
    "http://localhost:8000/api/direct/v1/analyze-fast",
    files={"file": open("speech.wav", "rb")},
    data={"speech_context": "conversational", "device": "cpu"}
)

job_id = response.json()["job_id"]
print(f"Job queued: {job_id}")

# 2. Poll for results
for i in range(30):  # 30 attempts, 2 sec each = 60 sec timeout
    result = requests.get(
        f"http://localhost:8000/api/direct/v1/result/{job_id}",
        params={"detail": "feedback"}
    )

    data = result.json()

    if data["status"] == "completed":
        # 3. Extract metrics
        print(f"\n✓ Analysis Complete:")
        print(f"  Band: {data['overall_band']}")
        print(f"  Criterion Bands:")
        for criterion, band in data['criterion_bands'].items():
            print(f"    - {criterion}: {band}")

        if "normalized_metrics" in data:
            metrics = data['normalized_metrics']
            print(f"\n  Metrics:")
            print(f"    - WPM: {metrics.get('speech_rate_wpm', 'N/A')}")
            print(f"    - Pauses/min: {metrics.get('pause_frequency', 'N/A')}")

        break

    time.sleep(2)
else:
    print("Timeout: Analysis took too long")
```

---

## Migration from Full to Fast

If you're currently using the full `/analyze` endpoint and want to switch:

### Before (Full Analysis)

```python
response = requests.post("/api/direct/v1/analyze", files={"file": audio})
```

### After (Fast Analysis)

```python
response = requests.post("/api/direct/v1/analyze-fast", files={"file": audio})
```

Response structure is identical - just faster!
