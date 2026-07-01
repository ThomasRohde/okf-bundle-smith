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
| Skills | Bundle architecture, web research, concept authoring, review/repair, update, data-catalog, and parallel-build workflows |
| Codex subagents | `agents/` role definitions (source scout, concept mapper, authoring worker, citation auditor, graph reviewer, skeptical reviewer) for parallel authoring of large bundles |
| MCP tools | Scaffold, validate, stats, generate indexes, export graph JSON, visualize (HTML), add log entries, package bundles, attach GitHub bundles, search/read/related/context/freshness, plan/coverage, and subagent install |
| CLI tools | Dependency-light Python commands for local use outside Codex, including producer and consumer workflows |
| Visualizer | Self-contained interactive HTML viewer: force-directed Graph + Overview dashboard, dependency-free (canvas renderer + built-in Markdown) |
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

Render the interactive HTML viewer (opens in a browser; works offline — only web fonts load from a CDN):

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

## Build A Large Bundle In Parallel

For bundles too large for a single agent context, fan out authoring across many
Codex subagents over a durable, sharded plan, then gate on a deterministic
coverage audit so no concept is dropped. See the `okf-parallel-build` skill for
the full orchestration playbook. The mechanics:

Install the bundled Codex subagents once (into `.codex/agents/`):

```powershell
python tools\okf_tool.py install-agents
```

Build a plan (concept ledger) from an inventory and assign shards:

```powershell
python tools\okf_tool.py plan .\tmp\eu-ai-act --inventory .\tmp\inventory.json --shards 10
```

The inventory is a JSON array (or CSV) of concept rows, each with at least a
`path`; `type`, `title`, `description`, `tags`, `source_ids`, and `depends_on`
are optional. This writes `<bundle>/.okf/plan.csv` (the fan-out input for Codex's
`spawn_agents_on_csv`) and a human-readable `plan.md`.

Audit coverage — the exhaustiveness gate. It exits non-zero until every planned
concept exists and is complete:

```powershell
python tools\okf_tool.py coverage .\tmp\eu-ai-act
```

Authoring workers mark their row done as they finish:

```powershell
python tools\okf_tool.py plan-status .\tmp\eu-ai-act --path concepts/high-risk-systems.md --status done
```

Raise Codex's parallelism ceiling (default `max_threads` is 6) in
`~/.codex/config.toml`:

```toml
[agents]
max_threads = 10
max_depth = 1
```

## Consume An OKF Bundle

Search a local bundle:

```powershell
python tools\okf_tool.py search examples\acme-sales-catalog "gross revenue"
```

Read a concept with neighbors:

```powershell
python tools\okf_tool.py read examples\acme-sales-catalog metrics/gross-revenue --neighbors
```

Prepare a strict answer context pack:

```powershell
python tools\okf_tool.py context examples\acme-sales-catalog "Which tables feed gross revenue?" --mode strict
```

Attach a GitHub-hosted bundle:

```powershell
python tools\okf_tool.py attach-github https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture --alias payments
```

Attach a local bundle for reuse by alias:

```powershell
python tools\okf_tool.py attach-local examples\acme-sales-catalog --alias sales
```

Get a machine-readable bundle overview:

```powershell
python tools\okf_tool.py overview examples\acme-sales-catalog
```

Inspect bundled MCP configuration and manual stdio fallback:

```powershell
python tools\okf_tool.py mcp-diagnostics
```

Generate ChatGPT/Codex usage instructions. With `--write`, this creates
bundle-local `CHATGPT.md` and `AGENTS.md` helper files. The output also includes
an optional `repo_agents_md_snippet`; add that to repository-level `AGENTS.md`
only after the repository owner agrees to make the bundle a persistent source
for relevant future tasks.

```powershell
python tools\okf_tool.py generate-chatgpt-usage examples\acme-sales-catalog --repo acme/okf-knowledge --write
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
- `okf_attach_github_bundle`
- `okf_attach_local_bundle`
- `okf_list_attached_bundles`
- `okf_refresh_bundle`
- `okf_search_concepts`
- `okf_read_concept`
- `okf_related_concepts`
- `okf_prepare_answer_context`
- `okf_freshness_report`
- `okf_bundle_overview`
- `okf_generate_chatgpt_usage`
- `okf_mcp_diagnostics`
- `okf_plan_bundle`
- `okf_coverage_report`
- `okf_plan_status`
- `okf_install_agents`

Every MCP tool has a matching `tools/okf_tool.py` subcommand, so the same
behavior is available inside Codex and on the command line.

The server is dependency-light and communicates over stdio JSON-RPC. GitHub bundle attachment shells out to `git` and uses the user's existing credentials; the plugin does not collect or store credentials.

If your Codex client does not resolve plugin-relative MCP command paths, replace the `.mcp.json` server args with an absolute path to `tools/okf_mcp_server.py`.

If skills load but MCP tools are not exposed in a fresh chat, use `mcp-diagnostics` from the CLI to inspect the bundled server declaration. After reinstalling or cache-busting a local plugin, start a new thread; if tools are still absent, restart the Codex app.

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
- [references/okf-consumption-contract.md](references/okf-consumption-contract.md) - strict and hybrid bundle-grounded answer rules.
- [references/github-bundle-url-syntax.md](references/github-bundle-url-syntax.md) - supported GitHub URL forms and ref/path resolution.
- [references/chatgpt-okf-usage-template.md](references/chatgpt-okf-usage-template.md) - ChatGPT helper-file template and usage guidance.
- [references/okf-v0.1-conformance.md](references/okf-v0.1-conformance.md) - what the validator treats as an error versus a quality warning.
- [references/concept-type-catalog.md](references/concept-type-catalog.md) - recommended concept types.

## Known Limits

- The validator is intentionally lightweight. It checks OKF v0.1 basics and practical quality rules, not every YAML edge case.
- Citation quality still requires human or model judgment. The validator can detect missing citation sections, but it cannot prove every claim is supported.
- GitHub consumer mode uses local `git` and existing credentials. Private repository access must be configured outside the plugin.
- Consumer search is lexical and deterministic. Vector search is intentionally out of scope for the MVP.
- The HTML visualizer is dependency-free at runtime: it ships its own canvas graph renderer and Markdown parser, so the graph and bundle data render offline. Only web fonts are loaded from a CDN (the layout degrades gracefully without them). The bundle data is embedded in the file.
