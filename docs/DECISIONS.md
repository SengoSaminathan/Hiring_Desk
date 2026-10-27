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
    future change.
