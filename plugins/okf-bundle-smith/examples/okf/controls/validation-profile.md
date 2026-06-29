---
type: Control
title: Validation Profile
description: Practical OKF Bundle Smith checks for hard conformance, quality warnings, link health, and discoverability.
tags: [okf, validation, quality]
timestamp: 2026-06-29T18:45:00+02:00
---

# Summary

The validation profile describes how [OKF Bundle Smith](/systems/okf-bundle-smith.md)
checks an [OKF bundle](/concepts/open-knowledge-format.md). It separates hard
format conformance from quality guidance that improves retrieval and review.

# Hard Conformance

Hard conformance checks include parseable Markdown concept files with YAML
[frontmatter](/concepts/frontmatter-schema.md), a non-empty `type` field, a
frontmatter mapping, and valid UTF-8. These checks map to the minimal OKF v0.1
contract.

# Quality Warnings

Quality warnings cover recommended metadata, real URI handling for `resource`,
timestamp shape, substantive body text, citation sections for external links,
resolved [concept links](/concepts/concept-links.md), directory indexes, reserved
file handling, duplicate titles, and orphan concepts.

# Evidence

A clean validation run should report zero errors and only intentional warnings.
For this example bundle, validation is performed with `python tools/okf_tool.py
lint examples/okf` from the plugin root.

# Citations

[1] Local source: `references/okf-v0.1-conformance.md`.
[2] Local source: `tools/okf_core.py`.
