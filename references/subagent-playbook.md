---
type: Playbook
title: Subagent Playbook for OKF Bundles
description: Role guidance for using subagents during broad OKF bundle research, mapping, authoring, citation audit, and graph review.
tags: [okf, subagents, playbook]
timestamp: 2026-06-29T18:45:00+02:00
---

# Subagent playbook for OKF bundles

Use subagents when a bundle is broad enough that research, validation, and graph design would pollute the main conversation.

## Recommended roles

## Source scout

Task: Find authoritative sources and return a source table.

Return format:

| id | title | url | publisher | date | source type | used for | concerns |
|---|---|---|---|---|---|---|---|

## Concept mapper

Task: Convert the source table and user goal into a concept inventory.

Return format:

| path | type | title | description | resource | tags | source ids |
|---|---|---|---|---|---|---|

## Authoring worker

Task: Draft a bounded set of concept files.

Return format: file path plus full Markdown content.

## Citation auditor

Task: Check whether claims are supported by the listed citations. Do not add new facts unless sourced.

Return format:

| file | claim | citation status | issue | proposed repair |
|---|---|---|---|---|

## Graph reviewer

Task: Review links, indexes, orphans, duplicate concepts, and directory structure.

Return format:

| issue type | file | issue | proposed repair |
|---|---|---|---|

## Skeptical reviewer

Task: Find overclaiming, outdated information, missing alternative views, or license/sensitivity problems.

Return format:

| severity | file | issue | evidence | action |
|---|---|---|---|---|
