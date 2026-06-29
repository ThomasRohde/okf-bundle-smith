# OKF Bundle Smith Marketplace

This repository is a Codex plugin marketplace for **OKF Bundle Smith**, a plugin for creating, validating, visualizing, and packaging Open Knowledge Format bundles.

## Install In Codex

From GitHub:

```powershell
codex plugin marketplace add ThomasRohde/okf-bundle-smith --ref master
codex plugin add okf-bundle-smith@okf-bundle-smith
```

From a local checkout:

```powershell
codex plugin marketplace add .
codex plugin add okf-bundle-smith@okf-bundle-smith
```

Start a new Codex thread after installing so the plugin skills and MCP tools are loaded.

## Repository Layout

```text
okf-bundle-smith/
├── .agents/plugins/marketplace.json
├── .github/workflows/ci.yml
├── plugins/okf-bundle-smith/
│   ├── .codex-plugin/plugin.json
│   ├── .mcp.json
│   ├── README.md
│   ├── skills/
│   ├── tools/
│   ├── references/
│   ├── examples/
│   └── tests/
└── LICENSE
```

Plugin documentation lives in [plugins/okf-bundle-smith/README.md](plugins/okf-bundle-smith/README.md).

## Validate

```powershell
python C:\Users\thoma\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py plugins\okf-bundle-smith
python -m unittest discover -s plugins\okf-bundle-smith\tests -v
python plugins\okf-bundle-smith\tools\check_manifest.py plugins\okf-bundle-smith
python scripts\check_marketplace.py
```
