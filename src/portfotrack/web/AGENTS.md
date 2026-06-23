# Web Agent Instructions

The web layer exposes the local Flask UI and JSON API.

## Invariants

- Routes are explicit and RESTful where practical.
- Page routes render templates.
- API routes return JSON and appropriate HTTP status codes.
- Route handlers stay thin and delegate business behavior to services or domain
  objects.
- Use Flask blueprints grouped by domain area.
- The app remains local-only; do not add external frontend or backend network
  dependencies.
- Entrypoints remain `python -m portfotrack` and `portfotrack`.
- Default host is `127.0.0.1`; default port is `5000`.

## Related Knowledge

- `docs/web-routes.md`
- `docs/error-policy.md`
- `docs/testing-playbook.md`
