"use client";

import React, { useState, useMemo, useRef, useEffect, useCallback } from "react";
import {
  Users,
  UserCheck,
  Search,
  Filter,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  Send,
  SendHorizontal,
  Star,
  CheckCircle2,
  Clock,
  MapPin,
  Briefcase,
  Building2,
  ChevronRight,
  RotateCw,
  CheckSquare,
  Square,
  Trash2,
  Cloud,
  Eye,
  Mail,
  Award,
  ArrowRight,
  Download,
  LayoutGrid,
  Table as TableIcon,
  X,
  FileText,
  Check,
} from "lucide-react";

// Inline SVG Icons for LinkedIn and GitHub sources
function LinkedInIcon({ className = "h-3 w-3" }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 8.76a1.62 1.62 0 1 0 0-3.24 1.62 1.62 0 0 0 0 3.24m1.39 9.74v-8.37H5.07v8.37h2.78Z" />
    </svg>
  );
}

function GithubIcon({ className = "h-3 w-3" }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2Z" />
    </svg>
  );
}

export default function CandidateReviewView({
  candidateList = [],
  selectedCandidate,
  setSelectedCandidate,
  handleEvaluateSingleCandidate,
  handleEvaluateAllCandidates,
  evaluatingCandidateId,
  batchEvaluating,
  handleUpdateStatus,
  handleOpenOutreach,
  handleDeleteCandidate,
  handleClearAllCandidates,
  handleSyncSupabase,
  syncingSupabase,
  handleOpenWizard,
  toggleSelectCandidate,
  toggleSelectAll,
  selectAll,
  availableRoles = [],
  jobRequirements = {},
  savedJobs = [],
  setEvalTargetRole,
  setActiveNav,
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all"); // "all" | "new" | "in_review" | "shortlisted" | "not_a_fit" | "contacted"
  const [roleFilter, setRoleFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all"); // "all" | "high" (>=80) | "strong" (60-79) | "pending"
  const [viewMode, setViewMode] = useState("table"); // "table" | "cards"

  // Horizontal mouse wheel scrolling for the candidate table container (Callback Ref for guaranteed first-time attachment)
  const tableContainerDomRef = useRef(null);

  const handleTableWheel = useCallback((e) => {
    const container = tableContainerDomRef.current;
    if (!container) return;

    const maxScrollLeft = container.scrollWidth - container.clientWidth;
    if (maxScrollLeft <= 0) return;

    // Detect vertical mouse wheel movement
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      // Normalize delta across Windows line mode (deltaMode = 1) and pixel mode (deltaMode = 0)
      let delta = e.deltaY;
      if (e.deltaMode === 1) {
        delta *= 40; // 40px per line on Windows mouse wheel
      } else if (e.deltaMode === 2) {
        delta *= container.clientWidth * 0.8;
      }
      // Guarantee responsive, immediate visible movement on the very first notch
      if (Math.abs(delta) < 40 && delta !== 0) {
        delta = Math.sign(delta) * 50;
      }

      const isDown = delta > 0;
      const isUp = delta < 0;

      const canScrollRight = isDown && container.scrollLeft < maxScrollLeft - 1;
      const canScrollLeft = isUp && container.scrollLeft > 1;

      if (canScrollRight || canScrollLeft) {
        e.preventDefault();
        container.scrollLeft += delta;
      }
    }
  }, []);

  const setTableScrollRef = useCallback((node) => {
    if (tableContainerDomRef.current) {
      tableContainerDomRef.current.removeEventListener("wheel", handleTableWheel);
    }
    tableContainerDomRef.current = node;
    if (node) {
      node.addEventListener("wheel", handleTableWheel, { passive: false });
    }
  }, [handleTableWheel]);

  // Aggregate count statistics
  const totalCount = candidateList.length;
  const newCount = candidateList.filter((c) => c.status === "New" || !c.status).length;
  const inReviewCount = candidateList.filter((c) => c.status === "In Review").length;
  const shortlistedCount = candidateList.filter((c) => c.status === "Shortlisted").length;
  const notAFitCount = candidateList.filter((c) => c.status === "Not a Fit").length;
  const contactedCount = candidateList.filter((c) => c.outreach_status === "Sent").length;
  const highFitCount = candidateList.filter((c) => (c.skill_match ?? c.fit_score ?? 0) >= 80).length;

  // Filter candidates
  const filteredCandidates = useMemo(() => {
    return (candidateList || []).filter((c) => {
      // 1. Status Filter
      if (statusFilter === "new" && c.status !== "New" && c.status) return false;
      if (statusFilter === "in_review" && c.status !== "In Review") return false;
      if (statusFilter === "shortlisted" && c.status !== "Shortlisted") return false;
      if (statusFilter === "not_a_fit" && c.status !== "Not a Fit") return false;
      if (statusFilter === "contacted" && c.outreach_status !== "Sent") return false;

      // 2. Role Filter
      if (roleFilter !== "all" && c.target_role !== roleFilter) return false;

      // 3. Score Filter
      const score = c.skill_match ?? c.fit_score;
      if (scoreFilter === "high" && (score === null || score === undefined || score < 80)) return false;
      if (scoreFilter === "strong" && (score === null || score === undefined || score < 60 || score >= 80)) return false;
      if (scoreFilter === "pending" && score !== null && score !== undefined) return false;

      // 4. Search Query Filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const rawSkills = Array.isArray(c.skills)
          ? c.skills
          : typeof c.skills === "string" && c.skills.startsWith("[")
          ? (() => {
              try {
                return JSON.parse(c.skills);
              } catch {
                return [];
              }
            })()
          : [];

        const matchesName = c.name?.toLowerCase().includes(query);
        const matchesTitle = (c.title || c.headline)?.toLowerCase().includes(query);
        const matchesCompany = c.company?.toLowerCase().includes(query);
        const matchesLocation = c.location?.toLowerCase().includes(query);
        const matchesTarget = c.target_role?.toLowerCase().includes(query);
        const matchesAuth = c.work_authorization?.toLowerCase().includes(query);
        const matchesSkills = rawSkills.some((s) => s.toLowerCase().includes(query));

        if (
          !matchesName &&
          !matchesTitle &&
          !matchesCompany &&
          !matchesLocation &&
          !matchesTarget &&
          !matchesAuth &&
          !matchesSkills
        ) {
          return false;
        }
      }

      return true;
    });
  }, [candidateList, statusFilter, roleFilter, scoreFilter, searchQuery]);

  // Selected candidates for batch operations
  const selectedCandidates = useMemo(() => {
    return candidateList.filter((c) => c.selected);
  }, [candidateList]);

  // Client-side 1-click CSV export
  const handleExportCSV = () => {
    if (!candidateList || candidateList.length === 0) return;
    const headers = [
      "Name",
      "Title",
      "Company",
      "Location",
      "Work Authorization",
      "Target Role",
      "Fit Score",
      "Evidence Status",
      "Status",
      "Outreach Status",
      "Profile URL",
    ];
    const rows = candidateList.map((c) => [
      `"${(c.name || "").replace(/"/g, '""')}"`,
      `"${(c.title || c.headline || "").replace(/"/g, '""')}"`,
      `"${(c.company || "").replace(/"/g, '""')}"`,
      `"${(c.location || "").replace(/"/g, '""')}"`,
      `"${(c.work_authorization || "").replace(/"/g, '""')}"`,
      `"${(c.target_role || "").replace(/"/g, '""')}"`,
      c.skill_match ?? c.fit_score ?? "Pending",
      `"${c.evidence_status || "Pending"}"`,
      `"${c.status || "New"}"`,
      `"${c.outreach_status || "Unsent"}"`,
      `"${c.canonical_url || c.profile_url || ""}"`,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Hiring_Desk_Candidates_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* 1. Executive Top Header Banner */}
      <div className="p-6 sm:p-7 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex flex-col xl:flex-row xl:items-center justify-between gap-5">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              <Users className="h-3.5 w-3.5" />
              Candidate Directory & Review Center
            </span>
            <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
              ● Local-First SQLite Persisted
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
            Candidate Repository & Evidence Review
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-3xl leading-relaxed">
            Full candidate roster across all target requisitions: inspect grounded citations, review deterministic match scores, manage pipeline qualifications, and dispatch calibrated outreach.
          </p>

          {/* KPI Stat Badges */}
          <div className="flex flex-wrap items-center gap-2.5 mt-4 text-xs font-bold">
            <div className="px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#1e2a4a] text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <Users className="h-3.5 w-3.5 text-indigo-500" />
              <span>{totalCount} Total Candidates</span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-emerald-500" />
              <span>{highFitCount} High Match (≥80%)</span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 flex items-center gap-2">
              <Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500" />
              <span>{shortlistedCount} Shortlisted</span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 flex items-center gap-2">
              <Mail className="h-3.5 w-3.5 text-teal-500" />
              <span>{contactedCount} Outreach Sent</span>
            </div>
          </div>
        </div>

        {/* Header Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <button
            onClick={handleEvaluateAllCandidates}
            disabled={batchEvaluating || candidateList.length === 0}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
          >
            <Sparkles className={`h-4 w-4 ${batchEvaluating ? "animate-spin" : ""}`} />
            <span>{batchEvaluating ? "Evaluating All..." : "⚡ Evaluate All with AI"}</span>
          </button>

          {handleSyncSupabase && (
            <button
              onClick={handleSyncSupabase}
              disabled={syncingSupabase || candidateList.length === 0}
              className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-xs font-semibold text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 transition-colors disabled:opacity-50 cursor-pointer"
              title="Sync candidates and evaluations to Supabase PostgreSQL database"
            >
              <Cloud className={`h-4 w-4 text-emerald-600 dark:text-emerald-400 ${syncingSupabase ? "animate-bounce" : ""}`} />
              <span>{syncingSupabase ? "Syncing..." : "☁️ Sync Cloud"}</span>
            </button>
          )}

          <button
            onClick={handleExportCSV}
            disabled={candidateList.length === 0}
            className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b] text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-slate-900 hover:border-slate-400 transition-colors disabled:opacity-50 cursor-pointer"
            title="Download candidates list as CSV"
          >
            <Download className="h-4 w-4 text-slate-500" />
            <span>Export CSV</span>
          </button>

          {handleOpenWizard && (
            <button
              onClick={() => handleOpenWizard(1)}
              className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b] text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-slate-900 hover:border-slate-400 transition-colors cursor-pointer"
              title="Launch candidate sourcing wizard"
            >
              <Filter className="h-4 w-4 text-slate-500" />
              <span>Sourcing Wizard</span>
            </button>
          )}
        </div>
      </div>

      {/* 2. Control Toolbar: Filter Tabs, Requisition Selector, Search, View Toggle */}
      <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3.5">
        {/* Tier 1: Status Filter Tabs (Left) + View Switcher & Search (Right) */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-0.5">
            {[
              { id: "all", label: "All Candidates", count: totalCount },
              { id: "new", label: "New", count: newCount },
              { id: "in_review", label: "In Review", count: inReviewCount },
              { id: "shortlisted", label: "Shortlisted", count: shortlistedCount },
              { id: "not_a_fit", label: "Not a Fit", count: notAFitCount },
              { id: "contacted", label: "Outreach Sent", count: contactedCount },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap shrink-0 transition-all flex items-center gap-1.5 cursor-pointer ${
                  statusFilter === tab.id
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-[#131b31]"
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    statusFilter === tab.id
                      ? "bg-indigo-700 text-indigo-100"
                      : "bg-slate-200/70 dark:bg-[#1a2542] text-slate-600 dark:text-slate-400"
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          {/* Right: View Mode Toggle (Table / Cards) */}
          <div className="flex items-center gap-2 shrink-0 self-end lg:self-auto">
            <div className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-[#12182c] border border-slate-200 dark:border-[#1e2a4a]">
              <button
                onClick={() => setViewMode("table")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  viewMode === "table"
                    ? "bg-white dark:bg-[#1b2542] text-indigo-600 dark:text-indigo-400 shadow-xs"
                    : "text-slate-500 hover:text-slate-800 dark:text-slate-400"
                }`}
                title="Full-Width Table View"
              >
                <TableIcon className="h-3.5 w-3.5" />
                <span>Table</span>
              </button>
              <button
                onClick={() => setViewMode("cards")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  viewMode === "cards"
                    ? "bg-white dark:bg-[#1b2542] text-indigo-600 dark:text-indigo-400 shadow-xs"
                    : "text-slate-500 hover:text-slate-800 dark:text-slate-400"
                }`}
                title="Rich Candidate Dossier Cards View"
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                <span>Cards</span>
              </button>
            </div>
          </div>
        </div>

        {/* Tier 2: Search Input, Role Selector, Score Filter */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100 dark:border-[#151e36]">
          {/* Left: Role Filter & Score Filter */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Role Filter */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b]">
              <Briefcase className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
              <span className="text-[11px] font-bold text-slate-400">Requisition:</span>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="bg-transparent text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="all">All Roles ({totalCount})</option>
                {availableRoles.map((r) => (
                  <option key={r.name} value={r.name}>
                    {r.name} ({r.count})
                  </option>
                ))}
              </select>
            </div>

            {/* Score Filter */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b]">
              <Sparkles className="h-3.5 w-3.5 text-amber-500 shrink-0" />
              <span className="text-[11px] font-bold text-slate-400">Match Level:</span>
              <select
                value={scoreFilter}
                onChange={(e) => setScoreFilter(e.target.value)}
                className="bg-transparent text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="all">All Scores</option>
                <option value="high">High Fit (≥80%)</option>
                <option value="strong">Strong Fit (60-79%)</option>
                <option value="pending">Pending Evaluation</option>
              </select>
            </div>

            {/* Mouse wheel scroll hint for table view */}
            {viewMode === "table" && (
              <span className="text-[11px] text-slate-400 dark:text-slate-500 hidden sm:inline-flex items-center gap-1 bg-slate-50 dark:bg-[#12182c] px-2.5 py-1 rounded-xl border border-slate-200/60 dark:border-[#1e2a4a]">
                <span>💡 Scroll mouse wheel on table to slide left / right</span>
              </span>
            )}
          </div>

          {/* Right: Search Input */}
          <div className="relative flex-1 sm:flex-initial sm:w-64">
            <Search className="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search candidate, skill, company..."
              className="w-full bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b] text-xs rounded-xl pl-9 pr-7 py-1.5 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>

        {/* Tier 3: Batch Selection Action Bar (when selected) */}
        {selectedCandidates.length > 0 && (
          <div className="p-2.5 rounded-xl bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 flex flex-wrap items-center justify-between gap-3 animate-in fade-in">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-indigo-700 dark:text-indigo-300">
                {selectedCandidates.length} candidate{selectedCandidates.length === 1 ? "" : "s"} selected
              </span>
              <span className="text-xs text-slate-400">•</span>
              <button
                onClick={() => {
                  selectedCandidates.forEach((c) => handleUpdateStatus(c.id, "Shortlisted"));
                }}
                className="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800 text-xs font-bold hover:bg-amber-100 transition-colors cursor-pointer"
              >
                ⭐ Shortlist Selected
              </button>
              <button
                onClick={() => {
                  selectedCandidates.forEach((c) => handleUpdateStatus(c.id, "In Review"));
                }}
                className="px-2.5 py-1 rounded-lg bg-white dark:bg-[#141d33] text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-[#202c4b] text-xs font-bold hover:bg-slate-50 transition-colors cursor-pointer"
              >
                Move to In Review
              </button>
            </div>

            <button
              onClick={() => handleOpenOutreach(selectedCandidates)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
            >
              <SendHorizontal className="h-3.5 w-3.5" />
              <span>✉️ Send Outreach ({selectedCandidates.length})</span>
            </button>
          </div>
        )}
      </div>

      {/* 3. Main Content: Full-Width Table View OR Dossier Cards View */}
      {filteredCandidates.length === 0 ? (
        <div className="p-16 text-center rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3">
          <div className="h-12 w-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto shadow-xs">
            <Users className="h-6 w-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">No candidates match active criteria</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
            {totalCount === 0
              ? "Run a candidate sourcing session to harvest profiles from public sources into local SQLite storage."
              : "Try relaxing search terms, changing the requisition filter, or clearing the status tabs above."}
          </p>
          {handleOpenWizard && (
            <div className="pt-2">
              <button
                onClick={() => handleOpenWizard(1)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold shadow-md shadow-indigo-600/20 hover:shadow-lg transition-all cursor-pointer"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Launch Sourcing Wizard</span>
              </button>
            </div>
          )}
        </div>
      ) : viewMode === "table" ? (
        /* =================== FULL-WIDTH EXPANSIVE TABLE VIEW =================== */
        <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-3xl shadow-xs overflow-hidden">
          <div ref={setTableScrollRef} className="overflow-x-auto w-full">
            <table className="w-full text-left border-collapse text-xs table-fixed min-w-[1100px]">
              <thead>
                <tr className="border-b border-slate-100 dark:border-[#162038] text-[11px] font-bold text-slate-500 dark:text-slate-400 bg-slate-50/70 dark:bg-[#0c1120]">
                  <th className="py-3.5 px-3 w-10 text-center">
                    <button onClick={toggleSelectAll} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                      {selectAll ? <CheckSquare className="h-3.5 w-3.5 text-indigo-600" /> : <Square className="h-3.5 w-3.5" />}
                    </button>
                  </th>
                  <th className="py-3.5 px-4 w-[280px]">Candidate Profile</th>
                  <th className="py-3.5 px-4 w-[250px]">Current Title & Company</th>
                  <th className="py-3.5 px-4 w-[160px]">Target Requisition</th>
                  <th className="py-3.5 px-4 w-[200px]">Skills & Match</th>
                  <th className="py-3.5 px-4 w-[140px]">Evidence & Sources</th>
                  <th className="py-3.5 px-3 w-[110px]">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-[#151d33]">
                {filteredCandidates.map((candidate, idx) => {
                  const fit = candidate.skill_match ?? candidate.fit_score;
                  const isShortlisted = candidate.status === "Shortlisted";
                  const rawSkills = Array.isArray(candidate.skills)
                    ? candidate.skills
                    : typeof candidate.skills === "string" && candidate.skills.startsWith("[")
                    ? (() => {
                        try {
                          return JSON.parse(candidate.skills);
                        } catch {
                          return [];
                        }
                      })()
                    : [];
                  const topSkills = rawSkills.slice(0, 3);

                  return (
                    <tr
                      key={`${candidate.id || "cand"}_${candidate.canonical_url || candidate.name}_${idx}`}
                      className="hover:bg-slate-50/80 dark:hover:bg-[#12192e]/60 transition-colors group cursor-pointer"
                      onClick={() => {
                        setSelectedCandidate(candidate);
                        if (setEvalTargetRole) {
                          setEvalTargetRole(
                            candidate.target_role ||
                              candidate.job_title ||
                              jobRequirements.jobTitle ||
                              savedJobs[0]?.job_title ||
                              "Senior AI Lead"
                          );
                        }
                      }}
                    >
                      {/* Checkbox */}
                      <td
                        className="py-3.5 px-3 text-center"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (toggleSelectCandidate) toggleSelectCandidate(candidate.id);
                        }}
                      >
                        <button className="text-slate-400 hover:text-indigo-600 cursor-pointer">
                          {candidate.selected ? (
                            <CheckSquare className="h-4 w-4 text-indigo-600" />
                          ) : (
                            <Square className="h-4 w-4" />
                          )}
                        </button>
                      </td>

                      {/* Candidate Avatar & Info */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="flex items-start gap-3">
                          <div className="relative shrink-0 mt-0.5">
                            <img
                              src={
                                candidate.avatar ||
                                candidate.avatar_url ||
                                "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"
                              }
                              alt={candidate.name}
                              onError={(e) => {
                                e.currentTarget.onerror = null;
                                e.currentTarget.src =
                                  "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80";
                              }}
                              className="h-10 w-10 rounded-xl object-cover border border-slate-200 dark:border-[#222e4d] shadow-2xs"
                            />
                            {isShortlisted && (
                              <span className="absolute -top-1 -right-1 h-3.5 w-3.5 bg-amber-400 rounded-full flex items-center justify-center text-[8px] text-white shadow-xs">
                                ★
                              </span>
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="font-bold text-slate-900 dark:text-white text-xs group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors">
                              {candidate.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, "")?.trim() || candidate.name}
                            </div>
                            <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
                              <MapPin className="h-3 w-3 text-slate-400 shrink-0" />
                              <span className="truncate">{candidate.location || "Location not stated"}</span>
                              {candidate.location_compatibility_status === "Compatible" && (
                                <span className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 shrink-0">• Compatible</span>
                              )}
                            </div>
                            {candidate.work_authorization && (
                              <div className="mt-1">
                                <span
                                  title={candidate.work_authorization}
                                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                                >
                                  <Award className="h-2.5 w-2.5 text-amber-600 shrink-0" />
                                  <span className="truncate max-w-[170px]">
                                    {candidate.work_authorization.includes("Golden Visa")
                                      ? "UAE Golden Visa"
                                      : candidate.work_authorization}
                                  </span>
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Current Title & Company */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="space-y-1">
                          <div
                            className="font-semibold text-slate-900 dark:text-white text-xs truncate max-w-[240px]"
                            title={candidate.headline || candidate.title}
                          >
                            {candidate.title || candidate.headline || "Software Engineer"}
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Building2 className="h-3 w-3 text-slate-400 shrink-0" />
                            <span
                              className="text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-[140px]"
                              title={candidate.company}
                            >
                              {candidate.company && candidate.company !== "Current Organization"
                                ? candidate.company
                                : "Technology Professional"}
                            </span>
                            {candidate.domain_relevance === "Highly Relevant" && (
                              <span className="shrink-0 px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                                IT Core
                              </span>
                            )}
                            {candidate.domain_relevance === "Relevant" && (
                              <span className="shrink-0 px-1.5 py-0.2 rounded text-[9px] font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                                Relevant
                              </span>
                            )}
                            {candidate.domain_relevance === "Partially Relevant" && (
                              <span className="shrink-0 px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                                Partial
                              </span>
                            )}
                            {candidate.domain_relevance === "Not Relevant" && (
                              <span
                                title="Academic / Non-IT Domain"
                                className="shrink-0 px-1.5 py-0.2 rounded text-[9px] font-bold bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800"
                              >
                                Non-IT
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Target Role Requisition */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-100 text-slate-700 dark:bg-[#162038] dark:text-slate-300 border border-slate-200/80 dark:border-[#223052] max-w-[150px] truncate"
                          title={candidate.target_role || "General Requisition"}
                        >
                          <Briefcase className="h-3 w-3 text-indigo-500 shrink-0" />
                          <span className="truncate">{candidate.target_role || "General Requisition"}</span>
                        </span>
                      </td>

                      {/* Skills & Match */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="space-y-1.5">
                          {fit != null ? (
                            <div className="flex items-center gap-2">
                              <span
                                className={`px-2 py-0.5 rounded-md text-[10px] font-extrabold flex items-center gap-1 ${
                                  fit >= 85
                                    ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                                    : fit >= 65
                                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                                    : "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                                }`}
                              >
                                <Sparkles className="h-2.5 w-2.5" />
                                {fit}% Match
                              </span>
                              <div className="w-16 bg-slate-100 dark:bg-[#16203a] h-1.5 rounded-full overflow-hidden shrink-0">
                                <div
                                  className="h-full rounded-full bg-gradient-to-r from-teal-400 to-indigo-600"
                                  style={{ width: `${fit}%` }}
                                />
                              </div>
                            </div>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200/80 dark:border-amber-800/60">
                              Pending Eval
                            </span>
                          )}

                          {/* Top Skills Tags */}
                          {topSkills.length > 0 && (
                            <div className="flex items-center gap-1 flex-wrap">
                              {topSkills.map((sk, sIdx) => (
                                <span
                                  key={sIdx}
                                  className="px-1.5 py-0.2 rounded text-[9px] font-medium bg-slate-100 text-slate-600 dark:bg-[#151f38] dark:text-slate-300 border border-slate-200/60 dark:border-[#202c4b]"
                                >
                                  {sk}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>

                      {/* Evidence & Sources */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="space-y-1.5">
                          <div>
                            {candidate.evidence_status === "Verified" && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                                <CheckCircle2 className="h-3 w-3 stroke-[2.5]" />
                                Verified
                              </span>
                            )}
                            {candidate.evidence_status === "Partial" && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20">
                                <Clock className="h-3 w-3" />
                                Partial
                              </span>
                            )}
                            {candidate.evidence_status === "Not Verified" && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-500 dark:bg-slate-700/30 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50">
                                Not Verified
                              </span>
                            )}
                            {(candidate.evidence_status === "Pending Review" || fit == null) && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50">
                                <Clock className="h-3 w-3" />
                                Pending
                              </span>
                            )}
                          </div>

                          {/* Source Icons */}
                          <div className="flex items-center gap-1 text-slate-400">
                            <span
                              className="h-5 w-5 rounded bg-blue-500 text-white flex items-center justify-center shadow-2xs"
                              title="LinkedIn Profile"
                            >
                              <LinkedInIcon className="h-2.5 w-2.5" />
                            </span>
                            {candidate.sources?.includes("github") && (
                              <span
                                className="h-5 w-5 rounded bg-slate-800 text-white flex items-center justify-center shadow-2xs"
                                title="GitHub Code Verified"
                              >
                                <GithubIcon className="h-2.5 w-2.5" />
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-3 whitespace-nowrap">
                        <div className="flex flex-col gap-1 items-start">
                          {candidate.status === "New" && (
                            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-sky-50 text-sky-700 dark:bg-blue-500/10 dark:text-blue-400 border border-sky-200 dark:border-blue-500/20">
                              New
                            </span>
                          )}
                          {candidate.status === "In Review" && (
                            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20">
                              In Review
                            </span>
                          )}
                          {candidate.status === "Shortlisted" && (
                            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                              Shortlisted
                            </span>
                          )}
                          {candidate.status === "Not a Fit" && (
                            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20">
                              Not a Fit
                            </span>
                          )}
                          {candidate.outreach_status === "Sent" && (
                            <span
                              className="inline-flex items-center gap-1 px-2 py-0.2 rounded-full text-[9px] font-bold bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 border border-teal-200 dark:border-teal-800"
                              title={`Outreach sent via ${candidate.outreach_method || "LinkedIn"}`}
                            >
                              <Mail className="h-2.5 w-2.5" /> Sent ✓
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* =================== RICH DOSSIER CARDS VIEW =================== */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredCandidates.map((candidate, idx) => {
            const fit = candidate.skill_match ?? candidate.fit_score;
            const isShortlisted = candidate.status === "Shortlisted";
            const rawSkills = Array.isArray(candidate.skills)
              ? candidate.skills
              : typeof candidate.skills === "string" && candidate.skills.startsWith("[")
              ? (() => {
                  try {
                    return JSON.parse(candidate.skills);
                  } catch {
                    return [];
                  }
                })()
              : [];

            return (
              <div
                key={`${candidate.id || "cand"}_${idx}`}
                className="p-5 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs hover:border-indigo-300 dark:hover:border-indigo-700/60 transition-all flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  {/* Card Header: Avatar, Name, Score Pill */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0">
                      <img
                        src={
                          candidate.avatar ||
                          candidate.avatar_url ||
                          "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"
                        }
                        alt={candidate.name}
                        onError={(e) => {
                          e.currentTarget.onerror = null;
                          e.currentTarget.src =
                            "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80";
                        }}
                        className="h-12 w-12 rounded-2xl object-cover border border-slate-200 dark:border-[#222e4d] shadow-2xs shrink-0"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-bold text-slate-900 dark:text-white truncate">
                            {candidate.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, "")?.trim() || candidate.name}
                          </h4>
                          {candidate.canonical_url && (
                            <a
                              href={candidate.canonical_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-slate-400 hover:text-indigo-600"
                              title="Open original profile"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                          )}
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-300 font-medium truncate mt-0.5">
                          {candidate.title || candidate.headline || "Software Professional"}
                        </p>
                        <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mt-1">
                          <MapPin className="h-3 w-3 text-slate-400 shrink-0" />
                          <span className="truncate">{candidate.location || "Location not stated"}</span>
                          {candidate.location_compatibility_status === "Compatible" && (
                            <span className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400">• Compatible</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Fit score badge */}
                    <div className="shrink-0 text-right">
                      {fit != null ? (
                        <span
                          className={`inline-flex items-center gap-1 px-3 py-1 rounded-xl text-xs font-black ${
                            fit >= 80
                              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"
                              : fit >= 60
                              ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800"
                              : "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400 border border-amber-200 dark:border-amber-800"
                          }`}
                        >
                          <Sparkles className="h-3 w-3" />
                          {fit}% Match
                        </span>
                      ) : (
                        <span className="text-[11px] font-semibold text-slate-400 bg-slate-100 dark:bg-[#151c33] px-2.5 py-1 rounded-lg">
                          Pending Eval
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Metadata Chips: Company, Work Auth, Target Requisition */}
                  <div className="flex flex-wrap items-center gap-2 text-[11px]">
                    {candidate.company && candidate.company !== "Current Organization" && (
                      <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-slate-50 dark:bg-[#131a2e] border border-slate-200 dark:border-[#1e293b] text-slate-700 dark:text-slate-300">
                        <Building2 className="h-3 w-3 text-slate-400" />
                        {candidate.company}
                      </span>
                    )}

                    {candidate.work_authorization && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                        <Award className="h-2.5 w-2.5 text-amber-600" />
                        {candidate.work_authorization}
                      </span>
                    )}

                    {candidate.target_role && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-bold bg-slate-100 text-slate-700 dark:bg-[#162038] dark:text-slate-300 border border-slate-200/80 dark:border-[#223052]">
                        <Briefcase className="h-2.5 w-2.5 text-indigo-500" />
                        {candidate.target_role}
                      </span>
                    )}

                    {candidate.outreach_status === "Sent" && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-bold bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                        <Mail className="h-2.5 w-2.5" /> Sent ✓
                      </span>
                    )}
                  </div>

                  {/* Verbatim Grounded Quote / Justification */}
                  <div className="p-3 rounded-2xl bg-slate-50/80 dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1e293b] text-xs text-slate-700 dark:text-slate-300 leading-relaxed italic">
                    “{candidate.justification || candidate.evidence_summary || candidate.headline || "Profile harvested and verified from public source record."}”
                  </div>

                  {/* Skills tags */}
                  {rawSkills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {rawSkills.slice(0, 5).map((sk, sIdx) => (
                        <span
                          key={sIdx}
                          className="px-2 py-0.5 rounded-lg text-[10px] font-semibold bg-slate-100 dark:bg-[#141c33] border border-slate-200 dark:border-[#1e2a4a] text-slate-700 dark:text-slate-300"
                        >
                          {sk}
                        </span>
                      ))}
                      {rawSkills.length > 5 && (
                        <span className="text-[10px] text-slate-400 font-bold self-center">
                          +{rawSkills.length - 5} more
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Bottom Action Toolbar */}
                <div className="pt-3 border-t border-slate-100 dark:border-[#162035] flex items-center justify-between gap-2">
                  <button
                    onClick={() => {
                      setSelectedCandidate(candidate);
                      if (setEvalTargetRole) {
                        setEvalTargetRole(
                          candidate.target_role ||
                            candidate.job_title ||
                            jobRequirements.jobTitle ||
                            savedJobs[0]?.job_title ||
                            "Senior AI Lead"
                        );
                      }
                    }}
                    className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex items-center gap-1 cursor-pointer"
                  >
                    <span>Inspect Dossier</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleUpdateStatus(candidate.id, isShortlisted ? "New" : "Shortlisted")}
                      className={`flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        isShortlisted
                          ? "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300"
                          : "bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] text-slate-700 dark:text-slate-200 hover:border-amber-400"
                      }`}
                    >
                      <Star className={`h-3 w-3 ${isShortlisted ? "fill-amber-500 text-amber-500" : ""}`} />
                      <span>{isShortlisted ? "Shortlisted" : "Shortlist"}</span>
                    </button>

                    <button
                      onClick={() => handleOpenOutreach([candidate])}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold shadow-xs transition-all active:scale-[0.98] cursor-pointer"
                    >
                      <Send className="h-3 w-3" />
                      <span>Outreach</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
