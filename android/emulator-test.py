"""Run wrapper checks inside Termux on the dedicated Android test emulator."""

import argparse
import re
import subprocess
import time
from pathlib import Path

AVD_NAME = "Codex_Android_Test_API34"
REMOTE = "/sdcard/Download/codex-android-tests"
TERMUX = "com.termux"


def run(adb, serial, *args, timeout=60, check=True):
    return subprocess.run(
        [str(adb), "-s", serial, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version", help="Exact published npm version, e.g. 0.160.0-android.4"
    )
    parser.add_argument("--serial", default="emulator-5580")
    parser.add_argument(
        "--npm-version",
        default="",
        help="Optional exact npm version to test, e.g. 12.2.0",
    )
    parser.add_argument(
        "--ready",
        action="store_true",
        help="Skip the checkpoint once Termux is bootstrapped and at its prompt",
    )
    parser.add_argument("--sdk", type=Path, default=Path.home() / "Library/Android/sdk")
    parser.add_argument(
        "--termux-apk", type=Path, help="Verified official ARM64 Termux APK"
    )
    parser.add_argument(
        "--reports",
        type=Path,
        default=Path.home() / ".codex/codex-android-release/emulator/reports",
    )
    parser.add_argument(
        "--timeout", type=int, default=1800, help="Suite timeout in seconds"
    )
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+-android\.\d+", args.version):
        parser.error(
            "Supply an exact Android release version, not latest or shell arguments"
        )
    if args.npm_version and not re.fullmatch(r"\d+\.\d+\.\d+", args.npm_version):
        parser.error("Supply an exact numeric npm version")
    if not re.fullmatch(r"emulator-\d+", args.serial):
        parser.error(
            "Only emulator serials are accepted; physical phones are never modified"
        )
    adb = args.sdk / "platform-tools/adb"
    if not adb.is_file():
        parser.error(f"ADB missing: {adb}")
    name = run(adb, args.serial, "emu", "avd", "name").stdout.splitlines()
    if not name or name[0].strip() != AVD_NAME:
        parser.error(f"Refusing to modify any AVD except {AVD_NAME}")
    if (
        run(adb, args.serial, "shell", "getprop", "sys.boot_completed").stdout.strip()
        != "1"
    ):
        parser.error("Wait for the emulator to finish booting before running")
    if args.termux_apk:
        run(
            adb,
            args.serial,
            "install",
            "-r",
            str(args.termux_apk.resolve()),
            timeout=180,
        )
    packages = run(adb, args.serial, "shell", "pm", "list", "packages", TERMUX).stdout
    if "package:com.termux\n" not in packages:
        parser.error("Install official Termux with --termux-apk first")
    run(
        adb, args.serial, "shell", "am", "start", "-n", "com.termux/.app.TermuxActivity"
    )
    print(
        "Termux opened. On its first launch, wait for bootstrap to finish.", flush=True
    )
    # Download storage is the narrow bridge for scripts and non-secret reports.
    for permission in ["READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE"]:
        run(
            adb,
            args.serial,
            "shell",
            "pm",
            "grant",
            TERMUX,
            f"android.permission.{permission}",
        )
    result = run(
        adb,
        args.serial,
        "shell",
        "pm",
        "grant",
        TERMUX,
        "android.permission.POST_NOTIFICATIONS",
        check=False,
    )
    if result.returncode:
        print("Notification permission unavailable; continuing.", flush=True)
    run(adb, args.serial, "shell", "mkdir", "-p", REMOTE)
    run(
        adb,
        args.serial,
        "shell",
        "rm",
        "-f",
        f"{REMOTE}/exit.txt",
        f"{REMOTE}/exit.tmp",
        f"{REMOTE}/report.txt",
    )
    for script in ["phone-test.sh", "emulator-suite.sh"]:
        run(
            adb,
            args.serial,
            "push",
            str(Path(__file__).with_name(script)),
            f"{REMOTE}/{script}",
        )
    # A normal terminal command preserves Termux's real app UID, PATH and startup.
    # Shell prompt readiness is intentionally a one-time human checkpoint.
    if not args.ready:
        input("When Termux shows its $ prompt, press Enter here to start the tests: ")
    command = f"bash {REMOTE}/emulator-suite.sh {args.version} {REMOTE}"
    if args.npm_version:
        command += f" {args.npm_version}"
    run(adb, args.serial, "shell", "input", "text", command.replace(" ", "%s"))
    run(adb, args.serial, "shell", "input", "keyevent", "66")
    print(
        "Running inside Termux; collecting report (no AI/model requests).", flush=True
    )
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        status = run(
            adb, args.serial, "shell", "cat", f"{REMOTE}/exit.txt", check=False
        )
        if status.returncode == 0 and re.fullmatch(r"\d+\s*", status.stdout):
            args.reports.mkdir(parents=True, exist_ok=True)
            report = (
                args.reports / f"{args.version}-{time.strftime('%Y%m%d-%H%M%S')}.txt"
            )
            run(adb, args.serial, "pull", f"{REMOTE}/report.txt", str(report))
            code = int(status.stdout.strip())
            print(f"{'PASS' if code == 0 else 'FAIL'}: report saved to {report}")
            return 0 if code == 0 else 1
        time.sleep(5)
    args.reports.mkdir(parents=True, exist_ok=True)
    report = args.reports / "timeout-report.txt"
    run(adb, args.serial, "pull", f"{REMOTE}/report.txt", str(report), check=False)
    print(
        f"Timed out; inspect Termux and {report}. Tests may still be running; do not rerun concurrently."
    )
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(f"ADB failed: {error.stderr.strip()[:2000]}")
        raise SystemExit(1) from None
    except subprocess.TimeoutExpired:
        print("ADB timed out; check the emulator is responsive before retrying.")
        raise SystemExit(1) from None
