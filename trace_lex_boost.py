"""
Re-run scoring with debug output for ielts8-8.5
"""
import sys
sys.path.insert(0, "/d/Work/Projects/AI/speech-analysis")

from src.core.ielts_band_scorer import IELTSBandScorer
import json

# Load the raw analysis
with open("d:/Work/Projects/AI/speech-analysis/outputs/audio_analysis/ielts8-8.5.json") as f:
    raw_analysis = json.load(f)

metrics = raw_analysis['raw_analysis']

# Create scorer and score
scorer = IELTSBandScorer()

print("=" * 60)
print("MANUAL LEXICAL SCORING TRACE FOR IELTS8-8.5")
print("=" * 60)
print()

vocab_richness = metrics.get("vocab_richness", 0)
lexical_density = metrics.get("lexical_density", 0)

print(f"Input metrics:")
print(f"  vocab_richness: {vocab_richness}")
print(f"  lexical_density: {lexical_density}")
print()

# Step 1: Determine base score
if vocab_richness >= 0.58 and lexical_density >= 0.50:
    base_score = 8.5
elif vocab_richness >= 0.54 and lexical_density >= 0.47:
    base_score = 8.0
elif vocab_richness >= 0.50 and lexical_density >= 0.44:
    base_score = 7.5
elif vocab_richness >= 0.46 and lexical_density >= 0.41:
    base_score = 7.0
elif vocab_richness >= 0.42 and lexical_density >= 0.38:
    base_score = 6.5
elif vocab_richness >= 0.38 and lexical_density >= 0.35:
    base_score = 6.0
else:
    base_score = 6.0

print(f"Step 1 - Metrics-based base score: {base_score}")
print()

# The LLM metrics would come from the scoring call
# But since we don't have them easily accessible here,
# let me just show what would happen with different LLM findings

print("Step 2 - Hypothetical LLM boost scenarios:")
print()

# Scenario 1: adv_vocab = 2
adv_vocab = 2
print(f"  IF adv_vocab={adv_vocab}:")
print(f"    - vocab >= 0.46? {vocab_richness >= 0.46}")
print(f"    - base_score >= 6.5? {base_score >= 6.5}")
if adv_vocab >= 2 and vocab_richness >= 0.46 and base_score >= 6.5:
    print(f"    → BOOST: max({base_score}, 7.5) = 7.5")
else:
    print(f"    → NO BOOST")
print()

# Scenario 2: adv_vocab = 3
adv_vocab = 3
print(f"  IF adv_vocab={adv_vocab}:")
print(f"    - vocab >= 0.48? {vocab_richness >= 0.48}")
print(f"    - base_score >= 7.0? {base_score >= 7.0}")
if adv_vocab >= 3 and vocab_richness >= 0.48 and base_score >= 7.0:
    print(f"    → BOOST: max({base_score}, 8.0) = 8.0")
else:
    print(f"    → NO BOOST")
print()

# Scenario 3: idioms
print(f"  IF register_mismatch=0 and vocab>=0.48 and idioms=1 and word_errors<=1 and base_score>=6.5:")
print(f"    vocab >= 0.48? {vocab_richness >= 0.48}")
print(f"    base_score >= 6.5? {base_score >= 6.5}")
if vocab_richness >= 0.48 and base_score >= 6.5:
    print(f"    → BOOST: max({base_score}, 7.5) = 7.5")
else:
    print(f"    → NO BOOST")
print()

print("=" * 60)
print("CONCLUSION: To reach 8.0, either:")
print("  1. LLM found 3+ advanced vocab (adv_vocab >= 3)")
print("  2. LLM found 2+ idioms with no errors")
print("=" * 60)
