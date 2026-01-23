# Quality-Preserving Optimizations - Implementation Guide

These optimizations improve performance without sacrificing analysis quality.

---

## Priority 1: Model Caching (Save 10-15 seconds per request)

### Current Issue

Models are loaded fresh for each request:

- Whisper model loaded each time
- Wav2Vec2 model loaded each time
- WhisperX model loaded each time

### Implementation

Create `src/audio/model_cache.py`:

```python
"""Global model cache for faster repeated requests."""
import torch
from functools import lru_cache
from src.utils.logging_config import logger

class ModelCache:
    """Singleton cache for audio processing models."""

    _whisper_model = None
    _wav2vec2_model = None
    _whisperx_model = None
    _device = "cpu"

    @classmethod
    def get_whisper(cls, device="cpu", model_name="base"):
        """Get or load Whisper model."""
        if cls._whisper_model is None or cls._device != device:
            logger.info(f"Loading Whisper model: {model_name} on {device}")
            import whisper
            cls._whisper_model = whisper.load_model(model_name, device=device)
            cls._device = device
        return cls._whisper_model

    @classmethod
    def get_wav2vec2(cls, device="cpu"):
        """Get or load Wav2Vec2 model."""
        if cls._wav2vec2_model is None or cls._device != device:
            logger.info(f"Loading Wav2Vec2 model on {device}")
            from transformers import pipeline
            cls._wav2vec2_model = pipeline(
                "automatic-speech-recognition",
                model="facebook/wav2vec2-base-960h",
                device=0 if device == "cuda" else -1
            )
            cls._device = device
        return cls._wav2vec2_model

    @classmethod
    def clear(cls):
        """Clear cache to free memory."""
        cls._whisper_model = None
        cls._wav2vec2_model = None
        cls._device = "cpu"

# Usage in analyzer_raw.py:
# Replace: import whisper; model = whisper.load_model(...)
# With: from src.audio.model_cache import ModelCache
#       model = ModelCache.get_whisper(device)
```

**Expected Savings:** 10-15 seconds per request after first request

---

## Priority 2: Conditional Wav2Vec2 Detection (Save 15-20 seconds conditionally)

### Current Issue

Always runs Wav2Vec2 even for clean, fluent speech where it's not needed.

### Implementation

In `src/core/analyzer_raw.py`, add conditional check before Wav2Vec2:

```python
# Step 4: Detect fillers with Wav2Vec2 (CONDITIONAL)
print("\n[4/5] Checking need for subtle filler detection...")

filler_count = df_words_whisper_raw['is_filler'].sum()
filler_ratio = filler_count / len(df_words_whisper_raw) if len(df_words_whisper_raw) > 0 else 0

# Only run Wav2Vec2 if we detected few fillers (likely has subtle ones we missed)
if filler_ratio < 0.05:  # Less than 5% fillers detected
    print(f"  Filler ratio: {filler_ratio:.1%} - Running Wav2Vec2 for subtle detection...")
    df_wav2vec_fillers = detect_fillers_wav2vec(audio_path, df_aligned_words)
else:
    print(f"  Filler ratio: {filler_ratio:.1%} - Skipping Wav2Vec2 (sufficient filler detection)")
    df_wav2vec_fillers = pd.DataFrame()  # Empty
```

**Expected Savings:** 15-20 seconds for fluent speakers with many obvious fillers

---

## Priority 3: Skip Redundant WhisperX Alignment (Save 5-10 seconds)

### Current Issue

WhisperX re-extracts confidence that Whisper already provides.

### Implementation

In `src/core/analyzer_raw.py`, skip WhisperX for confidence-only:

```python
# Step 3: Skip WhisperX alignment (use Whisper confidence directly)
print("\n[3/5] Using Whisper confidence directly (WhisperX skipped)...")

# Whisper already provides confidence via get_text_with_confidence()
# No need for WhisperX alignment - it's redundant for our use case
# (Skip 15-20 seconds of processing)

# If WhisperX was needed for word-level timing, enable below:
# df_aligned_words = align_words_whisperx(...)
```

**Expected Savings:** 5-10 seconds

---

## Priority 4: Combine LLM Calls (Save 5-8 seconds)

### Current Issue

Two separate LLM API calls:

1. Band scoring LLM call (~10-15s)
2. Annotation extraction call (~15-20s)

### Implementation

Create combined LLM call in `src/core/llm_processing.py`:

```python
async def extract_llm_analysis_combined(
    transcript: str,
    speech_context: str = "conversational",
    context_metadata: dict = None,
    metrics: dict = None  # NEW: include metrics
) -> dict:
    """
    Combined LLM analysis - semantic + band input in one call.
    Returns both band factors and annotations.
    """

    # Prepare single prompt that asks for both band scoring and annotations
    system_prompt = """You are an IELTS speaking assessor...

    TASK 1: Semantic Band Factors
    - Assess topic relevance
    - Estimate listener effort
    - Evaluate coherence

    TASK 2: Detailed Annotations
    - Find grammar errors
    - Find vocabulary issues
    - Mark advanced structures

    Return as JSON:
    {
        "band_factors": {...},
        "annotations": {...}
    }
    """

    response = await llm_call(system_prompt, transcript)

    parsed = json.loads(response)
    return {
        "band_factors": parsed["band_factors"],
        "annotations": parsed["annotations"]
    }
```

**Expected Savings:** 5-8 seconds (one API call instead of two)

---

## Priority 5: Parallel Transcription + Phonemes (Already Done)

### Status: ✅ Already Implemented

In `src/core/analyzer_raw.py` line 125-145:

```python
transcribe_task = asyncio.to_thread(transcribe_verbatim_fillers, ...)
phonemes_task = asyncio.to_thread(detect_phonemes_wav2vec, ...)
monotone_task = asyncio.to_thread(is_monotone_speech, ...)

results = await asyncio.gather(transcribe_task, phonemes_task, monotone_task)
```

**Already Saving:** ~10 seconds (tasks run in parallel)

---

## Implementation Checklist

### Quick Wins (1 hour)

- [ ] Priority 2: Add conditional Wav2Vec2 (check filler ratio)
- [ ] Priority 3: Comment out WhisperX alignment (use Whisper confidence)
- [ ] Update documentation

### Medium Effort (2-3 hours)

- [ ] Priority 1: Implement model caching
- [ ] Test model reuse across requests
- [ ] Verify memory usage

### Advanced (4-6 hours)

- [ ] Priority 4: Combine LLM calls
- [ ] Update LLM processing pipeline
- [ ] Regression testing

---

## Performance Impact Summary

| Optimization         | Time Saved | Effort | Impact                       |
| -------------------- | ---------- | ------ | ---------------------------- |
| Conditional Wav2Vec2 | 15-20s     | ⭐     | High (conditional)           |
| Skip WhisperX        | 5-10s      | ⭐     | Medium                       |
| Model Caching        | 10-15s     | ⭐⭐   | High (per-request after 1st) |
| Combined LLM         | 5-8s       | ⭐⭐⭐ | Medium                       |
| **Total**            | **40-50s** | -      | **40-50% faster**            |

---

## Testing Recommendations

Before deploying optimizations:

1. **Correctness Tests**

   ```python
   # Verify band scores match before/after
   full_result = analyze_speech_full(audio)
   optimized_result = analyze_speech_optimized(audio)
   assert full_result['band_scores']['overall_band'] == optimized_result['band_scores']['overall_band']
   ```

2. **Performance Benchmarks**

   ```python
   import time
   start = time.time()
   result = analyze_speech(audio)
   elapsed = time.time() - start
   print(f"Elapsed: {elapsed:.1f}s")
   ```

3. **Edge Cases**
   - Very quiet audio
   - Very fluent speech
   - Very disfluent speech
   - Multiple speakers

---

## Future Optimization Ideas

1. **Audio Pre-processing**
   - Cache audio after loading
   - Reuse preprocessed segments

2. **Metric Caching**
   - Cache WPM/pause calculations for similar audio

3. **Batch Processing**
   - Process multiple files in batch mode
   - Share models across batch

4. **GPU Optimization**
   - Use GPU for all ML operations
   - Batch tensor operations

5. **Smart Model Selection**
   - Use "tiny" Whisper for quick screening
   - Use "base" for final analysis only if needed

---

## Monitoring

Add performance tracking to monitor optimizations:

```python
from src.utils.logging_config import logger
import time

def log_stage_timing(stage_name: str):
    """Decorator to log stage execution time."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            elapsed = time.time() - start
            logger.info(f"[TIMING] {stage_name}: {elapsed:.1f}s")
            return result
        return wrapper
    return decorator

# Usage:
@log_stage_timing("Whisper Transcription")
async def transcribe_step():
    ...
```

This creates a clear audit trail of performance improvements.
