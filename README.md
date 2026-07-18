# Speech Analysis - IELTS Band Scoring API

A FastAPI backend that scores IELTS Speaking practice recordings: upload audio, get back an IELTS band score (5.0–9.0) across all four official criteria plus structured, data-driven feedback.

> **For architecture, request flow, and module map, see [`CLAUDE.md`](CLAUDE.md).** This README covers setup and day-to-day usage.

## Features

- **Transcription**: Verbatim Whisper transcription with word-level timestamps and confidence
- **Filler/disfluency detection**: Wav2Vec2-based (full mode) or Whisper-heuristic (fast mode)
- **LLM semantic analysis**: OpenAI-powered coherence, grammar, and vocabulary evaluation
- **IELTS band scoring**: Hybrid acoustic-metrics + LLM scoring across Fluency & Coherence, Pronunciation, Lexical Resource, and Grammatical Range & Accuracy
- **Two speeds**: `/analyze` (full, 20-40s/min of audio) and `/analyze-fast` (metrics-only, 5-10s/min)
- **Two auth surfaces**: direct API key access and a RapidAPI-gateway-trusted route

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- An OpenAI API key (required for full-mode LLM analysis; fast mode works without it)
- CUDA (optional, for GPU acceleration — set `AUDIO_DEVICE=cuda`)

## Installation

```bash
git clone <repo-url>
cd speech-analysis
uv sync
cp .env.example .env
# edit .env and set OPENAI_API_KEY (and RAPIDAPI_SECRET if serving the RapidAPI route)
```

## Running locally

```bash
uv run python app.py
# → http://localhost:8000, interactive docs at /docs
```

### Basic request

```bash
curl -X POST http://localhost:8000/api/direct/v1/analyze \
  -H "X-API-Key: <your-key>" \
  -F "file=@sample.wav" \
  -F "speech_context=conversational"
# → {"job_id": "...", "status": "queued"}

curl "http://localhost:8000/api/direct/v1/result/<job_id>?detail=feedback" \
  -H "X-API-Key: <your-key>"
```

Dev API keys are managed by hand in `src/auth/key_manager.py::VALID_KEYS`. Generate one with:

```bash
uv run python scripts/generate_test_keys.py
```

See `docs/API_RESPONSE_DOCUMENTATION.md` for the full response schema and `docs/ANALYZE_ENDPOINT_GUIDE.md` for a plain-English walkthrough of what each stage does.

## Configuration

`.env` (see `.env.example`):

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Required for LLM semantic analysis (full mode) |
| `RAPIDAPI_SECRET` | Verifies RapidAPI gateway signatures |
| `AUDIO_DEVICE` | `cpu` or `cuda` |
| `WHISPER_MODEL` | `tiny` / `base` / `small` / `medium` / `large` |
| `MIN_AUDIO_DURATION_SEC` | Minimum accepted audio length (default 5s) |

Scoring thresholds and weights (WPM ranges, pause tolerances, filler penalties, per-context tolerances) live in `src/utils/config.py`. That file is product policy — changing a value there changes the band a user gets, so treat edits accordingly.

## Deployment

`modal_app.py` deploys the same routers as `app.py` to [Modal](https://modal.com) as a serverless ASGI app, with a persistent volume for model caching and a `modal.Dict` for distributed job state across containers:

```bash
uv run modal deploy modal_app.py
```

## Testing

```bash
uv run pytest tests/ -v          # full suite
uv run pytest tests/ --cov=src   # with coverage (also the pytest default, see pyproject.toml)
```

## Project layout

See [`CLAUDE.md`](CLAUDE.md#directory-map) for the full directory map. Highlights:

- `src/api/` — FastAPI routes (`v1.py` RapidAPI, `direct.py` direct-access)
- `src/core/` — analysis engine, band scorer, job queue
- `src/audio/` — transcription/filler-detection used by the full pipeline
- `research/` — a separate, actively-evolving standalone fluency-scoring research track (not part of the API)
- `archive/` — retired one-off scripts and dead code, kept for reference (see `archive/README.md`)

## License

MIT — see `LICENSE`.
