import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("release.sh")


class ReleaseCommandsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.log = self.root / "calls.jsonl"
        self.env = dict(
            os.environ,
            PATH=f"{self.root}{os.pathsep}{os.environ['PATH']}",
            RELEASE_TEST_LOG=str(self.log),
        )
        for command in ["gh", "npm", "npx"]:
            fake = self.root / command
            fake.write_text(
                f"#!{sys.executable}\n"
                + """import json, os, sys
from pathlib import Path
with Path(os.environ["RELEASE_TEST_LOG"]).open("a") as output:
    output.write(json.dumps([Path(sys.argv[0]).name, *sys.argv[1:]]) + "\\n")
if os.environ.get("FAIL_STAGE_VIEW") and "view" in sys.argv and "stage" in sys.argv:
    sys.exit(1)
if os.environ.get("MISSING_RELEASE") and sys.argv[1:3] == ["release", "view"]:
    sys.exit(1)
"""
            )
            fake.chmod(0o755)

    def run_command(self, *args):
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_stage_dispatches_cloud_workflow_without_local_upload(self):
        result = self.run_command("stage", "123")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.calls(),
            [
                [
                    "gh",
                    "workflow",
                    "run",
                    "android-publish.yml",
                    "--repo",
                    "Ameer-Jamal/codex-android",
                    "--ref",
                    "main",
                    "-f",
                    "build_run_id=123",
                ]
            ],
        )

    def test_invalid_run_id_never_dispatches(self):
        result = self.run_command("stage", "123;bad")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_failed_stage_inspection_prevents_approval(self):
        self.env["FAIL_STAGE_VIEW"] = "1"
        result = self.run_command("approve", "685d768a-3911-4f3a-bb72-549707a97863")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(self.calls()), 1)
        self.assertIn("view", self.calls()[0])

    def test_watch_failure_propagates(self):
        # npm stage inspection and the watcher use set -e; test the actual watcher exit too.
        fake = self.root / "gh"
        fake.write_text("#!/usr/bin/env bash\nexit 7\n")
        result = self.run_command("watch", "123")
        self.assertEqual(result.returncode, 7)

    def test_mirror_creates_missing_release_then_dispatches_cloud_transfer(self):
        notes = self.root / "notes with spaces.md"
        notes.write_text("Release notes")
        self.env["MISSING_RELEASE"] = "1"
        result = self.run_command(
            "mirror", "0.160.0-android.4", "a" * 64, "b" * 40, str(notes)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual(
            [call[1:3] for call in calls],
            [["release", "view"], ["release", "create"], ["workflow", "run"]],
        )
        self.assertEqual(calls[1][-1], str(notes))
        self.assertIn("android-release-assets.yml", calls[2])

    def test_invalid_checksum_prevents_release_mutation(self):
        result = self.run_command(
            "mirror", "0.160.0-android.4", "invalid", "b" * 40, "missing.md"
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
