---
name: okf-data-catalog
description: Turn a data catalog (datasets, tables, columns, schemas, metrics, join paths) into an OKF bundle, mirroring the reference enrichment agent's metadata-then-docs passes.
type: Skill
title: OKF Data Catalog Skill
tags: [okf, skill, data-catalog]
timestamp: 2026-06-29T18:45:00+02:00
---

Use this skill when the user wants to represent a data warehouse, lakehouse, or
BigQuery/Snowflake-style catalog as an OKF bundle, or to enrich an existing
catalog export with curated context.

This is OKF's flagship use case: agents answer data questions far better when
they have curated table, metric, and join-path context instead of raw schemas.

## Two-pass model

The reference OKF agent works in two passes. Mirror it.

1. **Metadata pass** (cheap, deterministic): walk the catalog and emit one
   concept per durable asset using only structural metadata.
2. **Enrichment pass** (selective, sourced): add descriptions, caveats, lineage,
   and join paths from documentation, dbt models, query history, or owners.
   Cite external documentation under `# Citations`.

Do not block the metadata pass on enrichment. A skeleton catalog is useful
immediately and can be enriched incrementally.

## Directory shape

```
<catalog>/
  index.md
  log.md
  datasets/      # one concept per dataset/schema
  tables/        # one concept per table or view
  metrics/       # one concept per governed metric or KPI
  decisions/     # data-modeling and governance decisions
```

For very large catalogs, nest `tables/<dataset>/<table>.md` so paths stay stable
and indexes stay shallow.

## Concept types

| asset | type |
|---|---|
| dataset / schema | `Dataset` |
| table / view | `Table` |
| materialized metric / KPI | `Metric` |
| business definition | `Business Term` |
| pipeline / scheduled job | `Runbook` |
| modeling or governance choice | `Architectural Decision` |

## Table concept pattern

```markdown
---
type: Table
title: Orders
description: One row per completed customer order.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, table, orders]
timestamp: 2026-05-28T14:30:00Z
---

# Summary

# Schema

| column | type | description |
|---|---|---|
| `order_id` | STRING | Primary key. |
| `customer_id` | STRING | Foreign key to [customers](/tables/customers.md). |

# Grain

One row per `order_id`.

# Relationships
```

## Join paths are links

Express foreign keys and join relationships as Markdown links in the `Schema` or
`Relationships` section, e.g. a `customer_id` column linking to
[customers](/tables/customers.md). These links become graph edges that let an
agent plan multi-table queries. Prefer absolute bundle-relative links.

## Metrics

Give every governed metric its own concept with a precise definition, the SQL or
formula, the source tables (as links), and caveats. Ambiguous metrics are the
most common cause of wrong analytics answers, so make the definition explicit.

## Resource URIs

Use the real console or catalog URI as `resource` (BigQuery console URL,
Snowflake object path, dbt docs URL). Never invent one; omit `resource` when no
canonical URI exists.

## Quality gates

* Every table concept has a `# Schema` section.
* Foreign keys are expressed as links, not prose.
* Every metric has a formula and named source tables.
* Run `python tools/okf_tool.py lint <catalog>` and
  `python tools/okf_tool.py visualize <catalog> -o <catalog>/viz.html` before
  handoff so reviewers can see the join graph.

## Completion report

Return: datasets/tables/metrics documented, join edges created, enrichment gaps
(tables still lacking descriptions or owners), and validation status.
