"""Tests for FastAPI audio analysis endpoints."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from app import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


def test_analyze_audio_invalid_path(client):
    """Test analyze endpoint with invalid audio path."""
    response = client.post(
        "/api/v1/analyze",
        json={
            "audio_path": "/invalid/path/audio.wav",
            "speech_context": "conversational"
        }
    )
    assert response.status_code == 404


def test_analyze_audio_request_model(client):
    """Test that request validation works."""
    # Invalid context should fail
    response = client.post(
        "/api/v1/analyze",
        json={
            "audio_path": "/some/path.wav",
            "speech_context": "invalid_context"
        }
    )
    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_upload_no_file(client):
    """Test upload endpoint without file."""
    response = client.post("/api/v1/analyze-upload")
    assert response.status_code == 422  # Missing required field


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
