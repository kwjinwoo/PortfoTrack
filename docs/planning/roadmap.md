---
id: project-roadmap
title: Project Roadmap
kind: reference
depends_on:
  - architecture
  - project-status
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
while proposed work is evaluated.

## Next Candidate

### Machine-readable allocation context export

Status: `proposed`

Provide a versioned JSON export of an explicitly selected portfolio snapshot
and its allocation comparison. The first motivating consumer is PeakGuard,
which could combine its own price-discount observations with PortfoTrack's
allocation context. The export itself should remain consumer-neutral.

The capability should expose allocation facts only, such as stable asset ids,
current amounts and weights, target ranges, drift, snapshot date, currency, and
an export schema version. Exact fields, rounding, ordering, and missing-data
behavior are open contract decisions, not current behavior.

Likely delivery sequence:

1. Define and document a consumer-neutral export contract.
2. Implement a service builder by reusing existing allocation-report logic.
3. Add unit tests for payload values, boundary states, and absent inputs.
4. Add a local UI download path for a selected snapshot.
5. Validate the file through a manual, user-controlled consumer workflow.
6. Promote verified behavior into the owning contract and status nodes.

Acceptance questions:

- Which existing asset id is the canonical cross-tool identity?
- Does export require an explicit snapshot, or may it select the latest one?
- How are weights and percentage-point drift represented and rounded?
- What response is produced when a target or snapshot is unavailable?
- Which fields form the stable versioned contract versus optional metadata?

Completion means a documented and tested local JSON export can be produced
without parsing Markdown, fetching market data, introducing ticker-level
modeling, or generating buy or sell guidance.

## Later Horizon

No later milestone is currently durable enough to record. Add one only when it
has a clear user outcome, respects the product boundary, and can be evaluated
independently of transient implementation ideas.

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

- [Domain Model](../domain/overview.md)
- [Storage Contracts](../storage/contracts.md)
- [Web Routes](../web/routes.md)
- [Testing Playbook](../policies/testing-playbook.md)
