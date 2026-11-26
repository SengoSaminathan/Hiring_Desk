with open('frontend/src/app/page.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [previousNav, setPreviousNav] = useState("overview");

  const handleOpenCandidateProfile = useCallback((candidate) => {
    if (candidate) {
      setActiveNav((currNav) => {
        if (currNav !== "candidate_profile") {
          setPreviousNav(currNav);
        }
        return "candidate_profile";
      });
      setSelectedCandidate(candidate);
      if (candidate.target_role || candidate.job_title) {
        setEvalTargetRole(candidate.target_role || candidate.job_title);
      }
    } else {
      setSelectedCandidate(null);
      setActiveNav((currNav) => (currNav === "candidate_profile" ? previousNav || "overview" : currNav));
    }
  }, [previousNav]);'''

new_block = '''  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [previousNav, setPreviousNav] = useState("overview");

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
        if (isJdEditorOpen) {
          setIsJdEditorOpen(false);
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
    isJdEditorOpen,
    activeNav,
    previousNav,
    navigateTo,
  ]);'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print("Replaced old_block (LF)")
elif old_block.replace('\n', '\r\n') in content:
    content = content.replace(old_block.replace('\n', '\r\n'), new_block.replace('\n', '\r\n'))
    print("Replaced old_block (CRLF)")
else:
    print("ERROR: old_block not found in content!")

with open('frontend/src/app/page.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Navigation & Escape key logic integrated successfully!")

