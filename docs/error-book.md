---
id: error-book
title: Error Book
kind: correction-log
depends_on:
  - decisions
related:
  - architecture
  - error-policy
  - testing-playbook
  - storage-contracts
code_refs:
  - AGENTS.md
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

- [Architecture](architecture.md)
- [Domain Model](domain-model.md)
- [Storage Contracts](storage-contracts.md)
- [Web Routes](web-routes.md)

## Do Not Add Untested Behavior

Production behavior changes require corresponding tests unless explicitly
asked to skip tests.

Related nodes:

- [Testing Playbook](testing-playbook.md)

## Do Not Convert Invariants Into User Errors

Broken trusted internal structures should usually remain native exceptions.
Do not hide programmer errors behind application error classes.

Related nodes:

- [Error Policy](error-policy.md)
- [Storage Contracts](storage-contracts.md)

## Do Not Add Network or Database Dependencies

The project is local-only and file-based.
Do not add network calls, cloud services, databases, ORMs, or external storage
engines.

Related nodes:

- [Decisions](decisions.md)
- [Architecture](architecture.md)

## Do Not Turn Reports Into Advice Engines

Keep portfolio guidance minimal and rule-based.
Do not add forecasting, optimization-heavy strategy, automated trading signals,
or personalized financial advice.

Related nodes:

- [Decisions](decisions.md)
- [Domain Model](domain-model.md)
