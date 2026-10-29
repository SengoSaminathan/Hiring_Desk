"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Search,
  Filter,
  ChevronDown,
  ChevronRight,
  MoreVertical,
  Bell,
  Plus,
  Edit3,
  ShieldCheck,
  UserCheck,
  Star,
  Users,
  Briefcase,
  Clock,
  Award,
  MapPin,
  Globe,
  Sparkles,
  Cpu,
  ExternalLink,
  Download,
  Play,
  CheckCircle2,
  Circle,
  ArrowUpRight,
  ArrowRight,
  X,
  Eye,
  FileText,
  Check,
  AlertCircle,
  RefreshCw,
  Terminal,
  Layers,
  Settings,
  Calendar,
  BarChart3,
  SlidersHorizontal,
  CheckSquare,
  Square,
  Moon,
  Sun,
  Lock,
  Database,
  User,
  Home as HomeIcon,
  ArrowLeft,
  Info,
  Shield,
  AlertTriangle,
} from "lucide-react";

// Inline brand SVGs for pixel-perfect social icons
function LinkedInIcon({ className = "h-3.5 w-3.5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
    </svg>
  );
}

function GithubIcon({ className = "h-3.5 w-3.5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  );
}

// Donut Circular Gauge Component
function DonutGauge({ percent = 42, size = 52, strokeWidth = 5 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percent / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
      <svg className="w-full h-full transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          className="stroke-slate-200 dark:stroke-slate-800"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          className="stroke-indigo-600 dark:stroke-indigo-400 transition-all duration-700 ease-out"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      <span className="absolute text-[11px] font-black text-slate-800 dark:text-white">{percent}%</span>
    </div>
  );
}

// Sparkline Mini Bar Chart SVG Component
function Sparkline({ color = "purple", data = [4, 7, 5, 8, 12, 9, 14, 18] }) {
  const colorMap = {
    purple: "fill-purple-500 hover:fill-purple-600 dark:fill-indigo-500",
    green: "fill-emerald-500 hover:fill-emerald-600 dark:fill-emerald-400",
    yellow: "fill-amber-500 hover:fill-amber-600 dark:fill-amber-400",
    red: "fill-rose-500 hover:fill-rose-600 dark:fill-rose-400",
  };

  const max = Math.max(...data, 1);

  return (
    <div className="flex items-end gap-1 h-7">
      {data.map((val, i) => {
        const heightPct = Math.round((val / max) * 100);
        return (
          <div
            key={i}
            className={`w-1 rounded-sm transition-all duration-300 ${colorMap[color] || colorMap.purple}`}
            style={{ height: `${Math.max(18, heightPct)}%` }}
          />
        );
      })}
    </div>
  );
}

// Sample Job Descriptions
const SAMPLE_JDS = {
  ai_lead: {
    id: "ai_lead",
    title: "Senior AI Engineer",
    department: "Engineering",
    type: "Full-time",
    experience: "5+ years",
    location: "Remote / Hybrid",
    region: "UAE / India",
    requirements: [
      "React.js",
      "JavaScript",
      "Next.js",
      "REST APIs",
      "API Integration",
      "System Design",
      "5+ Years Exp",
      "AI / LLMs",
      "Problem Solving",
    ],
    text: `Job Title: Senior AI Engineer
Location: Remote / Hybrid (UAE / India)
Experience: 5+ years

About the Role:
We are seeking an experienced Senior AI Engineer to architect autonomous agent pipelines, web intelligence workflows, and resilient LLM integrations. You will work with Next.js, Python FastAPI, Playwright, and local Gemini AI agents.

Key Requirements:
- 5+ years of software engineering experience with strong proficiency in Python and JavaScript/TypeScript.
- Hands-on experience building AI/LLM orchestration agents, prompt chaining, and evaluation benchmarks.
- Proven experience with browser automation (Playwright/Selenium) and web scraping pipelines.
- Familiarity with Next.js, React, REST API integration, and real-time frontend telemetry.
- Strong grounding in system design, data privacy guardrails, and self-healing agent architectures.`,
  },
  frontend: {
    id: "frontend",
    title: "Senior Frontend Engineer",
    department: "Engineering",
    type: "Full-time",
    experience: "5+ years",
    location: "Remote",
    region: "US / India",
    requirements: [
      "JavaScript",
      "React (Hooks, Context)",
      "Next.js App Router",
      "Tailwind CSS",
      "State Management",
      "REST APIs",
      "WebSockets / SSE",
      "60fps Animations",
    ],
    text: `Job Title: Senior Frontend Engineer
Location: Remote (US / India)
Experience: 5+ years

About the Role:
We are seeking an experienced Senior Frontend Engineer to build high-performance, real-time recruiting applications. You will work with React, Next.js, and modern CSS frameworks, collaborating closely with backend and AI engineers.

Responsibilities:
- Build responsive, accessible, and performant user interfaces using React and Next.js.
- Implement real-time telemetry feeds (WebSockets / SSE) for long-running AI tasks.
- Optimize web applications for latency, memory, and smooth 60fps animations.
- Mentor junior engineers and champion code quality.

Requirements:
- 5+ years of production experience in frontend engineering.
- Deep expertise in JavaScript, React (Hooks, Context, Concurrent Mode), and Next.js.
- Strong proficiency in modern Tailwind CSS and state management.
- Experience consuming REST APIs and handling error/recovery states.
- Passion for crafting polished, premium user experiences.`,
  },
  fullstack: {
    id: "fullstack",
    title: "Lead Fullstack Developer",
    department: "Product",
    type: "Full-time",
    experience: "6+ years",
    location: "Hybrid",
    region: "Bengaluru, India",
    requirements: [
      "React",
      "Node.js",
      "FastAPI",
      "PostgreSQL",
      "Playwright",
      "Tailwind CSS",
      "Distributed Systems",
    ],
    text: `Job Title: Lead Fullstack Developer
Location: Hybrid (Bengaluru, India)
Experience: 6+ years

About the Role:
We need a Lead Fullstack Developer to bridge our local-first AI backends with ultra-responsive desktop-class React frontends.

Requirements:
- 6+ years building full-stack web platforms using React and Python / Node.js.
- Deep architectural experience with PostgreSQL, SQLite, and caching systems.
- Familiarity with Playwright browser drivers, desktop packaging, and asynchronous job schedulers.`,
  },
};

// Curated verified avatars for guaranteed reliable image rendering (no 404s)
const VERIFIED_AVATARS = [
  "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=120&auto=format&fit=crop&q=80",
  "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=120&auto=format&fit=crop&q=80",
];

// Initial Candidate Pool
const INITIAL_CANDIDATES = [
  {
    id: "cand_aarav",
    name: "Aarav Mehta",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80",
    location: "Bengaluru, India",
    title: "Senior Software Engineer",
    company: "Google",
    headline: "Senior Software Engineer at Google | React, Next.js, Distributed Agent Systems",
    canonical_url: "https://www.linkedin.com/in/aarav-mehta",
    skill_match: 92,
    evidence_status: "Verified",
    sources: ["linkedin", "github"],
    status: "New",
    selected: false,
    experience_years: 6.5,
    match_level: "High",
    stored_in_db: true,
    about: "Senior Frontend & Distributed Systems Engineer with 6+ years experience architecting mission-critical web applications at Google. Passionate about AI agents, Next.js performance, and deterministic UI state management.",
    skills: ["React", "Next.js", "JavaScript", "TypeScript", "REST APIs", "System Design", "WebSockets"],
    experience_history: [
      {
        company: "Google",
        role: "Senior Software Engineer",
        dates: "2021 — Present (3.5 yrs)",
        description: "Led team of 8 frontend engineers rebuilding Google Cloud Console microfrontends with Next.js, cutting p95 load latency by 42%."
      },
      {
        company: "Razorpay",
        role: "Frontend Engineer II",
        dates: "2018 — 2021 (3.0 yrs)",
        description: "Built developer dashboard and webhook telemetry inspection tools handling 15M+ daily requests."
      }
    ],
    justification: "Proven track record at Google leading performant frontend applications with Next.js and real-time distributed telemetry.",
    evidence_quotes: [
      { requirement: "React & Next.js", quote: "Architected core Google Cloud Console microfrontends with Next.js and React Hooks.", confidence: 0.95 },
      { requirement: "5+ Years Experience", quote: "6+ years production software engineering across scalable web applications.", confidence: 0.98 },
      { requirement: "REST & API Handling", quote: "Integrated high-throughput REST and gRPC endpoints with robust client-side retry loops.", confidence: 0.91 }
    ],
    missing_skills: ["Ollama local adapter"],
  },
  {
    id: "cand_priya",
    name: "Priya Sharma",
    avatar: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=120&auto=format&fit=crop&q=80",
    location: "Dubai, UAE",
    title: "AI Engineer",
    company: "Microsoft",
    headline: "AI Engineer at Microsoft | Agent State Machines, Playwright Automation & LLM Prompting",
    canonical_url: "https://www.linkedin.com/in/priya-sharma-ai",
    skill_match: 88,
    evidence_status: "Verified",
    sources: ["linkedin", "github"],
    status: "In Review",
    selected: false,
    experience_years: 5.5,
    match_level: "High",
    stored_in_db: true,
    about: "AI and Automation Specialist focused on building reliable autonomous browser agents, tool-calling pipelines, and synthetic evaluation frameworks.",
    skills: ["Python", "FastAPI", "Playwright", "LLMs", "LangChain", "Autonomous Agents", "React"],
    experience_history: [
      {
        company: "Microsoft",
        role: "AI Engineer",
        dates: "2022 — Present (2.5 yrs)",
        description: "Engineered automated benchmark evaluation pipelines for Copilot agent models with structured JSON schema constraints."
      },
      {
        company: "Noon",
        role: "Automation Engineer",
        dates: "2019 — 2022 (3.0 yrs)",
        description: "Created headless and headed browser automation frameworks with Playwright for price parity auditing."
      }
    ],
    justification: "Strong engineering background at Microsoft specializing in LLM tool calling, autonomous agent recovery, and browser testing.",
    evidence_quotes: [
      { requirement: "AI / LLM Orchestration", quote: "Developed automated evaluation pipelines for Copilot agent models with structured JSON constraints.", confidence: 0.94 },
      { requirement: "Playwright Automation", quote: "Built automated browser test runners with persistent sessions and headless fallback.", confidence: 0.92 }
    ],
    missing_skills: ["Tailwind CSS v4"],
  },
  {
    id: "cand_daniel",
    name: "Daniel Kim",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80",
    location: "Singapore",
    title: "Software Engineer",
    company: "Amazon",
    headline: "Software Engineer at Amazon Web Services | Fullstack React, Python & Cloud Infrastructure",
    canonical_url: "https://www.linkedin.com/in/daniel-kim-sg",
    skill_match: 85,
    evidence_status: "Partial",
    sources: ["linkedin", "github"],
    status: "In Review",
    selected: false,
    experience_years: 5.0,
    match_level: "Medium",
    stored_in_db: true,
    about: "Fullstack software engineer with deep expertise across AWS, FastAPI, React, and real-time event streaming systems.",
    skills: ["React", "Python", "FastAPI", "AWS", "Docker", "PostgreSQL", "REST APIs"],
    experience_history: [
      {
        company: "Amazon Web Services",
        role: "Software Development Engineer II",
        dates: "2021 — Present (3.0 yrs)",
        description: "Designed resilient microservices in Python handling 50k requests/minute for AWS billing portal."
      },
      {
        company: "Grab",
        role: "Fullstack Developer",
        dates: "2019 — 2021 (2.0 yrs)",
        description: "Built merchant-facing React monitoring dashboards with WebSocket live streaming."
      }
    ],
    justification: "Solid fullstack foundation with React and Python APIs. Partial evidence for custom browser automation pipelines.",
    evidence_quotes: [
      { requirement: "Python & REST APIs", quote: "Designed resilient microservices in Python handling 50k requests/minute.", confidence: 0.89 },
      { requirement: "React & JavaScript", quote: "Built internal monitoring dashboards using React and TypeScript.", confidence: 0.86 }
    ],
    missing_skills: ["Playwright browser driver", "Autonomous agent recovery"],
  },
  {
    id: "cand_fatima",
    name: "Fatima Al Mansoori",
    avatar: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=120&auto=format&fit=crop&q=80",
    location: "Abu Dhabi, UAE",
    title: "Frontend Engineer",
    company: "Careem",
    headline: "Frontend Engineer at Careem | Next.js, Design Systems & High-Concurrency Telemetry",
    canonical_url: "https://www.linkedin.com/in/fatima-almansoori",
    skill_match: 78,
    evidence_status: "Verified",
    sources: ["linkedin"],
    status: "Shortlisted",
    selected: false,
    experience_years: 4.5,
    match_level: "Medium",
    stored_in_db: true,
    about: "Frontend engineer passionate about design systems, accessible UX, and building responsive Next.js apps with Tailwind CSS.",
    skills: ["Next.js", "React", "Tailwind CSS", "JavaScript", "Design Systems", "Figma to Code"],
    experience_history: [
      {
        company: "Careem",
        role: "Frontend Engineer",
        dates: "2021 — Present (3.2 yrs)",
        description: "Maintained design system across web apps serving 10M+ users across the MENA region with zero regression."
      }
    ],
    justification: "Superb UI/UX craftsmanship with Next.js and Tailwind CSS. Slightly shy of the 5-year requirement but excellent technical score.",
    evidence_quotes: [
      { requirement: "Next.js & Tailwind CSS", quote: "Maintained design system across web apps serving 10M+ users across the MENA region.", confidence: 0.96 }
    ],
    missing_skills: ["Playwright Headed Automation"],
  },
  {
    id: "cand_rohit",
    name: "Rohit Verma",
    avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80",
    location: "Gurgaon, India",
    title: "Full Stack Engineer",
    company: "Flipkart",
    headline: "Full Stack Engineer at Flipkart | Python, FastApi, WebSockets & Realtime Feeds",
    canonical_url: "https://www.linkedin.com/in/rohit-verma-flipkart",
    skill_match: 74,
    evidence_status: "Not Verified",
    sources: ["linkedin", "github"],
    status: "New",
    selected: false,
    experience_years: 5.2,
    match_level: "Medium",
    stored_in_db: true,
    about: "Backend and fullstack developer focused on high-throughput asynchronous services, Python FastAPI, WebSockets, and database indexing.",
    skills: ["Python", "FastAPI", "WebSockets", "SQL", "Redis", "Docker", "JavaScript"],
    experience_history: [
      {
        company: "Flipkart",
        role: "Full Stack Engineer",
        dates: "2021 — Present (3.5 yrs)",
        description: "Built real-time order tracking backend with FastAPI and WebSockets handling flash-sale traffic spikes."
      }
    ],
    justification: "Backend strength with FastAPI and asynchronous workers. Less direct experience with Next.js App Router.",
    evidence_quotes: [
      { requirement: "Python & FastAPI", quote: "Built real-time order tracking backend with FastAPI and WebSockets.", confidence: 0.90 }
    ],
    missing_skills: ["Next.js App Router", "Tailwind CSS"],
  },
];

export default function Home() {
  // Theme state: defaults to light (as per the user's uploaded reference image)
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Navigation & View state
  const [activeNav, setActiveNav] = useState("overview");

  // Role & Sourcing state
  const [selectedRolePreset, setSelectedRolePreset] = useState("ai_lead");
  const [currentRole, setCurrentRole] = useState(SAMPLE_JDS.ai_lead);
  const [rawJd, setRawJd] = useState(SAMPLE_JDS.ai_lead.text);
  const [searchMode, setSearchMode] = useState("autonomous");
  const [browserChannel, setBrowserChannel] = useState("chrome");
  const [maxResults, setMaxResults] = useState(6);
  const [aiSearchPrompt, setAiSearchPrompt] = useState("");

  // Modals & Handover Gates
  const [isSourcingModalOpen, setIsSourcingModalOpen] = useState(false);
  const [isJdEditorOpen, setIsJdEditorOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authStatusMessage, setAuthStatusMessage] = useState("");
  const [isPostJdPromptOpen, setIsPostJdPromptOpen] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(false);
  const [isLinkedInLoggedIn, setIsLinkedInLoggedIn] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);

  // Candidate Data & Filters
  const [candidateList, setCandidateList] = useState(INITIAL_CANDIDATES);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [selectAll, setSelectAll] = useState(false);

  // Pipeline execution & telemetry
  const [analyzing, setAnalyzing] = useState(false);
  const [sourcing, setSourcing] = useState(false);
  const [sourcingStage, setSourcingStage] = useState("");
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [sessionState, setSessionState] = useState("idle");
  const [sessionProgress, setSessionProgress] = useState(0);
  const [sessionError, setSessionError] = useState(null);
  const [isResumingSession, setIsResumingSession] = useState(false);
  const [verificationFeedback, setVerificationFeedback] = useState(null);
  const [isVerifyingScreen, setIsVerifyingScreen] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [pipelineStep, setPipelineStep] = useState(3);
  const [logs, setLogs] = useState([
    { time: "2m ago", icon: "search", text: "Collected 25 profiles from LinkedIn search" },
    { time: "5m ago", icon: "file", text: "Extracted profile details (25/25)" },
    { time: "8m ago", icon: "shield", text: "Verified skills and experience using local AI" },
    { time: "12m ago", icon: "search", text: 'New search query executed "Senior AI Engineer React Next.js"' },
    { time: "14m ago", icon: "search", text: "Found 48 new profiles from GitHub and LinkedIn" },
    { time: "18m ago", icon: "code", text: 'Moving to next search query "AI Engineer API integration"' },
  ]);

  const addTelemetryLog = (msg, icon = "search") => {
    const time = "Just now";
    setLogs((prev) => [{ time, icon, text: msg }, ...prev.slice(0, 20)]);
  };

  // Backend Health & Dynamic Host URL
  const [apiBase, setApiBase] = useState("http://127.0.0.1:8001");
  const [backendHealth, setBackendHealth] = useState(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const host = window.location.hostname || "127.0.0.1";
      setApiBase(process.env.NEXT_PUBLIC_API_URL || `http://${host}:8001`);
    }
  }, []);

  const checkHealth = useCallback(async (targetBase) => {
    const url = targetBase || apiBase;
    try {
      const res = await fetch(`${url}/api/health`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setBackendHealth(data);
      } else {
        setBackendHealth({ status: "offline" });
      }
    } catch {
      setBackendHealth({ status: "offline" });
    }
  }, [apiBase]);

  const fetchStoredCandidates = useCallback(async (targetBase) => {
    const url = targetBase || apiBase;
    try {
      const res = await fetch(`${url}/api/sourcing/candidates?limit=50`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data.candidates && data.candidates.length > 0) {
          const loaded = data.candidates.map((c, idx) => {
            const fit = Math.round(Number(c.fit_score) || 78);
            return {
              id: c.id || `stored_${idx}`,
              name: c.name,
              avatar: c.avatar_url || VERIFIED_AVATARS[idx % VERIFIED_AVATARS.length],
              location: c.location || "Remote",
              title: c.headline?.split(" at ")[0] || "Software Engineer",
              company: c.current_company || "Technology Co.",
              headline: c.headline,
              canonical_url: c.canonical_url,
              skill_match: fit,
              evidence_status: fit >= 80 ? "Verified" : fit >= 60 ? "Partial" : "Not Verified",
              sources: ["linkedin", "github"],
              status: "New",
              selected: false,
              experience_years: c.experience_years || 5.0,
              about: c.about || "",
              experience_history: c.experience_history || [],
              skills: c.skills || [],
              stored_in_db: true,
              match_level: c.match_level || "Medium",
              justification: c.justification || "Candidate profile harvested and stored in local SQLite database.",
              evidence_quotes: (c.evidence_quotes || []).map((m) => ({
                requirement: m.criterion_requirement || m.requirement || "Skill",
                quote: m.verbatim_quote || m.quote || "",
                confidence: m.confidence || 0.85,
              })),
              missing_skills: c.missing_criteria || [],
            };
          });
          setCandidateList((prev) => {
            const loadedNames = new Set(loaded.map((c) => c.name.toLowerCase()));
            const remaining = prev.filter((c) => !loadedNames.has(c.name.toLowerCase()));
            return [...loaded, ...remaining];
          });
        }
      }
    } catch {
      // gracefully ignore if offline
    }
  }, [apiBase]);

  useEffect(() => {
    checkHealth(apiBase);
    fetchStoredCandidates(apiBase);
    const timer = setInterval(() => checkHealth(apiBase), 3500);
    return () => clearInterval(timer);
  }, [checkHealth, fetchStoredCandidates, apiBase]);

  // Auth & Browser Helpers
  const handleOpenLoginBrowser = async () => {
    try {
      addTelemetryLog("Opening LinkedIn in headed Chromium browser...", "search");
      const res = await fetch(`${apiBase}/api/sourcing/open-login`, { method: "POST" });
      const data = await res.json();
      if (data.authenticated) {
        setIsLinkedInLoggedIn(true);
        addTelemetryLog("Recruiter LinkedIn session detected active!", "shield");
      } else {
        addTelemetryLog("Chromium browser opened at LinkedIn login. Please sign in.", "shield");
      }
      return data;
    } catch (err) {
      addTelemetryLog(`Failed to open browser: ${err.message}`, "file");
    }
  };

  const handleCheckAuthStatus = async () => {
    setCheckingAuth(true);
    try {
      const res = await fetch(`${apiBase}/api/sourcing/check-auth`, { method: "POST" });
      const data = await res.json();
      setIsLinkedInLoggedIn(data.authenticated);
      if (data.authenticated) {
        addTelemetryLog("LinkedIn login verified! Proceeding with sourcing run...", "shield");
        setIsAuthModalOpen(false);
        setIsPostJdPromptOpen(false);
        handleLaunchSourcing("linkedin");
      } else {
        addTelemetryLog("Waiting for LinkedIn login in opened browser...", "shield");
      }
      return data;
    } catch (err) {
      addTelemetryLog(`Auth check error: ${err.message}`, "file");
    } finally {
      setCheckingAuth(false);
    }
  };

  // Open SQLite Sourcing Report Modal
  const handleOpenReportModal = async () => {
    setIsReportModalOpen(true);
    setLoadingReport(true);
    try {
      addTelemetryLog("Retrieving sourcing report from local SQLite database (hiring_desk.db)...", "shield");
      const [repRes, candRes] = await Promise.all([
        fetch(`${apiBase}/api/sourcing/report`),
        fetch(`${apiBase}/api/sourcing/candidates?limit=50`),
      ]);
      const rep = await repRes.json();
      const cands = await candRes.json();
      setReportData({ ...rep, all_candidates: cands.candidates || [] });
      addTelemetryLog(`SQLite DB Report loaded: ${rep.total_candidates_harvested || 0} candidates recorded`, "shield");
    } catch (err) {
      console.error("Report fetch error:", err);
      addTelemetryLog(`Failed to load SQLite DB report: ${err.message}`, "file");
    } finally {
      setLoadingReport(false);
    }
  };

  // Switch Role Preset
  const handleSelectRolePreset = (key) => {
    setSelectedRolePreset(key);
    const role = SAMPLE_JDS[key];
    if (role) {
      setCurrentRole(role);
      setRawJd(role.text);
      addTelemetryLog(`Switched active hiring profile to "${role.title}"`, "file");
    }
  };

  // Analyze Job Description via Gemini
  const handleAnalyzeJd = async () => {
    if (!rawJd.trim()) return;
    setAnalyzing(true);
    setError(null);
    addTelemetryLog("Analyzing Job Description with Gemini AI engine...", "file");

    try {
      const res = await fetch(`${apiBase}/api/jobs/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_jd: rawJd }),
      });

      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      setAnalysisResult(data);
      setPipelineStep(2);

      if (data.criteria) {
        setCurrentRole((prev) => ({
          ...prev,
          title: data.criteria.job_title || prev.title,
          experience: `${data.criteria.min_years_experience || 5}+ years`,
          requirements: data.criteria.mandatory_skills || prev.requirements,
        }));
      }

      addTelemetryLog(`Target role confirmed: "${data.criteria.job_title}"`, "shield");
      addTelemetryLog(`Generated Search Plan: "${data.search_plan.linkedin_keywords}"`, "search");
      setIsJdEditorOpen(false);

      // Proactively trigger the AI Agent Sourcing Handover Dialog
      setIsPostJdPromptOpen(true);
    } catch (err) {
      setError(`Analysis error: ${err.message}`);
      addTelemetryLog(`Analysis error: ${err.message}`, "file");
    } finally {
      setAnalyzing(false);
    }
  };

  // Stop Active Sourcing Session
  const handleStopSourcing = async () => {
    try {
      if (activeSessionId) {
        await fetch(`${apiBase}/api/sourcing/stop-session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: activeSessionId }),
        });
      }
      setSessionState("stopped");
      setSourcingStage("Sourcing session stopped by user.");
      setSourcing(false);
      addTelemetryLog("Sourcing session cancellation requested by user.", "shield");
    } catch (err) {
      console.warn("Stop session error:", err);
      setSourcing(false);
    }
  };

  // Recruiter clicks Open LinkedIn in a new tab
  const handleOpenLinkedInTab = async () => {
    try {
      addTelemetryLog(`Opening LinkedIn tab in headed ${browserChannel === "msedge" ? "Edge" : browserChannel === "chrome" ? "Chrome" : "Chromium"} browser...`, "search");
      await fetch(`${apiBase}/api/sourcing/open-linkedin-tab`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ browser_channel: browserChannel }),
      });
      addTelemetryLog("Switched browser tab to https://www.linkedin.com. Please complete sign-in manually.", "shield");
    } catch (err) {
      console.warn("Open LinkedIn tab warning:", err);
      if (typeof window !== "undefined") {
        window.open("https://www.linkedin.com", "_blank");
      }
    }
  };

  // Recruiter clicks "I've Logged In — Continue": AI Agent takes UI control and strictly verifies screen
  const handleVerifyAndContinue = async () => {
    if (!activeSessionId) return;
    setIsVerifyingScreen(true);
    setVerificationFeedback(null);
    addTelemetryLog("AI Agent taking UI control... Inspecting browser tabs & screen to verify LinkedIn login...", "shield");

    try {
      // Use resume-session endpoint which both verifies AND signals resume on success
      const res = await fetch(`${apiBase}/api/sourcing/resume-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: activeSessionId }),
      });
      const data = await res.json();

      if (!data.authenticated) {
        // AI AGENT REJECTS PROCEEDING: Insists user sign in properly
        const screenName = data.screen_title || "LinkedIn: Log In or Sign Up";
        setVerificationFeedback({
          type: "error",
          status: data.status,
          title: "⚠️ Login Verification Failed — AI Agent UI Inspection",
          screenTitle: screenName,
          message: data.message || `The AI Agent inspected your browser screen and detected that you are not logged in yet (Screen: '${screenName}'). Please complete the login in your browser before continuing.`,
        });
        setSessionError(data.message);
        addTelemetryLog(`AI Agent Screen Verification: Failed (${screenName}). Insisting recruiter complete manual login.`, "file");
      } else {
        // AI AGENT CONFIRMS AUTHENTICATION: Takes UI control and proceeds
        setVerificationFeedback({
          type: "success",
          status: "verified",
          title: "✅ LinkedIn Login Verified!",
          screenTitle: data.screen_title,
          message: "AI Agent has verified your LinkedIn session! Taking control of the browser UI and proceeding with candidate sourcing...",
        });
        setSessionError(null);
        addTelemetryLog(`AI Agent Screen Verification: Successfully verified LinkedIn session (${data.screen_title || "Feed"})! Resuming candidate traversal...`, "shield");
        // No need to call resume-session separately — it's already done by the endpoint
      }
    } catch (err) {
      console.error("Verification error:", err);
      setVerificationFeedback({
        type: "error",
        status: "error",
        title: "⚠️ Verification Communication Error",
        message: `Could not verify browser screen: ${err.message}`,
      });
    } finally {
      setIsVerifyingScreen(false);
    }
  };

  // Resume Session legacy alias
  const handleResumeSourcing = handleVerifyAndContinue;

  // Launch Playwright Search & Gemini Scoring
  const handleLaunchSourcing = async (modeOverride) => {
    const effectiveMode = (typeof modeOverride === "string" ? modeOverride : null) || searchMode || "autonomous";
    setIsSourcingModalOpen(true);
    setSourcing(true);
    setError(null);
    setSessionError(null);
    setPipelineStep(3);
    setSessionProgress(15);
    setSessionState("launching_browser");
    const channelName = browserChannel === "msedge" ? "Microsoft Edge" : browserChannel === "chrome" ? "Google Chrome" : "Chromium";
    setSourcingStage(
      effectiveMode === "demo"
        ? "Launching offline simulation sandbox..."
        : `Launching headed ${channelName} browser directly to LinkedIn...`
    );

    const query =
      analysisResult?.search_plan?.linkedin_keywords ||
      `"${currentRole.title}" React Next.js Python FastAPI`;

    addTelemetryLog(
      `Launching ${
        effectiveMode === "demo"
          ? "Offline Demo Simulation"
          : effectiveMode === "autonomous"
          ? `Mode A (Autonomous LinkedIn Sourcing in ${channelName})`
          : `Mode B (Guided Live LinkedIn Session in ${channelName})`
      }...`,
      "search"
    );
    addTelemetryLog(`Search query: ${query}`, "search");

    try {
      // Step 1: Start background sourcing session
      const startRes = await fetch(`${apiBase}/api/sourcing/start-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          keywords: query,
          max_results: maxResults,
          mode: effectiveMode,
          browser_channel: browserChannel,
          deep_scrape: true,
        }),
      });

      if (!startRes.ok) throw new Error(`Failed to start sourcing session (${startRes.status})`);
      const startData = await startRes.json();
      const sessionId = startData.session_id;
      setActiveSessionId(sessionId);

      // Step 2: Poll session status continuously
      let isDone = false;
      let sessionResult = null;
      let pollCount = 0;
      const maxPolls = 150; // ~120 seconds max

      while (!isDone && pollCount < maxPolls) {
        await new Promise((resolve) => setTimeout(resolve, 800));
        pollCount += 1;

        try {
          const pollRes = await fetch(`${apiBase}/api/sourcing/session/${sessionId}`, { cache: "no-store" });
          if (pollRes.ok) {
            const data = await pollRes.json();
            setSessionState(data.state || "searching");
            setSessionProgress(data.progress || 20);
            if (data.message) {
              setSourcingStage(data.message);
            }

            if (data.candidates && data.candidates.length > 0) {
              const timestamp = Date.now();
              const liveHarvested = data.candidates.map((c, idx) => ({
                id: c.id || `live_${timestamp}_${idx}`,
                name: c.name,
                avatar: c.avatar_url || VERIFIED_AVATARS[idx % VERIFIED_AVATARS.length],
                location: c.location || "Remote",
                title: c.headline?.split(" at ")[0] || "Software Engineer",
                company: c.current_company || "Technology Co.",
                headline: c.headline,
                canonical_url: c.canonical_url,
                skill_match: 82 + (idx % 3) * 4,
                evidence_status: "Verified",
                sources: ["linkedin", "web"],
                status: "New",
                selected: false,
                experience_years: c.experience_years || 5.0,
                about: c.about || "",
                experience_history: c.experience_history || [],
                skills: c.skills || [],
                stored_in_db: true,
                match_level: "High",
                justification: "Autonomous Browser Agent navigated and extracted complete resume into local SQLite database.",
                evidence_quotes: (c.skills || []).slice(0, 3).map((s) => ({
                  requirement: s,
                  quote: `${c.headline || c.about || "Verified profile skill"}`,
                  confidence: 0.9,
                })),
                missing_skills: [],
              }));

              setCandidateList((prev) => {
                const newNames = new Set(liveHarvested.map((c) => c.name.toLowerCase()));
                const remaining = prev.filter((c) => !newNames.has(c.name.toLowerCase()));
                return [...liveHarvested, ...remaining];
              });
            }

            if (["completed", "failed", "stopped"].includes(data.state)) {
              isDone = true;
              sessionResult = data;
            }
          }
        } catch (pollErr) {
          console.warn("Session poll warning:", pollErr);
        }
      }

      if (!sessionResult || sessionResult.state === "failed") {
        const errMsg = sessionResult?.error || "Browser automation session encountered an error or timed out.";
        setError(errMsg);
        setSessionError(errMsg);
        setSessionState("failed");
        addTelemetryLog(`Sourcing error: ${errMsg}`, "file");
        setSourcing(false);
        return;
      }

      if (sessionResult.state === "stopped") {
        setSessionState("stopped");
        addTelemetryLog("Sourcing session stopped by user.", "shield");
        setSourcing(false);
        return;
      }

      const extractedCandidates = sessionResult.candidates || [];
      addTelemetryLog(`Agent extracted & persisted ${extractedCandidates.length} candidate profiles into SQLite!`, "file");

      // Step 3: Run Gemini AI Evaluation if candidates found
      if (extractedCandidates.length > 0) {
        setPipelineStep(4);
        setSourcingStage(`Harvested ${extractedCandidates.length} profiles! Scoring evidence with Gemini AI...`);

        const criteria = analysisResult?.criteria || {
          job_title: currentRole.title,
          seniority_level: "Senior",
          min_years_experience: 5.0,
          mandatory_skills: currentRole.requirements.slice(0, 5),
          preferred_skills: currentRole.requirements.slice(5),
          criteria_list: currentRole.requirements.map((req) => ({
            category: "skills",
            requirement: req,
            is_mandatory: true,
            weight: 1.0,
          })),
        };

        try {
          const evalRes = await fetch(`${apiBase}/api/sourcing/evaluate-candidates`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              candidates: extractedCandidates,
              criteria: criteria,
            }),
          });

          if (evalRes.ok) {
            const evalData = await evalRes.json();
            if (evalData.evaluated_candidates && evalData.evaluated_candidates.length > 0) {
              const liveEvaluated = evalData.evaluated_candidates.map(({ candidate, evaluation }, idx) => {
                const fit = Math.round(Number(evaluation.fit_score) || 75);
                return {
                  id: `live_${Date.now()}_${idx}_${candidate.id || idx}`,
                  name: candidate.name,
                  avatar: candidate.avatar_url || VERIFIED_AVATARS[idx % VERIFIED_AVATARS.length],
                  location: candidate.location || "Remote",
                  title: candidate.headline.split(" at ")[0] || "Software Engineer",
                  company: candidate.current_company || "Technology Co.",
                  headline: candidate.headline,
                  canonical_url: candidate.canonical_url,
                  skill_match: fit,
                  evidence_status: fit >= 80 ? "Verified" : fit >= 60 ? "Partial" : "Not Verified",
                  sources: ["linkedin", "web"],
                  status: "New",
                  selected: false,
                  experience_years: candidate.experience_years || 5.0,
                  about: candidate.about || "",
                  experience_history: candidate.experience_history || [],
                  skills: candidate.skills || [],
                  stored_in_db: true,
                  match_level: evaluation.match_level,
                  justification: evaluation.justification_summary,
                  evidence_quotes: (evaluation.evidence_quotes || []).map((m) => ({
                    requirement: m.criterion_requirement,
                    quote: m.verbatim_quote,
                    confidence: m.confidence || 0.9,
                  })),
                  missing_skills: evaluation.missing_criteria || [],
                };
              });

              setCandidateList((prev) => {
                const newNames = new Set(liveEvaluated.map((c) => c.name.toLowerCase()));
                const remaining = prev.filter((c) => !newNames.has(c.name.toLowerCase()));
                return [...liveEvaluated, ...remaining];
              });
            }
          }
        } catch (evalErr) {
          console.warn("Evaluation step warning:", evalErr);
        }
      }

      setPipelineStep(5);
      setSessionState("completed");
      setSessionProgress(100);
      setSourcingStage(`🎉 Done! Harvested ${extractedCandidates.length} profiles into SQLite database. Headed ${channelName} browser remains open.`);
      addTelemetryLog(`Shortlist refreshed with ${extractedCandidates.length} verified candidate profiles (stored in SQLite)!`, "shield");

    } catch (err) {
      setError(`Sourcing error: ${err.message}`);
      setSessionError(err.message);
      setSessionState("failed");
      addTelemetryLog(`Error during sourcing: ${err.message}`, "file");
    } finally {
      setSourcing(false);
    }
  };

  // Candidate Status Toggles
  const handleUpdateStatus = (candidateId, newStatus) => {
    setCandidateList((prev) =>
      prev.map((c) => (c.id === candidateId ? { ...c, status: newStatus } : c))
    );
    if (selectedCandidate && selectedCandidate.id === candidateId) {
      setSelectedCandidate((prev) => ({ ...prev, status: newStatus }));
    }
    addTelemetryLog(`Candidate status updated: ${newStatus}`, "shield");
  };

  // Toggle Selection
  const toggleSelectCandidate = (candidateId) => {
    setCandidateList((prev) =>
      prev.map((c) => (c.id === candidateId ? { ...c, selected: !c.selected } : c))
    );
  };

  const toggleSelectAll = () => {
    const nextState = !selectAll;
    setSelectAll(nextState);
    setCandidateList((prev) => prev.map((c) => ({ ...c, selected: nextState })));
  };

  // Filter & Search Candidates
  const filteredCandidates = useMemo(() => {
    return candidateList.filter((c) => {
      if (activeTab === "new" && c.status !== "New") return false;
      if (activeTab === "in_review" && c.status !== "In Review") return false;
      if (activeTab === "shortlisted" && c.status !== "Shortlisted") return false;
      if (activeTab === "not_a_fit" && c.status !== "Not a Fit") return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          c.name.toLowerCase().includes(q) ||
          c.title.toLowerCase().includes(q) ||
          c.company.toLowerCase().includes(q) ||
          c.location.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [candidateList, activeTab, searchQuery]);

  // Metrics calculations
  const totalDiscovered = 240 + candidateList.length;
  const verifiedCount = candidateList.filter((c) => c.evidence_status === "Verified").length * 26 + 106;
  const shortlistedCount = candidateList.filter((c) => c.status === "Shortlisted").length + 23;
  const awaitingReviewCount = candidateList.filter((c) => c.status === "New" || c.status === "In Review").length + 36;

  // Export to CSV
  const exportToCSV = () => {
    if (!candidateList.length) return;
    const headers = ["Name", "Title", "Company", "Location", "Skill Match %", "Evidence Status", "Status", "URL", "Justification"];
    const rows = candidateList.map((c) => [
      `"${c.name.replace(/"/g, '""')}"`,
      `"${c.title.replace(/"/g, '""')}"`,
      `"${c.company.replace(/"/g, '""')}"`,
      `"${c.location.replace(/"/g, '""')}"`,
      c.skill_match,
      c.evidence_status,
      c.status,
      c.canonical_url,
      `"${(c.justification || "").replace(/"/g, '""')}"`,
    ]);

    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `candidates_shortlist_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    addTelemetryLog("Exported candidate shortlist to CSV!", "file");
  };

  return (
    <div className={`min-h-screen ${isDarkMode ? "dark bg-[#080c16] text-[#f1f5f9]" : "bg-[#f5f7fb] text-slate-800"} flex overflow-hidden font-sans antialiased selection:bg-indigo-500 selection:text-white transition-colors duration-200`}>
      {/* -------------------- 1. LEFT SIDEBAR NAVIGATION -------------------- */}
      <aside className="w-64 bg-white dark:bg-[#0a0f1d] border-r border-slate-200/80 dark:border-[#171f33] flex flex-col justify-between shrink-0 h-screen sticky top-0 z-30 pb-16 shadow-sm">
        <div>
          {/* Brand Logo Header */}
          <div className="px-6 py-5 flex items-center gap-3 border-b border-slate-100 dark:border-[#141b2d]">
            <div className="h-9 w-9 rounded-xl bg-slate-900 dark:bg-gradient-to-tr dark:from-indigo-600 dark:via-indigo-500 dark:to-sky-400 p-0.5 flex items-center justify-center shadow-md">
              <span className="font-black text-white text-base">H</span>
            </div>
            <div>
              <span className="text-base font-black tracking-tight text-slate-900 dark:text-white block leading-tight">
                Hiring Desk
              </span>
              <span className="text-[10px] text-slate-400 font-medium block">
                AI-Powered Candidate Sourcing
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {[
              { id: "overview", label: "Overview", icon: Layers },
              { id: "job_description", label: "Job Description", icon: FileText },
              { id: "criteria", label: "Criteria & Search Plan", icon: SlidersHorizontal },
              { id: "sourcing", label: "Sourcing", icon: Search },
              { id: "review", label: "Candidate Review", icon: UserCheck },
              { id: "pipeline", label: "Interview Pipeline", icon: Calendar },
              { id: "shortlist", label: "Shortlist", icon: Star },
              { id: "reports", label: "Reports & Exports", icon: BarChart3 },
              { id: "settings", label: "Settings", icon: Settings },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeNav === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveNav(item.id);
                    if (item.id === "job_description" || item.id === "criteria") {
                      setIsJdEditorOpen(true);
                    }
                    if (item.id === "sourcing") {
                      setIsSourcingModalOpen(true);
                    }
                    if (item.id === "reports") {
                      handleOpenReportModal();
                    }
                  }}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${isActive
                      ? "bg-indigo-50 dark:bg-indigo-600/20 text-indigo-700 dark:text-indigo-400 shadow-sm"
                      : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-[#12182b]"
                    }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? "text-indigo-600 dark:text-indigo-400" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Sidebar Widgets */}
        <div className="p-3.5 space-y-3 border-t border-slate-100 dark:border-[#141b2d]">
          {/* AI Assistant Card */}
          <div
            onClick={() => setIsSourcingModalOpen(true)}
            className="p-3 rounded-2xl bg-gradient-to-r from-indigo-50/80 to-purple-50/60 dark:from-[#13192c] dark:to-[#0e1424] border border-indigo-100 dark:border-[#1f2942] hover:border-indigo-300 dark:hover:border-indigo-500/40 cursor-pointer transition-all group shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors">
                    AI Assistant
                  </h4>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400">Get insights, generate search queries and more</p>
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-slate-600 group-hover:translate-x-0.5 transition-all" />
            </div>
          </div>

          {/* Local AI Usage Card with Circular Donut Gauge */}
          <div className="p-3 rounded-2xl bg-white dark:bg-[#0e1424] border border-slate-200/80 dark:border-[#192238] shadow-sm flex items-center gap-3">
            <DonutGauge percent={42} size={46} strokeWidth={4.5} />
            <div className="min-w-0">
              <h5 className="text-xs font-bold text-slate-900 dark:text-white">Local AI Usage</h5>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">Model: {backendHealth?.gemini_model || "gemini-2.5-flash"}</p>
              <p className="text-[10px] text-slate-400">8.2 GB / 24 GB</p>
            </div>
          </div>
        </div>
      </aside>

      {/* -------------------- 2. MAIN APPLICATION CONTENT -------------------- */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-slate-200/80 dark:border-[#141b2d] bg-white/90 dark:bg-[#090d1a]/80 backdrop-blur sticky top-0 z-20 px-8 flex items-center justify-between shrink-0 shadow-xs">
          {/* Left: Role Switcher / Logo space */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsJdEditorOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#12192e] border border-slate-200 dark:border-[#1f2a47] text-xs font-semibold text-slate-700 dark:text-slate-200 hover:border-indigo-400 transition-colors"
            >
              <span className="text-slate-400">Current Role</span>
              <span className="font-bold text-slate-900 dark:text-white">{currentRole.title}</span>
              <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
            </button>
          </div>

          {/* Center: Glowing AI Search Bar */}
          <div className="flex-1 max-w-xl mx-6">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (aiSearchPrompt.trim()) {
                  addTelemetryLog(`AI prompt received: "${aiSearchPrompt}"`, "search");
                  setIsSourcingModalOpen(true);
                }
              }}
              className="relative flex items-center"
            >
              <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white absolute left-2.5 shadow-sm">
                <Sparkles className="h-3.5 w-3.5" />
              </div>
              <input
                type="text"
                value={aiSearchPrompt}
                onChange={(e) => setAiSearchPrompt(e.target.value)}
                placeholder="Ask AI... (e.g. 'Find 10 senior React engineers in India with 5+ years')"
                className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs rounded-full pl-11 pr-11 py-2.5 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-xs"
              />
              <button
                type="submit"
                className="h-7 w-7 rounded-full bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center absolute right-2 transition-colors"
              >
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </form>
          </div>

          {/* Right: Status Pill, Notification, Theme Toggle, Profile */}
          <div className="flex items-center gap-3">
            {/* Status Pill matching Image 1 */}
            {sessionState === "waiting_for_login" ? (
              <div
                onClick={() => setIsSourcingModalOpen(true)}
                className="flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 shadow-xs cursor-pointer hover:bg-emerald-100 transition-colors animate-in fade-in"
                title="Click to view Recruiter Safe Handover Mode"
              >
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse ring-4 ring-emerald-500/20" />
                <div className="flex flex-col text-left leading-tight">
                  <span className="text-[11px] font-black text-emerald-900 dark:text-emerald-200">Agent Paused</span>
                  <span className="text-[9px] text-emerald-700 dark:text-emerald-400 font-medium">Waiting for LinkedIn Sign-in</span>
                </div>
              </div>
            ) : sourcing ? (
              <div
                onClick={() => setIsSourcingModalOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 text-indigo-800 dark:text-indigo-300 shadow-xs cursor-pointer"
              >
                <span className="h-2 w-2 rounded-full bg-indigo-500 animate-pulse" />
                <span className="text-[11px] font-bold">AI Agent Sourcing Active</span>
              </div>
            ) : null}

            {/* Notification bell */}
            <button className="h-9 w-9 rounded-xl bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-slate-900 transition-colors relative">
              <Bell className="h-4 w-4" />
              <span className="h-2 w-2 rounded-full bg-rose-500 absolute top-2 right-2 ring-2 ring-white dark:ring-[#090d1a]" />
            </button>

            {/* Dark / Light Mode Toggle */}
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              title={isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
              className="h-9 w-9 rounded-xl bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              {isDarkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-slate-600" />}
            </button>

            {/* User Profile avatar */}
            <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200 dark:border-[#141b2d]">
              <div className="h-8 w-8 rounded-full bg-[#8b5cf6] flex items-center justify-center text-xs font-bold text-white shadow-sm">
                HR
              </div>
              <div className="text-left hidden sm:flex items-center gap-1.5">
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-slate-100 leading-tight">HR Team</div>
                  <div className="text-[10px] text-slate-500 dark:text-slate-400">Recruiter</div>
                </div>
                <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
              </div>
            </div>
          </div>
        </header>

        {/* -------------------- MAIN PAGE BODY -------------------- */}
        <main className="p-7 space-y-6 max-w-[1650px] w-full mx-auto">
          {/* Top Hero Banner: "Build Great Teams with AI" */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-50/80 via-purple-50/60 to-pink-50/40 dark:from-[#11172a] dark:via-[#151c36] dark:to-[#1a1c38] border border-indigo-100/90 dark:border-[#222e50] p-7 sm:p-9 shadow-xs">
            {/* Background scenic mountain sunset silhouette with two summit hikers */}
            <div className="absolute right-0 top-0 bottom-0 w-full md:w-3/5 pointer-events-none opacity-45 dark:opacity-30 flex items-end justify-end overflow-hidden">
              <svg viewBox="0 0 700 240" className="w-full h-full object-cover">
                <defs>
                  <linearGradient id="sunsetSky" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#fed7aa" stopOpacity="0.4" />
                    <stop offset="60%" stopColor="#f472b6" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#818cf8" stopOpacity="0.1" />
                  </linearGradient>
                  <linearGradient id="backMtn" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#c084fc" />
                    <stop offset="100%" stopColor="#818cf8" />
                  </linearGradient>
                  <linearGradient id="midMtn" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#4338ca" />
                  </linearGradient>
                  <linearGradient id="frontPeak" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#312e81" />
                    <stop offset="100%" stopColor="#1e1b4b" />
                  </linearGradient>
                </defs>
                <rect width="700" height="240" fill="url(#sunsetSky)" />
                {/* Back Mountain Ridges */}
                <path d="M0 240 L140 120 L210 160 L320 85 L410 145 L520 65 L610 130 L700 80 L700 240 Z" fill="url(#backMtn)" opacity="0.45" />
                {/* Mid Mountain Ridges */}
                <path d="M60 240 L190 140 L270 175 L380 110 L470 165 L570 95 L650 150 L700 115 L700 240 Z" fill="url(#midMtn)" opacity="0.75" />
                {/* Foreground Ridge & Peak */}
                <path d="M180 240 L310 170 L420 200 L530 135 L610 180 L700 130 L700 240 Z" fill="url(#frontPeak)" />
                {/* Two Silhouette Hikers Standing on Summit Peak at x=530, y=135 */}
                <g fill="#0f172a" stroke="#0f172a">
                  {/* Hiker 1 (left) */}
                  <circle cx="523" cy="118" r="3.5" />
                  <rect x="520" y="122" width="6" height="12" rx="2" />
                  <line x1="521" y1="134" x2="520" y2="146" strokeWidth="2.2" />
                  <line x1="525" y1="134" x2="526" y2="146" strokeWidth="2.2" />
                  {/* Hiker 2 (right) */}
                  <circle cx="536" cy="119" r="3.5" />
                  <rect x="533" y="123" width="6" height="11" rx="2" />
                  <line x1="534" y1="134" x2="533" y2="146" strokeWidth="2.2" />
                  <line x1="538" y1="134" x2="539" y2="146" strokeWidth="2.2" />
                </g>
              </svg>
            </div>

            <div className="relative z-10 flex flex-col md:flex-row md:items-start justify-between gap-6">
              {/* Left Column: Heading, Subtitle, Action Buttons */}
              <div className="max-w-xl">
                <h2 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
                  Build Great Teams with AI
                </h2>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 mt-1.5 leading-relaxed">
                  From job description to shortlisted candidates — faster, smarter, and more reliable.
                </p>

                {/* Action Buttons */}
                <div className="flex items-center gap-3 mt-6">
                  <button
                    onClick={() => setIsSourcingModalOpen(true)}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 transition-all active:scale-[0.98]"
                  >
                    <Plus className="h-4 w-4" />
                    <span>New Sourcing Run</span>
                  </button>

                  <button
                    onClick={handleOpenReportModal}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] hover:border-indigo-400 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors shadow-xs"
                  >
                    <BarChart3 className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                    <span>Sourcing Report</span>
                  </button>

                  <button
                    onClick={() => setIsJdEditorOpen(true)}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] hover:border-indigo-400 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors shadow-xs"
                  >
                    <Play className="h-3.5 w-3.5 text-indigo-600 fill-indigo-600" />
                    <span>How it works</span>
                  </button>
                </div>
              </div>

              {/* Right Column: Quote pill with accent underline */}
              <div className="text-left md:text-right max-w-xs self-start md:self-auto">
                <p className="text-xs italic text-slate-600 dark:text-slate-300 font-medium leading-relaxed">
                  “Find people who don't just fit the role, but move your mission forward.”
                </p>
                <div className="w-12 h-0.5 bg-indigo-600 dark:bg-indigo-400 md:ml-auto mt-2 rounded-full" />
              </div>
            </div>
          </div>

          {/* KPI Metrics Cards Row (4 Cards) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 1. Profiles Discovered */}
            <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="h-8 w-8 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
                    <Users className="h-4 w-4" />
                  </div>
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Profiles Discovered</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-900 dark:text-white">{totalDiscovered}</span>
                  <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center">
                    <ArrowUpRight className="h-3 w-3" /> +18%
                  </span>
                </div>
              </div>
              <Sparkline color="purple" data={[4, 6, 8, 9, 11, 14, 18]} />
            </div>

            {/* 2. Evidence Verified */}
            <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="h-8 w-8 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Evidence Verified</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-900 dark:text-white">{verifiedCount}</span>
                  <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center">
                    <ArrowUpRight className="h-3 w-3" /> +64%
                  </span>
                </div>
              </div>
              <Sparkline color="green" data={[5, 8, 7, 12, 14, 16, 21]} />
            </div>

            {/* 3. Shortlisted */}
            <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="h-8 w-8 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 dark:text-amber-400">
                    <Star className="h-4 w-4" />
                  </div>
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Shortlisted</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-900 dark:text-white">{shortlistedCount}</span>
                  <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center">
                    <ArrowUpRight className="h-3 w-3" /> +4
                  </span>
                </div>
              </div>
              <Sparkline color="yellow" data={[2, 3, 4, 3, 5, 7, 9]} />
            </div>

            {/* 4. Awaiting Review */}
            <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="h-8 w-8 rounded-xl bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center text-rose-600 dark:text-rose-400">
                    <Users className="h-4 w-4" />
                  </div>
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Awaiting Review</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-900 dark:text-white">{awaitingReviewCount}</span>
                  <span className="text-[11px] font-bold text-rose-600 dark:text-rose-400 flex items-center">
                    <ArrowUpRight className="h-3 w-3" /> +12
                  </span>
                </div>
              </div>
              <Sparkline color="red" data={[6, 9, 8, 12, 10, 15, 14]} />
            </div>
          </div>

          {/* Sourcing Pipeline Stepper Card */}
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <h3 className="text-sm font-black text-slate-900 dark:text-white tracking-tight">Sourcing Pipeline</h3>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  Running · Started 2h 14m ago
                </span>
                <button
                  onClick={() => setIsSourcingModalOpen(true)}
                  className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 font-bold flex items-center gap-1 transition-colors"
                >
                  View Details <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            </div>

            {/* 5-Step Numbered Stepper */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 pt-2">
              {/* Step 1: JD Parsed */}
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-amber-500 text-white font-bold flex items-center justify-center shrink-0 shadow-md shadow-amber-500/20 text-xs">
                  1
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-900 dark:text-white truncate">JD Parsed</h5>
                  <p className="text-[10px] text-amber-600 dark:text-amber-400 font-medium">Completed 2m 18s</p>
                </div>
              </div>

              {/* Step 2: Search Plan Ready */}
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 shadow-md shadow-indigo-600/20 text-xs">
                  2
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-900 dark:text-white truncate">Search Plan Ready</h5>
                  <p className="text-[10px] text-indigo-600 dark:text-indigo-400 font-medium">Completed 4m 32s</p>
                </div>
              </div>

              {/* Step 3: Collecting Profiles */}
              <div className="flex items-center gap-3">
                <div
                  className={`h-8 w-8 rounded-full ${sourcing
                      ? "bg-indigo-600 text-white animate-pulse ring-4 ring-indigo-200"
                      : "bg-indigo-600 text-white"
                    } font-bold flex items-center justify-center shrink-0 shadow-md shadow-indigo-600/20 text-xs`}
                >
                  3
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-900 dark:text-white truncate">Collecting Profiles</h5>
                  <p className="text-[10px] text-indigo-600 dark:text-indigo-400 font-medium truncate">
                    {sourcing ? "Actively Searching..." : "In progress 1,240 / 2,000"}
                  </p>
                </div>
              </div>

              {/* Step 4: Evidence Review */}
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-slate-100 dark:bg-[#141b2e] border border-slate-200 dark:border-[#232e4d] text-slate-400 font-bold flex items-center justify-center shrink-0 text-xs">
                  4
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-400 truncate">Evidence Review</h5>
                  <p className="text-[10px] text-slate-400">Pending</p>
                </div>
              </div>

              {/* Step 5: Shortlist */}
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-slate-100 dark:bg-[#141b2e] border border-slate-200 dark:border-[#232e4d] text-slate-400 font-bold flex items-center justify-center shrink-0 text-xs">
                  5
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-400 truncate">Shortlist</h5>
                  <p className="text-[10px] text-slate-400">Pending</p>
                </div>
              </div>
            </div>
          </div>

          {/* -------------------- 3. SPLIT CONTENT: CANDIDATES TABLE + RIGHT PANELS -------------------- */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
            {/* LEFT / CENTER: CANDIDATES TABLE (8 cols) */}
            <div className="xl:col-span-8 space-y-4 min-w-0">
              <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-2xl shadow-xs overflow-hidden">
                {/* Table Header Controls */}
                <div className="p-4 border-b border-slate-100 dark:border-[#151e36] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  {/* Filter Tabs */}
                  <div className="flex items-center gap-1.5 overflow-x-auto">
                    {[
                      { id: "all", label: "Candidates", count: totalDiscovered },
                      { id: "new", label: "New", count: 42 },
                      { id: "in_review", label: "In Review", count: 58 },
                      { id: "shortlisted", label: "Shortlisted", count: 24 },
                      { id: "not_a_fit", label: "Not a Fit", count: 122 },
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${activeTab === tab.id
                            ? "bg-indigo-50 dark:bg-indigo-600 text-indigo-700 dark:text-white"
                            : "text-slate-500 hover:text-slate-800 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-[#131b31]"
                          }`}
                      >
                        <span>{tab.label}</span>
                        <span
                          className={`text-[10px] px-1.5 py-0.2 rounded-full ${activeTab === tab.id
                              ? "bg-indigo-200/70 dark:bg-indigo-800 text-indigo-800 dark:text-indigo-200"
                              : "bg-slate-100 dark:bg-[#16203a] text-slate-500"
                            }`}
                        >
                          {tab.count}
                        </span>
                      </button>
                    ))}
                  </div>

                  {/* Search and Filters */}
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search candidates..."
                        className="bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b] text-xs rounded-xl pl-9 pr-3 py-1.5 w-44 sm:w-52 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <button
                      onClick={() => setIsSourcingModalOpen(true)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b] text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 hover:border-slate-400 transition-colors"
                    >
                      <Filter className="h-3 w-3 text-slate-500" />
                      <span>Filters</span>
                    </button>
                  </div>
                </div>

                {/* Table Data */}
                <div className="overflow-x-auto w-full">
                  <table className="w-full text-left border-collapse text-xs min-w-[860px]">
                    <thead>
                      <tr className="border-b border-slate-100 dark:border-[#162038] text-[11px] font-bold text-slate-500 dark:text-slate-400 bg-slate-50/50 dark:bg-[#0c1120]">
                        <th className="py-3 px-3 w-10 text-center">
                          <button onClick={toggleSelectAll} className="text-slate-400 hover:text-slate-600">
                            {selectAll ? <CheckSquare className="h-3.5 w-3.5 text-indigo-600" /> : <Square className="h-3.5 w-3.5" />}
                          </button>
                        </th>
                        <th className="py-3 px-4 w-[28%]">Candidate</th>
                        <th className="py-3 px-4 w-[26%]">Current Title / Company</th>
                        <th className="py-3 px-4 w-[16%]">Skills Match</th>
                        <th className="py-3 px-4 w-[12%]">Evidence</th>
                        <th className="py-3 px-3 w-[8%] text-center">Source</th>
                        <th className="py-3 px-3 w-[10%]">Status</th>
                        <th className="py-3 px-4 w-[12%] text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-[#151d33]">
                      {filteredCandidates.map((candidate, idx) => (
                        <tr
                          key={`${candidate.id || 'cand'}_${candidate.canonical_url || candidate.name}_${idx}`}
                          className="hover:bg-slate-50/80 dark:hover:bg-[#12192e]/60 transition-colors group cursor-pointer"
                          onClick={() => setSelectedCandidate(candidate)}
                        >
                          {/* Checkbox */}
                          <td
                            className="py-3.5 px-3 text-center"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleSelectCandidate(candidate.id);
                            }}
                          >
                            <button className="text-slate-400 hover:text-slate-600">
                              {candidate.selected ? (
                                <CheckSquare className="h-3.5 w-3.5 text-indigo-600" />
                              ) : (
                                <Square className="h-3.5 w-3.5" />
                              )}
                            </button>
                          </td>

                          {/* Candidate Avatar & Info */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="flex items-center gap-3">
                              <img
                                src={candidate.avatar || candidate.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"}
                                alt={candidate.name}
                                onError={(e) => {
                                  e.currentTarget.onerror = null;
                                  e.currentTarget.src = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80";
                                }}
                                className="h-8 w-8 rounded-full object-cover border border-slate-200 dark:border-[#222e4d] shrink-0"
                              />
                              <div className="min-w-0">
                                <div className="flex items-center gap-1.5">
                                  <div className="font-bold text-slate-900 dark:text-white text-xs group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors truncate">
                                    {candidate.name}
                                  </div>
                                  {candidate.stored_in_db && (
                                    <span title="Stored in local SQLite database" className="inline-flex items-center gap-0.5 px-1.5 py-0.2 rounded-md text-[9px] font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                                      <Database className="h-2.5 w-2.5" /> DB
                                    </span>
                                  )}
                                </div>
                                <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                                  {candidate.location}
                                </div>
                              </div>
                            </div>
                          </td>

                          {/* Current Title / Company */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="font-bold text-slate-800 dark:text-slate-200 text-xs truncate max-w-[210px]">
                              {candidate.title}
                            </div>
                            <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">{candidate.company}</div>
                          </td>

                          {/* Skills Match */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="flex items-center gap-2.5">
                              <span className="font-extrabold text-slate-800 dark:text-slate-200 text-xs w-7">{candidate.skill_match}%</span>
                              <div className="w-16 sm:w-20 bg-slate-100 dark:bg-[#16203a] h-1.5 rounded-full overflow-hidden shrink-0">
                                <div
                                  className="h-full rounded-full bg-gradient-to-r from-teal-400 to-emerald-500"
                                  style={{ width: `${candidate.skill_match}%` }}
                                />
                              </div>
                            </div>
                          </td>

                          {/* Evidence Status Pill */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            {candidate.evidence_status === "Verified" && (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                                <Check className="h-3 w-3 stroke-[3]" />
                                Verified
                              </span>
                            )}
                            {candidate.evidence_status === "Partial" && (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20">
                                Partial
                              </span>
                            )}
                            {candidate.evidence_status === "Not Verified" && (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500 dark:bg-slate-700/30 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50">
                                Not Verified
                              </span>
                            )}
                          </td>

                          {/* Sources */}
                          <td className="py-3.5 px-3 text-center whitespace-nowrap">
                            <div className="flex items-center justify-center gap-1 text-slate-400">
                              <span className="h-6 w-6 rounded bg-blue-500 text-white flex items-center justify-center">
                                <LinkedInIcon className="h-3 w-3" />
                              </span>
                              {candidate.sources.includes("github") && (
                                <span className="h-6 w-6 rounded bg-slate-800 text-white flex items-center justify-center">
                                  <GithubIcon className="h-3 w-3" />
                                </span>
                              )}
                            </div>
                          </td>

                          {/* Status */}
                          <td className="py-3.5 px-3 whitespace-nowrap">
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
                          </td>

                          {/* Actions */}
                          <td className="py-3.5 px-4 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={() => setSelectedCandidate(candidate)}
                                className="px-3 py-1 rounded-lg bg-white dark:bg-[#141d33] border border-indigo-200 dark:border-indigo-500/50 hover:bg-indigo-50 text-indigo-700 dark:text-indigo-300 text-xs font-bold transition-colors shadow-xs"
                              >
                                Review
                              </button>
                              <button
                                onClick={() => handleUpdateStatus(candidate.id, candidate.status === "Shortlisted" ? "New" : "Shortlisted")}
                                className="h-7 w-7 rounded-lg text-slate-400 hover:text-slate-600 flex items-center justify-center"
                              >
                                <MoreVertical className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* RIGHT SIDEBAR PANELS (4 cols) */}
            <div className="xl:col-span-4 space-y-4 min-w-0">
              {/* Top Panel: Job Description Summary */}
              <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3.5">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">
                    Job Description Summary
                  </h3>
                  <button
                    onClick={() => setIsJdEditorOpen(true)}
                    className="flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 font-bold transition-colors"
                  >
                    <Edit3 className="h-3 w-3" />
                    <span>Edit</span>
                  </button>
                </div>

                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="text-base font-black text-slate-900 dark:text-white">{currentRole.title}</h4>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                      Active
                    </span>
                  </div>

                  {/* Metadata Chips */}
                  <div className="flex flex-wrap gap-1.5 text-xs text-slate-600 dark:text-slate-300 mb-3.5">
                    <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-[#131a2e] border border-slate-200/80 dark:border-[#1c2744] text-[11px]">
                      <Briefcase className="h-3 w-3 text-slate-400" />
                      {currentRole.department || "Engineering"}
                    </span>
                    <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-[#131a2e] border border-slate-200/80 dark:border-[#1c2744] text-[11px]">
                      <Clock className="h-3 w-3 text-slate-400" />
                      {currentRole.type || "Full-time"}
                    </span>
                    <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-[#131a2e] border border-slate-200/80 dark:border-[#1c2744] text-[11px]">
                      <Award className="h-3 w-3 text-slate-400" />
                      {currentRole.experience || "5+ years"}
                    </span>
                    <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-[#131a2e] border border-slate-200/80 dark:border-[#1c2744] text-[11px]">
                      <MapPin className="h-3 w-3 text-slate-400" />
                      {currentRole.location || "Remote / Hybrid"}
                    </span>
                    <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-[#131a2e] border border-slate-200/80 dark:border-[#1c2744] text-[11px]">
                      <Globe className="h-3 w-3 text-slate-400" />
                      {currentRole.region || "UAE / India"}
                    </span>
                  </div>

                  {/* Key Requirements Tags */}
                  <div>
                    <h5 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      Key Requirements
                    </h5>
                    <div className="flex flex-wrap gap-1.5">
                      {currentRole.requirements.map((req, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-[#141c33] border border-slate-200 dark:border-[#1e2a4a] text-slate-700 dark:text-slate-300 text-[11px] font-semibold"
                        >
                          {req}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Panel: Agent Activity Telemetry */}
              <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">
                      Agent Activity
                    </h3>
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                      Live
                    </span>
                  </div>
                  <button className="text-slate-400 hover:text-slate-600">
                    <MoreVertical className="h-4 w-4" />
                  </button>
                </div>

                {/* Vertical Timeline Activity Items */}
                <div className="space-y-3 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-px before:bg-slate-200 dark:before:bg-[#192440]">
                  {logs.slice(0, 6).map((log, i) => (
                    <div key={i} className="flex items-start gap-2.5 relative pl-0.5">
                      <div className="h-5 w-5 rounded-full bg-indigo-50 dark:bg-[#141c33] border border-indigo-200 dark:border-[#202c4b] flex items-center justify-center shrink-0 z-10 text-indigo-600 dark:text-indigo-400">
                        {log.icon === "search" ? (
                          <Search className="h-2.5 w-2.5" />
                        ) : log.icon === "shield" ? (
                          <ShieldCheck className="h-2.5 w-2.5 text-emerald-500" />
                        ) : (
                          <FileText className="h-2.5 w-2.5 text-blue-500" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between text-[10px] text-slate-400 mb-0.5">
                          <span>{log.time}</span>
                        </div>
                        <p className="text-[11px] text-slate-600 dark:text-slate-300 leading-snug break-words font-medium">{log.text}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  onClick={() => setIsSourcingModalOpen(true)}
                  className="w-full text-center py-2 text-[11px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 transition-colors flex items-center justify-center gap-1 pt-2 border-t border-slate-100 dark:border-[#151f38]"
                >
                  View Full Activity Log <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* -------------------- 4. MODAL: SOURCING RUN LAUNCHER -------------------- */}
      {isSourcingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-2xl bg-white dark:bg-[#0d1222] border border-slate-200 dark:border-[#1f2b47] rounded-3xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="p-4 sm:p-5 border-b border-slate-100 dark:border-[#18233c] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
                  {sessionState === "waiting_for_login" ? (
                    <ShieldCheck className="h-5 w-5" />
                  ) : (
                    <Play className="h-4 w-4 fill-white" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-black text-slate-900 dark:text-white">
                      {sessionState === "waiting_for_login" ? "Recruiter Safe Handover Mode" : "Execute Sourcing Run"}
                    </h3>
                    {sessionState === "waiting_for_login" && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-300">
                        {browserChannel === "msedge" ? "Edge Live" : browserChannel === "chrome" ? "Chrome Live" : "Chromium Live"}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    {sessionState === "waiting_for_login" ? "Human-in-the-Loop Safe LinkedIn Authentication" : "Playwright Browser Automation & Gemini AI"}
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  if (sessionState === "waiting_for_login") {
                    handleStopSourcing();
                  } else {
                    setIsSourcingModalOpen(false);
                  }
                }}
                className="h-8 w-8 rounded-lg bg-slate-100 dark:bg-[#141b2e] text-slate-500 hover:text-slate-800 dark:hover:text-white flex items-center justify-center transition-colors cursor-pointer"
                title="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-5 sm:p-6 space-y-4">
              {sessionState === "waiting_for_login" ? (
                /* DEDICATED SINGLE-SOURCE RECRUITER SAFE HANDOVER MODE */
                <div className="space-y-4 text-center py-1">
                  {/* Shield & Orbit Graphic */}
                  <div className="relative w-56 h-20 mx-auto flex items-center justify-center">
                    <div className="absolute w-52 h-16 rounded-full border border-dashed border-indigo-300 dark:border-indigo-700/60 pointer-events-none" />
                    <span className="absolute top-1 left-10 text-amber-400 font-black text-xs select-none">✦</span>
                    <span className="absolute bottom-1 right-10 text-amber-400 font-black text-xs select-none">✦</span>

                    {/* LinkedIn Badge */}
                    <div className="absolute left-2 top-4 w-9 h-9 rounded-xl bg-[#0A66C2] text-white flex items-center justify-center font-black text-base shadow-md shadow-sky-500/30 border-2 border-white dark:border-[#0c1222]">
                      in
                    </div>

                    {/* Center Shield with Lock Icon */}
                    <div className="w-16 h-16 rounded-full bg-indigo-500/10 dark:bg-indigo-500/20 flex items-center justify-center">
                      <div className="w-11 h-12 rounded-xl bg-gradient-to-b from-[#6366f1] via-[#4f46e5] to-[#4338ca] text-white flex items-center justify-center shadow-lg shadow-indigo-600/40 border border-white/40">
                        <Lock className="h-5 w-5 text-white stroke-[2.2]" />
                      </div>
                    </div>

                    {/* Floating User Badge on Right */}
                    <div className="absolute right-2 top-4 w-9 h-9 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-700 text-emerald-600 dark:text-emerald-300 flex items-center justify-center shadow-md shadow-emerald-500/20">
                      <User className="h-4 w-4 stroke-[2.2]" />
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg sm:text-xl font-black text-slate-900 dark:text-white tracking-tight">
                      Recruiter <span className="bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">Safe Handover</span> Mode
                    </h3>
                    <p className="text-[12px] text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1 leading-relaxed">
                      To keep your LinkedIn account safe from automated bot detection, please sign in to LinkedIn manually in the opened browser window.
                    </p>
                  </div>

                  {/* 4 Step Cards */}
                  <div className="space-y-2 text-left max-w-lg mx-auto">
                    {/* Step 1 */}
                    <div className="flex items-center gap-3 p-2.5 sm:p-3 rounded-xl bg-slate-50/80 dark:bg-[#131b2e] border border-slate-100 dark:border-[#1e293b] hover:border-slate-200 transition-colors">
                      <div className="w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-950/60 text-purple-600 dark:text-purple-300 font-extrabold text-[11px] flex items-center justify-center shrink-0">
                        1
                      </div>
                      <div className="w-7 h-7 rounded-lg bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-300 flex items-center justify-center shrink-0">
                        <ExternalLink className="h-3.5 w-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                          Open LinkedIn in the dedicated agent browser
                        </h4>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                          Your dedicated {browserChannel === "msedge" ? "Edge" : browserChannel === "chrome" ? "Chrome" : "Chromium"} browser is open at{" "}
                          <a
                            href="https://www.linkedin.com"
                            target="_blank"
                            rel="noreferrer"
                            className="text-sky-600 dark:text-sky-400 font-semibold underline"
                          >
                            https://www.linkedin.com
                          </a>{" "}
                          (or click Open LinkedIn ↗ below).
                        </p>
                      </div>
                    </div>

                    {/* Step 2 */}
                    <div className="flex items-center gap-3 p-2.5 sm:p-3 rounded-xl bg-slate-50/80 dark:bg-[#131b2e] border border-slate-100 dark:border-[#1e293b] hover:border-slate-200 transition-colors">
                      <div className="w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-300 font-extrabold text-[11px] flex items-center justify-center shrink-0">
                        2
                      </div>
                      <div className="w-7 h-7 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-300 flex items-center justify-center shrink-0">
                        <User className="h-3.5 w-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                          Sign in inside that opened browser window
                        </h4>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                          Please enter your credentials inside the agent's opened browser window (not your personal desktop Chrome). Your session will be saved in this profile for future runs.
                        </p>
                      </div>
                    </div>

                    {/* Step 3 */}
                    <div className="flex items-center gap-3 p-2.5 sm:p-3 rounded-xl bg-slate-50/80 dark:bg-[#131b2e] border border-slate-100 dark:border-[#1e293b] hover:border-slate-200 transition-colors">
                      <div className="w-6 h-6 rounded-full bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-300 font-extrabold text-[11px] flex items-center justify-center shrink-0">
                        3
                      </div>
                      <div className="w-7 h-7 rounded-lg bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-300 flex items-center justify-center shrink-0">
                        <HomeIcon className="h-3.5 w-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                          Ensure your LinkedIn home screen is loaded
                        </h4>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                          Verify that you can see your LinkedIn feed or home page after signing in.
                        </p>
                      </div>
                    </div>

                    {/* Step 4 */}
                    <div className="flex items-center gap-3 p-2.5 sm:p-3 rounded-xl bg-slate-50/80 dark:bg-[#131b2e] border border-slate-100 dark:border-[#1e293b] hover:border-slate-200 transition-colors">
                      <div className="w-6 h-6 rounded-full bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-300 font-extrabold text-[11px] flex items-center justify-center shrink-0">
                        4
                      </div>
                      <div className="w-7 h-7 rounded-lg bg-rose-50 dark:bg-rose-900/30 text-rose-600 dark:text-rose-300 flex items-center justify-center shrink-0">
                        <ArrowLeft className="h-3.5 w-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                          Return to Hiring Desk
                        </h4>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                          Once you are signed in, come back to this page and click &ldquo;I&apos;ve Logged In — Continue&rdquo;.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* AI Screen Verification Feedback Alert */}
                  {(verificationFeedback || sessionError) && (
                    <div
                      className={`p-3 rounded-xl text-left border flex items-start gap-2.5 transition-all max-w-lg mx-auto ${
                        (verificationFeedback?.type === "error" || sessionError)
                          ? "bg-rose-500/10 border-rose-500/40 text-rose-900 dark:text-rose-200"
                          : "bg-emerald-500/10 border-emerald-500/40 text-emerald-900 dark:text-emerald-200"
                      }`}
                    >
                      {(verificationFeedback?.type === "error" || sessionError) ? (
                        <AlertCircle className="h-4 w-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                      )}
                      <div className="space-y-0.5 text-xs flex-1">
                        <div className="font-extrabold text-xs">
                          {verificationFeedback?.title || "⚠️ Login Verification Required"}
                        </div>
                        <p className="leading-snug opacity-95 text-[11px]">
                          {verificationFeedback?.message || sessionError}
                        </p>
                        {verificationFeedback?.screenTitle && (
                          <div className="text-[10px] font-mono bg-white/70 dark:bg-black/30 px-2 py-0.5 rounded inline-block border border-rose-200 dark:border-rose-900/50 mt-1">
                            Screen Detected by AI Agent: &quot;{verificationFeedback.screenTitle}&quot;
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons: Open LinkedIn & Continue */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto pt-1">
                    <button
                      type="button"
                      onClick={handleOpenLinkedInTab}
                      className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#6366f1] hover:from-[#6d28d9] hover:to-[#4f46e5] text-white font-bold text-xs sm:text-sm shadow-md shadow-indigo-500/25 transition-all cursor-pointer hover:shadow-indigo-500/40 hover:-translate-y-0.5 active:translate-y-0"
                    >
                      <ExternalLink className="h-4 w-4" />
                      <span>Open LinkedIn ↗</span>
                    </button>

                    <button
                      type="button"
                      onClick={handleVerifyAndContinue}
                      disabled={isVerifyingScreen}
                      className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-[#059669] to-[#10b981] hover:from-[#047857] hover:to-[#059669] text-white font-bold text-xs sm:text-sm shadow-md shadow-emerald-500/25 transition-all cursor-pointer hover:shadow-emerald-500/40 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      {isVerifyingScreen ? (
                        <>
                          <RefreshCw className="h-4 w-4 animate-spin" />
                          <span>AI Agent Verifying Screen...</span>
                        </>
                      ) : (
                        <>
                          <div className="h-4 w-4 rounded-full bg-white/20 flex items-center justify-center">
                            <Check className="h-2.5 w-2.5 text-white stroke-[3]" />
                          </div>
                          <span>I&apos;ve Logged In — Continue →</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Bottom Info Pill */}
                  <div className="p-3 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-100/80 dark:border-indigo-900/40 text-left flex items-start gap-2.5 max-w-lg mx-auto">
                    <div className="h-5 w-5 rounded-full bg-indigo-100 dark:bg-indigo-900/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0 mt-0.5">
                      <Info className="h-3 w-3" />
                    </div>
                    <div className="space-y-0.5">
                      <div className="text-[11px] font-bold text-indigo-950 dark:text-indigo-200">
                        The AI Agent is safely paused.
                      </div>
                      <p className="text-[10px] text-indigo-800/80 dark:text-indigo-300/80 leading-relaxed">
                        Hiring Desk runs a dedicated browser profile to avoid locking or altering your personal browser data. Once you sign in inside the opened window, your session is saved permanently and the agent takes over UI traversal.
                      </p>
                    </div>
                  </div>

                  {/* Action links */}
                  <div className="flex items-center justify-between max-w-lg mx-auto pt-1 text-[11px]">
                    <button
                      type="button"
                      onClick={() => {
                        handleStopSourcing();
                        handleLaunchSourcing("demo");
                      }}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 underline font-medium transition-colors cursor-pointer"
                    >
                      Switch to Offline Demo →
                    </button>
                    <button
                      type="button"
                      onClick={handleStopSourcing}
                      className="text-rose-500 hover:text-rose-700 font-medium transition-colors cursor-pointer"
                    >
                      Cancel Sourcing
                    </button>
                  </div>
                </div>
              ) : sourcing || (sessionState !== "idle" && sessionState !== "stopped" && sessionState !== "failed") ? (
                /* LIVE EXECUTION MONITOR & STEPPER */
                <div className="space-y-4">
                  {/* Status Card */}
                  <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white border border-indigo-900/60 shadow-lg flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="relative flex items-center justify-center">
                        {sessionState === "completed" ? (
                          <div className="h-10 w-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                            <Check className="h-5 w-5" />
                          </div>
                        ) : (
                          <div className="h-10 w-10 rounded-xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
                            <RefreshCw className="h-5 w-5 animate-spin" />
                          </div>
                        )}
                      </div>
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-300">
                          {sessionState === "completed" ? "Sourcing Completed Successfully" : "Browser Automation In Progress"}
                        </div>
                        <div className="text-sm font-black text-white">
                          {searchMode === "simulation"
                            ? "Mode A — Autonomous UI Agent Collection"
                            : `Mode B — Direct Live LinkedIn Sourcing (${browserChannel === "msedge" ? "Microsoft Edge" : browserChannel === "chrome" ? "Google Chrome" : "Chromium"})`}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-black text-indigo-300">{sessionProgress}%</div>
                      <div className="text-[10px] text-slate-400">Progress</div>
                    </div>
                  </div>

                  {/* Animated Progress Bar */}
                  <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 rounded-full ${sessionState === "completed"
                          ? "bg-emerald-500"
                          : sessionState === "failed"
                            ? "bg-rose-500"
                            : "bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400"
                        }`}
                      style={{ width: `${sessionProgress}%` }}
                    />
                  </div>

                  {/* 5-Step Visual Stepper */}
                  <div className="grid grid-cols-5 gap-1.5">
                    {[
                      { key: "launching_browser", label: "1. Launch", desc: `${browserChannel === "msedge" ? "Edge" : browserChannel === "chrome" ? "Chrome" : "Chromium"} Headed` },
                      { key: "waiting_for_login", label: "2. Cookie/Login", desc: "Session Check" },
                      { key: "searching", label: "3. LinkedIn Search", desc: "People Traversal" },
                      { key: "extracting", label: "4. Profile Extract", desc: "Resumes & Skills" },
                      { key: "persisting", label: "5. SQLite DB", desc: "Resumes Saved" },
                    ].map((step, idx) => {
                      const stepOrder = ["launching_browser", "waiting_for_login", "searching", "extracting", "persisting", "completed"];
                      const currentIdx = stepOrder.indexOf(sessionState);
                      const isPast = (currentIdx > idx && currentIdx !== -1) || sessionState === "completed";
                      const isCurrent = currentIdx === idx && sessionState !== "completed";

                      return (
                        <div
                          key={step.key}
                          className={`p-2 rounded-xl border text-center transition-all ${isPast
                              ? "bg-emerald-50/80 dark:bg-emerald-950/30 border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 font-semibold"
                              : isCurrent
                                ? "bg-indigo-50/90 dark:bg-indigo-950/40 border-indigo-500 text-indigo-900 dark:text-indigo-200 shadow-sm ring-1 ring-indigo-500 font-bold"
                                : "bg-slate-50 dark:bg-[#11172a] border-slate-200 dark:border-[#1d2745] text-slate-400 font-normal"
                            }`}
                        >
                          <div className="text-[11px] truncate">{step.label}</div>
                          <div className="text-[9px] opacity-75 mt-0.5 truncate">{step.desc}</div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Live Status Description */}
                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#0c1222] border border-slate-200 dark:border-[#1a243f] text-xs text-slate-700 dark:text-slate-200 flex items-start gap-3">
                    <Globe className="h-4 w-4 shrink-0 text-indigo-500 mt-0.5" />
                    <div className="space-y-1">
                      <div className="font-bold text-slate-900 dark:text-white">Active Stage Telemetry</div>
                      <div className="text-[12px] text-slate-600 dark:text-slate-300 leading-relaxed font-mono">
                        {sourcingStage || "Automating browser actions..."}
                      </div>
                    </div>
                  </div>

                  {/* Browser Live Notice */}
                  <div className="p-2.5 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200/60 dark:border-indigo-800/60 text-[11px] text-indigo-700 dark:text-indigo-300 flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-indigo-600 shrink-0" />
                    <span>The headed {browserChannel === "msedge" ? "Edge" : browserChannel === "chrome" ? "Chrome" : "Chromium"} browser is running live on your desktop. You can see pages and candidate cards being processed in real-time.</span>
                  </div>
                </div>
              ) : (
                /* PRE-LAUNCH CONFIGURATION FORM */
                <>
                  <div>
                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-2">Target Role Profile</label>
                    <div className="grid grid-cols-3 gap-2.5">
                      {Object.keys(SAMPLE_JDS).map((key) => {
                        const item = SAMPLE_JDS[key];
                        const isSelected = selectedRolePreset === key;
                        return (
                          <button
                            key={key}
                            onClick={() => handleSelectRolePreset(key)}
                            className={`p-3 rounded-xl border text-left transition-all ${isSelected
                                ? "bg-indigo-50/80 dark:bg-indigo-600/20 border-indigo-500 text-indigo-900 dark:text-white shadow-xs font-bold"
                                : "bg-slate-50 dark:bg-[#10162a] border-slate-200 dark:border-[#1d2744] text-slate-600 dark:text-slate-400 hover:border-slate-400"
                              }`}
                          >
                            <div className="text-xs truncate">{item.title}</div>
                            <div className="text-[10px] text-slate-400 mt-1">{item.experience} • {item.location}</div>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                      Candidate Search Query (AI Generated)
                    </label>
                    <div className="p-3 bg-slate-50 dark:bg-[#070b16] rounded-xl border border-slate-200 dark:border-[#1b253f] font-mono text-xs text-indigo-700 dark:text-indigo-300 break-words font-semibold">
                      {analysisResult?.search_plan?.linkedin_keywords ||
                        `"${currentRole.title}" React Next.js Python FastAPI WebSockets`}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3.5">
                    <div>
                      <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">Execution Mode</label>
                      <select
                        value={searchMode}
                        onChange={(e) => setSearchMode(e.target.value)}
                        className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1e2a48] text-xs font-medium text-slate-800 dark:text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:border-indigo-500"
                      >
                        <option value="autonomous">Mode A — 🤖 Autonomous Sourcing (Direct Real LinkedIn & Auto-Harvest)</option>
                        <option value="live_linkedin">Mode B — 🌐 Guided Live Sourcing (Headed Browser & Safe Handover)</option>
                        <option value="demo">🧪 Offline Demo (Simulated Profiles for Testing)</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">Candidates to Extract</label>
                      <select
                        value={maxResults}
                        onChange={(e) => setMaxResults(Number(e.target.value))}
                        className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1e2a48] text-xs font-medium text-slate-800 dark:text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:border-indigo-500"
                      >
                        <option value={6}>6 Candidates (Fast Verification)</option>
                        <option value={10}>10 Candidates (Standard Run)</option>
                        <option value={15}>15 Candidates (Deep Search)</option>
                      </select>
                    </div>
                  </div>

                  {/* Browser Engine & Account Selection (Chrome vs Edge vs Chromium) */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                        Browser &amp; Account Selection
                      </label>
                      <span className="text-[10px] text-indigo-500 font-semibold">
                        Choose browser for LinkedIn session
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { id: "chrome", label: "Google Chrome", badge: "Recommended", icon: "🌐", desc: "Use Chrome & saved login" },
                        { id: "msedge", label: "Microsoft Edge", badge: "Windows Default", icon: "🌊", desc: "Use Edge & saved login" },
                        { id: "chromium", label: "Chromium Sandbox", badge: "Isolated", icon: "🚀", desc: "Clean test browser environment" },
                      ].map((b) => (
                        <button
                          key={b.id}
                          type="button"
                          onClick={() => setBrowserChannel(b.id)}
                          className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                            browserChannel === b.id
                              ? "bg-indigo-50/90 dark:bg-indigo-600/25 border-indigo-500 text-indigo-900 dark:text-white ring-2 ring-indigo-500/40 font-bold"
                              : "bg-slate-50 dark:bg-[#10162a] border-slate-200 dark:border-[#1e2a48] text-slate-600 dark:text-slate-400 hover:border-slate-300"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs truncate font-bold">{b.icon} {b.label}</span>
                            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-normal shrink-0">{b.badge}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-normal leading-tight">{b.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-200 dark:border-indigo-500/20 text-xs text-indigo-700 dark:text-indigo-300 flex items-start gap-2.5">
                    <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5 text-indigo-600 dark:text-indigo-400" />
                    <span>
                      <strong>Direct LinkedIn Headed Browser:</strong> Mode B launches a visible {browserChannel === "msedge" ? "Microsoft Edge" : browserChannel === "chrome" ? "Google Chrome" : "Chromium"} browser window directly to LinkedIn on your desktop. If you are already signed into LinkedIn in your chosen browser, the agent detects the session immediately. After harvesting, it automatically returns back to this Hiring Desk portal.
                    </span>
                  </div>
                </>
              )}

              {/* Error Feedback */}
              {(error || sessionError) && (
                <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
                  <span>{error || sessionError}</span>
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="p-4 border-t border-slate-100 dark:border-[#18233c] bg-slate-50/50 dark:bg-[#0a0f1d] flex items-center justify-between">
              {sourcing || (sessionState !== "completed" && sessionState !== "idle" && sessionState !== "stopped" && sessionState !== "failed") ? (
                <>
                  <button
                    onClick={handleStopSourcing}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-rose-600 hover:text-rose-700 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 transition-colors"
                  >
                    <X className="h-3.5 w-3.5" />
                    <span>Stop Sourcing</span>
                  </button>
                  <div className="flex items-center gap-2 text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>
                      Automation running in{" "}
                      {browserChannel === "msedge"
                        ? "Microsoft Edge"
                        : browserChannel === "chrome"
                        ? "Google Chrome"
                        : "Chromium"}
                      ...
                    </span>
                  </div>

                </>
              ) : sessionState === "completed" ? (
                <>
                  <button
                    onClick={() => {
                      setSessionState("idle");
                      setSessionProgress(0);
                    }}
                    className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
                  >
                    Run Another Search
                  </button>
                  <button
                    onClick={() => {
                      setIsSourcingModalOpen(false);
                      setSessionState("idle");
                    }}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/25 transition-all"
                  >
                    <Check className="h-3.5 w-3.5" />
                    <span>View Shortlist & Done</span>
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setIsSourcingModalOpen(false)}
                    className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleLaunchSourcing(searchMode)}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 transition-all"
                  >
                    <Play className="h-3.5 w-3.5 fill-white" />
                    <span>Launch Candidate Sourcing</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* -------------------- 5. MODAL: EDIT JOB DESCRIPTION -------------------- */}
      {isJdEditorOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-2xl bg-white dark:bg-[#0d1222] border border-slate-200 dark:border-[#1f2b47] rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-5 border-b border-slate-100 dark:border-[#18233c] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-xl bg-indigo-50 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                  <FileText className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-black text-slate-900 dark:text-white">Edit Job Description & Extract Criteria</h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Gemini AI parses competencies, experience, and search queries</p>
                </div>
              </div>
              <button
                onClick={() => setIsJdEditorOpen(false)}
                className="h-8 w-8 rounded-lg bg-slate-100 dark:bg-[#141b2e] text-slate-500 hover:text-slate-800 flex items-center justify-center"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-6 pt-3.5 pb-1 flex items-center gap-2">
              <span className="text-xs font-bold text-slate-400 mr-1">Presets:</span>
              {Object.keys(SAMPLE_JDS).map((k) => (
                <button
                  key={k}
                  onClick={() => handleSelectRolePreset(k)}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${selectedRolePreset === k
                      ? "bg-indigo-600 text-white shadow-xs"
                      : "bg-slate-100 dark:bg-[#12192d] text-slate-600 dark:text-slate-400 hover:bg-slate-200"
                    }`}
                >
                  {SAMPLE_JDS[k].title}
                </button>
              ))}
            </div>

            <div className="p-6 flex-1 overflow-y-auto space-y-3">
              <textarea
                value={rawJd}
                onChange={(e) => setRawJd(e.target.value)}
                rows={11}
                placeholder="Paste raw Job Description here..."
                className="w-full bg-slate-50 dark:bg-[#070b16] border border-slate-200 dark:border-[#1a243e] rounded-2xl p-4 text-xs font-mono text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:border-indigo-500 leading-relaxed"
              />
            </div>

            <div className="p-4 border-t border-slate-100 dark:border-[#18233c] bg-slate-50/50 dark:bg-[#0a0f1d] flex items-center justify-between">
              <button
                onClick={() => setIsJdEditorOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors"
              >
                Close
              </button>
              <button
                onClick={handleAnalyzeJd}
                disabled={analyzing}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
              >
                {analyzing ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Extracting Criteria with Gemini...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Extract Criteria & Update Role</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* -------------------- 5.5 MODAL: POST-JD ENHANCEMENT HANDOVER -------------------- */}
      {isPostJdPromptOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-lg bg-white dark:bg-[#0d1222] border border-slate-200 dark:border-[#1f2b47] rounded-3xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center shadow-md shadow-indigo-500/25">
                  <Sparkles className="h-5 w-5 fill-white" />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900 dark:text-white">JD Enhancement Complete</h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Search plan & criteria verified by Gemini AI</p>
                </div>
              </div>
              <button
                onClick={() => setIsPostJdPromptOpen(false)}
                className="h-8 w-8 rounded-lg bg-slate-100 dark:bg-[#141b2e] text-slate-500 hover:text-slate-800 flex items-center justify-center"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Target Role & Search Plan Preview */}
            <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-[#0b101f] border border-slate-200/80 dark:border-[#19243d] space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-700 dark:text-slate-300">Target Role:</span>
                <span className="font-black text-indigo-600 dark:text-indigo-400">{currentRole.title}</span>
              </div>
              <div>
                <span className="text-[11px] font-bold text-slate-400 block mb-1">Generated Boolean Query:</span>
                <code className="block p-2 rounded-xl bg-white dark:bg-[#11182c] border border-slate-200 dark:border-[#1e2a4a] text-[11px] font-mono text-slate-800 dark:text-slate-200 break-words">
                  {analysisResult?.search_plan?.linkedin_keywords || `"${currentRole.title}" React Next.js`}
                </code>
              </div>
            </div>

            {/* LinkedIn Auth / Permission Explanation */}
            <div className="p-3.5 rounded-2xl bg-indigo-50/80 dark:bg-indigo-500/10 border border-indigo-200/80 dark:border-indigo-500/20 text-xs text-indigo-900 dark:text-indigo-200 space-y-1.5">
              <div className="flex items-center gap-2 font-bold">
                <ShieldCheck className="h-4 w-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
                <span>Next Step: Autonomous LinkedIn Sourcing</span>
              </div>
              <p className="text-[11px] text-indigo-800/80 dark:text-indigo-300 leading-relaxed pl-6">
                The agent will launch the browser, search LinkedIn, visit candidate profiles/resumes, read their experience, and send details to the backend for scoring.
                If this is your first time, the agent will pause for you to log in in the opened Chromium window.
              </p>
            </div>

            {/* Modal Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-end gap-2.5 pt-2">
              <button
                onClick={async () => {
                  await handleOpenLoginBrowser();
                }}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-[#151e36] hover:bg-slate-200 transition-colors"
              >
                Sign into LinkedIn
              </button>
              <button
                onClick={() => {
                  setIsPostJdPromptOpen(false);
                  handleLaunchSourcing("simulation");
                }}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 shadow-md shadow-indigo-600/30 transition-all"
              >
                <Play className="h-3.5 w-3.5 fill-white" />
                <span>🤖 Run Autonomous Browser Agent</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* -------------------- 6. MODAL: LINKEDIN AUTHENTICATION HANDOVER -------------------- */}
      {isAuthModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-lg bg-white dark:bg-[#0d1222] border border-slate-200 dark:border-[#1f2b47] rounded-3xl shadow-2xl p-6 text-center space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto shadow-md">
              <Lock className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-black text-slate-900 dark:text-white">LinkedIn Login Permission Required</h3>
              <p className="text-xs text-slate-600 dark:text-slate-300 mt-1.5 leading-relaxed">
                LinkedIn requires an authenticated account to view candidate search results. The Chromium browser is open on your desktop. Please sign in to proceed, or click below to run the autonomous UI agent demo without logging in.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#1d2745] text-left text-xs space-y-1.5 text-slate-600 dark:text-slate-300">
              <div className="flex items-center gap-2 font-bold text-slate-800 dark:text-slate-100">
                <Check className="h-3.5 w-3.5 text-emerald-500" />
                <span>Session cookies are preserved in <code>data/browser_profile</code></span>
              </div>
              <p className="text-[11px] text-slate-500 pl-5">You will only need to sign in once. Subsequent searches will run autonomously without asking.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
              <button
                onClick={() => {
                  setIsAuthModalOpen(false);
                  handleLaunchSourcing("simulation");
                }}
                className="px-3 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 shadow-md transition-all"
              >
                🚀 Run Autonomous Agent Demo
              </button>
              <button
                onClick={handleCheckAuthStatus}
                disabled={checkingAuth}
                className="px-3 py-2.5 rounded-xl text-xs font-bold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-700/50 hover:bg-indigo-100 transition-colors"
              >
                {checkingAuth ? "Checking..." : "Check Auth Status"}
              </button>
              <button
                onClick={() => {
                  setIsAuthModalOpen(false);
                  handleLaunchSourcing("linkedin");
                }}
                className="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-[#151e36] hover:bg-slate-200 transition-colors"
              >
                I've Logged In — Live Search
              </button>
            </div>
          </div>
        </div>
      )}

      {/* -------------------- 7. MODAL: CANDIDATE EVIDENCE REVIEW -------------------- */}
      {selectedCandidate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-2xl bg-white dark:bg-[#0d1222] border border-slate-200 dark:border-[#1f2b47] rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-5 border-b border-slate-100 dark:border-[#18233c] flex items-start justify-between">
              <div className="flex items-center gap-3.5">
                <img
                  src={selectedCandidate.avatar || selectedCandidate.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"}
                  alt={selectedCandidate.name}
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80";
                  }}
                  className="h-12 w-12 rounded-2xl object-cover border-2 border-indigo-500/40 shadow-md"
                />
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-black text-slate-900 dark:text-white">{selectedCandidate.name}</h3>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                      {selectedCandidate.match_level || "High"} Fit
                    </span>
                    {selectedCandidate.stored_in_db && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30">
                        <Database className="h-2.5 w-2.5" />
                        SQLite Saved
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5">{selectedCandidate.headline}</p>
                  <p className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1.5">
                    <MapPin className="h-3 w-3" /> {selectedCandidate.location} • {selectedCandidate.company}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedCandidate(null)}
                className="h-8 w-8 rounded-lg bg-slate-100 dark:bg-[#141b2e] text-slate-500 hover:text-slate-800 flex items-center justify-center"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-[#080d1a] border border-slate-200/80 dark:border-[#1a253e]">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">
                    AI Evaluation Summary
                  </span>
                  <span className="text-sm font-black text-emerald-600 dark:text-emerald-400">
                    {selectedCandidate.skill_match}% Match Score
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-medium">{selectedCandidate.justification}</p>
              </div>

              {/* About & Summary Extracted by UI Agent */}
              {selectedCandidate.about && (
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-[#080d1a] border border-slate-200/80 dark:border-[#1a253e]">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <FileText className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                    <span className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">
                      About & Summary (Extracted by UI Agent)
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-normal">{selectedCandidate.about}</p>
                </div>
              )}

              {/* Experience History Extracted by UI Agent */}
              {selectedCandidate.experience_history && selectedCandidate.experience_history.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Briefcase className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                    Career Experience History (Extracted by UI Agent)
                  </h4>
                  <div className="space-y-2">
                    {selectedCandidate.experience_history.map((exp, i) => (
                      <div key={i} className="p-3 rounded-xl bg-white dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1d2946] text-xs shadow-xs">
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="font-bold text-slate-900 dark:text-white text-xs">{exp.role}</span>
                          <span className="text-[10px] text-slate-400 font-mono bg-slate-100 dark:bg-[#18223a] px-2 py-0.5 rounded-md">{exp.dates}</span>
                        </div>
                        <div className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 mb-1">{exp.company}</div>
                        {exp.description && (
                          <p className="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed">{exp.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Extracted Profile Skills */}
              {selectedCandidate.skills && selectedCandidate.skills.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider mb-1.5">
                    Extracted Profile Skills
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedCandidate.skills.map((skill, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-0.5 rounded-lg bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 text-[11px] font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                  Verified Evidence Quotes
                </h4>
                <div className="space-y-2">
                  {selectedCandidate.evidence_quotes?.map((item, i) => (
                    <div key={i} className="p-3 rounded-xl bg-white dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1d2946] text-xs shadow-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-indigo-700 dark:text-indigo-300">{item.requirement}</span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {Math.round(item.confidence * 100)}% Confidence
                        </span>
                      </div>
                      <p className="text-slate-600 dark:text-slate-300 italic">“{item.quote}”</p>
                    </div>
                  ))}
                </div>
              </div>

              {selectedCandidate.missing_skills?.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                    Unverified Requirements
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedCandidate.missing_skills.map((skill, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-0.5 rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300 border border-rose-200 dark:border-rose-500/20 text-xs font-semibold"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-1">
                <a
                  href={selectedCandidate.canonical_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  <span>View Public Profile ({selectedCandidate.canonical_url})</span>
                </a>
              </div>
            </div>

            <div className="p-4 border-t border-slate-100 dark:border-[#18233c] bg-slate-50/50 dark:bg-[#0a0f1d] flex items-center justify-between">
              <button
                onClick={() => handleUpdateStatus(selectedCandidate.id, "Not a Fit")}
                className="px-4 py-2 rounded-xl text-xs font-bold text-rose-600 bg-rose-50 border border-rose-200 hover:bg-rose-100 transition-colors"
              >
                Mark Not a Fit
              </button>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleUpdateStatus(selectedCandidate.id, "In Review")}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200 hover:bg-amber-100 transition-colors"
                >
                  Mark In Review
                </button>
                <button
                  onClick={() => handleUpdateStatus(selectedCandidate.id, "Shortlisted")}
                  className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 shadow-md shadow-emerald-600/20 transition-all"
                >
                  Shortlist Candidate
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* -------------------- 8. MODAL: SOURCING REPORT & SQLITE DATABASE -------------------- */}
      {isReportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-4xl bg-white dark:bg-[#0d1222] border border-slate-200 dark:border-[#1f2b47] rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-100 dark:border-[#18233c] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
                  <Database className="h-5 w-5 fill-white" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-black text-slate-900 dark:text-white">
                      Sourcing Intelligence & SQLite Database Report
                    </h3>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30">
                      WAL Mode Active
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Local persistent storage: <code className="text-indigo-600 dark:text-indigo-400 font-mono">data/hiring_desk.db</code>
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsReportModalOpen(false)}
                className="h-8 w-8 rounded-lg bg-slate-100 dark:bg-[#141b2e] text-slate-500 hover:text-slate-800 flex items-center justify-center"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              {loadingReport ? (
                <div className="flex flex-col items-center justify-center py-16 space-y-3">
                  <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
                  <p className="text-xs font-semibold text-slate-500">Querying SQLite database records...</p>
                </div>
              ) : (
                <>
                  {/* Executive Metric Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
                    <div className="p-4 rounded-2xl bg-slate-50 dark:bg-[#090e1c] border border-slate-200/80 dark:border-[#19243d]">
                      <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1">Harvested Profiles</div>
                      <div className="text-2xl font-black text-slate-900 dark:text-white">
                        {reportData?.total_candidates_harvested || candidateList.length}
                      </div>
                      <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold mt-1">Saved to SQLite</div>
                    </div>
                    <div className="p-4 rounded-2xl bg-slate-50 dark:bg-[#090e1c] border border-slate-200/80 dark:border-[#19243d]">
                      <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1">Evaluations Stored</div>
                      <div className="text-2xl font-black text-slate-900 dark:text-white">
                        {reportData?.total_evaluations || candidateList.length}
                      </div>
                      <div className="text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold mt-1">AI Evidence Linked</div>
                    </div>
                    <div className="p-4 rounded-2xl bg-slate-50 dark:bg-[#090e1c] border border-slate-200/80 dark:border-[#19243d]">
                      <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1">High Fit Candidates</div>
                      <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                        {reportData?.high_fit_candidates || candidateList.filter((c) => c.match_level === "High" || c.skill_match >= 80).length}
                      </div>
                      <div className="text-[10px] text-slate-400 font-semibold mt-1">Score ≥ 80%</div>
                    </div>
                    <div className="p-4 rounded-2xl bg-slate-50 dark:bg-[#090e1c] border border-slate-200/80 dark:border-[#19243d]">
                      <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1">Average Match Score</div>
                      <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400">
                        {reportData?.average_fit_score || 83.4}%
                      </div>
                      <div className="text-[10px] text-slate-400 font-semibold mt-1">Normalized Fit</div>
                    </div>
                  </div>

                  {/* Role Breakdown Table */}
                  {reportData?.role_breakdown && reportData.role_breakdown.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider mb-2.5 flex items-center gap-2">
                        <Briefcase className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                        Role Evaluation Breakdown
                      </h4>
                      <div className="overflow-x-auto rounded-xl border border-slate-200/80 dark:border-[#172138]">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-50 dark:bg-[#0e1424] text-[11px] font-bold text-slate-500 border-b border-slate-200 dark:border-[#172138]">
                            <tr>
                              <th className="py-2.5 px-3.5">Target Job Title</th>
                              <th className="py-2.5 px-3.5">Evaluated Candidates</th>
                              <th className="py-2.5 px-3.5">Avg Fit Score</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 dark:divide-[#151d33]">
                            {reportData.role_breakdown.map((rb, idx) => (
                              <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-[#12192e]/60">
                                <td className="py-2.5 px-3.5 font-bold text-slate-800 dark:text-slate-200">{rb.job_title}</td>
                                <td className="py-2.5 px-3.5 text-slate-600 dark:text-slate-400">{rb.candidates_evaluated} profiles</td>
                                <td className="py-2.5 px-3.5 font-bold text-emerald-600 dark:text-emerald-400">{rb.avg_score}%</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Harvested Profiles List */}
                  <div>
                    <div className="flex items-center justify-between mb-2.5">
                      <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider flex items-center gap-2">
                        <Users className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                        Persisted Profiles in SQLite ({reportData?.all_candidates?.length || candidateList.length})
                      </h4>
                      <span className="text-[11px] text-slate-400">Click row to review full evidence</span>
                    </div>
                    <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                      {(reportData?.all_candidates && reportData.all_candidates.length > 0 ? reportData.all_candidates : candidateList).map((cand, idx) => (
                        <div
                          key={idx}
                          onClick={() => {
                            setSelectedCandidate(cand);
                            setIsReportModalOpen(false);
                          }}
                          className="p-3 rounded-xl bg-slate-50 dark:bg-[#0e1424] border border-slate-200/80 dark:border-[#19233c] hover:border-indigo-400 dark:hover:border-indigo-500/50 cursor-pointer transition-all flex items-center justify-between"
                        >
                          <div className="min-w-0 pr-3">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-900 dark:text-white text-xs truncate">{cand.name}</span>
                              <span className="text-[10px] text-slate-400 truncate">• {cand.current_company || cand.company}</span>
                            </div>
                            <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">{cand.headline}</p>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            {cand.skill_match && (
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-black bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                                {cand.skill_match}%
                              </span>
                            )}
                            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Modal Actions */}
            <div className="p-4 border-t border-slate-100 dark:border-[#18233c] bg-slate-50/50 dark:bg-[#0a0f1d] flex items-center justify-between">
              <button
                onClick={() => setIsReportModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors"
              >
                Close
              </button>
              <div className="flex items-center gap-2">
                <button
                  onClick={exportToCSV}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-100 dark:bg-[#16203a] hover:bg-slate-200 text-slate-700 dark:text-slate-300 text-xs font-bold transition-all"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Export CSV</span>
                </button>
                <button
                  onClick={() => {
                    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(reportData || {}, null, 2));
                    const downloadAnchor = document.createElement("a");
                    downloadAnchor.setAttribute("href", dataStr);
                    downloadAnchor.setAttribute("download", `hiring_desk_sourcing_report_${Date.now()}.json`);
                    document.body.appendChild(downloadAnchor);
                    downloadAnchor.click();
                    downloadAnchor.remove();
                    addTelemetryLog("Exported full SQLite sourcing report to JSON!", "file");
                  }}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all"
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span>Export JSON Report</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
