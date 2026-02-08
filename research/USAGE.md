# Research Scripts Documentation

## Overview

Two complementary scripts for fluency analysis:

1. **analyzer.py** - Generate organized raw input data from audio files
2. **scorer.py** - Calculate fluency score from raw input data

---

## 1. Analyzer Script (`/research/analyzer.py`)

### Purpose

Takes an audio file and generates raw input data for fluency analysis, saving results to `/research/analysis/{filename}.json`

The analyzer extracts raw metrics that serve as INPUT to fluency scoring - NOT the fluency score itself.

### Usage

```bash
# Basic usage
uv run research/analyzer.py data/S01.wav

# With custom context
uv run research/analyzer.py data/S01.wav ielts

# With custom device
uv run research/analyzer.py data/S01.wav conversational cuda
```

### Arguments

- `<audio_file>` - Path to WAV file (required)
- `[context]` - Speech context: conversational, ielts, narrative, presentation, interview (default: conversational)
- `[device]` - Device: cpu or cuda (default: cpu)

### Output

Saves JSON to: `/research/analysis/{filename}.json`

**Data Structure:**
```json
{
  "metadata": {
    "filename": "S01",
    "duration_seconds": 89.9,
    "total_words_transcribed": 278,
    "content_words": 278,
    "filler_words_detected": 0,
    "is_monotone": true
  },

  "transcript": "Don't feel your best. The TV documentary...",

  "input_metrics": {
    "wpm": 185.54,
    "long_pauses_per_min": 0.0,
    "fillers_per_min": 3.34,
    "pause_variability": 0.0,
    "speech_rate_variability": 0.221,
    "vocab_richness": 0.496,
    "type_token_ratio": 0.496,
    "repetition_ratio": 0.034,
    "mean_utterance_length": 69.5,
    "mean_word_confidence": 0.9
  },

  "timestamps": {
    "words_timestamps_raw": [...],
    "words_timestamps_cleaned": [...],
    "segment_timestamps": [...],
    "filler_timestamps": [...]
  }
}
```

### Key Input Metrics

These are the RAW metrics passed to the fluency scoring calculation:

- **wpm** - Words per minute (calculated from content words)
- **fillers_per_min** - Filler words/events per minute
- **long_pauses_per_min** - Pauses > 1.5 seconds per minute
- **pause_variability** - Inconsistency in pause timing (0 = consistent)
- **speech_rate_variability** - Variation in speaking pace
- **vocab_richness** - Lexical diversity (0-1)
- **type_token_ratio** - Unique words / total words
- **repetition_ratio** - Repeated word percentage
- **mean_utterance_length** - Average words per sentence
- **mean_word_confidence** - Average ASR confidence (0-1)

---

## 2. Scorer Script (`/research/scorer.py`)

### Purpose

Reads raw input metrics from analyzer and calculates a fluency score (0-100) with detailed subscore breakdowns.

### Usage

```bash
# Score using filename
uv run research/scorer.py S01

# Score using full filename
uv run research/scorer.py S01.json

# Score using full path
uv run research/scorer.py analysis/S01.json
```

### Arguments

- `<analysis_file>` - Filename or path to JSON analysis
  - Can be absolute path or relative to `/research/analysis/`
  - Can include or omit `.json` extension

### Output

Displays comprehensive fluency report:

```
Fluency Analysis Report
File: S01
======================================================================

Fluency Score: 73/100
----------------------------------------------------------------------

Subscores (0.0-1.0):
  Speech Rate:       0.87
  Pause Structure:   1.00
  Filler Dependency: 0.44
  Rhythmic Stability:1.00
  Lexical Quality:   0.66

Input Metrics Used:
  Words Per Minute:           185.5
  Fillers Per Minute:         3.34
  Long Pauses Per Minute:     0.00
  ...

Audio Information:
  Duration:                   90.00s
  Total Words:                278

Issues Detected:
  [HIGH] filler_dependency: Fillers replace silent planning pauses.
         (Impact: -13 points)

======================================================================
```

### Subscores Explanation

- **Speech Rate** - How well speaking pace matches optimal range (120-160 WPM)
- **Pause Structure** - How naturally pauses are distributed
- **Filler Dependency** - Dependency on fillers vs. silent pauses (lower is better)
- **Rhythmic Stability** - Consistency of speech rhythm
- **Lexical Quality** - Vocabulary richness and word choice variety

## 3. Batch Analyzer Script (`/research/batch_analyzer.py`)

### Purpose

Analyze all WAV files in the `/research/data` directory in one command.

### Usage

```bash
# Analyze all files
uv run research/batch_analyzer.py

# With custom context
uv run research/batch_analyzer.py ielts

# With custom device
uv run research/batch_analyzer.py conversational cuda

# Skip files that are already analyzed
uv run research/batch_analyzer.py conversational cpu --skip
```

### Output

Generates JSON analysis file for each audio file and displays a summary:

```
[1/29] Processing: S01
  [OK] Success
    - Duration: 89.9s
    - Words: 278
    - WPM: 185.5
    - Fillers/min: 3.34
...
[29/29] Processing: S30
  [OK] Success
    - Duration: 45.4s
    - Words: 92
    - WPM: 121.5
    - Fillers/min: 3.70

======================================================================
BATCH PROCESSING SUMMARY
======================================================================

Total files processed: 29
Skipped: 0
Failed: 0

[OK] All files processed successfully!

Processed Files Summary:
  File                 Duration     Words      WPM        Fillers/min
  -------------------- ------------ ---------- ---------- ------------
  S01                  89.9         278        185.5      3.34
  S02                  91.2         218        143.4      3.87
  ...
```

---

## 4. Batch Scorer Script (`/research/batch_scorer.py`)

### Purpose

Score all analysis files in one command.

### Usage

```bash
# Score all analyses
uv run research/batch_scorer.py
```

### Output

Scores all files and displays comprehensive summary:

```
[1/29] Scoring: S01
  [OK] Fluency Score: 73/100
    - Speech Rate: 0.87
    - Pause Structure: 1.00
    - Filler Dependency: 0.44
    - Rhythmic Stability: 1.00
    - Lexical Quality: 0.66
    - Issues: 1 detected
...

======================================================================
BATCH SCORING SUMMARY
======================================================================

Total files scored: 29/29
Failed: 0

[OK] All files scored successfully!

Scores by File (sorted by fluency score):
  File       Score      Speech Rate     Pause      Filler
  ---------- ---------- --------------- ---------- ----------
  S12        81         1.00            1.00       0.58
  S23        74         1.00            0.56       0.59
  S01        73         0.87            1.00       0.44
  ...
  S17        24         0.42            0.59       0.20

Statistics:
  Average Score: 55.7/100
  Min Score: 24/100
  Max Score: 81/100
```

---

## Workflow

### Single File Analysis and Scoring

```bash
# Step 1: Analyze one file
uv run research/analyzer.py research/data/S01.wav

# Step 2: Score the analysis
uv run research/scorer.py S01
```

### Batch Processing (Recommended)

**Analyze all files in /research/data**
```bash
uv run research/batch_analyzer.py
```

**Score all analyses**
```bash
uv run research/batch_scorer.py
```

### Complete Batch Pipeline

Analyze and score all 29 audio files in one go:
```bash
# Step 1: Analyze all audio files
uv run research/batch_analyzer.py

# Step 2: Score all analyses
uv run research/batch_scorer.py
```

Both scripts will:
1. Process all files (analyzer) or all analyses (scorer)
2. Display progress for each file
3. Show a comprehensive summary at the end
4. Report any failures with error details

### Batch Script Options

**Batch Analyzer**
```bash
uv run research/batch_analyzer.py [context] [device] [--skip]
```
- `[context]` - Speech context (default: conversational)
- `[device]` - Device to use (default: cpu)
- `[--skip]` - Skip files that are already analyzed

**Batch Scorer**
```bash
uv run research/batch_scorer.py
```
- Scores all JSON files in /research/analysis/
- Displays summary sorted by fluency score
- Shows aggregate statistics

---

## Data Organization

```
research/
├── engine.py              # Original analysis engine (not used by analyzer.py)
├── analyzer.py            # Extract raw input metrics from audio
├── scorer.py              # Calculate fluency score from input metrics
├── batch_analyzer.py      # Batch analyze all audio files
├── batch_scorer.py        # Batch score all analysis files
├── data/
│   ├── S01.wav
│   ├── S02.wav
│   └── ... (29 total files)
└── analysis/              # Generated analysis files
    ├── S01.json           # Raw input data (no fluency score)
    ├── S02.json
    └── ... (29 total files)
```

---

## Key Design Principles

### analyzer.py
- Extracts RAW INPUT metrics only
- Does NOT calculate fluency score
- Does NOT calculate subscores
- Saves clean, organized JSON with:
  - Audio metadata
  - Transcript
  - Input metrics (9 key measures for scoring)
  - Timestamped data (words, fillers, segments)

### scorer.py
- Reads input metrics from JSON
- Calculates 5 subscores (speech rate, pause, filler, stability, lexical)
- Calculates overall fluency score (0-100)
- Detects and reports issues
- NO dependency on engine.py fluency analysis

---

## Test Results

### Single File Test (S01.wav)

Successfully analyzed and scored:
- **Duration**: 90 seconds, 278 words
- **Input Metrics**: WPM 185.5, Fillers/min 3.34, Vocab 0.496
- **Fluency Score**: 73/100
  - Speech Rate: 0.87
  - Pause Structure: 1.00 (good)
  - Filler Dependency: 0.44 (issue detected)
  - Rhythmic Stability: 1.00 (good)
  - Lexical Quality: 0.66

### Batch Processing Test (All 29 files)

Successfully analyzed and scored all files:
- **Files Processed**: 29/29
- **Success Rate**: 100%
- **Processing Time**: ~12 minutes (sequential, can be parallelized)

**Top 5 Fluency Scores**:
1. S12 - 81/100
2. S23 - 74/100
3. S01 - 73/100
4. S02 - 69/100
5. S09 - 69/100

**Fluency Score Statistics**:
- Average: 55.7/100
- Min: 24/100 (S17)
- Max: 81/100 (S12)

**Common Issues Found**:
- Filler dependency (most common - 28/29 files)
- Pause structure variations
- Rhythmic stability challenges
- Speech rate variations
