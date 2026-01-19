"""
Admin utilities for managing API keys.

Use this for production key management until we have a database.
"""
from src.auth.key_manager import KeyManager


def create_production_keys():
    """Create production API keys for known customers."""
    
    # RapidAPI key (one master key for all RapidAPI users)
    rapidapi_key, _ = KeyManager.generate_key(
        name="RapidAPI Production",
        owner_type="rapidapi"
    )
    print(f"RapidAPI Production Key: {rapidapi_key}")
    print("Use this key for all RapidAPI requests via X-RapidAPI-Key header")
    print()
    
    # Direct access keys (one per customer)
    customers = [
        ("Customer A", "direct"),
        ("Customer B", "direct"),
        ("Customer C", "direct"),
    ]
    
    direct_keys = {}
    for customer_name, owner_type in customers:
        key, key_hash = KeyManager.generate_key(customer_name, owner_type)
        direct_keys[customer_name] = key
        print(f"{customer_name:20} → {key}")
    
    return rapidapi_key, direct_keys


if __name__ == "__main__":
    print("=" * 70)
    print("Production API Key Generator")
    print("=" * 70)
    print()
    
    rapidapi_key, direct_keys = create_production_keys()
    
    print()
    print("=" * 70)
    print("Store these keys securely (e.g., in a secrets manager)")
    print("=" * 70)
