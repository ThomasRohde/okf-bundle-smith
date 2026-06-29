---
type: Process
title: Bundle Authoring Workflow
description: Repeatable process for turning a source boundary and concept inventory into a validated OKF bundle.
tags: [okf, authoring, workflow]
timestamp: 2026-06-29T18:45:00+02:00
---

# Summary

The bundle authoring workflow turns a source boundary into a useful
[OKF bundle](/concepts/open-knowledge-format.md). It emphasizes atomic concept
files, traceable claims, directory indexes, and validation before handoff.

# Steps

1. Define the [source policy](/sources/source-policy.md) and intended consumers.
2. Create a concept inventory with stable paths, types, titles, descriptions, tags, and key citations.
3. Write one [concept file](/concepts/concept-file.md) per durable concept.
4. Add bundle-relative [concept links](/concepts/concept-links.md) that support traversal.
5. Create root and directory [reserved files](/concepts/reserved-files.md) for indexes and update history.
6. Run the [validation profile](/controls/validation-profile.md), repair hard errors, and document any intentional warnings.
7. Package or publish the bundle only after validation.

# Outputs

The expected output is a directory tree of Markdown files that can be read
directly, linted by [OKF Bundle Smith](/systems/okf-bundle-smith.md), and used as
retrieval context by humans or agents.

# Citations

[1] Local source: `skills/okf-bundle-architect/SKILL.md`.
[2] Local source: `README.md`.

