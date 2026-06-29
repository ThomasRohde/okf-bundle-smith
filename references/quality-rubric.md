# OKF bundle quality rubric

Use this rubric after conformance checks pass.

## 1. Purpose fit

- The bundle has a clear intended consumer.
- Concepts are scoped to a real task or decision class.
- The root `index.md` tells an agent where to start.

## 2. Concept design

- Each concept file captures one durable concept.
- Concept file paths are stable IDs.
- Types are descriptive and consistent.
- Similar concepts are not duplicated.

## 3. Source quality

- Claims are traceable to sources.
- Primary sources are preferred.
- Time-sensitive claims include dates.
- Unsupported assumptions are marked as assumptions.

## 4. Metadata quality

- Recommended frontmatter is present where possible.
- Titles are human-readable.
- Descriptions distinguish concepts from one another.
- `resource` values are real URIs, not invented placeholders.
- Tags add cross-cutting categories rather than repeating directories.

## 5. Graph quality

- Important relationships are expressed as Markdown links.
- Index files support progressive disclosure.
- There are few or no accidental orphans.
- Broken links are intentional and documented.

## 6. Maintainability

- Changes are logged.
- Files are concise and reviewable.
- Unknown frontmatter fields are preserved during updates.
- Generated artifacts can be rebuilt deterministically.

## 7. Enterprise readiness

For regulated or internal use, add:

- owner/steward metadata;
- source-system lineage;
- classification/sensitivity tags;
- freshness expectations;
- review cadence;
- control mappings;
- clear boundary between public facts, internal facts, and inferred relationships.
