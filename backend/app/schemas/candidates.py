"""Pydantic schemas for Candidate profiles, Evidence, and Match Evaluations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CategoryEvaluation(BaseModel):
    """Detailed evidence-based evaluation of a single criteria category."""

    category_name: str = Field(description="Evaluation category name (e.g. Experience, Skills, Education)")
    weight: float = Field(ge=0.0, le=1.0, description="Category weight in composite fit (0.0 to 1.0)")
    score: Optional[float] = Field(default=None, description="Score 0-100 if evaluated; None if section is not available on profile")
    evaluation_state: str = Field(
        default="available_relevant",
        description="'available_relevant', 'available_irrelevant', or 'not_available'",
    )
    status: str = Field(
        default="Matched",
        description="'Matched', 'Partially Matched', 'Not Matched', 'Not Available', or 'Needs Verification'",
    )
    evidence_found: str = Field(default="", description="Verbatim or summarized evidence from candidate profile")
    evidence_source: str = Field(default="", description="Source section (e.g. Experience, Headline, About, Certifications)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence level of assessment")
    explanation: str = Field(default="", description="Clear recruiter explanation of why this score/status was assigned")


class CandidateProfile(BaseModel):
    """Normalized candidate profile extracted from a source."""

    id: Optional[str] = Field(default=None, description="Unique candidate ID")
    canonical_url: str = Field(description="Profile URL")
    name: str = Field(description="Candidate full name")
    headline: str = Field(description="Current professional headline")
    current_company: Optional[str] = Field(default=None, description="Current employer")
    location: Optional[str] = Field(default=None, description="Geographic location")
    current_location: Optional[str] = Field(default=None, description="Candidate's current residential or work location")
    preferred_work_locations: List[str] = Field(default_factory=list, description="Locations where candidate is willing to work")
    willingness_to_relocate: str = Field(default="Unknown", description="'Yes', 'Likely', 'Unknown', or 'No'")
    work_authorization: Optional[str] = Field(default=None, description="Work authorization details (e.g. UAE Golden Visa, Citizen)")
    location_compatibility_status: str = Field(default="Compatible", description="'Compatible', 'Needs Verification', or 'Incompatible'")
    location_compatibility_reason: str = Field(default="", description="Detailed explanation of location compatibility")
    domain_relevance: str = Field(default="Relevant", description="'Highly Relevant', 'Relevant', 'Partially Relevant', or 'Not Relevant'")
    domain_relevance_notes: str = Field(default="", description="Explanation of industry and professional domain fit")
    experience_years: Optional[float] = Field(default=None, description="Estimated years of experience")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    about: Optional[str] = Field(default=None, description="Candidate about / summary text")
    experience_history: List[Dict[str, Any]] = Field(default_factory=list, description="List of work experience entries")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="Education history (school, degree, field, dates)")
    certifications: List[Dict[str, Any]] = Field(default_factory=list, description="Licenses & Certifications")
    projects: List[Dict[str, Any]] = Field(default_factory=list, description="Featured projects, repositories, publications")
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Recent LinkedIn posts, articles, activity")
    section_scores: Dict[str, Optional[float]] = Field(default_factory=dict, description="Itemized scores for all 7 sections (0-100 or null if unavailable)")
    raw_snippet: Optional[str] = Field(default=None, description="Raw text snippet from search result")
    avatar_url: Optional[str] = Field(default=None, description="Candidate avatar / photo URL or base64 data URI")
    target_role: Optional[str] = Field(default=None, description="Job role candidate was sourced for or targeted under")
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
    fit_score: float = Field(ge=0.0, le=100.0, description="Overall fit score normalized across evaluable sections (0-100)")
    completeness_score: float = Field(ge=0.0, le=100.0, description="Evidence completeness (0-100)")
    evaluation_coverage: float = Field(default=100.0, ge=0.0, le=100.0, description="Percentage of criteria categories evaluable from profile (0-100)")
    match_level: str = Field(description="'High', 'Medium', 'Low', or 'Unclear'")
    domain_relevance: str = Field(default="Relevant", description="'Highly Relevant', 'Relevant', 'Partially Relevant', or 'Not Relevant'")
    domain_relevance_notes: str = Field(default="", description="Detailed evaluation of industry/domain suitability")
    location_compatibility: Dict[str, Any] = Field(default_factory=dict, description="Location evaluation breakdown")
    justification_summary: str = Field(description="Executive summary of why candidate matches")
    evidence_quotes: List[EvidenceQuote] = Field(default_factory=list)
    missing_criteria: List[str] = Field(default_factory=list, description="Requirements with no found evidence")
    section_scores: Dict[str, Optional[float]] = Field(default_factory=dict, description="Itemized section fit scores (null if section unavailable)")
    category_evaluations: Dict[str, CategoryEvaluation] = Field(default_factory=dict, description="Evidence-based category breakdown")


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
