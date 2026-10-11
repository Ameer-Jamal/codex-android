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
        tools = self.root / "cmdline-tools/latest"
        tools.mkdir(parents=True)
        (tools / "source.properties").write_text("Pkg.Revision=23.0\n")
        self.log = self.root / "calls"
        adb = self.root / "platform-tools/adb"
        adb.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            'with open(os.environ["EMU_CALLS"], "a") as out: out.write(" ".join(sys.argv[1:]) + "\\n")\n'
            'print(os.environ.get("EMU_NAME", "Pixel_API_34"))\n'
        )
        adb.chmod(0o755)
        self.env = dict(os.environ, EMU_CALLS=str(self.log), HOME=str(self.root))

    def invoke(self, *args):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                *args,
                "--sdk",
                str(self.root),
                "--reports",
                str(self.root / "reports"),
            ],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_old_sdk_tools_are_rejected_before_android_17_launch(self):
        (self.root / "cmdline-tools/latest/source.properties").write_text(
            "Pkg.Revision=12.0\n"
        )
        result = self.invoke("0.160.0-android.4")
        self.assertEqual(result.returncode, 1)
        self.assertIn("tools 23+", result.stdout)
        self.assertFalse(self.log.exists())

    def test_physical_phone_is_rejected_without_adb_calls(self):
        result = self.invoke("0.160.0-android.4", "--serial", "phone123")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())

    def test_other_avd_is_rejected_before_mutation(self):
        result = self.invoke("0.160.0-android.4")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            self.log.read_text().splitlines(),
            ["-s emulator-5580 get-state", "-s emulator-5580 emu avd name"],
        )

    def test_dedicated_avd_for_another_api_is_rejected_before_mutation(self):
        self.env["EMU_NAME"] = "Codex_Android_Test_API34"
        result = self.invoke("0.160.0-android.4", "--api", "37")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(self.log.read_text().splitlines()), 2)

    def test_invalid_npm_version_is_rejected_without_adb_calls(self):
        result = self.invoke("0.160.0-android.4", "--npm-version", "12;bad")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())

    def test_invalid_version_is_rejected_without_adb_calls(self):
        result = self.invoke("latest;bad")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())


class EmulatorSetupTests(unittest.TestCase):
    def test_cached_apk_checksum_mismatch_is_rejected_without_download(self):
        from unittest.mock import patch

        from emulator_support import official_termux

        with tempfile.TemporaryDirectory() as scratch:
            cache = Path(scratch)
            (cache / "termux-arm64.apk").write_bytes(b"tampered APK")
            with patch("emulator_support.urllib.request.urlopen") as download:
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    official_termux(cache)
                download.assert_not_called()

    def test_bootstrap_waits_for_a_focused_termux_terminal(self):
        from unittest.mock import patch

        from emulator_support import wait_for_termux

        calls = []

        def fake_run(adb, serial, *args, **kwargs):
            calls.append(args)
            if "run-as" in args:
                # First bootstrap check is not ready; the next is ready.
                code = 1 if len(calls) == 1 else 0
                return subprocess.CompletedProcess(args, code, "", "")
            if "dumpsys" in args:
                return subprocess.CompletedProcess(
                    args,
                    0,
                    "mCurrentFocus=Window{123 u0 com.termux/.app.TermuxActivity}",
                    "",
                )
            return subprocess.CompletedProcess(args, 0, "", "")

        with (
            patch("emulator_support.run", side_effect=fake_run),
            patch("emulator_support.time.sleep") as sleep,
        ):
            wait_for_termux("adb", "emulator-5580", "/report")
            sleep.assert_called_once_with(3)
        self.assertEqual(sum("run-as" in call for call in calls), 2)


if __name__ == "__main__":
    unittest.main()
