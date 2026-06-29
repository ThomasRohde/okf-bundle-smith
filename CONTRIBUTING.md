---
type: Process
title: Contributing to OKF Bundle Smith
description: Local development workflow and contribution conventions for OKF Bundle Smith.
tags: [okf, contributing, development]
timestamp: 2026-06-29T18:45:00+02:00
---

# Contributing

Thanks for improving OKF Bundle Smith. This project favors small, reviewable
changes and a dependency-light core.

## Prerequisites

* Python 3.11+ (developed and tested on 3.13).
* Optional: PyYAML (`pip install pyyaml`) for the richer frontmatter parser. The
  core also works without it via a built-in fallback parser.

## Local workflow

```powershell
# Run the test suite
python -m unittest discover -s tests -v

# Validate the plugin manifest and skills
python C:\Users\thoma\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .

# Exercise the CLI against the sample bundle
python tools\okf_tool.py lint examples\acme-sales-catalog --strict
python tools\okf_tool.py stats examples\acme-sales-catalog
python tools\okf_tool.py visualize examples\acme-sales-catalog -o examples\acme-sales-catalog\viz.html
```

On macOS/Linux, use forward slashes and `python3` as appropriate.

## Conventions

* **CLI / MCP parity.** Any new capability must be added in three places:
  `tools/okf_core.py` (logic), `tools/okf_tool.py` (CLI subcommand), and
  `tools/okf_mcp_server.py` (MCP tool). Add tests for each.
* **Keep the core dependency-light.** Prefer the standard library. Guard optional
  imports behind a fallback.
* **Conformance vs. quality.** New checks that reflect the OKF v0.1 spec are
  errors; everything else is a warning. Update
  [references/okf-v0.1-conformance.md](references/okf-v0.1-conformance.md) when
  you add a check.
* **Skills are guidance, not code.** Put model-facing instructions in
  `skills/<name>/SKILL.md`. The frontmatter needs a non-empty `name` and
  `description`. An optional `agents/openai.yaml` adds Codex display metadata;
  quote any value containing a colon.
* **Sample bundles double as fixtures.** `examples/` must always pass
  `lint --strict`.

## Adding a skill

```
skills/<skill-name>/
  SKILL.md              # required: frontmatter name + description, then guidance
  agents/openai.yaml    # optional: interface/policy/dependencies metadata
```

Run the plugin validator after adding or editing a skill.

## Pull request checklist

* [ ] `python -m unittest discover -s tests` passes.
* [ ] The plugin validator passes.
* [ ] `examples/` bundles pass `lint --strict`.
* [ ] CLI and MCP stay in parity for any new capability.
* [ ] `CHANGELOG.md` updated.
