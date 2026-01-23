#!/usr/bin/env python3
"""Debug Modal vs Local discrepancy for ielts5.5"""
import json

print("=" * 70)
print("LOCAL RESULTS vs MODAL RESULTS")
print("=" * 70)

with open('outputs/band_results/ielts5.5.json') as f:
    local_data = json.load(f)
    local_cb = local_data['band_scores']['criterion_bands']
    local_fc = local_cb['fluency_coherence']
    local_pr = local_cb['pronunciation']
    local_lr = local_cb['lexical_resource']
    local_gr = local_cb['grammatical_range_accuracy']
    local_avg = (local_fc + local_pr + local_lr + local_gr) / 4
    local_overall = local_data['band_scores']['overall_band']
    
    print("\nLOCAL (batch_band_analysis.py):")
    print(f"  Fluency:      {local_fc}")
    print(f"  Pronunciation: {local_pr}")
    print(f"  Lexical:      {local_lr}")
    print(f"  Grammar:      {local_gr}")
    print(f"  ───────────────────")
    print(f"  Average:      {local_avg}")
    print(f"  Overall:      {local_overall}")

print("\nMODAL (response from Modal):")
print(f"  Fluency:      6.5")
print(f"  Pronunciation: 5.5")
print(f"  Lexical:      8")
print(f"  Grammar:      7")
print(f"  ───────────────────")
print(f"  Average:      {(6.5 + 5.5 + 8 + 7) / 4}")
print(f"  Overall:      7 (WRONG!)")

print("\n" + "=" * 70)
print("ISSUE: Modal is returning different criterion scores!")
print("=" * 70)
print("\nPossible causes:")
print("1. Different code version deployed to Modal")
print("2. Different LLM responses (API inconsistency)")
print("3. Different metric extraction on Modal")
print("4. Cache/stale code on Modal")
print("\nAction: Need to check what version is running on Modal")
