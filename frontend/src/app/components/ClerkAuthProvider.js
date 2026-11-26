"use client";

import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from "react";
import { ClerkProvider, useUser, useClerk } from "@clerk/nextjs";
import CompanyProfileModal from "./CompanyProfileModal";
import {
  getCompanyProfile,
  saveCompanyProfile,
  isOnboardingCompleted,
  subscribeCompanyProfile,
  syncUserToServer,
  fetchCompanyProfileFromServer,
} from "../services/companyService";

// Check if Clerk publishable key is present and configured
const publishableKey =
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ||
  "pk_test_ZW1lcmdpbmctY29sdC01MDY5LmNsZXJrLmFjY291bnRzLmRldiQ";
export const isClerkConfigured = Boolean(
  publishableKey &&
    typeof publishableKey === "string" &&
    publishableKey.trim().length > 0 &&
    !publishableKey.includes("placeholder") &&
    !publishableKey.includes("YOUR_")
);

// Unified Authentication Context
const AppAuthContext = createContext({
  isSignedIn: false,
  isLoaded: false,
  isClerkConfigured: false,
  user: null,
  companyProfile: null,
  signIn: () => {},
  signUp: () => {},
  signOut: () => {},
  openCompanyProfileModal: () => {},
});

export const useAppAuth = () => useContext(AppAuthContext);

/**
 * Internal Dev Auth Provider when Clerk keys are not configured.
 * Provides frictionless offline / local development authentication.
 */
function DevAuthProvider({ children, onOpenCompanyModal }) {
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [companyProfile, setCompanyProfile] = useState(() => getCompanyProfile());

  useEffect(() => {
    // Read persisted dev sign-in status
    const persisted = localStorage.getItem("hiring_desk_dev_signed_in");
    if (persisted !== null) {
      setIsSignedIn(persisted === "true");
    } else {
      setIsSignedIn(false);
    }
    setCompanyProfile(getCompanyProfile());
    setIsLoaded(true);

    const unsubscribe = subscribeCompanyProfile((updated) => {
      setCompanyProfile(updated);
    });
    return unsubscribe;
  }, []);

  const signIn = (customData = {}) => {
    if (customData.companyName || customData.recruiterName) {
      saveCompanyProfile({
        ...(customData.companyName ? { companyName: customData.companyName } : {}),
        ...(customData.recruiterName ? { recruiterName: customData.recruiterName } : {}),
      });
    }
    localStorage.setItem("hiring_desk_dev_signed_in", "true");
    setIsSignedIn(true);
  };

  const signUp = (customData = {}) => {
    signIn(customData);
  };

  const signOut = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("hiring_desk_clerk_authenticated");
    }
    localStorage.setItem("hiring_desk_dev_signed_in", "false");
    setIsSignedIn(false);
  };

  const user = useMemo(() => {
    if (!isSignedIn) return null;
    const name = companyProfile.recruiterName?.trim() || "HR Recruiter";
    const parts = name.split(" ");
    return {
      id: "dev_user_hr",
      fullName: name,
      firstName: parts[0] || "HR",
      lastName: parts.slice(1).join(" ") || "Recruiter",
      primaryEmailAddress: {
        emailAddress: `${name.toLowerCase().replace(/[^a-z0-9]/g, "") || "recruiter"}@${
          companyProfile.companyName?.toLowerCase().replace(/[^a-z0-9]/g, "") || "company"
        }.com`,
      },
      imageUrl: null,
    };
  }, [isSignedIn, companyProfile]);

  const value = {
    isSignedIn,
    isLoaded,
    isClerkConfigured: false,
    user,
    companyProfile,
    signIn,
    signUp,
    signOut,
    openCompanyProfileModal: onOpenCompanyModal,
  };

  return <AppAuthContext.Provider value={value}>{children}</AppAuthContext.Provider>;
}

/**
 * Bridge inside ClerkProvider to expose standard useAppAuth interface
 */
function ClerkAuthBridge({ children, onOpenCompanyModal, onUserSync }) {
  const { user: clerkUser, isLoaded, isSignedIn } = useUser();
  const { signOut: clerkSignOut, openSignIn, openSignUp } = useClerk();
  const [companyProfile, setCompanyProfile] = useState(() => getCompanyProfile());

  useEffect(() => {
    setCompanyProfile(getCompanyProfile());
    const unsubscribe = subscribeCompanyProfile((updated) => {
      setCompanyProfile(updated);
    });
    return unsubscribe;
  }, []);

  // When Clerk user logs in or signs up:
  // 1. Sync user details to backend SQLite/Supabase `users` table
  // 2. Load linked company profile from server if already configured
  useEffect(() => {
    if (isSignedIn && clerkUser) {
      if (onUserSync) {
        onUserSync(clerkUser.id);
      }

      const email = clerkUser.primaryEmailAddress?.emailAddress || "";
      if (clerkUser.id && email) {
        syncUserToServer({
          id: clerkUser.id,
          email: email,
          fullName: clerkUser.fullName || "",
          firstName: clerkUser.firstName || "",
          lastName: clerkUser.lastName || "",
          avatarUrl: clerkUser.imageUrl || "",
          role: "Recruiter",
        }).then((synced) => {
          if (synced?.company_id) {
            fetchCompanyProfileFromServer(clerkUser.id);
          }
        });
      }

      const current = getCompanyProfile();
      if (!current.recruiterName && clerkUser.fullName) {
        saveCompanyProfile({ recruiterName: clerkUser.fullName, user_id: clerkUser.id });
      } else if (clerkUser.id) {
        fetchCompanyProfileFromServer(clerkUser.id);
      }
    }
  }, [isSignedIn, clerkUser, onUserSync]);

  const value = {
    isSignedIn: Boolean(isSignedIn),
    isLoaded: Boolean(isLoaded),
    isClerkConfigured: true,
    user: clerkUser,
    companyProfile,
    signIn: (opts) => (openSignIn ? openSignIn(opts) : null),
    signUp: (opts) => (openSignUp ? openSignUp(opts) : null),
    signOut: (opts) => {
      if (typeof window !== "undefined") {
        localStorage.removeItem("hiring_desk_clerk_authenticated");
      }
      return clerkSignOut ? clerkSignOut(opts) : null;
    },
    openCompanyProfileModal: onOpenCompanyModal,
  };

  return <AppAuthContext.Provider value={value}>{children}</AppAuthContext.Provider>;
}

/**
 * Inner watcher that ONLY triggers onboarding modal when signed in and onboarding is incomplete.
 * Unauthenticated users will never see the onboarding modal.
 */
function OnboardingModalWatcher({ onTriggerOnboarding }) {
  const { isSignedIn, isLoaded } = useAppAuth();

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      const completed = isOnboardingCompleted();
      if (!completed) {
        onTriggerOnboarding();
      }
    }
  }, [isLoaded, isSignedIn, onTriggerOnboarding]);

  return null;
}

/**
 * Root Clerk & Dev Auth Provider
 * Automatically prompts for Company Profile Onboarding ONLY if signed in and onboarding is incomplete.
 */
export default function ClerkAuthProvider({ children }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isFirstTimeOnboarding, setIsFirstTimeOnboarding] = useState(false);
  const [activeUserId, setActiveUserId] = useState(null);

  // Listen for custom modal open triggers (e.g. from user profile settings)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const handleOpenRequest = () => {
        setIsFirstTimeOnboarding(false);
        setIsModalOpen(true);
      };
      window.addEventListener("openCompanyProfileModal", handleOpenRequest);
      return () => {
        window.removeEventListener("openCompanyProfileModal", handleOpenRequest);
      };
    }
  }, []);

  const openCompanyModal = useCallback(() => {
    setIsFirstTimeOnboarding(false);
    setIsModalOpen(true);
  }, []);

  const triggerOnboarding = useCallback(() => {
    setIsFirstTimeOnboarding(true);
    setIsModalOpen(true);
  }, []);

  const handleModalClose = () => {
    setIsModalOpen(false);
    setIsFirstTimeOnboarding(false);
  };

  const authContent = isClerkConfigured ? (
    <ClerkProvider publishableKey={publishableKey}>
      <ClerkAuthBridge onOpenCompanyModal={openCompanyModal} onUserSync={setActiveUserId}>
        <OnboardingModalWatcher onTriggerOnboarding={triggerOnboarding} />
        {children}
      </ClerkAuthBridge>
    </ClerkProvider>
  ) : (
    <DevAuthProvider onOpenCompanyModal={openCompanyModal}>
      <OnboardingModalWatcher onTriggerOnboarding={triggerOnboarding} />
      {children}
    </DevAuthProvider>
  );

  return (
    <>
      {authContent}
      {/* Onboarding & Profile Modal */}
      <CompanyProfileModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        isFirstTime={isFirstTimeOnboarding}
        userId={activeUserId}
      />
    </>
  );
}
