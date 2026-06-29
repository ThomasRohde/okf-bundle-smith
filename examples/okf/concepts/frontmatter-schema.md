---
type: Reference
title: Frontmatter Schema
description: Minimal metadata contract for OKF concept files and the recommended fields used by OKF Bundle Smith.
tags: [okf, frontmatter, metadata]
timestamp: 2026-06-29T18:45:00+02:00
---

# Summary

OKF concept files use YAML frontmatter at the top of each
[concept file](/concepts/concept-file.md). The only required field in OKF v0.1
is `type`, but OKF Bundle Smith recommends adding `title`, `description`,
`tags`, and `timestamp` when possible.

# Field Guidance

`type` should be a short, descriptive concept type. `title` is the human display
name. `description` should be a compact one-sentence summary. `tags` should be a
YAML list so tools can filter by topic. `timestamp` should be ISO 8601 with a
timezone when possible. `resource` should be present only when there is a real
canonical URI for the underlying asset or source.

# Relationships

* [Reserved files](/concepts/reserved-files.md) such as `index.md` and `log.md` should not have frontmatter.
* The [validation profile](/controls/validation-profile.md) checks the required field and warns on missing recommended fields.
* The [OKF specification source](/sources/okf-spec.md) defines the minimal frontmatter contract.

# Citations

[1] [Open Knowledge Format specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
[2] Local source: `references/okf-v0.1-cheatsheet.md`.
[3] Local source: `references/okf-v0.1-conformance.md`.

