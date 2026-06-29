---
type: Architectural Decision
title: Use OKF for the Sales Catalog
description: Decision to publish the sales data catalog as an Open Knowledge Format bundle for agent and human use.
tags: [sales, decision, okf]
timestamp: 2026-06-15T16:00:00Z
---

# Context

Acme's analytics agents needed curated table and metric context, but that
knowledge was split between a proprietary catalog and a team wiki.

# Decision

Publish the sales catalog as an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
bundle: one Markdown concept per asset, cross-linked, with generated indexes.

# Rationale

* The format is plain Markdown and YAML, so it is diffable and version-controlled.
* Both agents and humans can read it without a proprietary SDK.
* It composes with the rest of the [sales domain](/concepts/sales-domain.md).

# Consequences

* Producers must keep concepts in sync with schema changes via the refresh job.
* Consumers tolerate unknown frontmatter fields, so we can extend metadata later.

# Citations

[1] [Open Knowledge Format specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
