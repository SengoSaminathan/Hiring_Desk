"""API routes for automated LinkedIn candidate outreach and message generation."""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.ai_service import ai_service
from backend.app.services.browser_service import browser_service
from backend.app.services.db_service import db_service

logger = logging.getLogger("hiring_desk.api_outreach")
router = APIRouter(prefix="/api/outreach", tags=["outreach"])


class GenerateOutreachRequest(BaseModel):
    candidate_name: str
    canonical_url: Optional[str] = None
    headline: Optional[str] = ""
    skills: Optional[List[str]] = None
    current_company: Optional[str] = ""
    target_role: Optional[str] = "Senior Engineer"
    company_name: Optional[str] = "Our Company"
    company_details: Optional[str] = ""
    recruiter_name: Optional[str] = "Talent Acquisition Team"
    tone: Optional[str] = "formal"
    force_deterministic: Optional[bool] = False


class GenerateOutreachResponse(BaseModel):
    subject: str
    message_body: str
    connection_note: str


class CandidateOutreachItem(BaseModel):
    candidate_id: Optional[str] = None
    canonical_url: str
    candidate_name: Optional[str] = "Candidate"
    message_body: str
    connection_note: Optional[str] = None


class SendOutreachBatchRequest(BaseModel):
    candidates: List[CandidateOutreachItem]
    browser_channel: Optional[str] = "chrome"
    mode: Optional[str] = "live"  # "live" or "simulation"


class UpdateOutreachStatusRequest(BaseModel):
    outreach_status: str
    outreach_message: Optional[str] = None
    outreach_method: Optional[str] = None


@router.post("/generate", response_model=GenerateOutreachResponse)
def generate_outreach(request: GenerateOutreachRequest):
    """Generates a formal, personalized hiring outreach message and a 300-char connection note."""
    try:
        candidate_data = {
            "name": request.candidate_name,
            "headline": request.headline,
            "skills": request.skills or [],
            "current_company": request.current_company,
        }
        res = ai_service.generate_outreach_message(
            candidate=candidate_data,
            role_title=request.target_role or "Key Engineering Role",
            company_name=request.company_name or "Our Company",
            company_details=request.company_details or "",
            recruiter_name=request.recruiter_name or "Talent Acquisition Team",
            tone=request.tone or "formal",
            force_deterministic=request.force_deterministic or False,
        )
        return GenerateOutreachResponse(
            subject=res.get("subject", "Hiring Opportunity"),
            message_body=res.get("message_body", ""),
            connection_note=res.get("connection_note", ""),
        )
    except Exception as e:
        logger.error("Failed to generate outreach message: %s", e)
        raise HTTPException(status_code=500, detail=f"Outreach generation failed: {str(e)}")


@router.post("/send")
def send_outreach_batch(request: SendOutreachBatchRequest, background_tasks: BackgroundTasks):
    """Dispatches autonomous browser agent to deliver formal outreach messages to selected candidates."""
    if not request.candidates:
        raise HTTPException(status_code=400, detail="No candidates provided for outreach.")

    ts = int(time.time() * 1000)
    session_id = f"outreach_{ts}_{uuid.uuid4().hex[:6]}"

    browser_service.tracker.create_session(
        session_id=session_id,
        mode=request.mode or "live",
        query="outreach_batch",
        max_results=len(request.candidates),
    )

    async def _execute_batch_outreach():
        logger.info("Starting background outreach batch %s for %d candidates", session_id, len(request.candidates))
        success_count = 0
        total = len(request.candidates)

        for idx, item in enumerate(request.candidates):
            progress_pct = int(((idx) / max(total, 1)) * 100)
            browser_service.tracker.update_session(
                session_id,
                state="sending",
                progress=progress_pct,
                message=f"Contacting ({idx + 1}/{total}): {item.candidate_name}...",
            )

            try:
                result = await browser_service.send_linkedin_outreach(
                    candidate_url=item.canonical_url,
                    message_body=item.message_body,
                    connection_note=item.connection_note,
                    candidate_name=item.candidate_name,
                    browser_channel=request.browser_channel or "chrome",
                    session_id=session_id,
                    mode=request.mode or "live",
                )

                if result.get("status") == "success":
                    success_count += 1
                elif result.get("status") == "auth_required":
                    browser_service.tracker.update_session(
                        session_id,
                        state="auth_required",
                        message=result.get("message", "Authentication required in browser."),
                    )
                    return

            except Exception as item_err:
                logger.error("Error sending outreach to %s: %s", item.canonical_url, item_err)

            # Polite anti-detection pause between profiles
            if idx < total - 1:
                await asyncio.sleep(2.5)

        browser_service.tracker.update_session(
            session_id,
            state="completed",
            progress=100,
            message=f"🎉 Batch Outreach Complete! Successfully contacted {success_count} of {total} candidates.",
        )

    background_tasks.add_task(_execute_batch_outreach)

    return {
        "session_id": session_id,
        "state": "initializing",
        "total": len(request.candidates),
        "message": f"Autonomous outreach agent initialized for {len(request.candidates)} candidates.",
    }


@router.get("/session/{session_id}")
async def get_outreach_session_status(session_id: str):
    """Retrieves live execution progress and delivery status for active outreach session."""
    session_data = browser_service.tracker.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Outreach session not found")
    return session_data


@router.patch("/candidates/{candidate_id}")
async def update_candidate_outreach_status(candidate_id: str, request: UpdateOutreachStatusRequest):
    """Manually updates a candidate's outreach status, delivery method, and recorded message."""
    success = db_service.update_candidate_outreach(
        candidate_id=candidate_id,
        outreach_status=request.outreach_status,
        outreach_message=request.outreach_message,
        outreach_method=request.outreach_method,
    )
    if not success:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")
    return {"status": "updated", "candidate_id": candidate_id, "outreach_status": request.outreach_status}
