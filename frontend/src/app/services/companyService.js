/**
 * Company Profile & Recruiter Onboarding Service
 * Manages persistence, retrieval, and reactive syncing of company/recruiter metadata
 * across local storage, backend SQLite, Supabase cloud, and AI outreach workflows.
 */

const STORAGE_KEY = "hiring_desk_company_profile";

export const DEFAULT_COMPANY_PROFILE = {
  companyName: "",
  industry: "",
  recruiterName: "",
  recruiterSignature: "",
  companyDetails: "",
  location: "",
  website: "",
  employeeCount: "50-250",
  onboardingCompleted: false,
  updatedAt: null,
};

/**
 * Returns the active FastAPI backend base URL.
 */
export function getApiBase() {
  if (typeof window !== "undefined") {
    return window.__HIRING_DESK_API_BASE__ || "http://127.0.0.1:8001";
  }
  return "http://127.0.0.1:8001";
}

/**
 * Retrieve the current company profile from persistent local storage.
 * Returns default values if no profile has been configured yet.
 */
export function getCompanyProfile() {
  if (typeof window === "undefined") {
    return { ...DEFAULT_COMPANY_PROFILE };
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { ...DEFAULT_COMPANY_PROFILE };
    }
    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_COMPANY_PROFILE,
      ...parsed,
    };
  } catch (err) {
    console.warn("[companyService] Failed to read company profile from localStorage:", err);
    return { ...DEFAULT_COMPANY_PROFILE };
  }
}

/**
 * Save or update the company profile, broadcast the change, and
 * persist it to both browser localStorage and backend SQLite / Supabase tables.
 */
export function saveCompanyProfile(profileUpdates = {}) {
  if (typeof window === "undefined") {
    return { ...DEFAULT_COMPANY_PROFILE, ...profileUpdates };
  }

  try {
    const current = getCompanyProfile();
    const updated = {
      ...current,
      ...profileUpdates,
      onboardingCompleted: true,
      updatedAt: new Date().toISOString(),
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

    // Dispatch global event for in-app reactive components
    const event = new CustomEvent("companyProfileUpdated", {
      detail: updated,
    });
    window.dispatchEvent(event);

    // Asynchronously synchronize with backend SQLite and Supabase
    const apiBase = getApiBase();
    fetch(`${apiBase}/api/company/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        companyName: updated.companyName,
        industry: updated.industry,
        website: updated.website,
        location: updated.location,
        employeeCount: updated.employeeCount,
        companyDetails: updated.companyDetails,
        recruiterName: updated.recruiterName,
        recruiterSignature: updated.recruiterSignature,
        user_id: profileUpdates.user_id || profileUpdates.userId || undefined,
      }),
    })
      .then((res) => {
        if (!res.ok) {
          console.warn("[companyService] Server company sync returned HTTP", res.status);
        }
      })
      .catch((err) => {
        console.warn("[companyService] Background server company sync error:", err);
      });

    return updated;
  } catch (err) {
    console.error("[companyService] Failed to save company profile:", err);
    return { ...DEFAULT_COMPANY_PROFILE, ...profileUpdates };
  }
}

/**
 * Synchronizes user profile with the backend database upon Clerk signup / login.
 */
export async function syncUserToServer(userPayload = {}) {
  if (typeof window === "undefined" || !userPayload.id || !userPayload.email) {
    return null;
  }

  try {
    const apiBase = getApiBase();
    const res = await fetch(`${apiBase}/api/auth/sync-user`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: userPayload.id,
        email: userPayload.email,
        full_name: userPayload.fullName || userPayload.full_name || "",
        first_name: userPayload.firstName || userPayload.first_name || "",
        last_name: userPayload.lastName || userPayload.last_name || "",
        avatar_url: userPayload.avatarUrl || userPayload.avatar_url || userPayload.imageUrl || "",
        role: userPayload.role || "Recruiter",
      }),
    });

    if (res.ok) {
      const data = await res.json();
      return data.user;
    }
  } catch (err) {
    console.warn("[companyService] Failed to sync user to backend server:", err);
  }
  return null;
}

/**
 * Loads company profile from backend SQLite / Supabase database
 * and synchronizes it with local storage if found.
 */
export async function fetchCompanyProfileFromServer(userId = null) {
  if (typeof window === "undefined") return null;

  try {
    const apiBase = getApiBase();
    const url = userId
      ? `${apiBase}/api/company/profile?user_id=${encodeURIComponent(userId)}`
      : `${apiBase}/api/company/profile`;

    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return null;

    const data = await res.json();
    if (data.status === "success" && data.company) {
      const comp = data.company;
      const current = getCompanyProfile();
      const merged = {
        ...current,
        companyName: comp.name || current.companyName,
        industry: comp.industry || current.industry,
        recruiterName: comp.recruiter_name || current.recruiterName,
        recruiterSignature: comp.recruiter_signature || current.recruiterSignature,
        companyDetails: comp.value_proposition || current.companyDetails,
        location: comp.location || current.location,
        website: comp.website || current.website,
        employeeCount: comp.employee_count || current.employeeCount,
        onboardingCompleted: Boolean(comp.name && comp.name.trim()),
        updatedAt: comp.updated_at || new Date().toISOString(),
      };

      localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
      window.dispatchEvent(new CustomEvent("companyProfileUpdated", { detail: merged }));
      return merged;
    }
  } catch (err) {
    console.warn("[companyService] Could not fetch profile from server:", err);
  }
  return null;
}

/**
 * Check whether the HR recruiter has completed the company onboarding.
 */
export function isOnboardingCompleted() {
  const profile = getCompanyProfile();
  return Boolean(profile.onboardingCompleted && profile.companyName?.trim());
}

/**
 * Subscribe to company profile updates across components and windows.
 */
export function subscribeCompanyProfile(callback) {
  if (typeof window === "undefined" || typeof callback !== "function") {
    return () => {};
  }

  const handleCustomEvent = (e) => {
    if (e.detail) {
      callback(e.detail);
    } else {
      callback(getCompanyProfile());
    }
  };

  const handleStorageEvent = (e) => {
    if (e.key === STORAGE_KEY && e.newValue) {
      try {
        const parsed = JSON.parse(e.newValue);
        callback(parsed);
      } catch (err) {
        callback(getCompanyProfile());
      }
    }
  };

  window.addEventListener("companyProfileUpdated", handleCustomEvent);
  window.addEventListener("storage", handleStorageEvent);

  return () => {
    window.removeEventListener("companyProfileUpdated", handleCustomEvent);
    window.removeEventListener("storage", handleStorageEvent);
  };
}
