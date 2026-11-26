"""Unit and integration tests for candidate outreach, AI message generator, and automated delivery."""

import pytest
import inspect
import re
import asyncio
from unittest.mock import AsyncMock, MagicMock
from backend.app.api.outreach import (
    generate_outreach,
    send_outreach_batch,
    GenerateOutreachRequest,
    SendOutreachBatchRequest,
    CandidateOutreachItem,
)
from backend.app.services.ai_service import ai_service
from backend.app.services.browser_service import _LinkedInBrowserEngine, browser_service, sourcing_tracker
from backend.app.services.db_service import db_service
from backend.app.services.supabase_service import supabase_service


@pytest.fixture(autouse=True)
def offline_mode(monkeypatch):
    """Ensures tests run deterministically offline without waiting for network/Gemini/Supabase DNS timeouts."""
    monkeypatch.setattr(ai_service, "_circuit_breaker_until", float("inf"))
    monkeypatch.setattr(supabase_service, "is_configured", lambda: False)


def test_generate_outreach_message_deterministic():
    """Verifies that the outreach generator creates a formal 3-paragraph message with role and company details."""
    candidate = {
        "name": "Sengottayan S",
        "headline": "Lead Fullstack & AI Systems Engineer",
        "skills": ["React", "Python", "FastAPI", "PostgreSQL"],
        "current_company": "Tech Corp",
    }
    
    result = ai_service.generate_outreach_message(
        candidate=candidate,
        role_title="Senior AI Solutions Architect",
        company_name="Apex Global Technologies",
        company_details="pioneering enterprise generative AI automation",
        recruiter_name="HR Talent Team",
        tone="formal",
        force_deterministic=True,
    )
    
    assert "subject" in result
    assert "message_body" in result
    assert "connection_note" in result
    
    assert "Senior AI Solutions Architect" in result["subject"]
    assert "Apex Global Technologies" in result["subject"]
    
    body = result["message_body"]
    assert "Dear Sengottayan," in body
    assert "Apex Global Technologies" in body
    assert "Senior AI Solutions Architect" in body
    assert "HR Talent Team" in body
    assert "introductory conversation" in body.lower() or "connect" in body.lower()


def test_connection_note_strict_300_character_limit():
    """Verifies that the LinkedIn connection request note NEVER exceeds 295 characters, preventing LinkedIn rejection."""
    result = ai_service.generate_outreach_message(
        candidate={
            "name": "Dr. Alexander Christopher Montgomery-Smith",
            "headline": "Principal Architect & Vice President of Worldwide Cloud Infrastructure Engineering",
            "skills": ["Distributed Kubernetes High-Throughput Stream Processing"],
        },
        role_title="Senior Principal Enterprise Deep Learning Systems Engineering Lead",
        company_name="International Consolidated Technologies & Solutions Group Inc.",
        company_details="Global enterprise cloud computing leader with 50,000 employees worldwide",
        recruiter_name="Executive Talent Acquisition & Leadership Recruiting Division",
        force_deterministic=True,
    )
    
    note = result["connection_note"]
    assert len(note) <= 295, f"Connection note exceeded LinkedIn 295 char safe limit! Length was {len(note)}: {note}"
    assert "Alexander" in note or "Dr." in note


def test_database_outreach_status_persistence():
    """Verifies that candidate outreach status, timestamp, message and delivery method persist in SQLite."""
    test_cand = {
        "id": "cand_outreach_test_001",
        "canonical_url": "https://www.linkedin.com/in/sengottayan-s-17b5ab329/",
        "name": "Sengottayan S",
        "headline": "Fullstack Developer",
        "skills": ["React", "FastAPI"],
    }
    db_service.save_candidate(test_cand)
    
    # Update outreach status
    updated = db_service.update_candidate_outreach(
        canonical_url="https://www.linkedin.com/in/sengottayan-s-17b5ab329/",
        outreach_status="Sent",
        outreach_message="Dear Sengottayan, We would love to connect regarding Senior AI Lead role.",
        outreach_method="Direct Message",
    )
    assert updated is True
    
    # Fetch from database and verify
    candidates = db_service.get_all_candidates(limit=50)
    matched = next((c for c in candidates if "sengottayan-s-17b5ab329" in (c.get("canonical_url") or "")), None)
    
    assert matched is not None
    assert matched["outreach_status"] == "Sent"
    assert "Senior AI Lead" in (matched["outreach_message"] or "")
    assert matched["outreach_method"] == "Direct Message"
    assert matched["outreach_sent_at"] is not None


def test_api_outreach_generate_endpoint():
    """Tests the /api/outreach/generate FastAPI endpoint directly."""
    req = GenerateOutreachRequest(
        candidate_name="Sengottayan S",
        canonical_url="https://www.linkedin.com/in/sengottayan-s-17b5ab329/",
        headline="Fullstack Engineer",
        skills=["React", "Node.js"],
        target_role="Senior Fullstack Engineer",
        company_name="Antigravity Corp",
        recruiter_name="Talent Partner",
        tone="formal",
        force_deterministic=True,
    )
    res = generate_outreach(req)
    assert res.subject
    assert "Senior Fullstack Engineer" in res.subject
    assert "Antigravity Corp" in res.message_body
    assert len(res.connection_note) <= 295


def test_api_outreach_send_simulation():
    """Tests the /api/outreach/send endpoint in simulation mode."""
    req = SendOutreachBatchRequest(
        candidates=[
            CandidateOutreachItem(
                canonical_url="https://www.linkedin.com/in/sengottayan-s-17b5ab329/",
                candidate_name="Sengottayan S",
                message_body="Test outreach message",
                connection_note="Hi Sengottayan!",
            )
        ],
        mode="simulation",
        browser_channel="chrome",
    )
    mock_bg = MagicMock()
    res = send_outreach_batch(req, mock_bg)
    assert res["state"] == "initializing"
    assert res["total"] == 1
    assert "session_id" in res
    mock_bg.add_task.assert_called_once()


def test_ai_outreach_with_gemini_json_mock(monkeypatch):
    """Verifies that when Gemini returns valid JSON, it is parsed and connection note length is enforced."""
    monkeypatch.setattr(ai_service, "_circuit_breaker_until", 0.0)
    monkeypatch.setattr(ai_service, "is_ai_available", lambda: True)
    
    mock_resp = {
        "subject": "Exciting Opportunity at Acme",
        "message_body": "Dear Sengottayan,\n\nWe love your profile.\n\nBest,\nHR",
        "connection_note": "A" * 320,  # Simulate model returning slightly too long note
    }
    monkeypatch.setattr(ai_service, "_call_gemini_json", lambda prompt, sys_inst: mock_resp)
    
    res = ai_service.generate_outreach_message(
        candidate={"name": "Sengottayan S", "skills": ["Python"]},
        role_title="Senior AI Engineer",
        company_name="Acme",
    )
    assert res["subject"] == "Exciting Opportunity at Acme"
    assert len(res["connection_note"]) <= 295
    assert res["connection_note"].endswith("...")


def test_selector_safety_no_has_text_in_evaluate():
    """Verifies that browser_service.py has zero occurrences of ':has-text' inside page.evaluate calls.
    
    Playwright's :has-text pseudo-class is invalid in native browser querySelector / querySelectorAll,
    throwing a fatal DOMException: SyntaxError.
    """
    source = inspect.getsource(browser_service._engine.__class__)
    
    eval_blocks = re.findall(r"evaluate\(\s*(?:r?\"{3}|r?\'{3}|f\"{3}|f\'{3})(.*?)(?:\"{3}|\'{3})", source, re.DOTALL)
    assert len(eval_blocks) > 0, "Expected to find page.evaluate blocks in browser_service"
    for idx, block in enumerate(eval_blocks):
        assert ":has-text" not in block, f"Found invalid :has-text inside page.evaluate block #{idx}: {block[:120]}..."


def _run_coroutine(coro):
    """Deterministically executes a coroutine where sub-operations are awaited AsyncMocks."""
    try:
        while True:
            coro.send(None)
    except StopIteration as e:
        return e.value


def test_send_linkedin_outreach_detects_pending_invitation(monkeypatch):
    """Verifies that an already pending connection (e.g. Sengottayan S) is detected immediately,
    updating DB to 'Sent' / 'Connection Pending', updating overlay, and returning success without hanging.
    """
    engine = _LinkedInBrowserEngine()
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    
    mock_name_el = AsyncMock()
    mock_name_el.inner_text.return_value = "Sengottayan S"
    
    async def mock_query(sel):
        if "h1" in sel:
            return mock_name_el
        return None
    mock_page.query_selector = mock_query
    
    async def mock_evaluate(script, *args):
        if "pending" in script.lower():
            return True
        return False
        
    mock_page.evaluate = mock_evaluate
    
    monkeypatch.setattr(engine, "_get_or_create_context", AsyncMock(return_value=(mock_context, mock_page)))
    monkeypatch.setattr(engine, "is_authenticated_session", AsyncMock(return_value=True))
    monkeypatch.setattr(engine, "_update_overlay", AsyncMock())
    monkeypatch.setattr(engine, "_dismiss_common_overlays", AsyncMock())
    
    session_id = "test-session-pending-001"
    sourcing_tracker.create_session(session_id, mode="live", query="AI Engineer", max_results=5)
    
    result = _run_coroutine(
        engine.send_linkedin_outreach(
            candidate_url="https://www.linkedin.com/in/sengottayan-s-17b5ab329/",
            message_body="Hello Sengottayan, let's connect!",
            candidate_name="Sengottayan S",
            session_id=session_id,
            mode="live",
        )
    )
    
    assert result["status"] == "success"
    assert result["delivery_method"] == "Connection Pending"
    assert "pending" in result["message"].lower()
    
    # Verify DB persistence
    candidates = db_service.get_all_candidates(limit=50)
    cand = next((c for c in candidates if "sengottayan-s-17b5ab329" in (c.get("canonical_url") or "")), None)
    assert cand is not None
    assert cand["outreach_status"] == "Sent"
    assert cand["outreach_method"] == "Connection Pending"
    
    # Verify session completed
    sess = sourcing_tracker.get_session(session_id)
    assert sess["state"] == "completed"
    assert "pending" in sess["message"].lower()


def test_send_linkedin_outreach_dropdown_pending_invitation(monkeypatch):
    """Verifies that if pending status is revealed inside the 'More' dropdown,
    it is detected and handled cleanly as Connection Pending.
    """
    engine = _LinkedInBrowserEngine()
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    
    mock_name_el = AsyncMock()
    mock_name_el.inner_text.return_value = "Jane Doe"
    mock_more_btn = AsyncMock()
    
    async def mock_query_selector(sel):
        if "h1" in sel:
            return mock_name_el
        if "Message" in sel:
            return None
        if "More" in sel:
            return mock_more_btn
        return None
        
    mock_page.query_selector = mock_query_selector
    
    async def mock_evaluate(script, *args):
        if "hasPending" in script:
            return "not_found"
        if "artdeco-dropdown__content" in script:
            return "pending"
        return False
        
    mock_page.evaluate = mock_evaluate
    
    monkeypatch.setattr(engine, "_get_or_create_context", AsyncMock(return_value=(mock_context, mock_page)))
    monkeypatch.setattr(engine, "is_authenticated_session", AsyncMock(return_value=True))
    monkeypatch.setattr(engine, "_update_overlay", AsyncMock())
    monkeypatch.setattr(engine, "_dismiss_common_overlays", AsyncMock())
    
    result = _run_coroutine(
        engine.send_linkedin_outreach(
            candidate_url="https://www.linkedin.com/in/jane-doe-test/",
            message_body="Hello Jane!",
            candidate_name="Jane Doe",
            mode="live",
        )
    )
    
    assert result["status"] == "success"
    assert result["delivery_method"] == "Connection Pending"
    assert "pending" in result["message"].lower()


def test_send_linkedin_outreach_locked_inmail_falls_back_to_connect(monkeypatch):
    """Verifies that when Message button requires InMail credit (lock icon / 2nd-3rd degree),
    it safely skips direct message and connects via standard DOM inspection without syntax errors.
    """
    engine = _LinkedInBrowserEngine()
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    
    mock_name_el = AsyncMock()
    mock_name_el.inner_text.return_value = "Bob Smith"
    
    mock_msg_btn = AsyncMock()
    mock_msg_btn.get_attribute.return_value = "Message (InMail)"
    
    async def mock_query_selector(sel):
        if "h1" in sel:
            return mock_name_el
        if "Message" in sel:
            return mock_msg_btn
        return None
        
    mock_page.query_selector = mock_query_selector
    
    async def mock_evaluate(script, *args):
        # Lock icon check on msg button -> True (locked)
        if "svg[data-test-icon*=\"lock\"]" in script or "lock" in script.lower():
            return True
        # Primary connect check -> "clicked"
        if "connectbutton" in script.lower():
            return "clicked"
        # Add a note check -> True
        if "add a note" in script.lower():
            return True
        # Focus editor -> True
        if "contenteditable" in script.lower():
            return True
        # Send invite -> True
        if "send now" in script.lower() or "send invitation" in script.lower():
            return True
        return False
        
    mock_page.evaluate = mock_evaluate
    
    monkeypatch.setattr(engine, "_get_or_create_context", AsyncMock(return_value=(mock_context, mock_page)))
    monkeypatch.setattr(engine, "is_authenticated_session", AsyncMock(return_value=True))
    monkeypatch.setattr(engine, "_update_overlay", AsyncMock())
    monkeypatch.setattr(engine, "_dismiss_common_overlays", AsyncMock())
    
    result = _run_coroutine(
        engine.send_linkedin_outreach(
            candidate_url="https://www.linkedin.com/in/bob-smith-test/",
            message_body="Hi Bob, would love to connect!",
            candidate_name="Bob Smith",
            mode="live",
        )
    )
    
    assert result["status"] == "success"
    assert result["delivery_method"] in ("Connection Note", "Connection Request")
    assert result["recipient"] == "Bob Smith"


def test_send_linkedin_outreach_dismisses_inmail_paywall_modal(monkeypatch):
    """Verifies that when clicking Message unexpectedly triggers an InMail paywall dialog,
    the modal is safely dismissed and the agent falls back to Connect without crashing.
    """
    engine = _LinkedInBrowserEngine()
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    
    mock_name_el = AsyncMock()
    mock_name_el.inner_text.return_value = "Alice Johnson"
    
    mock_msg_btn = AsyncMock()
    mock_msg_btn.get_attribute.return_value = "Message"
    
    async def mock_query_selector(sel):
        if "h1" in sel:
            return mock_name_el
        if "Message" in sel:
            return mock_msg_btn
        return None
        
    mock_page.query_selector = mock_query_selector
    
    async def mock_evaluate(script, *args):
        # Lock check -> False (initially looks unlocked)
        if "svg[data-test-icon*=\"lock\"]" in script:
            return False
        # InMail modal popup after clicking Message -> True (paywall modal detected)
        if "outside your network" in script or "artdeco-modal" in script:
            return True
        # Connect primary -> "clicked"
        if "connectbutton" in script.lower():
            return "clicked"
        # Add note -> True
        if "add a note" in script.lower():
            return True
        # Focus editor -> True
        if "contenteditable" in script.lower():
            return True
        # Send button -> True
        if "send now" in script.lower():
            return True
        return False
        
    mock_page.evaluate = mock_evaluate
    
    monkeypatch.setattr(engine, "_get_or_create_context", AsyncMock(return_value=(mock_context, mock_page)))
    monkeypatch.setattr(engine, "is_authenticated_session", AsyncMock(return_value=True))
    monkeypatch.setattr(engine, "_update_overlay", AsyncMock())
    monkeypatch.setattr(engine, "_dismiss_common_overlays", AsyncMock())
    
    result = _run_coroutine(
        engine.send_linkedin_outreach(
            candidate_url="https://www.linkedin.com/in/alice-johnson-test/",
            message_body="Hi Alice, exciting opportunity!",
            candidate_name="Alice Johnson",
            mode="live",
        )
    )
    
    assert result["status"] == "success"
    assert result["delivery_method"] in ("Connection Note", "Connection Request")


def test_is_connection_pending_helper():
    """Verifies that _is_connection_pending properly handles JS evaluate and query_selector fallbacks."""
    engine = _LinkedInBrowserEngine()
    
    # 1. Evaluate detects pending
    page1 = AsyncMock()
    page1.evaluate = AsyncMock(return_value=True)
    assert _run_coroutine(engine._is_connection_pending(page1)) is True
    
    # 2. Evaluate returns False, query_selector finds element
    page2 = AsyncMock()
    page2.evaluate = AsyncMock(return_value=False)
    page2.query_selector = AsyncMock(return_value=MagicMock())
    assert _run_coroutine(engine._is_connection_pending(page2)) is True
    
    # 3. Neither finds pending
    page3 = AsyncMock()
    page3.evaluate = AsyncMock(return_value=False)
    page3.query_selector = AsyncMock(return_value=None)
    assert _run_coroutine(engine._is_connection_pending(page3)) is False


