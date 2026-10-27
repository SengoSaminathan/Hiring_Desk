# Testing and Evaluation Strategy

## Unit Tests

Cover JD parsing, requirement normalization, query validation, URL
canonicalization, candidate normalization, deduplication, scoring,
evidence coverage, state transitions, retries, cancellation, SQLite
repository functions, and CSV escaping.

## Contract Tests

-   Validate API schemas.
-   Validate every source adapter against its common contract.
-   Validate LLM output against JSON/Pydantic schemas.
-   Reject or safely retry invalid model output.
-   Verify missing AI provider does not break core services.

## Integration Tests

-   API -\> run controller -\> fake source -\> persistence.
-   Cancellation -\> browser/task shutdown.
-   Extraction -\> deduplication -\> scoring -\> review.
-   Database migration from the previous supported schema.
-   Frontend progress UI against a deterministic fake backend.

## Browser Tests

Use local fixtures or a site that explicitly permits automation. Test
slow loading, timeouts, empty results, missing fields, duplicate links,
unexpected navigation, access-denied states, human-intervention pause,
and cancellation. Never test bypassing source controls.

## Hardware and Performance Tests

Benchmark representative profiles: - Low-memory CPU-only laptop. -
Standard 8--16 GB laptop. - Laptop with supported discrete GPU.

Record idle/peak RAM, model load time, inference latency, browser
memory, candidate processing time, disk use, and UI responsiveness. Do
not publish minimum specifications until measured.

## Evaluation Dataset

Use synthetic profiles and permitted sample data. Include exact/partial
matches, missing or conflicting data, duplicate URLs, title aliases, and
irrelevant results. Do not commit real candidate personal data.

## Matching Metrics

-   Precision at K on a manually reviewed set.
-   Recall where a defensible labeled set exists.
-   Agreement with human reviewers.
-   Evidence citation correctness.
-   False positives on irrelevant profiles.
-   Uncertainty/evidence-coverage quality.
-   Repeatability across model versions.

A numeric score is a decision-support signal, not a validated prediction
of job performance.

## Release Gates

-   Unit and integration tests pass.
-   Schemas validate.
-   Cancellation and shutdown work.
-   Database integrity survives simulated failures.
-   No known secrets in repository.
-   Basic prompt-injection tests pass.
-   Source-policy review completed for enabled adapters.
-   Known limitations and hardware benchmark results documented.


## Requirement Traceability
Use `docs/REQUIREMENTS_TRACEABILITY.md` to link each functional/non-functional requirement to one or more tests or manual verification procedures. Update the matrix when requirements or contracts change. Mark unimplemented items as planned; never populate it with guessed results.

## Mechanical Guardrails
Use `docs/ENFORCEMENT_AND_DRIFT.md` to track which principles are merely documented versus actually enforced by scripts or CI. When a failure recurs, prefer a regression test or deterministic check over another prose-only warning.
