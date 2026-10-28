"""API routes for Job Descriptions, criteria extraction, and search query planning."""

from fastapi import APIRouter, HTTPException
from backend.app.schemas.jobs import AnalyzeJobRequest, AnalyzeJobResponse
from backend.app.services.ai_service import ai_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/analyze", response_model=AnalyzeJobResponse)
async def analyze_job(request: AnalyzeJobRequest):
    """Parses a raw Job Description into structured criteria and generates an optimized search plan."""
    try:
        response = ai_service.analyze_job_description(request.raw_jd)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze job description: {str(e)}")
