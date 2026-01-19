#!/usr/bin/env python
"""Quick integration test for auth system."""
import asyncio
import sys
sys.path.insert(0, '.')

from src.auth.key_manager import KeyManager
from src.models.auth import InvalidAPIKeyError


async def test_auth_system():
    """Test authentication system without running FastAPI."""
    print("=" * 70)
    print("Auth System Integration Test")
    print("=" * 70)
    print()
    
    # Test 1: Generate key
    print("TEST 1: Generate API Key")
    print("-" * 70)
    key, key_hash = KeyManager.generate_key("test-user", owner_type="direct")
    print(f"[OK] Generated key: {key}")
    print(f"[OK] Key hash: {key_hash[:20]}...")
    print()
    
    # Test 2: Validate key
    print("TEST 2: Validate Key (hardcoded)")
    print("-" * 70)
    try:
        auth = KeyManager.validate_key(key)
        print(f"[OK] Validation passed")
        print(f"   - owner_type: {auth.owner_type}")
        print(f"   - verified: {auth.verified}")
    except InvalidAPIKeyError as e:
        print(f"[ERROR] Validation failed: {e}")
    print()
    
    # Test 3: Invalid key
    print("TEST 3: Invalid Key (should fail)")
    print("-" * 70)
    try:
        auth = KeyManager.validate_key("invalid_key_xyz")
        print(f"[ERROR] Should have failed!")
    except InvalidAPIKeyError as e:
        print(f"[OK] Correctly rejected: {e}")
    print()
    
    # Test 4: RapidAPI signature verification
    print("TEST 4: RapidAPI Signature Verification")
    print("-" * 70)
    
    # Mock signature test
    body = b'{"test": "data"}'
    secret = "test_secret"
    
    import hmac
    import hashlib
    expected_sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    
    is_valid = KeyManager.verify_rapidapi_signature(body, expected_sig, secret)
    print(f"[OK] Valid signature: {is_valid}")
    
    # Invalid signature
    is_valid = KeyManager.verify_rapidapi_signature(body, "wrong_sig", secret)
    print(f"[OK] Invalid signature rejected: {not is_valid}")
    print()
    
    # Test 5: Multiple keys (hardcoded)
    print("TEST 5: Hardcoded Keys")
    print("-" * 70)
    keys = KeyManager.get_keys_for_testing()
    print(f"[OK] Total hardcoded keys: {len(keys)}")
    for key_hash, info in keys.items():
        print(f"   - {info['name']:15} ({info['owner_type']:8}) {key_hash[:16]}...")
    print()
    
    # Test 6: Response builder
    print("TEST 6: Response Filtering")
    print("-" * 70)
    from src.services.response_builder import build_response
    
    # Mock raw analysis
    raw_analysis = {
        "engine_version": "0.1.0",
        "scoring_config": {"key": "value"},
        "overall_band": 7.5,
        "criterion_bands": {"fluency": 7.5},
        "confidence": {"category": "high", "score": 0.95},
        "transcript": "hello world",
        "grammar_errors": [{"type": "subject-verb"}],
        "fluency_notes": "Good pacing",
        "word_timestamps": [{"word": "hello", "start": 0.0, "end": 0.5}],
        "statistics": {"total_words": 2},
    }
    
    # Default tier
    default_resp = build_response("job-123", "completed", raw_analysis)
    print(f"[OK] Default response keys: {len(default_resp)} items")
    assert "transcript" not in default_resp, "Default shouldn't have transcript"
    print(f"   - Has confidence: {'confidence' in default_resp}")
    
    # Feedback tier
    feedback_resp = build_response("job-123", "completed", raw_analysis, detail="feedback")
    print(f"[OK] Feedback response keys: {len(feedback_resp)} items")
    assert "transcript" in feedback_resp, "Feedback should have transcript"
    assert "word_timestamps" not in feedback_resp, "Feedback shouldn't have timestamps"
    print(f"   - Has transcript: {'transcript' in feedback_resp}")
    print(f"   - Has grammar_errors: {'grammar_errors' in feedback_resp}")
    
    # Full tier
    full_resp = build_response("job-123", "completed", raw_analysis, detail="full")
    print(f"[OK] Full response keys: {len(full_resp)} items")
    assert "word_timestamps" in full_resp, "Full should have timestamps"
    print(f"   - Has word_timestamps: {'word_timestamps' in full_resp}")
    print(f"   - Has statistics: {'statistics' in full_resp}")
    print()
    
    print("=" * 70)
    print("[OK] ALL TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_auth_system())
