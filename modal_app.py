"""
Modal deployment for Speech Analysis API.
"""

import modal
import os

# ---------------------------------------------------------
# Modal Volumes for Model Caching
# ---------------------------------------------------------

# Create persistent volumes for caching models across executions
# This eliminates repeated downloads and dramatically reduces latency
model_cache_volume = modal.Volume.from_name(
    "speech-analysis-models",
    create_if_missing=True
)

# ---------------------------------------------------------
# Modal Dict for Job Results (Distributed State)
# ---------------------------------------------------------

# Create persistent distributed dict for async job tracking
# Allows multiple concurrent containers to share job state
job_results_store = modal.Dict.from_name(
    "speech-analysis-jobs",
    create_if_missing=True
)

# ---------------------------------------------------------
# Modal App
# ---------------------------------------------------------

app = modal.App("speech-analysis")


# ---------------------------------------------------------
# Image Builder
# ---------------------------------------------------------

def build_image():
    return (
        modal.Image.debian_slim()
        .apt_install("ffmpeg")  # ← ADD THIS LINEdesi
        .pip_install(
            # Web framework
            "fastapi>=0.104.0,<1.0",
            "uvicorn[standard]>=0.24.0,<1.0",
            "python-multipart>=0.0.6",

            # Core ML / Audio
            "torch>=2.1.0,<3.0",
            "torchaudio>=2.1.0,<3.0",
            "torchcodec>=0.9.1,<1.0",
            "transformers>=4.37.0,<5.0",

            # Audio processing
            "librosa>=0.10.1,<1.0",
            "soundfile>=0.12.1,<0.14",
            "pysoundfile>=0.9.0",  # Latest available version
            "openai-whisper>=20250625",
            "whisperx>=3.4.3",

            # Data
            "pandas>=2.2.0,<3.0",
            "numpy>=2.0.0,<3.0",
            "pydantic>=2.0.0,<3.0",

            # NLP / LLM
            "openai>=2.0.0,<3.0",
            "language-tool-python>=3.2.2,<3.3",

            # Utils
            "python-dotenv>=1.0.0,<2.0",
        )
        .workdir("/app")   # ← still fine
        # ⬇️ MUST BE LAST
        .add_local_dir(
            ".",
            remote_path="/app",
            ignore=[
                ".venv",
                "__pycache__",
                ".git",
                ".pytest_cache",
                ".mypy_cache",
            ],
        )
    )



# ---------------------------------------------------------
# FastAPI ASGI App
# ---------------------------------------------------------

@app.function(
    image=build_image(),
    timeout=600,                 # 10 minutes (safe for heavy jobs)
    cpu=2.0,
    memory=4096,                 # MB
    volumes={
        "/mnt/models": model_cache_volume,
    },
    env={
        # Cache models in persistent volume to avoid re-downloads
        # Using /mnt/models instead of /root/.cache (which pip already populates)
        "HF_HOME": "/mnt/models",
        "TORCH_HOME": "/mnt/models/torch",
        "WHISPER_DOWNLOAD_ROOT": "/mnt/models/whisper",
        # Disable huggingface analytics
        "HF_HUB_DISABLE_TELEMETRY": "1",
    },
    secrets=[
        modal.Secret.from_name("openai-secret"),
        modal.Secret.from_name("rapidapi-secret"),
    ],
)
@modal.asgi_app()
@modal.concurrent(max_inputs=10)
def fastapi_app():
    """Serve FastAPI app via Modal ASGI."""

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    # Local imports
    from src.api.v1 import router as rapidapi_router
    from src.api.direct import router as direct_router
    from src.utils.logging_config import logger

    app = FastAPI(
        title="Speech Analysis API",
        description="IELTS Band Scoring System with Hybrid Metrics + LLM Evaluation",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS (adjust in prod)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(rapidapi_router, prefix="/api/v1", tags=["analysis_rapidapi"])
    app.include_router(direct_router, prefix="/api/direct/v1", tags=["analysis_direct"])

    @app.get("/", tags=["root"])
    async def root():
        return {
            "message": "Welcome to Speech Analysis API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("Unhandled exception", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app
