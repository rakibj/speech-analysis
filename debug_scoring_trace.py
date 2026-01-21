"""
Debug lexical scoring for ielts8-8.5
"""
import json

# Load audio analysis (has metrics)
with open("outputs/audio_analysis/ielts8-8.5.json") as f:
    audio_data = json.load(f)

metrics = audio_data['raw_analysis']
vocab_richness = metrics.get('vocab_richness', 0)
lexical_density = metrics.get('lexical_density', 0)
unique_word_count = metrics.get('unique_word_count', 1)

print("=" * 60)
print("IELTS 8-8.5 METRICS:")
print(f"  vocab_richness: {vocab_richness}")
print(f"  lexical_density: {lexical_density}")
print(f"  unique_word_count: {unique_word_count}")
print()

# Now trace through scoring logic
print("SCORING LOGIC TRACE:")
print()

# Step 1: Base score from metrics
if vocab_richness >= 0.58 and lexical_density >= 0.50:
    base_score = 8.5
    reason = "vocab >= 0.58 AND lex >= 0.50"
elif vocab_richness >= 0.54 and lexical_density >= 0.47:
    base_score = 8.0
    reason = "vocab >= 0.54 AND lex >= 0.47"
elif vocab_richness >= 0.50 and lexical_density >= 0.44:
    base_score = 7.5
    reason = "vocab >= 0.50 AND lex >= 0.44"
elif vocab_richness >= 0.46 and lexical_density >= 0.41:
    base_score = 7.0
    reason = "vocab >= 0.46 AND lex >= 0.41"
elif vocab_richness >= 0.42 and lexical_density >= 0.38:
    base_score = 6.5
    reason = "vocab >= 0.42 AND lex >= 0.38"
elif vocab_richness >= 0.38 and lexical_density >= 0.35:
    base_score = 6.0
    reason = "vocab >= 0.38 AND lex >= 0.35"
else:
    base_score = 6.0
    reason = "DEFAULT"

print(f"BASE SCORE: {base_score} (reason: {reason})")
print()

# Check which boosts could apply
print("POTENTIAL BOOSTS:")
print(f"  vocab >= 0.50? {vocab_richness >= 0.50} -> Would allow adv_vocab >= 5 boost")
print(f"  vocab >= 0.48? {vocab_richness >= 0.48} -> Would allow adv_vocab >= 3 boost")
print(f"  vocab >= 0.46? {vocab_richness >= 0.46} -> Would allow adv_vocab >= 2 boost")
print()
print("⚠️  PROBLEM: vocab_richness={} is BELOW 0.46 minimum!".format(vocab_richness))
print("   So NO boosts should be allowed by the gating logic.")
print()

# Check for idiomatic boost
print("IDIOMATIC BOOST CHECK:")
print(f"  vocab >= 0.48? {vocab_richness >= 0.48} (required for idiom boost)")
print("   → Cannot apply idiomatic boost")
print()

print("CONCLUSION:")
print(f"  Expected final score: {base_score}")
print("  Actual from batch output: 8.0")
print()
print("⚠️  MISMATCH! Something is still boosting the score!")
print("=" * 60)
