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
    PLAN_FIELDS,
    add_log_entry,
    build_plan,
    build_visualization,
    bundle_stats,
    check_inventory,
    coverage_report,
    generate_indexes,
    graph,
    install_agents,
    package_bundle,
    plan_csv_path,
    retry_csv_path,
    scan_bundle,
    scaffold_bundle,
    update_plan_status,
    write_checked_plan,
    write_plan,
)


CONCEPT_BODY = """# Summary

This concept is intentionally long enough to clear the lightweight usefulness
check in the OKF validator. It describes one durable idea and provides enough
body content for downstream agents to decide whether the concept is relevant.

# Relationships

This concept is discoverable through generated index files.

# Citations

[1] Internal test fixture.
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
            self.assertIn("When The Bundle Points To External Data", (root / "AGENTS.md").read_text(encoding="utf-8"))
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
            # Large bundles use a bounded, normalized sizing curve.
            self.assertIn("nodeRadiusRange", html)
            self.assertIn("Math.log1p(n.deg) / Math.log1p(this.maxDeg)", html)
            self.assertIn("always-visible labels", html)
            self.assertIn("fillText(n.label", html)
            self.assertIn("Select all", html)
            self.assertIn("Unselect all", html)
            self.assertIn("afterTypeFilterChange", html)


class OkfPlanCoverageTests(unittest.TestCase):
    def _inventory(self) -> list[dict]:
        return [
            {"path": "concepts/alpha", "type": "API", "title": "Alpha", "description": "A.", "source_ids": ["s1"]},
            {"path": "concepts/beta", "type": "API", "title": "Beta", "description": "B.", "source_ids": "s2"},
            {"path": "concepts/gamma", "type": "API", "title": "Gamma", "description": "C."},
            {"path": "concepts/delta", "type": "API", "title": "Delta", "description": "D."},
        ]

    def _write_sources(self, root: Path, ids: list[str]) -> None:
        source_dir = root / ".okf"
        source_dir.mkdir(parents=True, exist_ok=True)
        rows = ["source_id,title,url,publisher,date,source_type,reliability,used_for"]
        rows.extend(
            f"{source_id},Source {source_id},https://example.com/{source_id},Example,2026-01-01,reference,primary,tests"
            for source_id in ids
        )
        (source_dir / "sources.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def test_build_plan_assigns_balanced_shards_and_normalizes_paths(self) -> None:
        plan = build_plan(self._inventory(), shards=2)

        self.assertEqual(2, plan.shards)
        self.assertEqual({0, 1}, {row.shard for row in plan.rows})
        self.assertTrue(all(row.path.endswith(".md") for row in plan.rows))
        # source_ids accepts list or delimited string.
        beta = next(row for row in plan.rows if row.path == "concepts/beta.md")
        self.assertEqual(["s2"], beta.source_ids)

    def test_build_plan_rejects_duplicate_paths(self) -> None:
        rows = [{"path": "concepts/a"}, {"path": "concepts/a.md"}]
        with self.assertRaises(ValueError):
            build_plan(rows)

    def test_build_plan_rejects_paths_outside_bundle(self) -> None:
        bad_paths = [
            "../outside",
            "concepts/../outside",
            "/absolute/concept",
            "\\absolute\\concept",
            "C:/tmp/outside",
            "C:\\tmp\\outside",
            "C:tmp/outside",
            ".okf/not-a-concept",
            "CHATGPT.md",
        ]
        for path in bad_paths:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    build_plan([{"path": path}])

    def test_inventory_check_blocks_dangling_depends_on_without_writing_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = build_plan([
                {
                    "path": "concepts/alpha",
                    "type": "API",
                    "title": "Alpha",
                    "description": "A.",
                    "depends_on": ["concepts/missing"],
                }
            ])

            result = write_checked_plan(root, plan)

            self.assertFalse(result["written"])
            self.assertEqual(1, result["check"]["errors"])
            self.assertFalse(plan_csv_path(root).exists())
            self.assertIn("depends_on target", result["check"]["issues"][0]["message"])

    def test_inventory_check_accepts_depends_on_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_concept(root / "concepts" / "existing.md", title="Existing")
            plan = build_plan([
                {
                    "path": "concepts/alpha",
                    "type": "API",
                    "title": "Alpha",
                    "description": "A.",
                    "depends_on": ["concepts/existing"],
                }
            ])

            result = write_checked_plan(root, plan)

            self.assertTrue(result["written"])
            self.assertEqual(0, result["check"]["errors"])

    def test_inventory_check_accepts_known_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_sources(root, ["s1"])
            plan = build_plan([
                {"path": "concepts/alpha", "type": "API", "title": "Alpha", "description": "A.", "source_ids": ["s1"]}
            ])

            result = write_checked_plan(root, plan)

            self.assertTrue(result["written"])
            self.assertEqual({"errors": 0, "warnings": 0}, {k: result["check"][k] for k in ("errors", "warnings")})

    def test_inventory_check_blocks_unknown_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_sources(root, ["known"])
            plan = build_plan([
                {"path": "concepts/alpha", "type": "API", "title": "Alpha", "description": "A.", "source_ids": ["missing"]}
            ])

            result = write_checked_plan(root, plan)

            self.assertFalse(result["written"])
            self.assertEqual(1, result["check"]["errors"])
            self.assertIn("Unknown source_id", result["check"]["issues"][0]["message"])

    def test_inventory_check_warns_when_source_ids_have_no_sources_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = build_plan([
                {"path": "concepts/alpha", "type": "API", "title": "Alpha", "description": "A.", "source_ids": ["s1"]}
            ])

            result = write_checked_plan(root, plan)

            self.assertTrue(result["written"])
            self.assertEqual(1, result["check"]["warnings"])
            self.assertIn("sources.csv is missing", result["check"]["issues"][0]["message"])
            self.assertTrue(plan_csv_path(root).is_file())

    def test_inventory_check_strict_promotes_missing_metadata_warning(self) -> None:
        rows = [{"path": "concepts/alpha", "type": "API", "title": "Alpha"}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_checked_plan(root, build_plan(rows))

            self.assertTrue(result["written"])
            self.assertEqual(1, result["check"]["warnings"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_checked_plan(root, build_plan(rows), strict=True)

            self.assertFalse(result["written"])
            self.assertEqual(1, result["check"]["warnings"])
            self.assertFalse(plan_csv_path(root).exists())

    def test_inventory_check_warns_on_duplicate_stems_in_different_directories(self) -> None:
        rows = [
            {"path": "data/customer-id", "type": "Data", "title": "Customer ID", "description": "A."},
            {"path": "concepts/customer-id", "type": "Concept", "title": "Customer ID", "description": "B."},
        ]

        issues = check_inventory(build_plan(rows), Path(tempfile.gettempdir()))

        self.assertEqual(1, len(issues))
        self.assertEqual("warning", issues[0]["severity"])
        self.assertIn("Near-duplicate concept stem", issues[0]["message"])

    def test_plan_artifacts_live_outside_the_scanned_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_concept(root / "concepts" / "alpha.md", title="Alpha")
            write_plan(root, build_plan(self._inventory(), shards=2))

            report = scan_bundle(root)

            # plan.md under .okf/ must not be parsed as a concept nor raise errors.
            self.assertEqual([], report.errors)
            self.assertTrue(all(".okf" not in c.rel for c in report.concepts))
            self.assertTrue(plan_csv_path(root).is_file())

    def test_coverage_flags_missing_incomplete_extra_and_status_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_plan(root, build_plan(self._inventory(), shards=2))

            # alpha: complete. beta: stub (incomplete). gamma+delta: missing.
            write_concept(root / "concepts" / "alpha.md", title="Alpha")
            (root / "concepts" / "beta.md").write_text(
                "---\ntype: API\n---\n\n# Beta\n", encoding="utf-8"
            )
            # An unplanned concept on disk shows up as extra.
            write_concept(root / "concepts" / "surprise.md", title="Surprise")
            # Worker wrongly marked the stub done -> status mismatch.
            update_plan_status(root, ["concepts/beta.md"], "done")

            cov = coverage_report(root)

            self.assertFalse(cov["complete"])
            self.assertEqual(cov["counts"]["complete"], 1)
            self.assertIn("concepts/beta.md", cov["incomplete"])
            self.assertEqual(sorted(cov["missing"]), ["concepts/delta.md", "concepts/gamma.md"])
            self.assertIn("concepts/surprise.md", cov["extra"])
            self.assertEqual([m["path"] for m in cov["status_mismatch"]], ["concepts/beta.md"])

    def test_coverage_requires_citations_for_rows_with_source_ids(self) -> None:
        concept_without_citations = "\n".join(
            [
                "---",
                "type: API",
                "title: Alpha",
                "description: A durable API concept used by the coverage test.",
                "tags: [test, api]",
                "timestamp: 2026-06-29T00:00:00Z",
                "---",
                "",
                "# Summary",
                "",
                "This concept body is intentionally long enough to clear the lightweight",
                "usefulness check but it intentionally omits the citations heading.",
            ]
        )
        concept_with_citations = concept_without_citations + "\n\n# Citations\n\n[1] [Source](https://example.com/source)\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_plan(root, build_plan([
                {"path": "concepts/alpha", "type": "API", "title": "Alpha", "description": "A.", "source_ids": ["s1"]}
            ]))
            path = root / "concepts" / "alpha.md"
            path.parent.mkdir(parents=True)
            path.write_text(concept_without_citations, encoding="utf-8")

            cov = coverage_report(root)

            self.assertFalse(cov["complete"])
            self.assertIn("concepts/alpha.md", cov["incomplete"])
            self.assertIn("missing citations section", cov["incomplete_reasons"][0]["reasons"])

            path.write_text(concept_with_citations, encoding="utf-8")
            cov = coverage_report(root)

            self.assertTrue(cov["complete"])
            self.assertEqual([], cov["incomplete"])

    def test_coverage_does_not_require_citations_without_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_plan(root, build_plan([
                {"path": "concepts/alpha", "type": "API", "title": "Alpha", "description": "A."}
            ]))
            path = root / "concepts" / "alpha.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "\n".join(
                    [
                        "---",
                        "type: API",
                        "title: Alpha",
                        "description: A durable API concept used by the coverage test.",
                        "tags: [test, api]",
                        "timestamp: 2026-06-29T00:00:00Z",
                        "---",
                        "",
                        "# Summary",
                        "",
                        "This concept body is intentionally long enough to clear the lightweight",
                        "usefulness check and has no citations because the plan row has no sources.",
                    ]
                ),
                encoding="utf-8",
            )

            cov = coverage_report(root)

            self.assertTrue(cov["complete"])

    def test_coverage_rejects_existing_plan_rows_that_escape_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bundle"
            root.mkdir()
            outside = Path(tmp) / "outside.md"
            write_concept(outside, title="Outside")
            plan_dir = root / ".okf"
            plan_dir.mkdir()
            (plan_dir / "plan.csv").write_text("path\n../outside.md\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                coverage_report(root)

    def test_coverage_does_not_count_unscanned_paths_as_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = root / ".okf"
            plan_dir.mkdir()
            (plan_dir / "plan.csv").write_text("path\n.hidden/alpha.md\n", encoding="utf-8")
            write_concept(root / ".hidden" / "alpha.md", title="Hidden")

            with self.assertRaises(ValueError):
                coverage_report(root)

    def test_coverage_is_complete_when_every_planned_concept_is_authored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_plan(root, build_plan(self._inventory(), shards=2))
            for name in ("alpha", "beta", "gamma", "delta"):
                write_concept(root / "concepts" / f"{name}.md", title=name.title())

            cov = coverage_report(root)

            self.assertTrue(cov["complete"])
            self.assertEqual(cov["counts"]["missing"], 0)
            self.assertEqual(cov["counts"]["incomplete"], 0)
            self.assertEqual(cov["planned"], 4)

    def test_coverage_retry_csv_contains_failing_rows_and_is_removed_when_complete(self) -> None:
        rows = [
            {"path": "concepts/alpha", "type": "API", "title": "Alpha", "description": "A."},
            {"path": "concepts/beta", "type": "API", "title": "Beta", "description": "B."},
            {"path": "concepts/gamma", "type": "API", "title": "Gamma", "description": "C."},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_plan(root, build_plan(rows, shards=2))
            write_concept(root / "concepts" / "alpha.md", title="Alpha")
            (root / "concepts" / "beta.md").write_text("---\ntype: API\n---\n\n# Beta\n", encoding="utf-8")

            retry_path = retry_csv_path(root)
            cov = coverage_report(root, retry_csv=retry_path)

            self.assertFalse(cov["complete"])
            self.assertEqual(str(retry_path.resolve()), cov["retry_csv"])
            retry_lines = retry_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(",".join(PLAN_FIELDS), retry_lines[0])
            self.assertIn("concepts/beta.md", "\n".join(retry_lines))
            self.assertIn("concepts/gamma.md", "\n".join(retry_lines))
            self.assertNotIn("concepts/alpha.md", "\n".join(retry_lines))

            write_concept(root / "concepts" / "beta.md", title="Beta")
            write_concept(root / "concepts" / "gamma.md", title="Gamma")
            cov = coverage_report(root, retry_csv=retry_path)

            self.assertTrue(cov["complete"])
            self.assertFalse(retry_path.exists())
            self.assertEqual(0, cov["retry_rows"])

    def test_install_agents_copies_bundled_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"

            result = install_agents(target)

            names = {Path(p).name for p in result["installed"]}
            self.assertIn("okf-authoring-worker.toml", names)
            self.assertIn("okf-concept-mapper.toml", names)
            self.assertTrue((target / "okf-authoring-worker.toml").is_file())
            # Re-running without overwrite skips existing files.
            again = install_agents(target)
            self.assertEqual(again["installed"], [])
            self.assertTrue(again["skipped"])


if __name__ == "__main__":
    unittest.main()
