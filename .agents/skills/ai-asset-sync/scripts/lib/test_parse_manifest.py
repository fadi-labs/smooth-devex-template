#!/usr/bin/env python3
"""Stdlib tests for parse_manifest.py. Run directly:

  python3 .agents/skills/ai-asset-sync/scripts/lib/test_parse_manifest.py
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def load():
    spec = importlib.util.spec_from_file_location("parse_manifest", SCRIPTS / "parse_manifest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pm = load()


class ParseSourceTests(unittest.TestCase):
    def test_happy(self):
        p = pm.parse_source("acme/tools@v1:.agents/skills/ai-brain-dump")
        self.assertEqual(p["owner"], "acme")
        self.assertEqual(p["repo"], "tools")
        self.assertEqual(p["ref"], "v1")
        self.assertEqual(p["path"], ".agents/skills/ai-brain-dump")

    def test_ref_with_slash_not_supported_as_path_split(self):
        p = pm.parse_source("acme/tools@main:.github/instructions/git/git-policy.instructions.md")
        self.assertEqual(p["ref"], "main")
        self.assertEqual(p["path"], ".github/instructions/git/git-policy.instructions.md")

    def test_sha_ref(self):
        p = pm.parse_source("acme/tools@deadbeef:.agents/skills/x")
        self.assertEqual(p["ref"], "deadbeef")

    def test_rejects_parent_path(self):
        with self.assertRaises(pm.ManifestError):
            pm.parse_source("acme/tools@main:../secrets")

    def test_rejects_missing_path(self):
        with self.assertRaises(pm.ManifestError):
            pm.parse_source("acme/tools@main")

    def test_rejects_absolute(self):
        with self.assertRaises(pm.ManifestError):
            pm.parse_source("acme/tools@main:/etc/passwd")

    def test_rejects_slash_in_repo(self):
        # `a/b/c@main:x` must NOT parse as repo="b/c".
        with self.assertRaises(pm.ManifestError):
            pm.parse_source("acme/nested/tools@main:.agents/skills/x")

    def test_rejects_hostile_owner_charset(self):
        for src in (
            "-acme/tools@main:.agents/skills/x",  # option-looking owner
            "ac me/tools@main:.agents/skills/x",  # space
            "acme%2f../tools@main:.agents/skills/x",  # URL metachar
        ):
            with self.assertRaises(pm.ManifestError, msg=src):
                pm.parse_source(src)

    def test_rejects_hostile_repo_charset(self):
        for src in (
            "acme/-tools@main:.agents/skills/x",
            "acme/to?ols@main:.agents/skills/x",
            "acme/to ols@main:.agents/skills/x",
        ):
            with self.assertRaises(pm.ManifestError, msg=src):
                pm.parse_source(src)

    def test_rejects_hostile_ref(self):
        for src in (
            "acme/tools@..:.agents/skills/x",
            "acme/tools@heads/../../x:.agents/skills/x",
            "acme/tools@ref?per_page=1:.agents/skills/x",
            "acme/tools@ref#frag:.agents/skills/x",
            "acme/tools@-ref:.agents/skills/x",
            "acme/tools@/ref:.agents/skills/x",
            "acme/tools@a ref:.agents/skills/x",
        ):
            with self.assertRaises(pm.ManifestError, msg=src):
                pm.parse_source(src)

    def test_rejects_embedded_traversal_and_tilde_and_dash_path(self):
        for src in (
            "acme/tools@main:a/../b",
            "acme/tools@main:~role",
            "acme/tools@main:-rf",
        ):
            with self.assertRaises(pm.ManifestError, msg=src):
                pm.parse_source(src)

    def test_ref_with_slash_allowed(self):
        p = pm.parse_source("acme/tools@release/v1.2:.agents/skills/x")
        self.assertEqual(p["ref"], "release/v1.2")

    def test_rejects_dangerous_destinations(self):
        for src in (
            "acme/tools@main:.",  # repo root
            "acme/tools@main:./",  # repo root
            "acme/tools@main:.git",  # git control dir
            "acme/tools@main:.git/hooks",  # git control subpath
            "acme/tools@main:a/.git/b",  # embedded .git segment
            "acme/tools@main:a/./b",  # '.' segment
            "acme/tools@main:a//b",  # empty segment
            "acme/tools@main:.github/workflows",  # executable CI
            "acme/tools@main:.github/workflows/x.yml",
        ):
            with self.assertRaises(pm.ManifestError, msg=src):
                pm.parse_source(src)

    def test_allows_dotted_asset_roots(self):
        for src in (
            "acme/tools@main:.agents/skills/x",
            "acme/tools@main:.github/instructions/git",
            "acme/tools@main:.claude/skills/y",
        ):
            pm.parse_source(src)  # must not raise


class ParseManifestTests(unittest.TestCase):
    def test_two_entries_default_strategy(self):
        text = """
version: 1
entries:
  - source: acme/tools@main:.agents/skills/ai-brain-dump
  - source: acme/tools@v1:.agents/rules/git
    strategy: overwrite
"""
        data = pm.parse_manifest(text)
        self.assertEqual(len(data["entries"]), 2)
        self.assertEqual(data["entries"][0]["strategy"], "ai-merge")
        self.assertEqual(data["entries"][1]["strategy"], "overwrite")

    def test_empty_entries(self):
        data = pm.parse_manifest("version: 1\nentries: []\n")
        self.assertEqual(data["entries"], [])

    def test_duplicate_source(self):
        text = """
entries:
  - source: acme/tools@main:.agents/skills/x
  - source: acme/tools@main:.agents/skills/x
"""
        with self.assertRaises(pm.ManifestError):
            pm.parse_manifest(text)

    def test_bad_strategy(self):
        text = """
entries:
  - source: acme/tools@main:.agents/skills/x
    strategy: merge
"""
        with self.assertRaises(pm.ManifestError):
            pm.parse_manifest(text)

    def test_comments_ignored(self):
        text = """
# consumer manifest
entries:
  - source: acme/tools@main:.agents/skills/x  # keep
"""
        data = pm.parse_manifest(text)
        self.assertEqual(data["entries"][0]["path"], ".agents/skills/x")

    def test_missing_entries_key(self):
        with self.assertRaises(pm.ManifestError):
            pm.parse_manifest("version: 1\n")

    def test_empty_text(self):
        with self.assertRaises(pm.ManifestError):
            pm.parse_manifest("")

    def test_rejects_overlapping_paths(self):
        text = """
entries:
  - source: acme/tools@main:.agents/skills
  - source: acme/tools@main:.agents/skills/x
"""
        with self.assertRaises(pm.ManifestError):
            pm.parse_manifest(text)

    def test_sibling_paths_ok(self):
        text = """
entries:
  - source: acme/tools@main:.agents/skills/x
  - source: acme/tools@main:.agents/skills/x-ray
"""
        data = pm.parse_manifest(text)
        self.assertEqual(len(data["entries"]), 2)


class LockfileTests(unittest.TestCase):
    def test_roundtrip(self):
        entries = [
            {
                "source": "acme/tools@main:.agents/skills/x",
                "resolved_sha": "abc1234",
                "synced_at": "2026-09-13T06:00:00Z",
            }
        ]
        dumped = pm.dump_lockfile(entries)
        parsed = pm.parse_lockfile(dumped)
        self.assertEqual(parsed["entries"][0]["resolved_sha"], "abc1234")

    def test_empty_lockfile(self):
        self.assertEqual(pm.parse_lockfile("")["entries"], [])

    def test_index_by_source(self):
        lock = pm.parse_lockfile(
            "version: 1\nentries:\n  - source: acme/tools@main:.agents/skills/x\n    resolved_sha: abcdef0\n"
        )
        idx = pm.lockfile_index(lock)
        self.assertEqual(idx["acme/tools@main:.agents/skills/x"]["resolved_sha"], "abcdef0")

    def test_bad_lockfile_version(self):
        with self.assertRaises(pm.ManifestError):
            pm.parse_lockfile("version: banana\nentries: []\n")

    def test_unsupported_lockfile_version(self):
        for text in ("version: 2\nentries: []\n", "version: 2\nentries:\n  - source: acme/tools@main:.agents/skills/x\n"):
            with self.assertRaises(pm.ManifestError, msg=text):
                pm.parse_lockfile(text)

    def test_bad_resolved_sha(self):
        with self.assertRaises(pm.ManifestError):
            pm.parse_lockfile(
                "version: 1\nentries:\n  - source: acme/tools@main:.agents/skills/x\n    resolved_sha: $(id)\n"
            )


if __name__ == "__main__":
    unittest.main()
