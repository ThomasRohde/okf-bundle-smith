from __future__ import annotations

import sys
import tempfile
import unittest
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
            bundle = str(Path(tmp) / "bundle")

            scaffold = handle({
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": "okf_scaffold_bundle", "arguments": {"bundle_path": bundle, "title": "Demo"}},
            })
            self.assertIn("Scaffolded", scaffold["result"]["content"][0]["text"])  # type: ignore[index]

            validate = handle({
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "okf_validate_bundle", "arguments": {"bundle_path": bundle}},
            })
            self.assertIn("validation report", validate["result"]["content"][0]["text"])  # type: ignore[index]

            viz_out = str(Path(tmp) / "viz.html")
            visualize = handle({
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "okf_visualize", "arguments": {"bundle_path": bundle, "output_path": viz_out}},
            })
            self.assertIn("visualization", visualize["result"]["content"][0]["text"])  # type: ignore[index]
            self.assertTrue(Path(viz_out).is_file())


if __name__ == "__main__":
    unittest.main()
