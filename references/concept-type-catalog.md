---
type: Reference
title: Concept Type Catalog
description: Recommended concept type names and usage guidance for OKF Bundle Smith bundles.
tags: [okf, concept-types, authoring]
timestamp: 2026-06-29T18:45:00+02:00
---

# Concept type catalog

OKF has no central type registry: `type` is a free-form string and consumers
must tolerate unknown types. Consistency still matters, so prefer these stable
nouns. Use the closest fit; only invent a new type when none of these apply, and
keep it a plain, self-explanatory noun.

| type | use for | typical sections |
|---|---|---|
| `Reference` | overviews, domain entry points, glossary-style explainers | Summary, Scope, Relationships |
| `System` | applications, platforms, products, services, repositories | Summary, Interfaces, Dependencies, Operations |
| `API` | an API surface as a whole | Summary, Authentication, Endpoints, Errors |
| `API Endpoint` | a single endpoint or operation | Request, Response, Errors, Examples |
| `Dataset` | a dataset, schema, or data product | Summary, Tables, Access |
| `Table` | a table or view | Summary, Schema, Grain, Relationships |
| `Metric` | a governed metric or KPI | Definition, Formula, Source, Caveats |
| `Business Term` | a definition that must be shared across teams | Definition, Synonyms, Usage |
| `Process` | an operating procedure or workflow | Trigger, Steps, Owners |
| `Runbook` | an operational/on-call procedure | Trigger, Preconditions, Steps, Validation, Rollback |
| `Playbook` | a repeatable strategy or decision procedure | Trigger, Steps, Escalation |
| `Control` | a governance or compliance control | Objective, Implementation, Evidence |
| `Risk` | a tracked risk | Description, Impact, Mitigation |
| `Architectural Decision` | a recorded decision and its rationale | Context, Decision, Rationale, Consequences |
| `Regulation` | a law, standard, or regulatory obligation | Summary, Scope, Obligations, Citations |
| `Source` | a source worth describing as a reusable concept | Summary, Reliability, Used for |

## Guidance

* Pick types from the **consumer's** point of view: what kind of question does
  this concept answer?
* Keep type usage consistent within a bundle. Mixed `Table` and `BigQuery Table`
  for the same kind of asset fragments the type filter in the visualizer.
* Capitalize types as proper nouns (`Architectural Decision`, not `adr`).
* Avoid cute, opaque, or directory-derived type names.

See also: [okf-v0.1-cheatsheet](okf-v0.1-cheatsheet.md) and
[okf-v0.1-conformance](okf-v0.1-conformance.md).
