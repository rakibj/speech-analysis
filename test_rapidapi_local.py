#!/usr/bin/env python
"""
Test RapidAPI endpoints locally before deployment.
Simulates RapidAPI calls to /api/v1/ endpoints with proper headers.
"""
import os
import sys
import json
import hmac
import hashlib
import requests
import time
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

RAPIDAPI_SECRET = os.getenv("RAPIDAPI_SECRET")
BASE_URL = "http://localhost:8000"
API_KEY = "sk_wpUwYgv2RMtAhwTecCh0Qfp9"

def generate_rapidapi_signature(body: str, secret: str) -> str:
    """Generate RapidAPI HMAC-SHA256 signature."""
    if isinstance(body, str):
        body = body.encode()
    return hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

def make_rapidapi_request(method: str, endpoint: str, data: dict = None, files: dict = None) -> dict:
    """
    Make a request to /api/v1/ endpoint with RapidAPI headers.
    
    Args:
        method: GET, POST, etc.
        endpoint: /health, /analyze, /result/{job_id}
        data: JSON data for body
        files: Files for multipart upload
        
    Returns:
        Response dict with status, data, headers
    """
    url = f"{BASE_URL}/api/v1{endpoint}"
    
    # Prepare body for signature
    if files:
        # For multipart, body is empty string for signature
        body = ""
    elif data:
        body = json.dumps(data)
    else:
        body = ""
    
    # Generate signature
    signature = generate_rapidapi_signature(body, RAPIDAPI_SECRET)
    
    # Build headers
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Signature": signature,
        "X-RapidAPI-Host": "localhost:8000"
    }
    
    print(f"\n{'='*70}")
    print(f"{method} {url}")
    print(f"{'='*70}")
    print("Headers:")
    print(f"  X-RapidAPI-Key: {API_KEY}")
    print(f"  X-RapidAPI-Signature: {signature}")
    print(f"  X-RapidAPI-Host: localhost:8000")
    
    if data:
        print(f"Body: {body}")
    
    # Make request
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            if files:
                # Multipart upload - don't set Content-Type
                response = requests.post(url, headers=headers, files=files, timeout=120)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, data=body, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"\nStatus: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return {
                "status": response.status_code,
                "data": result,
                "success": 200 <= response.status_code < 300
            }
        except:
            print(f"Response (text): {response.text}")
            return {
                "status": response.status_code,
                "data": response.text,
                "success": 200 <= response.status_code < 300
            }
    
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server!")
        print("Make sure to run: python app.py")
        return {"status": 0, "data": None, "success": False}
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {"status": 0, "data": str(e), "success": False}

def main():
    print("\n" + "="*70)
    print("RAPIDAPI LOCAL ENDPOINT TESTS")
    print("="*70)
    
    if not RAPIDAPI_SECRET:
        print("[ERROR] RAPIDAPI_SECRET not set in .env!")
        return False
    
    print(f"\nConfiguration:")
    print(f"  Base URL: {BASE_URL}")
    print(f"  API Key: {API_KEY}")
    print(f"  Secret: {RAPIDAPI_SECRET[:10]}...{RAPIDAPI_SECRET[-10:]}")
    
    all_passed = True
    
    # TEST 1: Health Check
    print("\n\n" + "*"*70)
    print("TEST 1: Health Check (/api/v1/health)")
    print("*"*70)
    result = make_rapidapi_request("GET", "/health")
    if result["success"] and result["data"].get("status") == "healthy":
        print("[OK] Health check passed")
    else:
        print("[FAIL] Health check failed")
        all_passed = False
    
    # TEST 2: Invalid signature should fail
    print("\n\n" + "*"*70)
    print("TEST 2: Invalid Signature (should fail with 401)")
    print("*"*70)
    
    url = f"{BASE_URL}/api/v1/health"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Signature": "invalid_signature_12345",
        "X-RapidAPI-Host": "localhost:8000"
    }
    
    print(f"GET {url}")
    print("Headers: (with INVALID signature)")
    print(f"  X-RapidAPI-Key: {API_KEY}")
    print(f"  X-RapidAPI-Signature: invalid_signature_12345")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("[OK] Invalid signature correctly rejected")
        else:
            print(f"[WARN] Expected 401, got {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        all_passed = False
    
    # TEST 3: Analyze audio
    print("\n\n" + "*"*70)
    print("TEST 3: Submit Audio for Analysis (/api/v1/analyze)")
    print("*"*70)
    
    # Create a dummy audio file for testing
    dummy_audio = b"RIFF" + b"\x00" * 100  # Minimal WAV header
    
    files = {
        "file": ("test.wav", dummy_audio, "audio/wav"),
        "speech_context": (None, "conversational"),
        "device": (None, "cpu")
    }
    
    analyze_result = make_rapidapi_request("POST", "/analyze", files=files)
    
    if analyze_result["success"]:
        print("[OK] Audio submission successful")
        job_id = analyze_result["data"].get("job_id")
        if job_id:
            print(f"Job ID: {job_id}")
            
            # TEST 4: Poll for results
            print("\n\n" + "*"*70)
            print(f"TEST 4: Poll Results (/api/v1/result/{job_id})")
            print("*"*70)
            
            # Poll a few times
            for i in range(3):
                result = make_rapidapi_request("GET", f"/result/{job_id}")
                status = result["data"].get("status") if result["success"] else "error"
                print(f"\nPoll #{i+1}: Status = {status}")
                
                if status == "completed":
                    print("[OK] Analysis completed!")
                    print(f"Band Score: {result['data'].get('overall_band')}")
                    break
                elif status == "error":
                    print(f"[ERROR] Analysis failed: {result['data'].get('error')}")
                    break
                else:
                    print("Still processing... waiting 2 seconds")
                    time.sleep(2)
        else:
            print("[WARN] No job_id in response")
            all_passed = False
    else:
        print(f"[FAIL] Audio submission failed: {analyze_result['data']}")
        all_passed = False
    
    # TEST 5: Invalid job ID should return 404
    print("\n\n" + "*"*70)
    print("TEST 5: Invalid Job ID (should return 404)")
    print("*"*70)
    result = make_rapidapi_request("GET", "/result/invalid-job-id")
    if result["status"] == 404:
        print("[OK] Invalid job correctly rejected with 404")
    else:
        print(f"[WARN] Expected 404, got {result['status']}")
    
    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if all_passed:
        print("""
[OK] ALL TESTS PASSED!

Your /api/v1/ endpoints are ready for RapidAPI:
  - Health check working
  - Signature verification working
  - Invalid signatures rejected
  - Analysis submission working
  - Result polling working

Next steps:
  1. Deploy to Modal (or keep running locally)
  2. Register API on RapidAPI dashboard
  3. Point RapidAPI to your endpoints
  4. Users can now call your API through RapidAPI
        """)
    else:
        print("""
[WARN] Some tests failed - check configuration and server

Troubleshooting:
  - Make sure 'python app.py' is running
  - Check .env has RAPIDAPI_SECRET set
  - Verify API_KEY matches your hardcoded key
  - Check server logs for errors
        """)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
