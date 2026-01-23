#!/usr/bin/env python3
"""
Test /analyze-fast endpoint in production on Modal
"""
import requests
import time
from pathlib import Path

# Modal API endpoint
API_URL = "https://rakibj56--speech-analysis-fastapi-app.modal.run"
TEST_FILE = "data/ielts_part_2/ielts7.wav"

def test_analyze_fast():
    """Test /analyze-fast endpoint on Modal"""
    
    if not Path(TEST_FILE).exists():
        print(f"Test file not found: {TEST_FILE}")
        return False
    
    print("=" * 70)
    print("PRODUCTION VERIFICATION - /analyze-fast Endpoint")
    print("=" * 70)
    print(f"\nTesting: {API_URL}/analyze-fast")
    print(f"Test file: {TEST_FILE}")
    
    try:
        # Prepare request
        with open(TEST_FILE, 'rb') as f:
            files = {'file': f}
            data = {
                'speech_context': 'ielts',
                'device': 'cpu'
            }
            
            # Send request
            print("\n[INFO] Sending request to /analyze-fast...")
            start = time.time()
            response = requests.post(
                f"{API_URL}/analyze-fast",
                files=files,
                data=data,
                timeout=120
            )
            elapsed = time.time() - start
            
        # Check response
        print(f"[INFO] Response received in {elapsed:.2f}s")
        print(f"[INFO] Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ERROR] Request failed: {response.text}")
            return False
        
        result = response.json()
        print(f"[OK] Response is valid JSON")
        
        # Check fields
        if 'job_id' not in result:
            print(f"[ERROR] Missing job_id in response")
            return False
        
        job_id = result['job_id']
        status = result.get('status')
        mode = result.get('mode')
        
        print(f"\n[OK] Analysis queued:")
        print(f"  Job ID: {job_id}")
        print(f"  Status: {status}")
        print(f"  Mode: {mode}")
        
        # Poll for result
        print(f"\n[INFO] Polling for results...")
        max_wait = 60
        poll_interval = 2
        elapsed_poll = 0
        
        while elapsed_poll < max_wait:
            response = requests.get(
                f"{API_URL}/result/{job_id}",
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                job_status = result.get('status')
                
                if job_status == 'completed':
                    print(f"[OK] Analysis completed!")
                    
                    # Check result structure
                    data = result.get('data', {})
                    if not data:
                        print(f"[ERROR] No data in result")
                        return False
                    
                    band_score = data.get('band_scores', {}).get('overall_band')
                    transcript_len = len((data.get('transcript', '')).split())
                    metadata = data.get('metadata', {})
                    opt_phase = metadata.get('optimization_phase')
                    
                    print(f"\n[Results]")
                    print(f"  Band Score: {band_score}")
                    print(f"  Transcript Words: {transcript_len}")
                    print(f"  Optimization Phase: {opt_phase}")
                    
                    if band_score and opt_phase == 1:
                        print(f"\n[SUCCESS] /analyze-fast is working correctly in production!")
                        return True
                    else:
                        print(f"[ERROR] Missing required fields")
                        return False
                        
                elif job_status == 'error':
                    error = result.get('error')
                    print(f"[ERROR] Analysis failed: {error}")
                    return False
                
                elif job_status == 'processing':
                    print(f"  [..] Still processing... ({elapsed_poll}s)")
            
            time.sleep(poll_interval)
            elapsed_poll += poll_interval
        
        print(f"[ERROR] Timeout waiting for results")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_analyze_fast()
    exit(0 if success else 1)
