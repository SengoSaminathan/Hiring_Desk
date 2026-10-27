# Source Adapter Permission Record — Template

Copy one record per source/method. Do not enable live automated collection until the relevant fields are completed and reviewed.

## Identity
- **Source name:** [name]
- **Official terms / API documentation:** [URL]
- **Adapter ID and version:** [identifier]
- **Record owner and review date:** [person/date]
- **Review status:** `Unreviewed` / `Approved for automation` / `Manual-only` / `Rejected` / `Re-review required`

## Intended Use
- **Business purpose:** [specific candidate-sourcing purpose]
- **Data fields needed:** [minimum fields]
- **Intended user group:** [single user / organization]
- **Regions/jurisdictions relevant to processing:** [known jurisdictions; identify unknowns]

## Access and Permission
- **Permitted access method:** [official API / licensed provider / explicitly permitted browser use / human-operated only]
- **Authorization basis:** [documented terms, contract, approval or official documentation]
- **Authentication/scopes required:** [list, or none]
- **Automation permitted for this intended use:** `Yes` / `No` / `Unclear`
- **Rate limits/quotas:** [documented details]
- **Prohibited actions:** [CAPTCHA bypass, unauthorized scraping, etc.]
- **Required human interaction:** [login, consent, review or other checkpoints]

## Data Handling
- **Source evidence retained:** [fields and reason]
- **Retrieval timestamp/source URL stored:** `Yes` / `No`
- **Retention/deletion requirements:** [known requirements; unknowns must remain open]
- **Redistribution/export restrictions:** [details]
- **Sensitive/protected data excluded:** [confirmation and exclusions]
- **Credential/session handling:** [secure storage approach; never record secrets here]

## Test and Enforcement
- **Fixture/contract tests:** [test paths]
- **Allowed domains and URL schemes:** [allowlist]
- **Rate/volume limits enforced by code:** [implementation path or `Not implemented`]
- **Blocked-state behavior:** [pause, stop, or manual-only]
- **Audit/log redaction:** [implementation path]

## Decision
- **Decision:** `Approved for automation` / `Manual-only` / `Rejected` / `Blocked pending clarification`
- **Evidence supporting the decision:** [links/contract or written approval]
- **Conditions and expiry/review date:** [details]
- **Approver:** [owner]

## Rules
- `Unclear` means automation is disabled until clarified.
- Do not infer permission from a public webpage, API key creation, or technical access alone.
- A source approval applies only to the documented method, fields, volume, and intended use.
- Any material change in source terms, contract, endpoints, automation behavior, data fields, or jurisdiction triggers re-review.
- Do not put credentials, cookies, private candidate data, or access tokens in this record.
