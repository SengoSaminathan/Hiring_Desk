# Phase 04 — Optional Local AI and Evidence-Based Matching

## Status
Not started. Requires stable data/evidence contracts.

## Purpose
Add optional local-model assistance without making hardware acceleration or model availability a hard prerequisite for the product.

## Scope
- Implement the AI provider interface and optional Ollama adapter if approved.
- Add capability checks for runtime/model availability and useful error messages.
- Keep rules-based JD parsing and matching fallback available.
- Use schema-constrained outputs and bounded context/token sizes.
- Implement transparent configurable scoring and store rubric/model versions.
- Separate job eligibility rules, match score, and evidence completeness.
- Benchmark candidate models on representative laptops before making default-model claims.

## Non-Goals
- Do not require cloud model credentials.
- Do not download large model weights silently or at install time.
- Do not treat model-generated assertions as source evidence.
- Do not automatically reject candidates or infer protected characteristics.

## Acceptance Criteria
- [ ] Core workflow functions with AI provider disabled.
- [ ] Invalid/timeout model outputs fail safely or fall back predictably.
- [ ] Match explanation links to stored evidence.
- [ ] Missing evidence is not treated as confirmed mismatch.
- [ ] Rubric/model version is saved with each match.
- [ ] Evaluation fixtures test partial matches, irrelevant results, conflicts and missing data.
- [ ] Model download requires consent and disk-space checks.

## Verification
Run provider contract tests, fallback tests, known-answer scoring tests, prompt-injection fixtures and small-device latency/memory benchmarks.
