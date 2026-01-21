import json

# Check actual results to see if lex and gram are consistent
from pathlib import Path

files = sorted(Path('outputs/band_results').glob('*.json'))

print('SCORING CONSISTENCY CHECK')
print('=' * 120)
print(f'{"File":<20} {"WPM":<8} {"VocabR":<8} {"LexDens":<8} {"MeanUtt":<8} {"MeanConf":<8} {"Fluency":<8} {"Pron":<8} {"Lex":<8} {"Gram":<8} {"Overall":<8}')
print('-' * 120)

for f in files:
    with open(f) as fp:
        data = json.load(fp)
    
    metrics = data['analysis']['metrics_for_scoring']
    cb = data['band_scores']['criterion_bands']
    
    wpm = metrics.get('wpm', 0)
    vocab_r = metrics.get('vocab_richness', 0)
    lex_dens = metrics.get('lexical_density', 0)
    mean_utt = metrics.get('mean_utterance_length', 0)
    mean_conf = metrics.get('mean_word_confidence', 0)
    
    fluency = cb.get('fluency_coherence', 0)
    pron = cb.get('pronunciation', 0)
    lex = cb.get('lexical_resource', 0)
    gram = cb.get('grammatical_range_accuracy', 0)
    overall = data['band_scores']['overall_band']
    
    print(f'{f.name[:17]:<20} {wpm:<8.1f} {vocab_r:<8.3f} {lex_dens:<8.3f} {mean_utt:<8.1f} {mean_conf:<8.3f} {fluency:<8.1f} {pron:<8.1f} {lex:<8.1f} {gram:<8.1f} {overall:<8.1f}')

print('\n' + '=' * 120)
print('OBSERVATIONS:')
print('- Lexical uses vocab_richness and lexical_density + LLM boost (no direct confidence penalty)')
print('- Grammar uses utterance_length and repetition (no confidence factor)')
print('- Pronunciation uses mean_word_confidence (direct correlation)')
print('- Fluency uses WPM and pause metrics (no confidence factor)')
print('\nConsistency question: Should lex/gram also consider audio clarity (confidence)?')
