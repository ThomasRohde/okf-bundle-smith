---
name: okf-parallel-build
description: Build a large, exhaustive OKF bundle by fanning out many Codex subagents in parallel over a durable concept ledger, then reconciling and auditing coverage deterministically so no concept is dropped.
type: Skill
title: OKF Parallel Build Skill
tags: [okf, skill, parallel, subagents, orchestration]
timestamp: 2026-07-01T09:00:00Z
---

Use this skill when the target OKF bundle is large enough that a single agent
context cannot hold the whole concept graph — the failure mode where concepts get
silently dropped. It orchestrates Codex subagents in parallel and uses the
deterministic `okf` tools as the coordination substrate.

## Why single-pass authoring fails on large bundles

The ordinary authoring flow keeps the concept inventory, drafts, citations, and
validator output in one conversation. On a large bundle that overflows the
window and concepts are lost. The fix is not "try harder" — it is to move
coordination **onto disk** and fan out:

1. **A plan is the ledger.** Every concept to author is one row in
   `.okf/plan.csv`, with a `shard` column assigning disjoint file ownership.
2. **Workers fan out in parallel.** Codex spawns one authoring subagent per row
   (`spawn_agents_on_csv`), each owning a single path, so writes never collide.
3. **Coverage is audited deterministically.** `okf coverage` diffs the plan
   against files on disk. This — not any single agent's diligence — is what makes
   the bundle provably exhaustive.

```
scouts (∥) → mapper → .okf/plan.csv ──spawn_agents_on_csv──▶ workers (∥, one per row)
                                                                     │
   reconcile (tools):  okf coverage → okf index → okf lint --strict │
                                                                     ▼
              review (∥):  citation-auditor · graph-reviewer · skeptical-reviewer
                              └────────── repair loop until coverage is COMPLETE ──────────┘
```

## One-time setup

Codex spawns only the subagents that exist in `.codex/agents/`. Install the
bundled role definitions once, and raise the parallelism ceiling.

1. Install the subagents:
   - MCP: `okf_install_agents`, or
   - CLI: `python tools/okf_tool.py install-agents`
   This copies `okf-source-scout`, `okf-concept-mapper`, `okf-authoring-worker`,
   `okf-citation-auditor`, `okf-graph-reviewer`, and `okf-skeptical-reviewer`
   into `.codex/agents/`.
2. Raise concurrency in `~/.codex/config.toml` (default `max_threads` is 6):
   ```toml
   [agents]
   max_threads = 10
   max_depth = 1
   ```

## Orchestration workflow

Run this from the orchestrator (the main Codex thread). Keep the orchestrator
context thin: it holds the plan and coverage summaries, not concept bodies.

1. **Scope.** Infer purpose, target consumer, freshness, and source boundaries.
   Define a source policy before writing.
2. **Scout sources in parallel.** Split the topic into subtopics and spawn one
   `okf-source-scout` per subtopic: *"Spawn one source scout per subtopic, wait
   for all, and merge their source tables."* Deduplicate into one source table.
3. **Map concepts.** Hand the merged source table and goal to `okf-concept-mapper`
   and get back one exhaustive concept inventory (JSON array). Over-enumerate;
   coverage will catch extras, but it cannot invent a concept nobody planned.
4. **Build the plan.** Turn the inventory into a sharded ledger:
   - MCP: `okf_plan_bundle` with `bundle_path`, `inventory`, and
     `shards` (match `max_threads`).
   - CLI: `python tools/okf_tool.py plan <bundle> --inventory inventory.json --shards 10`
   This writes `<bundle>/.okf/plan.csv` and `plan.md`.
5. **Fan out authoring.** Spawn authoring workers over the plan CSV:
   ```
   spawn_agents_on_csv(
     csv_path = "<bundle>/.okf/plan.csv",
     agent = "okf-authoring-worker",
     id_column = "path",
     instruction = "Author the OKF concept at {path}. type={type}, title={title}. "
                   "description: {description}. Cite sources {source_ids}. "
                   "Write only {path}; then mark it done and report the result.",
     max_concurrency = 10,
   )
   ```
   Each worker writes exactly one file and calls `report_agent_job_result` once.
   For inventories larger than `max_threads`, `spawn_agents_on_csv` queues the
   rows into waves automatically — you do not need to batch by hand.
6. **Reconcile deterministically** (tools, not model context):
   - `okf coverage <bundle>` — the gate; exits non-zero until every planned
     concept exists and is complete.
   - `okf index <bundle>` — regenerate root and directory indexes centrally.
   - `okf lint <bundle> --strict` — conformance + quality.
7. **Repair loop.** While `okf coverage` reports `missing`, `incomplete`, or
   `errored` concepts, re-spawn authoring workers for just those rows (filter the
   plan CSV to the failing paths) and re-run coverage. Stop when status is
   COMPLETE.
8. **Review in parallel.** Over disjoint directories, spawn `okf-citation-auditor`,
   `okf-graph-reviewer`, and `okf-skeptical-reviewer`. Feed their findings back
   into a repair wave, then re-run coverage and `lint --strict`.
9. **Finalize.** Add a `log.md` entry, create/refresh bundle-local `AGENTS.md`
   (`okf_generate_chatgpt_usage`), and package.

## Coordination invariants

- **Disjoint ownership.** One concept path per plan row; a worker writes only its
  path. Duplicate paths are rejected at plan time — that is the anti-collision
  guarantee, so git worktrees are not required for authoring.
- **Central indexes.** Never let workers write `index.md`; generate indexes once
  at reconcile time so they stay coherent.
- **Truth is on disk.** `okf coverage` derives completeness from files, not from
  the `status` column. A worker that marks a row `done` without a complete file is
  reported as a status mismatch.
- **Thin orchestrator.** Pass concept bodies through the filesystem and pass only
  tables/summaries between agents. This is what keeps a large bundle inside
  budget.

## Completion criteria

Before the final response, report:

- bundle path and packaging format;
- planned vs. authored concept counts and the number of shards/workers used;
- final `okf coverage` status (must be COMPLETE) and `lint --strict` result;
- review findings addressed and any accepted residual warnings;
- most important source/citation constraints and freshness assumptions.
