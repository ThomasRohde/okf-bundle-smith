from __future__ import annotations

import sys
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
        self.assertIn("okf_scaffold_bundle", tools)
        self.assertIn("okf_validate_bundle", tools)
        self.assertIn("okf_generate_indexes", tools)
        self.assertIn("okf_export_graph", tools)
        self.assertIn("okf_add_log_entry", tools)
        self.assertIn("okf_package_bundle", tools)


if __name__ == "__main__":
    unittest.main()
