"""Device-selection and UI guards for the zero-model app build experiment."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from app_emulator import choose_avd

spec = importlib.util.spec_from_file_location(
    "app_build_e2e", Path(__file__).with_name("app-build-e2e.py")
)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class AppBuildGuards(unittest.TestCase):
    def test_emulator_selection_never_falls_back_to_phone(self):
        output = "List of devices attached\nphone123\tdevice\nemulator-5580\tdevice\n"
        self.assertEqual(driver.select_device(output, emulator=True), "emulator-5580")
        for listing in [
            "List of devices attached\nphone123\tdevice\n",
        ]:
            with self.assertRaises(ValueError):
                driver.select_device(listing, emulator=True)
        self.assertEqual(
            driver.select_device(output + "emulator-5582\tdevice\n", emulator=True),
            "emulator-5580",
        )
        with self.assertRaises(ValueError):
            driver.select_device(output, "phone123", emulator=True)
        self.assertEqual(
            driver.select_device(output, "emulator-5580", emulator=True),
            "emulator-5580",
        )

    def test_avd_selection_prefers_recent_dedicated_arm64_and_skips_other_abis(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            names = [
                "Pixel",
                "Codex_Android_Test_API34",
                "Codex_Android_Test_API37",
                "Codex_Android_Test_API37_16KB",
                "Desktop",
            ]
            for name in names:
                directory = root / f"{name}.avd"
                directory.mkdir()
                (directory / "config.ini").write_text(
                    f"abi.type={'x86_64' if name == 'Desktop' else 'arm64-v8a'}\nimage.sysdir.1=system-images/android-{'34' if name.endswith('34') else '37'}/google_apis/arm64-v8a/\n"
                )
            self.assertEqual(choose_avd(names, root), "Codex_Android_Test_API37")
            with self.assertRaises(ValueError):
                choose_avd(["Desktop"], root)

    def test_usb_selection_ignores_wireless_duplicate_and_emulators(self):
        output = "List of devices attached\nphone123\tdevice\nadb-phone._adb-tls-connect._tcp.\tdevice\nemulator-5580\tdevice\n"
        self.assertEqual(driver.select_device(output), "phone123")

    def test_ambiguous_and_unauthorized_devices_require_explicit_selection(self):
        for output in [
            "List of devices attached\nphone1\tunauthorized\n",
            "List of devices attached\nphone1\tdevice\nphone2\tdevice\n",
        ]:
            with self.assertRaises(ValueError):
                driver.select_device(output)
        self.assertEqual(
            driver.select_device(
                "List of devices attached\nphone1\tdevice\nphone2\tdevice\n", "phone2"
            ),
            "phone2",
        )

    def test_ui_selection_never_uses_other_app_or_disabled_control(self):
        xml = '<hierarchy><node package="other.app" resource-id="com.termux:id/new_session_button" enabled="true"/><node package="com.termux" resource-id="com.termux:id/new_session_button" enabled="false"/></hierarchy>'
        with self.assertRaises(ValueError):
            driver.find_node(xml, resource="com.termux:id/new_session_button")
        valid = '<hierarchy><node package="com.termux" resource-id="com.termux:id/new_session_button" enabled="true" bounds="[10,20][30,40]"/></hierarchy>'
        node = driver.find_node(valid, resource="com.termux:id/new_session_button")
        self.assertEqual(driver.center(node.get("bounds")), ("20", "30"))
        with self.assertRaises(ValueError):
            driver.center("bad bounds")

    def test_missing_sdk_fails_before_device_operations(self):
        with tempfile.TemporaryDirectory() as scratch:
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("app-build-e2e.py")),
                    "--sdk",
                    scratch,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Install SDK", result.stderr)


if __name__ == "__main__":
    unittest.main()
