# Experiment & Test Scripts - Summary

## Files Created

### 1. `test_combined_llm_experiment.py`

**Purpose**: Test whether combining LLM band scoring + annotations into a single call maintains quality

**What It Does**:

1. Loads pre-analyzed audio files from `outputs/audio_analysis/`
2. Loads existing band results from `outputs/band_results/` (baseline for comparison)
3. Runs a **combined LLM call** that asks for both:
   - Band scores (fluency, pronunciation, lexical, grammar)
   - Detailed annotations (grammar errors, vocabulary level, discourse markers)
4. Compares combined LLM results with existing baseline results
5. Calculates differences in band scores
6. Reports findings with recommendations

**How to Run**:

```bash
python test_combined_llm_experiment.py
```

**Expected Output**:

- Per-file comparison of baseline vs combined LLM results
- Overall band score differences
- Criterion-by-criterion comparison
- Annotation quality assessment
- Summary statistics and recommendations

**Test Files**:

- ielts5.5.json
- ielts7.json
- ielts8.5.json

**Key Metrics**:

- Average band difference (should be ≤ 0.5 if successful)
- Max difference per criterion
- Annotation completeness

---

### 2. `test_quick_fast.py`

**Purpose**: Quick test of the fast analyzer variant (15-25 second runtime)

**What It Does**:

1. Uses the same audio file as `test_quick.py` (ielts7.wav)
2. Runs `analyze_speech_fast()` directly (bypasses full engine pipeline)
3. Measures execution time
4. Displays results in comparison with what full analysis would show
5. Highlights what's skipped in fast mode

**How to Run**:

```bash
python test_quick_fast.py
```

**Expected Output**:

- Runtime measurement (should be 15-25 seconds)
- Verdict (fluency score, readiness)
- Band scores (metrics-only, no LLM)
- Metrics summary
- Limitations of fast mode
- Comparison table (Fast vs Full)

**Key Features**:

- Shows what IS included (Whisper, basic metrics, band estimate)
- Shows what ISN'T included (Wav2Vec2, LLM, detailed feedback)
- Use case recommendations
- Side-by-side comparison with full analysis

---

## Experiment Flow

### Combined LLM Call Experiment

```
test_combined_llm_experiment.py
    ↓
For each test file (ielts5.5, ielts7, ielts8.5):
    ├─ Load audio_analysis/.../filename.json
    │  └─ Extract: transcript, metrics
    ├─ Load band_results/.../filename.json
    │  └─ Get: baseline band scores
    ├─ Call: combined_llm_analysis(transcript, metrics)
    │  └─ Returns: band_scores + annotations in ONE call
    ├─ Compare:
    │  ├─ Overall band difference
    │  ├─ Each criterion difference
    │  └─ Annotations quality
    └─ Store results

After all files:
    ├─ Calculate average band difference
    ├─ Determine if combined call is viable
    └─ Make recommendations
```

### Fast Analysis Test Flow

```
test_quick_fast.py
    ↓
Load audio: data/ielts_part_2/ielts7.wav
    ↓
Call: analyze_speech_fast(audio_path, "conversational", "cpu")
    ↓
Inside analyze_speech_fast():
    ├─ [1/3] Whisper transcription (30-40s)
    ├─ [2/3] Mark fillers (Whisper only, 5s)
    └─ [3/3] Score bands (metrics-only, 2s)

    Result: 15-25 seconds total
    ↓
Display results:
    ├─ Verdict
    ├─ Band scores (metrics-only)
    ├─ Transcript
    ├─ Statistics
    ├─ Normalized metrics
    ├─ What's NOT included
    ├─ Use cases
    └─ Comparison table
```

---

## Expected Results

### Combined LLM Experiment

**Success Criteria**:

- Average band difference ≤ 0.25: **EXCELLENT** - use combined call
- Average band difference ≤ 0.5: **GOOD** - use combined call
- Average band difference ≤ 1.0: **ACCEPTABLE** - may need tweaking
- Average band difference > 1.0: **CAUTION** - needs refinement

**What We're Testing**:

- Does asking for both band scores AND annotations in one prompt work?
- Do we get the same quality results?
- Can we save 5-8 seconds by combining calls?

### Fast Analysis Test

**Expected Output**:

- Runtime: 15-25 seconds
- Band scores present but lower confidence
- Transcript and basic metrics included
- Limitations clearly noted
- Comparison shows 5-8x speedup

---

## How to Use Results

### From Combined LLM Experiment

```
If average_diff ≤ 0.5:
    → Implement combined LLM call in production
    → Update src/core/llm_processing.py
    → Save 5-8 seconds per request

If average_diff > 0.5:
    → Refine the combined prompt
    → Try different model/temperature
    → Test on larger sample (20-30 files)
```

### From Fast Analysis Test

```
Use /analyze-fast for:
    • Development and testing
    • Real-time dashboards
    • Bulk screening
    • Quick feedback

Use /analyze for:
    • Production scoring
    • Detailed feedback
    • High-stakes assessment
```

---

## Key Differences: Current vs Proposed

### Current Pipeline

```
Call 1: extract_llm_annotations(transcript)
    ↓ (8-10 seconds)
    ├─ Grammar errors
    ├─ Vocabulary assessment
    └─ Discourse markers

Call 2: score_ielts_speaking(metrics, transcript, use_llm=True)
    ↓ (5-8 seconds)
    └─ Band scores

Total LLM time: 13-18 seconds (2 calls)
```

### Proposed Pipeline (if experiment succeeds)

```
Combined Call: unified_llm_analysis(transcript, metrics)
    ↓ (5-8 seconds)
    ├─ Band scores
    ├─ Grammar errors
    ├─ Vocabulary assessment
    └─ Discourse markers

Total LLM time: 5-8 seconds (1 call)

Time saved: ~8 seconds per request (50% reduction)
```

---

## Running Both Tests

```bash
# First, test fast analysis (quick, 15-25s)
python test_quick_fast.py

# Then, run combined LLM experiment (requires API calls, slower)
# This may take 1-2 minutes with API delays
python test_combined_llm_experiment.py
```

---

## Files Examined During Experiment

**Input Files**:

- outputs/audio_analysis/ielts5.5.json (2933 lines)
- outputs/audio_analysis/ielts7.json (2933 lines)
- outputs/audio_analysis/ielts8.5.json (2933 lines)

**Baseline for Comparison**:

- outputs/band_results/ielts5.5.json
- outputs/band_results/ielts7.json
- outputs/band_results/ielts8.5.json

**Data Extracted**:

- Raw transcript
- Fluency metrics (WPM, pauses, etc.)
- Word confidence scores
- Baseline band scores

---

## Notes

- No core code changed - purely experimental
- Uses existing pre-analyzed data
- Tests are non-destructive (read-only)
- Results are exported to outputs/ for inspection
- Fast test uses the new analyzer_fast.py (already implemented)
- Combined LLM test validates a proposed optimization
