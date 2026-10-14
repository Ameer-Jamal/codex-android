"""Select or start an existing ARM64 AVD without resetting its data."""

import os
from pathlib import Path
import re
import socket
import subprocess
import time

from emulator_support import official_termux, run, wait_for_termux


def prepare_termux(adb, serial, cache):
    """Provision the test emulator only; preserve existing Termux data."""
    packages = run(adb, serial, "shell", "pm", "list", "packages", "com.termux").stdout
    if "package:com.termux\n" not in packages:
        cache.mkdir(parents=True, exist_ok=True)
        run(adb, serial, "install", str(official_termux(cache)), timeout=240)
    for permission in ["READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE"]:
        run(
            adb,
            serial,
            "shell",
            "pm",
            "grant",
            "com.termux",
            f"android.permission.{permission}",
            check=False,
        )
    run(
        adb,
        serial,
        "shell",
        "am",
        "start",
        "-W",
        "-n",
        "com.termux/.app.TermuxActivity",
    )
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
    if ready.returncode != 0:
        wait_for_termux(adb, serial, "/data/local/tmp", 37)


def choose_avd(names, root):
    candidates = []
    for name in names:
        pointer = root / f"{name}.ini"
        values = {}
        if pointer.is_file():
            values = dict(
                line.split("=", 1)
                for line in pointer.read_text().splitlines()
                if "=" in line
            )
        config = Path(values.get("path", str(root / f"{name}.avd"))) / "config.ini"
        if not config.is_file():
            continue
        text = config.read_text()
        if "abi.type=arm64-v8a" not in text or "16KB" in name.upper():
            continue
        api = re.search(r"android-(\d+)", text)
        candidates.append(
            (name.startswith("Codex_Android_Test_"), int(api[1]) if api else 0, name)
        )
    if not candidates:
        raise ValueError(
            "No ARM64 AVD is installed; create one in Android Studio Device Manager"
        )
    return max(candidates)[2]


def ensure_available(sdk, adb, reports):
    def command(*args):
        return subprocess.run(
            [str(adb), *args], capture_output=True, text=True, timeout=20, check=False
        )

    listing = command("devices").stdout
    for line in sorted(listing.splitlines()):
        parts = line.split()
        if (
            len(parts) >= 2
            and parts[0].startswith("emulator-")
            and parts[1] == "device"
        ):
            serial = parts[0]
            if (
                command(
                    "-s", serial, "shell", "getprop", "ro.product.cpu.abi"
                ).stdout.strip()
                == "arm64-v8a"
            ):
                print(f"Using running ARM64 emulator {serial}.", flush=True)
                return serial
    emulator = next(
        (
            sdk / folder / "emulator"
            for folder in ["emulator", "emulator-2"]
            if (sdk / folder / "emulator").is_file()
        ),
        None,
    )
    if emulator is None:
        raise ValueError("Install Android Emulator through Android Studio SDK Manager")
    names = subprocess.check_output(
        [str(emulator), "-list-avds"], text=True, timeout=20
    ).splitlines()
    root = Path(
        os.environ.get(
            "ANDROID_AVD_HOME",
            str(
                Path(os.environ.get("ANDROID_USER_HOME", str(Path.home() / ".android")))
                / "avd"
            ),
        )
    )
    name = choose_avd(names, root)
    port = None
    for candidate in range(5554, 5682, 2):
        if f"emulator-{candidate}" in listing:
            continue
        try:
            with socket.socket() as console, socket.socket() as bridge:
                console.bind(("127.0.0.1", candidate))
                bridge.bind(("127.0.0.1", candidate + 1))
            port = candidate
            break
        except OSError:
            continue
    if port is None:
        raise ValueError("No emulator port is available")
    reports.mkdir(parents=True, exist_ok=True)
    logs = reports / f"emulator-start-{time.time_ns()}.log"
    print(f"Starting ARM64 emulator {name}; existing data is preserved.", flush=True)
    with logs.open("w") as output:
        process = subprocess.Popen(
            [
                str(emulator),
                "-avd",
                name,
                "-port",
                str(port),
                "-no-snapshot-save",
                "-no-audio",
            ],
            stdout=output,
            stderr=subprocess.STDOUT,
        )
    serial = f"emulator-{port}"
    deadline = time.monotonic() + 600
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise ValueError(f"Emulator stopped; see {logs}")
            if (
                command(
                    "-s", serial, "shell", "getprop", "sys.boot_completed"
                ).stdout.strip()
                == "1"
            ):
                return serial
            time.sleep(3)
        raise TimeoutError(f"Emulator boot timed out; see {logs}")
    except BaseException:
        if process.poll() is None:
            process.terminate()
        raise
