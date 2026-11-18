import io
from fastapi import APIRouter, File, HTTPException, UploadFile
from backend.app.schemas.jobs import AnalyzeJobRequest, AnalyzeJobResponse
from backend.app.services.ai_service import ai_service
from backend.app.services.db_service import db_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(limit: int = 50):
    """Retrieves all active structured job descriptions and target roles."""
    jobs = db_service.get_all_jobs(limit=limit)
    return {"total": len(jobs), "jobs": jobs}


@router.post("")
async def create_job(request: dict):
    """Saves or updates a job description requisition."""
    try:
        jid = db_service.save_job(request)
        return {"status": "saved", "job_id": jid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save job requisition: {str(e)}")


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Retrieves a single job requisition by ID or Title."""
    job = db_service.get_job_by_title_or_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job


@router.post("/analyze", response_model=AnalyzeJobResponse)
async def analyze_job(request: AnalyzeJobRequest):
    """Parses a raw Job Description into structured criteria and generates an optimized search plan."""
    try:
        response = ai_service.analyze_job_description(request.raw_jd)
        response.raw_jd = request.raw_jd
        if not response.criteria.job_description:
            response.criteria.job_description = request.raw_jd

        # Automatically persist structured job into repository for multi-role workflows
        try:
            db_service.save_job({
                "job_title": response.criteria.job_title,
                "department": response.criteria.department,
                "seniority_level": response.criteria.seniority_level,
                "min_years_experience": response.criteria.min_years_experience,
                "location": response.criteria.city or response.criteria.country or "",
                "preferred_locations": response.criteria.preferred_locations,
                "mandatory_skills": response.criteria.mandatory_skills,
                "preferred_skills": response.criteria.preferred_skills,
                "technologies": response.criteria.technologies,
                "raw_jd": response.raw_jd,
            })
        except Exception:
            pass

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze job description: {str(e)}")


@router.post("/upload-jd", response_model=AnalyzeJobResponse)
async def upload_jd_document(file: UploadFile = File(...)):
    """Accepts uploaded JD files (.pdf, .docx, .txt, .md), extracts text, and populates custom criteria fields."""
    filename = (file.filename or "").lower()
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extracted_text = ""
    try:
        if filename.endswith(".pdf"):
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages_text = [page.extract_text() or "" for page in reader.pages]
            extracted_text = "\n".join(pages_text).strip()
        elif filename.endswith(".docx"):
            import docx
            doc = docx.Document(io.BytesIO(content))
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        paras.append(" | ".join(row_text))
            extracted_text = "\n".join(paras).strip()
        else:
            # Plain text, markdown, or generic document
            extracted_text = content.decode("utf-8", errors="replace").strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read document contents: {str(e)}")

    if len(extracted_text) < 15:
        raise HTTPException(status_code=400, detail="Extracted document text is too short to be a valid Job Description.")

    try:
        response = ai_service.analyze_job_description(extracted_text)
        response.raw_jd = extracted_text
        if not response.criteria.job_description:
            response.criteria.job_description = extracted_text

        # Automatically persist structured job into repository for multi-role workflows
        try:
            db_service.save_job({
                "job_title": response.criteria.job_title,
                "department": response.criteria.department,
                "seniority_level": response.criteria.seniority_level,
                "min_years_experience": response.criteria.min_years_experience,
                "location": response.criteria.city or response.criteria.country or "",
                "preferred_locations": response.criteria.preferred_locations,
                "mandatory_skills": response.criteria.mandatory_skills,
                "preferred_skills": response.criteria.preferred_skills,
                "technologies": response.criteria.technologies,
                "raw_jd": response.raw_jd,
            })
        except Exception:
            pass

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze uploaded job description: {str(e)}")


@router.post("/generate-queries", response_model=list)
async def generate_queries(request: dict):
    """Generates 3 recruiter-grade Boolean search queries from full structured requirements."""
    try:
        job_title = request.get("job_title", "Software Engineer")
        mandatory_skills = request.get("mandatory_skills", [])
        preferred_skills = request.get("preferred_skills", [])
        technologies = request.get("technologies", [])
        tools_platforms = request.get("tools_platforms", [])
        domain_expertise = request.get("domain_expertise", [])
        city = request.get("city")
        state_region = request.get("state_region") or request.get("state")
        country = request.get("country")
        raw_preferred = request.get("preferred_locations") or []

        loc_parts = [p.strip() for p in [city, state_region, country] if p and str(p).strip()]
        preferred_locations = list(raw_preferred) if isinstance(raw_preferred, list) else []
        for part in loc_parts:
            if part not in preferred_locations:
                preferred_locations.append(part)

        location = request.get("location") or (", ".join(loc_parts) if loc_parts else None)
        seniority_level = request.get("seniority_level", "Senior")

        # Automatically persist current configured job requisition to DB
        try:
            db_service.save_job({
                "job_title": job_title,
                "department": request.get("department", "Engineering"),
                "seniority_level": seniority_level,
                "min_years_experience": float(request.get("min_years_experience") or 3.0),
                "max_years_experience": float(request.get("max_years_experience") or 8.0),
                "location": location or city or "",
                "preferred_locations": preferred_locations,
                "mandatory_skills": mandatory_skills,
                "preferred_skills": preferred_skills,
                "technologies": technologies,
                "raw_jd": request.get("job_description", ""),
            })
        except Exception as save_err:
            logger.warning("Could not auto-persist job in generate-queries: %s", save_err)

        queries = ai_service.generate_strategic_queries(
            job_title=job_title,
            mandatory_skills=mandatory_skills,
            preferred_skills=preferred_skills,
            technologies=technologies,
            tools_platforms=tools_platforms,
            domain_expertise=domain_expertise,
            location=location,
            preferred_locations=preferred_locations,
            seniority_level=seniority_level,
        )
        return [q.model_dump() for q in queries]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate search queries: {str(e)}")


@router.post("/regenerate-query", response_model=dict)
async def regenerate_query(request: dict):
    """Regenerates a single strategic search query with updated parameters or variations."""
    try:
        strategy_id = request.get("strategy_id", "precision")
        job_title = request.get("job_title", "Software Engineer")
        mandatory_skills = request.get("mandatory_skills", [])
        preferred_skills = request.get("preferred_skills", [])
        technologies = request.get("technologies", [])
        domain_expertise = request.get("domain_expertise", [])
        city = request.get("city")
        state_region = request.get("state_region") or request.get("state")
        country = request.get("country")
        raw_preferred = request.get("preferred_locations") or []

        loc_parts = [p.strip() for p in [city, state_region, country] if p and str(p).strip()]
        preferred_locations = list(raw_preferred) if isinstance(raw_preferred, list) else []
        for part in loc_parts:
            if part not in preferred_locations:
                preferred_locations.append(part)

        location = request.get("location") or (", ".join(loc_parts) if loc_parts else None)

        query = ai_service.generate_single_query(
            strategy_id=strategy_id,
            job_title=job_title,
            mandatory_skills=mandatory_skills,
            preferred_skills=preferred_skills,
            technologies=technologies,
            domain_expertise=domain_expertise,
            location=location,
            preferred_locations=preferred_locations,
        )
        return query.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate query: {str(e)}")

