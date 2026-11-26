"use client";

import React from "react";
import {
  Search,
  Play,
  Square,
  ShieldCheck,
  Terminal,
  RotateCw,
  ExternalLink,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Globe,
  Radio,
  FileText
} from "lucide-react";

export default function SourcingView({
  sourcing,
  setSourcing,
  searchMode,
  setSearchMode,
  browserChannel,
  setBrowserChannel,
  maxResults,
  setMaxResults,
  availableAccounts = [],
  selectedAccountId,
  setSelectedAccountId,
  activeSessionId,
  sessionState,
  sessionProgress,
  sessionError,
  logs = [],
  handleLaunchSourcing,
  handleStopSourcing,
  handleVerifyAndContinue,
  handleOpenLinkedInTab,
  handleOpenWizard,
}) {
  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              <Search className="h-3 w-3" />
              Sourcing Engine
            </span>
            <span className={`flex items-center gap-1 text-xs font-bold ${sourcing ? "text-emerald-600" : "text-slate-400"}`}>
              <span className={`h-2 w-2 rounded-full ${sourcing ? "bg-emerald-500 animate-ping" : "bg-slate-300"}`} />
              {sourcing ? "Agent Running" : "Engine Idle"}
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            Autonomous Browser Sourcing
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Execute headless or live Playwright traversals across approved candidate sources with grounded evidence extraction.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {sourcing ? (
            <button
              onClick={handleStopSourcing}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-md shadow-rose-600/20 transition-all active:scale-[0.98]"
            >
              <Square className="h-3.5 w-3.5 fill-white" />
              <span>Stop Sourcing</span>
            </button>
          ) : (
            <button
              onClick={() => handleLaunchSourcing(searchMode)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all active:scale-[0.98]"
            >
              <Play className="h-3.5 w-3.5 fill-white" />
              <span>Launch Sourcing Run</span>
            </button>
          )}

          <button
            onClick={() => handleOpenWizard(3)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] hover:border-indigo-400 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors shadow-xs"
          >
            <Sliders className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
            <span>Wizard Controls</span>
          </button>
        </div>
      </div>

      {/* Recruiter Safe Handover Mode Alert if waiting for login */}
      {sessionState === "waiting_for_login" && (
        <div className="p-5 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-in slide-in-from-top-2">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold">Recruiter Safe Handover: Sign-in Required</h4>
              <p className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
                The Playwright browser encountered a LinkedIn authentication checkpoint. Please complete sign-in directly in the browser window, then click Verify & Continue.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleOpenLinkedInTab}
              className="px-3 py-1.5 rounded-lg bg-white dark:bg-[#151c33] border border-amber-300 dark:border-amber-700 text-xs font-bold text-amber-800 dark:text-amber-300 hover:bg-amber-100 transition-colors flex items-center gap-1.5"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              <span>Open Login Tab</span>
            </button>
            <button
              onClick={handleVerifyAndContinue}
              className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold transition-all shadow-xs"
            >
              Verify & Continue
            </button>
          </div>
        </div>
      )}

      {/* Grid: Controls + Live Telemetry Terminal */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Sourcing Parameters (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Mode & Browser Channel Selection */}
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Sliders className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              Execution Controls
            </h3>

            {/* Mode Toggle */}
            <div>
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
                Execution Mode
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSearchMode("autonomous")}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    searchMode === "autonomous"
                      ? "bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-300 dark:border-indigo-700 ring-2 ring-indigo-500/10 shadow-xs"
                      : "bg-slate-50/50 dark:bg-[#11172a] border-slate-200 dark:border-[#1e293b]"
                  }`}
                >
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Autonomous</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Headless background traversal</div>
                </button>

                <button
                  type="button"
                  onClick={() => setSearchMode("live")}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    searchMode === "live"
                      ? "bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-300 dark:border-indigo-700 ring-2 ring-indigo-500/10 shadow-xs"
                      : "bg-slate-50/50 dark:bg-[#11172a] border-slate-200 dark:border-[#1e293b]"
                  }`}
                >
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Live Guided</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Visible browser window</div>
                </button>
              </div>
            </div>

            {/* Browser Channel */}
            <div>
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                Target Browser Engine
              </label>
              <select
                value={browserChannel}
                onChange={(e) => setBrowserChannel(e.target.value)}
                className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-[#222e4d] bg-white dark:bg-[#12182b] focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
              >
                <option value="chrome">Google Chrome (Default Recruiter Profile)</option>
                <option value="msedge">Microsoft Edge</option>
                <option value="chromium">Bundled Chromium</option>
              </select>
            </div>

            {/* Max Results Target */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  Target Candidate Quota
                </label>
                <span className="text-xs font-black text-indigo-600 dark:text-indigo-400">
                  {maxResults} Candidates
                </span>
              </div>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value))}
                className="w-full accent-indigo-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                <span>5 (Fast test)</span>
                <span>25 (Standard)</span>
                <span>50 (Deep pipeline)</span>
              </div>
            </div>
          </div>

          {/* Local-First Safety Card */}
          <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-2.5">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-white">
              <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              <span>Safe Desktop Automation Policy</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Hiring Desk operates directly on your local workstation with human-cadence pauses. Never solves CAPTCHAs or bypasses platform restrictions. Credentials remain stored locally in your browser session.
            </p>
          </div>
        </div>

        {/* Right Column: Live Terminal Activity Logs (7 cols) */}
        <div className="lg:col-span-7">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4 h-full flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Live Agent Telemetry Stream
                </h3>
              </div>
              <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
                <span className={`h-2 w-2 rounded-full ${sourcing ? "bg-emerald-500 animate-pulse" : "bg-slate-400"}`} />
                {logs.length} Events Logged
              </span>
            </div>

            {/* Terminal Window */}
            <div className="flex-1 min-h-[380px] max-h-[500px] overflow-y-auto p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 space-y-2.5">
              {logs.length === 0 ? (
                <div className="text-center py-16 text-slate-500">
                  <Terminal className="h-8 w-8 mx-auto mb-2 text-slate-700" />
                  <p>Agent telemetry stream is waiting for execution.</p>
                  <p className="text-[11px] text-slate-600 mt-1">Click "Launch Sourcing Run" to initiate Playwright traversal.</p>
                </div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="flex items-start gap-2.5 leading-snug">
                    <span className="text-[10px] text-slate-500 shrink-0 select-none">{log.time || "12:00:00"}</span>
                    <span className="text-indigo-400 shrink-0 select-none">&gt;</span>
                    <span className={`break-words ${
                      log.type === "error" ? "text-rose-400" :
                      log.type === "success" ? "text-emerald-400" :
                      "text-slate-200"
                    }`}>
                      {log.text}
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Bottom Actions */}
            <div className="flex items-center justify-between pt-2 text-xs">
              <span className="text-slate-400">
                Playwright process: {sourcing ? "Active PID running" : "Standby"}
              </span>
              {sourcing && (
                <button
                  onClick={handleStopSourcing}
                  className="text-rose-600 hover:text-rose-700 font-bold"
                >
                  Terminate Process
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

