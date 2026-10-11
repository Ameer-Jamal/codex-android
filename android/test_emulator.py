"""Verify emulator runner refuses unrelated devices before installing anything."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("emulator-test.py")


class EmulatorGuardTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        (self.root / "platform-tools").mkdir()
        self.log = self.root / "calls"
        adb = self.root / "platform-tools/adb"
        adb.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            'with open(os.environ["EMU_CALLS"], "a") as out: out.write(" ".join(sys.argv[1:]) + "\\n")\n'
            'print(os.environ.get("EMU_NAME", "Pixel_API_34"))\n'
        )
        adb.chmod(0o755)
        self.env = dict(os.environ, EMU_CALLS=str(self.log))

    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--sdk", str(self.root)],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_physical_phone_is_rejected_without_adb_calls(self):
        result = self.invoke("0.160.0-android.4", "--serial", "phone123")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())

    def test_other_avd_is_rejected_before_mutation(self):
        result = self.invoke("0.160.0-android.4")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            self.log.read_text().splitlines(), ["-s emulator-5580 emu avd name"]
        )

    def test_invalid_npm_version_is_rejected_without_adb_calls(self):
        result = self.invoke("0.160.0-android.4", "--npm-version", "12;bad")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())

    def test_invalid_version_is_rejected_without_adb_calls(self):
        result = self.invoke("latest;bad")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
