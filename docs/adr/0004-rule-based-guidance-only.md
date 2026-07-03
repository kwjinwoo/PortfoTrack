---
id: adr-0004-rule-based-guidance-only
title: "ADR-0004: Rule-Based Guidance Only"
kind: decision
status: accepted
depends_on:
  - adr-0003-asset-class-level-tracking
related:
  - domain-model
code_refs:
  - AGENTS.md
  - src/portfotrack/services/allocation_report.py
  - src/portfotrack/services/trend_analysis.py
tests:
  - tests/services
updates_when:
  - portfolio guidance scope is reconsidered
  - this decision is superseded or deprecated
---

# ADR-0004: Rule-Based Guidance Only

## Status

Accepted.

## Context

PortfoTrack needs to describe allocation drift without becoming a forecasting,
automated trading, or personalized advice system.

## Decision

The application may provide minimal, deterministic, rule-based rebalancing
guidance. It does not provide optimization-heavy strategies, forecasting,
automated trading signals, or personalized financial advice.

## Consequences

- Reports and trends remain descriptive and explainable from stored inputs.
- New analysis must be expressible as explicit rules rather than predictive
  models.
- Trade execution and individualized recommendations remain outside scope.

## Links

Depends on:

- [ADR-0003: Asset-Class-Level Tracking](0003-asset-class-level-tracking.md)

Related:

- [ADR Index](README.md)
- [Domain Model](../domain/overview.md)
