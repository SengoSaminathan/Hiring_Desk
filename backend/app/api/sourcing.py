"""API routes for browser automation, LinkedIn sourcing, and candidate evaluation."""

import logging
import time
import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from backend.app.schemas.candidates import (
    CandidateProfile,
    EvaluateCandidatesRequest,
    EvaluateCandidatesResponse,
    EvaluatedCandidate,
    SearchRequest,
    SearchResponse,
)
from backend.app.schemas.jobs import StructuredJobCriteria
from backend.app.services.ai_service import ai_service
from backend.app.services.browser_service import browser_service
from backend.app.services.db_service import db_service

logger = logging.getLogger("hiring_desk.api_sourcing")
router = APIRouter(prefix="/api/sourcing", tags=["sourcing"])


class StartSessionRequest(BaseModel):
    keywords: str
    max_results: int = Field(default=6, ge=1, le=25)
    mode: str = "simulation"
    deep_scrape: bool = True
    browser_channel: Optional[str] = "chrome"


class StopSessionRequest(BaseModel):
    session_id: Optional[str] = None


class ResumeSessionRequest(BaseModel):
    session_id: str


@router.post("/start-session")
async def start_sourcing_session(request: StartSessionRequest, background_tasks: BackgroundTasks):
    """Starts a live or simulated sourcing session in the background with continuous progress tracking."""
    ts = int(time.time() * 1000)
    session_id = f"sess_{ts}_{uuid.uuid4().hex[:6]}"
    browser_service.tracker.create_session(
        session_id=session_id,
        mode=request.mode,
        query=request.keywords,
        max_results=request.max_results,
    )

    async def _execute_sourcing():
        try:
            if request.mode in ("simulation", "demo", "offline_demo"):
                await browser_service.search_linkedin(
                    keywords=request.keywords,
                    max_results=request.max_results,
                    mode=request.mode,
                    deep_scrape=request.deep_scrape,
                    session_id=session_id,
                    browser_channel=request.browser_channel or "chrome",
                )
            else:
                # Mode A ("autonomous") and Mode B ("live_linkedin") execute REAL live LinkedIn sourcing
                await browser_service.search_live_linkedin(
                    keywords=request.keywords,
                    max_results=request.max_results,
                    deep_scrape=request.deep_scrape,
                    browser_channel=request.browser_channel or "chrome",
                    session_id=session_id,
                )
        except Exception as e:
            logger.error("Error executing background sourcing session %s: %s", session_id, e)
            browser_service.tracker.update_session(
                session_id,
                state="failed",
                error=str(e),
                message=f"Sourcing error: {str(e)[:120]}",
            )

    background_tasks.add_task(_execute_sourcing)
    return {
        "session_id": session_id,
        "state": "initializing",
        "message": f"Sourcing session initialized in mode: {request.mode}",
    }


class OpenTabRequest(BaseModel):
    browser_channel: Optional[str] = "chrome"


@router.post("/open-linkedin-tab")
async def open_linkedin_tab(req: Optional[OpenTabRequest] = None):
    """Opens or focuses a LinkedIn tab in the headed browser."""
    try:
        channel = req.browser_channel if req else "chrome"
        res = await browser_service.open_linkedin_tab(browser_channel=channel)
        return res
    except Exception as e:
        logger.exception("Failed to open LinkedIn tab: %s", e)
        return {
            "status": "error",
            "message": f"Browser launch error: {str(e)}",
            "error_type": type(e).__name__,
        }


@router.post("/verify-screen")
async def verify_linkedin_screen(req: ResumeSessionRequest):
    """AI Agent inspects the browser screen to verify if LinkedIn is logged in."""
    res = await browser_service.verify_linkedin_screen(session_id=req.session_id)
    return res


@router.post("/resume-session")
async def resume_sourcing_session(req: ResumeSessionRequest):
    """Verifies LinkedIn login AND signals an active sourcing session to resume.
    
    This is the endpoint called when the user clicks "I've Logged In — Continue".
    It first verifies authentication, and if verified, also signals the background
    sourcing task to proceed (resume_on_success=True).
    """
    verification = await browser_service.verify_linkedin_screen(
        session_id=req.session_id,
        resume_on_success=True,
    )
    return verification


@router.get("/session/{session_id}")
async def get_session_status(session_id: str):
    """Retrieves real-time progress, status, candidates, and errors for an active sourcing session."""
    session_data = browser_service.tracker.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Sourcing session not found")
    return session_data


@router.post("/stop-session")
async def stop_sourcing_session(req: Optional[StopSessionRequest] = None):
    """Stops the active or specified sourcing session."""
    sid = req.session_id if req else None
    browser_service.tracker.stop_session(sid)
    return {"status": "stopped", "message": "Sourcing session marked for cancellation."}


@router.post("/linkedin-search", response_model=SearchResponse)
async def search_linkedin(request: SearchRequest):
    """Executes a Playwright search on LinkedIn, takes control of the UI, visits profiles, and persists to DB."""
    try:
        logger.info("Received LinkedIn search request for query: %s (deep_scrape=%s)", request.keywords, request.deep_scrape)
        candidates, search_url, status_msg = await browser_service.search_linkedin(
            keywords=request.keywords,
            max_results=request.max_results,
            mode=request.mode,
            deep_scrape=request.deep_scrape,
        )
        return SearchResponse(
            candidates=candidates,
            search_url=search_url,
            status="success" if candidates else "warning",
            message=status_msg,
        )
    except Exception as e:
        logger.error("Failed to execute LinkedIn search: %s", e)
        raise HTTPException(status_code=500, detail=f"Browser search failed: {str(e)}")


@router.post("/evaluate-candidates", response_model=EvaluateCandidatesResponse)
async def evaluate_candidates(request: EvaluateCandidatesRequest):
    """Evaluates candidate profiles against job criteria using Gemini AI with verbatim evidence and persists evaluations."""
    try:
        # Cast criteria if dictionary
        if isinstance(request.criteria, dict):
            criteria = StructuredJobCriteria(**request.criteria)
        else:
            criteria = request.criteria

        evaluations = ai_service.evaluate_candidates_batch(request.candidates, criteria)
        evaluated_list = [
            EvaluatedCandidate(candidate=c, evaluation=ev)
            for c, ev in zip(request.candidates, evaluations)
        ]

        # Persist evaluations into SQLite database for persistent reporting
        for c, ev in zip(request.candidates, evaluations):
            try:
                db_service.save_evaluation({
                    "candidate_id": c.id or c.canonical_url,
                    "canonical_url": c.canonical_url,
                    "job_title": criteria.job_title,
                    "fit_score": ev.fit_score,
                    "completeness_score": ev.completeness_score,
                    "match_level": ev.match_level,
                    "justification_summary": ev.justification_summary,
                    "evidence_quotes": [q.model_dump() if hasattr(q, "model_dump") else q.dict() for q in ev.evidence_quotes],
                    "missing_criteria": ev.missing_criteria,
                })
            except Exception as err:
                logger.warning("Could not persist evaluation to DB: %s", err)

        # Sort candidate shortlist by fit_score descending
        evaluated_list.sort(key=lambda x: x.evaluation.fit_score, reverse=True)

        return EvaluateCandidatesResponse(evaluated_candidates=evaluated_list)
    except Exception as e:
        logger.error("Failed to evaluate candidates: %s", e)
        raise HTTPException(status_code=500, detail=f"Candidate evaluation failed: {str(e)}")


@router.get("/candidates")
async def get_stored_candidates(limit: int = 50):
    """Retrieves all harvested candidate profiles stored in the local SQLite database."""
    candidates = db_service.get_all_candidates(limit=limit)
    return {"total": len(candidates), "candidates": candidates}


@router.get("/report")
async def get_sourcing_report():
    """Generates an executive report of candidates, fit scores, and shortlist statistics from SQLite."""
    report = db_service.get_sourcing_report()
    return report


@router.post("/check-auth")
async def check_auth():
    """Checks whether the user has signed into LinkedIn in the active browser."""
    status = await browser_service.check_auth_status()
    return status


@router.post("/open-login")
async def open_login():
    """Opens LinkedIn login page in headed Chromium browser for recruiter login."""
    status = await browser_service.open_login_window()
    return status


@router.post("/close-browser")
async def close_browser():
    """Cleanly closes any open Playwright Chromium browser sessions."""
    await browser_service.close_browser()
    return {"status": "closed", "message": "Playwright browser session closed cleanly."}
