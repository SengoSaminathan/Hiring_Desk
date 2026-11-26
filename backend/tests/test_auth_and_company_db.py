"""Tests for User and Company Persistence (SQLite, Supabase sync, and Auth APIs)."""

import pytest
from backend.app.api.auth import (
    sync_user,
    get_user_profile,
    save_company_profile,
    get_company_profile_endpoint,
    SyncUserRequest,
    CompanyProfileRequest,
)
from backend.app.services.ai_service import ai_service
from backend.app.services.db_service import db_service
from backend.app.services.supabase_service import supabase_service


@pytest.fixture(autouse=True)
def offline_mode(monkeypatch):
    """Ensures tests run deterministically offline without waiting for network/Gemini/Supabase DNS timeouts."""
    monkeypatch.setattr(ai_service, "_circuit_breaker_until", float("inf"))
    monkeypatch.setattr(supabase_service, "is_configured", lambda: False)


def test_users_and_companies_tables_exist():
    """Verify that users and companies tables exist in SQLite schema."""
    with db_service._get_connection() as conn:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        assert "users" in tables, "Table 'users' must exist in SQLite database"
        assert "companies" in tables, "Table 'companies' must exist in SQLite database"


def test_upsert_user_and_retrieve():
    """Test inserting and updating a user synced from Clerk."""
    test_user = {
        "id": "user_test_clerk_123",
        "email": "sarah.recruiter@acmecorp.com",
        "full_name": "Sarah Recruiter",
        "first_name": "Sarah",
        "last_name": "Recruiter",
        "role": "Lead Recruiter",
        "avatar_url": "https://img.clerk.com/test_avatar.png",
    }
    synced = db_service.upsert_user(test_user)
    assert synced["id"] == "user_test_clerk_123"
    assert synced["email"] == "sarah.recruiter@acmecorp.com"
    assert synced["full_name"] == "Sarah Recruiter"

    # Retrieve from DB
    retrieved = db_service.get_user("user_test_clerk_123")
    assert retrieved is not None
    assert retrieved["email"] == "sarah.recruiter@acmecorp.com"
    assert retrieved["role"] == "Lead Recruiter"

    # Update user
    update_data = {
        "id": "user_test_clerk_123",
        "email": "sarah.recruiter@acmecorp.com",
        "full_name": "Sarah J. Recruiter",
    }
    updated = db_service.upsert_user(update_data)
    assert updated["full_name"] == "Sarah J. Recruiter"


def test_upsert_company_and_link_user():
    """Test inserting company profile and associating it with the user."""
    user_id = "user_test_clerk_comp_456"
    db_service.upsert_user({
        "id": user_id,
        "email": "alex.hr@techcorp.io",
        "full_name": "Alex HR",
    })

    company_payload = {
        "name": "TechCorp Innovations",
        "industry": "Artificial Intelligence & ML",
        "website": "https://techcorp.io/careers",
        "location": "Bengaluru, India / Hybrid",
        "employee_count": "50-250",
        "value_proposition": "Building next-generation generative AI infrastructure.",
        "recruiter_name": "Alex HR",
        "recruiter_signature": "Alex HR | Lead Talent Acquisition at TechCorp",
    }

    company = db_service.upsert_company(company_payload, user_id=user_id)
    assert company["id"].startswith("comp_")
    assert company["name"] == "TechCorp Innovations"
    assert company["created_by_user_id"] == user_id

    # Check that user is linked to this company
    user = db_service.get_user(user_id)
    assert user["company_id"] == company["id"]
    assert user["company_name"] == "TechCorp Innovations"

    # Retrieve company profile by user_id
    retrieved_comp = db_service.get_company_profile(user_id=user_id)
    assert retrieved_comp is not None
    assert retrieved_comp["name"] == "TechCorp Innovations"
    assert retrieved_comp["industry"] == "Artificial Intelligence & ML"


def test_api_sync_user():
    """Test sync_user API endpoint."""
    req = SyncUserRequest(
        id="user_api_test_789",
        email="recruiter.api@example.com",
        full_name="API Recruiter",
        first_name="API",
        last_name="Recruiter",
        role="Recruiter",
    )
    res = sync_user(req)
    assert res["status"] == "success"
    assert res["user"]["id"] == "user_api_test_789"
    assert res["user"]["email"] == "recruiter.api@example.com"

    # Test retrieval endpoint
    user_res = get_user_profile("user_api_test_789")
    assert user_res["status"] == "success"
    assert user_res["user"]["full_name"] == "API Recruiter"


def test_api_company_profile_endpoints():
    """Test save_company_profile and get_company_profile API endpoints."""
    req = CompanyProfileRequest(
        companyName="Acme Global Systems",
        industry="Enterprise Software & SaaS",
        location="San Francisco, CA",
        website="https://acmeglobal.com",
        employeeCount="250-1000",
        companyDetails="Enterprise scale mission-critical platform",
        recruiterName="John Recruiter",
        recruiterSignature="John Recruiter | Talent Lead",
        user_id="user_api_test_789",
    )
    post_res = save_company_profile(req)
    assert post_res["status"] == "success"
    assert post_res["company"]["name"] == "Acme Global Systems"

    # Get company profile endpoint
    get_res = get_company_profile_endpoint(user_id="user_api_test_789")
    assert get_res["status"] == "success"
    assert get_res["company"]["name"] == "Acme Global Systems"
    assert get_res["company"]["location"] == "San Francisco, CA"
