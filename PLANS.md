# Build Plan and Phase Order

This plan describes intended phases, not completed work. Do not mark a phase complete without evidence in `harness/build-log.md`. Work on one phase at a time and stop at its handoff point.

| Phase | File | Outcome | Status |
|---|---|---|---|
| 00 | `harness/build/00-repository-discovery.md` | Inspect repository, freeze conventions, define actual commands and unresolved decisions | Not started |
| 01 | `harness/build/01-foundation-and-contracts.md` | Establish project skeleton, schemas, state machine, config and smoke tests | Not started |
| 02 | `harness/build/02-source-adapter-and-agent.md` | Build an agent loop with a permitted fixture source and safe cancellation | Not started |
| 03 | `harness/build/03-extraction-and-persistence.md` | Normalize, deduplicate, persist records/evidence and export | Not started |
| 04 | `harness/build/04-local-ai-and-matching.md` | Add optional model provider, deterministic fallback and evidence-based score | Not started |
| 05 | `harness/build/05-review-ui-and-integration.md` | Connect React interface to backend and present run/candidate state | Not started |
| 06 | `harness/build/06-hardening-and-hardware-validation.md` | Security, reliability, performance and compatibility evidence | Not started |
| 07 | `harness/build/07-packaging-and-handoff.md` | Installer/build strategy, setup guide, release checklist and handoff | Not started |

## Phase Rules
- Phase 00 is read-only discovery until the owner approves repository writes or a scaffold plan.
- Do not start a later phase because the current phase is easy or mostly complete.
- If a phase depends on an unresolved source permission, model license, OS support, or data-retention decision, record the blocker; use a fixture where possible.
- The phase document is the scope authority. This roadmap does not override a more recent explicit owner decision.
- Update phase statuses only when there is observed evidence. Keep future phases `Not started` until work begins.
- Changes to scope or phase order must be documented in the relevant phase and decision log before implementation.
