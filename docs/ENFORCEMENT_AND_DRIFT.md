# Enforcement and Drift Control

Harness engineering works best when durable rules are checked mechanically wherever possible. This document defines what should become executable safeguards as the repository is built. Do not claim a safeguard exists until a script or CI check actually implements it.

## Enforcement Map

| Invariant | Preferred enforcement | Status in starter pack |
|---|---|---|
| Python code follows formatting/lint rules | locked formatter/linter + CI | Planned; choose after repository discovery |
| Frontend has valid lint/build/test commands | package scripts + CI | Planned |
| API boundaries validate payloads | Pydantic/schema contract tests | Design requirement |
| No secrets committed | `.gitignore` + secret scanner + pre-commit/CI | Planned |
| No real candidate data in test fixtures | synthetic fixture policy + scan/review | Design requirement |
| Source adapters have policy metadata | required adapter contract + test | Design requirement |
| Browser actions are bounded/cancellable | state-machine tests and integration tests | Design requirement |
| No unapproved source automation | release checklist + policy review | Manual gate required |
| Match score always carries rubric version/evidence | DB constraints/schema tests | Design requirement |
| Core workflow survives missing local AI | tests with provider disabled | Design requirement |
| Build docs do not claim unsupported success | build-log checklist/review | Manual gate initially |
| Release claims match tested hardware | benchmark report required | Manual gate initially |

## Build the Guardrails in the Right Order
1. Phase 00: discover current repository and tools; do not guess commands or framework versions.
2. Phase 01: establish deterministic formatting, linting, schema validation and basic tests based on the actual stack.
3. Phase 02 onward: add contract and integration checks with every new boundary.
4. Before release: enable CI, dependency/security checks, secret scanning, installer smoke tests and a hardware results artifact.

## CI Minimum Gate
When the repository has an established package layout, CI should run on relevant changes and include:
- install from lockfiles in a clean environment;
- formatter/linter;
- backend unit tests;
- frontend tests/build;
- API/schema/contract tests;
- dependency and secret checks;
- integration tests that do not require live third-party sites;
- build/package smoke test when feasible.

Live browser scraping against third-party sources must not be a normal CI dependency. Use fixture pages or a permitted test source.

## Drift Control
At phase close or after recurring agent mistakes:
- identify whether the problem is missing documentation, missing tests, weak architecture, or missing automation;
- prefer a mechanical check when a rule can be evaluated deterministically;
- add a regression test when a concrete bug recurs;
- remove or revise stale duplicated instructions;
- update the build log with observed evidence;
- avoid adding broad instructions for a one-off issue unless it reveals a reusable failure mode.

## Honest Status Labels
Use only `Not started`, `In progress`, `Blocked`, or `Complete` for phase status. A passing focused test is not enough to mark a whole phase complete unless all phase acceptance criteria are met.
