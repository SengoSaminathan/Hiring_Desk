"""SQLite Database Persistence Service for Candidate Sourcing & Evaluation Reports.

Stores:
- Extracted Candidate Profiles (headline, company, experience, skills, raw resume text).
- Match Evaluations (fit scores, evidence citations, verbatim quotes, missing skills).
- Sourcing Run Summaries and aggregated reports for recruiters.
"""

import json
import logging
import os
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from backend.app.services.supabase_service import supabase_service

logger = logging.getLogger("hiring_desk.db_service")

DB_DIR = os.path.abspath("./data")
DB_PATH = os.path.join(DB_DIR, "hiring_desk.db")


def clean_linkedin_card_text(raw_text: str) -> Dict[str, str]:
    """Decomposes concatenated LinkedIn search card / headline text into clean headline, location, company, and role."""
    if not raw_text:
        return {"headline": "", "location": "", "company": "", "current_role": ""}
    
    text = raw_text.replace("\xa0", " ").strip()
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    
    headline = ""
    location = ""
    company = ""
    current_role = ""

    def is_loc_string(s: str) -> bool:
        s_clean = s.strip()
        if not s_clean or len(s_clean) < 2 or len(s_clean) > 80:
            return False
        if any(w in s_clean.lower() for w in ["engineer", "developer", "manager", "lead", "architect", "consultant", "analyst", "founder", "specialist"]):
            return False
        if re.search(r"\b(India|United Arab Emirates|UAE|United States|USA|UK|Singapore|Germany|Canada|Australia|KSA|Saudi Arabia)\b", s_clean, re.I):
            return True
        if re.search(r"\b(Dubai|Abu Dhabi|Sharjah|Ajman|Delhi|Mumbai|Bengaluru|Bangalore|Hyderabad|Pune|Chennai|Coimbatore|Tamil\s*Nadu|Tamilnadu|Kolkata|London|San Francisco|New York|Austin|Seattle|Berlin|Toronto)\b", s_clean, re.I):
            return True
        if re.match(r"^[A-Za-z\s\.\-]+(?:,\s*[A-Za-z\s\.\-]+)+$", s_clean):
            return True
        return False
    
    clean_lines = []
    for ln in lines:
        if re.search(r"^\d+[\d,]*\s*followers$", ln, re.I):
            continue
        if re.match(r"^(?:Follow|Connect|Message|View Profile)$", ln, re.I):
            continue
        if re.match(r"^Current:\s*", ln, re.I):
            c_text = re.sub(r"^Current:\s*", "", ln, flags=re.I).strip()
            c_text = re.sub(r"\b\d+[\d,]*\s*followers\b", "", c_text, flags=re.I).strip()
            if " at " in c_text:
                current_role, company = c_text.split(" at ", 1)
            elif " @ " in c_text:
                current_role, company = c_text.split(" @ ", 1)
            else:
                current_role = c_text
            continue
        if is_loc_string(ln):
            if not location:
                location = ln.strip()
            continue
        clean_lines.append(ln)
        
    headline = " ".join(clean_lines).strip()
    headline = re.sub(r"\s+", " ", headline)
    
    # Also handle single-line case where newlines were already replaced by spaces
    if not current_role and "Current:" in headline:
        parts = re.split(r"\s+Current:\s*", headline, maxsplit=1)
        headline = parts[0].strip()
        c_text = parts[1].strip()
        c_text = re.sub(r"\b\d+[\d,]*\s*followers\b", "", c_text, flags=re.I).strip()
        if " at " in c_text:
            current_role, company = c_text.split(" at ", 1)
        else:
            current_role = c_text

    # Remove Follow / Connect and follower count from single line
    headline = re.sub(r"\b(Follow|Connect|Message|View Profile)\b", "", headline, flags=re.I).strip()
    headline = re.sub(r"\b\d+[\d,]*\s*followers\b", "", headline, flags=re.I).strip()
    
    # Strip any trailing followers from company
    if company:
        company = re.sub(r"\b\d+[\d,]*\s*followers\b", "", company, flags=re.I).strip()
        company = re.sub(r"[\s\n\r]+", " ", company).strip()

    if not location:
        sub_loc = re.search(r"\b((?:Dubai|Abu Dhabi|Sharjah|Ajman)(?:,\s*United Arab Emirates)?|Delhi,\s*India|Mumbai,\s*India|Bengaluru,\s*India|Bangalore,\s*India|Hyderabad,\s*India|India|United Arab Emirates|UAE)\b", headline, re.I)
        if sub_loc:
            location = sub_loc.group(0).strip()
            
    # Clean trailing punctuation and pipes from headline
    headline = re.sub(r"[\s•·\|\-]+$", "", headline).strip()
    
    return {
        "headline": headline,
        "company": company.strip(),
        "current_role": current_role.strip(),
        "location": location.strip(),
    }


class DatabaseService:
    """Thread-safe SQLite database manager for local candidate persistence."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """Initializes tables for candidates, work experiences, and match evaluations."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id TEXT PRIMARY KEY,
                    canonical_url TEXT UNIQUE,
                    name TEXT NOT NULL,
                    headline TEXT,
                    current_company TEXT,
                    location TEXT,
                    experience_years REAL,
                    about TEXT,
                    skills TEXT,
                    experience_history TEXT,
                    raw_snippet TEXT,
                    avatar_url TEXT,
                    target_role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT,
                    job_title TEXT,
                    fit_score REAL,
                    completeness_score REAL,
                    match_level TEXT,
                    justification TEXT,
                    evidence_quotes TEXT,
                    missing_criteria TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    job_title TEXT UNIQUE NOT NULL,
                    department TEXT,
                    seniority_level TEXT,
                    min_years_experience REAL,
                    location TEXT,
                    preferred_locations TEXT,
                    mandatory_skills TEXT,
                    preferred_skills TEXT,
                    technologies TEXT,
                    criteria_list TEXT,
                    raw_jd TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_candidates_url ON candidates(canonical_url);
                CREATE INDEX IF NOT EXISTS idx_eval_candidate ON evaluations(candidate_id);
                CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(job_title);
            """)

            # Safe migration check for existing tables
            cols = [r[1] for r in conn.execute("PRAGMA table_info(candidates)").fetchall()]
            if "avatar_url" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN avatar_url TEXT;")
            if "target_role" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN target_role TEXT;")
            if "education" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN education TEXT;")
            if "certifications" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN certifications TEXT;")
            if "projects" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN projects TEXT;")
            if "recent_activity" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN recent_activity TEXT;")
            if "section_scores" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN section_scores TEXT;")
            if "current_location" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN current_location TEXT;")
            if "preferred_work_locations" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN preferred_work_locations TEXT;")
            if "willingness_to_relocate" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN willingness_to_relocate TEXT;")
            if "work_authorization" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN work_authorization TEXT;")
            if "location_compatibility_status" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN location_compatibility_status TEXT;")
            if "location_compatibility_reason" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN location_compatibility_reason TEXT;")
            if "domain_relevance" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN domain_relevance TEXT;")
            if "domain_relevance_notes" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN domain_relevance_notes TEXT;")
            if "status" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN status TEXT DEFAULT 'New';")

            eval_cols = [r[1] for r in conn.execute("PRAGMA table_info(evaluations)").fetchall()]
            if "section_scores" not in eval_cols:
                conn.execute("ALTER TABLE evaluations ADD COLUMN section_scores TEXT;")
            if "category_evaluations" not in eval_cols:
                conn.execute("ALTER TABLE evaluations ADD COLUMN category_evaluations TEXT;")
            if "evaluation_coverage" not in eval_cols:
                conn.execute("ALTER TABLE evaluations ADD COLUMN evaluation_coverage REAL;")
            if "domain_relevance" not in eval_cols:
                conn.execute("ALTER TABLE evaluations ADD COLUMN domain_relevance TEXT;")
            if "domain_relevance_notes" not in eval_cols:
                conn.execute("ALTER TABLE evaluations ADD COLUMN domain_relevance_notes TEXT;")
            if "location_compatibility" not in eval_cols:
                conn.execute("ALTER TABLE evaluations ADD COLUMN location_compatibility TEXT;")

        self.sanitize_existing_candidates()
        self.seed_default_jobs()
        logger.info("SQLite database initialized at %s", self.db_path)

    def sanitize_existing_candidates(self):
        """Sanitizes candidate records to clean concatenated titles, mock companies, locations, and detect work authorizations."""
        try:
            with self._get_connection() as conn:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(candidates)").fetchall()]
                has_target_role = "target_role" in cols
                select_query = "SELECT id, name, headline, current_company, location, raw_snippet, work_authorization" + (", target_role" if has_target_role else "") + " FROM candidates"
                rows = conn.execute(select_query).fetchall()
                for r in rows:
                    raw_name = r["name"] or ""
                    clean_name = raw_name
                    headline = r["headline"] or ""
                    company = r["current_company"] or ""
                    location = r["location"] or ""
                    snippet = r["raw_snippet"] or ""
                    work_auth = r["work_authorization"] or ""
                    cand_role = r["target_role"] if has_target_role and "target_role" in r.keys() and r["target_role"] else ""

                    # Decompose and clean LinkedIn search card text / headline noise
                    parsed = clean_linkedin_card_text(headline)
                    if parsed["headline"]:
                        headline = parsed["headline"]
                    if parsed["company"] and (company == "Technology Co." or not company or "followers" in company):
                        company = parsed["company"]
                    if parsed["location"] and (location in ("Location on Profile", "Location not specified", "Technology Co.", "") or not location):
                        location = parsed["location"]

                    # Clean concatenated headline in name
                    if "•" in raw_name or "·" in raw_name or "3rd+" in raw_name or "2nd+" in raw_name or "1st+" in raw_name:
                        parts = re.split(r"\s+[•·]\s*", raw_name)
                        c_name = parts[0].strip()
                        c_name = re.sub(r"\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message|follow)\b", "", c_name, flags=re.IGNORECASE).strip()
                        if c_name:
                            clean_name = c_name
                        if len(parts) > 1 and (not headline or headline in ("Professional on LinkedIn", "Software Professional", "")):
                            rest = " • ".join(parts[1:]).strip()
                            rest = re.sub(r"^(?:3rd\+|2nd\+|1st\+|3rd|2nd|1st)\s*", "", rest, flags=re.IGNORECASE)
                            rest = re.sub(r"^[\|\-·•]\s*", "", rest).strip()
                            for stopword in [" Follow ", " Connect ", " Message ", " Past:", " Current:"]:
                                if stopword in rest:
                                    rest = rest.split(stopword)[0].strip()
                            if rest and len(rest) > 2:
                                headline = rest

                    # Detect Work Authorization (e.g. UAE Golden Visa)
                    combined_text = f"{headline} {snippet}".lower()
                    if not work_auth:
                        if "golden visa" in combined_text:
                            work_auth = "UAE Golden Visa Holder"
                        elif "citizen" in combined_text:
                            work_auth = "Citizen"

                    # Clean mock/fallback company
                    if company == "Technology Co." or not company:
                        if " at " in headline:
                            company = headline.split(" at ")[-1].strip()
                        elif " @ " in headline:
                            company = headline.split(" @ ")[-1].strip()
                        else:
                            company = ""

                    # Clean mock/fallback location
                    if location in ("Location on Profile", "Location not specified", "Technology Co.", "UAE", ""):
                        # If candidate snippet has specific city (e.g. Delhi, India) prioritize over broad UAE/India
                        if "delhi" in snippet.lower():
                            location = "Delhi, India"
                        elif "dubai" in snippet.lower():
                            location = "Dubai, United Arab Emirates"
                        elif "abu dhabi" in snippet.lower():
                            location = "Abu Dhabi, United Arab Emirates"
                        elif location == "":
                            loc_match = re.search(r"\b(Dubai(?:,\s*United Arab Emirates)?|Abu Dhabi(?:,\s*United Arab Emirates)?|United Arab Emirates|UAE|Bengaluru|Bangalore|Hyderabad|Pune|Mumbai|Delhi(?:,\s*India)?|Chennai|San Francisco|New York|Seattle|London|Berlin|Toronto|Singapore|Remote)\b", f"{headline} {snippet}", re.IGNORECASE)
                            if loc_match:
                                location = loc_match.group(0).strip()
                            else:
                                location = ""

                    # Determine and assign target_role for multi-role sourcing
                    if not cand_role:
                        lower_info = f"{clean_name} {headline} {company} {snippet}".lower()
                        if any(k in lower_info for k in ["sana khan", "kavipriya", "srinithi", "biotechnology", "ai news", "artificial intelligence", "data analyst"]):
                            cand_role = "Senior AI Lead"
                        elif "marcus vance" in lower_info or "fullstack" in lower_info:
                            cand_role = "Senior Fullstack Engineer"
                        elif "priya sharma" in lower_info or "ui engineer" in lower_info:
                            cand_role = "Lead UI Engineer"
                        elif "alex rivera" in lower_info or "sarah chen" in lower_info or "frontend" in lower_info:
                            cand_role = "Senior Frontend Developer"
                        else:
                            cand_role = "Senior Fullstack Engineer"

                    if has_target_role:
                        conn.execute(
                            "UPDATE candidates SET name = ?, headline = ?, current_company = ?, location = ?, work_authorization = ?, target_role = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (clean_name, headline, company, location, work_auth, cand_role, r["id"])
                        )
                    else:
                        conn.execute(
                            "UPDATE candidates SET name = ?, headline = ?, current_company = ?, location = ?, work_authorization = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (clean_name, headline, company, location, work_auth, r["id"])
                        )
                conn.commit()
        except Exception as e:
            logger.warning("Sanitize existing candidates warning: %s", e)

    def save_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Inserts or updates a candidate profile in the local database."""
        cid = candidate_data.get("id") or f"cand_{int(time.time()*1000)}"
        canonical_url = candidate_data.get("canonical_url") or f"https://linkedin.com/in/{cid}"
        name = candidate_data.get("name", "Unknown Candidate")
        headline = candidate_data.get("headline", "")

        # Automatically clean compound name strings
        if "•" in name or "·" in name or "3rd+" in name or "2nd+" in name:
            parts = re.split(r"\s+[•·]\s*", name)
            clean_n = parts[0].strip()
            clean_n = re.sub(r"\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message|follow)\b", "", clean_n, flags=re.IGNORECASE).strip()
            if clean_n:
                name = clean_n
            if len(parts) > 1 and (not headline or headline in ("Professional on LinkedIn", "Software Professional", "")):
                rest = " • ".join(parts[1:]).strip()
                rest = re.sub(r"^(?:3rd\+|2nd\+|1st\+|3rd|2nd|1st)\s*", "", rest, flags=re.IGNORECASE)
                rest = re.sub(r"^[\|\-·•]\s*", "", rest).strip()
                for stopword in [" Follow ", " Connect ", " Message ", " Past:", " Current:"]:
                    if stopword in rest:
                        rest = rest.split(stopword)[0].strip()
                if rest and len(rest) > 2:
                    headline = rest

        # Initial company & location retrieval
        company = candidate_data.get("current_company") or candidate_data.get("company", "")
        location = candidate_data.get("location", "")
        if location in ("Location on Profile", "Technology Co."):
            location = ""

        # Decompose and clean LinkedIn search card text / headline noise
        parsed = clean_linkedin_card_text(headline)
        if parsed["headline"]:
            headline = parsed["headline"]
        if parsed["company"] and (not company or company == "Technology Co." or "followers" in company):
            company = parsed["company"]
        if parsed["location"] and not location:
            location = parsed["location"]

        if company == "Technology Co." or "followers" in company:
            company = parsed["company"] if parsed["company"] else ""
        if not company and headline:
            if " at " in headline:
                company = headline.split(" at ")[-1].strip()
            elif " @ " in headline:
                company = headline.split(" @ ")[-1].strip()

        current_location = candidate_data.get("current_location") or location
        pref_locs_json = json.dumps(candidate_data.get("preferred_work_locations", []))
        willingness = candidate_data.get("willingness_to_relocate", "Unknown")
        work_auth = candidate_data.get("work_authorization") or ""
        if not work_auth:
            combined_h = f"{headline} {candidate_data.get('raw_snippet', '')}".lower()
            if "golden visa" in combined_h:
                work_auth = "UAE Golden Visa Holder"
            elif "citizen" in combined_h:
                work_auth = "Citizen"

        loc_compat_status = candidate_data.get("location_compatibility_status", "Compatible")
        loc_compat_reason = candidate_data.get("location_compatibility_reason", "")
        dom_rel = candidate_data.get("domain_relevance", "Relevant")
        dom_rel_notes = candidate_data.get("domain_relevance_notes", "")

        years = float(candidate_data.get("experience_years") or 5.0)
        about = candidate_data.get("about", "")
        skills_json = json.dumps(candidate_data.get("skills", []))
        exp_json = json.dumps(candidate_data.get("experience_history", []))
        edu_json = json.dumps(candidate_data.get("education", []))
        certs_json = json.dumps(candidate_data.get("certifications", []))
        proj_json = json.dumps(candidate_data.get("projects", []))
        act_json = json.dumps(candidate_data.get("recent_activity", []))
        sec_scores_json = json.dumps(candidate_data.get("section_scores", {}))
        raw_snippet = candidate_data.get("raw_snippet", "")
        avatar_url = candidate_data.get("avatar_url") or candidate_data.get("avatar") or ""
        target_role = candidate_data.get("target_role") or candidate_data.get("job_title") or ""

        with self._get_connection() as conn:
            # Check if candidate with same canonical_url exists to keep stable primary key
            existing = conn.execute("SELECT id FROM candidates WHERE canonical_url = ?", (canonical_url,)).fetchone()
            if existing:
                cid = existing["id"]

            conn.execute("""
                INSERT INTO candidates (
                    id, canonical_url, name, headline, current_company, location,
                    current_location, preferred_work_locations, willingness_to_relocate,
                    work_authorization, location_compatibility_status, location_compatibility_reason,
                    domain_relevance, domain_relevance_notes,
                    experience_years, about, skills, experience_history,
                    education, certifications, projects, recent_activity, section_scores,
                    raw_snippet, avatar_url, target_role, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(canonical_url) DO UPDATE SET
                    name = excluded.name,
                    headline = excluded.headline,
                    current_company = excluded.current_company,
                    location = excluded.location,
                    current_location = CASE WHEN excluded.current_location != '' THEN excluded.current_location ELSE candidates.current_location END,
                    preferred_work_locations = excluded.preferred_work_locations,
                    willingness_to_relocate = excluded.willingness_to_relocate,
                    work_authorization = CASE WHEN excluded.work_authorization != '' THEN excluded.work_authorization ELSE candidates.work_authorization END,
                    location_compatibility_status = excluded.location_compatibility_status,
                    location_compatibility_reason = excluded.location_compatibility_reason,
                    domain_relevance = excluded.domain_relevance,
                    domain_relevance_notes = excluded.domain_relevance_notes,
                    experience_years = excluded.experience_years,
                    about = excluded.about,
                    skills = excluded.skills,
                    experience_history = excluded.experience_history,
                    education = excluded.education,
                    certifications = excluded.certifications,
                    projects = excluded.projects,
                    recent_activity = excluded.recent_activity,
                    section_scores = excluded.section_scores,
                    raw_snippet = excluded.raw_snippet,
                    avatar_url = CASE WHEN excluded.avatar_url IS NOT NULL AND excluded.avatar_url != '' THEN excluded.avatar_url ELSE candidates.avatar_url END,
                    target_role = CASE WHEN excluded.target_role != '' THEN excluded.target_role ELSE candidates.target_role END,
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                cid, canonical_url, name, headline, company, location,
                current_location, pref_locs_json, willingness,
                work_auth, loc_compat_status, loc_compat_reason,
                dom_rel, dom_rel_notes,
                years, about, skills_json, exp_json, edu_json, certs_json,
                proj_json, act_json, sec_scores_json, raw_snippet, avatar_url, target_role
            ))
            conn.commit()

        logger.info("Saved candidate profile to DB: %s (%s)", name, cid)

        # Cloud synchronization with Supabase if configured
        if supabase_service.is_configured():
            try:
                candidate_data_copy = dict(candidate_data)
                candidate_data_copy["id"] = cid
                candidate_data_copy["canonical_url"] = canonical_url
                supabase_service.upsert_candidate(candidate_data_copy)
            except Exception as e:
                logger.warning("Optional Supabase candidate sync error: %s", e)

        return cid

    def save_evaluation(self, eval_data: Dict[str, Any]) -> int:
        """Saves a candidate match evaluation with verbatim quote citations, normalized coverage, and section breakdown."""
        cid = eval_data.get("candidate_id")
        canonical_url = eval_data.get("canonical_url")
        job_title = eval_data.get("job_title", "Target Role")
        fit_score = float(eval_data.get("fit_score", 0.0))
        completeness = float(eval_data.get("completeness_score", 0.0))
        coverage = float(eval_data.get("evaluation_coverage", 100.0))
        match_level = eval_data.get("match_level", "Medium")
        dom_rel = eval_data.get("domain_relevance", "Relevant")
        dom_rel_notes = eval_data.get("domain_relevance_notes", "")
        loc_compat_json = json.dumps(eval_data.get("location_compatibility", {}))
        justification = eval_data.get("justification_summary", "")
        quotes_json = json.dumps(eval_data.get("evidence_quotes", []))
        missing_json = json.dumps(eval_data.get("missing_criteria", []))
        sec_scores_json = json.dumps(eval_data.get("section_scores", {}))
        cat_evals = eval_data.get("category_evaluations", {})
        # Serialize Pydantic or dict category_evaluations
        cat_evals_dict = {
            k: (v.model_dump() if hasattr(v, "model_dump") else (v.dict() if hasattr(v, "dict") else v))
            for k, v in cat_evals.items()
        } if isinstance(cat_evals, dict) else {}
        cat_evals_json = json.dumps(cat_evals_dict)

        with self._get_connection() as conn:
            # Ensure candidate_id matches the candidate record in DB
            row = conn.execute(
                "SELECT id FROM candidates WHERE id = ? OR canonical_url = ? OR canonical_url = ?",
                (cid, cid, canonical_url)
            ).fetchone()
            if row:
                cid = row["id"]
            else:
                # Insert placeholder candidate to satisfy foreign key requirement
                conn.execute("""
                    INSERT OR IGNORE INTO candidates (
                        id, canonical_url, name, headline, current_company, location, experience_years
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (cid, canonical_url or f"https://linkedin.com/in/{cid}", "Candidate Profile", "", "", "", 5.0))

            cursor = conn.execute("""
                INSERT INTO evaluations (
                    candidate_id, job_title, fit_score, completeness_score, evaluation_coverage,
                    match_level, domain_relevance, domain_relevance_notes, location_compatibility,
                    justification, evidence_quotes, missing_criteria, section_scores, category_evaluations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, job_title, fit_score, completeness, coverage,
                match_level, dom_rel, dom_rel_notes, loc_compat_json,
                justification, quotes_json, missing_json, sec_scores_json, cat_evals_json
            ))

            # Automatically update candidate's target_role if unassigned or general
            if job_title and job_title.lower() not in ("target role", "general requisition"):
                conn.execute(
                    "UPDATE candidates SET target_role = ? WHERE id = ? AND (target_role IS NULL OR target_role = '' OR target_role = 'General Requisition')",
                    (job_title, cid)
                )

            conn.commit()
            last_id = cursor.lastrowid

        # Cloud synchronization with Supabase if configured
        if supabase_service.is_configured():
            try:
                # Guarantee candidate exists in Supabase before evaluation insert (satisfies foreign key)
                cand_info = self.get_candidate_by_id_or_url(cid, canonical_url)
                if cand_info:
                    supabase_service.upsert_candidate(cand_info)

                eval_data_copy = dict(eval_data)
                eval_data_copy["candidate_id"] = cid
                eval_data_copy["canonical_url"] = canonical_url
                supabase_service.insert_evaluation(eval_data_copy)
            except Exception as e:
                logger.warning("Optional Supabase evaluation sync error: %s", e)

        return last_id

    def get_candidate_by_id_or_url(self, cid: str, canonical_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a single candidate dictionary from SQLite by ID or URL."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM candidates WHERE id = ? OR canonical_url = ? OR canonical_url = ?",
                (cid, canonical_url or cid, cid)
            ).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "canonical_url": row["canonical_url"],
                "name": row["name"],
                "headline": row["headline"],
                "current_company": row["current_company"],
                "location": row["location"],
                "current_location": row["current_location"] if "current_location" in row.keys() else row["location"],
                "preferred_work_locations": json.loads(row["preferred_work_locations"]) if "preferred_work_locations" in row.keys() and row["preferred_work_locations"] else [],
                "willingness_to_relocate": row["willingness_to_relocate"] if "willingness_to_relocate" in row.keys() else "Unknown",
                "work_authorization": row["work_authorization"] if "work_authorization" in row.keys() else "",
                "location_compatibility_status": row["location_compatibility_status"] if "location_compatibility_status" in row.keys() else "Compatible",
                "location_compatibility_reason": row["location_compatibility_reason"] if "location_compatibility_reason" in row.keys() else "",
                "domain_relevance": row["domain_relevance"] if "domain_relevance" in row.keys() else "Relevant",
                "domain_relevance_notes": row["domain_relevance_notes"] if "domain_relevance_notes" in row.keys() else "",
                "experience_years": row["experience_years"],
                "about": row["about"],
                "skills": json.loads(row["skills"]) if row["skills"] else [],
                "experience_history": json.loads(row["experience_history"]) if row["experience_history"] else [],
                "education": json.loads(row["education"]) if "education" in row.keys() and row["education"] else [],
                "certifications": json.loads(row["certifications"]) if "certifications" in row.keys() and row["certifications"] else [],
                "projects": json.loads(row["projects"]) if "projects" in row.keys() and row["projects"] else [],
                "recent_activity": json.loads(row["recent_activity"]) if "recent_activity" in row.keys() and row["recent_activity"] else [],
                "section_scores": json.loads(row["section_scores"]) if "section_scores" in row.keys() and row["section_scores"] else {},
                "raw_snippet": row["raw_snippet"],
                "avatar_url": row["avatar_url"],
                "target_role": row["target_role"] if "target_role" in row.keys() and row["target_role"] else "",
            }

    def get_all_candidates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves candidates paired with their latest evaluation from the database.
        Prefers Supabase if configured and reachable; seamlessly falls back to SQLite."""
        if supabase_service.is_configured():
            try:
                cloud_candidates = supabase_service.get_all_candidates(limit=limit)
                if cloud_candidates is not None:
                    # Supabase is configured and successfully reachable.
                    # When Supabase is empty (e.g. user removed all records), purge local SQLite candidates & evaluations
                    # so the local cache does not retain phantom records.
                    if len(cloud_candidates) == 0:
                        with self._get_connection() as conn:
                            conn.execute("DELETE FROM evaluations")
                            conn.execute("DELETE FROM candidates")
                            conn.commit()
                    else:
                        # Synchronize local SQLite with Supabase: remove any local candidates that were deleted from Supabase
                        cloud_ids = {c["id"] for c in cloud_candidates if c.get("id")}
                        with self._get_connection() as conn:
                            local_ids = [r[0] for r in conn.execute("SELECT id FROM candidates").fetchall()]
                            stale_ids = [lid for lid in local_ids if lid not in cloud_ids]
                            for sid in stale_ids:
                                conn.execute("DELETE FROM evaluations WHERE candidate_id = ?", (sid,))
                                conn.execute("DELETE FROM candidates WHERE id = ?", (sid,))
                            if stale_ids:
                                conn.commit()
                    return cloud_candidates
            except Exception as e:
                logger.warning("Supabase get_all_candidates fallback to SQLite: %s", e)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    c.id, c.canonical_url, c.name, c.headline, c.current_company,
                    c.location, c.current_location, c.preferred_work_locations, c.willingness_to_relocate,
                    c.work_authorization, c.location_compatibility_status, c.location_compatibility_reason,
                    c.domain_relevance as cand_domain_relevance, c.domain_relevance_notes as cand_domain_notes,
                    c.experience_years, c.about, c.skills, c.experience_history,
                    c.education, c.certifications, c.projects, c.recent_activity, c.section_scores,
                    c.raw_snippet, c.avatar_url, c.target_role, c.created_at,
                    e.fit_score, e.completeness_score, e.evaluation_coverage, e.match_level,
                    e.domain_relevance as eval_domain_relevance, e.domain_relevance_notes as eval_domain_notes,
                    e.location_compatibility, e.justification,
                    e.evidence_quotes, e.missing_criteria, e.section_scores as eval_section_scores,
                    e.category_evaluations, e.job_title
                FROM candidates c
                LEFT JOIN evaluations e ON e.id = (
                    SELECT id FROM evaluations WHERE candidate_id = c.id ORDER BY id DESC LIMIT 1
                )
                ORDER BY c.created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()

        results = []
        for r in rows:
            skills = json.loads(r["skills"]) if r["skills"] else []
            exp_history = json.loads(r["experience_history"]) if r["experience_history"] else []
            edu = json.loads(r["education"]) if "education" in r.keys() and r["education"] else []
            certs = json.loads(r["certifications"]) if "certifications" in r.keys() and r["certifications"] else []
            proj = json.loads(r["projects"]) if "projects" in r.keys() and r["projects"] else []
            activity = json.loads(r["recent_activity"]) if "recent_activity" in r.keys() and r["recent_activity"] else []
            sec_scores = json.loads(r["eval_section_scores"]) if "eval_section_scores" in r.keys() and r["eval_section_scores"] else (
                json.loads(r["section_scores"]) if "section_scores" in r.keys() and r["section_scores"] else {}
            )
            quotes = json.loads(r["evidence_quotes"]) if r["evidence_quotes"] else []
            missing = json.loads(r["missing_criteria"]) if r["missing_criteria"] else []
            cat_evals = json.loads(r["category_evaluations"]) if "category_evaluations" in r.keys() and r["category_evaluations"] else {}
            loc_compat = json.loads(r["location_compatibility"]) if "location_compatibility" in r.keys() and r["location_compatibility"] else {}
            pref_locs = json.loads(r["preferred_work_locations"]) if "preferred_work_locations" in r.keys() and r["preferred_work_locations"] else []

            dom_rel = r["eval_domain_relevance"] or r["cand_domain_relevance"] or "Relevant"
            dom_notes = r["eval_domain_notes"] or r["cand_domain_notes"] or ""
            target_role = (r["target_role"] if "target_role" in r.keys() and r["target_role"] else "") or r["job_title"] or ""

            results.append({
                "id": r["id"],
                "canonical_url": r["canonical_url"],
                "name": r["name"],
                "headline": r["headline"],
                "current_company": r["current_company"],
                "location": r["location"] or r["current_location"] or "",
                "current_location": r["current_location"] or r["location"] or "",
                "preferred_work_locations": pref_locs,
                "willingness_to_relocate": r["willingness_to_relocate"] or "Unknown",
                "work_authorization": r["work_authorization"] or "",
                "location_compatibility_status": r["location_compatibility_status"] or "Compatible",
                "location_compatibility_reason": r["location_compatibility_reason"] or "",
                "domain_relevance": dom_rel,
                "domain_relevance_notes": dom_notes,
                "experience_years": r["experience_years"],
                "about": r["about"],
                "target_role": target_role,
                "skills": skills,
                "experience_history": exp_history,
                "education": edu,
                "certifications": certs,
                "projects": proj,
                "recent_activity": activity,
                "section_scores": sec_scores,
                "category_evaluations": cat_evals,
                "location_compatibility": loc_compat,
                "raw_snippet": r["raw_snippet"],
                "avatar_url": r["avatar_url"],
                "created_at": r["created_at"],
                "fit_score": r["fit_score"],
                "completeness_score": r["completeness_score"],
                "evaluation_coverage": r["evaluation_coverage"] if "evaluation_coverage" in r.keys() and r["evaluation_coverage"] is not None else 100.0,
                "match_level": r["match_level"],
                "justification": r["justification"],
                "evidence_quotes": quotes,
                "missing_criteria": missing,
                "job_title": r["job_title"],
            })

        return results

    def get_sourcing_report(self) -> Dict[str, Any]:
        """Generates an executive summary of stored candidates, score distributions, and shortlists."""
        candidates = self.get_all_candidates(limit=100)
        total = len(candidates)
        verified = sum(1 for c in candidates if (c.get("fit_score") or 0) >= 80)
        in_review = sum(1 for c in candidates if 60 <= (c.get("fit_score") or 0) < 80)
        not_a_fit = sum(1 for c in candidates if 0 < (c.get("fit_score") or 0) < 60)
        unscored = sum(1 for c in candidates if c.get("fit_score") is None)

        avg_score = round(sum((c.get("fit_score") or 0) for c in candidates) / max(total, 1), 1)

        return {
            "total_candidates_stored": total,
            "average_fit_score": avg_score,
            "breakdown": {
                "high_match_verified": verified,
                "medium_in_review": in_review,
                "low_not_fit": not_a_fit,
                "pending_score": unscored,
            },
            "top_shortlist": sorted(
                [c for c in candidates if c.get("fit_score") is not None],
                key=lambda x: x["fit_score"],
                reverse=True
            )[:10],
        }

    def sync_sqlite_to_supabase(self) -> Dict[str, Any]:
        """Automatically mirrors all local SQLite candidate profiles and evaluations into Supabase."""
        if not supabase_service.is_configured():
            return {"synced": False, "message": "Supabase credentials not configured in .env."}

        try:
            status = supabase_service.check_connection()
            if not status.get("connected"):
                return {"synced": False, "message": status.get("message", "Supabase unreachable.")}

            candidates = self.get_all_candidates(limit=100)
            synced_cands = 0
            synced_evals = 0

            for c in candidates:
                try:
                    cand_id = supabase_service.upsert_candidate(c)
                    if cand_id:
                        synced_cands += 1
                        if c.get("fit_score") is not None:
                            eval_id = supabase_service.insert_evaluation({
                                "candidate_id": cand_id,
                                "job_title": c.get("job_title") or "Target Role",
                                "fit_score": float(c.get("fit_score", 0.0)),
                                "completeness_score": float(c.get("completeness_score", 0.0)),
                                "evaluation_coverage": float(c.get("evaluation_coverage", 100.0)),
                                "match_level": c.get("match_level", "Medium"),
                                "domain_relevance": c.get("domain_relevance", "Relevant"),
                                "domain_relevance_notes": c.get("domain_relevance_notes", ""),
                                "location_compatibility": c.get("location_compatibility", {}),
                                "justification": c.get("justification", ""),
                                "evidence_quotes": c.get("evidence_quotes", []),
                                "missing_criteria": c.get("missing_criteria", []),
                                "section_scores": c.get("section_scores", {}),
                                "category_evaluations": c.get("category_evaluations", {}),
                            })
                            if eval_id:
                                synced_evals += 1
                except Exception as err:
                    logger.warning("Error syncing candidate %s to Supabase: %s", c.get("name"), err)

            logger.info("Supabase sync complete: %d candidates, %d evaluations synced", synced_cands, synced_evals)
            return {
                "synced": True,
                "synced_candidates": synced_cands,
                "synced_evaluations": synced_evals,
                "total_local": len(candidates),
                "message": f"Successfully synced {synced_cands} candidates and {synced_evals} evaluations to Supabase PostgreSQL.",
            }
        except Exception as e:
            logger.error("Supabase sync failed: %s", e)
            return {"synced": False, "error": str(e)}

    @staticmethod
    def normalize_url(url: Optional[str]) -> str:
        """Normalizes candidate profile URL for strict deduplication."""
        if not url:
            return ""
        u = url.split("?")[0].rstrip("/").strip().lower()
        u = re.sub(r"^https?://(www\.)?", "", u)
        return u

    @staticmethod
    def normalize_name(name: Optional[str]) -> str:
        """Normalizes candidate name removing degree badges and whitespace."""
        if not name:
            return ""
        n = re.sub(r"\b(1st|2nd|3rd|3rd\+|view profile|connect|message|linkedin member)\b", "", name, flags=re.IGNORECASE)
        n = re.sub(r"[^\w\s]", " ", n)
        n = re.sub(r"\s+", " ", n).strip().lower()
        return n

    def get_known_candidate_identifiers(self) -> Dict[str, Set[str]]:
        """Retrieves normalized canonical URLs and names of all existing candidates in SQLite.
        
        Provides fast O(1) deduplication knowledge for autonomous sourcing agents.
        """
        known_urls: Set[str] = set()
        known_names: Set[str] = set()

        try:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT canonical_url, name FROM candidates").fetchall()
                for r in rows:
                    norm_u = self.normalize_url(r["canonical_url"])
                    if norm_u and len(norm_u) > 10:
                        known_urls.add(norm_u)
                    norm_n = self.normalize_name(r["name"])
                    if norm_n and len(norm_n) > 3:
                        known_names.add(norm_n)
        except Exception as e:
            logger.warning("Error fetching known candidate identifiers: %s", e)

        return {"urls": known_urls, "names": known_names}

    def is_candidate_duplicate(
        self,
        canonical_url: Optional[str],
        name: Optional[str],
        known_identifiers: Dict[str, Set[str]]
    ) -> bool:
        """Checks if a candidate card matches an already persisted profile."""
        norm_u = self.normalize_url(canonical_url)
        if norm_u and norm_u in known_identifiers.get("urls", set()):
            return True

        norm_n = self.normalize_name(name)
        if norm_n and norm_n in known_identifiers.get("names", set()):
            return True

        return False

    def update_candidate_status(self, candidate_id: str, new_status: str) -> bool:
        """Updates candidate status across local SQLite and Supabase."""
        success = False
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE candidates SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_status, candidate_id),
            )
            conn.commit()
            success = cursor.rowcount > 0

        if supabase_service.is_configured():
            try:
                supabase_service.update_candidate_status(candidate_id, new_status)
            except Exception as e:
                logger.warning("Supabase update_candidate_status error: %s", e)

        return success

    def delete_candidate(self, candidate_id: str) -> bool:
        """Deletes candidate from local SQLite and Supabase."""
        success = False
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if supabase_service.is_configured():
            try:
                supabase_service.delete_candidate(candidate_id)
            except Exception as e:
                logger.warning("Supabase delete_candidate error: %s", e)

        return success

    def clear_all_candidates(self) -> bool:
        """Clears all candidate records and evaluations from local SQLite and Supabase."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM evaluations")
            conn.execute("DELETE FROM candidates")
            conn.commit()

        if supabase_service.is_configured():
            try:
                supabase_service.clear_all_candidates()
            except Exception as e:
                logger.warning("Supabase clear_all_candidates error: %s", e)

        return True

    def sync_local_to_supabase(self) -> Dict[str, Any]:
        """Pushes all stored candidates and evaluations from local SQLite to Supabase."""
        if not supabase_service.is_configured():
            return {
                "success": False,
                "message": "Supabase credentials are not configured in .env. Please set SUPABASE_URL and SUPABASE_KEY.",
            }

        # Query local SQLite directly to avoid looping
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM candidates ORDER BY created_at ASC")
            raw_cands = cursor.fetchall()

        synced_candidates = 0
        synced_evaluations = 0
        errors = []

        for row in raw_cands:
            r = dict(row)
            try:
                cand_payload = {
                    "id": r.get("id"),
                    "canonical_url": r.get("canonical_url"),
                    "name": r.get("name"),
                    "headline": r.get("headline"),
                    "current_company": r.get("current_company"),
                    "location": r.get("location"),
                    "current_location": r.get("current_location"),
                    "preferred_work_locations": r.get("preferred_work_locations"),
                    "willingness_to_relocate": r.get("willingness_to_relocate"),
                    "work_authorization": r.get("work_authorization"),
                    "location_compatibility_status": r.get("location_compatibility_status"),
                    "location_compatibility_reason": r.get("location_compatibility_reason"),
                    "domain_relevance": r.get("domain_relevance"),
                    "domain_relevance_notes": r.get("domain_relevance_notes"),
                    "experience_years": r.get("experience_years"),
                    "about": r.get("about"),
                    "skills": r.get("skills"),
                    "experience_history": r.get("experience_history"),
                    "education": r.get("education"),
                    "certifications": r.get("certifications"),
                    "projects": r.get("projects"),
                    "recent_activity": r.get("recent_activity"),
                    "section_scores": r.get("section_scores"),
                    "raw_snippet": r.get("raw_snippet"),
                    "avatar_url": r.get("avatar_url"),
                    "status": r.get("status") or "New",
                }
                supabase_service.upsert_candidate(cand_payload)
                synced_candidates += 1

                # Sync associated evaluations
                with self._get_connection() as conn:
                    eval_rows = conn.execute("SELECT * FROM evaluations WHERE candidate_id = ?", (r["id"],)).fetchall()
                    for erow in eval_rows:
                        e = dict(erow)
                        supabase_service.insert_evaluation(e)
                        synced_evaluations += 1

            except Exception as err:
                errors.append(f"{r.get('name')}: {str(err)}")

        return {
            "success": True,
            "synced_candidates": synced_candidates,
            "synced_evaluations": synced_evaluations,
            "errors": errors[:5],
            "message": f"Successfully synchronized {synced_candidates} candidates and {synced_evaluations} evaluations to Supabase.",
        }

    def get_database_status(self) -> Dict[str, Any]:
        """Returns stats and connectivity status for both local SQLite and Supabase."""
        sqlite_stats = {"path": self.db_path, "candidates_count": 0, "evaluations_count": 0}
        try:
            with self._get_connection() as conn:
                c_row = conn.execute("SELECT count(*) FROM candidates").fetchone()
                e_row = conn.execute("SELECT count(*) FROM evaluations").fetchone()
                sqlite_stats["candidates_count"] = c_row[0] if c_row else 0
                sqlite_stats["evaluations_count"] = e_row[0] if e_row else 0
        except Exception as e:
            sqlite_stats["error"] = str(e)

        supabase_status = supabase_service.check_connection()
        return {
            "sqlite": sqlite_stats,
            "supabase": supabase_status,
            "active_storage": "supabase" if supabase_status.get("connected") else "sqlite",
        }

    def seed_default_jobs(self):
        """Seeds default core enterprise job requisitions if jobs table is empty."""
        try:
            with self._get_connection() as conn:
                count_row = conn.execute("SELECT count(*) FROM jobs").fetchone()
                if count_row and count_row[0] > 0:
                    return

            default_jobs = [
                {
                    "id": "job_senior_ai_lead",
                    "job_title": "Senior AI Lead",
                    "department": "AI & Machine Learning",
                    "seniority_level": "Lead / Principal",
                    "min_years_experience": 5.0,
                    "location": "Dubai, UAE",
                    "preferred_locations": ["Dubai", "Abu Dhabi", "United Arab Emirates", "India", "Remote"],
                    "mandatory_skills": [
                        "Python", "Machine Learning", "Deep Learning",
                        "LLM Application Development", "Prompt Engineering",
                        "RAG & Vector Databases", "Agentic AI", "System Design & Architecture"
                    ],
                    "preferred_skills": [
                        "MLOps", "LLMOps", "LangChain", "LlamaIndex", "FastAPI", "Docker", "Kubernetes"
                    ],
                    "technologies": ["Python", "PyTorch", "Hugging Face", "LangChain", "ChromaDB", "Pinecone", "FastAPI"],
                    "raw_jd": """Job Title: Senior AI Lead
Location: Dubai, UAE / Hybrid / Remote Willingness
Experience: 5+ Years in Applied AI / Machine Learning

We are seeking a Senior AI Lead to architect, deploy, and scale enterprise Agentic AI workflows, LLM applications, and RAG pipelines in Dubai, UAE. You will lead machine learning system design, prompt engineering optimizations, and MLOps lifecycle from prototype to high-throughput production.

Requirements:
- Strong hands-on proficiency in Python, PyTorch, Transformers, and LLM orchestration (LangChain, LlamaIndex).
- In-depth expertise in RAG architectures, vector embeddings, and vector databases (Pinecone, ChromaDB, pgvector).
- Proven track record designing autonomous multi-agent systems and tool-calling agent pipelines.
- Production MLOps and LLMOps experience (Docker, Kubernetes, model monitoring, evaluations).
- Strategic leadership and clear technical communication.""",
                },
                {
                    "id": "job_senior_fullstack_engineer",
                    "job_title": "Senior Fullstack Engineer",
                    "department": "Core Product Engineering",
                    "seniority_level": "Senior",
                    "min_years_experience": 5.0,
                    "location": "Austin, TX / Remote",
                    "preferred_locations": ["Austin, TX", "United States", "Remote"],
                    "mandatory_skills": [
                        "React", "Node.js", "Python", "PostgreSQL", "REST APIs", "Distributed System Design"
                    ],
                    "preferred_skills": [
                        "TypeScript", "AWS / Cloud Infrastructure", "Docker", "Redis", "CI/CD", "GraphQL"
                    ],
                    "technologies": ["React", "Node.js", "Python", "FastAPI", "PostgreSQL", "Redis", "AWS"],
                    "raw_jd": """Job Title: Senior Fullstack Engineer
Location: Austin, TX / Remote
Experience: 5+ Years Fullstack Engineering

Looking for a seasoned Senior Fullstack Engineer to design scalable web architectures, build responsive frontend user interfaces, and develop reliable distributed backend microservices.

Requirements:
- 5+ years of software development experience with React and Node.js or Python.
- Strong SQL proficiency with relational databases (PostgreSQL) and caching (Redis).
- Experience building and maintaining resilient RESTful APIs and microservice architectures.
- Experience with cloud platforms (AWS, GCP) and containerization (Docker).""",
                },
                {
                    "id": "job_lead_ui_engineer",
                    "job_title": "Lead UI Engineer",
                    "department": "Frontend & Design Systems",
                    "seniority_level": "Lead",
                    "min_years_experience": 6.0,
                    "location": "Bengaluru, India / Remote",
                    "preferred_locations": ["Bengaluru", "India", "Remote"],
                    "mandatory_skills": [
                        "React", "JavaScript (ES6+)", "Modern CSS / Tailwind",
                        "Design Systems", "Web Performance", "State Management"
                    ],
                    "preferred_skills": [
                        "Next.js", "Micro-Frontends", "Jest / Cypress Testing", "Accessibility (WCAG)"
                    ],
                    "technologies": ["React", "TypeScript", "Tailwind CSS", "Storybook", "Redux", "Zustand", "Vite"],
                    "raw_jd": """Job Title: Lead UI Engineer
Location: Bengaluru, India / Remote
Experience: 6+ Years Frontend Engineering

We need a Lead UI Engineer to drive our enterprise design systems, lead frontend architecture, ensure sub-second page performance, and guide engineering teams on modern component patterns.

Requirements:
- Extensive production mastery of React, modern CSS, and component design systems.
- Deep understanding of browser rendering performance, Core Web Vitals, and web accessibility.
- Experience mentoring frontend engineers and driving UI architecture decisions.""",
                },
                {
                    "id": "job_data_analyst",
                    "job_title": "Data Analyst / BI Specialist",
                    "department": "Data & Analytics",
                    "seniority_level": "Mid-Senior",
                    "min_years_experience": 3.0,
                    "location": "Dubai, UAE / Remote",
                    "preferred_locations": ["Dubai", "UAE", "India", "Remote"],
                    "mandatory_skills": [
                        "SQL", "Python", "Power BI", "Data Modeling", "Business Intelligence Analytics"
                    ],
                    "preferred_skills": [
                        "Tableau", "ETL Pipelines", "Data Warehousing", "Snowflake", "dbt"
                    ],
                    "technologies": ["SQL", "Python", "Pandas", "Power BI", "PostgreSQL", "Snowflake"],
                    "raw_jd": """Job Title: Data Analyst / BI Specialist
Location: Dubai, UAE / Remote
Experience: 3+ Years in Data Analytics & BI

Seeking a proactive Data Analyst to translate complex business requirements into high-impact BI dashboards, optimized data pipelines, and analytical data models.

Requirements:
- Advanced SQL querying, performance tuning, and relational schema modeling.
- Hands-on data visualization expertise using Power BI or Tableau.
- Python scripting (Pandas, NumPy) for automated data extraction and transformation.""",
                },
            ]

            for job in default_jobs:
                self.save_job(job)
            logger.info("Successfully seeded %d default job requisitions.", len(default_jobs))
        except Exception as e:
            logger.warning("Seed default jobs warning: %s", e)

    def save_job(self, job_data: Dict[str, Any]) -> str:
        """Inserts or updates a structured job description in SQLite and Supabase."""
        jid = job_data.get("id") or f"job_{int(time.time()*1000)}"
        title = (job_data.get("job_title") or job_data.get("title") or "Target Role").strip()
        dept = job_data.get("department") or "Engineering"
        seniority = job_data.get("seniority_level") or "Senior"
        min_exp = float(job_data.get("min_years_experience") or 3.0)
        loc = job_data.get("location") or ""
        pref_locs_json = json.dumps(job_data.get("preferred_locations") or ([loc] if loc else ["Dubai", "Remote"]))
        mand_skills_json = json.dumps(job_data.get("mandatory_skills") or [])
        pref_skills_json = json.dumps(job_data.get("preferred_skills") or [])
        tech_json = json.dumps(job_data.get("technologies") or [])
        crit_json = json.dumps(job_data.get("criteria_list") or [])
        raw_jd = job_data.get("raw_jd") or job_data.get("job_description") or ""

        with self._get_connection() as conn:
            existing = conn.execute("SELECT id FROM jobs WHERE job_title = ?", (title,)).fetchone()
            if existing:
                jid = existing["id"]

            conn.execute("""
                INSERT INTO jobs (
                    id, job_title, department, seniority_level, min_years_experience,
                    location, preferred_locations, mandatory_skills, preferred_skills,
                    technologies, criteria_list, raw_jd, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(job_title) DO UPDATE SET
                    department = excluded.department,
                    seniority_level = excluded.seniority_level,
                    min_years_experience = excluded.min_years_experience,
                    location = excluded.location,
                    preferred_locations = excluded.preferred_locations,
                    mandatory_skills = excluded.mandatory_skills,
                    preferred_skills = excluded.preferred_skills,
                    technologies = excluded.technologies,
                    criteria_list = excluded.criteria_list,
                    raw_jd = excluded.raw_jd,
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                jid, title, dept, seniority, min_exp, loc, pref_locs_json,
                mand_skills_json, pref_skills_json, tech_json, crit_json, raw_jd
            ))
            conn.commit()

        if supabase_service.is_configured():
            try:
                supabase_service.create_or_update_job({
                    "id": jid,
                    "job_title": title,
                    "department": dept,
                    "seniority_level": seniority,
                    "min_years_experience": min_exp,
                    "location": loc,
                    "preferred_locations": job_data.get("preferred_locations") or [],
                    "mandatory_skills": job_data.get("mandatory_skills") or [],
                    "preferred_skills": job_data.get("preferred_skills") or [],
                    "technologies": job_data.get("technologies") or [],
                    "criteria_list": job_data.get("criteria_list") or [],
                    "raw_jd": raw_jd,
                })
            except Exception as e:
                logger.warning("Optional Supabase job sync warning: %s", e)

        return jid

    def get_all_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves all stored job descriptions from SQLite."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
            jobs = []
            for r in rows:
                jobs.append({
                    "id": r["id"],
                    "job_title": r["job_title"],
                    "department": r["department"],
                    "seniority_level": r["seniority_level"],
                    "min_years_experience": r["min_years_experience"],
                    "location": r["location"],
                    "preferred_locations": json.loads(r["preferred_locations"]) if r["preferred_locations"] else [],
                    "mandatory_skills": json.loads(r["mandatory_skills"]) if r["mandatory_skills"] else [],
                    "preferred_skills": json.loads(r["preferred_skills"]) if r["preferred_skills"] else [],
                    "technologies": json.loads(r["technologies"]) if r["technologies"] else [],
                    "criteria_list": json.loads(r["criteria_list"]) if r["criteria_list"] else [],
                    "raw_jd": r["raw_jd"],
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                })
            return jobs

    def get_job_by_title_or_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single job description by ID or Title (case-insensitive)."""
        if not identifier:
            return None
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE id = ? OR LOWER(job_title) = LOWER(?) LIMIT 1",
                (identifier, identifier.strip())
            ).fetchone()
            if not row:
                row = conn.execute(
                    "SELECT * FROM jobs WHERE LOWER(job_title) LIKE ? LIMIT 1",
                    (f"%{identifier.lower().strip()}%",)
                ).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "job_title": row["job_title"],
                "department": row["department"],
                "seniority_level": row["seniority_level"],
                "min_years_experience": row["min_years_experience"],
                "location": row["location"],
                "preferred_locations": json.loads(row["preferred_locations"]) if row["preferred_locations"] else [],
                "mandatory_skills": json.loads(row["mandatory_skills"]) if row["mandatory_skills"] else [],
                "preferred_skills": json.loads(row["preferred_skills"]) if row["preferred_skills"] else [],
                "technologies": json.loads(row["technologies"]) if row["technologies"] else [],
                "criteria_list": json.loads(row["criteria_list"]) if row["criteria_list"] else [],
                "raw_jd": row["raw_jd"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }


db_service = DatabaseService()
