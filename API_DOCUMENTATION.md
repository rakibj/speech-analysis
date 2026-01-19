# Speech Analysis API - Complete Guide

Your API is ready to use. This guide covers everything you need.

---

## 🚀 Quick Start (5 Minutes)

### 1. Start the Server

```bash
python app.py
```

Output:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Get Your API Key

```bash
python verify_hardcoded_keys.py
```

Output:

```
Hardcoded keys in system: 1
  - my-dev-key (direct) 5cc0f4d6...

Testing validation:
  [OK] Key validated successfully
```

Your key: **`sk_wpUwYgv2RMtAhwTecCh0Qfp9`**

### 3. Test Health

```bash
curl http://localhost:8000/api/direct/v1/health \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9"
```

Response:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "message": "RapidAPI endpoint is running"
}
```

✅ **You're connected!**

---

## 📊 API Overview

### Endpoints

| Endpoint           | Method | Purpose                   | Auth     |
| ------------------ | ------ | ------------------------- | -------- |
| `/health`          | GET    | Check server status       | Required |
| `/analyze`         | POST   | Submit audio for analysis | Required |
| `/result/{job_id}` | GET    | Get analysis results      | Required |

### Base URLs

- **For you (direct):** `http://localhost:8000/api/direct/v1`
- **For RapidAPI:** `http://localhost:8000/api/v1` (uses signature verification)

### Authentication

**Header needed for all requests:**

```
X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9
```

---

## 📍 Endpoint Details

### 1. Health Check

**Check if server is running**

```bash
curl http://localhost:8000/api/direct/v1/health \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9"
```

**Response:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "message": "RapidAPI endpoint is running"
}
```

---

### 2. Analyze Audio

**Submit audio file for speech analysis**

```bash
curl -X POST http://localhost:8000/api/direct/v1/analyze \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9" \
  -F "file=@sample.wav" \
  -F "speech_context=conversational" \
  -F "device=cpu"
```

**Parameters:**

| Parameter        | Type   | Required | Default        | Options                                            |
| ---------------- | ------ | -------- | -------------- | -------------------------------------------------- |
| `file`           | File   | Yes      | -              | .wav, .mp3, .m4a, .ogg                             |
| `speech_context` | String | No       | conversational | conversational, narrative, presentation, interview |
| `device`         | String | No       | cpu            | cpu, cuda                                          |

**Response (immediately):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Analysis started. Poll /api/direct/v1/result/{job_id} for results"
}
```

**What happens next:**

1. Server returns immediately (non-blocking)
2. Audio processing starts in background
3. Use `job_id` to poll for results

---

### 3. Get Results

**Poll for analysis results**

```bash
curl http://localhost:8000/api/direct/v1/result/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9"
```

**Response (still processing):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Analysis in progress..."
}
```

**Response (completed - minimal):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "engine_version": "0.1.0",
  "scoring_config": {
    "fluency_weight": 0.3,
    "accuracy_weight": 0.3,
    "lexical_weight": 0.2,
    "coherence_weight": 0.2
  },
  "overall_band": 7.5,
  "criterion_bands": {
    "fluency": 7.5,
    "accuracy": 7.0,
    "lexical_range": 7.0,
    "coherence": 8.0
  },
  "confidence": {
    "category": "high",
    "score": 0.95
  }
}
```

---

## 🎯 Response Tiers

Control response size with `?detail=` parameter:

### Tier 1: Default (Minimal)

```bash
curl http://localhost:8000/api/direct/v1/result/{job_id} \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9"
```

**Size:** ~500 bytes  
**Contains:** job_id, status, bands, confidence

---

### Tier 2: Feedback (Explanations)

```bash
curl "http://localhost:8000/api/direct/v1/result/{job_id}?detail=feedback" \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9"
```

**Size:** ~5-10 KB  
**Also contains:**

- `transcript` - Full audio transcript
- `grammar_errors` - Timestamped errors
- `word_choice_errors` - Vocabulary issues
- `examiner_descriptors` - Tags like "fluent", "clear"
- `fluency_notes` - Explanation of score

---

### Tier 3: Full (Debugging)

```bash
curl "http://localhost:8000/api/direct/v1/result/{job_id}?detail=full" \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9"
```

**Size:** ~50-100 KB  
**Also contains:**

- `word_timestamps` - Every word with timing
- `filler_events` - "Um", "uh" detection
- `statistics` - Raw counts and percentages
- `normalized_metrics` - WPM, pause rates
- `opinions` - LLM detailed analysis
- `confidence_multipliers` - Internal calculations
- `practice_hours_estimate` - Suggested study time

---

## 📋 Complete Workflow Example

### Step 1: Submit Audio

```bash
# Upload audio file
RESPONSE=$(curl -X POST http://localhost:8000/api/direct/v1/analyze \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9" \
  -F "file=@sample.wav" \
  -F "speech_context=conversational")

# Extract job_id
JOB_ID=$(echo $RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $JOB_ID"
```

### Step 2: Wait & Poll

```bash
# Poll every 2 seconds
while true; do
  RESULT=$(curl http://localhost:8000/api/direct/v1/result/$JOB_ID \
    -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9")

  STATUS=$(echo $RESULT | python -c "import sys, json; print(json.load(sys.stdin)['status'])")

  if [ "$STATUS" = "completed" ]; then
    echo "Analysis complete!"
    break
  elif [ "$STATUS" = "error" ]; then
    echo "Error!"
    break
  else
    echo "Still processing..."
    sleep 2
  fi
done
```

### Step 3: Get Results

```bash
# Get minimal response
curl http://localhost:8000/api/direct/v1/result/$JOB_ID \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9" | python -m json.tool

# Get with feedback
curl "http://localhost:8000/api/direct/v1/result/$JOB_ID?detail=feedback" \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9" | python -m json.tool

# Get full data
curl "http://localhost:8000/api/direct/v1/result/$JOB_ID?detail=full" \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9" | python -m json.tool
```

---

## ⚠️ Error Handling

### 401 Unauthorized

```json
{
  "detail": "Invalid API key"
}
```

**Solution:** Check `X-API-Key` header matches hardcoded key

### 404 Not Found

```json
{
  "detail": "Job abc-123 not found or access denied"
}
```

**Solution:** Check `job_id` is correct and from your API key

### 400 Bad Request

```json
{
  "detail": "Invalid speech_context. Valid: conversational, narrative, presentation, interview"
}
```

**Solution:** Use valid `speech_context` value

### 413 Payload Too Large

```json
{
  "detail": "File too large"
}
```

**Solution:** Audio file > 50MB. Use smaller file.

### 500 Server Error

```json
{
  "detail": "Internal server error"
}
```

**Solution:** Check server logs. Restart if needed.

---

## 🔑 API Key Management

### View Your Current Key

```bash
python verify_hardcoded_keys.py
```

### Add New API Key

**Step 1: Generate**

```bash
python -c "
from src.auth.key_manager import KeyManager
KeyManager.generate_key('customer-2', 'direct')
"
```

**Step 2: Copy the output** (key hash)

**Step 3: Edit** [src/auth/key_manager.py](src/auth/key_manager.py#L15)

Add to `VALID_KEYS`:

```python
VALID_KEYS = {
    "5cc0f4d6ecfb565223c8e714a027758f0774dbb7fd21b9be12d152fc0265c6e9": {
        "name": "my-dev-key",
        "owner_type": "direct"
    },
    # ADD NEW KEY HERE:
    "abc123def456...": {
        "name": "customer-2",
        "owner_type": "direct"
    },
}
```

**Step 4: Restart server**

---

## 🧪 Testing

### Run All Tests

```bash
python test_auth_integration.py
```

Expected output:

```
[OK] ALL TESTS PASSED
```

### Test Specific Endpoint

```bash
# Test health
curl http://localhost:8000/api/direct/v1/health \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9" \
  -w "\nHTTP Status: %{http_code}\n"

# Test with invalid key (should get 401)
curl http://localhost:8000/api/direct/v1/health \
  -H "X-API-Key: invalid" \
  -w "\nHTTP Status: %{http_code}\n"
```

---

## 🚀 Deployment to Modal

### 1. Push Code

```bash
git add .
git commit -m "Add API with hardcoded keys"
git push origin main
```

### 2. Deploy to Modal

```bash
# Install modal CLI
pip install modal

# Deploy
modal deploy app.py
```

### 3. Your API URL

```
https://your-username--speech-analysis-app.modal.run
```

### 4. Test Deployed API

```bash
curl https://your-username--speech-analysis-app.modal.run/api/direct/v1/health \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9"
```

**Key stays the same!** Hardcoded keys travel with your code.

---

## 💡 Common Tasks

### Upload and Analyze in One Script

```bash
#!/bin/bash
API_KEY="sk_wpUwYgv2RMtAhwTecCh0Qfp9"
BASE_URL="http://localhost:8000/api/direct/v1"

# Submit
JOB_ID=$(curl -s -X POST $BASE_URL/analyze \
  -H "X-API-Key: $API_KEY" \
  -F "file=@sample.wav" | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

echo "Analyzing... Job: $JOB_ID"

# Poll until done
for i in {1..30}; do
  RESULT=$(curl -s $BASE_URL/result/$JOB_ID \
    -H "X-API-Key: $API_KEY")

  STATUS=$(echo $RESULT | python -c "import sys, json; print(json.load(sys.stdin)['status'])")

  if [ "$STATUS" = "completed" ]; then
    echo "Done! Results:"
    echo $RESULT | python -m json.tool
    exit 0
  fi

  echo "Attempt $i: $STATUS"
  sleep 2
done

echo "Timeout!"
exit 1
```

### Check Response Size

```bash
# Default (minimal)
curl "http://localhost:8000/api/direct/v1/result/{job_id}" \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9" \
  -w "\nSize: %{size_download} bytes\n" -o /dev/null

# Feedback
curl "http://localhost:8000/api/direct/v1/result/{job_id}?detail=feedback" \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9" \
  -w "\nSize: %{size_download} bytes\n" -o /dev/null

# Full
curl "http://localhost:8000/api/direct/v1/result/{job_id}?detail=full" \
  -H "X-API-Key: sk_wpUwYgv2RMtAhwTecCh0Qfp9" \
  -w "\nSize: %{size_download} bytes\n" -o /dev/null
```

---

## 📞 Troubleshooting

### "Invalid API key"

**Problem:** 401 Unauthorized  
**Solution:**

```bash
python verify_hardcoded_keys.py  # Get correct key
```

### "Job not found"

**Problem:** 404 Not Found  
**Solution:**

- Check `job_id` is correct
- Make sure you submitted audio first
- Use same API key for poll as for submit

### Server won't start

**Problem:** Port 8000 already in use  
**Solution:**

```bash
python app.py --port 8001  # Use different port
```

### Slow analysis

**Problem:** Taking longer than expected  
**Solution:**

- Shorter audio files process faster
- GPU (`device=cuda`) faster if available
- Check server logs for errors

### Keys not working after restart

**Problem:** Keys lost  
**Solution:** They shouldn't be! Check:

```bash
python verify_hardcoded_keys.py  # Verify key exists
cat src/auth/key_manager.py | grep VALID_KEYS  # Check file
```

---

## 📚 Additional Resources

- [Hardcoded Keys Guide](HARDCODED_KEYS_GUIDE.md) - Key management
- [Auth Implementation](AUTH_IMPLEMENTATION.md) - How auth works
- [RapidAPI Contract](RAPIDAPI_CONTRACT.md) - Full API spec

---

## ✅ You're Ready!

- ✅ Server starts with `python app.py`
- ✅ API responds to requests with valid key
- ✅ Responses have 3 tiers (default, feedback, full)
- ✅ Keys hardcoded, no database needed
- ✅ Ready to deploy to Modal

**Start using the API!** 🚀

---

**Need help?** Check the troubleshooting section or review the documentation files.
