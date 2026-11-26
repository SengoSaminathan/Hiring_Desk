"""Authentication and Company Profile API Routes.

Handles:
- User synchronization from Clerk authentication
- Recruiter & company profile creation, updates, and retrieval
- Multi-tenant company association for candidates and AI outreach
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from backend.app.services.db_service import db_service

logger = logging.getLogger("hiring_desk.auth_api")

router = APIRouter(tags=["Auth & Company Profile"])


class SyncUserRequest(BaseModel):
    id: str = Field(..., description="Unique Clerk User ID (e.g. user_...)")
    email: str = Field(..., description="Primary email address of the recruiter")
    full_name: Optional[str] = Field(None, description="Recruiter full name")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: Optional[str] = Field("Recruiter", description="Platform user role")
    company_id: Optional[str] = Field(None, description="Associated company ID")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")


class CompanyProfileRequest(BaseModel):
    id: Optional[str] = Field(None, description="Company ID (generated if not provided)")
    name: Optional[str] = Field(None, description="Organization / Company name")
    company_name: Optional[str] = Field(None, description="Alias for organization name")
    companyName: Optional[str] = Field(None, description="CamelCase alias for company name")
    industry: Optional[str] = Field(None, description="Industry or Core Domain")
    website: Optional[str] = Field(None, description="Company careers website")
    location: Optional[str] = Field(None, description="Primary Office / Sourcing Hub")
    employee_count: Optional[str] = Field("50-250", description="Organization size band")
    employeeCount: Optional[str] = Field(None, description="CamelCase alias for employee count")
    value_proposition: Optional[str] = Field(None, description="Value Proposition & Mission Context")
    valueProposition: Optional[str] = Field(None, description="CamelCase alias for value proposition")
    companyDetails: Optional[str] = Field(None, description="Detailed company mission")
    company_details: Optional[str] = Field(None, description="Detailed company mission")
    recruiter_name: Optional[str] = Field(None, description="Recruiter Full Name")
    recruiterName: Optional[str] = Field(None, description="CamelCase alias for recruiter name")
    recruiter_signature: Optional[str] = Field(None, description="Official Email / Message Signature")
    recruiterSignature: Optional[str] = Field(None, description="CamelCase alias for recruiter signature")
    user_id: Optional[str] = Field(None, description="User ID who created or updated the company")


@router.post("/api/auth/sync-user", status_code=status.HTTP_200_OK)
def sync_user(payload: SyncUserRequest):
    """Synchronizes Clerk authenticated user details to the local and cloud database."""
    try:
        user_dict = payload.model_dump()
        synced = db_service.upsert_user(user_dict)
        return {
            "status": "success",
            "message": "User synchronized successfully.",
            "user": synced,
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Failed to sync user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synchronize user: {str(e)}",
        )


@router.get("/api/auth/user/{user_id}", status_code=status.HTTP_200_OK)
def get_user_profile(user_id: str):
    """Retrieves user profile and linked company details."""
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' was not found.",
        )
    return {
        "status": "success",
        "user": user,
    }


@router.post("/api/company/profile", status_code=status.HTTP_200_OK)
def save_company_profile(payload: CompanyProfileRequest):
    """Saves or updates the recruiter's company profile and associates it with their user account."""
    try:
        data = payload.model_dump(exclude_unset=True)
        # Normalize company name
        c_name = data.get("name") or data.get("company_name") or data.get("companyName")
        if not c_name or not str(c_name).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name is required.",
            )
        data["name"] = str(c_name).strip()

        saved = db_service.upsert_company(data, user_id=data.get("user_id"))
        return {
            "status": "success",
            "message": "Company profile saved successfully.",
            "company": saved,
        }
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Failed to save company profile: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save company profile: {str(e)}",
        )


@router.get("/api/company/profile", status_code=status.HTTP_200_OK)
def get_company_profile_endpoint(
    user_id: Optional[str] = Query(None, description="Optional user ID filter"),
    company_id: Optional[str] = Query(None, description="Optional company ID filter"),
):
    """Retrieves the active company profile for the current user or platform default."""
    clean_uid = user_id if isinstance(user_id, str) and user_id.strip() else None
    clean_cid = company_id if isinstance(company_id, str) and company_id.strip() else None
    profile = db_service.get_company_profile(user_id=clean_uid, company_id=clean_cid)
    if not profile:
        return {
            "status": "not_configured",
            "company": None,
            "message": "No company profile has been configured yet.",
        }
    return {
        "status": "success",
        "company": profile,
    }
