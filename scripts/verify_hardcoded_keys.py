#!/usr/bin/env python
"""Verify hardcoded keys are working."""
from src.auth.key_manager import KeyManager

print('=== Hardcoded Keys Validation ===')
print()

# Show current keys
keys = KeyManager.get_keys_for_testing()
print(f'Hardcoded keys in system: {len(keys)}')
for key_hash, info in keys.items():
    print(f'  - {info["name"]:20} ({info["owner_type"]:10}) {key_hash[:16]}...')

print()
print('Testing validation:')

# Test the hardcoded key
try:
    auth = KeyManager.validate_key('sk_wpUwYgv2RMtAhwTecCh0Qfp9')
    print(f'  [OK] Key validated successfully')
    print(f'       Owner type: {auth.owner_type}')
    print(f'       Verified: {auth.verified}')
except Exception as e:
    print(f'  [ERROR] {e}')

print()
print('When deployed to Modal:')
print('  - This hardcoded dict will be in the code')
print('  - Container restarts? Keys still there')
print('  - Users authenticate with sk_wpUwYgv2RMtAhwTecCh0Qfp9')
print('  - No database needed!')
