---
id: decisions
title: Decisions
kind: decision-log
depends_on: []
related:
  - architecture
  - error-policy
  - storage-contracts
  - error-book
code_refs:
  - AGENTS.md
tests: []
updates_when:
  - major project constraints change
  - architectural decisions are added or reversed
  - product scope changes
---

# Decisions

This file records stable project decisions.
Update it when a broad constraint changes intentionally.

## Local-Only Application

PortfoTrack runs on a single local machine.
It should not depend on network services, cloud APIs, or hosted databases.

## File-Based Persistence

Persistence uses local JSON or CSV files.
Do not introduce databases, ORMs, or external storage engines.

## Asset-Class-Level Tracking

The app tracks asset classes and KRW amounts.
It does not track individual security prices.

## Rule-Based Guidance Only

The app may provide minimal rule-based rebalancing guidance.
It should not provide optimization-heavy logic, forecasting, automated trading
signals, or personalized financial advice.

## Explicit Over Automation

Prefer explicit behavior over hidden side effects.
Avoid implicit overwrites, auto-migrations, and surprising persistence behavior.

## Links

Related:

- [Architecture](architecture.md)
- [Error Policy](error-policy.md)
- [Storage Contracts](storage-contracts.md)
- [Error Book](error-book.md)
