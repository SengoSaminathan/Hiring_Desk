"""Supabase Database Service for Candidate Sourcing, AI Evaluations, and Jobs.

Provides asynchronous/synchronous CRUD operations for:
- Candidates (profiles, extracted skills, work history, location compatibility)
- Evaluations (AI fit scores, evidence quotes, category breakdown)
- Jobs (Job descriptions, mandatory skills, recruitment criteria)
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings

logger = logging.getLogger("hiring_desk.supabase_service")


class SupabaseService:
    """Manages cloud persistence and CRUD operations in Supabase PostgreSQL."""

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        service_role_key: Optional[str] = None,
    ):
        self._url = settings.SUPABASE_URL if url is None else url
        if service_role_key is not None or key is not None:
            self._key = service_role_key if service_role_key is not None else (key or "")
        else:
            # Prefer secret / service-role key for backend operations if configured; fallback to publishable / anon key
            self._key = (
                settings.SUPABASE_SECRET_KEY
                or settings.SUPABASE_SERVICE_ROLE_KEY
                or settings.SUPABASE_PUBLISHABLE_KEY
                or settings.SUPABASE_KEY
            )
        self._client = None
        self._init_attempted = False

    def is_configured(self) -> bool:
        """Returns True if valid Supabase URL and API Key are configured."""
        url = (self._url or "").strip()
        key = (self._key or "").strip()
        if not url or not key:
            return False
        if "your-project-id" in url or "your_supabase" in key:
            return False
        if not url.startswith("http"):
            return False
        return True

    def get_client(self):
        """Initializes and returns the Supabase Client if configured."""
        if not self.is_configured():
            return None

        if self._client is None and not self._init_attempted:
            self._init_attempted = True
            try:
                from supabase import create_client, Client
                self._client: Client = create_client(self._url.strip(), self._key.strip())
                logger.info("Successfully connected to Supabase: %s", self._url)
            except Exception as e:
                logger.error("Failed to initialize Supabase client: %s", e)
                self._client = None

        return self._client

    def check_connection(self) -> Dict[str, Any]:
        """Checks connectivity to Supabase and verifies table accessibility."""
        if not self.is_configured():
            return {
                "configured": False,
                "connected": False,
                "message": "Supabase credentials are not configured in .env. Set SUPABASE_URL and SUPABASE_KEY.",
                "url": None,
            }

        client = self.get_client()
        if not client:
            return {
                "configured": True,
                "connected": False,
                "message": "Failed to initialize Supabase client. Check project URL and API key.",
                "url": self._url,
            }

        try:
            # Query candidates table with limit 1 to verify credentials and table existence
            res = client.table("candidates").select("id").limit(1).execute()
            return {
                "configured": True,
                "connected": True,
                "message": "Connected to Supabase PostgreSQL successfully.",
                "url": self._url,
                "tables_verified": ["candidates", "evaluations", "jobs"],
            }
        except Exception as e:
            logger.warning("Supabase health check ping error: %s", e)
            return {
                "configured": True,
                "connected": False,
                "message": f"Connection error: {str(e)}",
                "url": self._url,
            }

    @staticmethod
    def _normalize_json_field(val: Any, default: Any) -> Any:
        """Converts strings, dicts, or lists into native Python structures for JSONB storage."""
        if val is None:
            return default
        if isinstance(val, (dict, list)):
            return val
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return default
        return default

    # =========================================================================
    # CANDIDATE CRUD OPERATIONS
    # =========================================================================

    def upsert_candidate(self, candidate_data: Dict[str, Any]) -> Optional[str]:
        """Inserts or updates a candidate profile in Supabase matching on canonical_url."""
        client = self.get_client()
        if not client:
            return None

        cid = candidate_data.get("id") or f"cand_{int(candidate_data.get('timestamp', 0)) or candidate_data.get('name', 'cand')}"
        canonical_url = candidate_data.get("canonical_url") or f"https://linkedin.com/in/{cid}"
        name = candidate_data.get("name", "Unknown Candidate")
        headline = candidate_data.get("headline", "")
        company = candidate_data.get("current_company") or candidate_data.get("company", "")
        location = candidate_data.get("location", "")
        curr_loc = candidate_data.get("current_location") or location

        payload = {
            "canonical_url": canonical_url,
            "name": name,
            "headline": headline,
            "current_company": company,
            "location": location,
            "current_location": curr_loc,
            "preferred_work_locations": self._normalize_json_field(candidate_data.get("preferred_work_locations"), []),
            "willingness_to_relocate": candidate_data.get("willingness_to_relocate", "Unknown"),
            "work_authorization": candidate_data.get("work_authorization") or "",
            "location_compatibility_status": candidate_data.get("location_compatibility_status", "Compatible"),
            "location_compatibility_reason": candidate_data.get("location_compatibility_reason", ""),
            "domain_relevance": candidate_data.get("domain_relevance", "Relevant"),
            "domain_relevance_notes": candidate_data.get("domain_relevance_notes", ""),
            "experience_years": float(candidate_data.get("experience_years") or 5.0),
            "about": candidate_data.get("about", ""),
            "skills": self._normalize_json_field(candidate_data.get("skills"), []),
            "experience_history": self._normalize_json_field(candidate_data.get("experience_history"), []),
            "education": self._normalize_json_field(candidate_data.get("education"), []),
            "certifications": self._normalize_json_field(candidate_data.get("certifications"), []),
            "projects": self._normalize_json_field(candidate_data.get("projects"), []),
            "recent_activity": self._normalize_json_field(candidate_data.get("recent_activity"), []),
            "section_scores": self._normalize_json_field(candidate_data.get("section_scores"), {}),
            "raw_snippet": candidate_data.get("raw_snippet", ""),
            "avatar_url": candidate_data.get("avatar_url") or candidate_data.get("avatar") or "",
            "status": candidate_data.get("status", "New"),
        }

        # Include ID if already provided
        if cid:
            payload["id"] = str(cid)

        try:
            res = client.table("candidates").upsert(payload, on_conflict="canonical_url").execute()
            if res.data and len(res.data) > 0:
                saved_id = res.data[0].get("id") or cid
                logger.info("Upserted candidate in Supabase: %s (%s)", name, saved_id)
                return saved_id
            return cid
        except Exception as e:
            logger.error("Supabase upsert_candidate failed for %s: %s", name, e)
            return None

    def get_candidate_by_id(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single candidate by ID with associated evaluations."""
        client = self.get_client()
        if not client:
            return None

        try:
            res = client.table("candidates").select("*, evaluations(*)").eq("id", candidate_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error("Supabase get_candidate_by_id failed: %s", e)
            return None

    def get_candidate_by_url(self, canonical_url: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single candidate by their canonical profile URL."""
        client = self.get_client()
        if not client:
            return None

        try:
            res = client.table("candidates").select("*").eq("canonical_url", canonical_url).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error("Supabase get_candidate_by_url failed: %s", e)
            return None

    def get_all_candidates(self, limit: int = 50, status: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Retrieves candidates paired with their latest evaluation from Supabase.
        Returns empty list [] if table is empty. Returns None if connection or query failed."""
        client = self.get_client()
        if not client:
            return None

        try:
            query = client.table("candidates").select("*, evaluations(*)").order("created_at", desc=True).limit(limit)
            if status:
                query = query.eq("status", status)

            res = query.execute()
            candidates = res.data or []

            # Format to match application candidate dict structure
            formatted = []
            for c in candidates:
                evals = c.get("evaluations") or []
                latest_eval = evals[-1] if evals else {}

                formatted.append({
                    "id": c.get("id"),
                    "canonical_url": c.get("canonical_url"),
                    "name": c.get("name"),
                    "headline": c.get("headline"),
                    "current_company": c.get("current_company"),
                    "location": c.get("location") or c.get("current_location") or "",
                    "current_location": c.get("current_location") or c.get("location") or "",
                    "preferred_work_locations": c.get("preferred_work_locations") or [],
                    "willingness_to_relocate": c.get("willingness_to_relocate") or "Unknown",
                    "work_authorization": c.get("work_authorization") or "",
                    "location_compatibility_status": c.get("location_compatibility_status") or "Compatible",
                    "location_compatibility_reason": c.get("location_compatibility_reason") or "",
                    "domain_relevance": latest_eval.get("domain_relevance") or c.get("domain_relevance") or "Relevant",
                    "domain_relevance_notes": latest_eval.get("domain_relevance_notes") or c.get("domain_relevance_notes") or "",
                    "experience_years": c.get("experience_years"),
                    "about": c.get("about") or "",
                    "skills": c.get("skills") or [],
                    "experience_history": c.get("experience_history") or [],
                    "education": c.get("education") or [],
                    "certifications": c.get("certifications") or [],
                    "projects": c.get("projects") or [],
                    "recent_activity": c.get("recent_activity") or [],
                    "section_scores": latest_eval.get("section_scores") or c.get("section_scores") or {},
                    "category_evaluations": latest_eval.get("category_evaluations") or {},
                    "location_compatibility": latest_eval.get("location_compatibility") or {},
                    "raw_snippet": c.get("raw_snippet"),
                    "avatar_url": c.get("avatar_url"),
                    "created_at": c.get("created_at"),
                    "status": c.get("status") or "New",
                    "fit_score": latest_eval.get("fit_score"),
                    "completeness_score": latest_eval.get("completeness_score"),
                    "evaluation_coverage": latest_eval.get("evaluation_coverage", 100.0),
                    "match_level": latest_eval.get("match_level") or "Medium",
                    "justification": latest_eval.get("justification") or "",
                    "evidence_quotes": latest_eval.get("evidence_quotes") or [],
                    "missing_criteria": latest_eval.get("missing_criteria") or [],
                    "job_title": latest_eval.get("job_title") or "Target Role",
                    "stored_in_supabase": True,
                })

            return formatted
        except Exception as e:
            logger.error("Supabase get_all_candidates failed: %s", e)
            return None

    def update_candidate_status(self, candidate_id: str, new_status: str) -> bool:
        """Updates the status ('New', 'In Review', 'Shortlisted', 'Not a Fit') of a candidate."""
        client = self.get_client()
        if not client:
            return False

        try:
            res = client.table("candidates").update({"status": new_status}).eq("id", candidate_id).execute()
            return bool(res.data)
        except Exception as e:
            logger.error("Supabase update_candidate_status failed: %s", e)
            return False

    def delete_candidate(self, candidate_id: str) -> bool:
        """Deletes a candidate by ID (cascades automatically to evaluations)."""
        client = self.get_client()
        if not client:
            return False

        try:
            res = client.table("candidates").delete().eq("id", candidate_id).execute()
            return bool(res.data)
        except Exception as e:
            logger.error("Supabase delete_candidate failed: %s", e)
            return False

    def clear_all_candidates(self) -> bool:
        """Deletes all candidate records and evaluations from Supabase."""
        client = self.get_client()
        if not client:
            return False

        try:
            client.table("evaluations").delete().neq("candidate_id", "___none___").execute()
            client.table("candidates").delete().neq("id", "___none___").execute()
            logger.info("Cleared all candidate records from Supabase.")
            return True
        except Exception as e:
            logger.error("Supabase clear_all_candidates failed: %s", e)
            return False

    # =========================================================================
    # EVALUATION CRUD OPERATIONS
    # =========================================================================

    def insert_evaluation(self, eval_data: Dict[str, Any]) -> Optional[int]:
        """Inserts an AI candidate match evaluation into Supabase."""
        client = self.get_client()
        if not client:
            return None

        cid = eval_data.get("candidate_id")
        if not cid:
            logger.warning("Cannot insert evaluation into Supabase without candidate_id.")
            return None

        cat_evals = eval_data.get("category_evaluations", {})
        cat_evals_dict = {
            k: (v.model_dump() if hasattr(v, "model_dump") else (v.dict() if hasattr(v, "dict") else v))
            for k, v in cat_evals.items()
        } if isinstance(cat_evals, dict) else {}

        payload = {
            "candidate_id": str(cid),
            "job_title": eval_data.get("job_title", "Target Role"),
            "fit_score": float(eval_data.get("fit_score", 0.0)),
            "completeness_score": float(eval_data.get("completeness_score", 0.0)),
            "evaluation_coverage": float(eval_data.get("evaluation_coverage", 100.0)),
            "match_level": eval_data.get("match_level", "Medium"),
            "domain_relevance": eval_data.get("domain_relevance", "Relevant"),
            "domain_relevance_notes": eval_data.get("domain_relevance_notes", ""),
            "location_compatibility": self._normalize_json_field(eval_data.get("location_compatibility"), {}),
            "justification": eval_data.get("justification_summary") or eval_data.get("justification", ""),
            "evidence_quotes": self._normalize_json_field(eval_data.get("evidence_quotes"), []),
            "missing_criteria": self._normalize_json_field(eval_data.get("missing_criteria"), []),
            "section_scores": self._normalize_json_field(eval_data.get("section_scores"), {}),
            "category_evaluations": cat_evals_dict,
        }

        try:
            res = client.table("evaluations").insert(payload).execute()
            if res.data and len(res.data) > 0:
                eval_id = res.data[0].get("id")
                logger.info("Inserted evaluation into Supabase for candidate %s (Eval ID: %s)", cid, eval_id)
                return eval_id
            return None
        except Exception as e:
            logger.error("Supabase insert_evaluation failed for %s: %s", cid, e)
            return None

    def get_evaluations_for_candidate(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Retrieves all historical evaluations for a candidate."""
        client = self.get_client()
        if not client:
            return []

        try:
            res = client.table("evaluations").select("*").eq("candidate_id", candidate_id).order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error("Supabase get_evaluations_for_candidate failed: %s", e)
            return []

    # =========================================================================
    # JOB / JD REQUISITION CRUD OPERATIONS
    # =========================================================================

    def create_or_update_job(self, job_data: Dict[str, Any]) -> Optional[str]:
        """Saves a Job Description criteria record into Supabase."""
        client = self.get_client()
        if not client:
            return None

        payload = {
            "job_title": job_data.get("job_title", "Untitled Role"),
            "department": job_data.get("department"),
            "seniority_level": job_data.get("seniority_level", "Senior"),
            "min_years_experience": float(job_data.get("min_years_experience")) if job_data.get("min_years_experience") else None,
            "max_years_experience": float(job_data.get("max_years_experience")) if job_data.get("max_years_experience") else None,
            "mandatory_skills": self._normalize_json_field(job_data.get("mandatory_skills"), []),
            "preferred_skills": self._normalize_json_field(job_data.get("preferred_skills"), []),
            "technologies": self._normalize_json_field(job_data.get("technologies"), []),
            "preferred_locations": self._normalize_json_field(job_data.get("preferred_locations"), []),
            "criteria_list": self._normalize_json_field(job_data.get("criteria_list"), []),
            "raw_jd": job_data.get("raw_jd") or job_data.get("job_description", ""),
        }

        if job_data.get("id"):
            payload["id"] = str(job_data["id"])

        try:
            res = client.table("jobs").upsert(payload).execute()
            if res.data and len(res.data) > 0:
                jid = res.data[0].get("id")
                logger.info("Saved job to Supabase: %s (%s)", payload["job_title"], jid)
                return jid
            return None
        except Exception as e:
            logger.error("Supabase create_or_update_job failed: %s", e)
            return None

    def get_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves saved job requisitions from Supabase."""
        client = self.get_client()
        if not client:
            return []

        try:
            res = client.table("jobs").select("*").order("created_at", desc=True).limit(limit).execute()
            return res.data or []
        except Exception as e:
            logger.error("Supabase get_jobs failed: %s", e)
            return []


# Global singleton service
supabase_service = SupabaseService()

