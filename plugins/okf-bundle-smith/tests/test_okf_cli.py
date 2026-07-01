from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import okf_tool  # noqa: E402


def run(*argv: str) -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        return okf_tool.main(list(argv))


class OkfCliTests(unittest.TestCase):
    def test_full_cli_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_data_dir = os.environ.get("OKF_BUNDLE_SMITH_DATA_DIR")
            os.environ["OKF_BUNDLE_SMITH_DATA_DIR"] = str(Path(tmp) / "data")
            bundle = str(Path(tmp) / "bundle")
            try:
                self.assertEqual(0, run("new", bundle, "--title", "Demo Bundle"))
                self.assertTrue((Path(bundle) / "AGENTS.md").is_file())
                self.assertEqual(0, run("lint", bundle))
                self.assertEqual(0, run("stats", bundle))
                self.assertEqual(0, run("index", bundle))

                graph_out = str(Path(tmp) / "graph.json")
                self.assertEqual(0, run("graph", bundle, "--output", graph_out))
                self.assertTrue(Path(graph_out).is_file())

                viz_out = str(Path(tmp) / "viz.html")
                self.assertEqual(0, run("visualize", bundle, "-o", viz_out))
                self.assertTrue(Path(viz_out).is_file())

                self.assertEqual(0, run("log", bundle, "Reviewed bundle", "--kind", "Review"))

                pkg_out = str(Path(tmp) / "bundle.zip")
                self.assertEqual(0, run("package", bundle, pkg_out))
                self.assertTrue(Path(pkg_out).is_file())

                self.assertEqual(0, run("search", bundle, "Demo Bundle"))
                self.assertEqual(0, run("read", bundle, "concepts/demo-bundle", "--neighbors"))
                self.assertEqual(0, run("related", bundle, "concepts/demo-bundle"))
                self.assertEqual(0, run("context", bundle, "What is this bundle?", "--mode", "strict"))
                self.assertEqual(0, run("freshness", bundle))
                self.assertEqual(0, run("overview", bundle))
                self.assertEqual(0, run("attach-local", bundle, "--alias", "demo-local"))
                self.assertEqual(0, run("generate-chatgpt-usage", bundle, "--repo", "acme/demo"))
                self.assertEqual(0, run("mcp-diagnostics"))
            finally:
                if old_data_dir is None:
                    os.environ.pop("OKF_BUNDLE_SMITH_DATA_DIR", None)
                else:
                    os.environ["OKF_BUNDLE_SMITH_DATA_DIR"] = old_data_dir

    def test_plan_coverage_lifecycle(self) -> None:
        import json

        concept = "\n".join(
            [
                "---",
                "type: API",
                "title: Concept",
                "description: A durable concept used by the coverage test.",
                "tags: [test]",
                "timestamp: 2026-06-29T00:00:00Z",
                "---",
                "",
                "# Summary",
                "",
                "This concept body is intentionally long enough to clear the lightweight",
                "usefulness check so coverage classifies it as complete rather than a stub.",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle"
            (bundle / "concepts").mkdir(parents=True)
            inventory = Path(tmp) / "inventory.json"
            inventory.write_text(
                json.dumps([{"path": "concepts/x"}, {"path": "concepts/y"}]),
                encoding="utf-8",
            )

            self.assertEqual(0, run("plan", str(bundle), "--inventory", str(inventory), "--shards", "2"))
            self.assertTrue((bundle / ".okf" / "plan.csv").is_file())

            # Nothing authored yet -> coverage gate fails.
            self.assertEqual(1, run("coverage", str(bundle)))

            (bundle / "concepts" / "x.md").write_text(concept, encoding="utf-8")
            (bundle / "concepts" / "y.md").write_text(concept.replace("title: Concept", "title: Concept Y"), encoding="utf-8")

            # Every planned concept now exists and is complete.
            self.assertEqual(0, run("coverage", str(bundle)))
            self.assertEqual(0, run("plan-status", str(bundle), "--path", "concepts/x.md", "--status", "done"))

            target = Path(tmp) / "codex-agents"
            self.assertEqual(0, run("install-agents", "--target", str(target)))
            self.assertTrue((target / "okf-authoring-worker.toml").is_file())

    def test_lint_strict_returns_nonzero_on_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # A bare concept: valid (has type) but missing recommended fields -> warnings.
            (root / "a.md").write_text("---\ntype: Reference\n---\n\n# Body\n", encoding="utf-8")

            self.assertEqual(0, run("lint", str(root)))
            self.assertEqual(1, run("lint", str(root), "--strict"))


if __name__ == "__main__":
    unittest.main()
