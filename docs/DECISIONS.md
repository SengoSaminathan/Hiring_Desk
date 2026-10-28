# Architecture Decision Log

Record decisions that materially affect architecture, dependencies,
security, or product scope. Add new entries at the top. Revise entries
only when a decision is intentionally superseded.

## ADR-0001: Local-first, hardware-adaptive design

-   **Status:** Accepted
-   **Decision:** Core functions do not require a discrete GPU or local
    LLM. Local AI is optional and selected based on measured runtime
    capability.
-   **Reason:** The software targets a broad range of laptops.
-   **Consequences:** Capability detection, small-model benchmarks,
    bounded concurrency, deterministic fallback.

## ADR-0002: Browser automation respects source permissions

-   **Status:** Accepted
-   **Decision:** Automate only sources and methods that permit the
    intended use. Never bypass CAPTCHA, login restrictions, access
    controls, or rate limits.
-   **Reason:** Technical possibility does not establish authorization.
-   **Consequences:** Source adapters carry policy metadata; some
    sources are manual-only or require official/licensed integrations.

## ADR-0003: Transparent candidate matching

-   **Status:** Accepted
-   **Decision:** Rankings expose criteria, evidence, missing fields,
    and rubric version. Human review remains required.
-   **Reason:** Profile data may be incomplete or stale, and hiring
    decisions are consequential.
-   **Consequences:** Store evidence provenance and uncertainty
    separately from score.

## ADR-0004: MVP persistence

-   **Status:** Accepted
-   **Decision:** Use SQLite for the single-user local MVP.
-   **Reason:** Low operational overhead; no database server required.
-   **Consequences:** Migrations, transactions, backups, and
    repository/service layer.

## ADR-0005: Frontend stack preferences

-   **Status:** Accepted
-   **Decision:** React with JavaScript and standard CSS; no TypeScript
    or Tailwind unless explicitly approved.
-   **Reason:** Matches stated project preferences.
-   **Consequences:** Keep conventions consistent and document any
    future change. Superseded by ADR-0006.

## ADR-0006: Frontend stack updated to Next.js and Tailwind CSS (JavaScript)

-   **Status:** Accepted (Owner Directed)
-   **Decision:** Use Next.js with JavaScript (no TypeScript) and Tailwind CSS for the frontend application.
-   **Reason:** Explicit owner direction for rapid UI development, modern server/client components, and Tailwind styling.
-   **Consequences:** Frontend scaffolded with Next.js (JavaScript + Tailwind CSS). TypeScript remains excluded per request.

## ADR-0007: Cloud persistence with Supabase and Backblaze B2

-   **Status:** Accepted (Owner Directed)
-   **Decision:** Use Supabase (PostgreSQL) for relational candidate data and Backblaze B2 (S3-compatible) for candidate resume storage.
-   **Reason:** Eliminates local database bloat and ensures production reliability across client laptops.
-   **Consequences:** Backend connects to Supabase and uploads resumes to Backblaze B2 via S3 API.

## ADR-0008: Live Headed Chromium Browser with Multimodal Vision OCR and Session State Tracker

-   **Status:** Accepted
-   **Decision:** Support two complementary sourcing modes: Mode A (Autonomous UI Simulation with profile traversal) and Mode B (Live Headed Chromium with Multimodal Vision OCR via Gemini). Manage browser process lifecycle via `LiveSourcingTracker` with asynchronous polling.
-   **Reason:** Direct unauthenticated LinkedIn scraping triggers authwalls/captchas. Google X-Ray search combined with Gemini Vision OCR reliably reads candidate cards, crops avatars, highlights DOM elements, and keeps the browser window open for user visibility without premature closure.
-   **Consequences:** Sourcing UI monitors live execution state machine (`launching_browser` -> `searching` -> `extracting` -> `persisting` -> `completed`). Avatars cropped from screen via PIL and encoded as data URIs.


