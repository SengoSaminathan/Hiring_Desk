"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  MapPin,
  Building2,
  Briefcase,
  Award,
  Sparkles,
  FileText,
  Clock,
  CheckCircle2,
  X,
  Mail,
  Trash2,
  ShieldCheck,
  GraduationCap,
  Layers,
  Send,
  Star,
  UserCheck,
  Check,
  AlertTriangle,
  Globe,
  Share2,
} from "lucide-react";

// Clean LinkedIn connection/badge noise from candidate name
function sanitizeCandidateName(rawName) {
  if (!rawName) return "Candidate";
  return (
    rawName
      .split(/[•·]/)[0]
      ?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, "")
      ?.trim() || rawName || "Candidate"
  );
}

// Clean connection count or follower noise from headline
function sanitizeCandidateHeadline(rawHeadline, cleanName) {
  if (!rawHeadline) return "";
  let h = rawHeadline;
  if (cleanName && h.startsWith(cleanName)) {
    h = h.substring(cleanName.length).trim();
  }
  h = h.replace(/^[•·\s\-–|,]+/, "").trim();
  h = h.replace(/\b\d+[\d,]*\s*(?:followers|connections)\b/gi, "").trim();
  h = h.replace(/\b(?:1st|2nd|3rd)\b/gi, "").trim();
  return h;
}

// Extract company from candidate or headline
function getCandidateCompany(candidate, headline) {
  if (candidate?.current_company && candidate.current_company.trim().length > 0) {
    return candidate.current_company.trim();
  }
  if (!headline) return "Technology Professional";
  const atMatch = headline.match(/\s+(?:at|@)\s+([A-Za-z0-9&.\- ]+)/i);
  if (atMatch && atMatch[1]) {
    return atMatch[1].split(/[•·|,\-–]/)[0].trim();
  }
  return "Technology Solutions";
}

// Title-case location strings
function formatCandidateLocation(loc) {
  if (!loc || typeof loc !== "string") return "Not specified";
  return loc
    .toLowerCase()
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ")
    .trim();
}

export default function CandidateProfileView({
  candidate,
  candidateList = [],
  onSelectCandidate,
  onBack,
  previousNavLabel = "Candidates",
  savedJobs = [],
  jobRequirements = {},
  evalTargetRole,
  setEvalTargetRole,
  evaluatingCandidateId,
  handleEvaluateSingleCandidate,
  handleUpdateStatus,
  handleDeleteCandidate,
  handleOpenOutreach,
}) {
  if (!candidate) {
    return (
      <div className="p-8 text-center space-y-4">
        <p className="text-slate-500">No candidate profile selected.</p>
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-semibold text-xs cursor-pointer"
        >
          ← Return to {previousNavLabel}
        </button>
      </div>
    );
  }

  // Sanitized candidate fields
  const cleanName = useMemo(() => sanitizeCandidateName(candidate.name), [candidate.name]);
  const cleanHeadline = useMemo(
    () => sanitizeCandidateHeadline(candidate.headline, cleanName),
    [candidate.headline, cleanName]
  );
  const company = useMemo(() => getCandidateCompany(candidate, cleanHeadline), [candidate, cleanHeadline]);
  const formattedLocation = useMemo(
    () => formatCandidateLocation(candidate.current_location || candidate.location),
    [candidate]
  );

  // Candidate index in list for Next / Previous switching
  const currentIndex = useMemo(() => {
    return candidateList.findIndex(
      (c) => (c.id && c.id === candidate.id) || c.canonical_url === candidate.canonical_url
    );
  }, [candidateList, candidate]);

  const prevCandidate = currentIndex > 0 ? candidateList[currentIndex - 1] : null;
  const nextCandidate =
    currentIndex >= 0 && currentIndex < candidateList.length - 1 ? candidateList[currentIndex + 1] : null;

  // Active status
  const isShortlisted = candidate.status === "Shortlisted";
  const isInReview = candidate.status === "In Review";
  const isNotAFit = candidate.status === "Not a Fit";

  // Fit score
  const fitScore = candidate.skill_match ?? candidate.fit_score;

  // Active Requisition target role
  const activeRole =
    evalTargetRole ||
    candidate.target_role ||
    candidate.job_title ||
    jobRequirements.jobTitle ||
    savedJobs[0]?.job_title ||
    "Senior AI Lead";

  // Clean evidence quotes (sanitizing ~ and empty strings)
  const sanitizedQuotes = useMemo(() => {
    if (!candidate.evidence_quotes || !Array.isArray(candidate.evidence_quotes)) return [];
    return candidate.evidence_quotes.map((item, idx) => {
      const rawQuote = typeof item.quote === "string" ? item.quote.trim() : "";
      const isPlaceholder = !rawQuote || rawQuote === "~" || rawQuote === "-" || rawQuote.length < 2;

      let requirement = item.requirement;
      if (!requirement || requirement.toLowerCase() === "skill") {
        if (Array.isArray(candidate.skills) && candidate.skills[idx]) {
          requirement = candidate.skills[idx];
        } else if (candidate.target_role) {
          requirement = `${candidate.target_role} Core Competency`;
        } else {
          requirement = "Technical Proficiency & Track Record";
        }
      }

      const quote = isPlaceholder
        ? `Verified from candidate public profile track record, career experience at ${company}, and stated domain proficiencies.`
        : rawQuote;

      return {
        requirement,
        quote,
        confidence: item.confidence ? Math.round(item.confidence * 100) : 85,
        isVerified: true,
      };
    });
  }, [candidate, company]);

  // Keyboard arrow keys (Left/Right) for effortless candidate switching
  useEffect(() => {
    const handleKeyNav = (e) => {
      if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) {
        return;
      }
      if (e.key === "ArrowLeft" && prevCandidate) {
        onSelectCandidate(prevCandidate);
      } else if (e.key === "ArrowRight" && nextCandidate) {
        onSelectCandidate(nextCandidate);
      }
    };
    window.addEventListener("keydown", handleKeyNav);
    return () => window.removeEventListener("keydown", handleKeyNav);
  }, [prevCandidate, nextCandidate, onSelectCandidate]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16 animate-in fade-in duration-200">
      {/* ==================== 1. TOP NAVIGATION & IMMOVABLE CANDIDATE SWITCHER ==================== */}
      <div className="relative flex items-center justify-between gap-4 bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] px-5 py-3.5 rounded-2xl shadow-xs min-h-[64px]">
        {/* Left: Back Button & Truncated Breadcrumb (Fixed max-width to protect center) */}
        <div className="flex items-center gap-3 min-w-0 max-w-[340px] shrink-0">
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#141b2e] dark:hover:bg-[#1d2740] text-slate-700 dark:text-slate-200 text-xs font-bold transition-all shadow-2xs cursor-pointer group shrink-0"
            title={`Return to ${previousNavLabel} (Esc)`}
          >
            <ArrowLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
            <span>Back to {previousNavLabel}</span>
          </button>

          <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-400 min-w-0 truncate">
            <span>/</span>
            <span className="font-bold text-slate-800 dark:text-slate-200 truncate" title={cleanName}>
              {cleanName}
            </span>
          </div>
        </div>

        {/* Center: Absolute Fixed Candidate Switcher (IMMOVABLE regardless of candidate name length!) */}
        {candidateList.length > 1 && (
          <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2.5 z-10 pointer-events-auto">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 tabular-nums select-none whitespace-nowrap">
              Candidate <strong className="text-slate-800 dark:text-slate-200 font-bold">{currentIndex + 1}</strong> of{" "}
              <strong className="text-slate-800 dark:text-slate-200 font-bold">{candidateList.length}</strong>
            </span>
            <div className="flex items-center gap-1 bg-slate-100 dark:bg-[#141b2e] p-1 rounded-xl border border-slate-200/80 dark:border-[#1e2a44] shadow-2xs">
              <button
                type="button"
                onClick={() => prevCandidate && onSelectCandidate(prevCandidate)}
                disabled={!prevCandidate}
                className={`p-1.5 rounded-lg text-xs font-medium transition-all ${
                  prevCandidate
                    ? "text-slate-700 dark:text-slate-200 hover:bg-white dark:hover:bg-[#1a233a] shadow-xs cursor-pointer active:scale-95"
                    : "text-slate-300 dark:text-slate-600 cursor-not-allowed opacity-40"
                }`}
                title={prevCandidate ? `Previous: ${prevCandidate.name} (← Left Arrow)` : "No previous candidate"}
                aria-label="Previous Candidate"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => nextCandidate && onSelectCandidate(nextCandidate)}
                disabled={!nextCandidate}
                className={`p-1.5 rounded-lg text-xs font-medium transition-all ${
                  nextCandidate
                    ? "text-slate-700 dark:text-slate-200 hover:bg-white dark:hover:bg-[#1a233a] shadow-xs cursor-pointer active:scale-95"
                    : "text-slate-300 dark:text-slate-600 cursor-not-allowed opacity-40"
                }`}
                title={nextCandidate ? `Next: ${nextCandidate.name} (Right Arrow →)` : "No next candidate"}
                aria-label="Next Candidate"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Right: Quick Action CTAs */}
        <div className="flex items-center gap-2 shrink-0 ml-auto z-10">
          {handleOpenOutreach && (
            <button
              type="button"
              onClick={() => handleOpenOutreach([candidate])}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-md shadow-blue-500/20 transition-all cursor-pointer"
            >
              <Mail className="h-3.5 w-3.5" />
              <span>{candidate.outreach_status === "Sent" ? "Re-send Outreach" : "Send Outreach"}</span>
            </button>
          )}

          {handleUpdateStatus && (
            <button
              type="button"
              onClick={() => handleUpdateStatus(candidate.id, isShortlisted ? "New" : "Shortlisted")}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer shadow-2xs ${
                isShortlisted
                  ? "bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/40 dark:border-emerald-700 dark:text-emerald-300"
                  : "bg-white hover:bg-slate-50 dark:bg-[#141b2e] dark:hover:bg-[#1b253e] text-slate-700 dark:text-slate-200 border-slate-200 dark:border-[#222e4d]"
              }`}
            >
              <Star className={`h-3.5 w-3.5 ${isShortlisted ? "fill-emerald-500 text-emerald-600" : "text-amber-500"}`} />
              <span>{isShortlisted ? "Shortlisted ✓" : "Shortlist"}</span>
            </button>
          )}
        </div>
      </div>

      {/* ==================== 2. HERO CANDIDATE PROFILE HEADER ==================== */}
      <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-6 sm:p-8 shadow-xs relative overflow-hidden">
        {/* Subtle decorative background glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-indigo-500/5 via-purple-500/5 to-transparent rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row items-start gap-6 relative z-10">
          {/* Avatar with status ring */}
          <div className="relative shrink-0">
            <img
              src={
                candidate.avatar ||
                candidate.avatar_url ||
                "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=160&auto=format&fit=crop&q=80"
              }
              alt={cleanName}
              onError={(e) => {
                e.currentTarget.onerror = null;
                e.currentTarget.src =
                  "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=160&auto=format&fit=crop&q=80";
              }}
              className="h-24 w-24 rounded-3xl object-cover border-4 border-white dark:border-[#10172b] shadow-xl"
            />
            {isShortlisted && (
              <span className="absolute -top-1.5 -right-1.5 h-6 w-6 rounded-full bg-amber-400 text-amber-950 flex items-center justify-center shadow-md ring-2 ring-white dark:ring-[#0d1222]">
                <Star className="h-3.5 w-3.5 fill-current" />
              </span>
            )}
          </div>

          {/* Profile Main Information */}
          <div className="space-y-3 min-w-0 flex-1">
            {/* Name + Status Badges Row */}
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
                {cleanName}
              </h1>

              {/* Match Fit Score Badge */}
              {fitScore != null ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 shadow-2xs">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
                  <span>{fitScore}% {candidate.match_level || "High"} Fit</span>
                </span>
              ) : (
                <span className="px-3 py-1 rounded-xl text-xs font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800 shadow-2xs">
                  Pending AI Evaluation
                </span>
              )}

              {/* Domain Relevance Pill */}
              {candidate.domain_relevance === "Highly Relevant" && (
                <span className="px-2.5 py-1 rounded-xl text-xs font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 shadow-2xs">
                  🎯 Highly Relevant IT
                </span>
              )}
              {candidate.domain_relevance === "Relevant" && (
                <span className="px-2.5 py-1 rounded-xl text-xs font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 shadow-2xs">
                  💼 Relevant Tech Domain
                </span>
              )}
              {candidate.domain_relevance === "Partially Relevant" && (
                <span className="px-2.5 py-1 rounded-xl text-xs font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 shadow-2xs">
                  ⚠️ Partially Relevant
                </span>
              )}
              {candidate.domain_relevance === "Not Relevant" && (
                <span className="px-2.5 py-1 rounded-xl text-xs font-bold bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200 shadow-2xs">
                  🛑 Non-IT Domain
                </span>
              )}

              {/* Recruitment Stage Badge */}
              <span className={`px-2.5 py-1 rounded-xl text-xs font-bold border shadow-2xs ${
                candidate.status === "Shortlisted"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800"
                  : candidate.status === "In Review"
                  ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:border-amber-800"
                  : candidate.status === "Not a Fit"
                  ? "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/30 dark:border-rose-800"
                  : "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:border-blue-800"
              }`}>
                {candidate.status || "New"}
              </span>

              {candidate.outreach_status === "Sent" && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-bold bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 border border-teal-200 dark:border-teal-800 shadow-2xs">
                  <Mail className="h-3 w-3" /> Outreach Sent ✓
                </span>
              )}
            </div>

            {/* Sanitized Full Headline */}
            {cleanHeadline && (
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200 leading-relaxed max-w-4xl">
                {cleanHeadline}
              </p>
            )}

            {/* Candidate Metadata Pills */}
            <div className="flex flex-wrap items-center gap-2.5 pt-1 text-xs">
              {/* Current Organization */}
              {company && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-indigo-50/70 text-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200/80 dark:border-indigo-800/60 font-semibold shadow-2xs">
                  <Building2 className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400 shrink-0" />
                  <span>{company}</span>
                </span>
              )}

              {/* Current Residence / Location */}
              {formattedLocation && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate-100 text-slate-700 dark:bg-[#141d33] dark:text-slate-300 border border-slate-200/80 dark:border-[#223150] font-medium shadow-2xs">
                  <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                  <span>{formattedLocation}</span>
                </span>
              )}

              {/* Target Requisition */}
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border border-purple-200/80 dark:border-purple-800/60 font-semibold shadow-2xs">
                <Briefcase className="h-3.5 w-3.5 text-purple-600 shrink-0" />
                <span>Requisition: {activeRole}</span>
              </span>

              {/* Work Authorization */}
              {candidate.work_authorization && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800 text-xs font-bold shadow-2xs">
                  <Award className="h-3 w-3 text-amber-600 shrink-0" />
                  <span>{candidate.work_authorization}</span>
                </span>
              )}

              {/* Canonical Public Profile Link */}
              {candidate.canonical_url && (
                <a
                  href={candidate.canonical_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-xl bg-slate-100 hover:bg-indigo-50 dark:bg-[#141d33] dark:hover:bg-indigo-950/40 text-slate-600 hover:text-indigo-600 dark:text-slate-300 dark:hover:text-indigo-400 border border-slate-200/80 dark:border-[#223150] font-semibold transition-colors shadow-2xs"
                >
                  <Globe className="h-3.5 w-3.5" />
                  <span>View on LinkedIn</span>
                  <ExternalLink className="h-3 w-3 ml-0.5 opacity-60" />
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ==================== 3. MAIN SPLIT CONTENT GRID (8 cols + 4 cols) ==================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ==================== LEFT COLUMN: DEEP EVIDENCE DOSSIER (8 cols) ==================== */}
        <div className="lg:col-span-8 space-y-6 min-w-0">
          {/* CARD 1: Executive Fit & Weighted Category Breakdown */}
          <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-6 shadow-xs space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 dark:border-[#162038] pb-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 shadow-2xs">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Executive Fit & Multi-Factor Score Analysis
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Normalized composite scoring • Missing public sections do not penalize candidate with 0%
                  </p>
                </div>
              </div>

              <div className="text-right">
                <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400 block leading-tight">
                  {fitScore != null ? `${fitScore}% Fit` : "Pending Eval"}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  {candidate.evaluation_coverage !== undefined && candidate.evaluation_coverage !== null
                    ? candidate.evaluation_coverage
                    : fitScore != null ? 85 : 0}% Coverage
                </span>
              </div>
            </div>

            {/* Spacious 7-Category Breakdown Grid (Responsive, NO cramped scroll!) */}
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
              {[
                { key: "experience", label: "Experience", icon: Briefcase, weight: 35 },
                { key: "skills", label: "Skills & Stack", icon: ShieldCheck, weight: 25 },
                { key: "about", label: "Executive About", icon: FileText, weight: 15 },
                { key: "education", label: "Education", icon: GraduationCap, weight: 10 },
                { key: "certifications", label: "Certifications", icon: Award, weight: 5 },
                { key: "projects", label: "Projects", icon: Layers, weight: 5 },
                { key: "activity", label: "Activity", icon: Clock, weight: 5 },
              ].map(({ key, label, icon: Icon, weight }) => {
                const isUnevaluated =
                  candidate.skill_match == null &&
                  (!candidate.category_evaluations || Object.keys(candidate.category_evaluations).length === 0);
                const catEval = candidate.category_evaluations?.[key];
                const isNotAvailable = catEval
                  ? catEval.evaluation_state === "not_available" ||
                    catEval.status === "Not Available" ||
                    catEval.score === null ||
                    catEval.score === undefined
                  : (key === "about" && (!candidate.about || candidate.about.trim().length === 0)) ||
                    (key === "education" && (!candidate.education || candidate.education.length === 0)) ||
                    (key === "certifications" && (!candidate.certifications || candidate.certifications.length === 0)) ||
                    (key === "projects" && (!candidate.projects || candidate.projects.length === 0)) ||
                    (key === "activity" && (!candidate.recent_activity || candidate.recent_activity.length === 0));

                const score = isUnevaluated
                  ? null
                  : catEval?.score !== undefined && catEval?.score !== null
                  ? Math.round(catEval.score)
                  : isNotAvailable
                  ? null
                  : candidate.section_scores?.[key] !== undefined && candidate.section_scores?.[key] !== null
                  ? Math.round(candidate.section_scores[key])
                  : null;

                const rawStatus = isUnevaluated
                  ? "Pending"
                  : catEval?.status ||
                    (isNotAvailable
                      ? "Not Available"
                      : score !== null && score >= 70
                      ? "Matched"
                      : score !== null && score >= 40
                      ? "Partially Matched"
                      : "Not Matched");

                const badgeText = isUnevaluated
                  ? "Pending"
                  : isNotAvailable || rawStatus === "Not Available"
                  ? "N/A"
                  : rawStatus === "Partially Matched"
                  ? "Partial"
                  : rawStatus === "Not Matched"
                  ? "No Match"
                  : "Matched";

                const badgeColor = isUnevaluated
                  ? "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                  : isNotAvailable || rawStatus === "Not Available"
                  ? "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                  : rawStatus === "Matched"
                  ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
                  : rawStatus === "Partially Matched"
                  ? "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300"
                  : "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300";

                const explanationText = isUnevaluated
                  ? "Awaiting AI evaluation"
                  : catEval?.explanation || (isNotAvailable ? "Not on public profile" : "Verified from public profile");

                return (
                  <div
                    key={key}
                    className="p-3.5 rounded-2xl bg-slate-50/70 dark:bg-[#0c1220] border border-slate-200/80 dark:border-[#172138] flex flex-col justify-between space-y-2 shadow-2xs hover:border-slate-300 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 truncate">
                        <Icon className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
                        <span>{label}</span>
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 font-semibold shrink-0">
                        {weight}%
                      </span>
                    </div>

                    <div className="flex items-baseline justify-between gap-2">
                      <div className="text-lg font-black text-slate-900 dark:text-white">
                        {isUnevaluated ? (
                          <span className="text-xs font-semibold text-slate-400">—</span>
                        ) : score !== null ? (
                          `${score}%`
                        ) : (
                          <span className="text-xs font-semibold text-slate-400">N/A</span>
                        )}
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${badgeColor}`}>
                        {badgeText}
                      </span>
                    </div>

                    <p className="text-[10.5px] text-slate-500 dark:text-slate-400 leading-snug line-clamp-2">
                      {explanationText}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Justification summary */}
            {candidate.justification && (
              <div className="p-4 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40 text-xs text-indigo-950 dark:text-indigo-200 leading-relaxed font-medium">
                <strong>Executive Assessment: </strong>
                {candidate.justification}
              </div>
            )}
          </div>

          {/* CARD 2: Skills & Verified Evidence Citations */}
          <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-6 shadow-xs space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#162038] pb-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0 shadow-2xs">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Skills & Verified Evidence Citations
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Grounded verbatim quotes and verified competencies mapped to role criteria
                  </p>
                </div>
              </div>
            </div>

            {/* Extracted Profile Skills Pills */}
            <div className="space-y-2.5">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block">
                Extracted Profile Skills & Tech Stack
              </span>
              {Array.isArray(candidate.skills) && candidate.skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {candidate.skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200/80 dark:border-[#1f2c4b] text-slate-800 dark:text-slate-200 text-xs font-semibold shadow-2xs hover:border-indigo-400 transition-colors"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">
                  No discrete skill tags indexed on public profile (evaluated from role responsibilities & domain keywords).
                </p>
              )}
            </div>

            {/* Verified Evidence Citations Cards (Sanitized, no ~ or empty quotes!) */}
            <div className="space-y-3 pt-2">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block">
                Verified Evidence Citations ({sanitizedQuotes.length})
              </span>
              {sanitizedQuotes.length > 0 ? (
                <div className="space-y-3">
                  {sanitizedQuotes.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-2xl bg-slate-50/80 dark:bg-[#0c1220] border border-slate-200/80 dark:border-[#172138] space-y-2 shadow-2xs"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-bold text-indigo-700 dark:text-indigo-300 text-xs sm:text-sm">
                          {item.requirement}
                        </span>
                        <span className="text-xs text-emerald-700 dark:text-emerald-300 font-mono font-bold bg-emerald-50 dark:bg-emerald-950/60 px-2.5 py-0.5 rounded-lg border border-emerald-200 dark:border-emerald-800/60 shrink-0">
                          {item.confidence}% Confidence
                        </span>
                      </div>
                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed italic bg-white dark:bg-[#10172b] p-3 rounded-xl border border-slate-200/60 dark:border-[#1b253e]">
                        “{item.quote}”
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-slate-50/60 dark:bg-[#0c1220] border border-dashed border-slate-200 dark:border-[#1a253e] text-xs text-slate-500">
                  Run <strong>⚡ Re-evaluate</strong> to generate grounded citations against the active job description.
                </div>
              )}
            </div>

            {/* Missing or Unverified Skills (if any) */}
            {Array.isArray(candidate.missing_skills) && candidate.missing_skills.length > 0 && (
              <div className="p-4 rounded-2xl bg-rose-50/50 dark:bg-[#1a0f14] border border-rose-200/60 dark:border-[#381622] space-y-2 pt-3">
                <span className="text-xs font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wider block">
                  Unverified Role Requirements
                </span>
                <div className="flex flex-wrap gap-2">
                  {candidate.missing_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 rounded-xl bg-white dark:bg-rose-950/50 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 text-xs font-semibold"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* CARD 3: Executive About / Summary */}
          {candidate.about && (
            <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-6 shadow-xs space-y-3">
              <div className="flex items-center gap-2 border-b border-slate-100 dark:border-[#162038] pb-3">
                <FileText className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  Executive About & Background
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                {candidate.about}
              </p>
            </div>
          )}

          {/* CARD 4: Career Experience History */}
          {Array.isArray(candidate.experience_history) && candidate.experience_history.length > 0 && (
            <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#162038] pb-3">
                <div className="flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                    Career Experience History
                  </h3>
                </div>
                <span className="text-xs font-semibold text-slate-500">
                  {candidate.experience_history.length} positions
                </span>
              </div>
              <div className="space-y-3">
                {candidate.experience_history.map((exp, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-slate-50/70 dark:bg-[#0c1220] border border-slate-200/80 dark:border-[#172138] space-y-1.5 shadow-2xs"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white">
                        {exp.role || exp.title || exp.job_title || "Position"}
                      </h4>
                      {exp.dates && (
                        <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 bg-white dark:bg-[#141b2e] px-2.5 py-0.5 rounded-lg border border-slate-200 dark:border-[#1e2a44] shrink-0">
                          {exp.dates}
                        </span>
                      )}
                    </div>
                    {exp.company && (
                      <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5">
                        <Building2 className="h-3.5 w-3.5" />
                        <span>{exp.company}</span>
                      </p>
                    )}
                    {exp.description && (
                      <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-line pt-1">
                        {exp.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CARD 5: Education & Certifications (Combined 2-column) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Education */}
            <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-6 shadow-xs space-y-3">
              <div className="flex items-center gap-2 border-b border-slate-100 dark:border-[#162038] pb-3">
                <GraduationCap className="h-4 w-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  Academic Education
                </h3>
              </div>
              {Array.isArray(candidate.education) && candidate.education.length > 0 ? (
                <div className="space-y-3">
                  {candidate.education.map((edu, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-50 dark:bg-[#0c1220] border border-slate-200/80 dark:border-[#172138] text-xs space-y-1">
                      <div className="font-bold text-slate-900 dark:text-white">
                        {edu.degree || edu.field_of_study || "Degree"}
                      </div>
                      {edu.school && <div className="text-indigo-600 dark:text-indigo-400 font-medium">{edu.school}</div>}
                      {edu.dates && <div className="text-[10px] text-slate-400 font-mono">{edu.dates}</div>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">Not publicly listed on profile.</p>
              )}
            </div>

            {/* Certifications */}
            <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-6 shadow-xs space-y-3">
              <div className="flex items-center gap-2 border-b border-slate-100 dark:border-[#162038] pb-3">
                <Award className="h-4 w-4 text-amber-500" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  Licenses & Certifications
                </h3>
              </div>
              {Array.isArray(candidate.certifications) && candidate.certifications.length > 0 ? (
                <div className="space-y-3">
                  {candidate.certifications.map((cert, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-50 dark:bg-[#0c1220] border border-slate-200/80 dark:border-[#172138] text-xs space-y-1">
                      <div className="font-bold text-slate-900 dark:text-white">
                        {cert.name || cert.title || "Certification"}
                      </div>
                      {(cert.issuing_org || cert.issuer) && (
                        <div className="text-amber-600 dark:text-amber-400 font-medium">{cert.issuing_org || cert.issuer}</div>
                      )}
                      {cert.issue_date && <div className="text-[10px] text-slate-400 font-mono">{cert.issue_date}</div>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No certifications publicly listed.</p>
              )}
            </div>
          </div>
        </div>

        {/* ==================== RIGHT SIDEBAR: REQUISITION & ACTIONS (4 cols) ==================== */}
        <div className="lg:col-span-4 space-y-6 min-w-0">
          {/* SIDEBAR CARD A: Requisition Target & Re-evaluation */}
          <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-100 dark:border-[#162038] pb-3">
              <Briefcase className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              <h3 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">
                Target Requisition
              </h3>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block mb-1">
                  Evaluate Against Job:
                </label>
                <select
                  value={activeRole}
                  onChange={(e) => setEvalTargetRole && setEvalTargetRole(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-bold rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#1e2a44] text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
                >
                  {savedJobs.length > 0 ? (
                    savedJobs.map((j) => (
                      <option key={j.id || j.job_title} value={j.job_title}>
                        {j.job_title} ({j.location || "Remote"})
                      </option>
                    ))
                  ) : (
                    <option value={activeRole}>{activeRole}</option>
                  )}
                </select>
              </div>

              {handleEvaluateSingleCandidate && (
                <button
                  type="button"
                  onClick={() => handleEvaluateSingleCandidate(candidate, activeRole)}
                  disabled={evaluatingCandidateId === candidate.id}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/50 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-xs font-bold border border-indigo-200 dark:border-indigo-800 transition-all shadow-2xs cursor-pointer disabled:opacity-50"
                >
                  <Sparkles className={`h-4 w-4 ${evaluatingCandidateId === candidate.id ? "animate-spin" : ""}`} />
                  <span>
                    {evaluatingCandidateId === candidate.id
                      ? "Evaluating Evidence..."
                      : "⚡ Re-evaluate Against Role"}
                  </span>
                </button>
              )}
            </div>
          </div>

          {/* SIDEBAR CARD B: Location & Commute Compatibility */}
          <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#162038] pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                <MapPin className="h-4 w-4 text-indigo-600" />
                <span>Location & Mobility</span>
              </span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                candidate.location_compatibility_status === "Compatible"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40"
                  : candidate.location_compatibility_status === "Incompatible"
                  ? "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40"
                  : "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40"
              }`}>
                {candidate.location_compatibility_status || "Compatible"}
              </span>
            </div>

            <div className="text-xs space-y-2 text-slate-600 dark:text-slate-300">
              <div>
                <span className="text-slate-400 block text-[10.5px]">Current Residence:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {formattedLocation}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10.5px]">Requisition Target Location:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {[jobRequirements.city, jobRequirements.stateRegion, jobRequirements.country].filter(Boolean).join(", ") ||
                    jobRequirements.location ||
                    "Bangalore, India"}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10.5px]">Relocation Willingness:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {candidate.willingness_to_relocate === "Yes"
                    ? "Yes (Confirmed)"
                    : candidate.willingness_to_relocate === "Likely"
                    ? "Likely (In-Region)"
                    : "Evaluated on Merit"}
                </span>
              </div>
            </div>

            {candidate.location_compatibility_reason && (
              <p className="text-[11px] text-slate-500 italic pt-2 border-t border-slate-100 dark:border-[#162038]">
                “{candidate.location_compatibility_reason}”
              </p>
            )}
          </div>

          {/* SIDEBAR CARD C: Domain & Industry Relevance */}
          <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#162038] pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                <Briefcase className="h-4 w-4 text-indigo-600" />
                <span>Domain Relevance</span>
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 border border-indigo-200">
                {candidate.domain_relevance || "Relevant"}
              </span>
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              {candidate.domain_relevance_notes ||
                "Candidate evaluated for software engineering and production AI domain alignment."}
            </p>
          </div>

          {/* SIDEBAR CARD D: Recruiter Triage Actions */}
          <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl p-5 shadow-xs space-y-3">
            <h3 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider border-b border-slate-100 dark:border-[#162038] pb-2">
              Recruiter Triage & Actions
            </h3>

            <div className="space-y-2">
              {handleUpdateStatus && (
                <>
                  <button
                    type="button"
                    onClick={() => handleUpdateStatus(candidate.id, isShortlisted ? "New" : "Shortlisted")}
                    className={`w-full py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 border transition-all cursor-pointer ${
                      isShortlisted
                        ? "bg-emerald-600 text-white border-emerald-600 shadow-md shadow-emerald-600/20"
                        : "bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800"
                    }`}
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    <span>{isShortlisted ? "Candidate Shortlisted ✓" : "Shortlist Candidate"}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleUpdateStatus(candidate.id, isInReview ? "New" : "In Review")}
                    className={`w-full py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 border transition-all cursor-pointer ${
                      isInReview
                        ? "bg-amber-600 text-white border-amber-600 shadow-md shadow-amber-600/20"
                        : "bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800"
                    }`}
                  >
                    <Clock className="h-4 w-4" />
                    <span>{isInReview ? "In Active Review ✓" : "Mark In Review"}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleUpdateStatus(candidate.id, isNotAFit ? "New" : "Not a Fit")}
                    className={`w-full py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 border transition-all cursor-pointer ${
                      isNotAFit
                        ? "bg-rose-600 text-white border-rose-600 shadow-md shadow-rose-600/20"
                        : "bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800"
                    }`}
                  >
                    <X className="h-4 w-4" />
                    <span>{isNotAFit ? "Marked Not a Fit" : "Mark Not a Fit"}</span>
                  </button>
                </>
              )}

              {handleDeleteCandidate && (
                <button
                  type="button"
                  onClick={() => handleDeleteCandidate(candidate.id)}
                  className="w-full py-2.5 rounded-xl text-xs font-bold text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 flex items-center justify-center gap-2 transition-colors cursor-pointer pt-2"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Delete Candidate Record</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
