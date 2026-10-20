"""Check candidate identity and the exact bytes exposed to npm in the emulator."""

import hashlib
import io
import json
import tarfile
import tempfile
import unittest
import urllib.request
from pathlib import Path

from emulator_registry import CandidateRegistry
from emulator_version import resolve_version


class CandidateRegistryTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.archive = Path(self.scratch.name) / "candidate.tgz"
        self.version = "0.160.0-android.4"
        manifest = json.dumps(
            {
                "name": "codex-android",
                "version": self.version,
                "scripts": {"test": "node --test"},
            }
        ).encode()
        with tarfile.open(self.archive, "w:gz") as package:
            item = tarfile.TarInfo("package/package.json")
            item.size = len(manifest)
            package.addfile(item, io.BytesIO(manifest))

    def test_registry_serves_verified_manifest_and_identical_archive(self):
        registry = CandidateRegistry(self.archive, self.version)
        self.addCleanup(registry.close)
        with urllib.request.urlopen(registry.url + "/codex-android") as response:
            metadata = json.load(response)
        manifest = metadata["versions"][self.version]
        self.assertEqual(manifest["scripts"], {"test": "node --test"})
        with urllib.request.urlopen(manifest["dist"]["tarball"]) as response:
            archive = response.read()
        self.assertEqual(archive, self.archive.read_bytes())
        self.assertEqual(manifest["dist"]["shasum"], hashlib.sha1(archive).hexdigest())

    def test_candidate_version_is_detected_without_registry_access(self):
        from unittest.mock import patch

        with patch("emulator_version.urllib.request.urlopen") as request:
            self.assertEqual(resolve_version(archive=self.archive), self.version)
            request.assert_not_called()

    def test_explicit_version_must_match_candidate(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            resolve_version("0.160.0-android.5", self.archive)

    def test_wrong_candidate_version_is_rejected_before_serving(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            CandidateRegistry(self.archive, "0.160.0-android.5")


if __name__ == "__main__":
    unittest.main()
