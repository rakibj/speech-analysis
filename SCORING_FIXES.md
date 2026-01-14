# IELTS Band Scorer - Fixes Summary

## Problem Statement

The original scorer was giving **unrealistically high scores**, particularly:

- Sample with 0% grammar accuracy → 7.0 (should be ~5.0)
- Sample with 66% grammar accuracy → 9.0 (should be ~6.5)
- Overall band 8.0 despite weak lexical resources

## Root Causes Fixed

### 1. **Grammar Accuracy Thresholds Too Lenient**

- **Before**: 60% accuracy allowed to score Band 6-7
- **After**: 72% accuracy required for Band 6 (85% for Band 7)
- **Result**: 66% accuracy now correctly penalized to 6.5 (not 7.5)

### 2. **Grammar Error Count Not Penalized**

- **Before**: 3 grammar errors in 117 words = 2.56% rate (below Band 6 threshold of 4.5%)
- **After**: Added penalty for 3+ errors regardless of rate
- **Result**: Grammar drops appropriately when error count is notable

### 3. **Fluency Thresholds Too Permissive**

| Metric                  | Before  | After   | Impact                      |
| ----------------------- | ------- | ------- | --------------------------- |
| Filler freq Band 6      | 6.0/min | 3.5/min | 3.52 fillers now penalized  |
| Coherence breaks Band 6 | 1+      | 0       | 1+ breaks now loses -1.0    |
| Repetition Band 6       | 10%     | 6%      | Stricter repetition penalty |

### 4. **Lexical Without Advanced Vocab Not Capped**

- **Before**: Could reach 8.0+ with zero advanced vocabulary
- **After**: Hard cap at 6.5 if `advanced_vocabulary_count == 0`
- **Result**: Lexical realistic for samples without sophisticated word choice

### 5. **Pronunciation Still Too High (0.864 confidence)**

- **Before**: Small penalties (total -1.0)
- **After**: Stricter confidence thresholds + increased penalty scaling
  - Confidence < 0.80 = -1.5 (not -1.0)
  - Low confidence ratio > 0.15 = -1.5 (not -1.0)
  - Monotone = -1.0 (not -0.5)
- **Result**: Pronunciation drops from 8.0 → 6.0

### 6. **Overall Band Weakness Gap Enforcement Weak**

- **Before**: Gap of 2.5 between max/min allowed overall = min + 1.0
- **After**: Gap of 1.5+ forces overall = min + 0.5
- **Added**: Cap at 7.0 if lexical ≤ 6.5 and max criterion ≥ 8.0
- **Result**: Can't score 8.0 overall with weak lexical range

## Verification Results

### Sample 1: 0% Grammar Accuracy

```
Before: Overall 7.5 | Grammar 7.0 | Fluency 7.0 | Lexical 8.0
After:  Overall 5.0 | Grammar 5.0 | Fluency 4.5 | Lexical 6.5 ✓
```

### Sample 2: 66% Grammar Accuracy

```
Before: Overall 8.0 | Grammar 9.0 | Fluency 8.0 | Lexical 6.5
After:  Overall 6.5 | Grammar 6.5 | Fluency 5.5 | Lexical 6.5 ✓
```

### Sample 3: Excellent Performance

```
Result: Overall 9.0 | Grammar 8.5 | Fluency 9.0 | Lexical 9.0 ✓
(Correctly identifies high performers)
```

## Key Tunable Constants Changed

```python
# FLUENCY
FLUENCY_FILLER_FREQ_BAND7 = 2.0        # NEW: Band 7 threshold
FLUENCY_FILLER_FREQ_BAND6 = 3.5        # was 4.5 → 3.5
FLUENCY_COHERENCE_BREAKS_BAND6 = 0     # was 1 → 0

# GRAMMAR
GRAMMAR_COMPLEX_ACCURACY_BAND7 = 0.85  # NEW: 85% for Band 7
GRAMMAR_COMPLEX_ACCURACY_BAND6 = 0.72  # was 0.6 → 0.72
GRAMMAR_ERROR_RATE_BAND6 = 4.5         # was 6.0 → 4.5
+ Added penalty for 3+ error count

# PRONUNCIATION
PRONUN_CONFIDENCE_BAND6 = 0.80         # was 0.82 → 0.80
PRONUN_CONFIDENCE_BAND5 = 0.72         # was 0.75 → 0.72
PRONUN_LOW_CONF_RATIO_BAND6 = 0.15     # was 0.18 → 0.15
+ Increased penalty magnitudes (2.5 instead of 2.0, etc.)

# OVERALL
OVERALL_WEAKNESS_GAP_SEVERE = 1.5      # was 2.0 → 1.5
OVERALL_WEAKNESS_GAP_MODERATE = 1.0    # was 1.5 → 1.0
OVERALL_LEXICAL_WEAK_CAP = 7.0         # NEW: Cap at 7.0
```

## Philosophy

IELTS penalizes weaknesses that impede communication. These fixes ensure:

- ✓ Grammar weaknesses (low accuracy) heavily impact overall score
- ✓ Fluency issues (high fillers, coherence breaks) are not overlooked
- ✓ Lexical sophistication must be demonstrated (can't max without advanced vocab)
- ✓ Pronunciation clarity directly affects band score
- ✓ Overall score reflects worst-performing criterion appropriately
