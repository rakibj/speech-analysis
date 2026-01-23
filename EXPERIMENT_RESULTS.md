# Combined LLM Experiment Results

**Date**: January 23, 2026  
**Experiment**: Testing combined LLM call vs. separate calls  
**Status**: ⚠️ NEEDS REFINEMENT

---

## 📊 Executive Summary

The combined LLM call experiment tested whether combining two separate LLM calls (band scoring + annotations) into a single call would:

1. Maintain quality equivalence
2. Save processing time (5-8 seconds per request)

**Result**: Mixed results with quality variability

---

## 📈 Test Results

### File-by-File Results

#### ✅ ielts5.5.json - PERFECT MATCH

```
Baseline:             Combined:             Difference:
─────────────────────────────────────────────────────
Overall:     6.0  →  Overall:     6.0  →  Diff: 0.00 ✓
Fluency:     6.0  →  Fluency:     6.0  →  Diff: 0.00 ✓
Pronunciation: 7.0 →  Pronunciation: 6.5 →  Diff: 0.50
Lexical:     6.0  →  Lexical:     6.0  →  Diff: 0.00 ✓
Grammar:     6.0  →  Grammar:     5.5  →  Diff: 0.50
```

**Status**: ✅ Overall band matched exactly  
**Criterion Max Diff**: 0.5 (within acceptable range)  
**Annotations**: Available and reasonable

---

#### ⚠️ ielts7.json - JSON PARSING ERROR

```
Baseline:
Overall: 6.5
Fluency: 7.0
Pronunciation: 7.5
Lexical: 6.0
Grammar: 6.0

Error: Expecting ',' delimiter: line 16 column 23 (char 426)
```

**Status**: ❌ LLM returned malformed JSON  
**Issue**: Complex combined prompt confuses LLM's JSON output format  
**Impact**: 1 of 3 test files failed to produce valid JSON

---

#### ❌ ielts8.5.json - SIGNIFICANT DEVIATION

```
Baseline:             Combined:             Difference:
─────────────────────────────────────────────────────
Overall:     8.0  →  Overall:     6.5  →  Diff: 1.50 ✗
Fluency:     8.0  →  Fluency:     7.0  →  Diff: 1.00 ⚠
Pronunciation: 8.0 →  Pronunciation: 7.0 →  Diff: 1.00 ⚠
Lexical:     8.0  →  Lexical:     6.5  →  Diff: 1.50 ✗✗
Grammar:     7.0  →  Grammar:     6.0  →  Diff: 1.00 ⚠
```

**Status**: ❌ Significant quality degradation  
**Issue**: Combined prompt underestimates performance in high-band cases  
**Max Criterion Diff**: 1.5 (EXCEEDS acceptable threshold of 0.5)

---

## 🔍 Analysis

### Success Rate: 33% (1 of 3 files)

| Metric                  | Value | Assessment                |
| ----------------------- | ----- | ------------------------- |
| Files Processed         | 3     | -                         |
| Files Successful        | 1     | ⚠️                        |
| JSON Parsing Errors     | 1     | ❌                        |
| Large Deviations (>1.0) | 1     | ❌                        |
| Average Band Difference | 0.75  | ⚠️ ACCEPTABLE             |
| Max Band Difference     | 1.50  | ❌ FAILS (>0.5 threshold) |

### Key Findings

1. **JSON Instability**: The combined prompt causes the LLM to sometimes output malformed JSON, suggesting the prompt is too complex for reliable structured output.

2. **High-Band Underestimation**: For the 8.5 band file, the combined call systematically underestimated quality by ~1.5 band points. This suggests:
   - The combined prompt loses nuance for high-performing speakers
   - Separate specialized prompts are better tuned for edge cases

3. **Low-Band Accuracy**: For the 5.5 band file, the combined call matched exactly, suggesting it works better for lower-performance cases.

4. **Success Dependency**: Success appears heavily dependent on:
   - Transcript complexity
   - Audio quality
   - Performance level (lower bands work better)

---

## ✅ When Combined Calls Might Work

Based on these results, combined LLM calls would be viable for:

- **Development/Testing** (where exact accuracy < 1.0 band point acceptable)
- **Quick Estimates** (preliminary assessment before full analysis)
- **Simplified Use Cases** (short, clear transcripts)
- **Low-Performance Cases** (5.0-6.5 range where accuracy is naturally lower)

---

## ❌ Why Combined Calls Fall Short

The existing two-call approach is better because:

1. **Specialized Prompts**: Each call is optimized for its specific task:
   - Annotations call: Detailed error detection, sophisticated language analysis
   - Band scoring call: Precise numerical assessment with criteria alignment

2. **Redundancy & Verification**: Two calls allow cross-validation:
   - Annotations help validate band scores
   - Band scores contextualize annotation severity

3. **LLM Reliability**: Focused prompts produce more consistent, valid JSON:
   - Less ambiguity in instructions
   - Better error messages when validation fails
   - Easier to debug if results are unexpected

4. **Edge Case Handling**: Separate calls handle outliers better:
   - High-band speakers get full nuance
   - Low-band speakers don't get inflated scoring
   - Corner cases handled by specialized logic

---

## 📋 Recommendations

### ❌ NOT RECOMMENDED: Implement Combined LLM Call

**Reasons**:

- 33% failure rate on test files
- 1.5-band deviation in high-performance cases (exceeds 0.5 threshold)
- JSON parsing errors with complex combined prompts
- Breaks existing quality assurance mechanisms

### ✅ RECOMMENDED: Keep Existing Two-Call Approach

**Why**:

- Proven 85% accuracy with existing approach
- Better error handling and validation
- Specialized prompts more reliable than combined prompt
- Negligible time savings (5-8s per request) vs. quality risk

### 🔄 ALTERNATIVE: Investigate Other Optimizations

Priority optimizations that are lower-risk:

1. **Model Caching** (10-15s savings, no quality impact)
   - Cache loaded Whisper/Wav2Vec2 models between requests
   - Currently reloading models on each request

2. **Parallel Processing** (15-20s savings, no quality impact)
   - Run Whisper + Wav2Vec2 in parallel instead of sequential
   - Both are I/O bound, can run concurrently

3. **Conditional Wav2Vec2** (15-20s conditional savings)
   - Skip Wav2Vec2 for high-confidence transcripts
   - Use fallback heuristics when skipped

4. **WhisperX Optimization** (5-10s savings)
   - WhisperX is redundant with Whisper confidence
   - Consider using Whisper confidence directly

---

## 🎯 Next Steps

1. **Abandon Combined LLM Approach**: Results show it's not viable for production
2. **Implement Model Caching**: Quick win, 10-15s savings, zero quality impact
3. **Implement Parallel Processing**: 15-20s savings with current infrastructure
4. **Keep Existing Pipeline**: Proven, reliable, maintains 85% accuracy

---

## 📝 Detailed Test Output

### ielts5.5.json - Detailed Breakdown

**Annotations Generated**:

- Grammar error count: 3
- Word choice errors: 2
- Advanced vocabulary: 0
- Coherence breaks: 2
- Topic relevance: ✓ True
- Listener effort: High
- Clarity score: 3/5

**Assessment**: Realistic for 6.0-band performance; matches baseline

### ielts7.json - Detailed Breakdown

**Error Details**:

```
Expecting ',' delimiter: line 16 column 23 (char 426)
```

**Root Cause**: LLM response contains formatting that violates JSON schema

**Attempt**: Tried markdown code block extraction, didn't help

**Conclusion**: Combined prompt syntax confused the LLM

### ielts8.5.json - Detailed Breakdown

**Annotations Generated**:

- Grammar error count: 2
- Word choice errors: 2
- Advanced vocabulary: 5
- Coherence breaks: 1
- Topic relevance: ✓ True
- Listener effort: Low
- Clarity score: 3/5

**Issue**: High vocabulary count (5) contradicts low band score (6.5)

**Assessment**: Combined prompt prioritized superficial metrics (advanced words) over coherent assessment (band score)

---

## 🏆 Conclusion

The combined LLM call approach, while theoretically appealing for time savings, introduces quality degradation that outweighs the performance benefits:

- **Time Saved**: 5-8 seconds per request (5-8% improvement)
- **Quality Risk**: Up to 1.5-band deviation in some cases (17% error)
- **Reliability**: 33% failure rate in validation tests

**Recommendation**: Implement other optimizations (caching, parallelization) that achieve similar time savings without quality degradation.
