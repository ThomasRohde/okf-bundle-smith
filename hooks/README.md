# Optional Hooks

These scripts are optional local helpers for Codex environments that support hook configuration outside the plugin manifest.

They are not referenced from `.codex-plugin/plugin.json` because the current plugin validator rejects a top-level `hooks` field.

## Scripts

- `okf_session_context.py` prints OKF authoring guidance for session-start hooks.
- `okf_stop_review.py` scans likely OKF bundles near the current working directory and blocks finalization when hard conformance errors remain.

Review `hooks.json` before enabling these scripts in a local Codex configuration.
