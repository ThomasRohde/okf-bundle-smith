# OKF Bundle Smith

OKF Bundle Smith is a Codex plugin for creating, enriching, validating, repairing, graphing, and packaging Open Knowledge Format bundles.

The plugin is built around one practical idea: OKF is easy to write syntactically, but hard to write well. Useful bundles need intentional concept boundaries, source discipline, citations, durable file paths, indexes, logs, and validation.

## What Is Included

| area | contents |
|---|---|
| Plugin manifest | `.codex-plugin/plugin.json` with skills and MCP server wiring |
| Skills | Bundle architecture, web research, concept authoring, review/repair, and update workflows |
| MCP tools | Scaffold, validate, generate indexes, export graph JSON, add log entries, package bundles |
| CLI tools | Dependency-light Python commands for local use outside Codex |
| References | OKF cheat sheet, source policy template, quality rubric, and subagent playbook |
| Optional hooks | Local hook scripts kept under `hooks/`, not declared in the plugin manifest |
| Tests | Stdlib `unittest` coverage for core bundle behavior and MCP tool discovery |

## Repository Layout

```text
okf-bundle-smith/
├── .codex-plugin/plugin.json
├── .mcp.json
├── examples/minimal-bundle/
├── hooks/
├── references/
├── skills/
├── tests/
└── tools/
```

This repo is laid out as a standalone plugin root. It intentionally does not include a repo-local `.agents/plugins/marketplace.json`, because the plugin is not nested under `./plugins/okf-bundle-smith`. If you later want a repo/team marketplace, create the marketplace in a parent repo and point its plugin entry at `./plugins/okf-bundle-smith`.

## Validate The Plugin

From this repository:

```powershell
python C:\Users\thoma\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
```

Expected result:

```text
Plugin validation passed: C:\Users\thoma\Projects\okf-bundle-smith
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

Export a graph:

```powershell
python tools\okf_tool.py graph examples\minimal-bundle --output .\tmp\okf-graph.json
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
- `okf_generate_indexes`
- `okf_export_graph`
- `okf_add_log_entry`
- `okf_package_bundle`

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

## Known Limits

- The validator is intentionally lightweight. It checks OKF v0.1 basics and practical quality rules, not every YAML edge case.
- Citation quality still requires human or model judgment. The validator can detect missing citation sections, but it cannot prove every claim is supported.
- The MCP server is local and dependency-free. Replace or wrap it for authenticated enterprise search, source retrieval, caching, or richer provenance.
