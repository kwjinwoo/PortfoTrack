---
id: map
title: Knowledge Map
kind: graph-map
depends_on:
  - index
related:
  - project-status
  - project-roadmap
  - architecture
  - testing-playbook
  - error-book
code_refs: []
tests: []
updates_when:
  - docs nodes are added or removed
  - task reading paths change
---

# Knowledge Map

Use this map as the graph entrypoint for non-trivial repository work.
Each path lists the minimum docs nodes to read before editing code.
Also read the nearest `AGENTS.md` for any files you will touch.

## If Orienting or Choosing Work

Read:

1. [Project Status](project-status.md)
2. [Project Roadmap](planning/roadmap.md) when evaluating future work
3. The capability node linked from the relevant status or roadmap section

Then inspect the referenced code and tests before treating a status summary as
a detailed contract. Treat only `accepted` or `in-progress` roadmap milestones
as committed work.

## If Reviewing or Changing Product Plans

Read:

1. [Project Status](project-status.md)
2. [Project Roadmap](planning/roadmap.md)
3. [Architecture](foundation/architecture.md)

Then follow the roadmap links for affected capabilities. Keep proposals
distinct from implemented contracts, and use an ADR when accepting a broad or
costly-to-reverse architectural decision.

## If Changing Domain Logic

Read:

1. [Architecture](foundation/architecture.md)
2. [Domain Model](domain/overview.md)
3. [Error Policy](policies/error-policy.md)
4. [Testing Playbook](policies/testing-playbook.md)

Then inspect:

- `src/portfotrack/domain/AGENTS.md`
- `src/portfotrack/domain/`
- `src/portfotrack/services/` if behavior crosses a use-case boundary
- `tests/domain/`
- `tests/services/`

## If Changing Services

Read:

1. [Architecture](foundation/architecture.md)
2. [Domain Model](domain/overview.md)
3. [Storage Contracts](storage/contracts.md) when persistence is involved
4. [Testing Playbook](policies/testing-playbook.md)

Then inspect:

- `src/portfotrack/services/AGENTS.md`
- `src/portfotrack/services/`
- relevant domain and storage modules
- `tests/services/`

## If Changing JSON Persistence

Read:

1. [Architecture](foundation/architecture.md)
2. [Storage Contracts](storage/contracts.md)
3. [Error Policy](policies/error-policy.md)
4. [Testing Playbook](policies/testing-playbook.md)

Then inspect:

- `src/portfotrack/storage/AGENTS.md`
- `src/portfotrack/storage/serialization/`
- `src/portfotrack/storage/json_store/`
- `tests/storage/serialization/`
- `tests/storage/json_store/`

## If Changing Flask Routes or Pages

Read:

1. [Architecture](foundation/architecture.md)
2. [Web Routes](web/routes.md)
3. [Error Policy](policies/error-policy.md)
4. [Testing Playbook](policies/testing-playbook.md)

Then inspect:

- `src/portfotrack/web/AGENTS.md`
- `src/portfotrack/web/app.py`
- `src/portfotrack/web/routes/`
- `src/portfotrack/web/templates/`
- `src/portfotrack/web/static/`
- `tests/web/`

## If Changing Error Handling

Read:

1. [Error Policy](policies/error-policy.md)
2. [Domain Model](domain/overview.md)
3. [Storage Contracts](storage/contracts.md)
4. [Web Routes](web/routes.md)
5. [Testing Playbook](policies/testing-playbook.md)

Then inspect the layer-specific error modules before changing behavior.

## If Adding or Changing Project Rules

Read:

1. [Architecture Decision Records](adr/README.md)
2. The ADRs relevant to the rule
3. [Error Book](records/error-book.md)
4. [Architecture](foundation/architecture.md)

Then update `AGENTS.md` if the rule affects agent behavior.

## If Changing Docs Graph Nodes

Use `$portfotrack-docs-graph`.

Read:

1. `docs/AGENTS.md`
2. [Knowledge Index](index.md)
3. The node being edited
4. Any node listed in `depends_on`

Then inspect related nodes only when the edge or traversal path changes.

## Graph Edges

- `project-status` summarizes current repository capabilities and points to the
  owning contract nodes without replacing them.
- `project-roadmap` records future intent and milestone state without replacing
  `project-status`, implementation plans, contracts, or ADRs.
- `adr` indexes durable project decisions without replacing individual ADRs.
- `architecture` is a parent of domain, storage, services, and web nodes.
- `error-policy` applies across all layers.
- `testing-playbook` applies to every behavior change.
- Individual `adr-*` nodes explain why broad constraints exist.
- `error-book` records recurring corrections that agents should check before editing.
