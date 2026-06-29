---
type: System
title: OKF Bundle Smith
description: Repository overview for the OKF Bundle Smith Codex plugin and its OKF bundle lifecycle tools.
tags: [okf, codex-plugin, tooling]
timestamp: 2026-06-29T18:45:00+02:00
---

# OKF Bundle Smith

OKF Bundle Smith is a Codex plugin for creating, enriching, validating, repairing, graphing, and packaging Open Knowledge Format bundles.

The plugin is built around one practical idea: OKF is easy to write syntactically, but hard to write well. Useful bundles need intentional concept boundaries, source discipline, citations, durable file paths, indexes, logs, and validation.

## What Is Included

| area | contents |
|---|---|
| Plugin manifest | `.codex-plugin/plugin.json` with skills, MCP server wiring, brand assets, and per-skill Codex metadata |
| Skills | Bundle architecture, web research, concept authoring, review/repair, update, and data-catalog workflows |
| MCP tools | Scaffold, validate, stats, generate indexes, export graph JSON, visualize (HTML), add log entries, package bundles |
| CLI tools | Dependency-light Python commands for local use outside Codex |
| Visualizer | Self-contained interactive HTML graph viewer (Cytoscape.js + marked.js) |
| References | OKF cheat sheet, conformance map, concept-type catalog, source policy, quality rubric, subagent playbook |
| Examples | `minimal-bundle` and a realistic `acme-sales-catalog` data-catalog bundle (also used as test fixtures) |
| Optional hooks | Local hook scripts kept under `hooks/`, not declared in the plugin manifest |
| CI | GitHub Actions runs tests, validates sample bundles, and sanity-checks the manifest |
| Tests | Stdlib `unittest` coverage for the engine, CLI, and MCP server |

## Repository Layout

```text
okf-bundle-smith/
├── .agents/plugins/marketplace.json
├── .github/workflows/ci.yml
├── plugins/okf-bundle-smith/
│   ├── .codex-plugin/plugin.json
│   ├── .mcp.json
│   ├── assets/logo.svg
│   ├── examples/
│   ├── hooks/
│   ├── references/
│   ├── skills/
│   ├── tests/
│   └── tools/
└── LICENSE
```

This file lives at the plugin root: `plugins/okf-bundle-smith`. The repository root is a Codex marketplace and contains `.agents/plugins/marketplace.json`.

## Install From This Marketplace

From GitHub:

```powershell
codex plugin marketplace add ThomasRohde/okf-bundle-smith --ref master
codex plugin add okf-bundle-smith@okf-bundle-smith
```

From a local checkout at the repository root:

```powershell
codex plugin marketplace add .
codex plugin add okf-bundle-smith@okf-bundle-smith
```

## Validate The Plugin

From the plugin root (`plugins/okf-bundle-smith`):

```powershell
python C:\Users\thoma\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
```

Expected result:

```text
Plugin validation passed: C:\Users\thoma\Projects\okf-bundle-smith\plugins\okf-bundle-smith
```

A dependency-light, self-contained sanity check is also bundled (used in CI):

```powershell
python tools\check_manifest.py
```

## Run Tests

```powershell
python -m unittest discover -s tests -v
```

## Use The CLI

Create a new bundle:

```powershell
python tools\okf_tool.py new .\tmp\eu-ai-act --title "EU AI Act"
```

Validate a bundle:

```powershell
python tools\okf_tool.py lint examples\minimal-bundle
python tools\okf_tool.py lint examples\minimal-bundle --format json --output .\tmp\report.json
```

Regenerate indexes:

```powershell
python tools\okf_tool.py index examples\minimal-bundle
```

Summarize a bundle:

```powershell
python tools\okf_tool.py stats examples\acme-sales-catalog
```

Export a graph:

```powershell
python tools\okf_tool.py graph examples\acme-sales-catalog --output .\tmp\okf-graph.json
```

Render the interactive HTML viewer (opens in a browser; needs internet for the CDN libraries):

```powershell
python tools\okf_tool.py visualize examples\acme-sales-catalog -o .\tmp\acme-sales-catalog-viz.html
```

Add a log entry:

```powershell
python tools\okf_tool.py log examples\minimal-bundle "Reviewed bundle quality gates" --kind Review
```

Package a bundle:

```powershell
python tools\okf_tool.py package examples\minimal-bundle .\tmp\minimal-okf-bundle.zip
```

## MCP Tools

The bundled `okf-tools` MCP server is declared in `.mcp.json` and exposes:

- `okf_scaffold_bundle`
- `okf_validate_bundle`
- `okf_stats`
- `okf_generate_indexes`
- `okf_export_graph`
- `okf_visualize`
- `okf_add_log_entry`
- `okf_package_bundle`

Every MCP tool has a matching `tools/okf_tool.py` subcommand, so the same
behavior is available inside Codex and on the command line.

The server is dependency-light and communicates over stdio JSON-RPC. It is intended for local bundle work and does not perform authentication, remote retrieval, source caching, or enterprise policy checks.

If your Codex client does not resolve plugin-relative MCP command paths, replace the `.mcp.json` server args with an absolute path to `tools/okf_mcp_server.py`.

## Optional Hooks

The `hooks/` directory contains optional local hook scripts:

- `okf_session_context.py` injects OKF guidance at session start.
- `okf_stop_review.py` blocks finalization when nearby OKF bundles have hard conformance errors.

These hooks are not referenced from `.codex-plugin/plugin.json` because the current plugin validator rejects hook declarations. If your local Codex build supports hooks, review `hooks/hooks.json` and wire it manually in your local configuration.

## OKF Authoring Contract

Use these defaults unless the target bundle has stricter local conventions:

- One durable concept per Markdown file.
- Every concept file has YAML frontmatter with `type`; include `title`, `description`, `tags`, and `timestamp` where possible.
- Use `resource` only when there is a real canonical URI.
- `index.md` and `log.md` are reserved filenames and should not have frontmatter.
- Prefer bundle-relative Markdown links for internal relationships.
- Put external factual support under `# Citations`.
- Preserve unknown frontmatter fields when updating existing bundles.
- Run validation before packaging or handing off a bundle.

## Quality Bar

A good OKF bundle should have:

- a clear purpose and target consumer;
- stable concept paths that work as concept IDs;
- indexes for progressive disclosure at the root and participating directories;
- citations for external factual claims;
- few accidental orphan concepts or broken internal links;
- a date-grouped `log.md`;
- a graph export that reflects the intended retrieval paths.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - components, engine entry points, and design decisions.
- [CONTRIBUTING.md](CONTRIBUTING.md) - dev workflow and the CLI/MCP parity rule.
- [CHANGELOG.md](CHANGELOG.md) - release history.
- [references/okf-v0.1-conformance.md](references/okf-v0.1-conformance.md) - what the validator treats as an error versus a quality warning.
- [references/concept-type-catalog.md](references/concept-type-catalog.md) - recommended concept types.

## Known Limits

- The validator is intentionally lightweight. It checks OKF v0.1 basics and practical quality rules, not every YAML edge case.
- Citation quality still requires human or model judgment. The validator can detect missing citation sections, but it cannot prove every claim is supported.
- The MCP server is local and dependency-free. Replace or wrap it for authenticated enterprise search, source retrieval, caching, or richer provenance.
- The HTML visualizer loads Cytoscape.js and marked.js from a CDN, so the generated file needs internet access to render. The bundle data itself is embedded in the file.
