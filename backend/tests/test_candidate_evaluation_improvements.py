import pytest
from backend.app.schemas.candidates import CandidateProfile
from backend.app.schemas.jobs import StructuredJobCriteria
from backend.app.services.ai_service import AIService

@pytest.fixture
def ai_service():
    service = AIService()
    service.is_ai_available = lambda: False
    return service

# ---------------------------------------------------------
# 1. Preferred Location Search & Mobility Logic Tests
# ---------------------------------------------------------

def test_location_compatibility_current_resident(ai_service):
    """Candidate living in Dubai is directly compatible with Dubai roles."""
    candidate = CandidateProfile(
        canonical_url="https://linkedin.com/in/tariq",
        name="Tariq Mansoor",
        headline="Senior AI Engineer at Careem",
        current_location="Dubai, United Arab Emirates",
        preferred_work_locations=["Dubai, UAE"],
        willingness_to_relocate="Yes",
    )
    res = ai_service.analyze_location_compatibility(candidate, ["Dubai", "UAE"])
    assert res["status"] == "Compatible"
    assert "dubai" in res["reason"].lower()

def test_location_compatibility_abu_dhabi_golden_visa(ai_service):
    """Candidate in Abu Dhabi with UAE Golden Visa is fully compatible with Dubai."""
    candidate = CandidateProfile(
        canonical_url="https://linkedin.com/in/hamza",
        name="Hamza A.",
        headline="Head of AI and Technology | UAE Golden Visa Holder",
        current_location="Abu Dhabi Emirate, United Arab Emirates",
        work_authorization="UAE Golden Visa Holder",
        willingness_to_relocate="Likely",
    )
    res = ai_service.analyze_location_compatibility(candidate, ["Dubai", "UAE"])
    assert res["status"] == "Compatible"
    assert "golden visa" in res["reason"].lower()

def test_location_compatibility_unknown_relocation_not_rejected(ai_service):
    """Candidate from India whose relocation willingness is unknown MUST NOT be rejected."""
    candidate = CandidateProfile(
        canonical_url="https://linkedin.com/in/vikram",
        name="Vikram Malhotra",
        headline="Staff Machine Learning Engineer",
        current_location="Bengaluru, Karnataka, India",
        willingness_to_relocate="Unknown",
    )
    res = ai_service.analyze_location_compatibility(candidate, ["Dubai", "UAE"])
    assert res["status"] == "Needs Verification"
    assert "not rejected" in res["reason"].lower()

def test_location_compatibility_explicit_refusal_is_incompatible(ai_service):
    """Candidate explicitly unwilling to relocate/work in Dubai is Incompatible."""
    candidate = CandidateProfile(
        canonical_url="https://linkedin.com/in/johndoe",
        name="John Doe",
        headline="AI Lead (US Remote Only - No Relocation)",
        current_location="San Francisco, CA, USA",
        willingness_to_relocate="No",
    )
    res = ai_service.analyze_location_compatibility(candidate, ["Dubai", "UAE"])
    assert res["status"] == "Incompatible"
    assert "unwilling" in res["reason"].lower()

# ---------------------------------------------------------
# 2. Industry & Professional Domain Relevance Filtering
# ---------------------------------------------------------

def test_domain_relevance_edtech_teacher_training_screened(ai_service):
    """Candidate with 'Head of AI' in headline but working as STEM teacher trainer is classified as Not Relevant or Partially Relevant."""
    candidate = CandidateProfile(
        canonical_url="https://linkedin.com/in/hamza",
        name="Hamza A.",
        headline="Head of AI and Technology | Certified Master Trainer | EdTech and Innovation",
        experience_history=[
            {
                "role": "Head of AI and Technology",
                "company": "Ministry of Education - UAE",
                "dates": "Sep 2025 - Present",
                "description": "Guide school tech leaders in integrating technology effectively into educational curriculum."
            },
            {
                "role": "Professional Development Trainer - Sustainability, Innovation and Technology",
                "company": "Ministry of Education - UAE",
                "dates": "Jul 2022 - Present",
                "description": "Modernize training and teacher development in K-12 education."
            },
            {
                "role": "Head of STEM And Engineering Department",
                "company": "Ministry of Education - UAE",
                "dates": "Jul 2022 - Sep 2025",
                "description": "Oversee school operations, scheduling, budgeting, and STEM curriculum."
            },
            {
                "role": "STEM and Engineering program teacher",
                "company": "Ministry of Education - UAE",
                "dates": "Jul 2019 - Jul 2022",
                "description": "Integrate AI concepts into classroom curriculum and high school lesson plans."
            },
        ],
        skills=["Team Leadership", "Instructional Design", "Computer Science Education", "Curriculum Development"],
    )
    domain_rel, notes = ai_service.classify_domain_relevance(candidate, "Senior AI Lead", "IT / Software Engineering")
    assert domain_rel in ["Not Relevant", "Partially Relevant"]
    assert "education" in notes.lower() or "teacher" in notes.lower() or "academic" in notes.lower()

def test_domain_relevance_it_software_engineering_highly_relevant(ai_service):
    """Candidate with core production AI and software engineering experience is Highly Relevant."""
    candidate = CandidateProfile(
        canonical_url="https://linkedin.com/in/tariq",
        name="Tariq Mansoor",
        headline="Principal AI Architect | LLM Systems & Distributed Computing",
        experience_history=[
            {
                "role": "Principal AI Architect",
                "company": "Careem / Uber",
                "dates": "2021 - Present",
                "description": "Designed agentic RAG systems, vector search pipelines, and LLM inference endpoints in Python."
            }
        ],
        skills=["Python", "PyTorch", "LLM Application Development", "RAG", "Vector Databases", "System Design"],
    )
    domain_rel, notes = ai_service.classify_domain_relevance(candidate, "Senior AI Lead", "IT / Software Engineering")
    assert domain_rel == "Highly Relevant"

def test_domain_relevance_transferable_engineering_in_non_it_org(ai_service):
    """Candidate with actual engineering in a non-tech org (e.g. hospital/finance) is recognized for transferable experience."""
    candidate = CandidateProfile(
        canonical_url="https://linkedin.com/in/sarah",
        name="Sarah Jenkins",
        headline="Lead ML Engineer",
        experience_history=[
            {
                "role": "Lead ML Engineer",
                "company": "Cleveland Clinic Abu Dhabi",
                "dates": "2020 - Present",
                "description": "Developed deep learning diagnostic models in Python, deployed PyTorch pipelines on Kubernetes."
            }
        ],
        skills=["Python", "Machine Learning", "Deep Learning", "MLOps", "Docker", "Kubernetes"],
    )
    domain_rel, notes = ai_service.classify_domain_relevance(candidate, "Senior AI Lead", "IT / Software Engineering")
    assert domain_rel in ["Highly Relevant", "Relevant"]

# ---------------------------------------------------------
# 3. Missing Information & Evidence-Based Normalization Tests
# ---------------------------------------------------------

def test_3_state_scoring_missing_sections_no_artificial_zeros(ai_service):
    """
    Missing sections (e.g. projects and certifications not on public LinkedIn)
    must receive state 'not_available' with score=None, and MUST NOT pull the candidate down to 10-15%.
    """
    candidate = CandidateProfile(
        canonical_url="https://linkedin.com/in/alex",
        name="Alex Mercer",
        headline="Senior AI Engineer | Python & LLMs",
        about="Passionate software engineer building production agentic AI systems and LLM pipelines.",
        experience_history=[
            {
                "role": "Senior AI Engineer",
                "company": "TechCorp",
                "dates": "2021 - Present",
                "description": "Lead engineer for RAG pipelines using Python, FastAPI, Pinecone, and LangChain."
            }
        ],
        education=[
            {"school": "Carnegie Mellon University", "degree": "BS in Computer Science", "dates": "2016 - 2020"}
        ],
        skills=["Python", "RAG", "Vector Databases", "Prompt Engineering", "FastAPI"],
        certifications=[],  # Not listed on profile
        projects=[],        # Not listed on profile
        recent_activity=[], # Not listed on profile
    )

    criteria = StructuredJobCriteria(
        job_title="Senior AI Lead",
        mandatory_skills=["Python", "RAG", "LLM Application Development"],
        min_years_experience=4,
        preferred_locations=["Dubai", "UAE"],
    )

    eval_result = ai_service.evaluate_candidate(candidate, criteria)
    
    cat_evals = eval_result.category_evaluations
    assert "certifications" in cat_evals
    assert cat_evals["certifications"].evaluation_state == "not_available"
    assert cat_evals["certifications"].score is None
    assert cat_evals["certifications"].status == "Not Available"

    assert "projects" in cat_evals
    assert cat_evals["projects"].evaluation_state == "not_available"
    assert cat_evals["projects"].score is None

    # Coverage should reflect that only evaluable categories are evaluated
    assert eval_result.evaluation_coverage > 0
    assert eval_result.evaluation_coverage < 100

    # Composite fit score must be calculated across available categories, so Alex remains a strong fit (> 70%), NOT 10%!
    assert eval_result.fit_score >= 70.0, f"Expected fit_score >= 70.0, but got {eval_result.fit_score}"

# ---------------------------------------------------------
# 4. End-to-End Hamza A. Reference Profile Test
# ---------------------------------------------------------

def test_hamza_a_reference_profile_evaluation(ai_service):
    """
    Verify Hamza A. test fixture:
    - Current: Ministry of Education - UAE, Abu Dhabi
    - Authorization: UAE Golden Visa Holder
    - Education: University of Birmingham
    - Background: EdTech, Teacher Training, STEM Curriculum
    - Target: Senior AI Lead in Dubai
    """
    hamza = CandidateProfile(
        canonical_url="https://linkedin.com/in/hamza-a-913820165",
        name="Hamza A.",
        headline="Head of AI and Technology | EdTech and Innovation | University of Birmingham | Certified Trainer | Certified Master Trainer | UAE Golden Visa Holder",
        current_location="Abu Dhabi Emirate, United Arab Emirates",
        work_authorization="UAE Golden Visa Holder",
        education=[
            {"school": "University of Birmingham", "degree": "Master's in Education & Technology", "dates": "2018 - 2020"}
        ],
        certifications=[
            {"name": "Certified Master Trainer", "issuer": "Ministry of Education", "issue_date": "2021"}
        ],
        experience_history=[
            {
                "role": "Head of AI and Technology",
                "company": "Ministry of Education - UAE",
                "dates": "Sep 2025 - Present",
                "description": "Guide school tech leaders in integrating technology effectively into educational curriculum."
            },
            {
                "role": "Professional Development Trainer - Sustainability, Innovation and Technology",
                "company": "Ministry of Education - UAE",
                "dates": "Jul 2022 - Present",
                "description": "Modernize training and teacher development in K-12 education."
            },
            {
                "role": "Head of STEM And Engineering Department",
                "company": "Ministry of Education - UAE",
                "dates": "Jul 2022 - Sep 2025",
                "description": "Oversee school operations, scheduling, budgeting, and STEM curriculum."
            },
            {
                "role": "STEM and Engineering program teacher",
                "company": "Ministry of Education - UAE",
                "dates": "Jul 2019 - Jul 2022",
                "description": "Integrate AI concepts into classroom curriculum and high school lesson plans."
            },
        ],
        skills=["Team Leadership", "Instructional Design", "Computer Science Education", "Curriculum Development"],
    )

    criteria = StructuredJobCriteria(
        job_title="Senior AI Lead",
        mandatory_skills=[
            "Python programming",
            "Machine learning and deep learning",
            "LLM application development",
            "Prompt engineering",
            "RAG and vector databases",
            "Agentic workflows and tool-using systems",
            "MLOps / LLMOps practices",
            "System design and architecture"
        ],
        min_years_experience=5,
        preferred_locations=["Dubai", "UAE"],
    )

    eval_result = ai_service.evaluate_candidate(hamza, criteria)

    # 1. Location compatibility: Compatible because of UAE Golden Visa and in-region presence
    assert eval_result.location_compatibility["status"] == "Compatible"
    assert "golden visa" in eval_result.location_compatibility["reason"].lower()

    # 2. Domain relevance: Identified as EdTech / Teacher Training
    assert eval_result.domain_relevance in ["Not Relevant", "Partially Relevant"]
    assert "education" in eval_result.domain_relevance_notes.lower() or "teacher" in eval_result.domain_relevance_notes.lower() or "academic" in eval_result.domain_relevance_notes.lower()

    # 3. Education: NOT 0%! Hamza has University of Birmingham
    cat_evals = eval_result.category_evaluations
    assert cat_evals["education"].score is not None
    assert cat_evals["education"].score >= 50.0

    # 4. Certifications: NOT 0%! Hamza has Certified Master Trainer
    assert cat_evals["certifications"].score is not None
    assert cat_evals["certifications"].score >= 40.0

    # 5. Missing sections: Projects has no items -> marked as Not Available (score=None), NOT 0%!
    assert cat_evals["projects"].evaluation_state == "not_available"
    assert cat_evals["projects"].score is None

    # 6. Technical gaps clearly stated in unverified criteria
    missing = eval_result.missing_criteria
    assert any("python" in m.lower() for m in missing)
    assert any("rag" in m.lower() for m in missing)


def test_shafi_missing_about_not_penalized_with_zero(ai_service):
    """Candidate with no public About section MUST NOT get 0% or 'Not Matched'."""
    shafi = CandidateProfile(
        canonical_url="https://linkedin.com/in/shafi-rahman-dev",
        name="Shafi Ur Rahman",
        headline="Forward Deployed Engineer | AI Engineer | Backend & Solution Architect | Cloud Engineering • LLM • RAG • Agents | PHP • Python • Node.js • Laravel • AWS | 12+ Yrs | UAE • KSA",
        current_company="Unistic Group",
        location="Delhi, India",
        experience_years=12.0,
        skills=["Python", "Node.js", "AWS", "PHP", "Laravel"],
        about="",  # Missing about section
        education=[],  # Missing
        certifications=[],  # Missing
        projects=[],  # Missing
        recent_activity=[],  # Missing
    )
    criteria = StructuredJobCriteria(
        job_title="Senior Fullstack Engineer",
        mandatory_skills=["Python", "Node.js", "React", "AWS", "SQL", "Docker"],
        min_years_experience=5,
        preferred_locations=["San Francisco"],
    )

    eval_result = ai_service.evaluate_candidate(shafi, criteria)
    cat_evals = eval_result.category_evaluations

    # 1. About section must be 'Not Available' with score None, NEVER 0%
    assert cat_evals["about"].score is None
    assert cat_evals["about"].evaluation_state == "not_available"
    assert cat_evals["about"].status == "Not Available"

    # 2. Education, Certifications, Projects, Activity must also be None
    assert cat_evals["education"].score is None
    assert cat_evals["certifications"].score is None
    assert cat_evals["projects"].score is None
    assert cat_evals["activity"].score is None

    # 3. Fit score is normalized over available categories (Experience 35% + Skills 25% = 60% coverage)
    assert eval_result.evaluation_coverage == 60.0
    assert eval_result.fit_score >= 60.0  # Not dragged down by artificial 0%
    assert eval_result.section_scores["about"] is None

    # 4. Location compatibility detects Delhi, India
    assert eval_result.location_compatibility["current_location"] == "Delhi, India"
    assert eval_result.location_compatibility["status"] == "Needs Verification"


def test_clean_linkedin_card_text_decomposes_noise():
    """Verify clean_linkedin_card_text strips followers, buttons, and extracts location & company."""
    from backend.app.services.db_service import clean_linkedin_card_text

    raw_card = (
        "Forward Deployed Engineer | AI Engineer | Backend & Solution Architect | Cloud Engineering • LLM • RAG • Agents | PHP • Python • Node.js • Laravel • AWS | 12+ Yrs | UAE • KSA\n\n"
        "Delhi, India\n\n"
        "Follow\n\n"
        "Current: Technical Lead / Backend Architect - PHP, Laravel, Microservices, AWS at Unistic Group\n\n"
        "7,516 followers"
    )
    parsed = clean_linkedin_card_text(raw_card)
    assert "7,516" not in parsed["headline"]
    assert "Follow" not in parsed["headline"]
    assert "Current:" not in parsed["headline"]
    assert parsed["company"] == "Unistic Group"
    assert parsed["location"] == "Delhi, India"


def test_clean_skill_tokens_filters_fluff_and_limits(ai_service):
    """Verify _clean_skill_tokens strips parentheticals, filters soft-skill fluff, and caps tokens."""
    raw_skills = [
        "Product Vision & Strategy Definition",
        "Roadmapping",
        "Customer Discovery (Qualitative Interviews, Usability Testing, Workshops)",
        "Enterprise Procurement Requirements (SOC2 Compliance, Role-based Permissions)",
        "Relentless Customer Champion",
        "Deep Empathy for End-user Frustrations",
        "Superb Written & Verbal Communication",
        "Executive Presentation Skills",
        "Exceptional Analytical Skills",
        "Product Analytics Interpretation",
        "Problem Statement Synthesis",
        "User Persona Development",
        "Prioritized User Stories",
        "Product Requirement Documents (PRDs)",
        "Wireframing",
    ]
    cleaned = ai_service._clean_skill_tokens(raw_skills, max_tokens=8)
    assert len(cleaned) <= 8
    # Fluff suppressed
    assert not any("communication" in s.lower() for s in cleaned)
    assert not any("empathy" in s.lower() for s in cleaned)
    assert not any("champion" in s.lower() for s in cleaned)
    # Parentheticals stripped
    assert not any("(" in s or ")" in s for s in cleaned)
    assert "Customer Discovery" in cleaned
    assert "Roadmapping" in cleaned


def test_headline_experience_education_fallback():
    """Verify headline parsing properly populates experience and education for candidates like Vidhan Tripathi."""
    import re
    hl = "Senior Product Manager @Procol AI | ISB | Ex-Sprinklr, Target Bengaluru, Karnataka, India"

    # Current role & company
    first_seg = hl.split("|")[0].strip()
    assert "@" in first_seg
    parts = first_seg.split("@", 1)
    role = parts[0].strip()
    comp = parts[1].strip()
    assert role == "Senior Product Manager"
    assert comp == "Procol AI"

    # Past companies
    ex_match = re.search(r"\b(?:Ex-|Former\s+)([^\|]+)", hl, re.I)
    assert ex_match is not None
    raw_past = re.sub(r"\b(Bengaluru|Bangalore|Dubai|UAE|India|London|San Francisco|New York)\b.*$", "", ex_match.group(1), flags=re.I).strip()
    prior_comps = [c.strip() for c in re.split(r"[,/]+", raw_past) if c.strip() and len(c.strip()) > 2]
    assert "Sprinklr" in prior_comps
    assert "Target" in prior_comps

    # Education (ISB)
    univ_match = re.search(r"\b(ISB|IIT|IIM|BITS|MIT|Stanford|Harvard|INSEAD|University of [A-Za-z]+|[A-Za-z]+ (?:University|Institute of Technology|College|Business School))\b", hl, re.I)
    assert univ_match is not None
    assert univ_match.group(0).upper() == "ISB"

