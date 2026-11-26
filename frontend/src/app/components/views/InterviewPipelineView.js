"use client";

import React, { useMemo, useState } from "react";
import {
  Calendar,
  Users,
  Eye,
  Star,
  Send,
  CheckCircle2,
  ChevronRight,
  ArrowRight,
  ArrowLeft,
  ExternalLink,
  Sparkles,
  MapPin,
  Briefcase,
  GripVertical,
  Move
} from "lucide-react";

export default function InterviewPipelineView({
  candidateList = [],
  handleUpdateStatus,
  setSelectedCandidate,
  handleOpenOutreach,
}) {
  // Drag and drop state
  const [draggedCandidateId, setDraggedCandidateId] = useState(null);
  const [dragOverColumnId, setDragOverColumnId] = useState(null);

  // Partition candidates into 4 columns
  const columns = useMemo(() => {
    const discovered = [];
    const inReview = [];
    const shortlisted = [];
    const contacted = [];

    (candidateList || []).forEach((c) => {
      const st = (c.status || "new").toLowerCase();
      if (st === "shortlisted") {
        shortlisted.push(c);
      } else if (st === "in_review" || st === "reviewing") {
        inReview.push(c);
      } else if (st === "contacted" || st === "outreach_sent" || st === "messaged") {
        contacted.push(c);
      } else {
        discovered.push(c);
      }
    });

    return [
      {
        id: "new",
        title: "Discovered Profiles",
        icon: Users,
        color: "indigo",
        accent: "border-indigo-500",
        items: discovered,
        nextStage: "in_review",
        nextLabel: "Move to Review",
      },
      {
        id: "in_review",
        title: "In Review",
        icon: Eye,
        color: "amber",
        accent: "border-amber-500",
        items: inReview,
        prevStage: "new",
        nextStage: "shortlisted",
        nextLabel: "Shortlist",
      },
      {
        id: "shortlisted",
        title: "Shortlisted Talent",
        icon: Star,
        color: "purple",
        accent: "border-purple-500",
        items: shortlisted,
        prevStage: "in_review",
        nextStage: "contacted",
        nextLabel: "Send Outreach",
      },
      {
        id: "contacted",
        title: "Outreach Sent",
        icon: Send,
        color: "emerald",
        accent: "border-emerald-500",
        items: contacted,
        prevStage: "shortlisted",
      },
    ];
  }, [candidateList]);

  // Handle Drag Events
  const handleDragStart = (e, candidateId) => {
    e.dataTransfer.setData("text/plain", candidateId);
    e.dataTransfer.effectAllowed = "move";
    setDraggedCandidateId(candidateId);
  };

  const handleDragEnd = () => {
    setDraggedCandidateId(null);
    setDragOverColumnId(null);
  };

  const handleDragOver = (e, columnId) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (dragOverColumnId !== columnId) {
      setDragOverColumnId(columnId);
    }
  };

  const handleDragLeave = (e, columnId) => {
    // Only clear if actually leaving the column element (not entering child elements)
    if (!e.currentTarget.contains(e.relatedTarget)) {
      if (dragOverColumnId === columnId) {
        setDragOverColumnId(null);
      }
    }
  };

  const handleDrop = (e, targetColumnId) => {
    e.preventDefault();
    const candidateId = e.dataTransfer.getData("text/plain") || draggedCandidateId;
    if (candidateId && handleUpdateStatus) {
      handleUpdateStatus(candidateId, targetColumnId);
    }
    setDraggedCandidateId(null);
    setDragOverColumnId(null);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              <Calendar className="h-3 w-3" />
              Recruitment Workflow
            </span>
            <span className="text-xs font-medium text-slate-400">
              {candidateList.length} Total Pipeline Candidates
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            Interview & Outreach Pipeline
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Drag and drop candidate cards across stages or use 1-click stage advancement buttons.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#11172a] border border-slate-200 dark:border-[#1e293b] text-slate-500 text-xs font-medium">
            <Move className="h-3.5 w-3.5 text-indigo-500" />
            <span>Drag & drop cards to change stage</span>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-[#151c33] text-slate-700 dark:text-slate-300 font-bold">
              Shortlist: {columns[2].items.length}
            </span>
            <span className="px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-800">
              Contacted: {columns[3].items.length}
            </span>
          </div>
        </div>
      </div>

      {/* Kanban Board 4 Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 items-start">
        {columns.map((col) => {
          const Icon = col.icon;
          const isDragOver = dragOverColumnId === col.id;

          return (
            <div
              key={col.id}
              onDragOver={(e) => handleDragOver(e, col.id)}
              onDragEnter={(e) => handleDragOver(e, col.id)}
              onDragLeave={(e) => handleDragLeave(e, col.id)}
              onDrop={(e) => handleDrop(e, col.id)}
              className={`rounded-2xl p-4 flex flex-col min-h-[580px] transition-all duration-200 ${
                isDragOver
                  ? "bg-indigo-50/80 dark:bg-indigo-950/40 border-2 border-indigo-500 ring-4 ring-indigo-500/10 shadow-lg"
                  : "bg-slate-50/70 dark:bg-[#0a0f1e] border border-slate-200/80 dark:border-[#172138]"
              }`}
            >
              {/* Column Header */}
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200/80 dark:border-[#172138]">
                <div className="flex items-center gap-2">
                  <div className={`h-7 w-7 rounded-lg bg-${col.color}-100 dark:bg-${col.color}-900/30 flex items-center justify-center text-${col.color}-600 dark:text-${col.color}-400`}>
                    <Icon className="h-3.5 w-3.5" />
                  </div>
                  <h3 className="text-xs font-black text-slate-900 dark:text-white uppercase tracking-wider">
                    {col.title}
                  </h3>
                </div>
                <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-white dark:bg-[#12182b] border border-slate-200 dark:border-[#1e293b] text-slate-700 dark:text-slate-300 shadow-xs">
                  {col.items.length}
                </span>
              </div>

              {/* Drop Target Indicator banner when dragged over */}
              {isDragOver && (
                <div className="mb-3 p-3 rounded-xl border-2 border-dashed border-indigo-400 bg-indigo-100/70 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300 text-xs font-bold text-center flex items-center justify-center gap-2 animate-pulse shadow-xs">
                  <Move className="h-3.5 w-3.5" />
                  <span>Drop to move to {col.title}</span>
                </div>
              )}

              {/* Cards List */}
              <div className="space-y-3 flex-1 overflow-y-auto max-h-[680px] pr-0.5">
                {col.items.length === 0 ? (
                  <div
                    className={`py-16 text-center text-xs rounded-xl transition-all ${
                      isDragOver
                        ? "border-2 border-dashed border-indigo-400 text-indigo-600 font-bold bg-indigo-50/50"
                        : "text-slate-400 italic"
                    }`}
                  >
                    {isDragOver ? "Release to drop candidate here" : "No candidates in this stage."}
                  </div>
                ) : (
                  col.items.map((candidate) => {
                    const score = candidate.overall_score || candidate.fit_score || 0;
                    const isBeingDragged = draggedCandidateId === candidate.id;

                    return (
                      <div
                        key={candidate.id}
                        draggable={true}
                        onDragStart={(e) => handleDragStart(e, candidate.id)}
                        onDragEnd={handleDragEnd}
                        onClick={() => setSelectedCandidate && setSelectedCandidate(candidate)}
                        className={`p-4 rounded-xl border transition-all cursor-grab active:cursor-grabbing group select-none ${
                          isBeingDragged
                            ? "opacity-40 scale-[0.98] border-indigo-400 border-dashed ring-2 ring-indigo-400/20 bg-indigo-50/50 dark:bg-indigo-950/30"
                            : "bg-white dark:bg-[#0f172a] border-slate-200/80 dark:border-[#1e293b] shadow-xs hover:border-indigo-300 dark:hover:border-indigo-700 hover:shadow-md"
                        }`}
                      >
                        {/* Drag Handle & Candidate Name & Score */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex items-start gap-1.5 min-w-0">
                            <GripVertical className="h-4 w-4 text-slate-300 group-hover:text-indigo-500 shrink-0 mt-0.5 transition-colors" />
                            <div className="min-w-0">
                              <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate group-hover:text-indigo-600 transition-colors">
                                {candidate.name}
                              </h4>
                              <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                                {candidate.headline || "Software Engineer"}
                              </p>
                            </div>
                          </div>
                          {score > 0 && (
                            <span className={`px-2 py-0.5 rounded-lg text-[10px] font-black shrink-0 ${
                              score >= 80
                                ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"
                                : "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-400"
                            }`}>
                              {score}%
                            </span>
                          )}
                        </div>

                        {/* Company & Location */}
                        <div className="space-y-1 text-[10px] text-slate-500 dark:text-slate-400 mb-3 pl-5">
                          {candidate.current_company && (
                            <div className="flex items-center gap-1 truncate">
                              <Briefcase className="h-2.5 w-2.5 text-slate-400 shrink-0" />
                              <span className="truncate">{candidate.current_company}</span>
                            </div>
                          )}
                          <div className="flex items-center gap-1 truncate">
                            <MapPin className="h-2.5 w-2.5 text-slate-400 shrink-0" />
                            <span className="truncate">{candidate.current_location || candidate.location || "Remote"}</span>
                          </div>
                        </div>

                        {/* Actions row with 1-click stage buttons */}
                        <div
                          className="pt-2 border-t border-slate-100 dark:border-[#1e293b] flex items-center justify-between gap-1 text-[11px]"
                          onClick={(e) => e.stopPropagation()}
                          onMouseDown={(e) => e.stopPropagation()}
                        >
                          {col.prevStage ? (
                            <button
                              type="button"
                              onClick={() => handleUpdateStatus(candidate.id, col.prevStage)}
                              className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 p-1 rounded hover:bg-slate-100 dark:hover:bg-[#1a233b] transition-colors"
                              title="Move back to previous stage"
                            >
                              <ArrowLeft className="h-3 w-3" />
                            </button>
                          ) : (
                            <span />
                          )}

                          <div className="flex items-center gap-1.5">
                            {col.id === "shortlisted" && (
                              <button
                                type="button"
                                onClick={() => handleOpenOutreach(candidate)}
                                className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[10px] flex items-center gap-1 shadow-xs transition-all active:scale-95"
                              >
                                <Send className="h-2.5 w-2.5" />
                                <span>Outreach</span>
                              </button>
                            )}

                            {col.nextStage && (
                              <button
                                type="button"
                                onClick={() => handleUpdateStatus(candidate.id, col.nextStage)}
                                className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-[#1a233b] hover:bg-indigo-50 hover:text-indigo-600 dark:hover:bg-indigo-950/40 text-slate-700 dark:text-slate-300 font-bold text-[10px] flex items-center gap-1 transition-colors active:scale-95"
                              >
                                <span>{col.nextLabel}</span>
                                <ArrowRight className="h-2.5 w-2.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
