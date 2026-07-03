---
id: adr-0005-explicit-over-automation
title: "ADR-0005: Explicit Over Automation"
kind: decision
status: accepted
depends_on: []
related:
  - storage-contracts
  - error-policy
code_refs:
  - AGENTS.md
  - src/portfotrack/storage
tests:
  - tests/storage
updates_when:
  - implicit mutation or migration policy is reconsidered
  - this decision is superseded or deprecated
---

# ADR-0005: Explicit Over Automation

## Status

Accepted.

## Context

Hidden mutation and automatic recovery can make a local file-based application
difficult to reason about and can obscure malformed or outdated data.

## Decision

Prefer explicit behavior over hidden side effects. Avoid implicit overwrites,
automatic migrations, and surprising persistence behavior.

## Consequences

- Callers express overwrite and mutation intent directly.
- Persistence failures remain visible at the appropriate error boundary.
- Data-format changes require an intentional compatibility or migration
  decision rather than silent conversion.

## Links

Related:

- [ADR Index](README.md)
- [Storage Contracts](../storage/contracts.md)
- [Error Policy](../policies/error-policy.md)
