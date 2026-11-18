import pytest
import urllib.parse
from backend.app.services.ai_service import ai_service

def test_clean_location_tokens_strips_work_modes():
    raw_input = ["Hybrid, On-site, or Remote", "Dubai", "Abu Dhabi (On-site)", "Remote"]
    cleaned = ai_service._clean_location_tokens(raw_input)
    assert "Dubai" in cleaned
    assert "Abu Dhabi" in cleaned
    assert not any("hybrid" in c.lower() for c in cleaned)
    assert not any("remote" in c.lower() for c in cleaned)
    assert not any("on-site" in c.lower() for c in cleaned)

def test_build_location_clause_uae_expansion():
    clause = ai_service._build_location_clause(preferred_locations=["Dubai"])
    assert clause == ' AND ("Dubai" OR "UAE")'

    clause_with_garbage = ai_service._build_location_clause(
        preferred_locations=["Hybrid, On-site, or Remote", "Dubai"]
    )
    assert clause_with_garbage == ' AND ("Dubai" OR "UAE")'
    assert "Hybrid" not in clause_with_garbage

def test_generate_strategic_queries_lean_format():
    queries = ai_service.generate_strategic_queries(
        job_title="Senior AI Lead",
        mandatory_skills=["Python", "Machine Learning", "Deep Learning", "LLM", "RAG", "Vector Database", "LangChain"],
        technologies=["Azure", "AWS"],
        preferred_locations=["Dubai"],
    )
    assert len(queries) == 3
    for q in queries:
        # Must include location
        assert '("Dubai" OR "UAE")' in q.query
        # Must have at most ONE 'AND' operator connecting role/domain to location
        assert q.query.count(" AND ") <= 1
        # Must NOT contain standalone seniority keyword chains that choke LinkedIn
        assert "Lead OR Senior OR Head OR Architect" not in q.query
        # Must NOT contain work modes
        assert "Hybrid" not in q.query
        assert "On-site" not in q.query
        assert "Remote" not in q.query

    # Query 1 (Precision Stack): Core domain anchor + location (no restrictive title requirement)
    q1 = queries[0]
    assert "AI" in q1.query or "Machine Learning" in q1.query or "ML" in q1.query

    # Query 2 (Compound Titles): Compound role options with titles inside the same OR group
    q2 = queries[1]
    assert "AI Lead" in q2.query or "AI Architect" in q2.query or "AI Engineer" in q2.query

    # Query 3 (Specialized Tech): Technical skills + location
    q3 = queries[2]
    assert "LLM" in q3.query or "Generative AI" in q3.query or "Deep Learning" in q3.query

def test_optimize_sourcing_query_no_results_progressive_relaxation():
    current_q = '("AI" OR "Artificial Intelligence" OR "Machine Learning") AND (Lead OR Senior OR Head OR Architect OR Principal) AND ("Dubai" OR "UAE")'
    pivoted_1 = ai_service.optimize_sourcing_query(
        role_title="Senior AI Lead",
        current_query=current_q,
        attempt=1,
        reason="no_results",
    )
    assert pivoted_1["action"] == "pivot_query"
    assert pivoted_1["strategy"] == "domain_only_relaxation"
    assert '("Dubai" OR "UAE")' in pivoted_1["optimized_query"]
    assert "Lead OR Senior" not in pivoted_1["optimized_query"]
    assert '("AI" OR "Machine Learning")' in pivoted_1["optimized_query"]

    # Attempt 2 relaxes to core anchor in quotes + location (e.g. "AI" AND ("Dubai" OR "UAE"))
    pivoted_2 = ai_service.optimize_sourcing_query(
        role_title="Senior AI Lead",
        current_query=current_q,
        attempt=2,
        reason="no_results",
    )
    assert pivoted_2["strategy"] == "core_anchor_relaxation"
    assert pivoted_2["optimized_query"] == '"AI" AND ("Dubai" OR "UAE")'

    # Attempt 3 relaxes to plain recruiter keywords without quotes/parentheses
    pivoted_3 = ai_service.optimize_sourcing_query(
        role_title="Senior AI Lead",
        current_query=current_q,
        attempt=3,
        reason="no_results",
        preferred_locations=["Dubai"],
    )
    assert pivoted_3["strategy"] == "plain_keyword_relaxation"
    assert "AI Dubai" in pivoted_3["optimized_query"]

def test_search_url_encoding_uses_percent_twenty():
    query = '("AI" OR "Machine Learning") AND ("Dubai" OR "UAE")'
    encoded = urllib.parse.quote(query.strip())
    # %20 must be used for spaces, NOT '+'
    assert "+" not in encoded
    assert "%20" in encoded


def test_deterministic_jd_parser_preserves_location_and_queries():
    """Verify that deterministic JD analysis extracts location and generates queries with location filters."""
    raw_jd = """
    LEAD UI / FRONTEND ENGINEER
    Location: Dubai, UAE / Hybrid / Remote.
    Work arrangement: Full-time.
    We are looking for a Lead UI / Frontend Engineer with 7+ years of experience in React, Next.js, and TypeScript.
    """
    res = ai_service._deterministic_jd_parser(raw_jd)
    assert res.criteria.preferred_locations == ["Dubai", "UAE"]
    assert res.criteria.city == "Dubai"
    assert res.criteria.country == "UAE"
    assert len(res.search_plan.strategic_queries) == 3
    for q in res.search_plan.strategic_queries:
        assert '("Dubai" OR "UAE")' in q.query


def test_save_candidate_no_unbound_local_error():
    """Verify that db_service.save_candidate does not raise UnboundLocalError when company/location are not pre-set."""
    from backend.app.services.db_service import db_service
    test_cand = {
        "id": "cand_test_regress_01",
        "name": "Ashwin kp • 3rd+ Connect",
        "headline": "React Developer | Frontend Engineer • Bangalore • Follow",
        "canonical_url": "https://www.linkedin.com/in/ashwin-kp-parakkadavu/",
    }
    try:
        saved_id = db_service.save_candidate(test_cand)
        assert saved_id == "cand_test_regress_01"
        cand = db_service.get_candidate_by_id_or_url("cand_test_regress_01")
        assert cand is not None
        assert cand["name"] == "Ashwin kp"
    finally:
        db_service.delete_candidate("cand_test_regress_01")


def test_browser_service_has_update_overlay():
    """Verify that browser_service and its underlying engine provide _update_overlay for HUD tracking."""
    from backend.app.services.browser_service import browser_service
    assert hasattr(browser_service, "_update_overlay") or hasattr(browser_service._engine, "_update_overlay")


def test_build_location_clause_chennai_excludes_india():
    """Verify that Chennai/Tamil Nadu searches do not dilute with nationwide 'India' catch-all."""
    clause = ai_service._build_location_clause(preferred_locations=["Chennai", "Tamil Nadu", "India"])
    assert '("Chennai" OR "Madras" OR "Tamil Nadu" OR "Tamilnadu")' in clause
    assert '"India"' not in clause


def test_build_location_clause_coimbatore_excludes_india():
    """Verify that Coimbatore/Tamil Nadu searches do not dilute with nationwide 'India' catch-all."""
    clause = ai_service._build_location_clause(preferred_locations=["Coimbatore", "Tamil Nadu", "India"])
    assert '("Coimbatore" OR "Kovai" OR "Tamil Nadu" OR "Tamilnadu")' in clause
    assert '"India"' not in clause


def test_optimize_sourcing_query_chennai_preserves_location_across_all_attempts():
    """Verify that when 0 results occur, progressive relaxation NEVER drops Chennai location."""
    current_q = '("Product Manager" OR "Technical Product Manager") AND ("Chennai" OR "Madras" OR "Tamil Nadu")'
    
    # Attempt 1: domain_only_relaxation
    r1 = ai_service.optimize_sourcing_query(
        role_title="Senior Product Manager",
        current_query=current_q,
        attempt=1,
        reason="no_results",
        preferred_locations=["Chennai", "Tamil Nadu"],
    )
    assert r1["action"] == "pivot_query"
    assert "Chennai" in r1["optimized_query"]
    assert "Tamil Nadu" in r1["optimized_query"]

    # Attempt 2: core_anchor_relaxation
    r2 = ai_service.optimize_sourcing_query(
        role_title="Senior Product Manager",
        current_query=current_q,
        attempt=2,
        reason="no_results",
        preferred_locations=["Chennai", "Tamil Nadu"],
    )
    assert r2["action"] == "pivot_query"
    assert "Chennai" in r2["optimized_query"]
    assert "Product Manager" in r2["optimized_query"]

    # Attempt 3: plain_keyword_relaxation
    r3 = ai_service.optimize_sourcing_query(
        role_title="Senior Product Manager",
        current_query=current_q,
        attempt=3,
        reason="no_results",
        preferred_locations=["Chennai"],
    )
    assert r3["action"] == "pivot_query"
    assert "Chennai" in r3["optimized_query"]
    assert "Product Manager" in r3["optimized_query"]


def test_optimize_sourcing_query_coimbatore_preserves_location_across_all_attempts():
    """Verify that progressive relaxation NEVER drops Coimbatore location."""
    current_q = '("Fullstack Engineer" OR "Full Stack Developer") AND ("Coimbatore" OR "Kovai" OR "Tamil Nadu")'
    
    for att in [1, 2, 3]:
        r = ai_service.optimize_sourcing_query(
            role_title="Senior Fullstack Engineer",
            current_query=current_q,
            attempt=att,
            reason="no_results",
            preferred_locations=["Coimbatore", "Tamil Nadu"],
        )
        assert r["action"] == "pivot_query"
        assert ("Coimbatore" in r["optimized_query"]) or ("Kovai" in r["optimized_query"])


def test_geographic_compatibility_filtering():
    """Verify that foreign cards (Dubai, Egypt, US) are rejected when target is Indian cities."""
    from backend.app.services.browser_service import is_card_geographically_compatible, score_card_geographic_relevance

    # Target: Coimbatore / Tamil Nadu / India
    target_india = ["Coimbatore", "Tamil Nadu", "India"]

    assert is_card_geographically_compatible("Coimbatore, Tamil Nadu, India", target_india) is True
    assert is_card_geographically_compatible("Bengaluru, Karnataka, India", target_india) is True
    assert is_card_geographically_compatible("Dubai, United Arab Emirates", target_india) is False
    assert is_card_geographically_compatible("Cairo, Egypt", target_india) is False
    assert is_card_geographically_compatible("San Francisco, CA, United States", target_india) is False

    # Relevance scoring
    assert score_card_geographic_relevance("Coimbatore, Tamil Nadu, India", target_india) == 100
    assert score_card_geographic_relevance("Tamil Nadu, India", target_india) == 100
    assert score_card_geographic_relevance("Bengaluru, India", target_india) == 75


def test_clean_skill_tokens_sanitization():
    """Verify that skill tokens are capped and soft skills/parentheticals are stripped."""
    raw_skills = [
        "Product Vision & Strategy Definition",
        "Roadmapping",
        "Customer Discovery (Qualitative Interviews, Usability Testing, Workshops)",
        "Relentless Customer Champion",
        "Deep Empathy for End-user Frustrations",
        "Superb Written & Verbal Communication",
        "Exceptional Analytical Skills",
        "Product Requirement Documents (PRDs)",
        "Agile Scrum Environment",
        "Enterprise SaaS",
        "SQL",
        "Wireframing",
    ]
    cleaned = ai_service._clean_skill_tokens(raw_skills, max_tokens=10)
    assert len(cleaned) <= 10
    assert "Roadmapping" in cleaned
    assert "Enterprise SaaS" in cleaned
    # Fluff must be filtered out
    assert not any("empathy" in s.lower() for s in cleaned)
    assert not any("verbal" in s.lower() for s in cleaned)
    assert not any("champion" in s.lower() for s in cleaned)
    # Parentheticals must be stripped
    assert not any("(" in s for s in cleaned)

