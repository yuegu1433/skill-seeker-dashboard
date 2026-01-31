"""Skill Management Center - FastAPI Application Entry Point.

This module provides the main FastAPI application instance with all
necessary configurations, middleware, and route registrations.
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

# Import configurations
from app.core.config import settings

# Import API routes
from app.api.routes import skill_routes

# Import WebSocket handlers
from app.api.websocket import skill_websocket

# Import managers for initialization
from app.skill.manager import SkillManager
from app.skill.event_manager import SkillEventManager
from app.skill.editor import SkillEditor
from app.skill.version_manager import SkillVersionManager
from app.skill.importer import SkillImporter
from app.skill.analytics import SkillAnalytics

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("skill_management.log")
    ] if not settings.LOG_TO_FILE else [logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Skill Management Center...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database URL: {settings.DATABASE_URL[:20]}...")

    # Initialize managers
    try:
        app.state.skill_manager = SkillManager()
        app.state.event_manager = SkillEventManager()
        app.state.editor = SkillEditor()
        app.state.version_manager = SkillVersionManager()
        app.state.importer = SkillImporter()
        app.state.analytics = SkillAnalytics()

        logger.info("All managers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize managers: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Skill Management Center...")


# Create FastAPI application
app = FastAPI(
    title="Skill Management Center API",
    description="Enterprise-grade skill management system with version control, analytics, and real-time collaboration",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPException"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error" if not settings.DEBUG else str(exc),
                "type": "Exception"
            }
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Skill Management Center API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "status": "operational"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2026-02-01T00:00:00Z",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


# Include API routes
app.include_router(
    skill_routes.router,
    prefix="/api/v1",
    tags=["skills"]
)

# Include WebSocket routes
app.add_api_websocket_route(
    "/ws/skills/status",
    skill_websocket.skill_status_websocket,
    name="skill_status"
)

app.add_api_websocket_route(
    "/ws/skills/execution",
    skill_websocket.skill_execution_websocket,
    name="skill_execution"
)

app.add_api_websocket_route(
    "/ws/skills/events",
    skill_websocket.skill_event_websocket,
    name="skill_events"
)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
