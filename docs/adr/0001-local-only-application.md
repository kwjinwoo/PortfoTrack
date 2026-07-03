---
id: adr-0001-local-only-application
title: "ADR-0001: Local-Only Application"
kind: decision
status: accepted
depends_on: []
related:
  - architecture
  - adr-0002-file-based-persistence
code_refs:
  - AGENTS.md
  - src/portfotrack/web/app.py
tests:
  - tests/web
updates_when:
  - the local-only product boundary is reconsidered
  - this decision is superseded or deprecated
---

# ADR-0001: Local-Only Application

## Status

Accepted.

## Context

PortfoTrack is a personal portfolio tracker intended to run on one local
machine. Adding hosted services would expand deployment, privacy, failure, and
operational concerns beyond that purpose.

## Decision

PortfoTrack runs locally and does not depend on network services, cloud APIs,
or hosted databases.

## Consequences

- Core workflows remain available without internet access.
- Backend and frontend dependencies must not require runtime network calls.
- Features that require accounts, synchronization, or hosted infrastructure
  are outside the product boundary unless a later ADR supersedes this one.

## Links

Related:

- [ADR Index](README.md)
- [ADR-0002: File-Based Persistence](0002-file-based-persistence.md)
- [Architecture](../foundation/architecture.md)
