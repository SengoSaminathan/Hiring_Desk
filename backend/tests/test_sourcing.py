"""Tests for LinkedIn Sourcing and Candidate Evaluation endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.schemas.candidates import CandidateProfile
from backend.app.schemas.jobs import Criterion, StructuredJobCriteria


@pytest.mark.asyncio
async def test_search_linkedin_endpoint():
    """Verify that LinkedIn search endpoint returns candidates."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "keywords": "Senior React Engineer Next.js Tailwind",
            "max_results": 4,
            "mode": "simulation",
        }
        response = await client.post("/api/sourcing/linkedin-search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert len(data["candidates"]) > 0
        assert "search_url" in data
        first_candidate = data["candidates"][0]
        assert "name" in first_candidate
        assert "headline" in first_candidate
        assert "canonical_url" in first_candidate


@pytest.mark.asyncio
async def test_sourcing_session_lifecycle():
    """Verify background session initialization, progress querying, and stop signaling."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Start session
        start_payload = {
            "keywords": "Staff Frontend Lead",
            "max_results": 3,
            "mode": "simulation",
        }
        res_start = await client.post("/api/sourcing/start-session", json=start_payload)
        assert res_start.status_code == 200
        start_data = res_start.json()
        assert "session_id" in start_data
        session_id = start_data["session_id"]
        assert start_data["state"] == "initializing"

        # 2. Query session status
        res_poll = await client.get(f"/api/sourcing/session/{session_id}")
        assert res_poll.status_code == 200
        poll_data = res_poll.json()
        assert poll_data["session_id"] == session_id
        assert poll_data["state"] in ["initializing", "launching_browser", "searching", "extracting", "completed"]

        # 3. Stop session
        res_stop = await client.post("/api/sourcing/stop-session", json={"session_id": session_id})
        assert res_stop.status_code == 200
        assert res_stop.json()["status"] == "stopped"

        # 4. Verify session reflects stopped or completed
        res_poll_after = await client.get(f"/api/sourcing/session/{session_id}")
        assert res_poll_after.status_code == 200
        assert res_poll_after.json()["should_stop"] is True or res_poll_after.json()["state"] in ["stopped", "completed"]



@pytest.mark.asyncio
async def test_evaluate_candidates_endpoint():
    """Verify that evaluating candidates against criteria returns fit scores and evidence."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        criteria_payload = {
            "job_title": "Senior Frontend Engineer",
            "seniority_level": "Senior",
            "min_years_experience": 5.0,
            "mandatory_skills": ["React", "Next.js", "Tailwind CSS"],
            "preferred_skills": ["WebSockets"],
            "criteria_list": [
                {"category": "skills", "requirement": "Proficiency in React", "is_mandatory": True, "weight": 1.0},
                {"category": "skills", "requirement": "Proficiency in Next.js", "is_mandatory": True, "weight": 1.0},
            ],
        }
        candidates_payload = [
            {
                "id": "c_1",
                "name": "Sarah Chen",
                "canonical_url": "https://www.linkedin.com/in/sarah-chen",
                "headline": "Staff Frontend Engineer at Stripe | React, Next.js, WebSockets",
                "current_company": "Stripe",
                "location": "San Francisco, CA",
                "experience_years": 7.0,
                "skills": ["React", "Next.js", "WebSockets"],
                "raw_snippet": "Frontend Lead architecting Next.js dashboards.",
            }
        ]

        payload = {
            "candidates": candidates_payload,
            "criteria": criteria_payload,
        }
        response = await client.post("/api/sourcing/evaluate-candidates", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "evaluated_candidates" in data
        assert len(data["evaluated_candidates"]) == 1

        eval_result = data["evaluated_candidates"][0]["evaluation"]
        assert "fit_score" in eval_result
        assert eval_result["fit_score"] >= 50.0
        assert eval_result["match_level"] in ["High", "Medium", "Low"]
        assert "evidence_quotes" in eval_result
        assert len(eval_result["evidence_quotes"]) > 0
