# Integrations Agent Instructions

The integrations layer owns optional outbound communication with external
services.

## Invariants

- Domain and storage must not import integrations.
- Credentials come from the process environment or Git-ignored local `.env`.
- Never log or persist Telegram bot tokens.
- Network failure must not change successful snapshot persistence.
- Keep transport narrow: outbound snapshot summaries only, with no remote
  commands, cloud portfolio persistence, trading, or synchronization.
- External request behavior requires deterministic tests with injected I/O.

## Related Knowledge

- `docs/foundation/architecture.md`
- `docs/interfaces/snapshot-summary-notification.md`
- `docs/adr/0006-optional-outbound-notifications.md`
- `docs/policies/testing-playbook.md`
