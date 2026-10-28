# Phase 02 — Source Adapter and Browser Agent

## Status
Not started. Requires an approved source/method or use of a local fixture.

## Purpose
Implement a bounded Observe → Plan → Act → Verify loop that can be tested without relying on a live third-party website.

## Scope
- Implement the common source adapter contract.
- Add a local fixture or approved source adapter first.
- Add Playwright controller with page-state observation, locator-based actions, timeout, bounded retry and cleanup.
- Persist run state and progress events.
- Support pause-for-user, resume, cancellation and safe shutdown.
- Classify empty results, timeouts, network failures, login/consent barriers, CAPTCHA and access-denied states.
- Add loop detection and maximum-step/page/runtime limits.

## Non-Goals
- Do not evade access restrictions, disguise automation, solve CAPTCHAs, or automate a source without permission.
- Do not implement candidate scoring or full desktop UI yet.

## Acceptance Criteria
- [ ] Fixture/approved source can be searched and results observed reproducibly.
- [ ] Every meaningful action is verified against expected state.
- [ ] Failure and timeout paths terminate safely.
- [ ] Cancellation cleans up browser tasks/processes.
- [ ] Repeated actions/queries are bounded.
- [ ] Source policy and allowed fields are documented before enabling a live adapter.
- [ ] Integration tests do not depend on a live third-party website.

## Verification
Run adapter contract tests, fixture-browser integration tests, cancellation/timeout tests, and a source-policy review for any live adapter.
