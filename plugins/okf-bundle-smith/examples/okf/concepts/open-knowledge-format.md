---
type: Reference
title: Open Knowledge Format
description: Concept graph format that represents durable knowledge as Markdown files with YAML frontmatter and links.
resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
tags: [okf, knowledge-format, concept-graph]
timestamp: 2026-06-29T18:45:00+02:00
---

# Summary

Open Knowledge Format, or OKF, is a lightweight convention for representing a
knowledge bundle as Markdown [concept files](/concepts/concept-file.md). Each
concept file has YAML [frontmatter](/concepts/frontmatter-schema.md), a Markdown
body, and optional links to related concepts.

# Scope

OKF deliberately keeps the required contract small. The format defines how
concept files are stored, how reserved files such as [indexes and logs](/concepts/reserved-files.md)
are treated, and how normal Markdown [links](/concepts/concept-links.md) can
form a graph. Higher-level authoring practices, source discipline, and quality
checks are conventions layered on top of the minimal spec.

# Relationships

* The [OKF specification source](/sources/okf-spec.md) is the canonical public source for the format.
* [OKF Bundle Smith](/systems/okf-bundle-smith.md) provides local tools and skills for authoring and validating bundles.
* The [bundle authoring workflow](/processes/bundle-authoring-workflow.md) turns the format rules into a repeatable process.
* The [validation profile](/controls/validation-profile.md) separates hard conformance from quality warnings.

# Citations

[1] [Open Knowledge Format specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
[2] Local source: `references/okf-v0.1-cheatsheet.md`.

