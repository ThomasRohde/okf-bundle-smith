#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from okf_core import (
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
    )
    for path in written:
        print(path)
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
    p.set_defaults(func=cmd_new)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
