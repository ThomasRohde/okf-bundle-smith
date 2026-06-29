---
type: System
title: OKF Bundle Smith Architecture
description: Architecture overview for the OKF Bundle Smith plugin, core engine, MCP server, visualizer, and extension points.
tags: [okf, architecture, plugin]
timestamp: 2026-06-29T18:45:00+02:00
---

# Architecture

OKF Bundle Smith is a Codex plugin for producing high-quality Open Knowledge
Format (OKF) bundles. It is organized so that **judgment lives in skills** and
**deterministic mechanics live in tools**.

## Design principles

1. **Dependency-light.** The core runs on the Python standard library. PyYAML is
   used when available and the parser falls back to a minimal built-in parser
   otherwise. The MCP server has no third-party dependencies.
2. **Format, not platform.** The plugin emits plain OKF (Markdown + YAML), with
   no proprietary runtime, matching the OKF spec's own philosophy.
3. **Conformance vs. quality are separate.** The validator distinguishes hard
   OKF v0.1 errors from quality warnings (see
   [references/okf-v0.1-conformance.md](references/okf-v0.1-conformance.md)).
4. **CLI / MCP parity.** Every capability is reachable both from the CLI
   (`tools/okf_tool.py`) and from the `okf-tools` MCP server, backed by one core
   module so behavior cannot drift.

## Components

```
.codex-plugin/plugin.json   Plugin manifest (skills, MCP wiring, interface)
.mcp.json                   MCP server declaration (okf-tools, stdio)
assets/logo.svg             Brand asset referenced by the manifest
skills/                     Model-facing guidance (the "how to do it well")
tools/okf_core.py           Engine: parse, scan/validate, index, graph, stats, visualize, package
tools/okf_tool.py           CLI front end over the engine
tools/okf_mcp_server.py     Minimal stdio JSON-RPC MCP server over the engine
hooks/                      Optional session-context and stop-review hooks
references/                 Cheat sheet, conformance map, type catalog, rubric, policies
examples/                   Sample bundles (also used as test fixtures)
tests/                      Stdlib unittest coverage
.github/workflows/ci.yml    Tests + example-bundle validation
```

## Core engine (`tools/okf_core.py`)

The engine is the single source of truth. Key entry points:

| function | purpose |
|---|---|
| `parse_frontmatter` | YAML frontmatter parser with a stdlib fallback |
| `scan_bundle` | Walks the tree and produces a `BundleReport` of concepts + issues |
| `generate_indexes` | Writes `index.md` for the root and participating directories |
| `graph` | Emits a `{nodes, edges}` graph plus an issue summary |
| `bundle_stats` / `stats_markdown` | Type/tag distribution and link health |
| `build_visualization` / `write_visualization` | Self-contained interactive HTML viewer |
| `add_log_entry` | Inserts a dated entry into `log.md` |
| `scaffold_bundle` | Creates a minimal valid bundle |
| `package_bundle` | Zips or tars a bundle |

Data model: `Concept` (path, frontmatter, body), `Issue` (severity, path,
message), and `BundleReport` (concepts, issues, indexes, logs).

## Validation flow

`scan_bundle` collects concepts, then runs structural checks (`_check_indexes`,
`_check_links`, `_check_duplicates`, `_check_orphans`). Internal links are
resolved relative to the bundle root (absolute `/...`) or the source file
(relative). `--strict` promotes every warning to an error for CI gates.

## Visualizer

`build_visualization` renders a single HTML file with the bundle graph and each
concept's body embedded as JSON. It loads Cytoscape.js (graph) and marked.js
(Markdown) from a CDN, so the generated file needs internet access to render but
requires no build step. Nodes are colored by `type`; the panel shows frontmatter,
rendered body, outgoing links, and backlinks, and in-body concept links are
clickable for graph traversal.

## MCP server

`okf_mcp_server.py` implements `initialize`, `tools/list`, and `tools/call` over
stdio JSON-RPC with no dependencies. Each tool is a thin wrapper over the engine.
It performs no authentication, remote retrieval, or caching by design; wrap it
for enterprise use.

## Extending

* **New capability:** add it to `okf_core.py`, expose a CLI subcommand in
  `okf_tool.py`, and add a matching MCP tool in `okf_mcp_server.py` (keep
  parity), then cover it in `tests/`.
* **New workflow guidance:** add a skill under `skills/<name>/SKILL.md` with an
  optional `agents/openai.yaml`.

See [CONTRIBUTING.md](CONTRIBUTING.md).
