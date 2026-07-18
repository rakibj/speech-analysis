import pandas as pd
import json
import numpy as np
from scipy.stats import pearsonr, spearmanr
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Load the data
print("=" * 80)
print("FLUENCY ANALYSIS: Correlation Study")
print("=" * 80)

# Load CSV files
disfluency_df = pd.read_csv('research/disfluency_metrics.csv')
human_ratings_df = pd.read_csv('research/human_fluency_ratings_aggregated.csv')

# Merge on sample_id
df = pd.merge(disfluency_df, human_ratings_df[['sample_id', 'mean_fluency']], on='sample_id')

print("\n1. DATA SUMMARY")
print("-" * 80)
print(f"Total samples: {len(df)}")
print(f"\nBasic Statistics:")
print(df[['sample_id', 'wpm', 'duration_weighted_disfluency', 'mean_fluency']].describe())

# Load JSON metrics for each sample
analysis_dir = Path('research/analysis')
json_metrics = {}

for json_file in sorted(analysis_dir.glob('*.json')):
    sample_id = json_file.stem
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            if 'input_metrics' in data:
                metrics = data['input_metrics']
                json_metrics[sample_id] = {
                    'long_pauses_per_min': metrics.get('long_pauses_per_min', 0),
                    'fillers_per_min': metrics.get('fillers_per_min', 0),
                    'pause_variability': metrics.get('pause_variability', 0),
                    'speech_rate_variability': metrics.get('speech_rate_variability', 0)
                }
    except Exception as e:
        print(f"Error loading {sample_id}: {e}")

# Create DataFrame from JSON metrics
json_df = pd.DataFrame.from_dict(json_metrics, orient='index')
json_df['sample_id'] = json_df.index
json_df = json_df.reset_index(drop=True)

# Merge with main dataframe
df = pd.merge(df, json_df, on='sample_id', how='left')

print("\n2. DATA FROM JSON FILES")
print("-" * 80)
print(f"Loaded JSON metrics for {len(json_df)} samples")
print("\nJSON Metrics Summary:")
print(json_df[['long_pauses_per_min', 'fillers_per_min', 'pause_variability']].describe())

# Correlation Analysis
print("\n3. CORRELATION WITH HUMAN FLUENCY RATINGS")
print("=" * 80)

metrics_to_correlate = [
    ('wpm', 'Words Per Minute'),
    ('duration_weighted_disfluency', 'Disfluency Score'),
    ('long_pauses_per_min', 'Long Pauses per Min'),
    ('fillers_per_min', 'Fillers per Min'),
    ('pause_variability', 'Pause Variability'),
    ('speech_rate_variability', 'Speech Rate Variability')
]

correlations = []
for metric, label in metrics_to_correlate:
    try:
        # Remove NaN values
        valid_data = df[[metric, 'mean_fluency']].dropna()

        if len(valid_data) > 2:
            pearson_r, pearson_p = pearsonr(valid_data[metric], valid_data['mean_fluency'])
            spearman_r, spearman_p = spearmanr(valid_data[metric], valid_data['mean_fluency'])

            correlations.append({
                'Metric': label,
                'Pearson r': pearson_r,
                'Pearson p': pearson_p,
                'Spearman r': spearman_r,
                'Spearman p': spearman_p,
                'N': len(valid_data)
            })

            print(f"\n{label}:")
            print(f"  Pearson:  r = {pearson_r:7.4f}, p = {pearson_p:7.4f}")
            print(f"  Spearman: r = {spearman_r:7.4f}, p = {spearman_p:7.4f}")
            print(f"  Samples: {len(valid_data)}")
    except Exception as e:
        print(f"\nError calculating {label}: {e}")

# Create correlation dataframe
corr_df = pd.DataFrame(correlations)
print("\n" + "=" * 80)
print("CORRELATION SUMMARY TABLE")
print("=" * 80)
print(corr_df.to_string(index=False))

# Analyze weight allocation
print("\n\n4. DISFLUENCY COMPONENT ANALYSIS")
print("=" * 80)

# Calculate weighted contributions
# Current formula: 0.55 * pause_score + 0.45 * filler_score
# But first we need to understand the underlying formula

print("\nCurrent Weight Allocation: 55% pause, 45% filler")
print("\nComponent Correlations with Human Rating:")

pause_corr = df[['long_pauses_per_min', 'mean_fluency']].dropna()
if len(pause_corr) > 2:
    pause_r, pause_p = pearsonr(pause_corr['long_pauses_per_min'], pause_corr['mean_fluency'])
    print(f"\nLong Pauses per Min vs Human Rating:")
    print(f"  Pearson r = {pause_r:7.4f}, p = {pause_p:7.4f}")
    print(f"  Correlation strength: {'Significant' if pause_p < 0.05 else 'Not significant'}")

filler_corr = df[['fillers_per_min', 'mean_fluency']].dropna()
if len(filler_corr) > 2:
    filler_r, filler_p = pearsonr(filler_corr['fillers_per_min'], filler_corr['mean_fluency'])
    print(f"\nFillers per Min vs Human Rating:")
    print(f"  Pearson r = {filler_r:7.4f}, p = {filler_p:7.4f}")
    print(f"  Correlation strength: {'Significant' if filler_p < 0.05 else 'Not significant'}")

# Calculate absolute correlations for weighting
if len(pause_corr) > 2 and len(filler_corr) > 2:
    pause_strength = abs(pause_r)
    filler_strength = abs(filler_r)
    total_strength = pause_strength + filler_strength

    optimal_pause_weight = pause_strength / total_strength if total_strength > 0 else 0.5
    optimal_filler_weight = filler_strength / total_strength if total_strength > 0 else 0.5

    print(f"\n\nOptimal Weight Allocation (based on correlation strength):")
    print(f"  Long Pauses: {optimal_pause_weight*100:.1f}% (correlation magnitude: {pause_strength:.4f})")
    print(f"  Fillers: {optimal_filler_weight*100:.1f}% (correlation magnitude: {filler_strength:.4f})")
    print(f"\nCurrent allocation vs Optimal:")
    print(f"  Pauses: Current 55%, Optimal {optimal_pause_weight*100:.1f}%")
    print(f"  Fillers: Current 45%, Optimal {optimal_filler_weight*100:.1f}%")

# Summary
print("\n\n5. KEY FINDINGS")
print("=" * 80)

# Rank correlations
sorted_corr = sorted(correlations, key=lambda x: abs(x['Pearson r']), reverse=True)

print("\nMetrics ranked by correlation strength (Pearson r):")
for i, item in enumerate(sorted_corr, 1):
    r = item['Pearson r']
    p = item['Pearson p']
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
    print(f"{i}. {item['Metric']:30s} r = {r:7.4f} {sig}")

print("\n*** p < 0.001, ** p < 0.01, * p < 0.05")

# Check if pause and filler metrics are individually weak
if len(pause_corr) > 2 and len(filler_corr) > 2:
    print("\n\nIMPORTANT INSIGHT:")
    print("-" * 80)

    if abs(pause_r) < 0.3 and abs(filler_r) < 0.3:
        print("Both pause and filler metrics have WEAK individual correlations.")
        print("This suggests that:")
        print("  1. These features don't drive fluency rating much on their own")
        print("  2. WPM (speech rate) is likely a stronger predictor")
        print("  3. Pauses/fillers matter less than raw speed of delivery")
    else:
        if abs(pause_r) > abs(filler_r):
            print("Pauses have stronger correlation than fillers.")
        else:
            print("Fillers have stronger correlation than pauses.")

# WPM analysis
wpm_data = df[['wpm', 'mean_fluency']].dropna()
if len(wpm_data) > 2:
    wpm_r, wpm_p = pearsonr(wpm_data['wpm'], wpm_data['mean_fluency'])
    print(f"\n\nWPM Correlation: r = {wpm_r:.4f} (strongest predictor)")
    if abs(wpm_r) > 0.6:
        print("WPM shows STRONG correlation with human fluency ratings!")
    elif abs(wpm_r) > 0.4:
        print("WPM shows MODERATE correlation with human fluency ratings.")
    else:
        print("WPM shows WEAK correlation with human fluency ratings.")

print("\n" + "=" * 80)

# Export results
results = {
    'summary_table': corr_df,
    'df': df,
    'pause_r': pause_r if len(pause_corr) > 2 else None,
    'filler_r': filler_r if len(filler_corr) > 2 else None,
    'wpm_r': wpm_r if len(wpm_data) > 2 else None
}

# Save correlations to file for later analysis
corr_df.to_csv('research/correlation_results.csv', index=False)
df.to_csv('research/full_analysis_data.csv', index=False)

print("\nResults saved to:")
print("  - research/correlation_results.csv")
print("  - research/full_analysis_data.csv")
