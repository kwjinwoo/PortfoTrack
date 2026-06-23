# Storage Agent Instructions

The storage layer owns JSON DTO conversion and local file persistence.

## Invariants

- Persistence is local JSON or CSV only.
- Do not introduce databases, ORMs, cloud storage, network calls, or external
  storage engines.
- JSON should be human-readable and explicit.
- DTO shapes should stay typed and intentional.
- File naming must be deterministic and reproducible.
- Date-based filenames use date only, no time, with Asia/Seoul as the
  application timezone expectation.
- Do not add hidden auto-migrations or implicit overwrites.
- Broken trusted DTOs may raise native exceptions such as `RuntimeError` or
  `TypeError`; do not convert programmer errors into user errors.

## Related Knowledge

- `docs/storage-contracts.md`
- `docs/error-policy.md`
- `docs/testing-playbook.md`
