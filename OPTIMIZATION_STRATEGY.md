# Optimization Strategy & Fast Analysis Variant

## Analysis Overview

The current pipeline is comprehensive but includes several expensive operations. Here's the breakdown:

### Current Pipeline Stages (5 stages total)

**Stage 1: Raw Audio Analysis (100-120 seconds)**

- Transcribe with Whisper (sequential with device loading)
- WhisperX alignment (redundant confidence extraction)
- Wav2Vec2 phoneme detection (expensive ML model)
- Monotone speech detection
- Total: ~80-100s

**Stage 2: Build Analysis Report (~5 seconds)**

- Metric calculations from raw analysis

**Stage 3: Band Scoring (~2-3 seconds)**

- LLM call for semantic evaluation (~10-15 tokens)
- Metric-based scoring

**Stage 4: LLM Annotations (~15-20 seconds)**

- Another LLM call with transcript (~1000+ tokens)
- Grammar, vocab, coherence analysis

**Stage 5: Response Building (~0.5 seconds)**

---

## Optimization Opportunities (Quality-Preserving)

### 1. **Parallel Processing Improvements**

**Current Issue:** Some parallelizable tasks run sequentially
**Fix:** Ensure WhisperX and Wav2Vec2 run in true parallel threads
**Impact:** Save 5-10 seconds
**Code Location:** `src/core/analyzer_raw.py`, lines 125-145

### 2. **Eliminate Redundant Confidence Extraction**

**Current Issue:** Whisper extracts confidence, then WhisperX re-extracts it
**Fix:** Use Whisper's confidence directly, skip WhisperX alignment for confidence-only
**Impact:** Save 10-15 seconds
**Code Location:** `src/core/analyzer_raw.py`, lines 155-180

### 3. **Skip Wav2Vec2 for Clean Speech**

**Current Issue:** Always runs Wav2Vec2 even for fluent speech
**Fix:** Only run if initial filler count is low (speech likely has subtle fillers)
**Impact:** Save 15-20 seconds conditionally
**Code Location:** `src/core/analyzer_raw.py`, line 195

### 4. **Cache Model Instances**

**Current Issue:** Models loaded per request (Whisper, Wav2Vec2, etc.)
**Fix:** Load once, reuse across requests
**Impact:** Save 10-15 seconds per request
**Code Location:** `src/audio/whisper_interface.py`, `src/audio/wav2vec_interface.py`

### 5. **Reduce LLM Token Count in Band Scoring**

**Current Issue:** Full transcript sent to LLM for band scoring
**Fix:** Send only key metrics and snippet of transcript
**Impact:** Save 2-3 seconds (reduce token usage)
**Code Location:** `src/core/ielts_band_scorer.py`, LLM scoring function

### 6. **Batch LLM Calls**

**Current Issue:** Two separate LLM calls (band scoring + annotations)
**Fix:** Combine into single call with structured output
**Impact:** Save 5-8 seconds
**Code Location:** `src/core/llm_processing.py`

---

## Fast Analysis Variant

A lightweight `/analyze-fast` endpoint that:

- **Skip Wav2Vec2** (most expensive)
- **Skip LLM annotations** (15-20 seconds)
- **Skip WhisperX alignment** (redundant)
- **Simplified band scoring** (metrics-only, no LLM)
- **Still accurate for basic metrics**

### Expected Runtime

- Full Analysis: 100-120 seconds
- Fast Analysis: 15-25 seconds
- **Speedup: 5-8x faster**

### Quality Trade-offs

- ❌ No subtle filler detection (Wav2Vec2)
- ❌ No semantic analysis (LLM)
- ❌ No grammar/vocabulary feedback
- ✅ Still accurate WPM, pause metrics, basic band estimate
- ✅ Accurate confidence scores
- ✅ Basic fluency band estimate

### Use Cases for Fast Variant

1. **Development/Testing:** Quick feedback during dev
2. **Bulk Analysis:** Initial screening of many files
3. **Real-time Dashboards:** Show instant basic metrics
4. **A/B Testing:** Quick comparison without waiting

---

## Implementation Plan

### Phase 1: Quality-Preserving Optimizations (No breaking changes)

1. Add model caching for Whisper, Wav2Vec2, WhisperX
2. Skip redundant WhisperX confidence extraction
3. Conditional Wav2Vec2 (skip if low filler ratio)
4. Combine parallel LLM calls

### Phase 2: Fast Variant Implementation

1. Create `analyze_speech_fast()` in `src/core/analyzer_fast.py`
2. Add `/analyze-fast` endpoint in both routers
3. Tests comparing full vs fast output
4. Documentation on fast variant limitations

### Phase 3: Smart Mode Selection

1. Auto-detect when fast variant is appropriate
2. Add `speed` parameter to endpoints (full/fast/auto)

---

## Files to Modify

1. **src/core/analyzer_raw.py** - Add conditional logic for Wav2Vec2, optimize parallelization
2. **src/core/analyzer_fast.py** - NEW: Fast variant (skip expensive ops)
3. **src/core/ielts_band_scorer.py** - Reduce LLM token usage
4. **src/core/llm_processing.py** - Batch LLM calls
5. **src/audio/whisper_interface.py** - Model caching
6. **src/api/v1.py** - Add /analyze-fast endpoint
7. **src/api/direct.py** - Add /analyze-fast endpoint

---

## Estimated Time Savings

| Operation | Current      | Optimized  | Savings    |
| --------- | ------------ | ---------- | ---------- |
| Whisper   | 30-40s       | 30-40s     | 0s         |
| WhisperX  | 15-20s       | 5-10s      | 5-10s      |
| Wav2Vec2  | 15-20s       | Skip\*     | 15-20s\*   |
| LLM Call1 | 10-15s       | 5-8s       | 2-7s       |
| LLM Call2 | 15-20s       | Skip\*     | 15-20s\*   |
| **Total** | **100-120s** | **40-60s** | **40-60s** |

\*Fast variant only
