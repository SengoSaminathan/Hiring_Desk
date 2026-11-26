"use client";

import React, { useState } from "react";
import {
  FileText,
  Briefcase,
  MapPin,
  Clock,
  Award,
  Sparkles,
  Upload,
  Check,
  Save,
  ArrowRight,
  Layers,
  ChevronRight,
  Plus
} from "lucide-react";

export default function JobDescriptionView({
  jobRequirements,
  setJobRequirements,
  savedJobs = [],
  handleSelectActiveRole,
  handleOpenWizard,
  handleSaveDraft,
  draftSavedToast,
  handleDocumentUpload,
  uploadingJd,
  uploadedFile,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [tempRequirements, setTempRequirements] = useState({ ...jobRequirements });
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleStartEdit = () => {
    setTempRequirements({ ...jobRequirements });
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setTempRequirements({ ...jobRequirements });
    setIsEditing(false);
  };

  const handleApplyChanges = () => {
    setJobRequirements(tempRequirements);
    setIsEditing(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              <FileText className="h-3 w-3" />
              Active Requisition
            </span>
            <span className="text-xs font-medium text-slate-400">ID: REQ-{jobRequirements.jobTitle?.replace(/\s+/g, '-').slice(0, 10).toUpperCase() || "GEN-01"}</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            {jobRequirements.jobTitle || "Untitled Requisition"}
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure job specifications, candidate qualifications, and saved organizational roles.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSaveDraft}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] hover:border-indigo-400 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors shadow-xs"
          >
            <Save className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
            <span>{draftSavedToast ? "Saved!" : "Save Draft"}</span>
          </button>

          <button
            onClick={() => handleOpenWizard(1)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all active:scale-[0.98]"
          >
            <Sparkles className="h-4 w-4" />
            <span>Launch Sourcing Wizard</span>
          </button>
        </div>
      </div>

      {/* Saved Roles Switcher Row */}
      {savedJobs && savedJobs.length > 0 && (
        <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-2">
              <Layers className="h-3.5 w-3.5 text-indigo-500" />
              Switch Active Role Requisition
            </h3>
            <span className="text-[11px] text-slate-400">{savedJobs.length} Requisitions Available</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {savedJobs.map((job) => {
              const isCurrent = jobRequirements.jobTitle === job.job_title;
              return (
                <div
                  key={job.id || job.job_title}
                  onClick={() => handleSelectActiveRole(job)}
                  className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all flex items-center justify-between ${
                    isCurrent
                      ? "bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-300 dark:border-indigo-700 ring-2 ring-indigo-500/10 shadow-xs"
                      : "bg-slate-50/50 dark:bg-[#11172a] border-slate-200/80 dark:border-[#1e293b] hover:border-indigo-300"
                  }`}
                >
                  <div className="min-w-0 pr-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                        {job.job_title}
                      </span>
                      {isCurrent && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-black bg-indigo-600 text-white shrink-0">
                          ACTIVE
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                      <span>{job.department || "Engineering"}</span>
                      <span>•</span>
                      <span>{job.location || "Remote"}</span>
                    </div>
                  </div>
                  <ChevronRight className={`h-4 w-4 shrink-0 ${isCurrent ? "text-indigo-600 dark:text-indigo-400" : "text-slate-400"}`} />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Grid: Details + Raw JD + Upload */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Requisition Parameters (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                Position Specifications
              </h3>
              {!isEditing ? (
                <button
                  onClick={handleStartEdit}
                  className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700"
                >
                  Edit Specifications
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCancelEdit}
                    className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleApplyChanges}
                    className="px-2.5 py-1 rounded-lg bg-indigo-600 text-white text-xs font-bold shadow-xs hover:bg-indigo-500"
                  >
                    Apply
                  </button>
                </div>
              )}
            </div>

            {/* Spec fields */}
            <div className="space-y-3.5">
              <div>
                <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Job Title
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={tempRequirements.jobTitle || ""}
                    onChange={(e) => setTempRequirements({ ...tempRequirements, jobTitle: e.target.value })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                  />
                ) : (
                  <div className="text-xs font-bold text-slate-900 dark:text-white">
                    {jobRequirements.jobTitle || "Not specified"}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                    Department
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={tempRequirements.department || ""}
                      onChange={(e) => setTempRequirements({ ...tempRequirements, department: e.target.value })}
                      className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                    />
                  ) : (
                    <div className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      {jobRequirements.department || "Engineering"}
                    </div>
                  )}
                </div>

                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                    Experience
                  </label>
                  {isEditing ? (
                    <input
                      type="number"
                      value={tempRequirements.minExperience || 0}
                      onChange={(e) => setTempRequirements({ ...tempRequirements, minExperience: parseInt(e.target.value) || 0 })}
                      className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                    />
                  ) : (
                    <div className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      {jobRequirements.minExperience}+ years minimum
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                    Work Mode
                  </label>
                  {isEditing ? (
                    <select
                      value={tempRequirements.workMode || "Remote"}
                      onChange={(e) => setTempRequirements({ ...tempRequirements, workMode: e.target.value })}
                      className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                    >
                      <option value="Remote">Remote</option>
                      <option value="Hybrid">Hybrid</option>
                      <option value="Onsite">Onsite</option>
                    </select>
                  ) : (
                    <div className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      {jobRequirements.workMode || "Remote"}
                    </div>
                  )}
                </div>

                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                    Employment
                  </label>
                  {isEditing ? (
                    <select
                      value={tempRequirements.employmentType || "Full-time"}
                      onChange={(e) => setTempRequirements({ ...tempRequirements, employmentType: e.target.value })}
                      className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                    >
                      <option value="Full-time">Full-time</option>
                      <option value="Contract">Contract</option>
                      <option value="Part-time">Part-time</option>
                    </select>
                  ) : (
                    <div className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      {jobRequirements.employmentType || "Full-time"}
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Primary Location / Sourcing Hub
                </label>
                {isEditing ? (
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      placeholder="City"
                      value={tempRequirements.city || ""}
                      onChange={(e) => setTempRequirements({ ...tempRequirements, city: e.target.value })}
                      className="text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Country"
                      value={tempRequirements.country || ""}
                      onChange={(e) => setTempRequirements({ ...tempRequirements, country: e.target.value })}
                      className="text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                    />
                  </div>
                ) : (
                  <div className="text-xs font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-slate-400" />
                    {[jobRequirements.city, jobRequirements.country].filter(Boolean).join(", ") || "Global / Anywhere"}
                  </div>
                )}
              </div>
            </div>

            {saveSuccess && (
              <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs flex items-center gap-2">
                <Check className="h-4 w-4" />
                <span>Job specifications updated successfully!</span>
              </div>
            )}
          </div>

          {/* Document Upload Box */}
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Upload className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              Import from File (PDF / DOCX)
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Upload a recruiter requisition document to automatically extract requirements, skills, and search parameters.
            </p>

            <label className="border-2 border-dashed border-slate-200 dark:border-[#1e293b] hover:border-indigo-400 dark:hover:border-indigo-600 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all bg-slate-50/50 dark:bg-[#11172a]">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => handleDocumentUpload(e.target.files?.[0])}
                className="hidden"
              />
              <Upload className="h-7 w-7 text-indigo-600 dark:text-indigo-400 mb-2" />
              <span className="text-xs font-bold text-slate-700 dark:text-slate-200">
                {uploadingJd ? "Parsing document with AI..." : "Click or drag JD file to upload"}
              </span>
              <span className="text-[10px] text-slate-400 mt-1">
                Supports PDF, DOCX, TXT up to 10MB
              </span>
            </label>

            {uploadedFile && (
              <div className="p-2.5 rounded-xl bg-indigo-50/70 border border-indigo-200 text-xs text-indigo-800 flex items-center justify-between">
                <span className="truncate font-semibold">{uploadedFile.name}</span>
                <Check className="h-4 w-4 text-indigo-600 shrink-0 ml-2" />
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Full Description Text Editor (7 cols) */}
        <div className="lg:col-span-7">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4 h-full flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                Raw Job Description & Role Context
              </h3>
              <span className="text-[11px] text-slate-400">
                {(jobRequirements.roleOverview || "").length} characters
              </span>
            </div>

            <p className="text-xs text-slate-500 dark:text-slate-400">
              Paste or refine the detailed role summary, day-to-day responsibilities, and team expectations.
            </p>

            <textarea
              rows={16}
              value={jobRequirements.roleOverview || ""}
              onChange={(e) => setJobRequirements({ ...jobRequirements, roleOverview: e.target.value })}
              placeholder="Paste the full job description here (responsibilities, requirements, qualifications, team context)..."
              className="w-full flex-1 p-4 rounded-xl border border-slate-200 dark:border-[#1e293b] bg-slate-50/50 dark:bg-[#11172a] text-xs text-slate-800 dark:text-slate-100 leading-relaxed font-mono focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-all resize-y"
            />

            <div className="pt-2 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Changes are automatically synced with the search plan generator.
              </span>
              <button
                onClick={handleSaveDraft}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-sm transition-all"
              >
                <Save className="h-3.5 w-3.5" />
                <span>Save Changes</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

