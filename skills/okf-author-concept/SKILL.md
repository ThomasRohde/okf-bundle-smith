---
name: okf-author-concept
description: Author individual OKF concept documents with correct frontmatter, useful Markdown sections, citations, and cross-links.
---

Use this skill when editing or creating a single OKF concept document.

## Frontmatter

Use YAML frontmatter at the top of every concept file:

```yaml
---
type: Reference
title: Clear Human Title
description: One sentence that distinguishes this concept from nearby concepts.
tags: [domain, subdomain, lifecycle]
timestamp: 2026-06-29T00:00:00Z
---
```

`type` is required. Include recommended fields where possible. Add `resource` only when the concept has a real canonical URI. Preserve unknown fields when updating.

## Body pattern

Use sections that match the concept. Common options:

```markdown
# Summary

# Scope

# Key facts

# Relationships

# Examples

# Open questions

# Citations
```

For technical assets, use:

```markdown
# Schema

# Interfaces

# Dependencies

# Operations

# Risks and controls

# Examples

# Citations
```

For playbooks/runbooks, use:

```markdown
# Trigger

# Preconditions

# Steps

# Escalation

# Validation

# Rollback

# Citations
```

For decisions, use:

```markdown
# Context

# Decision

# Rationale

# Consequences

# Alternatives considered

# Citations
```

## Writing standards

- One concept per file.
- Use absolute bundle-relative links when linking to other concepts, e.g. `/data/customer.md`.
- Put external sources under `# Citations` and cite them by number from the body when useful.
- Do not overfit to today's org chart. Concepts should survive team changes.
- Use concise descriptions. Index generators depend on them.
- Avoid unstructured essays. Tables and lists are easier for agents to retrieve.
- Keep generated concept files small enough for review. Split broad files into linked neighboring concepts.

## Anti-patterns

Avoid:

- giant omnibus files;
- duplicate concepts under different directories;
- frontmatter without body substance;
- bodies full of unsourced claims;
- links that only say “here”;
- tags that are aliases for the directory path;
- generated prose that sounds confident but does not say where it came from.
