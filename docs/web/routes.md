---
id: web-routes
title: Web Routes
kind: interface
depends_on:
  - architecture
  - error-policy
related:
  - domain-model
  - storage-contracts
  - allocation-context-export
  - snapshot-summary-notification
  - testing-playbook
  - error-book
code_refs:
  - src/portfotrack/services/allocation_report_payload.py
  - src/portfotrack/web/app.py
  - src/portfotrack/web/date_validation.py
  - src/portfotrack/web/routes
  - src/portfotrack/web/templates
  - src/portfotrack/web/static
tests:
  - tests/web
updates_when:
  - routes are added or removed
  - API response shape changes
  - page behavior changes
  - route error handling changes
---

# Web Routes

The web layer exposes a local Flask interface.
Routes should be explicit, thin, and delegated.

## App Entrypoints

The application can be started with:

- `python -m portfotrack`
- `portfotrack`

The default host is `127.0.0.1`.
The default port is `5000`.

Primary code:

- `src/portfotrack/web/app.py`
- `src/portfotrack/__main__.py`

## Page Routes

Page routes render templates.
They should not contain business logic.

Current page areas:

- Dashboard: summarizes the latest snapshot, target setup status, drift status,
  first-use setup progress, and next actions by composing existing local JSON
  API endpoints.
- Snapshots
- Targets: presents allocation ratios as percent-scale inputs while preserving
  ratio-scale JSON API payloads.
- Reports: renders judgement-first allocation summaries before the detailed
  comparison table.
- Trends
- Optional bets

The snapshot detail panel can export the selected snapshot together with the
latest target as paste-ready Markdown. Users may copy it to the clipboard or
save it locally, omit holding labels, and hide exact amounts while retaining
allocation ratios. The export is factual and does not append a suggested AI
prompt. It can also download the selected snapshot's versioned,
consumer-neutral allocation context as local JSON.

## API Routes

API routes live in Flask blueprints under `src/portfotrack/web/routes/`.
They should return JSON and appropriate HTTP status codes.

User-provided date path and query values must be real calendar dates in exact
zero-padded `YYYY-MM-DD` form. Malformed values and impossible dates such as
`2026-02-30` return `400` with
`Invalid date format. Use YYYY-MM-DD.` Shared validation belongs to
`src/portfotrack/web/date_validation.py`; route modules must not maintain
separate date regular expressions.

Route modules:

- `snapshot_routes.py`
- `target_routes.py`
- `report_routes.py`
- `trend_routes.py`
- `optional_bet_routes.py`

`GET /api/reports/allocation?snapshot_date=YYYY-MM-DD` returns the selected
snapshot's comparison with the latest target. Its stable top-level fields are:

- `snapshot_date`: selected ISO snapshot date;
- `total_portfolio_amount`: integer amount in the snapshot currency;
- `is_complete`: whether every report item is within its inclusive tolerance;
- `total_additional_needed`: sum of positive target shortfalls; and
- `items`: target-ordered asset comparisons.

Each item contains `asset_id`, `asset_name`, `current_amount`,
`total_portfolio`, `current_ratio`, `target_ratio`, `target_amount_needed`,
inclusive `tolerance.lower` and `tolerance.upper`, and
`is_within_tolerance`. Ratios remain on the `0.0` to `1.0` scale without
presentation rounding. Payload construction belongs to the services layer;
the route owns request validation and HTTP conversion only.

Allocation report routes also expose
`GET /api/reports/allocation/export?snapshot_date=YYYY-MM-DD`. The response is
a local UTF-8 Markdown attachment; `include_labels=false` omits holding labels
and `hide_amounts=true` omits exact monetary amounts.

`GET /api/reports/allocation/export.json?snapshot_date=YYYY-MM-DD` returns a
versioned local JSON attachment. It requires an explicit snapshot and follows
the [Allocation Context Export](../interfaces/allocation-context-export.md)
contract.

After snapshot persistence succeeds, `POST /api/snapshots` and the `new` mode
of `PUT /api/snapshots/<date>` queue a local portable summary artifact and ask
the integrated Telegram transport to deliver all pending summaries when
credentials exist. Missing setup, unavailable networks, or rejected messages
do not change the successful snapshot response. Historical overwrite and
item-edit routes do not queue summaries.
See [Snapshot Summary Notification](../interfaces/snapshot-summary-notification.md).

## UI Assets

Templates live under `src/portfotrack/web/templates/`.
Static JavaScript and CSS live under `src/portfotrack/web/static/`.
Chart dependencies are vendored under `src/portfotrack/web/static/vendor/`
so trend pages remain usable without external network access.

Keep frontend behavior and assets local; optional outbound notification
transport remains a backend integration concern.

Form styling must distinguish text-like fields from choice inputs. Rules that
give inputs full width, field height, padding, or text-field borders must
explicitly exclude checkboxes and radio buttons. Choice inputs use the shared
compact choice-control pattern so labels remain clickable and keyboard focus
stays visible.

## Dynamic UI State

Templates may render panels, buttons, tables, and warnings with `is-hidden`
when they are initially unavailable.
Static JavaScript may reveal these elements after local API calls.
Do not make `is-hidden` stronger than script-driven display changes; in
particular, avoid `display: none !important` for dynamic visibility classes.

When changing CSS or JavaScript for dynamic panels, verify the user flow that
reveals the panel, not only the static page structure.
Examples include allocation report generation, snapshot detail display, target
editing, and optional bet record/edit panels.

## Links

Depends on:

- [Architecture](../foundation/architecture.md)
- [Error Policy](../policies/error-policy.md)

Related:

- [Domain Model](../domain/overview.md)
- [Storage Contracts](../storage/contracts.md)
- [Allocation Context Export](../interfaces/allocation-context-export.md)
- [Snapshot Summary Notification](../interfaces/snapshot-summary-notification.md)
- [Testing Playbook](../policies/testing-playbook.md)
- [Error Book](../records/error-book.md)
