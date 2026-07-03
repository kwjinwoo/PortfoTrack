---
id: adr-0002-file-based-persistence
title: "ADR-0002: File-Based Persistence"
kind: decision
status: accepted
depends_on:
  - adr-0001-local-only-application
related:
  - storage-contracts
  - adr-0005-explicit-over-automation
code_refs:
  - AGENTS.md
  - src/portfotrack/storage
tests:
  - tests/storage
updates_when:
  - the persistence engine boundary is reconsidered
  - this decision is superseded or deprecated
---

# ADR-0002: File-Based Persistence

## Status

Accepted.

## Context

The application needs durable local state without introducing infrastructure
that conflicts with its single-machine scope.

## Decision

Persistence uses local JSON or CSV files. Databases, ORMs, cloud stores, and
external storage engines are not used.

## Consequences

- Stored data remains inspectable and portable with ordinary local tools.
- Serialization and file stores own explicit persistence contracts.
- Schema evolution must stay intentional; database-style implicit migrations
  are not available.

## Links

Depends on:

- [ADR-0001: Local-Only Application](0001-local-only-application.md)

Related:

- [ADR Index](README.md)
- [Storage Contracts](../storage/contracts.md)
- [ADR-0005: Explicit Over Automation](0005-explicit-over-automation.md)
