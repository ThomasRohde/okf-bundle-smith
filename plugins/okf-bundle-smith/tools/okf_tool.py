#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from okf_core import (
    add_log_entry,
    build_plan,
    bundle_stats,
    coverage_markdown,
    coverage_report,
    generate_indexes,
    graph,
    install_agents,
    inventory_check_blocks_plan,
    markdown_report,
    package_bundle,
    retry_csv_path,
    scan_bundle,
    scaffold_bundle,
    stats_markdown,
    update_plan_status,
    write_checked_plan,
    write_visualization,
)
from okf_consume import (
    attach_local_bundle,
    attach_github_url,
    bundle_context,
    bundle_freshness,
    chatgpt_usage,
    detach_bundle,
    list_attached_bundles,
    mcp_diagnostics,
    overview_bundle,
    read_bundle_concept,
    refresh_bundle,
    related_bundle_concepts,
    search_bundle,
)


def print_json(payload: dict | list) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def cmd_lint(args: argparse.Namespace) -> int:
    report = scan_bundle(args.bundle, strict=args.strict)
    payload = json.dumps(report.to_dict(), indent=2, ensure_ascii=False) if args.format == "json" else markdown_report(report)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    if args.format == "json":
        print(payload)
    else:
        print(payload)
    return 1 if report.errors else 0


def cmd_index(args: argparse.Namespace) -> int:
    written = generate_indexes(args.bundle, overwrite=not args.no_overwrite)
    for path in written:
        print(path)
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    report = scan_bundle(args.bundle)
    if args.format == "json":
        payload = json.dumps(bundle_stats(report), indent=2, ensure_ascii=False)
    else:
        payload = stats_markdown(report)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


def cmd_visualize(args: argparse.Namespace) -> int:
    out = write_visualization(args.bundle, args.output)
    print(out)
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    data = graph(args.bundle)
    if args.output:
        Path(args.output).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(args.output)
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    out = package_bundle(args.bundle, args.output, fmt=args.format)
    print(out)
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    path = add_log_entry(args.bundle, args.entry, kind=args.kind, date=args.date)
    print(path)
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    written = scaffold_bundle(
        args.bundle,
        title=args.title,
        seed_title=args.seed_title,
        overwrite=args.overwrite,
        include_agents_md=not args.no_agents_md,
    )
    for path in written:
        print(path)
    return 0


def cmd_attach_github(args: argparse.Namespace) -> int:
    payload = attach_github_url(
        args.url,
        alias=args.alias,
        ref=args.ref,
        path=args.path,
        persist_project=args.persist_project,
        refresh=args.refresh,
    )
    print_json(payload)
    return 0


def cmd_attach_local(args: argparse.Namespace) -> int:
    payload = attach_local_bundle(
        args.path,
        alias=args.alias,
        persist_project=args.persist_project,
    )
    print_json(payload)
    return 0


def cmd_list_attached(args: argparse.Namespace) -> int:
    print_json(list_attached_bundles(scope=args.scope))
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    print_json(refresh_bundle(args.alias))
    return 0


def cmd_detach(args: argparse.Namespace) -> int:
    print_json(detach_bundle(args.alias, project=args.project))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    filters = {"type": args.type, "tags": args.tag or []}
    print_json(search_bundle(args.bundle, args.query, filters=filters, max_results=args.max_results))
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    print_json(read_bundle_concept(args.bundle, args.concept_id, include_neighbors=args.neighbors))
    return 0


def cmd_related(args: argparse.Namespace) -> int:
    print_json(related_bundle_concepts(args.bundle, args.concept_id, depth=args.depth, max_results=args.max_results))
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    options = {
        "mode": args.mode,
        "max_concepts": args.max_concepts,
        "link_depth": args.link_depth,
        "max_chars_per_concept": args.max_chars_per_concept,
        "max_total_chars": args.max_total_chars,
        "include_index": not args.no_index,
        "include_log": not args.no_log,
    }
    print_json(bundle_context(args.bundle, args.question, options=options))
    return 0


def cmd_overview(args: argparse.Namespace) -> int:
    print_json(overview_bundle(args.bundle))
    return 0


def cmd_freshness(args: argparse.Namespace) -> int:
    print_json(bundle_freshness(args.bundle))
    return 0


def cmd_generate_chatgpt_usage(args: argparse.Namespace) -> int:
    options = {
        "repo_name": args.repo,
        "repo_root": args.repo_root,
        "write_files": args.write,
        "include_agents_md": not args.no_agents_md,
        "include_llms_txt": args.llms_txt,
        "include_registry": args.registry,
    }
    print_json(chatgpt_usage(args.bundle_path, options=options))
    return 0


def cmd_mcp_diagnostics(args: argparse.Namespace) -> int:
    print_json(mcp_diagnostics())
    return 0


def _load_inventory(source: str) -> list[dict]:
    if source == "-":
        text = sys.stdin.read()
        data = json.loads(text)
    else:
        path = Path(source)
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".csv":
            import csv

            return list(csv.DictReader(text.splitlines()))
        data = json.loads(text)
    if isinstance(data, dict) and "concepts" in data:
        data = data["concepts"]
    if not isinstance(data, list):
        raise ValueError("Inventory must be a JSON array of concept rows (or a CSV).")
    return data


def cmd_plan(args: argparse.Namespace) -> int:
    plan = build_plan(_load_inventory(args.inventory), shards=args.shards)
    written = write_checked_plan(args.bundle, plan, plan_dir=args.plan_dir, strict=args.strict)
    payload = {
        "csv": str(written["csv"]),
        "md": str(written["md"]),
        "planned": len(plan.rows),
        "shards": plan.shards,
        "written": bool(written["written"]),
        "check": written["check"],
    }
    if args.format == "json":
        print_json(payload)
    else:
        if payload["written"]:
            print(f"Wrote plan: {payload['csv']}")
            print(f"Wrote plan: {payload['md']}")
        else:
            print("Plan check failed; no plan files were written.")
        print(f"Planned {payload['planned']} concepts across {payload['shards']} shards.")
        check = payload["check"]
        print(f"Inventory check: {check['errors']} errors, {check['warnings']} warnings.")
        for issue in check["issues"]:
            marker = "ERROR" if issue["severity"] == "error" else "WARN"
            print(f"- {marker} {issue['path']}: {issue['message']}")
    return 1 if inventory_check_blocks_plan(payload["check"], strict=args.strict) else 0


def cmd_coverage(args: argparse.Namespace) -> int:
    retry_path = None
    if args.retry_csv is not None:
        retry_path = retry_csv_path(args.bundle, args.plan_dir) if args.retry_csv == "" else Path(args.retry_csv)
    cov = coverage_report(args.bundle, plan_dir=args.plan_dir, retry_csv=retry_path)
    payload = json.dumps(cov, indent=2, ensure_ascii=False) if args.format == "json" else coverage_markdown(cov)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if cov["complete"] else 1


def cmd_plan_status(args: argparse.Namespace) -> int:
    print_json(update_plan_status(args.bundle, args.path, args.status, plan_dir=args.plan_dir))
    return 0


def cmd_install_agents(args: argparse.Namespace) -> int:
    print_json(install_agents(args.target, overwrite=args.overwrite))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OKF bundle helper tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("lint", help="Validate an OKF bundle")
    p.add_argument("bundle")
    p.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--output", help="Write the report to a file as well as stdout")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("index", help="Generate index.md files for directories containing concepts")
    p.add_argument("bundle")
    p.add_argument("--no-overwrite", action="store_true")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("stats", help="Summarize a bundle's concepts, types, tags, and link health")
    p.add_argument("bundle")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--output", help="Write the summary to a file as well as stdout")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("graph", help="Export bundle graph JSON")
    p.add_argument("bundle")
    p.add_argument("--output")
    p.set_defaults(func=cmd_graph)

    p = sub.add_parser("visualize", help="Render a self-contained interactive HTML graph of the bundle")
    p.add_argument("bundle")
    p.add_argument("-o", "--output", default="viz.html", help="Output HTML path (default: viz.html)")
    p.set_defaults(func=cmd_visualize)

    p = sub.add_parser("package", help="Package bundle as zip or tar.gz")
    p.add_argument("bundle")
    p.add_argument("output")
    p.add_argument("--format", choices=["zip", "tar", "tar.gz", "tgz"], default="zip")
    p.set_defaults(func=cmd_package)

    p = sub.add_parser("log", help="Add a root log.md entry")
    p.add_argument("bundle")
    p.add_argument("entry")
    p.add_argument("--kind", default="Update")
    p.add_argument("--date")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("new", help="Scaffold a small OKF bundle")
    p.add_argument("bundle")
    p.add_argument("--title", required=True, help="Human-readable bundle title")
    p.add_argument("--seed-title", help="Title for the initial concept; defaults to --title")
    p.add_argument("--overwrite", action="store_true", help="Allow scaffolding into a non-empty directory")
    p.add_argument("--no-agents-md", action="store_true", help="Do not create bundle-local AGENTS.md usage guidance")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("attach-github", help="Attach and index a GitHub-hosted OKF bundle")
    p.add_argument("url")
    p.add_argument("--alias")
    p.add_argument("--ref")
    p.add_argument("--path")
    p.add_argument("--persist-project", action="store_true")
    p.add_argument("--refresh", action="store_true")
    p.set_defaults(func=cmd_attach_github)

    p = sub.add_parser("attach-local", help="Attach and index a local OKF bundle")
    p.add_argument("path")
    p.add_argument("--alias")
    p.add_argument("--persist-project", action="store_true")
    p.set_defaults(func=cmd_attach_local)

    p = sub.add_parser("list-attached", help="List attached OKF bundles")
    p.add_argument("--scope", choices=["all", "plugin", "project"], default="all")
    p.set_defaults(func=cmd_list_attached)

    p = sub.add_parser("refresh", help="Refresh an attached GitHub OKF bundle")
    p.add_argument("alias")
    p.set_defaults(func=cmd_refresh)

    p = sub.add_parser("detach", help="Detach an OKF bundle alias")
    p.add_argument("alias")
    p.add_argument("--project", action="store_true", help="Also remove the project-local attachment")
    p.set_defaults(func=cmd_detach)

    p = sub.add_parser("search", help="Search concepts in an attached or local OKF bundle")
    p.add_argument("bundle", help="Attached alias or local bundle path")
    p.add_argument("query")
    p.add_argument("--type")
    p.add_argument("--tag", action="append", help="Require a tag; can be repeated")
    p.add_argument("--max-results", type=int, default=10)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("read", help="Read one concept by concept ID or path")
    p.add_argument("bundle", help="Attached alias or local bundle path")
    p.add_argument("concept_id")
    p.add_argument("--neighbors", action="store_true")
    p.set_defaults(func=cmd_read)

    p = sub.add_parser("related", help="Return neighboring concepts by links and directory proximity")
    p.add_argument("bundle", help="Attached alias or local bundle path")
    p.add_argument("concept_id")
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--max-results", type=int, default=20)
    p.set_defaults(func=cmd_related)

    p = sub.add_parser("context", help="Prepare a compact answer context pack")
    p.add_argument("bundle", help="Attached alias or local bundle path")
    p.add_argument("question")
    p.add_argument("--mode", choices=["strict", "hybrid"], default="strict")
    p.add_argument("--max-concepts", type=int, default=8)
    p.add_argument("--link-depth", type=int, default=1)
    p.add_argument("--max-chars-per-concept", type=int, default=4000)
    p.add_argument("--max-total-chars", type=int, default=24000, help="Budget for the sum of all concept excerpts in the pack")
    p.add_argument("--no-index", action="store_true")
    p.add_argument("--no-log", action="store_true")
    p.set_defaults(func=cmd_context)

    p = sub.add_parser("overview", help="Return a compact bundle overview for orchestration")
    p.add_argument("bundle", help="Attached alias or local bundle path")
    p.set_defaults(func=cmd_overview)

    p = sub.add_parser("freshness", help="Report OKF bundle freshness")
    p.add_argument("bundle", help="Attached alias or local bundle path")
    p.set_defaults(func=cmd_freshness)

    p = sub.add_parser("generate-chatgpt-usage", help="Generate ChatGPT/Codex-friendly OKF usage instructions")
    p.add_argument("bundle_path")
    p.add_argument("--repo")
    p.add_argument("--repo-root")
    p.add_argument("--write", action="store_true")
    p.add_argument("--no-agents-md", action="store_true", help="Do not write or return bundle-local AGENTS.md content")
    p.add_argument("--llms-txt", action="store_true", help="With --write, also write llms.txt at the repository root")
    p.add_argument("--registry", action="store_true", help="With --write, also write okf-registry.yaml at the repository root")
    p.set_defaults(func=cmd_generate_chatgpt_usage)

    p = sub.add_parser("mcp-diagnostics", help="Report the bundled okf-tools MCP configuration and manual probe command")
    p.set_defaults(func=cmd_mcp_diagnostics)

    p = sub.add_parser("plan", help="Build a parallel-authoring plan (concept ledger + shard assignment) from an inventory")
    p.add_argument("bundle", help="Bundle root where the plan is written (under <bundle>/.okf)")
    p.add_argument("--inventory", required=True, help="Concept inventory: JSON array file, CSV file, or '-' for JSON on stdin")
    p.add_argument("--shards", type=int, default=6, help="Number of parallel authoring shards (default: 6, matching Codex max_threads)")
    p.add_argument("--plan-dir", help="Override the plan directory (default: <bundle>/.okf)")
    p.add_argument("--strict", action="store_true", help="Treat inventory warnings as blocking plan issues")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("coverage", help="Audit planned concepts against files on disk; exits non-zero until the bundle is exhaustive")
    p.add_argument("bundle")
    p.add_argument("--plan-dir", help="Override the plan directory (default: <bundle>/.okf)")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--output", help="Write the report to a file as well as stdout")
    p.add_argument("--retry-csv", nargs="?", const="", default=None, help="Write failing plan rows to PATH, or to <bundle>/.okf/retry.csv when PATH is omitted")
    p.set_defaults(func=cmd_coverage)

    p = sub.add_parser("plan-status", help="Mark plan rows with a status (planned/in_progress/done)")
    p.add_argument("bundle")
    p.add_argument("--path", action="append", required=True, help="Concept path to update; can be repeated")
    p.add_argument("--status", choices=["planned", "in_progress", "done"], default="done")
    p.add_argument("--plan-dir", help="Override the plan directory (default: <bundle>/.okf)")
    p.set_defaults(func=cmd_plan_status)

    p = sub.add_parser("install-agents", help="Install the bundled Codex subagent definitions into .codex/agents")
    p.add_argument("--target", help="Target agents directory (default: <cwd>/.codex/agents)")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing agent files")
    p.set_defaults(func=cmd_install_agents)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
