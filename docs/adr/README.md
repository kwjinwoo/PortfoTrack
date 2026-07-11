---
id: adr
title: Architecture Decision Records
kind: decision-index
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
  - an ADR is added
  - an ADR status changes
  - project decision navigation changes
---

# Architecture Decision Records

This directory preserves durable project decisions, their context, and their
consequences. Read the relevant ADR before changing a constraint; do not erase
history when a decision changes.

## Records

- [ADR-0001: Local-Only Application](0001-local-only-application.md) — superseded
- [ADR-0002: File-Based Persistence](0002-file-based-persistence.md) — accepted
- [ADR-0003: Asset-Class-Level Tracking](0003-asset-class-level-tracking.md) — accepted
- [ADR-0004: Rule-Based Guidance Only](0004-rule-based-guidance-only.md) — accepted
- [ADR-0005: Explicit Over Automation](0005-explicit-over-automation.md) — accepted
- [ADR-0006: Optional Outbound Notifications](0006-optional-outbound-notifications.md) — accepted

## Recording A Decision

- Use the next four-digit sequence and a stable `adr-NNNN-short-title` node id.
- Record status, context, decision, consequences, and graph links.
- Keep accepted ADR content immutable except for clarifications that do not
  change the decision.
- Replace a decision with a new ADR and mark the old one `superseded`; link both
  records explicitly.
- Update this README, `docs/index.md`, and `docs/map.md` when navigation changes.

## Links

Related:

- [Architecture](../foundation/architecture.md)
- [Error Policy](../policies/error-policy.md)
- [Storage Contracts](../storage/contracts.md)
- [Error Book](../records/error-book.md)
