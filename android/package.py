#!/usr/bin/env python3
"""Package an already built Android runtime without downloading or publishing."""

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "aarch64-linux-android"


def validate_android_elf(source: Path) -> None:
    with source.open("rb") as binary:
        header = binary.read(64)
    if (
        len(header) < 64
        or header[:6] != b"\x7fELF\x02\x01"
        or struct.unpack_from("<H", header, 18)[0] != 183
    ):
        raise ValueError(f"{source} is not a little-endian ARM64 ELF binary")


def stage_runtime(binary_dir: Path, libcxx: Path, staging: Path) -> None:
    # Resolve and validate every required runtime component before staging.
    sources = [binary_dir / "codex", binary_dir / "codex-code-mode-host", libcxx]
    for source in sources:
        validate_android_elf(source)
    staging.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((ROOT / "codex-cli/package.json").read_text())
    (staging / "package.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for name in ["LICENSE", "NOTICE", "README.md"]:
        shutil.copy2(ROOT / name, staging / name)
    shutil.copytree(ROOT / "third_party/v8/licenses", staging / "licenses/v8")
    (staging / "assets").mkdir()
    shutil.copy2(ROOT / "assets/icon.png", staging / "assets/icon.png")
    for name in ["bin/codex.js", "scripts/postinstall.js"]:
        destination = staging / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "codex-cli" / name, destination)
    runtime = staging / "vendor" / TARGET
    (runtime / "bin").mkdir(parents=True)
    (runtime / "codex-package.json").write_text(
        json.dumps({"version": manifest["version"]}, indent=2) + "\n"
    )
    for source in sources:
        destination = runtime / "bin" / source.name
        shutil.copy2(source, destination)
        destination.chmod(0o755)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary-dir", type=Path, required=True)
    parser.add_argument("--libcxx", type=Path, required=True)
    parser.add_argument("--ndk-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="codex-android-package-") as scratch:
        staging = Path(scratch) / "package"
        stage_runtime(args.binary_dir, args.libcxx, staging)
        for name in ["NOTICE", "NOTICE.toolchain"]:
            shutil.copy2(args.ndk_root / name, staging / "licenses" / f"NDK-{name}")
        result = subprocess.run(
            [
                "npm",
                "pack",
                "--ignore-scripts",
                "--json",
                "--pack-destination",
                str(output),
            ],
            cwd=staging,
            check=True,
            capture_output=True,
            text=True,
        )
        archive = output / json.loads(result.stdout)[0]["filename"]
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    archive.with_name(archive.name + ".sha256").write_text(
        f"{digest}  {archive.name}\n"
    )
    print(archive)


if __name__ == "__main__":
    main()
