"""Regression coverage for the Android runtime artifact boundary."""

import json
import struct
import tempfile
import unittest
from pathlib import Path

from package import stage_runtime, validate_android_elf


def write_elf(path: Path, machine: int = 183) -> None:
    header = bytearray(64)
    header[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<H", header, 18, machine)
    path.write_bytes(header)


class AndroidPackageTests(unittest.TestCase):
    def test_stages_complete_runtime_with_licenses_and_local_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            binaries = root / "binaries"
            binaries.mkdir()
            for name in ["codex", "codex-code-mode-host", "libc++_shared.so"]:
                write_elf(binaries / name)
            staging = root / "staging"
            stage_runtime(binaries, binaries / "libc++_shared.so", staging)
            runtime = staging / "vendor/aarch64-linux-android"
            self.assertEqual(
                {path.name for path in (runtime / "bin").iterdir()},
                {"codex", "codex-code-mode-host", "libc++_shared.so"},
            )
            manifest = json.loads((staging / "package.json").read_text())
            self.assertEqual(manifest["bin"], {"codex": "bin/codex.js"})
            self.assertEqual(
                json.loads((runtime / "codex-package.json").read_text()),
                {"version": manifest["version"]},
            )
            for name in ["LICENSE", "NOTICE", "bin/codex.js", "scripts/postinstall.js"]:
                self.assertTrue((staging / name).is_file(), name)

    def test_rejects_host_binaries_before_staging(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            write_elf(root / "codex", machine=62)
            with self.assertRaisesRegex(ValueError, "ARM64 ELF"):
                stage_runtime(root, root / "libc++_shared.so", root / "staging")
            self.assertFalse((root / "staging").exists())

    def test_requires_code_mode_host_and_shared_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            write_elf(root / "codex")
            with self.assertRaises(FileNotFoundError):
                stage_runtime(root, root / "libc++_shared.so", root / "staging")
            write_elf(root / "codex-code-mode-host")
            with self.assertRaises(FileNotFoundError):
                stage_runtime(root, root / "libc++_shared.so", root / "staging")
            self.assertFalse((root / "staging").exists())

    def test_rejects_truncated_elf(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "codex"
            source.write_bytes(b"\x7fELF")
            with self.assertRaises(ValueError):
                validate_android_elf(source)


if __name__ == "__main__":
    unittest.main()
