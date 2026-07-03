---
name: portfotrack-docs-graph
description: Read, traverse, create, and update the PortfoTrack repository documentation graph. Use when working in the PortfoTrack repo and the task involves AGENTS.md, docs/map.md, docs/*.md knowledge nodes, documentation frontmatter, typed links, graph traversal paths, project status, architecture/domain/storage/web docs, decisions, glossary, error-book, or keeping docs synchronized with code changes.
---

# PortfoTrack Docs Graph

Use this skill to read and maintain PortfoTrack's graph-shaped documentation
system. The repo treats `AGENTS.md` as the agent entrypoint and `docs/map.md`
as the graph traversal map.

## Quick Workflow

1. Confirm you are in the PortfoTrack repository root.
2. Read `AGENTS.md`.
3. Read `docs/map.md`.
4. Follow the task-specific reading path in `docs/map.md`.
5. Inspect the referenced code and tests before editing docs.
6. When adding or changing docs nodes, preserve frontmatter and typed links.
7. Re-check links, node ids, and changed-file status before finishing.

## Reading The Graph

Start from `docs/map.md`, not from a directory listing.
Use the map's task paths to choose only relevant nodes.

For common tasks:

- Orientation or work selection: read `project-status`, then follow its link to
  the owning capability node before treating the summary as a contract.
- Domain behavior: read `architecture`, `domain-model`, `error-policy`, `testing-playbook`.
- Persistence: read `architecture`, `storage-contracts`, `error-policy`, `testing-playbook`.
- Web/API/UI: read `architecture`, `web-routes`, `error-policy`, `testing-playbook`.
- Rules or constraints: read `decisions`, `error-book`, `architecture`, then `AGENTS.md`.

If a node's frontmatter names `depends_on` entries, read those before relying
on that node. Use `related` entries for adjacent context only when needed.

## Writing The Graph

Every docs node should have YAML frontmatter with:

- `id`
- `title`
- `kind`
- `depends_on`
- `related`
- `code_refs`
- `tests`
- `updates_when`

Use stable lowercase hyphenated ids, and make markdown links point to local
docs files by relative path. Keep the folder flat under `docs/`.

When adding a node:

1. Create `docs/<id>.md`.
2. Add frontmatter.
3. Add a short purpose statement.
4. Add code and test references where relevant.
5. Add a `## Links` section.
6. Update `docs/index.md`.
7. Update `docs/map.md` if traversal paths change.
8. Update related nodes' frontmatter if the graph edge is meaningful.

For the exact node shape and examples, read
`references/graph-node-template.md`.

## Synchronization Rules

Update docs in the same change when code changes alter:

- behavior or invariants
- persistence format or file naming
- routes, API response shapes, or page behavior
- error handling boundaries
- test layout or required checks
- project-level constraints or decisions

Also review `project-status` in the same change when it alters:

- user-visible capabilities summarized by the status node
- an accepted milestone or known implementation gap
- the full-suite verification baseline used as a repository reference point

Do not update `project-status` for internal refactors that leave its summary
accurate. Keep detailed contracts and rationale in their owning nodes.

Do not create `llms.txt` for this repo unless the user explicitly asks.
Use `AGENTS.md` as the agent-facing entrypoint.

## Validation

Before finishing:

- Run `rg -n "\\[[^\\]]+\\]\\(([^)#]+\\.md)(#[^)]+)?\\)" docs AGENTS.md` to inspect markdown links when docs changed.
- Run `find docs -maxdepth 1 -type f -name '*.md' -print` to confirm docs stay flat.
- Run `git status --short` and report only the relevant changes.

Code tests are not required for docs-only changes unless the docs change is
paired with behavior changes.
