#!/usr/bin/env python3
"""Build and persist deterministic lexical indexes for OKF bundles."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse
import hashlib
import json
import os
import re

from okf_core import MD_LINK_RE, scan_bundle

SCHEMA_VERSION = "okf-consumer-index/v1"
HELPER_MARKDOWN_FILES = {"CHATGPT.md", "AGENTS.md"}
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
CITATIONS_HEADING_RE = re.compile(r"^#\s+Citations\s*$", re.IGNORECASE | re.MULTILINE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_rel(path: Path, root: Path) -> str:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if not _is_relative_to(resolved, root_resolved):
        raise ValueError(f"Path escapes bundle root: {path}")
    return resolved.relative_to(root_resolved).as_posix()


def assert_safe_bundle_tree(root: str | Path) -> Path:
    """Return a resolved bundle path after checking symlink escape cases."""
    root_path = Path(root).resolve()
    if not root_path.exists():
        raise ValueError(f"Bundle path does not exist: {root_path}")
    if not root_path.is_dir():
        raise ValueError(f"Bundle path is not a directory: {root_path}")

    for path in root_path.rglob("*"):
        if path.is_symlink() and not _is_relative_to(path.resolve(), root_path):
            rel = path.relative_to(root_path).as_posix()
            raise ValueError(f"Symlink escapes bundle root: {rel}")
    return root_path


def _normalize_tags(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _body_excerpt(body: str, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", body).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _headings(body: str) -> list[str]:
    return [match.group(2).strip() for match in HEADING_RE.finditer(body)]


def _iter_internal_links(body: str) -> Iterable[str]:
    for _text, target in MD_LINK_RE.findall(body):
        target = target.strip()
        if not target or target.startswith("#"):
            continue
        parsed = urlparse(target)
        if parsed.scheme or target.startswith("mailto:"):
            continue
        clean = target.split("#", 1)[0].split("?", 1)[0].strip()
        if clean:
            yield clean


def _resolve_link(source_rel: str, target: str, root: Path) -> Path:
    if target.startswith("/"):
        return (root / target.lstrip("/")).resolve()
    return (root / Path(source_rel).parent / target).resolve()


def _extract_citations(body: str) -> list[dict[str, str]]:
    match = CITATIONS_HEADING_RE.search(body)
    if not match:
        return []
    section = body[match.end() :]
    next_heading = re.search(r"^#\s+", section, re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]

    citations: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for label, url in MD_LINK_RE.findall(section):
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"}:
            continue
        item = (label.strip(), url.strip())
        if item in seen:
            continue
        seen.add(item)
        citations.append({"label": item[0], "url": item[1]})
    return citations


def _read_optional(path: Path, root: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    return {"path": _safe_rel(path, root), "body": path.read_text(encoding="utf-8")}


def build_concept_index(
    bundle_path: str | Path,
    source: dict[str, Any] | None = None,
    alias: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic lexical index for a local OKF bundle."""
    root = assert_safe_bundle_tree(bundle_path)
    report = scan_bundle(root)
    source_payload = dict(source or {})
    bundle_alias = alias or source_payload.get("alias") or root.name

    rel_by_path = {concept.path.resolve(): concept.rel for concept in report.concepts}
    concepts: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}

    for concept in report.concepts:
        rel = _safe_rel(concept.path, root)
        if Path(rel).name in HELPER_MARKDOWN_FILES:
            continue
        concept_id = concept.concept_id
        tags = _normalize_tags(concept.frontmatter.get("tags"))
        outlinks: list[str] = []
        for target in _iter_internal_links(concept.body):
            target_path = _resolve_link(concept.rel, target, root)
            target_rel = rel_by_path.get(target_path)
            if target_rel and Path(target_rel).name not in HELPER_MARKDOWN_FILES:
                outlinks.append(target_rel[:-3] if target_rel.endswith(".md") else target_rel)

        body_hash = "sha256:" + hashlib.sha256(concept.body.encode("utf-8")).hexdigest()
        item = {
            "concept_id": concept_id,
            "path": rel,
            "title": concept.frontmatter.get("title") or Path(rel).stem.replace("-", " ").title(),
            "type": concept.frontmatter.get("type"),
            "description": concept.frontmatter.get("description") or "",
            "tags": tags,
            "timestamp": str(concept.frontmatter.get("timestamp") or ""),
            "headings": _headings(concept.body),
            "outlinks": sorted(set(outlinks)),
            "inlinks": [],
            "citations": _extract_citations(concept.body),
            "body_hash": body_hash,
            "body_excerpt": _body_excerpt(concept.body),
        }
        concepts.append(item)
        by_id[concept_id] = item

    for concept in concepts:
        for target in concept["outlinks"]:
            if target in by_id:
                by_id[target].setdefault("inlinks", []).append(concept["concept_id"])
    for concept in concepts:
        concept["inlinks"] = sorted(set(concept.get("inlinks", [])))

    root_index = _read_optional(root / "index.md", root)
    root_log = _read_optional(root / "log.md", root)
    validation = report.to_dict()
    validation_summary = {
        "errors": validation["error_count"],
        "warnings": validation["warning_count"],
        "issues": validation["issues"],
    }
    title = root_index["body"].splitlines()[0].lstrip("#").strip() if root_index and root_index["body"].strip() else root.name

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "source": source_payload or {"kind": "local", "url": str(root), "bundle_path": "."},
        "bundle": {
            "alias": bundle_alias,
            "local_path": str(root),
            "title": title,
            "has_index": root_index is not None,
            "has_log": root_log is not None,
            "concept_count": len(concepts),
        },
        "validation": validation_summary,
        "entrypoints": {
            "index": root_index,
            "log": root_log,
        },
        "concepts": sorted(concepts, key=lambda item: item["concept_id"]),
    }


def save_index(index: dict[str, Any], index_path: str | Path) -> Path:
    path = Path(index_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_index(index_path: str | Path) -> dict[str, Any]:
    path = Path(index_path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported OKF consumer index schema: {data.get('schema_version')}")
    return data


def looks_like_bundle(path: str | Path) -> bool:
    root = Path(path)
    if not root.is_dir():
        return False
    markdown = [p for p in root.rglob("*.md") if p.name not in HELPER_MARKDOWN_FILES]
    return bool(markdown or (root / "index.md").is_file())


def default_index_path(bundle_path: str | Path, output_dir: str | Path | None = None) -> Path:
    root = Path(bundle_path).resolve()
    directory = Path(output_dir).resolve() if output_dir else root / ".okf"
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", root.name).strip("-") or "bundle"
    return directory / f"{safe_name}.okf-index.json"
