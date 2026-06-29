#!/usr/bin/env python3
"""Minimal stdio MCP server for OKF Bundle Smith.

It implements a small JSON-RPC subset used by MCP clients:
- initialize
- tools/list
- tools/call

The server is intentionally dependency-free.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

# Make sibling imports work when launched from the plugin root or tools directory.
_THIS = Path(__file__).resolve()
sys.path.insert(0, str(_THIS.parent))

from okf_core import (  # noqa: E402
    add_log_entry,
    bundle_stats,
    generate_indexes,
    graph,
    markdown_report,
    package_bundle,
    scan_bundle,
    scaffold_bundle,
    stats_markdown,
    write_visualization,
)


def _write(message: dict) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _text_result(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def _tool_schema() -> list[dict]:
    return [
        {
            "name": "okf_validate_bundle",
            "description": "Validate an Open Knowledge Format bundle and return a Markdown report.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string", "description": "Path to the OKF bundle directory."},
                    "strict": {"type": "boolean", "description": "Treat warnings as errors."}
                },
                "required": ["bundle_path"]
            }
        },
        {
            "name": "okf_scaffold_bundle",
            "description": "Create a small OKF bundle skeleton with a seed concept, indexes, and log.md.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string", "description": "Path where the bundle should be created."},
                    "title": {"type": "string", "description": "Human-readable bundle title."},
                    "seed_title": {"type": "string", "description": "Optional title for the initial concept."},
                    "overwrite": {"type": "boolean", "default": False}
                },
                "required": ["bundle_path", "title"]
            }
        },
        {
            "name": "okf_generate_indexes",
            "description": "Generate index.md files for directories containing OKF concept files.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string"},
                    "overwrite": {"type": "boolean", "default": True}
                },
                "required": ["bundle_path"]
            }
        },
        {
            "name": "okf_stats",
            "description": "Summarize an OKF bundle: concept counts, type and tag distribution, and link health.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string", "description": "Path to the OKF bundle directory."},
                    "format": {"type": "string", "enum": ["markdown", "json"], "default": "markdown"}
                },
                "required": ["bundle_path"]
            }
        },
        {
            "name": "okf_export_graph",
            "description": "Export a JSON graph of OKF concepts and Markdown links.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string"}
                },
                "required": ["bundle_path"]
            }
        },
        {
            "name": "okf_visualize",
            "description": "Render a self-contained interactive HTML graph of an OKF bundle (Cytoscape.js viewer).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string", "description": "Path to the OKF bundle directory."},
                    "output_path": {"type": "string", "description": "Where to write the HTML file (default: <bundle>/viz.html)."}
                },
                "required": ["bundle_path"]
            }
        },
        {
            "name": "okf_add_log_entry",
            "description": "Add a dated log.md entry to an OKF bundle.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string"},
                    "entry": {"type": "string"},
                    "kind": {"type": "string", "default": "Update"},
                    "date": {"type": "string", "description": "Optional YYYY-MM-DD date override."}
                },
                "required": ["bundle_path", "entry"]
            }
        },
        {
            "name": "okf_package_bundle",
            "description": "Package an OKF bundle as a zip or tar archive.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string"},
                    "output_path": {"type": "string"},
                    "format": {"type": "string", "enum": ["zip", "tar", "tar.gz", "tgz"], "default": "zip"}
                },
                "required": ["bundle_path", "output_path"]
            }
        }
    ]


def _call_tool(name: str, arguments: dict) -> dict:
    if name == "okf_validate_bundle":
        report = scan_bundle(arguments["bundle_path"], strict=bool(arguments.get("strict", False)))
        return _text_result(markdown_report(report))

    if name == "okf_generate_indexes":
        written = generate_indexes(arguments["bundle_path"], overwrite=bool(arguments.get("overwrite", True)))
        text = "Generated indexes:\n" + "\n".join(str(p) for p in written)
        return _text_result(text)

    if name == "okf_scaffold_bundle":
        written = scaffold_bundle(
            arguments["bundle_path"],
            title=arguments["title"],
            seed_title=arguments.get("seed_title"),
            overwrite=bool(arguments.get("overwrite", False)),
        )
        text = "Scaffolded OKF bundle:\n" + "\n".join(str(p) for p in written)
        return _text_result(text)

    if name == "okf_stats":
        report = scan_bundle(arguments["bundle_path"])
        if arguments.get("format", "markdown") == "json":
            return _text_result(json.dumps(bundle_stats(report), indent=2, ensure_ascii=False))
        return _text_result(stats_markdown(report))

    if name == "okf_export_graph":
        return _text_result(json.dumps(graph(arguments["bundle_path"]), indent=2, ensure_ascii=False))

    if name == "okf_visualize":
        bundle_path = arguments["bundle_path"]
        output_path = arguments.get("output_path") or str(Path(bundle_path) / "viz.html")
        out = write_visualization(bundle_path, output_path)
        return _text_result(f"Wrote OKF visualization: {out}")

    if name == "okf_add_log_entry":
        path = add_log_entry(
            arguments["bundle_path"],
            arguments["entry"],
            kind=arguments.get("kind", "Update"),
            date=arguments.get("date"),
        )
        return _text_result(f"Updated OKF log: {path}")

    if name == "okf_package_bundle":
        out = package_bundle(arguments["bundle_path"], arguments["output_path"], fmt=arguments.get("format", "zip"))
        return _text_result(f"Packaged OKF bundle: {out}")

    raise ValueError(f"Unknown tool: {name}")


def handle(request: dict) -> dict | None:
    method = request.get("method")
    request_id = request.get("id")

    # Notifications have no id; do not reply.
    is_notification = request_id is None

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "okf-bundle-smith", "version": "0.4.0"}
        }
    elif method == "tools/list":
        result = {"tools": _tool_schema()}
    elif method == "tools/call":
        params = request.get("params") or {}
        result = _call_tool(params.get("name"), params.get("arguments") or {})
    elif method in {"notifications/initialized", "ping"}:
        if is_notification:
            return None
        result = {}
    else:
        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

    if is_notification:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle(request)
            if response is not None:
                _write(response)
        except Exception as exc:
            request_id = None
            try:
                request_id = json.loads(line).get("id")
            except Exception:
                pass
            _write({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(exc), "data": traceback.format_exc(limit=5)}
            })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
