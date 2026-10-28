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
    """Structured role requirements extracted from a raw JD."""

    job_title: str = Field(description="Target role title")
    seniority_level: str = Field(description="Seniority level, e.g., 'Junior', 'Mid', 'Senior', 'Staff', 'Lead'")
    min_years_experience: Optional[float] = Field(default=None, description="Minimum years of experience")
    mandatory_skills: List[str] = Field(default_factory=list, description="Must-have skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have skills")
    criteria_list: List[Criterion] = Field(default_factory=list, description="Detailed itemized criteria")


class SearchPlan(BaseModel):
    """Search plan generated for candidate sourcing."""

    linkedin_keywords: str = Field(description="Optimized keywords for LinkedIn search query")
    xray_query: str = Field(description="Google X-Ray boolean search string")
    target_titles: List[str] = Field(default_factory=list, description="Alternative job titles to search")
    target_skills: List[str] = Field(default_factory=list, description="Key skills included in the search")


class AnalyzeJobRequest(BaseModel):
    """Input request for parsing a Job Description."""

    raw_jd: str = Field(min_length=10, description="Raw text of the job description")
    role_title_hint: Optional[str] = Field(default=None, description="Optional job title hint")


class AnalyzeJobResponse(BaseModel):
    """Output response containing structured criteria and search plan."""

    criteria: StructuredJobCriteria
    search_plan: SearchPlan
