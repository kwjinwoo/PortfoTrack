# Graph Node Template

Use this reference when creating or substantially rewriting a PortfoTrack docs
node.

## Frontmatter Template

```md
---
id: node-id
title: Human Title
kind: concept
depends_on:
  - architecture
related:
  - testing-playbook
code_refs:
  - src/portfotrack/example
tests:
  - tests/example
updates_when:
  - relevant behavior changes
---
```

## Field Meanings

- `id`: Globally unique lowercase hyphenated node identifier. It remains stable
  when a file moves and usually matches the filename outside special entrypoints
  such as `adr/README.md`.
- `title`: Human-readable title.
- `kind`: Node type such as `entrypoint`, `graph-map`, `concept`, `contract`, `interface`, `policy`, `decision`, `decision-index`, `correction-log`, or `reference`.
- `depends_on`: Nodes that must be read first for correctness.
- `related`: Adjacent nodes that may be useful but are not prerequisites.
- `code_refs`: Source paths governed or explained by the node.
- `tests`: Test paths related to the node.
- `updates_when`: Triggers for keeping the node synchronized.

## Body Shape

```md
# Human Title

One or two short paragraphs explaining the node's purpose.

## Main Section

Use concise bullets and code references.

## Links

Depends on:

- [Architecture](../foundation/architecture.md)

Related:

- [Testing Playbook](../policies/testing-playbook.md)
```

## Edge Rules

- Add `depends_on` when another node is required to interpret this node safely.
- Add `related` for useful but optional context.
- Keep graph edges meaningful; avoid linking every node to every other node.
- If `docs/map.md` gains a path that mentions this node, ensure the node has
  enough links for local traversal after the map path is followed.
- Resolve links relative to the file that contains them; moving a node requires
  updating its inbound and outbound paths without changing its id.
