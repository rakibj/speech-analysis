#!/usr/bin/env python3
"""
Test job queue persistence in Modal.
Tests both /analyze and /analyze-fast endpoints with polling.
"""

import requests
import time
import sys
import os
from pathlib import Path

# Fix unicode issues on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Configuration
MODAL_BASE_URL = "https://rakibj56--speech-analysis-fastapi-app.modal.run"
TEST_AUDIO_FILE = "samples/sample4.wav"
API_KEY = "my-test-key-123"  # Direct API key (for testing)

def test_analyze_endpoint():
    """Test /analyze endpoint with polling."""
    print("\n" + "="*70)
    print("TEST 1: Full Analysis (/analyze) - Polling Test")
    print("="*70)
    
    # Upload audio file
    with open(TEST_AUDIO_FILE, "rb") as f:
        files = {"file": (Path(TEST_AUDIO_FILE).name, f, "audio/mpeg")}
        headers = {"X-API-Key": API_KEY}
        
        print(f"\n[1] Uploading audio to /analyze...")
        response = requests.post(
            f"{MODAL_BASE_URL}/api/direct/v1/analyze",
            files=files,
            headers=headers,
            timeout=60  # Allow time for initial processing
        )
        
        if response.status_code != 200:
            print(f"[FAIL] Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        job_id = result.get("job_id")
        print(f"[OK] Upload successful, Job ID: {job_id}")
        print(f"  Status: {result.get('status')}")
        print(f"  Message: {result.get('message')}")
    
    # Poll for results
    print(f"\n[2] Polling for results...")
    max_polls = 180  # 3 minutes with 1s interval
    poll_count = 0
    
    while poll_count < max_polls:
        response = requests.get(
            f"{MODAL_BASE_URL}/api/direct/v1/result/{job_id}",
            headers=headers,
            timeout=30  # Increase timeout for polling too
        )
        
        poll_count += 1
        
        if response.status_code == 404:
            print(f"  [{poll_count}] Job not found (404)")
            time.sleep(1)
            continue
        elif response.status_code == 403:
            print(f"  [{poll_count}] Access denied (403)")
            return False
        elif response.status_code == 200:
            result = response.json()
            status = result.get("status")
            print(f"  [{poll_count}] Status: {status}")
            
            if status == "completed":
                print(f"[OK] Analysis completed!")
                band_score = result.get("data", {}).get("band_score")
                print(f"  Band Score: {band_score}")
                return True
            elif status == "error":
                print(f"[FAIL] Analysis failed!")
                print(f"  Error: {result.get('detail')}")
                return False
        
        time.sleep(1)
    
    print(f"[FAIL] Timeout - analysis did not complete in {max_polls}s")
    return False


def test_analyze_fast_endpoint():
    """Test /analyze-fast endpoint with polling."""
    print("\n" + "="*70)
    print("TEST 2: Fast Analysis (/analyze-fast) - Polling Test")
    print("="*70)
    
    # Upload audio file
    with open(TEST_AUDIO_FILE, "rb") as f:
        files = {"file": (Path(TEST_AUDIO_FILE).name, f, "audio/mpeg")}
        headers = {"X-API-Key": API_KEY}
        
        print(f"\n[1] Uploading audio to /analyze-fast...")
        response = requests.post(
            f"{MODAL_BASE_URL}/api/direct/v1/analyze-fast",
            files=files,
            headers=headers,
            timeout=60  # Allow time for initial processing
        )
        
        if response.status_code != 200:
            print(f"[FAIL] Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        job_id = result.get("job_id")
        print(f"[OK] Upload successful, Job ID: {job_id}")
        print(f"  Status: {result.get('status')}")
        print(f"  Mode: {result.get('mode')}")
        print(f"  Message: {result.get('message')}")
    
    # Poll for results
    print(f"\n[2] Polling for results...")
    max_polls = 60  # 1 minute with 1s interval (fast analysis)
    poll_count = 0
    
    while poll_count < max_polls:
        response = requests.get(
            f"{MODAL_BASE_URL}/api/direct/v1/result/{job_id}",
            headers=headers,
            timeout=30  # Increase timeout for polling too
        )
        
        poll_count += 1
        
        if response.status_code == 404:
            print(f"  [{poll_count}] Job not found (404)")
            time.sleep(1)
            continue
        elif response.status_code == 403:
            print(f"  [{poll_count}] Access denied (403)")
            return False
        elif response.status_code == 200:
            result = response.json()
            status = result.get("status")
            print(f"  [{poll_count}] Status: {status}")
            
            if status == "completed":
                print(f"[OK] Fast analysis completed!")
                band_score = result.get("data", {}).get("band_score")
                print(f"  Band Score: {band_score}")
                return True
            elif status == "error":
                print(f"[FAIL] Fast analysis failed!")
                print(f"  Error: {result.get('detail')}")
                return False
        
        time.sleep(1)
    
    print(f"[FAIL] Timeout - fast analysis did not complete in {max_polls}s")
    return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("TESTING JOB QUEUE PERSISTENCE IN MODAL")
    print("="*70)
    
    # Check test file exists
    if not Path(TEST_AUDIO_FILE).exists():
        print(f"[FAIL] Test audio file not found: {TEST_AUDIO_FILE}")
        return 1
    
    # Run tests
    results = {
        "Full Analysis": test_analyze_endpoint(),
        "Fast Analysis": test_analyze_fast_endpoint()
    }
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + ("="*70))
    if all_passed:
        print("[OK] ALL TESTS PASSED")
        return 0
    else:
        print("[FAIL] SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
