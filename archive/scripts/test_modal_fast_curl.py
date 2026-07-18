#!/usr/bin/env python3
"""
Simple test to verify /analyze-fast works without SSL issues
"""
import json
import subprocess
import time
import sys

# Test file path
TEST_FILE = "data/ielts_part_2/ielts7.wav"

def test_with_curl():
    """Test using curl to avoid SSL issues"""
    
    print("=" * 70)
    print("PRODUCTION VERIFICATION - /analyze-fast")
    print("=" * 70)
    print(f"\nEndpoint: https://rakibj56--speech-analysis-fastapi-app.modal.run")
    print(f"Test file: {TEST_FILE}")
    
    try:
        # Upload file and get job_id
        print("\n[1/3] Submitting /analyze-fast request...")
        cmd = [
            'curl',
            '-s',
            '-X', 'POST',
            '-F', f'file=@{TEST_FILE}',
            '-F', 'speech_context=ielts',
            '-F', 'device=cpu',
            'https://rakibj56--speech-analysis-fastapi-app.modal.run/analyze-fast'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"[ERROR] Request failed: {result.stderr}")
            return False
        
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid JSON response: {result.stdout[:200]}")
            return False
        
        job_id = response.get('job_id')
        status = response.get('status')
        mode = response.get('mode')
        
        if not job_id:
            print(f"[ERROR] No job_id in response: {response}")
            return False
        
        print(f"[OK] Request submitted:")
        print(f"  Job ID: {job_id}")
        print(f"  Status: {status}")
        print(f"  Mode: {mode}")
        
        # Poll for result
        print(f"\n[2/3] Polling for results...")
        max_wait = 90
        elapsed = 0
        
        while elapsed < max_wait:
            cmd = [
                'curl',
                '-s',
                f'https://rakibj56--speech-analysis-fastapi-app.modal.run/result/{job_id}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout)
                    job_status = response.get('status')
                    
                    if job_status == 'completed':
                        print(f"[OK] Analysis completed!")
                        
                        # Extract results
                        data = response.get('data', {})
                        band_score = data.get('band_scores', {}).get('overall_band')
                        transcript_len = len((data.get('transcript', '')).split())
                        metadata = data.get('metadata', {})
                        opt_phase = metadata.get('optimization_phase')
                        
                        print(f"\n[3/3] Results:")
                        print(f"  Band Score: {band_score}")
                        print(f"  Transcript Words: {transcript_len}")
                        print(f"  Optimization Phase: {opt_phase}")
                        
                        if band_score and opt_phase == 1:
                            print(f"\n[SUCCESS] /analyze-fast is working in production!")
                            return True
                        else:
                            print(f"[ERROR] Invalid result structure")
                            print(f"  Full response: {json.dumps(data, indent=2)[:500]}")
                            return False
                        
                    elif job_status == 'error':
                        error = response.get('detail', response.get('error', 'Unknown error'))
                        print(f"[ERROR] Analysis failed: {error}")
                        return False
                    
                    elif job_status == 'processing':
                        print(f"  [..] Processing... ({elapsed}s elapsed)")
                
                except json.JSONDecodeError:
                    print(f"[ERROR] Invalid JSON: {result.stdout[:200]}")
            
            time.sleep(3)
            elapsed += 3
        
        print(f"[ERROR] Timeout waiting for results after {max_wait}s")
        return False
        
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Request timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_curl()
    sys.exit(0 if success else 1)
