# Project Goals and Success Conditions

## Product Outcome
Deliver a laptop-friendly desktop assistant that helps HR users find and review role-relevant candidates using permitted sources. It should preserve evidence and explain why a candidate matches a JD. It is decision support, not an autonomous hiring decision-maker.

## Desired Outcomes
1. HR can enter a JD and inspect/edit structured role criteria.
2. The application creates a search plan and uses configured, approved sources.
3. The agent observes, plans, acts, and verifies rather than blindly replaying clicks.
4. Results are normalized, deduplicated, and linked to their source and retrieval time.
5. Matching is explainable and distinguishes fit from evidence completeness.
6. Users can pause, resume, cancel, review, correct, delete, and export results.
7. Core workflow and storage remain usable without a GPU or local LLM.
8. Coding agents can work in bounded phases with automated verification and clear evidence.

## Scope for the Initial MVP
- Single-user desktop app; Windows is the first target platform.
- React JavaScript UI, Python backend, SQLite persistence, Playwright where the source permits browser automation, and optional local LLM provider.
- Approved source adapter interface; source choice and authorization are explicit release gates.
- JD parsing, query planning, permitted collection, normalization, deduplication, evidence-based scoring, review and CSV export.
- Hardware/runtime diagnostics, robust cancellation, bounded retries, and local logs.

## Non-Goals
- Circumventing CAPTCHAs, access controls, authentication restrictions, rate limits, or website terms.
- Unauthorized LinkedIn scraping or automation. LinkedIn-specific collection must use a permitted official/licensed route or remain human-operated.
- Sending messages to candidates or automating outreach in the MVP.
- Automatically rejecting or selecting candidates without HR review.
- Inferring protected characteristics or suitability from unrelated personal data.
- Requiring a discrete GPU, cloud LLM, or a large local model for core features.
- Claiming compatibility with every laptop before defining a support matrix and measuring representative systems.

## Quality Attributes
- **Correctness:** structured contracts, evidence provenance, deduplication and reproducible scoring.
- **Reliability:** bounded loops, cancellation, checkpointing, safe recovery and database integrity.
- **Portability:** configurable paths, capability detection, no hidden developer-machine assumptions.
- **Responsiveness:** background runs; UI remains usable under CPU/RAM pressure.
- **Privacy:** data local by default, minimal collection, visible retention/deletion controls.
- **Security:** untrusted input isolation, secrets protection, loopback API by default, no external actions without authorization.
- **Maintainability:** source adapters and model providers behind interfaces; concise docs and enforced checks.

## Success Conditions
- A user can complete a small end-to-end run using a permitted fixture/source and inspect the resulting evidence.
- The run can be paused/cancelled without leaving orphan browser processes or corrupting data.
- Candidate match reasons link to evidence and the rubric version.
- Missing fields remain unknown rather than being fabricated.
- Removing Ollama or having no supported GPU does not prevent core workflows.
- Tests exercise key state transitions, boundary validation, source contracts, matching, storage and export.
- Tested hardware support and known performance limits are documented before release.
- The release is not enabled for a source until policy and permission requirements are reviewed.

## Explicit Unknowns (Do Not Guess)
- Final permitted search/data sources and their automation permissions.
- Exact minimum supported RAM/CPU and acceptable latency target.
- Final model(s), quantization and model licensing review.
- Final installer/packaging strategy and supported Windows versions.
- Required candidate-data retention period and jurisdiction-specific compliance requirements.
