---
type: Reference
title: ChatGPT and Codex OKF Usage Template
description: Template for generating ChatGPT-friendly instructions, bundle-local AGENTS.md usage guidance, and optional Codex repository AGENTS.md snippets.
tags: [okf, chatgpt, codex, github, instructions]
timestamp: 2026-06-29
---

# ChatGPT and Codex OKF Usage Template

Use the generated `CHATGPT.md` file to make a repository-hosted OKF bundle easier for ChatGPT to consume through the GitHub connector.
Use the generated bundle-local `AGENTS.md` file to explain how any agent can consume the bundle as plain OKF Markdown without Codex, MCP, CLI, or other OKF-specific tools.
Use `repo_agents_md_snippet` as an optional, user-approved repository `AGENTS.md` section when a bundle should become the default source for relevant future Codex tasks.

## CHATGPT.md Template

```markdown
# ChatGPT instructions for this OKF bundle

This directory is an Open Knowledge Format bundle.

## Entry points

Start with:

- `index.md`
- `log.md`

Then follow Markdown links to relevant concept files.

## Answering rules

- Prefer bundle content over general model knowledge.
- Cite concept paths such as `[systems/payment-router]`.
- Distinguish direct bundle facts from inference.
- Report if the bundle is stale, incomplete, or missing relevant concepts.
- Use external knowledge only when explicitly requested, and label it.
```

## Bundle AGENTS.md Template

```markdown
# How to Use This OKF Bundle

This directory is an Open Knowledge Format (OKF) bundle. It is designed for direct Markdown consumption by humans and agents.

## Start Here

- Read `index.md` first to understand the bundle map and entry points.
- Read `log.md` to understand recent changes, freshness, and known maintenance history.
- Follow internal Markdown links to relevant concept files instead of loading every file at once.

## Answering From This Bundle

- Prefer bundle content over general model knowledge for covered topics.
- Cite concept paths after bundle-grounded claims.
- Distinguish direct bundle facts from inference or external knowledge.
- Report when the bundle is stale, incomplete, contradictory, or missing concepts needed to answer.
```

`CHATGPT.md` is an agent helper file, not an OKF concept file.
Bundle-local `AGENTS.md` is also an agent helper file, not an OKF concept file. Repository-level `AGENTS.md` changes are policy changes; do not make them without explicit user approval.
