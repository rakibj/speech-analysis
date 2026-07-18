# Debug Scripts

This folder contains development and testing scripts used during development and debugging of the speech analysis system.

## Organization

### Core Scripts (Root)

- `test_quick.py` - Quick end-to-end test
- `app.py` - Streamlit web application
- `main.py` - Main CLI entry point
- `modal_app.py` - Modal deployment configuration

### Debug & Validation Scripts

All debugging and validation scripts are organized here to keep the root clean.

## Script Categories

### Data Quality Checks

- `check_5_5_5_scores.py` - Validate 5.5 band scoring
- `check_pronunciation.py` - Check pronunciation metrics
- `check_pron_metrics.py` - Detailed pronunciation analysis
- `check_score_consistency.py` - Verify score consistency across runs

### Debugging

- `debug_5_5_scoring.py` - Debug 5.5 band calculation
- `debug_coupling_too_strict.py` - Debug inter-criterion coupling
- `debug_llm.py` - LLM annotation debugging
- `debug_regenerate.py` - Data regeneration debugging

### Investigation Scripts

- `investigate_5_5_criteria.py` - Investigate 5.5 scoring criteria
- `final_validation.py` - Final validation of system

### Regeneration Scripts

- `regenerate_band_results.py` - Regenerate band result files
- `regenerate_band_results_with_confidence.py` - With confidence scores
- `regenerate_band_results_with_coupling.py` - With inter-criterion coupling

### Testing & Validation

- `test_complete_integration.py` - Full integration testing
- `test_confidence_features.py` - Confidence factor testing
- `test_coupling.py` - Inter-criterion coupling tests
- `test_determinism.py` - Determinism verification
- `test_determinism_coupling.py` - Determinism with coupling
- `test_edge_cases.py` - Edge case testing
- `test_edge_cases_local.py` - Local edge case testing
- `test_rescore_with_coupling.py` - Rescoring with coupling
- `test_words_fillers_structure.py` - Timestamped data structure testing

### Verification Scripts

- `verify_consistency_after_coupling.py` - Verify coupling consistency
- `verify_fixes.py` - Verify bug fixes
- `validate_pron.py` - Pronunciation validation

### Utility Scripts

- `quick_regen.py` - Quick data regeneration
- `show_summary.py` - Show analysis summary
- `TIMESTAMPED_STRUCTURE_DEMO.py` - Demo timestamped structures

## Running Debug Scripts

From the root directory:

```bash
# Run a debug script
python debug_scripts/check_score_consistency.py

# Or from within debug_scripts
cd debug_scripts
python check_score_consistency.py
```

## Usage Tips

- These scripts are development artifacts
- Use them to verify fixes, validate changes, and test edge cases
- Most scripts output to `outputs/` or `logs/` directories
- Safe to delete after validation is complete

## Related

- Main code: `src/`
- Tests: `tests/`
- Notebooks: `notebooks/`
