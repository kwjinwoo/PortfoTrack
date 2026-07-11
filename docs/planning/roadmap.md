---
id: project-roadmap
title: Project Roadmap
kind: reference
depends_on:
  - architecture
  - project-status
related:
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
  - a milestone is proposed, accepted, deferred, or completed
  - product direction or deliberate non-goals change
  - completed work changes the next useful milestone
---

# Project Roadmap

This node records intended product direction and candidate milestones. It does
not describe implemented behavior; read [Project Status](../project-status.md)
for the current evidence-based baseline and follow the owning contract nodes
before changing code.

## Product Direction

PortfoTrack should remain a small, local-only source of truth for personal
portfolio allocation. Its useful growth path is to make existing allocation
facts easier to record, compare, review, and exchange without expanding into
market-data collection or investment decision-making.

Prefer changes that:

- preserve asset-class-level KRW tracking;
- reuse the existing target, snapshot, and allocation-report semantics;
- keep workflows explicit, deterministic, and locally inspectable;
- improve interoperability through user-controlled local files; and
- maintain clear domain, service, storage, and web boundaries.

## Roadmap States

- `proposed`: Worth investigating, but not approved implementation work.
- `accepted`: Scope and boundaries are agreed; implementation may be selected.
- `in-progress`: Code or documentation work is actively underway.
- `completed`: The capability is implemented, verified, and reflected in its
  owning knowledge nodes.
- `deferred`: Intentionally not scheduled; retain the rationale before
  reconsidering it.

Only `accepted` and `in-progress` milestones should be treated as committed
work. Roadmap order expresses a likely sequence, not a delivery promise.

## Current Focus

No new milestone is currently accepted or in progress. Preserve the verified
local portfolio workflow described in [Project Status](../project-status.md)
until another candidate has a clear user outcome and durable boundaries.

## Completed Milestone

### Machine-readable allocation context export

Status: `completed`

Provide a versioned JSON export of an explicitly selected portfolio snapshot
and its allocation comparison. The first motivating consumer is PeakGuard,
which could combine its own price-discount observations with PortfoTrack's
allocation context. The export itself should remain consumer-neutral.

The completed capability exposes allocation facts only: stable asset ids,
current amounts and weights, target ranges, drift, snapshot date, currency, and
an export schema version. It requires an explicit snapshot, sorts assets by id,
retains ratio precision, normalizes percentage-point floating noise, and uses
the existing report route's `400` and `404` missing-data behavior.

The service builder reuses allocation-report semantics, the snapshot UI offers
a local JSON download, and tests cover payload values, tolerance boundaries,
empty inputs, deterministic ordering, attachment headers, and explicit
selection. The durable shape is owned by the
[Allocation Context Export](../interfaces/allocation-context-export.md)
contract.

### Portable snapshot summary notification

Status: `completed`

Make a newly recorded snapshot reviewable from a phone after the PortfoTrack
machine has been turned off. PortfoTrack produces a deterministic local summary
artifact after an explicit successful snapshot save; the separately maintained
Telegram bridge can deliver that artifact to a durable chat.

The summary should reuse existing snapshot, target, and allocation-report
semantics. It should present:

- the snapshot date, currency, total portfolio amount, and change from the
  previous snapshot when one exists;
- each asset class's current amount and weight, target weight and tolerance
  range, and tolerance status;
- the rule-based additional amount needed for each underweight asset class;
- the total additional amount and its distribution amount and ratio across
  eligible asset classes; and
- a clear note that these values are deterministic allocation-rule references,
  not forecasts, personalized recommendations, or trade instructions.

Snapshot persistence must succeed independently of notification delivery.
PortfoTrack must not contain channel credentials, call hosted APIs, or depend
on the bridge being available. Any retry queue should remain an explicit local
artifact, and the external bridge should minimize disclosed financial data and
require deliberate user configuration.

The implemented service and local JSON store define the versioned summary and
outbox lifecycle. Snapshot routes queue only after explicit new-save success
and isolate summary failures from snapshot persistence. The sibling bridge
loads Git-ignored `.env` credentials with process-environment overrides,
splits messages to Telegram's size limit, moves successful artifacts to `sent`,
and leaves failures pending for retry. Unit and route tests cover formatting,
previous-snapshot change,
zero-value edges, deterministic persistence, failure isolation, request shape,
message splitting, completion, and retry behavior. The durable contract is
owned by
[Snapshot Summary Notification](../interfaces/snapshot-summary-notification.md).

## Deliberate Non-goals

The roadmap must not promote:

- network calls, cloud synchronization, or automatic repository uploads;
- databases, ORMs, or external storage engines;
- security-level price or ticker tracking as PortfoTrack's primary model;
- forecasting, optimization-heavy advice, or automated trading signals;
- personalized buy or sell recommendations; or
- trade execution.

An external tool may consume a user-exported local file, but its market data,
security mapping, alert classification, and automation remain outside
PortfoTrack.

## Roadmap Maintenance

Before promoting a proposal to `accepted`, resolve its product boundaries and
contract-level questions. Record a durable architectural decision in an ADR
when the change establishes a broad or costly-to-reverse rule.

When a milestone is completed, update [Project Status](../project-status.md)
and the relevant domain, storage, service, or web contract nodes in the same
change. Keep implementation checklists out of this node once their durable
outcome is documented elsewhere.

## Links

Depends on:

- [Architecture](../foundation/architecture.md)
- [Project Status](../project-status.md)

Related:

- [Allocation Context Export](../interfaces/allocation-context-export.md)
- [Snapshot Summary Notification](../interfaces/snapshot-summary-notification.md)
- [Domain Model](../domain/overview.md)
- [Storage Contracts](../storage/contracts.md)
- [Web Routes](../web/routes.md)
- [Testing Playbook](../policies/testing-playbook.md)
