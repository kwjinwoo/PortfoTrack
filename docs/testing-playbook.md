---
id: testing-playbook
title: Testing Playbook
kind: policy
depends_on:
  - architecture
related:
  - domain-model
  - storage-contracts
  - web-routes
  - error-policy
code_refs:
  - tests
  - pyproject.toml
  - .pre-commit-config.yaml
tests: []
updates_when:
  - test layout changes
  - tooling changes
  - TDD policy changes
  - pre-commit policy changes
---

# Testing Playbook

PortfoTrack follows TDD for behavior changes.
Write or update tests before production code when changing behavior.

## Red, Green, Refactor

1. Red: add or update a failing test for the intended behavior.
2. Green: implement the smallest change needed to pass.
3. Refactor: improve names, structure, or duplication after tests pass.

## Test Placement

Mirror the package structure where practical:

- Domain changes: `tests/domain/`
- Service changes: `tests/services/`
- Serialization changes: `tests/storage/serialization/`
- JSON store changes: `tests/storage/json_store/`
- Web route or UI behavior changes: `tests/web/`
- Common error behavior: `tests/common/`

## Coverage Expectations

For new or modified logic, cover:

- Happy path.
- At least one failure or edge case.
- Error policy boundary where relevant.

## Commit Gate

Before committing, stage changes and run:

```bash
pre-commit run --all-files
```

Do not bypass hooks with `--no-verify`.
Do not commit while checks are failing.

## Links

Depends on:

- [Architecture](architecture.md)

Related:

- [Domain Model](domain-model.md)
- [Storage Contracts](storage-contracts.md)
- [Web Routes](web-routes.md)
- [Error Policy](error-policy.md)
