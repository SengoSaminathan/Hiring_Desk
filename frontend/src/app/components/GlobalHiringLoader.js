"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Bot,
  ShieldCheck,
  Search,
  MapPin,
  CheckCircle2,
  Briefcase,
  Layers,
  Cpu,
} from "lucide-react";

const RECRUITMENT_STAGES = [
  {
    title: "Initializing Hiring Desk Autonomous Engine...",
    subtitle: "Calibrating role schemas, search plan matrices, and extraction rules",
    badge: "System Boot",
    icon: Cpu,
  },
  {
    title: "Connecting Candidate Sourcing Adapters...",
    subtitle: "Verifying Playwright browser automation channels and session state",
    badge: "Browser Automation",
    icon: Bot,
  },
  {
    title: "Calibrating Multi-Factor Evidence Scoring...",
    subtitle: "Configuring objective match weights, commute radius, and citation guards",
    badge: "AI Scoring Matrix",
    icon: ShieldCheck,
  },
  {
    title: "Synthesizing Talent Radar & Shortlists...",
    subtitle: "Preparing executive candidate dossiers and automated outreach pipeline",
    badge: "Ready",
    icon: Sparkles,
  },
];

export default function GlobalHiringLoader({
  minDisplayMs = 1500,
  onFinished,
  customTitle = null,
  customSubtitle = null,
  customBadge = null,
  forceActive = false,
}) {
  const [stageIndex, setStageIndex] = useState(0);
  const [progress, setProgress] = useState(15);
  const [isVisible, setIsVisible] = useState(true);
  const [isFadingOut, setIsFadingOut] = useState(false);

  useEffect(() => {
    // Stage cycle timer
    const stageTimer = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % RECRUITMENT_STAGES.length);
    }, 450);

    // Progress bar increment
    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 98) {
          clearInterval(progressTimer);
          return 100;
        }
        return prev + Math.floor(Math.random() * 15 + 10);
      });
    }, 180);

    let dismissTimer = null;
    if (!forceActive) {
      dismissTimer = setTimeout(() => {
        setIsFadingOut(true);
        setTimeout(() => {
          setIsVisible(false);
          if (onFinished) onFinished();
        }, 400); // Wait for transition
      }, minDisplayMs);
    } else {
      setIsFadingOut(false);
      setIsVisible(true);
    }

    return () => {
      clearInterval(stageTimer);
      clearInterval(progressTimer);
      if (dismissTimer) clearTimeout(dismissTimer);
    };
  }, [minDisplayMs, onFinished, forceActive]);

  if (!isVisible && !forceActive) return null;

  const currentStage = RECRUITMENT_STAGES[stageIndex];
  const StageIcon = currentStage.icon;
  const activeTitle = customTitle || currentStage.title;
  const activeSubtitle = customSubtitle || currentStage.subtitle;
  const activeBadge = customBadge || currentStage.badge;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-white/90 backdrop-blur-md transition-opacity duration-400 ${
        isFadingOut ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
    >
      <style>{`
        @keyframes global-radar-sweep {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes talent-blip-pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.25); opacity: 0.6; }
        }
        @keyframes pulse-ring-wave {
          0% { transform: scale(0.9); opacity: 0.8; }
          100% { transform: scale(1.4); opacity: 0; }
        }
      `}</style>

      {/* Main Glassmorphic Card */}
      <div className="w-full max-w-md mx-4 p-6 sm:p-8 rounded-3xl bg-white border border-slate-200/90 shadow-2xl flex flex-col items-center text-center relative overflow-hidden">
        {/* Subtle decorative background gradient */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* -------------------- TALENT RADAR SCANNER -------------------- */}
        <div className="relative w-40 h-40 mb-6 flex items-center justify-center">
          {/* Outer Pulsing Wave */}
          <div
            className="absolute inset-0 rounded-full border border-indigo-400/40 pointer-events-none"
            style={{ animation: "pulse-ring-wave 2s infinite ease-out" }}
          />

          {/* Concentric Radar Rings */}
          <div className="absolute inset-0 rounded-full border border-slate-200 bg-slate-50/50" />
          <div className="absolute inset-4 rounded-full border border-slate-200/80 border-dashed" />
          <div className="absolute inset-9 rounded-full border border-indigo-100" />
          <div className="absolute inset-14 rounded-full border border-slate-200" />

          {/* Crosshairs */}
          <div className="absolute w-full h-[1px] bg-slate-200/80" />
          <div className="absolute h-full w-[1px] bg-slate-200/80" />

          {/* Sweeping Radar Beam */}
          <div
            className="absolute inset-0 rounded-full overflow-hidden pointer-events-none"
            style={{ animation: "global-radar-sweep 2.4s infinite linear" }}
          >
            <div
              className="w-1/2 h-1/2 origin-bottom-right"
              style={{
                background:
                  "conic-gradient(from 180deg at 100% 100%, transparent 60deg, rgba(99, 102, 241, 0.25) 90deg)",
              }}
            />
          </div>

          {/* Discovered Candidate Blips */}
          <div
            className="absolute top-7 right-8 flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-white border border-indigo-200 shadow-xs z-10"
            style={{ animation: "talent-blip-pulse 1.8s infinite ease-in-out" }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-ping" />
            <span className="text-[9px] font-bold text-indigo-700">94% Lead Fit</span>
          </div>

          <div
            className="absolute bottom-8 left-6 flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-white border border-emerald-200 shadow-xs z-10"
            style={{ animation: "talent-blip-pulse 2.2s infinite ease-in-out 0.4s" }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-[9px] font-bold text-emerald-700">Location Match</span>
          </div>

          {/* Center Brand Pulse */}
          <div className="relative z-10 h-11 w-11 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-600 p-0.5 flex items-center justify-center shadow-md">
            <Briefcase className="h-5 w-5 text-white" />
          </div>
        </div>

        {/* -------------------- RECRUITMENT STATUS & STAGE -------------------- */}
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200/60 text-indigo-700 text-xs font-bold mb-2">
          <StageIcon className="h-3.5 w-3.5 text-indigo-600 animate-spin" />
          <span>{activeBadge}</span>
        </div>

        <h3 className="text-base font-extrabold text-slate-900 tracking-tight mb-1.5">
          {activeTitle}
        </h3>

        <p className="text-xs text-slate-500 max-w-xs mb-5 leading-normal">
          {activeSubtitle}
        </p>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2 border border-slate-200/80">
          <div
            className="h-full bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-500 transition-all duration-200 rounded-full"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>

        <div className="w-full flex items-center justify-between text-[10px] font-bold text-slate-400">
          <span>AI Sourcing Pipeline</span>
          <span>{Math.min(progress, 100)}%</span>
        </div>
      </div>
    </div>
  );
}

