"""Health check and runtime diagnostic API routes."""

from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """Returns application health and configuration metadata."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "gemini_model": settings.GEMINI_MODEL,
        "has_google_api_key": bool(settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "your_gemini_api_key_here"),
        "playwright_headless": settings.PLAYWRIGHT_HEADLESS,
    }
