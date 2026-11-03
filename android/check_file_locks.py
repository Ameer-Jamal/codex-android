"""Flag new raw standard-library file-lock calls in the Android source inventory.

This is a source-pattern tripwire, not Rust type analysis. It recognizes File::
methods, file-named receivers and shared/unlock methods. Review differently named
handles and OS-specific additions during every upstream merge as well.
"""

import collections
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(
    r"\b(?:File::(?P<static>try_lock_shared|lock_shared|try_lock|unlock|lock)\b"
    r"|(?P<receiver>(?:\w*_)?file(?:_\w+)?)\s*\.\s*"
    r"(?P<method>try_lock_shared|lock_shared|try_lock|unlock|lock)\s*\()"
)
# Reviewed pre-existing fallbacks or platform-specific test fixtures. Counts make
# an additional matching call in these files require review rather than pass free.
REVIEWED = {
    "arg0/src/lib.rs": {
        "try_lock": 3
    },  # Unsupported => skip cleanup/keep startup working.
    "execpolicy/src/amend.rs": {"lock": 1},  # Unsupported fallback retained.
    "message-history/src/lib.rs": {"try_lock": 1, "try_lock_shared": 1},
    "message-history/src/batch.rs": {
        "try_lock_shared": 1
    },  # History fallback retained.
    "rollout/src/writer_lock.rs": {
        "try_lock": 4
    },  # Existing Android ownership fallback.
    "core/src/installation_id.rs": {
        "lock": 1
    },  # Injected lock with Unsupported fallback.
    "rollout/src/session_index_tests.rs": {"try_lock": 2, "unlock": 1},
    "windows-sandbox-rs/tests/support/src/lib.rs": {"lock": 1},
}


def calls(source):
    # Keep newlines so diagnostics point to the real source line.
    source = re.sub(r"/\*.*?\*/", lambda m: "\n" * m[0].count("\n"), source, flags=re.S)
    source = re.sub(r"//[^\n]*", "", source)
    return [
        (source.count("\n", 0, m.start()) + 1, m["static"] or m["method"])
        for m in PATTERN.finditer(source)
    ]


def check(root=ROOT / "codex-rs"):
    errors = []
    for path in root.rglob("*.rs"):
        relative = path.relative_to(root).as_posix()
        if (
            "target" in path.relative_to(root).parts
            or relative == "keyring-store/src/file_lock.rs"
        ):
            continue
        found = calls(path.read_text())
        actual = collections.Counter(method for _, method in found)
        allowed = REVIEWED.get(relative, {})
        for method, count in actual.items():
            if count > allowed.get(method, 0):
                lines = [str(line) for line, name in found if name == method]
                errors.append(
                    f"{relative}:{','.join(lines)}: raw {method}; use codex_keyring_store::file_lock or review Android handling"
                )
    return errors


if __name__ == "__main__":
    errors = check()
    print("\n".join(errors) if errors else "PASS: Android file-lock source inventory")
    raise SystemExit(bool(errors))
