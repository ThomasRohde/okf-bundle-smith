---
name: okf-review-and-repair
description: Validate, audit, and repair an existing OKF bundle for conformance, citations, indexes, logs, links, metadata quality, and graph usefulness.
---

Use this skill when the user asks to check, lint, validate, review, or improve an OKF bundle.

## Review sequence

1. Run the bundled validator when available:

```bash
python tools/okf_tool.py lint path/to/bundle --format markdown
```

2. Inspect errors first, warnings second.
3. Repair hard errors:
   - missing frontmatter;
   - missing `type`;
   - invalid Markdown file placement;
   - malformed frontmatter;
   - broken generated index references;
   - invalid `log.md` date headings.
4. Repair quality issues:
   - missing titles/descriptions;
   - empty or malformed `resource` values;
   - weak or missing citations;
   - orphan concepts;
   - duplicate concepts;
   - weak cross-linking;
   - stale timestamps;
   - over-broad files.
5. Regenerate indexes if the concept inventory changed.
6. Update `log.md` with a concise dated entry.
7. Re-run validation.
8. Provide a review report with fixed items and remaining risks.

## Strictness levels

- **Conformance**: OKF v0.1 minimum only.
- **Good**: recommended frontmatter, citations, index files, reasonable links.
- **Enterprise**: source policy, ownership metadata, sensitivity tags, freshness model, stewardship, controls, and audit trail.

Default to **Good**. Use **Enterprise** for regulated, internal, or architecture-critical knowledge.

## Repair principles

- Preserve unknown frontmatter fields.
- Do not delete user-authored sections unless clearly obsolete.
- Prefer small, reviewable changes.
- Mark uncertainty rather than hiding it.
- Never invent citations.
- If a source is missing, add an `# Open questions` section rather than pretending confidence.
