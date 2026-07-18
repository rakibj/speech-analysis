"""
Final validation test for context system refactoring.
Ensures all changes are correct and nothing broke.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, '.')

from src.utils.context_parser import parse_context, format_context_for_llm, get_tolerance_config


def test_all_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from src.core.engine import analyze_speech
        from src.core.engine_runner import run_engine
        from src.core.llm_processing import extract_llm_annotations
        from src.utils.context_parser import parse_context
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_backward_compatibility():
    """Test backward compatibility."""
    print("\nTesting backward compatibility...")
    old_contexts = ["conversational", "narrative", "presentation", "interview"]
    
    for ctx in old_contexts:
        base_type, metadata = parse_context(ctx)
        if base_type != ctx or metadata != {}:
            print(f"  ✗ {ctx} not compatible")
            return False
    
    print(f"  ✓ All {len(old_contexts)} old contexts compatible")
    return True


def test_new_ielts_format():
    """Test new IELTS format."""
    print("\nTesting new IELTS format...")
    
    test_cases = [
        ("ielts", "ielts", {}),
        ("ielts[topic: family]", "ielts", {"topic": "family"}),
        ("ielts[topic: family, cue_card: Describe someone]", "ielts", 
         {"topic": "family", "cue_card": "Describe someone"}),
    ]
    
    for input_str, expected_base, expected_meta in test_cases:
        base_type, metadata = parse_context(input_str)
        if base_type != expected_base or metadata != expected_meta:
            print(f"  ✗ Failed: {input_str}")
            return False
    
    print(f"  ✓ All {len(test_cases)} IELTS formats working")
    return True


def test_tolerance_config():
    """Test tolerance config retrieval."""
    print("\nTesting tolerance config retrieval...")
    
    contexts = ["conversational", "ielts", "narrative", "presentation", "interview"]
    
    for ctx in contexts:
        config = get_tolerance_config(ctx)
        if "pause_tolerance" not in config or "pause_variability_tolerance" not in config:
            print(f"  ✗ Config missing for {ctx}")
            return False
    
    print(f"  ✓ All {len(contexts)} configs accessible")
    return True


def test_llm_formatting():
    """Test LLM context formatting."""
    print("\nTesting LLM context formatting...")
    
    # Test basic
    result = format_context_for_llm("conversational", {})
    if "Conversational" not in result:
        print(f"  ✗ Basic formatting failed")
        return False
    
    # Test IELTS
    result = format_context_for_llm("ielts", {"topic": "family"})
    if "IELTS" not in result or "family" not in result:
        print(f"  ✗ IELTS formatting failed")
        return False
    
    print("  ✓ LLM formatting working")
    return True


def test_band_results_valid():
    """Test that band results are still valid."""
    print("\nTesting band results validity...")
    
    band_dir = Path("outputs/band_results")
    if not band_dir.exists():
        print("  ✗ Band results directory not found")
        return False
    
    files = list(band_dir.glob("*.json"))
    if not files:
        print("  ✗ No band result files found")
        return False
    
    valid_count = 0
    for file in files:
        with open(file) as f:
            data = json.load(f)
        
        if "overall_band" in data and "criterion_bands" in data:
            valid_count += 1
    
    if valid_count == len(files):
        print(f"  ✓ All {valid_count} band result files valid")
        return True
    else:
        print(f"  ✗ Only {valid_count}/{len(files)} files valid")
        return False


def test_syntax_compilation():
    """Test that modified files compile."""
    print("\nTesting syntax compilation...")
    
    import py_compile
    files_to_check = [
        "src/core/engine.py",
        "src/core/engine_runner.py",
        "src/core/llm_processing.py",
        "src/utils/context_parser.py",
    ]
    
    for file in files_to_check:
        try:
            py_compile.compile(file, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ✗ {file} has syntax error: {e}")
            return False
    
    print(f"  ✓ All {len(files_to_check)} files compile successfully")
    return True


def main():
    print("=" * 70)
    print("CONTEXT SYSTEM - FINAL VALIDATION TEST")
    print("=" * 70)
    
    tests = [
        ("Imports", test_all_imports),
        ("Backward Compatibility", test_backward_compatibility),
        ("New IELTS Format", test_new_ielts_format),
        ("Tolerance Config", test_tolerance_config),
        ("LLM Formatting", test_llm_formatting),
        ("Band Results", test_band_results_valid),
        ("Syntax Compilation", test_syntax_compilation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {name}")
    
    print("-" * 70)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n✅ ALL VALIDATION TESTS PASSED - PRODUCTION READY\n")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
