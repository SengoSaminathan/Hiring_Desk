# Phase 05 — Review UI and End-to-End Integration

## Status
Not started. Requires stable backend contracts.

## Purpose
Provide HR users a clear way to create jobs, monitor the agent, and inspect/export evidence-backed results.

## Scope
- JD input and requirement review.
- Source/method selection with policy status visible.
- Start/pause/resume/cancel and progress display.
- Candidate table/details with sources, evidence, missing fields, match score and rubric explanation.
- Correction/deletion and CSV export interactions.
- Accessible keyboard focus, semantic controls, error/empty/loading/partial-success states.
- Progress streaming with reconnection behavior; keep long-running work off the UI thread.

## Non-Goals
- No autonomous candidate outreach or irreversible external action.
- No final hiring decisions by the model.
- Do not expose local secrets or raw browser session contents in the UI.

## Acceptance Criteria
- [ ] UI remains responsive during long-running work.
- [ ] Run status is understandable and controls reflect valid state transitions.
- [ ] Errors preserve entered JD and already collected records.
- [ ] Candidate scores expose evidence and uncertainty.
- [ ] Keyboard navigation and primary accessibility checks pass.
- [ ] End-to-end tests work with deterministic fake/fixture sources.

## Verification
Run frontend unit/component tests, production build, API/UI integration tests, and an accessibility review.
