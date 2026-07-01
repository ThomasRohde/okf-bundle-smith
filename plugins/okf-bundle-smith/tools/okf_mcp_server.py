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
    build_plan,
    bundle_stats,
    coverage_markdown,
    coverage_report,
    generate_indexes,
    graph,
    install_agents,
    markdown_report,
    package_bundle,
    scan_bundle,
    scaffold_bundle,
    stats_markdown,
    update_plan_status,
    write_plan,
    write_visualization,
)
from okf_consume import (  # noqa: E402
    attach_local_bundle,
    attach_github_url,
    bundle_context,
    bundle_freshness,
    chatgpt_usage,
    list_attached_bundles,
    mcp_diagnostics,
    overview_bundle,
    read_bundle_concept,
    refresh_bundle,
    related_bundle_concepts,
    resolve_bundle_index,
    search_bundle,
)


def _write(message: dict) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _text_result(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def _json_result(payload: dict | list) -> dict:
    return _text_result(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _bundle_path_arg(arguments: dict) -> str:
    value = arguments.get("bundle_path") or arguments.get("bundle")
    if not value:
        raise ValueError("Expected `bundle_path` or `bundle`.")
    return str(value)


def _bundle_arg(arguments: dict) -> str:
    value = arguments.get("bundle") or arguments.get("bundle_path")
    if not value:
        raise ValueError("Expected `bundle` or `bundle_path`.")
    return str(value)


def _readable_bundle_path_arg(arguments: dict) -> str:
    reference = _bundle_path_arg(arguments)
    if Path(reference).exists():
        return reference
    try:
        index = resolve_bundle_index(reference)
    except KeyError:
        return reference
    return str(index.get("bundle", {}).get("local_path") or reference)


def _tool_schema() -> list[dict]:
    return [
        {
            "name": "okf_validate_bundle",
            "description": "Validate an Open Knowledge Format bundle and return a Markdown or JSON report.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string", "description": "Path to the OKF bundle directory."},
                    "bundle": {"type": "string", "description": "Alias for bundle_path."},
                    "strict": {"type": "boolean", "description": "Treat warnings as errors."},
                    "format": {"type": "string", "enum": ["markdown", "json"], "default": "markdown"}
                }
            }
        },
        {
            "name": "okf_scaffold_bundle",
            "description": "Create a small OKF bundle skeleton with a seed concept, indexes, log.md, and bundle-local AGENTS.md usage guidance.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string", "description": "Path where the bundle should be created."},
                    "title": {"type": "string", "description": "Human-readable bundle title."},
                    "seed_title": {"type": "string", "description": "Optional title for the initial concept."},
                    "overwrite": {"type": "boolean", "default": False},
                    "include_agents_md": {"type": "boolean", "default": True}
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
                    "bundle": {"type": "string", "description": "Alias for bundle_path."},
                    "format": {"type": "string", "enum": ["markdown", "json"], "default": "markdown"}
                }
            }
        },
        {
            "name": "okf_export_graph",
            "description": "Export a JSON graph of OKF concepts and Markdown links.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string"},
                    "bundle": {"type": "string", "description": "Alias for bundle_path."}
                }
            }
        },
        {
            "name": "okf_visualize",
            "description": "Render a self-contained interactive HTML viewer for an OKF bundle (force-directed Graph plus an Overview dashboard; no runtime dependencies).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string", "description": "Path to the OKF bundle directory."},
                    "bundle": {"type": "string", "description": "Alias for bundle_path."},
                    "output_path": {"type": "string", "description": "Where to write the HTML file (default: <bundle>/viz.html)."}
                }
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
        },
        {
            "name": "okf_attach_github_bundle",
            "description": "Attach, validate, and index a GitHub-hosted OKF bundle.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "alias": {"type": "string"},
                    "ref": {"type": "string"},
                    "path": {"type": "string"},
                    "persist_project": {"type": "boolean", "default": False},
                    "refresh": {"type": "boolean", "default": False}
                },
                "required": ["url"]
            }
        },
        {
            "name": "okf_attach_local_bundle",
            "description": "Attach, validate, and index a local OKF bundle path.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "bundle_path": {"type": "string", "description": "Alias for path."},
                    "alias": {"type": "string"},
                    "persist_project": {"type": "boolean", "default": False}
                }
            }
        },
        {
            "name": "okf_list_attached_bundles",
            "description": "List OKF bundles attached in plugin state and project state.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": ["all", "plugin", "project"], "default": "all"}
                }
            }
        },
        {
            "name": "okf_refresh_bundle",
            "description": "Refresh an attached GitHub OKF bundle and rebuild its index.",
            "inputSchema": {
                "type": "object",
                "properties": {"alias": {"type": "string"}},
                "required": ["alias"]
            }
        },
        {
            "name": "okf_search_concepts",
            "description": "Search concepts in an attached alias or local OKF bundle path.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle": {"type": "string"},
                    "query": {"type": "string"},
                    "type": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "max_results": {"type": "integer", "default": 10}
                },
                "required": ["bundle", "query"]
            }
        },
        {
            "name": "okf_read_concept",
            "description": "Read one OKF concept by concept ID or path.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle": {"type": "string"},
                    "concept_id": {"type": "string"},
                    "include_neighbors": {"type": "boolean", "default": False}
                },
                "required": ["bundle", "concept_id"]
            }
        },
        {
            "name": "okf_related_concepts",
            "description": "Return related concepts using Markdown links and directory proximity.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle": {"type": "string"},
                    "concept_id": {"type": "string"},
                    "depth": {"type": "integer", "default": 1},
                    "max_results": {"type": "integer", "default": 20}
                },
                "required": ["bundle", "concept_id"]
            }
        },
        {
            "name": "okf_prepare_answer_context",
            "description": "Prepare a compact OKF context pack for a bundle-grounded answer.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle": {"type": "string"},
                    "question": {"type": "string"},
                    "mode": {"type": "string", "enum": ["strict", "hybrid"], "default": "strict"},
                    "max_concepts": {"type": "integer", "default": 8},
                    "link_depth": {"type": "integer", "default": 1},
                    "max_chars_per_concept": {"type": "integer", "default": 4000}
                },
                "required": ["bundle", "question"]
            }
        },
        {
            "name": "okf_freshness_report",
            "description": "Report freshness and potential staleness for an OKF bundle.",
            "inputSchema": {
                "type": "object",
                "properties": {"bundle": {"type": "string"}},
                "required": ["bundle"]
            }
        },
        {
            "name": "okf_bundle_overview",
            "description": "Return validation, freshness, counts, directory groups, central concepts, and entrypoints for an OKF bundle.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle": {"type": "string"},
                    "bundle_path": {"type": "string", "description": "Alias for bundle."}
                }
            }
        },
        {
            "name": "okf_generate_chatgpt_usage",
            "description": "Generate ChatGPT/Codex-friendly usage instructions, bundle-local AGENTS.md guidance, optional helper files, and a repository AGENTS.md snippet.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string"},
                    "repo_name": {"type": "string"},
                    "repo_root": {"type": "string"},
                    "write_files": {"type": "boolean", "default": False},
                    "include_agents_md": {"type": "boolean", "default": True},
                    "include_llms_txt": {"type": "boolean", "default": True},
                    "include_registry": {"type": "boolean", "default": True}
                },
                "required": ["bundle_path"]
            }
        },
        {
            "name": "okf_mcp_diagnostics",
            "description": "Return the bundled okf-tools MCP declaration and manual stdio probe command.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "okf_plan_bundle",
            "description": "Build a parallel-authoring plan: a durable concept ledger with disjoint shard assignments so many subagents can author concepts in parallel without collisions. Writes <bundle>/.okf/plan.csv (fan-out input for spawn_agents_on_csv) and plan.md.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string", "description": "Bundle root where the plan is written."},
                    "inventory": {
                        "type": "array",
                        "description": "Concept inventory rows.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "description": "Bundle-relative concept path (stable ID)."},
                                "type": {"type": "string"},
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "source_ids": {"type": "array", "items": {"type": "string"}},
                                "depends_on": {"type": "array", "items": {"type": "string"}},
                                "notes": {"type": "string"}
                            },
                            "required": ["path"]
                        }
                    },
                    "inventory_path": {"type": "string", "description": "Alternative to `inventory`: path to a JSON array or CSV file."},
                    "shards": {"type": "integer", "default": 6, "description": "Number of parallel authoring shards."},
                    "plan_dir": {"type": "string", "description": "Override the plan directory (default: <bundle>/.okf)."}
                },
                "required": ["bundle_path"]
            }
        },
        {
            "name": "okf_coverage_report",
            "description": "Audit planned concepts against the files on disk. This is the exhaustiveness gate: it reports missing, incomplete (stub), errored, and unplanned concepts, plus per-shard rollups, so nothing planned is silently dropped.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string"},
                    "bundle": {"type": "string", "description": "Alias for bundle_path."},
                    "plan_dir": {"type": "string", "description": "Override the plan directory (default: <bundle>/.okf)."},
                    "format": {"type": "string", "enum": ["markdown", "json"], "default": "markdown"}
                }
            }
        },
        {
            "name": "okf_plan_status",
            "description": "Mark plan rows with a status (planned, in_progress, or done). Authoring workers call this after writing their concept file.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_path": {"type": "string"},
                    "paths": {"type": "array", "items": {"type": "string"}, "description": "Concept paths to update."},
                    "status": {"type": "string", "enum": ["planned", "in_progress", "done"], "default": "done"},
                    "plan_dir": {"type": "string", "description": "Override the plan directory (default: <bundle>/.okf)."}
                },
                "required": ["bundle_path", "paths"]
            }
        },
        {
            "name": "okf_install_agents",
            "description": "Install the bundled Codex subagent definitions (okf-source-scout, okf-concept-mapper, okf-authoring-worker, okf-citation-auditor, okf-graph-reviewer, okf-skeptical-reviewer) into a .codex/agents directory so Codex can spawn them in parallel.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target agents directory (default: <cwd>/.codex/agents)."},
                    "overwrite": {"type": "boolean", "default": False}
                }
            }
        }
    ]


def _call_tool(name: str, arguments: dict) -> dict:
    if name == "okf_validate_bundle":
        report = scan_bundle(_readable_bundle_path_arg(arguments), strict=bool(arguments.get("strict", False)))
        if arguments.get("format", "markdown") == "json":
            return _json_result(report.to_dict())
        return _text_result(markdown_report(report))

    if name == "okf_generate_indexes":
        written = generate_indexes(_bundle_path_arg(arguments), overwrite=bool(arguments.get("overwrite", True)))
        text = "Generated indexes:\n" + "\n".join(str(p) for p in written)
        return _text_result(text)

    if name == "okf_scaffold_bundle":
        written = scaffold_bundle(
            arguments["bundle_path"],
            title=arguments["title"],
            seed_title=arguments.get("seed_title"),
            overwrite=bool(arguments.get("overwrite", False)),
            include_agents_md=bool(arguments.get("include_agents_md", True)),
        )
        text = "Scaffolded OKF bundle:\n" + "\n".join(str(p) for p in written)
        return _text_result(text)

    if name == "okf_stats":
        report = scan_bundle(_readable_bundle_path_arg(arguments))
        if arguments.get("format", "markdown") == "json":
            return _text_result(json.dumps(bundle_stats(report), indent=2, ensure_ascii=False))
        return _text_result(stats_markdown(report))

    if name == "okf_export_graph":
        return _text_result(json.dumps(graph(_readable_bundle_path_arg(arguments)), indent=2, ensure_ascii=False))

    if name == "okf_visualize":
        bundle_path = _readable_bundle_path_arg(arguments)
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

    if name == "okf_attach_github_bundle":
        return _json_result(attach_github_url(
            arguments["url"],
            alias=arguments.get("alias"),
            ref=arguments.get("ref"),
            path=arguments.get("path"),
            persist_project=bool(arguments.get("persist_project", False)),
            refresh=bool(arguments.get("refresh", False)),
        ))

    if name == "okf_attach_local_bundle":
        return _json_result(attach_local_bundle(
            arguments.get("path") or arguments.get("bundle_path"),
            alias=arguments.get("alias"),
            persist_project=bool(arguments.get("persist_project", False)),
        ))

    if name == "okf_list_attached_bundles":
        return _json_result(list_attached_bundles(scope=arguments.get("scope", "all")))

    if name == "okf_refresh_bundle":
        return _json_result(refresh_bundle(arguments["alias"]))

    if name == "okf_search_concepts":
        filters = {"type": arguments.get("type"), "tags": arguments.get("tags") or []}
        return _json_result(search_bundle(
            _bundle_arg(arguments),
            arguments["query"],
            filters=filters,
            max_results=int(arguments.get("max_results", 10)),
        ))

    if name == "okf_read_concept":
        return _json_result(read_bundle_concept(
            _bundle_arg(arguments),
            arguments["concept_id"],
            include_neighbors=bool(arguments.get("include_neighbors", False)),
        ))

    if name == "okf_related_concepts":
        return _json_result(related_bundle_concepts(
            _bundle_arg(arguments),
            arguments["concept_id"],
            depth=int(arguments.get("depth", 1)),
            max_results=int(arguments.get("max_results", 20)),
        ))

    if name == "okf_prepare_answer_context":
        return _json_result(bundle_context(_bundle_arg(arguments), arguments["question"], options={
            "mode": arguments.get("mode", "strict"),
            "max_concepts": int(arguments.get("max_concepts", 8)),
            "link_depth": int(arguments.get("link_depth", 1)),
            "max_chars_per_concept": int(arguments.get("max_chars_per_concept", 4000)),
        }))

    if name == "okf_freshness_report":
        return _json_result(bundle_freshness(_bundle_arg(arguments)))

    if name == "okf_bundle_overview":
        return _json_result(overview_bundle(_bundle_arg(arguments)))

    if name == "okf_generate_chatgpt_usage":
        return _json_result(chatgpt_usage(arguments["bundle_path"], options={
            "repo_name": arguments.get("repo_name"),
            "repo_root": arguments.get("repo_root"),
            "write_files": bool(arguments.get("write_files", False)),
            "include_agents_md": bool(arguments.get("include_agents_md", True)),
            "include_llms_txt": bool(arguments.get("include_llms_txt", True)),
            "include_registry": bool(arguments.get("include_registry", True)),
        }))

    if name == "okf_mcp_diagnostics":
        return _json_result(mcp_diagnostics())

    if name == "okf_plan_bundle":
        inventory = arguments.get("inventory")
        if inventory is None and arguments.get("inventory_path"):
            inv_path = Path(arguments["inventory_path"])
            text = inv_path.read_text(encoding="utf-8")
            if inv_path.suffix.lower() == ".csv":
                import csv

                inventory = list(csv.DictReader(text.splitlines()))
            else:
                inventory = json.loads(text)
        if not isinstance(inventory, list):
            raise ValueError("Expected `inventory` array or `inventory_path`.")
        plan = build_plan(inventory, shards=int(arguments.get("shards", 6)))
        written = write_plan(_bundle_path_arg(arguments), plan, plan_dir=arguments.get("plan_dir"))
        return _json_result({
            "csv": str(written["csv"]),
            "md": str(written["md"]),
            "planned": len(plan.rows),
            "shards": plan.shards,
        })

    if name == "okf_coverage_report":
        cov = coverage_report(_readable_bundle_path_arg(arguments), plan_dir=arguments.get("plan_dir"))
        if arguments.get("format", "markdown") == "json":
            return _json_result(cov)
        return _text_result(coverage_markdown(cov))

    if name == "okf_plan_status":
        paths = arguments.get("paths") or []
        if not isinstance(paths, list) or not paths:
            raise ValueError("Expected a non-empty `paths` array.")
        return _json_result(update_plan_status(
            _bundle_path_arg(arguments),
            paths,
            arguments.get("status", "done"),
            plan_dir=arguments.get("plan_dir"),
        ))

    if name == "okf_install_agents":
        return _json_result(install_agents(
            arguments.get("target"),
            overwrite=bool(arguments.get("overwrite", False)),
        ))

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
            "serverInfo": {"name": "okf-bundle-smith", "version": "0.5.0"}
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
