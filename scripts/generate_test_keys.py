#!/usr/bin/env python
"""Generate test API keys for direct access and RapidAPI testing."""
import sys
sys.path.insert(0, '.')

from src.auth.key_manager import KeyManager


def main():
    """Generate test API keys."""
    print("=" * 70)
    print("Speech Analysis API - Test Key Generator")
    print("=" * 70)
    
    # Generate a direct access key
    direct_key, direct_hash = KeyManager.generate_key("test-direct", owner_type="direct")
    print(f"\n✅ Direct Access API Key:")
    print(f"   Key:  {direct_key}")
    print(f"   Hash: {direct_hash[:16]}...")
    print(f"\n   Use with header: X-API-Key: {direct_key}")
    print(f"   Endpoint:        /api/direct/v1/analyze")
    
    # Generate a RapidAPI key (mock)
    rapidapi_key, rapidapi_hash = KeyManager.generate_key("test-rapidapi", owner_type="rapidapi")
    print(f"\n✅ RapidAPI Mock Key:")
    print(f"   Key:  {rapidapi_key}")
    print(f"   Hash: {rapidapi_hash[:16]}...")
    print(f"\n   Use with header: X-RapidAPI-Key: {rapidapi_key}")
    print(f"   Endpoint:        /api/v1/analyze")
    print(f"   Requires:        X-RapidAPI-Signature (HMAC-SHA256)")
    
    print("\n" + "=" * 70)
    print("Testing Direct Access:")
    print(f"curl -X POST http://localhost:8000/api/direct/v1/health \\")
    print(f"  -H 'X-API-Key: {direct_key}'")
    
    print("\n" + "=" * 70)
    print("Stored Keys (in-memory):")
    keys = KeyManager.get_keys_for_testing()
    for key_hash, info in keys.items():
        print(f"  {key_hash[:16]}... - {info['name']} ({info['owner_type']})")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
