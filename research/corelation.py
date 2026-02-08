import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from pathlib import Path

# -------------------------------
# LOAD DATA
# -------------------------------
script_dir = Path(__file__).parent
root_dir = script_dir.parent

# Load human ratings
human_file = script_dir / "human_fluency_ratings_aggregated.csv"
if not human_file.exists():
    print(f"Warning: Human ratings file not found at {human_file}")
    print("Please provide: human_fluency_ratings_aggregated.csv in research folder")
    exit(1)

human = pd.read_csv(human_file)

# Load auto-generated scores from the latest CSV
results_dir = script_dir / "results"
csv_files = sorted(results_dir.glob("batch_scoring_*.csv"))
if not csv_files:
    print(f"Error: No scoring CSV files found in {results_dir}")
    exit(1)

auto_file = csv_files[-1]  # Get the latest file
print(f"Loading auto scores from: {auto_file.name}")
auto = pd.read_csv(auto_file)

# Remove summary rows from auto
auto = auto[auto['File'] != 'SUMMARY'].copy()
auto = auto[auto['File'].notna()].copy()
# Keep only rows that start with 'S' (valid sample IDs)
auto = auto[auto['File'].str.startswith('S', na=False)].copy()

# Convert File column (S01, S02, etc.) to numeric sample_id for matching
auto['sample_id'] = auto['File'].str.replace('S', '').astype(int)

print(f"Auto CSV columns: {list(auto.columns)}")
print(f"Human CSV columns: {list(human.columns)}")


# -------------------------------
# STANDARDIZE COLUMN NAMES
# (adjust if needed)
# -------------------------------
human = human.rename(columns={
    "mean_fluency": "human_fluency"
})

# Our auto CSV has Score (0-100) and Band (1-9) columns
# We'll use Score (0-100) for comparison
auto = auto.rename(columns={
    "Score (0-100)": "auto_fluency_score",
    "Band (1-9)": "auto_fluency_band"
})

# Ensure both sample_id columns are the same type (int)
human['sample_id'] = human['sample_id'].str.replace('S', '').astype(int)
auto['sample_id'] = auto['sample_id'].astype(int)

# -------------------------------
# MERGE
# -------------------------------
# Merge on sample_id
df = pd.merge(
    human[["sample_id", "human_fluency"]],
    auto[["sample_id", "auto_fluency_score", "auto_fluency_band"]],
    on="sample_id",
    how="inner"
)

print(f"\nMerged data shape: {df.shape}")
print(f"Merged columns: {list(df.columns)}")

# sanity checks
if df.shape[0] == 0:
    print("Error: No matching records found after merge")
    print(f"Human IDs: {[int(x) for x in human['sample_id'].tolist()][:10]}")
    print(f"Auto IDs: {[int(x) for x in auto['sample_id'].tolist()][:10]}")
    exit(1)

assert df.isnull().sum().sum() == 0, "Missing values detected"
print(f"Successfully merged {df.shape[0]} records")

# -------------------------------
# SPEARMAN CORRELATIONS
# -------------------------------
rho_auto, p_auto = spearmanr(
    df["auto_fluency_score"],
    df["human_fluency"]
)

rho_band, p_band = spearmanr(
    df["auto_fluency_band"],
    df["human_fluency"]
)

print("\nSpearman correlations:")
print(f"Auto fluency score (0-100) vs human:  r = {rho_auto:.3f}, p = {p_auto:.4g}")
print(f"Auto fluency band (1-9) vs human:     r = {rho_band:.3f}, p = {p_band:.4g}")

# -------------------------------
# BOOTSTRAP DIFFERENCE IN CORRELATIONS
# -------------------------------
rng = np.random.default_rng(42)
n_boot = 5000
diffs = []

for _ in range(n_boot):
    sample = df.sample(frac=1, replace=True, random_state=rng)
    r_score, _ = spearmanr(sample["auto_fluency_score"], sample["human_fluency"])
    r_band, _ = spearmanr(sample["auto_fluency_band"], sample["human_fluency"])
    diffs.append(r_score - r_band)

diffs = np.array(diffs)
ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])

print("\nDifference in correlation (score - band):")
print(f"Mean diff = {diffs.mean():.3f}")
print(f"95% CI = [{ci_low:.3f}, {ci_high:.3f}]")
