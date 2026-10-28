# Phase 00 — Repository Discovery and Baseline

## Status
Not started. Read-only until the owner approves implementation or scaffold changes.

## Purpose
Understand the actual repository and establish trustworthy build/test instructions before code is added or rewritten.

## Read First
`AGENTS.md`, `GOALS.md`, `PLANS.md`, `docs/ARCHITECTURE.md`, `docs/ENGINEERING_WORKFLOW.md`, and the current `harness/build-log.md`.

## Scope
- Inspect repository tree, git status, current manifests, source code, tests, configs, and existing documentation.
- Identify established stack, coding conventions, runnable commands, and existing useful code.
- Identify OS assumptions and hidden machine-specific paths.
- Record current capabilities separately from intended capabilities.
- Identify unresolved source-provider, model/license, hardware target, and packaging decisions.
- Recommend the smallest next implementation slice.

## Non-Goals
- Do not rewrite or scaffold the app during discovery.
- Do not install dependencies, run destructive migrations, modify credentials, or contact external sources unnecessarily.
- Do not assume the repository is empty or adopt the preferred stack without inspecting current implementation.

## Deliverables
- Discovery summary in the user response.
- Proposed command list for setup, lint, test, build and verification.
- List of existing files/components to preserve.
- Unresolved decisions and risks.
- Proposed exact file allowlist for Phase 01.

## Acceptance Criteria
- [ ] Git status and current changes are understood and preserved.
- [ ] Actual framework/runtime versions are observed from manifests or commands.
- [ ] Existing tests and commands have been run only where safe and practical; outcomes are reported accurately.
- [ ] Unknowns are explicitly recorded rather than guessed.
- [ ] Phase 01 scope is proposed but not started automatically.

## Verification
Read-only inspection; run only non-destructive version/status/test-discovery commands. Do not mark this phase complete until the discovery report and unresolved decisions are recorded.
