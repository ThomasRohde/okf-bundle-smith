---
type: Reference
title: OKF Consumption Contract
description: Answering and retrieval contract for using an OKF bundle as grounded agent context.
tags: [okf, consumption, citations, retrieval]
timestamp: 2026-06-29
---

# OKF Consumption Contract

OKF consumer mode treats concept paths as citation IDs and bundle content as the primary evidence source.

## Entry Sequence

1. Attach or resolve the bundle alias or path.
2. Read the root `index.md` for progressive disclosure when present.
3. Read the root `log.md` for freshness when present.
4. Search title, description, tags, type, headings, and body excerpts.
5. Traverse internal Markdown links for neighboring concepts.
6. Prepare an answer context pack before giving a bundle-grounded answer.

## Strict Mode

Strict mode is for answers that must be grounded only in the bundle.

- Use retrieved concepts only.
- Cite concept IDs in brackets.
- Say when evidence is missing.
- Report validation and freshness limitations.
- Do not fill gaps from general model knowledge.

## Hybrid Mode

Hybrid mode is for analysis or planning where external reasoning is useful.

- Start with bundle facts.
- Cite bundle claims with concept IDs.
- Label inference separately.
- Label external knowledge separately.
- Call out conflicts instead of silently choosing one source.
