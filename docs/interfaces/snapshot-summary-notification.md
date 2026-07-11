---
id: snapshot-summary-notification
title: Snapshot Summary Notification
kind: contract
depends_on:
  - architecture
  - domain-model
related:
  - storage-contracts
  - web-routes
  - testing-playbook
  - project-roadmap
code_refs:
  - src/portfotrack/services/snapshot_summary.py
  - src/portfotrack/storage/serialization/notification_summary_json.py
  - src/portfotrack/storage/json_store/notification_outbox_store.py
  - src/portfotrack/web/routes/snapshot_routes.py
  - ../PortfoTrackTelegramBridge/telegram_bridge.py
tests:
  - tests/services/test_snapshot_summary.py
  - tests/storage/json_store/test_notification_outbox_store.py
  - tests/web/test_snapshot_routes.py
  - ../PortfoTrackTelegramBridge/tests/test_telegram_bridge.py
updates_when:
  - the summary message or artifact schema changes
  - snapshot-save queue behavior changes
  - outbox naming or delivery lifecycle changes
  - the external bridge boundary changes
---

# Snapshot Summary Notification

This contract lets a phone retain a readable allocation summary after the
PortfoTrack machine is turned off. PortfoTrack produces a local message
artifact only; the separately maintained Telegram bridge owns credentials,
HTTPS delivery, polling, and delivery retries.

## Save Boundary

An explicit successful `POST /api/snapshots` save and the `new` mode of
`PUT /api/snapshots/<date>` request summary generation after snapshot
persistence completes. Item edits and historical overwrites do not queue a
notification.

The saved snapshot is authoritative. Missing target setup produces no summary,
and any later summary or outbox failure is logged without changing the
successful snapshot response. PortfoTrack never calls Telegram or reads a bot
credential.

## Version 1.0 Artifact

Pending files use
`data/notification_outbox/snapshot_summary_<snapshot-date>_v1.json`:

```json
{
  "schema_version": "1.0",
  "kind": "snapshot_summary",
  "snapshot_date": "2026-07-11",
  "message": "📊 PortfoTrack 스냅샷\n..."
}
```

A repeated explicit save for the same date replaces the pending artifact with
the latest summary. The local file is an interoperability outbox artifact, not
portfolio persistence.

## Message Semantics

The plain-text message contains:

- snapshot date, currency, total amount, and change from the most recent
  earlier snapshot;
- the number of asset classes outside their inclusive tolerance;
- each target asset's current amount and weight, target weight, tolerance
  range, and status;
- each positive `target_amount_needed`, with negative values presented as zero
  because the summary does not calculate sales; and
- the sum of positive target gaps plus each positive gap's share of that sum.

`target_amount_needed` retains the existing allocation report definition:
`int(current_total * target_ratio) - current_amount`. Distribution ratios are
each positive gap divided by the sum of positive gaps. These values describe
the current snapshot and do not recalculate a future portfolio after a deposit.
The message identifies them as deterministic references rather than forecasts,
personalized advice, trade signals, or execution instructions.

## External Telegram Bridge

The sibling `PortfoTrackTelegramBridge` companion reads only version `1.0`
snapshot-summary artifacts. It loads `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`,
and the optional `PORTFOTRACK_OUTBOX_DIR` from a bridge-local `.env` file.
Existing process environment values take precedence. The real `.env` is
excluded from version control, while `.env.example` documents the supported
keys. The bridge sends plain text through Telegram's HTTPS `sendMessage`
method and splits messages at the 4,096 character API limit.

Only after every chunk succeeds does the bridge move the artifact to the
outbox's `sent/` directory. Failed artifacts stay pending for a later pass.
This provides at-least-once retry behavior; a failure after a partial
multi-message delivery can repeat an earlier chunk.

## Links

Depends on:

- [Architecture](../foundation/architecture.md)
- [Domain Model](../domain/overview.md)

Related:

- [Storage Contracts](../storage/contracts.md)
- [Web Routes](../web/routes.md)
- [Testing Playbook](../policies/testing-playbook.md)
- [Project Roadmap](../planning/roadmap.md)
