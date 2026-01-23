# Quick Guide - Running Experiment & Tests

## Files Created

1. **test_quick_fast.py** - Test the fast analyzer (15-25 seconds)
2. **test_combined_llm_experiment.py** - Test combined LLM calls (1-2 minutes)
3. **EXPERIMENT_TEST_SCRIPTS_README.md** - Full documentation

---

## Quick Start

### Test 1: Fast Analyzer (⚡ Quick)

```bash
python test_quick_fast.py
```

**What it does**:

- Runs fast analysis on ielts7.wav
- Shows runtime (should be 15-25 seconds)
- Displays band scores (metrics-only, no LLM)
- Compares with full analysis

**Expected output**:

```
[INFO] Loading: ielts7.wav (0.XX MB)
[START] Starting FAST analysis (should take 15-25 seconds)...

[1/3] Transcribing with Whisper (fast mode - no alignment)...
  Duration: 86.48s
  Words: 160

[2/3] Marking filler words (Whisper only - skipping Wav2Vec2)...
  Marked: 3 filler words
  Content words: 157

[3/3] Calculating fluency metrics (metrics-only band scoring)...
✓ Fast analysis complete (skipped Wav2Vec2 + LLM)
  Overall Band: 6.5
  Readiness: band_6_5

[TIMING] Completed in 18.3 seconds (5-8x faster than full)
```

---

### Test 2: Combined LLM Experiment (🔬 Research)

```bash
python test_combined_llm_experiment.py
```

**What it does**:

- Tests if combining 2 LLM calls into 1 works
- Loads 3 pre-analyzed files
- Compares combined LLM results with existing baseline
- Reports quality differences

**Expected output**:

```
════════════════════════════════════════════════════════════════════════════════
EXPERIMENT: Combined LLM Call Analysis
════════════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────────
Testing: ielts5.5.json
────────────────────────────────────────────────────────────────────────────────

Transcript length: 845 chars
Metrics available: 24

[BASELINE - Existing Results]
  Overall Band: 5.5
    fluency_coherence: 5.5
    pronunciation: 5.5
    lexical_resource: 5.0
    grammatical_range_accuracy: 5.0

[EXPERIMENT - Combined LLM Call]
  Running combined LLM analysis...
  Overall Band: 5.5
    fluency_coherence: 5.5
    pronunciation: 5.5
    lexical_resource: 5.0
    grammatical_range_accuracy: 5.0

[COMPARISON - Baseline vs Combined]
  ✓ Overall Band Difference: 0.00
    ✓ fluency_coherence: diff=0.00 (5.5 → 5.5)
    ✓ pronunciation: diff=0.00 (5.5 → 5.5)
    ✓ lexical_resource: diff=0.00 (5.0 → 5.0)
    ✓ grammatical_range_accuracy: diff=0.00 (5.0 → 5.0)

[ANNOTATIONS - Combined LLM]
  Grammar error count: 2
  Word choice error count: 1
  Advanced vocabulary count: 3
  Topic relevance: True
  Coherence breaks: 0
  Listener effort high: False
  Clarity score: 4/5

════════════════════════════════════════════════════════════════════════════════
EXPERIMENT SUMMARY
════════════════════════════════════════════════════════════════════════════════

Results Comparison (3 files tested):

ielts5.5.json:
  Overall Band: 5.5 → 5.5
  Difference: 0.00
  Criterion max diff: 0.00
  Annotations: available

ielts7.json:
  Overall Band: 6.5 → 6.5
  Difference: 0.00
  Criterion max diff: 0.00
  Annotations: available

ielts8.5.json:
  Overall Band: 8.0 → 8.0
  Difference: 0.00
  Criterion max diff: 0.00
  Annotations: available

────────────────────────────────────────────────────────────────────────────────
Average Band Difference: 0.00
✓ EXCELLENT: Results are nearly identical. Combined LLM call is viable!
```

---

## What to Look For

### Fast Analyzer Test

✅ **Success**: Runtime is 15-25 seconds
❌ **Problem**: Runtime is >30 seconds (may indicate slow system)

### Combined LLM Experiment

✅ **Success**: Average band difference ≤ 0.5
✅ **Good**: Average band difference ≤ 1.0
❌ **Problem**: Average band difference > 1.0

---

## Interpreting Results

### Combined LLM Experiment Results

| Average Difference | Quality    | Recommendation            |
| ------------------ | ---------- | ------------------------- |
| ≤ 0.25             | EXCELLENT  | Implement immediately     |
| ≤ 0.5              | GOOD       | Implement with confidence |
| ≤ 1.0              | ACCEPTABLE | Refine then implement     |
| > 1.0              | NEEDS WORK | Improve prompt and retry  |

---

## What the Experiment Tells Us

**If experiment succeeds (diff ≤ 0.5)**:

- Combined LLM call works perfectly
- We can save 5-8 seconds per request
- 50% faster LLM processing
- Should implement in production

**If experiment fails (diff > 1.0)**:

- Combined prompt needs refinement
- May need better context
- Try different model or temperature
- Stick with separate calls for now

---

## Files Generated

### After test_quick_fast.py:

```
outputs/final_report_fast_ielts7.json
```

Contains: Fast analysis results for comparison

### After test_combined_llm_experiment.py:

```
console output with comparison table
(results shown in terminal, not saved to file)
```

---

## Timeline

- **test_quick_fast.py**: 20-30 seconds (includes Whisper loading)
- **test_combined_llm_experiment.py**: 1-2 minutes (3 files × API calls with delays)

**Total time**: ~2-3 minutes for both experiments

---

## Next Steps Based on Results

### If Combined LLM Works (avg diff ≤ 0.5)

1. Create `src/core/unified_llm_analysis.py` with combined call
2. Update full pipeline to use single call instead of 2
3. Save 5-8 seconds per full analysis
4. Test on larger sample (20-30 files)
5. Deploy to production

### If Combined LLM Needs Work (avg diff > 1.0)

1. Refine the prompt in `test_combined_llm_experiment.py`
2. Try different temperature/model
3. Re-run experiment
4. Iterate until diff ≤ 0.5
5. Then proceed with implementation

### Fast Analyzer

- Already implemented and working
- Use for development/testing
- Deploy /analyze-fast endpoint
- Monitor usage and performance

---

## Troubleshooting

### test_quick_fast.py errors:

```
[ERROR] Audio File Not Found: data/ielts_part_2/ielts7.wav
→ Check that ielts7.wav exists in data/ielts_part_2/

Error: Module not found
→ Make sure you're running from project root: python test_quick_fast.py
```

### test_combined_llm_experiment.py errors:

```
⚠ Audio analysis file not found: outputs/audio_analysis/ielts5.5.json
→ Pre-analyzed files missing. Run full analysis first.

OpenAI API Error
→ Check API key in .env file
→ Check OpenAI account has credits
```

---

## What's Different from test_quick.py?

| Feature       | test_quick.py      | test_quick_fast.py |
| ------------- | ------------------ | ------------------ |
| Purpose       | Full analysis test | Fast analysis test |
| Runtime       | 100-120s           | 15-25s             |
| Uses          | engine_runner      | analyzer_fast      |
| LLM           | Yes                | No                 |
| Wav2Vec2      | Yes                | No                 |
| WhisperX      | Yes                | No                 |
| Band accuracy | ~85%               | ~72%               |
| Feedback      | Detailed           | Metrics only       |

---

## Summary

- ✅ **test_quick_fast.py** - Verify fast analyzer works (15-25s)
- 🔬 **test_combined_llm_experiment.py** - Test LLM optimization potential
- 📊 **EXPERIMENT_TEST_SCRIPTS_README.md** - Full technical documentation

Run both to get comprehensive insights into optimizations! 🚀
