"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.api import router as old_router
from src.api.v1 import router as rapidapi_router
from src.api.direct import router as direct_router
from src.utils.logging_config import logger

# Create FastAPI app
app = FastAPI(
    title="Speech Analysis API",
    description="IELTS Band Scoring System with Hybrid Metrics + LLM Evaluation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# RapidAPI endpoint
app.include_router(rapidapi_router, prefix="/api/v1", tags=["analysis_rapidapi"])

# Direct access endpoint
app.include_router(direct_router, prefix="/api/direct/v1", tags=["analysis_direct"])

# Legacy endpoint (if still needed for backward compatibility)
app.include_router(old_router, prefix="/api/legacy", tags=["analysis_legacy"])

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Speech Analysis API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "rapidapi": "/api/v1/health",
            "direct": "/api/direct/v1/health",
            "legacy": "/api/legacy/health"
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

