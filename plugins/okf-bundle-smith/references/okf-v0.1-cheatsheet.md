---
type: Reference
title: OKF v0.1 Cheat Sheet
description: Compact OKF v0.1 authoring reference for conformance, metadata, reserved files, links, citations, indexes, logs, and tooling.
tags: [okf, cheat-sheet, conformance]
timestamp: 2026-06-29T18:45:00+02:00
---

# OKF v0.1 cheat sheet

Source of truth: GoogleCloudPlatform/knowledge-catalog `okf/SPEC.md`.

## Minimum conformance

An OKF bundle is a directory tree of Markdown files. Each concept is one Markdown file with YAML frontmatter. The only required frontmatter field is `type`.

```markdown
---
type: Reference
---

# Summary

Concept body in Markdown.
```

## Recommended frontmatter

```yaml
type: <required concept type>
title: <display title>
description: <one-sentence summary>
resource: <canonical URI for the underlying asset, when one exists>
tags: [tag-one, tag-two]
timestamp: <ISO 8601 datetime>
```

Producers may add additional fields. Consumers should tolerate unknown fields.
Omit `resource` when there is no real canonical URI.

## Reserved filenames

- `index.md`: directory listing, no frontmatter.
- `log.md`: update history, no frontmatter.

All other `.md` files are concept documents.

## Links

- Prefer absolute bundle-relative links: `/systems/payments.md`.
- Relative links are allowed.
- Link semantics are conveyed by surrounding prose.
- Broken links are not malformed under the spec, but this plugin treats them as quality warnings.

## Citations

Use a `# Citations` heading at the bottom of a concept when external material supports claims in the body.

```markdown
# Citations

[1] [Source title](https://example.com/source)
```

## Index files

Index files support progressive disclosure. Generate them at the root and for every ancestor directory that participates in the concept tree.

```markdown
# Systems

* [Payments API](systems/payments-api.md) - Public API for payment initiation and status queries.
```

## Log files

Log entries are date-grouped newest first.

```markdown
# Directory Update Log

## 2026-06-29
* **Creation**: Created initial OKF bundle.
```

## Tooling

The plugin's CLI and `okf-tools` MCP server cover the full lifecycle:

| action | CLI | MCP tool |
|---|---|---|
| Scaffold | `okf_tool.py new <dir> --title ...` | `okf_scaffold_bundle` |
| Validate | `okf_tool.py lint <dir>` | `okf_validate_bundle` |
| Summarize | `okf_tool.py stats <dir>` | `okf_stats` |
| Generate indexes | `okf_tool.py index <dir>` | `okf_generate_indexes` |
| Export graph JSON | `okf_tool.py graph <dir>` | `okf_export_graph` |
| Interactive viewer | `okf_tool.py visualize <dir> -o viz.html` | `okf_visualize` |
| Add log entry | `okf_tool.py log <dir> "..."` | `okf_add_log_entry` |
| Package | `okf_tool.py package <dir> out.zip` | `okf_package_bundle` |

See [okf-v0.1-conformance](okf-v0.1-conformance.md) for what the validator
treats as an error versus a quality warning.
