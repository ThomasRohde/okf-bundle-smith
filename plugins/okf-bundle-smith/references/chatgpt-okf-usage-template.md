---
type: Reference
title: ChatGPT OKF Usage Template
description: Template for generating ChatGPT-friendly instructions for repository-hosted OKF bundles.
tags: [okf, chatgpt, github, instructions]
timestamp: 2026-06-29
---

# ChatGPT OKF Usage Template

Use the generated `CHATGPT.md` file to make a repository-hosted OKF bundle easier for ChatGPT to consume through the GitHub connector.

## Template

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

`CHATGPT.md` is an agent helper file, not an OKF concept file.
