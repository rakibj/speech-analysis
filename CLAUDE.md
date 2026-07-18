# CLAUDE.md

This file guides Claude Code (and anyone else) working in this repository.

## What this is

A FastAPI backend that scores IELTS Speaking practice recordings. Upload audio → get an IELTS band score (5.0–9.0) across the four official criteria (Fluency & Coherence, Pronunciation, Lexical Resource, Grammatical Range & Accuracy) plus structured per-criterion feedback.

Pipeline: **Whisper transcription → WhisperX alignment → Wav2Vec2 filler/disfluency detection → OpenAI LLM semantic analysis (coherence, grammar, vocabulary) → hybrid metrics+LLM band scoring.**

Served two ways:
- **Locally**: `app.py` (plain FastAPI + uvicorn)
- **Deployed**: `modal_app.py` (Modal serverless GPU/CPU containers, defines the same app inline)

Both wire up the exact same routers from `src/api/`.

## Quick start

```bash
uv sync
cp .env.example .env   # fill in OPENAI_API_KEY at minimum
uv run python app.py   # serves on http://localhost:8000, docs at /docs
```

Run tests: `uv run pytest tests/ -v`

## Request flow

```
POST /api/direct/v1/analyze  (or /api/v1/analyze for the RapidAPI-gated variant)
        │
        ▼
  src/api/direct.py or src/api/v1.py
        │  - auth dependency (src/auth/middleware.py)
        │  - protections: file size / duration / rate limit (src/api/protections.py, v1 only)
        │  - saves upload to a temp file, returns {job_id, status:"queued"} immediately
        │  - queues a BackgroundTasks coroutine
        ▼
  src/services/AnalysisService.analyze_speech()  (full)
    OR
  src/core/analyzer_fast.analyze_speech_fast()   (fast, /analyze-fast)
        │
        ▼
  src/core/engine_runner.run_engine() → src/core/engine.analyze_speech()
        │  1. src/core/analyzer_raw.py    — transcribe + fluency metrics (full path only)
        │  2. src/core/analyze_band.py    — build_analysis(): wraps raw metrics + band scorer
        │  3. src/core/ielts_band_scorer.py — score_ielts_speaking(): hybrid metrics+LLM scoring
        │  4. src/core/llm_processing.py  — OpenAI call for semantic annotations (skipped in fast mode)
        ▼
  Result stored in src/core/job_queue.py (JobQueue)
        │
        ▼
GET /api/direct/v1/result/{job_id}?detail=feedback|full
        │
        ▼
  src/services/response_builder.build_response() — shapes the tiered response
```

Poll the result endpoint until `status` is `completed` or `error`. See `docs/API_RESPONSE_DOCUMENTATION.md` for the full response schema and `docs/ANALYZE_ENDPOINT_GUIDE.md` for a plain-English walkthrough of what happens at each stage.

### Full vs. fast analysis

There are **two independent audio/transcription implementations**, not one shared path with a flag:

| | Full (`/analyze`) | Fast (`/analyze-fast`) |
|---|---|---|
| Orchestrator | `src/services/response_builder` via `AnalysisService` → `engine_runner` → `engine.py` | `src/core/analyzer_fast.py` directly |
| Audio/transcription module | `src/audio/processing.py` + `src/audio/filler_detection.py` | `src/core/audio_processing.py` |
| WhisperX alignment | Yes | Skipped |
| Wav2Vec2 filler detection | Yes | Skipped (Whisper-only filler heuristics) |
| LLM semantic analysis | Yes | Skipped |
| Speed | 20–40s per minute of audio | 5–10s per minute (5–8x faster) |

Both converge on the same output shape so `response_builder.py` can format either one identically (LLM-derived fields are just `null` in fast mode).

### Job queue

`src/core/job_queue.py`'s `JobQueue` is in-memory by default (fine for a single container). `src/api/direct.py` lazily wraps it in a `modal.Dict` when running on Modal, so job state is shared across concurrent Modal containers. `src/api/v1.py` (RapidAPI) always uses a plain in-process instance — it does not get the distributed-KV treatment, worth knowing if you ever run the RapidAPI path across multiple Modal containers.

## Auth model

Two parallel auth schemes, both producing an `AuthContext` (`src/models/auth.py`):

- **Direct** (`src/api/direct.py`, `get_direct_auth`): validates `X-API-Key` against a hardcoded dict in `src/auth/key_manager.py::KeyManager.VALID_KEYS` (SHA-256 hashes → key metadata). There's no database — see Known Issues below.
- **RapidAPI** (`src/api/v1.py`, `get_rapidapi_auth`): trusts RapidAPI's gateway. If the request carries `x-rapidapi-proxy-secret` + `x-rapidapi-user`/`x-mashape-user` headers, it's accepted as already-authenticated — no key lookup, since RapidAPI validated the subscription before forwarding. `src/api/protections.py::enforce_rapidapi_only` additionally rejects any request to `/api/v1/*` missing the proxy-secret header, so that route can't be hit by bypassing RapidAPI directly.

`/api/v1/*` (RapidAPI) also has request protections that `/api/direct/v1/*` does not: 15MB file size cap, 5-minute audio duration cap (`MAX_AUDIO_DURATION_MINUTES` in `protections.py` — note the module-level docstring/route comments say 30 min, the actual constant is 5), and a 100 req/hour per-user rate limit (in-memory, resets on restart).

## Configuration

- `.env` — secrets and runtime device/model choice (`OPENAI_API_KEY`, `RAPIDAPI_SECRET`, `AUDIO_DEVICE`, `WHISPER_MODEL`). Copy from `.env.example`.
- `src/utils/config.py` — **product policy, not engineering config.** Filler-word patterns, pause/WPM thresholds, scoring weights (`WEIGHT_PAUSE`, `WEIGHT_FILLER`, etc., must sum to 1.0), and per-context tolerances (conversational/ielts/narrative/presentation/interview). Changing values here directly changes user-facing band scores — treat edits like a rubric change, not a refactor.

## Directory map

```
app.py                 FastAPI entrypoint (local dev)
modal_app.py           Modal deployment (same routers, serverless container)
src/
  api/                 FastAPI routers: v1.py (RapidAPI), direct.py, protections.py
  auth/                key_manager.py (key validation), middleware.py (FastAPI deps)
  models/              Pydantic schemas: auth.py, __init__.py (response/request models)
  services/            AnalysisService — thin orchestration wrapper over engine_runner
  core/                Analysis engine: engine.py/engine_runner.py (full pipeline),
                       analyzer_raw.py / analyzer_fast.py (two audio pipelines, see above),
                       ielts_band_scorer.py (scoring), llm_processing.py (OpenAI calls),
                       job_queue.py, config-driven metrics modules
  audio/               processing.py + filler_detection.py — used by the FULL pipeline only
  utils/               config.py (scoring policy), enums.py, exceptions.py,
                       context_parser.py, logging_config.py
  cli/                 Standalone CLI entrypoints (registered in pyproject.toml [project.scripts])
tests/                 pytest suite (test_api/, plus unit tests per module)
scripts/               admin_keys.py, generate_test_keys.py — the only scripts kept out of archive/
docs/                  API_RESPONSE_DOCUMENTATION.md, ANALYZE_ENDPOINT_GUIDE.md
research/              Separate, actively-evolving research track for a standalone fluency
                       scorer (not wired into the API — see research/USAGE.md)
archive/               Retired one-off scripts and dead code, kept for reference only.
                       See archive/README.md before assuming anything in here still runs.
notebooks/             Exploratory Jupyter notebooks (dataset extraction, prosody, wav2vec)
data/, samples/        Local audio fixtures for manual testing (gitignored, not committed)
outputs/               Generated analysis/scoring artifacts (gitignored, regenerable)
```

## Known issues / gotchas

- **Hardcoded dev API key**: `src/auth/key_manager.py::VALID_KEYS` has one hardcoded SHA-256 hash for local dev. There's no persistence layer for keys — `scripts/admin_keys.py` / `scripts/generate_test_keys.py` just print new keys/hashes for you to paste into the dict by hand. Fine for now, but don't mistake it for real key management.
- **`src/cli/batch_band_analysis.py` has broken imports** — it imports `src.utils.analyzer_raw` and `src.utils.analyze_band`, but those modules live under `src.core`, not `src.utils`. It predates a module reorg and hasn't been run since. `src/cli/batch_analysis.py` and `batch_analysis_deep.py` (which import from `src.services`) are fine.
- **Two parallel audio-processing stacks** (`src/audio/*` vs `src/core/audio_processing.py`) — see "Full vs fast analysis" above. Don't "deduplicate" these without checking both `/analyze` and `/analyze-fast` still work; they intentionally trade accuracy for speed.
- **`research/`** is a separate, currently-active line of work (branch `research/fluency`) building a standalone fluency scorer decoupled from the API's LLM-hybrid approach. It is not imported by `src/`, and has its own docs (`research/USAGE.md`, `research/CORRELATION_SETUP.md`).
- Root `README.md` may lag behind `src/` reality — this file (`CLAUDE.md`) and `docs/` are the source of truth for current architecture.

## Testing

`tests/` uses pytest (`uv run pytest tests/ -v`, or `--cov=src` for coverage — configured by default in `pyproject.toml`). Structure:
- `tests/test_api/` — route-level tests with a `conftest.py` fixture setup
- `tests/test_audio_processing.py`, `test_ielts_band_scorer.py`, `test_llm_processing.py`, `test_exceptions.py` — unit tests per core module

Anything under `archive/` or `debug_scripts`-style throwaway scripts is intentionally outside this suite.
