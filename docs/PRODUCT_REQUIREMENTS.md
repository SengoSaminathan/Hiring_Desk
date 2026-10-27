# Product Requirements

## Goal

Build a laptop-friendly, local-first desktop application that helps HR
users discover and review candidates for a role. It converts a JD into a
search plan, collects candidate evidence from permitted sources,
compares evidence to role requirements, and exports a transparent
shortlist.

## Users and Initial Target

-   HR sourcers and recruiters.
-   Initial target: single-user Windows desktop application.
-   Future portability: macOS and other supported platforms after
    validation.

## Core User Journey

1.  Create a sourcing job by pasting/importing a JD.
2.  Review and edit extracted role requirements.
3.  Generate search queries and select approved sources.
4.  Start a collection run and observe progress.
5.  Pause, resume, or cancel a run.
6.  Review candidate records, source URLs, evidence, missing fields, and
    match explanations.
7.  Correct data where necessary.
8.  Export to CSV or Excel.
9.  Reopen previous jobs and review run history.

## MVP Scope

-   JD input and structured requirement extraction.
-   Search-query planning.
-   Pluggable source adapter interface.
-   Browser automation only for sources and actions permitted by their
    terms.
-   Candidate extraction and normalization.
-   URL normalization and deduplication.
-   Evidence-based matching with configurable weights.
-   SQLite persistence.
-   Progress events, cancellation, bounded retries, and recovery.
-   Candidate review UI and CSV export.
-   Local hardware/runtime diagnostics.
-   Rules-based fallback when a local model cannot run.

## Out of Scope for MVP

-   Autonomous candidate outreach or messaging.
-   Bypassing CAPTCHAs, authentication barriers, access controls, or
    rate limits.
-   Unauthorized scraping of LinkedIn or other restricted platforms.
-   Automated hiring decisions without human review.
-   Inferring protected or sensitive characteristics.
-   Multi-user cloud infrastructure or distributed queues.
-   Guaranteeing acceptable LLM performance on every laptop.

## Hardware Adaptability

-   No discrete GPU requirement.
-   Core UI, persistence, run management, and deterministic matching
    work without a local LLM.
-   Detect OS, available memory, free disk space, browser runtime, model
    runtime, and GPU support where practical.
-   Choose model size, context length, batch size, and concurrency
    conservatively.
-   Process candidates sequentially on constrained machines.
-   Download models only after consent and a disk-space check.
-   Explain unavailable or slow features clearly.
-   Publish minimum hardware only after profiling representative
    devices.

## Candidate Data Principles

-   Collect only fields needed for the role and supported by the source.
-   Preserve source URL, retrieval time, and evidence for extracted
    fields.
-   Represent unknown values as unknown; do not invent missing skills or
    experience.
-   Store evidence coverage separately from match score.
-   Allow human correction and deletion.
-   Keep data local by default.

## Success Criteria

-   User can create a job, run an approved source adapter, review
    records, and export a shortlist.
-   Candidate records are deduplicated across queries.
-   Match explanations point to stored evidence.
-   UI remains responsive during a run.
-   Cancelled runs stop cleanly.
-   Application opens and supports non-AI functions without Ollama/model
    access.
-   Tests cover critical parsing, scoring, persistence, and run-state
    transitions.
-   No source restriction is bypassed.
