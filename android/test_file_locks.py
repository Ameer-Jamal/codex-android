import tempfile
import unittest
from pathlib import Path
from check_file_locks import calls, check


class FileLockInventoryTests(unittest.TestCase):
    def test_recognizes_file_calls_and_ignores_mutex_and_comments(self):
        self.assertEqual(
            calls(
                "// file.lock();\nfile.lock()?;\nself._file.try_lock();\nstd::fs::File::unlock(&f);\nmutex.lock();"
            ),
            [(2, "lock"), (3, "try_lock"), (4, "unlock")],
        )

    def test_rejects_new_raw_lock_but_accepts_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "new.rs"
            source.write_text("file.try_lock()?;")
            self.assertTrue(check(root))
            source.write_text(
                "codex_keyring_store::file_lock::try_lock_exclusive(&file)?;"
            )
            self.assertEqual(check(root), [])

    def test_reviewed_file_cannot_gain_an_extra_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "execpolicy/src/amend.rs"
            source.parent.mkdir(parents=True)
            source.write_text("file.lock()?;\nfile.lock()?;")
            self.assertTrue(check(root))
