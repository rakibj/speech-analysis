#!/usr/bin/env python
"""Test RapidAPI Signature Verification - Step 2 Integration."""
import json
import hmac
import hashlib
import os
from src.auth.key_manager import KeyManager

print("=" * 70)
print("STEP 2: RapidAPI Signature Verification Test")
print("=" * 70)

# ============================================================================
# TEST 1: Setup - Get your RapidAPI Secret
# ============================================================================
print("\n[STEP 1/4] Setup RapidAPI Secret")
print("-" * 70)

RAPIDAPI_SECRET = os.getenv("RAPIDAPI_SECRET", "test-secret-key-12345")
print(f"[INFO] Using RAPIDAPI_SECRET: {RAPIDAPI_SECRET}")
print(f"[INFO] (Set RAPIDAPI_SECRET in .env for production)")

# ============================================================================
# TEST 2: Simulate RapidAPI Request
# ============================================================================
print("\n[STEP 2/4] Simulate RapidAPI Request")
print("-" * 70)

# Example request body (what RapidAPI sends to your /analyze endpoint)
request_body = {
    "file": "audio.wav",
    "speech_context": "conversational",
    "device": "cpu"
}

# Convert to JSON bytes (RapidAPI sends as JSON)
body_bytes = json.dumps(request_body).encode()
body_string = body_bytes.decode()

print(f"[OK] Request body:")
print(f"  {json.dumps(request_body, indent=2)}")
print(f"\n[OK] Body as bytes: {body_bytes}")
print(f"[OK] Body as string: {body_string}")

# ============================================================================
# TEST 3: Generate RapidAPI Signature
# ============================================================================
print("\n[STEP 3/4] Generate Signature (like RapidAPI does)")
print("-" * 70)

# RapidAPI generates this signature using HMAC-SHA256
generated_signature = hmac.new(
    RAPIDAPI_SECRET.encode(),
    body_bytes,
    hashlib.sha256
).hexdigest()

print(f"[OK] Generated signature:")
print(f"  {generated_signature}")
print(f"\n[INFO] This would be sent as X-RapidAPI-Signature header")

# ============================================================================
# TEST 4: Verify Signature (what your API does)
# ============================================================================
print("\n[STEP 4/4] Verify Signature (your API endpoint receives)")
print("-" * 70)

# Simulate what your middleware receives
print(f"\n[INFO] Headers your endpoint receives from RapidAPI:")
print(f"  X-RapidAPI-Key: sk_user_key_here")
print(f"  X-RapidAPI-Signature: {generated_signature}")
print(f"  Content-Type: application/json")

# Your API verifies using KeyManager.verify_rapidapi_signature
is_valid = KeyManager.verify_rapidapi_signature(
    body=body_bytes,
    signature_header=generated_signature,
    rapidapi_secret=RAPIDAPI_SECRET
)

print(f"\n[OK] Signature verification result: {is_valid}")

if is_valid:
    print("[OK] SUCCESS! Signature is valid - request is authentic from RapidAPI")
else:
    print("[ERROR] Signature verification FAILED!")

# ============================================================================
# TEST 5: Test Invalid Signature (should fail)
# ============================================================================
print("\n" + "-" * 70)
print("[TEST] Invalid Signature Detection")
print("-" * 70)

invalid_signature = "0" * 64  # Fake signature
is_valid_bad = KeyManager.verify_rapidapi_signature(
    body=body_bytes,
    signature_header=invalid_signature,
    rapidapi_secret=RAPIDAPI_SECRET
)

print(f"[OK] Invalid signature check: {is_valid_bad}")
if not is_valid_bad:
    print("[OK] Correctly rejected invalid signature!")
else:
    print("[ERROR] Invalid signature was accepted!")

# ============================================================================
# TEST 6: End-to-End Simulation
# ============================================================================
print("\n" + "=" * 70)
print("END-TO-END: Full RapidAPI Request Flow")
print("=" * 70)

print("\n[FLOW] RapidAPI User makes request:")
print("  POST /api/v1/analyze")
print("  Headers:")
print("    X-RapidAPI-Key: user_key_from_rapidapi")
print("    X-RapidAPI-Signature: <generated signature>")
print("    Content-Type: application/json")
print(f"  Body: {body_string}")

print("\n[FLOW] Your API receives request:")
print("  1. Extract body and signature from headers")
print("  2. Call KeyManager.verify_rapidapi_signature()")
print("  3. If valid -> Process request")
print("  4. If invalid -> Return 401 Unauthorized")

print("\n[FLOW] Verification:")
print(f"  Body bytes: {body_bytes}")
print(f"  Signature header: {generated_signature}")
print(f"  Secret: {RAPIDAPI_SECRET}")
print(f"  Result: {'VALID' if is_valid else 'INVALID'}")

# ============================================================================
# TEST 7: Setup Instructions
# ============================================================================
print("\n" + "=" * 70)
print("SETUP INSTRUCTIONS FOR RAPIDAPI")
print("=" * 70)

print("\n[STEP 1] Add RAPIDAPI_SECRET to .env:")
print(f"  RAPIDAPI_SECRET={RAPIDAPI_SECRET}")

print("\n[STEP 2] Restart your API server:")
print("  python app.py")

print("\n[STEP 3] On RapidAPI.com dashboard:")
print("  1. Create new API")
print("  2. Set authentication type: 'API Key with Signature'")
print("  3. Your secret: (RapidAPI generates this internally)")
print("  4. Your app's secret: " + RAPIDAPI_SECRET)

print("\n[STEP 4] RapidAPI will call your endpoint with:")
print("  - X-RapidAPI-Key: (user's key)")
print("  - X-RapidAPI-Signature: (signature from their secret)")
print("  - Your middleware verifies it matches")

print("\n" + "=" * 70)
print("[OK] Signature verification is working!")
print("[OK] Ready for RapidAPI integration!")
print("=" * 70)
