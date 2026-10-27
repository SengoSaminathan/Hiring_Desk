# Reusable Coding-Agent Prompts

Use these as task launchers. Replace bracketed fields. The agent must read the source-of-truth files before acting. Do not paste secrets into prompts.

## 1. Read-Only Repository Discovery
> Read `AGENTS.md`, `GOALS.md`, `PLANS.md`, the current build log, relevant phase docs, existing README/setup docs, manifests, tests, and git status. Do not change files. Report the actual repository layout, current stack, executable test/build commands, existing behavior, gaps against project goals, security/source-policy concerns, and unresolved questions. Distinguish observed facts from assumptions. Recommend the smallest next step and list exact files that would change if approved.

## 2. Prepare a Phase Plan
> Read the applicable instructions and `harness/build/[phase].md`. Perform a read-only preflight. Summarize scope, non-goals, files likely to change, dependencies, risks, acceptance criteria, and exact verification commands. Flag unresolved blockers. Do not begin implementation until the phase is explicitly selected/approved by the user.

## 3. Execute an Approved Phase
> Implement only the approved phase in `harness/build/[phase].md`. Preserve existing work. Before editing, confirm the exact scope and expected behavior. Follow a test-first loop where practical: reproduce/failing test, minimal fix/implementation, passing test, refactor, broader verification. Do not start the next phase. Do not perform commits, pushes, deploys, credential changes, or external writes. At the end, inspect the diff and report exact commands/results and unverified areas. Update phase-owned docs/build log only within the approved scope.

## 4. Investigate a Bug
> Reproduce the problem before editing. Trace the execution path and locate the smallest cause. Add or update a regression test that fails before the fix where practical. Avoid speculative rewrites and unrelated cleanup. Run the targeted test, then relevant integration checks. Report evidence and any remaining uncertainty.

## 5. Security/Source-Policy Review
> Read `docs/SECURITY_AND_DATA_POLICY.md` and the adapter's source-policy record. Review trust boundaries, prompt injection, URL handling, credential handling, local API exposure, PII minimization, retention, and compliance with source rules. Do not test bypassing access controls. Provide findings by severity with file/line references and concrete mitigations. Do not change code until the findings and proposed scope are summarized.

## 6. Verification and Evidence
> Read the current phase acceptance criteria. Run the smallest relevant test set first, then broader checks that are available. Capture exact commands, exit statuses, and concise outputs. Distinguish passed, failed, skipped, and not run. Never infer success from code inspection alone. Identify which acceptance criteria still lack evidence.

## 7. Code Review
> Review the diff as a skeptical maintainer. Prioritize correctness, regressions, security, data loss, source-policy violations, privacy, cancellation/recovery, performance on constrained laptops, and missing tests. Avoid style-only feedback unless it affects maintainability. Cite file/line locations, explain impact, and propose a fix. Do not edit files during the review pass.

## 8. Phase Handoff
> Compare the phase deliverables with its acceptance criteria. Inspect the final diff and test results. Update `harness/build-log.md` with observed facts only, including blockers and verification evidence. Mark the phase complete only if every required criterion is supported; otherwise mark it blocked/in progress and enumerate missing evidence. Summarize the safe next phase, but do not start it.

## 9. Harness Retrospective
> After a meaningful completed phase, inspect build log, test failures, review findings, and repeated agent mistakes. Recommend small durable improvements to instructions, automation, tests, or docs. Do not modify files during the retrospective. Classify each recommendation as: instruction, product/phase plan, test/eval, mechanical guard, or no action. Prioritize guardrails that can be enforced automatically over repeated prose warnings.
