# Docs Agent Instructions

The `docs/` directory is the LLM wiki for PortfoTrack.

## Invariants

- Use `$portfotrack-docs-graph` for docs graph work.
- Start from `docs/map.md`; do not treat a directory listing as the graph.
- Keep docs files flat under `docs/`.
- Every docs node must preserve frontmatter fields: `id`, `title`, `kind`,
  `depends_on`, `related`, `code_refs`, `tests`, and `updates_when`.
- Use stable lowercase hyphenated node ids.
- Keep typed links meaningful; do not connect every node to every other node.
- Update `docs/index.md` when adding or removing a node.
- Update `docs/map.md` when traversal paths change.
- Do not add `llms.txt` unless explicitly requested.

## Related Knowledge

- `docs/map.md`
- `docs/index.md`
- `docs/error-book.md`
