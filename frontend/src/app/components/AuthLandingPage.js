"use client";

import React, { useState, useEffect, Suspense } from "react";
import {
  Sparkles,
  ShieldCheck,
  Bot,
  Zap,
  MapPin,
  ArrowRight,
  CheckCircle2,
  FileText,
  Compass,
  Cpu,
  Send,
  Check,
  ChevronRight,
  Clock,
  Layers,
  Lock,
} from "lucide-react";
import { SignIn } from "@clerk/nextjs";
import { useAppAuth } from "./ClerkAuthProvider";

const LIFECYCLE_STEPS = [
  {
    id: 1,
    name: "1. Ingest & Parse JD",
    shortTitle: "JD Parsing",
    icon: FileText,
    accent: "indigo",
    badge: "Semantic Extraction",
    headline: "Automated Job Description Decomposition",
    desc: "Transforms raw job descriptions into structured search plans, extracting mandatory skills, seniority depth, and strict location constraints.",
    metrics: [
      { label: "Target Requisition", val: "Senior Engineering Lead" },
      { label: "Required Core Stack", val: "Python • RAG • Distributed Systems" },
      { label: "Location Radius", val: "Strict City & Regional Commute Match" },
    ],
    statusPill: "✓ Search Plan Generated in 1.2s",
  },
  {
    id: 2,
    name: "2. Desktop Traversal",
    shortTitle: "Browser Traversal",
    icon: Bot,
    accent: "purple",
    badge: "Playwright Automation",
    headline: "Autonomous Public Profile Harvesting",
    desc: "Headed desktop browser agent navigates public candidate directories with human-cadence pauses, extracting About, Experience, Certs, and Projects.",
    metrics: [
      { label: "Execution Engine", val: "Headed Desktop Chrome Automation" },
      { label: "Safety Cadence", val: "Anti-Detection Pauses & Zero Scraping Fatigue" },
      { label: "Deep Harvesting", val: "Multi-Section Candidate Dossier Extraction" },
    ],
    statusPill: "✓ 5 Candidate Dossiers Harvested",
  },
  {
    id: 3,
    name: "3. Grounded Scoring",
    shortTitle: "Evidence Match",
    icon: ShieldCheck,
    accent: "emerald",
    badge: "Zero Hallucinations",
    headline: "Objective Multi-Factor Fit & Evidence Citations",
    desc: "Evaluates candidates against role criteria with strict category weighting. Every score is explainable and cited with verifiable public proof.",
    metrics: [
      { label: "Technical Competence", val: "95% Normalized Category Match" },
      { label: "Evidence Rigor", val: "100% Cites Public Repos & Track Records" },
      { label: "Location Verification", val: "Exact Residence & Mobility Alignment" },
    ],
    statusPill: "✓ Explainable Evidence Shortlist Ready",
  },
  {
    id: 4,
    name: "4. Calibrated Outreach",
    shortTitle: "Outreach Dispatch",
    icon: Zap,
    accent: "rose",
    badge: "Autonomous Delivery",
    headline: "1-Click Personalized Candidate Engagement",
    desc: "Generates personalized connection notes strictly under 195 characters, signed with your company mission, and delivers them via automated browser.",
    metrics: [
      { label: "Note Constraints", val: "Strictly ≤ 195 Chars (Free-Tier Safe)" },
      { label: "Brand Personalization", val: "Dynamic Company Value Prop & Recruiter Sign" },
      { label: "Delivery Channel", val: "Dual-Path: Direct Message or Connection Note" },
    ],
    statusPill: "✓ Connection Invitation Note Dispatched",
  },
];

export default function AuthLandingPage() {
  const { isSignedIn, isLoaded } = useAppAuth();
  const [activeStep, setActiveStep] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Auto-cycle lifecycle animation every 3.8s when not hovered
  useEffect(() => {
    if (isPaused) return;
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % LIFECYCLE_STEPS.length);
    }, 3800);
    return () => clearInterval(timer);
  }, [isPaused]);

  // If already signed in, do not render landing page
  if (isLoaded && isSignedIn) {
    return null;
  }

  const currentStep = LIFECYCLE_STEPS[activeStep];
  const StepIcon = currentStep.icon;

  return (
    <div className="h-screen max-h-screen overflow-hidden bg-white text-slate-900 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* -------------------- COMPACT TOP NAVIGATION BAR -------------------- */}
      <header className="w-full bg-white/95 backdrop-blur-md border-b border-slate-200/80 shrink-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-13 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-700 to-violet-600 p-0.5 flex items-center justify-center shadow-xs">
              <span className="font-black text-white text-base tracking-tight">H</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-extrabold tracking-tight text-slate-900">
                  Hiring Desk
                </span>
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  Autonomous Sourcing Platform
                </span>
              </div>
            </div>
          </div>

          {/* Right Status Badge */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200/70 text-emerald-700 text-[11px] font-semibold">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
            </span>
            <span>Desktop Playwright & AI Match Active</span>
          </div>
        </div>
      </header>

      {/* -------------------- MAIN SECTION WITH SUFFICIENT BREATHING ROOM -------------------- */}
      <main className="flex-1 min-h-0 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-3 lg:py-5 flex flex-col lg:flex-row items-center justify-between gap-8 lg:gap-12 overflow-hidden">
        {/* Left Column: Platform Content & Dynamic Lifecycle Process Animation */}
        <div className="flex-1 max-w-2xl flex flex-col justify-center overflow-hidden">
          {/* Top Pill */}
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200/70 text-indigo-700 text-xs font-bold mb-2.5 w-fit shadow-2xs">
            <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
            <span>Local-First Candidate Sourcing & Evaluation Architecture</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-2xl sm:text-3xl lg:text-[2.25rem] font-extrabold tracking-tight text-slate-900 leading-[1.2] mb-2">
            Turn any Job Description into an{" "}
            <span className="bg-gradient-to-r from-indigo-600 via-indigo-700 to-violet-600 bg-clip-text text-transparent">
              Evidence-Backed Shortlist
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-xs sm:text-[13px] text-slate-600 leading-relaxed mb-4">
            Hiring Desk replaces manual boolean search fatigue with an autonomous 4-stage pipeline: deep job decomposition, headed desktop browser sourcing, grounded evidence scoring, and calibrated candidate outreach.
          </p>

          {/* -------------------- INTERACTIVE LIFECYCLE PROCESS ANIMATION -------------------- */}
          <div
            className="w-full rounded-2xl bg-slate-50/70 border border-slate-200/90 p-3 sm:p-4 shadow-xs relative overflow-hidden transition-all duration-300"
            onMouseEnter={() => setIsPaused(true)}
            onMouseLeave={() => setIsPaused(false)}
          >
            {/* Stage Selector Stepper */}
            <div className="grid grid-cols-4 gap-1.5 mb-3 bg-white p-1 rounded-xl border border-slate-200/80 shadow-2xs">
              {LIFECYCLE_STEPS.map((step, idx) => {
                const isActive = activeStep === idx;
                const Icon = step.icon;
                return (
                  <button
                    key={step.id}
                    type="button"
                    onClick={() => setActiveStep(idx)}
                    className={`flex items-center justify-center gap-1.5 py-1.5 px-1 rounded-lg text-[11px] font-bold transition-all relative ${
                      isActive
                        ? "bg-indigo-600 text-white shadow-xs"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                    }`}
                  >
                    <Icon className={`h-3 w-3 ${isActive ? "text-white" : "text-slate-500"}`} />
                    <span className="truncate">{step.shortTitle}</span>
                  </button>
                );
              })}
            </div>

            {/* Active Stage Detail Showcase */}
            <div className="bg-white rounded-xl border border-slate-200/90 p-3.5 shadow-2xs relative overflow-hidden">
              {/* Header of Stage */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="h-7 w-7 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
                    <StepIcon className="h-4 w-4 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 leading-tight">
                      {currentStep.headline}
                    </h3>
                    <span className="text-[10px] text-indigo-600 font-semibold block">
                      Stage {currentStep.id} of 4 • {currentStep.badge}
                    </span>
                  </div>
                </div>

                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60 shrink-0">
                  {currentStep.statusPill}
                </span>
              </div>

              {/* Description */}
              <p className="text-[11px] text-slate-600 leading-relaxed mb-3">
                {currentStep.desc}
              </p>

              {/* 3 Metric Value Pillars */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[10px]">
                {currentStep.metrics.map((m, i) => (
                  <div
                    key={i}
                    className="p-2 rounded-lg bg-slate-50 border border-slate-200/70 flex flex-col justify-between"
                  >
                    <span className="text-slate-400 font-medium mb-0.5">{m.label}</span>
                    <span className="font-bold text-slate-800 leading-tight">{m.val}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Auto-cycle indicator bar */}
            <div className="w-full bg-slate-200/60 h-1 rounded-full overflow-hidden mt-2.5">
              <div
                className="h-full bg-indigo-600 transition-all duration-300 rounded-full"
                style={{ width: `${((activeStep + 1) / LIFECYCLE_STEPS.length) * 100}%` }}
              />
            </div>
            <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium">
              <span>Interactive Process Lifecycle</span>
              <span>{isPaused ? "Paused on hover" : "Auto-cycling stages"}</span>
            </div>
          </div>

          {/* Sourcing Platform Guarantees */}
          <div className="grid grid-cols-3 gap-2.5 mt-3 text-center">
            <div className="p-2 rounded-xl bg-slate-50 border border-slate-200/60">
              <span className="text-xs font-black text-slate-900 block">3x Faster</span>
              <span className="text-[10px] text-slate-500">Candidate Discovery</span>
            </div>
            <div className="p-2 rounded-xl bg-slate-50 border border-slate-200/60">
              <span className="text-xs font-black text-slate-900 block">100% Grounded</span>
              <span className="text-[10px] text-slate-500">Public Evidence Proof</span>
            </div>
            <div className="p-2 rounded-xl bg-slate-50 border border-slate-200/60">
              <span className="text-xs font-black text-slate-900 block">Local-First</span>
              <span className="text-[10px] text-slate-500">Desktop SQLite Privacy</span>
            </div>
          </div>
        </div>

        {/* Right Column: Clean Clerk Default Auth Container */}
        <div className="w-full max-w-[390px] shrink-0 flex flex-col items-center justify-center">
          <div className="w-full flex justify-center">
            <Suspense
              fallback={
                <div className="w-full p-6 rounded-2xl bg-white border border-slate-200 shadow-sm text-center">
                  <div className="h-5 w-5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  <p className="text-xs font-semibold text-slate-600">
                    Loading authentication...
                  </p>
                </div>
              }
            >
              <SignIn
                routing="hash"
                fallbackRedirectUrl="/"
                forceRedirectUrl="/"
                signUpFallbackRedirectUrl="/"
                signUpForceRedirectUrl="/"
                appearance={{
                  elements: {
                    rootBox: "w-full",
                    card: "w-full shadow-md border border-slate-200 rounded-2xl bg-white p-5",
                    footerItem: "hidden",
                  },
                }}
              />
            </Suspense>
          </div>
        </div>
      </main>

      {/* -------------------- COMPACT FOOTER -------------------- */}
      <footer className="w-full bg-slate-50 border-t border-slate-200/80 py-2 shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-1 text-[11px] text-slate-500">
          <div className="flex items-center gap-2">
            <span>© 2026 Hiring Desk</span>
            <span>•</span>
            <span>Local-first Candidate Sourcing & Evaluation Platform</span>
          </div>
          <div className="flex items-center gap-3 text-slate-400">
            <span>Desktop Playwright Engine</span>
            <span>•</span>
            <span>Grounded Evidence Citations</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
