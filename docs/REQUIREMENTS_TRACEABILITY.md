# Requirements Traceability Matrix

This matrix connects product intent to implementation evidence. Update it when requirements or tests change. “Planned” does not mean implemented.

| ID | Requirement | Primary owner | Required evidence |
|---|---|---|---|
| FR-01 | Create/edit a JD and structured role criteria | UI + JD service | UI test; schema test; persistence test |
| FR-02 | Generate search plan and queries | query planner | deterministic fixtures; schema validation; quality evaluation |
| FR-03 | Execute only permitted source actions | source adapter + policy record | adapter contract tests; source-policy review |
| FR-04 | Observe/act/verify browser state | browser controller | fixture browser integration tests for success and failure paths |
| FR-05 | Extract and normalize candidate fields with provenance | extraction service | field-level normalization tests; evidence provenance tests |
| FR-06 | Deduplicate candidates across queries/runs | normalization/storage | canonical URL and duplicate fixture tests |
| FR-07 | Score candidates transparently | matching service | known-answer rubric tests; missing-evidence tests |
| FR-08 | Review/correct/delete/export records | UI + API + persistence | integration tests; export tests; deletion tests |
| FR-09 | Pause/resume/cancel runs safely | run controller | state transition tests; cancellation/shutdown integration tests |
| FR-10 | Persist history and recover after interruption | persistence + run controller | restart/recovery tests; migration/integrity tests |
| NFR-01 | Core path works without GPU/local LLM | capability layer + fallback | test with model provider unavailable; CPU-only benchmark |
| NFR-02 | UI remains responsive during collection | frontend + task manager | responsiveness test/measurement on constrained device |
| NFR-03 | Local API is not exposed on LAN by default | backend config | startup/config test and security check |
| NFR-04 | Page/model content cannot issue tools or commands | agent boundary | prompt-injection test fixtures; tool allowlist tests |
| NFR-05 | Candidate fields have source and retrieval time | data model | schema and persistence tests |
| NFR-06 | Supported hardware claims are evidence-based | release process | hardware benchmark report and documented limits |
| NFR-07 | Secrets and candidate data are excluded from git | repo hygiene + CI | secret scan, ignore rules, review checklist |
| NFR-08 | UI has accessible keyboard and error states | frontend | accessibility checks and manual review |
| NFR-09 | Installer can install, upgrade, and uninstall safely | packaging | clean-machine install/upgrade/uninstall smoke test |

## Rules
- Every implemented FR/NFR must link to at least one test or explicit manual verification procedure before release.
- If a requirement is not yet implemented, leave its evidence empty or mark it planned; never fabricate evidence.
- When implementation changes a contract, update the owning requirement and tests in the same change.
- Risk-sensitive requirements (source policy, cancellation, data deletion, secrets, local API exposure) require explicit review, not only unit tests.
