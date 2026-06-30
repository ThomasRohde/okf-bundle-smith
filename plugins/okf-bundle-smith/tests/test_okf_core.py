from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from okf_core import (  # noqa: E402
    MD_LINK_RE,
    add_log_entry,
    build_visualization,
    bundle_stats,
    generate_indexes,
    graph,
    package_bundle,
    scan_bundle,
    scaffold_bundle,
)


CONCEPT_BODY = """# Summary

This concept is intentionally long enough to clear the lightweight usefulness
check in the OKF validator. It describes one durable idea and provides enough
body content for downstream agents to decide whether the concept is relevant.

# Relationships

This concept is discoverable through generated index files.
"""


def write_concept(path: Path, title: str = "Payment API") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "type: API",
                f"title: {title}",
                "description: A durable API concept used by the test bundle.",
                "tags: [test, api]",
                "timestamp: 2026-06-29T00:00:00Z",
                "---",
                "",
                CONCEPT_BODY,
            ]
        ),
        encoding="utf-8",
    )


class OkfCoreTests(unittest.TestCase):
    def test_crlf_frontmatter_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "concepts" / "payment-api.md"
            write_concept(path)
            path.write_text(path.read_text(encoding="utf-8").replace("\n", "\r\n"), encoding="utf-8")

            report = scan_bundle(root)

            self.assertEqual([], report.errors)
            self.assertEqual(1, len(report.concepts))

    def test_generate_indexes_creates_root_and_ancestor_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_concept(root / "concepts" / "apis" / "payment-api.md")

            written = generate_indexes(root)

            self.assertIn(root / "index.md", written)
            self.assertIn(root / "concepts" / "index.md", written)
            self.assertIn(root / "concepts" / "apis" / "index.md", written)
            self.assertIn("[Concepts](concepts/index.md)", (root / "index.md").read_text(encoding="utf-8"))
            self.assertIn("[Apis](apis/index.md)", (root / "concepts" / "index.md").read_text(encoding="utf-8"))

    def test_package_bundle_excludes_output_archive_inside_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_concept(root / "concepts" / "payment-api.md")
            generate_indexes(root)
            output = root / "bundle.zip"

            package_bundle(root, output)

            with zipfile.ZipFile(output) as archive:
                self.assertNotIn("bundle.zip", archive.namelist())
                self.assertIn("concepts/payment-api.md", archive.namelist())

    def test_scaffold_bundle_creates_valid_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "new-bundle"

            written = scaffold_bundle(root, title="EU AI Act")
            report = scan_bundle(root)

            self.assertTrue((root / "index.md").is_file())
            self.assertTrue((root / "log.md").is_file())
            self.assertTrue((root / "AGENTS.md").is_file())
            self.assertIn("No OKF-specific tools are required.", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertTrue(any(path.name == "eu-ai-act.md" for path in written))
            self.assertIn(root / "AGENTS.md", written)
            self.assertEqual([], report.errors)

    def test_scaffold_bundle_can_skip_agents_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "new-bundle"

            written = scaffold_bundle(root, title="EU AI Act", include_agents_md=False)

            self.assertFalse((root / "AGENTS.md").exists())
            self.assertNotIn(root / "AGENTS.md", written)

    def test_missing_type_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.md").write_text("---\ntitle: No Type\n---\n\n# Body\n", encoding="utf-8")

            report = scan_bundle(root)

            self.assertTrue(any("type" in i.message for i in report.errors))

    def test_broken_internal_link_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "concepts" / "a.md"
            write_concept(path)
            path.write_text(
                path.read_text(encoding="utf-8") + "\nSee [missing](/concepts/nope.md).\n",
                encoding="utf-8",
            )

            report = scan_bundle(root)

            self.assertTrue(any("Broken internal link" in i.message for i in report.warnings))

    def test_orphan_concept_is_flagged_without_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_concept(root / "a.md", title="Alpha")
            write_concept(root / "b.md", title="Beta")
            # Alpha links to Beta, so only Alpha is an orphan.
            (root / "a.md").write_text(
                (root / "a.md").read_text(encoding="utf-8") + "\nLink to [Beta](/b.md).\n",
                encoding="utf-8",
            )

            report = scan_bundle(root)
            orphans = {i.path for i in report.warnings if "No incoming links" in i.message}

            self.assertIn("a.md", orphans)
            self.assertNotIn("b.md", orphans)

    def test_image_links_are_not_treated_as_concept_links(self) -> None:
        matches = MD_LINK_RE.findall("![diagram](/tables/orders.md) and [real](/tables/customers.md)")
        targets = [target for _text, target in matches]

        self.assertEqual(["/tables/customers.md"], targets)

    def test_future_timestamp_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "a.md"
            write_concept(path)
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "timestamp: 2026-06-29T00:00:00Z", "timestamp: 2999-01-01T00:00:00Z"
                ),
                encoding="utf-8",
            )

            report = scan_bundle(root)

            self.assertTrue(any("future" in i.message for i in report.warnings))

    def test_graph_export_has_nodes_and_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_concept(root / "a.md", title="Alpha")
            write_concept(root / "b.md", title="Beta")
            (root / "a.md").write_text(
                (root / "a.md").read_text(encoding="utf-8") + "\nLink to [Beta](/b.md).\n",
                encoding="utf-8",
            )

            data = graph(root)

            self.assertEqual(2, len(data["nodes"]))
            self.assertIn({"from": "a", "to": "b", "link": "/b.md"}, data["edges"])

    def test_bundle_stats_counts_types_and_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_concept(root / "a.md", title="Alpha")
            write_concept(root / "b.md", title="Beta")
            (root / "a.md").write_text(
                (root / "a.md").read_text(encoding="utf-8") + "\nLink to [Beta](/b.md).\n",
                encoding="utf-8",
            )

            stats = bundle_stats(scan_bundle(root))

            self.assertEqual(2, stats["concepts"])
            self.assertEqual(2, stats["types"]["API"])
            self.assertEqual(1, stats["internal_edges"])

    def test_add_log_entry_groups_by_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            add_log_entry(root, "First change", kind="Update", date="2026-06-29")
            add_log_entry(root, "Second change", kind="Review", date="2026-06-29")

            text = (root / "log.md").read_text(encoding="utf-8")

            self.assertEqual(1, text.count("## 2026-06-29"))
            self.assertIn("First change", text)
            self.assertIn("Second change", text)

    def test_build_visualization_embeds_data_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "a.md"
            write_concept(path, title="Alpha Concept")
            # A script-close sequence in the body must not break out of the data block.
            path.write_text(
                path.read_text(encoding="utf-8") + "\nDanger </script> text.\n",
                encoding="utf-8",
            )

            html = build_visualization(root)

            self.assertIn("window.OKF_DATA", html)
            self.assertIn("class OKFViewer", html)
            self.assertIn("Alpha Concept", html)
            # Body content is neutralized so it cannot terminate the inline <script>.
            self.assertIn("<\\/script>", html)
            # Resource links pass through a protocol allowlist before rendering.
            self.assertIn("safeUrl", html)


if __name__ == "__main__":
    unittest.main()
