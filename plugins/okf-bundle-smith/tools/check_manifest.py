#!/usr/bin/env python3
"""Self-contained sanity check for the plugin manifest, skills, and assets.

This is a lightweight mirror of the external Codex plugin validator so CI can run
without it. It does not replace the official validator; it catches the common
ways the manifest, skills, or referenced assets drift out of sync.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+].*)?$")


def check(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        return ["missing .codex-plugin/plugin.json"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"plugin.json is not valid JSON: {exc}"]

    for field in ("name", "version", "description"):
        if not str(manifest.get(field, "")).strip():
            errors.append(f"plugin.json missing non-empty `{field}`")
    if not SEMVER_RE.match(str(manifest.get("version", ""))):
        errors.append("plugin.json `version` must be semver")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin.json `interface` must be an object")
        interface = {}
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        if not str(interface.get(field, "")).strip():
            errors.append(f"plugin.json interface missing `{field}`")
    if "defaultPrompt" not in interface and "default_prompt" not in interface:
        errors.append("plugin.json interface missing `defaultPrompt`")

    # Referenced assets must exist inside the archive.
    for field in ("logo", "logoDark", "composerIcon"):
        rel = interface.get(field)
        if rel and not (root / rel).is_file():
            errors.append(f"interface.{field} points to missing file: {rel}")

    # mcpServers either inline or via .mcp.json.
    mcp = manifest.get("mcpServers")
    if isinstance(mcp, str):
        mcp_path = root / mcp
        if not mcp_path.is_file():
            errors.append(f"mcpServers path missing: {mcp}")
        else:
            try:
                mcp_doc = json.loads(mcp_path.read_text(encoding="utf-8"))
                if not isinstance(mcp_doc.get("mcpServers"), dict):
                    errors.append(".mcp.json must contain an `mcpServers` object")
            except json.JSONDecodeError as exc:
                errors.append(f".mcp.json is not valid JSON: {exc}")

    # Skills: each dir needs SKILL.md with frontmatter name + description.
    skills_root = root / "skills"
    if skills_root.is_dir():
        for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir() and not p.name.startswith(".")):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                errors.append(f"skill `{skill_dir.name}` missing SKILL.md")
                continue
            text = skill_md.read_text(encoding="utf-8")
            if not text.startswith("---"):
                errors.append(f"skill `{skill_dir.name}` SKILL.md missing frontmatter")
                continue
            end = text.find("\n---", 3)
            fm = text[3:end] if end != -1 else ""
            if not re.search(r"^name:\s*\S", fm, re.MULTILINE):
                errors.append(f"skill `{skill_dir.name}` missing frontmatter `name`")
            if not re.search(r"^description:\s*\S", fm, re.MULTILINE):
                errors.append(f"skill `{skill_dir.name}` missing frontmatter `description`")

    return errors


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("Manifest sanity check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Manifest sanity check passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
