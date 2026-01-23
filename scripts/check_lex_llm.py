import json
from pathlib import Path

# Check LLM metrics for ielts8-8.5 and ielts5.5
for fname in ['ielts5.5.json', 'ielts8-8.5.json']:
    with open(f'outputs/band_results/{fname}') as f:
        data = json.load(f)
    
    analysis = data['analysis']
    metrics = analysis['metrics_for_scoring']
    print(f'\n{fname}:')
    print(f'  VocabRich: {metrics.get("vocab_richness", 0):.3f}')
    print(f'  LexDens: {metrics.get("lexical_density", 0):.3f}')
    
    # Check lexical analysis
    lex_analysis = analysis.get('lexical_resource', {})
    print(f'  Lexical analysis keys: {list(lex_analysis.keys())}')
    if lex_analysis:
        print(f'  Lexical analysis: {json.dumps(lex_analysis, indent=4)[:300]}...')
