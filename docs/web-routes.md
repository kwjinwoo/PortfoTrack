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
  and next actions by composing existing local JSON API endpoints.
- Snapshots
- Targets
- Reports
- Trends
- Optional bets

## API Routes

API routes live in Flask blueprints under `src/portfotrack/web/routes/`.
They should return JSON and appropriate HTTP status codes.

Route modules:

- `snapshot_routes.py`
- `target_routes.py`
- `report_routes.py`
- `trend_routes.py`
- `optional_bet_routes.py`

## UI Assets

Templates live under `src/portfotrack/web/templates/`.
Static JavaScript and CSS live under `src/portfotrack/web/static/`.

Keep UI behavior aligned with the local-only application model.
Do not add external network dependencies for frontend behavior.

## Links

Depends on:

- [Architecture](architecture.md)
- [Error Policy](error-policy.md)

Related:

- [Domain Model](domain-model.md)
- [Storage Contracts](storage-contracts.md)
- [Testing Playbook](testing-playbook.md)
