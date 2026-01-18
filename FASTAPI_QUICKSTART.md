# FastAPI Quick Start

## Installation

Install dependencies with the new FastAPI packages:

```bash
uv sync
```

Or with pip:

```bash
pip install -e .
```

## Running the API Server

### Development Mode (with auto-reload)

```bash
python app.py
```

Or directly with uvicorn:

```bash
uvicorn app:app --reload --port 8000
```

### Production Mode

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Accessing the API

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "message": "API is running"
}
```

### Analyze Audio (with file path)

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "audio_path": "path/to/audio.wav",
    "speech_context": "conversational",
    "device": "cpu"
  }'
```

Request Parameters:

- `audio_path` (string, required): Path to audio file
- `speech_context` (enum): conversational | narrative | presentation | interview
- `device` (string): cpu or cuda

Response: Complete analysis with fluency score, metrics, and filler detection

### Analyze Audio (with file upload)

```bash
curl -X POST http://localhost:8000/api/v1/analyze-upload \
  -F "file=@path/to/audio.wav" \
  -F "speech_context=conversational" \
  -F "device=cpu"
```

## Example Response

```json
{
  "verdict": {
    "fluency_score": 75.5,
    "readiness": "proficient"
  },
  "benchmarking": {
    "percentile": 82,
    "comparison": {...}
  },
  "normalized_metrics": {
    "speech_rate_wpm": 142.3,
    "articulation_rate_wpm": 156.8,
    "filler_frequency": 2.1,
    "pause_frequency": 3.4
  },
  "word_timestamps": [
    {
      "word": "hello",
      "start": 0.0,
      "end": 0.5,
      "duration": 0.5,
      "confidence": 0.95,
      "is_filler": false
    }
  ],
  "content_words": [...],
  "segment_timestamps": [...],
  "filler_events": [...],
  "statistics": {
    "total_words_transcribed": 234,
    "content_words": 210,
    "filler_words_detected": 12,
    "filler_percentage": 5.13
  }
}
```

## Testing the API

```bash
# Run API tests
pytest tests/test_api/ -v

# Test a specific endpoint
pytest tests/test_api/test_routes.py::test_health_check -v
```

## Performance Notes

- First analysis takes longer (~30s) due to model loading
- Subsequent analyses are faster (model cached in memory)
- GPU (CUDA) support available with `device=cuda`
- File uploads are saved to temp location and cleaned up after analysis

## Environment Variables

Create a `.env` file in project root:

```
OPENAI_API_KEY=your-key-here
LOG_LEVEL=INFO
```

## Troubleshooting

### CUDA not detected

- Ensure NVIDIA CUDA 11.8+ is installed
- Use `device=cpu` parameter or check CUDA installation

### Model loading issues

- Models download automatically on first use
- Requires internet connection
- Check disk space for model cache

### Audio file not found

- Use absolute path or relative path from project root
- For uploads, file is automatically saved to temp directory

## Next Steps

- See [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for architecture overview
- Add database support for persisting results
- Add authentication if needed
- Deploy with Docker or cloud platform
