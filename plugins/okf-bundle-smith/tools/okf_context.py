#!/usr/bin/env python3
"""Context-pack and helper-file generation for OKF consumer mode."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import re

from okf_index import build_concept_index
from okf_retrieve import read_concept, related_concepts, search_concepts

LOG_DATE_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _trim(value: str, max_chars: int) -> str:
    text = value or ""
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)].rstrip() + "..."


def freshness_report(index: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    timestamps: list[datetime] = []
    missing = 0
    for concept in index.get("concepts", []):
        parsed = _parse_datetime(str(concept.get("timestamp") or ""))
        if parsed:
            timestamps.append(parsed)
        else:
            missing += 1

    log_body = ((index.get("entrypoints") or {}).get("log") or {}).get("body") or ""
    log_dates = LOG_DATE_RE.findall(log_body)
    latest_log_entry = max(log_dates) if log_dates else None

    older_counts: dict[str, int] = {}
    for days in (90, 180, 365):
        older_counts[str(days)] = sum(1 for ts in timestamps if (now - ts).days > days)

    warnings: list[str] = []
    if not latest_log_entry:
        warnings.append("No dated root log entry found.")
    if missing:
        warnings.append(f"{missing} concept(s) have no parseable timestamp.")
    if older_counts["180"]:
        warnings.append(f"{older_counts['180']} concept(s) are older than 180 days.")

    return {
        "latest_log_entry": latest_log_entry,
        "oldest_concept_timestamp": min((ts.isoformat() for ts in timestamps), default=None),
        "newest_concept_timestamp": max((ts.isoformat() for ts in timestamps), default=None),
        "concepts_without_timestamp": missing,
        "concepts_older_than_days": older_counts,
        "warnings": warnings,
    }


def _answer_instructions(mode: str) -> list[str]:
    if mode == "hybrid":
        return [
            "Start from retrieved OKF concepts.",
            "Cite concept IDs in brackets after bundle-grounded claims.",
            "Label inference and external knowledge explicitly.",
            "Call out conflicts between the bundle and other evidence.",
        ]
    return [
        "Answer only from the retrieved OKF concepts.",
        "Cite concept IDs in brackets after material claims.",
        "Say when the bundle does not contain enough information.",
        "Report freshness limitations when relevant.",
    ]


def prepare_answer_context(
    index: dict[str, Any],
    question: str,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    options = dict(options or {})
    mode = options.get("mode", "strict")
    if mode not in {"strict", "hybrid"}:
        raise ValueError("mode must be 'strict' or 'hybrid'")

    validation = index.get("validation") or {}
    if mode == "strict" and validation.get("errors", 0):
        return {
            "bundle": index["bundle"]["alias"],
            "mode": mode,
            "blocked": True,
            "block_reason": "Strict mode is blocked because the bundle has validation errors.",
            "validation": validation,
            "answer_instructions": _answer_instructions(mode),
        }

    max_concepts = int(options.get("max_concepts", 8))
    max_chars = int(options.get("max_chars_per_concept", 4000))
    link_depth = int(options.get("link_depth", 1))
    include_index = bool(options.get("include_index", True))
    include_log = bool(options.get("include_log", True))

    results = search_concepts(index, question, max_results=max_concepts)
    selected_ids: list[str] = []
    for result in results:
        selected_ids.append(result["concept_id"])
        if link_depth > 0:
            for related in related_concepts(index, result["concept_id"], depth=link_depth, max_results=max_concepts).get("related", []):
                selected_ids.append(related["concept_id"])

    deduped: list[str] = []
    for concept_id in selected_ids:
        if concept_id not in deduped:
            deduped.append(concept_id)
    deduped = deduped[:max_concepts]

    concepts: list[dict[str, Any]] = []
    follow_up: list[str] = []
    for concept_id in deduped:
        concept = read_concept(index, concept_id)
        concepts.append(
            {
                "citation_id": concept["concept_id"],
                "title": concept.get("title"),
                "type": concept.get("type"),
                "path": concept.get("path"),
                "excerpt": _trim(concept.get("body", ""), max_chars),
                "outlinks": concept.get("outlinks", []),
                "inlinks": concept.get("inlinks", []),
                "citations": concept.get("citations", []),
            }
        )
        follow_up.extend(concept.get("outlinks", []))
        follow_up.extend(concept.get("inlinks", []))

    entrypoints: dict[str, Any] = {}
    if include_index:
        root_index = ((index.get("entrypoints") or {}).get("index") or {})
        if root_index:
            entrypoints["index"] = {"path": root_index.get("path"), "excerpt": _trim(root_index.get("body", ""), 2000)}
    if include_log:
        root_log = ((index.get("entrypoints") or {}).get("log") or {})
        if root_log:
            entrypoints["log"] = {"path": root_log.get("path"), "excerpt": _trim(root_log.get("body", ""), 2000)}

    follow_up_candidates = [item for item in sorted(set(follow_up)) if item not in deduped]
    return {
        "bundle": index["bundle"]["alias"],
        "mode": mode,
        "blocked": False,
        "source": index.get("source", {}),
        "validation": validation,
        "freshness": freshness_report(index),
        "answer_instructions": _answer_instructions(mode),
        "entrypoints": entrypoints,
        "search_results": results,
        "concepts": concepts,
        "follow_up_candidates": follow_up_candidates[:max_concepts],
    }


def _bundle_relative_path(bundle_path: Path, repo_root: Path) -> str:
    try:
        return bundle_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return bundle_path.name


def _default_repo_root(bundle_path: Path) -> Path:
    if bundle_path.parent.name in {"bundles", "okf"}:
        return bundle_path.parent.parent
    return bundle_path.parent


def generate_chatgpt_usage(bundle_path: str | Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = dict(options or {})
    root = Path(bundle_path).resolve()
    index = build_concept_index(root, source={"kind": "local", "url": str(root), "bundle_path": "."})
    repo_root = Path(options.get("repo_root") or _default_repo_root(root)).resolve()
    bundle_rel = _bundle_relative_path(root, repo_root)
    repo_name = options.get("repo_name") or options.get("repo") or repo_root.name
    write_files = bool(options.get("write_files", False))
    include_llms = bool(options.get("include_llms_txt", True))
    include_registry = bool(options.get("include_registry", True))

    chatgpt = f"""# ChatGPT instructions for this OKF bundle

This directory is an Open Knowledge Format bundle.

## Entry points

Start with:

- `{bundle_rel}/index.md`
- `{bundle_rel}/log.md`

Then follow Markdown links to relevant concept files.

## Answering rules

- Prefer bundle content over general model knowledge.
- Cite concept paths such as `[systems/payment-router]`.
- Distinguish direct bundle facts from inference.
- Report if the bundle is stale, incomplete, or missing relevant concepts.
- Use external knowledge only when explicitly requested, and label it.

## Suggested prompt

Use the GitHub repo `{repo_name}` as an OKF bundle source.
Read `{bundle_rel}/index.md` and `{bundle_rel}/log.md` first.
Then answer from the bundle and cite concept paths.
"""

    llms = f"""# OKF bundle repository

This repository contains Open Knowledge Format bundles for agent consumption.

## Bundles

- {index['bundle']['title']}: {bundle_rel}/index.md

## Usage

When answering questions about a bundle, read its index.md and log.md first, then follow internal Markdown links. Cite concept paths.
"""

    registry = f"""version: 1
bundles:
  - id: {root.name}
    title: {index['bundle']['title']}
    path: {bundle_rel}
    chatgpt_instructions: {bundle_rel}/CHATGPT.md
    index: {bundle_rel}/index.md
    log: {bundle_rel}/log.md
"""

    created: list[str] = []
    if write_files:
        chatgpt_path = root / "CHATGPT.md"
        chatgpt_path.write_text(chatgpt, encoding="utf-8")
        created.append(str(chatgpt_path))
        if include_llms:
            llms_path = repo_root / "llms.txt"
            llms_path.write_text(llms, encoding="utf-8")
            created.append(str(llms_path))
        if include_registry:
            registry_path = repo_root / "okf-registry.yaml"
            registry_path.write_text(registry, encoding="utf-8")
            created.append(str(registry_path))

    return {
        "created": created,
        "bundle_path": str(root),
        "repo_root": str(repo_root),
        "chatgpt_md": chatgpt,
        "llms_txt": llms if include_llms else None,
        "okf_registry_yaml": registry if include_registry else None,
        "prompt_example": (
            f"Use the GitHub repo {repo_name}. Use the OKF bundle under {bundle_rel}. "
            "Read index.md and log.md first. Answer from the bundle and cite concept paths."
        ),
    }
