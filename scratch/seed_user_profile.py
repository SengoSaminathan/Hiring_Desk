"""Seeds the test profile for Sengottayan S into SQLite and Supabase."""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import json
import time
from backend.app.services.db_service import db_service
from backend.app.services.supabase_service import supabase_service

def seed_profile():
    cid = f"cand_sengottayan_{int(time.time())}"
    canonical_url = "https://www.linkedin.com/in/sengottayan-s-17b5ab329/"
    name = "Sengottayan S"
    headline = "Senior AI Lead | Generative AI & Agentic Systems Architect | Python, LLM, RAG"
    company = "Technology Solutions"
    location = "Coimbatore, Tamil Nadu, India"
    target_role = "Senior AI Lead"

    skills = [
        "Python", "FastAPI", "React", "LLM Development", "RAG Pipelines",
        "Prompt Engineering", "Agentic Systems", "Machine Learning",
        "System Architecture", "Production Engineering"
    ]

    exp_history = [
        {
            "title": "Senior AI Lead",
            "company": "Technology Solutions",
            "duration": "2023 - Present · 2 yrs",
            "location": "Tamil Nadu, India",
            "description": "Architecting autonomous agentic frameworks and high-throughput RAG search systems. Leading technical roadmap for enterprise AI solutions."
        },
        {
            "title": "Senior Python & AI Engineer",
            "company": "Innovate AI Labs",
            "duration": "2020 - 2023 · 3 yrs",
            "location": "India",
            "description": "Developed distributed Python microservices, FastAPI gateways, and machine learning pipelines."
        }
    ]

    education = [
        {
            "degree": "Bachelor of Technology in Computer Science & Engineering",
            "school": "Anna University",
            "years": "2015 - 2019"
        }
    ]

    certs = [
        {
            "name": "Generative AI & Agentic Systems Specialization",
            "issuer": "DeepLearning.AI",
            "year": "2024"
        },
        {
            "name": "AWS Certified Machine Learning - Specialty",
            "issuer": "Amazon Web Services",
            "year": "2023"
        }
    ]

    projects = [
        {
            "title": "Autonomous Multi-Agent Recruitment & Sourcing Assistant",
            "description": "Engineered local-first AI recruitment platform combining Playwright automation, multi-agent orchestration, and normalized evidence scoring."
        }
    ]

    recent_activity = [
        {
            "title": "Published insights on multi-agent architectures and high-precision RAG pipelines on LinkedIn."
        }
    ]

    sec_scores = {
        "experience": {"score": 95, "status": "Matched", "weight": 35, "summary": "Extensive experience in Generative AI architecture and enterprise Python delivery."},
        "skills": {"score": 95, "status": "Matched", "weight": 25, "summary": "Core technical stack (Python, FastAPI, RAG, LLM) precisely matches Senior AI Lead requirements."},
        "about": {"score": 90, "status": "Matched", "weight": 15, "summary": "Clear, compelling executive summary highlighting deep AI domain focus."},
        "education": {"score": 90, "status": "Matched", "weight": 10, "summary": "B.Tech in Computer Science from Anna University directly aligns."},
        "certifications": {"score": 95, "status": "Matched", "weight": 5, "summary": "Industry-standard certifications in Generative AI and Machine Learning."},
        "projects": {"score": 90, "status": "Matched", "weight": 5, "summary": "Direct relevant projects in autonomous agent systems."},
        "activity": {"score": 85, "status": "Matched", "weight": 5, "summary": "Active contributor in AI engineering space."}
    }

    cand_data = {
        "id": cid,
        "canonical_url": canonical_url,
        "name": name,
        "headline": headline,
        "current_company": company,
        "company": company,
        "location": location,
        "current_location": location,
        "preferred_work_locations": ["Coimbatore", "Tamil Nadu", "Bangalore", "Remote"],
        "willingness_to_relocate": "Open to Relocation",
        "work_authorization": "Authorized to work in India",
        "location_compatibility_status": "Compatible",
        "location_compatibility_reason": "Candidate location matches target requisition (Tamil Nadu, India / Remote).",
        "domain_relevance": "Highly Relevant IT",
        "domain_relevance_notes": "Proven track record in generative AI architecture, enterprise LLM agents, and Python backend engineering.",
        "experience_years": 7.0,
        "about": "Senior AI Lead and Architect specializing in Generative AI, multi-agent frameworks, LLM integrations, and RAG pipelines. Passionate about building robust, autonomous AI workflows and scalable Python microservices.",
        "skills": skills,
        "experience_history": exp_history,
        "education": education,
        "certifications": certs,
        "projects": projects,
        "recent_activity": recent_activity,
        "section_scores": sec_scores,
        "raw_snippet": "Senior AI Lead | Generative AI & Agentic Systems Architect",
        "avatar_url": "",
        "target_role": target_role,
        "outreach_status": "Unsent",
        "outreach_message": "",
        "outreach_method": "",
    }

    saved_id = db_service.save_candidate(cand_data)
    print(f"Saved candidate {name} to SQLite: {saved_id}")

    eval_data = {
        "candidate_id": saved_id,
        "canonical_url": canonical_url,
        "job_title": target_role,
        "fit_score": 94.0,
        "completeness_score": 95.0,
        "evaluation_coverage": 100.0,
        "match_level": "High Fit",
        "domain_relevance": "Highly Relevant IT",
        "domain_relevance_notes": "Deep technical expertise in AI systems architecture and RAG pipelines.",
        "location_compatibility": {
            "status": "Compatible",
            "candidate_residence": "Coimbatore, Tamil Nadu",
            "target_location": "Coimbatore / Bangalore / Remote, Tamil Nadu",
            "compatibility_type": "Regional / State Match",
            "reason": "Candidate residence in Tamil Nadu is directly compatible with the requisition."
        },
        "justification_summary": "Sengottayan is an exceptional candidate for the Senior AI Lead role. Demonstrates deep domain expertise in generative AI systems, RAG workflows, agentic automation, and Python backend engineering with perfect location compatibility.",
        "evidence_quotes": [
            "7 years hands-on engineering experience in Python, FastAPI, and Generative AI",
            "Architected autonomous agentic frameworks and high-throughput RAG search systems",
            "Industry specialization in Generative AI and Machine Learning"
        ],
        "missing_criteria": [],
        "section_scores": sec_scores,
        "category_evaluations": {
            "experience": {"fit_status": "High Fit", "summary": "Senior AI leadership with proven hands-on delivery."},
            "skills": {"fit_status": "High Fit", "summary": "Strong command of modern AI stack (Python, RAG, LLMs, Agents)."},
            "location": {"fit_status": "Compatible", "summary": "Local in Tamil Nadu, India."}
        }
    }

    eval_id = db_service.save_evaluation(eval_data)
    print(f"Saved evaluation for candidate: eval_id={eval_id}")

    # Verify retrieval
    all_cands = db_service.get_all_candidates()
    print(f"Total candidates currently in DB: {len(all_cands)}")
    found = any(c.get("canonical_url", "").rstrip("/") == canonical_url.rstrip("/") for c in all_cands)
    print(f"Candidate visible in get_all_candidates: {found}")

if __name__ == "__main__":
    seed_profile()
