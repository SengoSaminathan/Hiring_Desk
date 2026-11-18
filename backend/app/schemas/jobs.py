"""Pydantic schemas for Job Descriptions and Search Planning."""

from typing import List, Optional
from pydantic import BaseModel, Field


class Criterion(BaseModel):
    """Individual requirement extracted from a JD."""

    category: str = Field(description="Category such as 'skills', 'experience', 'education', 'leadership'")
    requirement: str = Field(description="Specific requirement statement")
    is_mandatory: bool = Field(default=True, description="True if requirement is must-have")
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Relative scoring weight")


class StructuredJobCriteria(BaseModel):
    """Structured role requirements extracted from a raw JD or manual entry."""

    job_title: str = Field(description="Target role title")
    job_description: Optional[str] = Field(default=None, description="Detailed job description")
    department: Optional[str] = Field(default=None, description="Department or business unit")
    employment_type: Optional[str] = Field(default="Full-time", description="Employment type (Full-time, Part-time, Contract, Internship)")
    seniority_level: str = Field(default="Senior", description="Seniority level, e.g., 'Junior', 'Mid', 'Senior', 'Staff', 'Lead'")
    vacancies: Optional[int] = Field(default=1, description="Number of open positions")
    min_years_experience: Optional[float] = Field(default=None, description="Minimum years of experience")
    max_years_experience: Optional[float] = Field(default=None, description="Maximum years of experience")
    relevant_experience: Optional[str] = Field(default=None, description="Specific relevant experience criteria")
    leadership_experience: Optional[str] = Field(default=None, description="Leadership or management experience")
    mandatory_skills: List[str] = Field(default_factory=list, description="Must-have skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have skills")
    technologies: List[str] = Field(default_factory=list, description="Core technologies and frameworks")
    tools_platforms: List[str] = Field(default_factory=list, description="Tools, platforms, and infrastructure")
    domain_expertise: List[str] = Field(default_factory=list, description="Industry or domain-specific expertise")
    certifications: List[str] = Field(default_factory=list, description="Required or preferred certifications")
    country: Optional[str] = Field(default=None, description="Target country")
    state_region: Optional[str] = Field(default=None, description="State, province, or region")
    city: Optional[str] = Field(default=None, description="Primary city")
    location: Optional[str] = Field(default=None, description="Combined or primary location string")
    preferred_locations: List[str] = Field(default_factory=list, description="Multiple preferred locations")
    work_mode: Optional[str] = Field(default="Remote", description="Work mode (Remote, Hybrid, On-site)")
    willingness_to_relocate: Optional[bool] = Field(default=False, description="Willingness to relocate required")
    salary_range: Optional[str] = Field(default=None, description="Expected salary range")
    notice_period: Optional[str] = Field(default=None, description="Preferred notice period")
    education_requirements: Optional[str] = Field(default=None, description="Education or degree requirements")
    preferred_industries: List[str] = Field(default_factory=list, description="Target or preferred industries")
    companies_to_target: List[str] = Field(default_factory=list, description="Target companies to source from")
    companies_to_exclude: List[str] = Field(default_factory=list, description="Companies to exclude from search")
    additional_instructions: Optional[str] = Field(default=None, description="Specific instructions for AI search formulation")
    criteria_list: List[Criterion] = Field(default_factory=list, description="Detailed itemized criteria")


class SearchQueryOption(BaseModel):
    """Specific curated search query strategy."""

    id: str = Field(description="Strategy identifier, e.g. 'precision', 'lateral', 'domain'")
    label: str = Field(description="Recruiter-facing strategy label")
    query: str = Field(description="The executable search query string")
    description: str = Field(description="Explanation of why this query strategy was formed")
    strategy_type: str = Field(default="Precision Stack", description="Category of the strategy")


class SearchPlan(BaseModel):
    """Search plan generated for candidate sourcing."""

    linkedin_keywords: str = Field(description="Optimized keywords for LinkedIn search query")
    xray_query: str = Field(description="Google X-Ray boolean search string")
    target_titles: List[str] = Field(default_factory=list, description="Alternative job titles to search")
    target_skills: List[str] = Field(default_factory=list, description="Key skills included in the search")
    strategic_queries: List[SearchQueryOption] = Field(default_factory=list, description="3 curated strategic queries for recruiter review & edit")


class AnalyzeJobRequest(BaseModel):
    """Input request for parsing a Job Description."""

    raw_jd: str = Field(min_length=10, description="Raw text of the job description")
    role_title_hint: Optional[str] = Field(default=None, description="Optional job title hint")


class AnalyzeJobResponse(BaseModel):
    """Output response containing structured criteria and search plan."""

    criteria: StructuredJobCriteria
    search_plan: SearchPlan
    raw_jd: Optional[str] = Field(default=None, description="Raw document text extracted from the uploaded JD")


class GenerateQueriesRequest(BaseModel):
    """Request to generate 3 strategic LinkedIn search queries from structured requirements."""

    job_title: str
    mandatory_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    tools_platforms: List[str] = Field(default_factory=list)
    domain_expertise: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    min_years_experience: Optional[float] = None
    seniority_level: Optional[str] = "Senior"


class RegenerateQueryRequest(BaseModel):
    """Request to regenerate a single strategic search query."""

    job_title: str
    strategy_id: str  # 'precision', 'lateral', or 'domain'
    mandatory_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    domain_expertise: List[str] = Field(default_factory=list)
    location: Optional[str] = None

