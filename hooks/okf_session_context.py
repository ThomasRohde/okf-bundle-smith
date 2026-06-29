#!/usr/bin/env python3
from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    context = """
OKF Bundle Smith active. When creating or updating OKF bundles, follow these invariants:
- One durable concept per Markdown file.
- Every concept file has YAML frontmatter with required `type`; include `title`, `description`, `tags`, and `timestamp` where possible.
- Add `resource` only when there is a real canonical URI.
- `index.md` and `log.md` are reserved filenames and should not have frontmatter.
- Prefer absolute bundle-relative links for internal concept relationships.
- External factual claims should be backed by `# Citations` entries.
- Preserve unknown frontmatter fields when updating existing concepts.
- Use `python <plugin-root>/tools/okf_tool.py lint <bundle>` or the `okf-tools` MCP server before finalizing.
""".strip()
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
