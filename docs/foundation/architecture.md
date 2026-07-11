---
id: architecture
title: Architecture
kind: concept
depends_on:
  - adr
related:
  - domain-model
  - storage-contracts
  - web-routes
  - testing-playbook
code_refs:
  - src/portfotrack/domain
  - src/portfotrack/services
  - src/portfotrack/storage
  - src/portfotrack/web
  - src/portfotrack/integrations
tests:
  - tests/domain
  - tests/services
  - tests/storage
  - tests/web
  - tests/integrations
updates_when:
  - layer boundaries change
  - dependency direction changes
  - a new top-level package or architectural role is added
---

# Architecture

PortfoTrack is a local-first Flask application for personal portfolio tracking.
It uses explicit layers, file-based persistence, and narrowly scoped optional
outbound integrations.

## Layers

Domain:

- Owns business concepts and invariants.
- Must not perform file I/O, HTTP handling, template rendering, or JSON store access.
- Lives under `src/portfotrack/domain/`.

Services:

- Orchestrate use cases across domain and storage.
- Hold application behavior that is larger than a single domain object.
- Live under `src/portfotrack/services/`.

Storage:

- Converts domain objects to and from JSON-friendly DTOs.
- Reads and writes local files.
- Owns deterministic file naming and persistence contracts.
- Lives under `src/portfotrack/storage/`.

Web:

- Provides the local Flask interface.
- Keeps route handlers thin and delegates business logic to services or domain objects.
- Lives under `src/portfotrack/web/`.

Integrations:

- Own optional outbound communication and external protocol details.
- Load local credentials without exposing them to domain or storage.
- Must not become portfolio persistence, inbound remote control, or trading.
- Live under `src/portfotrack/integrations/`.

## Dependency Direction

Preferred direction:

```text
web -> services -> domain
web -> services -> storage -> domain
web -> services -> integrations
```

Storage may import domain classes to reconstruct objects.
Domain must not import storage, services, or web code.

## Local-First Boundary

Local JSON remains the portfolio source of truth and core workflows remain
usable offline. Optional outbound notifications may use the network through
`integrations` only after local persistence succeeds. Cloud persistence,
databases, ORMs, inbound remote control, automated trading integrations, and
external storage engines remain outside the boundary.

## Links

Depends on:

- [Architecture Decision Records](../adr/README.md)

Related:

- [Domain Model](../domain/overview.md)
- [Storage Contracts](../storage/contracts.md)
- [Web Routes](../web/routes.md)
- [Testing Playbook](../policies/testing-playbook.md)
