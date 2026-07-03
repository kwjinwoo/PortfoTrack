---
id: error-book
title: Error Book
kind: correction-log
depends_on:
  - adr
related:
  - architecture
  - error-policy
  - testing-playbook
  - storage-contracts
  - web-routes
code_refs:
  - AGENTS.md
  - src/portfotrack/web/static/css/styles.css
  - src/portfotrack/web/static/js
tests: []
updates_when:
  - agents repeatedly make the same mistake
  - a code review identifies a recurring documentation gap
  - a project rule needs a concrete correction example
---

# Error Book

This node records recurring mistakes that coding agents should avoid.
Add entries when the same correction would otherwise need to be repeated.

## Do Not Cross Layer Boundaries

Do not put file access, Flask route logic, or JSON store behavior in domain
objects. Use the architecture map before editing.

Related nodes:

- [Architecture](../foundation/architecture.md)
- [Domain Model](../domain/overview.md)
- [Storage Contracts](../storage/contracts.md)
- [Web Routes](../web/routes.md)

## Do Not Add Untested Behavior

Production behavior changes require corresponding tests unless explicitly
asked to skip tests.

Related nodes:

- [Testing Playbook](../policies/testing-playbook.md)

## Do Not Overpower Dynamic UI State

The web UI uses initially hidden elements that JavaScript reveals after local
API calls. Do not add `!important` to dynamic visibility classes such as
`is-hidden`; it can prevent scripted panels from appearing even when the API
call and rendering logic succeed.

Example: allocation report generation reveals `#report-result-card` from
`reports-ui.js`. If `.is-hidden` uses `display: none !important`, the report
button appears to do nothing because the card remains visually hidden.

Related nodes:

- [Web Routes](../web/routes.md)
- [Testing Playbook](../policies/testing-playbook.md)

## Do Not Convert Invariants Into User Errors

Broken trusted internal structures should usually remain native exceptions.
Do not hide programmer errors behind application error classes.

Related nodes:

- [Error Policy](../policies/error-policy.md)
- [Storage Contracts](../storage/contracts.md)

## Do Not Add Network or Database Dependencies

The project is local-only and file-based.
Do not add network calls, cloud services, databases, ORMs, or external storage
engines.

Related nodes:

- [ADR-0001: Local-Only Application](../adr/0001-local-only-application.md)
- [ADR-0002: File-Based Persistence](../adr/0002-file-based-persistence.md)
- [Architecture](../foundation/architecture.md)

## Do Not Turn Reports Into Advice Engines

Keep portfolio guidance minimal and rule-based.
Do not add forecasting, optimization-heavy strategy, automated trading signals,
or personalized financial advice.

Related nodes:

- [ADR-0004: Rule-Based Guidance Only](../adr/0004-rule-based-guidance-only.md)
- [Domain Model](../domain/overview.md)
