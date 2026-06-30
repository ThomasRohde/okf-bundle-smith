#!/usr/bin/env python3
"""Attachment state and alias/path resolution for OKF consumer mode."""
from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re

from okf_context import bundle_overview, generate_chatgpt_usage, prepare_answer_context, freshness_report
from okf_git import attach_github_bundle, parse_github_bundle_url
from okf_index import build_concept_index, load_index, looks_like_bundle, save_index
from okf_retrieve import read_concept, related_concepts, search_concepts

STATE_VERSION = 1


def plugin_data_root() -> Path:
    explicit = os.environ.get("OKF_BUNDLE_SMITH_DATA_DIR")
    if explicit:
        return Path(explicit).resolve()
    plugin_data = os.environ.get("PLUGIN_DATA")
    if plugin_data:
        return Path(plugin_data).resolve() / "okf-consumer"
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".cache")
    return Path(base).resolve() / "okf-bundle-smith" / "okf-consumer"


def _state_path() -> Path:
    return plugin_data_root() / "state.json"


def _indexes_dir() -> Path:
    return plugin_data_root() / "indexes"


def _safe_alias(value: str) -> str:
    alias = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")
    return alias or "bundle"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _local_source(root: Path) -> dict[str, str]:
    resolved = str(root.resolve())
    return {"kind": "local", "url": resolved, "bundle_path": resolved}


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.is_file():
        return {"version": STATE_VERSION, "bundles": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("version", STATE_VERSION)
    data.setdefault("bundles", {})
    return data


def _save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _index_path(alias: str) -> Path:
    return _indexes_dir() / f"{_safe_alias(alias)}.json"


def _project_attachments_path(project_root: str | Path | None = None) -> Path:
    root = Path(project_root or Path.cwd()).resolve()
    return root / ".okf" / "attachments.yaml"


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(str(value), ensure_ascii=False)


def _read_project_attachments(project_root: str | Path | None = None) -> dict[str, Any]:
    path = _project_attachments_path(project_root)
    if not path.is_file():
        return {"version": 1, "bundles": {}}
    bundles: dict[str, dict[str, str]] = {}
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  ") and not line.startswith("    ") and line.rstrip().endswith(":"):
            current = line.strip()[:-1]
            bundles[current] = {}
            continue
        if current and line.startswith("    ") and ":" in line:
            key, raw = line.strip().split(":", 1)
            value = raw.strip().strip('"').strip("'")
            bundles[current][key] = value
    return {"version": 1, "bundles": bundles}


def _write_project_attachment(attachment: dict[str, Any], project_root: str | Path | None = None) -> None:
    path = _project_attachments_path(project_root)
    data = _read_project_attachments(project_root)
    data.setdefault("bundles", {})[attachment["alias"]] = {
        "kind": attachment.get("kind", "github"),
        "url": attachment.get("source_url", ""),
        "owner": attachment.get("owner", ""),
        "repo": attachment.get("repo", ""),
        "ref": attachment.get("requested_ref", ""),
        "path": attachment.get("bundle_path", ""),
        "mode": "read-only",
        "last_attached": attachment.get("fetched_at", ""),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["version: 1", "bundles:"]
    for alias, bundle in sorted(data["bundles"].items()):
        lines.append(f"  {alias}:")
        for key, value in bundle.items():
            lines.append(f"    {key}: {_yaml_scalar(value)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _remove_project_attachment(alias: str, project_root: str | Path | None = None) -> None:
    path = _project_attachments_path(project_root)
    data = _read_project_attachments(project_root)
    if alias not in data.get("bundles", {}):
        return
    del data["bundles"][alias]
    if not data["bundles"]:
        path.write_text("version: 1\nbundles: {}\n", encoding="utf-8")
        return
    lines = ["version: 1", "bundles:"]
    for name, bundle in sorted(data["bundles"].items()):
        lines.append(f"  {name}:")
        for key, value in bundle.items():
            lines.append(f"    {key}: {_yaml_scalar(value)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _attachment_from_index(alias: str, resolved: dict[str, Any], index: dict[str, Any], index_path: Path) -> dict[str, Any]:
    validation = index.get("validation", {})
    if validation.get("errors", 0):
        validation_status = "errors"
    elif validation.get("warnings", 0):
        validation_status = "warnings"
    else:
        validation_status = "ok"
    return {
        **resolved,
        "alias": alias,
        "status": "attached",
        "index_path": str(index_path),
        "concept_count": index["bundle"]["concept_count"],
        "validation_status": validation_status,
        "validation": {
            "errors": validation.get("errors", 0),
            "warnings": validation.get("warnings", 0),
        },
        "freshness": freshness_report(index),
    }


def attach_github_url(
    url: str,
    alias: str | None = None,
    ref: str | None = None,
    path: str | None = None,
    persist_project: bool = False,
    refresh: bool = False,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    parsed = parse_github_bundle_url(url)
    if ref is not None or path is not None:
        parsed = replace(parsed, ref=ref if ref is not None else parsed.ref, path=path if path is not None else parsed.path, tree_tail=None)
    bundle_alias = _safe_alias(alias or Path(parsed.path or parsed.repo).name)
    resolved = attach_github_bundle(parsed, plugin_data_root(), alias=bundle_alias, refresh=refresh)
    if not looks_like_bundle(resolved.local_path):
        raise ValueError("The selected path does not look like an OKF bundle. I found no Markdown concept files and no index.md.")

    source = {
        "kind": "github",
        "url": resolved.source_url,
        "owner": resolved.owner,
        "repo": resolved.repo,
        "requested_ref": resolved.requested_ref,
        "commit_sha": resolved.commit_sha,
        "bundle_path": resolved.bundle_path,
    }
    index = build_concept_index(resolved.local_path, source=source, alias=bundle_alias)
    index_path = save_index(index, _index_path(bundle_alias))
    attachment = _attachment_from_index(bundle_alias, asdict(resolved), index, index_path)
    state = _load_state()
    state["bundles"][bundle_alias] = attachment
    _save_state(state)
    if persist_project:
        _write_project_attachment(attachment, project_root)
    return attachment


def attach_local_bundle(
    path: str | Path,
    alias: str | None = None,
    persist_project: bool = False,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(path).resolve()
    if not looks_like_bundle(root):
        raise ValueError("The selected path does not look like an OKF bundle. I found no Markdown concept files and no index.md.")

    bundle_alias = _safe_alias(alias or root.name)
    source = _local_source(root)
    index = build_concept_index(root, source=source, alias=bundle_alias)
    index_path = save_index(index, _index_path(bundle_alias))
    resolved = {
        "kind": "local",
        "owner": None,
        "repo": None,
        "requested_ref": None,
        "commit_sha": None,
        "bundle_path": str(root),
        "local_path": str(root),
        "source_url": str(root),
        "fetched_at": _now_iso(),
    }
    attachment = _attachment_from_index(bundle_alias, resolved, index, index_path)
    state = _load_state()
    state["bundles"][bundle_alias] = attachment
    _save_state(state)
    if persist_project:
        _write_project_attachment(attachment, project_root)
    return attachment


def list_attached_bundles(scope: str = "all", project_root: str | Path | None = None) -> dict[str, Any]:
    bundles: list[dict[str, Any]] = []
    if scope in {"all", "plugin"}:
        for alias, item in sorted(_load_state().get("bundles", {}).items()):
            bundles.append({"scope": "plugin", **item, "alias": alias})
    if scope in {"all", "project"}:
        for alias, item in sorted(_read_project_attachments(project_root).get("bundles", {}).items()):
            bundles.append({"scope": "project", "alias": alias, **item})
    if scope not in {"all", "plugin", "project"}:
        raise ValueError("scope must be one of: all, plugin, project")
    return {"bundles": bundles}


def refresh_bundle(alias: str) -> dict[str, Any]:
    state = _load_state()
    if alias not in state.get("bundles", {}):
        raise KeyError(f"No attached OKF bundle alias found: {alias}")
    old = state["bundles"][alias]
    if old.get("kind") == "local":
        refreshed = attach_local_bundle(old["local_path"], alias=alias)
        return {
            "alias": alias,
            "old_commit_sha": None,
            "new_commit_sha": None,
            "changed": False,
            "concept_count": refreshed.get("concept_count"),
            "validation": refreshed.get("validation"),
            "freshness": refreshed.get("freshness"),
        }
    refreshed = attach_github_url(
        old["source_url"],
        alias=alias,
        ref=old.get("requested_ref"),
        path=old.get("bundle_path"),
        refresh=True,
    )
    return {
        "alias": alias,
        "old_commit_sha": old.get("commit_sha"),
        "new_commit_sha": refreshed.get("commit_sha"),
        "changed": old.get("commit_sha") != refreshed.get("commit_sha"),
        "concept_count": refreshed.get("concept_count"),
        "validation": refreshed.get("validation"),
    }


def detach_bundle(alias: str, project: bool = False, project_root: str | Path | None = None) -> dict[str, Any]:
    removed = False
    state = _load_state()
    if alias in state.get("bundles", {}):
        del state["bundles"][alias]
        _save_state(state)
        removed = True
    if project:
        _remove_project_attachment(alias, project_root)
        removed = True
    return {"alias": alias, "detached": removed}


def resolve_bundle_index(reference: str, project_root: str | Path | None = None) -> dict[str, Any]:
    candidate = Path(reference)
    if candidate.exists():
        return build_concept_index(candidate, source=_local_source(candidate), alias=candidate.name)

    state = _load_state()
    attached = state.get("bundles", {}).get(reference)
    if attached:
        index_path = Path(attached.get("index_path", ""))
        if index_path.is_file():
            return load_index(index_path)
        index = build_concept_index(
            attached["local_path"],
            source={
                "kind": attached.get("kind"),
                "url": attached.get("source_url"),
                "owner": attached.get("owner"),
                "repo": attached.get("repo"),
                "requested_ref": attached.get("requested_ref"),
                "commit_sha": attached.get("commit_sha"),
                "bundle_path": attached.get("bundle_path"),
            },
            alias=reference,
        )
        save_index(index, _index_path(reference))
        return index

    project = _read_project_attachments(project_root).get("bundles", {}).get(reference)
    if project and project.get("url"):
        if project.get("kind") == "local":
            attach_local_bundle(project["url"], alias=reference)
        else:
            attach_github_url(project["url"], alias=reference, ref=project.get("ref") or None, path=project.get("path") or None)
        return resolve_bundle_index(reference, project_root)

    raise KeyError(f"Could not resolve OKF bundle alias or path: {reference}")


def search_bundle(reference: str, query: str, filters: dict[str, Any] | None = None, max_results: int = 10) -> dict[str, Any]:
    index = resolve_bundle_index(reference)
    return {"bundle": index["bundle"]["alias"], "query": query, "results": search_concepts(index, query, filters, max_results)}


def read_bundle_concept(reference: str, concept_id: str, include_neighbors: bool = False) -> dict[str, Any]:
    index = resolve_bundle_index(reference)
    return {"bundle": index["bundle"]["alias"], "concept": read_concept(index, concept_id, include_neighbors)}


def related_bundle_concepts(reference: str, concept_id: str, depth: int = 1, max_results: int = 20) -> dict[str, Any]:
    index = resolve_bundle_index(reference)
    payload = related_concepts(index, concept_id, depth, max_results)
    return {"bundle": index["bundle"]["alias"], **payload}


def bundle_context(reference: str, question: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    index = resolve_bundle_index(reference)
    return prepare_answer_context(index, question, options)


def overview_bundle(reference: str) -> dict[str, Any]:
    index = resolve_bundle_index(reference)
    return bundle_overview(index)


def bundle_freshness(reference: str) -> dict[str, Any]:
    index = resolve_bundle_index(reference)
    return {"bundle": index["bundle"]["alias"], **freshness_report(index)}


def chatgpt_usage(bundle_path: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    return generate_chatgpt_usage(bundle_path, options)


def mcp_diagnostics() -> dict[str, Any]:
    plugin_root = Path(__file__).resolve().parents[1]
    mcp_path = plugin_root / ".mcp.json"
    mcp_config = json.loads(mcp_path.read_text(encoding="utf-8")) if mcp_path.is_file() else {}
    server = (mcp_config.get("mcpServers") or {}).get("okf-tools") or {}
    return {
        "plugin_root": str(plugin_root),
        "mcp_config_path": str(mcp_path),
        "server_name": "okf-tools",
        "declared": bool(server),
        "command": server.get("command"),
        "args": server.get("args", []),
        "env": server.get("env", {}),
        "manual_probe": {
            "powershell": (
                "'{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}' | "
                f"{server.get('command', 'python')} {str(plugin_root / 'tools' / 'okf_mcp_server.py')}"
            )
        },
        "host_troubleshooting": [
            "Confirm the plugin is installed and enabled.",
            "Start a new Codex thread after reinstalling or cache-busting a local plugin.",
            "Restart the Codex app if skills load but plugin MCP tools are absent.",
            "If plugin-relative paths are not resolved by the host, configure an absolute path to tools/okf_mcp_server.py.",
        ],
    }
