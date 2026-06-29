from __future__ import annotations

import unittest
from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import okf_git  # noqa: E402
from okf_git import GitHubBundleRef, attach_github_bundle, parse_github_bundle_url, resolve_github_ref  # noqa: E402


class OkfGitTests(unittest.TestCase):
    def test_parse_tree_url(self) -> None:
        ref = parse_github_bundle_url("https://github.com/acme/okf-knowledge/tree/main/bundles/payments")
        resolved = resolve_github_ref(ref, remote_refs={"main"})

        self.assertEqual("acme", resolved.owner)
        self.assertEqual("okf-knowledge", resolved.repo)
        self.assertEqual("main", resolved.ref)
        self.assertEqual("bundles/payments", resolved.path)

    def test_branch_with_slashes_uses_longest_remote_ref_match(self) -> None:
        ref = parse_github_bundle_url("https://github.com/acme/repo/tree/release/2026.06/bundles/payments")
        resolved = resolve_github_ref(ref, remote_refs={"release/2026.06", "release"})

        self.assertEqual("release/2026.06", resolved.ref)
        self.assertEqual("bundles/payments", resolved.path)

    def test_blob_index_url_resolves_to_bundle_directory(self) -> None:
        ref = parse_github_bundle_url("https://github.com/acme/repo/blob/main/bundles/payments/index.md")
        resolved = resolve_github_ref(ref, remote_refs={"main"})

        self.assertEqual("main", resolved.ref)
        self.assertEqual("bundles/payments", resolved.path)

    def test_shorthand_url(self) -> None:
        ref = parse_github_bundle_url("acme/repo//bundles/payments?ref=main")

        self.assertEqual("acme", ref.owner)
        self.assertEqual("repo", ref.repo)
        self.assertEqual("main", ref.ref)
        self.assertEqual("bundles/payments", ref.path)

    def test_attach_uses_git_cache_and_records_commit(self) -> None:
        original_run_git = okf_git._run_git
        calls: list[list[str]] = []

        def fake_run_git(args: list[str], cwd: Path | None = None) -> str:
            calls.append(args)
            if args[0] == "clone":
                destination = Path(args[-1])
                (destination / ".git").mkdir(parents=True)
                return ""
            if "sparse-checkout" in args and "set" in args:
                repo = Path(args[args.index("-C") + 1])
                (repo / args[-1]).mkdir(parents=True)
                return ""
            if "rev-parse" in args:
                return "abc123"
            return ""

        with tempfile.TemporaryDirectory() as tmp:
            okf_git._run_git = fake_run_git
            try:
                ref = GitHubBundleRef(
                    owner="acme",
                    repo="repo",
                    ref="main",
                    path="bundles/payments",
                    url="https://github.com/acme/repo/tree/main/bundles/payments",
                )
                resolved = attach_github_bundle(ref, tmp, alias="payments")
            finally:
                okf_git._run_git = original_run_git

        self.assertEqual("payments", resolved.alias)
        self.assertEqual("abc123", resolved.commit_sha)
        self.assertTrue(any("sparse-checkout" in call for call in calls))


if __name__ == "__main__":
    unittest.main()
