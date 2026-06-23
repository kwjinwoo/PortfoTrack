# Services Agent Instructions

The services layer orchestrates application use cases across domain and
storage.

## Invariants

- Keep services thin where a domain object already owns the rule.
- Do not duplicate domain validation in service wrappers.
- Convert domain objects to DTOs before delegating persistence to storage.
- Convert DTOs back to domain objects after loading from storage.
- Aggregation and reporting may coordinate multiple domain concepts, but should
  remain deterministic and rule-based.
- Unknown snapshot asset ids in allocation reports are programmer/invariant
  violations unless the surrounding boundary explicitly treats them as user
  input.
- Do not add network calls, automated trading integrations, or forecasting.

## Related Knowledge

- `docs/architecture.md`
- `docs/domain-model.md`
- `docs/storage-contracts.md`
- `docs/testing-playbook.md`
