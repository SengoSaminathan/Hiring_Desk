# Accessibility and UX Requirements

## Core Interaction Requirements
- Show the current run state, current step, source being used, and candidate counts without exposing secrets.
- Provide pause, resume, cancel, and human-intervention states that are visibly distinct.
- Prevent duplicate start actions and explain why a control is disabled.
- Keep the UI responsive while the agent, browser, or local model is busy.
- Preserve user-entered JD text when validation or network/source failures occur.
- Provide useful empty, loading, success, partial-success, permission-blocked, and error states.
- Do not show a confident candidate score without showing evidence coverage and criteria.

## Accessibility
- All primary actions must be keyboard accessible.
- Use visible focus indicators, semantic labels, and sensible tab order.
- Do not rely on color alone to communicate run status or match categories.
- Use sufficient contrast and support UI scaling.
- Announce important progress/status updates to assistive technology without flooding it with every low-level event.
- Tables need accessible column headers and a usable narrow-screen layout.

## User Control and Recovery
- Confirm destructive actions such as deleting a job or candidate record.
- Distinguish a retry from starting a new run.
- Explain when collection is blocked by a login, CAPTCHA, access policy, or source unavailability. Never instruct the agent to bypass the block.
- Provide a way to inspect evidence and correct extraction mistakes before export.
- Allow the user to review export contents and destination.

## Performance
- Run browser/model tasks off the UI thread.
- Prefer progressive updates and bounded logs over rendering every raw event.
- Limit retained screenshots/traces and provide explicit cleanup controls.
- On low-memory devices, reduce concurrent work and make AI features optional.
