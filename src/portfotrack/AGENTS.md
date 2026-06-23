# PortfoTrack Source Agent Instructions

This package contains production code for the local-only application.

## Invariants

- Keep the dependency direction: `web -> services -> domain` and
  `web -> services -> storage -> domain`.
- Domain must not depend on services, storage, web, Flask, or file I/O.
- Services orchestrate use cases; they should not duplicate domain validation.
- Storage owns DTO conversion and local file persistence.
- Web routes stay thin and delegate behavior.
- Do not introduce network calls, databases, ORMs, cloud dependencies, or
  external storage engines.
- For behavior changes, update tests before production code.

## Related Knowledge

- `docs/architecture.md`
- `docs/error-policy.md`
- `docs/testing-playbook.md`
