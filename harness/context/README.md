# Harness Context Files

Use this folder for phase-specific discoveries that materially affect implementation. Do not create empty context files for phases that have not started.

## Ownership
A context file records facts discovered during work, decisions actually made, constraints, trade-offs, and unresolved questions. It does not replace `GOALS.md`, `PLANS.md`, the phase acceptance criteria, or the build log.

## Suggested Naming
`phase-<number>-<short-topic>.md`

## Template
```markdown
# Phase <N> Context — <Topic>

## Observed Facts
- Include evidence path, command, version, or relevant source.

## Decisions Made
- Decision, reason, and owner/date if applicable.

## Constraints and Risks
- Technical, policy, data, performance, or compatibility limits.

## Unresolved Questions
- Clearly mark what has not been decided.

## Impact on Implementation
- Link to the code/docs/tests affected.

## Revalidation Triggers
- What change would make these facts stale?
```

Avoid copying large logs or duplicating plans. Record durable discoveries, not every temporary thought.
