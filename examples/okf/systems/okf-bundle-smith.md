---
type: System
title: OKF Bundle Smith
description: Local Codex plugin and command-line toolkit for creating, validating, graphing, visualizing, and packaging OKF bundles.
tags: [okf, tooling, codex-plugin]
timestamp: 2026-06-29T18:45:00+02:00
---

# Summary

OKF Bundle Smith is the local toolkit used to create this
[Open Knowledge Format](/concepts/open-knowledge-format.md) example. It provides
skills, a command-line tool, and an MCP server for the OKF bundle lifecycle.

# Capabilities

The toolkit can scaffold a bundle, validate concepts, generate indexes, compute
stats, export graph JSON, render an HTML visualization, add log entries, and
package a bundle. The same lifecycle supports the
[bundle authoring workflow](/processes/bundle-authoring-workflow.md) and the
[validation profile](/controls/validation-profile.md).

# Interfaces

The local CLI entry point is `tools/okf_tool.py`. The local MCP server exposes
matching operations through `tools/okf_mcp_server.py`. Repository skills under
`skills/` define authoring, review, update, data catalog, and web research
workflows for OKF bundles.

# Citations

[1] Local source: `README.md`.
[2] Local source: `tools/okf_tool.py`.
[3] Local source: `tools/okf_mcp_server.py`.

