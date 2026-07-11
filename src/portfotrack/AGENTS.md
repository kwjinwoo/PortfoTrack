# PortfoTrack Source Agent Instructions

This package contains production code for the local-first application.

## Invariants

- Keep the dependency direction: `web -> services -> domain`,
  `web -> services -> storage -> domain`, and
  `web -> services -> integrations`.
- Domain must not depend on services, storage, web, Flask, or file I/O.
- Services orchestrate use cases; they should not duplicate domain validation.
- Storage owns DTO conversion and local file persistence.
- Web routes stay thin and delegate behavior.
- Optional outbound network calls belong only in `integrations` and must not
  affect successful local persistence.
- Do not introduce databases, ORMs, cloud persistence, or external storage
  engines.
- For behavior changes, update tests before production code.

## Related Knowledge

- `docs/architecture.md`
- `docs/error-policy.md`
- `docs/testing-playbook.md`
