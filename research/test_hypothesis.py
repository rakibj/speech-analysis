#!/usr/bin/env python3
"""
PREREGISTERED HYPOTHESIS TEST + FLUENCY ENGINE COMPARISON

Hypothesis:
  Duration-weighted disfluency (pause structure + filler dependency)
  correlates MORE STRONGLY with human fluency judgments
  than baseline WPM alone.

Extended Analysis:
  Also includes composite fluency score from the fluency engine
  to compare three approaches:
  1. Pure duration-weighted disfluency metric
  2. WPM baseline
  3. Composite fluency score (all 5 dimensions)

Method:
  1. Load human fluency ratings (1-9 scale)
  2. Load duration-weighted disfluency metric (from compute_disfluency_metric.py)
  3. Load composite fluency scores (from batch_scorer.py results)
  4. Compute Spearman correlations for all three metrics
  5. Test with bootstrap 95% CI for pairwise comparisons
  6. Report results with full statistical details
"""

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from pathlib import Path


def main():
    script_dir = Path(__file__).parent

    # =====================================================================
    # LOAD DATA
    # =====================================================================

    print("=" * 70)
    print("PREREGISTERED HYPOTHESIS TEST + FLUENCY ENGINE COMPARISON")
    print("=" * 70)

    # Load human ratings
    human_file = script_dir / "human_fluency_ratings_aggregated.csv"
    if not human_file.exists():
        print(f"ERROR: Human ratings not found: {human_file}")
        return 1

    human = pd.read_csv(human_file)
    human["sample_id"] = human["sample_id"].str.replace("S", "").astype(int)
    print(f"\n1. Loaded human ratings: {len(human)} samples")

    # Load disfluency metrics
    disfluency_file = script_dir / "disfluency_metrics.csv"
    if not disfluency_file.exists():
        print(f"ERROR: Disfluency metrics not found: {disfluency_file}")
        print("   Run: python compute_disfluency_metric.py")
        return 1

    metrics = pd.read_csv(disfluency_file)
    metrics["sample_id"] = metrics["sample_id"].str.replace("S", "").astype(int)
    print(f"2. Loaded disfluency metrics: {len(metrics)} samples")

    # Load composite fluency scores from batch scoring results
    results_dir = script_dir / "results"
    csv_files = sorted(results_dir.glob("batch_scoring_*.csv"))
    if not csv_files:
        print(f"WARNING: No batch scoring results found in {results_dir}")
        print("   Run: python batch_scorer.py")
        fluency_scores = None
    else:
        fluency_file = csv_files[-1]  # Get the latest file
        fluency_scores = pd.read_csv(fluency_file)
        # Clean up the data
        fluency_scores = fluency_scores[fluency_scores['File'] != 'SUMMARY'].copy()
        fluency_scores = fluency_scores[fluency_scores['File'].notna()].copy()
        fluency_scores = fluency_scores[fluency_scores['File'].str.startswith('S', na=False)].copy()
        fluency_scores['sample_id'] = fluency_scores['File'].str.replace('S', '').astype(int)
        # Rename score column for clarity
        fluency_scores = fluency_scores.rename(columns={'Score (0-100)': 'composite_fluency_score'})
        print(f"3. Loaded composite fluency scores: {len(fluency_scores)} samples from {fluency_file.name}")

    # =====================================================================
    # MERGE DATA
    # =====================================================================

    df = pd.merge(
        human[["sample_id", "mean_fluency"]],
        metrics[["sample_id", "wpm", "duration_weighted_disfluency"]],
        on="sample_id",
        how="inner"
    )

    # Add composite fluency scores if available
    if fluency_scores is not None:
        df = pd.merge(
            df,
            fluency_scores[["sample_id", "composite_fluency_score"]],
            on="sample_id",
            how="left"
        )
        # Normalize composite score to 0-1 scale for fair comparison
        df["composite_fluency_normalized"] = df["composite_fluency_score"] / 100.0

        # Create combined metric: 80% WPM + 20% Composite Fluency (both normalized)
        # Normalize WPM to 0-1 scale (using observed range for this sample)
        wpm_min = df["wpm"].min()
        wpm_max = df["wpm"].max()
        df["wpm_normalized"] = (df["wpm"] - wpm_min) / (wpm_max - wpm_min)

        # Combine: 80% WPM + 20% Composite
        df["combined_wpm_composite"] = (
            0.80 * df["wpm_normalized"] +
            0.20 * df["composite_fluency_normalized"]
        )

    if len(df) != 29:
        print(f"WARNING: Only {len(df)} samples merged (expected 29)")

    print(f"4. Merged data: {len(df)} samples\n")

    # =====================================================================
    # COMPUTE CORRELATIONS
    # =====================================================================

    print("=" * 70)
    print("MAIN RESULTS: Spearman Rank Correlations with Human Ratings")
    print("=" * 70)

    # Duration-weighted disfluency
    rho_disfluency, p_disfluency = spearmanr(
        df["duration_weighted_disfluency"],
        df["mean_fluency"]
    )

    # WPM baseline
    rho_wpm, p_wpm = spearmanr(
        df["wpm"],
        df["mean_fluency"]
    )

    # Composite fluency score (if available)
    rho_composite = None
    p_composite = None
    if "composite_fluency_normalized" in df.columns and df["composite_fluency_normalized"].notna().all():
        rho_composite, p_composite = spearmanr(
            df["composite_fluency_normalized"],
            df["mean_fluency"]
        )

    # Combined WPM + Composite metric (if available)
    rho_combined = None
    p_combined = None
    if "combined_wpm_composite" in df.columns and df["combined_wpm_composite"].notna().all():
        rho_combined, p_combined = spearmanr(
            df["combined_wpm_composite"],
            df["mean_fluency"]
        )

    print(f"\n1. Duration-Weighted Disfluency vs Human Ratings:")
    print(f"   Correlation (r):  {rho_disfluency:.4f}")
    print(f"   P-value:          {p_disfluency:.4g}")
    print(f"   Significance:     {'***' if p_disfluency < 0.001 else '**' if p_disfluency < 0.01 else '*' if p_disfluency < 0.05 else 'ns'}")
    print(f"   Variance (r²):    {rho_disfluency**2:.3f} ({rho_disfluency**2*100:.1f}%)")

    print(f"\n2. WPM Baseline vs Human Ratings:")
    print(f"   Correlation (r):  {rho_wpm:.4f}")
    print(f"   P-value:          {p_wpm:.4g}")
    print(f"   Significance:     {'***' if p_wpm < 0.001 else '**' if p_wpm < 0.01 else '*' if p_wpm < 0.05 else 'ns'}")
    print(f"   Variance (r²):    {rho_wpm**2:.3f} ({rho_wpm**2*100:.1f}%)")

    if rho_composite is not None:
        print(f"\n3. Composite Fluency Score vs Human Ratings:")
        print(f"   Correlation (r):  {rho_composite:.4f}")
        print(f"   P-value:          {p_composite:.4g}")
        print(f"   Significance:     {'***' if p_composite < 0.001 else '**' if p_composite < 0.01 else '*' if p_composite < 0.05 else 'ns'}")
        print(f"   Variance (r²):    {rho_composite**2:.3f} ({rho_composite**2*100:.1f}%)")
    else:
        print(f"\n3. Composite Fluency Score: NOT AVAILABLE (no batch scoring results)")
        rho_composite = None

    if rho_combined is not None:
        print(f"\n4. Combined Metric (80% WPM + 20% Composite) vs Human Ratings:")
        print(f"   Correlation (r):  {rho_combined:.4f}")
        print(f"   P-value:          {p_combined:.4g}")
        print(f"   Significance:     {'***' if p_combined < 0.001 else '**' if p_combined < 0.01 else '*' if p_combined < 0.05 else 'ns'}")
        print(f"   Variance (r²):    {rho_combined**2:.3f} ({rho_combined**2*100:.1f}%)")
    else:
        print(f"\n4. Combined Metric: NOT AVAILABLE")

    # =====================================================================
    # HYPOTHESIS TEST: Pairwise Comparisons
    # =====================================================================

    print(f"\n" + "=" * 70)
    print("HYPOTHESIS TESTS: Pairwise Comparisons")
    print("=" * 70)

    rng = np.random.default_rng(42)
    n_boot = 5000

    # TEST 1: Disfluency vs WPM (Primary hypothesis)
    print(f"\nTEST 1: Disfluency vs WPM")
    print("-" * 70)

    diff_dis_wpm = rho_disfluency - rho_wpm
    percent_improvement = (diff_dis_wpm / abs(rho_wpm)) * 100 if rho_wpm != 0 else 0

    print(f"Raw difference (disfluency - wpm):")
    print(f"  {rho_disfluency:.4f} - {rho_wpm:.4f} = {diff_dis_wpm:.4f}")
    print(f"  Percent change: {percent_improvement:+.1f}%")

    differences_dis_wpm = []
    for _ in range(n_boot):
        sample_df = df.sample(frac=1, replace=True, random_state=rng)
        r_dis, _ = spearmanr(sample_df["duration_weighted_disfluency"], sample_df["mean_fluency"])
        r_wpm_boot, _ = spearmanr(sample_df["wpm"], sample_df["mean_fluency"])
        differences_dis_wpm.append(r_dis - r_wpm_boot)

    differences_dis_wpm = np.array(differences_dis_wpm)
    ci_low_dw, ci_high_dw = np.percentile(differences_dis_wpm, [2.5, 97.5])

    print(f"Bootstrap 95% CI for difference (n={n_boot} resamples):")
    print(f"  Mean difference:  {differences_dis_wpm.mean():.4f}")
    print(f"  95% CI:           [{ci_low_dw:.4f}, {ci_high_dw:.4f}]")

    if ci_low_dw > 0:
        print(f"\n[RESULT] Disfluency BETTER than WPM (CI > 0)")
        print(f"  HYPOTHESIS: SUPPORTED")
    elif ci_high_dw < 0:
        print(f"\n[RESULT] WPM BETTER than Disfluency (CI < 0)")
        print(f"  HYPOTHESIS: REJECTED")
    else:
        print(f"\n[RESULT] Difference not significant (CI includes 0)")

    # TEST 2: Composite vs WPM (if composite is available)
    if rho_composite is not None:
        print(f"\nTEST 2: Composite vs WPM")
        print("-" * 70)

        diff_comp_wpm = rho_composite - rho_wpm
        percent_improvement_comp = (diff_comp_wpm / abs(rho_wpm)) * 100 if rho_wpm != 0 else 0

        print(f"Raw difference (composite - wpm):")
        print(f"  {rho_composite:.4f} - {rho_wpm:.4f} = {diff_comp_wpm:.4f}")
        print(f"  Percent change: {percent_improvement_comp:+.1f}%")

        differences_comp_wpm = []
        for _ in range(n_boot):
            sample_df = df.sample(frac=1, replace=True, random_state=rng)
            r_comp, _ = spearmanr(sample_df["composite_fluency_normalized"], sample_df["mean_fluency"])
            r_wpm_boot, _ = spearmanr(sample_df["wpm"], sample_df["mean_fluency"])
            differences_comp_wpm.append(r_comp - r_wpm_boot)

        differences_comp_wpm = np.array(differences_comp_wpm)
        ci_low_cw, ci_high_cw = np.percentile(differences_comp_wpm, [2.5, 97.5])

        print(f"Bootstrap 95% CI for difference (n={n_boot} resamples):")
        print(f"  Mean difference:  {differences_comp_wpm.mean():.4f}")
        print(f"  95% CI:           [{ci_low_cw:.4f}, {ci_high_cw:.4f}]")

        if ci_low_cw > 0:
            print(f"\n[RESULT] Composite BETTER than WPM (CI > 0)")
        elif ci_high_cw < 0:
            print(f"\n[RESULT] WPM BETTER than Composite (CI < 0)")
        else:
            print(f"\n[RESULT] Difference not significant (CI includes 0)")

        # TEST 3: Composite vs Disfluency
        print(f"\nTEST 3: Composite vs Disfluency")
        print("-" * 70)

        diff_comp_dis = rho_composite - rho_disfluency
        percent_improvement_comp_dis = (diff_comp_dis / abs(rho_disfluency)) * 100 if rho_disfluency != 0 else 0

        print(f"Raw difference (composite - disfluency):")
        print(f"  {rho_composite:.4f} - {rho_disfluency:.4f} = {diff_comp_dis:.4f}")
        print(f"  Percent change: {percent_improvement_comp_dis:+.1f}%")

        differences_comp_dis = []
        for _ in range(n_boot):
            sample_df = df.sample(frac=1, replace=True, random_state=rng)
            r_comp, _ = spearmanr(sample_df["composite_fluency_normalized"], sample_df["mean_fluency"])
            r_dis_boot, _ = spearmanr(sample_df["duration_weighted_disfluency"], sample_df["mean_fluency"])
            differences_comp_dis.append(r_comp - r_dis_boot)

        differences_comp_dis = np.array(differences_comp_dis)
        ci_low_cd, ci_high_cd = np.percentile(differences_comp_dis, [2.5, 97.5])

        print(f"Bootstrap 95% CI for difference (n={n_boot} resamples):")
        print(f"  Mean difference:  {differences_comp_dis.mean():.4f}")
        print(f"  95% CI:           [{ci_low_cd:.4f}, {ci_high_cd:.4f}]")

        if ci_low_cd > 0:
            print(f"\n[RESULT] Composite BETTER than Disfluency (CI > 0)")
        elif ci_high_cd < 0:
            print(f"\n[RESULT] Disfluency BETTER than Composite (CI < 0)")
        else:
            print(f"\n[RESULT] Difference not significant (CI includes 0)")

    # TEST 4: Combined vs WPM (if combined is available)
    if rho_combined is not None:
        print(f"\nTEST 4: Combined (80% WPM + 20% Composite) vs WPM")
        print("-" * 70)

        diff_combined_wpm = rho_combined - rho_wpm
        percent_improvement_combined = (diff_combined_wpm / abs(rho_wpm)) * 100 if rho_wpm != 0 else 0

        print(f"Raw difference (combined - wpm):")
        print(f"  {rho_combined:.4f} - {rho_wpm:.4f} = {diff_combined_wpm:.4f}")
        print(f"  Percent change: {percent_improvement_combined:+.1f}%")

        differences_combined_wpm = []
        for _ in range(n_boot):
            sample_df = df.sample(frac=1, replace=True, random_state=rng)
            r_combined, _ = spearmanr(sample_df["combined_wpm_composite"], sample_df["mean_fluency"])
            r_wpm_boot, _ = spearmanr(sample_df["wpm"], sample_df["mean_fluency"])
            differences_combined_wpm.append(r_combined - r_wpm_boot)

        differences_combined_wpm = np.array(differences_combined_wpm)
        ci_low_cwpm, ci_high_cwpm = np.percentile(differences_combined_wpm, [2.5, 97.5])

        print(f"Bootstrap 95% CI for difference (n={n_boot} resamples):")
        print(f"  Mean difference:  {differences_combined_wpm.mean():.4f}")
        print(f"  95% CI:           [{ci_low_cwpm:.4f}, {ci_high_cwpm:.4f}]")

        if ci_low_cwpm > 0:
            print(f"\n[RESULT] Combined BETTER than WPM (CI > 0)")
        elif ci_high_cwpm < 0:
            print(f"\n[RESULT] WPM BETTER than Combined (CI < 0)")
        else:
            print(f"\n[RESULT] Difference not significant (CI includes 0)")

        # TEST 5: Combined vs Composite
        print(f"\nTEST 5: Combined (80% WPM + 20% Composite) vs Composite")
        print("-" * 70)

        diff_combined_comp = rho_combined - rho_composite
        percent_improvement_combined_comp = (diff_combined_comp / abs(rho_composite)) * 100 if rho_composite != 0 else 0

        print(f"Raw difference (combined - composite):")
        print(f"  {rho_combined:.4f} - {rho_composite:.4f} = {diff_combined_comp:.4f}")
        print(f"  Percent change: {percent_improvement_combined_comp:+.1f}%")

        differences_combined_comp = []
        for _ in range(n_boot):
            sample_df = df.sample(frac=1, replace=True, random_state=rng)
            r_combined, _ = spearmanr(sample_df["combined_wpm_composite"], sample_df["mean_fluency"])
            r_comp_boot, _ = spearmanr(sample_df["composite_fluency_normalized"], sample_df["mean_fluency"])
            differences_combined_comp.append(r_combined - r_comp_boot)

        differences_combined_comp = np.array(differences_combined_comp)
        ci_low_ccomp, ci_high_ccomp = np.percentile(differences_combined_comp, [2.5, 97.5])

        print(f"Bootstrap 95% CI for difference (n={n_boot} resamples):")
        print(f"  Mean difference:  {differences_combined_comp.mean():.4f}")
        print(f"  95% CI:           [{ci_low_ccomp:.4f}, {ci_high_ccomp:.4f}]")

        if ci_low_ccomp > 0:
            print(f"\n[RESULT] Combined BETTER than Composite (CI > 0)")
        elif ci_high_ccomp < 0:
            print(f"\n[RESULT] Composite BETTER than Combined (CI < 0)")
        else:
            print(f"\n[RESULT] Difference not significant (CI includes 0)")

        # TEST 6: Combined vs Disfluency
        print(f"\nTEST 6: Combined (80% WPM + 20% Composite) vs Disfluency")
        print("-" * 70)

        diff_combined_dis = rho_combined - rho_disfluency
        percent_improvement_combined_dis = (diff_combined_dis / abs(rho_disfluency)) * 100 if rho_disfluency != 0 else 0

        print(f"Raw difference (combined - disfluency):")
        print(f"  {rho_combined:.4f} - {rho_disfluency:.4f} = {diff_combined_dis:.4f}")
        print(f"  Percent change: {percent_improvement_combined_dis:+.1f}%")

        differences_combined_dis = []
        for _ in range(n_boot):
            sample_df = df.sample(frac=1, replace=True, random_state=rng)
            r_combined, _ = spearmanr(sample_df["combined_wpm_composite"], sample_df["mean_fluency"])
            r_dis_boot, _ = spearmanr(sample_df["duration_weighted_disfluency"], sample_df["mean_fluency"])
            differences_combined_dis.append(r_combined - r_dis_boot)

        differences_combined_dis = np.array(differences_combined_dis)
        ci_low_cdis, ci_high_cdis = np.percentile(differences_combined_dis, [2.5, 97.5])

        print(f"Bootstrap 95% CI for difference (n={n_boot} resamples):")
        print(f"  Mean difference:  {differences_combined_dis.mean():.4f}")
        print(f"  95% CI:           [{ci_low_cdis:.4f}, {ci_high_cdis:.4f}]")

        if ci_low_cdis > 0:
            print(f"\n[RESULT] Combined BETTER than Disfluency (CI > 0)")
        elif ci_high_cdis < 0:
            print(f"\n[RESULT] Disfluency BETTER than Combined (CI < 0)")
        else:
            print(f"\n[RESULT] Difference not significant (CI includes 0)")

    # =====================================================================
    # DESCRIPTIVE STATISTICS
    # =====================================================================

    print(f"\n" + "=" * 70)
    print("DESCRIPTIVE STATISTICS")
    print("=" * 70)

    print(f"\nHuman Fluency Ratings (1-9 scale):")
    print(f"  Mean:     {df['mean_fluency'].mean():.2f}")
    print(f"  Median:   {df['mean_fluency'].median():.2f}")
    print(f"  Std Dev:  {df['mean_fluency'].std():.2f}")
    print(f"  Range:    {df['mean_fluency'].min():.1f} - {df['mean_fluency'].max():.1f}")

    print(f"\nWPM (Baseline):")
    print(f"  Mean:     {df['wpm'].mean():.1f}")
    print(f"  Median:   {df['wpm'].median():.1f}")
    print(f"  Std Dev:  {df['wpm'].std():.1f}")
    print(f"  Range:    {df['wpm'].min():.1f} - {df['wpm'].max():.1f}")

    print(f"\nDuration-Weighted Disfluency (0=fluent, 1=disfluent):")
    print(f"  Mean:     {df['duration_weighted_disfluency'].mean():.3f}")
    print(f"  Median:   {df['duration_weighted_disfluency'].median():.3f}")
    print(f"  Std Dev:  {df['duration_weighted_disfluency'].std():.3f}")
    print(f"  Range:    {df['duration_weighted_disfluency'].min():.3f} - {df['duration_weighted_disfluency'].max():.3f}")

    if "composite_fluency_score" in df.columns:
        print(f"\nComposite Fluency Score (0-100 scale):")
        print(f"  Mean:     {df['composite_fluency_score'].mean():.1f}")
        print(f"  Median:   {df['composite_fluency_score'].median():.1f}")
        print(f"  Std Dev:  {df['composite_fluency_score'].std():.1f}")
        print(f"  Range:    {df['composite_fluency_score'].min():.1f} - {df['composite_fluency_score'].max():.1f}")

    if "combined_wpm_composite" in df.columns:
        print(f"\nCombined Metric (80% WPM + 20% Composite, 0-1 scale):")
        print(f"  Mean:     {df['combined_wpm_composite'].mean():.3f}")
        print(f"  Median:   {df['combined_wpm_composite'].median():.3f}")
        print(f"  Std Dev:  {df['combined_wpm_composite'].std():.3f}")
        print(f"  Range:    {df['combined_wpm_composite'].min():.3f} - {df['combined_wpm_composite'].max():.3f}")

    # =====================================================================
    # SAMPLE-BY-SAMPLE COMPARISON
    # =====================================================================

    print(f"\n" + "=" * 70)
    print("SAMPLE-BY-SAMPLE DATA")
    print("=" * 70)

    if "combined_wpm_composite" in df.columns:
        df_display = df[["sample_id", "mean_fluency", "wpm", "duration_weighted_disfluency", "composite_fluency_score", "combined_wpm_composite"]].copy()
        df_display["sample_id"] = "S" + df_display["sample_id"].astype(str).str.zfill(2)
        df_display.columns = ["Sample", "Human", "WPM", "Disfluency", "Composite", "Combined"]
        df_display = df_display.sort_values("Sample")
        # Format for readability
        df_display["Composite"] = df_display["Composite"].apply(lambda x: f"{x:.0f}")
        df_display["Combined"] = df_display["Combined"].apply(lambda x: f"{x:.3f}")
    elif "composite_fluency_score" in df.columns:
        df_display = df[["sample_id", "mean_fluency", "wpm", "duration_weighted_disfluency", "composite_fluency_score"]].copy()
        df_display["sample_id"] = "S" + df_display["sample_id"].astype(str).str.zfill(2)
        df_display.columns = ["Sample", "Human", "WPM", "Disfluency", "Composite"]
        df_display = df_display.sort_values("Sample")
        # Format for readability
        df_display["Composite"] = df_display["Composite"].apply(lambda x: f"{x:.0f}")
    else:
        df_display = df[["sample_id", "mean_fluency", "wpm", "duration_weighted_disfluency"]].copy()
        df_display["sample_id"] = "S" + df_display["sample_id"].astype(str).str.zfill(2)
        df_display.columns = ["Sample", "Human", "WPM", "Disfluency"]
        df_display = df_display.sort_values("Sample")

    print("\n" + df_display.to_string(index=False))

    # =====================================================================
    # WRITE RESULTS TO FILE
    # =====================================================================

    results_file = script_dir / "HYPOTHESIS_TEST_RESULTS.txt"
    with open(results_file, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("PREREGISTERED HYPOTHESIS TEST RESULTS\n")
        f.write("=" * 70 + "\n\n")

        f.write("PRIMARY HYPOTHESIS:\n")
        f.write("Duration-weighted disfluency correlates MORE STRONGLY with human\n")
        f.write("fluency judgments than baseline WPM alone.\n\n")

        f.write("RESULTS SUMMARY (Four-Way Comparison):\n")
        f.write(f"1. Duration-Weighted Disfluency vs Human: r = {rho_disfluency:.4f}, p = {p_disfluency:.4g}\n")
        f.write(f"2. WPM Baseline vs Human:                r = {rho_wpm:.4f}, p = {p_wpm:.4g}\n")
        if rho_composite is not None:
            f.write(f"3. Composite Fluency Score vs Human:    r = {rho_composite:.4f}, p = {p_composite:.4g}\n")
        if rho_combined is not None:
            f.write(f"4. Combined (80% WPM + 20% Comp) vs Human: r = {rho_combined:.4f}, p = {p_combined:.4g}\n\n")
        else:
            f.write("\n")

        f.write("HYPOTHESIS TEST (Disfluency vs WPM):\n")
        f.write(f"Correlation difference: {diff_dis_wpm:.4f}\n")
        f.write(f"Bootstrap 95% CI: [{ci_low_dw:.4f}, {ci_high_dw:.4f}]\n\n")

        if ci_low_dw > 0:
            f.write("CONCLUSION: HYPOTHESIS SUPPORTED\n")
            f.write("Duration-weighted disfluency correlates better than WPM.\n")
        elif ci_high_dw < 0:
            f.write("CONCLUSION: HYPOTHESIS REJECTED\n")
            f.write("WPM correlates better than duration-weighted disfluency.\n")
        else:
            f.write("CONCLUSION: INCONCLUSIVE\n")
            f.write("Difference is not significant at 95% confidence level.\n")

        if rho_composite is not None:
            f.write("\n\nADDITIONAL COMPARISON (Composite vs WPM):\n")
            f.write(f"Correlation difference: {diff_comp_wpm:.4f}\n")
            f.write(f"Bootstrap 95% CI: [{ci_low_cw:.4f}, {ci_high_cw:.4f}]\n\n")

            if ci_low_cw > 0:
                f.write("RESULT: Composite score correlates better than WPM.\n")
            elif ci_high_cw < 0:
                f.write("RESULT: WPM correlates better than composite score.\n")
            else:
                f.write("RESULT: Difference not significant.\n")

            f.write("\n\nADDITIONAL COMPARISON (Composite vs Disfluency):\n")
            f.write(f"Correlation difference: {diff_comp_dis:.4f}\n")
            f.write(f"Bootstrap 95% CI: [{ci_low_cd:.4f}, {ci_high_cd:.4f}]\n\n")

            if ci_low_cd > 0:
                f.write("RESULT: Composite score correlates better than disfluency.\n")
            elif ci_high_cd < 0:
                f.write("RESULT: Disfluency correlates better than composite score.\n")
            else:
                f.write("RESULT: Difference not significant.\n")

        if rho_combined is not None:
            f.write("\n\nNEW COMPARISON (Combined vs WPM):\n")
            f.write(f"Metric: 80% WPM + 20% Composite Fluency\n")
            f.write(f"Correlation difference: {diff_combined_wpm:.4f}\n")
            f.write(f"Bootstrap 95% CI: [{ci_low_cwpm:.4f}, {ci_high_cwpm:.4f}]\n\n")

            if ci_low_cwpm > 0:
                f.write("RESULT: Combined metric correlates better than WPM alone.\n")
            elif ci_high_cwpm < 0:
                f.write("RESULT: WPM alone correlates better than combined metric.\n")
            else:
                f.write("RESULT: Difference not significant.\n")

            f.write("\n\nNEW COMPARISON (Combined vs Composite):\n")
            f.write(f"Correlation difference: {diff_combined_comp:.4f}\n")
            f.write(f"Bootstrap 95% CI: [{ci_low_ccomp:.4f}, {ci_high_ccomp:.4f}]\n\n")

            if ci_low_ccomp > 0:
                f.write("RESULT: Combined metric correlates better than composite alone.\n")
            elif ci_high_ccomp < 0:
                f.write("RESULT: Composite alone correlates better than combined metric.\n")
            else:
                f.write("RESULT: Difference not significant.\n")

            f.write("\n\nNEW COMPARISON (Combined vs Disfluency):\n")
            f.write(f"Correlation difference: {diff_combined_dis:.4f}\n")
            f.write(f"Bootstrap 95% CI: [{ci_low_cdis:.4f}, {ci_high_cdis:.4f}]\n\n")

            if ci_low_cdis > 0:
                f.write("RESULT: Combined metric correlates better than disfluency.\n")
            elif ci_high_cdis < 0:
                f.write("RESULT: Disfluency correlates better than combined metric.\n")
            else:
                f.write("RESULT: Difference not significant.\n")

    print(f"\nResults written to: {results_file}")
    return 0


if __name__ == "__main__":
    exit(main())
