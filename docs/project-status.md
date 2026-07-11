---
id: project-status
title: Project Status
kind: reference
depends_on:
  - architecture
related:
  - project-roadmap
  - allocation-context-export
  - snapshot-summary-notification
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

PortfoTrack is a runnable local-first Flask application with local JSON
persistence and optional outbound Telegram notifications. Its implemented
workflow covers:

- defining asset-class target allocations and tolerance ranges;
- recording, viewing, updating, and deleting dated KRW portfolio snapshots;
- comparing snapshots with targets to identify allocation drift;
- presenting rule-based allocation reports and trend views;
- recording optional bets separately from the core allocation model;
- using a dashboard to surface setup state, latest data, drift, and next actions;
- exporting snapshot and target information as paste-ready Markdown, with
  controls for labels and exact amounts;
- downloading a versioned, consumer-neutral allocation-context JSON file for
  an explicitly selected snapshot;
- producing a local, mobile-readable allocation summary outbox artifact after
  an explicit new snapshot save and immediately attempting delivery through
  the integrated Telegram transport; and
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

A canonical [Project Roadmap](planning/roadmap.md) is recorded in the docs
graph. It currently contains no accepted or in-progress milestone. The
machine-readable allocation context export, portable snapshot summary, and
integrated Telegram delivery milestones are completed.

## Verification Baseline

On 2026-07-11, `uv run pytest -q` completed with `664 passed` and
`uv run pre-commit run --all-files` passed after Telegram delivery moved into
PortfoTrack. A live message also succeeded through the integrated transport
using the project-root `.env`. This is a verification record, not a promise
about later changes; re-run the commands before relying on the current
checkout.

## Maintenance Rule

Keep this page short and evidence-based. Update capability summaries in the
same change that alters them, but leave invariants, payload details, and design
rationale in their owning nodes. A status claim should point to code, tests, or
another docs node; transient personal task lists do not belong here.

## Links

Depends on:

- [Architecture](foundation/architecture.md)

Related:

- [Project Roadmap](planning/roadmap.md)
- [Allocation Context Export](interfaces/allocation-context-export.md)
- [Snapshot Summary Notification](interfaces/snapshot-summary-notification.md)
- [Domain Model](domain/overview.md)
- [Storage Contracts](storage/contracts.md)
- [Web Routes](web/routes.md)
- [Testing Playbook](policies/testing-playbook.md)
