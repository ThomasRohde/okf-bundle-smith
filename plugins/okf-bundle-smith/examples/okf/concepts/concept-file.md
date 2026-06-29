---
type: Reference
title: Concept File
description: Atomic Markdown document that represents one durable idea, asset, process, decision, source, or system in an OKF bundle.
tags: [okf, concept-file, markdown]
timestamp: 2026-06-29T18:45:00+02:00
---

# Summary

A concept file is the basic unit of an [OKF bundle](/concepts/open-knowledge-format.md).
It is a Markdown file with YAML [frontmatter](/concepts/frontmatter-schema.md)
followed by a substantive Markdown body. Each concept file should describe one
durable thing, such as a reference concept, system, process, control, source,
dataset, metric, or architectural decision.

# Authoring Guidance

Atomic concept boundaries keep the bundle reusable. A concept should be small
enough that an agent can retrieve it directly for one question, but complete
enough that the body gives useful context without forcing the reader to load the
whole bundle. Related ideas should be connected through [concept links](/concepts/concept-links.md).

# Relationships

* Metadata belongs in the [frontmatter schema](/concepts/frontmatter-schema.md).
* Navigation and update history belong in [reserved files](/concepts/reserved-files.md), not concept files.
* The [bundle authoring workflow](/processes/bundle-authoring-workflow.md) starts by inventorying concept files before writing them.

# Citations

[1] [Open Knowledge Format specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
[2] Local source: `references/concept-type-catalog.md`.
[3] Local source: `skills/okf-bundle-architect/SKILL.md`.

