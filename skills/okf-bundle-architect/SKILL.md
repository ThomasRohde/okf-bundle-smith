---
name: okf-bundle-architect
description: Design a new Open Knowledge Format bundle, including scope, concept taxonomy, directory structure, source policy, indexes, logs, validation gates, and final packaging.
---

Use this skill when the user asks to create a new OKF bundle or asks how an OKF bundle should be structured.

## Operating contract

Create bundles that are useful to both humans and agents. Do not merely convert pages into Markdown. Produce an intentional concept graph.

Always optimize for:

1. **Atomic concepts**: one durable idea, asset, metric, process, API, system, data table, decision, or playbook per concept file.
2. **Traceability**: claims from external material are backed by numbered citations under `# Citations`.
3. **Progressive disclosure**: root and directory `index.md` files tell an agent where to go next without loading every file.
4. **Stable identity**: file paths are stable concept IDs. Avoid temporary, vendor-specific, or date-stamped paths unless chronology is the domain.
5. **Preservation**: when updating an existing bundle, preserve unknown frontmatter fields and user-authored prose unless there is a clear reason to change them.
6. **Reviewability**: keep files diffable, structured, and small enough for code review.

## Creation workflow

1. Infer the bundle purpose, target consumers, intended freshness, and source boundaries from the request. Ask only when the answer cannot be discovered and a wrong assumption would materially damage the bundle.
2. Define a source policy before writing: authoritative sources, allowed secondary sources, excluded sources, citation requirements, and licensing constraints.
3. Gather facts using available tools. For web-derived bundles, prefer primary sources and official documentation; use secondary sources only to identify leads or compare interpretations.
4. Create a concept inventory before writing files. Include `path`, `type`, `title`, `description`, `resource`, `tags`, and key citations.
5. Design the directory tree around retrieval behavior, not organizational politics. Recommended top-level directories:
   - `concepts/` for core domain ideas.
   - `systems/` for applications, platforms, products, services, or repositories.
   - `data/` for datasets, tables, schemas, metrics, data contracts.
   - `processes/` for operating procedures, runbooks, controls, and workflows.
   - `decisions/` for architectural decisions and rationale.
   - `sources/` only when source material itself is a concept worth describing.
6. Write concept files with YAML frontmatter and structural Markdown sections.
7. Add cross-links where they help traversal. Prefer absolute bundle-relative links, e.g. `/systems/payments-api.md`.
8. Generate `index.md` for the root and every ancestor directory that participates in the concept tree. Keep index entries compact.
9. Add or update `log.md` with a date-grouped summary.
10. Run validation and repair until the bundle has no hard errors and only intentional warnings. Use `python tools/okf_tool.py lint <bundle>` when the plugin repo is available.

## Required OKF conformance minimum

Every concept file must:

```markdown
---
type: <short descriptive type>
title: <human display title>
description: <one sentence summary>
resource: <canonical URI when there is one>
tags: [tag-one, tag-two]
timestamp: <ISO 8601 datetime>
---

# Summary
...

# Citations

[1] [Source title](https://example.com/source)
```

Only `type` is strictly required by the OKF v0.1 spec, but this plugin should usually include the recommended fields unless there is a reason not to. Omit `resource` when there is no real canonical URI; do not invent one to satisfy a template.

## Concept types

OKF has no central type registry. Use self-explanatory types. Prefer stable nouns:

- `Reference`
- `System`
- `API`
- `API Endpoint`
- `Data Product`
- `Dataset`
- `Table`
- `Metric`
- `Business Term`
- `Process`
- `Playbook`
- `Runbook`
- `Control`
- `Risk`
- `Architectural Decision`
- `Regulation`
- `Source`

Do not invent cute or opaque type names.

## Completion criteria

Before final response, report:

- bundle path and packaging format;
- number of concept files;
- number of indexes and logs;
- validation status;
- open warnings and known limitations;
- most important source/citation constraints.
