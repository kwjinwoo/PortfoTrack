# Docs Agent Instructions

The `docs/` directory is the LLM wiki for PortfoTrack.

## Invariants

- Use `$portfotrack-docs-graph` for docs graph work.
- Start from `docs/map.md`; do not treat a directory listing as the graph.
- Keep `index.md`, `map.md`, and `project-status.md` as stable root entrypoints.
- Group other nodes in shallow, purpose-based directories one level below
  `docs/`; do not mirror the source tree mechanically.
- Every docs node must preserve frontmatter fields: `id`, `title`, `kind`,
  `depends_on`, `related`, `code_refs`, `tests`, and `updates_when`.
- Use globally unique, lowercase hyphenated node ids that do not depend on a
  node's filesystem path.
- Keep typed links meaningful; do not connect every node to every other node.
- Update `docs/index.md` when adding or removing a node.
- Update `docs/map.md` when traversal paths change.
- Keep ADRs under `docs/adr/`, list them in `docs/adr/README.md`, and preserve
  superseded decisions instead of rewriting their history.
- Do not add `llms.txt` unless explicitly requested.

## Node Growth

- Split a node when independently changing concepts accumulate, tasks usually
  need only one section, or the node becomes difficult to scan.
- Treat roughly 200 lines or 1,500 words as a review signal, not a hard limit.
- Keep the original node as a concise hub when callers still need an overview.
- Put extracted leaf nodes in the same purpose-based directory and update the
  index, map, frontmatter edges, and relative links in the same change.

## Related Knowledge

- `docs/map.md`
- `docs/index.md`
- `docs/records/error-book.md`
