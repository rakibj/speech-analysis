import json

# Check ielts8-8.5 metrics
with open("outputs/audio_analysis/ielts8-8.5.json") as f:
    data = json.load(f)
    
print("ielts8-8.5 METRICS:")
print(f"  vocab_richness: {data['metrics'].get('vocab_richness')}")
print(f"  lexical_density: {data['metrics'].get('lexical_density')}")
print()

print("ielts8-8.5 LLM METRICS:")
llm = data.get('llm_metrics', {})
print(f"  advanced_vocabulary_count: {llm.get('advanced_vocabulary_count')}")
print(f"  idiomatic_collocation_count: {llm.get('idiomatic_collocation_count')}")
print(f"  word_choice_error_count: {llm.get('word_choice_error_count')}")
print(f"  topic_relevance: {llm.get('topic_relevance')}")
print(f"  listener_effort_high: {llm.get('listener_effort_high')}")
print(f"  flow_instability_present: {llm.get('flow_instability_present')}")
print(f"  register_mismatch_count: {llm.get('register_mismatch_count')}")
print()

# Compare to ielts8.5 which correctly stays 8.0
with open("outputs/audio_analysis/ielts8.5.json") as f:
    data = json.load(f)
    
print("ielts8.5 METRICS:")
print(f"  vocab_richness: {data['metrics'].get('vocab_richness')}")
print(f"  lexical_density: {data['metrics'].get('lexical_density')}")
print()

print("ielts8.5 LLM METRICS:")
llm = data.get('llm_metrics', {})
print(f"  advanced_vocabulary_count: {llm.get('advanced_vocabulary_count')}")
print(f"  idiomatic_collocation_count: {llm.get('idiomatic_collocation_count')}")
print(f"  word_choice_error_count: {llm.get('word_choice_error_count')}")
