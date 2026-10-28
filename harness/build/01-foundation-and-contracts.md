# Phase 01 — Foundation and Contracts

## Status
Not started. Requires Phase 00 review and approval.

## Purpose
Set up the smallest runnable application foundation and the contracts that prevent components from drifting.

## Scope
- Establish the approved project layout without replacing useful existing files.
- Define validated schemas for JD criteria, source results, candidate records, evidence, match results, run states, and progress events.
- Implement configuration validation and safe defaults.
- Define the run state machine and valid transitions.
- Define source-adapter and AI-provider interfaces without selecting an unapproved live source.
- Establish formatting, lint, unit-test, and smoke-test commands based on the actual chosen stack.
- Confirm the UI or a minimal health endpoint can run, as appropriate to the approved repository.

## Non-Goals
- No live third-party collection.
- No model-specific business logic or scoring implementation beyond contracts.
- No packaging or full visual UI.

## Acceptance Criteria
- [ ] Clean setup instructions work in a fresh environment.
- [ ] Core data contracts reject invalid/missing required fields.
- [ ] Run state transitions are tested, including invalid transitions.
- [ ] Optional AI configuration can be absent without startup failure.
- [ ] Lint/format/test/smoke commands are documented and actually run.
- [ ] No secrets, live candidate data, model files, or browser profiles are committed.

## Verification
Run exact repository setup, unit/schema tests, lint/format, and smoke commands. Record command output/status in the build log.
