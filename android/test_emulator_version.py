"""Check automatic version resolution without launching or resetting an emulator."""

import io
import json
import unittest
from unittest.mock import patch

from emulator_version import resolve_version


class PublishedVersionTests(unittest.TestCase):
    def test_latest_is_resolved_from_small_registry_metadata(self):
        body = json.dumps(
            {"name": "codex-android", "version": "0.160.0-android.8"}
        ).encode()
        with patch(
            "emulator_version.urllib.request.urlopen", return_value=io.BytesIO(body)
        ) as request:
            self.assertEqual(resolve_version(), "0.160.0-android.8")
            request.assert_called_once_with(
                "https://registry.npmjs.org/codex-android/latest", timeout=30
            )

    def test_explicit_version_does_not_query_registry(self):
        with patch("emulator_version.urllib.request.urlopen") as request:
            self.assertEqual(resolve_version("0.160.0-android.4"), "0.160.0-android.4")
            request.assert_not_called()

    def test_wrong_registry_package_is_rejected(self):
        with (
            patch(
                "emulator_version.urllib.request.urlopen",
                return_value=io.BytesIO(
                    b'{"name":"other","version":"0.160.0-android.4"}'
                ),
            ),
            self.assertRaisesRegex(ValueError, "different package"),
        ):
            resolve_version()


if __name__ == "__main__":
    unittest.main()
