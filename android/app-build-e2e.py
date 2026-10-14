"""Build a fixture APK in Termux, install via ADB and verify its counter; no AI."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from app_emulator import ensure_available, prepare_termux


def select_device(output, requested=None, *, emulator=False):
    devices = [line.split() for line in output.splitlines()[1:] if line.strip()]
    ready = [parts[0] for parts in devices if len(parts) >= 2 and parts[1] == "device"]
    if requested:
        if requested not in ready:
            raise ValueError("Selected device is not connected and authorized")
        if emulator and not requested.startswith("emulator-"):
            raise ValueError("--emulator requires an emulator serial")
        return requested
    if emulator:
        candidates = [name for name in ready if name.startswith("emulator-")]
        if not candidates:
            raise ValueError("Start one ARM64 emulator, or select it with --serial")
        return sorted(candidates)[0]
    usb = [
        name
        for name in ready
        if not name.startswith("emulator-") and ":" not in name and "_adb" not in name
    ]
    if len(usb) != 1:
        raise ValueError("Connect one authorized USB phone, or specify --serial")
    return usb[0]


def center(bounds):
    values = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not values:
        raise ValueError("Invalid UI bounds")
    x1, y1, x2, y2 = map(int, values.groups())
    return str((x1 + x2) // 2), str((y1 + y2) // 2)


def find_node(xml, resource=None, text=None, package="com.termux"):
    for node in ET.fromstring(xml).iter("node"):
        if node.get("package") != package:
            continue
        if resource and node.get("resource-id") != resource:
            continue
        if text and node.get("text") != text:
            continue
        if node.get("enabled") == "true":
            return node
    raise ValueError(
        "Expected UI control not found; unlock the phone and keep Termux available"
    )


def execute(args):
    sdk = args.sdk.expanduser().resolve()
    adb = sdk / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
    android_jar = sdk / f"platforms/android-{args.api}/android.jar"
    jars = sorted((sdk / "build-tools").glob("*/lib/d8.jar"))
    if not adb.is_file() or not android_jar.is_file() or not jars:
        raise ValueError(
            "Install SDK platform 34 and Android build-tools in Android Studio, or specify --sdk/--api"
        )
    serial = (
        ensure_available(sdk, adb, args.reports.expanduser())
        if args.emulator and not args.serial
        else select_device(
            subprocess.check_output([str(adb), "devices"], text=True),
            args.serial,
            emulator=args.emulator,
        )
    )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + secrets.token_hex(2)
    app = f"dev.codexandroid.e2e.demo{run_id}"
    reports = args.reports.expanduser().resolve() / run_id
    reports.mkdir(parents=True)
    transport = f"/sdcard/Download/codex-app-e2e-{run_id}"
    record = {
        "app_id": app,
        "run_id": run_id,
        "model_requests": 0,
        "target": "emulator" if serial.startswith("emulator-") else "phone",
    }

    def call(*command, timeout=30, check=True):
        return subprocess.run(
            [str(adb), "-s", serial, *command],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )

    def shell(*command, **kwargs):
        return call("shell", shlex.join(command), **kwargs)

    def ui():
        try:
            shell("uiautomator", "dump", f"{transport}/ui.xml", timeout=20)
            return shell("cat", f"{transport}/ui.xml").stdout
        finally:
            shell("rm", "-f", f"{transport}/ui.xml", check=False)

    try:
        abi = shell("getprop", "ro.product.cpu.abi").stdout.strip()
        if abi != "arm64-v8a":
            raise ValueError("This demo requires ARM64 Termux")
        if serial.startswith("emulator-"):
            prepare_termux(adb, serial, args.reports.expanduser() / "termux-cache")
        record["android"] = shell("getprop", "ro.build.version.release").stdout.strip()
        record["abi"] = abi
        if shell("pm", "list", "packages", app).stdout.strip():
            raise ValueError("Demo package already exists; refusing to replace it")
        shell("mkdir", transport)
        shell("input", "keyevent", "224")
        if any(
            "keyguard" in node.get("resource-id", "")
            for node in ET.fromstring(ui()).iter("node")
        ):
            raise ValueError("Unlock the phone before running this test")
        fixture = Path(__file__).parent / "demos/hello-world"
        with tempfile.TemporaryDirectory(prefix="codex-app-fixture-") as scratch:
            stage = Path(scratch)
            for source in fixture.iterdir():
                if source.suffix in [".java", ".xml"]:
                    (stage / source.name).write_text(
                        source.read_text().replace("__APP_ID__", app)
                    )
                else:
                    shutil.copy2(source, stage / source.name)
            call(
                "push",
                *[str(p) for p in stage.iterdir()],
                str(android_jar),
                str(jars[-1]),
                transport + "/",
                timeout=120,
            )
        print(
            "Opening a new Termux session; existing sessions remain running.",
            flush=True,
        )
        shell("am", "start", "-W", "-n", "com.termux/.app.TermuxActivity")
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                find_node(ui(), resource="com.termux:id/terminal_view")
                break
            except ValueError:
                time.sleep(2)
        else:
            raise ValueError(
                "Termux terminal did not become ready; check its emulator window"
            )
        size = re.findall(r"(\d+)x(\d+)", shell("wm", "size").stdout)
        width, height = map(int, size[-1])
        for inset in [max(10, width // 50), width // 14, width // 8]:
            try:
                button = find_node(ui(), resource="com.termux:id/new_session_button")
                break
            except ValueError:
                shell(
                    "input",
                    "swipe",
                    str(inset),
                    str(height // 3),
                    str(width // 2),
                    str(height // 3),
                    "350",
                )
                time.sleep(1)
        else:
            button = find_node(ui(), resource="com.termux:id/new_session_button")
        shell("input", "tap", *center(button.get("bounds", "")))
        time.sleep(3)
        # Require a new visible terminal; never type into an unidentified app.
        terminal = find_node(ui(), resource="com.termux:id/terminal_view")
        if terminal.get("focused") != "true":
            raise ValueError("New Termux terminal is not focused; refusing to type")
        command = f"bash {transport}/build.sh {transport} {run_id}"
        # Pace key injection: Android keyboards can drop a long initial burst.
        for offset in range(0, len(command), 8):
            shell("input", "text", command[offset : offset + 8].replace(" ", "%s"))
            time.sleep(0.15)
        shell("input", "keyevent", "66")
        started = time.monotonic() + 30
        while time.monotonic() < started:
            if (
                shell("test", "-f", f"{transport}/build.log", check=False).returncode
                == 0
            ):
                break
            time.sleep(1)
        else:
            raise ValueError(
                "Termux did not start the build; its new session is left intact"
            )
        print(
            "Compiling/signing inside Android. No Codex or model invocation.",
            flush=True,
        )
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            result = shell("cat", f"{transport}/exit.txt", check=False)
            if result.returncode == 0:
                break
            time.sleep(3)
        else:
            raise TimeoutError(
                "On-phone build timed out; its Termux session is left intact"
            )
        call("pull", f"{transport}/build.log", str(reports / "build.log"))
        if result.stdout.strip() != "0":
            raise ValueError(f"On-phone build failed; see {reports / 'build.log'}")
        call("pull", f"{transport}/hello-world.apk", str(reports / "hello-world.apk"))
        digest = hashlib.sha256((reports / "hello-world.apk").read_bytes()).hexdigest()
        if shell("cat", f"{transport}/sha256.txt").stdout.split()[0] != digest:
            raise ValueError("Transferred APK checksum mismatch")
        record["sha256"] = digest
        record["phone_project"] = shell(
            "cat", f"{transport}/project-path.txt"
        ).stdout.strip()
        print("Installing only the new demo package through ADB.", flush=True)
        installed = call("install", str(reports / "hello-world.apk"), timeout=120)
        if "Success" not in installed.stdout:
            raise ValueError("Android did not report successful installation")
        shell("am", "start", "-n", f"{app}/.MainActivity")
        screen = ui()
        find_node(screen, text="Taps: 0", package=app)
        button = find_node(screen, text="Tap me", package=app)
        shell("input", "tap", *center(button.get("bounds", "")))
        find_node(ui(), text="Taps: 1", package=app)
        screenshot = subprocess.check_output(
            [str(adb), "-s", serial, "exec-out", "screencap", "-p"], timeout=30
        )
        (reports / "running.png").write_bytes(screenshot)
        pid = shell("pidof", app).stdout.strip()
        if not re.fullmatch(r"\d+", pid):
            raise ValueError("Demo process is not running")
        logs = shell(
            "logcat",
            "-d",
            f"--pid={pid}",
            "-s",
            "CodexHelloWorld:I",
            "AndroidRuntime:E",
        ).stdout
        (reports / "app.log").write_text(logs)
        if "FATAL EXCEPTION" in logs:
            raise ValueError("Demo crash found in its process log")
        record["result"] = "pass"
        print(
            f"PASS: built inside Android, installed and counter verified. Report: {reports}",
            flush=True,
        )
    except BaseException as error:
        record["result"] = "fail"
        record["error"] = str(error)
        raise
    finally:
        (reports / "result.json").write_text(json.dumps(record, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sdk",
        type=Path,
        default=Path(
            os.environ.get("ANDROID_HOME", str(Path.home() / "Library/Android/sdk"))
        ),
    )
    parser.add_argument("--serial")
    parser.add_argument(
        "--emulator",
        action="store_true",
        help="Choose a running ARM64 emulator or start an installed ARM64 AVD",
    )
    parser.add_argument("--api", type=int, default=34)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument(
        "--reports",
        type=Path,
        default=Path.home() / ".codex/codex-android-release/app-e2e",
    )
    args = parser.parse_args()
    if args.timeout <= 0 or args.api < 26:
        parser.error("--timeout must be positive and --api must be at least 26")
    execute(args)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        raise SystemExit(f"FAIL: {error}") from error
