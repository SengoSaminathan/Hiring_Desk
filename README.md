# Candidate-Sourcing Agent — Harness Engineering Pack

This pack is a starter harness for coding agents. It defines project intent, phase boundaries, evidence-based verification, and durable engineering constraints. It does not claim the application is implemented or tested.

## Start Here
1. `AGENTS.md` — concise agent contract and routing.
2. `GOALS.md` — outcomes and non-goals.
3. `PLANS.md` — phase order.
4. `harness/build-log.md` — observed progress and verification evidence.
5. `harness/build/00-repository-discovery.md` — first, read-only implementation phase.
6. Read the relevant `docs/` file when working on that area.

## Files
- `AGENTS.md` — operating rules, source-of-truth ownership, definition of done.
- `GOALS.md` — intended outcomes and success conditions.
- `PLANS.md` — ordered phases and status.
- `PROMPTS.md` — reusable prompts for discovery, planning, implementation, verification, review and handoff.
- `harness/build/` — phase-specific scope, non-goals, acceptance criteria and verification.
- `harness/context/README.md` — format for discoveries that materially affect a phase.
- `harness/build-log.md` — actual progress and observed test evidence.
- `docs/` — detailed product, architecture, setup, security, testing, traceability, accessibility, enforcement and references.

## Integration Steps
1. Extract into the project repository root.
2. If the repository already has instructions/plans, merge carefully rather than overwriting them.
3. Run Phase 00 as read-only discovery first.
4. Update technology choices and actual commands to match the existing repo.
5. Approve and execute one phase at a time.
6. Convert recurring failures into automated tests or mechanical guardrails, not just more prose.
7. Update statuses only with observed evidence.

## Important Product Constraints
- Initial target is Windows, but hardware support must be measured.
- Core functions must work without GPU or local LLM.
- Use React JavaScript + CSS, Python/FastAPI, Playwright, SQLite and optional Ollama only where compatible with the actual repo.
- Automate only sources and methods that permit the intended access. Do not bypass access controls.
- Candidate scores require evidence and human review.

## References
See `docs/REFERENCES.md` for official/current documentation used as starting points.
