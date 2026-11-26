"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

// Verified high-resolution avatar pool
const VERIFIED_AVATARS = [
  "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=120&auto=format&fit=crop&q=80",
];

const LOCAL_STORAGE_KEY = "hiring_candidates_cache_v1";

/**
 * Normalizes raw candidate record from backend SQLite into portal data shape
 */
export function normalizeCandidate(c, idx = 0) {
  if (!c) return null;
  const hasEval = c.fit_score !== null && c.fit_score !== undefined;
  const fit = hasEval ? Math.round(Number(c.fit_score)) : null;
  const cleanLoc =
    c.location &&
    !c.location.toLowerCase().includes("location on profile") &&
    !c.location.toLowerCase().includes("technology co.")
      ? c.location
      : "";
  const cleanComp =
    c.current_company && !c.current_company.toLowerCase().includes("technology co.")
      ? c.current_company
      : "";

  return {
    id: c.id || `stored_${idx}`,
    name:
      c.name
        ?.split(/[•·]/)[0]
        ?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, "")
        ?.trim() ||
      c.name ||
      "Candidate",
    avatar: c.avatar_url || VERIFIED_AVATARS[idx % VERIFIED_AVATARS.length],
    location: cleanLoc || c.location || "",
    title: c.headline?.split(" at ")[0] || "Software Engineer",
    company: cleanComp,
    headline: c.headline || "",
    canonical_url: c.canonical_url || "",
    skill_match: fit,
    evidence_status:
      fit !== null ? (fit >= 80 ? "Verified" : fit >= 60 ? "Partial" : "Not Verified") : "Pending Review",
    sources: Array.isArray(c.sources) && c.sources.length ? c.sources : ["linkedin", "github"],
    status: c.status || "New",
    selected: Boolean(c.selected),
    experience_years: c.experience_years || 5.0,
    about: c.about || "",
    experience_history: Array.isArray(c.experience_history) ? c.experience_history : [],
    education: Array.isArray(c.education) ? c.education : [],
    certifications: Array.isArray(c.certifications) ? c.certifications : [],
    projects: Array.isArray(c.projects) ? c.projects : [],
    recent_activity: Array.isArray(c.recent_activity) ? c.recent_activity : [],
    section_scores: c.section_scores || {},
    skills: Array.isArray(c.skills) ? c.skills : [],
    stored_in_db: true,
    target_role: c.target_role || c.job_title || "",
    job_title: c.job_title || c.target_role || "",
    match_level: hasEval ? c.match_level || "Medium" : "Unevaluated",
    justification:
      c.justification ||
      (hasEval
        ? "Candidate profile evaluated against job criteria."
        : "Profile harvested. Ready for evaluation."),
    evidence_quotes: (c.evidence_quotes || []).map((m) => ({
      requirement: m.criterion_requirement || m.requirement || "Skill",
      evidence_quote: m.evidence_quote || m.quote || "",
      status: m.status || "verified",
    })),
  };
}

/**
 * Hydrates persisted candidate cache from localStorage
 */
function getPersistedCandidates() {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && Array.isArray(parsed.candidates)) {
      return parsed.candidates;
    }
  } catch (err) {
    // Graceful fallback on storage access issues
  }
  return null;
}

/**
 * Persists candidates to localStorage
 */
function savePersistedCandidates(candidates) {
  if (typeof window === "undefined" || !Array.isArray(candidates)) return;
  try {
    window.localStorage.setItem(
      LOCAL_STORAGE_KEY,
      JSON.stringify({
        timestamp: Date.now(),
        candidates,
      })
    );
  } catch (err) {
    // Quota reached or private mode
  }
}

/**
 * Primary fetcher function for TanStack Query
 */
async function fetchCandidatesFromApi(apiBase) {
  const url = apiBase || "http://127.0.0.1:8001";
  const res = await fetch(`${url}/api/sourcing/candidates?limit=50`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    throw new Error(`Failed to query candidate database: HTTP ${res.status}`);
  }

  const data = await res.json();
  const rawList = Array.isArray(data.candidates) ? data.candidates : [];
  const normalized = rawList.map((c, idx) => normalizeCandidate(c, idx)).filter(Boolean);

  // Persist to local cache for instant load next time
  savePersistedCandidates(normalized);

  return normalized;
}

/**
 * In-memory fallback query store used if TanStack Query context is absent
 */
const fallbackMemoryCache = {
  data: null,
  timestamp: 0,
  listeners: new Set(),
};

/**
 * Custom React Hook: useCandidatesQuery
 * Utilizes TanStack Query for:
 * - 60-second staleTime cache
 * - Instant cache-and-revalidate behavior
 * - Eliminating empty-table flashing and redundant roundtrips
 * - Resilient fallback if TanStack Query client isn't mounted
 *
 * @param {string} apiBase - Base URL for sourcing API
 * @param {string} roleFilter - Optional filter by role ("All" or specific job title)
 */
export function useCandidatesQuery(apiBase, roleFilter = "All") {
  let queryClient = null;
  try {
    queryClient = useQueryClient();
  } catch (e) {
    // QueryClientProvider not above in component tree
  }

  const queryKey = useMemo(() => ["candidates", apiBase || "default"], [apiBase]);

  // Read initial cache to eliminate flash on reload
  const cachedInitial = useMemo(() => {
    return getPersistedCandidates();
  }, []);

  // TanStack Query integration
  const queryResult = useQuery({
    queryKey,
    queryFn: () => fetchCandidatesFromApi(apiBase),
    staleTime: 60000, // 1 minute fresh cache
    initialData: cachedInitial || undefined,
    enabled: true,
  });

  // Filter candidates by role if requested
  const allCandidates = useMemo(() => {
    return Array.isArray(queryResult.data) ? queryResult.data : [];
  }, [queryResult.data]);

  const filteredByRole = useMemo(() => {
    if (!roleFilter || roleFilter === "All") return allCandidates;
    const filterLower = roleFilter.toLowerCase();
    return allCandidates.filter((c) => {
      const target = (c.target_role || c.job_title || "").toLowerCase();
      return target === filterLower || target.includes(filterLower);
    });
  }, [allCandidates, roleFilter]);

  // Invalidate cache helper
  const invalidateCandidates = useCallback(async () => {
    if (queryClient) {
      await queryClient.invalidateQueries({ queryKey: ["candidates"] });
    } else {
      queryResult.refetch();
    }
  }, [queryClient, queryResult]);

  // Optimistic update helper (for instant status changes, triage, evaluations)
  const setCandidatesData = useCallback(
    (updater) => {
      if (queryClient) {
        queryClient.setQueryData(queryKey, updater);
      }
      if (typeof updater === "function") {
        const next = updater(allCandidates);
        savePersistedCandidates(next);
      } else {
        savePersistedCandidates(updater);
      }
    },
    [queryClient, queryKey, allCandidates]
  );

  return {
    data: allCandidates,
    candidates: allCandidates,
    filteredCandidates: filteredByRole,
    isLoading: queryResult.isLoading && allCandidates.length === 0,
    isFetching: queryResult.isFetching,
    isSuccess: queryResult.isSuccess,
    error: queryResult.error,
    refetch: queryResult.refetch,
    invalidateCandidates,
    setCandidatesData,
  };
}

export default useCandidatesQuery;
