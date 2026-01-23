#!/usr/bin/env python
import sys
from pathlib import Path
sys.path.insert(0, '.')

from src.audio.processing import transcribe_verbatim_fillers, align_words_whisperx, load_audio

# Test on one file
audio_path = Path('data/ielts_part_2/ielts5.5.wav')
print(f'Testing with: {audio_path}')

# Transcribe
result = transcribe_verbatim_fillers(str(audio_path), device='cpu')
segs = result.get('segments', [])
print(f'Segments: {len(segs)}')

# Check if segments have 'words' key
if segs:
    seg0 = segs[0]
    print(f'Segment 0 keys: {list(seg0.keys())}')
    print(f'Has words: {"words" in seg0}')
    if 'words' in seg0 and len(seg0['words']) > 0:
        w0 = seg0['words'][0]
        print(f'Word 0 keys: {list(w0.keys())}')
        print(f'Word 0: {w0}')

# Align
audio, _ = load_audio(audio_path)
df_aligned = align_words_whisperx(result['segments'], audio, device='cpu')
print(f'\nAligned words: {len(df_aligned)}')
print(f'Columns: {list(df_aligned.columns)}')
if 'confidence' in df_aligned.columns:
    print(f'Confidence mean: {df_aligned["confidence"].mean():.4f}')
    print(f'Confidence min: {df_aligned["confidence"].min():.4f}')
    print(f'Confidence max: {df_aligned["confidence"].max():.4f}')
    print(f'Confidence unique values: {sorted(df_aligned["confidence"].unique())}')
    print(f'\nFirst 3 rows:')
    print(df_aligned.head(3))
