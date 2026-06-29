#!/usr/bin/env python3
"""Search and read OKF consumer indexes."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from okf_core import parse_frontmatter
from okf_index import assert_safe_bundle_tree

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def _tokens(value: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(value or "")]


def _concept_map(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {concept["concept_id"]: concept for concept in index.get("concepts", [])}


def _normalize_concept_id(value: str) -> str:
    candidate = value.replace("\\", "/").strip().lstrip("/")
    return candidate[:-3] if candidate.endswith(".md") else candidate


def _find_concept(index: dict[str, Any], concept_id: str) -> dict[str, Any]:
    candidate = _normalize_concept_id(concept_id)
    for concept in index.get("concepts", []):
        if concept["concept_id"] == candidate:
            return concept
        if concept["path"] == candidate or concept["path"] == f"{candidate}.md":
            return concept
    raise KeyError(f"Unknown OKF concept: {concept_id}")


def _read_concept_file(index: dict[str, Any], concept: dict[str, Any]) -> tuple[dict[str, Any], str]:
    root = assert_safe_bundle_tree(index["bundle"]["local_path"])
    path = (root / concept["path"]).resolve()
    path.relative_to(root)
    text = path.read_text(encoding="utf-8")
    frontmatter, body, _raw, parse_error = parse_frontmatter(text)
    if parse_error:
        raise ValueError(f"Could not parse concept frontmatter for {concept['path']}: {parse_error}")
    return frontmatter, body


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _passes_filters(concept: dict[str, Any], filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    wanted_type = filters.get("type")
    if wanted_type and str(concept.get("type", "")).lower() != str(wanted_type).lower():
        return False
    wanted_tags = filters.get("tags") or []
    if isinstance(wanted_tags, str):
        wanted_tags = [wanted_tags]
    existing = {str(tag).lower() for tag in concept.get("tags", [])}
    return all(str(tag).lower() in existing for tag in wanted_tags)


def _score_concept(concept: dict[str, Any], query: str, query_tokens: list[str]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    q = query.strip().lower()
    concept_id = str(concept.get("concept_id", "")).lower()
    title = str(concept.get("title", "")).lower()
    ctype = str(concept.get("type", "")).lower()
    tags = [str(tag).lower() for tag in concept.get("tags", [])]
    description = str(concept.get("description", "")).lower()
    headings = " ".join(str(item).lower() for item in concept.get("headings", []))
    body = str(concept.get("body_excerpt", "")).lower()

    if q and q == concept_id:
        score += 100
        reasons.append("concept_id")
    elif q and q in concept_id:
        score += 35
        reasons.append("concept_id")
    if q and q == title:
        score += 80
        reasons.append("title")
    elif q and q in title:
        score += 28
        reasons.append("title")
    if q and q == ctype:
        score += 18
        reasons.append("type")
    if q and q in tags:
        score += 24
        reasons.append("tag")

    title_tokens = set(_tokens(title))
    tag_tokens = set(token for tag in tags for token in _tokens(tag))
    type_tokens = set(_tokens(ctype))
    description_tokens = set(_tokens(description))
    heading_tokens = set(_tokens(headings))
    body_tokens = _tokens(body)
    body_counts: dict[str, int] = {}
    for token in body_tokens:
        body_counts[token] = body_counts.get(token, 0) + 1

    for token in query_tokens:
        if token in title_tokens:
            score += 10
            reasons.append("title")
        if token in tag_tokens:
            score += 8
            reasons.append("tag")
        if token in type_tokens:
            score += 6
            reasons.append("type")
        if token in description_tokens:
            score += 5
            reasons.append("description")
        if token in heading_tokens:
            score += 4
            reasons.append("heading")
        if token in body_counts:
            score += min(body_counts[token], 5)
            reasons.append("body")

    return score, sorted(set(reasons))


def search_concepts(
    index: dict[str, Any],
    query: str,
    filters: dict[str, Any] | None = None,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    scores: dict[str, tuple[float, list[str]]] = {}

    for concept in index.get("concepts", []):
        if not _passes_filters(concept, filters):
            continue
        score, reasons = _score_concept(concept, query, query_tokens)
        if score > 0:
            scores[concept["concept_id"]] = (score, reasons)

    by_id = _concept_map(index)
    for concept_id, (score, reasons) in list(scores.items()):
        concept = by_id.get(concept_id)
        if not concept:
            continue
        for neighbor in set(concept.get("outlinks", []) + concept.get("inlinks", [])):
            if neighbor in by_id and neighbor not in scores:
                scores[neighbor] = (score * 0.12, ["link-neighborhood"])

    ranked = sorted(scores.items(), key=lambda item: (-item[1][0], item[0]))[: max(0, max_results)]
    results: list[dict[str, Any]] = []
    for concept_id, (score, reasons) in ranked:
        concept = by_id[concept_id]
        results.append(
            {
                "concept_id": concept_id,
                "title": concept.get("title"),
                "type": concept.get("type"),
                "path": concept.get("path"),
                "score": round(score, 3),
                "reason": ", ".join(reasons),
                "excerpt": concept.get("body_excerpt") or concept.get("description") or "",
            }
        )
    return results


def read_concept(index: dict[str, Any], concept_id: str, include_neighbors: bool = False) -> dict[str, Any]:
    concept = _find_concept(index, concept_id)
    frontmatter, body = _read_concept_file(index, concept)
    payload = {
        "concept_id": concept["concept_id"],
        "title": concept.get("title"),
        "type": concept.get("type"),
        "path": concept.get("path"),
        "frontmatter": _json_safe(frontmatter),
        "body": body,
        "outlinks": concept.get("outlinks", []),
        "inlinks": concept.get("inlinks", []),
        "citations": concept.get("citations", []),
    }
    if include_neighbors:
        by_id = _concept_map(index)
        neighbor_ids = sorted(set(payload["outlinks"] + payload["inlinks"]))
        payload["neighbors"] = [
            {
                "concept_id": item,
                "title": by_id[item].get("title"),
                "type": by_id[item].get("type"),
                "path": by_id[item].get("path"),
            }
            for item in neighbor_ids
            if item in by_id
        ]
    return payload


def related_concepts(
    index: dict[str, Any],
    concept_id: str,
    depth: int = 1,
    max_results: int = 20,
) -> dict[str, Any]:
    start = _find_concept(index, concept_id)
    by_id = _concept_map(index)
    start_id = start["concept_id"]
    queue: list[tuple[str, int]] = [(start_id, 0)]
    seen = {start_id}
    related: list[dict[str, Any]] = []

    while queue and len(related) < max_results:
        current_id, current_depth = queue.pop(0)
        if current_depth >= depth:
            continue
        current = by_id[current_id]
        neighbors: list[tuple[str, str]] = []
        neighbors.extend((item, "outlink") for item in current.get("outlinks", []))
        neighbors.extend((item, "inlink") for item in current.get("inlinks", []))

        current_dir = str(Path(current.get("path", "")).parent)
        if current_depth == 0:
            for item in by_id.values():
                if item["concept_id"] != current_id and str(Path(item.get("path", "")).parent) == current_dir:
                    neighbors.append((item["concept_id"], "directory"))

        for neighbor_id, relationship in sorted(neighbors, key=lambda item: (item[1], item[0])):
            if neighbor_id in seen or neighbor_id not in by_id:
                continue
            seen.add(neighbor_id)
            distance = current_depth + 1
            related.append(
                {
                    "concept_id": neighbor_id,
                    "title": by_id[neighbor_id].get("title"),
                    "type": by_id[neighbor_id].get("type"),
                    "path": by_id[neighbor_id].get("path"),
                    "relationship": relationship,
                    "distance": distance,
                }
            )
            queue.append((neighbor_id, distance))
            if len(related) >= max_results:
                break

    return {"start": start_id, "related": related}
