"""SQLite Database Persistence Service for Candidate Sourcing & Evaluation Reports.

Stores:
- Extracted Candidate Profiles (headline, company, experience, skills, raw resume text).
- Match Evaluations (fit scores, evidence citations, verbatim quotes, missing skills).
- Sourcing Run Summaries and aggregated reports for recruiters.
"""

import json
import logging
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("hiring_desk.db_service")

DB_DIR = os.path.abspath("./data")
DB_PATH = os.path.join(DB_DIR, "hiring_desk.db")


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

                CREATE INDEX IF NOT EXISTS idx_candidates_url ON candidates(canonical_url);
                CREATE INDEX IF NOT EXISTS idx_eval_candidate ON evaluations(candidate_id);
            """)

            # Safe migration check for existing tables
            cols = [r[1] for r in conn.execute("PRAGMA table_info(candidates)").fetchall()]
            if "avatar_url" not in cols:
                conn.execute("ALTER TABLE candidates ADD COLUMN avatar_url TEXT;")
        logger.info("SQLite database initialized at %s", self.db_path)

    def save_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Inserts or updates a candidate profile in the local database."""
        cid = candidate_data.get("id") or f"cand_{int(time.time()*1000)}"
        canonical_url = candidate_data.get("canonical_url") or f"https://linkedin.com/in/{cid}"
        name = candidate_data.get("name", "Unknown Candidate")
        headline = candidate_data.get("headline", "")
        company = candidate_data.get("current_company") or candidate_data.get("company", "")
        location = candidate_data.get("location", "")
        years = float(candidate_data.get("experience_years") or 5.0)
        about = candidate_data.get("about", "")
        skills_json = json.dumps(candidate_data.get("skills", []))
        exp_json = json.dumps(candidate_data.get("experience_history", []))
        raw_snippet = candidate_data.get("raw_snippet", "")
        avatar_url = candidate_data.get("avatar_url") or candidate_data.get("avatar") or ""

        with self._get_connection() as conn:
            # Check if candidate with same canonical_url exists to keep stable primary key
            existing = conn.execute("SELECT id FROM candidates WHERE canonical_url = ?", (canonical_url,)).fetchone()
            if existing:
                cid = existing["id"]

            conn.execute("""
                INSERT INTO candidates (
                    id, canonical_url, name, headline, current_company, location,
                    experience_years, about, skills, experience_history, raw_snippet, avatar_url, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(canonical_url) DO UPDATE SET
                    name = excluded.name,
                    headline = excluded.headline,
                    current_company = excluded.current_company,
                    location = excluded.location,
                    experience_years = excluded.experience_years,
                    about = excluded.about,
                    skills = excluded.skills,
                    experience_history = excluded.experience_history,
                    raw_snippet = excluded.raw_snippet,
                    avatar_url = CASE WHEN excluded.avatar_url IS NOT NULL AND excluded.avatar_url != '' THEN excluded.avatar_url ELSE candidates.avatar_url END,
                    updated_at = CURRENT_TIMESTAMP;
            """, (cid, canonical_url, name, headline, company, location, years, about, skills_json, exp_json, raw_snippet, avatar_url))
            conn.commit()

        logger.info("Saved candidate profile to DB: %s (%s)", name, cid)
        return cid

    def save_evaluation(self, eval_data: Dict[str, Any]) -> int:
        """Saves a candidate match evaluation with verbatim quote citations."""
        cid = eval_data.get("candidate_id")
        canonical_url = eval_data.get("canonical_url")
        job_title = eval_data.get("job_title", "Target Role")
        fit_score = float(eval_data.get("fit_score", 0.0))
        completeness = float(eval_data.get("completeness_score", 0.0))
        match_level = eval_data.get("match_level", "Medium")
        justification = eval_data.get("justification_summary", "")
        quotes_json = json.dumps(eval_data.get("evidence_quotes", []))
        missing_json = json.dumps(eval_data.get("missing_criteria", []))

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
                    candidate_id, job_title, fit_score, completeness_score,
                    match_level, justification, evidence_quotes, missing_criteria
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cid, job_title, fit_score, completeness, match_level, justification, quotes_json, missing_json))
            conn.commit()
            return cursor.lastrowid

    def get_all_candidates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves candidates paired with their latest evaluation from the database."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    c.id, c.canonical_url, c.name, c.headline, c.current_company,
                    c.location, c.experience_years, c.about, c.skills, c.experience_history,
                    c.raw_snippet, c.avatar_url, c.created_at,
                    e.fit_score, e.completeness_score, e.match_level, e.justification,
                    e.evidence_quotes, e.missing_criteria, e.job_title
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
            quotes = json.loads(r["evidence_quotes"]) if r["evidence_quotes"] else []
            missing = json.loads(r["missing_criteria"]) if r["missing_criteria"] else []
            results.append({
                "id": r["id"],
                "canonical_url": r["canonical_url"],
                "name": r["name"],
                "headline": r["headline"],
                "current_company": r["current_company"],
                "location": r["location"],
                "experience_years": r["experience_years"],
                "about": r["about"],
                "skills": skills,
                "experience_history": exp_history,
                "raw_snippet": r["raw_snippet"],
                "avatar_url": r["avatar_url"],
                "created_at": r["created_at"],
                "fit_score": r["fit_score"],
                "completeness_score": r["completeness_score"],
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


db_service = DatabaseService()
