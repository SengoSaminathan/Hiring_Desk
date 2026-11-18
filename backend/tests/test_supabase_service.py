"""Unit tests for Supabase Database Service, CRUD operations, and hybrid SQLite fallback."""

import json
from unittest.mock import MagicMock, patch
import pytest

from backend.app.services.supabase_service import SupabaseService
from backend.app.services.db_service import db_service


def test_supabase_service_unconfigured():
    """When credentials are empty or placeholder, service reports unconfigured."""
    service = SupabaseService(url="", key="")
    assert not service.is_configured()
    status = service.check_connection()
    assert not status["configured"]
    assert not status["connected"]
    assert "not configured" in status["message"].lower()

    # Placeholder detection
    service_placeholder = SupabaseService(url="https://your-project-id.supabase.co", key="your_supabase_key")
    assert not service_placeholder.is_configured()


def test_supabase_service_supports_new_publishable_and_secret_keys():
    """Verify that new Supabase sb_publishable_ and sb_secret_ key formats are supported."""
    service_pub = SupabaseService(
        url="https://rvqtzlixrbzuceiysbqx.supabase.co",
        key="sb_publishable_vvNJYmWTCScKmMn_BAn2cQ_Hr6y"
    )
    assert service_pub.is_configured()
    assert service_pub._key.startswith("sb_publishable_")

    service_sec = SupabaseService(
        url="https://rvqtzlixrbzuceiysbqx.supabase.co",
        service_role_key="sb_secret_x5si0123456789"
    )
    assert service_sec.is_configured()
    assert service_sec._key.startswith("sb_secret_")


def test_supabase_service_json_normalization():
    """_normalize_json_field parses JSON strings or returns native collections for JSONB."""
    service = SupabaseService()
    
    # Already list/dict
    assert service._normalize_json_field(["Python", "FastAPI"], []) == ["Python", "FastAPI"]
    assert service._normalize_json_field({"experience": 85}, {}) == {"experience": 85}

    # JSON string
    assert service._normalize_json_field('["Python", "RAG"]', []) == ["Python", "RAG"]
    assert service._normalize_json_field('{"skills": 90}', {}) == {"skills": 90}

    # None and invalid JSON string
    assert service._normalize_json_field(None, []) == []
    assert service._normalize_json_field("not-valid-json", []) == []


def test_db_service_get_database_status():
    """db_service reports both local SQLite stats and Supabase connectivity status."""
    with patch("backend.app.services.supabase_service.supabase_service.check_connection") as mock_chk:
        mock_chk.return_value = {
            "configured": True,
            "connected": True,
            "message": "Connected",
            "url": "https://test.supabase.co"
        }
        status = db_service.get_database_status()
        assert "sqlite" in status
        assert "supabase" in status
        assert "active_storage" in status
        assert "candidates_count" in status["sqlite"]
        assert "evaluations_count" in status["sqlite"]
        assert status["supabase"]["configured"] is True


def test_db_service_local_fallback_when_supabase_unconfigured():
    """db_service falls back cleanly to local SQLite when Supabase is not configured."""
    candidates = db_service.get_all_candidates(limit=10)
    assert isinstance(candidates, list)


def test_mock_supabase_candidate_crud():
    """Tests Supabase CRUD operations using a mocked PostgREST client."""
    service = SupabaseService(url="https://test-project.supabase.co", key="test-key")
    mock_client = MagicMock()
    service._client = mock_client
    service._init_attempted = True

    candidate_payload = {
        "id": "cand_test_01",
        "name": "Jane Developer",
        "canonical_url": "https://linkedin.com/in/janedev",
        "headline": "Lead AI Architect",
        "skills": ["Python", "LLM", "RAG"],
        "experience_history": [{"role": "AI Architect", "company": "TechCorp", "dates": "2022-Present"}],
        "work_authorization": "UAE Golden Visa Holder",
        "location_compatibility_status": "Compatible",
        "domain_relevance": "Highly Relevant",
    }

    # 1. Upsert candidate
    mock_upsert_res = MagicMock()
    mock_upsert_res.data = [{"id": "cand_test_01", "name": "Jane Developer"}]
    mock_client.table().upsert().execute.return_value = mock_upsert_res

    res_id = service.upsert_candidate(candidate_payload)
    assert res_id == "cand_test_01"
    mock_client.table.assert_called_with("candidates")

    # 2. Update status
    mock_update_res = MagicMock()
    mock_update_res.data = [{"id": "cand_test_01", "status": "Shortlisted"}]
    mock_client.table().update().eq().execute.return_value = mock_update_res

    updated = service.update_candidate_status("cand_test_01", "Shortlisted")
    assert updated is True

    # 3. Delete candidate
    mock_delete_res = MagicMock()
    mock_delete_res.data = [{"id": "cand_test_01"}]
    mock_client.table().delete().eq().execute.return_value = mock_delete_res

    deleted = service.delete_candidate("cand_test_01")
    assert deleted is True


def test_mock_supabase_evaluation_crud():
    """Tests Supabase evaluation insert with 3-state category breakdown."""
    service = SupabaseService(url="https://test-project.supabase.co", key="test-key")
    mock_client = MagicMock()
    service._client = mock_client
    service._init_attempted = True

    eval_payload = {
        "candidate_id": "cand_test_01",
        "job_title": "Senior AI Lead",
        "fit_score": 88.5,
        "completeness_score": 92.0,
        "evaluation_coverage": 85.0,
        "match_level": "High",
        "domain_relevance": "Highly Relevant",
        "evidence_quotes": [{"requirement": "Python", "quote": "Lead Python developer for 5 years", "confidence": 0.95}],
        "missing_criteria": ["Kubernetes"],
        "category_evaluations": {
            "experience": {"weight": 0.35, "score": 90.0, "status": "Matched", "evaluation_state": "available_relevant"},
            "projects": {"weight": 0.05, "score": None, "status": "Not Available", "evaluation_state": "not_available"},
        },
    }

    mock_insert_res = MagicMock()
    mock_insert_res.data = [{"id": 101}]
    mock_client.table().insert().execute.return_value = mock_insert_res

    eval_id = service.insert_evaluation(eval_payload)
    assert eval_id == 101
    mock_client.table.assert_called_with("evaluations")

