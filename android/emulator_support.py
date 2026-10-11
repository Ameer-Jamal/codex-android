"""macOS/Unix SDK setup for the dedicated disposable Termux test emulator."""

import hashlib
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET

AVD_NAME = "Codex_Android_Test_API34"
TERMUX_SHA256 = "72fdb596045116bf5ba1b5bdf5b26fddb9acc0bd074ad9f2da9eb0ae85e83a4e"
TERMUX_URL = "https://github.com/termux/termux-app/releases/download/v0.118.3/termux-app_v0.118.3%2Bgithub-debug_arm64-v8a.apk"


def run(adb, serial, *args, timeout=60, check=True):
    return subprocess.run(
        [str(adb), "-s", serial, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )


def require_test_avd(adb, serial):
    name = run(adb, serial, "emu", "avd", "name").stdout.splitlines()
    if not name or name[0].strip() != AVD_NAME:
        raise ValueError(f"Refusing to modify any AVD except {AVD_NAME}")


def ensure_emulator(sdk, adb, serial, logs):
    if run(adb, serial, "get-state", check=False, timeout=15).returncode == 0:
        require_test_avd(adb, serial)
        wait_for_boot(adb, serial, None, logs)
        return None
    emulator = next(
        (
            sdk / directory / "emulator"
            for directory in ["emulator", "emulator-2"]
            if (sdk / directory / "emulator").is_file()
        ),
        None,
    )
    if emulator is None:
        raise ValueError(
            "Install Android Emulator through Android Studio's SDK Manager"
        )
    avds = subprocess.run(
        [str(emulator), "-list-avds"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    if AVD_NAME not in avds:
        image = (
            sdk / "system-images/android-34/google_apis_playstore/arm64-v8a/system.img"
        )
        if not image.is_file():
            raise ValueError(
                "Install the Android 14 Google Play ARM64 system image in Android Studio's SDK Manager"
            )
        manager = sdk / "cmdline-tools/latest/bin/avdmanager"
        subprocess.run(
            [
                str(manager),
                "create",
                "avd",
                "--name",
                AVD_NAME,
                "--package",
                "system-images;android-34;google_apis_playstore;arm64-v8a",
                "--device",
                "pixel",
            ],
            input="no\n",
            text=True,
            capture_output=True,
            check=True,
            timeout=120,
        )
    print("Starting dedicated ARM64 emulator...", flush=True)
    with logs.open("w") as output:
        process = subprocess.Popen(
            [
                str(emulator),
                "-avd",
                AVD_NAME,
                "-port",
                serial.split("-")[1],
                "-memory",
                "4096",
                "-no-snapshot",
                "-no-audio",
                "-no-boot-anim",
            ],
            stdout=output,
            stderr=subprocess.STDOUT,
        )
    wait_for_boot(adb, serial, process, logs)
    return process


def wait_for_boot(adb, serial, process, logs):
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        if process and process.poll() is not None:
            raise ValueError(f"Emulator stopped unexpectedly; see {logs}")
        if run(adb, serial, "get-state", check=False, timeout=15).returncode == 0:
            require_test_avd(adb, serial)
            if (
                run(
                    adb, serial, "shell", "getprop", "sys.boot_completed", check=False
                ).stdout.strip()
                == "1"
            ):
                return
        time.sleep(3)
    # Only this newly launched process is terminated; unrelated devices are untouched.
    if process:
        process.terminate()
    raise ValueError(f"Emulator boot timed out; see {logs}")


def official_termux(cache):
    apk = cache / "termux-arm64.apk"
    if not apk.exists():
        print("Downloading pinned official ARM64 Termux APK...", flush=True)
        partial = apk.with_suffix(".partial")
        with (
            urllib.request.urlopen(TERMUX_URL, timeout=60) as response,
            partial.open("wb") as output,
        ):
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        partial.replace(apk)
    with apk.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != TERMUX_SHA256:
        raise ValueError(f"Termux APK checksum mismatch: {apk}; remove it and retry")
    return apk


def wait_for_termux(adb, serial, remote):
    print("Waiting for Termux bootstrap and terminal readiness...", flush=True)
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        ready = run(
            adb,
            serial,
            "shell",
            "run-as",
            "com.termux",
            "test",
            "-x",
            "files/usr/bin/bash",
            check=False,
        )
        if ready.returncode == 0:
            dump = run(
                adb,
                serial,
                "shell",
                "uiautomator",
                "dump",
                f"{remote}/window.xml",
                check=False,
                timeout=30,
            )
            if dump.returncode == 0:
                xml = run(adb, serial, "shell", "cat", f"{remote}/window.xml").stdout
                try:
                    nodes = ET.fromstring(xml).iter("node")
                    if any(
                        node.get("resource-id") == "com.termux:id/terminal_view"
                        and node.get("focused") == "true"
                        for node in nodes
                    ):
                        return
                except ET.ParseError:
                    pass
        time.sleep(3)
    raise ValueError(
        "Termux bootstrap/terminal readiness timed out; see the emulator window"
    )


def dispatch(adb, serial, command):
    # Callers only pass fixed paths and validated version arguments, no shell metacharacters.
    run(adb, serial, "shell", "input", "text", command.replace(" ", "%s"))
    run(adb, serial, "shell", "input", "keyevent", "66")
