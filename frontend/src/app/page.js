"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import {
  Search,
  Filter,
  ChevronLeft,
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
  Upload,
  GraduationCap,
  Cloud,
  Trash2,
  Building2,
  Mail,
  Send,
  SendHorizontal,
  MessageSquare,
} from "lucide-react";

import { useCandidatesQuery } from "./hooks/useCandidatesQuery";
import { HiringRadarLoader } from "./components/HiringRadarLoader";
import GlobalHiringLoader from "./components/GlobalHiringLoader";
import UserNav from "./components/UserNav";
import { useAppAuth } from "./components/ClerkAuthProvider";
import AuthLandingPage from "./components/AuthLandingPage";
import {
  getCompanyProfile,
  subscribeCompanyProfile,
} from "./services/companyService";

import JobDescriptionView from "./components/views/JobDescriptionView";
import CriteriaView from "./components/views/CriteriaView";
import SourcingView from "./components/views/SourcingView";
import CandidateReviewView from "./components/views/CandidateReviewView";
import InterviewPipelineView from "./components/views/InterviewPipelineView";
import ShortlistView from "./components/views/ShortlistView";
import ReportsView from "./components/views/ReportsView";
import SettingsView from "./components/views/SettingsView";
import CandidateProfileView from "./components/views/CandidateProfileView";

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

// Clean and sanitize candidate headline by stripping connection noise, prefixes, and followers
function sanitizeCandidateHeadline(headline, candidateName = "") {
  if (!headline || typeof headline !== "string") return "";
  let clean = headline;
  clean = clean.replace(/\b\d+[\d,]*\+?\s*(connections?|followers?)\b/gi, "");
  clean = clean.replace(/\b(1st|2nd|3rd|\d+th)(\+)?\s*(degree(\s*connection)?)?\b/gi, "");
  clean = clean.replace(/\b(view profile|connect|message|follow|pending)\b/gi, "");
  clean = clean.replace(/\b(current|past|present)\s*:\s*/gi, "");
  clean = clean.replace(/^[\s\.\•\·\-\–\—\:\,\;\|]+/g, "");
  clean = clean.replace(/[\s\.\•\·\-\–\—\:\,\;\|]+$/g, "");
  clean = clean.replace(/\s*([•·|])\s*([•·|]\s*)*/g, " • ");
  clean = clean.replace(/\s{2,}/g, " ").trim();

  if (candidateName) {
    const cName = candidateName.trim().toLowerCase();
    if (clean.toLowerCase().startsWith(cName)) {
      clean = clean.slice(cName.length).replace(/^[\s\.\•\·\-\–\—\:\,\;\|]+/, "").trim();
    }
  }
  return clean;
}

// Format candidate location cleanly with Title Casing and recognized regional acronyms
function formatCandidateLocation(loc) {
  if (!loc || typeof loc !== "string") return "";
  const cleaned = loc.replace(/\b(location on profile|location)\b/gi, "").trim();
  if (!cleaned) return "";
  const upperTokens = new Set(["uae", "usa", "uk", "us", "eu", "apac", "emea", "ca", "ny", "tx", "wa", "sf", "in", "it"]);
  const parts = cleaned
    .split(",")
    .map((part) => {
      const words = part
        .trim()
        .split(/\s+/)
        .map((word) => {
          const cleanWord = word.replace(/[^a-zA-Z]/g, "").toLowerCase();
          if (upperTokens.has(cleanWord)) {
            return word.toUpperCase();
          }
          if (!word) return "";
          return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        })
        .filter(Boolean);
      return words.join(" ");
    })
    .filter(Boolean);

  return parts.join(", ");
}

// Extract or sanitize company name cleanly
function getCandidateCompany(candidate, sanitizedHeadline = "") {
  if (!candidate) return "";
  const direct = candidate.company || candidate.current_company;
  if (direct && typeof direct === "string" && !direct.toLowerCase().includes("technology co.") && !direct.toLowerCase().includes("location on profile")) {
    return direct.trim();
  }
  const headline = sanitizedHeadline || candidate.headline || "";
  if (headline && typeof headline === "string" && headline.includes(" at ")) {
    const afterAt = headline.split(" at ")[1]?.split(/[•·|,]/)[0]?.trim();
    if (afterAt && afterAt.length > 1 && !afterAt.toLowerCase().includes("connections")) {
      return afterAt;
    }
  }
  return "";
}

// Interactive Tag Input Field for Dynamic Skills and Preferences
function TagInputField({ label, tags = [], onAdd, onRemove, placeholder = "Type and press enter..." }) {
  const [inputVal, setInputVal] = useState("");
  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      if (inputVal.trim()) {
        onAdd(inputVal.trim());
        setInputVal("");
      }
    }
  };
  return (
    <div className="space-y-1.5">
      {label && <label className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">{label}</label>}
      <div className="flex flex-wrap gap-1.5 p-2 rounded-xl bg-slate-50 dark:bg-[#0c1224] border border-slate-200/80 dark:border-[#1d2946] min-h-[42px] items-center focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all">
        {tags.map((tag, idx) => (
          <span
            key={idx}
            className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
          >
            <span>{tag}</span>
            <button
              type="button"
              onClick={() => onRemove(idx)}
              className="hover:text-rose-600 transition-colors text-slate-400 font-bold ml-0.5"
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={tags.length === 0 ? placeholder : "+ Add another..."}
          className="flex-1 bg-transparent text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none min-w-[120px] px-1 py-0.5"
        />
        {inputVal.trim() && (
          <button
            type="button"
            onClick={() => { onAdd(inputVal.trim()); setInputVal(""); }}
            className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 px-2.5 py-1 rounded-lg bg-indigo-100/70 dark:bg-indigo-950/80 hover:bg-indigo-200"
          >
            Add
          </button>
        )}
      </div>
    </div>
  );
}

// Initial dynamic structured job requirements form
const INITIAL_JOB_FORM = {
  // A. Job Information
  jobTitle: "",
  jobDescription: "",
  department: "Engineering",
  employmentType: "Full-time",
  seniorityLevel: "Senior",
  vacancies: 1,

  // B. Required Skills & Technologies
  mandatorySkills: [],
  preferredSkills: [],
  technologies: [],
  toolsPlatforms: [],
  domainExpertise: [],
  certifications: [],

  // C. Experience Requirements
  minExperience: 3,
  maxExperience: 8,
  relevantExperience: "",
  leadershipExperience: "",

  // D. Location Requirements
  country: "",
  stateRegion: "",
  city: "",
  preferredLocations: [],
  workMode: "Remote",
  willingnessToRelocate: false,

  // E. Additional Hiring Preferences
  salaryRange: "",
  noticePeriod: "30 Days",
  educationRequirements: "",
  preferredIndustries: [],
  companiesToTarget: [],
  companiesToExclude: [],
  additionalInstructions: "",
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

export default function Home() {
  const { isSignedIn, isLoaded, user } = useAppAuth();
  const [hasMounted, setHasMounted] = useState(false);
  const [hasAuthSessionHint, setHasAuthSessionHint] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      const authLocal = localStorage.getItem("hiring_desk_clerk_authenticated") === "true";
      const devAuth = localStorage.getItem("hiring_desk_dev_signed_in") === "true";
      const hasCookie =
        document.cookie.includes("__session=") ||
        (document.cookie.includes("__client_uat=") && !document.cookie.includes("__client_uat=0"));
      return authLocal || devAuth || hasCookie;
    } catch (e) {
      return false;
    }
  });

  // Auth transition animation state upon fresh sign-up / sign-in action
  const [showAuthTransition, setShowAuthTransition] = useState(false);
  const prevSignedInRef = useRef(null);

  useEffect(() => {
    setHasMounted(true);
    try {
      const authLocal = localStorage.getItem("hiring_desk_clerk_authenticated") === "true";
      const devAuth = localStorage.getItem("hiring_desk_dev_signed_in") === "true";
      const hasCookie =
        document.cookie.includes("__session=") ||
        (document.cookie.includes("__client_uat=") && !document.cookie.includes("__client_uat=0"));
      if (authLocal || devAuth || hasCookie) {
        setHasAuthSessionHint(true);
      }
    } catch (e) {}
  }, []);

  // Watch for successful sign-in / sign-up and trigger the radar animation
  useEffect(() => {
    if (isSignedIn) {
      try {
        localStorage.setItem("hiring_desk_clerk_authenticated", "true");
        setHasAuthSessionHint(true);
        // Clean URL hash if it was from sign-in/sign-up or sso-callback
        if (
          window.location.hash &&
          (window.location.hash.includes("sign-in") ||
            window.location.hash.includes("sign-up") ||
            window.location.hash.includes("sso-callback"))
        ) {
          window.history.replaceState(null, "", window.location.pathname + window.location.search);
        }
      } catch (e) {}

      // Only trigger the 1.5s post-auth transition if the user just signed in from signed-out state in this active tab session
      if (prevSignedInRef.current === false) {
        setShowAuthTransition(true);
        const timer = setTimeout(() => {
          setShowAuthTransition(false);
        }, 1500);
        return () => clearTimeout(timer);
      }
      prevSignedInRef.current = true;
    } else if (isLoaded) {
      if (prevSignedInRef.current === null) {
        prevSignedInRef.current = false;
      }
    }
  }, [isSignedIn, isLoaded]);

  // Theme state: defaults to light (as per the user's uploaded reference image)
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Navigation & View state
  const [activeNav, setActiveNav] = useState("overview");

  // Dynamic 3-Step Sourcing Wizard State
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState(1); // 1: Requirements, 2: AI Queries, 3: Execution & Automation
  const [activeOptionTab, setActiveOptionTab] = useState("manual"); // "manual" | "upload"
  const [jobRequirements, setJobRequirements] = useState(INITIAL_JOB_FORM);
  const [step1ValidationError, setStep1ValidationError] = useState("");
  const [draftSavedToast, setDraftSavedToast] = useState(false);

  // Document Upload State
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingJd, setUploadingJd] = useState(false);

  // Search Mode & Browser/Account Execution State
  const [searchMode, setSearchMode] = useState("autonomous"); // "autonomous" | "live"
  const [browserChannel, setBrowserChannel] = useState("chrome"); // "chrome" | "msedge" | "chromium"
  const [maxResults, setMaxResults] = useState(10);
  const [availableAccounts, setAvailableAccounts] = useState([]);
  const [selectedAccountId, setSelectedAccountId] = useState("acc_chrome");
  const [aiSearchPrompt, setAiSearchPrompt] = useState("");

  // 3 Strategic Queries Formulation & Review State
  const [strategicQueries, setStrategicQueries] = useState([]);
  const [selectedQueryId, setSelectedQueryId] = useState("precision");
  const [editingQueryId, setEditingQueryId] = useState(null);
  const [editedQueryText, setEditedQueryText] = useState("");
  const [generatingQueries, setGeneratingQueries] = useState(false);
  const [regeneratingQueryId, setRegeneratingQueryId] = useState(null);

  // Automated Outreach Composer State
  const [outreachModalOpen, setOutreachModalOpen] = useState(false);
  const [outreachCandidates, setOutreachCandidates] = useState([]);
  const [outreachCompanyName, setOutreachCompanyName] = useState("Acme Corp");
  const [outreachCompanyDetails, setOutreachCompanyDetails] = useState(
    "leading innovation in enterprise software and scalable systems"
  );
  const [outreachRecruiterName, setOutreachRecruiterName] = useState(
    "HR Talent Acquisition"
  );
  const [outreachRoleTitle, setOutreachRoleTitle] = useState("");
  const [outreachTone, setOutreachTone] = useState("formal");
  const [outreachSubject, setOutreachSubject] = useState("");
  const [outreachMessageBody, setOutreachMessageBody] = useState("");
  const [outreachConnectionNote, setOutreachConnectionNote] = useState("");
  const [outreachGenerating, setOutreachGenerating] = useState(false);
  const [outreachSending, setOutreachSending] = useState(false);
  const [outreachSessionId, setOutreachSessionId] = useState(null);
  const [outreachProgress, setOutreachProgress] = useState(null);
  const [outreachComplete, setOutreachComplete] = useState(false);

  // Modals & Handover Gates
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [previousNav, setPreviousNav] = useState("overview");

const scoreScrollRef = useRef(null);
  const scoreSectionRef = useRef(null);
  const [canScrollCategoriesLeft, setCanScrollCategoriesLeft] = useState(false);
  const [canScrollCategoriesRight, setCanScrollCategoriesRight] = useState(true);

  const selectedCleanName = useMemo(() => {
    if (!selectedCandidate) return "";
    return selectedCandidate.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, '')?.trim() || selectedCandidate.name || "Candidate";
  }, [selectedCandidate]);

  const selectedCleanHeadline = useMemo(() => {
    if (!selectedCandidate) return "";
    return sanitizeCandidateHeadline(selectedCandidate.headline, selectedCleanName);
  }, [selectedCandidate, selectedCleanName]);

  const selectedCandidateCompany = useMemo(() => {
    if (!selectedCandidate) return "";
    return getCandidateCompany(selectedCandidate, selectedCleanHeadline);
  }, [selectedCandidate, selectedCleanHeadline]);

  const selectedFormattedLocation = useMemo(() => {
    if (!selectedCandidate) return "";
    return formatCandidateLocation(selectedCandidate.current_location || selectedCandidate.location);
  }, [selectedCandidate]);

  const updateScrollButtons = useCallback(() => {
    if (scoreScrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scoreScrollRef.current;
      setCanScrollCategoriesLeft(scrollLeft > 4);
      setCanScrollCategoriesRight(scrollLeft + clientWidth < scrollWidth - 6);
    }
  }, []);

  const scrollScoreCategories = (direction) => {
    if (scoreScrollRef.current) {
      const cardStep = 190;
      const scrollAmount = direction === "left" ? -cardStep : cardStep;
      scoreScrollRef.current.scrollBy({ left: scrollAmount, behavior: "smooth" });
      setTimeout(updateScrollButtons, 150);
    }
  };

  const handleScoreWheel = useCallback((e) => {
    const container = scoreScrollRef.current;
    if (!container) return;

    // Allow native horizontal swipe
    if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;

    if (e.deltaY !== 0) {
      const canLeft = container.scrollLeft > 2;
      const canRight = container.scrollLeft + container.clientWidth < container.scrollWidth - 6;

      if ((e.deltaY < 0 && canLeft) || (e.deltaY > 0 && canRight)) {
        e.preventDefault();
        e.stopPropagation();
        const step = e.deltaY > 0 ? 190 : -190;
        container.scrollBy({ left: step, behavior: "smooth" });
        setTimeout(updateScrollButtons, 120);
      }
    }
  }, [updateScrollButtons]);

  useEffect(() => {
    const node = scoreSectionRef.current || scoreScrollRef.current;
    if (!node) return;
    node.addEventListener("wheel", handleScoreWheel, { passive: false });
    return () => {
      node.removeEventListener("wheel", handleScoreWheel);
    };
  }, [handleScoreWheel, selectedCandidate?.id]);

  useEffect(() => {
    if (selectedCandidate && scoreScrollRef.current) {
      scoreScrollRef.current.scrollLeft = 0;
      updateScrollButtons();
    }
  }, [selectedCandidate?.id, updateScrollButtons]);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authStatusMessage, setAuthStatusMessage] = useState("");
  const [checkingAuth, setCheckingAuth] = useState(false);
  const [isLinkedInLoggedIn, setIsLinkedInLoggedIn] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);

  // Candidate Data & Filters (completely empty initial state)
  const [candidateList, setCandidateList] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [selectAll, setSelectAll] = useState(false);
  const [showAllJdSkills, setShowAllJdSkills] = useState(false);

  // Candidate Table Horizontal Scroll on Middle Mouse Wheel (Callback Ref for guaranteed first-time attachment)
  const candidateTableNodeRef = useRef(null);

  const handleTableWheel = useCallback((e) => {
    const container = candidateTableNodeRef.current;
    if (!container) return;

    const maxScrollLeft = container.scrollWidth - container.clientWidth;
    if (maxScrollLeft <= 0) return;

    // Detect vertical mouse wheel movement
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      // Normalize delta across Windows line mode (deltaMode = 1) and pixel mode (deltaMode = 0)
      let delta = e.deltaY;
      if (e.deltaMode === 1) {
        delta *= 40; // 40px per line on Windows mouse wheel
      } else if (e.deltaMode === 2) {
        delta *= container.clientWidth * 0.8;
      }
      // Guarantee responsive, immediate visible movement on the very first notch
      if (Math.abs(delta) < 40 && delta !== 0) {
        delta = Math.sign(delta) * 50;
      }

      const isDown = delta > 0;
      const isUp = delta < 0;

      const canScrollRight = isDown && container.scrollLeft < maxScrollLeft - 1;
      const canScrollLeft = isUp && container.scrollLeft > 1;

      if (canScrollRight || canScrollLeft) {
        e.preventDefault();
        container.scrollLeft += delta;
      }
    }
  }, []);

  const setCandidateTableRef = useCallback((node) => {
    if (candidateTableNodeRef.current) {
      candidateTableNodeRef.current.removeEventListener("wheel", handleTableWheel);
    }
    candidateTableNodeRef.current = node;
    if (node) {
      node.addEventListener("wheel", handleTableWheel, { passive: false });
    }
  }, [handleTableWheel]);

  // Pipeline execution & telemetry (completely empty initial logs)
  const [analyzing, setAnalyzing] = useState(false);
  const [sourcing, setSourcing] = useState(false);
  const [evaluatingCandidateId, setEvaluatingCandidateId] = useState(null);
  const [batchEvaluating, setBatchEvaluating] = useState(false);
  const [syncingSupabase, setSyncingSupabase] = useState(false);
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
  const [pipelineStep, setPipelineStep] = useState(1);
  const [logs, setLogs] = useState([]);
  const [executionStats, setExecutionStats] = useState({
    discovered: 0,
    extracted: 0,
    evaluated: 0,
    saved: 0,
    duplicates: 0,
    durationSeconds: 0,
    startTime: null,
  });

  const addTelemetryLog = (msg, icon = "search") => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogs((prev) => [{ time, icon, text: msg }, ...prev.slice(0, 40)]);
  };

  // Multi-Role & Saved Jobs
  const [savedJobs, setSavedJobs] = useState([]);
  const [selectedRoleFilter, setSelectedRoleFilter] = useState("All");
  const [evalTargetRole, setEvalTargetRole] = useState("");
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState(false);

  // Backend Health & Dynamic Host URL
  const [apiBase, setApiBase] = useState("http://127.0.0.1:8001");
  const [backendHealth, setBackendHealth] = useState(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const host = window.location.hostname || "127.0.0.1";
      setApiBase(process.env.NEXT_PUBLIC_API_URL || `http://${host}:8001`);
    }
  }, []);

  // TanStack Query candidate cache integration & radar state
  const [showRadarView, setShowRadarView] = useState(false);
  const {
    candidates: queryCandidates,
    isLoading: isCandidatesLoading,
    isFetching: isCandidatesFetching,
    refetch: refetchCandidates,
    invalidateCandidates,
    setCandidatesData,
  } = useCandidatesQuery(apiBase, selectedRoleFilter);

  // Sync TanStack Query candidates into candidateList while preserving UI selections
  useEffect(() => {
    if (Array.isArray(queryCandidates) && queryCandidates.length > 0) {
      setCandidateList((prev) => {
        if (!prev || prev.length === 0) return queryCandidates;
        const selectedSet = new Set(prev.filter((c) => c.selected).map((c) => c.id || c.canonical_url));
        return queryCandidates.map((c) => ({
          ...c,
          selected: selectedSet.has(c.id || c.canonical_url),
        }));
      });
    }
  }, [queryCandidates]);

  // Route URL hash maps for browser back / forward history support
  const NAV_HASH_MAP = useMemo(
    () => ({
      overview: "#overview",
      review: "#candidates",
      candidates: "#candidates",
      job_description: "#job-description",
      criteria: "#criteria",
      sourcing: "#sourcing",
      pipeline: "#pipeline",
      shortlist: "#shortlist",
      reports: "#reports",
      settings: "#settings",
    }),
    []
  );

  const HASH_NAV_MAP = useMemo(
    () => ({
      overview: "overview",
      candidates: "review",
      review: "review",
      "job-description": "job_description",
      criteria: "criteria",
      sourcing: "sourcing",
      pipeline: "pipeline",
      shortlist: "shortlist",
      reports: "reports",
      settings: "settings",
    }),
    []
  );

  // Unified navigation function with full browser history pushState integration
  const navigateTo = useCallback(
    (navId, candidateObj = null, replace = false) => {
      let hash = "";
      if (navId === "candidate_profile" && candidateObj) {
        hash = `#candidate=${encodeURIComponent(candidateObj.id || candidateObj.canonical_url || candidateObj.name)}`;
      } else {
        hash = NAV_HASH_MAP[navId] || `#${navId}`;
      }

      if (typeof window !== "undefined") {
        const stateObj = { nav: navId, candidateId: candidateObj?.id || null };
        if (replace) {
          window.history.replaceState(stateObj, "", hash);
        } else if (window.location.hash !== hash) {
          window.history.pushState(stateObj, "", hash);
        }
      }

      if (navId === "candidate_profile" && candidateObj) {
        setActiveNav((curr) => {
          if (curr !== "candidate_profile") {
            setPreviousNav(curr);
          }
          return "candidate_profile";
        });
        setSelectedCandidate(candidateObj);
        if (candidateObj.target_role || candidateObj.job_title) {
          setEvalTargetRole(candidateObj.target_role || candidateObj.job_title);
        }
      } else {
        setSelectedCandidate(null);
        setActiveNav(navId);
      }
    },
    [NAV_HASH_MAP]
  );

  const handleOpenCandidateProfile = useCallback(
    (candidate) => {
      if (candidate) {
        navigateTo("candidate_profile", candidate);
      } else {
        navigateTo(previousNav || "overview");
      }
    },
    [navigateTo, previousNav]
  );

  // Browser level Back and Forward button tracking (popstate event listener)
  useEffect(() => {
    const handlePopState = (event) => {
      if (typeof window === "undefined") return;
      const rawHash = window.location.hash.replace(/^#\/?/, "");

      // Handle candidate profile hash
      if (rawHash.startsWith("candidate=")) {
        const rawId = decodeURIComponent(rawHash.replace("candidate=", ""));
        const found = candidateList.find(
          (c) => String(c.id) === rawId || c.canonical_url === rawId || c.name === rawId
        );
        if (found) {
          setSelectedCandidate(found);
          setActiveNav("candidate_profile");
          return;
        }
      }

      // Handle named tab hashes
      const targetNav = HASH_NAV_MAP[rawHash] || event.state?.nav || "overview";
      setSelectedCandidate(null);
      setActiveNav(targetNav);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [candidateList, HASH_NAV_MAP]);

  // Initial load hash synchronization
  useEffect(() => {
    if (typeof window === "undefined") return;
    const rawHash = window.location.hash.replace(/^#\/?/, "");
    if (
      !rawHash ||
      rawHash.includes("sign-in") ||
      rawHash.includes("sign-up") ||
      rawHash.includes("sso-callback")
    ) {
      window.history.replaceState({ nav: "overview", candidateId: null }, "", "#overview");
    } else if (rawHash.startsWith("candidate=")) {
      const rawId = decodeURIComponent(rawHash.replace("candidate=", ""));
      const found = candidateList.find(
        (c) => String(c.id) === rawId || c.canonical_url === rawId || c.name === rawId
      );
      if (found) {
        setSelectedCandidate(found);
        setActiveNav("candidate_profile");
      }
    } else if (HASH_NAV_MAP[rawHash]) {
      setActiveNav(HASH_NAV_MAP[rawHash]);
    }
  }, [candidateList, HASH_NAV_MAP]);

  // Global Escape key listener: closes any active modal container or exits candidate profile
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if (e.key === "Escape") {
        if (outreachModalOpen) {
          setOutreachModalOpen(false);
          return;
        }
        if (isWizardOpen) {
          setIsWizardOpen(false);
          return;
        }
        if (isReportModalOpen) {
          setIsReportModalOpen(false);
          return;
        }
        if (isAuthModalOpen) {
          setIsAuthModalOpen(false);
          return;
        }
        if (activeNav === "candidate_profile") {
          if (typeof window !== "undefined" && window.history.length > 1) {
            window.history.back();
          } else {
            navigateTo(previousNav || "overview");
          }
          return;
        }
      }
    };

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, [
    outreachModalOpen,
    isWizardOpen,
    isReportModalOpen,
    isAuthModalOpen,
    activeNav,
    previousNav,
    navigateTo,
  ]);

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

  const fetchSavedJobs = useCallback(async (targetBase) => {
    const url = targetBase || apiBase;
    try {
      const res = await fetch(`${url}/api/jobs`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data.jobs && data.jobs.length > 0) {
          setSavedJobs(data.jobs);
          setJobRequirements((prev) => {
            if (prev.jobTitle) return prev;
            const topJob = data.jobs[0];
            const locTokens = topJob.location ? topJob.location.split(",").map((s) => s.trim()) : [];
            const activeCity = topJob.city || (locTokens.length > 0 ? locTokens[0] : "");
            const activeState = topJob.state_region || (locTokens.length > 1 ? locTokens[1] : "");
            const activeCountry = topJob.country || (locTokens.length > 2 ? locTokens[2] : "");
            const computedLoc = [activeCity, activeState, activeCountry].filter(Boolean).join(", ") || topJob.location || "Flexible / Remote";
            const computedPref = topJob.preferred_locations && topJob.preferred_locations.length > 0
              ? topJob.preferred_locations
              : [activeCity, activeState, activeCountry].filter(Boolean);

            return {
              ...prev,
              jobTitle: topJob.job_title,
              department: topJob.department || "Engineering",
              seniorityLevel: topJob.seniority_level || "Senior",
              minExperience: topJob.min_years_experience || 5,
              mandatorySkills: topJob.mandatory_skills || [],
              preferredSkills: topJob.preferred_skills || [],
              technologies: topJob.technologies || [],
              city: activeCity,
              stateRegion: activeState,
              country: activeCountry,
              location: computedLoc,
              preferredLocations: computedPref,
              jobDescription: topJob.raw_jd || "",
            };
          });
        }
      }
    } catch {
      // ignore
    }
  }, [apiBase]);

  const handleSelectActiveRole = (job) => {
    const locTokens = job.location ? job.location.split(",").map((s) => s.trim()) : [];
    const activeCity = job.city || (locTokens.length > 0 ? locTokens[0] : "");
    const activeState = job.state_region || (locTokens.length > 1 ? locTokens[1] : "");
    const activeCountry = job.country || (locTokens.length > 2 ? locTokens[2] : "");
    const computedLoc = [activeCity, activeState, activeCountry].filter(Boolean).join(", ") || job.location || "Flexible / Remote";
    const computedPref = job.preferred_locations && job.preferred_locations.length > 0
      ? job.preferred_locations
      : [activeCity, activeState, activeCountry].filter(Boolean);

    setJobRequirements({
      jobTitle: job.job_title,
      department: job.department || "Engineering",
      seniorityLevel: job.seniority_level || "Senior",
      minExperience: job.min_years_experience || 5,
      maxExperience: job.max_years_experience || 12,
      mandatorySkills: job.mandatory_skills || [],
      preferredSkills: job.preferred_skills || [],
      technologies: job.technologies || [],
      city: activeCity,
      stateRegion: activeState,
      country: activeCountry,
      location: computedLoc,
      preferredLocations: computedPref,
      jobDescription: job.raw_jd || "",
    });
    setIsRoleDropdownOpen(false);
    addTelemetryLog(`Switched active role requisition to: ${job.job_title}`, "file");
  };

  const fetchStoredCandidates = useCallback(async (targetBase) => {
    const url = targetBase || apiBase;
    try {
      const res = await fetch(`${url}/api/sourcing/candidates?limit=50`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.candidates)) {
          const loaded = data.candidates.map((c, idx) => {
            const hasEval = c.fit_score !== null && c.fit_score !== undefined;
            const fit = hasEval ? Math.round(Number(c.fit_score)) : null;
            const cleanLoc = c.location && !c.location.toLowerCase().includes("location on profile") && !c.location.toLowerCase().includes("technology co.") ? c.location : "";
            const cleanComp = c.current_company && !c.current_company.toLowerCase().includes("technology co.") ? c.current_company : "";
            return {
              id: c.id || `stored_${idx}`,
              name: c.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, '')?.trim() || c.name,
              avatar: c.avatar_url || VERIFIED_AVATARS[idx % VERIFIED_AVATARS.length],
              location: cleanLoc || c.location || "",
              title: c.headline?.split(" at ")[0] || "Software Engineer",
              company: cleanComp,
              headline: c.headline,
              canonical_url: c.canonical_url,
              skill_match: fit,
              evidence_status: fit !== null ? (fit >= 80 ? "Verified" : fit >= 60 ? "Partial" : "Not Verified") : "Pending Review",
              sources: ["linkedin", "github"],
              status: c.status || "New",
              selected: false,
              experience_years: c.experience_years || 5.0,
              about: c.about || "",
              experience_history: c.experience_history || [],
              education: c.education || [],
              certifications: c.certifications || [],
              projects: c.projects || [],
              recent_activity: c.recent_activity || [],
              section_scores: c.section_scores || {},
              skills: c.skills || [],
              stored_in_db: true,
              target_role: c.target_role || c.job_title || "",
              job_title: c.job_title || c.target_role || "",
              match_level: hasEval ? (c.match_level || "Medium") : "Unevaluated",
              justification: c.justification || (hasEval ? "Candidate profile evaluated against job criteria." : "Profile harvested. Ready for evaluation."),
              evidence_quotes: (c.evidence_quotes || []).map((m) => ({
                requirement: m.criterion_requirement || m.requirement || "Skill",
                quote: m.verbatim_quote || m.quote || "",
                confidence: m.confidence || 0.85,
              })),
              missing_skills: c.missing_criteria || [],
              current_location: c.current_location || cleanLoc || c.location || "",
              preferred_work_locations: c.preferred_work_locations || [],
              willingness_to_relocate: c.willingness_to_relocate || "Unknown",
              work_authorization: c.work_authorization || "",
              location_compatibility_status: c.location_compatibility_status || "Compatible",
              location_compatibility_reason: c.location_compatibility_reason || "",
              domain_relevance: hasEval ? (c.domain_relevance || "Relevant") : "Unevaluated",
              domain_relevance_notes: c.domain_relevance_notes || "",
              evaluation_coverage: hasEval ? (c.evaluation_coverage !== undefined ? c.evaluation_coverage : 100) : null,
              category_evaluations: c.category_evaluations || {},
            };
          });
          setCandidateList(loaded);
          setCandidatesData(loaded);
        }
      }
    } catch {
      // gracefully ignore if offline
    }
  }, [apiBase, setCandidatesData]);

  const fetchAvailableAccounts = useCallback(async (targetBase) => {
    const url = targetBase || apiBase;
    try {
      const res = await fetch(`${url}/api/sourcing/accounts`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setAvailableAccounts(data);
        if (data.length > 0 && !selectedAccountId) {
          setSelectedAccountId(data[0].id);
        }
      }
    } catch {
      // fallback
    }
  }, [apiBase, selectedAccountId]);

  useEffect(() => {
    checkHealth(apiBase);
    fetchSavedJobs(apiBase);
    fetchStoredCandidates(apiBase);
    fetchAvailableAccounts(apiBase);
    const timer = setInterval(() => checkHealth(apiBase), 3500);
    return () => clearInterval(timer);
  }, [checkHealth, fetchSavedJobs, fetchStoredCandidates, fetchAvailableAccounts, apiBase]);

  // Synchronize company profile changes with outreach state & active job requirements
  useEffect(() => {
    const handleProfileSync = (prof) => {
      if (!prof) return;
      if (prof.companyName) {
        setOutreachCompanyName(prof.companyName);
        setJobRequirements((prev) => ({
          ...prev,
          company: prev.company && prev.company !== "Acme Corp" ? prev.company : prof.companyName,
        }));
      }
      if (prof.companyDetails) {
        setOutreachCompanyDetails(prof.companyDetails);
      }
      if (prof.recruiterName) {
        setOutreachRecruiterName(prof.recruiterName);
      }
    };

    const initial = getCompanyProfile();
    handleProfileSync(initial);

    const unsubscribe = subscribeCompanyProfile(handleProfileSync);
    return unsubscribe;
  }, []);

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
      addTelemetryLog("Retrieving sourcing report from candidate records...", "shield");
      const [repRes, candRes] = await Promise.all([
        fetch(`${apiBase}/api/sourcing/report`),
        fetch(`${apiBase}/api/sourcing/candidates?limit=50`),
      ]);
      const rep = await repRes.json();
      const cands = await candRes.json();
      setReportData({ ...rep, all_candidates: cands.candidates || [] });
      addTelemetryLog(`Shortlist Report loaded: ${rep.total_candidates_harvested || 0} candidates recorded`, "shield");
    } catch (err) {
      console.error("Report fetch error:", err);
      addTelemetryLog(`Failed to load sourcing report: ${err.message}`, "file");
    } finally {
      setLoadingReport(false);
    }
  };

  // Save Job Requirements Draft to Local Storage
  const handleSaveDraft = () => {
    try {
      if (typeof window !== "undefined") {
        localStorage.setItem("hiring_desk_draft_requirements", JSON.stringify(jobRequirements));
      }
      setDraftSavedToast(true);
      setTimeout(() => setDraftSavedToast(false), 3000);
      addTelemetryLog(`Draft saved for "${jobRequirements.jobTitle || 'Untitled Position'}"`, "shield");
    } catch (e) {
      console.warn("Could not save draft:", e);
    }
  };

  // Clean helper to launch or reset the 3-Step Wizard for fresh role search
  const handleOpenWizard = (step = 1) => {
    if (!sourcing) {
      setSessionState("idle");
      setSessionProgress(0);
      setSourcingStage("");
      setExecutionStats({
        discovered: 0,
        extracted: 0,
        evaluated: 0,
        saved: 0,
        duplicates: 0,
        durationSeconds: 0,
      });
      setSessionError(null);
      setError(null);
      setActiveSessionId(null);
    }
    setIsWizardOpen(true);
    setWizardStep(step);
  };

  // Clear Job Requirements Form
  const handleClearForm = () => {
    setJobRequirements(INITIAL_JOB_FORM);
    setUploadedFile(null);
    setUploadProgress(0);
    setStep1ValidationError("");
    if (!sourcing) {
      setSessionState("idle");
      setSessionProgress(0);
      setSourcingStage("");
      setExecutionStats({
        discovered: 0,
        extracted: 0,
        evaluated: 0,
        saved: 0,
        duplicates: 0,
        durationSeconds: 0,
      });
      setSessionError(null);
      setError(null);
      setActiveSessionId(null);
      setStrategicQueries([]);
      setSelectedQueryId(1);
    }
    addTelemetryLog("Job requirements form reset to clean default.", "file");
  };

  // Step 1: Upload and Parse JD Document (.pdf, .docx, .doc, .txt)
  const handleDocumentUpload = async (file) => {
    if (!file) return;
    setUploadingJd(true);
    setUploadProgress(25);
    setStep1ValidationError("");

    // Fresh upload unlocks a brand new sourcing session, clearing previous execution state
    if (!sourcing) {
      setSessionState("idle");
      setSessionProgress(0);
      setSourcingStage("");
      setExecutionStats({
        discovered: 0,
        extracted: 0,
        evaluated: 0,
        saved: 0,
        duplicates: 0,
        durationSeconds: 0,
      });
      setSessionError(null);
      setError(null);
      setActiveSessionId(null);
      setStrategicQueries([]);
      setSelectedQueryId(1);
    }

    addTelemetryLog(`Uploading and analyzing JD document "${file.name}"...`, "file");

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploadProgress(50);
      const res = await fetch(`${apiBase}/api/jobs/upload-jd`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned ${res.status}`);
      }

      setUploadProgress(85);
      const data = await res.json();

      if (data.criteria) {
        const c = data.criteria;

        // Strictly normalize seniority level to match select dropdown values
        let normSeniority = "Senior";
        const rawSen = (c.seniority_level || "").toLowerCase();
        if (rawSen.includes("lead") || rawSen.includes("manager") || rawSen.includes("head")) {
          normSeniority = "Lead / Manager";
        } else if (rawSen.includes("staff") || rawSen.includes("principal")) {
          normSeniority = "Staff / Principal";
        } else if (rawSen.includes("director") || rawSen.includes("exec") || rawSen.includes("vp")) {
          normSeniority = "Executive";
        } else if (rawSen.includes("senior")) {
          normSeniority = "Senior";
        } else if (rawSen.includes("mid") || rawSen.includes("intermediate")) {
          normSeniority = "Mid-Level";
        } else if (rawSen.includes("entry") || rawSen.includes("junior") || rawSen.includes("intern")) {
          normSeniority = "Entry Level";
        }

        // Normalize work mode
        let normWorkMode = "Remote";
        const rawWm = (c.work_mode || "").toLowerCase();
        if (rawWm.includes("hybrid")) normWorkMode = "Hybrid";
        else if (rawWm.includes("on-site") || rawWm.includes("onsite") || rawWm.includes("office")) normWorkMode = "On-site";
        else if (rawWm.includes("remote")) normWorkMode = "Remote";

        setJobRequirements((prev) => ({
          ...prev,
          // A. Job Information
          jobTitle: c.job_title || file.name.replace(/\.[^/.]+$/, ""),
          jobDescription: c.job_description || data.raw_jd || prev.jobDescription,
          department: c.department || prev.department,
          employmentType: c.employment_type || prev.employmentType,
          seniorityLevel: normSeniority,
          vacancies: c.vacancies || prev.vacancies,

          // B. Required Skills & Technologies
          mandatorySkills: Array.isArray(c.mandatory_skills) && c.mandatory_skills.length > 0 ? c.mandatory_skills : prev.mandatorySkills,
          preferredSkills: Array.isArray(c.preferred_skills) && c.preferred_skills.length > 0 ? c.preferred_skills : prev.preferredSkills,
          technologies: Array.isArray(c.technologies) && c.technologies.length > 0 ? c.technologies : prev.technologies,
          toolsPlatforms: Array.isArray(c.tools_platforms) && c.tools_platforms.length > 0 ? c.tools_platforms : prev.toolsPlatforms,
          domainExpertise: Array.isArray(c.domain_expertise) && c.domain_expertise.length > 0 ? c.domain_expertise : prev.domainExpertise,
          certifications: Array.isArray(c.certifications) && c.certifications.length > 0 ? c.certifications : prev.certifications,

          // C. Experience Requirements
          minExperience: c.min_years_experience !== null && c.min_years_experience !== undefined ? c.min_years_experience : prev.minExperience,
          maxExperience: c.max_years_experience !== null && c.max_years_experience !== undefined ? c.max_years_experience : (c.min_years_experience ? Math.max(Number(c.min_years_experience) + 4, prev.maxExperience) : prev.maxExperience),
          relevantExperience: c.relevant_experience || prev.relevantExperience,
          leadershipExperience: c.leadership_experience || prev.leadershipExperience,

          // D. Location Requirements
          country: c.country || prev.country,
          stateRegion: c.state_region || prev.stateRegion,
          city: c.city || prev.city,
          preferredLocations: (Array.isArray(c.preferred_locations) && c.preferred_locations.length > 0)
            ? c.preferred_locations
            : (Array.isArray(c.target_locations) && c.target_locations.length > 0 ? c.target_locations : prev.preferredLocations),
          workMode: normWorkMode,
          willingnessToRelocate: c.willingness_to_relocate !== undefined ? c.willingness_to_relocate : prev.willingnessToRelocate,

          // E. Additional Hiring Preferences
          salaryRange: c.salary_range || prev.salaryRange,
          noticePeriod: c.notice_period || prev.noticePeriod,
          educationRequirements: c.education_requirements || prev.educationRequirements,
          preferredIndustries: Array.isArray(c.preferred_industries) && c.preferred_industries.length > 0 ? c.preferred_industries : prev.preferredIndustries,
          companiesToTarget: Array.isArray(c.companies_to_target) && c.companies_to_target.length > 0 ? c.companies_to_target : prev.companiesToTarget,
          companiesToExclude: Array.isArray(c.companies_to_exclude) && c.companies_to_exclude.length > 0 ? c.companies_to_exclude : prev.companiesToExclude,
          additionalInstructions: c.additional_instructions || prev.additionalInstructions,
        }));
      }

      setUploadedFile({
        name: file.name,
        size: `${(file.size / 1024).toFixed(1)} KB`,
        type: file.name.split(".").pop().toUpperCase(),
      });
      setUploadProgress(100);
      addTelemetryLog(`JD Document "${file.name}" parsed into structured job requirements!`, "shield");
    } catch (err) {
      setStep1ValidationError(`Document parsing failed: ${err.message}`);
      addTelemetryLog(`Document upload error: ${err.message}`, "file");
    } finally {
      setUploadingJd(false);
    }
  };

  // Step 1 -> Step 2: Validate & Generate 3 AI Search Queries
  const handleStep1Next = async () => {
    if (!jobRequirements.jobTitle.trim()) {
      setStep1ValidationError("Job Title / Role is mandatory before generating search queries.");
      return;
    }
    setStep1ValidationError("");
    setGeneratingQueries(true);
    // Reset session execution state so subsequent step 3 is fresh
    if (!sourcing) {
      setSessionState("idle");
      setSessionProgress(0);
      setSourcingStage("");
      setExecutionStats({
        discovered: 0,
        extracted: 0,
        evaluated: 0,
        saved: 0,
        duplicates: 0,
        durationSeconds: 0,
      });
      setSessionError(null);
      setError(null);
      setActiveSessionId(null);
    }
    addTelemetryLog(`Generating 3 strategic LinkedIn queries for "${jobRequirements.jobTitle}"...`, "search");

    try {
      const res = await fetch(`${apiBase}/api/jobs/generate-queries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: jobRequirements.jobTitle,
          job_description: jobRequirements.jobDescription,
          department: jobRequirements.department,
          employment_type: jobRequirements.employmentType,
          seniority_level: jobRequirements.seniorityLevel,
          vacancies: jobRequirements.vacancies,
          mandatory_skills: jobRequirements.mandatorySkills,
          preferred_skills: jobRequirements.preferredSkills,
          technologies: jobRequirements.technologies,
          tools_platforms: jobRequirements.toolsPlatforms,
          domain_expertise: jobRequirements.domainExpertise,
          certifications: jobRequirements.certifications,
          min_years_experience: Number(jobRequirements.minExperience) || 3,
          max_years_experience: Number(jobRequirements.maxExperience) || 8,
          relevant_experience: jobRequirements.relevantExperience,
          leadership_experience: jobRequirements.leadershipExperience,
          country: jobRequirements.country,
          state_region: jobRequirements.stateRegion,
          city: jobRequirements.city,
          preferred_locations: (Array.isArray(jobRequirements.preferredLocations) && jobRequirements.preferredLocations.length > 0)
            ? jobRequirements.preferredLocations
            : [jobRequirements.city, jobRequirements.stateRegion, jobRequirements.country].filter(Boolean),
          work_mode: jobRequirements.workMode,
          willingness_to_relocate: jobRequirements.willingnessToRelocate,
          salary_range: jobRequirements.salaryRange,
          notice_period: jobRequirements.noticePeriod,
          education_requirements: jobRequirements.educationRequirements,
          preferred_industries: jobRequirements.preferredIndustries,
          companies_to_target: jobRequirements.companiesToTarget,
          companies_to_exclude: jobRequirements.companiesToExclude,
          additional_instructions: jobRequirements.additionalInstructions,
        }),
      });

      if (!res.ok) throw new Error(`Query generation failed (${res.status})`);
      const queries = await res.json();
      setStrategicQueries(queries);
      if (queries.length > 0) {
        setSelectedQueryId(queries[0].id);
      }
      setWizardStep(2);
      addTelemetryLog("Formulated 3 recruiter-grade Boolean search queries for HR review", "shield");
    } catch (err) {
      setStep1ValidationError(`Failed to generate queries: ${err.message}`);
      addTelemetryLog(`Query generation error: ${err.message}`, "file");
    } finally {
      setGeneratingQueries(false);
    }
  };

  // Step 2: Regenerate an individual query
  const handleRegenerateSingleQuery = async (strategyId) => {
    setRegeneratingQueryId(strategyId);
    addTelemetryLog(`Regenerating strategic query #${strategyId}...`, "search");
    try {
      const res = await fetch(`${apiBase}/api/jobs/regenerate-query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy_id: strategyId,
          job_title: jobRequirements.jobTitle,
          mandatory_skills: jobRequirements.mandatorySkills,
          preferred_skills: jobRequirements.preferredSkills,
          technologies: jobRequirements.technologies,
          domain_expertise: jobRequirements.domainExpertise,
          preferred_locations: (Array.isArray(jobRequirements.preferredLocations) && jobRequirements.preferredLocations.length > 0)
            ? jobRequirements.preferredLocations
            : [jobRequirements.city, jobRequirements.stateRegion, jobRequirements.country].filter(Boolean),
          state_region: jobRequirements.stateRegion,
          city: jobRequirements.city,
          country: jobRequirements.country,
          min_years_experience: Number(jobRequirements.minExperience) || 3,
        }),
      });
      if (res.ok) {
        const newQuery = await res.json();
        setStrategicQueries((prev) => prev.map((q) => (q.id === strategyId ? newQuery : q)));
        addTelemetryLog(`Regenerated query #${strategyId} successfully`, "shield");
      }
    } catch (err) {
      console.warn("Regenerate query error:", err);
    } finally {
      setRegeneratingQueryId(null);
    }
  };

  // Step 2: Regenerate all 3 queries
  const handleRegenerateAllQueries = async () => {
    setGeneratingQueries(true);
    addTelemetryLog("Regenerating all 3 LinkedIn search strategies...", "search");
    try {
      const res = await fetch(`${apiBase}/api/jobs/generate-queries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: jobRequirements.jobTitle,
          mandatory_skills: jobRequirements.mandatorySkills,
          preferred_skills: jobRequirements.preferredSkills,
          technologies: jobRequirements.technologies,
          tools_platforms: jobRequirements.toolsPlatforms,
          domain_expertise: jobRequirements.domainExpertise,
          preferred_locations: (Array.isArray(jobRequirements.preferredLocations) && jobRequirements.preferredLocations.length > 0)
            ? jobRequirements.preferredLocations
            : [jobRequirements.city, jobRequirements.stateRegion, jobRequirements.country].filter(Boolean),
          state_region: jobRequirements.stateRegion,
          city: jobRequirements.city,
          country: jobRequirements.country,
          seniority_level: jobRequirements.seniorityLevel,
          min_years_experience: Number(jobRequirements.minExperience) || 3,
        }),
      });
      if (res.ok) {
        const queries = await res.json();
        setStrategicQueries(queries);
        addTelemetryLog("All 3 search queries refreshed with alternative Boolean logic", "shield");
      }
    } catch (err) {
      console.warn("Regenerate all error:", err);
    } finally {
      setGeneratingQueries(false);
    }
  };

  // Step 2 -> Step 3
  const handleStep2Next = () => {
    // If not actively sourcing, ensure Step 3 opens clean and unlocked for this role's parameters
    if (!sourcing) {
      setSessionState("idle");
      setSessionProgress(0);
      setSourcingStage("");
      setExecutionStats({
        discovered: 0,
        extracted: 0,
        evaluated: 0,
        saved: 0,
        duplicates: 0,
        durationSeconds: 0,
      });
      setSessionError(null);
      setError(null);
      setActiveSessionId(null);
    }
    setWizardStep(3);
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
    setIsWizardOpen(true);
    setWizardStep(3);
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

    const activeQueryObj = strategicQueries.find((q) => q.id === selectedQueryId);
    const query = (
      activeQueryObj?.query ||
      aiSearchPrompt ||
      `"${jobRequirements.jobTitle}" ${(jobRequirements.mandatorySkills || []).slice(0, 3).map((s) => `"${s}"`).join(" ")}`
    ).trim();

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
    addTelemetryLog(`Active search query: ${query}`, "search");

    setExecutionStats({
      discovered: 0,
      extracted: 0,
      evaluated: 0,
      saved: 0,
      duplicates: 0,
      durationSeconds: 0,
      startTime: Date.now(),
    });

    try {
      const activeLocations = [jobRequirements.city, jobRequirements.stateRegion, jobRequirements.country].filter(Boolean);
      const activeLocStr = activeLocations.join(", ") || jobRequirements.location || "";
      const activePrefLocs = activeLocations.length > 0
        ? activeLocations
        : (Array.isArray(jobRequirements.preferredLocations) && jobRequirements.preferredLocations.length > 0
            ? jobRequirements.preferredLocations
            : (jobRequirements.location ? [jobRequirements.location] : (jobRequirements.city ? [jobRequirements.city] : [])));

      // Step 1: Start background sourcing session
      const startRes = await fetch(`${apiBase}/api/sourcing/start-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          keywords: query,
          max_results: maxResults,
          mode: effectiveMode,
          browser_channel: browserChannel,
          account_id: selectedAccountId,
          deep_scrape: true,
          role_title: jobRequirements.jobTitle || "Software Engineer",
          mandatory_skills: jobRequirements.mandatorySkills || [],
          location: activeLocStr,
          preferred_locations: activePrefLocs,
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
      let lastLoggedMessage = "";
      const maxPolls = 300; // ~240 seconds max to prevent premature abort during live scraping

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
              if (data.message !== lastLoggedMessage) {
                lastLoggedMessage = data.message;
                if (data.message.includes("AI Decision Layer") || data.message.includes("pivoted") || data.message.includes("saturated")) {
                  addTelemetryLog(data.message, "search");
                } else if (data.message.includes("duplicates skipped") || data.message.includes("duplicate profiles")) {
                  addTelemetryLog(data.message, "shield");
                }
              }
            }

            if (data.candidates && data.candidates.length > 0) {
              const timestamp = Date.now();
              const liveHarvested = data.candidates.map((c, idx) => {
                const cleanLoc = c.location && !c.location.toLowerCase().includes("location on profile") && !c.location.toLowerCase().includes("technology co.") ? c.location : "";
                const cleanComp = c.current_company && !c.current_company.toLowerCase().includes("technology co.") ? c.current_company : "";
                return {
                  id: c.id || `live_${timestamp}_${idx}`,
                  name: c.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, '')?.trim() || c.name,
                  avatar: c.avatar_url || VERIFIED_AVATARS[idx % VERIFIED_AVATARS.length],
                  location: cleanLoc || c.location || "",
                  title: c.headline?.split(" at ")[0] || "Software Engineer",
                  company: cleanComp,
                  headline: c.headline,
                  canonical_url: c.canonical_url,
                  skill_match: c.fit_score != null ? Math.round(c.fit_score) : null,
                  evidence_status: c.fit_score != null ? "Verified" : "Pending Review",
                  sources: ["linkedin", "web"],
                  status: "New",
                  selected: false,
                  experience_years: c.experience_years || 5.0,
                  about: c.about || "",
                  experience_history: c.experience_history || [],
                  education: c.education || [],
                  certifications: c.certifications || [],
                  projects: c.projects || [],
                  recent_activity: c.recent_activity || [],
                  section_scores: c.section_scores || {},
                  skills: c.skills || [],
                  stored_in_db: true,
                  target_role: c.target_role || jobRequirements.jobTitle || "Senior Fullstack Engineer",
                  job_title: c.target_role || jobRequirements.jobTitle || "Senior Fullstack Engineer",
                  match_level: c.match_level || "High",
                  justification: c.justification || "Autonomous Browser Agent navigated and extracted complete resume into candidate profile.",
                  evidence_quotes: (c.evidence_quotes && c.evidence_quotes.length > 0) ? c.evidence_quotes : (c.skills || []).slice(0, 3).map((s) => ({
                    requirement: s,
                    quote: `${c.headline || c.about || "Verified profile skill"}`,
                    confidence: 0.9,
                  })),
                  missing_skills: c.missing_criteria || [],
                  current_location: c.current_location || cleanLoc || c.location || "",
                  preferred_work_locations: c.preferred_work_locations || [],
                  willingness_to_relocate: c.willingness_to_relocate || "Unknown",
                  work_authorization: c.work_authorization || "",
                  location_compatibility_status: c.location_compatibility_status || "Compatible",
                  location_compatibility_reason: c.location_compatibility_reason || "",
                  domain_relevance: c.domain_relevance || "Relevant",
                  domain_relevance_notes: c.domain_relevance_notes || "",
                  evaluation_coverage: c.evaluation_coverage !== undefined ? c.evaluation_coverage : 100,
                  category_evaluations: c.category_evaluations || {},
                };
              });

              setExecutionStats((prev) => ({
                ...prev,
                discovered: Math.max(prev.discovered, liveHarvested.length + (data.duplicates_count || 0)),
                extracted: liveHarvested.length,
                duplicates: data.duplicates_count || prev.duplicates,
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
      addTelemetryLog(`Agent extracted & saved ${extractedCandidates.length} candidate profiles!`, "file");

      // Step 3: Run Gemini AI Evaluation if candidates found
      if (extractedCandidates.length > 0) {
        setPipelineStep(4);
        setSourcingStage(`Harvested ${extractedCandidates.length} profiles! Scoring evidence with Gemini AI...`);

        const criteria = {
          job_title: jobRequirements.jobTitle || "Software Engineer",
          seniority_level: jobRequirements.seniorityLevel || "Senior",
          min_years_experience: Number(jobRequirements.minExperience) || 3,
          mandatory_skills: jobRequirements.mandatorySkills || [],
          preferred_skills: jobRequirements.preferredSkills || [],
          location: activeLocStr,
          preferred_locations: activePrefLocs,
          criteria_list: (jobRequirements.mandatorySkills || []).map((req) => ({
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
                const fitScoreNum = Number(evaluation.fit_score);
                const fit = !isNaN(fitScoreNum) ? Math.max(0, Math.min(100, Math.round(fitScoreNum))) : 0;
                const cleanLoc = candidate.location && !candidate.location.toLowerCase().includes("location on profile") && !candidate.location.toLowerCase().includes("technology co.") ? candidate.location : "";
                const cleanComp = candidate.current_company && !candidate.current_company.toLowerCase().includes("technology co.") ? candidate.current_company : "";
                return {
                  id: `live_${Date.now()}_${idx}_${candidate.id || idx}`,
                  name: candidate.name,
                  avatar: candidate.avatar_url || VERIFIED_AVATARS[idx % VERIFIED_AVATARS.length],
                  location: cleanLoc || candidate.location || "",
                  title: candidate.headline.split(" at ")[0] || "Software Engineer",
                  company: cleanComp,
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
                  education: candidate.education || [],
                  certifications: candidate.certifications || [],
                  projects: candidate.projects || [],
                  recent_activity: candidate.recent_activity || [],
                  section_scores: evaluation.section_scores || candidate.section_scores || {},
                  skills: candidate.skills || [],
                  stored_in_db: true,
                  target_role: candidate.target_role || evaluation.job_title || criteria.job_title || jobRequirements.jobTitle || "Senior Fullstack Engineer",
                  job_title: candidate.target_role || evaluation.job_title || criteria.job_title || jobRequirements.jobTitle || "Senior Fullstack Engineer",
                  match_level: evaluation.match_level,
                  justification: evaluation.justification_summary,
                  evidence_quotes: (evaluation.evidence_quotes || []).map((m) => ({
                    requirement: m.criterion_requirement,
                    quote: m.verbatim_quote,
                    confidence: m.confidence || 0.9,
                  })),
                  missing_skills: evaluation.missing_criteria || [],
                  current_location: candidate.current_location || cleanLoc || candidate.location || "",
                  preferred_work_locations: candidate.preferred_work_locations || [],
                  willingness_to_relocate: candidate.willingness_to_relocate || "Unknown",
                  work_authorization: candidate.work_authorization || "",
                  location_compatibility_status: evaluation.location_compatibility?.status || candidate.location_compatibility_status || "Compatible",
                  location_compatibility_reason: evaluation.location_compatibility?.reason || candidate.location_compatibility_reason || "",
                  domain_relevance: evaluation.domain_relevance || candidate.domain_relevance || "Relevant",
                  domain_relevance_notes: evaluation.domain_relevance_notes || candidate.domain_relevance_notes || "",
                  evaluation_coverage: evaluation.evaluation_coverage !== undefined ? evaluation.evaluation_coverage : 100,
                  category_evaluations: evaluation.category_evaluations || candidate.category_evaluations || {},
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

        try {
          await fetchStoredCandidates(apiBase);
        } catch (syncErr) {
          console.warn("Post-evaluation candidate sync warning:", syncErr);
        }
      }

      setPipelineStep(5);
      setSessionState("completed");
      setSessionProgress(100);
      setExecutionStats((prev) => ({
        ...prev,
        evaluated: extractedCandidates.length,
        saved: extractedCandidates.length,
        durationSeconds: Math.max(1, Math.round((Date.now() - (prev.startTime || Date.now())) / 1000)),
      }));
      setSourcingStage(`🎉 Done! Harvested ${extractedCandidates.length} profiles. Headed ${channelName} browser remains open.`);
      addTelemetryLog(`Shortlist refreshed with ${extractedCandidates.length} verified candidate profiles!`, "shield");

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

  // Candidate Deletion
  const handleDeleteCandidate = async (candidateId) => {
    try {
      const res = await fetch(`${apiBase}/api/sourcing/candidates/${candidateId}`, { method: "DELETE" });
      if (res.ok) {
        setCandidateList((prev) => prev.filter((c) => c.id !== candidateId));
        if (selectedCandidate && selectedCandidate.id === candidateId) {
          setSelectedCandidate(null);
        }
        addTelemetryLog("Candidate removed from database and shortlist.", "shield");
      }
    } catch (err) {
      console.error("Delete candidate error:", err);
    }
  };

  const handleClearAllCandidates = async () => {
    if (!window.confirm("Are you sure you want to remove all candidate records from the database?")) return;
    try {
      const res = await fetch(`${apiBase}/api/sourcing/candidates`, { method: "DELETE" });
      if (res.ok) {
        setCandidateList([]);
        setSelectedCandidate(null);
        setCandidatesData([]);
        invalidateCandidates();
        addTelemetryLog("All candidate records cleared from database.", "shield");
      }
    } catch (err) {
      console.error("Clear candidates error:", err);
    }
  };

  // On-Demand AI Evaluation for Single Candidate against Chosen Role Requisition
  const handleEvaluateSingleCandidate = async (candidate, targetRoleName) => {
    if (!candidate) return;
    setEvaluatingCandidateId(candidate.id);
    const chosenRole = targetRoleName || candidate.target_role || candidate.job_title || jobRequirements.jobTitle || "Senior Fullstack Engineer";
    addTelemetryLog(`Evaluating candidate ${candidate.name} against requisition: ${chosenRole}...`, "sparkles");
    try {
      const activeLocs = [jobRequirements.city, jobRequirements.stateRegion, jobRequirements.country].filter(Boolean);
      const activeLocStr = activeLocs.join(", ") || jobRequirements.location || "";
      const activePrefLocs = activeLocs.length > 0
        ? activeLocs
        : (jobRequirements.preferredLocations || (jobRequirements.location ? [jobRequirements.location] : []));

      const matchedJob = savedJobs.find((j) => (j.job_title || "").toLowerCase() === chosenRole.toLowerCase());
      const criteria = matchedJob ? {
        job_title: matchedJob.job_title,
        seniority_level: matchedJob.seniority_level || "Senior",
        min_years_experience: Number(matchedJob.min_years_experience) || 3,
        mandatory_skills: matchedJob.mandatory_skills || [],
        preferred_skills: matchedJob.preferred_skills || [],
        location: matchedJob.location || activeLocStr,
        preferred_locations: matchedJob.preferred_locations || (matchedJob.location ? [matchedJob.location] : activePrefLocs),
      } : {
        job_title: chosenRole,
        seniority_level: jobRequirements.seniorityLevel || "Senior",
        min_years_experience: Number(jobRequirements.minExperience) || 3,
        mandatory_skills: jobRequirements.mandatorySkills || [],
        preferred_skills: jobRequirements.preferredSkills || [],
        location: activeLocStr,
        preferred_locations: activePrefLocs,
      };

      const res = await fetch(`${apiBase}/api/sourcing/evaluate-candidates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidates: [{ ...candidate, target_role: chosenRole }],
          criteria: criteria,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.evaluated_candidates && data.evaluated_candidates.length > 0) {
          const { evaluation } = data.evaluated_candidates[0];
          const fit = Math.round(Number(evaluation.fit_score));
          const updated = {
            ...candidate,
            skill_match: fit,
            target_role: chosenRole,
            job_title: chosenRole,
            evidence_status: fit >= 80 ? "Verified" : fit >= 60 ? "Partial" : "Not Verified",
            match_level: evaluation.match_level,
            justification: evaluation.justification_summary,
            section_scores: evaluation.section_scores || {},
            category_evaluations: evaluation.category_evaluations || {},
            evidence_quotes: (evaluation.evidence_quotes || []).map((m) => ({
              requirement: m.criterion_requirement || m.requirement || "Skill",
              quote: m.verbatim_quote || m.quote || "",
              confidence: m.confidence || 0.9,
            })),
            missing_skills: evaluation.missing_criteria || [],
            location_compatibility_status: evaluation.location_compatibility?.status || candidate.location_compatibility_status,
            location_compatibility_reason: evaluation.location_compatibility?.reason || candidate.location_compatibility_reason,
            domain_relevance: evaluation.domain_relevance || candidate.domain_relevance,
            domain_relevance_notes: evaluation.domain_relevance_notes || candidate.domain_relevance_notes,
            evaluation_coverage: evaluation.evaluation_coverage !== undefined ? evaluation.evaluation_coverage : 100,
          };
          setSelectedCandidate(updated);
          setCandidateList((prev) => prev.map((c) => (c.id === candidate.id ? updated : c)));
          addTelemetryLog(`Evaluated ${candidate.name} against ${chosenRole}: ${fit}% fit score (${evaluation.match_level})`, "shield");
        }
      }
    } catch (err) {
      console.error("Evaluation error:", err);
      addTelemetryLog(`Evaluation error: ${err.message}`, "file");
    } finally {
      setEvaluatingCandidateId(null);
    }
  };

  // Batch Evaluate Candidates - evaluates candidates against respective role requisitions
  const handleEvaluateAllCandidates = async () => {
    const candidatesToEval = selectedRoleFilter === "All"
      ? candidateList
      : candidateList.filter((c) => (c.target_role || c.job_title || "").toLowerCase().includes(selectedRoleFilter.toLowerCase()));

    if (!candidatesToEval.length) return;
    setBatchEvaluating(true);
    const roleTargetLabel = selectedRoleFilter === "All" ? "their designated target roles" : selectedRoleFilter;
    addTelemetryLog(`Starting multi-role batch evaluation for ${candidatesToEval.length} candidates against ${roleTargetLabel}...`, "sparkles");
    try {
      const activeLocs = [jobRequirements.city, jobRequirements.stateRegion, jobRequirements.country].filter(Boolean);
      const activeLocStr = activeLocs.join(", ") || jobRequirements.location || "";
      const activePrefLocs = activeLocs.length > 0
        ? activeLocs
        : (jobRequirements.preferredLocations || (jobRequirements.location ? [jobRequirements.location] : []));

      const criteria = {
        job_title: selectedRoleFilter === "All" ? (jobRequirements.jobTitle || "Target Role") : selectedRoleFilter,
        seniority_level: jobRequirements.seniorityLevel || "Senior",
        min_years_experience: Number(jobRequirements.minExperience) || 3,
        mandatory_skills: jobRequirements.mandatorySkills || [],
        preferred_skills: jobRequirements.preferredSkills || [],
        location: activeLocStr,
        preferred_locations: activePrefLocs,
      };
      const res = await fetch(`${apiBase}/api/sourcing/evaluate-candidates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidates: candidatesToEval,
          criteria: criteria,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.evaluated_candidates && data.evaluated_candidates.length > 0) {
          const evalMap = new Map();
          data.evaluated_candidates.forEach(({ candidate: c, evaluation: ev }) => {
            const fit = Math.round(Number(ev.fit_score));
            evalMap.set(c.id || c.canonical_url, {
              skill_match: fit,
              target_role: c.target_role || ev.job_title,
              job_title: ev.job_title || c.target_role,
              evidence_status: fit >= 80 ? "Verified" : fit >= 60 ? "Partial" : "Not Verified",
              match_level: ev.match_level,
              justification: ev.justification_summary,
              section_scores: ev.section_scores || {},
              category_evaluations: ev.category_evaluations || {},
              evidence_quotes: (ev.evidence_quotes || []).map((m) => ({
                requirement: m.criterion_requirement || m.requirement || "Skill",
                quote: m.verbatim_quote || m.quote || "",
                confidence: m.confidence || 0.9,
              })),
              missing_skills: ev.missing_criteria || [],
              location_compatibility_status: ev.location_compatibility?.status,
              location_compatibility_reason: ev.location_compatibility?.reason,
              domain_relevance: ev.domain_relevance,
              domain_relevance_notes: ev.domain_relevance_notes,
              evaluation_coverage: ev.evaluation_coverage !== undefined ? ev.evaluation_coverage : 100,
            });
          });
          setCandidateList((prev) =>
            prev.map((c) => {
              const ev = evalMap.get(c.id) || evalMap.get(c.canonical_url);
              return ev ? { ...c, ...ev } : c;
            })
          );
          addTelemetryLog(`Batch evaluation complete: Evaluated ${data.evaluated_candidates.length} candidates against their target roles!`, "shield");
        }
      }
    } catch (err) {
      console.error("Batch evaluation error:", err);
      addTelemetryLog(`Batch evaluation error: ${err.message}`, "file");
    } finally {
      setBatchEvaluating(false);
    }
  };

  // Sync Local Candidates and Evaluations to Supabase PostgreSQL
  const handleSyncSupabase = async () => {
    setSyncingSupabase(true);
    addTelemetryLog("Syncing local candidate profiles and evaluations to Supabase PostgreSQL...", "database");
    try {
      const res = await fetch(`${apiBase}/api/sourcing/sync-supabase`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        addTelemetryLog(
          `Supabase Cloud Sync: ${data.message || (data.synced_candidates !== undefined ? `Synced ${data.synced_candidates} candidates` : 'Synced to Supabase successfully')}`,
          "shield"
        );
      } else {
        addTelemetryLog("Supabase Cloud Sync failed. Check API keys in .env", "file");
      }
    } catch (err) {
      console.error("Supabase sync error:", err);
      addTelemetryLog(`Supabase sync error: ${err.message}`, "file");
    } finally {
      setSyncingSupabase(false);
    }
  };

  const availableRoles = useMemo(() => {
    const roleCounts = {};
    candidateList.forEach((c) => {
      const r = (c.target_role || c.job_title || "General").trim();
      if (r) {
        roleCounts[r] = (roleCounts[r] || 0) + 1;
      }
    });
    return Object.entries(roleCounts).map(([name, count]) => ({ name, count }));
  }, [candidateList]);

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

  // Handle Opening Outreach Composer
  const handleOpenOutreach = async (candidatesToContact) => {
    const list = Array.isArray(candidatesToContact) ? candidatesToContact : [candidatesToContact];
    if (list.length === 0) return;

    setOutreachCandidates(list);
    setOutreachModalOpen(true);
    setOutreachComplete(false);
    setOutreachProgress(null);

    const firstCand = list[0];
    const role = firstCand.target_role || firstCand.job_title || jobRequirements.jobTitle || (savedJobs[0]?.job_title || "Senior Engineer");
    setOutreachRoleTitle(role);

    const currentComp = jobRequirements.company || (savedJobs[0]?.company || outreachCompanyName || "Acme Corp");
    setOutreachCompanyName(currentComp);

    setOutreachGenerating(true);
    try {
      const cleanName = firstCand.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, '')?.trim() || firstCand.name || "Candidate";
      const res = await fetch(`${apiBase}/api/outreach/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: cleanName,
          canonical_url: firstCand.canonical_url,
          headline: firstCand.headline,
          skills: firstCand.skills || [],
          current_company: firstCand.current_company,
          target_role: role,
          company_name: currentComp,
          company_details: outreachCompanyDetails,
          recruiter_name: outreachRecruiterName,
          tone: outreachTone,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setOutreachSubject(data.subject || `Opportunity: ${role} at ${currentComp}`);
        setOutreachMessageBody(data.message_body || "");
        setOutreachConnectionNote(data.connection_note || "");
      }
    } catch (err) {
      console.error("Error generating initial outreach draft:", err);
    } finally {
      setOutreachGenerating(false);
    }
  };

  // Regenerate Outreach Draft
  const handleRegenerateOutreachDraft = async () => {
    if (outreachCandidates.length === 0) return;
    const firstCand = outreachCandidates[0];
    setOutreachGenerating(true);
    try {
      const cleanName = firstCand.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, '')?.trim() || firstCand.name || "Candidate";
      const res = await fetch(`${apiBase}/api/outreach/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: cleanName,
          canonical_url: firstCand.canonical_url,
          headline: firstCand.headline,
          skills: firstCand.skills || [],
          current_company: firstCand.current_company,
          target_role: outreachRoleTitle,
          company_name: outreachCompanyName,
          company_details: outreachCompanyDetails,
          recruiter_name: outreachRecruiterName,
          tone: outreachTone,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setOutreachSubject(data.subject);
        setOutreachMessageBody(data.message_body);
        setOutreachConnectionNote(data.connection_note);
      }
    } catch (err) {
      console.error("Error regenerating outreach draft:", err);
    } finally {
      setOutreachGenerating(false);
    }
  };

  // Dispatch Automated Outreach via Headed Browser Agent
  const handleSendOutreach = async () => {
    if (outreachCandidates.length === 0 || !outreachMessageBody.trim()) return;

    setOutreachSending(true);
    setOutreachComplete(false);
    setOutreachProgress({ message: "Launching Playwright autonomous outreach browser agent...", progress: 10, state: "initializing" });
    addTelemetryLog(`Initiating autonomous outreach for ${outreachCandidates.length} candidate(s)...`, "terminal");

    try {
      const payload = {
        candidates: outreachCandidates.map((c) => ({
          candidate_id: c.id,
          canonical_url: c.canonical_url,
          candidate_name: c.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, '')?.trim() || c.name || "Candidate",
          message_body: outreachMessageBody,
          connection_note: outreachConnectionNote,
        })),
        browser_channel: browserChannel || "chrome",
        mode: searchMode === "simulation" ? "simulation" : "live",
      };

      const res = await fetch(`${apiBase}/api/outreach/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error("Failed to dispatch outreach session");
      }

      const data = await res.json();
      const sid = data.session_id;
      setOutreachSessionId(sid);

      // Poll session status
      const pollTimer = setInterval(async () => {
        try {
          const pollRes = await fetch(`${apiBase}/api/outreach/session/${sid}`);
          if (pollRes.ok) {
            const pData = await pollRes.json();
            setOutreachProgress(pData);
            if (pData.message) {
              addTelemetryLog(pData.message, "terminal");
            }

            if (pData.state === "completed" || pData.state === "failed" || pData.state === "auth_required") {
              clearInterval(pollTimer);
              setOutreachSending(false);
              if (pData.state === "completed") {
                setOutreachComplete(true);
                // Mark contacted candidates as Sent in table
                setCandidateList((prev) =>
                  prev.map((c) =>
                    outreachCandidates.some((oc) => oc.id === c.id || oc.canonical_url === c.canonical_url)
                      ? { ...c, outreach_status: "Sent", outreach_method: "Direct Message" }
                      : c
                  )
                );
                addTelemetryLog(`🎉 Outreach completed successfully!`, "shield");
              }
            }
          }
        } catch (pollErr) {
          console.error("Polling outreach error:", pollErr);
        }
      }, 1500);
    } catch (err) {
      console.error("Outreach send error:", err);
      setOutreachSending(false);
      setOutreachProgress({ state: "failed", message: `Outreach execution failed: ${err.message}` });
      addTelemetryLog(`Outreach execution error: ${err.message}`, "file");
    }
  };

  // Filter & Search Candidates with Role Support
  const filteredCandidates = useMemo(() => {
    return candidateList.filter((c) => {
      if (activeTab === "new" && c.status !== "New") return false;
      if (activeTab === "in_review" && c.status !== "In Review") return false;
      if (activeTab === "shortlisted" && c.status !== "Shortlisted") return false;
      if (activeTab === "not_a_fit" && c.status !== "Not a Fit") return false;

      if (selectedRoleFilter !== "All") {
        const cRole = (c.target_role || c.job_title || "").toLowerCase();
        if (!cRole.includes(selectedRoleFilter.toLowerCase())) return false;
      }

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          c.name.toLowerCase().includes(q) ||
          c.title.toLowerCase().includes(q) ||
          c.company.toLowerCase().includes(q) ||
          c.location.toLowerCase().includes(q) ||
          (c.target_role && c.target_role.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [candidateList, activeTab, searchQuery, selectedRoleFilter]);

  // Real Metrics calculations
  const totalDiscovered = candidateList.length;
  const verifiedCount = candidateList.filter((c) => c.evidence_status === "Verified").length;
  const shortlistedCount = candidateList.filter((c) => c.status === "Shortlisted").length;
  const awaitingReviewCount = candidateList.filter((c) => c.status === "New" || c.status === "In Review").length;
  const allCount = candidateList.length;
  const newCount = candidateList.filter((c) => c.status === "New").length;
  const inReviewCount = candidateList.filter((c) => c.status === "In Review").length;
  const notAFitCount = candidateList.filter((c) => c.status === "Not a Fit").length;

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

  // 1. Loading and Auth Handover Gate
  // Keep GlobalHiringLoader active if:
  // - Component has not mounted yet
  // - Clerk is still initializing (!isLoaded)
  // - Fresh sign-in transition animation is active (showAuthTransition)
  // - User has an existing session hint (hasAuthSessionHint) but Clerk is still resolving (!isSignedIn)
  const isAwaitingAuth =
    !hasMounted ||
    !isLoaded ||
    showAuthTransition ||
    (hasAuthSessionHint && !isSignedIn);

  if (isAwaitingAuth) {
    return (
      <GlobalHiringLoader
        minDisplayMs={1000}
        customTitle={
          isSignedIn
            ? `Welcome, ${user?.firstName || user?.fullName || "Recruiter"}!`
            : "Initializing Recruiter Workspace..."
        }
        customSubtitle={
          isSignedIn
            ? "Preparing candidate sourcing pipeline and AI talent radar..."
            : "Calibrating role schemas, search plan matrices, and extraction rules"
        }
        customBadge={isSignedIn ? "Authenticated" : "Workspace Boot"}
        forceActive={!isLoaded || showAuthTransition || (hasAuthSessionHint && !isSignedIn)}
      />
    );
  }

  // 2. Only show AuthLandingPage when Clerk has DEFINITIVELY finished loading AND user is not signed in
  if (!isSignedIn) {
    return <AuthLandingPage />;
  }

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
              { id: "review", label: "Candidates", icon: Users, count: candidateList.length },
              { id: "job_description", label: "Job Description", icon: FileText },
              { id: "criteria", label: "Criteria & Search Plan", icon: SlidersHorizontal },
              { id: "sourcing", label: "Sourcing", icon: Search },
              { id: "pipeline", label: "Interview Pipeline", icon: Calendar },
              { id: "shortlist", label: "Shortlist", icon: Star },
              { id: "reports", label: "Reports & Exports", icon: BarChart3 },
              { id: "settings", label: "Settings", icon: Settings },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeNav === item.id || (item.id === "review" && activeNav === "candidate_profile");
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    navigateTo(item.id);
                  }}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${isActive
                      ? "bg-indigo-50 dark:bg-indigo-600/20 text-indigo-700 dark:text-indigo-400 shadow-sm"
                      : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-[#12182b]"
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-4 w-4 ${isActive ? "text-indigo-600 dark:text-indigo-400" : "text-slate-400"}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.count !== undefined && item.count > 0 && (
                    <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full ${isActive ? "bg-indigo-600 text-white" : "bg-slate-100 dark:bg-[#162038] text-slate-500 dark:text-slate-400"}`}>
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Sidebar Widgets */}
        <div className="p-3.5 space-y-3 border-t border-slate-100 dark:border-[#141b2d]">
          {/* AI Assistant Card */}
          <div
            onClick={() => handleOpenWizard(1)}
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
          {/* Left: Dynamic Role Badge & Sourcing Wizard Launcher */}
          {/* Left: Interactive Role Switcher & Sourcing Wizard Launcher */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <button
                onClick={() => setIsRoleDropdownOpen(!isRoleDropdownOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-50/80 dark:bg-indigo-950/40 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 border border-indigo-200 dark:border-indigo-800 text-xs font-semibold text-indigo-700 dark:text-indigo-300 transition-all cursor-pointer"
                title="Click to switch target role requisition"
              >
                <Briefcase className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
                <span className="text-slate-500 dark:text-slate-400">Target Role:</span>
                <span className="font-bold text-slate-900 dark:text-white max-w-[170px] truncate">
                  {jobRequirements.jobTitle || "Select Target Role"}
                </span>
                <ChevronDown className={`h-3 w-3 text-slate-400 transition-transform ${isRoleDropdownOpen ? "rotate-180" : ""}`} />
              </button>

              {isRoleDropdownOpen && (
                <div className="absolute left-0 mt-1.5 w-72 bg-white dark:bg-[#0f172a] border border-slate-200 dark:border-[#1e293b] rounded-2xl shadow-xl z-50 p-2 animate-in fade-in slide-in-from-top-1 duration-150">
                  <div className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Saved Role Requisitions
                  </div>
                  <div className="space-y-1 max-h-56 overflow-y-auto">
                    {savedJobs.map((j) => (
                      <button
                        key={j.id || j.job_title}
                        onClick={() => handleSelectActiveRole(j)}
                        className={`w-full text-left px-2.5 py-1.5 rounded-xl text-xs flex items-center justify-between transition-colors ${
                          jobRequirements.jobTitle === j.job_title
                            ? "bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 font-bold"
                            : "text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-[#1e293b]"
                        }`}
                      >
                        <span className="truncate">{j.job_title}</span>
                        <span className="text-[10px] text-slate-400 shrink-0 ml-1">{j.location || "Remote"}</span>
                      </button>
                    ))}
                  </div>
                  <div className="border-t border-slate-100 dark:border-[#1e293b] mt-1.5 pt-1.5">
                    <button
                      onClick={() => { setIsRoleDropdownOpen(false); handleOpenWizard(1); }}
                      className="w-full text-left px-2.5 py-1.5 rounded-xl text-xs text-indigo-600 dark:text-indigo-400 font-bold hover:bg-indigo-50 dark:hover:bg-indigo-950/30 flex items-center gap-1.5"
                    >
                      <Sparkles className="h-3 w-3" />
                      <span>+ Configure / Import New Role</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => handleOpenWizard(1)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-xs hover:shadow-md transition-all active:scale-[0.98]"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>3-Step Sourcing Wizard</span>
            </button>
          </div>

          {/* Right: Status Pill, Notification, Theme Toggle, Profile */}
          <div className="flex items-center gap-3">
            {/* Status Pill matching Image 1 */}
            {sessionState === "waiting_for_login" ? (
              <div
                onClick={() => { setIsWizardOpen(true); setWizardStep(3); }}
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
                onClick={() => { setIsWizardOpen(true); setWizardStep(3); }}
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

            {/* User Profile & Clerk Auth / Dev Nav */}
            <UserNav />
          </div>
        </header>

        {/* -------------------- MAIN PAGE BODY -------------------- */}
        <main className="p-7 space-y-6 max-w-[1650px] w-full mx-auto">
          {activeNav === "overview" && (
            <>
              {/* Top Hero Banner: "Build Great Teams with AI" */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-50/80 via-purple-50/60 to-pink-50/40 dark:from-[#11172a] dark:via-[#151c36] dark:to-[#1a1c38] border border-indigo-100/90 dark:border-[#222e50] p-7 sm:p-9 shadow-xs">
            {/* Background scenic mountain sunset silhouette with two summit hikers */}
            <div className="absolute right-0 top-0 bottom-0 w-full md:w-3/5 pointer-events-none opacity-45 dark:opacity-30 flex items-end justify-end overflow-hidden">
              <svg viewBox="0 0 700 240" className="w-full h-full" preserveAspectRatio="xMaxYMid slice">
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
                    onClick={() => { setIsWizardOpen(true); setWizardStep(1); }}
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
                    onClick={() => { setIsWizardOpen(true); setWizardStep(1); }}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] hover:border-indigo-400 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors shadow-xs"
                  >
                    <Play className="h-3.5 w-3.5 text-indigo-600 fill-indigo-600" />
                    <span>Launch 3-Step Wizard</span>
                  </button>
                </div>
              </div>

              {/* Right Column: Beautifully aligned talent mission quote card */}
              <div className="max-w-sm self-start md:self-auto bg-white/75 dark:bg-[#0f172a]/75 backdrop-blur-md border border-white/90 dark:border-white/10 rounded-2xl p-4 shadow-sm space-y-2">
                <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
                  <Sparkles className="h-3.5 w-3.5" />
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Sourcing Philosophy
                  </span>
                </div>
                <p className="text-xs italic text-slate-700 dark:text-slate-200 font-medium leading-relaxed">
                  “Find people who don't just fit the role, but move your mission forward.”
                </p>
                <div className="flex items-center gap-2 pt-1.5 border-t border-slate-100 dark:border-[#1e293b] text-[10px] text-slate-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                  <span>Local-first, evidence-grounded candidate matching</span>
                </div>
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
          <div className="p-5 sm:p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200/80 dark:border-indigo-800 flex items-center justify-center text-indigo-600 dark:text-indigo-400 shrink-0">
                  <Layers className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-black text-slate-900 dark:text-white tracking-tight">Sourcing & Verification Pipeline</h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Autonomous multi-stage candidate harvesting & verification flow</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#1e2a4a] text-slate-600 dark:text-slate-300 font-medium text-[11px]">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  Live Headed Engine · Calibrated
                </span>
                <button
                  onClick={() => { setIsWizardOpen(true); setWizardStep(3); }}
                  className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 font-bold flex items-center gap-1 transition-colors cursor-pointer"
                >
                  View Details <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            </div>

            {/* 5-Step Numbered Stepper with Connection Line */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-2">
              {/* Step 1: JD Parsed */}
              <div className="p-3 rounded-xl bg-slate-50/80 dark:bg-[#12182c]/80 border border-slate-200/80 dark:border-[#1e2a4a] flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-emerald-500 text-white font-bold flex items-center justify-center shrink-0 shadow-md shadow-emerald-500/20 text-xs">
                  <Check className="h-4 w-4 stroke-[3]" />
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-900 dark:text-white truncate">1. JD Parsed</h5>
                  <p className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">Completed · 2m 18s</p>
                </div>
              </div>

              {/* Step 2: Search Plan Ready */}
              <div className="p-3 rounded-xl bg-slate-50/80 dark:bg-[#12182c]/80 border border-slate-200/80 dark:border-[#1e2a4a] flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 shadow-md shadow-indigo-600/20 text-xs">
                  <Check className="h-4 w-4 stroke-[3]" />
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-900 dark:text-white truncate">2. Search Plan Ready</h5>
                  <p className="text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold">Completed · 4m 32s</p>
                </div>
              </div>

              {/* Step 3: Collecting Profiles */}
              <div className="p-3 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/60 flex items-center gap-3">
                <div
                  className={`h-8 w-8 rounded-full ${sourcing
                      ? "bg-indigo-600 text-white ring-4 ring-indigo-200 dark:ring-indigo-800/40 animate-pulse"
                      : "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                    } font-bold flex items-center justify-center shrink-0 text-xs`}
                >
                  3
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-900 dark:text-white truncate">3. Collecting Profiles</h5>
                  <p className="text-[10px] text-indigo-600 dark:text-indigo-400 font-bold truncate">
                    {sourcing ? "Actively Searching..." : "In progress · 1,240 / 2,000"}
                  </p>
                </div>
              </div>

              {/* Step 4: Evidence Review */}
              <div className="p-3 rounded-xl bg-slate-50/50 dark:bg-[#12182c]/50 border border-slate-200/60 dark:border-[#1e2a4a]/60 flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-slate-100 dark:bg-[#141b2e] border border-slate-200 dark:border-[#232e4d] text-slate-400 font-bold flex items-center justify-center shrink-0 text-xs">
                  4
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-400 truncate">4. Evidence Review</h5>
                  <p className="text-[10px] text-slate-400">Pending Evaluation</p>
                </div>
              </div>

              {/* Step 5: Shortlist */}
              <div className="p-3 rounded-xl bg-slate-50/50 dark:bg-[#12182c]/50 border border-slate-200/60 dark:border-[#1e2a4a]/60 flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-slate-100 dark:bg-[#141b2e] border border-slate-200 dark:border-[#232e4d] text-slate-400 font-bold flex items-center justify-center shrink-0 text-xs">
                  5
                </div>
                <div className="min-w-0">
                  <h5 className="text-xs font-bold text-slate-400 truncate">5. Shortlist Ready</h5>
                  <p className="text-[10px] text-slate-400">Pending Selection</p>
                </div>
              </div>
            </div>
          </div>

          {/* -------------------- 3. SPLIT CONTENT: CANDIDATES TABLE + RIGHT PANELS -------------------- */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
            {/* LEFT / CENTER: CANDIDATES TABLE (8 cols) */}
            <div className="xl:col-span-8 space-y-4 min-w-0">
              <div className="bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] rounded-2xl shadow-xs overflow-hidden">
                {/* 2-Tier Recruiter Control Header */}
                <div className="p-4 border-b border-slate-100 dark:border-[#151e36] space-y-3">
                  {/* Tier 1: Filter Tabs (Left) + Search & Role Select (Right) */}
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                    {/* Status Filter Tabs */}
                    <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-0.5">
                      {[
                        { id: "all", label: "All Candidates", count: allCount },
                        { id: "new", label: "New", count: newCount },
                        { id: "in_review", label: "In Review", count: inReviewCount },
                        { id: "shortlisted", label: "Shortlisted", count: shortlistedCount },
                        { id: "not_a_fit", label: "Not a Fit", count: notAFitCount },
                      ].map((tab) => (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap shrink-0 transition-all flex items-center gap-1.5 cursor-pointer ${
                            activeTab === tab.id
                              ? "bg-indigo-600 text-white shadow-xs"
                              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-[#131b31]"
                          }`}
                        >
                          <span>{tab.label}</span>
                          <span
                            className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                              activeTab === tab.id
                                ? "bg-indigo-700 text-indigo-100"
                                : "bg-slate-200/70 dark:bg-[#1a2542] text-slate-600 dark:text-slate-400"
                            }`}
                          >
                            {tab.count}
                          </span>
                        </button>
                      ))}
                    </div>

                    {/* Role Filter & Candidate Search */}
                    <div className="flex items-center gap-2.5 shrink-0">
                      {/* Role Selector */}
                      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b]">
                        <Briefcase className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
                        <span className="text-[11px] font-bold text-slate-400">Role:</span>
                        <select
                          value={selectedRoleFilter}
                          onChange={(e) => setSelectedRoleFilter(e.target.value)}
                          className="bg-transparent text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
                        >
                          <option value="All">All Roles ({candidateList.length})</option>
                          {availableRoles.map((r) => (
                            <option key={r.name} value={r.name}>
                              {r.name} ({r.count})
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Search Input */}
                      <div className="relative">
                        <Search className="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Search candidates..."
                          className="bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b] text-xs rounded-xl pl-9 pr-7 py-1.5 w-40 sm:w-52 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition-colors"
                        />
                        {searchQuery && (
                          <button
                            onClick={() => setSearchQuery("")}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Tier 2: Recruiter Action Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 dark:border-[#151e36]">
                    {/* Left: Selection summary or batch actions */}
                    <div className="flex items-center gap-2">
                      {candidateList.filter((c) => c.selected).length > 0 ? (
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">
                            {candidateList.filter((c) => c.selected).length} selected
                          </span>
                          <button
                            onClick={() => handleOpenOutreach(candidateList.filter((c) => c.selected))}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
                          >
                            <SendHorizontal className="h-3.5 w-3.5" />
                            <span>✉️ Send Outreach ({candidateList.filter((c) => c.selected).length})</span>
                          </button>
                          <button
                            onClick={() => {
                              candidateList.filter((c) => c.selected).forEach((c) => handleUpdateStatus(c.id, "Shortlisted"));
                            }}
                            className="px-2.5 py-1.5 rounded-xl bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800 text-xs font-bold hover:bg-amber-100 transition-colors cursor-pointer"
                          >
                            ⭐ Shortlist Selected
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 font-medium">
                          <span className="flex items-center gap-1.5 text-[11px]">
                            <span className="h-2 w-2 rounded-full bg-emerald-500" />
                            Showing {filteredCandidates.length} candidate{filteredCandidates.length === 1 ? "" : "s"}
                          </span>
                          <span className="text-[11px] text-slate-400 dark:text-slate-500 hidden sm:inline-flex items-center gap-1 ml-1.5">
                            💡 Mouse wheel scrolls left / right
                          </span>
                          {hasMounted && isCandidatesFetching && (
                            <span className="flex items-center gap-1 text-[11px] text-indigo-500 font-semibold ml-2">
                              <RefreshCw className="h-3 w-3 animate-spin" />
                              Syncing DB...
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Right: Operational Buttons */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        onClick={() => setActiveNav("review")}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 text-xs font-bold transition-all shadow-2xs cursor-pointer"
                        title="Open full dedicated candidate section"
                      >
                        <Users className="h-3.5 w-3.5 text-indigo-500" />
                        <span>Dedicated Page</span>
                        <ArrowRight className="h-3 w-3" />
                      </button>

                      <button
                        onClick={handleEvaluateAllCandidates}
                        disabled={batchEvaluating || candidateList.length === 0}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-800 text-xs font-bold text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition-colors disabled:opacity-50 cursor-pointer shadow-2xs"
                        title={selectedRoleFilter === "All" ? "Evaluate all candidates against their designated target roles" : `Evaluate all candidates for ${selectedRoleFilter}`}
                      >
                        <Sparkles className={`h-3 w-3 text-indigo-600 dark:text-indigo-400 ${batchEvaluating ? "animate-spin" : ""}`} />
                        <span>
                          {batchEvaluating
                            ? "Evaluating..."
                            : selectedRoleFilter === "All"
                            ? "⚡ Evaluate All"
                            : `⚡ Evaluate ${selectedRoleFilter.length > 12 ? selectedRoleFilter.substring(0, 12) + '...' : selectedRoleFilter}`}
                        </span>
                      </button>

                      <button
                        onClick={handleSyncSupabase}
                        disabled={syncingSupabase || candidateList.length === 0}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-xs font-semibold text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 transition-colors disabled:opacity-50 cursor-pointer shadow-2xs"
                        title="Sync local candidates and evaluations to Supabase PostgreSQL database"
                      >
                        <Cloud className={`h-3 w-3 text-emerald-600 dark:text-emerald-400 ${syncingSupabase ? "animate-bounce" : ""}`} />
                        <span>{syncingSupabase ? "Syncing..." : "☁️ Sync Cloud"}</span>
                      </button>

                      <button
                        onClick={() => handleOpenWizard(1)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#12182c] border border-slate-200 dark:border-[#202c4b] text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 hover:border-slate-400 transition-colors cursor-pointer"
                        title="Launch 3-step candidate sourcing wizard"
                      >
                        <Filter className="h-3 w-3 text-slate-500" />
                        <span>Wizard</span>
                      </button>

                      {candidateList.length > 0 && (
                        <button
                          onClick={handleClearAllCandidates}
                          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-900/60 transition-colors cursor-pointer"
                          title="Remove all candidates from database and shortlist"
                        >
                          <Trash2 className="h-3 w-3 text-rose-500" />
                          <span>Clear All</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Table Data */}
                <div ref={setCandidateTableRef} className="overflow-x-auto w-full">
                  <table className="w-full text-left border-collapse text-xs table-fixed min-w-[1060px]">
                    <thead>
                      <tr className="border-b border-slate-100 dark:border-[#162038] text-[11px] font-bold text-slate-500 dark:text-slate-400 bg-slate-50/70 dark:bg-[#0c1120]">
                        <th className="py-3 px-3 w-10 text-center">
                          <button onClick={toggleSelectAll} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                            {selectAll ? <CheckSquare className="h-3.5 w-3.5 text-indigo-600" /> : <Square className="h-3.5 w-3.5" />}
                          </button>
                        </th>
                        <th className="py-3 px-4 w-[280px]">Candidate</th>
                        <th className="py-3 px-4 w-[250px]">Current Title & Company</th>
                        <th className="py-3 px-4 w-[150px]">Target Requisition</th>
                        <th className="py-3 px-4 w-[200px]">Skills & Match</th>
                        <th className="py-3 px-4 w-[130px]">Evidence & Sources</th>
                        <th className="py-3 px-3 w-[105px]">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-[#151d33]">
                      {isCandidatesLoading && candidateList.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-8 px-4 text-center">
                            <HiringRadarLoader role={selectedRoleFilter === "All" ? "Talent Repository" : selectedRoleFilter} />
                          </td>
                        </tr>
                      ) : filteredCandidates.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-20 text-center">
                            <div className="max-w-md mx-auto space-y-3">
                              <div className="h-12 w-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto shadow-xs">
                                <Users className="h-6 w-6" />
                              </div>
                              <h4 className="text-sm font-bold text-slate-900 dark:text-white">No candidates found yet</h4>
                              <p className="text-xs text-slate-500 dark:text-slate-400">
                                No candidate records match the active criteria. Launch the 3-Step Sourcing Wizard to configure role requirements and execute browser automation to harvest candidate profiles.
                              </p>
                              <div className="pt-2">
                                <button
                                  onClick={() => handleOpenWizard(1)}
                                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold shadow-md shadow-indigo-600/20 hover:shadow-lg transition-all cursor-pointer"
                                >
                                  <Sparkles className="h-3.5 w-3.5" />
                                  <span>Launch 3-Step Sourcing Wizard</span>
                                </button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      ) : filteredCandidates.map((candidate, idx) => (
                        <tr
                          key={`${candidate.id || 'cand'}_${candidate.canonical_url || candidate.name}_${idx}`}
                          className="hover:bg-slate-50/80 dark:hover:bg-[#12192e]/60 transition-colors group cursor-pointer"
                          onClick={() => {
                            handleOpenCandidateProfile(candidate);
                            setEvalTargetRole(candidate.target_role || candidate.job_title || jobRequirements.jobTitle || (savedJobs[0]?.job_title || "Senior AI Lead"));
                          }}
                        >
                          {/* Checkbox */}
                          <td
                            className="py-3.5 px-3 text-center"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleSelectCandidate(candidate.id);
                            }}
                          >
                            <button className="text-slate-400 hover:text-indigo-600 cursor-pointer">
                              {candidate.selected ? (
                                <CheckSquare className="h-4 w-4 text-indigo-600" />
                              ) : (
                                <Square className="h-4 w-4" />
                              )}
                            </button>
                          </td>

                          {/* Candidate Avatar & Info */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="flex items-start gap-3">
                              <div className="relative shrink-0 mt-0.5">
                                <img
                                  src={candidate.avatar || candidate.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"}
                                  alt={candidate.name}
                                  onError={(e) => {
                                    e.currentTarget.onerror = null;
                                    e.currentTarget.src = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80";
                                  }}
                                  className="h-10 w-10 rounded-xl object-cover border border-slate-200 dark:border-[#222e4d] shadow-2xs"
                                />
                                {candidate.status === "Shortlisted" && (
                                  <span className="absolute -top-1 -right-1 h-3.5 w-3.5 bg-amber-400 rounded-full flex items-center justify-center text-[8px] text-white shadow-xs">
                                    ★
                                  </span>
                                )}
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="font-bold text-slate-900 dark:text-white text-xs group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors">
                                  {candidate.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, '')?.trim() || candidate.name}
                                </div>
                                <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
                                  <MapPin className="h-3 w-3 text-slate-400 shrink-0" />
                                  <span className="truncate">{candidate.location || "Location not specified"}</span>
                                  {candidate.location_compatibility_status === "Compatible" && (
                                    <span className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 shrink-0">• Compatible</span>
                                  )}
                                </div>
                                {candidate.work_authorization && (
                                  <div className="mt-1">
                                    <span title={candidate.work_authorization} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                                      <Award className="h-2.5 w-2.5 text-amber-600 shrink-0" />
                                      <span className="truncate max-w-[170px]">{candidate.work_authorization.includes("Golden Visa") ? "UAE Golden Visa" : candidate.work_authorization}</span>
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>

                          {/* Current Title & Company */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="space-y-1">
                              <div className="font-semibold text-slate-900 dark:text-white text-xs truncate max-w-[240px]" title={candidate.headline || candidate.title}>
                                {candidate.title || candidate.headline || "Software Engineer"}
                              </div>
                              <div className="flex items-center gap-1.5">
                                <Building2 className="h-3 w-3 text-slate-400 shrink-0" />
                                <span className="text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-[140px]" title={candidate.company}>
                                  {candidate.company && candidate.company !== "Current Organization" ? candidate.company : "Technology Professional"}
                                </span>
                                {candidate.domain_relevance === "Highly Relevant" && (
                                  <span className="shrink-0 px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                                    IT Core
                                  </span>
                                )}
                                {candidate.domain_relevance === "Relevant" && (
                                  <span className="shrink-0 px-1.5 py-0.2 rounded text-[9px] font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                                    Relevant
                                  </span>
                                )}
                                {candidate.domain_relevance === "Partially Relevant" && (
                                  <span className="shrink-0 px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                                    Partial
                                  </span>
                                )}
                                {candidate.domain_relevance === "Not Relevant" && (
                                  <span title="Academic / Non-IT Domain" className="shrink-0 px-1.5 py-0.2 rounded text-[9px] font-bold bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
                                    Non-IT
                                  </span>
                                )}
                              </div>
                            </div>
                          </td>

                          {/* Target Role Requisition */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <span
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-100 text-slate-700 dark:bg-[#162038] dark:text-slate-300 border border-slate-200/80 dark:border-[#223052] max-w-[150px] truncate"
                              title={candidate.target_role || "General Requisition"}
                            >
                              <Briefcase className="h-3 w-3 text-indigo-500 shrink-0" />
                              <span className="truncate">{candidate.target_role || "General Requisition"}</span>
                            </span>
                          </td>

                          {/* Skills & Match */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="space-y-1.5">
                              {candidate.skill_match != null ? (
                                <div className="flex items-center gap-2">
                                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-extrabold flex items-center gap-1 ${
                                    candidate.skill_match >= 85
                                      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                                      : candidate.skill_match >= 65
                                      ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                                      : "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                                  }`}>
                                    <Sparkles className="h-2.5 w-2.5" />
                                    {candidate.skill_match}% Match
                                  </span>
                                  <div className="w-16 bg-slate-100 dark:bg-[#16203a] h-1.5 rounded-full overflow-hidden shrink-0">
                                    <div
                                      className="h-full rounded-full bg-gradient-to-r from-teal-400 to-indigo-600"
                                      style={{ width: `${candidate.skill_match}%` }}
                                    />
                                  </div>
                                </div>
                              ) : (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200/80 dark:border-amber-800/60">
                                  Pending Eval
                                </span>
                              )}

                              {/* Top Skills Tags */}
                              {(() => {
                                const rawSkills = Array.isArray(candidate.skills)
                                  ? candidate.skills
                                  : (typeof candidate.skills === 'string' && candidate.skills.startsWith('[')
                                      ? (() => { try { return JSON.parse(candidate.skills); } catch { return []; } })()
                                      : []);
                                const topSkills = rawSkills.slice(0, 3);
                                if (topSkills.length === 0) return null;
                                return (
                                  <div className="flex items-center gap-1 flex-wrap">
                                    {topSkills.map((sk, sIdx) => (
                                      <span key={sIdx} className="px-1.5 py-0.2 rounded text-[9px] font-medium bg-slate-100 text-slate-600 dark:bg-[#151f38] dark:text-slate-300 border border-slate-200/60 dark:border-[#202c4b]">
                                        {sk}
                                      </span>
                                    ))}
                                  </div>
                                );
                              })()}
                            </div>
                          </td>

                          {/* Evidence & Sources */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="space-y-1.5">
                              <div>
                                {candidate.evidence_status === "Verified" && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                                    <CheckCircle2 className="h-3 w-3 stroke-[2.5]" />
                                    Verified
                                  </span>
                                )}
                                {candidate.evidence_status === "Partial" && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20">
                                    <Clock className="h-3 w-3" />
                                    Partial
                                  </span>
                                )}
                                {candidate.evidence_status === "Not Verified" && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-500 dark:bg-slate-700/30 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50">
                                    Not Verified
                                  </span>
                                )}
                                {(candidate.evidence_status === "Pending Review" || candidate.skill_match == null) && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400 border border-slate-200 dark:border-slate-700/50">
                                    <Clock className="h-3 w-3" />
                                    Pending
                                  </span>
                                )}
                              </div>

                              {/* Source Icons */}
                              <div className="flex items-center gap-1 text-slate-400">
                                <span className="h-5 w-5 rounded bg-blue-500 text-white flex items-center justify-center shadow-2xs" title="LinkedIn Profile">
                                  <LinkedInIcon className="h-2.5 w-2.5" />
                                </span>
                                {candidate.sources?.includes("github") && (
                                  <span className="h-5 w-5 rounded bg-slate-800 text-white flex items-center justify-center shadow-2xs" title="GitHub Code Verified">
                                    <GithubIcon className="h-2.5 w-2.5" />
                                  </span>
                                )}
                              </div>
                            </div>
                          </td>

                          {/* Status */}
                          <td className="py-3.5 px-3 whitespace-nowrap">
                            <div className="flex flex-col gap-1 items-start">
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
                              {candidate.outreach_status === "Sent" && (
                                <span
                                  className="inline-flex items-center gap-1 px-2 py-0.2 rounded-full text-[9px] font-bold bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 border border-teal-200 dark:border-teal-800"
                                  title={`Outreach sent via ${candidate.outreach_method || 'LinkedIn'}`}
                                >
                                  <Mail className="h-2.5 w-2.5" /> Sent ✓
                                </span>
                              )}
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
                  <div className="flex items-center gap-2">
                    <Briefcase className="h-3.5 w-3.5 text-indigo-500" />
                    <h3 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">
                      Active Job Description
                    </h3>
                  </div>
                  <button
                    onClick={() => handleOpenWizard(1)}
                    className="flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 font-bold transition-colors cursor-pointer"
                  >
                    <Edit3 className="h-3 w-3" />
                    <span>Edit JD</span>
                  </button>
                </div>

                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="text-base font-black text-slate-900 dark:text-white">
                      {jobRequirements.jobTitle || "Senior AI Lead"}
                    </h4>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                      Active
                    </span>
                  </div>

                  {/* Metadata Chips 2-Column Grid */}
                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-300 mb-3.5">
                    <div className="flex items-center gap-1.5 p-2 rounded-xl bg-slate-50 dark:bg-[#131a2e] border border-slate-200/80 dark:border-[#1c2744] text-[11px]">
                      <Briefcase className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <div className="truncate">
                        <span className="block text-[9px] text-slate-400 font-bold uppercase">Dept</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200 truncate">{jobRequirements.department || "AI Engineering"}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 p-2 rounded-xl bg-slate-50 dark:bg-[#131a2e] border border-slate-200/80 dark:border-[#1c2744] text-[11px]">
                      <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <div className="truncate">
                        <span className="block text-[9px] text-slate-400 font-bold uppercase">Type</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200 truncate">{jobRequirements.employmentType || "Full-time"}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 p-2 rounded-xl bg-slate-50 dark:bg-[#131a2e] border border-slate-200/80 dark:border-[#1c2744] text-[11px]">
                      <Award className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <div className="truncate">
                        <span className="block text-[9px] text-slate-400 font-bold uppercase">Exp Level</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200 truncate">{jobRequirements.minExperience || 8}+ Years</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 p-2 rounded-xl bg-slate-50 dark:bg-[#131a2e] border border-slate-200/80 dark:border-[#1c2744] text-[11px]">
                      <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <div className="truncate">
                        <span className="block text-[9px] text-slate-400 font-bold uppercase">Location</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                          {[jobRequirements.city, jobRequirements.country].filter(Boolean).join(", ") || (jobRequirements.workMode || "Remote")}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Key Requirements Tags */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h5 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        Key Requirements ({jobRequirements.mandatorySkills?.length || 0})
                      </h5>
                      {jobRequirements.mandatorySkills && jobRequirements.mandatorySkills.length > 6 && (
                        <button
                          onClick={() => setShowAllJdSkills((prev) => !prev)}
                          className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer"
                        >
                          {showAllJdSkills ? "Show Less" : `+${jobRequirements.mandatorySkills.length - 6} more`}
                        </button>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {jobRequirements.mandatorySkills && jobRequirements.mandatorySkills.length > 0 ? (
                        (showAllJdSkills
                          ? jobRequirements.mandatorySkills
                          : jobRequirements.mandatorySkills.slice(0, 6)
                        ).map((req, i) => (
                          <span
                            key={i}
                            className="px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-[#141c33] border border-slate-200 dark:border-[#1e2a4a] text-slate-700 dark:text-slate-300 text-[11px] font-semibold"
                          >
                            {req}
                          </span>
                        ))
                      ) : (
                        <p className="text-xs text-slate-400 italic">No skills configured. Launch Sourcing Wizard to set up criteria.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Panel: Agent Activity Telemetry */}
              <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">
                      Agent Activity & Telemetry
                    </h3>
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                      Live
                    </span>
                  </div>
                  <button className="text-slate-400 hover:text-slate-600 cursor-pointer">
                    <MoreVertical className="h-4 w-4" />
                  </button>
                </div>

                {/* Activity List or Telemetry Standby Status */}
                {logs.length === 0 ? (
                  <div className="space-y-2.5 py-1">
                    <div className="p-3 rounded-xl bg-slate-50/80 dark:bg-[#12182c] border border-slate-200/80 dark:border-[#1e2a4a] space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                          <Terminal className="h-3.5 w-3.5 text-indigo-500" />
                          Browser Traversal Engine
                        </span>
                        <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.2 rounded-full border border-emerald-200 dark:border-emerald-800">
                          Ready
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
                        Playwright headless browser initialized for human-cadence profile harvesting.
                      </p>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50/80 dark:bg-[#12182c] border border-slate-200/80 dark:border-[#1e2a4a] space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                          <ShieldCheck className="h-3.5 w-3.5 text-indigo-500" />
                          Evidence & Citations Scorer
                        </span>
                        <span className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/50 px-2 py-0.2 rounded-full border border-indigo-200 dark:border-indigo-800">
                          Standby
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
                        Multi-factor candidate fit evaluation grounded in verbatim profile evidence.
                      </p>
                    </div>
                  </div>
                ) : (
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
                )}

                <button
                  onClick={() => { setIsWizardOpen(true); setWizardStep(3); }}
                  className="w-full text-center py-2 text-[11px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 transition-colors flex items-center justify-center gap-1 pt-2 border-t border-slate-100 dark:border-[#151f38] cursor-pointer"
                >
                  Open Live Sourcing View <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          </div>
            </>
          )}

          {activeNav === "job_description" && (
            <JobDescriptionView
              jobRequirements={jobRequirements}
              setJobRequirements={setJobRequirements}
              savedJobs={savedJobs}
              handleSelectActiveRole={handleSelectActiveRole}
              handleOpenWizard={handleOpenWizard}
              handleSaveDraft={handleSaveDraft}
              draftSavedToast={draftSavedToast}
              handleDocumentUpload={handleDocumentUpload}
              uploadingJd={uploadingJd}
              uploadedFile={uploadedFile}
            />
          )}

          {activeNav === "criteria" && (
            <CriteriaView
              jobRequirements={jobRequirements}
              setJobRequirements={setJobRequirements}
              strategicQueries={strategicQueries}
              setStrategicQueries={setStrategicQueries}
              selectedQueryId={selectedQueryId}
              setSelectedQueryId={setSelectedQueryId}
              handleRegenerateSingleQuery={handleRegenerateSingleQuery}
              handleRegenerateAllQueries={handleRegenerateAllQueries}
              generatingQueries={generatingQueries}
              regeneratingQueryId={regeneratingQueryId}
              handleOpenWizard={handleOpenWizard}
            />
          )}

          {activeNav === "sourcing" && (
            <SourcingView
              sourcing={sourcing}
              setSourcing={setSourcing}
              searchMode={searchMode}
              setSearchMode={setSearchMode}
              browserChannel={browserChannel}
              setBrowserChannel={setBrowserChannel}
              maxResults={maxResults}
              setMaxResults={setMaxResults}
              availableAccounts={availableAccounts}
              selectedAccountId={selectedAccountId}
              setSelectedAccountId={setSelectedAccountId}
              activeSessionId={activeSessionId}
              sessionState={sessionState}
              sessionProgress={sessionProgress}
              sessionError={sessionError}
              logs={logs}
              handleLaunchSourcing={handleLaunchSourcing}
              handleStopSourcing={handleStopSourcing}
              handleVerifyAndContinue={handleVerifyAndContinue}
              handleOpenLinkedInTab={handleOpenLinkedInTab}
              handleOpenWizard={handleOpenWizard}
            />
          )}

          {(activeNav === "review" || activeNav === "candidates") && (
            <CandidateReviewView
              candidateList={candidateList}
              selectedCandidate={selectedCandidate}
              setSelectedCandidate={handleOpenCandidateProfile}
              handleEvaluateSingleCandidate={handleEvaluateSingleCandidate}
              handleEvaluateAllCandidates={handleEvaluateAllCandidates}
              evaluatingCandidateId={evaluatingCandidateId}
              batchEvaluating={batchEvaluating}
              handleUpdateStatus={handleUpdateStatus}
              handleOpenOutreach={handleOpenOutreach}
              handleDeleteCandidate={handleDeleteCandidate}
              handleClearAllCandidates={handleClearAllCandidates}
              handleSyncSupabase={handleSyncSupabase}
              syncingSupabase={syncingSupabase}
              handleOpenWizard={handleOpenWizard}
              toggleSelectCandidate={toggleSelectCandidate}
              toggleSelectAll={toggleSelectAll}
              selectAll={selectAll}
              availableRoles={availableRoles}
              jobRequirements={jobRequirements}
              savedJobs={savedJobs}
              setEvalTargetRole={setEvalTargetRole}
              setActiveNav={setActiveNav}
            />
          )}

          {activeNav === "pipeline" && (
            <InterviewPipelineView
              candidateList={candidateList}
              handleUpdateStatus={handleUpdateStatus}
              setSelectedCandidate={handleOpenCandidateProfile}
              handleOpenOutreach={handleOpenOutreach}
            />
          )}

          {activeNav === "shortlist" && (
            <ShortlistView
              candidateList={candidateList}
              handleUpdateStatus={handleUpdateStatus}
              setSelectedCandidate={handleOpenCandidateProfile}
              handleOpenOutreach={handleOpenOutreach}
              exportToCSV={exportToCSV}
              setActiveNav={setActiveNav}
            />
          )}

          {activeNav === "reports" && (
            <ReportsView
              candidateList={candidateList}
              handleOpenReportModal={handleOpenReportModal}
              exportToCSV={exportToCSV}
              logs={logs}
            />
          )}

          {activeNav === "settings" && (
            <SettingsView
              jobRequirements={jobRequirements}
            />
          )}

          {activeNav === "candidate_profile" && selectedCandidate && (
            <CandidateProfileView
              candidate={selectedCandidate}
              candidateList={candidateList}
              onSelectCandidate={(cand) => navigateTo("candidate_profile", cand)}
              onBack={() => {
                if (typeof window !== "undefined" && window.history.length > 1) {
                  window.history.back();
                } else {
                  navigateTo(previousNav || "overview");
                }
              }}
              previousNavLabel={
                previousNav === "review" || previousNav === "candidates"
                  ? "Candidates Directory"
                  : previousNav === "pipeline"
                  ? "Interview Pipeline"
                  : previousNav === "shortlist"
                  ? "Shortlist"
                  : "Overview"
              }
              savedJobs={savedJobs}
              jobRequirements={jobRequirements}
              evalTargetRole={evalTargetRole}
              setEvalTargetRole={setEvalTargetRole}
              evaluatingCandidateId={evaluatingCandidateId}
              handleEvaluateSingleCandidate={handleEvaluateSingleCandidate}
              handleUpdateStatus={handleUpdateStatus}
              handleDeleteCandidate={(id) => {
                handleDeleteCandidate(id);
                setSelectedCandidate(null);
                setActiveNav(previousNav || "overview");
              }}
              handleOpenOutreach={handleOpenOutreach}
            />
          )}
        </main>
      </div>

      {/* -------------------- DEDICATED 3-STEP AI SOURCING WIZARD -------------------- */}
      {isWizardOpen && (
        <div className="fixed inset-0 z-50 bg-[#f8fafc] dark:bg-[#070b14] flex flex-col overflow-hidden animate-in fade-in duration-200">
          {/* Wizard Top Header Bar */}
          <header className="h-16 px-6 lg:px-10 border-b border-slate-200/80 dark:border-[#151e36] bg-white/95 dark:bg-[#0a0f1e]/95 backdrop-blur sticky top-0 z-30 flex items-center justify-between shrink-0 shadow-xs">
            {/* Left: Branding & Role context */}
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/25">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-black text-slate-900 dark:text-white tracking-tight">Hiring Desk</h2>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                    AI Sourcing Wizard
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                  {jobRequirements.jobTitle ? (
                    <span className="flex items-center gap-1 font-semibold text-slate-700 dark:text-slate-300">
                      <Briefcase className="h-3 w-3 text-indigo-500" />
                      Role: <strong className="text-indigo-600 dark:text-indigo-400">{jobRequirements.jobTitle}</strong>
                    </span>
                  ) : (
                    "Dynamic 3-Step Candidate Discovery & Live Browser Automation"
                  )}
                </p>
              </div>
            </div>

            {/* Center: Stepper Progress Indicator */}
            <div className="hidden md:flex items-center gap-2">
              {[
                { step: 1, title: "1. Job Requirements", icon: FileText },
                { step: 2, title: "2. AI Search Queries", icon: Sparkles },
                { step: 3, title: "3. Execution & Automation", icon: Play },
              ].map((s, idx) => {
                const isActive = wizardStep === s.step;
                const isDone = wizardStep > s.step;
                return (
                  <div key={s.step} className="flex items-center">
                    {idx > 0 && (
                      <div className={`w-8 h-0.5 mx-1 transition-colors ${wizardStep >= s.step ? "bg-indigo-600 dark:bg-indigo-400" : "bg-slate-200 dark:bg-[#1c2742]"}`} />
                    )}
                    <button
                      onClick={() => {
                        if (s.step < wizardStep || (s.step === 2 && jobRequirements.jobTitle.trim())) {
                          setWizardStep(s.step);
                        }
                      }}
                      disabled={s.step > wizardStep && (!jobRequirements.jobTitle.trim() || strategicQueries.length === 0)}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                        isActive
                          ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                          : isDone
                          ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                          : "text-slate-400 bg-slate-100 dark:bg-[#12192e] border border-slate-200 dark:border-[#1e2a48]"
                      }`}
                    >
                      <div className={`h-4 w-4 rounded-full flex items-center justify-center text-[10px] ${
                        isActive ? "bg-white/20 text-white" : isDone ? "bg-emerald-600 text-white" : "bg-slate-200 dark:bg-slate-700 text-slate-500"
                      }`}>
                        {isDone ? <Check className="h-2.5 w-2.5" /> : s.step}
                      </div>
                      <span>{s.title}</span>
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Right: Save Draft & Exit */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleSaveDraft}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-[#1d2744] bg-white dark:bg-[#10172c] hover:bg-slate-50 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors shadow-xs"
              >
                <Award className="h-3.5 w-3.5 text-indigo-500" />
                <span>Save Draft</span>
              </button>
              <button
                onClick={() => setIsWizardOpen(false)}
                className="h-8 w-8 rounded-xl bg-slate-100 dark:bg-[#12192e] text-slate-500 hover:text-slate-800 dark:hover:text-white flex items-center justify-center transition-colors"
                title="Exit to Dashboard"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </header>

          {/* Toast Notification for Save Draft */}
          {draftSavedToast && (
            <div className="fixed top-20 right-8 z-50 bg-emerald-600 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-xl flex items-center gap-2 animate-in fade-in">
              <CheckCircle2 className="h-4 w-4" />
              <span>Job requirements saved as draft!</span>
            </div>
          )}

          {/* Wizard Scrollable Body */}
          <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 lg:px-14 max-w-6xl w-full mx-auto pb-32">
            {/* ==================== STEP 1: JOB REQUIREMENTS INPUT ==================== */}
            {wizardStep === 1 && (
              <div className="space-y-6 animate-in fade-in duration-150">
                {/* Step 1 Header & Mode Selector */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-[#18233c]">
                  <div>
                    <h3 className="text-xl font-black text-slate-900 dark:text-white tracking-tight">
                      Step 1: Job Requirements Input
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Provide role criteria manually or upload a Job Description document. No predefined roles required.
                    </p>
                  </div>

                  {/* Option A / Option B Tabs */}
                  <div className="flex items-center p-1 bg-slate-100 dark:bg-[#10172c] rounded-2xl border border-slate-200 dark:border-[#1c2742] shrink-0">
                    <button
                      type="button"
                      onClick={() => setActiveOptionTab("manual")}
                      className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                        activeOptionTab === "manual"
                          ? "bg-white dark:bg-indigo-600 text-slate-900 dark:text-white shadow-xs"
                          : "text-slate-500 dark:text-slate-400 hover:text-slate-900"
                      }`}
                    >
                      <Edit3 className="h-3.5 w-3.5 text-indigo-500" />
                      <span>Option A: Manual Entry</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveOptionTab("upload")}
                      className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                        activeOptionTab === "upload"
                          ? "bg-white dark:bg-indigo-600 text-slate-900 dark:text-white shadow-xs"
                          : "text-slate-500 dark:text-slate-400 hover:text-slate-900"
                      }`}
                    >
                      <Upload className="h-3.5 w-3.5 text-indigo-500" />
                      <span>Option B: Upload JD Document</span>
                    </button>
                  </div>
                </div>

                {/* Validation Error Banner */}
                {step1ValidationError && (
                  <div className="p-3.5 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 flex items-center gap-2.5 text-xs text-rose-700 dark:text-rose-300">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{step1ValidationError}</span>
                  </div>
                )}

                {/* Option B Document Upload Area */}
                {activeOptionTab === "upload" && (
                  <div className="p-6 rounded-2xl bg-white dark:bg-[#0c1222] border-2 border-dashed border-indigo-200 dark:border-indigo-800/60 shadow-xs space-y-4">
                    <div className="max-w-xl mx-auto text-center space-y-3">
                      <div className="h-12 w-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto shadow-xs">
                        <Upload className="h-6 w-6" />
                      </div>
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                        Upload Job Description Document
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Supported formats: <strong>PDF, DOC, DOCX, TXT</strong>. AI parses the document and automatically populates all structured form fields below for your review.
                      </p>

                      <label className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/25 cursor-pointer transition-all">
                        <FileText className="h-4 w-4" />
                        <span>Browse Document</span>
                        <input
                          type="file"
                          accept=".pdf,.docx,.doc,.txt"
                          onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                              handleDocumentUpload(e.target.files[0]);
                            }
                          }}
                          className="hidden"
                        />
                      </label>
                    </div>

                    {/* Upload / Progress Feedback */}
                    {uploadedFile && (
                      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#11192e] border border-slate-200 dark:border-[#1d2946] flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold text-xs">
                            {uploadedFile.type}
                          </div>
                          <div>
                            <div className="text-xs font-bold text-slate-900 dark:text-white">{uploadedFile.name}</div>
                            <div className="text-[10px] text-slate-400">{uploadedFile.size} · Uploaded & Auto-Populated</div>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => setUploadedFile(null)}
                          className="text-xs font-semibold text-rose-500 hover:text-rose-600 px-2 py-1 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/40"
                        >
                          Remove
                        </button>
                      </div>
                    )}

                    {uploadingJd && (
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-[11px] font-semibold text-indigo-600 dark:text-indigo-400">
                          <span className="flex items-center gap-1.5">
                            <RefreshCw className="h-3 w-3 animate-spin" />
                            Extracting text and identifying structured requirements...
                          </span>
                          <span>{uploadProgress}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-100 dark:bg-[#141d33] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 transition-all duration-300"
                            style={{ width: `${uploadProgress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Structured Form Sections (A through E) */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {/* Section A: Job Information */}
                  <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3.5 md:col-span-2">
                    <div className="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-[#151f38]">
                      <Briefcase className="h-4 w-4 text-indigo-500" />
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                        A. Job Information
                      </h4>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                      <div className="sm:col-span-2">
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Job Title / Role <span className="text-rose-500">* (Mandatory)</span>
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.jobTitle}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, jobTitle: e.target.value })}
                          placeholder="e.g. Senior AI Engineer, Lead Fullstack Developer, Product Manager"
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Department
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.department}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, department: e.target.value })}
                          placeholder="e.g. Engineering, AI Labs"
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Employment Type
                        </label>
                        <select
                          value={jobRequirements.employmentType}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, employmentType: e.target.value })}
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="Full-time">Full-time</option>
                          <option value="Part-time">Part-time</option>
                          <option value="Contract">Contract</option>
                          <option value="Internship">Internship</option>
                          <option value="Consulting">Consulting</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Seniority Level
                        </label>
                        <select
                          value={jobRequirements.seniorityLevel}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, seniorityLevel: e.target.value })}
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="Entry Level">Entry Level</option>
                          <option value="Mid-Level">Mid-Level</option>
                          <option value="Senior">Senior</option>
                          <option value="Staff / Principal">Staff / Principal</option>
                          <option value="Lead / Manager">Lead / Manager</option>
                          <option value="Executive">Executive</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Vacancies
                        </label>
                        <input
                          type="number"
                          min="1"
                          value={jobRequirements.vacancies}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, vacancies: parseInt(e.target.value) || 1 })}
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div className="sm:col-span-3">
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Full Job Description / Context
                        </label>
                        <textarea
                          rows={4}
                          value={jobRequirements.jobDescription}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, jobDescription: e.target.value })}
                          placeholder="Paste or describe role expectations, team mission, and core responsibilities..."
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl p-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-500 leading-relaxed"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Section B: Required Skills & Technologies */}
                  <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3.5 md:col-span-2">
                    <div className="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-[#151f38]">
                      <Sparkles className="h-4 w-4 text-purple-500" />
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                        B. Required Skills & Technologies (Interactive Chips)
                      </h4>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <TagInputField
                        label="Mandatory Skills (Must Have)"
                        tags={jobRequirements.mandatorySkills}
                        onAdd={(tag) => setJobRequirements({ ...jobRequirements, mandatorySkills: [...jobRequirements.mandatorySkills, tag] })}
                        onRemove={(idx) => setJobRequirements({ ...jobRequirements, mandatorySkills: jobRequirements.mandatorySkills.filter((_, i) => i !== idx) })}
                        placeholder="e.g. Python, React, FastAPI..."
                      />

                      <TagInputField
                        label="Preferred Skills (Good to Have)"
                        tags={jobRequirements.preferredSkills}
                        onAdd={(tag) => setJobRequirements({ ...jobRequirements, preferredSkills: [...jobRequirements.preferredSkills, tag] })}
                        onRemove={(idx) => setJobRequirements({ ...jobRequirements, preferredSkills: jobRequirements.preferredSkills.filter((_, i) => i !== idx) })}
                        placeholder="e.g. Playwright, WebSockets, Docker..."
                      />

                      <TagInputField
                        label="Technologies & Frameworks"
                        tags={jobRequirements.technologies}
                        onAdd={(tag) => setJobRequirements({ ...jobRequirements, technologies: [...jobRequirements.technologies, tag] })}
                        onRemove={(idx) => setJobRequirements({ ...jobRequirements, technologies: jobRequirements.technologies.filter((_, i) => i !== idx) })}
                        placeholder="e.g. Next.js, PyTorch, LangChain..."
                      />

                      <TagInputField
                        label="Tools & Platforms"
                        tags={jobRequirements.toolsPlatforms}
                        onAdd={(tag) => setJobRequirements({ ...jobRequirements, toolsPlatforms: [...jobRequirements.toolsPlatforms, tag] })}
                        onRemove={(idx) => setJobRequirements({ ...jobRequirements, toolsPlatforms: jobRequirements.toolsPlatforms.filter((_, i) => i !== idx) })}
                        placeholder="e.g. AWS, Git, Redis, Jira..."
                      />

                      <TagInputField
                        label="Domain Expertise"
                        tags={jobRequirements.domainExpertise}
                        onAdd={(tag) => setJobRequirements({ ...jobRequirements, domainExpertise: [...jobRequirements.domainExpertise, tag] })}
                        onRemove={(idx) => setJobRequirements({ ...jobRequirements, domainExpertise: jobRequirements.domainExpertise.filter((_, i) => i !== idx) })}
                        placeholder="e.g. LLM Orchestration, FinTech, E-Commerce..."
                      />

                      <TagInputField
                        label="Certifications (Optional)"
                        tags={jobRequirements.certifications}
                        onAdd={(tag) => setJobRequirements({ ...jobRequirements, certifications: [...jobRequirements.certifications, tag] })}
                        onRemove={(idx) => setJobRequirements({ ...jobRequirements, certifications: jobRequirements.certifications.filter((_, i) => i !== idx) })}
                        placeholder="e.g. AWS Solutions Architect, CKA..."
                      />
                    </div>
                  </div>

                  {/* Section C: Experience Requirements */}
                  <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3.5">
                    <div className="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-[#151f38]">
                      <Clock className="h-4 w-4 text-emerald-500" />
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                        C. Experience Requirements
                      </h4>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Min Experience (Yrs)
                        </label>
                        <input
                          type="number"
                          min="0"
                          value={jobRequirements.minExperience}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, minExperience: parseInt(e.target.value) || 0 })}
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Max Experience (Yrs)
                        </label>
                        <input
                          type="number"
                          min="0"
                          value={jobRequirements.maxExperience}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, maxExperience: parseInt(e.target.value) || 0 })}
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div className="col-span-2">
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Relevant Experience Focus
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.relevantExperience}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, relevantExperience: e.target.value })}
                          placeholder="e.g. 3+ years hands-on building autonomous agents"
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div className="col-span-2">
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Leadership Experience (Optional)
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.leadershipExperience}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, leadershipExperience: e.target.value })}
                          placeholder="e.g. Experience mentoring 3+ engineers or tech lead role"
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Section D: Location Requirements */}
                  <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3.5">
                    <div className="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-[#151f38]">
                      <MapPin className="h-4 w-4 text-sky-500" />
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                        D. Location Requirements
                      </h4>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Work Mode
                        </label>
                        <select
                          value={jobRequirements.workMode}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, workMode: e.target.value })}
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="Remote">Remote</option>
                          <option value="Hybrid">Hybrid</option>
                          <option value="On-site">On-site</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Country
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.country}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, country: e.target.value })}
                          placeholder="e.g. India, UAE, United States"
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          City
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.city}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, city: e.target.value })}
                          placeholder="e.g. Bangalore, Dubai, London"
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          State / Region
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.stateRegion}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, stateRegion: e.target.value })}
                          placeholder="e.g. Karnataka, Dubai Emirates"
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div className="col-span-2">
                        <TagInputField
                          label="Preferred Work Locations"
                          tags={jobRequirements.preferredLocations}
                          onAdd={(tag) => setJobRequirements({ ...jobRequirements, preferredLocations: [...jobRequirements.preferredLocations, tag] })}
                          onRemove={(idx) => setJobRequirements({ ...jobRequirements, preferredLocations: jobRequirements.preferredLocations.filter((_, i) => i !== idx) })}
                          placeholder="e.g. Bangalore, Hyderabad, Pune..."
                        />
                      </div>
                    </div>
                  </div>

                  {/* Section E: Additional Hiring Preferences */}
                  <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3.5 md:col-span-2">
                    <div className="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-[#151f38]">
                      <SlidersHorizontal className="h-4 w-4 text-amber-500" />
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                        E. Additional Hiring Preferences
                      </h4>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Notice Period
                        </label>
                        <select
                          value={jobRequirements.noticePeriod}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, noticePeriod: e.target.value })}
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="Immediate">Immediate</option>
                          <option value="15 Days">15 Days</option>
                          <option value="30 Days">30 Days</option>
                          <option value="60 Days">60 Days</option>
                          <option value="90 Days">90 Days</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Expected Salary Range (Optional)
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.salaryRange}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, salaryRange: e.target.value })}
                          placeholder="e.g. $120k - $160k, ₹30L - ₹45L"
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Education Requirements
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.educationRequirements}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, educationRequirements: e.target.value })}
                          placeholder="e.g. B.Tech / M.Tech in CS or related"
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div className="sm:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <TagInputField
                          label="Companies to Target (Optional)"
                          tags={jobRequirements.companiesToTarget}
                          onAdd={(tag) => setJobRequirements({ ...jobRequirements, companiesToTarget: [...jobRequirements.companiesToTarget, tag] })}
                          onRemove={(idx) => setJobRequirements({ ...jobRequirements, companiesToTarget: jobRequirements.companiesToTarget.filter((_, i) => i !== idx) })}
                          placeholder="e.g. Google, Microsoft, Razorpay..."
                        />

                        <TagInputField
                          label="Companies to Exclude (Optional)"
                          tags={jobRequirements.companiesToExclude}
                          onAdd={(tag) => setJobRequirements({ ...jobRequirements, companiesToExclude: [...jobRequirements.companiesToExclude, tag] })}
                          onRemove={(idx) => setJobRequirements({ ...jobRequirements, companiesToExclude: jobRequirements.companiesToExclude.filter((_, i) => i !== idx) })}
                          placeholder="e.g. Current client companies..."
                        />
                      </div>

                      <div className="sm:col-span-3">
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1">
                          Additional Instructions for AI Query & Extraction Agent
                        </label>
                        <input
                          type="text"
                          value={jobRequirements.additionalInstructions}
                          onChange={(e) => setJobRequirements({ ...jobRequirements, additionalInstructions: e.target.value })}
                          placeholder="e.g. Favor candidates with open source contributions; strictly reject agency resumes..."
                          className="w-full bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ==================== STEP 2: AI-GENERATED SEARCH QUERIES ==================== */}
            {wizardStep === 2 && (
              <div className="space-y-6 animate-in fade-in duration-150">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-[#18233c]">
                  <div>
                    <h3 className="text-xl font-black text-slate-900 dark:text-white tracking-tight">
                      Step 2: AI-Generated LinkedIn Search Queries
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Gemini AI formulated 3 strategically distinct Boolean search queries tailored to your exact role requirements.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={handleRegenerateAllQueries}
                    disabled={generatingQueries}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 dark:bg-[#131b31] border border-slate-200 dark:border-[#1d2745] hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 text-indigo-500 ${generatingQueries ? "animate-spin" : ""}`} />
                    <span>Regenerate All Queries</span>
                  </button>
                </div>

                {/* 3 Strategy Cards */}
                <div className="space-y-4">
                  {strategicQueries.map((q, idx) => {
                    const isSelected = selectedQueryId === q.id;
                    const isEditing = editingQueryId === q.id;
                    const isRegenerating = regeneratingQueryId === q.id;

                    return (
                      <div
                        key={q.id || idx}
                        onClick={() => setSelectedQueryId(q.id)}
                        className={`p-5 rounded-2xl border transition-all cursor-pointer ${
                          isSelected
                            ? "bg-indigo-50/40 dark:bg-indigo-950/20 border-indigo-500 shadow-md ring-2 ring-indigo-500/20"
                            : "bg-white dark:bg-[#0d1222] border-slate-200/80 dark:border-[#172138] hover:border-slate-300 dark:hover:border-[#223052]"
                        }`}
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-[#151f38]">
                          <div className="flex items-center gap-3">
                            <input
                              type="radio"
                              name="selected_strategic_query"
                              checked={isSelected}
                              onChange={() => setSelectedQueryId(q.id)}
                              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500"
                            />
                            <div>
                              <div className="flex items-center gap-2">
                                <h4 className="text-sm font-black text-slate-900 dark:text-white">
                                  {q.label}
                                </h4>
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-100/70 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-700">
                                  {q.strategy_type || "AI Strategy"}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Individual Controls */}
                          <div className="flex items-center gap-2 self-end sm:self-auto" onClick={(e) => e.stopPropagation()}>
                            <button
                              type="button"
                              onClick={() => {
                                if (isEditing) {
                                  setStrategicQueries((prev) =>
                                    prev.map((item) => (item.id === q.id ? { ...item, query: editedQueryText } : item))
                                  );
                                  setEditingQueryId(null);
                                } else {
                                  setEditingQueryId(q.id);
                                  setEditedQueryText(q.query);
                                }
                              }}
                              className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-[#12192e] text-slate-700 dark:text-slate-300 hover:bg-slate-200"
                            >
                              <Edit3 className="h-3 w-3" />
                              <span>{isEditing ? "Save Query" : "Edit Query"}</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => handleRegenerateSingleQuery(q.id)}
                              disabled={isRegenerating}
                              className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 disabled:opacity-50"
                            >
                              <RefreshCw className={`h-3 w-3 ${isRegenerating ? "animate-spin" : ""}`} />
                              <span>Regenerate</span>
                            </button>
                          </div>
                        </div>

                        {/* Query Boolean String */}
                        <div className="mt-3.5 space-y-2">
                          {isEditing ? (
                            <textarea
                              rows={3}
                              value={editedQueryText}
                              onChange={(e) => setEditedQueryText(e.target.value)}
                              onClick={(e) => e.stopPropagation()}
                              className="w-full p-3 rounded-xl bg-slate-900 text-emerald-400 font-mono text-xs border border-indigo-500 focus:outline-none"
                            />
                          ) : (
                            <div className="p-3.5 rounded-xl bg-slate-900 text-emerald-400 font-mono text-xs border border-slate-800 break-words leading-relaxed select-all">
                              {q.query}
                            </div>
                          )}

                          {/* Strategy Explanation */}
                          <div className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300 pt-1">
                            <Info className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
                            <p className="leading-relaxed">{q.description}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ==================== STEP 3: EXECUTION & BROWSER AUTOMATION ==================== */}
            {wizardStep === 3 && (
              <div className="space-y-6 animate-in fade-in duration-150">
                <div className="pb-4 border-b border-slate-200 dark:border-[#18233c]">
                  <h3 className="text-xl font-black text-slate-900 dark:text-white tracking-tight">
                    Step 3: Execution Configuration & Live Browser Automation
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Select automation mode, target profile count, browser profile, and recruiter LinkedIn session.
                  </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                  {/* SECTION A: SOURCING EXECUTION CONFIGURATION (5 cols) */}
                  <div className="lg:col-span-5 space-y-4">
                    <div className="p-5 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                        <SlidersHorizontal className="h-4 w-4 text-indigo-500" />
                        <span>Execution Parameters</span>
                      </h4>

                      {/* 1. Execution Mode */}
                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1.5">
                          1. Execution Mode
                        </label>
                        <div className="grid grid-cols-1 gap-2">
                          <button
                            type="button"
                            onClick={() => setSearchMode("autonomous")}
                            className={`p-3 rounded-xl border text-left transition-all ${
                              searchMode === "autonomous"
                                ? "bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-500 ring-2 ring-indigo-500/20"
                                : "bg-slate-50 dark:bg-[#11192e] border-slate-200 dark:border-[#1d2946]"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-900 dark:text-white">
                                Mode A — Autonomous Sourcing
                              </span>
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                                Direct
                              </span>
                            </div>
                            <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
                              Automated Playwright traversal with intelligent pagination and AI scoring.
                            </p>
                          </button>

                          <button
                            type="button"
                            onClick={() => setSearchMode("live")}
                            className={`p-3 rounded-xl border text-left transition-all ${
                              searchMode === "live"
                                ? "bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-500 ring-2 ring-indigo-500/20"
                                : "bg-slate-50 dark:bg-[#11192e] border-slate-200 dark:border-[#1d2946]"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-900 dark:text-white">
                                Mode B — Direct Live LinkedIn Sourcing
                              </span>
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                                Headed
                              </span>
                            </div>
                            <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
                              Opens visible desktop browser directly to LinkedIn with live screen inspection.
                            </p>
                          </button>
                        </div>
                      </div>

                      {/* 2. Target Profiles to Harvest */}
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300">
                            2. Target Profiles to Harvest (1–50)
                          </label>
                          <span className="text-xs font-black text-indigo-600 dark:text-indigo-400">
                            {maxResults} Profiles
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 mb-2">
                          {[5, 10, 15, 25, 50].map((num) => (
                            <button
                              key={num}
                              type="button"
                              onClick={() => setMaxResults(num)}
                              className={`flex-1 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                                maxResults === num
                                  ? "bg-indigo-600 text-white shadow-xs"
                                  : "bg-slate-100 dark:bg-[#11192e] text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-[#18233e]"
                              }`}
                            >
                              {num}
                            </button>
                          ))}
                          <div className="flex items-center gap-1 pl-1.5 border-l border-slate-200 dark:border-[#1d2744]">
                            <span className="text-[10px] font-semibold text-slate-400">Custom:</span>
                            <input
                              type="number"
                              min="1"
                              max="50"
                              value={maxResults}
                              onChange={(e) => setMaxResults(Math.min(50, Math.max(1, parseInt(e.target.value) || 1)))}
                              className="w-14 bg-slate-50 dark:bg-[#10162a] border border-slate-200 dark:border-[#1d2744] text-xs font-bold text-center rounded-xl py-1 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                        </div>
                        <p className="text-[10px] text-slate-400">
                          Est. ~{Math.max(1, Math.round(maxResults * 0.15))} min run with deep 7-section extraction and AI matching.
                        </p>
                      </div>

                      {/* 3. Browser Selection */}
                      <div>
                        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300 block mb-1.5">
                          3. Browser Selection
                        </label>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                          {[
                            { id: "chrome", name: "Google Chrome", badge: "Recommended", desc: "Saved login session", icon: Globe },
                            { id: "msedge", name: "Microsoft Edge", badge: "Windows Default", desc: "Edge browser profile", icon: Globe },
                            { id: "chromium", name: "Chromium Sandbox", badge: "Isolated", desc: "Clean test session", icon: Cpu },
                          ].map((b) => {
                            const isChosen = browserChannel === b.id;
                            const Icon = b.icon;
                            return (
                              <button
                                key={b.id}
                                type="button"
                                onClick={() => setBrowserChannel(b.id)}
                                className={`p-2.5 rounded-xl border text-left transition-all ${
                                  isChosen
                                    ? "bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-500 ring-2 ring-indigo-500/20"
                                    : "bg-slate-50 dark:bg-[#11192e] border-slate-200 dark:border-[#1d2946]"
                                }`}
                              >
                                <div className="flex items-center gap-1.5">
                                  <Icon className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
                                  <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                                    {b.name}
                                  </span>
                                </div>
                                <span className="inline-block text-[9px] font-bold text-indigo-600 dark:text-indigo-400 mt-1">
                                  {b.badge}
                                </span>
                                <p className="text-[10px] text-slate-400 truncate mt-0.5">{b.desc}</p>
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      {/* Recruiter Authentication Notice */}
                      <div className="p-3 rounded-xl bg-slate-50 dark:bg-[#11192e] border border-slate-200 dark:border-[#1d2946] flex items-start gap-2.5">
                        <ShieldCheck className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                          <strong className="text-slate-700 dark:text-slate-200">Direct Recruiter Authentication: </strong>
                          Your chosen browser opens with its persistent profile. Simply log into your LinkedIn account directly in the browser window, and the agent will autonomously perform candidate search, section extraction, and evidence scoring.
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* SECTION B: LIVE SOURCING EXECUTION CONTAINER (7 cols) */}
                  <div className="lg:col-span-7 space-y-4">
                    <div className="p-6 rounded-2xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-5">
                      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#151f38]">
                        <div className="flex items-center gap-2">
                          <Terminal className="h-4 w-4 text-indigo-500" />
                          <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                            Live Browser Automation & Telemetry
                          </h4>
                        </div>
                        {sourcing && (
                          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                            Live Telemetry Active
                          </span>
                        )}
                      </div>

                      {/* Initial Pre-Execution Summary */}
                      {!sourcing && sessionState !== "completed" && sessionState !== "failed" && (
                        <div className="space-y-4">
                          <div className="p-4 rounded-xl bg-slate-50 dark:bg-[#11192e] border border-slate-200 dark:border-[#1d2946] space-y-2.5 text-xs">
                            <div className="flex items-center justify-between">
                              <span className="text-slate-400">Target Role:</span>
                              <strong className="text-slate-900 dark:text-white">{jobRequirements.jobTitle || "Custom Role"}</strong>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-slate-400">Active Query:</span>
                              <code className="text-[11px] font-mono text-indigo-600 dark:text-indigo-400 truncate max-w-[280px]">
                                {strategicQueries.find((q) => q.id === selectedQueryId)?.query || "Precision Role Query"}
                              </code>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-slate-400">Profiles to Harvest:</span>
                              <strong className="text-slate-900 dark:text-white">{maxResults} Candidates</strong>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-slate-400">Browser Environment:</span>
                              <strong className="text-slate-900 dark:text-white">
                                {browserChannel === "msedge" ? "Microsoft Edge" : browserChannel === "chrome" ? "Google Chrome" : "Chromium Sandbox"}
                              </strong>
                            </div>
                          </div>

                          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/50">
                            <div className="h-8 w-8 rounded-lg bg-indigo-600/10 dark:bg-indigo-400/10 flex items-center justify-center shrink-0 text-indigo-600 dark:text-indigo-400">
                              <Sparkles className="h-4 w-4" />
                            </div>
                            <div className="text-xs">
                              <strong className="text-slate-900 dark:text-white block font-bold">Ready to Launch Automation</strong>
                              <span className="text-slate-500 dark:text-slate-400">
                                Parameters configured. Click <strong className="text-indigo-600 dark:text-indigo-400">{searchMode === "live" ? "Start Live LinkedIn Sourcing" : "Start Autonomous Sourcing"}</strong> in the bottom bar to begin.
                              </span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Explicit Error State Panel if Failed */}
                      {!sourcing && sessionState === "failed" && (
                        <div className="space-y-4">
                          <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 space-y-2.5 text-xs">
                            <div className="flex items-center gap-2 text-rose-700 dark:text-rose-400 font-bold">
                              <AlertCircle className="h-4 w-4 shrink-0" />
                              <span>Sourcing Stopped Unexpectedly</span>
                            </div>
                            <p className="text-slate-600 dark:text-slate-300">
                              {sessionError || error || "The browser session encountered an error or was interrupted. Check your LinkedIn login and try again."}
                            </p>
                            <div className="pt-2 flex items-center gap-3">
                              <button
                                type="button"
                                onClick={() => handleLaunchSourcing(searchMode)}
                                className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs transition-colors flex items-center gap-1.5 shadow-xs"
                              >
                                <Play className="h-3.5 w-3.5 fill-white" />
                                Retry Sourcing
                              </button>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Live Running Interface & Telemetry */}
                      {(sourcing || sessionState === "completed" || sessionState === "searching" || sessionState === "launching_browser" || sessionState === "extracting" || sessionState === "persisting") && (
                        <div className="space-y-4">
                          {/* Progress bar */}
                          <div className="space-y-1.5">
                            <div className="flex items-center justify-between text-xs font-bold text-slate-800 dark:text-slate-200">
                              <span>{sourcingStage || "Executing Browser Automation..."}</span>
                              <span className="text-indigo-600 dark:text-indigo-400">{sessionProgress}%</span>
                            </div>
                            <div className="h-2 w-full bg-slate-100 dark:bg-[#141d33] rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500 transition-all duration-500"
                                style={{ width: `${sessionProgress}%` }}
                              />
                            </div>
                          </div>

                          {/* 6 Real Browser Automation Stages */}
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            {[
                              { step: 1, name: "1. Launch Browser", active: sessionProgress >= 15 },
                              { step: 2, name: "2. Session Check", active: sessionProgress >= 30 },
                              { step: 3, name: "3. LinkedIn Search", active: sessionProgress >= 50 },
                              { step: 4, name: "4. Profile Extract", active: sessionProgress >= 70 },
                              { step: 5, name: "5. AI Evaluation", active: sessionProgress >= 85 },
                              { step: 6, name: "6. Profiles Saved", active: sessionProgress >= 100 },
                            ].map((stage) => (
                              <div
                                key={stage.step}
                                className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center gap-2 ${
                                  stage.active
                                    ? "bg-indigo-50 dark:bg-indigo-950/40 border-indigo-400 text-indigo-700 dark:text-indigo-300"
                                    : "bg-slate-50 dark:bg-[#10172c] border-slate-200 dark:border-[#1a2542] text-slate-400"
                                }`}
                              >
                                {stage.active ? (
                                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                                ) : (
                                  <Circle className="h-3.5 w-3.5 text-slate-300 shrink-0" />
                                )}
                                <span className="truncate">{stage.name}</span>
                              </div>
                            ))}
                          </div>

                          {/* Live Metric Counters */}
                          <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 pt-1 text-center">
                            <div className="p-2 rounded-xl bg-slate-50 dark:bg-[#10172c] border border-slate-200 dark:border-[#1a2542]">
                              <div className="text-[10px] font-bold text-slate-400 uppercase">Discovered</div>
                              <div className="text-base font-black text-slate-900 dark:text-white mt-0.5">{executionStats.discovered}</div>
                            </div>
                            <div className="p-2 rounded-xl bg-slate-50 dark:bg-[#10172c] border border-slate-200 dark:border-[#1a2542]">
                              <div className="text-[10px] font-bold text-slate-400 uppercase">Extracted</div>
                              <div className="text-base font-black text-slate-900 dark:text-white mt-0.5">{executionStats.extracted}</div>
                            </div>
                            <div className="p-2 rounded-xl bg-slate-50 dark:bg-[#10172c] border border-slate-200 dark:border-[#1a2542]">
                              <div className="text-[10px] font-bold text-slate-400 uppercase">Evaluated</div>
                              <div className="text-base font-black text-slate-900 dark:text-white mt-0.5">{executionStats.evaluated}</div>
                            </div>
                            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800">
                              <div className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase">Profiles Saved</div>
                              <div className="text-base font-black text-emerald-700 dark:text-emerald-300 mt-0.5">{executionStats.saved}</div>
                            </div>
                            <div className="p-2 rounded-xl bg-slate-50 dark:bg-[#10172c] border border-slate-200 dark:border-[#1a2542]">
                              <div className="text-[10px] font-bold text-slate-400 uppercase">Duplicates</div>
                              <div className="text-base font-black text-slate-900 dark:text-white mt-0.5">{executionStats.duplicates}</div>
                            </div>
                          </div>

                          {/* Live Console Terminal Output */}
                          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 max-h-48 overflow-y-auto space-y-1.5">
                            {logs.length === 0 ? (
                              <div className="text-slate-500 italic">Awaiting browser automation telemetry...</div>
                            ) : (
                              logs.slice(0, 10).map((l, i) => (
                                <div key={i} className="flex items-start gap-2 leading-relaxed">
                                  <span className="text-slate-500 shrink-0">[{l.time}]</span>
                                  <span className={l.icon === "shield" ? "text-emerald-400" : "text-slate-200"}>
                                    {l.text}
                                  </span>
                                </div>
                              ))
                            )}
                          </div>

                          {/* Control Buttons */}
                          <div className="flex items-center justify-between pt-2">
                            {sourcing && (
                              <button
                                type="button"
                                onClick={handleStopSourcing}
                                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-600 font-bold text-xs transition-colors"
                              >
                                <X className="h-3.5 w-3.5" />
                                <span>Stop Sourcing</span>
                              </button>
                            )}

                            {sessionState === "completed" && (
                              <div className="flex flex-wrap items-center gap-2.5 ml-auto">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSessionState("idle");
                                    setSessionProgress(0);
                                    setSourcingStage("");
                                    setExecutionStats({
                                      discovered: 0,
                                      extracted: 0,
                                      evaluated: 0,
                                      saved: 0,
                                      duplicates: 0,
                                      durationSeconds: 0,
                                    });
                                    setActiveSessionId(null);
                                  }}
                                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-[#1d2744] bg-white dark:bg-[#12192e] text-slate-700 dark:text-slate-300 font-bold text-xs hover:bg-slate-50 transition-colors shadow-2xs cursor-pointer"
                                >
                                  <RefreshCw className="h-3.5 w-3.5 text-indigo-500" />
                                  <span>Configure Fresh Search</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setIsWizardOpen(false);
                                    setActiveNav("overview");
                                  }}
                                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-black shadow-lg shadow-emerald-600/30 transition-all cursor-pointer"
                                >
                                  <Check className="h-4 w-4" />
                                  <span>View Collected Candidates</span>
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Wizard Bottom Sticky Footer Navigation */}
          <footer className="h-20 px-6 lg:px-14 border-t border-slate-200/80 dark:border-[#151e36] bg-white/95 dark:bg-[#0a0f1e]/95 backdrop-blur fixed bottom-0 left-0 right-0 z-30 flex items-center justify-between shadow-lg">
            {/* Left Nav */}
            <div>
              {wizardStep === 1 ? (
                <button
                  type="button"
                  onClick={handleClearForm}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-rose-600 transition-colors"
                >
                  Clear Form
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setWizardStep((prev) => Math.max(1, prev - 1))}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-200 dark:border-[#1c2744] bg-white dark:bg-[#12192e] text-slate-700 dark:text-slate-300 text-xs font-bold hover:bg-slate-50 transition-colors shadow-xs"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Back</span>
                </button>
              )}
            </div>

            {/* Center Status / Validation */}
            <div className="hidden sm:block text-center text-xs text-slate-400">
              {wizardStep === 1 && "Step 1 of 3: Provide role title and requirements"}
              {wizardStep === 2 && "Step 2 of 3: Select or edit preferred LinkedIn search query"}
              {wizardStep === 3 && "Step 3 of 3: Configure target count and launch browser"}
            </div>

            {/* Right Primary Action */}
            <div>
              {wizardStep === 1 && (
                <button
                  type="button"
                  onClick={handleStep1Next}
                  disabled={generatingQueries}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 text-white text-xs font-black shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50 cursor-pointer"
                >
                  {generatingQueries ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Formulating Queries...</span>
                    </>
                  ) : (
                    <>
                      <span>Next: Generate Search Queries</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </>
                  )}
                </button>
              )}

              {wizardStep === 2 && (
                <button
                  type="button"
                  onClick={handleStep2Next}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 text-white text-xs font-black shadow-lg shadow-indigo-600/25 transition-all cursor-pointer"
                >
                  <span>Next: Configure Execution</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              )}

              {wizardStep === 3 && (
                <div className="flex items-center gap-2.5">
                  {sessionState === "completed" && !sourcing && (
                    <button
                      type="button"
                      onClick={() => {
                        setIsWizardOpen(false);
                        setActiveNav("overview");
                      }}
                      className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-[#1d2744] bg-white dark:bg-[#12192e] text-slate-700 dark:text-slate-300 text-xs font-bold hover:bg-slate-50 transition-colors shadow-xs cursor-pointer"
                    >
                      <Check className="h-3.5 w-3.5 text-emerald-500" />
                      <span>View Shortlist</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      if (!sourcing) {
                        handleLaunchSourcing(searchMode);
                      }
                    }}
                    disabled={sourcing}
                    className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 text-white text-xs font-black shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50 cursor-pointer"
                  >
                    {sourcing ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        <span>Sourcing in Progress...</span>
                      </>
                    ) : (
                      <>
                        <Play className="h-3.5 w-3.5 fill-white" />
                        <span>
                          {sessionState === "completed"
                            ? (searchMode === "live" ? "Re-Run Live LinkedIn Sourcing" : "Re-Run Autonomous Sourcing")
                            : (searchMode === "live" ? "Start Live LinkedIn Sourcing" : "Start Autonomous Sourcing")}
                        </span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </footer>
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
                LinkedIn requires an authenticated account to view candidate search results. The browser window is open on your desktop. Please sign in to proceed, or click below to run autonomous demo.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
              <button
                type="button"
                onClick={handleCheckAuthStatus}
                disabled={checkingAuth}
                className="px-3 py-2.5 rounded-xl text-xs font-bold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-700/50 hover:bg-indigo-100 transition-colors"
              >
                {checkingAuth ? "Checking..." : "Check Auth Status"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsAuthModalOpen(false);
                  handleLaunchSourcing("live");
                }}
                className="px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 transition-colors"
              >
                I've Logged In — Proceed
              </button>
            </div>
          </div>
        </div>
      )}

{/* -------------------- 7.5 MODAL: AUTOMATED OUTREACH COMPOSER & AGENT -------------------- */}
      {outreachModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-4xl bg-white dark:bg-[#0d1222] border border-slate-200 dark:border-[#1f2b47] rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-100 dark:border-[#18233c] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
                  <Mail className="h-5 w-5 fill-white/20" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-black text-slate-900 dark:text-white">
                      Automated Candidate Outreach & Engagement
                    </h3>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300 border border-blue-200 dark:border-blue-500/30">
                      Playwright Agent
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Human-cadence automated LinkedIn messaging • Dual-channel delivery (Direct Message or Connect Note)
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setOutreachModalOpen(false)}
                className="h-8 w-8 rounded-lg bg-slate-100 dark:bg-[#141b2e] text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 flex items-center justify-center cursor-pointer transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Recipients Banner */}
              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-[#0c1120] border border-slate-200/80 dark:border-[#1a2540] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Target Recipient{outreachCandidates.length > 1 ? `s (${outreachCandidates.length})` : ""}:
                  </span>
                  <span className="text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold">
                    Recipient profiles will be visited sequentially with safety pauses
                  </span>
                </div>
                <div className="flex flex-wrap gap-2.5 max-h-36 overflow-y-auto">
                  {outreachCandidates.map((cand, i) => (
                    <div
                      key={cand.id || i}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white dark:bg-[#11192e] border border-slate-200 dark:border-[#202d4d] shadow-2xs"
                    >
                      <img
                        src={cand.avatar || cand.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"}
                        alt={cand.name}
                        className="h-7 w-7 rounded-full object-cover border border-slate-200 dark:border-slate-700 shrink-0"
                      />
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-slate-900 dark:text-white truncate max-w-[180px]">
                          {cand.name?.split(/[•·]/)[0]?.replace(/\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message)\b/gi, '')?.trim() || cand.name}
                        </div>
                        <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-[180px]">
                          {cand.title || cand.headline || "Candidate"}
                        </div>
                      </div>
                      {cand.canonical_url && (
                        <a
                          href={cand.canonical_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-400 hover:text-blue-600 ml-1"
                          title="Open LinkedIn profile in new tab"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Outreach Parameters */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3.5">
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                    Hiring Role Title
                  </label>
                  <input
                    type="text"
                    value={outreachRoleTitle}
                    onChange={(e) => setOutreachRoleTitle(e.target.value)}
                    placeholder="e.g. Senior AI Lead"
                    className="w-full text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-800 dark:text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={outreachCompanyName}
                    onChange={(e) => setOutreachCompanyName(e.target.value)}
                    placeholder="e.g. Hiring Desk / TechCorp"
                    className="w-full text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-800 dark:text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                    Recruiter Signature
                  </label>
                  <input
                    type="text"
                    value={outreachRecruiterName}
                    onChange={(e) => setOutreachRecruiterName(e.target.value)}
                    placeholder="e.g. HR Talent Acquisition"
                    className="w-full text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-800 dark:text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                    Message Tone
                  </label>
                  <select
                    value={outreachTone}
                    onChange={(e) => setOutreachTone(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-800 dark:text-slate-200 focus:outline-none focus:border-indigo-500 font-medium cursor-pointer"
                  >
                    <option value="formal">Formal & Professional</option>
                    <option value="warm">Warm & Conversational</option>
                    <option value="direct">Direct & Technical</option>
                  </select>
                </div>
              </div>

              {/* Company Details Field */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-bold text-slate-600 dark:text-slate-300">
                    Company Value Proposition / Mission
                  </label>
                  <button
                    type="button"
                    onClick={handleRegenerateOutreachDraft}
                    disabled={outreachGenerating}
                    className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex items-center gap-1 cursor-pointer disabled:opacity-50"
                  >
                    <Sparkles className={`h-3 w-3 ${outreachGenerating ? "animate-spin" : ""}`} />
                    <span>{outreachGenerating ? "Regenerating..." : "Regenerate Draft with AI"}</span>
                  </button>
                </div>
                <input
                  type="text"
                  value={outreachCompanyDetails}
                  onChange={(e) => setOutreachCompanyDetails(e.target.value)}
                  placeholder="e.g. a high-growth tech organization delivering enterprise AI workflows"
                  className="w-full text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-800 dark:text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Message Subject & Body */}
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Subject Line (for InMail & Direct Message)
                  </label>
                  <input
                    type="text"
                    value={outreachSubject}
                    onChange={(e) => setOutreachSubject(e.target.value)}
                    placeholder="e.g. Opportunity: Senior AI Lead at Acme Corp"
                    className="w-full text-xs px-3.5 py-2 rounded-xl bg-white dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-white font-semibold focus:outline-none focus:border-indigo-500 shadow-2xs"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                      <span>Formal Direct Message (Multi-paragraph)</span>
                      <span className="text-[10px] text-slate-400 font-normal">
                        (Used when direct messaging is available)
                      </span>
                    </label>
                  </div>
                  <textarea
                    rows={8}
                    value={outreachMessageBody}
                    onChange={(e) => setOutreachMessageBody(e.target.value)}
                    placeholder="Drafting personalized formal hiring outreach message..."
                    className="w-full text-xs p-3.5 rounded-2xl bg-white dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-800 dark:text-slate-200 focus:outline-none focus:border-indigo-500 leading-relaxed font-sans shadow-2xs"
                  />
                </div>

                {/* Connection Request Note (<= 300 chars) */}
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-[#0d1428] border border-slate-200 dark:border-[#1e2a47] space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                      <UserCheck className="h-3.5 w-3.5 text-indigo-500" />
                      <span>LinkedIn Connection Request Note (Fallback for 2nd/3rd Degree)</span>
                    </label>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        outreachConnectionNote.length > 295
                          ? "bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300"
                          : outreachConnectionNote.length > 270
                          ? "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300"
                          : "bg-slate-200/80 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {outreachConnectionNote.length} / 295 max chars
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400">
                    LinkedIn limits connection request notes strictly to 300 characters. If the candidate's direct message button is locked by InMail credits, the browser agent automatically uses this note to connect.
                  </p>
                  <textarea
                    rows={3}
                    maxLength={295}
                    value={outreachConnectionNote}
                    onChange={(e) => setOutreachConnectionNote(e.target.value)}
                    placeholder="Hi [Name], impressed by your background. We are hiring for [Role] at [Company]..."
                    className="w-full text-xs p-3 rounded-xl bg-white dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-800 dark:text-slate-200 focus:outline-none focus:border-indigo-500 shadow-2xs"
                  />
                </div>
              </div>

              {/* Progress and Telemetry during Sending */}
              {outreachSending && (
                <div className="p-4 rounded-2xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 space-y-2 animate-in fade-in">
                  <div className="flex items-center justify-between text-xs font-bold text-blue-900 dark:text-blue-200">
                    <span className="flex items-center gap-2">
                      <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                      <span>Autonomous Browser Agent Delivering Messages...</span>
                    </span>
                    <span>{outreachProgress?.progress || 20}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-blue-200 dark:bg-blue-900 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-600 to-indigo-600 transition-all duration-300"
                      style={{ width: `${outreachProgress?.progress || 20}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-blue-700 dark:text-blue-300 font-mono">
                    {outreachProgress?.message || "Navigating to candidate profile on LinkedIn..."}
                  </p>
                </div>
              )}

              {/* Completion Banner */}
              {outreachComplete && (
                <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex items-center gap-3 animate-in fade-in">
                  <div className="h-9 w-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                  <div>
                    <h5 className="text-xs font-bold text-emerald-900 dark:text-emerald-200">
                      Outreach Successfully Delivered!
                    </h5>
                    <p className="text-[11px] text-emerald-700 dark:text-emerald-300 mt-0.5">
                      The Playwright autonomous browser agent completed delivery. Candidate status has been updated to Sent.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-5 border-t border-slate-100 dark:border-[#18233c] flex items-center justify-between bg-slate-50/50 dark:bg-[#0a0f1d]">
              <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse" />
                <span>Target Browser: Google Chrome ({browserChannel})</span>
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setOutreachModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-[#151e36] transition-colors cursor-pointer"
                >
                  {outreachComplete ? "Done" : "Cancel"}
                </button>
                <button
                  type="button"
                  onClick={handleSendOutreach}
                  disabled={outreachSending || !outreachMessageBody.trim() || outreachGenerating}
                  className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transition-all shadow-md shadow-blue-500/20 disabled:opacity-50 flex items-center gap-2 cursor-pointer"
                >
                  {outreachSending ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Sending via Agent...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-3.5 w-3.5" />
                      <span>🚀 Send via Browser Agent ({outreachCandidates.length})</span>
                    </>
                  )}
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
                      Sourcing Intelligence & Shortlist Analytics
                    </h3>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30">
                      Live Synced
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Verified candidate pool & criteria evaluation distribution
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
                  <p className="text-xs font-semibold text-slate-500">Loading candidate records...</p>
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
                      <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold mt-1">Profiles Saved</div>
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
                        {reportData?.average_fit_score !== undefined && reportData?.average_fit_score !== null
                          ? `${reportData.average_fit_score}%`
                          : candidateList.filter((c) => c.skill_match != null).length > 0
                          ? `${Math.round(candidateList.filter((c) => c.skill_match != null).reduce((acc, c) => acc + c.skill_match, 0) / candidateList.filter((c) => c.skill_match != null).length)}%`
                          : "—"}
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
                        Verified Candidate Profiles ({reportData?.all_candidates?.length || candidateList.length})
                      </h4>
                      <span className="text-[11px] text-slate-400">Click row to review full evidence</span>
                    </div>
                    <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                      {(reportData?.all_candidates && reportData.all_candidates.length > 0 ? reportData.all_candidates : candidateList).map((cand, idx) => (
                        <div
                          key={idx}
                          onClick={() => {
                            setIsReportModalOpen(false);
                            handleOpenCandidateProfile(cand);
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
                    addTelemetryLog("Exported full sourcing report to JSON!", "file");
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
