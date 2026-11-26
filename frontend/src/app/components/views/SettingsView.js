"use client";

import React, { useState, useEffect } from "react";
import {
  Settings,
  Building,
  User,
  Shield,
  ShieldCheck,
  Cpu,
  CheckCircle2,
  Globe,
  Mail,
  Briefcase,
  MapPin,
  Users,
  Save,
  Check,
  Copy,
  LogOut,
  Sparkles,
  ExternalLink,
  MessageSquare,
  Radio,
  FileText
} from "lucide-react";
import { useUser, useClerk } from "@clerk/nextjs";
import {
  getCompanyProfile,
  saveCompanyProfile,
} from "../../services/companyService";

const INDUSTRY_OPTIONS = [
  "Artificial Intelligence & ML",
  "Enterprise Software & SaaS",
  "Financial Services & FinTech",
  "Healthcare & Life Sciences",
  "E-Commerce & Retail Tech",
  "Cloud & Infrastructure",
  "Consulting & Professional Services",
];

const SIZE_OPTIONS = [
  "1-10 employees (Early stage)",
  "10-50 employees (Seed / Series A)",
  "50-250 employees (Growth stage)",
  "250-1000 employees (Mid-market)",
  "1000+ employees (Enterprise)",
];

export default function SettingsView({ jobRequirements }) {
  const { user } = useUser();
  const { signOut } = useClerk();

  const [activeTab, setActiveTab] = useState("organization"); // "organization" | "recruiter" | "auth" | "engine"
  const [formData, setFormData] = useState({
    companyName: "ROR Technologies",
    industry: "Artificial Intelligence & ML",
    location: "Bengaluru, India / Hybrid",
    website: "https://rortechnologies.com",
    employeeCount: "50-250 employees (Growth stage)",
    companyDetails: "Leading innovation in enterprise software, agentic workflows, and scalable AI systems",
    recruiterName: "Sengo",
    recruiterSignature: "Lead Talent Acquisition Partner",
    tone: "formal",
  });

  const [isDirty, setIsDirty] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

  // Load existing profile from companyService on mount
  useEffect(() => {
    try {
      const current = getCompanyProfile();
      setFormData((prev) => ({
        ...prev,
        companyName: current.companyName || current.company_name || prev.companyName,
        industry: current.industry || prev.industry,
        location: current.location || current.sourcing_hub || prev.location,
        website: current.website || prev.website,
        employeeCount: current.employeeCount || prev.employeeCount,
        companyDetails: current.companyDetails || current.value_proposition || prev.companyDetails,
        recruiterName: current.recruiterName || current.recruiter_name || user?.fullName || prev.recruiterName,
        recruiterSignature: current.recruiterSignature || current.recruiter_title || prev.recruiterSignature,
      }));
    } catch (e) {
      // Ignore
    }

    const onUpdate = (e) => {
      if (e.detail) {
        const u = e.detail;
        setFormData((prev) => ({
          ...prev,
          companyName: u.companyName || prev.companyName,
          industry: u.industry || prev.industry,
          location: u.location || prev.location,
          website: u.website || prev.website,
          employeeCount: u.employeeCount || prev.employeeCount,
          companyDetails: u.companyDetails || prev.companyDetails,
          recruiterName: u.recruiterName || prev.recruiterName,
          recruiterSignature: u.recruiterSignature || prev.recruiterSignature,
        }));
      }
    };
    window.addEventListener("companyProfileUpdated", onUpdate);
    return () => window.removeEventListener("companyProfileUpdated", onUpdate);
  }, [user]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setIsDirty(true);
  };

  const handleSave = () => {
    try {
      saveCompanyProfile({
        ...formData,
        userId: user?.id,
      });
      setIsDirty(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      console.error("Error saving settings:", e);
    }
  };

  const handleSignOut = () => {
    try {
      localStorage.removeItem("hiring_desk_clerk_authenticated");
      localStorage.removeItem("hiring_desk_dev_signed_in");
    } catch (e) {}
    if (signOut) signOut();
  };

  const handleCopyUserId = () => {
    if (user?.id) {
      navigator.clipboard.writeText(user.id);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12 animate-in fade-in duration-200">
      {/* Top Header Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              <Settings className="h-3 w-3" />
              Settings & Configuration
            </span>
            <span className="text-xs font-medium text-slate-400">
              {formData.companyName || "Organization"} Workspace
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            Organization & Recruiter Settings
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure your enterprise branding, recruiter outreach persona, Clerk authentication, and AI automation engine.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold transition-all shadow-md active:scale-95 ${
              isDirty
                ? "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-indigo-600/25 ring-2 ring-indigo-500/20"
                : "bg-white dark:bg-[#141d33] border border-slate-200 dark:border-[#222e4d] text-slate-700 dark:text-slate-200 hover:border-indigo-400"
            }`}
          >
            {saveSuccess ? (
              <>
                <Check className="h-4 w-4 text-emerald-500" />
                <span>Saved & Synced!</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>{isDirty ? "Save Changes *" : "Save Settings"}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {saveSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex items-center justify-between text-emerald-900 dark:text-emerald-200 animate-in fade-in">
          <div className="flex items-center gap-2.5 text-xs font-bold">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>Settings successfully updated and synced with AI candidate outreach agent!</span>
          </div>
          <span className="text-[10px] text-emerald-700 dark:text-emerald-300 font-medium">Persisted to SQLite DB</span>
        </div>
      )}

      {/* Clean Tabs Navigation Bar */}
      <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-slate-100/80 dark:bg-[#0c1122] border border-slate-200/80 dark:border-[#172138] overflow-x-auto">
        {[
          { id: "organization", label: "Organization Profile", icon: Building },
          { id: "recruiter", label: "Recruiter Persona & Outreach", icon: User },
          { id: "auth", label: "Clerk Account & Access", icon: Shield },
          { id: "engine", label: "AI Engine & Data Privacy", icon: Cpu },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                isActive
                  ? "bg-white dark:bg-[#151c33] text-indigo-600 dark:text-indigo-400 shadow-sm border border-slate-200/60 dark:border-[#1f2b4d]"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-white/50"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* -------------------- TAB 1: ORGANIZATION PROFILE -------------------- */}
      {activeTab === "organization" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in">
          {/* Main Info Fields (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Building className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  Enterprise Branding & Workspace Info
                </h3>
                <span className="text-[11px] text-slate-400">Used across candidate search & outreach</span>
              </div>

              {/* Form Grid */}
              <div className="space-y-4">
                {/* Company Name */}
                <div>
                  <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                    Company Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Building className="h-4 w-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={formData.companyName}
                      onChange={(e) => handleChange("companyName", e.target.value)}
                      placeholder="e.g. ROR Technologies or Acme Corp"
                      className="w-full text-xs pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-[#1f2b4d] bg-slate-50/50 dark:bg-[#11172a] text-slate-800 dark:text-slate-100 font-semibold focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-all"
                    />
                  </div>
                </div>

                {/* Industry & Location Row */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                      Core Industry / Domain
                    </label>
                    <select
                      value={formData.industry}
                      onChange={(e) => handleChange("industry", e.target.value)}
                      className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-[#1f2b4d] bg-slate-50/50 dark:bg-[#11172a] text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-all"
                    >
                      {INDUSTRY_OPTIONS.map((ind) => (
                        <option key={ind} value={ind}>
                          {ind}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                      Primary Sourcing Hub / Location
                    </label>
                    <div className="relative">
                      <MapPin className="h-4 w-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={formData.location}
                        onChange={(e) => handleChange("location", e.target.value)}
                        placeholder="e.g. Bengaluru, India / Hybrid"
                        className="w-full text-xs pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-[#1f2b4d] bg-slate-50/50 dark:bg-[#11172a] text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-all"
                      />
                    </div>
                  </div>
                </div>

                {/* Website & Size Row */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                      Company Website
                    </label>
                    <div className="relative">
                      <Globe className="h-4 w-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={formData.website}
                        onChange={(e) => handleChange("website", e.target.value)}
                        placeholder="https://example.com"
                        className="w-full text-xs pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-[#1f2b4d] bg-slate-50/50 dark:bg-[#11172a] text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-all"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                      Organization Size
                    </label>
                    <select
                      value={formData.employeeCount}
                      onChange={(e) => handleChange("employeeCount", e.target.value)}
                      className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-[#1f2b4d] bg-slate-50/50 dark:bg-[#11172a] text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-all"
                    >
                      {SIZE_OPTIONS.map((sz) => (
                        <option key={sz} value={sz}>
                          {sz}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Value Proposition Textarea */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                      Company Value Proposition & Mission Context
                    </label>
                    <span className="text-[11px] text-slate-400">
                      {(formData.companyDetails || "").length} characters
                    </span>
                  </div>
                  <textarea
                    rows={4}
                    value={formData.companyDetails}
                    onChange={(e) => handleChange("companyDetails", e.target.value)}
                    placeholder="Describe your company's core mission, competitive edge, and work culture (e.g. Leading innovation in enterprise software and scalable AI systems)..."
                    className="w-full p-3.5 rounded-xl border border-slate-200 dark:border-[#1f2b4d] bg-slate-50/50 dark:bg-[#11172a] text-xs text-slate-800 dark:text-slate-100 leading-relaxed focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-all resize-y"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    This context is automatically synthesized by the AI agent when generating tailored LinkedIn connection notes and outreach messages.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Organization Card Preview & Quick Stats (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
                Active Workspace Summary
              </h4>

              <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-50/70 to-purple-50/40 dark:from-[#11172a] dark:to-[#161c36] border border-indigo-100/90 dark:border-[#1f2b4d] space-y-3">
                <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-black text-sm flex items-center justify-center shadow-sm">
                  {formData.companyName?.slice(0, 2).toUpperCase() || "RO"}
                </div>
                <div>
                  <h3 className="text-sm font-black text-slate-900 dark:text-white">
                    {formData.companyName || "Organization"}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {formData.industry}
                  </p>
                </div>
                <div className="pt-2 border-t border-indigo-100/80 dark:border-[#1f2b4d] space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{formData.location}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span>{formData.employeeCount.split("(")[0]}</span>
                  </div>
                  {formData.website && (
                    <div className="flex items-center gap-2">
                      <Globe className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <a
                        href={formData.website}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-600 dark:text-indigo-400 hover:underline truncate"
                      >
                        {formData.website.replace(/^https?:\/\//, "")}
                      </a>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleSave}
                  className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-xs transition-all flex items-center justify-center gap-2"
                >
                  <Save className="h-3.5 w-3.5" />
                  <span>Save Organization Profile</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* -------------------- TAB 2: RECRUITER PERSONA & OUTREACH -------------------- */}
      {activeTab === "recruiter" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in">
          {/* Left Column: Form Fields (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <User className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  Recruiter Identity & Messaging Persona
                </h3>
                <span className="text-[11px] text-slate-400">Personalized in candidate outreach</span>
              </div>

              <div className="space-y-4">
                {/* Full Name */}
                <div>
                  <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                    Recruiter Full Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="h-4 w-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={formData.recruiterName}
                      onChange={(e) => handleChange("recruiterName", e.target.value)}
                      placeholder="e.g. Sengo or Sarah Jenkins"
                      className="w-full text-xs pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-[#1f2b4d] bg-slate-50/50 dark:bg-[#11172a] text-slate-800 dark:text-slate-100 font-semibold focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-all"
                    />
                  </div>
                </div>

                {/* Title / Role */}
                <div>
                  <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                    Official Title / Signature Line
                  </label>
                  <div className="relative">
                    <Briefcase className="h-4 w-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={formData.recruiterSignature}
                      onChange={(e) => handleChange("recruiterSignature", e.target.value)}
                      placeholder="e.g. Lead Talent Acquisition Partner or VP of Engineering"
                      className="w-full text-xs pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-[#1f2b4d] bg-slate-50/50 dark:bg-[#11172a] text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-all"
                    />
                  </div>
                </div>

                {/* Tone Preferences */}
                <div>
                  <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-2">
                    Default Outreach Tone
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: "formal", label: "Formal & Professional" },
                      { id: "warm", label: "Warm & Conversational" },
                      { id: "concise", label: "Concise & Executive" },
                    ].map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => handleChange("tone", t.id)}
                        className={`p-2.5 rounded-xl border text-xs font-bold text-center transition-all ${
                          formData.tone === t.id
                            ? "bg-indigo-50 dark:bg-indigo-950/50 border-indigo-300 dark:border-indigo-700 text-indigo-700 dark:text-indigo-400 ring-2 ring-indigo-500/10 shadow-xs"
                            : "bg-slate-50/50 dark:bg-[#11172a] border-slate-200 dark:border-[#1e293b] text-slate-600 dark:text-slate-300"
                        }`}
                      >
                        {t.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Live Candidate Outreach Preview Card (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-indigo-500" />
                  Live Outreach Signature Preview
                </h4>
                <span className="text-[10px] text-emerald-600 font-bold bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-md">
                  Real-time
                </span>
              </div>

              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Here is exactly how your sign-off and company identity will appear to candidates on LinkedIn and in direct messages:
              </p>

              {/* Message Bubble Card */}
              <div className="p-5 rounded-2xl bg-slate-50 dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1f2b4d] font-sans text-xs text-slate-700 dark:text-slate-300 space-y-3 shadow-inner">
                <p className="italic text-slate-500 text-[11px]">
                  "...We were extremely impressed by your engineering leadership track record and would love to connect about our Senior AI Lead role."
                </p>

                <div className="pt-3 border-t border-slate-200/80 dark:border-[#1f2b4d] space-y-1">
                  <div className="font-medium text-slate-500">Best regards,</div>
                  <div className="font-black text-sm text-slate-900 dark:text-white">
                    {formData.recruiterName || "Recruiter Name"}
                  </div>
                  <div className="font-semibold text-indigo-600 dark:text-indigo-400 text-xs">
                    {formData.recruiterSignature || "Talent Acquisition Partner"}
                  </div>
                  <div className="text-[11px] text-slate-500 font-medium flex items-center gap-1 pt-0.5">
                    <span>{formData.companyName || "Organization"}</span>
                    <span>•</span>
                    <span>{formData.location || "Bengaluru, India"}</span>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={handleSave}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-xs transition-all flex items-center justify-center gap-2"
              >
                <Save className="h-3.5 w-3.5" />
                <span>Save Persona Changes</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* -------------------- TAB 3: CLERK AUTH & ACCESS -------------------- */}
      {activeTab === "auth" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in">
          {/* Clerk Account Overview (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  Authenticated Clerk Identity
                </h3>
                <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                  <CheckCircle2 className="h-3 w-3" />
                  Verified Session
                </span>
              </div>

              {/* User Identity Card */}
              <div className="p-5 rounded-2xl bg-slate-50/70 dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1f2b4d] flex items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  {user?.imageUrl ? (
                    <img
                      src={user.imageUrl}
                      alt="Avatar"
                      className="h-14 w-14 rounded-2xl border-2 border-white dark:border-[#1e293b] shadow-sm object-cover"
                    />
                  ) : (
                    <div className="h-14 w-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-black text-lg flex items-center justify-center shadow-md">
                      {user?.firstName?.slice(0, 1) || "U"}
                    </div>
                  )}
                  <div>
                    <h4 className="text-sm font-black text-slate-900 dark:text-white">
                      {user?.fullName || user?.firstName || "HR Recruiter"}
                    </h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 font-medium">
                      {user?.primaryEmailAddress?.emailAddress || "recruiter@rortechnologies.com"}
                    </p>
                    <span className="inline-block mt-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                      Primary Recruiter Admin
                    </span>
                  </div>
                </div>
              </div>

              {/* Account Details List */}
              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-white dark:bg-[#0f172a] border border-slate-200/80 dark:border-[#1e293b]">
                  <span className="text-slate-500">Clerk User Identifier:</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] text-slate-700 dark:text-slate-300">
                      {user?.id ? `${user.id.slice(0, 16)}...` : "user_2xxxxxxxxx"}
                    </span>
                    <button
                      type="button"
                      onClick={handleCopyUserId}
                      className="p-1 rounded hover:bg-slate-100 dark:hover:bg-[#1a233b] text-slate-400 hover:text-indigo-600 transition-colors"
                      title="Copy Clerk User ID"
                    >
                      {copiedId ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between p-3.5 rounded-xl bg-white dark:bg-[#0f172a] border border-slate-200/80 dark:border-[#1e293b]">
                  <span className="text-slate-500">Authentication Method:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    Google OAuth / Clerk Secure Password
                  </span>
                </div>

                <div className="flex items-center justify-between p-3.5 rounded-xl bg-white dark:bg-[#0f172a] border border-slate-200/80 dark:border-[#1e293b]">
                  <span className="text-slate-500">Database Sync Status:</span>
                  <span className="font-bold text-emerald-600 flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Synced with Local SQLite (`users` table)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Session & Sign Out Actions (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Shield className="h-3.5 w-3.5 text-indigo-500" />
                Session Controls
              </h4>

              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Signing out will safely clear active session tokens and return you to the recruiter sign-in gateway.
              </p>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="w-full py-2.5 rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/60 dark:bg-rose-950/20 text-rose-700 dark:text-rose-400 hover:bg-rose-100 font-bold text-xs transition-all flex items-center justify-center gap-2 shadow-xs cursor-pointer active:scale-95"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Sign Out of Clerk Account</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* -------------------- TAB 4: AI ENGINE & PRIVACY -------------------- */}
      {activeTab === "engine" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in">
          <div className="lg:col-span-8 space-y-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#162035]">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  AI Intelligence & Local Automation Architecture
                </h3>
                <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-md">
                  Operating
                </span>
              </div>

              <div className="space-y-3.5 text-xs">
                {/* AI Model */}
                <div className="p-4 rounded-2xl bg-slate-50/70 dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1f2b4d] flex items-center justify-between">
                  <div>
                    <h5 className="font-bold text-slate-900 dark:text-white">Active Reasoning Model</h5>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Powers job description parsing, calibrated search queries, and candidate evidence scoring.
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-bold border border-indigo-200 dark:border-indigo-800">
                    gemini-2.5-flash
                  </span>
                </div>

                {/* Playwright Browser */}
                <div className="p-4 rounded-2xl bg-slate-50/70 dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1f2b4d] flex items-center justify-between">
                  <div>
                    <h5 className="font-bold text-slate-900 dark:text-white">Desktop Automation Engine</h5>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Playwright headed & headless browser with anti-detection pauses and safe handover checkpointing.
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-800">
                    Playwright Ready
                  </span>
                </div>

                {/* Local SQLite DB */}
                <div className="p-4 rounded-2xl bg-slate-50/70 dark:bg-[#11172a] border border-slate-200/80 dark:border-[#1f2b4d] flex items-center justify-between">
                  <div>
                    <h5 className="font-bold text-slate-900 dark:text-white">Local-First Storage Engine</h5>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Persisted in SQLite (`data/hiring_desk.db`) in WAL mode. Zero cloud candidate data leakage.
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-800">
                    100% Local / Private
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-4 space-y-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-[#0d1222] border border-slate-200/80 dark:border-[#172138] shadow-xs space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Data Privacy Guarantee
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                All candidates harvested during sourcing are stored directly on your computer. Credentials and session cookies are never transmitted to third parties or bypass access controls.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
