"""macOS/Unix SDK setup for the dedicated disposable Termux test emulator."""

import hashlib
import subprocess
import time
import urllib.request

IMAGES = {
    34: "system-images;android-34;google_apis_playstore;arm64-v8a",
    37: "system-images;android-37.0;google_apis_playstore;arm64-v8a",
}
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


def require_test_avd(adb, serial, api=37):
    avd_name = f"Codex_Android_Test_API{api}"
    name = run(adb, serial, "emu", "avd", "name").stdout.splitlines()
    if not name or name[0].strip() != avd_name:
        raise ValueError(f"Refusing to modify any AVD except {avd_name}")


def ensure_emulator(sdk, adb, serial, logs, api=37):
    avd_name = f"Codex_Android_Test_API{api}"
    package = IMAGES[api]
    manager = sdk / "cmdline-tools/latest/bin/avdmanager"
    if api == 37:
        properties = (sdk / "cmdline-tools/latest/source.properties").read_text()
        revision = next(
            (
                line.split("=", 1)[1].strip()
                for line in properties.splitlines()
                if line.startswith("Pkg.Revision=")
            ),
            "0",
        )
        if int(revision.split(".")[0]) < 23:
            raise ValueError(
                "Android 17 requires SDK command-line tools 23+; update them in SDK Manager before creating its AVD"
            )
    if run(adb, serial, "get-state", check=False, timeout=15).returncode == 0:
        require_test_avd(adb, serial, api)
        wait_for_boot(adb, serial, None, logs, api)
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
    if avd_name not in avds:
        image = sdk / package.replace(";", "/") / "system.img"
        if not image.is_file():
            raise ValueError(
                f"Install {package} through Android Studio SDK Manager or sdkmanager"
            )
        subprocess.run(
            [
                str(manager),
                "create",
                "avd",
                "--name",
                avd_name,
                "--package",
                package,
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
                avd_name,
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
    try:
        wait_for_boot(adb, serial, process, logs, api)
    except BaseException:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=30)
        raise
    return process


def wait_for_boot(adb, serial, process, logs, api):
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        if process and process.poll() is not None:
            raise ValueError(f"Emulator stopped unexpectedly; see {logs}")
        if run(adb, serial, "get-state", check=False, timeout=15).returncode == 0:
            require_test_avd(adb, serial, api)
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


def wait_for_termux(adb, serial, remote, api=37):
    print("Waiting for Termux bootstrap and terminal readiness...", flush=True)
    deadline = time.monotonic() + 600
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
            windows = run(
                adb,
                serial,
                "shell",
                "dumpsys",
                "window",
                check=False,
                timeout=30,
            ).stdout
            if any(
                "mCurrentFocus=" in line
                and "com.termux" in line
                and "TermuxActivity" in line
                for line in windows.splitlines()
            ):
                return
        errors = run(
            adb,
            serial,
            "logcat",
            "-d",
            "-t",
            "5000",
            check=False,
            timeout=30,
        ).stdout
        errors = "\n".join(
            line for line in errors.splitlines() if "Termux:TermuxInstaller" in line
        )
        if "Bootstrap Error:" in errors:
            raise ValueError(
                "Termux bootstrap failed before Codex installation: " + errors[-2000:]
            )
        time.sleep(3)
    raise ValueError(
        "Termux bootstrap/terminal readiness timed out; see the emulator window"
    )


def dispatch(adb, serial, command):
    # Callers only pass fixed paths and validated version arguments, no shell metacharacters.
    run(adb, serial, "shell", "input", "text", command.replace(" ", "%s"))
    run(adb, serial, "shell", "input", "keyevent", "66")
