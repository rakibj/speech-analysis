# Engine Runner - Quick Reference Card

## 🚀 Three Ways to Test

### 1️⃣ Command Line (30-60 seconds)
```bash
python test_quick.py
```

### 2️⃣ Interactive Notebook (Best for Development)
Open: `notebooks/test_engine_runner.ipynb`

### 3️⃣ Python Script
```python
import asyncio
from src.engine_runner import run_engine
from pathlib import Path

audio_bytes = Path("data/ielts_part_2/audio.wav").read_bytes()
result = asyncio.run(run_engine(audio_bytes, context="conversational"))
print(f"Band Score: {result['band_scores']['overall_band']}")
print(f"Transcript: {result['transcript']}")
```

---

## 📝 Function Signatures

### Async (Use in async contexts)
```python
result = await run_engine(
    audio_bytes=b'...',      # Raw audio bytes
    context="conversational", # "conversational", "narrative", "presentation"
    device="cpu",            # "cpu" or "cuda"
    use_llm=True,            # True=slow but accurate, False=fast
    filename="audio.wav"     # Optional, for reference
)
```

### Sync (Use in regular Python)
```python
result = run_engine_sync(
    audio_bytes=b'...',
    context="conversational"
)
```

---

## 🎯 Key Result Fields

```python
result['transcript']                    # Speech text
result['band_scores']['overall_band']   # IELTS band (5.0-9.0)
result['statistics']                    # Word counts, duration, etc.
result['fluency_analysis']              # Fluency metrics
result['pronunciation']                 # Clarity & prosody
result['llm_analysis']                  # Semantic analysis (if use_llm=True)
```

---

## ⚡ Quick Tests

### Basic Test
```python
result = await run_engine(audio_bytes, use_llm=False)  # 30-60s
```

### Accurate Test (with LLM)
```python
result = await run_engine(audio_bytes, use_llm=True)   # 60-120s
```

### Error Handling
```python
try:
    result = await run_engine(audio_bytes)
except ValueError:
    print("Invalid audio bytes")
except Exception as e:
    print(f"Analysis failed: {e}")
```

### Multiple Contexts
```python
for ctx in ["conversational", "narrative", "presentation"]:
    result = await run_engine(audio_bytes, context=ctx)
    print(f"{ctx}: {result['band_scores']['overall_band']}")
```

---

## 📊 Performance

| Scenario | Time |
|----------|------|
| No LLM | 30-60s |
| With LLM | 60-120s |
| Sync overhead | <1s |

---

## ✅ Testing Checklist

Run in this order:

1. ✅ `python test_quick.py`
2. ✅ Open notebook, run sections 1-4
3. ✅ Test error handling (notebook section 6)
4. ✅ Test different contexts (notebook section 5)
5. ✅ Test sync wrapper (notebook section 8)

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| "No audio files found" | Update path: `Path("your/audio/file.wav")` |
| CUDA out of memory | Use `device="cpu"` |
| Too slow | Disable LLM: `use_llm=False` |
| API errors | Check OPENAI_API_KEY environment variable |
| Temp files accumulate | Rare; automatic cleanup usually works |

---

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `src/engine_runner.py` | Main implementation |
| `src/engine.py` | Underlying analysis engine |
| `test_quick.py` | Quick CLI test |
| `notebooks/test_engine_runner.ipynb` | Interactive testing |
| `ENGINE_RUNNER_COMPLETE.md` | Full documentation |
| `IMPLEMENTATION_GUIDE.md` | Implementation details |
| `TEST_ENGINE_RUNNER.md` | Testing guide |

---

## 🎓 Learning Resources

1. **Start here:** Run `test_quick.py`
2. **Explore:** Open `notebooks/test_engine_runner.ipynb`
3. **Understand:** Read docstrings in `src/engine_runner.py`
4. **Deep dive:** See `ENGINE_RUNNER_COMPLETE.md`

---

## 💡 Pro Tips

- Use `use_llm=False` for testing (faster)
- Check logs with `logger.info()` in code
- Export results: `json.dump(result, file)`
- Handle errors with try/except blocks
- Monitor temp file cleanup
- Test with different audio lengths

---

**Next Step:** Run `python test_quick.py` now! 🚀
