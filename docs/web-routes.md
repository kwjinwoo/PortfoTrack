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
  - testing-playbook
  - error-book
code_refs:
  - src/portfotrack/web/app.py
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
prompt.

## API Routes

API routes live in Flask blueprints under `src/portfotrack/web/routes/`.
They should return JSON and appropriate HTTP status codes.

Route modules:

- `snapshot_routes.py`
- `target_routes.py`
- `report_routes.py`
- `trend_routes.py`
- `optional_bet_routes.py`

Allocation report routes also expose
`GET /api/reports/allocation/export?snapshot_date=YYYY-MM-DD`. The response is
a local UTF-8 Markdown attachment; `include_labels=false` omits holding labels
and `hide_amounts=true` omits exact monetary amounts.

## UI Assets

Templates live under `src/portfotrack/web/templates/`.
Static JavaScript and CSS live under `src/portfotrack/web/static/`.
Chart dependencies are vendored under `src/portfotrack/web/static/vendor/`
so trend pages remain usable without external network access.

Keep UI behavior aligned with the local-only application model.
Do not add external network dependencies for frontend behavior.

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

- [Architecture](architecture.md)
- [Error Policy](error-policy.md)

Related:

- [Domain Model](domain-model.md)
- [Storage Contracts](storage-contracts.md)
- [Testing Playbook](testing-playbook.md)
- [Error Book](error-book.md)
