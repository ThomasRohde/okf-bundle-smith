---
type: Reference
title: GitHub Bundle URL Syntax
description: Supported GitHub URL forms and ref/path parsing rules for OKF consumer mode.
tags: [okf, github, url-parsing, retrieval]
timestamp: 2026-06-29
---

# GitHub Bundle URL Syntax

Consumer mode accepts GitHub repository, tree, blob, SSH, and compact owner/repo references.

## Supported Forms

```text
https://github.com/org/repo
https://github.com/org/repo/tree/main/bundles/payments
https://github.com/org/repo/tree/release/2026.06/bundles/payments
https://github.com/org/repo/blob/main/bundles/payments/index.md
git@github.com:org/repo.git
org/repo//bundles/payments?ref=main
```

## Ref Resolution

Tree and blob URLs are ambiguous because branch and tag names can contain slashes. The resolver checks remote heads and tags, then selects the longest matching ref and treats the remainder as the bundle path.

If no ref is supplied, the resolver uses the remote default branch when discoverable, otherwise `HEAD`.

## Security Posture

The implementation uses `git` and the user's existing credentials. It does not store GitHub credentials, execute repository scripts, or read outside the selected bundle path except for attachment metadata.
