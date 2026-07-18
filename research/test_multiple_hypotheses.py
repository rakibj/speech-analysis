#!/usr/bin/env python3
"""
HYPOTHESIS EXPLORATION: Test Multiple Metric Combinations

Tests various combinations and weight allocations to find the best
predictors of human fluency judgments.

Hypotheses tested:
1. WPM alone (baseline)
2. Composite fluency alone
3. Disfluency alone
4. Various weighted combinations of WPM + Composite (90/10, 80/20, 70/30, 60/40, 50/50)
5. WPM + Disfluency combinations
6. Custom "fluency control" metric (WPM + Stability indicator)
"""

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from pathlib import Path
import json


def main():
    script_dir = Path(__file__).parent

    # =====================================================================
    # LOAD DATA
    # =====================================================================

    print("=" * 80)
    print("HYPOTHESIS EXPLORATION: Testing Multiple Metric Combinations")
    print("=" * 80)

    # Load human ratings
    human_file = script_dir / "human_fluency_ratings_aggregated.csv"
    if not human_file.exists():
        print(f"ERROR: Human ratings not found: {human_file}")
        return 1

    human = pd.read_csv(human_file)
    human["sample_id"] = human["sample_id"].str.replace("S", "").astype(int)
    print(f"\nLoaded human ratings: {len(human)} samples")

    # Load disfluency metrics
    disfluency_file = script_dir / "disfluency_metrics.csv"
    if not disfluency_file.exists():
        print(f"ERROR: Disfluency metrics not found: {disfluency_file}")
        return 1

    metrics = pd.read_csv(disfluency_file)
    metrics["sample_id"] = metrics["sample_id"].str.replace("S", "").astype(int)
    print(f"Loaded disfluency metrics: {len(metrics)} samples")

    # Load composite fluency scores
    results_dir = script_dir / "results"
    csv_files = sorted(results_dir.glob("batch_scoring_*.csv"))
    if not csv_files:
        print(f"ERROR: No batch scoring results found in {results_dir}")
        return 1

    fluency_file = csv_files[-1]
    fluency_scores = pd.read_csv(fluency_file)
    fluency_scores = fluency_scores[fluency_scores['File'] != 'SUMMARY'].copy()
    fluency_scores = fluency_scores[fluency_scores['File'].notna()].copy()
    fluency_scores = fluency_scores[fluency_scores['File'].str.startswith('S', na=False)].copy()
    fluency_scores['sample_id'] = fluency_scores['File'].str.replace('S', '').astype(int)
    fluency_scores = fluency_scores.rename(columns={'Score (0-100)': 'composite_fluency_score'})
    print(f"Loaded composite fluency scores: {len(fluency_scores)} samples")

    # Merge data
    df = pd.merge(
        human[["sample_id", "mean_fluency"]],
        metrics[["sample_id", "wpm", "duration_weighted_disfluency"]],
        on="sample_id",
        how="inner"
    )

    df = pd.merge(
        df,
        fluency_scores[["sample_id", "composite_fluency_score"]],
        on="sample_id",
        how="left"
    )

    print(f"Merged data: {len(df)} samples\n")

    # Normalize metrics to 0-1 scale
    df["composite_norm"] = df["composite_fluency_score"] / 100.0
    wpm_min, wpm_max = df["wpm"].min(), df["wpm"].max()
    df["wpm_norm"] = (df["wpm"] - wpm_min) / (wpm_max - wpm_min)
    # Disfluency is already 0-1, but invert it (higher is better for fluency)
    df["disfluency_fluency"] = 1.0 - df["duration_weighted_disfluency"]

    # =====================================================================
    # BUILD HYPOTHESES / METRIC COMBINATIONS
    # =====================================================================

    hypotheses = {}

    # Baseline metrics
    hypotheses["WPM Baseline"] = df["wpm"]
    hypotheses["Composite Fluency (0-100)"] = df["composite_fluency_score"]
    hypotheses["Pure Disfluency"] = df["duration_weighted_disfluency"]
    hypotheses["Disfluency as Fluency"] = df["disfluency_fluency"]

    # WPM + Composite combinations
    for wpm_weight in [50, 60, 70, 80, 90]:
        comp_weight = 100 - wpm_weight
        name = f"WPM {wpm_weight}% + Composite {comp_weight}%"
        hypotheses[name] = (
            (wpm_weight / 100.0) * df["wpm_norm"] +
            (comp_weight / 100.0) * df["composite_norm"]
        )

    # WPM + Disfluency combinations
    for wpm_weight in [70, 75, 80, 85, 90]:
        dis_weight = 100 - wpm_weight
        name = f"WPM {wpm_weight}% + Disfluency-Fluency {dis_weight}%"
        hypotheses[name] = (
            (wpm_weight / 100.0) * df["wpm_norm"] +
            (dis_weight / 100.0) * df["disfluency_fluency"]
        )

    # Maybe a multiplicative approach
    hypotheses["WPM * Composite"] = df["wpm_norm"] * df["composite_norm"]
    hypotheses["WPM * Disfluency-Fluency"] = df["wpm_norm"] * df["disfluency_fluency"]

    # =====================================================================
    # TEST ALL HYPOTHESES
    # =====================================================================

    results = []

    print("=" * 80)
    print("CORRELATION RESULTS")
    print("=" * 80)
    print(f"\n{'Hypothesis':<50} {'r':>8} {'r²':>8} {'p-value':>12}")
    print("-" * 80)

    for hypothesis_name, metric_values in hypotheses.items():
        # Skip if all NaN
        if metric_values.isna().all():
            continue

        rho, p_value = spearmanr(metric_values, df["mean_fluency"])
        r_squared = rho ** 2

        results.append({
            "hypothesis": hypothesis_name,
            "r": rho,
            "r_squared": r_squared,
            "p_value": p_value,
            "percent_variance": r_squared * 100
        })

        sig = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
        print(f"{hypothesis_name:<50} {rho:>8.4f} {r_squared:>8.1%} {p_value:>12.4g} {sig}")

    # =====================================================================
    # RANK BY PERFORMANCE
    # =====================================================================

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("r", ascending=False)

    print("\n" + "=" * 80)
    print("RANKED BY CORRELATION (BEST TO WORST)")
    print("=" * 80)
    print(f"\n{'Rank':<6} {'Hypothesis':<50} {'r':>8} {'Variance':>10}")
    print("-" * 80)

    for idx, (_, row) in enumerate(results_df.iterrows(), 1):
        print(f"{idx:<6} {row['hypothesis']:<50} {row['r']:>8.4f} {row['percent_variance']:>9.1f}%")

    # =====================================================================
    # TOP 5 ANALYSIS
    # =====================================================================

    print("\n" + "=" * 80)
    print("TOP 5 WINNERS: Detailed Analysis")
    print("=" * 80)

    top_5 = results_df.head(5)

    for idx, (_, row) in enumerate(top_5.iterrows(), 1):
        print(f"\n{idx}. {row['hypothesis']}")
        print(f"   Correlation:        r = {row['r']:.4f}")
        print(f"   Variance Explained:  {row['percent_variance']:.1f}%")
        print(f"   P-value:             {row['p_value']:.4g}")
        print(f"   Significance:        {'***' if row['p_value'] < 0.001 else '**' if row['p_value'] < 0.01 else '*' if row['p_value'] < 0.05 else 'ns'}")

    # =====================================================================
    # STATISTICAL COMPARISON OF TOP 3
    # =====================================================================

    if len(top_5) >= 3:
        print("\n" + "=" * 80)
        print("BOOTSTRAP CONFIDENCE INTERVALS: Top 3 vs Each Other")
        print("=" * 80)

        rng = np.random.default_rng(42)
        n_boot = 5000

        top_3_names = top_5.head(3)["hypothesis"].values
        top_3_metrics = [hypotheses[name] for name in top_3_names]

        # Compare 1 vs 2
        if len(top_3_names) >= 2:
            print(f"\nComparison: {top_3_names[0]} vs {top_3_names[1]}")
            differences = []
            for _ in range(n_boot):
                sample_idx = rng.choice(len(df), len(df), replace=True)
                r1, _ = spearmanr(top_3_metrics[0].iloc[sample_idx], df["mean_fluency"].iloc[sample_idx])
                r2, _ = spearmanr(top_3_metrics[1].iloc[sample_idx], df["mean_fluency"].iloc[sample_idx])
                differences.append(r1 - r2)

            differences = np.array(differences)
            ci_low, ci_high = np.percentile(differences, [2.5, 97.5])
            print(f"  Difference: {differences.mean():.4f}")
            print(f"  95% CI: [{ci_low:.4f}, {ci_high:.4f}]")
            if ci_low > 0:
                print(f"  >> {top_3_names[0]} SIGNIFICANTLY BETTER")
            elif ci_high < 0:
                print(f"  >> {top_3_names[1]} SIGNIFICANTLY BETTER")
            else:
                print(f"  >> No significant difference")

        # Compare 1 vs 3
        if len(top_3_names) >= 3:
            print(f"\nComparison: {top_3_names[0]} vs {top_3_names[2]}")
            differences = []
            for _ in range(n_boot):
                sample_idx = rng.choice(len(df), len(df), replace=True)
                r1, _ = spearmanr(top_3_metrics[0].iloc[sample_idx], df["mean_fluency"].iloc[sample_idx])
                r3, _ = spearmanr(top_3_metrics[2].iloc[sample_idx], df["mean_fluency"].iloc[sample_idx])
                differences.append(r1 - r3)

            differences = np.array(differences)
            ci_low, ci_high = np.percentile(differences, [2.5, 97.5])
            print(f"  Difference: {differences.mean():.4f}")
            print(f"  95% CI: [{ci_low:.4f}, {ci_high:.4f}]")
            if ci_low > 0:
                print(f"  >> {top_3_names[0]} SIGNIFICANTLY BETTER")
            elif ci_high < 0:
                print(f"  >> {top_3_names[2]} SIGNIFICANTLY BETTER")
            else:
                print(f"  >> No significant difference")

    # =====================================================================
    # WRITE RESULTS TO FILE
    # =====================================================================

    results_file = script_dir / "HYPOTHESIS_EXPLORATION_RESULTS.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "all_results": results_df.to_dict(orient="records"),
                "top_5": top_5.to_dict(orient="records"),
                "winner": top_5.iloc[0].to_dict() if len(top_5) > 0 else None
            },
            f,
            indent=2
        )

    print(f"\n\nDetailed results saved to: {results_file}")

    return 0


if __name__ == "__main__":
    exit(main())
