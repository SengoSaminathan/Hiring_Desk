# Phase 07 — Packaging and Handoff

## Status
Not started. Requires a tested end-to-end build.

## Purpose
Deliver a reproducible installable build and an honest user-facing setup/support guide.

## Scope
- Select packaging approach based on measured startup, update and browser-runtime behavior.
- Create clean-machine install, launch, update, rollback and uninstall procedures.
- Define how optional Ollama/models are detected and installed without silent downloads.
- Keep user database/config outside disposable application install directories.
- Add diagnostics bundle with secrets/PII redaction.
- Record license/attribution notices for dependencies and models.
- Create release checklist and versioned known-issues document.

## Non-Goals
- Do not publish/distribute/sign/deploy without explicit authorization.
- Do not claim compatibility with untested platforms.

## Acceptance Criteria
- [ ] Clean-machine installation and first launch succeed on tested target OS.
- [ ] Upgrade preserves user data; uninstall behavior is documented and tested.
- [ ] Model/runtime missing scenarios show actionable setup choices.
- [ ] Database/config path and backup/restore guidance are clear.
- [ ] Dependency/model notices and release notes are included.
- [ ] Release checklist includes test results and hardware validation evidence.

## Verification
Run build/package smoke tests, install/upgrade/uninstall tests, launch/offline scenarios, secret scan, and final release review. Do not publish without separate explicit approval.
