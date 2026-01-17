import json
from pathlib import Path

output_dir = Path('outputs/band_results')

# Show detailed output for multiple samples
samples = ['ielts5.5.json', 'ielts7.json', 'ielts8-8.5.json', 'ielts9.json']

for file_name in samples:
    file_path = output_dir / file_name
    if file_path.exists():
        with open(file_path) as f:
            data = json.load(f)
        
        expected = file_name.replace('.json', '')
        bs = data['band_scores']
        
        print(f'\n' + '='*70)
        print(f'IELTS {expected.upper()}')
        print('='*70)
        print(f'OVERALL BAND: {bs["overall_band"]}')
        print(f'\nCriterion Bands:')
        for crit, band in bs['criterion_bands'].items():
            print(f'  {crit:30s}: {band}')
        print(f'\nFeedback:')
        for crit, comment in bs['feedback'].items():
            if crit != 'overall_recommendation':
                print(f'  {crit:30s}: {comment}')
        print(f'\nRecommendation:')
        print(f'  {bs["feedback"]["overall_recommendation"]}')
