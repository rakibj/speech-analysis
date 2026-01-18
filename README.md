# Speech Analysis - IELTS Band Scoring System

A comprehensive speech analysis and IELTS band scoring system that combines acoustic/linguistic metrics with LLM-based semantic evaluation for accurate speaking proficiency assessment.

## Features

- **Audio Transcription**: Verbatim transcription with filler word detection using Whisper
- **Speech Analysis**: Metrics for fluency, pronunciation, lexical quality, and grammar
- **Filler Detection**: Multi-method detection using Whisper and Wav2Vec2
- **LLM Annotation**: OpenAI-powered semantic analysis (coherence, topic relevance, register)
- **IELTS Band Scoring**: Hybrid scoring combining metrics + LLM insights
- **Structured Logging**: Comprehensive logging for production debugging
- **Error Handling**: Custom exceptions with detailed context
- **Type Safety**: Full type hints on core functions

## Quick Start

### Prerequisites

- Python 3.11+
- CUDA 11.8+ (optional, for GPU acceleration)
- OpenAI API key

### Installation

```bash
# Clone repository
cd speech-analysis

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Fill in OpenAI API key
# Edit .env and add your OPENAI_API_KEY
```

### Basic Usage

```python
import asyncio
from src.analyzer_raw import analyze_speech
from src.analyze_band import analyze_band_from_analysis

async def analyze_audio_sample():
    # Analyze speech from audio file
    result = await analyze_speech("path/to/audio.wav")
    
    # Get IELTS band scoring
    band_result = await analyze_band_from_analysis(result)
    
    print(f"Overall Band: {band_result['band_scores']['overall_band']}")
    print(f"Fluency: {band_result['band_scores']['criterion_bands']['fluency_coherence']}")
    print(f"Pronunciation: {band_result['band_scores']['criterion_bands']['pronunciation']}")
    print(f"Lexical: {band_result['band_scores']['criterion_bands']['lexical_resource']}")
    print(f"Grammar: {band_result['band_scores']['criterion_bands']['grammatical_range_accuracy']}")

asyncio.run(analyze_audio_sample())
```

## Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...  # Your OpenAI API key

# Audio Processing
AUDIO_DEVICE=cpu       # cpu or cuda
WHISPER_MODEL=base     # tiny, base, small, medium, large

# Validation
MIN_AUDIO_DURATION_SEC=5

# Logging
LOG_LEVEL=INFO         # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=              # Leave empty for console only, or specify path

# Caching
CACHE_MODELS=true      # Cache loaded models
```

### Thresholds & Weights

Edit `src/config.py` for:
- **Filler patterns**: Detection rules for um, uh, er, etc.
- **Pause thresholds**: Long pause detection (400ms default)
- **Scoring weights**: WEIGHT_PAUSE, WEIGHT_FILLER, WEIGHT_STABILITY, etc.
- **Context-specific tolerances**: Conversational vs. presentation settings

## API Reference

### Core Functions

#### `analyze_speech(audio_path, speech_context, device)`

Comprehensive speech analysis from audio file.

**Parameters:**
- `audio_path` (str): Path to audio file (.wav, .flac, .mp3, etc.)
- `speech_context` (str): One of "conversational", "narrative", "presentation", "interview"
- `device` (str): "cpu" or "cuda" for GPU acceleration

**Returns:**
```python
{
    "raw_transcript": "Full verbatim transcription",
    "fluency_analysis": {...},  # Fluency metrics
    "wpm": 120,                  # Words per minute
    "long_pauses_per_min": 1.5,  # Pause frequency
    "pause_variability": 0.65,   # Pause rhythm stability
    "statistics": {
        "total_words_transcribed": 229,
        "content_words": 200,
        "filler_words_detected": 5,
        "filler_percentage": 2.2,
        "is_monotone": false
    },
    "timestamps": {
        "words_timestamps_raw": [...],      # Word-level timing
        "words_timestamps_cleaned": [...],  # Content words only
        "segment_timestamps": [...],
        "filler_timestamps": [...]
    }
}
```

**Raises:**
- `AudioNotFoundError`: File doesn't exist
- `AudioFormatError`: Cannot read file
- `AudioDurationError`: Too short (< 5 seconds)
- `TranscriptionError`: Whisper transcription failed
- `ModelLoadError`: Model failed to load
- `NoSpeechDetectedError`: No speech in audio

**Example:**
```python
import asyncio
from src.analyzer_raw import analyze_speech

result = asyncio.run(analyze_speech("speaker.wav", "conversational"))
print(f"WPM: {result['wpm']}")
print(f"Fillers: {result['statistics']['filler_percentage']}%")
```

#### `score_ielts_speaking(metrics, transcript, use_llm)`

IELTS band scoring from metrics.

**Parameters:**
- `metrics` (dict): Metrics dictionary from analyzer
- `transcript` (str): Full transcription text
- `use_llm` (bool): Enable OpenAI semantic evaluation (default: False)

**Returns:**
```python
{
    "overall_band": 6.5,
    "criterion_bands": {
        "fluency_coherence": 6.5,
        "pronunciation": 6.5,
        "lexical_resource": 6.0,
        "grammatical_range_accuracy": 6.5
    },
    "descriptors": {...},  # IELTS band descriptors
    "feedback": {
        "fluency_coherence": "Adequate fluency...",
        "pronunciation": "Clear pronunciation...",
        "lexical_resource": "Good vocabulary...",
        "grammatical_range_accuracy": "Good control...",
        "overall_recommendation": "..."
    }
}
```

**Raises:**
- `LLMAPIError`: OpenAI API call failed (degrades to metrics-only)
- `ConfigurationError`: Missing OpenAI API key (with LLM enabled)

**Example:**
```python
from src.ielts_band_scorer import score_ielts_speaking

result = score_ielts_speaking(
    metrics=analysis_result,
    transcript=transcription,
    use_llm=True
)
print(f"Band: {result['overall_band']}")
for criterion, score in result['criterion_bands'].items():
    print(f"  {criterion}: {score}")
```

### Exception Handling

All errors inherit from `SpeechAnalysisError` with structured context:

```python
from src.exceptions import (
    AudioProcessingError,
    TranscriptionError,
    LLMProcessingError,
)
from src.logging_config import logger

try:
    result = await analyze_speech(audio_path)
except AudioProcessingError as e:
    logger.error(f"Error: {e.message}")
    logger.error(f"Details: {e.details}")
except TranscriptionError as e:
    # Handle transcription-specific issues
    pass
except LLMProcessingError as e:
    # LLM failures degrade gracefully
    pass
```

## Logging

View real-time analysis progress:

```python
from src.logging_config import setup_logging

# Configure logging
logger = setup_logging(
    level="INFO",           # DEBUG for verbose output
    log_file="analysis.log" # Optional file output
)

# Logs include:
# - Model loading progress
# - Transcription completion
# - Alignment status
# - LLM annotation extraction
# - Band scoring results
```

**Log Levels:**
- `DEBUG`: Detailed model and processing info
- `INFO`: Stage completion and results
- `WARNING`: Non-critical issues (missing API key, model warnings)
- `ERROR`: Critical failures with context
- `CRITICAL`: System failures

## Scripts

### Batch Analysis

Analyze multiple audio files and score them:

```bash
uv run python scripts/batch_band_analysis.py
```

Processes:
1. All `.wav` files in `data/ielts_part_2/`
2. Saves analysis to `outputs/audio_analysis/`
3. Scores with IELTS bands to `outputs/band_results/`

Configure limits in script:
```python
await run_analysis(limit=5)  # Process first 5 files
```

## Testing

Run comprehensive test suite:

```bash
# All tests
uv run python -m pytest tests/ -v

# Specific test file
uv run python -m pytest tests/test_audio_processing.py -v

# With coverage
uv run python -m pytest tests/ --cov=src

# End-to-end test
uv run python test_e2e.py
```

**Test Coverage:**
- Exception handling (4 tests)
- Audio processing utilities (6 tests)
- LLM integration (3 tests)
- IELTS scoring logic (4 tests)
- **Total: 17 tests** ✓

## Performance

Typical analysis times (single audio file, base model):

| Operation | Duration | Notes |
|-----------|----------|-------|
| Audio loading | 0.1s | File I/O |
| Whisper transcription | 15-30s | GPU 2-3x faster |
| WhisperX alignment | 5-10s | For 2 min audio |
| Wav2Vec2 filler detection | 10-20s | GPU recommended |
| LLM annotation | 10-15s | OpenAI API call |
| IELTS scoring | < 1s | Metrics calculation |
| **Total (with LLM)** | ~50-90s | ~30-50s on GPU |

## Metrics Explained

### Fluency & Coherence

- **WPM (Words Per Minute)**: Speaking rate (optimal: 100-130)
- **Long Pauses Per Minute**: Hesitation frequency (optimal: ≤ 2.0)
- **Pause Variability**: Rhythm consistency (lower is better)
- **Repetition Ratio**: Word/phrase repetition (optimal: ≤ 0.065)

### Pronunciation

- **Mean Word Confidence**: Model confidence on word recognition (0.85+)
- **Low Confidence Ratio**: % of words with low confidence (≤ 20%)
- **Monotone Detection**: Lack of prosodic variation

### Lexical Resource

- **Vocabulary Richness**: Ratio of unique to total words (0.50+)
- **Lexical Density**: Content words as % of total words (0.45+)
- **Advanced Vocabulary Count**: From LLM analysis
- **Word Choice Errors**: Inappropriate word usage

### Grammatical Accuracy

- **Mean Utterance Length**: Complexity indicator (20+ words)
- **Speech Rate Variability**: Pacing consistency
- **Grammar Error Count**: From LLM analysis
- **Complex Structure Accuracy**: Successful vs. attempted complex sentences

## Troubleshooting

### "No speech detected in audio"

- Ensure audio is at least 5 seconds
- Check audio quality (clear speech, not background noise)
- Try with a different model size (larger models more tolerant)

### "CUDA out of memory"

- Use `AUDIO_DEVICE=cpu` in `.env`
- Use smaller model: `WHISPER_MODEL=base` or `tiny`
- Process fewer files in batch

### "LLM annotation extraction successful but scoring uses metrics-only"

- OpenAI API call failed or returned invalid schema
- Check `LOG_LEVEL=DEBUG` for details
- Verify `OPENAI_API_KEY` is correct
- System gracefully falls back to metrics-only scoring

### "Type errors with pandas DataFrames"

- Ensure columns exist before filtering: `mark_filler_words()` before `get_content_words()`
- Check DataFrame structure matches expected schema

## Architecture

```
speech-analysis/
├── src/
│   ├── analyzer_raw.py           # Main analysis orchestrator
│   ├── audio_processing.py       # Audio I/O + transcription
│   ├── fluency_metrics.py        # Metrics calculation
│   ├── disfluency_detection.py   # Filler/stutter detection
│   ├── llm_processing.py         # OpenAI integration
│   ├── ielts_band_scorer.py      # Band scoring logic
│   ├── config.py                 # Thresholds & weights
│   ├── exceptions.py             # Error definitions
│   ├── logging_config.py         # Logging setup
│   └── ...
├── scripts/
│   ├── batch_band_analysis.py    # Batch processing
│   └── ...
├── tests/
│   ├── test_exceptions.py
│   ├── test_audio_processing.py
│   ├── test_llm_processing.py
│   └── test_ielts_band_scorer.py
├── .env.example                  # Configuration template
├── pyproject.toml               # Dependencies
└── README.md
```

## Contributing

To extend the system:

1. **Add new metrics**: Edit `src/fluency_metrics.py`
2. **Modify scoring logic**: Edit `src/ielts_band_scorer.py`
3. **Adjust thresholds**: Edit `src/config.py`
4. **Add tests**: Create test file in `tests/`

All changes should:
- Include type hints
- Have error handling with custom exceptions
- Add logging at key points
- Include docstrings
- Pass all existing tests

## Support

For issues or questions:

1. Check logs: `LOG_LEVEL=DEBUG` for verbose output
2. Run tests: Verify system integrity
3. Check documentation above
4. Review exception messages for context

## License

[Add your license here]

## Authors

- Speech Analysis Team
- Version: 0.1.0
- Last Updated: January 18, 2026
