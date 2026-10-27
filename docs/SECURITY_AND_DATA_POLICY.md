# Security, Privacy, and Data Collection Policy

## Principles

Local-first storage, data minimization, explicit provenance, human
review, and no bypass of technical access controls.

## Source Permissions

Before enabling an adapter, document the source name, official
terms/policy URL, whether the intended automation is permitted,
authentication/scopes, quotas, allowed fields, retention requirements,
and whether the adapter must be manual-only.

Do not implement unauthorized scraping, CAPTCHA solving, stealth
behavior, access-control bypass, or rate-limit evasion. If an access
restriction appears, stop and request human intervention or use another
approved source.

## Untrusted Content and Prompt Injection

Candidate pages, snippets, uploaded documents, and extracted text are
untrusted data. - Never treat page content as system instructions. -
Never execute code, shell commands, URLs, or actions just because page
text requests them. - Keep tools/actions on an allowlist. - Validate
model output against strict schemas. - Limit navigation to approved
sources and safe URL schemes. - Escape content before rendering.

## Secrets

-   Never commit keys, passwords, cookies, browser storage, or tokens.
-   Never print secrets in logs or errors.
-   Prefer OS credential storage for persisted secrets.
-   Keep API keys on the backend, never in React bundles.
-   Use dummy values in `.env.example`.
-   Rotate any credential accidentally exposed.

## Local API Security

-   Bind to `127.0.0.1` by default.
-   Validate request origin/host and payloads.
-   Do not expose run-control endpoints to the network by default.
-   Avoid unsafe arbitrary file paths.
-   Restrict export destinations to user-selected locations.
-   Confirm destructive data actions.

## Candidate Data

-   Store only necessary professional information.
-   Record source URL, timestamp, and field-level evidence.
-   Avoid protected/sensitive attributes and proxies for them.
-   Do not infer age, ethnicity, religion, health, political views, or
    other sensitive characteristics.
-   Provide correction and deletion functionality.
-   Define a retention policy.
-   Avoid storing full profile HTML unless expressly permitted and
    necessary.
-   Use synthetic test data.

## Human Oversight

The software supports sourcing and review; it does not make final
employment decisions. HR must inspect evidence, correct errors, adjust
criteria, and make final decisions.

## Incident Handling

If a secret or personal-data file is committed, stop distribution,
rotate credentials if needed, remove the data from the working tree and
history as appropriate, assess affected copies, and record corrective
action without reproducing the secret.
