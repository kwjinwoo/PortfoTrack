---
id: adr-0003-asset-class-level-tracking
title: "ADR-0003: Asset-Class-Level Tracking"
kind: decision
status: accepted
depends_on: []
related:
  - domain-model
  - adr-0004-rule-based-guidance-only
code_refs:
  - AGENTS.md
  - src/portfotrack/domain/asset
  - src/portfotrack/domain/snapshot
tests:
  - tests/domain
updates_when:
  - portfolio tracking granularity is reconsidered
  - this decision is superseded or deprecated
---

# ADR-0003: Asset-Class-Level Tracking

## Status

Accepted.

## Context

The product compares portfolio allocation against asset-class targets. Tracking
individual securities or prices would create a different data and analysis
model.

## Decision

PortfoTrack tracks asset classes and KRW amounts. It does not track individual
security prices.

## Consequences

- Domain identifiers represent allocation categories rather than tradable
  instruments.
- Snapshots store amount-based holdings without market-data integration.
- Security lookup, quote ingestion, and price history remain outside scope.

## Links

Related:

- [ADR Index](README.md)
- [Domain Model](../domain/overview.md)
- [ADR-0004: Rule-Based Guidance Only](0004-rule-based-guidance-only.md)
