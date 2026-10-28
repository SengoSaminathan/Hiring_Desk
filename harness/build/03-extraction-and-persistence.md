# Phase 03 — Extraction, Deduplication, Persistence, and Export

## Status
Not started. Requires validated source-result contracts.

## Purpose
Turn permitted result evidence into durable, inspectable candidate records.

## Scope
- Normalize names, titles, organizations, skills, locations and URLs only when supported by source evidence.
- Preserve source URL, retrieval timestamp and field-level evidence.
- Deduplicate canonical profile URLs and define safe secondary signals for cases without canonical URLs.
- Implement SQLite schema, transactions, migrations, indexes and repository layer.
- Support review/update/delete, backups where applicable, and CSV export.
- Keep candidate data local by default and make retention/deletion behavior explicit.

## Non-Goals
- Do not guess missing skills, years of experience or employment facts.
- Do not persist full page HTML or raw session cookies by default.
- Do not build the scoring model or polished UI yet.

## Acceptance Criteria
- [ ] Repeated results across queries do not create duplicate candidates under defined rules.
- [ ] Every derived field retains provenance or is explicitly marked unavailable/derived.
- [ ] Unknown values remain unknown.
- [ ] Migrations and writes preserve database integrity.
- [ ] Delete/correction/export behavior is tested.
- [ ] CSV is safe against malformed text and spreadsheet formula injection.
- [ ] Tests use synthetic candidate data only.

## Verification
Run normalization, deduplication, repository, migration, deletion and export tests. Inspect test fixtures for real personal data.
