---
name: okf-from-web-research
description: Build or enrich an OKF bundle from web research with source quality controls, citations, freshness checks, and parallel subagent research patterns.
type: Skill
title: OKF From Web Research Skill
tags: [okf, skill, web-research]
timestamp: 2026-06-29T18:45:00+02:00
---

Use this skill when the user asks to create, update, or enrich an OKF bundle from public web sources.

## Source discipline

Do not treat web search snippets as sufficient evidence. Open sources when possible. Prefer:

1. Primary documentation, official specifications, standards, statutes, API docs, repositories, and author-maintained pages.
2. High-quality secondary analysis only when it explains tradeoffs or helps locate primary material.
3. News sources only for event chronology or recent developments.
4. Community sources only for implementation caveats, and label them as such.

Every non-obvious factual claim in a concept body should be backed by a citation. For controversial, recent, regulatory, financial, or enterprise-sensitive material, use multiple independent sources.

## Web-to-OKF workflow

1. Define the research question as a concept map, not a search query.
2. Create a source table with: `source_id`, `title`, `url`, `publisher`, `date`, `source_type`, `reliability`, `used_for`.
3. Extract candidate concepts from sources.
4. Deduplicate concepts: combine near-identical pages into one durable concept file.
5. Separate source facts from analysis. If you infer relationships, say so in prose and cite supporting facts.
6. Write `# Citations` in every concept where external claims appear.
7. Add a `/sources/` directory only when the source itself is valuable to describe as a reusable concept.
8. Mark freshness-sensitive claims with dates in the prose.
9. Create or update bundle-local `AGENTS.md` so readers and non-Codex agents can consume the bundle as plain OKF Markdown.
10. Run validation and a skeptical review pass.

## Recommended subagent split

For broad research tasks, ask Codex to spawn bounded subagents explicitly:

- **Source scout**: find primary sources and create a source table.
- **Concept mapper**: propose concept inventory and directory structure.
- **Citation auditor**: verify each concept's claims are supported.
- **Skeptical reviewer**: identify weak claims, outdated material, missing viewpoints, and licensing problems.
- **Graph reviewer**: check cross-links, indexes, orphan concepts, and broken links.

Each subagent should return concise findings, not raw browsing logs.

## Output rules

When writing concepts:

- Use direct, compact prose.
- Use structural Markdown: headings, tables, numbered procedures, definitions, examples.
- Do not include long quotations. Paraphrase and cite.
- Keep link text meaningful.
- Do not include unsupported predictions.
- Do not manufacture canonical `resource` URIs. Leave `resource` absent if there is no clear canonical asset URI.

## Final quality report

Return:

- source coverage summary;
- concepts created/updated;
- citation gaps, if any;
- freshness assumptions;
- recommended next enrichment pass.
