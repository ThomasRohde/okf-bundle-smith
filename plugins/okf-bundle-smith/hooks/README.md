---
type: Reference
title: Optional Hooks
description: Reference for optional Codex hook scripts bundled with OKF Bundle Smith.
tags: [okf, hooks, codex]
timestamp: 2026-06-29T18:45:00+02:00
---

# Optional Hooks

These scripts are optional local helpers for Codex environments that support hook configuration outside the plugin manifest.

They are not referenced from `.codex-plugin/plugin.json` because the current plugin validator rejects a top-level `hooks` field.

## Scripts

- `okf_session_context.py` prints OKF authoring guidance for session-start hooks.
- `okf_stop_review.py` scans likely OKF bundles near the current working directory and blocks finalization when hard conformance errors remain.

Review `hooks.json` before enabling these scripts in a local Codex configuration.
