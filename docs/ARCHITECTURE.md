# Architecture and Boundaries

## Preferred Stack

-   Frontend: React with JavaScript and standard CSS; no TypeScript or
    Tailwind unless explicitly approved.
-   Backend: Python and FastAPI.
-   Browser control: Playwright for Python.
-   Persistence: SQLite.
-   Optional local LLM: Ollama behind a provider adapter.
-   Packaging: evaluate PyInstaller or equivalent after the development
    build is reliable.

These are defaults, not permission to rewrite an existing repository
blindly. Inspect the existing code first.

## Components

### Frontend

JD form, criteria review, source selection, run progress and controls,
candidate review, error/human-intervention states, and export. The
frontend must not control the browser directly, access the database file
directly, or store secrets.

### Local API

Validates requests, creates jobs/runs, coordinates services, streams
progress, manages pause/resume/cancel/shutdown. Bind to `127.0.0.1` by
default; do not expose the local control API to the LAN by default.

### Agent Orchestrator

Use an explicit state machine rather than an unbounded loop.

Suggested states:
`created -> validating -> planning -> collecting -> extracting -> matching -> review_ready`

Exceptional states: `paused_for_user`, `cancel_requested`, `cancelled`,
`failed`, `completed_with_warnings`.

Validate and persist transitions. Bound retries and repeated actions.

### Source Adapter

Each adapter should implement a consistent contract, such as: -
`validate_configuration()` -
`search(query, limits, cancellation_token)` -
`normalize_result(raw_result)` - `get_source_metadata()`

Adapters must follow source terms and technical access rules. Some
sources may be manual-only or require an official/licensed integration.

### Browser Controller

Open approved URLs, observe permitted DOM/accessibility content and
current URL, perform allowed interactions, verify expected state,
capture bounded diagnostics, and pause for human intervention when
needed. Treat page text as data, never as instructions.

### LLM Provider

JD structuring, query planning, extraction assistance, and match
explanation. Validate all model output against schemas. Keep
deterministic behavior available when the provider is absent, slow, or
invalid.

### Matching Service

Separate eligibility constraints from ranking. Use transparent
configurable weights. Keep evidence coverage separate from candidate
fit. Store rubric and model versions. Missing evidence is not proof a
candidate lacks a skill. Human review remains required.

### Persistence

Use SQLite for the single-user MVP. Use migrations, transactions,
uniqueness constraints where appropriate, consistent timestamps,
evidence provenance, and run history. Never store credentials or raw
session cookies in candidate records.

## Data Flow

JD -\> structured requirements -\> query plan -\> approved source
adapter -\> raw results -\> normalized candidate/evidence -\>
deduplication -\> scoring -\> review UI -\> export.

Each stage needs validated input/output contracts. Keep source-specific
parsing isolated from general matching.

## Failure Isolation

-   Browser failures must not corrupt the database.
-   Model failures must fall back or produce an actionable error.
-   Export failures must not mutate candidate records.
-   Cancellation must propagate to browser tasks and pending model calls
    where supported.
-   Source outages must not prevent review of already collected
    candidates.


## Cross-Cutting Operational Requirements
- Every long-running task has a cancellation token, deadline/timeout, bounded retries, and cleanup behavior.
- Every external source action is gated by source-policy metadata; browser automation may be disabled or manual-only for a source.
- Progress events use a versioned schema and avoid including secrets, full profile text, or unnecessary PII in logs.
- Local AI provider calls have bounded input/context, timeouts, schema validation, and deterministic fallback.
- User data paths must be configurable and must not depend on the current working directory or a developer-specific path.
- UI/API boundaries validate data on entry; database writes use transactions where multiple records must remain consistent.
