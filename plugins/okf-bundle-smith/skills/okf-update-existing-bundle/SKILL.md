---
name: okf-update-existing-bundle
description: Update an existing OKF bundle with new research, changed sources, repaired links, preserved metadata, and dated log entries.
type: Skill
title: OKF Update Existing Bundle Skill
tags: [okf, skill, update]
timestamp: 2026-06-29T18:45:00+02:00
---

Use this skill when a user asks to refresh, extend, or update an OKF bundle.

## Update workflow

1. Read the root `index.md`, any relevant directory `index.md`, and `log.md` before editing concept files.
2. Identify the current concept model: directories, types, tags, naming conventions, citation style, and custom frontmatter fields.
3. Preserve existing conventions unless they are harmful.
4. Research only the delta needed for the requested update.
5. For each changed concept:
   - preserve unknown frontmatter fields;
   - update `timestamp` only when the meaningful content changed;
   - update citations when facts changed;
   - add dated language for time-sensitive claims;
   - keep cross-links intact or repair them.
6. Add new concept files only when the information is a durable concept, not a transient note.
7. Regenerate affected indexes.
8. Add or update the nearest `log.md` and root `log.md` if the change affects the whole bundle. Use `python tools/okf_tool.py log <bundle> "<entry>"` when the plugin repo is available.
9. Run validation.

## Update report

Return:

- changed files;
- added concepts;
- removed or deprecated concepts;
- source changes;
- validation result;
- unresolved questions.
