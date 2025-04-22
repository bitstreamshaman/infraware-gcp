from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import uuid
from datetime import datetime

from .config import settings
from .routers import process, status, diagrams, confirmation, generation
from .models.api import HealthResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NL to IaC API",
    description="API for converting natural language to Infrastructure as Code",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(process.router, tags=["Process"])
app.include_router(status.router, tags=["Status"])
app.include_router(diagrams.router, tags=["Diagrams"])
app.include_router(confirmation.router, tags=["Confirmation"])
app.include_router(generation.router, tags=["Generation"])

@app.get("/", response_model=HealthResponse, tags=["Health"])
async def root():
    """Root endpoint that returns service status"""
    return {
        "status": "operational",
        "version": app.version,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "operational",
        "version": app.version,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )