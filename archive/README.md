# Archive

This folder collects code that isn't part of the running API but was kept instead of deleted outright, in case it's still useful for reference. Nothing here is imported by `app.py`, `modal_app.py`, or anything under `src/`.

It's safe to delete any of these folders once you're sure you don't need them.

## Contents

### `debug_scripts/`

One-off debugging/validation scripts written while tuning the IELTS band scorer (checking specific band edge cases like 5.5, verifying scoring determinism, regenerating `outputs/band_results` after calibration changes, etc.). Each script was a throwaway tool for a specific investigation, not a reusable utility. See its own `README.md` for the original categorization.

### `scripts/`

Everything that used to live in the top-level `scripts/` folder *except* `admin_keys.py` and `generate_test_keys.py` (those two are genuinely-used API-key tooling and were moved back to `scripts/`).

What's here is mostly:

- **Calibration/tuning one-offs**: `push_to_55.py`, `ultra_low_band.py`, `aggressive_low_band.py`, `fine_tune_low_band.py`, `adjust_confidence.py`, `analyze_calibration.py`, `analyze_mismatch.py` — scripts written to chase specific band-scoring discrepancies.
- **`test_*.py` / `verify_*.py` / `check_*.py` / `debug_*.py` / `trace_*.py`**: ad hoc scripts for manually poking at the API, Modal deployment, RapidAPI signature checks, LLM prompts, etc. — not part of the `tests/` suite (which uses pytest and is still active).
- **Superseded duplicates**: `batch_analysis.py`, `batch_analysis_deep.py`, `batch_band_analysis.py`, `export_src_to_md.py`, `extract_youtube.py` all have newer equivalents living in `src/cli/` or `src/utils/`. These scripts folder versions predate that move.

### `root/`

Files that were sitting at the repository root without being wired into anything:

- `main.py` — the default `uv init` "Hello from speech-analysis!" stub. Not referenced by `pyproject.toml`'s `[project.scripts]`, not imported anywhere. `app.py` is the real FastAPI entrypoint.
- `QUICK_START.md` — a reference card for `engine_runner`, but it points at files that don't exist (`ENGINE_RUNNER_COMPLETE.md`, `IMPLEMENTATION_GUIDE.md`, `TEST_ENGINE_RUNNER.md`) and stale import paths (`src.engine_runner` instead of `src.core.engine_runner`).
- `analysis_correlations.py`, `create_visualizations.py` — untracked scratch scripts related to the correlation research now done properly in `research/corelation.py`.

### `src_core/`

- `ielts_band_scorer_original.py` — the pre-rewrite version of `src/core/ielts_band_scorer.py`. Confirmed unused (nothing imports it); kept only for diffing against the current scorer if needed.
- `disfluency_detection.py` — an earlier filler/stutter detection implementation. Confirmed unused; superseded by `src/audio/filler_detection.py` (used by the full analysis pipeline) and `src/core/audio_processing.py` (used by the fast pipeline).
