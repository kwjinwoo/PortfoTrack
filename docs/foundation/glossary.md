---
id: glossary
title: Glossary
kind: reference
depends_on: []
related:
  - domain-model
  - storage-contracts
  - web-routes
code_refs:
  - src/portfotrack
tests: []
updates_when:
  - domain terminology changes
  - user-facing labels introduce new concepts
  - docs use a term ambiguously
---

# Glossary

Use these terms consistently in code, tests, docs, and UI copy.

## Asset

An asset-class-level unit such as cash, stocks, bonds, or another portfolio
category. It is not an individual security.

## Target Allocation

The intended portfolio allocation by asset class.
Each asset has a target ratio and a tolerance range.

## Target Ratio

The desired allocation ratio for an asset, expressed between `0.0` and `1.0`.

## Tolerance

An absolute lower and upper allocation bound.
It is not a relative deviation from the target ratio.

## Snapshot

A dated record of portfolio holdings and amounts.

## Snapshot Item

One holding entry inside a snapshot.
Snapshot items can be aggregated by asset id.

## Allocation Report

A comparison between a target allocation and a snapshot.
It reports current ratios, target ratios, shortfalls, and tolerance status.

## Drift

The difference between current allocation and intended allocation after a target
allocation is established.

## Optional Bet

A separated non-core allocation idea.
It should not replace the target allocation model.

## User Error

An error caused by invalid user-controlled input.
Use the application error hierarchy.

## Programmer Error

An impossible internal state, broken invariant, or misuse of code contracts.
Use native Python exceptions.

## Links

Related:

- [Domain Model](../domain/overview.md)
- [Storage Contracts](../storage/contracts.md)
- [Web Routes](../web/routes.md)
