---
id: domain-model
title: Domain Model
kind: concept
depends_on:
  - architecture
  - error-policy
related:
  - storage-contracts
  - testing-playbook
  - glossary
code_refs:
  - src/portfotrack/domain/asset
  - src/portfotrack/domain/target_allocation
  - src/portfotrack/domain/snapshot
  - src/portfotrack/domain/trend
  - src/portfotrack/domain/optional_bet
tests:
  - tests/domain
  - tests/domain/snapshot
updates_when:
  - domain invariants change
  - asset allocation semantics change
  - snapshot semantics change
  - optional bet semantics change
  - trend semantics change
---

# Domain Model

The domain layer represents portfolio concepts without I/O or web concerns.
Domain objects should stay small, explicit, and testable.

## Asset

An asset is an asset-class-level concept, not a tradable security.
PortfoTrack tracks asset classes and KRW amounts, not prices or automated
trading signals.

Primary code:

- `src/portfotrack/domain/asset/asset.py`
- `src/portfotrack/domain/asset/factory.py`

## Target Allocation

A target allocation maps assets to a target ratio and an absolute tolerance
range. Tolerance bounds are allocation ratios, not relative deviations.

Important invariants:

- Target ratios are between `0.0` and `1.0`.
- Tolerance lower and upper bounds are between `0.0` and `1.0`.
- Tolerance lower bound cannot exceed the upper bound.
- Total ratio validation is explicit and should be called once the target is complete.
- Duplicate assets are rejected.

Primary code:

- `src/portfotrack/domain/target_allocation/target.py`
- `src/portfotrack/domain/target_allocation/errors.py`

## Snapshot

A snapshot records amount-based holdings for a date and currency.
Amounts are integer KRW values in normal application use.

Primary code:

- `src/portfotrack/domain/snapshot/snapshot.py`

## Trend

Trend concepts compare snapshots over time.
They should remain descriptive and rule-based.
Do not introduce prediction, forecasting, or investment advice.

Primary code:

- `src/portfotrack/domain/trend/trend.py`
- `src/portfotrack/services/trend_analysis.py`

## Optional Bet

Optional bets represent explicitly separated non-core allocation ideas.
They should not blur the target allocation model or become security-level
price tracking.

Primary code:

- `src/portfotrack/domain/optional_bet/optional_bet.py`
- `src/portfotrack/services/optional_bet_services.py`
- `src/portfotrack/services/optional_bet_trend_analysis.py`

## Links

Depends on:

- [Architecture](architecture.md)
- [Error Policy](error-policy.md)

Related:

- [Storage Contracts](storage-contracts.md)
- [Testing Playbook](testing-playbook.md)
- [Glossary](glossary.md)
