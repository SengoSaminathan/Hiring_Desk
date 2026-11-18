"""Tests for Candidate Profile Extraction: About, Licenses & Certifications, Projects, and Skills."""

import pytest
import re
import json
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.schemas.candidates import CandidateProfile
from backend.app.services.browser_service import _LinkedInBrowserEngine
from backend.app.services.db_service import db_service
from backend.app.services.ai_service import ai_service
from backend.app.schemas.jobs import StructuredJobCriteria, Criterion


SAMPLE_LINKEDIN_PROFILE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Santosh Pothula | LinkedIn</title></head>
<body>
  <!-- Top Card -->
  <div class="pv-text-details__left-panel">
    <h1 class="text-heading-xlarge">Santosh Pothula</h1>
    <div class="text-body-medium break-words">Senior BI & Data Engineering Specialist | Power BI, DAX, Snowflake, Fabric | Generative AI-Enabled Analytics</div>
    <span class="text-body-small inline t-black--light break-words">Hyderabad, Telangana, India</span>
  </div>

  <!-- Spacer to simulate page height & virtualization -->
  <div style="height: 400px;"></div>

  <!-- About Section -->
  <section id="about" class="artdeco-card">
    <div class="pvs-header__title-container">
      <h2 class="pvs-header__title">About</h2>
    </div>
    <div class="inline-show-more-text">
      <span>13+ years turning complex enterprise data into decisions — across Business Intelligence, data engineering, and increasingly Generative AI-augmented analytics. I specialize in Power BI semantic modeling, advanced DAX, and Snowflake/dbt-based data engineering, with deep experience building scalable star-schema models, performance-optimized reports, and governed RLS security frameworks for enterprise environments. Recent focus: bringing GenAI into the BI stack — designed Microsoft Copilot Studio agents and automated classification pipelines. Core tools: Power BI • DAX • Power Query • Snowflake • dbt • Microsoft Fabric • Azure Data Factory • Python • Copilot Studio • Claude/Azure OpenAI</span>
      <button class="inline-show-more-text__button">… more</button>
    </div>
  </section>

  <div style="height: 500px;"></div>

  <!-- Experience Section -->
  <section id="experience" class="artdeco-card">
    <div class="pvs-header__title-container">
      <h2 class="pvs-header__title">Experience</h2>
    </div>
    <ul class="pvs-list">
      <li>
        <span aria-hidden="true">Senior BI & Data Engineering Specialist</span>
        <span aria-hidden="true">Enterprise Tech Corp</span>
        <span aria-hidden="true">2020 - Present · 4 yrs</span>
        <span aria-hidden="true">Architected enterprise semantic models and automated reporting suites.</span>
      </li>
    </ul>
  </section>

  <div style="height: 500px;"></div>

  <!-- Education Section -->
  <section id="education" class="artdeco-card">
    <div class="pvs-header__title-container">
      <h2 class="pvs-header__title">Education</h2>
    </div>
    <ul class="pvs-list">
      <li>
        <span aria-hidden="true">Jawaharlal Nehru Technological University</span>
        <span aria-hidden="true">Bachelor of Technology - BTech, Computer Science</span>
        <span aria-hidden="true">2007 - 2011</span>
      </li>
    </ul>
  </section>

  <div style="height: 600px;"></div>

  <!-- Licenses & Certifications Section with Count (4) -->
  <section id="licenses_and_certifications" class="artdeco-card">
    <div class="pvs-header__title-container">
      <h2 class="pvs-header__title">Licenses &amp; certifications (4)</h2>
    </div>
    <ul class="pvs-list">
      <li>
        <span aria-hidden="true">Google Prompting Essentials Specialization</span>
        <span aria-hidden="true">Google</span>
        <span aria-hidden="true">Issued May 2024</span>
        <span aria-hidden="true">Credential ID GPE-884920</span>
        <span aria-hidden="true">Skills: Prompt Engineering · Generative AI</span>
        <a href="https://coursera.org/verify/specialization/GPE-884920" class="optional-action-target-wrapper">Show credential</a>
      </li>
      <li>
        <span aria-hidden="true">Microsoft Certified: Data Analyst Associate</span>
        <span aria-hidden="true">Microsoft</span>
        <span aria-hidden="true">Issued Dec 2023 · Expires Dec 2025</span>
        <span aria-hidden="true">Credential ID MS-DA-99231</span>
        <span aria-hidden="true">Skills: Power BI · DAX · Data Modeling</span>
        <a href="https://learn.microsoft.com/credentials/MS-DA-99231" class="optional-action-target-wrapper">Show credential</a>
      </li>
    </ul>
    <div class="pvs-list__footer-wrapper">
      <a href="https://www.linkedin.com/in/santoshpothula/details/certifications/" class="optional-action-target-wrapper">
        <span aria-hidden="true">Show all 4 licenses</span>
      </a>
    </div>
  </section>

  <div style="height: 600px;"></div>

  <!-- Projects Section with Count (5) -->
  <section id="projects" class="artdeco-card">
    <div class="pvs-header__title-container">
      <h2 class="pvs-header__title">Projects (5)</h2>
    </div>
    <ul class="pvs-list">
      <li>
        <div class="display-flex"><span aria-hidden="true">HS Cargo Classifier</span></div>
        <span aria-hidden="true">Jan 2024 - Present</span>
        <div class="inline-show-more-text">
          <span>Automated classification pipeline for HS customs codes using Claude API and Groq LLMs with high-throughput self-growing vector lookups.</span>
          <button class="inline-show-more-text__button">… more</button>
        </div>
        <span aria-hidden="true">Skills: Python · Streamlit · Machine Learning · Claude API</span>
        <a href="https://github.com/santoshpothula/hs-cargo-classifier">Show project</a>
      </li>
      <li>
        <div class="display-flex"><span aria-hidden="true">Job Hunt Agent</span></div>
        <span aria-hidden="true">May 2024 - Present</span>
        <div class="inline-show-more-text">
          <span>Autonomous agent for candidate search matching and automated qualification analysis.</span>
          <button class="inline-show-more-text__button">… more</button>
        </div>
        <span aria-hidden="true">Skills: Python · FastAPI · Playwright · LLM Orchestration</span>
      </li>
    </ul>
    <div class="pvs-list__footer-wrapper">
      <a href="https://www.linkedin.com/in/santoshpothula/details/projects/">
        <span aria-hidden="true">Show all 5 projects</span>
      </a>
    </div>
  </section>

  <div style="height: 600px;"></div>

  <!-- Skills Section with Count (65) -->
  <section id="skills" class="artdeco-card">
    <div class="pvs-header__title-container">
      <h2 class="pvs-header__title">Skills (65)</h2>
    </div>
    <ul class="pvs-list">
      <li>
        <div class="display-flex"><span aria-hidden="true">Metadata Management</span></div>
      </li>
      <li>
        <div class="display-flex"><span aria-hidden="true">Azure Data Lake</span></div>
      </li>
      <li>
        <div class="display-flex"><span aria-hidden="true">Power BI</span></div>
      </li>
      <li>
        <div class="display-flex"><span aria-hidden="true">DAX</span></div>
      </li>
      <li>
        <div class="display-flex"><span aria-hidden="true">Snowflake</span></div>
      </li>
    </ul>
    <div class="pvs-list__footer-wrapper">
      <a href="https://www.linkedin.com/in/santoshpothula/details/skills/">
        <span aria-hidden="true">Show all 65 skills</span>
      </a>
    </div>
  </section>
</body>
</html>
"""

SAMPLE_CERTS_SUBPAGE_HTML = """
<!DOCTYPE html>
<html>
<body>
  <main>
    <ul class="pvs-list">
      <li>
        <span aria-hidden="true">Google Prompting Essentials Specialization</span>
        <span aria-hidden="true">Google</span>
        <span aria-hidden="true">Issued May 2024</span>
        <span aria-hidden="true">Credential ID GPE-884920</span>
        <span aria-hidden="true">Skills: Prompt Engineering · Generative AI</span>
      </li>
      <li>
        <span aria-hidden="true">Microsoft Certified: Data Analyst Associate</span>
        <span aria-hidden="true">Microsoft</span>
        <span aria-hidden="true">Issued Dec 2023 · Expires Dec 2025</span>
        <span aria-hidden="true">Credential ID MS-DA-99231</span>
        <span aria-hidden="true">Skills: Power BI · DAX</span>
      </li>
      <li>
        <span aria-hidden="true">Snowflake SnowPro Core Certified</span>
        <span aria-hidden="true">Snowflake</span>
        <span aria-hidden="true">Issued Aug 2023</span>
        <span aria-hidden="true">Credential ID SNOW-CORE-1029</span>
        <span aria-hidden="true">Skills: Snowflake · Data Warehousing</span>
      </li>
      <li>
        <span aria-hidden="true">dbt Certified Developer</span>
        <span aria-hidden="true">dbt Labs</span>
        <span aria-hidden="true">Issued Feb 2023</span>
        <span aria-hidden="true">Credential ID DBT-DEV-5541</span>
        <span aria-hidden="true">Skills: dbt · SQL Data Transformation</span>
      </li>
    </ul>
  </main>
</body>
</html>
"""

SAMPLE_PROJECTS_SUBPAGE_HTML = """
<!DOCTYPE html>
<html>
<body>
  <main>
    <ul class="pvs-list">
      <li>
        <div class="display-flex"><span aria-hidden="true">HS Cargo Classifier</span></div>
        <span aria-hidden="true">Jan 2024 - Present</span>
        <div class="inline-show-more-text">
          <span>Automated classification pipeline for HS customs codes using Claude API and Groq LLMs with high-throughput self-growing vector lookups.</span>
        </div>
        <span aria-hidden="true">Skills: Python · Streamlit · Machine Learning · Claude API</span>
        <a href="https://github.com/santoshpothula/hs-cargo-classifier">Show project</a>
      </li>
      <li>
        <div class="display-flex"><span aria-hidden="true">Job Hunt Agent</span></div>
        <span aria-hidden="true">May 2024 - Present</span>
        <div class="inline-show-more-text">
          <span>Autonomous agent for candidate search matching and automated qualification analysis.</span>
        </div>
        <span aria-hidden="true">Skills: Python · FastAPI · Playwright · LLM Orchestration</span>
      </li>
      <li>
        <div class="display-flex"><span aria-hidden="true">Copilot Studio Natural-Language-to-SQL</span></div>
        <span aria-hidden="true">2023 - 2024</span>
        <div class="inline-show-more-text">
          <span>Enterprise Copilot Studio agent allowing business stakeholders to query Snowflake using natural language prompts.</span>
        </div>
        <span aria-hidden="true">Skills: Copilot Studio · SQL · Snowflake</span>
      </li>
      <li>
        <div class="display-flex"><span aria-hidden="true">Enterprise Star-Schema Semantic Lakehouse</span></div>
        <span aria-hidden="true">2022 - 2023</span>
        <div class="inline-show-more-text">
          <span>High-concurrency dimensional modeling in Microsoft Fabric and Azure Data Factory.</span>
        </div>
        <span aria-hidden="true">Skills: Microsoft Fabric · Azure Data Factory · DAX</span>
      </li>
      <li>
        <div class="display-flex"><span aria-hidden="true">Natural-Language-to-Dashboard Prototype</span></div>
        <span aria-hidden="true">2024</span>
        <div class="inline-show-more-text">
          <span>Generative AI prototype translating conversational requirements directly into Power BI visual specifications.</span>
        </div>
        <span aria-hidden="true">Skills: Generative AI · Power BI · Python</span>
      </li>
    </ul>
  </main>
</body>
</html>
"""

SAMPLE_SKILLS_SUBPAGE_HTML = """
<!DOCTYPE html>
<html>
<body>
  <main>
    <ul class="pvs-list">
      <li><div class="display-flex"><span aria-hidden="true">Metadata Management</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">Azure Data Lake</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">Power BI</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">DAX</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">Snowflake</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">dbt</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">Microsoft Fabric</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">Azure Data Factory</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">Generative AI</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">Large Language Models (LLM)</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">SQL</span></div></li>
      <li><div class="display-flex"><span aria-hidden="true">Python</span></div></li>
    </ul>
  </main>
</body>
</html>
"""


def test_candidate_profile_schema_fields():
    """Verify CandidateProfile schema supports certifications, projects, about, and skills."""
    cand = CandidateProfile(
        canonical_url="https://www.linkedin.com/in/santoshpothula",
        name="Santosh Pothula",
        headline="Senior BI & Data Engineering Specialist",
        about="13+ years turning complex enterprise data into decisions.",
        skills=["Metadata Management", "Azure Data Lake", "Power BI", "DAX", "Snowflake"],
        certifications=[
            {
                "name": "Google Prompting Essentials Specialization",
                "issuing_org": "Google",
                "issue_date": "Issued May 2024",
                "credential_id": "GPE-884920",
            },
            {
                "name": "Microsoft Certified: Data Analyst Associate",
                "issuing_org": "Microsoft",
                "issue_date": "Issued Dec 2023 · Expires Dec 2025",
                "credential_id": "MS-DA-99231",
            },
        ],
        projects=[
            {
                "title": "HS Cargo Classifier",
                "description": "Automated classification pipeline for HS customs codes.",
                "dates": "Jan 2024 - Present",
                "skills": ["Python", "Streamlit", "Machine Learning"],
            },
            {
                "title": "Job Hunt Agent",
                "description": "Autonomous agent for candidate search matching.",
                "dates": "May 2024 - Present",
                "skills": ["Python", "FastAPI", "Playwright"],
            },
        ],
    )
    assert len(cand.certifications) == 2
    assert cand.certifications[0]["name"] == "Google Prompting Essentials Specialization"
    assert cand.certifications[0]["credential_id"] == "GPE-884920"
    assert len(cand.projects) == 2
    assert cand.projects[0]["title"] == "HS Cargo Classifier"
    assert cand.projects[0]["skills"] == ["Python", "Streamlit", "Machine Learning"]
    assert len(cand.skills) == 5
    assert "Power BI" in cand.skills


def test_candidate_persistence_and_retrieval_roundtrip():
    """Verify SQLite persistence preserves certifications, projects, about, and skills without data loss."""
    cand_data = {
        "id": "cand_test_santosh_verification",
        "canonical_url": "https://www.linkedin.com/in/santoshpothula-test-verification",
        "name": "Santosh Pothula Test",
        "headline": "Senior BI Specialist | Power BI, Snowflake, Fabric",
        "location": "Hyderabad, India",
        "about": "13+ years turning complex enterprise data into decisions — across Business Intelligence, data engineering, and increasingly Generative AI.",
        "skills": ["Metadata Management", "Azure Data Lake", "Power BI", "DAX", "Snowflake", "dbt"],
        "certifications": [
            {
                "name": "Google Prompting Essentials Specialization",
                "issuing_org": "Google",
                "issue_date": "Issued May 2024",
                "credential_id": "GPE-884920",
            },
            {
                "name": "Microsoft Certified: Data Analyst Associate",
                "issuing_org": "Microsoft",
                "issue_date": "Issued Dec 2023 · Expires Dec 2025",
                "credential_id": "MS-DA-99231",
            },
        ],
        "projects": [
            {
                "title": "HS Cargo Classifier",
                "description": "Automated classification pipeline for HS customs codes using Claude API and Groq LLMs.",
                "dates": "Jan 2024 - Present",
                "skills": ["Python", "Streamlit", "Machine Learning"],
            },
            {
                "title": "Job Hunt Agent",
                "description": "Autonomous agent for candidate search matching and automated qualification analysis.",
                "dates": "May 2024 - Present",
                "skills": ["Python", "FastAPI", "Playwright"],
            },
        ],
    }

    # Save candidate to SQLite
    cid = db_service.save_candidate(cand_data)
    assert cid == "cand_test_santosh_verification"

    # Retrieve candidate by ID
    loaded = db_service.get_candidate_by_id_or_url("cand_test_santosh_verification")
    assert loaded is not None
    assert loaded["name"] == "Santosh Pothula Test"
    assert "… more" not in loaded["about"]
    assert len(loaded["certifications"]) == 2
    assert loaded["certifications"][0]["name"] == "Google Prompting Essentials Specialization"
    assert loaded["certifications"][0]["credential_id"] == "GPE-884920"
    assert len(loaded["projects"]) == 2
    assert loaded["projects"][0]["title"] == "HS Cargo Classifier"
    assert "… more" not in loaded["projects"][0]["description"]
    assert len(loaded["skills"]) == 6
    assert "Snowflake" in loaded["skills"]


def test_ai_evaluation_recognizes_certifications_and_projects():
    """Verify ai_service assigns available_relevant status and scores when certs and projects are populated."""
    candidate = CandidateProfile(
        id="cand_test_eval_populated",
        canonical_url="https://www.linkedin.com/in/santosh-eval-test",
        name="Santosh Pothula",
        headline="Senior BI & Data Engineering Specialist | Power BI, Snowflake, dbt",
        current_company="Enterprise Corp",
        location="Hyderabad, India",
        experience_years=13.0,
        about="13+ years turning complex enterprise data into decisions across Business Intelligence and data engineering.",
        skills=["Power BI", "DAX", "Snowflake", "dbt", "SQL", "Python"],
        certifications=[
            {"name": "Google Prompting Essentials Specialization", "issuing_org": "Google", "issue_date": "Issued May 2024", "credential_id": "GPE-123"},
            {"name": "Microsoft Certified: Data Analyst Associate", "issuing_org": "Microsoft", "issue_date": "Issued Dec 2023", "credential_id": "MS-DA-456"},
        ],
        projects=[
            {"title": "HS Cargo Classifier", "description": "Automated LLM classification pipeline for customs codes.", "dates": "2024", "skills": ["Python", "Groq"]},
            {"title": "Job Hunt Agent", "description": "Autonomous desktop recruiter assistant.", "dates": "2024", "skills": ["FastAPI", "Playwright"]},
        ],
    )

    criteria = StructuredJobCriteria(
        job_title="Senior Data Analyst & BI Specialist",
        seniority_level="Senior",
        min_years_experience=5.0,
        mandatory_skills=["Power BI", "SQL", "Snowflake"],
        preferred_skills=["dbt", "Python"],
        criteria_list=[
            Criterion(category="skills", requirement="Power BI & SQL", is_mandatory=True, weight=1.0),
        ],
    )

    evaluation = ai_service.evaluate_candidate(candidate, criteria)
    assert evaluation.fit_score >= 60.0
    cat_evals = evaluation.category_evaluations

    # Certifications evaluation must NOT be 'not_available'
    assert "certifications" in cat_evals
    assert cat_evals["certifications"].evaluation_state in ["available_relevant", "available_irrelevant"]
    assert cat_evals["certifications"].status != "Not Available"
    assert "Google Prompting Essentials" in cat_evals["certifications"].evidence_found or "Microsoft Certified" in cat_evals["certifications"].evidence_found

    # Projects evaluation must NOT be 'not_available'
    assert "projects" in cat_evals
    assert cat_evals["projects"].evaluation_state in ["available_relevant", "available_irrelevant"]
    assert cat_evals["projects"].status != "Not Available"
    assert "HS Cargo Classifier" in cat_evals["projects"].evidence_found or "Job Hunt Agent" in cat_evals["projects"].evidence_found

    # Section scores must be non-null for certs and projects
    assert evaluation.section_scores["certifications"] is not None
    assert evaluation.section_scores["projects"] is not None


@pytest.mark.asyncio
async def test_full_profile_extraction_logic():
    """Verify profile extraction parses About, Certifications, Projects, and Skills cleanly."""
    candidate = CandidateProfile(
        canonical_url="https://www.linkedin.com/in/santoshpothula",
        name="Santosh Pothula",
        headline="Initial Headline",
    )

    def mock_evaluate(script, *args, **kwargs):
        s = script.lower()
        if "pv-text-details__left-panel" in s or "text-heading-xlarge" in s:
            return {
                "name": "Santosh Pothula",
                "headline": "Senior BI & Data Engineering Specialist | Power BI, DAX, Snowflake, Fabric | Generative AI-Enabled Analytics",
                "location": "Hyderabad, Telangana, India",
                "avatar": "https://media.licdn.com/dms/image/v2/mock/avatar.jpg",
            }
        if "/details/" in s and "totalheight" in s:
            return {
                "certifications": "https://www.linkedin.com/in/santoshpothula/details/certifications/",
                "projects": "https://www.linkedin.com/in/santoshpothula/details/projects/",
                "skills": "https://www.linkedin.com/in/santoshpothula/details/skills/",
            }
        if "aboutanchor" in s or "about" in s and "sec.scrollintoview" in s:
            return (
                "13+ years turning complex enterprise data into decisions — across Business Intelligence, "
                "data engineering, and increasingly Generative AI-augmented analytics. I specialize in Power BI semantic modeling, "
                "advanced DAX, and Snowflake/dbt-based data engineering, with deep experience building scalable star-schema models, "
                "performance-optimized reports, and governed RLS security frameworks for enterprise environments. Recent focus: "
                "bringing GenAI into the BI stack — designed Microsoft Copilot Studio agents and automated classification pipelines. "
                "Core tools: Power BI • DAX • Power Query • Snowflake • dbt • Microsoft Fabric • Azure Data Factory • Python • Copilot Studio • Claude/Azure OpenAI"
            )
        if "actanchor" in s:
            return []
        if "expanchor" in s:
            return [
                {
                    "title": "Senior BI & Data Engineering Specialist",
                    "role": "Senior BI & Data Engineering Specialist",
                    "company": "Enterprise Tech Corp",
                    "dates": "2020 - Present · 4 yrs",
                    "description": "Architected enterprise semantic models and automated reporting suites.",
                }
            ]
        if "eduanchor" in s:
            return [
                {
                    "school": "Jawaharlal Nehru Technological University",
                    "degree": "Bachelor of Technology - BTech, Computer Science",
                    "dates": "2007 - 2011",
                }
            ]
        if "licenses_and_certifications" in s:
            return {
                "items": [
                    {
                        "name": "Google Prompting Essentials Specialization",
                        "issuing_org": "Google",
                        "issue_date": "Issued May 2024",
                        "credential_id": "GPE-884920",
                        "skills": ["Prompt Engineering", "Generative AI"],
                        "url": "https://coursera.org/verify/specialization/GPE-884920",
                    },
                    {
                        "name": "Microsoft Certified: Data Analyst Associate",
                        "issuing_org": "Microsoft",
                        "issue_date": "Issued Dec 2023 · Expires Dec 2025",
                        "credential_id": "MS-DA-99231",
                        "skills": ["Power BI", "DAX", "Data Modeling"],
                        "url": "https://learn.microsoft.com/credentials/MS-DA-99231",
                    },
                ],
                "total_expected": 4,
                "detail_link": "https://www.linkedin.com/in/santoshpothula/details/certifications/",
            }
        if "featured_projects" in s:
            return {
                "items": [
                    {
                        "title": "HS Cargo Classifier",
                        "description": "Automated classification pipeline for HS customs codes using Claude API and Groq LLMs with high-throughput self-growing vector lookups.",
                        "dates": "Jan 2024 - Present",
                        "skills": ["Python", "Streamlit", "Machine Learning", "Claude API"],
                        "url": "https://github.com/santoshpothula/hs-cargo-classifier",
                    },
                    {
                        "title": "Job Hunt Agent",
                        "description": "Autonomous agent for candidate search matching and automated qualification analysis.",
                        "dates": "May 2024 - Present",
                        "skills": ["Python", "FastAPI", "Playwright", "LLM Orchestration"],
                        "url": "",
                    },
                ],
                "total_expected": 5,
                "detail_link": "https://www.linkedin.com/in/santoshpothula/details/projects/",
            }
        if "['skills']" in s:
            return {
                "items": ["Metadata Management", "Azure Data Lake", "Power BI", "DAX", "Snowflake"],
                "total_expected": 65,
                "detail_link": "https://www.linkedin.com/in/santoshpothula/details/skills/",
            }
        return None

    page = AsyncMock()
    page.evaluate = AsyncMock(side_effect=mock_evaluate)

    engine = _LinkedInBrowserEngine()
    engine._update_overlay = AsyncMock()
    engine._dismiss_common_overlays = AsyncMock()

    extracted = await engine._visit_and_extract_profile(page, candidate, skip_navigation=True)

    # 1. Verify About section is fully extracted and cleaned of trailing "...more"
    assert extracted.about is not None
    assert "13+ years turning complex enterprise data into decisions" in extracted.about
    assert "Claude/Azure OpenAI" in extracted.about
    assert not extracted.about.strip().endswith("… more")
    assert not extracted.about.strip().endswith("...more")
    assert not extracted.about.strip().endswith("more")

    # 2. Verify Licenses & Certifications
    assert len(extracted.certifications) >= 2
    cert_names = [c["name"] for c in extracted.certifications]
    assert "Google Prompting Essentials Specialization" in cert_names
    assert "Microsoft Certified: Data Analyst Associate" in cert_names

    # Check credential_id and issuing_org
    g_cert = next(c for c in extracted.certifications if "Google" in c["name"])
    assert g_cert["issuing_org"] == "Google"
    assert "May 2024" in g_cert["issue_date"]
    assert "GPE-884920" in g_cert["credential_id"]

    # 3. Verify Projects
    assert len(extracted.projects) >= 2
    proj_titles = [p["title"] for p in extracted.projects]
    assert "HS Cargo Classifier" in proj_titles
    assert "Job Hunt Agent" in proj_titles

    hs_proj = next(p for p in extracted.projects if p["title"] == "HS Cargo Classifier")
    assert "Automated classification pipeline" in hs_proj["description"]
    assert not hs_proj["description"].endswith("… more")
    assert not hs_proj["description"].endswith("...more")
    assert hs_proj["dates"] == "Jan 2024 - Present"
    assert any("Python" in s for s in hs_proj["skills"])

    # 4. Verify Skills
    assert len(extracted.skills) >= 5
    assert "Metadata Management" in extracted.skills
    assert "Power BI" in extracted.skills
    assert "Snowflake" in extracted.skills
    assert "DAX" in extracted.skills

    # 5. Verify Raw Snippet Dossier
    assert "About:" in extracted.raw_snippet
    assert "Certifications:" in extracted.raw_snippet
    assert "Projects:" in extracted.raw_snippet
    assert "Skills:" in extracted.raw_snippet


def test_html_parsing_extracts_certs_projects_about_skills():
    """Verify BeautifulSoup DOM parser on sample profile and subpage HTML fixtures."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(SAMPLE_LINKEDIN_PROFILE_HTML, "html.parser")

    # 1. About section
    about_sec = soup.find("section", id="about")
    assert about_sec is not None
    for btn in about_sec.find_all("button", class_="inline-show-more-text__button"):
        btn.decompose()
    about_text = about_sec.find("div", class_="inline-show-more-text").get_text(strip=True)
    about_text = re.sub(r"[\s\n\r]*[…\.]+\s*(?:more|see more)\s*$", "", about_text)
    assert "13+ years turning complex enterprise data into decisions" in about_text
    assert not about_text.endswith("… more")

    # 2. Licenses & Certifications from profile
    cert_sec = soup.find("section", id="licenses_and_certifications")
    assert cert_sec is not None
    cert_items = []
    for li in cert_sec.select("ul.pvs-list > li"):
        spans = [s.get_text(strip=True) for s in li.find_all("span", attrs={"aria-hidden": "true"})]
        name = spans[0] if spans else ""
        org = spans[1] if len(spans) > 1 else ""
        cred_id = ""
        for s in spans:
            if "credential id" in s.lower():
                cred_id = re.sub(r"credential\s*id\s*[:\-]?\s*", "", s, flags=re.I).strip()
        cert_items.append({"name": name, "issuing_org": org, "credential_id": cred_id})
    assert len(cert_items) == 2
    assert cert_items[0]["name"] == "Google Prompting Essentials Specialization"
    assert cert_items[0]["credential_id"] == "GPE-884920"
    assert cert_items[1]["name"] == "Microsoft Certified: Data Analyst Associate"

    # 3. Projects from profile
    proj_sec = soup.find("section", id="projects")
    assert proj_sec is not None
    proj_items = []
    for li in proj_sec.select("ul.pvs-list > li"):
        t_span = li.select_one("div.display-flex span[aria-hidden='true']")
        title = t_span.get_text(strip=True) if t_span else ""
        desc_el = li.find("div", class_="inline-show-more-text")
        desc = ""
        if desc_el:
            for b in desc_el.find_all("button"):
                b.decompose()
            desc = desc_el.get_text(strip=True)
            desc = re.sub(r"[\s\n\r]*[…\.]+\s*(?:more|see more)\s*$", "", desc)
        proj_items.append({"title": title, "description": desc})
    assert len(proj_items) == 2
    assert proj_items[0]["title"] == "HS Cargo Classifier"
    assert "Automated classification pipeline" in proj_items[0]["description"]
    assert not proj_items[0]["description"].endswith("… more")

    # 4. Skills from profile
    skill_sec = soup.find("section", id="skills")
    assert skill_sec is not None
    skills = [
        s.get_text(strip=True)
        for s in skill_sec.select("ul.pvs-list > li div.display-flex span[aria-hidden='true']")
    ]
    assert len(skills) == 5
    assert "Metadata Management" in skills
    assert "Power BI" in skills
    assert "Snowflake" in skills

    # 5. Certifications subpage
    sub_cert_soup = BeautifulSoup(SAMPLE_CERTS_SUBPAGE_HTML, "html.parser")
    sub_certs = []
    for li in sub_cert_soup.select("main ul.pvs-list > li"):
        spans = [s.get_text(strip=True) for s in li.find_all("span", attrs={"aria-hidden": "true"})]
        name = spans[0] if spans else ""
        sub_certs.append(name)
    assert len(sub_certs) == 4
    assert "Snowflake SnowPro Core Certified" in sub_certs
    assert "dbt Certified Developer" in sub_certs

    # 6. Projects subpage
    sub_proj_soup = BeautifulSoup(SAMPLE_PROJECTS_SUBPAGE_HTML, "html.parser")
    sub_projs = []
    for li in sub_proj_soup.select("main ul.pvs-list > li"):
        t_span = li.select_one("div.display-flex span[aria-hidden='true']")
        if t_span:
            sub_projs.append(t_span.get_text(strip=True))
    assert len(sub_projs) == 5
    assert "Copilot Studio Natural-Language-to-SQL" in sub_projs
    assert "Enterprise Star-Schema Semantic Lakehouse" in sub_projs
