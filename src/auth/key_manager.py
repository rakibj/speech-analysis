"""Key manager for API key validation and RapidAPI signature verification."""
import hmac
import hashlib
import secrets
from typing import Optional, Dict, Tuple
from src.models.auth import InvalidAPIKeyError, AuthContext
import os


class KeyManager:
    """Manages API key validation and RapidAPI signature verification."""
    
    # Hardcoded valid API keys for development
    # Format: {key_hash: {"name": str, "owner_type": str}}
    # Generate new keys with: KeyManager.create_test_key("your-name")
    VALID_KEYS = {
        "5cc0f4d6ecfb565223c8e714a027758f0774dbb7fd21b9be12d152fc0265c6e9": {
            "name": "my-dev-key",
            "owner_type": "direct"
        },
    }
    
    # Prefix for generated keys
    KEY_PREFIX = "sk_"
    
    @classmethod
    def generate_key(cls, name: str, owner_type: str = "direct") -> Tuple[str, str]:
        """
        Generate a new test API key.
        
        Args:
            name: Human-readable name
            owner_type: "direct" or "rapidapi"
            
        Returns:
            Tuple of (key, key_hash)
            
        Note: For production use, add the key_hash to VALID_KEYS dict above
        """
        # Generate short alphanumeric key like "sk_AbCdEfGhIjKlMnOpQrStUvWxYz"
        token = secrets.token_urlsafe(24).replace("-", "").replace("_", "")[:24]
        key = f"{cls.KEY_PREFIX}{token}"
        key_hash = cls._hash_key(key)
        
        print(f"\n[OK] Generated key: {key}")
        print(f"[OK] Key hash: {key_hash}")
        print(f"\n[INFO] To use this key, add to VALID_KEYS in key_manager.py:")
        print(f'\n    "{key_hash}": {{"name": "{name}", "owner_type": "{owner_type}"}},')
        print()
        
        return key, key_hash
    
    @classmethod
    def validate_key(cls, api_key: str) -> AuthContext:
        """
        Validate an API key against hardcoded VALID_KEYS.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            AuthContext with key info
            
        Raises:
            InvalidAPIKeyError if key is invalid
        """
        if not api_key:
            raise InvalidAPIKeyError("API key is required")
        
        key_hash = cls._hash_key(api_key)
        
        # Check against hardcoded valid keys
        if key_hash not in cls.VALID_KEYS:
            raise InvalidAPIKeyError("Invalid API key")
        
        key_info = cls.VALID_KEYS[key_hash]
        
        return AuthContext(
            api_key=api_key,
            key_hash=key_hash,
            owner_type=key_info["owner_type"],
            verified=True
        )
    
    @classmethod
    def verify_rapidapi_signature(
        cls,
        body: bytes,
        signature_header: str,
        rapidapi_secret: Optional[str] = None
    ) -> bool:
        """
        Verify RapidAPI request signature.
        
        Args:
            body: Request body bytes
            signature_header: X-RapidAPI-Signature header value
            rapidapi_secret: RapidAPI secret (from env or param)
            
        Returns:
            True if signature is valid
        """
        if not rapidapi_secret:
            rapidapi_secret = os.getenv("RAPIDAPI_SECRET")
        
        if not rapidapi_secret:
            # If no secret configured, skip verification but warn
            import logging
            logging.warning("RAPIDAPI_SECRET not configured, skipping signature verification")
            return True
        
        # Reconstruct signature
        expected_sig = hmac.new(
            rapidapi_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison
        return hmac.compare_digest(signature_header, expected_sig)
    
    @classmethod
    def _hash_key(cls, key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @classmethod
    def get_keys_for_testing(cls) -> Dict[str, Dict]:
        """Get all hardcoded valid keys."""
        return cls.VALID_KEYS.copy()
    
    @classmethod
    def clear_keys(cls) -> None:
        """Clear all keys (for testing only)."""
        cls.VALID_KEYS.clear()
