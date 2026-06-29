---
type: Reference
title: OKF v0.1 Conformance Map
description: Mapping between OKF v0.1 requirements, OKF Bundle Smith validator errors, and quality warnings.
tags: [okf, conformance, validation]
timestamp: 2026-06-29T18:45:00+02:00
---

# OKF v0.1 conformance map

How OKF Bundle Smith's validator maps to the OKF v0.1 specification. The spec is
deliberately minimal, so this plugin separates **hard conformance** (spec
requirements) from **quality** (recommended practice). Quality issues are
warnings, not errors, unless you run with `--strict`.

Source of truth: `GoogleCloudPlatform/knowledge-catalog` `okf/SPEC.md`.

## Hard conformance (validator errors)

These map to actual OKF v0.1 requirements. A bundle that trips these is not a
conformant OKF bundle.

| check | spec basis |
|---|---|
| Every non-reserved `.md` file parses as frontmatter + body | Concept files are Markdown with YAML frontmatter. |
| Frontmatter contains a non-empty `type` | `type` is the only required field. |
| Frontmatter is a mapping (not a list/scalar) | Frontmatter is a key/value block. |
| Files are valid UTF-8 | Concept files are UTF-8 Markdown. |

## Quality (validator warnings)

These are **not** spec violations. The spec says consumers must tolerate them,
so the validator reports them as warnings to raise bundle quality without
breaking conformance.

| check | rationale |
|---|---|
| Recommended fields present (`title`, `description`, `tags`, `timestamp`) | Improves retrieval and index quality. |
| `resource` is a real URI or omitted | The spec says omit `resource` when no canonical URI exists. |
| `timestamp` is ISO 8601 and not future-dated | Keeps freshness signals trustworthy. |
| `tags` is a YAML list | Consistent, queryable categorization. |
| `description` is one sentence (<= 240 chars) | Index snippets stay compact. |
| Concept body is non-empty and substantive | Frontmatter without substance is not useful to an agent. |
| External links are backed by a `# Citations` section | Traceability of factual claims. |
| Internal links resolve | The spec says consumers must tolerate broken links; we flag them anyway. |
| Concepts have an incoming link (no orphans) | Discoverability via the graph or indexes. |
| No duplicate titles | Avoids ambiguous concepts. |
| Root and participating directories have `index.md` | Progressive disclosure (recommended, not required). |
| `index.md` / `log.md` have no frontmatter | Reserved files are not concepts. |
| `log.md` date headings are `YYYY-MM-DD` | Consistent, sortable update history. |

## Explicitly tolerated (no finding)

Per the spec, consumers must not reject bundles for:

* unknown frontmatter fields (the validator preserves and ignores them);
* unknown or custom `type` values;
* missing optional fields;
* missing `index.md` files (we warn at quality level only).

## Strictness profiles

| profile | meaning |
|---|---|
| Conformance | Only the hard-conformance errors above. |
| Good (default) | Conformance plus the quality warnings above. |
| Enterprise | Good plus ownership, sensitivity, lineage, and review-cadence metadata (see the quality rubric). |

Run `--strict` to promote every warning to an error for CI gates.
