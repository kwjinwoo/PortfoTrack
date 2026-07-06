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
- Do not overpower script-driven UI state with CSS. Dynamic visibility classes
  such as `is-hidden` must remain revealable by JavaScript.
- Scope form-control CSS by input type. Text-field sizing, padding, and borders
  must not apply to checkboxes or radio buttons; use the shared compact choice
  control for those inputs.
- Entrypoints remain `python -m portfotrack` and `portfotrack`.
- Default host is `127.0.0.1`; default port is `5000`.

## Related Knowledge

- `docs/web-routes.md`
- `docs/error-book.md`
- `docs/error-policy.md`
- `docs/testing-playbook.md`
