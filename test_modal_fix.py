#!/usr/bin/env python
"""Test Modal endpoint with fixed code."""
import requests
import hmac
import hashlib
import os
import json

RAPIDAPI_SECRET = os.getenv("RAPIDAPI_SECRET", "64154860-f55f-11f0-b756-49f7033c3bd8")
MODAL_URL = "https://rakibj56--speech-analysis-fastapi-app.modal.run"
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

# Test with ielts5.5 audio file  
audio_file_path = 'data/ielts_part_2/ielts5.5.wav'

print("=" * 80)
print("TESTING MODAL API WITH FIXED CODE")
print("=" * 80)
print()

try:
    with open(audio_file_path, 'rb') as f:
        audio_data = f.read()
    
    # Prepare multipart request
    files = {'audio': ('ielts5.5.wav', audio_data, 'audio/wav')}
    
    # Use direct API key authentication (not RapidAPI)
    headers = {
        "X-API-Key": API_KEY,
    }
    
    url = f"{MODAL_URL}/direct/analyze"
    
    print(f"POST {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print()
    
    response = requests.post(url, files=files, headers=headers, timeout=180, verify=False)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        cb = data.get('criterion_bands', {})
        
        print("\n" + "=" * 80)
        print("SCORING RESULTS (AFTER FIX):")
        print("=" * 80)
        print(f"  Overall Band:    {data.get('overall_band')}")
        print(f"  Fluency:         {cb.get('fluency_coherence')}")
        print(f"  Pronunciation:   {cb.get('pronunciation')}")
        print(f"  Lexical:         {cb.get('lexical_resource')}")
        print(f"  Grammar:         {cb.get('grammatical_range_accuracy')}")
        print()
        print("✓ EXPECTED RESULTS:")
        print("  - Lexical = 6.0 (FIXED: was 8.0 before)")
        print("  - Overall = 6.0 (FIXED: was 7.0 before)")
        print("  - Pronunciation = 7.0 (should use real confidence data)")
        print()
        
        if cb.get('lexical_resource') == 6.0:
            print("✅ SUCCESS! Lexical score is now correct!")
        else:
            print(f"❌ FAILED: Lexical is {cb.get('lexical_resource')}, expected 6.0")
    else:
        print(f"Error response ({response.status_code}):")
        print(response.text[:500])

except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
