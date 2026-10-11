"""One-command unattended wrapper tests on a dedicated macOS/Unix Android emulator."""

import argparse
import fcntl
import re
import subprocess
import time
from pathlib import Path

from emulator_registry import CandidateRegistry
from emulator_support import (
    dispatch,
    ensure_emulator,
    official_termux,
    run,
    wait_for_termux,
)
from emulator_version import resolve_version

REMOTE = "/data/data/com.termux/files/home/codex-android-tests"


def execute(args, adb):
    run_id = time.time_ns()
    report = args.reports / f"{args.version}-{run_id}.txt"
    remote = f"{REMOTE}-{run_id}"
    staging = f"/data/local/tmp/codex-android-tests-{run_id}"
    process = ensure_emulator(
        args.sdk,
        adb,
        args.serial,
        report.with_suffix(".emulator.log"),
        args.api,
        headless=args.headless,
    )
    launched_suite = False
    registry = None
    try:
        if not args.reuse:
            print("Resetting Termux in the dedicated test AVD...", flush=True)
            run(adb, args.serial, "uninstall", "com.termux", check=False, timeout=120)
        packages = run(
            adb, args.serial, "shell", "pm", "list", "packages", "com.termux"
        ).stdout
        if "package:com.termux\n" not in packages:
            cache = Path.home() / ".codex/codex-android-release/emulator"
            cache.mkdir(parents=True, exist_ok=True)
            apk = args.termux_apk or official_termux(cache)
            run(adb, args.serial, "install", "-r", str(apk.resolve()), timeout=240)
        run(adb, args.serial, "logcat", "-c")
        run(adb, args.serial, "shell", "mkdir", "-p", staging)
        run(
            adb,
            args.serial,
            "shell",
            "am",
            "start",
            "-n",
            "com.termux/.app.TermuxActivity",
        )
        wait_for_termux(adb, args.serial, staging, args.api)
        run(adb, args.serial, "shell", "run-as", "com.termux", "mkdir", "-p", remote)
        # Copy through the debug app UID; Android shared-storage FUSE blocks ADB
        # writes on some repeat runs. Tests still execute in the Termux terminal.
        for script in ["phone-test.sh", "emulator-suite.sh", "runtime-e2e.cjs"]:
            run(
                adb,
                args.serial,
                "push",
                str(Path(__file__).with_name(script)),
                f"{staging}/{script}",
            )
            run(
                adb,
                args.serial,
                "shell",
                "run-as",
                "com.termux",
                "cp",
                f"{staging}/{script}",
                f"{remote}/{script}",
            )
        # The probe is executed by the actual Termux terminal, not ADB's shell UID.
        probe = report.with_suffix(".probe.sh")
        probe.write_text(
            f"#!/usr/bin/env bash\nprintf 'READY\\n' > {remote}/ready.txt\n"
        )
        run(adb, args.serial, "push", str(probe), f"{staging}/ready.sh")
        run(
            adb,
            args.serial,
            "shell",
            "run-as",
            "com.termux",
            "cp",
            f"{staging}/ready.sh",
            f"{remote}/ready.sh",
        )
        probe.unlink()
        source = ""
        if args.package:
            registry = CandidateRegistry(args.package.resolve(), args.version)
            run(
                adb,
                args.serial,
                "reverse",
                f"tcp:{registry.port}",
                f"tcp:{registry.port}",
            )
            source = f" {registry.url}"
        dispatch(adb, args.serial, f"bash {remote}/ready.sh")
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            ready = run(
                adb,
                args.serial,
                "shell",
                "run-as",
                "com.termux",
                "cat",
                f"{remote}/ready.txt",
                check=False,
            )
            if ready.returncode == 0 and ready.stdout.strip() == "READY":
                break
            time.sleep(1)
        else:
            raise ValueError(
                "Termux did not acknowledge the readiness probe; refusing to start tests"
            )
        dispatch(
            adb,
            args.serial,
            f"bash {remote}/emulator-suite.sh {args.version} {remote} {args.npm_version}{source}",
        )
        launched_suite = True
        print("Running unattended inside Termux; no live model requests...", flush=True)
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            status = run(
                adb,
                args.serial,
                "shell",
                "run-as",
                "com.termux",
                "cat",
                f"{remote}/exit.txt",
                check=False,
            )
            if status.returncode == 0 and re.fullmatch(r"\d+\s*", status.stdout):
                report.write_text(
                    run(
                        adb,
                        args.serial,
                        "shell",
                        "run-as",
                        "com.termux",
                        "cat",
                        f"{remote}/report.txt",
                    ).stdout
                )
                code = int(status.stdout.strip())
                print(f"{'PASS' if code == 0 else 'FAIL'}: {report}")
                return 0 if code == 0 else 1
            time.sleep(5)
        raise ValueError(f"Suite timed out; partial report: {report}")
    finally:
        try:
            if not launched_suite:
                bootstrap = run(
                    adb,
                    args.serial,
                    "logcat",
                    "-d",
                    "-t",
                    "5000",
                    check=False,
                    timeout=30,
                )
                report.with_suffix(".bootstrap.log").write_text(
                    "\n".join(
                        line
                        for line in bootstrap.stdout.splitlines()
                        if "Termux:TermuxInstaller" in line
                    )
                )
            if registry:
                run(
                    adb,
                    args.serial,
                    "reverse",
                    "--remove",
                    f"tcp:{registry.port}",
                    check=False,
                )
            if launched_suite:
                partial = run(
                    adb,
                    args.serial,
                    "shell",
                    "run-as",
                    "com.termux",
                    "cat",
                    f"{remote}/report.txt",
                    check=False,
                )
                if partial.returncode == 0:
                    report.write_text(partial.stdout)
            run(adb, args.serial, "shell", "rm", "-rf", staging, check=False)
            run(
                adb, args.serial, "shell", "am", "force-stop", "com.termux", check=False
            )
            run(
                adb,
                args.serial,
                "shell",
                "run-as",
                "com.termux",
                "rm",
                "-rf",
                remote,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            print(f"Cleanup diagnostic unavailable: {error}", flush=True)
        finally:
            if registry:
                registry.close()
            if process and not args.keep_emulator:
                try:
                    run(adb, args.serial, "emu", "kill", check=False, timeout=15)
                    process.wait(timeout=30)
                except subprocess.SubprocessError:
                    process.terminate()
                    process.wait(timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version",
        nargs="?",
        help="Optional exact version; defaults to candidate version or npm latest",
    )
    parser.add_argument("--serial", default="emulator-5580")
    parser.add_argument(
        "--api",
        type=int,
        choices=[34, 37],
        default=37,
        help="API 37: Android 17, standard page-size image (default); API 34: Android 14",
    )
    parser.add_argument("--npm-version", default="12.2.0")
    parser.add_argument("--sdk", type=Path, default=Path.home() / "Library/Android/sdk")
    parser.add_argument(
        "--termux-apk", type=Path, help="Optional verified official debug APK"
    )
    parser.add_argument(
        "--package",
        type=Path,
        help="Built candidate .tgz to test before npm publication",
    )
    parser.add_argument(
        "--reuse", action="store_true", help="Reuse Termux instead of clean install"
    )
    parser.add_argument("--keep-emulator", action="store_true")
    parser.add_argument(
        "--headless", action="store_true", help="Run without an emulator window"
    )
    parser.add_argument(
        "--ready", action="store_true", help=argparse.SUPPRESS
    )  # Backwards compatible; readiness is always automatic.
    parser.add_argument(
        "--reports",
        type=Path,
        default=Path.home() / ".codex/codex-android-release/emulator/reports",
    )
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if args.version is not None and not re.fullmatch(
        r"\d+\.\d+\.\d+-android\.\d+", args.version
    ):
        parser.error(
            "Supply an exact Android release version, not latest or shell arguments"
        )
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.npm_version):
        parser.error("Supply an exact numeric npm version")
    if (
        not re.fullmatch(r"emulator-\d+", args.serial)
        or int(args.serial.split("-")[1]) % 2
    ):
        parser.error(
            "Only even-port emulator serials are accepted; physical phones are never modified"
        )
    if args.timeout < 30:
        parser.error("Timeout must be at least 30 seconds")
    for path in [args.package, args.termux_apk]:
        if path and not path.is_file():
            parser.error(f"File does not exist: {path}")
    adb = args.sdk / "platform-tools/adb"
    if not adb.is_file():
        parser.error(f"ADB missing: {adb}")
    args.version = resolve_version(args.version, args.package)
    print(f"Testing codex-android@{args.version}", flush=True)
    args.reports.mkdir(parents=True, exist_ok=True)
    lock_dir = Path.home() / ".codex/codex-android-release/emulator/locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    with (lock_dir / f"{args.serial}.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("An emulator test is already running; wait for its report")
        return execute(args, adb)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted; test processes stopped and any partial report saved.")
        raise SystemExit(130) from None
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or str(error)).strip()
        print(f"FAIL: {detail[:2000]}")
        raise SystemExit(1) from None
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}")
        raise SystemExit(1) from None
