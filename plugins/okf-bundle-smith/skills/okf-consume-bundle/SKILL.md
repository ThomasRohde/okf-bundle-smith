---
name: okf-consume-bundle
description: Use when a user wants Codex to consume, search, read, cite, review, or answer from an existing OKF bundle, especially a GitHub-hosted bundle URL.
type: Skill
title: OKF Consume Bundle Skill
tags: [okf, skill, retrieval, github]
timestamp: 2026-06-29
---

# OKF Bundle Consumption Workflow

Use this skill when the user wants to use an existing Open Knowledge Format bundle as context.

## Required Behavior

1. Identify the bundle source: attached alias, local path, GitHub URL, or registry entry.
2. If the user gives a GitHub URL, call `okf_attach_github_bundle` unless the bundle is already attached.
3. If the user gives a local path and wants reuse, call `okf_attach_local_bundle`.
4. Inspect attach diagnostics: source URL, commit SHA when available, bundle path, validation errors, validation warnings, freshness, and concept count.
5. Read `index.md` and `log.md` when available.
6. Use `okf_search_concepts` for the user's question or review topic.
7. Use `okf_read_concept` for high-scoring concepts.
8. Use `okf_related_concepts` when relationships matter.
9. Use `okf_prepare_answer_context` before final answers that claim to be bundle-grounded.
10. Use `okf_bundle_overview` for a broad bundle summary before answering open-ended overview questions.
11. Cite concept IDs or paths after material claims.
12. Distinguish direct bundle facts, inferences from bundle content, and external knowledge.

## Tool Availability

Prefer MCP tools. If the MCP tools are unavailable in the chat, use the CLI-equivalent commands before direct file lookup:

```bash
python tools/okf_tool.py search <bundle> "<query>"
python tools/okf_tool.py context <bundle> "<question>" --mode strict
python tools/okf_tool.py overview <bundle>
python tools/okf_tool.py mcp-diagnostics
```

Use direct file reads only as a last fallback when neither MCP nor CLI access is available.

## Answer Modes

Strict mode:

- Answer only from the OKF bundle.
- Say when the bundle does not contain enough information.
- Do not supplement with general knowledge unless the user asks.

Hybrid mode:

- Use the bundle first.
- Label external knowledge clearly.
- Do not override bundle facts silently.

## Citation Style

Prefer concept path citations:

- `[data/customer-identifier]`
- `[systems/payment-router]`
- `[controls/customer-data-classification]`

For a specific section, use a heading fragment such as `[systems/payment-router#dependencies]`.

## Limitations

If the bundle cannot be fetched, say why and suggest one of:

- provide a local path;
- clone the repository into the workspace;
- check GitHub credentials;
- use a public repository URL;
- specify the bundle path inside the repository.
