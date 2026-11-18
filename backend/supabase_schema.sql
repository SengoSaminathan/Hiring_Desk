-- ==============================================================================
-- HIRING DESK: SUPABASE POSTGRESQL SCHEMA
-- ==============================================================================
-- Run this script in the Supabase SQL Editor (https://supabase.com/dashboard/project/_/sql)
-- It creates the complete schema for candidates, AI match evaluations, and job requisitions.
-- Includes JSONB column types, foreign keys, cascade deletes, automated updated_at triggers,
-- GIN indexes for fast skill/profile searches, and Row Level Security (RLS) policies.
-- ==============================================================================

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Trigger function to automatically maintain updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- TABLE 1: candidates
-- Normalized profiles harvested from LinkedIn and candidate resumes.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.candidates (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    canonical_url TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    headline TEXT,
    current_company TEXT,
    location TEXT,
    current_location TEXT,
    preferred_work_locations JSONB DEFAULT '[]'::jsonb,
    willingness_to_relocate TEXT DEFAULT 'Unknown', -- 'Yes', 'Likely', 'Unknown', 'No'
    work_authorization TEXT,                        -- e.g. 'UAE Golden Visa Holder', 'Citizen', etc.
    location_compatibility_status TEXT DEFAULT 'Compatible', -- 'Compatible', 'Needs Verification', 'Incompatible'
    location_compatibility_reason TEXT,
    domain_relevance TEXT DEFAULT 'Relevant',       -- 'Highly Relevant', 'Relevant', 'Partially Relevant', 'Not Relevant'
    domain_relevance_notes TEXT,
    experience_years NUMERIC(4, 1) DEFAULT 5.0,
    about TEXT,
    skills JSONB DEFAULT '[]'::jsonb,               -- Array of extracted skill strings: ["Python", "FastAPI", "RAG"]
    experience_history JSONB DEFAULT '[]'::jsonb,   -- Array of positions: [{role, company, dates, description}]
    education JSONB DEFAULT '[]'::jsonb,            -- Array of degrees: [{school, degree, field_of_study, dates}]
    certifications JSONB DEFAULT '[]'::jsonb,       -- Array of certs: [{name, issuer, issue_date}]
    projects JSONB DEFAULT '[]'::jsonb,             -- Array of projects: [{title, url, description}]
    recent_activity JSONB DEFAULT '[]'::jsonb,      -- Array of posts: [{engagement_type, date, post_snippet}]
    section_scores JSONB DEFAULT '{}'::jsonb,       -- Itemized scores: {experience: 85, skills: 90, ...}
    raw_snippet TEXT,
    avatar_url TEXT,
    status TEXT DEFAULT 'New',                      -- 'New', 'In Review', 'Shortlisted', 'Not a Fit'
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Trigger for candidates updated_at
DROP TRIGGER IF EXISTS set_candidates_updated_at ON public.candidates;
CREATE TRIGGER set_candidates_updated_at
BEFORE UPDATE ON public.candidates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- TABLE 2: evaluations
-- Multi-criteria AI candidate evaluations with 3-state evidence scoring.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.evaluations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id TEXT NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
    job_title TEXT DEFAULT 'Target Role',
    fit_score NUMERIC(5, 2) NOT NULL,               -- Composite normalized score (0.00 to 100.00)
    completeness_score NUMERIC(5, 2) DEFAULT 0.00,
    evaluation_coverage NUMERIC(5, 2) DEFAULT 100.00,-- % of evaluable profile sections (avoids 0% missing penalties)
    match_level TEXT DEFAULT 'Medium',              -- 'High', 'Medium', 'Low', 'Poor'
    domain_relevance TEXT DEFAULT 'Relevant',       -- 'Highly Relevant', 'Relevant', 'Partially Relevant', 'Not Relevant'
    domain_relevance_notes TEXT,
    location_compatibility JSONB DEFAULT '{}'::jsonb,
    justification TEXT,
    evidence_quotes JSONB DEFAULT '[]'::jsonb,      -- Array of [{requirement, verbatim_quote, confidence}]
    missing_criteria JSONB DEFAULT '[]'::jsonb,     -- Array of unverified JD criteria: ["Docker", "Kubernetes"]
    section_scores JSONB DEFAULT '{}'::jsonb,
    category_evaluations JSONB DEFAULT '{}'::jsonb, -- 3-state category objects: {weight, score, evaluation_state, status, evidence_found, explanation}
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==============================================================================
-- TABLE 3: jobs (Optional / Recommended)
-- Stored Job Descriptions, requirements, and target criteria.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.jobs (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    job_title TEXT NOT NULL,
    department TEXT,
    seniority_level TEXT DEFAULT 'Senior',
    min_years_experience NUMERIC(4, 1),
    max_years_experience NUMERIC(4, 1),
    mandatory_skills JSONB DEFAULT '[]'::jsonb,
    preferred_skills JSONB DEFAULT '[]'::jsonb,
    technologies JSONB DEFAULT '[]'::jsonb,
    preferred_locations JSONB DEFAULT '[]'::jsonb,
    criteria_list JSONB DEFAULT '[]'::jsonb,
    raw_jd TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Trigger for jobs updated_at
DROP TRIGGER IF EXISTS set_jobs_updated_at ON public.jobs;
CREATE TRIGGER set_jobs_updated_at
BEFORE UPDATE ON public.jobs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- INDEXES FOR HIGH-PERFORMANCE SEARCH & FILTERING
-- ==============================================================================
-- Candidate lookup & deduplication
CREATE INDEX IF NOT EXISTS idx_candidates_canonical_url ON public.candidates(canonical_url);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON public.candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_domain_relevance ON public.candidates(domain_relevance);
CREATE INDEX IF NOT EXISTS idx_candidates_location_status ON public.candidates(location_compatibility_status);
CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON public.candidates(created_at DESC);

-- GIN indexes for fast JSONB querying (skills, experience, etc.)
CREATE INDEX IF NOT EXISTS idx_candidates_skills_gin ON public.candidates USING GIN (skills jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_candidates_exp_history_gin ON public.candidates USING GIN (experience_history jsonb_path_ops);

-- Evaluation lookups & ranking
CREATE INDEX IF NOT EXISTS idx_evaluations_candidate_id ON public.evaluations(candidate_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_fit_score ON public.evaluations(fit_score DESC);
CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON public.evaluations(created_at DESC);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================
-- Enable RLS on all tables
ALTER TABLE public.candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Default open policies for service_role and authenticated users (adjust as needed for your auth strategy)
DROP POLICY IF EXISTS "Allow full access to candidates for all roles" ON public.candidates;
CREATE POLICY "Allow full access to candidates for all roles"
    ON public.candidates
    FOR ALL
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Allow full access to evaluations for all roles" ON public.evaluations;
CREATE POLICY "Allow full access to evaluations for all roles"
    ON public.evaluations
    FOR ALL
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Allow full access to jobs for all roles" ON public.jobs;
CREATE POLICY "Allow full access to jobs for all roles"
    ON public.jobs
    FOR ALL
    USING (true)
    WITH CHECK (true);

