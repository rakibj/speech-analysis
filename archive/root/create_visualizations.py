import pandas as pd
import numpy as np
import json
from pathlib import Path
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

# Load data
df = pd.read_csv('research/full_analysis_data.csv')
corr_df = pd.read_csv('research/correlation_results.csv')

# Create comprehensive visualization
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Fluency Metrics vs Human Rating Correlation Analysis', fontsize=16, fontweight='bold')

# 1. WPM vs Human Rating
ax = axes[0, 0]
valid = df[['wpm', 'mean_fluency']].dropna()
wpm_r, _ = pearsonr(valid['wpm'], valid['mean_fluency'])
ax.scatter(valid['wpm'], valid['mean_fluency'], alpha=0.6, s=100)
z = np.polyfit(valid['wpm'], valid['mean_fluency'], 1)
p = np.poly1d(z)
ax.plot(valid['wpm'].sort_values(), p(valid['wpm'].sort_values()), "r--", alpha=0.8, linewidth=2)
ax.set_xlabel('Words Per Minute', fontsize=11)
ax.set_ylabel('Human Fluency Rating', fontsize=11)
ax.set_title(f'WPM vs Human Rating\nr={wpm_r:.4f} (STRONG ***)', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.3)

# 2. Disfluency Score vs Human Rating
ax = axes[0, 1]
valid = df[['duration_weighted_disfluency', 'mean_fluency']].dropna()
dis_r, _ = pearsonr(valid['duration_weighted_disfluency'], valid['mean_fluency'])
ax.scatter(valid['duration_weighted_disfluency'], valid['mean_fluency'], alpha=0.6, s=100, color='orange')
z = np.polyfit(valid['duration_weighted_disfluency'], valid['mean_fluency'], 1)
p = np.poly1d(z)
ax.plot(valid['duration_weighted_disfluency'].sort_values(), p(valid['duration_weighted_disfluency'].sort_values()), "r--", alpha=0.8, linewidth=2)
ax.set_xlabel('Disfluency Score', fontsize=11)
ax.set_ylabel('Human Fluency Rating', fontsize=11)
ax.set_title(f'Disfluency Score vs Human Rating\nr={dis_r:.4f} (MODERATE *)', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.3)

# 3. Long Pauses per Min
ax = axes[0, 2]
valid = df[['long_pauses_per_min', 'mean_fluency']].dropna()
pause_r, _ = pearsonr(valid['long_pauses_per_min'], valid['mean_fluency'])
ax.scatter(valid['long_pauses_per_min'], valid['mean_fluency'], alpha=0.6, s=100, color='red')
z = np.polyfit(valid['long_pauses_per_min'], valid['mean_fluency'], 1)
p = np.poly1d(z)
ax.plot(valid['long_pauses_per_min'].sort_values(), p(valid['long_pauses_per_min'].sort_values()), "r--", alpha=0.8, linewidth=2)
ax.set_xlabel('Long Pauses per Min', fontsize=11)
ax.set_ylabel('Human Fluency Rating', fontsize=11)
ax.set_title(f'Long Pauses vs Human Rating\nr={pause_r:.4f} (WEAK)', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.3)

# 4. Fillers per Min
ax = axes[1, 0]
valid = df[['fillers_per_min', 'mean_fluency']].dropna()
filler_r, _ = pearsonr(valid['fillers_per_min'], valid['mean_fluency'])
ax.scatter(valid['fillers_per_min'], valid['mean_fluency'], alpha=0.6, s=100, color='green')
z = np.polyfit(valid['fillers_per_min'], valid['mean_fluency'], 1)
p = np.poly1d(z)
ax.plot(valid['fillers_per_min'].sort_values(), p(valid['fillers_per_min'].sort_values()), "r--", alpha=0.8, linewidth=2)
ax.set_xlabel('Fillers per Min', fontsize=11)
ax.set_ylabel('Human Fluency Rating', fontsize=11)
ax.set_title(f'Fillers vs Human Rating\nr={filler_r:.4f} (VERY WEAK)', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.3)

# 5. Pause Variability
ax = axes[1, 1]
valid = df[['pause_variability', 'mean_fluency']].dropna()
pvar_r, _ = pearsonr(valid['pause_variability'], valid['mean_fluency'])
ax.scatter(valid['pause_variability'], valid['mean_fluency'], alpha=0.6, s=100, color='purple')
z = np.polyfit(valid['pause_variability'], valid['mean_fluency'], 1)
p = np.poly1d(z)
ax.plot(valid['pause_variability'].sort_values(), p(valid['pause_variability'].sort_values()), "r--", alpha=0.8, linewidth=2)
ax.set_xlabel('Pause Variability', fontsize=11)
ax.set_ylabel('Human Fluency Rating', fontsize=11)
ax.set_title(f'Pause Variability vs Human Rating\nr={pvar_r:.4f} (WEAK)', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.3)

# 6. Speech Rate Variability
ax = axes[1, 2]
valid = df[['speech_rate_variability', 'mean_fluency']].dropna()
svar_r, _ = pearsonr(valid['speech_rate_variability'], valid['mean_fluency'])
ax.scatter(valid['speech_rate_variability'], valid['mean_fluency'], alpha=0.6, s=100, color='brown')
z = np.polyfit(valid['speech_rate_variability'], valid['mean_fluency'], 1)
p = np.poly1d(z)
ax.plot(valid['speech_rate_variability'].sort_values(), p(valid['speech_rate_variability'].sort_values()), "r--", alpha=0.8, linewidth=2)
ax.set_xlabel('Speech Rate Variability', fontsize=11)
ax.set_ylabel('Human Fluency Rating', fontsize=11)
ax.set_title(f'Speech Rate Variability vs Human Rating\nr={svar_r:.4f} (MODERATE *)', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('research/correlation_scatter_plots.png', dpi=150, bbox_inches='tight')
print("Saved: research/correlation_scatter_plots.png")

# Create correlation bar chart
fig, ax = plt.subplots(figsize=(12, 6))

metrics = ['WPM', 'Speech Rate\nVariability', 'Disfluency\nScore', 'Pause\nVariability', 'Long Pauses\nper Min', 'Fillers\nper Min']
correlations = [0.7906, -0.4580, 0.4362, -0.2990, -0.2750, -0.0875]
colors = ['green' if r > 0.6 else 'orange' if r > 0.3 else 'red' if r < -0.3 else 'lightcoral' for r in correlations]

bars = ax.barh(metrics, correlations, color=colors, alpha=0.7, edgecolor='black')

# Add value labels
for i, (bar, val) in enumerate(zip(bars, correlations)):
    ax.text(val + 0.02 if val > 0 else val - 0.02, i, f'{val:.4f}', va='center', ha='left' if val > 0 else 'right', fontweight='bold')

ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
ax.set_xlabel('Correlation Coefficient (Pearson r)', fontsize=12, fontweight='bold')
ax.set_title('Correlation of Metrics with Human Fluency Rating\n(Ranked by Strength)', fontsize=14, fontweight='bold')
ax.set_xlim(-1, 1)
ax.grid(True, alpha=0.3, axis='x')

# Add significance markers
significance = ['***', '**', '*', '', '', '']
for i, sig in enumerate(significance):
    if sig:
        ax.text(0.95, i, sig, va='center', ha='center', fontsize=14, color='darkgreen', fontweight='bold')

plt.tight_layout()
plt.savefig('research/correlation_bar_chart.png', dpi=150, bbox_inches='tight')
print("Saved: research/correlation_bar_chart.png")

# Create weight analysis visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Current weights
current_weights = [55, 45]
labels_current = ['Long Pauses\n(55%)', 'Fillers\n(45%)']
colors_current = ['#ff9999', '#66b3ff']

wedges, texts, autotexts = ax1.pie(current_weights, labels=labels_current, autopct='%1.1f%%',
                                     colors=colors_current, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
ax1.set_title('CURRENT Disfluency Weighting\n(Arbitrary)', fontsize=12, fontweight='bold')

# Optimal weights based on correlation
optimal_weights = [75.9, 24.1]
labels_optimal = ['Long Pauses\n(75.9%)', 'Fillers\n(24.1%)']
colors_optimal = ['#ff6666', '#99ccff']

wedges, texts, autotexts = ax2.pie(optimal_weights, labels=labels_optimal, autopct='%1.1f%%',
                                     colors=colors_optimal, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
ax2.set_title('OPTIMIZED Disfluency Weighting\n(Based on Correlation Magnitude)', fontsize=12, fontweight='bold')

fig.suptitle('Weight Allocation Analysis: Current vs Optimal', fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig('research/weight_allocation.png', dpi=150, bbox_inches='tight')
print("Saved: research/weight_allocation.png")

print("\nAll visualizations saved successfully!")
