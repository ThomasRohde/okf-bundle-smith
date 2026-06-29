---
type: Design
title: Extend OKF Bundle Smith to Consume GitHub-Hosted OKF Bundles
description: Implementation design for adding consumer-mode indexing, retrieval, context packing, and GitHub bundle attachment to OKF Bundle Smith.
tags: [okf, github, context-engineering, consumer-mode]
timestamp: 2026-06-29
---

# Design Spec: Extend OKF Bundle Smith to Consume GitHub-Hosted OKF Bundles

**Document status:** Draft implementation design  
**Target repository:** `ThomasRohde/okf-bundle-smith`  
**Target plugin:** `plugins/okf-bundle-smith`  
**Date:** 2026-06-29  
**Primary goal:** Make it easy for a user to point Codex or ChatGPT at an OKF bundle in GitHub and use that bundle as reliable, cited context.

---

## 1. Executive summary

`okf-bundle-smith` currently focuses on producing and maintaining OKF bundles: creation, enrichment, validation, repair, graphing, visualization, packaging, and local MCP tooling. The next extension should add a **consumer mode**.

The consumer mode should let a user say:

```text
Use OKF Bundle Smith with this bundle:
https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture

Answer: Which systems depend on the canonical customer identifier?
```

Codex should then:

1. Normalize the GitHub URL into a bundle reference.
2. Fetch or refresh the bundle into a local read-only cache.
3. Validate that the target path is an OKF bundle.
4. Build a lightweight searchable concept index.
5. Read `index.md` and `log.md` first.
6. Search and traverse related concepts.
7. Prepare answer context with concept-path citations.
8. Answer in either **strict bundle-grounded mode** or **hybrid mode**.

The extension should not replace the existing producer tools. It should add a second operating mode:

```text
Producer mode: create / enrich / validate / package OKF.
Consumer mode: attach / search / read / trace / answer from OKF.
```

---

## 2. Background and constraints

### 2.1 OKF characteristics to preserve

The OKF spec defines a bundle as a directory tree of Markdown files with YAML frontmatter. The spec is intentionally minimal: there is no schema registry, central authority, or required runtime. Concept IDs are file paths without the `.md` suffix. `index.md` and `log.md` are reserved structural files, and Markdown links express relationships between concepts.

Design implications:

- Treat the filesystem path as the stable knowledge identifier.
- Do not require a database or hosted service for the MVP.
- Preserve normal Git workflows: clone, diff, branch, review, release.
- Read `index.md` for progressive disclosure before doing broad search.
- Use `log.md` to report freshness and recent changes.
- Cite concept paths, not vague repository names.

### 2.2 Codex integration constraints

Codex plugins are the installable distribution unit for skills, MCP servers, hooks, app mappings, and assets. Skills provide reusable workflows. MCP servers expose tools and context to Codex. `AGENTS.md` gives project-level instructions and is read before work starts.

Design implications:

- Implement the user-facing workflow as a new skill: `okf-consume-bundle`.
- Implement deterministic bundle operations as CLI + MCP tools.
- Add optional project guidance templates for `AGENTS.md`.
- Keep all MCP tools read-only by default when consuming remote bundles.
- Keep CLI and MCP parity: every MCP consumer operation should have an equivalent CLI command.

### 2.3 ChatGPT constraints

ChatGPT can connect to GitHub repositories through the GitHub connector in supported plans and experiences, but that connector is read-focused and does not behave like a deterministic bundle runtime. ChatGPT forms search queries from user prompts and retrieves relevant snippets from connected repositories.

Design implications:

- Do not assume ChatGPT can run the Codex plugin.
- Make bundles easier for ChatGPT to consume by generating explicit entry files such as `CHATGPT.md`, `llms.txt`, and `okf-registry.yaml`.
- Provide a prompt contract that instructs ChatGPT to read `index.md`, `log.md`, and relevant concepts first.
- Treat a future ChatGPT custom app / MCP service as a later productization path.

---

## 3. Product goal

### 3.1 User promise

> “Give OKF Bundle Smith a GitHub URL, and it will make the bundle usable as agent context with searchable concepts, link traversal, freshness checks, and concept-path citations.”

### 3.2 Primary user stories

#### Story 1: Attach a public GitHub bundle in Codex

```text
Use OKF Bundle Smith to attach:
https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture
as payments.

Then answer: Which services depend on the canonical customer identifier?
```

Expected behavior:

- Codex calls `okf_attach_github_bundle`.
- The plugin clones or refreshes the repo into a cache.
- The plugin detects the bundle root at `bundles/payments-architecture`.
- The plugin validates the bundle and indexes concepts.
- Codex searches and reads relevant concepts.
- The final answer cites concept IDs such as `systems/customer-identity` and `data/customer-identifier`.

#### Story 2: Attach a bundle once and reuse it

```text
Attach this bundle as payments and persist it for this repo:
https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture
```

Expected behavior:

- The plugin writes a project-local `.okf/attachments.yaml` if the user requests persistence.
- Later Codex sessions can list and use the attached bundle without repeating the URL.

#### Story 3: Use a bundle in PR/code review

```text
Use the payments OKF bundle to review this change for architecture conflicts.
Focus on ownership boundaries, data classification, and deprecated integration paths.
```

Expected behavior:

- Codex reads the bundle index and log.
- Codex searches concepts related to touched files and changed terms.
- Codex reports conflicts with concept-path citations.
- Codex separates direct bundle statements from model inference.

#### Story 4: Generate a ChatGPT consumption file

```text
Generate ChatGPT usage files for this OKF bundle.
```

Expected behavior:

- The plugin creates `CHATGPT.md` with usage instructions.
- The plugin optionally creates or updates `llms.txt` and `okf-registry.yaml`.
- A ChatGPT user can connect the GitHub repo and ask it to use the bundle with clear instructions.

---

## 4. Non-goals for the MVP

The MVP should avoid turning OKF Bundle Smith into a hosted knowledge platform.

Out of scope for the first implementation:

- Hosted search service.
- Long-running daemon.
- Vector database dependency.
- Automatic enterprise authentication setup.
- Claim-level proof checking.
- Executing code from the target bundle repository.
- Editing remote GitHub repositories directly.
- Replacing GitHub, Knowledge Catalog, Confluence, SharePoint, or data catalogs.

The MVP should be local, deterministic, dependency-light, and compatible with the current plugin architecture.

---

## 5. Proposed user experience

### 5.1 Codex prompt-first usage

The user should be able to use natural language:

```text
Use OKF Bundle Smith.
Attach this OKF bundle as payments:
https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture

Use strict bundle mode.
Question: What systems depend on customer identifier normalization?
```

Codex should select the `okf-consume-bundle` skill, then use MCP tools.

### 5.2 Codex CLI usage

Equivalent command-line usage:

```bash
python plugins/okf-bundle-smith/tools/okf_tool.py attach-github \
  https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture \
  --alias payments

python plugins/okf-bundle-smith/tools/okf_tool.py search payments \
  "customer identifier normalization"

python plugins/okf-bundle-smith/tools/okf_tool.py context payments \
  "What systems depend on customer identifier normalization?" \
  --mode strict
```

### 5.3 Persistent project usage

For a repository that always uses a known OKF bundle:

```bash
python plugins/okf-bundle-smith/tools/okf_tool.py attach-github \
  https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture \
  --alias payments \
  --persist-project
```

This creates:

```text
.okf/
└── attachments.yaml
```

Example:

```yaml
version: 1
bundles:
  payments:
    kind: github
    url: https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture
    owner: acme
    repo: okf-knowledge
    ref: main
    path: bundles/payments-architecture
    mode: read-only
    last_attached: 2026-06-29T19:30:00+02:00
```

### 5.4 ChatGPT usage

For ChatGPT, the plugin should generate a `CHATGPT.md` file in the bundle repo or bundle root:

```markdown
# ChatGPT usage for this OKF bundle

Use this repository as an OKF bundle source.

Start with:

1. `bundles/payments-architecture/index.md`
2. `bundles/payments-architecture/log.md`
3. linked concept files relevant to the question

Answer mode:

- Prefer bundle facts over general model knowledge.
- Cite concept paths.
- Distinguish direct bundle facts from inference.
- Report if the bundle appears stale or incomplete.
```

Then the user can ask ChatGPT:

```text
Use the GitHub repo acme/okf-knowledge.
Follow the instructions in bundles/payments-architecture/CHATGPT.md.
Answer from the OKF bundle and cite concept paths.

Question: Which systems depend on customer identifier normalization?
```

---

## 6. Architecture

### 6.1 Current plugin baseline

The current plugin root is:

```text
plugins/okf-bundle-smith/
├── .codex-plugin/plugin.json
├── .mcp.json
├── README.md
├── skills/
├── tools/
├── references/
├── examples/
├── tests/
└── hooks/
```

The existing MCP tools cover scaffold, validation, stats, index generation, graph export, visualization, log entries, and packaging.

### 6.2 New components

Add the following:

```text
plugins/okf-bundle-smith/
├── skills/
│   └── okf-consume-bundle/
│       └── SKILL.md
├── references/
│   ├── okf-consumption-contract.md
│   ├── github-bundle-url-syntax.md
│   └── chatgpt-okf-usage-template.md
├── tools/
│   ├── okf_consume.py
│   ├── okf_git.py
│   ├── okf_index.py
│   ├── okf_retrieve.py
│   └── okf_context.py
└── tests/
    ├── test_okf_git.py
    ├── test_okf_index.py
    ├── test_okf_retrieve.py
    ├── test_okf_context.py
    └── fixtures/github-bundles/
```

Extend existing files:

```text
plugins/okf-bundle-smith/tools/okf_tool.py
plugins/okf-bundle-smith/tools/okf_mcp_server.py
plugins/okf-bundle-smith/tools/okf_core.py
plugins/okf-bundle-smith/README.md
plugins/okf-bundle-smith/references/okf-v0.1-conformance.md
```

### 6.3 Data flow

```text
User prompt / CLI command
        |
        v
okf-consume-bundle skill
        |
        v
MCP tool or CLI command
        |
        v
GitHub URL normalizer
        |
        v
Read-only Git cache in PLUGIN_DATA
        |
        v
Bundle root detection and validation
        |
        v
Concept index builder
        |
        v
Search / read / link traversal / context pack
        |
        v
Codex or ChatGPT answer with concept-path citations
```

### 6.4 Storage locations

Use plugin data for cached remote bundles:

```text
${PLUGIN_DATA}/okf-consumer/
├── state.json
├── github-cache/
│   └── acme/okf-knowledge/<ref-hash>/
└── indexes/
    └── <bundle-alias-or-hash>.json
```

Use project storage only when the user explicitly asks to persist the attachment:

```text
<project-root>/.okf/attachments.yaml
```

Rationale:

- Plugin data avoids polluting the user repository by default.
- Project-local `.okf/attachments.yaml` makes team usage reproducible.
- Cache contents are disposable and can be refreshed from GitHub.

---

## 7. GitHub bundle reference model

### 7.1 Supported input forms

Support these forms:

```text
https://github.com/org/repo
https://github.com/org/repo/tree/main/bundles/payments
https://github.com/org/repo/tree/v2026.06/bundles/payments
https://github.com/org/repo/blob/main/bundles/payments/index.md
git@github.com:org/repo.git
org/repo//bundles/payments?ref=main
```

Recommended user-facing form:

```text
https://github.com/org/repo/tree/<ref>/<path-to-bundle>
```

### 7.2 Normalized reference object

```python
@dataclass(frozen=True)
class GitHubBundleRef:
    owner: str
    repo: str
    ref: str | None
    path: str | None
    url: str
    host: str = "github.com"
```

After fetch, resolve to:

```python
@dataclass(frozen=True)
class ResolvedBundleRef:
    alias: str
    kind: str  # "github" or "local"
    owner: str | None
    repo: str | None
    requested_ref: str | None
    commit_sha: str | None
    bundle_path: str
    local_path: str
    source_url: str
    fetched_at: str
    validation_status: str
```

### 7.3 Branch and path parsing

GitHub tree URLs are ambiguous because branch names can contain slashes. The resolver should use this strategy:

1. Parse owner and repo from the URL.
2. For `/tree/<tail>`, attempt candidate splits from longest possible ref to shortest possible ref.
3. Use `git ls-remote --heads --tags` to identify valid refs.
4. Select the longest matching ref.
5. Treat the remaining path as the bundle path.
6. If no ref is supplied, default to the remote default branch if discoverable; otherwise use `HEAD`.

Example:

```text
https://github.com/org/repo/tree/release/2026.06/bundles/payments
```

Possible interpretation:

```yaml
ref: release/2026.06
path: bundles/payments
```

### 7.4 Clone strategy

Use Git, not the GitHub API, for MVP. This keeps the implementation compatible with public repos, private repos with existing credentials, GitHub Enterprise later, and pinned refs.

Suggested clone flow:

```bash
git clone --filter=blob:none --no-checkout https://github.com/org/repo.git <cache-dir>
git -C <cache-dir> sparse-checkout init --cone
git -C <cache-dir> sparse-checkout set <bundle-path>
git -C <cache-dir> checkout <ref>
git -C <cache-dir> rev-parse HEAD
```

Refresh flow:

```bash
git -C <cache-dir> fetch --depth 1 origin <ref>
git -C <cache-dir> checkout FETCH_HEAD
git -C <cache-dir> rev-parse HEAD
```

For the MVP, private repository access should rely on the user's existing Git credentials, SSH agent, GitHub CLI auth, or environment. Do not build credential collection into the plugin.

---

## 8. Bundle detection and validation

### 8.1 Bundle root detection

If the URL includes a path:

1. Use that path as the candidate bundle root.
2. Require at least one Markdown concept file or `index.md` under the path.
3. Run the existing validator.
4. Return clear diagnostics if the path is not an OKF bundle.

If the URL points only to a repo:

1. Look for `okf-registry.yaml` at the repo root.
2. If present, list candidate bundles from the registry.
3. Else scan common locations:
   - `bundles/*`
   - `okf/*`
   - `docs/okf/*`
   - repository root only as a last resort
4. If multiple candidates exist, ask the user to choose unless an alias/path was supplied.

### 8.2 OKF registry format

Add optional registry support:

```yaml
version: 1
bundles:
  - id: payments
    title: Payments Architecture
    path: bundles/payments-architecture
    status: active
    description: Canonical architecture knowledge for payments systems.
    owner: payments-architecture-team
    tags: [payments, architecture, customer-identity]
    default_mode: strict
  - id: ai-governance
    title: AI Governance
    path: bundles/ai-governance
    status: active
    tags: [ai, governance, model-risk]
```

This is not part of OKF v0.1. It is a practical discovery layer for repositories containing multiple bundles.

### 8.3 Validation behavior

On attach:

- Run existing bundle validation.
- Store validation summary in the attachment state.
- Do not block attach on warnings.
- Block strict mode if hard errors make the bundle unreadable.

Hard errors:

- Missing bundle path.
- No readable Markdown files.
- Malformed frontmatter in concept files.
- Concept file missing required `type`.
- Path traversal or symlink escape.

Warnings:

- Missing `index.md`.
- Missing `log.md`.
- Missing timestamps.
- Missing descriptions.
- Broken internal links.
- Concepts without inbound links.
- Missing citation sections for heavily factual files.

---

## 9. Concept index design

### 9.1 Index goals

The index should support:

- Fast concept lookup by ID.
- Search across title, description, tags, type, headings, and body text.
- Internal link traversal.
- Freshness reporting.
- Citation extraction.
- Context-pack generation for answer prompts.

### 9.2 Index file schema

```json
{
  "schema_version": "okf-consumer-index/v1",
  "generated_at": "2026-06-29T19:30:00+02:00",
  "source": {
    "kind": "github",
    "url": "https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture",
    "owner": "acme",
    "repo": "okf-knowledge",
    "requested_ref": "main",
    "commit_sha": "abc123...",
    "bundle_path": "bundles/payments-architecture"
  },
  "bundle": {
    "alias": "payments",
    "local_path": "/.../github-cache/acme/okf-knowledge/.../bundles/payments-architecture",
    "title": "Payments Architecture",
    "has_index": true,
    "has_log": true,
    "concept_count": 84
  },
  "concepts": [
    {
      "concept_id": "systems/customer-identity-service",
      "path": "systems/customer-identity-service.md",
      "title": "Customer Identity Service",
      "type": "System",
      "description": "Canonical service for customer identity resolution.",
      "tags": ["customer", "identity", "payments"],
      "timestamp": "2026-06-28T12:00:00+02:00",
      "headings": ["Responsibilities", "Dependencies", "Controls", "Citations"],
      "outlinks": ["data/customer-identifier", "controls/customer-data-classification"],
      "citations": [
        {
          "label": "Architecture decision record ADR-014",
          "url": "https://github.com/acme/architecture/adr/014"
        }
      ],
      "body_hash": "sha256:...",
      "body_excerpt": "The Customer Identity Service owns canonical customer identifier normalization..."
    }
  ]
}
```

### 9.3 Search implementation

MVP search should be dependency-light and deterministic.

Recommended MVP ranking:

1. Exact concept ID match.
2. Exact title match.
3. Tag match.
4. Type match.
5. Description match.
6. Heading match.
7. Body token match.
8. Link-neighborhood boost from already matched concepts.

Do not add vector search in the MVP. Add an optional later module:

```text
okf_vector_index.py
```

Keep the lexical index as the canonical fallback.

### 9.4 Context budget controls

Add parameters:

```text
max_concepts: default 8
max_chars_per_concept: default 4000
include_index: default true
include_log: default true
link_depth: default 1
mode: strict | hybrid
```

The context pack should include:

- Bundle identity.
- Commit SHA.
- Validation status.
- Freshness summary.
- Retrieved concepts.
- Short excerpts.
- Citation tokens.
- Internal links worth following.

---

## 10. MCP tool surface

Add these MCP tools to `okf_mcp_server.py`.

### 10.1 `okf_attach_github_bundle`

Attach and index a GitHub-hosted OKF bundle.

Input:

```json
{
  "url": "https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture",
  "alias": "payments",
  "ref": null,
  "path": null,
  "persist_project": false,
  "refresh": false
}
```

Output:

```json
{
  "alias": "payments",
  "status": "attached",
  "source_url": "https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture",
  "commit_sha": "abc123...",
  "bundle_path": "bundles/payments-architecture",
  "concept_count": 84,
  "validation": {
    "errors": 0,
    "warnings": 7
  }
}
```

### 10.2 `okf_list_attached_bundles`

List bundles attached in plugin state and project state.

Input:

```json
{
  "scope": "all"
}
```

Output:

```json
{
  "bundles": [
    {
      "alias": "payments",
      "kind": "github",
      "source_url": "https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture",
      "commit_sha": "abc123...",
      "concept_count": 84,
      "validation_status": "ok"
    }
  ]
}
```

### 10.3 `okf_refresh_bundle`

Refresh a GitHub bundle and rebuild the index.

Input:

```json
{
  "alias": "payments",
  "force": false
}
```

Output:

```json
{
  "alias": "payments",
  "old_commit_sha": "abc123...",
  "new_commit_sha": "def456...",
  "changed": true,
  "concept_count": 86,
  "validation": {
    "errors": 0,
    "warnings": 5
  }
}
```

### 10.4 `okf_search_concepts`

Search concepts in an attached or local bundle.

Input:

```json
{
  "bundle": "payments",
  "query": "customer identifier normalization dependencies",
  "type": null,
  "tags": ["customer"],
  "max_results": 10
}
```

Output:

```json
{
  "bundle": "payments",
  "query": "customer identifier normalization dependencies",
  "results": [
    {
      "concept_id": "data/customer-identifier",
      "title": "Customer Identifier",
      "type": "Data Concept",
      "path": "data/customer-identifier.md",
      "score": 12.8,
      "reason": "title, tag, description, body",
      "excerpt": "The canonical customer identifier is normalized before payment routing..."
    }
  ]
}
```

### 10.5 `okf_read_concept`

Read one concept by concept ID or path.

Input:

```json
{
  "bundle": "payments",
  "concept_id": "data/customer-identifier",
  "include_neighbors": true
}
```

Output:

```json
{
  "bundle": "payments",
  "concept": {
    "concept_id": "data/customer-identifier",
    "title": "Customer Identifier",
    "type": "Data Concept",
    "path": "data/customer-identifier.md",
    "frontmatter": {
      "type": "Data Concept",
      "title": "Customer Identifier",
      "tags": ["customer", "identity", "payments"]
    },
    "body": "...",
    "outlinks": ["systems/customer-identity-service"],
    "inlinks": ["systems/payment-router"]
  }
}
```

### 10.6 `okf_related_concepts`

Return neighboring concepts by Markdown links and directory proximity.

Input:

```json
{
  "bundle": "payments",
  "concept_id": "data/customer-identifier",
  "depth": 1,
  "max_results": 20
}
```

Output:

```json
{
  "bundle": "payments",
  "start": "data/customer-identifier",
  "related": [
    {
      "concept_id": "systems/customer-identity-service",
      "relationship": "outlink",
      "distance": 1
    },
    {
      "concept_id": "systems/payment-router",
      "relationship": "inlink",
      "distance": 1
    }
  ]
}
```

### 10.7 `okf_prepare_answer_context`

Prepare a compact context pack for Codex to answer from.

Input:

```json
{
  "bundle": "payments",
  "question": "Which systems depend on customer identifier normalization?",
  "mode": "strict",
  "max_concepts": 8,
  "link_depth": 1,
  "max_chars_per_concept": 4000
}
```

Output:

```json
{
  "bundle": "payments",
  "mode": "strict",
  "source": {
    "url": "https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture",
    "commit_sha": "abc123..."
  },
  "freshness": {
    "latest_log_entry": "2026-06-28",
    "oldest_concept_timestamp": "2026-02-01",
    "warnings": []
  },
  "answer_instructions": [
    "Answer only from the retrieved OKF concepts.",
    "Cite concept IDs in brackets after claims.",
    "Say when the bundle does not contain enough information."
  ],
  "concepts": [
    {
      "citation_id": "data/customer-identifier",
      "title": "Customer Identifier",
      "path": "data/customer-identifier.md",
      "excerpt": "..."
    }
  ],
  "follow_up_candidates": [
    "systems/payment-router",
    "controls/customer-data-classification"
  ]
}
```

### 10.8 `okf_freshness_report`

Report freshness and potential staleness.

Input:

```json
{
  "bundle": "payments"
}
```

Output:

```json
{
  "bundle": "payments",
  "latest_log_entry": "2026-06-28",
  "concepts_without_timestamp": 3,
  "concepts_older_than_days": {
    "90": 12,
    "180": 4,
    "365": 0
  },
  "warnings": [
    "4 concepts have not been updated in more than 180 days."
  ]
}
```

### 10.9 `okf_generate_chatgpt_usage`

Generate ChatGPT-friendly usage files for a bundle.

Input:

```json
{
  "bundle_path": "bundles/payments-architecture",
  "repo_name": "acme/okf-knowledge",
  "write_files": true,
  "include_llms_txt": true,
  "include_registry": true
}
```

Output:

```json
{
  "created": [
    "bundles/payments-architecture/CHATGPT.md",
    "llms.txt",
    "okf-registry.yaml"
  ],
  "prompt_example": "Use the GitHub repo acme/okf-knowledge..."
}
```

---

## 11. CLI surface

Add subcommands to `tools/okf_tool.py`.

```text
attach-github <url> [--alias ALIAS] [--ref REF] [--path PATH] [--persist-project] [--refresh]
list-attached [--scope all|project|plugin]
refresh <alias>
detach <alias> [--project]
search <alias-or-path> <query> [--type TYPE] [--tag TAG] [--max-results N]
read <alias-or-path> <concept-id> [--neighbors]
related <alias-or-path> <concept-id> [--depth N]
context <alias-or-path> <question> [--mode strict|hybrid] [--max-concepts N]
freshness <alias-or-path>
generate-chatgpt-usage <bundle-path> [--repo OWNER/REPO] [--write]
```

Examples:

```bash
# Attach a bundle from GitHub.
python tools/okf_tool.py attach-github \
  https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture \
  --alias payments

# Search it.
python tools/okf_tool.py search payments "customer identifier normalization"

# Read a concept.
python tools/okf_tool.py read payments data/customer-identifier --neighbors

# Prepare answer context.
python tools/okf_tool.py context payments \
  "Which systems depend on customer identifier normalization?" \
  --mode strict

# Refresh the cache.
python tools/okf_tool.py refresh payments
```

---

## 12. Skill design: `okf-consume-bundle`

Create:

```text
plugins/okf-bundle-smith/skills/okf-consume-bundle/SKILL.md
```

Suggested `SKILL.md`:

```markdown
---
name: okf-consume-bundle
description: Use when a user wants Codex to consume, search, read, cite, review, or answer from an existing OKF bundle, especially a GitHub-hosted bundle URL. Trigger on phrases such as "use this OKF bundle", "attach this OKF bundle", "answer from this bundle", "review against the OKF bundle", "search the OKF bundle", or GitHub URLs pointing to OKF bundle directories.
---

# OKF bundle consumption workflow

Use this skill when the user wants to use an existing Open Knowledge Format bundle as context.

## Required behavior

1. Identify the bundle source:
   - attached alias,
   - local path,
   - GitHub URL,
   - registry entry.
2. If the user gives a GitHub URL, call `okf_attach_github_bundle` unless the bundle is already attached.
3. Read or summarize attach diagnostics:
   - source URL,
   - commit SHA,
   - bundle path,
   - validation errors and warnings.
4. Read `index.md` and `log.md` through the consumer tools when available.
5. Use `okf_search_concepts` for the question or review task.
6. Use `okf_read_concept` for high-scoring concepts.
7. Use `okf_related_concepts` when relationships matter.
8. Use `okf_prepare_answer_context` before final answers that claim to be bundle-grounded.
9. Cite concept IDs or paths after material claims.
10. Clearly distinguish:
    - facts stated directly in the bundle,
    - inferences from bundle content,
    - external knowledge.

## Answer modes

Strict mode:
- Answer only from the OKF bundle.
- Say when the bundle does not contain enough information.
- Do not supplement with general knowledge unless the user asks.

Hybrid mode:
- Use the bundle first.
- Label external knowledge clearly.
- Do not override bundle facts silently.

## Citation style

Prefer concept path citations:

- `[data/customer-identifier]`
- `[systems/payment-router]`
- `[controls/customer-data-classification]`

If citing a specific section, use:

- `[systems/payment-router#dependencies]`

## Refusal / limitation handling

If the bundle cannot be fetched, say why and suggest one of:

- provide a local path,
- clone the repository into the workspace,
- check GitHub credentials,
- use a public repo URL,
- specify the bundle path inside the repo.
```

---

## 13. Answering contract

The consumer extension should enforce a clear answer contract.

### 13.1 Strict mode

Use when the user says:

```text
answer from the bundle
use only the OKF bundle
strict bundle mode
```

Rules:

- Only use retrieved OKF concept content.
- Cite concept IDs.
- If evidence is missing, say so.
- Do not use web or model memory to fill gaps.
- Report freshness limitations.

Example answer style:

```text
The bundle identifies three systems that depend on customer identifier normalization:

1. Customer Identity Service — owns canonical normalization and publishes normalized identifiers. [systems/customer-identity-service]
2. Payment Router — consumes normalized identifiers before routing decisions. [systems/payment-router]
3. Audit Event Store — stores the normalized identifier for traceability and investigation. [systems/audit-event-store]

The bundle does not state whether downstream fraud systems consume the normalized identifier directly. That would need a follow-up source or bundle update.
```

### 13.2 Hybrid mode

Use when the user asks for analysis, advice, or implementation planning where external reasoning is helpful.

Rules:

- Start from bundle facts.
- Label inference explicitly.
- Label external/general knowledge explicitly.
- Never hide conflicts between bundle and code.

Example:

```text
Bundle facts:
- The Payment Router depends on normalized customer identifiers. [systems/payment-router]
- Customer identifiers are classified as confidential customer data. [controls/customer-data-classification]

Inference:
- A migration that changes identifier format should be treated as architecture-significant because it crosses routing and audit boundaries.

External engineering practice:
- I would add backward-compatible parsing and telemetry before cutover, but that specific rollout pattern is not documented in the bundle.
```

---

## 14. ChatGPT support design

ChatGPT support should be treated as a companion output, not as the same runtime as Codex.

### 14.1 Generate `CHATGPT.md`

For each bundle, generate:

```text
<bundle-root>/CHATGPT.md
```

Template:

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

## Suggested prompt

Use this GitHub repository as an OKF bundle source.
Read `<bundle-root>/index.md` and `<bundle-root>/log.md` first.
Then answer from the bundle and cite concept paths.
```

### 14.2 Generate root `llms.txt`

For repos with multiple bundles:

```text
llms.txt
```

Example:

```text
# OKF bundle repository

This repository contains Open Knowledge Format bundles for agent consumption.

## Bundles

- Payments Architecture: bundles/payments-architecture/index.md
- AI Governance: bundles/ai-governance/index.md

## Usage

When answering questions about a bundle, read its index.md and log.md first, then follow internal Markdown links. Cite concept paths.
```

### 14.3 Generate `okf-registry.yaml`

At the repository root:

```yaml
version: 1
bundles:
  - id: payments
    title: Payments Architecture
    path: bundles/payments-architecture
    chatgpt_instructions: bundles/payments-architecture/CHATGPT.md
    index: bundles/payments-architecture/index.md
    log: bundles/payments-architecture/log.md
```

### 14.4 Prompt examples for ChatGPT

Simple:

```text
Use the GitHub repo acme/okf-knowledge.
Use the OKF bundle at bundles/payments-architecture.
Read index.md and log.md first.
Answer from the bundle and cite concept paths.

Question: Which services depend on customer identifier normalization?
```

Strict:

```text
Use only the OKF bundle at acme/okf-knowledge/bundles/payments-architecture.
Do not use external knowledge unless I ask.
If the bundle does not contain enough information, say so.
Cite concept paths.
```

Review:

```text
Use the OKF bundle at acme/okf-knowledge/bundles/payments-architecture.
Review this proposed change for conflicts with documented architecture.
Check ownership boundaries, data classification, controls, and deprecated integration paths.
Cite concept paths.
```

---

## 15. Project guidance templates

### 15.1 Bundle repository `AGENTS.md`

Generate this at the root of a bundle repository:

```markdown
# AGENTS.md

## OKF bundle usage

This repository contains Open Knowledge Format bundles under `bundles/`.

Before answering questions about a domain covered by a bundle:

1. Read `okf-registry.yaml` if present.
2. Identify the relevant bundle.
3. Read that bundle's `index.md`.
4. Read that bundle's `log.md`.
5. Traverse bundle-relative Markdown links before broad search.
6. Prefer bundle content over general knowledge for domain-specific answers.
7. Distinguish direct bundle facts from inference.
8. Cite concept paths.
9. Report freshness limitations.

Before changing a bundle:

1. Preserve concept IDs unless a rename is intentional.
2. Preserve unknown frontmatter fields.
3. Update affected indexes.
4. Add or update `log.md`.
5. Run OKF validation.
```

### 15.2 Consuming code repository `AGENTS.md`

Generate this for a code repository that consumes an external OKF bundle:

```markdown
# AGENTS.md

## OKF domain context

Use the OKF bundle alias `payments` as primary domain context for payments architecture work.

Bundle source:
`https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture`

Before architecture-significant code changes:

1. Attach or refresh the OKF bundle.
2. Read the bundle index and log.
3. Search concepts related to the files and domain terms being changed.
4. Check ownership boundaries, data classification, controls, and deprecated paths.
5. If code and bundle conflict, call out the conflict instead of silently choosing one.
6. Cite OKF concept paths in review comments or design notes.
```

---

## 16. Security and governance

### 16.1 Default security posture

Consumer mode should be read-only and conservative.

Rules:

- Do not execute scripts from fetched bundle repositories.
- Do not follow symlinks that escape the bundle root.
- Do not read files outside the selected bundle path except approved registry files.
- Do not fetch external URLs referenced in citations unless a separate tool explicitly does so.
- Do not store GitHub credentials in plugin state.
- Do not print secrets from Git config or environment variables.
- Record commit SHA for every attached bundle.
- Report whether the bundle came from a branch, tag, or pinned commit.

### 16.2 Enterprise controls

Add optional policy file support later:

```text
.okf/policy.yaml
```

Example:

```yaml
version: 1
allowed_hosts:
  - github.com
  - github.mybank.example
allowed_owners:
  - acme
  - platform-architecture
require_pinned_refs: false
max_bundle_size_mb: 50
max_concepts: 5000
allow_private_repos: true
classification_defaults:
  unknown: internal
```

### 16.3 Bank-grade extensions

For regulated enterprise usage, add optional frontmatter awareness for:

```yaml
owner: payments-architecture-team
steward: enterprise-architecture
classification: internal
jurisdiction: EU
review_cycle: quarterly
valid_from: 2026-06-01
valid_until: 2026-12-31
control_refs:
  - DORA-ICT-RISK-001
  - EBA-OUTSOURCING-014
```

The consumer should surface these fields but not require them for base OKF conformance.

---

## 17. Implementation plan

### Phase 1: Local consumer core

Deliver:

- `okf_index.py`
- `okf_retrieve.py`
- `okf_context.py`
- CLI commands for `search`, `read`, `related`, `context`, `freshness`
- Tests using existing example bundles

Acceptance criteria:

- A local bundle can be indexed.
- Search returns ranked concept results.
- `read` returns body, frontmatter, outlinks, and inlinks.
- `context` returns a compact answer context pack.
- Existing producer tests still pass.

### Phase 2: GitHub attach

Deliver:

- `okf_git.py`
- `attach-github`, `refresh`, `list-attached`, `detach`
- Plugin-data cache
- Project-persistent `.okf/attachments.yaml`
- URL parser tests
- Git clone integration tests where feasible, plus mocked Git tests

Acceptance criteria:

- A GitHub tree URL can be attached by alias.
- Commit SHA is recorded.
- Sparse checkout works for subdirectory bundles.
- Refresh detects changed commit SHA.
- Attach fails safely on invalid path or invalid bundle.

### Phase 3: MCP consumer tools

Deliver:

- MCP tools listed in section 10
- CLI/MCP parity tests
- README updates

Acceptance criteria:

- Codex can attach, search, read, and prepare context through MCP.
- Tool outputs are deterministic JSON.
- Errors are actionable and do not expose credentials.

### Phase 4: Skill and documentation

Deliver:

- `skills/okf-consume-bundle/SKILL.md`
- `references/okf-consumption-contract.md`
- `references/github-bundle-url-syntax.md`
- `references/chatgpt-okf-usage-template.md`
- README usage examples

Acceptance criteria:

- The skill triggers on GitHub OKF bundle prompts.
- The README has copy-paste usage examples.
- Documentation distinguishes Codex, ChatGPT, and CLI usage.

### Phase 5: ChatGPT support files

Deliver:

- `generate-chatgpt-usage` command
- `okf_generate_chatgpt_usage` MCP tool
- Templates for `CHATGPT.md`, `llms.txt`, `okf-registry.yaml`, and `AGENTS.md`

Acceptance criteria:

- Running the command creates clear ChatGPT usage instructions.
- Generated files do not violate OKF bundle conventions.
- Bundle repos become easier to use through the ChatGPT GitHub connector.

### Phase 6: Optional advanced retrieval

Deliver later:

- Optional vector index.
- Optional remote MCP service.
- Optional GitHub Enterprise host support.
- Optional policy enforcement.
- Optional source/citation quality scoring.

---

## 18. Proposed file-level changes

### 18.1 `tools/okf_git.py`

Responsibilities:

- Parse GitHub bundle URLs.
- Resolve refs.
- Clone/fetch repos.
- Configure sparse checkout.
- Return local bundle path and commit SHA.

Key functions:

```python
def parse_github_bundle_url(url: str) -> GitHubBundleRef: ...
def resolve_github_ref(ref: GitHubBundleRef) -> GitHubBundleRef: ...
def attach_github_bundle(ref: GitHubBundleRef, cache_root: Path, refresh: bool = False) -> ResolvedBundleRef: ...
def refresh_github_bundle(resolved: ResolvedBundleRef) -> ResolvedBundleRef: ...
```

### 18.2 `tools/okf_index.py`

Responsibilities:

- Build concept index from bundle path.
- Extract frontmatter, title, description, tags, headings, links, citations.
- Preserve concept IDs.
- Write/read JSON index files.

Key functions:

```python
def build_concept_index(bundle_path: Path, source: dict) -> BundleIndex: ...
def load_index(index_path: Path) -> BundleIndex: ...
def save_index(index: BundleIndex, index_path: Path) -> None: ...
```

### 18.3 `tools/okf_retrieve.py`

Responsibilities:

- Search index.
- Read concepts.
- Resolve inlinks/outlinks.
- Trace related concepts.

Key functions:

```python
def search_concepts(index: BundleIndex, query: str, filters: SearchFilters) -> list[SearchResult]: ...
def read_concept(index: BundleIndex, concept_id: str) -> ConceptRead: ...
def related_concepts(index: BundleIndex, concept_id: str, depth: int) -> RelatedGraph: ...
```

### 18.4 `tools/okf_context.py`

Responsibilities:

- Prepare compact context packs for Codex answers.
- Enforce strict/hybrid answer instructions.
- Generate freshness reports.
- Generate ChatGPT usage files.

Key functions:

```python
def prepare_answer_context(index: BundleIndex, question: str, options: ContextOptions) -> AnswerContext: ...
def freshness_report(index: BundleIndex) -> FreshnessReport: ...
def generate_chatgpt_usage(bundle_path: Path, options: ChatGPTUsageOptions) -> GeneratedUsageFiles: ...
```

### 18.5 `tools/okf_tool.py`

Add CLI subcommands from section 11.

### 18.6 `tools/okf_mcp_server.py`

Add MCP tools from section 10.

### 18.7 `README.md`

Add sections:

- “Consume an OKF bundle from GitHub”
- “Use attached bundles in Codex”
- “Use OKF bundles from ChatGPT”
- “Strict vs hybrid answer modes”
- “Security model for remote bundles”

---

## 19. Testing strategy

### 19.1 Unit tests

Add tests for:

- GitHub URL parsing.
- Branch/path ambiguity.
- Registry parsing.
- Concept ID generation.
- Frontmatter extraction.
- Markdown link extraction.
- Citation extraction.
- Search ranking.
- Context budget trimming.
- Freshness reporting.
- Path traversal defense.
- Symlink escape defense.

### 19.2 Fixture bundles

Add fixtures:

```text
tests/fixtures/consumer/
├── simple-bundle/
├── multi-bundle-repo/
├── broken-links-bundle/
├── stale-bundle/
├── malformed-frontmatter-bundle/
└── symlink-escape-bundle/
```

### 19.3 CLI smoke tests

Examples:

```bash
python tools/okf_tool.py search tests/fixtures/consumer/simple-bundle "customer identifier"
python tools/okf_tool.py read tests/fixtures/consumer/simple-bundle data/customer-identifier
python tools/okf_tool.py context tests/fixtures/consumer/simple-bundle "Who owns customer identity?"
```

### 19.4 MCP tests

For each MCP tool:

- Validate input schema.
- Validate successful response shape.
- Validate error response shape.
- Check CLI/MCP parity where applicable.

### 19.5 Network-dependent tests

Do not make normal CI depend on live GitHub network calls.

Use:

- unit tests with mocked `git` subprocess calls;
- optional integration tests behind an environment flag:

```bash
OKF_INTEGRATION_GITHUB=1 python -m unittest tests.test_okf_git_integration -v
```

---

## 20. Error handling

### 20.1 User-facing error examples

Invalid GitHub URL:

```text
Could not parse this as a supported GitHub bundle URL. Use one of:
- https://github.com/org/repo/tree/main/path/to/bundle
- org/repo//path/to/bundle?ref=main
```

Private repo without credentials:

```text
The repository could not be cloned. If it is private, configure Git credentials or clone it locally and attach the local path instead.
```

No bundle at path:

```text
The path exists, but it does not look like an OKF bundle. I found no Markdown concept files and no index.md under the selected directory.
```

Validation errors:

```text
The bundle was fetched, but strict mode is blocked because 3 concept files have malformed frontmatter. Run validation for details or use a repaired bundle.
```

Multiple bundles found:

```text
The repository contains multiple candidate OKF bundles. Specify one:
- bundles/payments-architecture
- bundles/ai-governance
- docs/okf/data-catalog
```

---

## 21. Documentation examples to add

### 21.1 README quick start

````markdown
## Consume a GitHub-hosted OKF bundle

Attach a bundle:

```bash
python tools/okf_tool.py attach-github \
  https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture \
  --alias payments
```

Ask Codex:

```text
Use OKF Bundle Smith and the attached `payments` bundle.
Use strict bundle mode.
Question: Which systems depend on customer identifier normalization?
```
````

### 21.2 README Codex prompt

```text
Use OKF Bundle Smith to attach this GitHub-hosted OKF bundle:
https://github.com/acme/okf-knowledge/tree/main/bundles/payments-architecture

Use alias `payments`.
Use strict bundle-grounded mode.
Answer with concept-path citations.

Question: What controls apply to customer identifier data?
```

### 21.3 README ChatGPT prompt

```text
Use the GitHub repo acme/okf-knowledge.
Use the OKF bundle under bundles/payments-architecture.
Read index.md and log.md first.
Answer from the bundle, cite concept paths, and say if the bundle lacks evidence.

Question: Which services depend on customer identifier normalization?
```

---

## 22. Acceptance criteria for the full feature

The feature is complete when all of the following are true:

1. A user can provide a GitHub URL to a bundle directory and attach it with one command or one Codex prompt.
2. The plugin records the source URL, ref, path, commit SHA, validation status, and concept count.
3. The plugin can search concept titles, descriptions, tags, headings, and body content.
4. The plugin can read a concept by concept ID.
5. The plugin can return related concepts using internal Markdown links.
6. The plugin can prepare a compact answer context pack with concept-path citations.
7. Strict mode prevents unsupported answers and reports missing evidence.
8. Hybrid mode labels inference and external knowledge.
9. ChatGPT support files can be generated for a bundle repository.
10. CLI and MCP surfaces have parity.
11. Existing authoring, validation, graphing, visualization, and packaging functionality still works.
12. Tests cover URL parsing, indexing, retrieval, context generation, and security constraints.

---

## 23. Suggested first PR

Keep the first PR small enough to review.

### PR title

```text
Add OKF consumer core for local bundles
```

### Scope

- Add `okf_index.py`.
- Add `okf_retrieve.py`.
- Add `okf_context.py`.
- Add CLI commands:
  - `search`
  - `read`
  - `related`
  - `context`
  - `freshness`
- Add `skills/okf-consume-bundle/SKILL.md` in draft form.
- Add tests using existing example bundles.

### Defer

- GitHub attach.
- Persistent `.okf/attachments.yaml`.
- ChatGPT usage file generation.
- Vector search.

Rationale: consuming local bundles first gives a stable retrieval core. GitHub attach then becomes a source adapter, not the foundation of the feature.

---

## 24. Suggested second PR

### PR title

```text
Add GitHub attach and cached bundle indexing
```

### Scope

- Add `okf_git.py`.
- Add `attach-github`, `refresh`, `list-attached`, and `detach` CLI commands.
- Add plugin-data cache and state file.
- Add MCP tools:
  - `okf_attach_github_bundle`
  - `okf_list_attached_bundles`
  - `okf_refresh_bundle`
- Add URL parsing and mocked Git tests.

---

## 25. Suggested third PR

### PR title

```text
Add MCP consumer tools and ChatGPT usage generation
```

### Scope

- Add MCP tools for search, read, related, context, freshness.
- Add `okf_generate_chatgpt_usage`.
- Add templates for `CHATGPT.md`, `llms.txt`, `okf-registry.yaml`, and `AGENTS.md`.
- Update README with Codex and ChatGPT examples.

---

## 26. Open design questions

1. Should project-persistent attachments be written to `.okf/attachments.yaml`, `okf-registry.yaml`, or `.codex/okf.toml`?
   - Recommendation: `.okf/attachments.yaml`, because it is OKF-specific and tool-neutral.

2. Should the MCP tool ever answer directly?
   - Recommendation: no for MVP. The MCP tool should prepare evidence/context; Codex should produce the final answer.

3. Should vector search be included?
   - Recommendation: no for MVP. Add optional vector search later.

4. Should `CHATGPT.md` live inside the bundle root even though it is not an OKF concept?
   - Recommendation: yes, but document that `CHATGPT.md` is an agent instruction file, not a concept. The validator should either ignore it or allow it as a reserved helper file. Alternatively put it at repository root with bundle-specific sections.

5. Should GitHub Enterprise be supported?
   - Recommendation: design parser with `host`, but initially test only `github.com`. Add allowlisted enterprise hosts later.

---

## 27. References

- OKF v0.1 spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
- Google Cloud OKF announcement: https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing
- OKF Bundle Smith repository: https://github.com/ThomasRohde/okf-bundle-smith
- OKF Bundle Smith plugin README: https://github.com/ThomasRohde/okf-bundle-smith/blob/master/plugins/okf-bundle-smith/README.md
- Codex skills documentation: https://developers.openai.com/codex/skills
- Codex plugin build documentation: https://developers.openai.com/codex/plugins/build
- Codex MCP documentation: https://developers.openai.com/codex/mcp
- Codex `AGENTS.md` documentation: https://developers.openai.com/codex/guides/agents-md
- ChatGPT GitHub connector documentation: https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt
