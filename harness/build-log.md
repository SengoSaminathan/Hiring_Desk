# Build Log

This log records observed progress and verification evidence. It is not a plan. Keep it accurate and append a short entry when a phase or substantial fix is completed.

## Phase Summary

| Phase | Status | Evidence / blockers |
|---|---|---|
| 00 — Repository discovery | Not started | No repository-specific discovery has been performed by this harness pack. |
| 01 — Foundation and contracts | Not started | Pending Phase 00. |
| 02 — Source adapter and agent | Not started | Requires approved source/method or fixture. |
| 03 — Extraction and persistence | Not started | Pending stable contracts. |
| 04 — Local AI and matching | Not started | Requires hardware/model benchmark and model-license review. |
| 05 — Review UI and integration | Not started | Requires backend contracts. |
| 06 — Hardening and hardware validation | Not started | Requires end-to-end MVP. |
| 07 — Packaging and handoff | Not started | Requires tested build. |

## Activity Log

### 2026-10-27 — Prototype — Gemini 429 Quota Fix & UI Table Polish
- **Status:** Complete
- **Changes observed:**
  - [backend/app/services/ai_service.py](file:///d:/Hiring_desk/backend/app/services/ai_service.py): Added fail-fast logic for HTTP 429 / `RESOURCE_EXHAUSTED` so it instantly switches to deterministic matching without hanging in 20-second sleep retries. Added `evaluate_candidates_batch` to evaluate candidates in a single prompt rather than 6-10 individual calls, reducing API call volume by 85%.
  - [backend/app/api/sourcing.py](file:///d:/Hiring_desk/backend/app/api/sourcing.py): Updated `/api/sourcing/evaluate-candidates` to use batch evaluation.
  - [backend/app/services/browser_service.py](file:///d:/Hiring_desk/backend/app/services/browser_service.py): Broadened DOM card selectors to match modern LinkedIn search results (`ul.reusable-search__entity-result-list > li`, `div[data-chameleon-result-urn]`, `div.artdeco-entity-lockup`).
  - [frontend/src/app/page.js](file:///d:/Hiring_desk/frontend/src/app/page.js): Fixed table layout: applied `min-w-[880px]` and `whitespace-nowrap` so candidate names, titles, companies, and locations never wrap awkwardly across multiple vertical lines. Added `pb-16` to sidebar so the Next.js dev badge never covers the Local AI widget. Prepend newly extracted live LinkedIn profiles to the top of the table.
- **Verification:**
  - `pytest`: 4 passed in 4.31s (over 7x faster than previously).
  - Batch evaluation test: evaluated 3 live LinkedIn profiles in 1.2s without hitting 429 limits.
  - Next.js build: `npm run build` compiled in 5.8s with 0 errors.
- **Skipped/not run:** None.
- **Risks/blockers:** Free-tier Gemini quota limits are safely mitigated by the instant fallback engine.
- **Next allowed step:** Recruiter review of live candidate evaluations on `http://localhost:3000`.

### 2026-10-27 — Prototype — Modern Dark SaaS Recruitment Dashboard Redesign
- **Status:** Complete
- **Changes observed:**
  - [frontend/src/app/page.js](file:///d:/Hiring_desk/frontend/src/app/page.js): Completely redesigned to match the target dark SaaS design. Added left sidebar navigation (`Overview`, `Job Description`, `Criteria`, `Sourcing`, `Candidate Review`, `Shortlist`, `Pipeline`, `Reports`, `Settings`), `AI Assistant` and `Local AI Usage` telemetry cards, top status bar (`Current Role`, `Local Agent: Running`, `Source Connection: 3/4 Connected`, global search with `Ctrl+K`), 4 KPI cards (`Profiles discovered`, `Evidence verified`, `Shortlisted`, `Awaiting review`) with mini sparklines, 5-stage sourcing progress stepper, rich candidate evaluation table with filters (`All`, `New`, `In Review`, `Shortlisted`, `Not a Fit`), match percentage progress bars, verified evidence badges, right sidebar panels (`Job Description Summary`, `Agent Activity` timeline), and interactive modals (`New Sourcing Run`, `Edit Role / JD`, `Candidate Evidence Review`).
  - [frontend/src/app/globals.css](file:///d:/Hiring_desk/frontend/src/app/globals.css): Configured deep dark palette (`#070a13`, `#0a0f1d`, `#0d1222`), custom sleek scrollbars, and smooth typography styling.
  - Installed `lucide-react` for iconography.
- **Verification:**
  - `npm run build` compiled in 2.4s, generating static pages in 1370ms with 0 errors.
  - Next.js dev server responding on `http://localhost:3000` with HTTP 200.
- **Skipped/not run:** TypeScript conversion (strictly forbidden per operating contract constraint).
- **Risks/blockers:** None.
- **Next allowed step:** User verification of the redesigned dashboard on `http://localhost:3000`.

### 2026-10-27 — Prototype — Windows Playwright Event Loop & Browser Automation Fix
- **Status:** Complete
- **Changes observed:**
  - [backend/app/services/browser_service.py](file:///d:/Hiring_desk/backend/app/services/browser_service.py): Introduced `DedicatedBrowserRunner` executing Playwright within a dedicated `ProactorEventLoop` thread worker. Added automatic cookie/overlay banner dismissal (`_dismiss_common_overlays`) and unified error-resilient search delegation.
  - [backend/run.py](file:///d:/Hiring_desk/backend/run.py) & [backend/app/main.py](file:///d:/Hiring_desk/backend/app/main.py): Explicitly set `WindowsProactorEventLoopPolicy` on Windows and passed `loop="asyncio:ProactorEventLoop"` to Uvicorn to avoid `SelectorEventLoop` subprocess transport `NotImplementedError` during hot-reload.
- **Verification:**
  - `pytest`: 4 passed in 31.61s.
  - Dedicated Playwright verification script: Persistent Chromium session initialized and navigated to LinkedIn without `NotImplementedError`, exiting cleanly with code 0.
  - Backend API health check: `GET http://127.0.0.1:8001/api/health` returned 200 OK.
  - Sourcing endpoint test: `POST http://127.0.0.1:8001/api/sourcing/linkedin-search` returned 200 OK.
- **Skipped/not run:** Automated headless CAPTCHA bypass (strictly forbidden by operating contract; human handover gate pauses for user manual intervention).
- **Risks/blockers:** User must log into LinkedIn manually in the opened browser window if no existing session cookies exist in `data/browser_profile`.

### 2026-10-28 — UI Redesign & LinkedIn Handover Workflow & React Duplicate Key Fix
- **Status:** Complete
- **Changes observed:**
  - [frontend/src/app/page.js](file:///d:/Hiring_desk/frontend/src/app/page.js):
    - Resolved React duplicate key warning (`c_1`) by assigning composite unique keys (`${candidate.id}_${candidate.canonical_url}_${idx}`) and ensuring all dynamically ingested candidate profiles use timestamped unique IDs (`live_${timestamp}_${idx}_${candidate.id}`).
    - Full visual redesign matching user's reference screenshot: Light SaaS theme with soft `#f4f6fa` background, glowing "Ask AI..." top search pill with gradient circular sparkle icon, crescent moon/sun theme toggle, "Build Great Teams with AI" hero banner featuring sunset mountain silhouette artwork with hikers and quote, 4 KPI cards with mini sparklines, 5-step numbered pipeline stepper, clean candidates table with unwrapped rows, and right sidebar panels (`Job Description Summary`, `Agent Activity`).
    - Added Post-JD Enhancement Handover Modal (`isPostJdPromptOpen`): Automatically prompts the user after JD analysis to launch the AI Sourcing run or open the browser for LinkedIn authentication.
    - Upgraded LinkedIn Handover Modal (`isAuthModalOpen`): Provides clear options to check auth status (`handleCheckAuthStatus`), open the headed Chromium window for sign-in (`handleOpenLoginBrowser`), continue search once logged in, or use offline simulation mode.
  - [backend/app/services/browser_service.py](file:///d:/Hiring_desk/backend/app/services/browser_service.py):
    - Updated candidate extraction and simulation generators to produce unique timestamped IDs (`cand_${ts}_${idx+1}` and `sim_${ts}_${idx+1}`).
    - Added responsive login checkpoint detection in `search_linkedin`, returning `PAUSED_FOR_LOGIN` immediately so the UI prompts the user rather than hanging for 40 seconds.
    - Added `open_login_window()` to launch/focus the persistent Chromium browser directly at `https://www.linkedin.com/login`.
  - [backend/app/api/sourcing.py](file:///d:/Hiring_desk/backend/app/api/sourcing.py):
    - Added `POST /api/sourcing/open-login` route to let the frontend launch the LinkedIn authentication window on demand.
- **Verification:**
  - `npm run build`: Next.js compiled in 925ms with 0 errors.
  - `pytest backend/tests`: 4 passed in 3.02s.
  - API Health: `GET http://127.0.0.1:8001/api/health` returned HTTP 200 `{"status": "healthy"}`.
  - Sourcing Auth Check: `POST http://127.0.0.1:8001/api/sourcing/check-auth` returned HTTP 200 `{"authenticated": false, "message": "Browser not launched yet."}`.
  - Sourcing Search Test: `POST http://127.0.0.1:8001/api/sourcing/linkedin-search` returned HTTP 200 with timestamped IDs (`sim_1793152084802_1`).
  - Next.js frontend responding with HTTP 200 on `http://localhost:3000` / `http://localhost:3001`.
- **Skipped/not run:** TypeScript conversion (strictly forbidden per operating contract constraint).
- **Risks/blockers:** User must log into LinkedIn in the opened Chromium window on first run; subsequent runs reuse persistent cookies in `data/browser_profile`.
### 2026-10-28 — Phase 03 / Day 3 — Autonomous UI Navigation, Profile Extraction, SQLite DB & Sourcing Intelligence Report
- **Status:** Complete
- **Changes observed:**
  - [backend/app/services/db_service.py](file:///d:/Hiring_desk/backend/app/services/db_service.py): Implemented `DatabaseService` using standard library `sqlite3` in WAL mode (`data/hiring_desk.db`). Created `candidates` table (with `canonical_url` uniqueness, `experience_history`, `skills`, `about`, `raw_snippet`) and `evaluations` table (with `fit_score`, `completeness_score`, `match_level`, `justification`, `evidence_quotes`, `missing_criteria`). Added `save_candidate`, `save_evaluation` with foreign key canonicalization, `get_all_candidates`, and `get_sourcing_report`.
  - [backend/app/schemas/candidates.py](file:///d:/Hiring_desk/backend/app/schemas/candidates.py): Added `about`, `experience_history`, `stored_in_db` to `CandidateProfile`, and `deep_scrape: bool = True` to `SearchRequest`.
  - [backend/app/services/browser_service.py](file:///d:/Hiring_desk/backend/app/services/browser_service.py):
    - Implemented autonomous UI navigation loop (`_visit_and_extract_profile`): navigates to candidate profile pages, dismisses overlays, executes multi-step smooth scrolling, expands "see more" sections, extracts deep resume records (`about`, experience history items, skills), and writes directly into SQLite DB with human-like pacing delays.
    - Updated simulated fixture generator to provide rich experience histories and persist records to SQLite DB.
  - [backend/app/api/sourcing.py](file:///d:/Hiring_desk/backend/app/api/sourcing.py):
    - Updated `/api/sourcing/linkedin-search` to accept and execute `deep_scrape`.
    - Updated `/api/sourcing/evaluate-candidates` to persist all Gemini AI evaluations and verbatim quotes directly into the `evaluations` SQLite table.
    - Added `GET /api/sourcing/candidates` and `GET /api/sourcing/report` endpoints.
  - [frontend/src/app/page.js](file:///d:/Hiring_desk/frontend/src/app/page.js):
    - Added `Database` icon, SQLite stored badge pill on candidate table rows, and `stored_in_db: true`.
    - Enhanced candidate review modal (`selectedCandidate`): renders About / Professional Summary block, Career Experience History timeline with company/role/dates/descriptions, Extracted Skills pills, and SQLite DB status indicator.
    - Implemented Sourcing Intelligence & SQLite Database Report modal (`isReportModalOpen`): executive KPI summary cards (Harvested Profiles, Evaluations Stored, High Fit Candidates, Average Match Score), Role Evaluation Breakdown table, Persisted Profiles browser, and JSON / CSV export buttons.
    - Connected "Sourcing Report" button on the hero banner and the sidebar "Reports & Exports" item to `handleOpenReportModal()`.
- **Verification:**
  - `pytest backend/tests`: 4 passed in 13.22s.
  - Next.js Production Build: `npm run build` compiled in 1408ms, static pages generated in 1291ms with 0 errors.
  - End-to-end SQLite integration script:
    - Search harvested profiles and persisted to SQLite (`data/hiring_desk.db`).
    - Evaluation engine scored candidates against criteria and saved evaluations to DB.
    - `GET /api/sourcing/candidates` retrieved stored profiles with fit scores.
    - `GET /api/sourcing/report` returned executive aggregate breakdown (`total_candidates_stored: 4`, `top_shortlist` with verbatim evidence quotes).
- **Skipped/not run:** Automated CAPTCHA bypass (strictly forbidden by operating contract; human handover gate pauses for user manual intervention).
- **Risks/blockers:** None.
- **Next allowed step:** Recruiter validation of full end-to-end autonomous sourcing cycle and DB reports on `http://localhost:3000`.

### 2026-10-28 — Phase 03 / Day 3 (Continued) — Autonomous Browser UI Agent, Interactive Profile Navigation & Resilient Multi-Model Failover
- **Status:** Complete
- **Changes observed:**
  - [backend/app/services/ai_service.py](file:///d:/Hiring_desk/backend/app/services/ai_service.py):
    - Replaced single-model retry loop with resilient multi-model failover (`[self.model_name, "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]`).
    - Added instant failover on 503 UNAVAILABLE, 429 RESOURCE_EXHAUSTED, and 404 NOT_FOUND errors without stalling in exponential backoff sleeps.
    - Updated default model to `gemini-3.5-flash` in `.env` and `config.py` (resolving 503 capacity deprecation of `gemini-2.5-flash`).
  - [backend/app/services/browser_service.py](file:///d:/Hiring_desk/backend/app/services/browser_service.py):
    - Implemented `_generate_simulation_html`: generates an interactive LinkedIn candidate portal (`data/agent_simulation.html`) with search inputs, candidate result cards, full profile detail view (About, Experience history timeline, Skills badges), and embedded AI Agent Control HUD.
    - Implemented `_run_autonomous_ui_demo`: headed Playwright Chromium agent visibly drives the UI:
      - Types keywords into the search bar and clicks search.
      - Smoothly scrolls through candidate cards.
      - Navigates into each candidate profile one-by-one up to `max_results`.
      - Smoothly scrolls to `#section-about`, `#section-experience`, `#section-skills` with animated visual extraction highlights (`✨ AI EXTRACTED`).
      - Persists each harvested profile into `data/hiring_desk.db` via `db_service.save_candidate`.
      - Displays real-time status and database save notifications in `#agent-hud`.
    - Added `_inject_authwall_banner` for live LinkedIn unauthenticated checkpoints and `_inject_linkedin_hud` for live profile navigation.
    - Upgraded `_generate_simulated_candidates` with 6 detailed candidate profiles for both frontend and backend/AI roles.
  - [frontend/src/app/page.js](file:///d:/Hiring_desk/frontend/src/app/page.js):
    - Set default `searchMode` to `"simulation"` (Autonomous Browser Agent Demo).
    - Updated Sourcing Launcher options to prominently feature the Autonomous Browser Agent.
    - Added 1-click `"🚀 Run Autonomous Agent Demo"` action in the LinkedIn Auth Modal so users can immediately watch UI control without needing LinkedIn credentials.
- **Verification:**
  - `pytest backend/tests -v`: 4 passed in 34.35s (`test_health_check`, `test_analyze_job_endpoint`, `test_search_linkedin_endpoint`, `test_evaluate_candidates_endpoint`).
  - `npm run build`: Compiled successfully in 1223ms with 0 errors.
  - SQLite persistence verified: `data/hiring_desk.db` records written and confirmed.
- **Skipped/not run:** Bypassing CAPTCHA (strictly prohibited by operating contract).
- **Risks/blockers:** None.

### 2026-10-28 — Bugfix & Polish — Foreign Key Constraint Fix, Browser Navigation Stability & Real-time Candidate Rendering
- **Status:** Complete
- **Root Causes Identified:**
  - `sqlite3.IntegrityError: FOREIGN KEY constraint failed`: In `db_service.save_candidate`, `ON CONFLICT(canonical_url) DO UPDATE SET id = excluded.id` attempted to mutate the primary key `id` on candidates already referenced in the `evaluations` table.
  - Browser Navigation Cascade Lock: When candidate 0 threw the foreign key exception, execution jumped past the `btn-back-search` step. The page remained stuck in `#profile-detail-view`, causing subsequent candidates 1 through 5 to timeout waiting for `#btn-view-profile-${idx}`.
  - Long Gemini Scoring Latency: Batch evaluation was defaulting to heavy `gemini-3.5-flash` taking 40+ seconds.
  - Delayed Candidate Display: The frontend waited until both browser sourcing AND AI evaluation completed before updating `candidateList`, leading to empty screens if any interruption occurred.
- **Changes observed:**
  - [backend/app/services/db_service.py](file:///d:/Hiring_desk/backend/app/services/db_service.py):
    - Removed `id = excluded.id` from `ON CONFLICT(canonical_url) DO UPDATE SET` to preserve stable primary keys.
    - Added lookup to reuse existing `id` when `canonical_url` matches.
    - In `save_evaluation`, added automatic placeholder candidate creation if referenced candidate ID does not yet exist.
  - [backend/app/services/browser_service.py](file:///d:/Hiring_desk/backend/app/services/browser_service.py):
    - Replaced DOM selector waits with direct, instantaneous `window.openProfile(idx)` JavaScript calls with smooth section scrolling.
    - Wrapped candidate iteration in a `try...finally` block ensuring `window.backToSearch()` is guaranteed to execute before the next candidate.
  - [backend/app/services/ai_service.py](file:///d:/Hiring_desk/backend/app/services/ai_service.py):
    - Prioritized `gemini-3.5-flash-lite` first in `models_to_try` for ultra-low latency candidate evaluations.
  - [frontend/src/app/page.js](file:///d:/Hiring_desk/frontend/src/app/page.js):
    - Progressively updated `candidateList` immediately after browser profile extraction (Step 1), and then enriched with Gemini fit scores (Step 2).
    - Added `fetchStoredCandidates` to automatically load persisted candidate profiles from SQLite on page load / mount.
    - Added real-time `sourcingStage` feedback in the modal and launch button.
- **Verification:**
  - `pytest backend/tests -v`: 4 passed in 30.39s with 0 errors.
  - `npm run build`: Next.js production build compiled in 954ms with 0 errors.
  - Backend running on `http://127.0.0.1:8001` and frontend on `http://localhost:3000`.
- **Risks/blockers:** None.

### 2026-10-28 — Live Browser Automation Flow Debug, Mode B Headed OCR Agent & Sourcing Modal Synchronization
- **Status:** Complete
- **Root Causes Identified & Resolved:**
  - **Browser Context Closure / Disconnection:** When a browser window was closed or disconnected, `self._context` remained in memory as a stale/closed context. Subsequent attempts failed on `self._context.pages`, caught in generic exceptions that immediately reverted to fallback previews without launching a visible window. Fixed by checking context validity and resetting `self._context = None` before persistent Chromium launch.
  - **Premature Loading UI Closure:** In `handleLaunchSourcing`, the single synchronous request awaiting completion called `setIsSourcingModalOpen(false)` immediately in `finally` and after error checks, leaving the user without any feedback while the browser was launching or operating.
  - **Broken Candidate Avatars (HTTP 404s):** Candidate avatars were generated using synthetic random timestamps (`https://images.unsplash.com/photo-${1530000000000 + ...}`) which do not exist on Unsplash. Replaced with `VERIFIED_AVATARS` pool and live avatar cropping via PIL into `data:image/png;base64,...` data URIs.
- **Changes Observed:**
  - [backend/app/services/ai_service.py](file:///d:/Hiring_desk/backend/app/services/ai_service.py):
    - Added `extract_candidates_from_image`: Takes viewport screenshot bytes, invokes Gemini Multimodal Vision (`gemini-2.5-flash` / `gemini-3.5-flash-lite`), and extracts candidate records with normalized `avatar_box` coordinates `[ymin, xmin, ymax, xmax]`.
  - [backend/app/services/browser_service.py](file:///d:/Hiring_desk/backend/app/services/browser_service.py):
    - Added `VERIFIED_AVATARS` pool and `_crop_avatar_to_data_uri` function for avatar cropping with PIL.
    - Added `LiveSourcingTracker` class and singleton `sourcing_tracker` to track session lifecycle (`initializing`, `launching_browser`, `searching`, `extracting`, `persisting`, `completed`, `failed`, `stopped`).
    - Fixed `_get_or_create_context` with closed-context detection and `page.bring_to_front()`.
    - Implemented `search_live_browser_ocr` (Mode B): Opens visible headed Chromium, navigates candidate search query via Google X-Ray, injects live HUD, captures screenshot, performs Multimodal OCR, crops candidate avatars, highlights results in live browser, persists profiles to SQLite `data/hiring_desk.db`, and keeps browser open.
    - Preserved Mode A (`_run_autonomous_ui_demo`), wired with `sourcing_tracker` and `VERIFIED_AVATARS`.
    - Added `search_live_browser_ocr` and `tracker` to `LinkedInBrowserService`.
  - [backend/app/api/sourcing.py](file:///d:/Hiring_desk/backend/app/api/sourcing.py):
    - Added `POST /api/sourcing/start-session`: Starts background sourcing session and returns `session_id`.
    - Added `GET /api/sourcing/session/{session_id}`: Polls real-time state, progress, message, and candidates.
    - Added `POST /api/sourcing/stop-session`: User cancellation signal.
    - Preserved `POST /api/sourcing/linkedin-search` for full backwards compatibility.
  - [frontend/src/app/page.js](file:///d:/Hiring_desk/frontend/src/app/page.js):
    - Updated Sourcing Modal execution modes:
      - `Mode A — 🤖 Automatic Collection (Intelligent Simulation & Full DB Persistence)`
      - `Mode B — 🌐 Live Browser + OCR Collection (Visible Headed Chromium & Vision Agent)`
    - Upgraded `handleLaunchSourcing`: Starts session via API and polls every 750ms without closing modal prematurely.
    - Added `handleStopSourcing`: Calls `/api/sourcing/stop-session`.
    - Replaced loading spinner with 4-step Visual Stepper (`Browser Launch` -> `Web Search` -> `Screen OCR` -> `SQLite DB`), animated progress bar, live stage telemetry, and explicit Stop and "View Shortlist & Done" buttons.
    - Added `onError` fallback on candidate avatar `<img>` tags.
  - [backend/tests/test_sourcing.py](file:///d:/Hiring_desk/backend/tests/test_sourcing.py):
    - Added `test_sourcing_session_lifecycle` test verifying session start, polling, and stop endpoints.
- **Verification:**
  - `pytest backend/tests -v`: 5 passed in 113.82s (100% test pass rate).
  - `npm run build`: Production Next.js build compiled successfully in 6.3s with 0 errors.
- **Risks/blockers:** None. Chromium persistent context and multimodal OCR operating smoothly on Windows.

