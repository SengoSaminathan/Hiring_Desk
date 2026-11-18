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
        assert eval_result["fit_score"] >= 30.0
        assert eval_result["match_level"] in ["High", "Medium", "Low"]
        assert "evidence_quotes" in eval_result
        assert len(eval_result["evidence_quotes"]) > 0


def test_candidate_deduplication_and_normalization():
    """Verify that db_service correctly normalizes URLs and names and detects duplicates."""
    from backend.app.services.db_service import db_service

    # URL normalization
    raw_url = "https://www.linkedin.com/in/john-doe-123/?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3A123"
    norm = db_service.normalize_url(raw_url)
    assert norm == "linkedin.com/in/john-doe-123"

    # Name normalization
    raw_name = "John Doe 3rd+ \n View profile"
    norm_name = db_service.normalize_name(raw_name)
    assert norm_name == "john doe"

    # Duplicate check
    known = {
        "urls": {"linkedin.com/in/john-doe-123"},
        "names": {"john doe"},
    }
    assert db_service.is_candidate_duplicate("https://linkedin.com/in/john-doe-123", "John Doe", known) is True
    assert db_service.is_candidate_duplicate("https://linkedin.com/in/jane-smith-456", "Jane Smith", known) is False


def test_ai_query_optimization_decision_layer():
    """Verify that ai_service decision layer pivots queries when saturation is detected."""
    from backend.app.services.ai_service import ai_service

    initial_query = '"Senior AI Engineer" Python FastAPI'
    role_title = "Senior AI Engineer"
    skills = ["Python", "FastAPI", "React", "Next.js"]

    # Attempt 1: Should pivot to a distinct query
    decision_1 = ai_service.optimize_sourcing_query(
        role_title=role_title,
        current_query=initial_query,
        mandatory_skills=skills,
        attempt=1,
        previous_queries=[initial_query],
    )
    assert decision_1["action"] == "pivot_query"
    assert "optimized_query" in decision_1
    assert decision_1["optimized_query"] != initial_query

    # Attempt 2: Should generate another distinct query not in previous
    prev = [initial_query, decision_1["optimized_query"]]
    decision_2 = ai_service.optimize_sourcing_query(
        role_title=role_title,
        current_query=decision_1["optimized_query"],
        mandatory_skills=skills,
        attempt=2,
        previous_queries=prev,
    )
    assert decision_2["action"] == "pivot_query"
    assert decision_2["optimized_query"] not in prev

    # Attempt > 3: Should gracefully stop saturation
    decision_stop = ai_service.optimize_sourcing_query(
        role_title=role_title,
        current_query=decision_2["optimized_query"],
        mandatory_skills=skills,
        attempt=4,
        previous_queries=prev,
    )
    assert decision_stop["action"] == "stop_saturation"
    assert "saturated" in decision_stop["explanation"].lower() or "talent pool" in decision_stop["explanation"].lower()


def test_strategic_queries_generation():
    """Verify that 3 distinct strategic search queries are generated (precision, lateral, domain)."""
    from backend.app.services.ai_service import ai_service

    queries = ai_service.generate_strategic_queries(
        job_title="Senior AI Engineer",
        mandatory_skills=["Python", "FastAPI", "PyTorch", "LangChain"],
    )
    assert len(queries) == 3
    ids = [q.id for q in queries]
    assert "precision" in ids
    assert "lateral" in ids
    assert "domain" in ids
    for q in queries:
        assert len(q.query.strip()) > 5
        assert q.label
        assert q.strategy_type


def test_seven_section_multi_factor_evaluation():
    """Verify that candidate evaluation produces itemized scores across all 7 profile sections."""
    from backend.app.services.ai_service import ai_service
    from backend.app.schemas.candidates import CandidateProfile
    from backend.app.schemas.jobs import StructuredJobCriteria, Criterion

    candidate = CandidateProfile(
        id="c_test_7sec",
        name="Alex Rivera",
        canonical_url="https://www.linkedin.com/in/alex-rivera",
        headline="Staff Machine Learning Engineer at Anthropic",
        current_company="Anthropic",
        location="San Francisco, CA",
        experience_years=8.0,
        skills=["Python", "PyTorch", "FastAPI", "Transformers"],
        about="Staff AI Engineer specializing in transformer model fine-tuning and inference pipelines.",
        experience_history=[
            {"role": "Staff AI Engineer", "company": "Anthropic", "dates": "2022 - Present", "description": "Trained scalable LLM inference pipelines."}
        ],
        education=[
            {"degree": "M.S. in Computer Science", "school": "Stanford University", "dates": "2016 - 2018"}
        ],
        certifications=[
            {"name": "AWS Certified Machine Learning Specialist", "issuer": "Amazon Web Services"}
        ],
        projects=[
            {"title": "Distributed LLM Engine", "description": "Ultra-fast transformer inference server in C++/Python.", "url": "https://github.com/alex/dist-llm"}
        ],
        recent_activity=[
            {"post_snippet": "Shared our new benchmark results on high-throughput model serving.", "engagement_type": "Post", "date": "2d"}
        ],
    )

    criteria = StructuredJobCriteria(
        job_title="Senior AI Engineer",
        seniority_level="Senior",
        min_years_experience=5.0,
        mandatory_skills=["Python", "PyTorch", "FastAPI"],
        preferred_skills=["Transformers"],
        criteria_list=[
            Criterion(category="skills", requirement="Python & PyTorch", is_mandatory=True, weight=1.0),
        ],
    )

    eval_res = ai_service.evaluate_candidate(candidate, criteria)
    assert eval_res.fit_score >= 50.0
    assert eval_res.section_scores is not None
    assert "experience" in eval_res.section_scores
    assert "skills" in eval_res.section_scores
    assert "about" in eval_res.section_scores
    assert "education" in eval_res.section_scores
    assert "certifications" in eval_res.section_scores
    assert "projects" in eval_res.section_scores
    assert "activity" in eval_res.section_scores


@pytest.mark.asyncio
async def test_upload_jd_endpoint():
    """Verify that uploading a JD document parses text and formulates structured criteria & strategic queries."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sample_jd_bytes = b"Job Title: Senior Backend Engineer\nWe are looking for a Senior Python Developer with 5+ years experience in FastAPI, Docker, and PostgreSQL. Location: San Francisco, CA."
        files = {
            "file": ("sample_job_desc.txt", sample_jd_bytes, "text/plain")
        }
        response = await client.post("/api/jobs/upload-jd", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "search_plan" in data
        assert "criteria" in data
        assert len(data["search_plan"]["strategic_queries"]) == 3
        assert "Senior Backend Engineer" in data["criteria"]["job_title"] or "Backend" in data["criteria"]["job_title"]


