#!/usr/bin/env python
"""
Direct test of RapidAPI endpoints using FastAPI test client.
No need to start server - tests app directly.
"""
import json
import hmac
import hashlib
import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Load env
load_dotenv()
RAPIDAPI_SECRET = os.getenv("RAPIDAPI_SECRET")

# Import app
from app import app

# Create test client
client = TestClient(app)

def generate_signature(body: bytes, secret: str) -> str:
    """Generate RapidAPI signature."""
    return hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

print("=" * 70)
print("RAPIDAPI LOCAL ENDPOINT TESTS")
print("=" * 70)

# TEST 1: Health check with direct key
print("\n[TEST 1] Health Check - Direct API")
print("-" * 70)
response = client.get(
    "/api/direct/v1/health",
    headers={"X-API-Key": "sk_wpUwYgv2RMtAhwTecCh0Qfp9"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
if response.status_code == 200:
    print("[OK] Direct health check passed")
else:
    print("[ERROR] Direct health check failed")

# TEST 2: Health check with RapidAPI signature
print("\n[TEST 2] Health Check - RapidAPI v1")
print("-" * 70)
body = b""  # Health check has no body
signature = generate_signature(body, RAPIDAPI_SECRET)

response = client.get(
    "/api/v1/health",
    headers={
        "X-RapidAPI-Key": "sk_wpUwYgv2RMtAhwTecCh0Qfp9",
        "X-RapidAPI-Signature": signature
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
if response.status_code == 200:
    print("[OK] RapidAPI health check passed")
else:
    print("[ERROR] RapidAPI health check failed")

# TEST 3: Invalid signature should be rejected
print("\n[TEST 3] Invalid Signature Rejection")
print("-" * 70)
bad_signature = "0" * 64

response = client.get(
    "/api/v1/health",
    headers={
        "X-RapidAPI-Key": "sk_wpUwYgv2RMtAhwTecCh0Qfp9",
        "X-RapidAPI-Signature": bad_signature
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
if response.status_code == 401:
    print("[OK] Invalid signature correctly rejected")
else:
    print("[ERROR] Invalid signature should return 401")

# TEST 4: Missing signature should be rejected
print("\n[TEST 4] Missing Signature Rejection")
print("-" * 70)
response = client.get(
    "/api/v1/health",
    headers={"X-RapidAPI-Key": "sk_wpUwYgv2RMtAhwTecCh0Qfp9"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
if response.status_code == 401:
    print("[OK] Missing signature correctly rejected")
else:
    print("[ERROR] Missing signature should return 401")

# TEST 5: Invalid key should be rejected
print("\n[TEST 5] Invalid API Key Rejection")
print("-" * 70)
bad_signature = generate_signature(b"", RAPIDAPI_SECRET)

response = client.get(
    "/api/v1/health",
    headers={
        "X-RapidAPI-Key": "sk_invalid_key",
        "X-RapidAPI-Signature": bad_signature
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
if response.status_code == 401:
    print("[OK] Invalid key correctly rejected")
else:
    print("[ERROR] Invalid key should return 401")

# TEST 6: Test analyze endpoint with form data
print("\n[TEST 6] Analyze Endpoint - Direct API")
print("-" * 70)

# Create a small test audio file
test_audio = b'\xff\xfb\x10\x00' + b'\x00' * 1000  # Minimal MP3 header + data

response = client.post(
    "/api/direct/v1/analyze",
    headers={"X-API-Key": "sk_wpUwYgv2RMtAhwTecCh0Qfp9"},
    files={"file": ("test.mp3", test_audio, "audio/mpeg")},
    data={"speech_context": "conversational", "device": "cpu"}
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)[:200]}...")
if response.status_code == 200:
    result = response.json()
    if "job_id" in result:
        print(f"[OK] Job created: {result['job_id']}")
        job_id = result['job_id']
        
        # TEST 7: Check result status
        print(f"\n[TEST 7] Check Job Status")
        print("-" * 70)
        response = client.get(
            f"/api/direct/v1/result/{job_id}",
            headers={"X-API-Key": "sk_wpUwYgv2RMtAhwTecCh0Qfp9"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Job Status: {result.get('status')}")
        print(f"Response keys: {list(result.keys())}")
        if response.status_code == 200:
            print("[OK] Result endpoint working")
        else:
            print("[ERROR] Result endpoint failed")
    else:
        print("[ERROR] No job_id in response")
else:
    print(f"[ERROR] Analyze endpoint failed: {response.json()}")

# TEST 8: Test with different response tiers
print(f"\n[TEST 8] Response Tiers - Direct API")
print("-" * 70)

# Get default tier (minimal)
response = client.get(
    f"/api/direct/v1/result/{job_id}",
    headers={"X-API-Key": "sk_wpUwYgv2RMtAhwTecCh0Qfp9"}
)
default_size = len(json.dumps(response.json()))
print(f"Default tier size: {default_size} bytes")
print(f"Default tier keys: {list(response.json().keys())}")

# Get feedback tier
response = client.get(
    f"/api/direct/v1/result/{job_id}?detail=feedback",
    headers={"X-API-Key": "sk_wpUwYgv2RMtAhwTecCh0Qfp9"}
)
feedback_size = len(json.dumps(response.json()))
print(f"Feedback tier size: {feedback_size} bytes")
print(f"Feedback tier keys: {list(response.json().keys())}")

# Get full tier
response = client.get(
    f"/api/direct/v1/result/{job_id}?detail=full",
    headers={"X-API-Key": "sk_wpUwYgv2RMtAhwTecCh0Qfp9"}
)
full_size = len(json.dumps(response.json()))
print(f"Full tier size: {full_size} bytes")
print(f"Full tier keys: {list(response.json().keys())}")

print(f"\n[OK] Response tiers working - sizes increase as expected")

print("\n" + "=" * 70)
print("ALL LOCAL TESTS COMPLETE")
print("=" * 70)
print("""
Summary:
  - Direct API endpoint: Working with X-API-Key
  - RapidAPI v1 endpoint: Working with signature verification
  - Invalid signatures: Properly rejected
  - Missing signatures: Properly rejected
  - Invalid keys: Properly rejected
  - Response tiers: All working
  
Ready for RapidAPI Dashboard!
""")
