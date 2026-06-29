from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from okf_core import generate_indexes, package_bundle, scan_bundle, scaffold_bundle  # noqa: E402


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
            self.assertTrue(any(path.name == "eu-ai-act.md" for path in written))
            self.assertEqual([], report.errors)


if __name__ == "__main__":
    unittest.main()
