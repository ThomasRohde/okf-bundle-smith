---
type: Reference
title: Reserved Files
description: Index and log files that support navigation and change history without becoming concepts themselves.
tags: [okf, indexes, logs]
timestamp: 2026-06-29T18:45:00+02:00
---

# Summary

OKF reserves `index.md` and `log.md` for bundle navigation and update history.
These files are Markdown, but they are not [concept files](/concepts/concept-file.md)
and should not contain YAML [frontmatter](/concepts/frontmatter-schema.md).

# Usage

`index.md` files provide progressive disclosure. A root index introduces the
bundle, and directory indexes list child directories and local concepts. `log.md`
records date-grouped changes so bundle consumers can understand freshness and
maintenance history.

# Relationships

* Index links help expose [concept links](/concepts/concept-links.md) and improve discoverability.
* The [bundle authoring workflow](/processes/bundle-authoring-workflow.md) creates or regenerates indexes after concept files are written.
* The [validation profile](/controls/validation-profile.md) warns when participating directories lack indexes or logs have invalid date headings.

# Citations

[1] [Open Knowledge Format specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
[2] Local source: `references/okf-v0.1-cheatsheet.md`.
[3] Local source: `references/okf-v0.1-conformance.md`.

