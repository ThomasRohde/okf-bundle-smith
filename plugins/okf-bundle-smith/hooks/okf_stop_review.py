#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(PLUGIN_ROOT / "tools"))

from okf_core import scan_bundle  # noqa: E402


def _looks_like_okf_bundle(path: Path) -> bool:
    if (path / "index.md").exists() or (path / "log.md").exists():
        return any(p.name not in {"index.md", "log.md"} for p in path.rglob("*.md"))
    for md in list(path.rglob("*.md"))[:50]:
        try:
            text = md.read_text(encoding="utf-8")[:500]
        except Exception:
            continue
        if text.startswith("---") and "type:" in text:
            return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    if payload.get("stop_hook_active"):
        print(json.dumps({"continue": True}))
        return 0

    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    candidates = []
    if _looks_like_okf_bundle(cwd):
        candidates.append(cwd)
    for child in cwd.iterdir() if cwd.exists() and cwd.is_dir() else []:
        if child.is_dir() and _looks_like_okf_bundle(child):
            candidates.append(child)

    if not candidates:
        print(json.dumps({"continue": True}))
        return 0

    blocking = []
    for candidate in candidates[:5]:
        report = scan_bundle(candidate)
        if report.errors:
            blocking.append(f"{candidate}: {len(report.errors)} OKF conformance error(s), {len(report.warnings)} warning(s)")

    if blocking:
        reason = (
            "Before finalizing, repair OKF conformance errors found by OKF Bundle Smith:\n"
            + "\n".join(f"- {item}" for item in blocking)
            + "\nRun the validator, fix missing/malformed frontmatter and required `type` fields, then re-check."
        )
        print(json.dumps({"decision": "block", "reason": reason}))
    else:
        print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
