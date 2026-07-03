---
applyTo: '**'
---
# Agent Instructions — PortfoTrack

PortfoTrack is a local-only personal portfolio tracking app.
It tracks asset-class-level KRW amounts, compares snapshots against target
allocations, detects drift, and provides minimal rule-based rebalancing
guidance.

## Project Constraints

- No network calls, cloud dependencies, databases, ORMs, or external storage
  engines.
- Persistence is local JSON or CSV only.
- Do not add security-level price tracking.
- Do not add forecasting, optimization-heavy advice, automated trading
  signals, or personalized financial advice.
- Preserve layer boundaries between domain, services, storage, and web.
- Assertions are not allowed in production code.

## Development Conventions

- Python version: 3.12+.
- Prefer `dataclass`, `TypedDict`, and explicit type annotations.
- Public functions and classes need Google-style docstrings.
- Docstrings should describe invariants and intent, not obvious mechanics.
- Use `pytest`.
- Follow TDD for behavior changes: write or update tests first, implement the
  smallest passing change, then refactor.
- New tests should mirror the source package structure where practical.
- Before committing, run `pre-commit run --all-files`.
- Never bypass hooks with `--no-verify`.
- Commit messages use Conventional Commits with a scope:
  `<type>(<scope>): <short summary>`.

## LLM Wiki Operation

This repository uses `docs/` as an LLM-readable knowledge graph.
Use `$portfotrack-docs-graph` when reading, creating, or updating docs graph
nodes.

Durable project knowledge lives under `docs/`.
Module-level invariants live in nested `AGENTS.md` files.
Keep root entrypoints stable and group knowledge nodes in shallow,
purpose-based directories.
Do not add `llms.txt` unless explicitly requested.
