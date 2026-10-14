# On-phone app build E2E

From the repository root, run:

```sh
python3 android/app-build-e2e.py
```

For a virtual device, run:

```sh
python3 android/app-build-e2e.py --emulator
```

This automatically selects a running ARM64 emulator even when your phone is
connected. If none is running, it starts an installed ARM64 AVD, preferring the
newest dedicated Codex test device. No manual serial selection is needed; `--serial`
remains available as an override. If Termux is missing, the script installs the
checksum-pinned official test APK, waits for bootstrap and grants its test storage
permissions in the emulator. Existing Termux data is preserved. Compilation and execution
happen inside the virtual Android device, with the same counter/checksum checks
and no model requests. Emulator success is recorded separately from phone success.

Connect one authorized ARM64 phone through USB, unlock it, and leave it available
while the test runs. Install Termux, complete its initial bootstrap, and grant its
shared-storage access (`termux-setup-storage`) beforehand. The host needs Python 3
and an Android SDK with platform-tools, platform 34 and build-tools. Android Studio
can install those SDK components. Use `--sdk PATH`, `--api NUMBER` or `--serial ID`
if necessary; `--help` lists all options.

The test opens a separate Termux session, creates an isolated project, and copies
this Java fixture and two SDK jars to the phone. It installs missing Termux build
packages, compiles Java and DEX, packages and signs the APK **on the phone**, then
installs it through authorized USB ADB. It launches the app, taps the counter,
checks the result and captures a screenshot and app-specific logs. No Codex
command, login, model request or API token is used.

The test leaves the demo app, source, build tools and disposable development key
available. Every run uses a unique package ID and directory, and refuses to
replace an existing app. The terminal session is left intact on failure. The
default build timeout is 15 minutes; package installation needs internet access
and can download substantial files on the first run.

Reports are saved under `~/.codex/codex-android-release/app-e2e/RUN_ID/`, including
`result.json`, `build.log`, the APK, its SHA-256 and `running.png`. The report records
the exact phone project and package ID. Rebuild inside Termux with:

```sh
cd ~/codex-app-e2e-RUN_ID
bash rebuild.sh
```

To remove a particular demo, use its recorded package ID:

```sh
adb uninstall dev.codexandroid.e2e.demoRUN_ID
```

Delete that run's project and `Download/codex-app-e2e-RUN_ID` directory separately
if no longer needed. The script does not remove existing projects or Codex data.

This verifies the on-phone toolchain and app execution. USB ADB performs installation;
it does **not** verify Termux's APK installer handoff, autonomous AI development,
or the Codex npm package's installation flow. Those are separate acceptance tests.

These optional development dependencies stay outside `codex-android`'s npm package:
most users do not need a Java toolchain or SDK jars. The script provisions them for
this experiment; ordinary Codex installation does not provision an Android SDK.
The copied SDK jars come from your existing SDK installation and are not distributed
inside the npm package.
