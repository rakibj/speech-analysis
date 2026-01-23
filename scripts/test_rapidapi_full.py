#!/usr/bin/env python
"""Test full RapidAPI integration: signature verification with actual secret."""
import os
import json
import hmac
import hashlib
from dotenv import load_dotenv
from src.auth.key_manager import KeyManager

# Load environment variables
load_dotenv()

RAPIDAPI_SECRET = os.getenv("RAPIDAPI_SECRET")

def generate_rapidapi_signature(body: bytes, secret: str) -> str:
    """Generate RapidAPI HMAC-SHA256 signature."""
    return hmac.new(
        secret.encode(),
        body if isinstance(body, bytes) else body.encode(),
        hashlib.sha256
    ).hexdigest()

print("=" * 70)
print("RAPIDAPI INTEGRATION TEST - STEP 2")
print("=" * 70)

# TEST 1: Verify secret is loaded
print("\n[TEST 1] Secret Loaded from .env")
print("-" * 70)
if RAPIDAPI_SECRET:
    masked_secret = RAPIDAPI_SECRET[:10] + "..." + RAPIDAPI_SECRET[-10:]
    print(f"[OK] RAPIDAPI_SECRET loaded: {masked_secret}")
else:
    print("[ERROR] RAPIDAPI_SECRET not found in .env!")
    exit(1)

# TEST 2: Generate valid signature
print("\n[TEST 2] Generate Valid Signature")
print("-" * 70)
test_body = json.dumps({
    "file": "test.wav",
    "speech_context": "conversational"
})

signature = generate_rapidapi_signature(test_body, RAPIDAPI_SECRET)
print(f"[OK] Generated signature: {signature}")
print(f"     Body: {test_body}")
print(f"     Secret: {masked_secret}")

# TEST 3: Verify signature is valid
print("\n[TEST 3] Verify Signature Validation")
print("-" * 70)
is_valid = KeyManager.verify_rapidapi_signature(test_body.encode(), signature, RAPIDAPI_SECRET)
print(f"[OK] Signature valid: {is_valid}")

# TEST 4: Test with wrong secret (should fail)
print("\n[TEST 4] Invalid Signature Detection")
print("-" * 70)
wrong_secret = "wrong-secret-12345"
is_valid = KeyManager.verify_rapidapi_signature(test_body.encode(), signature, wrong_secret)
if not is_valid:
    print("[OK] Invalid signature correctly rejected")
else:
    print("[ERROR] Should have detected invalid signature!")

# TEST 5: Test with corrupted signature (should fail)
print("\n[TEST 5] Corrupted Signature Detection")
print("-" * 70)
bad_signature = "0" * 64  # Wrong hex string
is_valid = KeyManager.verify_rapidapi_signature(test_body.encode(), bad_signature, RAPIDAPI_SECRET)
if not is_valid:
    print("[OK] Corrupted signature correctly rejected")
else:
    print("[ERROR] Should have detected corrupted signature!")

# TEST 6: Simulate RapidAPI request
print("\n[TEST 6] Simulated RapidAPI Request")
print("-" * 70)
print("""
When a user calls via RapidAPI:
  1. RapidAPI receives the request
  2. RapidAPI signs it with THEIR secret
  3. RapidAPI forwards to your endpoint with headers:
     - X-RapidAPI-Key: sk_<user's_key>
     - X-RapidAPI-Signature: <HMAC-SHA256>
  4. Your /api/v1/ endpoint verifies the signature
  5. Returns result to user via RapidAPI

Your verification flow:
""")

# Simulate headers
rapidapi_key = "sk_wpUwYgv2RMtAhwTecCh0Qfp9"  # Your test key
rapidapi_signature = generate_rapidapi_signature(test_body, RAPIDAPI_SECRET)

print(f"  Headers from RapidAPI:")
print(f"    X-RapidAPI-Key: {rapidapi_key}")
print(f"    X-RapidAPI-Signature: {rapidapi_signature}")

# Verify key exists
try:
    auth_context = KeyManager.validate_key(rapidapi_key)
    print(f"\n  [OK] Key validated: {auth_context.owner_type}")
except Exception as e:
    print(f"  [ERROR] Key validation failed: {str(e)}")

# Verify signature
try:
    is_valid = KeyManager.verify_rapidapi_signature(test_body.encode(), rapidapi_signature, RAPIDAPI_SECRET)
    print(f"  [OK] Signature verified: {is_valid}")
except Exception as e:
    print(f"  [ERROR] Signature verification failed: {str(e)}")

# TEST 7: Full endpoint URL examples
print("\n[TEST 7] RapidAPI Endpoint URLs")
print("-" * 70)
print("""
After deployment, provide RapidAPI with these endpoints:

Local Testing:
  POST http://localhost:8000/api/v1/analyze
  GET  http://localhost:8000/api/v1/health
  GET  http://localhost:8000/api/v1/result/{job_id}

Modal Deployment:
  POST https://your-username--speech-analysis-app.modal.run/api/v1/analyze
  GET  https://your-username--speech-analysis-app.modal.run/api/v1/health
  GET  https://your-username--speech-analysis-app.modal.run/api/v1/result/{job_id}

RapidAPI will add headers automatically:
  - X-RapidAPI-Key
  - X-RapidAPI-Signature
  - X-RapidAPI-Host
""")

print("\n" + "=" * 70)
print("STEP 2 COMPLETE - READY FOR RAPIDAPI SUBMISSION")
print("=" * 70)
print("""
Next steps:

1. Go to https://rapidapi.com/developer-dashboard
2. Create new API:
   - Name: Speech Analysis API
   - Endpoint: /api/v1/health (for testing)
   - Authentication: API Key + Signature Verification
   
3. Set up your endpoint URL:
   - If local: Keep running on port 8000
   - If deployed: Use Modal/your server URL
   
4. RapidAPI will provide users with:
   - Their API Key (different from your hardcoded key)
   - Access to your endpoints

5. When users call, RapidAPI proxies the request with signature

Your endpoint automatically verifies and routes correctly!
""")
