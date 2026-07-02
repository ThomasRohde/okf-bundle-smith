from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from okf_consume import attach_local_bundle, mcp_diagnostics, overview_bundle  # noqa: E402
from okf_context import bundle_overview, generate_chatgpt_usage, prepare_answer_context  # noqa: E402
from okf_core import scan_bundle  # noqa: E402
from okf_index import assert_safe_bundle_tree, build_concept_index  # noqa: E402
from okf_retrieve import read_concept, related_concepts, search_concepts  # noqa: E402


def write_consumer_bundle(root: Path) -> None:
    (root / "index.md").write_text("# Consumer Test Bundle\n\n- [Customer Identifier](data/customer-identifier.md)\n", encoding="utf-8")
    (root / "log.md").write_text("# Log\n\n## 2026-06-29\n\n- Created fixture.\n", encoding="utf-8")
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "systems").mkdir(parents=True, exist_ok=True)
    (root / "data" / "customer-identifier.md").write_text(
        """---
type: Data Concept
title: Customer Identifier
description: Canonical customer identifier used across payment systems.
tags: [customer, identity, payments]
timestamp: 2026-06-29T00:00:00Z
---

# Summary

The customer identifier is normalized before payment routing. It is owned by the
Customer Identity Service and used by the Payment Router for routing decisions.

# Relationships

See [Customer Identity Service](/systems/customer-identity-service.md).

# Citations

- [ADR-014](https://example.com/adr-014)
""",
        encoding="utf-8",
    )
    (root / "systems" / "customer-identity-service.md").write_text(
        """---
type: System
title: Customer Identity Service
description: Service that owns customer identity normalization.
tags: [customer, identity, service]
timestamp: 2026-06-28T00:00:00Z
---

# Summary

The Customer Identity Service owns canonical customer identifier normalization
and publishes identifiers for payment routing and audit workflows.

# Relationships

See [Customer Identifier](/data/customer-identifier.md).
""",
        encoding="utf-8",
    )


def write_concept(root: Path, rel: str, ctype: str, title: str, description: str, tags: list[str], body: str) -> None:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"---\ntype: {ctype}\ntitle: {title}\ndescription: {description}\n"
        f"tags: [{', '.join(tags)}]\ntimestamp: 2026-06-29T00:00:00Z\n---\n\n{body}\n",
        encoding="utf-8",
    )


def write_hub_bundle(root: Path) -> None:
    """One well-connected hub plus three keyword hits in other directories."""
    (root / "index.md").write_text("# Hub Fixture\n\n- [Gadget Hub](concepts/hub.md)\n", encoding="utf-8")
    (root / "log.md").write_text("# Log\n\n## 2026-06-29\n\n- Created fixture.\n", encoding="utf-8")
    links = "\n".join(f"- [Bolt {i}](/parts/bolt-{i}.md)" for i in range(1, 7))
    write_concept(root, "concepts/hub.md", "System", "Gadget Hub", "Central gadget hub concept.", ["gadget"],
                  f"# Summary\n\nGadget hub overview.\n\n# Relationships\n\n{links}")
    for i in range(1, 7):
        write_concept(root, f"parts/bolt-{i}.md", "Reference", f"Bolt {i}", f"Fastener part number {i}.", ["parts"],
                      "# Summary\n\nA plain fastener part.")
    write_concept(root, "data/gadget-alpha.md", "Dataset", "Gadget Alpha", "Alpha gadget dataset.", ["gadget"],
                  "# Summary\n\nGadget records for alpha.")
    write_concept(root, "systems/gadget-beta.md", "System", "Gadget Beta", "Beta gadget system.", ["gadget"],
                  "# Summary\n\nGadget services for beta.")
    write_concept(root, "processes/gadget-gamma.md", "Process", "Gadget Gamma", "Gamma gadget process.", ["gadget"],
                  "# Summary\n\nGadget workflow for gamma.")


class OkfConsumerTests(unittest.TestCase):
    def test_index_search_read_related_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_consumer_bundle(root)

            index = build_concept_index(root, source={"kind": "local", "url": str(root), "bundle_path": "."}, alias="fixture")
            results = search_concepts(index, "customer identifier routing")
            concept_ids = [item["concept_id"] for item in results]

            self.assertEqual("okf-consumer-index/v1", index["schema_version"])
            self.assertIn("data/customer-identifier", concept_ids)
            concept = read_concept(index, "data/customer-identifier", include_neighbors=True)
            self.assertEqual("Customer Identifier", concept["title"])
            self.assertEqual(["systems/customer-identity-service"], concept["outlinks"])
            self.assertEqual("systems/customer-identity-service", concept["neighbors"][0]["concept_id"])

            related = related_concepts(index, "data/customer-identifier", depth=1)
            self.assertEqual("data/customer-identifier", related["start"])
            self.assertEqual("systems/customer-identity-service", related["related"][0]["concept_id"])

            context = prepare_answer_context(index, "Which systems use customer identifiers?", {"mode": "strict"})
            self.assertFalse(context["blocked"])
            self.assertTrue(context["concepts"])
            self.assertEqual("2026-06-29", context["freshness"]["latest_log_entry"])
            self.assertIn("inventory", context)
            self.assertEqual("index.md", context["entrypoints"]["index"]["citation_id"])

    def test_direct_hits_are_not_evicted_by_link_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_hub_bundle(root)
            index = build_concept_index(root, alias="hub")

            context = prepare_answer_context(index, "gadget hub", {"mode": "strict", "max_concepts": 4})
            citation_ids = [item["citation_id"] for item in context["concepts"]]

            # All four direct hits survive; the hub's six neighbors take no slot.
            self.assertEqual(4, len(citation_ids))
            self.assertIn("concepts/hub", citation_ids)
            for concept_id in ("data/gadget-alpha", "systems/gadget-beta", "processes/gadget-gamma"):
                self.assertIn(concept_id, citation_ids)

            # With spare slots, neighbors fill the remainder of the pack.
            wide = prepare_answer_context(index, "gadget hub", {"mode": "strict", "max_concepts": 8})
            wide_ids = [item["citation_id"] for item in wide["concepts"]]
            self.assertEqual(8, len(wide_ids))
            self.assertTrue(any(concept_id.startswith("parts/bolt-") for concept_id in wide_ids))

    def test_weak_direct_hits_beat_neighborhood_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.md").write_text("# Weak Fixture\n\n- [Gadget Hub](concepts/hub.md)\n", encoding="utf-8")
            (root / "log.md").write_text("# Log\n\n## 2026-06-29\n\n- Created fixture.\n", encoding="utf-8")
            links = "\n".join(f"- [Bolt {i}](/parts/bolt-{i}.md)" for i in range(1, 8))
            write_concept(root, "concepts/hub.md", "System", "Gadget Hub", "Central gadget hub concept.", ["gadget"],
                          f"# Summary\n\nGadget hub overview.\n\n# Relationships\n\n{links}")
            for i in range(1, 8):
                write_concept(root, f"parts/bolt-{i}.md", "Reference", f"Bolt {i}", f"Fastener part number {i}.", ["parts"],
                              "# Summary\n\nA plain fastener part.")
            # Direct matches whose only signal is a single body token: they score
            # far below the hub's injected link-neighborhood entries.
            for name in ("alpha", "beta", "gamma"):
                write_concept(root, f"notes/{name}.md", "Reference", f"{name.title()} Notes",
                              f"Working notes for {name}.", ["notes"],
                              f"# Summary\n\nThe gadget assembly for {name}.")
            index = build_concept_index(root, alias="weak")

            context = prepare_answer_context(index, "gadget hub", {"mode": "strict", "max_concepts": 4})
            citation_ids = [item["citation_id"] for item in context["concepts"]]

            self.assertEqual(
                {"concepts/hub", "notes/alpha", "notes/beta", "notes/gamma"},
                set(citation_ids),
            )
            # Search results report direct matches only.
            self.assertTrue(context["search_results"])
            self.assertTrue(all(item["reason"] != "link-neighborhood" for item in context["search_results"]))

    def test_link_depth_zero_packs_direct_hits_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_hub_bundle(root)
            index = build_concept_index(root, alias="hub")

            context = prepare_answer_context(index, "gadget hub", {"mode": "strict", "max_concepts": 8, "link_depth": 0})
            citation_ids = [item["citation_id"] for item in context["concepts"]]

            # Spare slots stay empty: no link-derived concept enters the pack.
            self.assertEqual(
                {"concepts/hub", "data/gadget-alpha", "systems/gadget-beta", "processes/gadget-gamma"},
                set(citation_ids),
            )

    def test_context_pack_is_slim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_hub_bundle(root)
            index = build_concept_index(root, alias="hub")

            context = prepare_answer_context(index, "gadget hub", {"mode": "strict"})

            # Concept bodies live in `concepts` only; search results carry no excerpt.
            self.assertTrue(context["search_results"])
            for result in context["search_results"]:
                self.assertNotIn("excerpt", result)
            # Validation ships as counts, not the full issue list.
            self.assertEqual({"errors", "warnings"}, set(context["validation"].keys()))

    def test_context_inventory_is_trimmed_but_overview_is_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tags = [f"tag-{i:02d}" for i in range(15)]
            write_concept(root, "concepts/tagged.md", "Reference", "Tagged", "A concept with many tags.", tags,
                          "# Summary\n\nA tag-heavy concept.")
            index = build_concept_index(root, alias="tags")

            context = prepare_answer_context(index, "tagged", {"mode": "strict"})
            overview = bundle_overview(index)

            self.assertEqual(10, len(context["inventory"]["tags"]))
            self.assertEqual(15, context["inventory"]["tag_count"])
            self.assertEqual(15, len(overview["inventory"]["tags"]))

    def test_context_respects_total_char_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            long_body = "# Summary\n\n" + ("saga detail " * 500)
            for name in ("alpha", "beta", "gamma"):
                write_concept(root, f"notes/saga-{name}.md", "Reference", f"Saga {name.title()}",
                              f"The {name} saga chronicle.", ["saga"], long_body)
            index = build_concept_index(root, alias="saga")

            context = prepare_answer_context(index, "saga", {"mode": "strict", "max_total_chars": 5000})
            concepts = context["concepts"]

            self.assertEqual(3, len(concepts))
            self.assertLessEqual(sum(len(item["excerpt"]) for item in concepts), 5000)
            # Trimming keeps a useful floor per concept instead of emptying the tail.
            self.assertTrue(all(len(item["excerpt"]) >= 300 for item in concepts))

            # Even degenerate budgets are enforced strictly.
            tiny = prepare_answer_context(index, "saga", {"mode": "strict", "max_total_chars": 5})
            self.assertLessEqual(sum(len(item["excerpt"]) for item in tiny["concepts"]), 5)

    def test_strict_context_blocks_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "broken.md").write_text("---\ntitle: Broken\n---\n\n# Body\nMissing required type.\n", encoding="utf-8")

            index = build_concept_index(root, alias="broken")
            context = prepare_answer_context(index, "What is broken?", {"mode": "strict"})

            self.assertTrue(context["blocked"])
            self.assertGreater(context["validation"]["errors"], 0)
            # The blocked pack names the blocking issues so repair needs no second call.
            self.assertTrue(context["validation_issues"])
            self.assertTrue(all(issue["severity"] == "error" for issue in context["validation_issues"]))

    def test_generated_helper_markdown_is_not_a_concept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_consumer_bundle(root)
            (root / "CHATGPT.md").write_text("# Helper\n\nThis is not a concept.\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Agent helper\n\nThis is not a concept.\n", encoding="utf-8")

            report = scan_bundle(root)

            self.assertEqual([], report.errors)
            self.assertFalse(any(concept.rel == "CHATGPT.md" for concept in report.concepts))
            self.assertFalse(any(concept.rel == "AGENTS.md" for concept in report.concepts))

    def test_generate_chatgpt_usage_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bundles" / "payments"
            root.mkdir(parents=True)
            write_consumer_bundle(root)

            payload = generate_chatgpt_usage(root, {"repo_name": "acme/okf-knowledge", "write_files": False})

            self.assertEqual([], payload["created"])
            self.assertIn("acme/okf-knowledge", payload["prompt_example"])
            self.assertIn("bundles/payments/index.md", payload["chatgpt_md"])
            self.assertEqual(str(root / "AGENTS.md"), payload["agents_md_path"])
            self.assertIn("No OKF-specific tools are required.", payload["agents_md"])
            self.assertIn("When The Bundle Points To External Data", payload["agents_md"])
            self.assertEqual(str(root.parent.parent / "AGENTS.md"), payload["repo_agents_md_path"])
            self.assertIn("When a task concerns this bundle's domain", payload["repo_agents_md_snippet"])
            self.assertIn("bundles/payments/index.md", payload["repo_agents_md_snippet"])
            self.assertFalse((root / "AGENTS.md").exists())

    def test_generate_chatgpt_usage_writes_bundle_agents_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bundle"
            root.mkdir()
            write_consumer_bundle(root)

            payload = generate_chatgpt_usage(root, {"write_files": True, "include_llms_txt": False, "include_registry": False})

            self.assertIn(str(root / "AGENTS.md"), payload["created"])
            self.assertTrue((root / "AGENTS.md").is_file())
            self.assertIn("How to Use This OKF Bundle", (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_generate_chatgpt_usage_repo_root_writes_are_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bundles" / "payments"
            root.mkdir(parents=True)
            write_consumer_bundle(root)
            repo_root = root.parent.parent

            payload = generate_chatgpt_usage(root, {"write_files": True})

            # Default writes stay inside the bundle directory.
            self.assertIn(str(root / "CHATGPT.md"), payload["created"])
            self.assertIn(str(root / "AGENTS.md"), payload["created"])
            self.assertFalse((repo_root / "llms.txt").exists())
            self.assertFalse((repo_root / "okf-registry.yaml").exists())
            # The repo-root helper content is still previewed in the payload.
            self.assertIsNotNone(payload["llms_txt"])
            self.assertIsNotNone(payload["okf_registry_yaml"])

            generate_chatgpt_usage(root, {"write_files": True, "include_llms_txt": True, "include_registry": True})

            self.assertTrue((repo_root / "llms.txt").is_file())
            self.assertTrue((repo_root / "okf-registry.yaml").is_file())

    def test_generate_chatgpt_usage_can_skip_bundle_agents_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bundle"
            root.mkdir()
            write_consumer_bundle(root)

            payload = generate_chatgpt_usage(root, {"write_files": True, "include_agents_md": False, "include_llms_txt": False, "include_registry": False})

            self.assertNotIn(str(root / "AGENTS.md"), payload["created"])
            self.assertIsNone(payload["agents_md"])
            self.assertFalse((root / "AGENTS.md").exists())

    def test_attach_local_and_overview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            root = Path(tmp) / "bundle"
            root.mkdir()
            write_consumer_bundle(root)
            old_data_dir = os.environ.get("OKF_BUNDLE_SMITH_DATA_DIR")
            os.environ["OKF_BUNDLE_SMITH_DATA_DIR"] = str(data_dir)
            try:
                attached = attach_local_bundle(root, alias="local-fixture")
                overview = overview_bundle("local-fixture")
            finally:
                if old_data_dir is None:
                    os.environ.pop("OKF_BUNDLE_SMITH_DATA_DIR", None)
                else:
                    os.environ["OKF_BUNDLE_SMITH_DATA_DIR"] = old_data_dir

            self.assertEqual("local-fixture", attached["alias"])
            self.assertEqual("local", attached["kind"])
            self.assertEqual(2, attached["concept_count"])
            self.assertEqual(2, overview["inventory"]["concept_count"])
            self.assertIn("central_concepts", overview["inventory"])

    def test_mcp_diagnostics_reports_server(self) -> None:
        diagnostics = mcp_diagnostics()

        self.assertTrue(diagnostics["declared"])
        self.assertEqual("okf-tools", diagnostics["server_name"])
        self.assertIn("manual_probe", diagnostics)

    def test_symlink_escape_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bundle"
            outside = Path(tmp) / "outside.md"
            root.mkdir()
            outside.write_text("outside", encoding="utf-8")
            try:
                os.symlink(outside, root / "escape.md")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are not available in this environment")

            with self.assertRaises(ValueError):
                assert_safe_bundle_tree(root)


if __name__ == "__main__":
    unittest.main()
