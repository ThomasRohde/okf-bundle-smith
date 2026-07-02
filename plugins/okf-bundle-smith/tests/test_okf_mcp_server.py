from __future__ import annotations

import sys
import tempfile
import unittest
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from okf_mcp_server import handle  # noqa: E402


class OkfMcpServerTests(unittest.TestCase):
    def test_tools_list_exposes_core_workflow_tools(self) -> None:
        response = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

        self.assertIsNotNone(response)
        tools = {tool["name"] for tool in response["result"]["tools"]}  # type: ignore[index]
        for expected in (
            "okf_scaffold_bundle",
            "okf_validate_bundle",
            "okf_stats",
            "okf_generate_indexes",
            "okf_export_graph",
            "okf_visualize",
            "okf_add_log_entry",
            "okf_package_bundle",
            "okf_attach_github_bundle",
            "okf_attach_local_bundle",
            "okf_list_attached_bundles",
            "okf_refresh_bundle",
            "okf_search_concepts",
            "okf_read_concept",
            "okf_related_concepts",
            "okf_prepare_answer_context",
            "okf_freshness_report",
            "okf_bundle_overview",
            "okf_generate_chatgpt_usage",
            "okf_mcp_diagnostics",
            "okf_plan_bundle",
            "okf_coverage_report",
            "okf_plan_status",
            "okf_install_agents",
        ):
            self.assertIn(expected, tools)

    def test_initialize_reports_server_info(self) -> None:
        response = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})

        self.assertEqual("okf-bundle-smith", response["result"]["serverInfo"]["name"])  # type: ignore[index]

    def test_notification_without_id_gets_no_reply(self) -> None:
        self.assertIsNone(handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_unknown_method_returns_error(self) -> None:
        response = handle({"jsonrpc": "2.0", "id": 9, "method": "does/not/exist"})

        self.assertEqual(-32601, response["error"]["code"])  # type: ignore[index]

    def test_tools_call_scaffold_validate_and_visualize_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_data_dir = os.environ.get("OKF_BUNDLE_SMITH_DATA_DIR")
            os.environ["OKF_BUNDLE_SMITH_DATA_DIR"] = str(Path(tmp) / "data")
            bundle = str(Path(tmp) / "bundle")
            try:
                scaffold = handle({
                    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "okf_scaffold_bundle", "arguments": {"bundle_path": bundle, "title": "Demo"}},
                })
                self.assertIn("Scaffolded", scaffold["result"]["content"][0]["text"])  # type: ignore[index]
                self.assertTrue((Path(bundle) / "AGENTS.md").is_file())

                validate = handle({
                    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "okf_validate_bundle", "arguments": {"bundle": bundle, "format": "json"}},
                })
                self.assertIn('"error_count"', validate["result"]["content"][0]["text"])  # type: ignore[index]

                viz_out = str(Path(tmp) / "viz.html")
                visualize = handle({
                    "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "okf_visualize", "arguments": {"bundle": bundle, "output_path": viz_out}},
                })
                self.assertIn("visualization", visualize["result"]["content"][0]["text"])  # type: ignore[index]
                self.assertTrue(Path(viz_out).is_file())

                attach = handle({
                    "jsonrpc": "2.0", "id": 4, "method": "tools/call",
                    "params": {"name": "okf_attach_local_bundle", "arguments": {"path": bundle, "alias": "demo"}},
                })
                self.assertIn('"status": "attached"', attach["result"]["content"][0]["text"])  # type: ignore[index]

                validate_alias = handle({
                    "jsonrpc": "2.0", "id": 9, "method": "tools/call",
                    "params": {"name": "okf_validate_bundle", "arguments": {"bundle": "demo", "format": "json"}},
                })
                self.assertIn('"root": "' + bundle.replace("\\", "\\\\") + '"', validate_alias["result"]["content"][0]["text"])  # type: ignore[index]
                self.assertIn('"error_count": 0', validate_alias["result"]["content"][0]["text"])  # type: ignore[index]

                stats_alias = handle({
                    "jsonrpc": "2.0", "id": 10, "method": "tools/call",
                    "params": {"name": "okf_stats", "arguments": {"bundle": "demo", "format": "json"}},
                })
                self.assertIn('"concepts": 1', stats_alias["result"]["content"][0]["text"])  # type: ignore[index]

                search = handle({
                    "jsonrpc": "2.0", "id": 5, "method": "tools/call",
                    "params": {"name": "okf_search_concepts", "arguments": {"bundle_path": bundle, "query": "Demo"}},
                })
                self.assertIn("results", search["result"]["content"][0]["text"])  # type: ignore[index]

                context = handle({
                    "jsonrpc": "2.0", "id": 6, "method": "tools/call",
                    "params": {"name": "okf_prepare_answer_context", "arguments": {
                        "bundle": bundle, "question": "What is this?", "max_total_chars": 10000,
                    }},
                })
                self.assertIn("answer_instructions", context["result"]["content"][0]["text"])  # type: ignore[index]
                self.assertIn("inventory", context["result"]["content"][0]["text"])  # type: ignore[index]

                overview = handle({
                    "jsonrpc": "2.0", "id": 7, "method": "tools/call",
                    "params": {"name": "okf_bundle_overview", "arguments": {"bundle": bundle}},
                })
                self.assertIn("central_concepts", overview["result"]["content"][0]["text"])  # type: ignore[index]

                diagnostics = handle({
                    "jsonrpc": "2.0", "id": 8, "method": "tools/call",
                    "params": {"name": "okf_mcp_diagnostics", "arguments": {}},
                })
                self.assertIn("manual_probe", diagnostics["result"]["content"][0]["text"])  # type: ignore[index]
            finally:
                if old_data_dir is None:
                    os.environ.pop("OKF_BUNDLE_SMITH_DATA_DIR", None)
                else:
                    os.environ["OKF_BUNDLE_SMITH_DATA_DIR"] = old_data_dir


    def test_plan_coverage_and_install_agents_round_trip(self) -> None:
        concept = (
            "---\ntype: API\ntitle: X\ndescription: A durable concept for the "
            "coverage round trip.\ntags: [test]\ntimestamp: 2026-06-29T00:00:00Z\n---\n\n"
            "# Summary\n\nThis body is long enough to clear the lightweight usefulness "
            "check so coverage treats the concept as complete rather than a stub.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            bundle = str(Path(tmp) / "bundle")
            (Path(bundle) / "concepts").mkdir(parents=True)

            plan = handle({
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": "okf_plan_bundle", "arguments": {
                    "bundle_path": bundle,
                    "inventory": [{"path": "concepts/x", "type": "API", "title": "X"}],
                    "shards": 1,
                }},
            })
            self.assertIn('"planned": 1', plan["result"]["content"][0]["text"])  # type: ignore[index]

            cov = handle({
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "okf_coverage_report", "arguments": {"bundle": bundle, "format": "json"}},
            })
            self.assertIn('"complete": false', cov["result"]["content"][0]["text"])  # type: ignore[index]

            (Path(bundle) / "concepts" / "x.md").write_text(concept, encoding="utf-8")

            cov_done = handle({
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "okf_coverage_report", "arguments": {"bundle": bundle, "format": "json"}},
            })
            self.assertIn('"complete": true', cov_done["result"]["content"][0]["text"])  # type: ignore[index]

            status = handle({
                "jsonrpc": "2.0", "id": 4, "method": "tools/call",
                "params": {"name": "okf_plan_status", "arguments": {"bundle_path": bundle, "paths": ["concepts/x.md"], "status": "done"}},
            })
            self.assertIn('"updated"', status["result"]["content"][0]["text"])  # type: ignore[index]

            install = handle({
                "jsonrpc": "2.0", "id": 5, "method": "tools/call",
                "params": {"name": "okf_install_agents", "arguments": {"target": str(Path(tmp) / "codex-agents")}},
            })
            self.assertIn("okf-authoring-worker.toml", install["result"]["content"][0]["text"])  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
