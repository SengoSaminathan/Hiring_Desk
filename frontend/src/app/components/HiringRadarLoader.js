"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Cpu,
  Database,
  Search,
  CheckCircle2,
  MapPin,
  Briefcase,
  Layers,
  ShieldCheck,
  Zap,
} from "lucide-react";

const STAGES = [
  {
    title: "Querying Candidate Repository & Evaluations...",
    subtitle: "Retrieving indexed candidate dossiers, LinkedIn profiles, and verified credentials from local database",
    icon: Database,
    badge: "Database Query",
    color: "indigo",
  },
  {
    title: "Cross-referencing Requisition Requirements...",
    subtitle: "Aligning harvested skills, experience depth, and verified licenses against role specifications",
    icon: Search,
    badge: "Criteria Match",
    color: "purple",
  },
  {
    title: "Synthesizing Evidence & Section Scores...",
    subtitle: "Validating objective evidence quotes, category breakdown scores, and fit level confidence",
    icon: Sparkles,
    badge: "Evidence Synthesis",
    color: "emerald",
  },
  {
    title: "Calibrating Candidate Shortlist Rankings...",
    subtitle: "Applying TanStack Query cache persistence for instant sub-millisecond retrieval",
    icon: Cpu,
    badge: "TanStack Revalidation",
    color: "blue",
  },
];

export function HiringRadarLoader({
  message,
  subMessage,
  role = "Requisition Candidates",
  compact = false,
  fullScreen = false,
}) {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % STAGES.length);
    }, 2400);
    return () => clearInterval(timer);
  }, []);

  const currentStage = STAGES[stageIndex];
  const StageIcon = currentStage.icon;

  const content = (
    <div
      className={`relative overflow-hidden transition-all duration-500 ${
        fullScreen
          ? "fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-md p-4"
          : "w-full max-w-4xl mx-auto my-6"
      }`}
    >
      <style>{`
        @keyframes radar-beam-sweep {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
        @keyframes pulse-ring {
          0% {
            transform: scale(0.95);
            opacity: 0.8;
          }
          50% {
            transform: scale(1.35);
            opacity: 0.2;
          }
          100% {
            transform: scale(0.95);
            opacity: 0.8;
          }
        }
        @keyframes radar-blip {
          0%, 100% {
            transform: scale(1);
            filter: drop-shadow(0 0 2px rgba(99, 102, 241, 0.4));
          }
          50% {
            transform: scale(1.18);
            filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.8));
          }
        }
        @keyframes bar-shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
      `}</style>

      {/* Main Glassmorphic Card Container */}
      <div className="relative rounded-3xl bg-white/90 dark:bg-[#0c1224]/90 backdrop-blur-xl border border-slate-200/90 dark:border-[#1c294d] shadow-2xl shadow-indigo-500/10 p-6 sm:p-10 flex flex-col items-center text-center">
        {/* Subtle Ambient Background Gradients */}
        <div className="absolute top-0 left-1/4 -translate-y-1/2 w-72 h-72 bg-indigo-500/10 dark:bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 translate-y-1/2 w-72 h-72 bg-purple-500/10 dark:bg-purple-600/15 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header Tag */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200/80 dark:border-indigo-800/80 mb-6 shadow-xs">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-[11px] font-black tracking-wider uppercase bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-300 bg-clip-text text-transparent">
            AI Talent Radar • Discovery Scanner
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 font-bold">
            {role}
          </span>
        </div>

        {/* Circular Radar Scanner Visualization */}
        <div className="relative w-64 h-64 sm:w-80 sm:h-80 flex items-center justify-center my-2 select-none">
          {/* Outer Ring */}
          <div className="absolute inset-0 rounded-full border border-indigo-300/40 dark:border-indigo-500/30" />

          {/* Concentric Range Rings */}
          <div className="absolute w-3/4 h-3/4 rounded-full border border-indigo-300/30 dark:border-indigo-500/20" />
          <div className="absolute w-1/2 h-1/2 rounded-full border border-dashed border-indigo-400/40 dark:border-indigo-400/30" />
          <div className="absolute w-1/4 h-1/4 rounded-full border border-indigo-300/30 dark:border-indigo-500/20" />

          {/* Range Grid Axes (Crosshairs) */}
          <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-px bg-gradient-to-r from-transparent via-indigo-400/30 dark:via-indigo-500/30 to-transparent" />
          <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-px bg-gradient-to-b from-transparent via-indigo-400/30 dark:via-indigo-500/30 to-transparent" />

          {/* Sweeping Radar Beam (Conic Gradient) */}
          <div
            className="absolute inset-0 rounded-full pointer-events-none"
            style={{
              animation: "radar-beam-sweep 3.2s linear infinite",
              background:
                "conic-gradient(from 0deg, transparent 0deg, transparent 270deg, rgba(99, 102, 241, 0.05) 300deg, rgba(99, 102, 241, 0.35) 358deg, rgba(165, 180, 252, 0.9) 360deg)",
            }}
          />

          {/* Discovered Talent Node 1: Top Right (Match 94%) */}
          <div
            className="absolute top-[18%] right-[16%] flex items-center gap-1.5 z-10 transition-transform duration-300"
            style={{ animation: "radar-blip 2.6s ease-in-out infinite" }}
          >
            <div className="relative flex items-center justify-center">
              <span className="absolute w-5 h-5 rounded-full bg-emerald-400/30 animate-ping" />
              <div className="w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900 shadow-sm" />
            </div>
            <div className="px-2 py-0.5 rounded-lg bg-emerald-500/90 text-white text-[10px] font-black tracking-tight shadow-md flex items-center gap-1 backdrop-blur-xs">
              <CheckCircle2 className="w-2.5 h-2.5" />
              <span>Match 94%</span>
            </div>
          </div>

          {/* Discovered Talent Node 2: Bottom Left (Python/RAG Verified) */}
          <div
            className="absolute bottom-[22%] left-[12%] flex items-center gap-1.5 z-10"
            style={{ animation: "radar-blip 3s ease-in-out infinite 0.8s" }}
          >
            <div className="relative flex items-center justify-center">
              <span className="absolute w-5 h-5 rounded-full bg-indigo-400/30 animate-ping" />
              <div className="w-3.5 h-3.5 rounded-full bg-indigo-600 border-2 border-white dark:border-slate-900 shadow-sm" />
            </div>
            <div className="px-2 py-0.5 rounded-lg bg-indigo-600/90 text-white text-[10px] font-black tracking-tight shadow-md flex items-center gap-1 backdrop-blur-xs">
              <Sparkles className="w-2.5 h-2.5" />
              <span>Python/RAG Verified</span>
            </div>
          </div>

          {/* Discovered Talent Node 3: Top Left (Location: Compatible) */}
          <div
            className="absolute top-[28%] left-[15%] flex items-center gap-1.5 z-10"
            style={{ animation: "radar-blip 3.4s ease-in-out infinite 1.5s" }}
          >
            <div className="relative flex items-center justify-center">
              <span className="absolute w-4 h-4 rounded-full bg-sky-400/30 animate-ping" />
              <div className="w-3 h-3 rounded-full bg-sky-500 border-2 border-white dark:border-slate-900 shadow-sm" />
            </div>
            <div className="px-2 py-0.5 rounded-lg bg-sky-600/90 text-white text-[10px] font-bold tracking-tight shadow-md flex items-center gap-1 backdrop-blur-xs">
              <MapPin className="w-2.5 h-2.5" />
              <span>Location: Compatible</span>
            </div>
          </div>

          {/* Discovered Talent Node 4: Bottom Right (Experience) */}
          <div
            className="absolute bottom-[20%] right-[14%] flex items-center gap-1.5 z-10"
            style={{ animation: "radar-blip 2.8s ease-in-out infinite 2.1s" }}
          >
            <div className="relative flex items-center justify-center">
              <span className="absolute w-4 h-4 rounded-full bg-purple-400/30 animate-ping" />
              <div className="w-3 h-3 rounded-full bg-purple-600 border-2 border-white dark:border-slate-900 shadow-sm" />
            </div>
            <div className="px-2 py-0.5 rounded-lg bg-purple-600/90 text-white text-[10px] font-bold tracking-tight shadow-md flex items-center gap-1 backdrop-blur-xs">
              <Briefcase className="w-2.5 h-2.5" />
              <span>8+ Yrs • Enterprise</span>
            </div>
          </div>

          {/* Center AI Talent Radar Core */}
          <div className="relative z-20 flex items-center justify-center">
            <div
              className="absolute w-16 h-16 rounded-full bg-indigo-500/20 dark:bg-indigo-600/30"
              style={{ animation: "pulse-ring 2.2s ease-in-out infinite" }}
            />
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 text-white flex items-center justify-center shadow-lg shadow-indigo-500/30 border border-white/20">
              <Cpu className="w-6 h-6 animate-pulse" />
            </div>
          </div>
        </div>

        {/* Dynamic Contextual Status Info */}
        <div className="w-full max-w-lg mt-5 space-y-3">
          <div className="flex items-center justify-center gap-2">
            <div className="p-1.5 rounded-lg bg-indigo-100 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400">
              <StageIcon className="w-4 h-4 animate-spin-slow" />
            </div>
            <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white tracking-tight transition-all duration-300">
              {message || currentStage.title}
            </h3>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed min-h-[32px] transition-opacity duration-300">
            {subMessage || currentStage.subtitle}
          </p>

          {/* Stepper Progress Bar */}
          <div className="relative w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${((stageIndex + 1) / STAGES.length) * 100}%` }}
            />
            <div
              className="absolute inset-0 bg-white/30 dark:bg-white/10 pointer-events-none"
              style={{ animation: "bar-shimmer 2s infinite linear" }}
            />
          </div>

          {/* Interactive Stage Dots & Badge */}
          <div className="flex items-center justify-between pt-2 text-[11px] text-slate-400 dark:text-slate-500">
            <div className="flex items-center gap-1.5">
              {STAGES.map((s, idx) => (
                <div
                  key={s.title}
                  onClick={() => setStageIndex(idx)}
                  className={`h-2 rounded-full cursor-pointer transition-all duration-300 ${
                    idx === stageIndex
                      ? "w-6 bg-indigo-600 dark:bg-indigo-400"
                      : "w-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300"
                  }`}
                  title={s.title}
                />
              ))}
              <span className="ml-1 text-[10px] font-semibold">
                Phase {stageIndex + 1} of {STAGES.length}
              </span>
            </div>

            <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400 font-bold">
              <Zap className="w-3 h-3" />
              <span>TanStack Query Persisted Cache</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return content;
}

export default HiringRadarLoader;
