"""Pydantic schemas for Candidate profiles, Evidence, and Match Evaluations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CandidateProfile(BaseModel):
    """Normalized candidate profile extracted from a source."""

    id: Optional[str] = Field(default=None, description="Unique candidate ID")
    canonical_url: str = Field(description="Profile URL")
    name: str = Field(description="Candidate full name")
    headline: str = Field(description="Current professional headline")
    current_company: Optional[str] = Field(default=None, description="Current employer")
    location: Optional[str] = Field(default=None, description="Geographic location")
    experience_years: Optional[float] = Field(default=None, description="Estimated years of experience")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    about: Optional[str] = Field(default=None, description="Candidate about / summary text")
    experience_history: List[Dict[str, Any]] = Field(default_factory=list, description="List of work experience entries")
    raw_snippet: Optional[str] = Field(default=None, description="Raw text snippet from search result")
    avatar_url: Optional[str] = Field(default=None, description="Candidate avatar / photo URL or base64 data URI")
    stored_in_db: bool = Field(default=False, description="Whether saved in local SQLite DB")


class EvidenceQuote(BaseModel):
    """Verbatim quote linking candidate claim to role criteria."""

    criterion_requirement: str = Field(description="Requirement being evaluated")
    verbatim_quote: str = Field(description="Exact quote from profile")
    is_match: bool = Field(description="Whether the quote confirms the requirement")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class MatchEvaluation(BaseModel):
    """Evaluation of a candidate against job criteria."""

    candidate_id: str
    fit_score: float = Field(ge=0.0, le=100.0, description="Overall fit score (0-100)")
    completeness_score: float = Field(ge=0.0, le=100.0, description="Evidence completeness (0-100)")
    match_level: str = Field(description="'High', 'Medium', 'Low', or 'Unclear'")
    justification_summary: str = Field(description="Executive summary of why candidate matches")
    evidence_quotes: List[EvidenceQuote] = Field(default_factory=list)
    missing_criteria: List[str] = Field(default_factory=list, description="Requirements with no found evidence")


class SearchRequest(BaseModel):
    """Input request for triggering browser-based sourcing."""

    keywords: str = Field(description="Search keywords or boolean query")
    max_results: int = Field(default=10, ge=1, le=50, description="Max candidate profiles to extract")
    mode: str = Field(default="linkedin", description="'linkedin' (direct browser) or 'simulation'")
    deep_scrape: bool = Field(default=True, description="Whether agent visits individual candidate profiles to extract full details")

    @field_validator("mode", mode="before")
    @classmethod
    def sanitize_mode(cls, v: Any) -> str:
        if not isinstance(v, str) or not v:
            return "linkedin"
        return v.strip().lower()


class SearchResponse(BaseModel):
    """Output response from candidate search."""

    candidates: List[CandidateProfile] = Field(default_factory=list)
    search_url: str
    status: str
    message: str


class EvaluatedCandidate(BaseModel):
    """Candidate profile paired with its AI match evaluation."""

    candidate: CandidateProfile
    evaluation: MatchEvaluation


class EvaluateCandidatesRequest(BaseModel):
    """Request to score a batch of candidates against criteria."""

    candidates: List[CandidateProfile]
    criteria: Any  # StructuredJobCriteria


class EvaluateCandidatesResponse(BaseModel):
    """Scored candidate shortlist."""

    evaluated_candidates: List[EvaluatedCandidate]
