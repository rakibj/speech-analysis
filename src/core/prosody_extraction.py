import numpy as np
import librosa
from pathlib import Path
import sys
import warnings

PROJECT_ROOT = Path.cwd().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Suppress librosa audioread deprecation warning
warnings.filterwarnings('ignore', category=FutureWarning, module='librosa')


def prosody_variation_robust(audio_path: str, hop_length: int = 256) -> float:
    """
    Robust prosody variation using:
      - YIN for speed
      - IQR-based outlier removal
      - Median absolute deviation (MAD) as variation metric
    """
    y, sr = librosa.load(audio_path, sr=None)
    
    # Estimate F0 with YIN (faster than PYIN)
    f0 = librosa.yin(
        y,
        fmin=librosa.note_to_hz('C2'),   # 65 Hz
        fmax=librosa.note_to_hz('C6'),   # 1046 Hz (reduce max to avoid harmonics)
        sr=sr,
        hop_length=hop_length
    )
    
    # Remove unvoiced frames (YIN returns 0 for unvoiced)
    voiced_f0 = f0[f0 > 0]
    
    if len(voiced_f0) < 10:  # Need min frames
        return 0.0

    # Remove outliers using IQR (keeps only plausible F0)
    q25, q75 = np.percentile(voiced_f0, [25, 75])
    iqr = q75 - q25
    lower_bound = q25 - 1.5 * iqr
    upper_bound = q75 + 1.5 * iqr
    filtered_f0 = voiced_f0[(voiced_f0 >= lower_bound) & (voiced_f0 <= upper_bound)]
    
    if len(filtered_f0) == 0:
        return 0.0
        
    # Use MAD (robust to outliers) instead of std
    # Convert to Hz-scale MAD: MAD ≈ 0.6745 * σ for normal dist, but we care about relative variation
    mad = np.median(np.abs(filtered_f0 - np.median(filtered_f0)))
    return float(mad)


def monotone_detected(prosody_var: float, threshold: float = 20.0) -> bool:
    """Detect monotone speech based on F0 std (in Hz)."""
    return prosody_var < threshold


# Example usage
def is_monotone_speech(audio_file: str) -> None:
    prosody_var = prosody_variation_robust(audio_file, hop_length=512)  # try 1024 for even faster
    monotone = monotone_detected(prosody_var)

    print(f"Prosody Variation (F0 std): {prosody_var:.2f} Hz")
    print(f"Monotone Detected: {monotone}")

    return monotone