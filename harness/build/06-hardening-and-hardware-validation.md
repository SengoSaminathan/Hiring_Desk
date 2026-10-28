# Phase 06 — Hardening, Security, and Hardware Validation

## Status
Not started. Requires the end-to-end MVP.

## Purpose
Turn assumptions into measured limits and test high-risk failure boundaries.

## Scope
- Test representative low-memory CPU-only, standard laptop, and optional discrete-GPU profiles.
- Measure idle/peak RAM, browser memory, model load time, inference latency, candidates/minute, disk use and UI responsiveness.
- Test low disk space, no internet, provider unavailable, model missing, interrupted run, cancellation, corrupt/old database and export failures.
- Review prompt injection, untrusted URLs, local API exposure, secret handling, data minimization, deletion/retention and adapter source policy.
- Add mechanical guardrails for repeated defects.
- Document supported OS and known limitations from evidence.

## Non-Goals
- Do not claim support for every laptop based on one machine.
- Do not benchmark by bypassing third-party access controls.

## Acceptance Criteria
- [ ] No-GPU/no-LLM fallback is demonstrated.
- [ ] Hardware matrix contains actual measured results and test environment details.
- [ ] Cancellation/recovery tests pass.
- [ ] Source-policy review is complete for every enabled live adapter.
- [ ] Security issues have severity, owners/next steps and documented disposition.
- [ ] Compatibility statements are limited to tested configurations.

## Verification
Run full unit/integration/regression tests, security checks, dependency scan, resource benchmarks, and manual review of the documented risk areas.
