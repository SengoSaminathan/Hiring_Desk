"use client";

import React, { useMemo } from "react";
import {
  BarChart3,
  Download,
  FileSpreadsheet,
  Database,
  ShieldCheck,
  CheckCircle2,
  Users,
  Star,
  Sparkles,
  ExternalLink,
  HardDrive
} from "lucide-react";

export default function ReportsView({
  candidateList = [],
  handleOpenReportModal,
  exportToCSV,
  logs = [],
}) {
  // Aggregate stats
  const stats = useMemo(() => {
    const total = candidateList.length;
    const shortlisted = candidateList.filter((c) => c.status === "shortlisted").length;
    const verified = candidateList.filter((c) => (c.overall_score || c.fit_score || 0) > 0).length;

    let totalScore = 0;
    let scoredCount = 0;
    let highFit = 0;
    let strongFit = 0;
    let moderateFit = 0;

    candidateList.forEach((c) => {
      const score = c.overall_score || c.fit_score || 0;
      if (score > 0) {
        totalScore += score;
        scoredCount += 1;
        if (score >= 80) highFit += 1;
        else if (score >= 60) strongFit += 1;
        else moderateFit += 1;
      }
    });

    const avgScore = scoredCount > 0 ? Math.round(totalScore / scoredCount) : 0;
    const conversionRate = total > 0 ? Math.round((shortlisted / total) * 100) : 0;

    return {
      total,
      shortlisted,
      verified,
      avgScore,
      conversionRate,
      highFit,
      strongFit,
      moderateFit,
    };
  }, [candidateList]);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              <BarChart3 className="h-3 w-3" />
              Intelligence & Auditing
            </span>
            <span className="text-xs font-medium text-slate-400">
              Local SQLite Database Analytics
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            Sourcing Reports & Analytics
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Review candidate match distributions, audit trails, and export local evidence dossiers.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] hover:border-indigo-400 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors shadow-xs"
          >
            <Download className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
            <span>Download CSV</span>
          </button>

          <button
            onClick={handleOpenReportModal}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all active:scale-[0.98]"
          >
            <FileSpreadsheet className="h-4 w-4" />
            <span>Open Sourcing Report Modal</span>
          </button>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-bold mb-2">
            <Users className="h-4 w-4 text-purple-600" />
            <span>Total Traversed</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">{stats.total}</div>
          <span className="text-[10px] text-slate-400">Profiles stored in SQLite database</span>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-bold mb-2">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span>Evidence Grounded</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">{stats.verified}</div>
          <span className="text-[10px] text-slate-400">Evaluated against role criteria</span>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-bold mb-2">
            <Star className="h-4 w-4 text-amber-500" />
            <span>Shortlist Conversion</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">{stats.conversionRate}%</div>
          <span className="text-[10px] text-slate-400">{stats.shortlisted} candidates qualified</span>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-bold mb-2">
            <Sparkles className="h-4 w-4 text-indigo-600" />
            <span>Average Fit Score</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">{stats.avgScore}%</div>
          <span className="text-[10px] text-slate-400">Across evaluated profiles</span>
        </div>
      </div>

      {/* Grid: Fit Distribution + Database Status */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Match Distribution (7 cols) */}
        <div className="lg:col-span-7">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              Fit Score Distribution
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Breakdown of candidates across scoring tiers based on multi-factor requirements.
            </p>

            <div className="space-y-3 pt-2">
              {/* High Fit */}
              <div>
                <div className="flex justify-between text-xs font-bold mb-1">
                  <span className="text-emerald-700 dark:text-emerald-400">High Fit (≥80%)</span>
                  <span className="text-slate-700 dark:text-slate-300">{stats.highFit} candidates</span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-[#1a233b] overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all"
                    style={{ width: `${stats.total > 0 ? (stats.highFit / stats.total) * 100 : 0}%` }}
                  />
                </div>
              </div>

              {/* Strong Fit */}
              <div>
                <div className="flex justify-between text-xs font-bold mb-1">
                  <span className="text-indigo-700 dark:text-indigo-400">Strong Fit (60-79%)</span>
                  <span className="text-slate-700 dark:text-slate-300">{stats.strongFit} candidates</span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-[#1a233b] overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full transition-all"
                    style={{ width: `${stats.total > 0 ? (stats.strongFit / stats.total) * 100 : 0}%` }}
                  />
                </div>
              </div>

              {/* Moderate Fit */}
              <div>
                <div className="flex justify-between text-xs font-bold mb-1">
                  <span className="text-amber-700 dark:text-amber-400">Moderate Fit (&lt;60%)</span>
                  <span className="text-slate-700 dark:text-slate-300">{stats.moderateFit} candidates</span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-[#1a233b] overflow-hidden">
                  <div
                    className="h-full bg-amber-500 rounded-full transition-all"
                    style={{ width: `${stats.total > 0 ? (stats.moderateFit / stats.total) * 100 : 0}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Local SQLite Database Card (5 cols) */}
        <div className="lg:col-span-5">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Database className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              Local Database Architecture
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              All candidate evaluations, evidence links, and company settings are persisted in your local SQLite engine.
            </p>

            <div className="p-3.5 rounded-xl bg-slate-50/70 dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1e293b] space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Storage Engine:</span>
                <span className="font-bold text-slate-900 dark:text-white">SQLite 3 (WAL Mode)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">File Path:</span>
                <span className="font-mono text-[11px] text-indigo-600 dark:text-indigo-400 truncate max-w-[200px]">
                  data/hiring_desk.db
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Local Privacy:</span>
                <span className="font-bold text-emerald-600 flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5" /> Zero Cloud Leak
                </span>
              </div>
            </div>

            <button
              onClick={handleOpenReportModal}
              className="w-full py-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-bold text-xs hover:bg-indigo-100 transition-colors flex items-center justify-center gap-2"
            >
              <FileSpreadsheet className="h-4 w-4" />
              <span>View Full SQLite Data Table</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

