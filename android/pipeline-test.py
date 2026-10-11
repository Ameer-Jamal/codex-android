"""Test a successful GitHub ARM64 build locally and publish its commit status."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "Ameer-Jamal/codex-android"


def gh(*args):
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout


def validate_build(build):
    if (
        build.get("conclusion") != "success"
        or build.get("head_branch") != "main"
        or build.get("event") not in ["push", "workflow_dispatch"]
        or build.get("path") != ".github/workflows/android.yml"
        or build.get("head_repository", {}).get("full_name") != REPO
        or not re.fullmatch(r"[0-9a-f]{40}", build.get("head_sha", ""))
    ):
        raise ValueError(
            "Only successful Android builds from this repository's main branch are accepted"
        )


def verify_archive(directory):
    archives = list(directory.rglob("*.tgz"))
    if len(archives) != 1:
        raise ValueError("Build must contain exactly one candidate package")
    archive = archives[0]
    sidecar = archive.with_name(archive.name + ".sha256")
    expected = sidecar.read_text().split()[0]
    with archive.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != expected:
        raise ValueError("Candidate checksum does not match the build's sidecar")
    return archive, actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "run_id",
        nargs="?",
        help="Successful build ID; defaults to a successful build of current main",
    )
    parser.add_argument("--api", type=int, choices=[34, 37], default=37)
    parser.add_argument("--sdk", type=Path, default=Path.home() / "Library/Android/sdk")
    parser.add_argument(
        "--no-status",
        action="store_true",
        help="Test without writing a GitHub commit status",
    )
    args = parser.parse_args()
    if args.run_id is None:
        head = json.loads(gh("api", f"repos/{REPO}/commits/main"))["sha"]
        runs = json.loads(
            gh(
                "api",
                f"repos/{REPO}/actions/workflows/android.yml/runs?head_sha={head}&status=success&per_page=1",
            )
        )["workflow_runs"]
        if not runs:
            raise ValueError(
                "Current main has no successful Android build yet; wait for its build before testing"
            )
        args.run_id = str(runs[0]["id"])
    if not args.run_id.isdigit():
        parser.error("Run ID must contain digits only")
    build = json.loads(gh("api", f"repos/{REPO}/actions/runs/{args.run_id}"))
    validate_build(build)
    harness_source = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parent,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    harness_dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain", "--", "android"],
            cwd=Path(__file__).resolve().parent.parent,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    context = f"android/emulator-api{args.api}"
    endpoint = f"repos/{REPO}/statuses/{build['head_sha']}"

    def status(state, description):
        if not args.no_status:
            gh(
                "api",
                endpoint,
                "--method",
                "POST",
                "-f",
                f"state={state}",
                "-f",
                f"context={context}",
                "-f",
                f"description={description}",
                "-f",
                f"target_url={build['html_url']}",
            )

    reports = (
        Path.home()
        / f".codex/codex-android-release/emulator/pipeline-{args.run_id}-api{args.api}"
    )
    reports.mkdir(parents=True, exist_ok=True)
    status("pending", "Mac emulator acceptance running")
    try:
        with tempfile.TemporaryDirectory(prefix="codex-android-candidate-") as scratch:
            gh(
                "run",
                "download",
                args.run_id,
                "--repo",
                REPO,
                "--name",
                "codex-android-arm64",
                "--dir",
                scratch,
            )
            archive, digest = verify_archive(Path(scratch))
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("emulator-test.py")),
                    "--package",
                    str(archive),
                    "--api",
                    str(args.api),
                    "--sdk",
                    str(args.sdk),
                    "--reports",
                    str(reports),
                ],
                check=False,
            )
            record = {
                "build_run": args.run_id,
                "source": build["head_sha"],
                "harness_source": harness_source,
                "harness_dirty": harness_dirty,
                "sha256": digest,
                "api": args.api,
                "exit_code": result.returncode,
            }
            (reports / "result.json").write_text(json.dumps(record, indent=2) + "\n")
            status(
                "success" if result.returncode == 0 else "failure",
                f"Emulator {'passed' if result.returncode == 0 else 'failed'}; SHA256 {digest[:16]}",
            )
            print(f"Pipeline report: {reports}")
            return result.returncode
    except BaseException:
        status(
            "error",
            "Emulator acceptance interrupted or setup failed; inspect Mac report",
        )
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from None
