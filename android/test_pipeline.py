"""Candidate provenance and integrity checks before local execution."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "pipeline", Path(__file__).with_name("pipeline-test.py")
)
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class PipelineTests(unittest.TestCase):
    def test_untrusted_or_incomplete_builds_are_rejected(self):
        build = {
            "conclusion": "success",
            "head_branch": "main",
            "event": "push",
            "path": ".github/workflows/android.yml",
            "head_sha": "a" * 40,
            "head_repository": {"full_name": pipeline.REPO},
        }
        pipeline.validate_build(build)
        for field, value in [
            ("event", "pull_request"),
            ("head_branch", "feature"),
            ("conclusion", "failure"),
            ("path", "other.yml"),
            ("head_repository", {"full_name": "untrusted/repo"}),
        ]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                pipeline.validate_build(dict(build, **{field: value}))

    def test_default_does_not_fall_back_to_an_older_build(self):
        with (
            patch("sys.argv", ["pipeline-test.py"]),
            patch.object(
                pipeline,
                "gh",
                side_effect=[json.dumps({"sha": "b" * 40}), '{"workflow_runs":[]}'],
            ) as api,
            self.assertRaisesRegex(ValueError, "Current main has no successful"),
        ):
            pipeline.main()
        self.assertEqual(api.call_count, 2)
        self.assertIn("head_sha=" + "b" * 40, api.call_args.args[1])

    def test_tampered_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / "candidate.tgz").write_bytes(b"tampered")
            (root / "candidate.tgz.sha256").write_text("0" * 64)
            with self.assertRaisesRegex(ValueError, "checksum"):
                pipeline.verify_archive(root)
