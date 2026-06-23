# Tests Agent Instructions

Tests document behavior and protect module invariants.

## Invariants

- Use `pytest`.
- Follow TDD for behavior changes.
- Mirror the source package structure where practical.
- Prefer small, focused unit tests.
- Avoid integration-heavy fixtures unless necessary.
- Import inside test functions is acceptable when it improves readability.
- Cover the happy path, at least one failure or edge case, and relevant error
  policy boundaries.
- Assertions are allowed in tests.
- Do not change production behavior without corresponding tests unless the user
  explicitly asks to skip tests.

## Related Knowledge

- `docs/testing-playbook.md`
- `docs/error-policy.md`
