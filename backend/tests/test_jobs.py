"""Tests for the Jobs analysis API endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

SAMPLE_JD = """
Senior Frontend Engineer (React & Next.js)

We are looking for a Senior Frontend Engineer with 5+ years of experience building web applications.
You will lead our frontend architecture and mentor team members.

Requirements:
- 5+ years of experience with modern JavaScript, React, and Next.js.
- Strong proficiency in Tailwind CSS and state management.
- Experience with REST APIs, GraphQL, and performance optimization.
- Excellent communication and leadership skills.
"""


@pytest.mark.asyncio
async def test_analyze_job_endpoint():
    """Verify that analyzing a raw JD returns structured criteria and a search plan."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/jobs/analyze", json={"raw_jd": SAMPLE_JD})
        assert response.status_code == 200
        data = response.json()

        assert "criteria" in data
        assert "search_plan" in data

        criteria = data["criteria"]
        assert "job_title" in criteria
        assert criteria["min_years_experience"] == 5.0
        assert "React" in criteria["mandatory_skills"] or "JavaScript" in criteria["mandatory_skills"]

        search_plan = data["search_plan"]
        assert "linkedin_keywords" in search_plan
        assert "xray_query" in search_plan
        assert len(search_plan["target_skills"]) > 0
