"use client";

import React, { useState, useEffect } from "react";
import {
  Building2,
  Briefcase,
  User,
  PenTool,
  Sparkles,
  MapPin,
  Globe,
  CheckCircle2,
  X,
  AlertCircle,
  ShieldCheck,
  ArrowRight,
  Info,
} from "lucide-react";
import {
  getCompanyProfile,
  saveCompanyProfile,
  isOnboardingCompleted,
} from "../services/companyService";

export default function CompanyProfileModal({
  isOpen,
  onClose,
  initialData = null,
  isFirstTime = false,
  onSaveSuccess = null,
  userId = null,
}) {
  const [formData, setFormData] = useState({
    companyName: "",
    industry: "",
    recruiterName: "",
    recruiterSignature: "",
    companyDetails: "",
    location: "",
    website: "",
    employeeCount: "50-250",
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [savedFeedback, setSavedFeedback] = useState(false);

  // Load existing profile when modal opens
  useEffect(() => {
    if (isOpen) {
      const current = initialData || getCompanyProfile();
      setFormData({
        companyName: current.companyName || "",
        industry: current.industry || "",
        recruiterName: current.recruiterName || "",
        recruiterSignature: current.recruiterSignature || "",
        companyDetails: current.companyDetails || "",
        location: current.location || "",
        website: current.website || "",
        employeeCount: current.employeeCount || "50-250",
      });
      setErrors({});
      setSavedFeedback(false);
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const validate = () => {
    const newErrors = {};
    if (!formData.companyName.trim()) {
      newErrors.companyName = "Company name is required";
    }
    if (!formData.recruiterName.trim()) {
      newErrors.recruiterName = "Recruiter full name is required";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const rest = { ...prev };
        delete rest[field];
        return rest;
      });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const updated = saveCompanyProfile({
        ...formData,
        user_id: userId || initialData?.user_id || undefined,
        // Auto-generate recruiter signature if left blank
        recruiterSignature:
          formData.recruiterSignature.trim() ||
          `${formData.recruiterName} | Talent Acquisition at ${formData.companyName}`,
      });

      setSavedFeedback(true);
      setTimeout(() => {
        setIsSubmitting(false);
        if (onSaveSuccess) {
          onSaveSuccess(updated);
        }
        if (onClose) {
          onClose();
        }
      }, 400);
    } catch (err) {
      console.error("Failed to save profile:", err);
      setIsSubmitting(false);
    }
  };

  const industries = [
    "Enterprise Software & SaaS",
    "Artificial Intelligence & ML",
    "Financial Services & Fintech",
    "Healthcare & Life Sciences",
    "E-Commerce & Retail",
    "Cloud & Infrastructure",
    "Consulting & Professional Services",
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 dark:bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl bg-white dark:bg-[#0c1222] border border-slate-200 dark:border-[#1d2744] rounded-3xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby="company-profile-title"
      >
        {/* Modal Header */}
        <div className="relative px-6 py-5 border-b border-slate-200/80 dark:border-[#19233c] bg-gradient-to-r from-indigo-50/70 via-purple-50/40 to-transparent dark:from-[#11172a] dark:via-[#161d36] dark:to-transparent flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3.5">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 shrink-0">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3
                  id="company-profile-title"
                  className="text-base font-bold text-slate-900 dark:text-white tracking-tight"
                >
                  {isFirstTime ? "Recruiter & Company Onboarding" : "Company & Recruiter Profile"}
                </h3>
                {isFirstTime && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-950/80 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                    Required Onboarding
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {isFirstTime
                  ? "Configure your organization details to personalize candidate outreach and search requisitions"
                  : "Sync your company details with AI outreach templates and sourcing workflows"}
              </p>
            </div>
          </div>

          {!isFirstTime && (
            <button
              onClick={onClose}
              className="h-8 w-8 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-[#19233c] flex items-center justify-center transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Modal Body / Scrollable Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* First-time welcoming alert */}
          {isFirstTime && (
            <div className="p-3.5 rounded-2xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200/80 dark:border-indigo-900/60 flex items-start gap-3">
              <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
              <div className="text-xs text-indigo-900 dark:text-indigo-200 leading-relaxed">
                <strong>Welcome to Hiring Desk!</strong> Please specify your organization profile so the
                AI assistant can craft tailored outreach messages, accurate job descriptions, and branded candidate invitations.
              </div>
            </div>
          )}

          {/* Section 1: Company Fundamentals */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-[#162038]">
              <Building2 className="h-3.5 w-3.5 text-indigo-500" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Company Information
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Company Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Company Name <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={formData.companyName}
                    onChange={(e) => handleChange("companyName", e.target.value)}
                    placeholder="e.g. Acme Corp or Stripe"
                    className={`w-full text-xs px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#10172b] border ${
                      errors.companyName
                        ? "border-rose-400 focus:border-rose-500"
                        : "border-slate-200 dark:border-[#1d2946] focus:border-indigo-500"
                    } text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none transition-all font-medium`}
                  />
                </div>
                {errors.companyName && (
                  <p className="text-[11px] text-rose-500 mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" /> {errors.companyName}
                  </p>
                )}
              </div>

              {/* Primary Location */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Primary Office / Sourcing Hub
                </label>
                <div className="relative">
                  <MapPin className="h-3.5 w-3.5 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => handleChange("location", e.target.value)}
                    placeholder="e.g. San Francisco, CA / Bengaluru / Hybrid"
                    className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition-all font-medium"
                  />
                </div>
              </div>
            </div>

            {/* Industry Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Industry / Core Domain
              </label>
              <input
                type="text"
                value={formData.industry}
                onChange={(e) => handleChange("industry", e.target.value)}
                placeholder="e.g. Enterprise Software & Scalable AI Systems"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition-all font-medium mb-2"
              />
              <div className="flex flex-wrap gap-1.5">
                {industries.map((ind) => (
                  <button
                    key={ind}
                    type="button"
                    onClick={() => handleChange("industry", ind)}
                    className={`text-[10px] font-medium px-2.5 py-1 rounded-lg border transition-all ${
                      formData.industry === ind
                        ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border-indigo-300 dark:border-indigo-700 font-bold"
                        : "bg-slate-50 dark:bg-[#10172b] text-slate-600 dark:text-slate-400 border-slate-200 dark:border-[#1d2946] hover:border-slate-300"
                    }`}
                  >
                    {ind}
                  </button>
                ))}
              </div>
            </div>

            {/* Company Value Proposition / Context for AI Outreach */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Value Proposition & Mission Context
                </label>
                <span className="text-[10px] text-indigo-600 dark:text-indigo-400 font-medium flex items-center gap-1">
                  <Sparkles className="h-3 w-3" /> Used in AI Outreach Messages
                </span>
              </div>
              <textarea
                rows={2}
                value={formData.companyDetails}
                onChange={(e) => handleChange("companyDetails", e.target.value)}
                placeholder="e.g. Leading innovation in high-throughput enterprise systems with Series B funding and an engineering-first culture"
                className="w-full text-xs px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition-all font-medium leading-relaxed resize-none"
              />
            </div>
          </div>

          {/* Section 2: Recruiter Persona */}
          <div className="space-y-4 pt-2">
            <div className="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-[#162038]">
              <User className="h-3.5 w-3.5 text-purple-500" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Recruiter Profile
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Recruiter Full Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Recruiter Full Name <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <User className="h-3.5 w-3.5 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    value={formData.recruiterName}
                    onChange={(e) => handleChange("recruiterName", e.target.value)}
                    placeholder="e.g. Sarah Jenkins"
                    className={`w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#10172b] border ${
                      errors.recruiterName
                        ? "border-rose-400 focus:border-rose-500"
                        : "border-slate-200 dark:border-[#1d2946] focus:border-indigo-500"
                    } text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none transition-all font-medium`}
                  />
                </div>
                {errors.recruiterName && (
                  <p className="text-[11px] text-rose-500 mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" /> {errors.recruiterName}
                  </p>
                )}
              </div>

              {/* Official Outreach Signature */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Official Email/Message Signature
                </label>
                <div className="relative">
                  <PenTool className="h-3.5 w-3.5 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    value={formData.recruiterSignature}
                    onChange={(e) => handleChange("recruiterSignature", e.target.value)}
                    placeholder="e.g. Lead Talent Acquisition Partner"
                    className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition-all font-medium"
                  />
                </div>
              </div>
            </div>

            {/* Optional Website / Company Size */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Company Careers Website (Optional)
                </label>
                <div className="relative">
                  <Globe className="h-3.5 w-3.5 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    value={formData.website}
                    onChange={(e) => handleChange("website", e.target.value)}
                    placeholder="e.g. https://acme.com/careers"
                    className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition-all font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Organization Size
                </label>
                <select
                  value={formData.employeeCount}
                  onChange={(e) => handleChange("employeeCount", e.target.value)}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-slate-100 focus:outline-none focus:border-indigo-500 transition-all font-medium cursor-pointer"
                >
                  <option value="1-10">1-10 employees (Seed stage)</option>
                  <option value="11-50">11-50 employees (Early stage)</option>
                  <option value="50-250">50-250 employees (Growth stage)</option>
                  <option value="250-1000">250-1,000 employees (Scale-up)</option>
                  <option value="1000+">1,000+ employees (Enterprise)</option>
                </select>
              </div>
            </div>
          </div>
        </form>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-200/80 dark:border-[#19233c] bg-slate-50/50 dark:bg-[#0a0f1d]/60 flex items-center justify-between shrink-0">
          <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
            <span>Settings saved locally and synced with outreach prompts</span>
          </div>

          <div className="flex items-center gap-2">
            {!isFirstTime && (
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200/60 dark:hover:bg-[#1a233a] transition-colors"
              >
                Cancel
              </button>
            )}

            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-md shadow-indigo-500/20 active:scale-[0.98] transition-all disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <span className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Saving...</span>
                </>
              ) : savedFeedback ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" />
                  <span>Profile Synced!</span>
                </>
              ) : (
                <>
                  <span>{isFirstTime ? "Complete Onboarding" : "Save Changes"}</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
