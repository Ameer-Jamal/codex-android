"""Check phone diagnostics isolation and failure reporting with a fake runtime."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("phone-test.sh")


class PhoneChecksTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.package = self.root / "modules/codex-android"
        (self.package / "bin").mkdir(parents=True)
        (self.package / "package.json").write_text(
            json.dumps({"name": "codex-android", "version": "1.0.0-test"})
        )
        self.home = self.root / "home"
        self.home.mkdir()
        self.secret = self.home / ".codex-android/auth.json"
        self.secret.parent.mkdir()
        self.secret.write_text("private sentinel")
        self.env = dict(
            os.environ,
            HOME=str(self.home),
            TMPDIR=str(self.root),
            PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            CODEX_HOME=str(self.secret.parent),
            CODEX_ANDROID_USE_DAEMON="1",
            PHONE_CALLS=str(self.root / "calls"),
        )
        real_node = shutil.which("node")
        self.write_tool(
            "node",
            f"#!{sys.executable}\n"
            "import os, sys\n"
            'if "process.platform" in sys.argv[2]: sys.exit(0)\n'
            f"os.execv({real_node!r}, [{real_node!r}, *sys.argv[1:]])\n",
        )
        self.write_tool("npm", f"#!/usr/bin/env bash\necho '{self.package.parent}'\n")
        self.write_tool("termux-open-url", "#!/usr/bin/env bash\nexit 0\n")
        runtime = self.package / "bin/codex.js"
        runtime.write_text(
            "#!/usr/bin/env bash\n"
            'mkdir -m 700 -p "$CODEX_HOME"\n'
            'printf "%s|%s|%s\\n" "$CODEX_HOME" "${CODEX_ANDROID_USE_DAEMON:-}" "$*" >> "$PHONE_CALLS"\n'
            'if [[ $* == "login status" ]]; then echo "Not logged in" >&2; exit 1; fi\n'
            "if [[ ${PHONE_FAIL_EXEC:-} == 1 && $1 == exec ]]; then exit 1; fi\n"
        )
        runtime.chmod(0o755)
        (self.bin / "codex").symlink_to(runtime)

    def write_tool(self, name, content):
        target = self.bin / name
        target.write_text(content)
        target.chmod(0o755)

    def run_checks(self, *args):
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_success_isolates_home_and_never_sends_model_requests(self):
        result = self.run_checks("1.0.0-test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = (self.root / "calls").read_text().splitlines()
        self.assertEqual(len(calls), 8)
        for call in calls:
            home, daemon, args = call.split("|")
            self.assertNotEqual(home, str(self.secret.parent))
            self.assertFalse(Path(home).exists())
            self.assertEqual(daemon, "")
            self.assertTrue(
                args.endswith("--help") or args in ["--version", "login status"]
            )
        self.assertEqual(self.secret.read_text(), "private sentinel")

    def test_runtime_failure_returns_failure_and_cleans_temporary_home(self):
        self.env["PHONE_FAIL_EXEC"] = "1"
        result = self.run_checks()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL  Exec help", result.stdout)
        self.assertEqual(list(self.root.glob("codex-phone-test.*")), [])
        self.assertEqual(self.secret.read_text(), "private sentinel")

    def test_wrong_path_command_is_never_launched(self):
        (self.bin / "codex").unlink()
        self.write_tool("codex", "#!/usr/bin/env bash\nexit 99\n")
        result = self.run_checks()
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not point to this package", result.stdout)
        self.assertFalse((self.root / "calls").exists())

    def test_unexpected_release_returns_failure(self):
        result = self.run_checks("2.0.0-test")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Expected 2.0.0-test", result.stdout)


if __name__ == "__main__":
    unittest.main()
