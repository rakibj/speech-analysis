# src/audio/model_cache.py
"""Shared in-process model cache for audio/ASR models.

Whisper, WhisperX alignment, and Wav2Vec2 model weights were previously reloaded
from disk on every single request. This gives every caller a small keyed cache
so repeated requests in the same process (or warm Modal container) reuse
already-loaded models instead of paying disk I/O + deserialization again.

Controlled by the CACHE_MODELS env var (default: enabled).
"""
import os
import threading
from typing import Any, Callable, Dict, Hashable

_lock = threading.Lock()
_cache: Dict[Hashable, Any] = {}


def model_caching_enabled() -> bool:
    """Whether cached model reuse is enabled (CACHE_MODELS env var, default true)."""
    return os.getenv("CACHE_MODELS", "true").strip().lower() not in ("false", "0", "no")


def get_cached_model(key: Hashable, loader: Callable[[], Any]) -> Any:
    """
    Return the cached object for `key`, loading it via `loader()` on first use.

    Args:
        key: Hashable cache key, e.g. (model_kind, model_name, device)
        loader: Zero-arg callable that loads and returns the model/object

    Returns:
        The cached (or freshly loaded) object.

    Notes:
        When CACHE_MODELS is disabled, `loader()` runs on every call and nothing
        is cached - matches the pre-caching behavior for environments that need it
        (e.g. memory-constrained containers running a single request at a time).
    """
    if not model_caching_enabled():
        return loader()

    with _lock:
        if key not in _cache:
            _cache[key] = loader()
        return _cache[key]
