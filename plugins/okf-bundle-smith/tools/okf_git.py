#!/usr/bin/env python3
"""GitHub bundle URL parsing and sparse checkout helpers for OKF consumer mode."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import hashlib
import re
import subprocess


@dataclass(frozen=True)
class GitHubBundleRef:
    owner: str
    repo: str
    ref: str | None
    path: str | None
    url: str
    host: str = "github.com"
    tree_tail: str | None = None
    is_blob: bool = False


@dataclass(frozen=True)
class ResolvedBundleRef:
    alias: str
    kind: str
    owner: str | None
    repo: str | None
    requested_ref: str | None
    commit_sha: str | None
    bundle_path: str
    local_path: str
    source_url: str
    fetched_at: str
    validation_status: str


def _strip_repo_suffix(value: str) -> str:
    return value[:-4] if value.endswith(".git") else value


def _clean_path(value: str | None) -> str | None:
    if value in (None, "", "."):
        return None
    path = value.replace("\\", "/").strip("/")
    if path.endswith("/index.md"):
        path = path[: -len("/index.md")]
    elif path == "index.md":
        path = ""
    return path or None


def parse_github_bundle_url(url: str) -> GitHubBundleRef:
    raw = url.strip()
    ssh_match = re.fullmatch(r"git@([^:]+):([^/]+)/(.+?)(?:\.git)?", raw)
    if ssh_match:
        host, owner, repo = ssh_match.groups()
        return GitHubBundleRef(owner=owner, repo=_strip_repo_suffix(repo), ref=None, path=None, url=raw, host=host)

    shorthand_match = re.fullmatch(r"([^/\s]+)/([^/\s]+)//([^?\s]+)(?:\?(.*))?", raw)
    if shorthand_match:
        owner, repo, path, query = shorthand_match.groups()
        ref = (parse_qs(query or "").get("ref") or [None])[0]
        return GitHubBundleRef(
            owner=owner,
            repo=_strip_repo_suffix(repo),
            ref=ref,
            path=_clean_path(path),
            url=raw,
        )

    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Could not parse this as a supported GitHub bundle URL.")
    host = parsed.netloc.lower()
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub URL must include owner and repository.")
    owner = parts[0]
    repo = _strip_repo_suffix(parts[1])

    if len(parts) == 2:
        return GitHubBundleRef(owner=owner, repo=repo, ref=None, path=None, url=raw, host=host)
    if len(parts) >= 4 and parts[2] in {"tree", "blob"}:
        tail = "/".join(parts[3:])
        first = parts[3] if len(parts) > 3 else None
        rest = "/".join(parts[4:]) if len(parts) > 4 else None
        return GitHubBundleRef(
            owner=owner,
            repo=repo,
            ref=first,
            path=_clean_path(rest),
            url=raw,
            host=host,
            tree_tail=tail,
            is_blob=parts[2] == "blob",
        )
    raise ValueError("GitHub URL must point to a repository, tree, or blob path.")


def clone_url(ref: GitHubBundleRef) -> str:
    if ref.url.startswith("git@"):
        return f"git@{ref.host}:{ref.owner}/{ref.repo}.git"
    return f"https://{ref.host}/{ref.owner}/{ref.repo}.git"


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise RuntimeError(message)
    return completed.stdout.strip()


def _remote_refs(ref: GitHubBundleRef) -> set[str]:
    output = _run_git(["ls-remote", "--heads", "--tags", clone_url(ref)])
    refs: set[str] = set()
    for line in output.splitlines():
        if not line.strip():
            continue
        _sha, remote_ref = line.split(None, 1)
        if remote_ref.startswith("refs/heads/"):
            refs.add(remote_ref[len("refs/heads/") :])
        elif remote_ref.startswith("refs/tags/"):
            refs.add(remote_ref[len("refs/tags/") :].removesuffix("^{}"))
    return refs


def _default_branch(ref: GitHubBundleRef) -> str:
    output = _run_git(["ls-remote", "--symref", clone_url(ref), "HEAD"])
    for line in output.splitlines():
        if line.startswith("ref: refs/heads/") and line.endswith("\tHEAD"):
            return line[len("ref: refs/heads/") : -len("\tHEAD")]
    return "HEAD"


def resolve_github_ref(ref: GitHubBundleRef, remote_refs: set[str] | None = None) -> GitHubBundleRef:
    if ref.tree_tail:
        refs = remote_refs if remote_refs is not None else _remote_refs(ref)
        parts = ref.tree_tail.split("/")
        for split_at in range(len(parts), 0, -1):
            candidate_ref = "/".join(parts[:split_at])
            if candidate_ref in refs:
                candidate_path = _clean_path("/".join(parts[split_at:]))
                if ref.is_blob:
                    candidate_path = _clean_path(candidate_path)
                return replace(ref, ref=candidate_ref, path=candidate_path, tree_tail=None)
        fallback_ref = parts[0]
        fallback_path = _clean_path("/".join(parts[1:]))
        return replace(ref, ref=fallback_ref, path=fallback_path, tree_tail=None)
    if ref.ref:
        return replace(ref, path=_clean_path(ref.path))
    return replace(ref, ref=_default_branch(ref), path=_clean_path(ref.path))


def _cache_dir(cache_root: Path, ref: GitHubBundleRef) -> Path:
    key = f"{ref.host}/{ref.owner}/{ref.repo}/{ref.ref or 'HEAD'}/{ref.path or '.'}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return cache_root / "github-cache" / ref.owner / ref.repo / digest


def attach_github_bundle(
    ref: GitHubBundleRef,
    cache_root: str | Path,
    alias: str | None = None,
    refresh: bool = False,
) -> ResolvedBundleRef:
    resolved = resolve_github_ref(ref)
    cache = _cache_dir(Path(cache_root).resolve(), resolved)
    cache.parent.mkdir(parents=True, exist_ok=True)
    repo_url = clone_url(resolved)

    if refresh and cache.exists():
        _run_git(["-C", str(cache), "fetch", "--depth", "1", "origin", resolved.ref or "HEAD"])
    elif not (cache / ".git").is_dir():
        _run_git(["clone", "--filter=blob:none", "--no-checkout", repo_url, str(cache)])
        _run_git(["-C", str(cache), "sparse-checkout", "init", "--cone"])
        if resolved.path:
            _run_git(["-C", str(cache), "sparse-checkout", "set", resolved.path])
        _run_git(["-C", str(cache), "fetch", "--depth", "1", "origin", resolved.ref or "HEAD"])
    else:
        if resolved.path:
            _run_git(["-C", str(cache), "sparse-checkout", "set", resolved.path])
        _run_git(["-C", str(cache), "fetch", "--depth", "1", "origin", resolved.ref or "HEAD"])

    _run_git(["-C", str(cache), "checkout", "FETCH_HEAD"])
    commit_sha = _run_git(["-C", str(cache), "rev-parse", "HEAD"])
    bundle_path = resolved.path or "."
    local_path = cache / bundle_path
    if not local_path.exists():
        raise ValueError(f"The path exists in the reference model but was not checked out: {bundle_path}")

    from datetime import datetime, timezone

    return ResolvedBundleRef(
        alias=alias or Path(bundle_path).name or resolved.repo,
        kind="github",
        owner=resolved.owner,
        repo=resolved.repo,
        requested_ref=resolved.ref,
        commit_sha=commit_sha,
        bundle_path=bundle_path,
        local_path=str(local_path.resolve()),
        source_url=resolved.url,
        fetched_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        validation_status="unknown",
    )
