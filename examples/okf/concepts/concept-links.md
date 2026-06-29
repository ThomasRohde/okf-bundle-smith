---
type: Reference
title: Concept Links
description: Markdown links that connect OKF concept files into a traversable knowledge graph.
tags: [okf, links, graph]
timestamp: 2026-06-29T18:45:00+02:00
---

# Summary

Concept links are ordinary Markdown links between [concept files](/concepts/concept-file.md).
They let OKF consumers traverse from one durable concept to related concepts
without needing a separate graph database or proprietary catalog API.

# Link Practice

Use bundle-relative links when linking concepts inside a bundle. Absolute
bundle-relative links such as `/systems/okf-bundle-smith.md` keep paths stable
when files move between directories. Link semantics should be clear from the
sentence or list item around the link.

# Relationships

* [Open Knowledge Format](/concepts/open-knowledge-format.md) uses links as the graph edge mechanism.
* [Reserved files](/concepts/reserved-files.md) use links for progressive disclosure.
* The [validation profile](/controls/validation-profile.md) warns on broken internal links.

# Citations

[1] [Open Knowledge Format specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
[2] Local source: `references/okf-v0.1-cheatsheet.md`.
[3] Local source: `references/okf-v0.1-conformance.md`.

