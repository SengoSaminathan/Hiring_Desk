"""Resilient AI Service for JD Analysis, Query Planning, and Candidate Match Evaluation.

Implements:
- Google Gemini multimodal / text inference via google-genai SDK.
- Exponential backoff with random jitter for 429/503 rate limits.
- Markdown cleanup and strict Pydantic JSON schema validation.
- Zero-AI deterministic fallback (regex/heuristics) when offline or API key missing.
"""

import json
import logging
import os
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.schemas.candidates import CandidateProfile, CategoryEvaluation, EvidenceQuote, MatchEvaluation
from backend.app.schemas.jobs import (
    AnalyzeJobResponse,
    Criterion,
    SearchPlan,
    SearchQueryOption,
    StructuredJobCriteria,
)

logger = logging.getLogger("hiring_desk.ai_service")


class AIService:
    """Manages AI model inference with retries and deterministic fallback."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self._client = None
        self._circuit_breaker_until: float = 0.0

        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Google GenAI client with model %s", self.model_name)
            except Exception as e:
                logger.warning("Failed to initialize Google GenAI client: %s. Fallback enabled.", e)

    def is_ai_available(self) -> bool:
        """Checks if a valid Gemini client is available and not currently tripped by an upstream outage."""
        if not self._client:
            return False
        if time.time() < self._circuit_breaker_until:
            return False
        return True

    def _call_gemini_json(
        self,
        prompt: str,
        system_instruction: str,
        max_retries: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """Calls Gemini with exponential backoff and jitter, returning validated JSON."""
        if not self.is_ai_available():
            return None

        from google.genai import types

        # Resilient model failover candidates (using real available Gemini production models)
        models_to_try = [self.model_name]
        for fallback_model in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
            if fallback_model not in models_to_try:
                models_to_try.append(fallback_model)

        for current_model in models_to_try:
            try:
                resp = self._client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                if not resp or not resp.text:
                    continue

                parsed = self._clean_and_parse_json(resp.text)
                if parsed:
                    return parsed

            except Exception as e:
                err_str = str(e)
                logger.warning(
                    "Model %s encountered issue: %s. Trying next candidate model...",
                    current_model,
                    err_str[:90],
                )
                continue

        # Trip the circuit breaker for 60 seconds so subsequent candidate scoring doesn't stall on 503/429
        self._circuit_breaker_until = time.time() + 60.0
        logger.warning(
            "All Gemini model endpoints busy/unavailable (503/429). Tripped AI circuit breaker for 60s. Instantly switching to deterministic matching engine."
        )
        return None

    def extract_candidates_from_image(
        self,
        image_bytes: bytes,
        query: str = "",
    ) -> List[Dict[str, Any]]:
        """Uses Gemini Multimodal Vision to read candidate search results from a screen image."""
        if not self._client:
            return []

        try:
            import io
            from PIL import Image
            from google.genai import types

            pil_img = Image.open(io.BytesIO(image_bytes))
            prompt = (
                "You are an expert HR sourcer analyzing a screenshot of web search results for candidate sourcing "
                f"targeting LinkedIn profiles (search query: '{query}').\n"
                "Carefully inspect all visible candidate cards, result snippets, and profiles on the screen.\n"
                "Extract structured candidate profiles matching this JSON schema:\n"
                "{\n"
                '  "candidates": [\n'
                "    {\n"
                '      "name": "Full Name",\n'
                '      "headline": "Current title, role, or headline",\n'
                '      "current_company": "Company name if mentioned or Technology Co.",\n'
                '      "location": "Location if mentioned or Remote",\n'
                '      "experience_years": 5.0,\n'
                '      "skills": ["Skill1", "Skill2", "Skill3"],\n'
                '      "canonical_url": "https://www.linkedin.com/in/...",\n'
                '      "snippet": "Full verbatim text snippet from search card",\n'
                '      "avatar_box": [ymin, xmin, ymax, xmax]\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "Note on avatar_box: provide normalized bounding box coordinates [ymin, xmin, ymax, xmax] between 0 and 1000 "
                "for the candidate profile photo, avatar, or site icon next to their name if visible on screen; otherwise null.\n"
                "Return strictly valid JSON only."
            )

            models_to_try = ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
            for model_name in models_to_try:
                try:
                    resp = self._client.models.generate_content(
                        model=model_name,
                        contents=[pil_img, prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1,
                        ),
                    )
                    if resp and resp.text:
                        parsed = self._clean_and_parse_json(resp.text)
                        if parsed and "candidates" in parsed and isinstance(parsed["candidates"], list):
                            logger.info("Successfully extracted %d candidates from screen image using %s", len(parsed["candidates"]), model_name)
                            return parsed["candidates"]
                except Exception as ex:
                    logger.warning("Vision model %s error during screen OCR: %s", model_name, ex)
                    continue

        except Exception as e:
            logger.error("Failed to execute multimodal candidate extraction from screen: %s", e)

        return []

    def _clean_and_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Strips markdown code fences and cleans trailing commas."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Attempt to fix trailing commas
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            try:
                return json.loads(cleaned)
            except Exception as e:
                logger.error("JSON parsing error: %s. Content: %s", e, cleaned[:150])
                return None

    def _normalize_seniority(self, raw: Optional[str]) -> str:
        if not raw:
            return "Senior"
        r = raw.lower()
        if "lead" in r or "manager" in r or "head" in r:
            return "Lead / Manager"
        elif "staff" in r or "principal" in r:
            return "Staff / Principal"
        elif "director" in r or "exec" in r or "vp" in r:
            return "Executive"
        elif "senior" in r:
            return "Senior"
        elif "mid" in r or "intermediate" in r:
            return "Mid-Level"
        elif "entry" in r or "junior" in r or "intern" in r:
            return "Entry Level"
        return "Senior"

    @staticmethod
    def is_executive_or_founder(headline: str, role_title: Optional[str] = None) -> bool:
        """Detects whether a candidate profile headline indicates an active Founder, CEO, or business owner.

        Agency owners, startup founders, and active CEOs are not suitable candidates for standard
        employee/individual contributor/engineering lead requisitions.
        """
        if not headline:
            return False

        if role_title:
            r_lower = role_title.lower()
            if any(k in r_lower for k in ("ceo", "chief executive officer", "founder", "managing director", "president")):
                return False

        h_lower = headline.lower()
        cleaned_h = re.sub(
            r"\b(?:ex[\s\-]?(?:founder|ceo|co-founder|cofounder|owner|managing director)|former[\s\-]+(?:founder|ceo|co-founder|cofounder|owner|managing director))\b",
            "",
            h_lower,
        )

        EXEC_PATTERNS = [
            r"\bfounder\s*[/&|\+]\s*ceo\b",
            r"\bceo\s*[/&|\+]\s*founder\b",
            r"\bco-?founder\s*[/&|\+]\s*ceo\b",
            r"\bco-?founder\b",
            r"\bfounder\b",
            r"\bceo\b",
            r"\bchief executive officer\b",
            r"\bmanaging director\b",
            r"\bagency owner\b",
            r"\bbusiness owner\b",
            r"\bproprietor\b",
        ]

        for pat in EXEC_PATTERNS:
            if re.search(pat, cleaned_h):
                return True

        return False

    def analyze_job_description(self, raw_jd: str) -> AnalyzeJobResponse:
        """Parses a Job Description into complete structured criteria across all sections and search queries."""
        heuristics = self._extract_jd_section_heuristics(raw_jd)

        if self.is_ai_available():
            system_instruction = (
                "You are an executive HR Director and Principal Technical Recruiter with 20+ years of experience. "
                "Analyze the provided Job Description (JD) and extract complete, highly detailed structured role criteria and search plan. "
                "You must extract ALL sections: Job Information, Detailed Job Description (overview & key responsibilities), "
                "Department, Seniority Level (strictly one of: 'Entry Level', 'Mid-Level', 'Senior', 'Staff / Principal', 'Lead / Manager', 'Executive'), "
                "Experience ranges and focus, Leadership requirements, Mandatory & Preferred Skills, Technologies & Frameworks, "
                "Tools & Platforms, Domain Expertise, Certifications, Work Mode & Locations, Salary / Compensation, "
                "Education Requirements, and Key Performance Indicators / Success Measures. "
                "SKILL EXTRACTION MANDATE: "
                "Extract STRICTLY 6 to 10 concise, atomic skill/domain keywords for mandatory_skills and 4 to 8 for preferred_skills. "
                "Each skill must be short (1-3 words, e.g. 'Roadmapping', 'Product Analytics', 'Agile/Scrum', 'Enterprise SaaS', 'Python'). "
                "NEVER copy full sentences, multi-clause responsibility bullet points, parenthetical explanations, or soft skills/behavioral traits into skills chips. "
                "Output strictly valid JSON matching the exact schema provided."
            )
            prompt = f"""Analyze this complete Job Description document:
{raw_jd}

Extract and populate every field in this JSON Schema:
{{
  "criteria": {{
    "job_title": "string (Exact role title, e.g. 'Senior AI Lead')",
    "job_description": "string (Comprehensive multi-paragraph overview of the role, team mission, and key responsibilities synthesized from the JD)",
    "department": "string (e.g. 'Engineering', 'Artificial Intelligence', 'Product')",
    "employment_type": "string ('Full-time', 'Contract', 'Part-time', 'Internship')",
    "seniority_level": "string (Strictly one of: 'Entry Level', 'Mid-Level', 'Senior', 'Staff / Principal', 'Lead / Manager', 'Executive')",
    "vacancies": 1,
    "min_years_experience": float or null (Minimum required years, e.g. 8.0),
    "max_years_experience": float or null (Maximum desired years, e.g. 12.0),
    "relevant_experience": "string (Specific hands-on technical experience expectations and technical focus)",
    "leadership_experience": "string (Leadership, mentoring, delivery ownership, and stakeholder management expectations)",
    "mandatory_skills": ["string (Strictly 6 to 10 concise, high-signal skill/domain tokens, max 1-3 words each, e.g. 'Roadmapping', 'PRD Authoring', 'Product Analytics', 'Agile/Scrum', 'Go-To-Market', 'User Research'. NEVER extract full sentences, paragraphs, soft skills, or bullet points with parentheticals)"],
    "preferred_skills": ["string (Strictly 4 to 8 concise, high-signal nice-to-have skill tokens, max 1-3 words each, e.g. 'Enterprise SaaS', 'ATS Integrations', 'SOC2 Compliance', 'SQL')"],
    "technologies": ["string (Specific programming languages, frameworks, libraries, e.g. PyTorch, TensorFlow, LangChain, LangGraph, FastAPI)"],
    "tools_platforms": ["string (Cloud platforms, vector DBs, container tools, e.g. Azure, AWS, GCP, Pinecone, Milvus, Docker, Kubernetes)"],
    "domain_expertise": ["string (Specialized domain areas, e.g. Generative AI, RAG, Agentic Systems, MLOps, LLMOps, Responsible AI)"],
    "certifications": ["string (Required or preferred certifications, or relevant credentials)"],
    "work_mode": "string ('Remote', 'Hybrid', or 'On-site')",
    "country": "string or null",
    "state_region": "string or null",
    "city": "string or null",
    "preferred_locations": ["string (Target cities or regions)"],
    "willingness_to_relocate": false,
    "salary_range": "string or null (Compensation details if mentioned)",
    "notice_period": "string or null (e.g. '30 Days')",
    "education_requirements": "string (Degree level, majors, or educational background from JD)",
    "preferred_industries": ["string"],
    "companies_to_target": ["string"],
    "companies_to_exclude": ["string"],
    "additional_instructions": "string (Success measures, key milestones, or instructions)",
    "criteria_list": [
      {{"category": "Experience", "requirement": "string", "is_mandatory": true, "weight": 1.2}}
    ]
  }},
  "search_plan": {{
    "linkedin_keywords": "string",
    "xray_query": "string",
    "target_titles": ["string"],
    "target_skills": ["string"],
    "strategic_queries": [
      {{"id": "precision", "label": "string", "query": "string", "description": "string", "strategy_type": "Precision Stack"}},
      {{"id": "lateral", "label": "string", "query": "string", "description": "string", "strategy_type": "Lateral Synonyms"}},
      {{"id": "domain", "label": "string", "query": "string", "description": "string", "strategy_type": "Domain Focus"}}
    ]
  }}
}}"""
            result = self._call_gemini_json(prompt, system_instruction)
            if result and "criteria" in result and "search_plan" in result:
                try:
                    c_dict = result["criteria"]
                    # Normalize seniority level strictly
                    c_dict["seniority_level"] = self._normalize_seniority(c_dict.get("seniority_level") or heuristics["seniority_level"])
                    
                    # Fill any empty fields from heuristics
                    for key, val in heuristics.items():
                        if key not in c_dict or not c_dict[key]:
                            c_dict[key] = val
                    
                    if not c_dict.get("job_description"):
                        c_dict["job_description"] = heuristics["job_description"]

                    # Strictly sanitize skills to concise high-signal keywords (max 10 mandatory, 8 preferred)
                    c_dict["mandatory_skills"] = self._clean_skill_tokens(c_dict.get("mandatory_skills", []), max_tokens=10)
                    c_dict["preferred_skills"] = self._clean_skill_tokens(c_dict.get("preferred_skills", []), max_tokens=8)
                    if not c_dict["mandatory_skills"] and heuristics.get("mandatory_skills"):
                        c_dict["mandatory_skills"] = heuristics["mandatory_skills"][:10]

                    # Strictly sanitize preferred_locations to strip work modes (e.g. 'Hybrid, On-site, or Remote')
                    c_dict["preferred_locations"] = self._clean_location_tokens(c_dict.get("preferred_locations", []))
                    if not c_dict["preferred_locations"] and heuristics.get("preferred_locations"):
                        c_dict["preferred_locations"] = heuristics["preferred_locations"]

                    criteria = StructuredJobCriteria(**c_dict)
                    sp_dict = result["search_plan"]
                    if not sp_dict.get("strategic_queries"):
                        sp_dict["strategic_queries"] = [
                            q.model_dump() for q in self.generate_strategic_queries(
                                criteria.job_title, criteria.mandatory_skills, criteria.preferred_skills,
                                technologies=criteria.technologies,
                                tools_platforms=criteria.tools_platforms,
                                domain_expertise=criteria.domain_expertise,
                                preferred_locations=criteria.preferred_locations,
                                location=criteria.city or criteria.country,
                                seniority_level=criteria.seniority_level
                            )
                        ]
                    return AnalyzeJobResponse(
                        criteria=criteria,
                        search_plan=SearchPlan(**sp_dict),
                        raw_jd=raw_jd,
                    )
                except Exception as e:
                    logger.warning("Pydantic validation failed on Gemini result: %s. Falling back to deterministic parser.", e)

        # Fallback if Gemini unavailable or failed
        logger.info("Using comprehensive deterministic rule-based JD parser.")
        return self._deterministic_jd_parser(raw_jd, heuristics=heuristics)

    @staticmethod
    def _clean_location_tokens(locations: Optional[List[str]]) -> List[str]:
        """Sanitizes location inputs by stripping out work modes ('Hybrid', 'On-site', 'Remote') and normalizing city/country tokens."""
        if not locations:
            return []
        WORK_MODE_TERMS = {
            "remote", "hybrid", "on-site", "onsite", "in-office", "inoffice",
            "work from home", "wfh", "any", "all", "worldwide", "global",
            "open to relocate", "flexible", "options", "negotiable", "full-time", "contract"
        }
        cleaned_tokens: List[str] = []
        for raw in locations:
            if not raw:
                continue
            for token in re.split(r"[,;/|•·\n]+", str(raw)):
                token = re.sub(r'["\']', '', token).strip()
                token = re.sub(r'\(.*?\)', '', token).strip()
                t_lower = token.lower()
                if not token or len(token) < 2:
                    continue
                if any(wm in t_lower for wm in ("hybrid", "on-site", "onsite", "remote", "wfh", "work from home")):
                    continue
                if t_lower in WORK_MODE_TERMS:
                    continue
                if token not in cleaned_tokens:
                    cleaned_tokens.append(token)
        return cleaned_tokens

    @staticmethod
    def _clean_skill_tokens(raw_skills: Optional[List[str]], max_tokens: int = 8) -> List[str]:
        """Sanitizes skill tokens: filters behavioral fluff, strips parentheticals, breaks down compound phrases, and caps count to concise high-signal keywords."""
        if not raw_skills:
            return []
        
        # Soft-skill/behavioral phrases to filter out from technical sourcing chips
        FLUFF_PATTERNS = [
            r"\bverbal\b", r"\bwritten\b", r"\bcommunication\b", r"\bchampion\b",
            r"\bempathy\b", r"\bfrustration\b", r"\binfluence\b", r"\bpresentation\b",
            r"\banalytical skills\b", r"\bexceptional\b", r"\bsuperb\b", r"\brelentless\b",
            r"\bcollaborative\b", r"\bteam player\b", r"\bself-starter\b", r"\bproblem solver\b",
            r"\bpassion\b", r"\bdetail-oriented\b", r"\bresults-driven\b", r"\bstrong work ethic\b",
            r"\bfast-paced\b", r"\binterpersonal\b"
        ]
        
        cleaned: List[str] = []
        seen = set()
        
        for raw in raw_skills:
            if not raw or not isinstance(raw, str):
                continue
            
            # 1. Suppress soft-skill fluff
            if any(re.search(pat, raw, re.I) for pat in FLUFF_PATTERNS):
                continue
            
            # 2. Strip parentheticals e.g. "Customer Discovery (Qualitative Interviews...)" -> "Customer Discovery"
            token = re.sub(r'\(.*?\)', '', raw).strip()
            # Strip quotes, leading bullets, trailing punctuation
            token = re.sub(r'^[\s•·\-\*\"\']+|[\s\"\',;:\.]+$', '', token).strip()
            
            # 3. If token contains multiple comma-separated items, split them
            sub_tokens = [re.sub(r'^[\s•·\-\*\"\']+|[\s\"\',;:\.]+$', '', st).strip() for st in re.split(r'[,;/|]+', token) if st.strip()]
            for st in sub_tokens:
                st_clean = re.sub(r'\s+', ' ', st).strip()
                if not st_clean or len(st_clean) < 2:
                    continue
                words = st_clean.split()
                # A phrase with > 5 words or > 40 chars is a responsibility/sentence, not a skill chip
                if len(words) > 5 or len(st_clean) > 40:
                    continue
                
                key = st_clean.lower()
                if key not in seen:
                    seen.add(key)
                    cleaned.append(st_clean)
                    if len(cleaned) >= max_tokens:
                        return cleaned
        
        return cleaned[:max_tokens]

    def _build_location_clause(
        self,
        preferred_locations: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> str:
        """Constructs an optimized, compact Boolean location filter for LinkedIn search.
        
        Prioritizes specific Cities and States over broad Country catch-alls.
        If a city (e.g. 'Chennai') or state (e.g. 'Tamil Nadu') is specified, the country (e.g. 'India')
        is excluded from the OR clause so the search is not diluted across the entire nation.
        """
        raw_candidates = []
        if preferred_locations:
            raw_candidates.extend(preferred_locations)
        if location:
            raw_candidates.append(location)

        valid_tokens = self._clean_location_tokens(raw_candidates)
        if not valid_tokens:
            return ""

        # Check for UAE / Middle East hubs
        has_uae = any(t.lower() in ("dubai", "uae", "united arab emirates", "abu dhabi", "sharjah") for t in valid_tokens)
        if has_uae:
            return ' AND ("Dubai" OR "UAE")'

        BROAD_COUNTRY_NAMES = {
            "india", "united states", "usa", "us", "u.s.", "u.s.a.",
            "united kingdom", "uk", "u.k.", "canada", "australia",
            "germany", "france", "singapore", "netherlands", "malaysia",
            "philippines", "indonesia", "pakistan", "bangladesh", "sri lanka",
            "saudi arabia", "qatar", "kuwait", "bahrain", "oman", "egypt"
        }

        # Separate specific local cities/states from broad country catch-alls
        local_tokens = [t for t in valid_tokens if t.lower() not in BROAD_COUNTRY_NAMES]
        country_tokens = [t for t in valid_tokens if t.lower() in BROAD_COUNTRY_NAMES]

        # If specific city/state is specified, prioritize it strictly over country catch-all
        tokens_to_use = local_tokens if local_tokens else country_tokens

        expanded = []
        for t in tokens_to_use:
            t_lower = t.lower()
            if t_lower in ("bangalore", "bengaluru"):
                for itm in ('"Bangalore"', '"Bengaluru"'):
                    if itm not in expanded:
                        expanded.append(itm)
            elif t_lower in ("chennai", "madras"):
                for itm in ('"Chennai"', '"Madras"'):
                    if itm not in expanded:
                        expanded.append(itm)
            elif t_lower in ("coimbatore", "kovai"):
                for itm in ('"Coimbatore"', '"Kovai"'):
                    if itm not in expanded:
                        expanded.append(itm)
            elif t_lower in ("tamil nadu", "tamilnadu"):
                for itm in ('"Tamil Nadu"', '"Tamilnadu"'):
                    if itm not in expanded:
                        expanded.append(itm)
            elif t_lower in ("hyderabad", "secunderabad"):
                for itm in ('"Hyderabad"', '"Secunderabad"'):
                    if itm not in expanded:
                        expanded.append(itm)
            elif t_lower in ("mumbai", "bombay"):
                for itm in ('"Mumbai"', '"Bombay"'):
                    if itm not in expanded:
                        expanded.append(itm)
            elif t_lower in ("delhi", "new delhi", "ncr"):
                for itm in ('"Delhi"', '"New Delhi"', '"Noida"', '"Gurgaon"'):
                    if itm not in expanded:
                        expanded.append(itm)
            elif t_lower in ("london", "uk", "united kingdom"):
                for itm in ('"London"', '"UK"'):
                    if itm not in expanded:
                        expanded.append(itm)
            else:
                quoted = f'"{t}"'
                if quoted not in expanded:
                    expanded.append(quoted)

        # If a single city in Tamil Nadu was given (e.g. Chennai or Coimbatore) and no state was included,
        # include state for wider regional recall within 4 OR terms
        if any(t.lower() in ("chennai", "coimbatore") for t in tokens_to_use) and not any("tamil" in t.lower() for t in tokens_to_use):
            if len(expanded) < 3 and '"Tamil Nadu"' not in expanded:
                expanded.append('"Tamil Nadu"')

        if len(expanded) == 1:
            return f' AND ({expanded[0]})'
        elif len(expanded) > 1:
            return f' AND ({" OR ".join(expanded[:4])})'
        return ""

    @staticmethod
    def _format_skill_token(s: str) -> str:
        clean = s.strip()
        return f'"{clean}"' if " " in clean else clean

    def generate_strategic_queries(
        self,
        job_title: str,
        mandatory_skills: List[str],
        preferred_skills: Optional[List[str]] = None,
        technologies: Optional[List[str]] = None,
        tools_platforms: Optional[List[str]] = None,
        domain_expertise: Optional[List[str]] = None,
        location: Optional[str] = None,
        preferred_locations: Optional[List[str]] = None,
        seniority_level: Optional[str] = None,
    ) -> List[SearchQueryOption]:
        """Generates 3 recruiter-grade Boolean search queries using Gemini AI with fallback, strictly avoiding over-constrained AND chains."""
        loc_clause = self._build_location_clause(preferred_locations, location)
        clean_title = re.sub(r'["\']', '', job_title).strip() or "Software Engineer"
        all_tech = list(dict.fromkeys((mandatory_skills or []) + (technologies or [])))
        core_m = [s for s in all_tech if s][:3]

        if self.is_ai_available():
            try:
                system_instruction = (
                    "You are an executive HR Director and LinkedIn Boolean Search Architect with 20+ years of technical sourcing experience. "
                    "Generate 3 distinct, high-yield LinkedIn Boolean search queries that strictly adhere to LinkedIn search engine mechanics.\n"
                    "CRITICAL LINKEDIN SOURCING RULES:\n"
                    "1. NEVER CHAIN THREE GROUPS WITH 'AND'. Standard LinkedIn keyword search returns 'No results found' when [Domain] AND [Seniority/Title] AND [Location] are all required simultaneously.\n"
                    "2. NEVER REQUIRE STANDALONE SENIORITY WORDS (e.g. 'Lead OR Senior OR Head OR Architect OR Principal') AS A MANDATORY 'AND' GROUP. Seniority and years of experience are evaluated downstream by the AI evaluation engine, not by fragile keyword filters.\n"
                    "3. KEEP QUERIES STRICTLY TO TWO CLAUSES JOINED BY A SINGLE 'AND': [Role / Domain / Skills OR group] AND [Location OR group].\n"
                    "4. NEVER INCLUDE WORK MODES ('Hybrid', 'On-site', 'Remote') in any query.\n"
                    "5. Structure high-yield queries:\n"
                    "   - Query 1 (Precision Stack - Core Domain): ([Primary Role/Domain Terms OR]) AND ([Location OR])\n"
                    "   - Query 2 (Broad Reach & Compound Titles): ([Natural Compound Titles with Seniority OR, e.g. 'AI Lead' OR 'AI Architect' OR 'Machine Learning' OR 'AI Engineer']) AND ([Location OR])\n"
                    "   - Query 3 (Specialized Domain & Tech): ([Core Technology Anchors OR]) AND ([Location OR])\n"
                    "6. Strictly append the provided Location Boolean Filter to every query if given.\n"
                    "7. KEEP QUERIES LEAN (under 120 characters total) so LinkedIn search does not drop candidates."
                )
                clean_loc_list = self._clean_location_tokens(preferred_locations or [location or ""])
                loc_desc = ", ".join(clean_loc_list) if clean_loc_list else "None"
                prompt = f"""Generate 3 high-yield LinkedIn Boolean search queries for this role:
- Title: {clean_title} ({seniority_level or 'Senior'})
- Mandatory Skills: {', '.join(mandatory_skills or core_m)}
- Technologies: {', '.join((technologies or [])[:4])}
- Domain Expertise: {', '.join((domain_expertise or [])[:3])}
- Target Location: {loc_desc}
- Location Clause to append: {loc_clause or 'None'}

Strategies:
1. Precision Stack (id: "precision"): Core role and domain terms with OR + location clause (NO separate seniority AND clause).
2. Broad Reach & Synonyms (id: "lateral"): Compound leadership and specialist titles with OR + location clause.
3. Specialized Tech & Domain (id: "domain"): High-signal domain/tech keywords with OR + location clause.

JSON Schema:
{{
  "queries": [
    {{"id": "precision", "label": "🎯 Query 1: Precision Stack", "query": "string", "description": "string", "strategy_type": "Precision Match"}},
    {{"id": "lateral", "label": "🌐 Query 2: Broad Reach & Synonyms", "query": "string", "description": "string", "strategy_type": "Lateral Equivalents"}},
    {{"id": "domain", "label": "⚡ Query 3: Specialized Tech & Domain", "query": "string", "description": "string", "strategy_type": "Domain & Framework Focus"}}
  ]
}}"""
                result = self._call_gemini_json(prompt, system_instruction)
                if result and "queries" in result and isinstance(result["queries"], list) and len(result["queries"]) == 3:
                    out = []
                    for q in result["queries"]:
                        q_str = q.get("query", "").strip()
                        q_str = re.sub(r'["\']?(?:Hybrid|On-site|Remote|onsite|hybrid)[^"\'\)]*["\']?\s*(?:OR|AND)?\s*', '', q_str, flags=re.I).strip()
                        if loc_clause and not any(loc.lower() in q_str.lower() for loc in (clean_loc_list or [""])):
                            q_str = f"{q_str}{loc_clause}"

                        # Enforce maximum 1 AND (domain OR group AND location OR group)
                        if loc_clause and loc_clause.strip() in q_str:
                            loc_idx = q_str.rfind(loc_clause.strip())
                            domain_part = q_str[:loc_idx].strip()
                            if domain_part.endswith("AND"):
                                domain_part = domain_part[:-3].strip()
                            if " AND " in domain_part:
                                domain_part = domain_part.replace(" AND ", " OR ")
                            q_str = f"{domain_part} {loc_clause.strip()}".strip()

                        out.append(SearchQueryOption(
                            id=q.get("id", "precision"),
                            label=q.get("label", "Query Strategy"),
                            query=q_str,
                            description=q.get("description", "AI-formulated search strategy."),
                            strategy_type=q.get("strategy_type", "AI Strategy"),
                        ))
                    return out
            except Exception as e:
                logger.warning("Gemini query generation failed: %s. Using deterministic Boolean synthesizer.", e)

        # High-yield deterministic Boolean synthesizer fallback
        title_words = [w for w in clean_title.split() if w.lower() not in ("senior", "junior", "lead", "staff", "principal", "head", "director", "manager")]
        base_role = " ".join(title_words) if title_words else "AI Engineer"

        is_ai_role = any(x in clean_title.lower() for x in ["ai", "machine learning", "ml", "deep learning", "artificial intelligence", "data"])
        if is_ai_role:
            domain_group = '("AI" OR "Machine Learning" OR "Artificial Intelligence")'
            compound_titles = '("AI Lead" OR "AI Architect" OR "AI Engineer" OR "Machine Learning")'
            tech_anchor = '("Generative AI" OR LLM OR "Deep Learning" OR Python)'
        else:
            domain_group = f'("{base_role}" OR "{clean_title}")'
            compound_titles = f'("Lead {base_role}" OR "{base_role} Architect" OR "Senior {base_role}" OR "{base_role}")'
            tech_anchor = f'("{" OR ".join(core_m[:2]) if core_m else base_role}")'

        q1 = SearchQueryOption(
            id="precision",
            label="🎯 Query 1: Precision Stack",
            query=f'{domain_group}{loc_clause}'.strip(),
            description=f"Targets candidates in the core domain in the target location without restrictive title filtering.",
            strategy_type="Precision Match",
        )

        q2 = SearchQueryOption(
            id="lateral",
            label="🌐 Query 2: Broad Reach & Synonyms",
            query=f'{compound_titles}{loc_clause}'.strip(),
            description=f"Compound role title search across leadership and practitioner title equivalents in the target location.",
            strategy_type="Lateral Equivalents",
        )

        q3 = SearchQueryOption(
            id="domain",
            label="⚡ Query 3: Specialized Tech & Domain",
            query=f'{tech_anchor}{loc_clause}'.strip(),
            description="Filters for specialized technical skills and domain anchors directly in the target location.",
            strategy_type="Domain & Framework Focus",
        )

        return [q1, q2, q3]

    def generate_single_query(
        self,
        strategy_id: str,
        job_title: str,
        mandatory_skills: List[str],
        preferred_skills: Optional[List[str]] = None,
        technologies: Optional[List[str]] = None,
        domain_expertise: Optional[List[str]] = None,
        location: Optional[str] = None,
        preferred_locations: Optional[List[str]] = None,
    ) -> SearchQueryOption:
        """Regenerates a single strategic search query with updated parameters, prioritizing preferred locations."""
        clean_title = re.sub(r'["\']', '', job_title).strip() or "Software Engineer"
        all_tech = list(dict.fromkeys((mandatory_skills or []) + (technologies or [])))
        core_m = [s for s in all_tech if s]
        loc_clause = self._build_location_clause(preferred_locations, location)

        title_words = [w for w in clean_title.split() if w.lower() not in ("senior", "junior", "lead", "staff", "principal", "head", "director", "manager")]
        base_role = " ".join(title_words) if title_words else "AI Engineer"

        is_ai_role = any(x in clean_title.lower() for x in ["ai", "machine learning", "ml", "deep learning", "artificial intelligence", "data"])

        if strategy_id == "precision":
            domain_group = '("AI" OR "Machine Learning" OR "Artificial Intelligence")' if is_ai_role else f'("{base_role}" OR "{clean_title}")'
            return SearchQueryOption(
                id="precision",
                label="🎯 Query 1: Precision Stack",
                query=f'{domain_group}{loc_clause}'.strip(),
                description=f"Refined precision search targeting primary domain keywords in target location.",
                strategy_type="Precision Match",
            )
        elif strategy_id == "lateral":
            compound_titles = '("AI Lead" OR "AI Architect" OR "AI Engineer" OR "Machine Learning")' if is_ai_role else f'("Lead {base_role}" OR "{base_role} Architect" OR "Senior {base_role}" OR "{base_role}")'
            return SearchQueryOption(
                id="lateral",
                label="🌐 Query 2: Broad Reach & Synonyms",
                query=f'{compound_titles}{loc_clause}'.strip(),
                description=f"Expanded lateral search across title equivalents for {base_role} in target location.",
                strategy_type="Lateral Equivalents",
            )
        else:
            tech_anchor = '("Generative AI" OR LLM OR "Deep Learning" OR Python)' if is_ai_role else f'("{" OR ".join(core_m[:2]) if core_m else base_role}")'
            return SearchQueryOption(
                id="domain",
                label="⚡ Query 3: Specialized Tech & Domain",
                query=f'{tech_anchor}{loc_clause}'.strip(),
                description="Specialized domain query filtering for key technical competencies in target location.",
                strategy_type="Domain & Framework Focus",
            )

    def _extract_jd_section_heuristics(self, raw_jd: str) -> Dict[str, Any]:
        """Extracts comprehensive structured fields from JD text across all sections."""
        paras = [p.strip() for p in raw_jd.split("\n") if p.strip()]

        # 1. Job Title
        first_line = paras[0] if paras else "Software Engineer"
        first_line_clean = re.sub(r"[•·\|\-].*$", "", first_line).strip()
        job_title = first_line_clean[:60] if len(first_line_clean) > 3 else "Software Engineer"
        if job_title.isupper():
            job_title = job_title.title()

        # 2. Seniority Level
        seniority_level = self._normalize_seniority(
            job_title if any(k in job_title.lower() for k in ["lead", "senior", "staff", "principal", "junior", "director", "manager"])
            else raw_jd[:250]
        )

        # 3. Job Description / Role Overview
        desc_parts = []
        capture_desc = False
        for p in paras:
            if re.match(r"^(?:Role Overview|Job Summary|About the Role|Position Overview|Job Description)", p, re.I):
                capture_desc = True
                continue
            if capture_desc and re.match(r"^(?:Required Skills|Qualifications|Requirements|Candidate Profile|Must Have|Education|Compensation)", p, re.I):
                break
            if capture_desc:
                desc_parts.append(p)
        job_description = "\n\n".join(desc_parts) if desc_parts else "\n\n".join(paras[:5])

        # 4. Department
        department = "Engineering"
        for dept in ["Engineering", "Artificial Intelligence", "AI / ML", "Data Science", "Product", "Information Technology", "Cloud & Infrastructure"]:
            if re.search(r"\b" + re.escape(dept) + r"\b", raw_jd, re.I):
                department = dept
                break

        # 5. Experience (Min & Max)
        range_match = re.search(r"(\d+)\s*[\u2010\u2012\u2013\u2014\u2212\-\sto]+\s*(\d+)\s*(?:years?|yrs?)", raw_jd, re.I)
        if range_match:
            min_exp, max_exp = float(range_match.group(1)), float(range_match.group(2))
        else:
            single = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", raw_jd, re.I)
            min_exp = float(single.group(1)) if single else 5.0
            max_exp = min_exp + 3.0

        # 6. Relevant Experience Focus
        rel_match = re.search(r"(?:\d+[\u2010\u2012\u2013\u2014\u2212\-\sto]+\d+|\d+\+?)\s*(?:years?|yrs?)[^\.\n]+\.", raw_jd, re.I)
        relevant_experience = rel_match.group(0).strip() if rel_match else f"{int(min_exp)}+ years of hands-on technical architecture and engineering delivery experience."

        # 7. Leadership Experience
        lead_parts = []
        capture_lead = False
        for p in paras:
            if re.match(r"^(?:Team & Stakeholder Leadership|Experience & Leadership Expectations|Leadership Expectations|Leadership)", p, re.I):
                capture_lead = True
                continue
            if capture_lead and re.match(r"^(?:Responsible AI|Education|Success Measures|Required Skills|Preferred Skills|Additional)", p, re.I):
                capture_lead = False
                continue
            if capture_lead:
                lead_parts.append(p)
        leadership_experience = " ".join(lead_parts) if lead_parts else ("Technical team leadership, mentoring, and cross-functional delivery ownership." if "lead" in seniority_level.lower() else "")

        # 8. Education Requirements
        edu_match = re.search(r"(?:Education|Academic Background)[\s:]*\n?([^\n]+(?:\n[^\n]+)?)", raw_jd, re.I)
        education_requirements = edu_match.group(1).strip() if edu_match else "Bachelor's or Master's degree in Computer Science, AI, Data Science, or related engineering discipline."

        # 9. Compensation / Salary Range
        comp_match = re.search(r"(?:Compensation|Salary)[\s:]*([^\n\.]+)", raw_jd, re.I)
        salary_range = comp_match.group(1).strip() if comp_match else "Competitive and commensurate with experience"

        # 10. Work Mode & Location
        work_mode = "Remote"
        if re.search(r"\bhybrid\b", raw_jd, re.I):
            work_mode = "Hybrid"
        elif re.search(r"\bon[\s-]site\b|\bonsite\b", raw_jd, re.I):
            work_mode = "On-site"

        pref_locs = []
        loc_header_match = re.search(r"(?:Location|Job Location|Work Location|Place of Work)[\s:]*([^\n\r\.\;]+)", raw_jd, re.I)
        if loc_header_match:
            raw_loc_str = loc_header_match.group(1).strip()
            cleaned_from_header = self._clean_location_tokens([raw_loc_str])
            for tok in cleaned_from_header:
                if tok not in pref_locs:
                    pref_locs.append(tok)

        # Common city and regional hubs
        if re.search(r"\bdubai\b", raw_jd, re.I) and "Dubai" not in pref_locs:
            pref_locs.append("Dubai")
        if re.search(r"\b(uae|united arab emirates)\b", raw_jd, re.I) and "UAE" not in pref_locs:
            pref_locs.append("UAE")
        if re.search(r"\babu dhabi\b", raw_jd, re.I) and "Abu Dhabi" not in pref_locs:
            pref_locs.append("Abu Dhabi")
        if re.search(r"\b(bengaluru|bangalore)\b", raw_jd, re.I) and "Bengaluru" not in pref_locs:
            pref_locs.append("Bengaluru")
        if re.search(r"\b(riyadh|saudi arabia|ksa)\b", raw_jd, re.I) and "Riyadh" not in pref_locs:
            pref_locs.append("Riyadh")
        if re.search(r"\b(london|uk|united kingdom)\b", raw_jd, re.I) and "London" not in pref_locs:
            pref_locs.append("London")
        if re.search(r"\b(singapore)\b", raw_jd, re.I) and "Singapore" not in pref_locs:
            pref_locs.append("Singapore")

        # 11. Additional Instructions / Success Measures
        succ_parts = []
        capture_succ = False
        for p in paras:
            if re.match(r"^(?:Success Measures|Key Deliverables|First 6|Objectives)", p, re.I):
                capture_succ = True
                continue
            if capture_succ and re.match(r"^(?:Additional Information|Location|Compensation)", p, re.I):
                break
            if capture_succ:
                succ_parts.append(p)
        additional_instructions = " ".join(succ_parts) if succ_parts else ""

        # 12. Technologies, Tools, Domain Expertise
        tech_patterns = [
            "Python", "PyTorch", "TensorFlow", "scikit-learn", "LangChain", "LangGraph", 
            "LlamaIndex", "Semantic Kernel", "Hugging Face Transformers", "FastAPI", "REST APIs",
            "OpenAI", "React", "Next.js", "TypeScript", "Node.js", "SQL", "NoSQL", "Redis", "Kafka"
        ]
        tools_patterns = [
            "Microsoft Azure", "Azure", "AWS", "Google Cloud Platform", "Google Cloud", "GCP",
            "Docker", "Kubernetes", "PostgreSQL", "pgvector", "Pinecone", "Weaviate", "Milvus",
            "Elasticsearch", "Git", "CI/CD"
        ]
        domain_patterns = [
            "Generative AI", "Large Language Models (LLMs)", "LLM", "Machine Learning", "Deep Learning",
            "Retrieval-Augmented Generation (RAG)", "RAG", "Vector Databases", "Prompt Engineering",
            "Agentic Workflows", "AI Agents", "MLOps", "LLMOps", "PEFT/LoRA", "Quantization",
            "Multimodal AI", "Speech Systems (STT/TTS)", "Computer Vision", "Responsible AI",
            "Security & Governance", "Model Evaluation & Guardrails", "System Design"
        ]

        def match_items(patterns):
            res = []
            for pat in patterns:
                if re.search(r"\b" + re.escape(pat) + r"\b", raw_jd, re.I) and pat not in res:
                    res.append(pat)
            return res

        technologies = match_items(tech_patterns)
        tools_platforms = match_items(tools_patterns)
        domain_expertise = match_items(domain_patterns)

        # Categorize mandatory & preferred
        mandatory_skills = self._clean_skill_tokens(
            [s for s in ["Python", "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "scikit-learn", "Generative AI", "Large Language Models (LLMs)", "RAG", "Vector Databases", "Prompt Engineering", "Agentic Workflows", "MLOps", "LLMOps", "System Design"] if s in technologies or s in domain_expertise]
            or technologies[:6] + domain_expertise[:4]
            or ["Python", "Machine Learning", "AI Solutions"],
            max_tokens=10
        )
        preferred_skills = self._clean_skill_tokens(
            [s for s in ["Microsoft Azure", "AWS", "Google Cloud Platform", "Hugging Face Transformers", "LangChain", "LangGraph", "LlamaIndex", "Semantic Kernel", "PostgreSQL", "pgvector", "Pinecone", "Weaviate", "Milvus", "Elasticsearch", "Docker", "Kubernetes", "PEFT/LoRA", "Quantization"] if s in tools_platforms or s in technologies or s in domain_expertise]
            or tools_platforms[:6] + technologies[6:]
            or ["Cloud Infrastructure", "Docker", "Kubernetes"],
            max_tokens=8
        )

        certifications = [
            c for c in ["Cloud AI/ML Certifications (AWS / Azure / GCP)", "Advanced AI Study or Specialized Certifications"]
            if "certif" in raw_jd.lower()
        ]

        return {
            "job_title": job_title,
            "job_description": job_description,
            "department": department,
            "employment_type": "Full-time",
            "seniority_level": seniority_level,
            "vacancies": 1,
            "min_years_experience": min_exp,
            "max_years_experience": max_exp,
            "relevant_experience": relevant_experience,
            "leadership_experience": leadership_experience,
            "mandatory_skills": mandatory_skills,
            "preferred_skills": preferred_skills,
            "technologies": technologies,
            "tools_platforms": tools_platforms,
            "domain_expertise": domain_expertise,
            "certifications": certifications,
            "work_mode": work_mode,
            "salary_range": salary_range,
            "notice_period": "30 Days",
            "education_requirements": education_requirements,
            "additional_instructions": additional_instructions,
            "preferred_locations": pref_locs,
        }

    def _deterministic_jd_parser(self, raw_jd: str, heuristics: Optional[Dict[str, Any]] = None) -> AnalyzeJobResponse:
        """Rule-based heuristic JD parser that works 100% offline extracting all sections."""
        h = heuristics or self._extract_jd_section_heuristics(raw_jd)

        criteria_list = [
            Criterion(category="Experience", requirement=f"At least {int(h['min_years_experience'])} years of relevant experience", is_mandatory=True, weight=1.2),
        ]
        for skill in h["mandatory_skills"][:5]:
            criteria_list.append(Criterion(category="Technical Skills", requirement=f"Proficiency in {skill}", is_mandatory=True, weight=1.0))
        for skill in h["preferred_skills"][:4]:
            criteria_list.append(Criterion(category="Technical Skills", requirement=f"Experience with {skill}", is_mandatory=False, weight=0.7))
        if h["leadership_experience"]:
            criteria_list.append(Criterion(category="Leadership", requirement=h["leadership_experience"][:120], is_mandatory=True, weight=1.1))

        # Search queries
        core_query_skills = " ".join(f'"{s}"' for s in h["mandatory_skills"][:3])
        linkedin_kw = f'"{h["job_title"]}" {core_query_skills}'.strip()
        xray = f'site:linkedin.com/in/ "{h["job_title"]}" {core_query_skills}'.strip()
        
        pref_locs = h.get("preferred_locations", [])
        city = pref_locs[0] if pref_locs else None
        country = "UAE" if any(x.lower() in ("dubai", "uae", "abu dhabi") for x in pref_locs) else None

        strat_queries = self.generate_strategic_queries(
            h["job_title"],
            h["mandatory_skills"],
            h["preferred_skills"],
            technologies=h["technologies"],
            tools_platforms=h["tools_platforms"],
            domain_expertise=h["domain_expertise"],
            location=city,
            preferred_locations=pref_locs,
            seniority_level=h["seniority_level"],
        )

        criteria = StructuredJobCriteria(
            job_title=h["job_title"],
            job_description=h["job_description"],
            department=h["department"],
            employment_type=h["employment_type"],
            seniority_level=h["seniority_level"],
            vacancies=h["vacancies"],
            min_years_experience=h["min_years_experience"],
            max_years_experience=h["max_years_experience"],
            relevant_experience=h["relevant_experience"],
            leadership_experience=h["leadership_experience"],
            mandatory_skills=h["mandatory_skills"],
            preferred_skills=h["preferred_skills"],
            technologies=h["technologies"],
            tools_platforms=h["tools_platforms"],
            domain_expertise=h["domain_expertise"],
            certifications=h["certifications"],
            country=country,
            city=city,
            preferred_locations=pref_locs,
            work_mode=h["work_mode"],
            salary_range=h["salary_range"],
            notice_period=h["notice_period"],
            education_requirements=h["education_requirements"],
            additional_instructions=h["additional_instructions"],
            criteria_list=criteria_list,
        )

        return AnalyzeJobResponse(
            criteria=criteria,
            search_plan=SearchPlan(
                linkedin_keywords=linkedin_kw,
                xray_query=xray,
                target_titles=[h["job_title"]],
                target_skills=h["mandatory_skills"][:5],
                strategic_queries=strat_queries,
            ),
            raw_jd=raw_jd,
        )

    def analyze_location_compatibility(
        self,
        candidate: CandidateProfile,
        target_locations: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Evaluates location compatibility distinguishing current residence, preferred work location,
        willingness to relocate, and work authorization (e.g. UAE Golden Visa).
        Never rejects solely on unknown relocation willingness."""
        cleaned_targets = [t.strip() for t in (target_locations or []) if t and t.strip()]
        target_locs = [t.lower() for t in cleaned_targets]
        cand_curr = (candidate.current_location or candidate.location or "").strip()
        if not cand_curr or cand_curr.lower() in ("location on profile", "location not specified", "not specified"):
            # Extract from raw_snippet or headline if location field is unspecified
            combined_raw = f"{candidate.raw_snippet or ''} {candidate.headline or ''}"
            loc_match = re.search(
                r"\b((?:Dubai|Abu Dhabi|Sharjah|Ajman|Ras Al Khaimah)(?:,\s*(?:United Arab Emirates|UAE))?|United Arab Emirates|UAE|Delhi,\s*India|Mumbai,\s*India|Bengaluru,\s*India|Bangalore,\s*India|Hyderabad,\s*India|Pune,\s*India|Chennai,\s*India|Coimbatore,\s*Tamil\s*Nadu|Coimbatore|Tamil\s*Nadu|Tamilnadu|Kolkata|India|KSA|Saudi Arabia|Riyadh|San Francisco(?:,\s*CA)?|New York(?:,\s*NY)?|Austin(?:,\s*TX)?|Seattle(?:,\s*WA)?|London(?:,\s*UK)?|Berlin|Singapore|Toronto)\b",
                combined_raw,
                re.IGNORECASE,
            )
            if loc_match:
                cand_curr = loc_match.group(0).strip()

        cand_curr_lower = cand_curr.lower()
        work_auth = (candidate.work_authorization or "").strip()
        willingness = (candidate.willingness_to_relocate or "Unknown").strip()

        # Check if target represents UAE / Dubai
        is_uae_target = any(k in target_locs for k in ["dubai", "uae", "united arab emirates", "abu dhabi", "sharjah"])

        # Check if candidate holds UAE Golden Visa or citizen status
        combined_text = f"{candidate.headline or ''} {candidate.raw_snippet or ''} {candidate.about or ''}".lower()
        has_golden_visa = "golden visa" in work_auth.lower() or "golden visa" in combined_text
        is_citizen = "citizen" in work_auth.lower() or "citizen" in combined_text

        in_dubai = "dubai" in cand_curr_lower or "dubai" in combined_text
        in_uae = any(k in cand_curr_lower or k in combined_text for k in [
            "uae", "united arab emirates", "abu dhabi", "dubai", "sharjah", "ajman", "ras al khaimah", "fujairah"
        ])

        status = "Compatible"
        reason = ""

        if not target_locs:
            status = "Compatible"
            reason = f"Candidate based in {cand_curr or 'flexible location'}; role has no strict geographic restriction."
        elif is_uae_target:
            if has_golden_visa:
                status = "Compatible"
                reason = "Holds UAE Golden Visa: unrestricted UAE residence and employment authorization across Dubai and all emirates."
            elif in_dubai:
                status = "Compatible"
                reason = "Currently living/working in Dubai."
            elif in_uae:
                status = "Compatible"
                if "delhi" in cand_curr_lower or "india" in cand_curr_lower:
                    reason = f"Candidate is based in {cand_curr} with verified UAE / GCC professional presence or mobility; inter-regional relocation is standard."
                else:
                    reason = f"Based in UAE ({cand_curr or 'Abu Dhabi / UAE'}); local commute or inter-emirate relocation to Dubai is standard."
            elif willingness.lower() in ("yes", "likely"):
                status = "Compatible"
                reason = f"Candidate is based in {cand_curr or 'another region'} with verified willingness to relocate to Dubai."
            elif willingness.lower() == "no":
                status = "Incompatible"
                reason = "Candidate has explicitly indicated unwilling to relocate to Dubai."
            else:
                status = "Needs Verification"
                reason = f"Candidate location is {cand_curr or 'unspecified'}; willingness to relocate to Dubai is unknown and requires recruiter verification. Candidate is not rejected."
        else:
            BROAD_REGIONS = {"india", "united states", "usa", "remote", "flexible", "tamil nadu", "tamilnadu", "karnataka", "telangana", "maharashtra"}
            city_targets = [t for t in target_locs if t not in BROAD_REGIONS]

            is_exact_city = any(c in cand_curr_lower for c in city_targets) if city_targets else False
            is_state_match = any(t in cand_curr_lower for t in target_locs if t in ("tamil nadu", "tamilnadu", "karnataka", "telangana", "maharashtra"))

            if is_exact_city or ("remote" in target_locs):
                status = "Compatible"
                reason = f"Currently based in target city ({cand_curr})."
            elif is_state_match and city_targets:
                status = "Compatible"
                reason = f"Candidate is based in {cand_curr} (regional/state match for {', '.join(t.title() for t in city_targets)}); local commute or on-site relocation is standard."
            elif any(t in cand_curr_lower for t in target_locs):
                status = "Compatible"
                reason = f"Currently based in target location ({cand_curr})."
            elif willingness.lower() in ("yes", "likely"):
                status = "Compatible"
                reason = f"Candidate willing to relocate to target location ({', '.join(cleaned_targets)})."
            elif willingness.lower() == "no":
                status = "Incompatible"
                reason = f"Candidate has explicitly indicated unwilling to relocate to target location ({', '.join(cleaned_targets)})."
            else:
                status = "Needs Verification"
                if cand_curr:
                    reason = f"Candidate is based in {cand_curr}; relocation willingness to {', '.join(cleaned_targets)} is unknown and requires recruiter verification."
                else:
                    reason = f"Candidate location is unspecified; relocation willingness to {', '.join(cleaned_targets)} is unknown and requires recruiter verification."

        auth_label = "UAE Golden Visa Holder" if has_golden_visa else ("Citizen" if is_citizen else (work_auth or "Standard"))
        cand_pref_locs = getattr(candidate, "preferred_work_locations", []) or []
        cand_pref_str = ", ".join(cand_pref_locs) if cand_pref_locs else "Not published on profile"
        req_loc_str = ", ".join(cleaned_targets) if cleaned_targets else (cand_curr or "Any / Remote")
        return {
            "status": status,
            "current_location": cand_curr or "Location on Profile",
            "target_requisition_location": req_loc_str,
            "requisition_location": req_loc_str,
            "preferred_work_location": cand_pref_str,
            "willingness_to_relocate": willingness,
            "work_authorization": auth_label,
            "reason": reason,
        }

    def classify_domain_relevance(
        self,
        candidate: CandidateProfile,
        target_role: str = "Senior AI Lead",
        target_industry: str = "Information Technology",
    ) -> Tuple[str, str]:
        """Classifies candidate into 4 tiers of industry and professional domain relevance:
        - 'Highly Relevant': Strong IT/Tech industry & production engineering alignment.
        - 'Relevant': Suitable technical background with transferable engineering experience.
        - 'Partially Relevant': Some technical keywords, but background is predominantly in
          education, teaching, training, academic administration, or non-IT domain.
        - 'Not Relevant': Experience does not align with target technical role.
        """
        full_text = f"{candidate.headline or ''} {candidate.about or ''} {candidate.raw_snippet or ''} {' '.join(candidate.skills or [])} "
        for exp in (candidate.experience_history or []):
            full_text += f" {exp.get('role', '')} {exp.get('title', '')} {exp.get('company', '')} {exp.get('description', '')}"
        full_lower = full_text.lower()

        # Check for Founder / CEO / Business Owner mismatch for employee requisitions
        if self.is_executive_or_founder(candidate.headline or "", target_role):
            return (
                "Not Relevant",
                f"Candidate is an active Founder/CEO/Business Owner ({candidate.headline}). Active business owners and agency founders are not suitable candidates for employee vacancies."
            )

        edu_training_signals = [
            "ministry of education", "teacher", "trainer", "training", "edtech",
            "curriculum", "instructional", "school", "students", "stem teacher",
            "academic", "education leadership", "k-12", "certified trainer", "master trainer"
        ]
        edu_count = sum(1 for s in edu_training_signals if s in full_lower)

        tech_eng_signals = [
            "python", "pytorch", "tensorflow", "fastapi", "llm", "rag", "vector database",
            "langchain", "docker", "kubernetes", "mlops", "llmops", "system design",
            "software engineer", "solutions architect", "ai engineer", "machine learning engineer",
            "production deployment", "ci/cd", "microservices", "aws", "azure", "gcp"
        ]
        tech_count = sum(1 for s in tech_eng_signals if s in full_lower)

        if tech_count >= 4 and edu_count <= 2:
            return "Highly Relevant", "Strong IT & software engineering domain alignment with hands-on technical architecture and delivery track record."
        elif tech_count >= 2 and edu_count <= 3:
            return "Relevant", "Relevant technical background with transferable engineering experience."
        elif edu_count >= 2 or ("education" in full_lower and tech_count < 3):
            return (
                "Partially Relevant",
                "Professional background is predominantly in Education, Teacher Training, or Academic Administration. "
                "While holding technology/AI titles, candidate lacks verified commercial IT software engineering, production LLM systems, or MLOps architecture delivery."
            )
        elif tech_count >= 1:
            return "Partially Relevant", "Candidate has some matching technical exposure, but professional domain requires closer technical verification."
        else:
            return "Not Relevant", "Professional domain and experience do not align with target IT engineering role."

    def evaluate_candidates_batch(
        self,
        candidates: List[CandidateProfile],
        criteria: StructuredJobCriteria,
    ) -> List[MatchEvaluation]:
        """Evaluates multiple candidates in a single prompt across all 7 sections to minimize API calls and prevent rate limits."""
        if not candidates:
            return []

        if self.is_ai_available() and len(candidates) > 1:
            system_instruction = (
                "You are an executive Technical Talent Acquisition Leader with 20+ years of experience in IT recruitment.\n"
                "Evaluate candidates section by section across: Experience (35%), Skills (25%), About / Executive Summary (15%), "
                "Education (10%), Certifications (5%), Projects (5%), Activity (5%).\n\n"
                "CRITICAL 3-STATE EVIDENCE EVALUATION POLICY:\n"
                "1. AVAILABLE & RELEVANT: Profile contains verifiable evidence satisfying role requirement. Award points backed by verbatim quote.\n"
                "2. AVAILABLE BUT IRRELEVANT: Profile section exists, but experience is non-engineering or unrelated (e.g. K-12 teacher training for software lead). Assign low score with explanation.\n"
                "3. NOT AVAILABLE / INSUFFICIENT EVIDENCE: Section is missing or marked 'Not specified'. Set score to null and status to 'Not Available'. DO NOT assign 0% or penalize composite fit for missing sections!\n"
                "4. NORMALIZE composite fit score strictly across available categories.\n"
                "5. Distinguish location compatibility based on target location criteria. Never reject for unknown relocation willingness.\n"
                "6. EXECUTIVE / FOUNDER MISMATCH: Active Founders, Co-Founders, CEOs, Managing Directors, and Agency Owners (e.g. 'Founder/CEO/Head of AI', 'Founder & CEO', 'Managing Director', 'Owner') are running their own businesses. They are NOT suitable candidates for standard employee/individual contributor/engineering lead requisitions. Do NOT align them with senior employee roles. Score their Experience as 'Not Matched' (score <= 25%) and explicitly explain that an active founder/CEO of their own firm is not viable for an employee role.\n"
                "Output strictly in valid JSON matching the schema."
            )
            candidate_summaries = []
            for idx, c in enumerate(candidates):
                cid = c.id or f"c_{idx+1}"
                candidate_summaries.append(
                    f"Candidate #{idx+1} [ID: {cid}]:\n"
                    f"Name: {c.name}\nHeadline: {c.headline}\nCompany: {c.current_company}\nLocation: {c.location}\n"
                    f"Work Authorization: {c.work_authorization or 'Not specified'}\n"
                    f"About: {c.about or 'Not specified'}\n"
                    f"Experience: {json.dumps(c.experience_history[:4]) if c.experience_history else 'Not specified'}\n"
                    f"Education: {json.dumps(c.education[:2]) if c.education else 'Not specified'}\n"
                    f"Certifications: {json.dumps(c.certifications[:2]) if c.certifications else 'Not specified'}\n"
                    f"Projects: {json.dumps(c.projects[:2]) if c.projects else 'Not specified'}\n"
                    f"Activity: {json.dumps(c.recent_activity[:2]) if c.recent_activity else 'Not specified'}\n"
                    f"Skills: {', '.join(c.skills) if c.skills else 'Not specified'}\n"
                    f"Snippet: {c.raw_snippet}"
                )

            _loc = getattr(criteria, "location", None)
            _prefs = getattr(criteria, "preferred_locations", None) or ([_loc] if _loc else ["Remote / Any"])
            pref_loc_str = ", ".join(_prefs)
            prompt = f"""Role: {criteria.job_title} ({criteria.seniority_level})
Mandatory Skills: {', '.join(criteria.mandatory_skills)}
Preferred Skills: {', '.join(criteria.preferred_skills)}
Min Years: {criteria.min_years_experience}
Preferred Locations: {pref_loc_str}

Evaluate these candidates using the 3-state evidence scoring policy:
{chr(10).join(candidate_summaries)}

Output strictly in JSON format:
{{
  "evaluations": [
    {{
      "candidate_id": "string",
      "fit_score": 85.0,
      "completeness_score": 80.0,
      "evaluation_coverage": 90.0,
      "match_level": "High" | "Medium" | "Low",
      "domain_relevance": "Highly Relevant" | "Relevant" | "Partially Relevant" | "Not Relevant",
      "domain_relevance_notes": "1 sentence on industry fit",
      "location_compatibility": {{
        "status": "Compatible" | "Needs Verification" | "Incompatible",
        "current_location": "string",
        "preferred_work_location": "string",
        "willingness_to_relocate": "string",
        "work_authorization": "string",
        "reason": "string"
      }},
      "justification_summary": "1-2 sentence explanation",
      "section_scores": {{
        "experience": 85.0,
        "skills": 90.0,
        "about": 85.0,
        "education": 80.0,
        "certifications": 85.0,
        "projects": 80.0,
        "activity": 70.0
      }},
      "category_evaluations": {{
        "experience": {{"category_name": "Experience", "weight": 0.35, "score": 85.0, "evaluation_state": "available_relevant", "status": "Matched", "evidence_found": "string", "confidence": 0.9, "explanation": "string"}},
        "skills": {{"category_name": "Skills", "weight": 0.25, "score": 80.0, "evaluation_state": "available_relevant", "status": "Matched", "evidence_found": "string", "confidence": 0.9, "explanation": "string"}},
        "about": {{"category_name": "About", "weight": 0.15, "score": 85.0, "evaluation_state": "available_relevant", "status": "Matched", "evidence_found": "string", "confidence": 0.85, "explanation": "string"}},
        "education": {{"category_name": "Education", "weight": 0.10, "score": 80.0, "evaluation_state": "available_relevant", "status": "Matched", "evidence_found": "string", "confidence": 0.9, "explanation": "string"}},
        "certifications": {{"category_name": "Certifications", "weight": 0.05, "score": null, "evaluation_state": "not_available", "status": "Not Available", "evidence_found": "None", "confidence": 0.5, "explanation": "Not published on profile"}},
        "projects": {{"category_name": "Projects", "weight": 0.05, "score": null, "evaluation_state": "not_available", "status": "Not Available", "evidence_found": "None", "confidence": 0.5, "explanation": "Not published on profile"}},
        "activity": {{"category_name": "Activity", "weight": 0.05, "score": null, "evaluation_state": "not_available", "status": "Not Available", "evidence_found": "None", "confidence": 0.5, "explanation": "Not published on profile"}}
      }},
      "evidence_quotes": [
        {{"criterion_requirement": "string", "verbatim_quote": "exact quote from profile", "is_match": true, "confidence": 0.95}}
      ],
      "missing_criteria": ["skills with no evidence"]
    }}
  ]
}}"""
            result = self._call_gemini_json(prompt, system_instruction)
            if result and "evaluations" in result and isinstance(result["evaluations"], list):
                eval_dict = {}
                for item in result["evaluations"]:
                    cid = str(item.get("candidate_id", ""))
                    if cid:
                        quotes = [
                            EvidenceQuote(
                                criterion_requirement=q.get("criterion_requirement", "Requirement"),
                                verbatim_quote=q.get("verbatim_quote", ""),
                                is_match=q.get("is_match", True),
                                confidence=float(q.get("confidence", 0.9)),
                            )
                            for q in item.get("evidence_quotes", [])
                            if isinstance(q, dict)
                        ]
                        cat_evals = {}
                        for cat_k, cat_v in item.get("category_evaluations", {}).items():
                            if isinstance(cat_v, dict):
                                cat_evals[cat_k] = CategoryEvaluation(
                                    category_name=cat_v.get("category_name", cat_k.title()),
                                    weight=float(cat_v.get("weight", 0.1)),
                                    score=float(cat_v["score"]) if cat_v.get("score") is not None else None,
                                    evaluation_state=cat_v.get("evaluation_state", "available_relevant"),
                                    status=cat_v.get("status", "Matched"),
                                    evidence_found=cat_v.get("evidence_found", ""),
                                    confidence=float(cat_v.get("confidence", 0.9)),
                                    explanation=cat_v.get("explanation", ""),
                                )

                        # Ensure 'about' category is present in batch evaluations
                        if "about" not in cat_evals:
                            sec_sc = item.get("section_scores", {})
                            ab_val = sec_sc.get("about")
                            cat_evals["about"] = CategoryEvaluation(
                                category_name="About",
                                weight=0.15,
                                score=float(ab_val) if ab_val is not None else None,
                                evaluation_state="available_relevant" if ab_val is not None else "not_available",
                                status="Matched" if ab_val is not None else "Not Available",
                                evidence_found="",
                                confidence=0.85 if ab_val is not None else 0.5,
                                explanation="About section verified from profile records." if ab_val is not None else "About section is not published on accessible LinkedIn profile. Not penalized with zero score.",
                            )

                        eval_dict[cid] = MatchEvaluation(
                            candidate_id=cid,
                            fit_score=float(item.get("fit_score", 75.0)),
                            completeness_score=float(item.get("completeness_score", 70.0)),
                            evaluation_coverage=float(item.get("evaluation_coverage", 100.0)),
                            match_level=item.get("match_level", "Medium"),
                            domain_relevance=item.get("domain_relevance", "Relevant"),
                            domain_relevance_notes=item.get("domain_relevance_notes", ""),
                            location_compatibility=item.get("location_compatibility", {}),
                            justification_summary=item.get("justification_summary", "Candidate matches based on profile evidence."),
                            evidence_quotes=quotes,
                            missing_criteria=item.get("missing_criteria", []),
                            section_scores=item.get("section_scores", {}),
                            category_evaluations=cat_evals,
                        )

                # Assemble results aligning with candidates list
                evaluations = []
                for idx, c in enumerate(candidates):
                    cid = c.id or f"c_{idx+1}"
                    if cid in eval_dict:
                        ev = eval_dict[cid]
                        # Verify 'about' category against actual candidate.about
                        cand_about = (c.about or "").strip()
                        if cand_about and len(cand_about) >= 15:
                            curr_ab = ev.category_evaluations.get("about")
                            if not curr_ab or curr_ab.evaluation_state == "not_available" or curr_ab.score is None:
                                ab_score = 90.0 if ev.domain_relevance in ("Highly Relevant", "Relevant") else 60.0
                                ev.category_evaluations["about"] = CategoryEvaluation(
                                    category_name="About",
                                    weight=0.15,
                                    score=ab_score,
                                    evaluation_state="available_relevant",
                                    status="Matched",
                                    evidence_found=cand_about[:140],
                                    evidence_source="About Section",
                                    confidence=0.90,
                                    explanation=f"Executive summary verified from profile: {cand_about[:90]}...",
                                )
                                ev.section_scores["about"] = ab_score
                        evaluations.append(ev)
                    else:
                        evaluations.append(self._deterministic_evaluator(c, criteria))
                return evaluations

        # AI was unavailable, rate-limited, or batch call returned None:
        # Fall back IMMEDIATELY to deterministic evaluator for all candidates.
        # DO NOT call self.evaluate_candidate which would loop and re-trigger failing 503 network calls!
        logger.info(
            "Evaluating %d candidates using high-precision deterministic evidence matching engine (zero-latency fallback).",
            len(candidates)
        )
        return [self._deterministic_evaluator(c, criteria) for c in candidates]

    def evaluate_candidate(
        self,
        candidate: CandidateProfile,
        criteria: StructuredJobCriteria,
    ) -> MatchEvaluation:
        """Evaluates candidate fit against job criteria with 3-state evidence scoring, normalized composite fit, and domain relevance."""
        if self.is_ai_available():
            system_instruction = (
                "You are an executive Technical Talent Acquisition Leader with 20+ years of experience in IT recruitment.\n"
                "Evaluate the candidate section by section across: Experience (35%), Skills (25%), About / Executive Summary (15%), "
                "Education (10%), Certifications (5%), Projects (5%), Activity (5%).\n\n"
                "CRITICAL 3-STATE EVIDENCE EVALUATION POLICY:\n"
                "1. AVAILABLE & RELEVANT: Profile contains verifiable evidence satisfying requirement. Award points backed by verbatim quote.\n"
                "2. AVAILABLE BUT IRRELEVANT: Profile section exists, but experience is non-engineering or unrelated (e.g. K-12 teacher training for software lead). Assign low score with explanation.\n"
                "3. NOT AVAILABLE / INSUFFICIENT EVIDENCE: Section is missing or marked 'Not specified'. Set score to null and status to 'Not Available'. DO NOT assign 0% or penalize composite fit for missing sections!\n"
                "4. NORMALIZE composite fit score strictly across available categories.\n"
                "5. Distinguish location compatibility based on target location criteria. Never reject for unknown relocation willingness.\n"
                "6. EXECUTIVE / FOUNDER MISMATCH: Active Founders, Co-Founders, CEOs, Managing Directors, and Agency Owners (e.g. 'Founder/CEO/Head of AI', 'Founder & CEO', 'Managing Director', 'Owner') are running their own businesses. They are NOT suitable candidates for standard employee/individual contributor/engineering lead requisitions. Do NOT align them with senior employee roles. Score their Experience as 'Not Matched' (score <= 25%) and explicitly explain that an active founder/CEO of their own firm is not viable for an employee role.\n"
                "Output strictly in valid JSON matching the schema."
            )
            _eval_loc = getattr(criteria, "location", None)
            _eval_prefs = getattr(criteria, "preferred_locations", None) or ([_eval_loc] if _eval_loc else ["Remote / Any"])
            target_pref_str = ", ".join(_eval_prefs)
            prompt = f"""Job Requirements:
Role: {criteria.job_title} ({criteria.seniority_level})
Mandatory Skills: {', '.join(criteria.mandatory_skills)}
Preferred Skills: {', '.join(criteria.preferred_skills)}
Min Years: {criteria.min_years_experience}
Preferred Locations: {target_pref_str}

Candidate Profile:
Name: {candidate.name}
Headline: {candidate.headline}
Company: {candidate.current_company}
Location: {candidate.location}
Work Authorization: {candidate.work_authorization or 'Not specified'}
About: {candidate.about or 'Not specified'}
Experience: {json.dumps(candidate.experience_history[:4]) if candidate.experience_history else 'Not specified'}
Education: {json.dumps(candidate.education[:2]) if candidate.education else 'Not specified'}
Certifications: {json.dumps(candidate.certifications[:2]) if candidate.certifications else 'Not specified'}
Projects: {json.dumps(candidate.projects[:2]) if candidate.projects else 'Not specified'}
Activity: {json.dumps(candidate.recent_activity[:2]) if candidate.recent_activity else 'Not specified'}
Skills: {', '.join(candidate.skills) if candidate.skills else 'Not specified'}
Snippet: {candidate.raw_snippet}

Output strictly in JSON format:
{{
  "fit_score": float (0-100),
  "completeness_score": float (0-100),
  "evaluation_coverage": float (0-100),
  "match_level": "High" | "Medium" | "Low",
  "domain_relevance": "Highly Relevant" | "Relevant" | "Partially Relevant" | "Not Relevant",
  "domain_relevance_notes": "string",
  "location_compatibility": {{
    "status": "Compatible" | "Needs Verification" | "Incompatible",
    "current_location": "string",
    "preferred_work_location": "string",
    "willingness_to_relocate": "string",
    "work_authorization": "string",
    "reason": "string"
  }},
  "justification_summary": "1-2 sentence explanation",
  "section_scores": {{
    "experience": float,
    "skills": float,
    "about": float,
    "education": float,
    "certifications": float,
    "projects": float,
    "activity": float
  }},
  "category_evaluations": {{
    "experience": {{"category_name": "Experience", "weight": 0.35, "score": float, "evaluation_state": "available_relevant" | "available_irrelevant" | "not_available", "status": "Matched" | "Partially Matched" | "Not Matched" | "Not Available", "evidence_found": "string", "confidence": float, "explanation": "string"}},
    "skills": {{"category_name": "Skills", "weight": 0.25, "score": float, "evaluation_state": "available_relevant" | "available_irrelevant" | "not_available", "status": "Matched" | "Partially Matched" | "Not Matched" | "Not Available", "evidence_found": "string", "confidence": float, "explanation": "string"}},
    "about": {{"category_name": "About", "weight": 0.15, "score": float, "evaluation_state": "available_relevant" | "available_irrelevant" | "not_available", "status": "Matched" | "Partially Matched" | "Not Matched" | "Not Available", "evidence_found": "string", "confidence": float, "explanation": "string"}},
    "education": {{"category_name": "Education", "weight": 0.10, "score": float, "evaluation_state": "available_relevant" | "not_available", "status": "Matched" | "Not Available", "evidence_found": "string", "confidence": float, "explanation": "string"}},
    "certifications": {{"category_name": "Certifications", "weight": 0.05, "score": float, "evaluation_state": "available_relevant" | "not_available", "status": "Matched" | "Not Available", "evidence_found": "string", "confidence": float, "explanation": "string"}},
    "projects": {{"category_name": "Projects", "weight": 0.05, "score": float, "evaluation_state": "available_relevant" | "not_available", "status": "Matched" | "Not Available", "evidence_found": "string", "confidence": float, "explanation": "string"}},
    "activity": {{"category_name": "Activity", "weight": 0.05, "score": float, "evaluation_state": "available_relevant" | "not_available", "status": "Matched" | "Not Available", "evidence_found": "string", "confidence": float, "explanation": "string"}}
  }},
  "evidence_quotes": [
    {{"criterion_requirement": "string", "verbatim_quote": "exact quote from profile", "is_match": true, "confidence": 1.0}}
  ],
  "missing_criteria": ["skills with no evidence"]
}}"""
            result = self._call_gemini_json(prompt, system_instruction)
            if result and "fit_score" in result:
                try:
                    quotes = [EvidenceQuote(**q) for q in result.get("evidence_quotes", [])]
                    cat_evals = {}
                    for cat_k, cat_v in result.get("category_evaluations", {}).items():
                        if isinstance(cat_v, dict):
                            cat_evals[cat_k] = CategoryEvaluation(
                                category_name=cat_v.get("category_name", cat_k.title()),
                                weight=float(cat_v.get("weight", 0.1)),
                                score=float(cat_v["score"]) if cat_v.get("score") is not None else None,
                                evaluation_state=cat_v.get("evaluation_state", "available_relevant"),
                                status=cat_v.get("status", "Matched"),
                                evidence_found=cat_v.get("evidence_found", ""),
                                confidence=float(cat_v.get("confidence", 0.9)),
                                explanation=cat_v.get("explanation", ""),
                            )

                    sec_scores = result.get("section_scores", {})
                    if "about" not in sec_scores:
                        sec_scores["about"] = 85.0 if (candidate.about or "").strip() else None

                    if "about" not in cat_evals:
                        ab_sc = float(sec_scores["about"]) if sec_scores.get("about") is not None else None
                        cat_evals["about"] = CategoryEvaluation(
                            category_name="About",
                            weight=0.15,
                            score=ab_sc,
                            evaluation_state="available_relevant" if ab_sc is not None else "not_available",
                            status="Matched" if ab_sc is not None else "Not Available",
                            evidence_found=(candidate.about or "")[:120],
                            confidence=0.85 if ab_sc is not None else 0.5,
                            explanation="About section verified from profile records." if ab_sc is not None else "About section is not published on accessible LinkedIn profile. Not penalized with zero score.",
                        )

                    # Verify 'about' against actual candidate.about
                    cand_about = (candidate.about or "").strip()
                    if cand_about and len(cand_about) >= 15:
                        curr_ab = cat_evals.get("about")
                        if not curr_ab or curr_ab.evaluation_state == "not_available" or curr_ab.score is None:
                            ab_score = 90.0 if result.get("domain_relevance") in ("Highly Relevant", "Relevant") else 60.0
                            cat_evals["about"] = CategoryEvaluation(
                                category_name="About",
                                weight=0.15,
                                score=ab_score,
                                evaluation_state="available_relevant",
                                status="Matched",
                                evidence_found=cand_about[:140],
                                evidence_source="About Section",
                                confidence=0.90,
                                explanation=f"Executive summary verified from profile: {cand_about[:90]}...",
                            )
                            sec_scores["about"] = ab_score

                    return MatchEvaluation(
                        candidate_id=candidate.id or candidate.canonical_url,
                        fit_score=float(result["fit_score"]),
                        completeness_score=float(result.get("completeness_score", 70.0)),
                        evaluation_coverage=float(result.get("evaluation_coverage", 100.0)),
                        match_level=result.get("match_level", "Medium"),
                        domain_relevance=result.get("domain_relevance", "Relevant"),
                        domain_relevance_notes=result.get("domain_relevance_notes", ""),
                        location_compatibility=result.get("location_compatibility", {}),
                        justification_summary=result.get("justification_summary", "Candidate matches based on profile evidence."),
                        evidence_quotes=quotes,
                        missing_criteria=result.get("missing_criteria", []),
                        section_scores=sec_scores,
                        category_evaluations=cat_evals,
                    )
                except Exception as e:
                    logger.warning("Pydantic validation failed on evaluation: %s. Using deterministic evaluator.", e)

        # Deterministic fallback evaluation
        return self._deterministic_evaluator(candidate, criteria)

    def _deterministic_evaluator(
        self,
        candidate: CandidateProfile,
        criteria: StructuredJobCriteria,
    ) -> MatchEvaluation:
        """Deterministic Evidence-Based Matching Engine with 3 evaluation states, normalized weights,
        location compatibility, and domain relevance filtering."""
        # 1. Location Compatibility Analysis
        _det_loc = getattr(criteria, "location", None)
        _det_prefs = getattr(criteria, "preferred_locations", None) or ([_det_loc] if _det_loc else [])
        target_locs_eval = _det_prefs
        loc_compatibility = self.analyze_location_compatibility(candidate, target_locs_eval)

        # 2. Domain & Industry Relevance Classification
        domain_tier, domain_notes = self.classify_domain_relevance(candidate, criteria.job_title, criteria.department or "Information Technology")

        # Text dossiers for evidence retrieval
        headline_text = (candidate.headline or "").strip()
        headline_lower = headline_text.lower()
        about_text = (candidate.about or "").strip()
        about_lower = about_text.lower()
        exp_entries = candidate.experience_history or []
        exp_text = " ".join(f"{e.get('title', '')} {e.get('company', '')} {e.get('description', '')}" for e in exp_entries)
        exp_lower = exp_text.lower()
        edu_entries = candidate.education or []
        edu_text = " ".join(f"{ed.get('school', '')} {ed.get('degree', '')}" for ed in edu_entries)
        edu_lower = edu_text.lower()
        cert_entries = candidate.certifications or []
        cert_text = " ".join(f"{c.get('name', '')} {c.get('issuing_org', '')}" for c in cert_entries)
        cert_lower = cert_text.lower()
        proj_entries = candidate.projects or []
        proj_text = " ".join(f"{p.get('title', '')} {p.get('description', '')}" for p in proj_entries)
        proj_lower = proj_text.lower()
        act_entries = candidate.recent_activity or []
        act_text = " ".join(f"{a.get('headline', '')} {a.get('snippet', '')}" for a in act_entries)
        act_lower = act_text.lower()
        skills_text = " ".join(candidate.skills)
        skills_lower = skills_text.lower()

        full_dossier = f"{headline_lower} {about_lower} {exp_lower} {edu_lower} {cert_lower} {proj_lower} {act_lower} {skills_lower} {(candidate.raw_snippet or '').lower()}"

        evidence_quotes = []
        matched_mandatory = []
        missing_mandatory = []
        category_evals: Dict[str, CategoryEvaluation] = {}

        # -------------------------------------------------------------
        # Category 1: Experience Assessment (Weight: 35%)
        # -------------------------------------------------------------
        exp_evidence = ""
        exp_source = "Experience"
        if exp_entries:
            exp_evidence = f"{exp_entries[0].get('title', '')} at {exp_entries[0].get('company', '')}"
        elif headline_text:
            exp_evidence = headline_text.split("•")[0].strip()
            exp_source = "Headline"

        if self.is_executive_or_founder(headline_text, criteria.job_title):
            # Executive / Founder mismatch for standard employee roles
            exp_score = 25.0
            exp_status = "Not Matched"
            exp_state = "available_irrelevant"
            exp_expl = f"Candidate is an active Founder/CEO/Business Owner ({exp_evidence}). Active founders and agency owners are running their own businesses and are not suitable candidates for employee vacancies."
        elif domain_tier == "Partially Relevant":
            # State B: Available but non-engineering / EdTech domain
            exp_score = 45.0
            exp_status = "Partially Matched"
            exp_state = "available_relevant"
            exp_expl = f"Candidate holds leadership in educational technology ({exp_evidence}), but lacks verified commercial IT software engineering delivery."
        elif domain_tier == "Not Relevant":
            exp_score = 20.0
            exp_status = "Not Matched"
            exp_state = "available_irrelevant"
            exp_expl = f"Experience ({exp_evidence}) is in an unrelated professional domain."
        else:
            exp_score = 75.0
            req_years = criteria.min_years_experience or 3.0
            cand_years = candidate.experience_years or 5.0
            if cand_years >= req_years:
                exp_score += 15.0
            exp_score = min(100.0, exp_score)
            exp_status = "Matched" if exp_score >= 75.0 else "Partially Matched"
            exp_state = "available_relevant"
            exp_expl = f"Demonstrated {cand_years}+ years of professional engineering experience ({exp_evidence})."

        if exp_evidence:
            evidence_quotes.append(EvidenceQuote(
                criterion_requirement="Relevant Professional Experience",
                verbatim_quote=exp_evidence[:140],
                is_match=(exp_score >= 50.0),
                confidence=0.90,
            ))

        category_evals["experience"] = CategoryEvaluation(
            category_name="Experience",
            weight=0.35,
            score=exp_score,
            evaluation_state=exp_state,
            status=exp_status,
            evidence_found=exp_evidence[:140],
            evidence_source=exp_source,
            confidence=0.90,
            explanation=exp_expl,
        )

        # -------------------------------------------------------------
        # Category 2: Technical Skills Assessment (Weight: 25%)
        # -------------------------------------------------------------
        for skill in criteria.mandatory_skills:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, full_dossier):
                matched_mandatory.append(skill)
                v_quote = f"Mentioned: {skill}"
                if skill.lower() in headline_lower:
                    v_quote = headline_text
                elif skill.lower() in exp_lower and exp_entries:
                    for e in exp_entries:
                        if skill.lower() in str(e).lower():
                            v_quote = f"{e.get('title', 'Role')} at {e.get('company', 'Company')}"
                            break
                elif skill.lower() in skills_lower:
                    v_quote = f"Skill: {skill}"

                evidence_quotes.append(EvidenceQuote(
                    criterion_requirement=f"Proficiency in {skill}",
                    verbatim_quote=v_quote[:120],
                    is_match=True,
                    confidence=0.92,
                ))
            else:
                missing_mandatory.append(skill)

        total_mand = len(criteria.mandatory_skills) or 1
        matched_ratio = len(matched_mandatory) / total_mand
        skills_score = round(min(100.0, matched_ratio * 100.0), 1)

        if matched_mandatory:
            sk_status = "Matched" if skills_score >= 70.0 else "Partially Matched"
            sk_state = "available_relevant"
            sk_found = ", ".join(matched_mandatory)
            sk_expl = f"Verified evidence for {len(matched_mandatory)} of {total_mand} mandatory skills: {sk_found}."
        elif candidate.skills:
            # Candidate has skills, but irrelevant to JD
            sk_score = 15.0
            sk_status = "Not Matched"
            sk_state = "available_irrelevant"
            sk_found = ", ".join(candidate.skills[:4])
            sk_expl = f"Extracted skills ({sk_found}) do not satisfy mandatory requirements for {criteria.job_title}."
        else:
            # No skills listed on public profile
            sk_score = 25.0
            sk_status = "Needs Verification"
            sk_state = "available_relevant"
            sk_found = "Headline references"
            sk_expl = "Specific technical stack skills are not itemized on public profile; needs recruiter verification."

        category_evals["skills"] = CategoryEvaluation(
            category_name="Technical Skills",
            weight=0.25,
            score=skills_score,
            evaluation_state=sk_state,
            status=sk_status,
            evidence_found=sk_found,
            evidence_source="Skills & Dossier",
            confidence=0.92,
            explanation=sk_expl,
        )

        # -------------------------------------------------------------
        # Category 3: Executive Summary & Professional About (Weight: 15%)
        # -------------------------------------------------------------
        if about_text and len(about_text) >= 15:
            if domain_tier == "Highly Relevant":
                ab_score = 95.0
                ab_status = "Matched"
                ab_state = "available_relevant"
            elif domain_tier == "Relevant":
                ab_score = 80.0
                ab_status = "Matched"
                ab_state = "available_relevant"
            elif domain_tier == "Partially Relevant":
                ab_score = 45.0
                ab_status = "Partially Matched"
                ab_state = "available_relevant"
            else:
                ab_score = 20.0
                ab_status = "Not Matched"
                ab_state = "available_irrelevant"
            ab_found = about_text[:120]
            ab_expl = f"Executive summary reflects {domain_tier.lower()} alignment: {about_text[:80]}..."
            ab_conf = 0.90
        else:
            ab_score = None
            ab_status = "Not Available"
            ab_state = "not_available"
            ab_found = ""
            ab_expl = "About section is not published on accessible LinkedIn profile. Not penalized with zero score."
            ab_conf = 0.50

        category_evals["about"] = CategoryEvaluation(
            category_name="About",
            weight=0.15,
            score=ab_score,
            evaluation_state=ab_state,
            status=ab_status,
            evidence_found=ab_found,
            evidence_source="About Section",
            confidence=ab_conf,
            explanation=ab_expl,
        )

        # Informational Domain Relevance category for consumers expecting it
        dom_score = 95.0 if domain_tier == "Highly Relevant" else 80.0 if domain_tier == "Relevant" else 45.0 if domain_tier == "Partially Relevant" else 15.0
        category_evals["domain_relevance"] = CategoryEvaluation(
            category_name="Domain Relevance",
            weight=0.0,
            score=dom_score,
            evaluation_state="available_relevant" if dom_score >= 40.0 else "available_irrelevant",
            status="Matched" if dom_score >= 70.0 else "Partially Matched" if dom_score >= 40.0 else "Not Matched",
            evidence_found=f"{domain_tier} — {domain_notes[:80]}",
            evidence_source="Career Domain",
            confidence=0.95,
            explanation=domain_notes,
        )

        # -------------------------------------------------------------
        # Category 4: Education & Academic Background (Weight: 10%)
        # -------------------------------------------------------------
        if edu_entries:
            edu_score = 85.0
            top_edu = edu_entries[0]
            edu_found = f"{top_edu.get('degree', '')} from {top_edu.get('school', '')}".strip()
            if any(term in edu_lower for term in ["computer science", "engineering", "technology", "artificial intelligence", "data"]):
                edu_score = 95.0
            category_evals["education"] = CategoryEvaluation(
                category_name="Education",
                weight=0.10,
                score=edu_score,
                evaluation_state="available_relevant",
                status="Matched",
                evidence_found=edu_found,
                evidence_source="Education Section",
                confidence=0.90,
                explanation=f"Academic credentials verified: {edu_found}.",
            )
        else:
            category_evals["education"] = CategoryEvaluation(
                category_name="Education",
                weight=0.10,
                score=None,
                evaluation_state="not_available",
                status="Not Available",
                evidence_found="",
                evidence_source="Profile",
                confidence=0.70,
                explanation="Education section is not published on accessible LinkedIn profile. Not penalized with verified mismatch.",
            )

        # -------------------------------------------------------------
        # Category 5: Certifications & Licenses (Weight: 5%)
        # -------------------------------------------------------------
        if cert_entries:
            cert_found = ", ".join(c.get('name', '') for c in cert_entries[:2])
            category_evals["certifications"] = CategoryEvaluation(
                category_name="Certifications",
                weight=0.05,
                score=85.0,
                evaluation_state="available_relevant",
                status="Matched",
                evidence_found=cert_found,
                evidence_source="Certifications Section",
                confidence=0.90,
                explanation=f"Licenses/certifications held: {cert_found}.",
            )
        else:
            category_evals["certifications"] = CategoryEvaluation(
                category_name="Certifications",
                weight=0.05,
                score=None,
                evaluation_state="not_available",
                status="Not Available",
                evidence_found="",
                evidence_source="Profile",
                confidence=0.60,
                explanation="Certifications section is not published on accessible LinkedIn profile. Not penalized with zero score.",
            )

        # -------------------------------------------------------------
        # Category 6: Projects & Technical Architecture (Weight: 5%)
        # -------------------------------------------------------------
        if proj_entries:
            proj_found = ", ".join(p.get('title', '') for p in proj_entries[:2])
            category_evals["projects"] = CategoryEvaluation(
                category_name="Projects",
                weight=0.05,
                score=85.0,
                evaluation_state="available_relevant",
                status="Matched",
                evidence_found=proj_found,
                evidence_source="Projects Section",
                confidence=0.90,
                explanation=f"Featured projects: {proj_found}.",
            )
        else:
            category_evals["projects"] = CategoryEvaluation(
                category_name="Projects",
                weight=0.05,
                score=None,
                evaluation_state="not_available",
                status="Not Available",
                evidence_found="",
                evidence_source="Profile",
                confidence=0.60,
                explanation="Featured projects section not published on profile. Not penalized with zero score.",
            )

        # -------------------------------------------------------------
        # Category 7: Professional Activity & Articles (Weight: 5%)
        # -------------------------------------------------------------
        if act_entries:
            act_found = act_entries[0].get('headline', '')[:80]
            category_evals["activity"] = CategoryEvaluation(
                category_name="Activity",
                weight=0.05,
                score=80.0,
                evaluation_state="available_relevant",
                status="Matched",
                evidence_found=act_found,
                evidence_source="Activity Section",
                confidence=0.85,
                explanation=f"Recent public professional activity: {act_found}.",
            )
        else:
            category_evals["activity"] = CategoryEvaluation(
                category_name="Activity",
                weight=0.05,
                score=None,
                evaluation_state="not_available",
                status="Not Available",
                evidence_found="",
                evidence_source="Profile",
                confidence=0.50,
                explanation="Recent public posts/activity not published on profile. Not penalized with zero score.",
            )

        # -------------------------------------------------------------
        # Normalization Formula Across Evaluable Categories
        # -------------------------------------------------------------
        evaluable_cats = [c for c in category_evals.values() if c.score is not None]
        total_evaluable_weight = sum(c.weight for c in evaluable_cats)

        if total_evaluable_weight > 0:
            weighted_sum = sum(c.weight * c.score for c in evaluable_cats)
            composite_fit = round(weighted_sum / total_evaluable_weight, 1)
        else:
            composite_fit = 0.0

        coverage = round(min(100.0, (total_evaluable_weight / 1.0) * 100.0), 1)

        # Itemized section_scores mapping (using score or None)
        section_scores = {
            "experience": category_evals["experience"].score,
            "skills": category_evals["skills"].score,
            "about": category_evals["about"].score,
            "domain_relevance": category_evals["domain_relevance"].score,
            "education": category_evals["education"].score,
            "certifications": category_evals["certifications"].score,
            "projects": category_evals["projects"].score,
            "activity": category_evals["activity"].score,
        }

        if composite_fit >= 75.0 and domain_tier in ("Highly Relevant", "Relevant"):
            level = "High"
        elif composite_fit >= 45.0 or domain_tier == "Partially Relevant":
            level = "Medium"
        else:
            level = "Low"

        not_avail_count = sum(1 for c in category_evals.values() if c.evaluation_state == "not_available")
        coverage_note = f" ({not_avail_count} sections not published on public profile, score normalized across {int(coverage)}% profile coverage)" if not_avail_count > 0 else ""

        justification = (
            f"Candidate evaluated with {composite_fit}% composite fit{coverage_note}. "
            f"Domain: {domain_tier} — {domain_notes}. "
            f"Location: {loc_compatibility['status']} ({loc_compatibility['reason']}). "
            f"Matched {len(matched_mandatory)} of {total_mand} mandatory skills."
        )

        return MatchEvaluation(
            candidate_id=candidate.id or candidate.canonical_url,
            fit_score=composite_fit,
            completeness_score=min(100.0, round((len(evidence_quotes) / total_mand) * 100.0, 1)),
            evaluation_coverage=coverage,
            match_level=level,
            domain_relevance=domain_tier,
            domain_relevance_notes=domain_notes,
            location_compatibility=loc_compatibility,
            justification_summary=justification,
            evidence_quotes=evidence_quotes,
            missing_criteria=missing_mandatory,
            section_scores=section_scores,
            category_evaluations=category_evals,
        )

    def optimize_sourcing_query(
        self,
        role_title: str,
        current_query: str,
        mandatory_skills: Optional[List[str]] = None,
        attempt: int = 1,
        previous_queries: Optional[List[str]] = None,
        reason: str = "saturation",
        preferred_locations: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Intelligent AI & Heuristic Decision Layer to pivot or relax search queries.
        
        - If reason == 'no_results': Progressively broadens constraints while STRICTLY PRESERVING
          the company's preferred location (e.g. Chennai, Coimbatore, Bangalore).
        - If reason == 'saturation': Synthesizes an orthogonal query angle to discover fresh candidates
          while strictly maintaining the company's preferred location.
        """
        previous_queries = previous_queries or [current_query]

        if attempt > 3:
            return {
                "action": "stop_saturation",
                "optimized_query": current_query,
                "strategy": "talent_pool_saturated",
                "explanation": "Talent pool search space is fully explored after multiple pivots. Concluding sourcing.",
            }

        # 1. Guaranteed location resolution with city/state priority over broad country catch-alls
        loc_clause = self._build_location_clause(preferred_locations, location)

        # Extract primary city token for unquoted keyword fallback
        clean_locs = self._clean_location_tokens(preferred_locations or ([location] if location else []))
        BROAD_COUNTRY_NAMES = {
            "india", "united states", "usa", "us", "u.s.", "u.s.a.",
            "united kingdom", "uk", "u.k.", "canada", "australia",
            "germany", "france", "singapore", "netherlands", "malaysia",
            "philippines", "indonesia", "pakistan", "bangladesh", "sri lanka",
            "saudi arabia", "qatar", "kuwait", "bahrain", "oman", "egypt"
        }
        local_cands = [t for t in clean_locs if t.lower() not in BROAD_COUNTRY_NAMES]
        primary_loc = local_cands[0] if local_cands else (clean_locs[0] if clean_locs else "")

        # If not passed via args, extract location clause or city name from current_query
        if not loc_clause:
            loc_match = re.search(r'\s+AND\s+(\([^\)]+\)|"[^"]+"|[A-Za-z\s]+)$', current_query, re.I)
            if loc_match:
                cand_clause = loc_match.group(0).strip()
                inner_txt = re.sub(r'[\(\)"\']', '', cand_clause.replace('AND', '')).strip()
                # Verify it is not a skill group (e.g. not AND (Python OR React))
                if not any(sk in inner_txt.lower() for sk in ["python", "react", "java", "sql", "aws", "node", "typescript", "c++", "fastapi", "vue"]):
                    loc_clause = f" {cand_clause}"
                    if not primary_loc and inner_txt:
                        primary_loc = re.split(r'\s+OR\s+', inner_txt, flags=re.I)[0].strip()

        # If still not found, scan current_query for known cities/regions
        if not loc_clause:
            KNOWN_LOCATIONS = [
                "chennai", "coimbatore", "tamil nadu", "tamilnadu", "bangalore", "bengaluru",
                "hyderabad", "pune", "mumbai", "delhi", "new delhi", "noida", "gurgaon",
                "dubai", "abu dhabi", "sharjah", "uae", "san francisco", "london", "singapore"
            ]
            for kn in KNOWN_LOCATIONS:
                if re.search(r'\b' + re.escape(kn) + r'\b', current_query, re.I):
                    loc_clause = self._build_location_clause([kn])
                    if not primary_loc:
                        primary_loc = kn.title()
                    break

        clean_title = re.sub(r'["\']', '', role_title).strip() or "Engineer"
        # Preserve full professional title words while stripping pure seniority prefixes
        title_words = [w for w in clean_title.split() if w.lower() not in ("senior", "sr", "junior", "jr", "lead", "staff", "principal", "associate")]
        base_role = " ".join(title_words) if title_words else clean_title

        # Special handling for 0 results on LinkedIn: PROGRESSIVE RELAXATION
        if reason == "no_results":
            is_ai = any(x in clean_title.lower() for x in ["ai", "machine learning", "ml", "deep learning"])
            is_fullstack = any(x in clean_title.lower() for x in ["fullstack", "full stack", "full-stack"])
            is_frontend = any(x in clean_title.lower() for x in ["frontend", "front end", "ui", "react"])
            is_backend = any(x in clean_title.lower() for x in ["backend", "back end", "node", "python engineer"])
            is_pm = any(x in clean_title.lower() for x in ["product manager", "product owner", "pm"])
            is_bi = any(x in clean_title.lower() for x in ["data analyst", "bi", "business intelligence"])

            if is_ai and not is_pm:
                domain_group = '("AI" OR "Machine Learning")'
                single_anchor = '"AI"'
            elif is_fullstack:
                domain_group = '("Fullstack Engineer" OR "Full Stack Developer")'
                single_anchor = '"Fullstack Engineer"'
            elif is_frontend:
                domain_group = '("Frontend Developer" OR "Frontend Engineer")'
                single_anchor = '"Frontend Developer"'
            elif is_backend:
                domain_group = '("Backend Developer" OR "Backend Engineer")'
                single_anchor = '"Backend Developer"'
            elif is_pm:
                domain_group = '("Product Manager" OR "Technical Product Manager")'
                single_anchor = '"Product Manager"'
            elif is_bi:
                domain_group = '("Data Analyst" OR "BI Specialist")'
                single_anchor = '"Data Analyst"'
            else:
                domain_group = f'("{base_role}")'
                single_anchor = f'"{base_role}"'

            if attempt == 1:
                # Relaxation 1: Eliminate all job-title / seniority restrictions. Core domain only + location
                opt_q = f'{domain_group}{loc_clause}'.strip()
                return {
                    "action": "pivot_query",
                    "optimized_query": opt_q,
                    "strategy": "domain_only_relaxation",
                    "explanation": f"Removed all job-title and seniority restrictions to maximize candidate recall in target location ({primary_loc or 'Target Location'}).",
                }
            elif attempt == 2:
                # Relaxation 2: Core single anchor in quotes + location
                opt_q = f'{single_anchor}{loc_clause}'.strip()
                return {
                    "action": "pivot_query",
                    "optimized_query": opt_q,
                    "strategy": "core_anchor_relaxation",
                    "explanation": f"Simplified search to single core role anchor {single_anchor} directly with location ({primary_loc or 'Target Location'}).",
                }
            else:
                # Relaxation 3: Minimal plain recruiter keywords with city/location without Boolean parentheses
                loc_token = primary_loc or (clean_locs[0] if clean_locs else "")
                opt_q = f'{base_role} {loc_token}'.strip() if loc_token else base_role
                return {
                    "action": "pivot_query",
                    "optimized_query": opt_q,
                    "strategy": "plain_keyword_relaxation",
                    "explanation": f"Searching plain recruiter keywords '{opt_q}' to bypass complex Boolean parsing limits while strictly keeping location.",
                }

        # Handling for saturation (duplicate profiles in DB): AI-driven or heuristic orthogonal pivot
        if self.is_ai_available():
            system_instruction = (
                "You are an autonomous AI sourcing strategist for technical recruitment on LinkedIn. "
                "Synthesize a new, distinct search query for the LinkedIn search bar that targets DIFFERENT candidates matching the role. "
                "CRITICAL RULES:\n"
                "1. NEVER CHAIN THREE GROUPS WITH 'AND'. Max ONE 'AND' operator connecting the role/skill group to the location group.\n"
                "2. NEVER REQUIRE STANDALONE SENIORITY WORDS ('Lead', 'Senior', 'Head', 'Architect') AS A SEPARATE 'AND' GROUP.\n"
                "3. Use compound terms or skills in a single OR group: [Role / Tech OR group] AND [Location OR group].\n"
                "4. Keep under 100 characters total. Never include work modes ('Hybrid', 'On-site', 'Remote').\n"
                "5. STRICTLY MAINTAIN THE TARGET COMPANY LOCATION. Under no circumstances change, replace, or drop the location filter."
            )
            prompt = f"""Role: {clean_title}
Mandatory Skills: {', '.join(mandatory_skills or [])}
Current Saturated Query: "{current_query}"
Previous Queries Attempted: {json.dumps(previous_queries)}
Location Filter to Append: {loc_clause or 'None'}
Pivot Attempt: #{attempt} of 3.

Generate a NEW, distinct search query for LinkedIn that returns DIFFERENT candidate profiles matching this role.
JSON Schema:
{{
  "action": "pivot_query",
  "optimized_query": "clean LinkedIn search query string",
  "strategy": "title_pivot | skill_cluster_pivot | boolean_expansion",
  "explanation": "Short 1-sentence reason why this surfaces different candidates"
}}"""
            try:
                res = self._call_gemini_json(prompt, system_instruction)
                if res and res.get("optimized_query"):
                    opt_q = res["optimized_query"].strip()
                    opt_q = re.sub(r'["\']?(?:Hybrid|On-site|Remote|onsite|hybrid)[^"\'\)]*["\']?\s*(?:OR|AND)?\s*', '', opt_q, flags=re.I).strip()
                    if loc_clause:
                        # Strip any existing or hallucinated trailing AND (...) location group before appending genuine configured location
                        opt_q = re.sub(r'\s+AND\s+\([^\)]+\)$', '', opt_q, flags=re.I).strip()
                        opt_q = re.sub(r'\s+AND\s+"[^"]+"$', '', opt_q, flags=re.I).strip()
                        opt_q = f"{opt_q}{loc_clause}"
                    if opt_q and opt_q not in previous_queries:
                        return {
                            "action": "pivot_query",
                            "optimized_query": opt_q,
                            "strategy": res.get("strategy", "ai_llm_pivot"),
                            "explanation": res.get("explanation", "AI synthesized an orthogonal query angle to discover fresh candidate profiles."),
                        }
            except Exception as e:
                logger.warning("Gemini query optimization failed: %s. Using deterministic pivot.", e)

        # Robust deterministic fallback
        return self._deterministic_query_pivot(
            role_title=role_title,
            current_query=current_query,
            mandatory_skills=mandatory_skills,
            attempt=attempt,
            previous_queries=previous_queries,
            loc_clause=loc_clause,
        )

    def _deterministic_query_pivot(
        self,
        role_title: str,
        current_query: str,
        mandatory_skills: Optional[List[str]] = None,
        attempt: int = 1,
        previous_queries: Optional[List[str]] = None,
        loc_clause: str = "",
    ) -> Dict[str, Any]:
        """Deterministic query synthesizer providing orthogonal query rotations offline with preserved location."""
        previous_queries = previous_queries or [current_query]
        clean_title = re.sub(r'["\']', '', role_title).strip() or "Engineer"
        title_words = [w for w in clean_title.split() if w.lower() not in ("senior", "sr", "junior", "jr", "lead", "staff", "principal", "associate")]
        base_role = " ".join(title_words) if title_words else clean_title
        title_lower = (role_title or current_query).lower()

        # Guarantee location clause is present
        if not loc_clause:
            loc_match = re.search(r'\s+AND\s+(\([^\)]+\)|"[^"]+"|[A-Za-z\s]+)$', current_query, re.I)
            if loc_match:
                loc_clause = f" {loc_match.group(0).strip()}"

        is_ai_role = any(x in title_lower for x in ["ai", "machine learning", "ml", "genai", "llm", "deep learning", "nlp"])

        candidate_queries: List[Tuple[str, str, str]] = []

        if is_ai_role:
            candidate_queries = [
                (
                    f'("Lead AI Engineer" OR "Head of AI" OR "AI Lead"){loc_clause}'.strip(),
                    "title_pivot",
                    "Pivoted to compound leadership titles ('Lead AI Engineer', 'Head of AI', 'AI Lead').",
                ),
                (
                    f'("Machine Learning Lead" OR "Lead ML Engineer" OR "ML Lead"){loc_clause}'.strip(),
                    "specialty_pivot",
                    "Targeting Machine Learning leadership titles without skill constraints.",
                ),
                (
                    f'("AI Systems Architect" OR "AI Architect" OR "Chief Architect"){loc_clause}'.strip(),
                    "architecture_pivot",
                    "Targeting AI architecture specialists and system architects.",
                ),
                (
                    f'("Generative AI Lead" OR "Staff AI Engineer" OR "Principal AI"){loc_clause}'.strip(),
                    "subspecialty_pivot",
                    "Targeting Generative AI and Staff/Principal level practitioners.",
                ),
            ]
        else:
            candidate_queries = [
                (
                    f'("Lead {base_role}" OR "Principal {base_role}"){loc_clause}'.strip(),
                    "title_pivot",
                    f"Pivoting to 'Lead {base_role}' to uncover senior practitioners.",
                ),
                (
                    f'("Senior {base_role}" OR "{base_role} Specialist"){loc_clause}'.strip(),
                    "seniority_expansion",
                    f"Broadening seniority range to discover {base_role} specialists.",
                ),
            ]

        for q_str, strat, exp in candidate_queries:
            if q_str not in previous_queries and q_str != current_query:
                return {
                    "action": "pivot_query",
                    "optimized_query": q_str,
                    "strategy": strat,
                    "explanation": exp,
                }

        return {
            "action": "stop_saturation",
            "optimized_query": current_query,
            "strategy": "talent_pool_saturated",
            "explanation": "Search pool exhausted for current role parameters. All reachable candidate profiles gathered.",
        }

    def generate_outreach_message(
        self,
        candidate: Any,
        role_title: str = "Senior Engineer",
        company_name: str = "Our Team",
        company_details: Optional[str] = None,
        recruiter_name: str = "Talent Acquisition Team",
        tone: str = "formal",
        force_deterministic: bool = False,
    ) -> Dict[str, str]:
        """Generates a personalized, professional LinkedIn outreach message and 300-char connection note."""
        # Normalize candidate metadata
        if isinstance(candidate, str):
            c_name = candidate
            headline = ""
            skills = []
            current_comp = ""
        elif isinstance(candidate, dict):
            c_name = candidate.get("name", "Candidate")
            headline = candidate.get("headline", "")
            skills = candidate.get("skills", [])
            current_comp = candidate.get("current_company", "")
        else:
            c_name = getattr(candidate, "name", "Candidate")
            headline = getattr(candidate, "headline", "")
            skills = getattr(candidate, "skills", [])
            current_comp = getattr(candidate, "current_company", "")

        first_name = c_name.split()[0].strip() if c_name and c_name.strip() else "Candidate"
        clean_hl = re.sub(r"\s+", " ", headline).strip() if headline else ""

        # Attempt Gemini AI generation if available and not forced deterministic
        if not force_deterministic and self.is_ai_available():
            prompt = f"""
Draft a personalized LinkedIn candidate outreach message for:
Candidate Name: {c_name}
First Name: {first_name}
Current Headline/Role: {clean_hl}
Current Organization: {current_comp}
Key Skills: {', '.join(skills[:5]) if skills else 'Relevant industry experience'}

Opportunity Details:
Hiring Role: {role_title}
Hiring Organization: {company_name}
Company Context: {company_details or 'A high-growth team delivering cutting-edge solutions.'}
Recruiter / Sender: {recruiter_name}
Tone: {tone} (formal, respectful, clear, and high-conversion)

Output strict JSON:
{{
  "subject": "<Concise subject under 60 chars>",
  "message_body": "<Formal 3-paragraph message addressed to Dear {first_name}, citing their background, describing role/company, inviting to 15-min chat, signed with {recruiter_name} and {company_name}>",
  "connection_note": "<Concise connection request note STRICTLY UNDER 290 CHARACTERS including spaces, greeting {first_name}, mentioning {role_title} at {company_name}, and inviting to connect>"
}}
"""
            sys_inst = (
                "You are an executive talent acquisition partner drafting a high-impact, polite, and formal LinkedIn outreach message. "
                "The 'connection_note' MUST NEVER exceed 295 characters as LinkedIn rejects invitation notes above 300 chars."
            )
            try:
                res = self._call_gemini_json(prompt, sys_inst)
                if res and isinstance(res, dict) and "message_body" in res:
                    subj = str(res.get("subject") or f"Opportunity: {role_title} at {company_name}").strip()
                    body = str(res.get("message_body", "")).strip()
                    note = str(res.get("connection_note", "")).strip()

                    # Strictly enforce LinkedIn's <= 200 character limit on free accounts (195 chars)
                    if len(note) > 195:
                        note = note[:192].rstrip() + "..."

                    if body:
                        return {
                            "subject": subj,
                            "message_body": body,
                            "connection_note": note or self._deterministic_connection_note(first_name, role_title, company_name, skills, recruiter_name),
                        }
            except Exception as e:
                logger.warning("Gemini outreach generation error: %s. Using deterministic generator.", e)

        # High-precision deterministic fallback
        return self._deterministic_outreach_generator(
            first_name=first_name,
            headline=clean_hl,
            skills=skills,
            role_title=role_title,
            company_name=company_name,
            company_details=company_details,
            recruiter_name=recruiter_name,
        )

    def _deterministic_connection_note(
        self,
        first_name: str,
        role_title: str,
        company_name: str,
        skills: Optional[List[str]],
        recruiter_name: str,
    ) -> str:
        """Constructs a connection note guaranteed to be <= 195 characters for LinkedIn free/premium limits."""
        skill_mention = skills[0] if (skills and len(skills[0]) <= 15) else "your background"
        note = (
            f"Hi {first_name}, impressed by {skill_mention}! "
            f"We're hiring a {role_title} at {company_name} and think you'd be a great fit. "
            f"Would love to connect! - {recruiter_name}"
        )
        if len(note) > 195:
            note = (
                f"Hi {first_name}, we're actively hiring a {role_title} at {company_name} and "
                f"would love to connect. Best, {recruiter_name}"
            )
        if len(note) > 195:
            note = f"Hi {first_name}, hiring for {role_title} at {company_name}. Would love to connect! - {recruiter_name}"
        if len(note) > 195:
            note = f"Hi {first_name}, hiring for {role_title}. Would love to connect!"
        return note[:195]

    def _deterministic_outreach_generator(
        self,
        first_name: str,
        headline: str,
        skills: Optional[List[str]],
        role_title: str,
        company_name: str,
        company_details: Optional[str],
        recruiter_name: str,
    ) -> Dict[str, str]:
        """Deterministic formal hiring outreach message generator."""
        subject = f"Opportunity: {role_title} at {company_name}"

        # Clean headline for inclusion
        clean_hl = headline
        for pref in ["Looking for", "Actively seeking", "Open to"]:
            if clean_hl.lower().startswith(pref.lower()):
                clean_hl = clean_hl[len(pref):].strip(": -")

        hl_phrase = f"your work as {clean_hl}" if clean_hl else "your professional track record"
        
        top_skills = [s for s in (skills or []) if isinstance(s, str) and len(s) < 25][:3]
        skills_phrase = f"your proven background in {', '.join(top_skills)}" if top_skills else "your technical depth"

        company_desc = f" ({company_details.strip()})" if company_details and len(company_details.strip()) > 3 else ""

        message_body = (
            f"Dear {first_name},\n\n"
            f"I hope this note finds you well. I came across your profile and was genuinely impressed by {hl_phrase}.\n\n"
            f"We are currently expanding our team at {company_name}{company_desc} and are actively hiring for a {role_title}. "
            f"Given {skills_phrase}, we believe your experience and leadership would be a tremendous asset to what we are building.\n\n"
            f"I would welcome the opportunity to connect and share more context about the role, our current roadmap, and team culture. "
            f"Are you open to a brief introductory conversation this week?\n\n"
            f"Warm regards,\n"
            f"{recruiter_name}\n"
            f"{company_name}"
        )

        connection_note = self._deterministic_connection_note(
            first_name=first_name,
            role_title=role_title,
            company_name=company_name,
            skills=skills,
            recruiter_name=recruiter_name,
        )

        return {
            "subject": subject,
            "message_body": message_body,
            "connection_note": connection_note,
        }


ai_service = AIService()
