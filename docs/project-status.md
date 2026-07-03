---
id: project-status
title: Project Status
kind: reference
depends_on:
  - architecture
related:
  - domain-model
  - storage-contracts
  - web-routes
  - testing-playbook
code_refs:
  - src/portfotrack
tests:
  - tests
updates_when:
  - user-visible capabilities are added, removed, or substantially changed
  - a project milestone or known implementation gap is recorded
  - the full test-suite verification baseline changes
---

# Project Status

This node is the repository situation board: use it to learn what exists before
choosing a task. It summarizes evidence from code, tests, and the durable
knowledge nodes; those sources remain authoritative for detailed behavior.

## Current Product State

PortfoTrack is a runnable local-only Flask application with local JSON
persistence. Its implemented workflow covers:

- defining asset-class target allocations and tolerance ranges;
- recording, viewing, updating, and deleting dated KRW portfolio snapshots;
- comparing snapshots with targets to identify allocation drift;
- presenting rule-based allocation reports and trend views;
- recording optional bets separately from the core allocation model;
- using a dashboard to surface setup state, latest data, drift, and next actions;
- exporting snapshot and target information as paste-ready Markdown, with
  controls for labels and exact amounts; and
- using vendored chart assets without an external network dependency.

See [Domain Model](domain/overview.md),
[Storage Contracts](storage/contracts.md), and [Web Routes](web/routes.md) for
the contracts behind these capabilities.

## Deliberate Boundaries

The following are product constraints, not missing features:

- tracking is at asset-class level rather than security or price level;
- persistence stays in local JSON or CSV rather than a database or cloud;
- analysis stays descriptive and rule-based rather than predictive,
  optimization-heavy, or personalized financial advice; and
- the app does not generate automated trading signals or execute trades.

See [Architecture](foundation/architecture.md) for layer and dependency
boundaries.

## Known Work State

No next milestone, open implementation gap, or canonical roadmap is currently
recorded in the docs graph. Do not infer planned work from an absent feature.
When work is intentionally accepted, record its durable scope here or in a
dedicated decision node and link it from this section.

## Verification Baseline

At commit `d7eabe1` on 2026-07-04, `uv run pytest -q` completed with `624 passed`.
This is a historical baseline, not a promise about an unverified working tree.
Re-run the command before relying on the current checkout, and update this
baseline when a later project-status review establishes a new reference point.

## Maintenance Rule

Keep this page short and evidence-based. Update capability summaries in the
same change that alters them, but leave invariants, payload details, and design
rationale in their owning nodes. A status claim should point to code, tests, or
another docs node; transient personal task lists do not belong here.

## Links

Depends on:

- [Architecture](foundation/architecture.md)

Related:

- [Domain Model](domain/overview.md)
- [Storage Contracts](storage/contracts.md)
- [Web Routes](web/routes.md)
- [Testing Playbook](policies/testing-playbook.md)
