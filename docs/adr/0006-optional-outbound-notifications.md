---
id: adr-0006-optional-outbound-notifications
title: "ADR-0006: Optional Outbound Notifications"
kind: decision
status: accepted
depends_on:
  - adr-0001-local-only-application
  - adr-0002-file-based-persistence
related:
  - architecture
  - snapshot-summary-notification
code_refs:
  - AGENTS.md
  - src/portfotrack/integrations
  - src/portfotrack/services/snapshot_summary.py
tests:
  - tests/integrations
  - tests/web/test_snapshot_routes.py
updates_when:
  - outbound notification scope changes
  - credentials or delivery ownership changes
  - this decision is superseded or deprecated
---

# ADR-0006: Optional Outbound Notifications

## Status

Accepted. Supersedes the blanket runtime network prohibition in
[ADR-0001](0001-local-only-application.md).

## Context

PortfoTrack remains a personal application whose portfolio source of truth is
local JSON. A durable Telegram message is nevertheless useful for reviewing a
saved snapshot after the computer is turned off. Operating a second repository
and long-running bridge adds setup and operational overhead disproportionate
to this narrow notification use case.

## Decision

PortfoTrack may make optional outbound network calls for user-configured
notifications. Telegram delivery is owned by a dedicated `integrations` layer
inside the repository.

- Domain and storage code remain network-free.
- Local snapshot persistence completes before notification work begins.
- Missing credentials, unavailable networks, and rejected messages do not
  change snapshot-save success.
- Credentials are loaded from a Git-ignored local `.env`; committed examples
  contain placeholders only.
- Pending local artifacts provide retry input, and only fully delivered
  artifacts move to `sent`.
- The integration sends portfolio summaries outward but does not accept remote
  commands, synchronize portfolio state, or use Telegram as persistence.

## Consequences

- Core portfolio workflows remain usable offline, but PortfoTrack as a whole is
  no longer described as strictly local-only.
- Network privacy and Telegram availability become explicit concerns for the
  optional notification workflow.
- New network use cases require their own scope decision; this ADR does not
  generally authorize cloud storage, hosted databases, inbound control, or
  arbitrary external APIs.
- The standalone Telegram bridge is removed after its transport behavior and
  tests move into PortfoTrack.

## Links

Depends on:

- [ADR-0001: Local-Only Application](0001-local-only-application.md)
- [ADR-0002: File-Based Persistence](0002-file-based-persistence.md)

Related:

- [ADR Index](README.md)
- [Architecture](../foundation/architecture.md)
- [Snapshot Summary Notification](../interfaces/snapshot-summary-notification.md)
