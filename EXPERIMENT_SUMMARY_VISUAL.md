# Experiment Scripts - Visual Overview

## 📋 Quick Reference

### Test 1: Fast Analyzer

```
📁 File: test_quick_fast.py
⏱️  Runtime: 20-30 seconds (includes model loading)
📊 Analyzes: data/ielts_part_2/ielts7.wav
🎯 Purpose: Verify fast analyzer works (15-25 second core runtime)
📤 Output: outputs/final_report_fast_ielts7.json

Command: python test_quick_fast.py
```

### Test 2: Combined LLM Experiment

```
📁 File: test_combined_llm_experiment.py
⏱️  Runtime: 1-2 minutes (includes API calls)
📊 Analyzes: 3 pre-analyzed files
🎯 Purpose: Test if combining 2 LLM calls into 1 works
📤 Output: Console comparison table
💾 Saved: No file (results printed only)

Command: python test_combined_llm_experiment.py
```

---

## 🔄 Flow Diagrams

### Fast Analyzer Test Flow

```
┌─────────────────────────────────────────────────────────────┐
│ START: test_quick_fast.py                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Load ielts7.wav    │
        │ (from data/)       │
        └────────┬───────────┘
                 │
                 ▼
     ┌──────────────────────────────┐
     │ Call: analyze_speech_fast()  │
     └──────────┬───────────────────┘
                │
                ├─ [1/3] Whisper transcription (30-40s)
                ├─ [2/3] Mark fillers (5s)
                └─ [3/3] Metrics + scoring (2s)
                │
                ▼ Total: 15-25 seconds
        ┌──────────────────────────────┐
        │ Display Results              │
        ├─ Verdict                     │
        ├─ Band scores (metrics-only)  │
        ├─ Metrics (WPM, pauses, etc.) │
        └─ Comparison table            │
                │
                ▼
        ┌──────────────────────────────┐
        │ Save to outputs/             │
        │ final_report_fast_ielts7.json│
        └──────────────────────────────┘
```

### Combined LLM Experiment Flow

```
┌─────────────────────────────────────────────────────────────┐
│ START: test_combined_llm_experiment.py                      │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
    ┌─────────────┐  ┌─────────────┐
    │ Load audio_ │  │ Load band_  │
    │ analysis/*  │  │ results/*   │
    │ (metrics)   │  │ (baseline)  │
    └────────┬────┘  └────────┬────┘
             │                 │
             └────────┬────────┘
                      │
              ┌───────▼───────┐
              │ For each file │
              └───────┬───────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
   ┌─────────────────┐    ┌──────────────────────┐
   │ Extract:        │    │ Get baseline:        │
   │ - transcript    │    │ - band scores        │
   │ - metrics       │    │ - confidence         │
   └────────┬────────┘    └──────────┬───────────┘
            │                        │
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────────────┐
            │ Call: combined_llm_analysis()  │
            │ (makes 1 LLM call instead of 2)
            └────────────┬───────────────────┘
                         │
                         ▼
            ┌────────────────────────────────┐
            │ Compare Results:               │
            │ - Baseline vs Combined         │
            │ - Calculate differences        │
            │ - Assess annotation quality    │
            └────────────┬───────────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
     ▼      ▼      ▼      ▼          ▼
[ielts5.5] [ielts7] [ielts8.5] [summary]
   │        │        │         │
   └────────┴────────┴─────────┘
            │
            ▼
┌──────────────────────────────────────┐
│ Print Summary Report:                │
│ - Average band difference            │
│ - Success rating                     │
│ - Recommendations                    │
└──────────────────────────────────────┘
```

---

## 📊 Data Flow

### Test 1: Fast Analyzer

```
ielts7.wav (audio file)
    ↓
analyze_speech_fast()
    ├─ Whisper transcription
    ├─ Filler marking (Whisper only)
    └─ Metrics-only band scoring
    ↓
results = {
  mode: "fast",
  verdict: { fluency_score, readiness },
  band_scores: { overall, criterion_bands, confidence },
  normalized_metrics: { wpm, pause_freq, ... },
  raw_transcript: "...",
  statistics: { word_counts, filler_% },
  word_timestamps: [...],
  ...
}
    ↓
outputs/final_report_fast_ielts7.json
```

### Test 2: Combined LLM Experiment

```
audio_analysis/ielts7.json (pre-analyzed)
    ├─ Extract: transcript, metrics
    │
band_results/ielts7.json (baseline)
    ├─ Extract: baseline band_scores
    │
combined_llm_analysis()
    ├─ Call: LLM with unified prompt
    │  (requests: band_scores + annotations in one call)
    │
    └─ Returns: {
         band_scores: {...},
         annotations: {...},
         confidence: 0.XX
       }
    │
Compare: baseline vs combined
    ├─ Overall band diff
    ├─ Criterion-wise diffs
    └─ Annotations quality
    │
Print: Comparison table + summary
```

---

## 📈 Expected Results

### Test 1: Fast Analyzer

```
┌──────────────────────────────────────────┐
│ Expected Results                         │
├──────────────────────────────────────────┤
│                                          │
│ ⏱️  Runtime: 15-25 seconds              │
│    (plus 5-10s for Whisper model load)   │
│                                          │
│ 🎯 Band Scores:                         │
│    Overall: 6.5 (metrics-only)          │
│    Criterion bands: populated           │
│    Confidence: ~0.65 (lower than full) │
│                                          │
│ 📊 Metrics:                             │
│    WPM: ~109                            │
│    Pause freq: ~1.4/min                 │
│    Filler %: ~2-3%                      │
│                                          │
│ ✅ Status: FAST MODE ⚡                 │
│           (Wav2Vec2 + LLM skipped)     │
│                                          │
└──────────────────────────────────────────┘
```

### Test 2: Combined LLM Experiment

```
┌────────────────────────────────────────────┐
│ Scenario A: SUCCESS ✅                    │
├────────────────────────────────────────────┤
│ Average Band Difference: 0.00-0.25        │
│ Rating: EXCELLENT                         │
│ Recommendation: Implement immediately     │
│ Savings: 5-8 seconds per request         │
│                                            │
├────────────────────────────────────────────┤
│ Scenario B: GOOD ✅                       │
├────────────────────────────────────────────┤
│ Average Band Difference: 0.25-0.50        │
│ Rating: GOOD                              │
│ Recommendation: Implement with confidence │
│ Savings: 5-8 seconds per request         │
│                                            │
├────────────────────────────────────────────┤
│ Scenario C: ACCEPTABLE ⚠️                 │
├────────────────────────────────────────────┤
│ Average Band Difference: 0.50-1.00        │
│ Rating: ACCEPTABLE                        │
│ Recommendation: Refine prompt, retry      │
│ Savings: Conditional                     │
│                                            │
├────────────────────────────────────────────┤
│ Scenario D: NEEDS WORK ❌                 │
├────────────────────────────────────────────┤
│ Average Band Difference: > 1.00           │
│ Rating: NEEDS WORK                        │
│ Recommendation: Revise approach           │
│ Savings: Not viable                      │
│                                            │
└────────────────────────────────────────────┘
```

---

## 🎯 Success Criteria

### Fast Analyzer Test

```
✅ PASS if:
   └─ Runtime is 15-25 seconds (core analysis)
   └─ Band scores are generated
   └─ Metrics are populated
   └─ Output shows "FAST MODE" confirmation

❌ FAIL if:
   └─ Runtime is > 30 seconds
   └─ Band scores are missing/None
   └─ Errors occur during execution
```

### Combined LLM Experiment

```
✅ PASS if:
   └─ Average band difference ≤ 0.5
   └─ Annotations are available
   └─ All 3 files complete successfully

⚠️  INVESTIGATE if:
   └─ Average band difference 0.5-1.0
   └─ Some criterion scores differ > 1.0

❌ FAIL if:
   └─ Average band difference > 1.0
   └─ API errors prevent completion
   └─ Results are completely different
```

---

## 📝 What to Check in Console Output

### From test_quick_fast.py

```
Look for these lines:

[FAST MODE] Analyzing audio: ...
[1/3] Transcribing with Whisper (fast mode - no alignment)...
[2/3] Marking filler words (Whisper only - skipping Wav2Vec2)...
[3/3] Calculating fluency metrics (metrics-only band scoring)...
[TIMING] Completed in XX.X seconds

If you see these: ✅ Test is working!
```

### From test_combined_llm_experiment.py

```
Look for these lines:

[BASELINE - Existing Results]
  Overall Band: X.X

[EXPERIMENT - Combined LLM Call]
  Overall Band: X.X

[COMPARISON - Baseline vs Combined]
  Overall Band Difference: 0.XX

════════════════════════════════════════════════════
Average Band Difference: X.XX
✓ EXCELLENT: Results are nearly identical...

If you see this at the end: ✅ Experiment is done!
```

---

## 🚀 Running the Experiments

### Quick Reference

```bash
# Test 1: Fast Analyzer (quick)
python test_quick_fast.py

# Test 2: Combined LLM (comprehensive)
python test_combined_llm_experiment.py

# Check results
cat outputs/final_report_fast_ielts7.json
```

### Timeline

```
test_quick_fast.py:
  Loading Whisper model:  5-10 seconds
  Core analysis:          15-25 seconds
  ─────────────────────────────────────
  Total:                  20-35 seconds

test_combined_llm_experiment.py:
  Setup:                  5 seconds
  For each of 3 files:
    - Load data:          2 seconds
    - LLM call:           20-30 seconds
    - Compare:            5 seconds
    - Delay:              2 seconds
  ─────────────────────────────────────
  Total:                  ~90-120 seconds (1.5-2 minutes)

GRAND TOTAL:            ~2-3 minutes
```

---

## 📚 Documentation Files

```
├─ EXPERIMENT_QUICK_START.md
│  └─ Start here! Quick reference guide
│
├─ EXPERIMENT_TEST_SCRIPTS_README.md
│  └─ Technical details and flow diagrams
│
├─ EXPERIMENT_SUMMARY.md
│  └─ Comprehensive overview
│
└─ This file: EXPERIMENT_SUMMARY_VISUAL.md
   └─ Visual guide and flowcharts
```

---

## ⚡ TL;DR

```
1. Run: python test_quick_fast.py
   Check: Does it finish in 15-25 seconds?

2. Run: python test_combined_llm_experiment.py
   Check: Is average band difference ≤ 0.5?

3. Review results
   If both ✅: Great! Fast analyzer works, LLM combo viable
   If mixed ⚠️: Fast works, LLM needs refinement
   If ❌: Fast works, LLM approach not viable yet
```
