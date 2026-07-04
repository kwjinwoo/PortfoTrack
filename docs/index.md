---
id: index
title: Repository Knowledge Index
kind: entrypoint
depends_on: []
related:
  - map
  - project-status
  - project-roadmap
  - architecture
code_refs: []
tests: []
updates_when:
  - docs navigation changes
---

# Repository Knowledge Index

This directory is the shared knowledge graph for PortfoTrack.
It is written for both humans and coding agents.

Start with [Knowledge Map](map.md) when you need to change code.
Use this page when you only need a quick overview of the available nodes.

For a quick orientation before selecting work, read
[Project Status](project-status.md).

## Core Nodes

- [Knowledge Map](map.md): Task-oriented traversal paths through the docs graph.
- [Project Status](project-status.md): Current capabilities, deliberate boundaries, work state, and verification baseline.
- [Project Roadmap](planning/roadmap.md): Intended direction, milestone states, and candidate future capabilities.
- [Architecture](foundation/architecture.md): Layer boundaries and dependency direction.
- [Domain Model](domain/overview.md): Asset, target allocation, snapshot, trend, and optional bet concepts.
- [Storage Contracts](storage/contracts.md): JSON DTOs, file stores, naming, and persistence rules.
- [Web Routes](web/routes.md): Flask app pages, API route ownership, and response expectations.
- [Allocation Context Export](interfaces/allocation-context-export.md): Versioned local JSON exchange contract for a selected allocation state.

## Cross-Cutting Nodes

- [Error Policy](policies/error-policy.md): User errors versus programmer/invariant errors.
- [Testing Playbook](policies/testing-playbook.md): TDD workflow and test placement.
- [Architecture Decision Records](adr/README.md): Accepted decisions and their consequences.
- [Error Book](records/error-book.md): Repeated agent mistakes and corrections.
- [Glossary](foundation/glossary.md): Canonical terms used across the codebase.

## Maintenance Rule

If a change alters a concept described by a docs node, update that node in the
same change. Keep links accurate enough that an agent can traverse from the
changed layer to its dependent policies.
