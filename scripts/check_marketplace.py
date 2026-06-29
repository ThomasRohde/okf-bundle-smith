#!/usr/bin/env python3
"""Validate the repository-level Codex marketplace wiring."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def check(root: Path) -> list[str]:
    errors: list[str] = []
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    if not marketplace_path.is_file():
        return ["missing .agents/plugins/marketplace.json"]

    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"marketplace.json is not valid JSON: {exc}"]

    if marketplace.get("name") != "okf-bundle-smith":
        errors.append("marketplace name must be `okf-bundle-smith`")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        return errors + ["marketplace plugins must be an array"]

    matches = [entry for entry in plugins if isinstance(entry, dict) and entry.get("name") == "okf-bundle-smith"]
    if len(matches) != 1:
        errors.append("marketplace must contain exactly one `okf-bundle-smith` plugin entry")
        return errors

    entry = matches[0]
    source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
    if source.get("source") != "local":
        errors.append("okf-bundle-smith source.source must be `local`")
    if source.get("path") != "./plugins/okf-bundle-smith":
        errors.append("okf-bundle-smith source.path must be `./plugins/okf-bundle-smith`")

    policy = entry.get("policy") if isinstance(entry.get("policy"), dict) else {}
    if policy.get("installation") != "AVAILABLE":
        errors.append("okf-bundle-smith policy.installation must be `AVAILABLE`")
    if policy.get("authentication") != "ON_INSTALL":
        errors.append("okf-bundle-smith policy.authentication must be `ON_INSTALL`")
    if entry.get("category") != "Productivity":
        errors.append("okf-bundle-smith category must be `Productivity`")

    plugin_root = root / "plugins" / "okf-bundle-smith"
    if not (plugin_root / ".codex-plugin" / "plugin.json").is_file():
        errors.append("plugins/okf-bundle-smith is missing .codex-plugin/plugin.json")

    return errors


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("Marketplace sanity check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Marketplace sanity check passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
