#!/usr/bin/env python3
"""Check what metrics are actually extracted from ielts5-5.5"""
import json

with open('outputs/audio_analysis/ielts5-5.5.json') as f:
    data = json.load(f)

metrics = data['raw_analysis']

print('METRICS FROM ielts5-5.5:')
print('=' * 70)
print()
print('PRONUNCIATION METRICS:')
print(f'  Mean word confidence: {metrics.get("mean_word_confidence")}')
print(f'  Low confidence ratio: {metrics.get("low_confidence_ratio")}')
print()
print('FLUENCY METRICS:')
print(f'  WPM: {metrics.get("wpm")}')
print(f'  Long pauses/min: {metrics.get("long_pauses_per_min")}')
print(f'  Pause variability: {metrics.get("pause_variability")}')
print(f'  Repetition ratio: {metrics.get("repetition_ratio")}')
print()
print('GRAMMAR/LEXICAL METRICS:')
print(f'  Mean utterance length: {metrics.get("mean_utterance_length")}')
print(f'  Vocab richness: {metrics.get("vocab_richness")}')
print(f'  Lexical density: {metrics.get("lexical_density")}')
print()
print('RAW TRANSCRIPT (first 400 chars):')
transcript = data['raw_analysis'].get('raw_transcript', '')
print(f'  "{transcript[:400]}..."')
print()
print('STATISTICS:')
stats = metrics.get('statistics', {})
print(f'  Total words: {stats.get("total_words_transcribed")}')
print(f'  Content words: {stats.get("content_words")}')
print(f'  Filler words: {stats.get("filler_words_detected")}')
print(f'  Filler %: {stats.get("filler_percentage")}')
