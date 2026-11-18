"""API routes for browser automation, LinkedIn sourcing, and candidate evaluation."""

import logging
import time
import uuid
from typing import List, Optional
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


import os

class StartSessionRequest(BaseModel):
    keywords: str
    max_results: int = Field(default=10, ge=1, le=50)
    mode: str = "simulation"
    deep_scrape: bool = True
    browser_channel: Optional[str] = "chrome"
    account_id: Optional[str] = "acc_chrome"
    role_title: Optional[str] = None
    mandatory_skills: Optional[List[str]] = None
    location: Optional[str] = None
    preferred_locations: Optional[List[str]] = None


class StopSessionRequest(BaseModel):
    session_id: Optional[str] = None


class ResumeSessionRequest(BaseModel):
    session_id: str


@router.get("/accounts")
async def get_accounts():
    """Returns available LinkedIn accounts and session status for recruiter selection."""
    chrome_profile = os.path.abspath(os.path.join("data", "browser_profile_chrome"))
    edge_profile = os.path.abspath(os.path.join("data", "browser_profile_edge"))
    
    return [
        {
            "id": "acc_chrome",
            "name": "HR Recruiter (Primary)",
            "identifier": "recruiter.primary@company.internal",
            "browser": "Google Chrome",
            "channel": "chrome",
            "status": "Active Session" if os.path.exists(chrome_profile) else "Ready to Connect",
            "has_session": os.path.exists(chrome_profile),
            "is_default": True,
        },
        {
            "id": "acc_edge",
            "name": "HR Talent Lead",
            "identifier": "talent.lead@company.internal",
            "browser": "Microsoft Edge",
            "channel": "msedge",
            "status": "Session Saved" if os.path.exists(edge_profile) else "Ready to Connect",
            "has_session": os.path.exists(edge_profile),
            "is_default": False,
        },
        {
            "id": "acc_sandbox",
            "name": "Chromium Sandbox Profile",
            "identifier": "sandbox.test@isolated.local",
            "browser": "Chromium Sandbox",
            "channel": "chromium",
            "status": "Isolated Environment",
            "has_session": False,
            "is_default": False,
        },
    ]


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

    # Resolve active role, location, and preferred_locations from active job in SQLite if missing
    active_role = request.role_title
    active_pref_locs = request.preferred_locations or []
    active_loc = request.location
    active_skills = request.mandatory_skills or []

    if not active_role or active_role == "Software Engineer" or (not active_pref_locs and not active_loc):
        job = None
        if active_role and active_role != "Software Engineer":
            job = db_service.get_job_by_title_or_id(active_role)
        if not job:
            all_jobs = db_service.get_all_jobs(limit=1)
            if all_jobs:
                job = all_jobs[0]
        if job:
            if not active_role or active_role == "Software Engineer":
                active_role = job.get("job_title") or active_role
            if not active_pref_locs:
                active_pref_locs = job.get("preferred_locations") or []
            if not active_loc:
                active_loc = job.get("location") or job.get("city")
            if not active_skills:
                active_skills = job.get("mandatory_skills") or []

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
                    role_title=active_role,
                    mandatory_skills=active_skills,
                    preferred_locations=active_pref_locs,
                    location=active_loc,
                )
            else:
                # Mode A ("autonomous") and Mode B ("live_linkedin") execute REAL live LinkedIn sourcing
                await browser_service.search_live_linkedin(
                    keywords=request.keywords,
                    max_results=request.max_results,
                    deep_scrape=request.deep_scrape,
                    browser_channel=request.browser_channel or "chrome",
                    session_id=session_id,
                    role_title=active_role,
                    mandatory_skills=active_skills,
                    preferred_locations=active_pref_locs,
                    location=active_loc,
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
    """Evaluates candidate profiles against role requirements.
    Supports multi-role evaluation where candidates are evaluated against their designated target role requisition,
    or uniform evaluation when evaluating for a single active role."""
    from collections import defaultdict

    try:
        # Cast criteria if dictionary
        if isinstance(request.criteria, dict):
            default_criteria = StructuredJobCriteria(**request.criteria)
        else:
            default_criteria = request.criteria

        evaluated_list: List[EvaluatedCandidate] = []
        is_single_candidate = len(request.candidates) == 1

        # Group candidates by target role criteria
        role_groups: Dict[str, Tuple[StructuredJobCriteria, List[Any]]] = {}

        for c in request.candidates:
            cand_role_name = getattr(c, "target_role", None)
            crit = default_criteria

            # In multi-candidate evaluations, look up specific role requisition if assigned
            if not is_single_candidate and cand_role_name and cand_role_name.strip():
                is_active_role = bool(default_criteria.job_title and cand_role_name.strip().lower() == default_criteria.job_title.strip().lower())
                matched_job = db_service.get_job_by_title_or_id(cand_role_name)
                if matched_job:
                    # Respect caller's explicitly passed active locations & requirements
                    pref_locs = (default_criteria.preferred_locations if (is_active_role and default_criteria.preferred_locations)
                                 else (matched_job.get("preferred_locations") or default_criteria.preferred_locations or []))
                    loc_val = (default_criteria.location if (is_active_role and default_criteria.location)
                               else (matched_job.get("location") or default_criteria.location))

                    crit = StructuredJobCriteria(
                        job_title=matched_job.get("job_title", cand_role_name),
                        seniority_level=matched_job.get("seniority_level", "Senior"),
                        min_years_experience=matched_job.get("min_years_experience") or default_criteria.min_years_experience,
                        mandatory_skills=default_criteria.mandatory_skills if (is_active_role and default_criteria.mandatory_skills) else (matched_job.get("mandatory_skills") or default_criteria.mandatory_skills or []),
                        preferred_skills=default_criteria.preferred_skills if (is_active_role and default_criteria.preferred_skills) else (matched_job.get("preferred_skills") or default_criteria.preferred_skills or []),
                        technologies=matched_job.get("technologies", []),
                        preferred_locations=pref_locs,
                        location=loc_val,
                        raw_jd=matched_job.get("raw_jd", ""),
                    )

            key = crit.job_title or "Target Role"
            if key not in role_groups:
                role_groups[key] = (crit, [])
            role_groups[key][1].append(c)

        # Evaluate each role group
        for role_name, (group_crit, group_candidates) in role_groups.items():
            try:
                evaluations = ai_service.evaluate_candidates_batch(group_candidates, group_crit)
            except Exception as eval_err:
                logger.warning(
                    "Batch evaluation for role '%s' encountered error: %s. Using high-precision deterministic evaluator fallback.",
                    role_name,
                    eval_err,
                )
                evaluations = [ai_service._deterministic_evaluator(c, group_crit) for c in group_candidates]

            # Persist evaluations into database
            for c, ev in zip(group_candidates, evaluations):
                c.target_role = group_crit.job_title
                try:
                    db_service.save_evaluation({
                        "candidate_id": c.id or c.canonical_url,
                        "canonical_url": c.canonical_url,
                        "job_title": group_crit.job_title,
                        "fit_score": ev.fit_score,
                        "completeness_score": ev.completeness_score,
                        "evaluation_coverage": ev.evaluation_coverage,
                        "match_level": ev.match_level,
                        "domain_relevance": ev.domain_relevance,
                        "domain_relevance_notes": ev.domain_relevance_notes,
                        "location_compatibility": ev.location_compatibility,
                        "justification_summary": ev.justification_summary,
                        "evidence_quotes": [q.model_dump() if hasattr(q, "model_dump") else q.dict() for q in ev.evidence_quotes],
                        "missing_criteria": ev.missing_criteria,
                        "section_scores": ev.section_scores,
                        "category_evaluations": {
                            k: (v.model_dump() if hasattr(v, "model_dump") else v) for k, v in ev.category_evaluations.items()
                        },
                    })
                except Exception as err:
                    logger.warning("Could not persist evaluation to DB: %s", err)

                evaluated_list.append(EvaluatedCandidate(candidate=c, evaluation=ev))

        # Sort candidate shortlist by fit_score descending
        evaluated_list.sort(key=lambda x: x.evaluation.fit_score, reverse=True)

        return EvaluateCandidatesResponse(evaluated_candidates=evaluated_list)
    except Exception as e:
        logger.error("Failed to evaluate candidates: %s", e)
        # Even on critical unexpected failure, provide deterministic evaluations rather than blocking HR!
        try:
            fallback_evals = [ai_service._deterministic_evaluator(c, default_criteria) for c in request.candidates]
            evaluated_list = [
                EvaluatedCandidate(candidate=c, evaluation=ev)
                for c, ev in zip(request.candidates, fallback_evals)
            ]
            return EvaluateCandidatesResponse(evaluated_candidates=evaluated_list)
        except Exception:
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


class UpdateCandidateStatusRequest(BaseModel):
    status: str


@router.get("/db-status")
async def get_database_status():
    """Returns connectivity and stats for local SQLite and remote Supabase database."""
    return db_service.get_database_status()


@router.post("/sync-supabase")
async def sync_supabase():
    """Pushes all stored candidate profiles and match evaluations from local SQLite to Supabase."""
    res = db_service.sync_local_to_supabase()
    return res


@router.patch("/candidates/{candidate_id}/status")
async def update_candidate_status(candidate_id: str, request: UpdateCandidateStatusRequest):
    """Updates candidate status across local SQLite and Supabase."""
    success = db_service.update_candidate_status(candidate_id, request.status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")
    return {"status": "updated", "candidate_id": candidate_id, "new_status": request.status}


@router.delete("/candidates/{candidate_id}")
async def delete_candidate(candidate_id: str):
    """Deletes candidate from local SQLite and Supabase."""
    success = db_service.delete_candidate(candidate_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")
    return {"status": "deleted", "candidate_id": candidate_id}


@router.delete("/candidates")
async def clear_all_candidates():
    """Clears all stored candidates and evaluations from local SQLite and Supabase."""
    success = db_service.clear_all_candidates()
    return {"status": "cleared", "success": success}
