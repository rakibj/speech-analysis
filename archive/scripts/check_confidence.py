import json
from pathlib import Path

# Check a recently generated audio analysis file
with open('outputs/audio_analysis/ielts5.5.json') as f:
    data = json.load(f)

words = data['raw_analysis']['timestamps']['words_timestamps_raw']
print(f'Total words: {len(words)}')

# Check confidence values
confs = [w['confidence'] for w in words]
unique_confs = sorted(set(confs))
print(f'Unique confidence values: {unique_confs[:20]}')
print(f'Min: {min(confs):.4f}, Max: {max(confs):.4f}, Mean: {sum(confs)/len(confs):.4f}')

# Show first 5 words
print(f'\nFirst 5 words:')
for w in words[:5]:
    print(f'  {w["word"]:15} conf={w["confidence"]:.4f}')

# Check the mean_word_confidence in metrics
print(f'\nMetrics:')
print(f'  mean_word_confidence: {data["raw_analysis"].get("mean_word_confidence", "N/A")}')
print(f'  low_confidence_ratio: {data["raw_analysis"].get("low_confidence_ratio", "N/A")}')
