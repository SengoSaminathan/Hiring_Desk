"use client";

import React, { useState, useMemo } from "react";
import {
  Star,
  Download,
  Send,
  ExternalLink,
  Trash2,
  Sparkles,
  ChevronRight,
  MapPin,
  Briefcase,
  CheckSquare,
  Square,
  ArrowRight
} from "lucide-react";

export default function ShortlistView({
  candidateList = [],
  handleUpdateStatus,
  setSelectedCandidate,
  handleOpenOutreach,
  exportToCSV,
  setActiveNav,
}) {
  const [selectedIds, setSelectedIds] = useState([]);

  // Shortlisted candidates
  const shortlistedCandidates = useMemo(() => {
    return (candidateList || []).filter((c) => c.status === "shortlisted");
  }, [candidateList]);

  // Toggle select all
  const handleToggleSelectAll = () => {
    if (selectedIds.length === shortlistedCandidates.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(shortlistedCandidates.map((c) => c.id));
    }
  };

  // Toggle single
  const handleToggleSelect = (id) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((item) => item !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  // Batch outreach
  const handleBatchOutreach = () => {
    const selected = shortlistedCandidates.filter((c) => selectedIds.includes(c.id));
    if (selected.length > 0 && handleOpenOutreach) {
      handleOpenOutreach(selected);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
              <Star className="h-3 w-3 fill-amber-500 text-amber-500" />
              Qualified Shortlist
            </span>
            <span className="text-xs font-medium text-slate-400">
              {shortlistedCandidates.length} Candidates Selected
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            Shortlisted Talent Pool
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Export verified candidate rosters or launch multi-candidate calibrated outreach campaigns.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={exportToCSV}
            disabled={shortlistedCandidates.length === 0}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] hover:border-indigo-400 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors shadow-xs disabled:opacity-50"
          >
            <Download className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
            <span>Export to CSV</span>
          </button>

          <button
            onClick={handleBatchOutreach}
            disabled={selectedIds.length === 0}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            <Send className="h-3.5 w-3.5" />
            <span>Batch Outreach ({selectedIds.length})</span>
          </button>
        </div>
      </div>

      {/* Multi-select Toolbar */}
      {shortlistedCandidates.length > 0 && (
        <div className="p-4 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex items-center justify-between">
          <button
            onClick={handleToggleSelectAll}
            className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-300 hover:text-indigo-600"
          >
            {selectedIds.length === shortlistedCandidates.length ? (
              <CheckSquare className="h-4 w-4 text-indigo-600" />
            ) : (
              <Square className="h-4 w-4 text-slate-400" />
            )}
            <span>
              {selectedIds.length === shortlistedCandidates.length
                ? "Deselect All"
                : `Select All (${shortlistedCandidates.length})`}
            </span>
          </button>

          <span className="text-xs text-slate-400">
            {selectedIds.length} candidate{selectedIds.length === 1 ? "" : "s"} selected for bulk action
          </span>
        </div>
      )}

      {/* Shortlist Table / Cards */}
      {shortlistedCandidates.length === 0 ? (
        <div className="p-16 text-center rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] space-y-3">
          <Star className="h-12 w-12 text-amber-300 dark:text-amber-600 mx-auto" />
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Your shortlist is currently empty</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
            Review discovered profiles in Candidate Review or Interview Pipeline and click "Shortlist" to curate top talent here.
          </p>
          <div className="pt-2">
            <button
              onClick={() => setActiveNav && setActiveNav("review")}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-xs transition-all"
            >
              <span>Go to Candidate Review</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {shortlistedCandidates.map((candidate) => {
            const isSelected = selectedIds.includes(candidate.id);
            const score = candidate.overall_score || candidate.fit_score || 0;

            return (
              <div
                key={candidate.id}
                className={`p-5 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                  isSelected
                    ? "bg-indigo-50/50 dark:bg-indigo-950/30 border-indigo-300 dark:border-indigo-700 shadow-xs"
                    : "bg-white dark:bg-[#0d1222] border-slate-200/80 dark:border-[#172138]"
                }`}
              >
                {/* Left: Checkbox, Avatar, Name & Info */}
                <div className="flex items-center gap-3.5 min-w-0">
                  <button
                    onClick={() => handleToggleSelect(candidate.id)}
                    className="text-slate-400 hover:text-indigo-600 shrink-0"
                  >
                    {isSelected ? (
                      <CheckSquare className="h-4 w-4 text-indigo-600" />
                    ) : (
                      <Square className="h-4 w-4 text-slate-400" />
                    )}
                  </button>

                  <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-amber-500 to-indigo-600 text-white font-black text-xs flex items-center justify-center shrink-0">
                    {candidate.name?.slice(0, 2).toUpperCase() || "SH"}
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h4
                        onClick={() => setSelectedCandidate(candidate)}
                        className="text-xs font-bold text-slate-900 dark:text-white truncate cursor-pointer hover:text-indigo-600 transition-colors"
                      >
                        {candidate.name}
                      </h4>
                      {candidate.profile_url && (
                        <a
                          href={candidate.profile_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-400 hover:text-indigo-600 shrink-0"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                      {candidate.headline || "Software Engineer"}
                    </p>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-500">
                      {candidate.current_company && <span>{candidate.current_company}</span>}
                      {candidate.current_company && <span>•</span>}
                      <span>{candidate.current_location || candidate.location || "Remote"}</span>
                    </div>
                  </div>
                </div>

                {/* Right: Score Pill & Action Buttons */}
                <div className="flex items-center gap-3 self-end md:self-auto shrink-0">
                  {score > 0 && (
                    <span className="px-3 py-1 rounded-xl text-xs font-black bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                      {score}% High Fit
                    </span>
                  )}

                  <button
                    onClick={() => handleOpenOutreach(candidate)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-xs transition-all active:scale-[0.98]"
                  >
                    <Send className="h-3 w-3" />
                    <span>Outreach</span>
                  </button>

                  <button
                    onClick={() => handleUpdateStatus(candidate.id, "new")}
                    className="p-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
                    title="Remove from Shortlist"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

