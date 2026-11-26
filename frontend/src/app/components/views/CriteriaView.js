"use client";

import React, { useState } from "react";
import {
  SlidersHorizontal,
  Sparkles,
  Check,
  Copy,
  RotateCw,
  Plus,
  X,
  Target,
  MapPin,
  ShieldCheck,
  Award,
  Zap,
  ArrowRight
} from "lucide-react";

export default function CriteriaView({
  jobRequirements,
  setJobRequirements,
  strategicQueries = [],
  setStrategicQueries,
  selectedQueryId,
  setSelectedQueryId,
  handleRegenerateSingleQuery,
  handleRegenerateAllQueries,
  generatingQueries,
  regeneratingQueryId,
  handleOpenWizard,
}) {
  const [newMandatorySkill, setNewMandatorySkill] = useState("");
  const [newPreferredSkill, setNewPreferredSkill] = useState("");
  const [copiedQueryId, setCopiedQueryId] = useState(null);

  // Add mandatory skill
  const handleAddMandatorySkill = (e) => {
    e?.preventDefault();
    const trimmed = newMandatorySkill.trim();
    if (!trimmed) return;
    const current = jobRequirements.mandatorySkills || [];
    if (!current.includes(trimmed)) {
      setJobRequirements({
        ...jobRequirements,
        mandatorySkills: [...current, trimmed],
      });
    }
    setNewMandatorySkill("");
  };

  // Remove mandatory skill
  const handleRemoveMandatorySkill = (skillToRemove) => {
    setJobRequirements({
      ...jobRequirements,
      mandatorySkills: (jobRequirements.mandatorySkills || []).filter((s) => s !== skillToRemove),
    });
  };

  // Add preferred skill
  const handleAddPreferredSkill = (e) => {
    e?.preventDefault();
    const trimmed = newPreferredSkill.trim();
    if (!trimmed) return;
    const current = jobRequirements.preferredSkills || [];
    if (!current.includes(trimmed)) {
      setJobRequirements({
        ...jobRequirements,
        preferredSkills: [...current, trimmed],
      });
    }
    setNewPreferredSkill("");
  };

  // Remove preferred skill
  const handleRemovePreferredSkill = (skillToRemove) => {
    setJobRequirements({
      ...jobRequirements,
      preferredSkills: (jobRequirements.preferredSkills || []).filter((s) => s !== skillToRemove),
    });
  };

  // Copy query to clipboard
  const handleCopyQuery = (queryText, queryId) => {
    navigator.clipboard.writeText(queryText);
    setCopiedQueryId(queryId);
    setTimeout(() => setCopiedQueryId(null), 2000);
  };

  // Fallback default queries if empty
  const queriesToDisplay = strategicQueries && strategicQueries.length > 0 ? strategicQueries : [
    {
      id: "precision",
      title: "Precision Boolean",
      description: "Strict keyword matching targeting senior candidates with all required skills.",
      query: `("${jobRequirements.jobTitle || 'Senior Engineer'}") AND (${(jobRequirements.mandatorySkills || ['Python', 'AI']).map(s => `"${s}"`).join(' AND ')}) AND ("${jobRequirements.city || 'Bangalore'}" OR "Remote")`,
    },
    {
      id: "broad",
      title: "Broad Discovery",
      description: "Wider talent reach accommodating equivalent role titles and cross-functional competencies.",
      query: `("${jobRequirements.jobTitle || 'Tech Lead'}" OR "Staff Engineer") AND (${(jobRequirements.mandatorySkills || ['Python']).map(s => `"${s}"`).join(' OR ')})`,
    },
    {
      id: "creative",
      title: "Alternative Titles & Synonyms",
      description: "Discovers hidden high-caliber talent using alternative domain phrasing and tech stack variants.",
      query: `("Machine Learning Engineer" OR "Founding Engineer" OR "AI Researcher") AND (${(jobRequirements.mandatorySkills || ['LLM', 'RAG']).map(s => `"${s}"`).join(' OR ')})`,
    }
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header Banner */}
      <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              <SlidersHorizontal className="h-3 w-3" />
              Criteria & Boolean Plan
            </span>
            <span className="text-xs font-medium text-slate-400">Target: {jobRequirements.jobTitle || "Role"}</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            Search Plan & Calibration
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Fine-tune mandatory skills, preferred qualifications, commute boundaries, and calibrated boolean queries.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRegenerateAllQueries}
            disabled={generatingQueries}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] hover:border-indigo-400 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors shadow-xs disabled:opacity-50"
          >
            <RotateCw className={`h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400 ${generatingQueries ? "animate-spin" : ""}`} />
            <span>{generatingQueries ? "Regenerating..." : "Regenerate All Queries"}</span>
          </button>

          <button
            onClick={() => handleOpenWizard(2)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all active:scale-[0.98]"
          >
            <Sparkles className="h-4 w-4" />
            <span>Edit in 3-Step Wizard</span>
          </button>
        </div>
      </div>

      {/* Grid: Skills Config + Search Queries */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Mandatory & Preferred Skills (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Mandatory Skills */}
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Mandatory Skills (Must-Haves)
                </h3>
              </div>
              <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-md">
                {(jobRequirements.mandatorySkills || []).length} Required
              </span>
            </div>

            <p className="text-xs text-slate-500 dark:text-slate-400">
              Profiles lacking these skills are strictly flagged or scored down during AI evaluation.
            </p>

            {/* Skills Tag Pills */}
            <div className="flex flex-wrap gap-2 min-h-12 p-3 rounded-xl bg-slate-50/70 dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1e293b]">
              {(jobRequirements.mandatorySkills || []).map((skill, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-white dark:bg-[#151c33] border border-slate-200 dark:border-[#202c4b] text-slate-800 dark:text-slate-200 shadow-xs"
                >
                  <span>{skill}</span>
                  <button
                    onClick={() => handleRemoveMandatorySkill(skill)}
                    className="text-slate-400 hover:text-rose-500 transition-colors"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
              {(jobRequirements.mandatorySkills || []).length === 0 && (
                <span className="text-xs text-slate-400 italic">No mandatory skills added yet.</span>
              )}
            </div>

            {/* Add Skill Input */}
            <form onSubmit={handleAddMandatorySkill} className="flex gap-2">
              <input
                type="text"
                placeholder="Add skill (e.g. Python, LLM, RAG)..."
                value={newMandatorySkill}
                onChange={(e) => setNewMandatorySkill(e.target.value)}
                className="flex-1 text-xs px-3.5 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
              />
              <button
                type="submit"
                className="px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1 shadow-xs"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Add</span>
              </button>
            </form>
          </div>

          {/* Preferred Skills */}
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
              <div className="flex items-center gap-2">
                <Award className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Preferred Skills (Nice-to-Haves)
                </h3>
              </div>
              <span className="text-[11px] font-bold text-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 px-2 py-0.5 rounded-md">
                {(jobRequirements.preferredSkills || []).length} Bonus
              </span>
            </div>

            {/* Skills Tag Pills */}
            <div className="flex flex-wrap gap-2 min-h-12 p-3 rounded-xl bg-slate-50/70 dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1e293b]">
              {(jobRequirements.preferredSkills || []).map((skill, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-white dark:bg-[#151c33] border border-slate-200 dark:border-[#202c4b] text-slate-700 dark:text-slate-300 shadow-xs"
                >
                  <span>{skill}</span>
                  <button
                    onClick={() => handleRemovePreferredSkill(skill)}
                    className="text-slate-400 hover:text-rose-500 transition-colors"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
              {(jobRequirements.preferredSkills || []).length === 0 && (
                <span className="text-xs text-slate-400 italic">No preferred skills added.</span>
              )}
            </div>

            {/* Add Preferred Skill Input */}
            <form onSubmit={handleAddPreferredSkill} className="flex gap-2">
              <input
                type="text"
                placeholder="Add preferred skill (e.g. LangChain, Docker)..."
                value={newPreferredSkill}
                onChange={(e) => setNewPreferredSkill(e.target.value)}
                className="flex-1 text-xs px-3.5 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
              />
              <button
                type="submit"
                className="px-3 py-2 rounded-xl bg-slate-800 dark:bg-slate-700 hover:bg-slate-700 text-white text-xs font-bold flex items-center gap-1 shadow-xs"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Add</span>
              </button>
            </form>
          </div>

          {/* Location & Scoring Breakdown */}
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <MapPin className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              Location & Mobility Rules
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-[#172138]">
                <span className="text-slate-500">Target Region:</span>
                <span className="font-bold text-slate-900 dark:text-white">{[jobRequirements.city, jobRequirements.country].filter(Boolean).join(", ") || "Remote"}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-[#172138]">
                <span className="text-slate-500">Commute Tolerance:</span>
                <span className="font-bold text-emerald-600">35 miles / In-Region Only</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Relocation Check:</span>
                <span className="font-bold text-slate-900 dark:text-white">Strict Verified Residency</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Strategic AI Boolean Queries (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Strategic Boolean Search Queries (AI-Generated)
                </h3>
              </div>
              <span className="text-[11px] text-slate-400">
                Calibrated for LinkedIn & Web Traversal
              </span>
            </div>

            <p className="text-xs text-slate-500 dark:text-slate-400">
              Select a calibrated query to execute or copy it directly into your candidate sourcing runner.
            </p>

            <div className="space-y-4 pt-2">
              {queriesToDisplay.map((queryObj) => {
                const isSelected = selectedQueryId === queryObj.id;
                const isRegenerating = regeneratingQueryId === queryObj.id;
                const isCopied = copiedQueryId === queryObj.id;

                return (
                  <div
                    key={queryObj.id}
                    onClick={() => setSelectedQueryId && setSelectedQueryId(queryObj.id)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? "bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-300 dark:border-indigo-700 ring-2 ring-indigo-500/10 shadow-xs"
                        : "bg-slate-50/50 dark:bg-[#11172a] border-slate-200/80 dark:border-[#1e293b] hover:border-indigo-200"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${
                          isSelected ? "bg-indigo-600 text-white" : "bg-slate-200 dark:bg-[#1a233b] text-slate-700 dark:text-slate-300"
                        }`}>
                          {queryObj.title || "Query"}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">
                          {queryObj.description}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => handleCopyQuery(queryObj.query, queryObj.id)}
                          className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white dark:bg-[#151c33] border border-slate-200 dark:border-[#202c4b] text-[11px] font-semibold text-slate-700 dark:text-slate-300 hover:text-indigo-600 transition-colors shadow-xs"
                        >
                          {isCopied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
                          <span>{isCopied ? "Copied!" : "Copy"}</span>
                        </button>

                        <button
                          onClick={() => handleRegenerateSingleQuery && handleRegenerateSingleQuery(queryObj.id)}
                          disabled={isRegenerating}
                          className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-[#1a233b] text-slate-400 hover:text-indigo-600 transition-colors"
                          title="Regenerate this strategy"
                        >
                          <RotateCw className={`h-3.5 w-3.5 ${isRegenerating ? "animate-spin text-indigo-600" : ""}`} />
                        </button>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-white dark:bg-[#090e1c] border border-slate-200/80 dark:border-[#19243f] font-mono text-[11px] text-slate-800 dark:text-slate-200 leading-relaxed break-words select-all">
                      {queryObj.query}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

