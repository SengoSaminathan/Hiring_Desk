"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/nextjs";
import {
  User,
  Building2,
  Settings,
  LogOut,
  LogIn,
  KeyRound,
  ChevronDown,
  Sparkles,
  HelpCircle,
  ExternalLink,
  ShieldCheck,
  Check,
} from "lucide-react";
import { useAppAuth, isClerkConfigured } from "./ClerkAuthProvider";

export default function UserNav() {
  const {
    isSignedIn,
    isLoaded,
    user,
    companyProfile,
    signIn,
    signOut,
    openCompanyProfileModal,
  } = useAppAuth();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [showKeyHelpModal, setShowKeyHelpModal] = useState(false);
  const [showDevSignInModal, setShowDevSignInModal] = useState(false);

  // Dev sign-in form state
  const [devEmail, setDevEmail] = useState("");
  const [devRecruiterName, setDevRecruiterName] = useState("");
  const [devCompany, setDevCompany] = useState("");

  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleDevSignInSubmit = (e) => {
    e.preventDefault();
    signIn({
      recruiterName: devRecruiterName.trim() || "HR Recruiter",
      companyName: devCompany.trim() || companyProfile?.companyName || "Acme Corp",
      email: devEmail.trim() || "recruiter@company.com",
    });
    setShowDevSignInModal(false);
  };

  const recruiterDisplayName =
    user?.fullName ||
    companyProfile?.recruiterName ||
    "HR Recruiter";

  const companyDisplayName =
    companyProfile?.companyName ||
    "Acme Corp";

  // Initials for avatar
  const initials = recruiterDisplayName
    .split(" ")
    .map((n) => n[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase() || "HR";

  // If using Clerk production/sandbox keys
  if (isClerkConfigured) {
    if (!isSignedIn) {
      return (
        <div className="flex items-center gap-2">
          <SignInButton mode="modal">
            <button className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-[#1a233a] transition-colors">
              Sign In
            </button>
          </SignInButton>
          <SignUpButton mode="modal">
            <button className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold shadow-xs hover:shadow-md transition-all">
              Sign Up
            </button>
          </SignUpButton>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-3 pl-2 border-l border-slate-200 dark:border-[#141b2d]">
        <button
          onClick={openCompanyProfileModal}
          title="Manage Company & Recruiter Profile"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 border border-indigo-200/80 dark:border-indigo-800 text-[11px] font-semibold text-indigo-700 dark:text-indigo-300 transition-colors"
        >
          <Building2 className="h-3 w-3 text-indigo-500" />
          <span className="max-w-[120px] truncate">{companyDisplayName}</span>
        </button>

        <div className="flex items-center gap-2">
          <UserButton
            appearance={{
              elements: {
                avatarBox: "h-8 w-8 rounded-full shadow-sm ring-1 ring-indigo-500/20",
              },
            }}
          />
          <div className="hidden sm:block text-left">
            <div className="text-xs font-bold text-slate-900 dark:text-slate-100 leading-tight truncate max-w-[120px]">
              {recruiterDisplayName}
            </div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400">
              Recruiter
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Dev Mode Fallback (Clerk Keys Not Configured in .env)
  return (
    <div className="flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-[#141b2d] relative" ref={dropdownRef}>
      {/* Dev Mode Clerk Key helper pill */}
      <button
        onClick={() => setShowKeyHelpModal(true)}
        title="Clerk Auth: Local Dev Mode Active. Click to configure API keys."
        className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-700 dark:text-amber-300 text-[10px] font-medium hover:bg-amber-100 transition-colors cursor-pointer"
      >
        <KeyRound className="h-2.5 w-2.5 text-amber-500" />
        <span>Dev Auth</span>
      </button>

      {/* Company Profile quick button */}
      <button
        onClick={openCompanyProfileModal}
        title="Manage Company & Recruiter Profile"
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-indigo-50 dark:bg-[#12182b] dark:hover:bg-indigo-950/40 border border-slate-200 dark:border-[#1d2744] hover:border-indigo-300 text-[11px] font-semibold text-slate-700 dark:text-slate-200 hover:text-indigo-600 transition-all cursor-pointer"
      >
        <Building2 className="h-3 w-3 text-indigo-500" />
        <span className="max-w-[130px] truncate">{companyDisplayName}</span>
      </button>

      {/* User profile dropdown trigger */}
      {isSignedIn ? (
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="flex items-center gap-2 p-1 rounded-xl hover:bg-slate-100 dark:hover:bg-[#12182b] transition-colors cursor-pointer text-left"
          aria-expanded={isDropdownOpen}
        >
          <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-xs font-bold text-white shadow-sm ring-2 ring-indigo-500/10">
            {initials}
          </div>
          <div className="hidden sm:flex items-center gap-1">
            <div>
              <div className="text-xs font-bold text-slate-900 dark:text-slate-100 leading-tight truncate max-w-[110px]">
                {recruiterDisplayName}
              </div>
              <div className="text-[10px] text-slate-400">HR Recruiter</div>
            </div>
            <ChevronDown
              className={`h-3 w-3 text-slate-400 transition-transform ${
                isDropdownOpen ? "rotate-180" : ""
              }`}
            />
          </div>
        </button>
      ) : (
        <button
          onClick={() => setShowDevSignInModal(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold shadow-xs hover:shadow-md transition-all cursor-pointer"
        >
          <LogIn className="h-3 w-3" />
          <span>HR Sign In</span>
        </button>
      )}

      {/* User Profile Dropdown Menu */}
      {isDropdownOpen && isSignedIn && (
        <div className="absolute right-0 top-11 w-64 bg-white dark:bg-[#0f172a] border border-slate-200 dark:border-[#1e293b] rounded-2xl shadow-xl z-50 p-2 animate-in fade-in slide-in-from-top-1 duration-150">
          <div className="px-3 py-2.5 border-b border-slate-100 dark:border-[#1e293b]">
            <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
              {recruiterDisplayName}
            </div>
            <div className="text-[11px] text-slate-400 truncate">
              {user?.primaryEmailAddress?.emailAddress || "recruiter@hiringdesk.local"}
            </div>
            <div className="mt-1 flex items-center gap-1 text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold">
              <Building2 className="h-2.5 w-2.5" />
              <span className="truncate">{companyDisplayName}</span>
            </div>
          </div>

          <div className="py-1 space-y-0.5">
            <button
              onClick={() => {
                setIsDropdownOpen(false);
                openCompanyProfileModal();
              }}
              className="w-full text-left px-3 py-2 rounded-xl text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-[#1a233a] flex items-center gap-2.5 transition-colors cursor-pointer"
            >
              <Building2 className="h-3.5 w-3.5 text-indigo-500" />
              <span>Company & Recruiter Profile</span>
            </button>

            <button
              onClick={() => {
                setIsDropdownOpen(false);
                setShowKeyHelpModal(true);
              }}
              className="w-full text-left px-3 py-2 rounded-xl text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-[#1a233a] flex items-center gap-2.5 transition-colors cursor-pointer"
            >
              <KeyRound className="h-3.5 w-3.5 text-amber-500" />
              <span>Configure Clerk API Keys</span>
            </button>
          </div>

          <div className="border-t border-slate-100 dark:border-[#1e293b] pt-1 mt-1">
            <button
              onClick={() => {
                setIsDropdownOpen(false);
                signOut();
              }}
              className="w-full text-left px-3 py-2 rounded-xl text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 flex items-center gap-2.5 transition-colors cursor-pointer"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Sign Out (Dev Mode)</span>
            </button>
          </div>
        </div>
      )}

      {/* Configure Clerk Keys Helper Modal */}
      {showKeyHelpModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 dark:bg-black/75 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-white dark:bg-[#0c1222] border border-slate-200 dark:border-[#1d2744] rounded-3xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-900 flex items-center justify-center text-amber-600 shrink-0">
                <KeyRound className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Clerk Authentication Setup
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Enable production Google, SSO & Email authentication
                </p>
              </div>
            </div>

            <div className="text-xs text-slate-600 dark:text-slate-300 space-y-2 leading-relaxed bg-slate-50 dark:bg-[#10172b] p-3.5 rounded-2xl border border-slate-200 dark:border-[#1d2946]">
              <p>
                To enable Clerk in production, create a free application at{" "}
                <a
                  href="https://dashboard.clerk.com"
                  target="_blank"
                  rel="noreferrer"
                  className="text-indigo-600 dark:text-indigo-400 font-semibold underline inline-flex items-center gap-0.5"
                >
                  dashboard.clerk.com <ExternalLink className="h-2.5 w-2.5" />
                </a>{" "}
                and add these variables to your <code>.env.local</code>:
              </p>
              <div className="bg-slate-900 text-slate-200 p-2.5 rounded-xl font-mono text-[11px] select-all space-y-1">
                <div>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...</div>
                <div>CLERK_SECRET_KEY=sk_test_...</div>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                ✅ When keys are present, Hiring Desk automatically switches to Clerk's secure login and user management without code changes.
              </p>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowKeyHelpModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#1a233a] dark:hover:bg-[#222e4c] text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dev Mode Sign-In Modal */}
      {showDevSignInModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 dark:bg-black/75 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-sm bg-white dark:bg-[#0c1222] border border-slate-200 dark:border-[#1d2744] rounded-3xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-900 flex items-center justify-center text-indigo-600 shrink-0">
                <LogIn className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  HR Portal Sign In
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Development mode quick entry
                </p>
              </div>
            </div>

            <form onSubmit={handleDevSignInSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Recruiter Full Name
                </label>
                <input
                  type="text"
                  value={devRecruiterName}
                  onChange={(e) => setDevRecruiterName(e.target.value)}
                  placeholder="e.g. Sarah Jenkins"
                  className="w-full text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Company Name
                </label>
                <input
                  type="text"
                  value={devCompany}
                  onChange={(e) => setDevCompany(e.target.value)}
                  placeholder="e.g. Acme Corp"
                  className="w-full text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Work Email (Optional)
                </label>
                <input
                  type="email"
                  value={devEmail}
                  onChange={(e) => setDevEmail(e.target.value)}
                  placeholder="e.g. recruiter@company.com"
                  className="w-full text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#10172b] border border-slate-200 dark:border-[#1d2946] text-slate-900 dark:text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowDevSignInModal(false)}
                  className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-[#1a233a]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold shadow-xs hover:shadow-md transition-all cursor-pointer"
                >
                  Enter Portal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
