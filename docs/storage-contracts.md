---
id: storage-contracts
title: Storage Contracts
kind: contract
depends_on:
  - architecture
  - error-policy
related:
  - domain-model
  - testing-playbook
  - decisions
code_refs:
  - src/portfotrack/storage/serialization
  - src/portfotrack/storage/json_store
  - src/portfotrack/path.py
tests:
  - tests/storage/serialization
  - tests/storage/json_store
updates_when:
  - JSON DTO shape changes
  - file naming rules change
  - persistence behavior changes
  - schema/version expectations change
---

# Storage Contracts

Storage is file-based and local-only.
It owns JSON DTO conversion and local file persistence.

## Serialization

Serialization modules convert domain objects to and from JSON-friendly DTOs.
DTOs are explicit `TypedDict` shapes where practical.

Primary code:

- `src/portfotrack/storage/serialization/target_json.py`
- `src/portfotrack/storage/serialization/snapshot_json.py`
- `src/portfotrack/storage/serialization/optional_bet_json.py`

## File Stores

JSON stores read and write human-readable local JSON files.
They should avoid hidden side effects and implicit overwrites without intent.

Primary code:

- `src/portfotrack/storage/json_store/target_store.py`
- `src/portfotrack/storage/json_store/snapshot_store.py`
- `src/portfotrack/storage/json_store/optional_bet_store.py`

## Error Boundary

Malformed user input should become an application-level user error at the
appropriate boundary.

Broken trusted DTOs or impossible saved structures can be treated as
programmer/invariant violations and may use native exceptions such as
`RuntimeError` or `TypeError`.

See [Error Policy](error-policy.md) before changing this boundary.

## Naming and Time

Persistence filenames should be deterministic and reproducible.
Date-based filenames use date only, no time, and Asia/Seoul as the application
timezone expectation.

## Links

Depends on:

- [Architecture](architecture.md)
- [Error Policy](error-policy.md)

Related:

- [Domain Model](domain-model.md)
- [Testing Playbook](testing-playbook.md)
- [Decisions](decisions.md)
