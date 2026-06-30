---
type: Reference
title: OKF Bundle Smith Changelog
description: Release history for OKF Bundle Smith features, fixes, and version changes.
tags: [okf, changelog, release-notes]
timestamp: 2026-06-29T18:45:00+02:00
---

# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-06-29

### Added
- Marketplace repository layout with `.agents/plugins/marketplace.json` and the
  plugin nested under `plugins/okf-bundle-smith`.
- Public GitHub `homepage` and `repository` metadata in the plugin manifest.

### Changed
- Redesigned the HTML visualizer to a light "Paper" theme with two modes: a
  force-directed **Graph** (degree-sized nodes, pan/zoom, minimap, hover cards,
  concept inspector) and a new **Overview** dashboard (type distribution,
  most-connected concepts, tag vocabulary, connectivity health). Node colors come
  from the server-provided `meta.type_colors`, so any bundle's types are covered.
- The viewer is now dependency-free at runtime: it ships its own canvas graph
  renderer and Markdown parser instead of loading Cytoscape.js and marked.js from
  a CDN, so the graph and bundle data render offline (only web fonts are remote).
- GitHub Actions now validates the nested plugin path and all sample bundles,
  including `examples/okf`.

### Fixed
- The HTML visualizer HTML-escapes all rendered concept text, restricts in-body
  links to a URL-scheme allowlist, and only renders `resource` as a clickable
  link for safe URL schemes.
- Generated `viz.html` files are ignored as build artifacts.
- GitHub bundle attachment no longer leaves repository-root bundles in a
  root-files-only sparse checkout, and now reports incomplete cached checkouts
  when tracked bundle directories are missing from the working tree.

## [0.3.0] - 2026-06-29

### Added
- Interactive HTML visualizer: `okf_tool.py visualize` and the `okf_visualize`
  MCP tool render a self-contained Cytoscape.js + marked.js graph viewer with
  search, type legend toggles, layouts, backlinks, and clickable in-body links.
- `stats` command and `okf_stats` MCP tool: concept counts, type/tag
  distribution, and link health (orphans, broken links, internal edges).
- New skill `okf-data-catalog` for turning datasets, tables, and metrics into a
  cross-linked OKF bundle (the reference enrichment agent's two-pass model).
- Realistic sample bundle `examples/acme-sales-catalog` (dataset, tables with
  schemas and foreign keys, metrics, a runbook, and an architecture decision),
  used as a demo and a test fixture.
- Per-skill `agents/openai.yaml` Codex display metadata for all six skills.
- Brand logo asset wired into the manifest (`logo`, `composerIcon`).
- New references: OKF v0.1 conformance map and concept-type catalog.
- Project docs: `ARCHITECTURE.md`, `CONTRIBUTING.md`, this changelog.
- GitHub Actions CI: runs the test suite and validates the sample bundles.
- Expanded test coverage: link/orphan detection, graph export, stats, log
  entries, visualizer output, CLI smoke tests, and an MCP `tools/call` round-trip.

### Changed
- Manifest version bumped to 0.3.0; description now mentions visualization.
- MCP `serverInfo.version` bumped to 0.3.0.

### Fixed
- Internal-link detection no longer matches Markdown image syntax, so image
  references are not treated as concept links.
- `timestamp` validation now flags future-dated concepts (beyond a one-day skew).

## [0.2.0]

### Added
- Initial plugin: core engine, CLI, `okf-tools` MCP server (scaffold, validate,
  generate indexes, export graph, add log entry, package), five authoring and
  review skills, references, optional hooks, and a minimal example bundle.

# Citations

[1] [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
[2] [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
