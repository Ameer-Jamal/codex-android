# Android maintenance

## Assessment before implementation

The input was an unzipped source archive without `.git`, commit history, or remotes.
All 8,926 source paths were inventoried and compared byte-for-byte with the
matching OpenAI `rust-v0.160.0` archive: 353 modified paths, 340 fork-only paths,
and one missing upstream path. The exact original path classification is retained
in `source-audit.json`; it records historical names, not active modules.

The upstream architecture includes the Rust CLI, core, TUI, app-server, state,
execution and sandboxing crates, MCP, authentication, PTY utilities, SDKs, Bazel,
and maintenance tooling. Standard goals and remote-control protocols are upstream
features, not evidence of VL ownership. They remain compatible with the baseline.
Normal upstream image support is preserved.

Android infrastructure includes the NDK ARM64 target, bundled C++ runtime,
checksum-pinned V8 archives and sandbox verification, short private socket paths,
Termux browser launching and clipboard handling, local MCP environment forwarding,
unsupported-lock handling, process start ticks, and approval-aware execution on
platforms without a desktop sandbox backend. Several of these adaptations were
already byte-identical to upstream, including PTY and TLS implementation files.

Removed fork infrastructure includes Vivling UI/runtime/assets, `vivling-core`,
`vivling-memory-agent`, `vendor/msa-core` and its index/embedding dependencies,
`fork-gate`, `/vivling`, `/vl`, `/loop`, `manage_loops`, VL SQLite migrations,
fleet identity channels and protocol extensions, VL release gates, macOS install
builds, multi-platform VL npm bootstrap logic, and VL release documentation.
Unrelated fork changes were restored directly from the same upstream release.
The missing upstream login identity module was restored. The unzipped input marked
most source files executable; executable bits were normalized to the matching
upstream archive so a later Git import does not create thousands of mode changes.

Risky mixed areas were the state runtime (VL migrations plus Android WAL fallback),
TUI orchestration (companions plus normal execution), app-server identity (fleet
experiments plus Android paths), and release launchers (remote daemon bootstrap
plus Termux runtime selection). No Android build or execution dependency on the
removed companion/index crates was found. Mechanical deletion/restoration is
necessarily larger than the usual change-size guidance; it is split conceptually
into upstream restoration and the remaining Android compatibility layer.

## Remaining delta

The existing 8 KiB model-message limits are retained independently of VL. Remote
and cached catalogs reject oversized entries; persistent instruction rendering
and Guardian policy consumption validate again. Upstream response-body-limit
tests remain complete (the fork had replaced one with an empty test). These
protections should be proposed upstream separately from Android compatibility.

- `android/build.sh`, `package.py`: one host-aware NDK build path and one local npm
  artifact, without registry publication or remote installers.
- `codex-cli/`: Android-only launcher/package metadata and Termux shebang repair.
- `codex-rs/.cargo/config.toml`, `core/Cargo.toml`: target-scoped Android linker
  flags and vendored OpenSSL. Compiler environment variables live in the build
  script rather than affecting every developer build.
- `scripts/fetch_rusty_v8_android.py`, `check_v8_sandbox.py`, bindgen patcher,
  `third_party/v8/android-artifacts.toml`: existing Android V8 supply chain.
  Historical upstream-fork URLs are retained only where they identify the pinned
  binary source. Changing their branding would break artifact resolution.
- `core/src/tools/{sandboxing,orchestrator}.rs`: retained approval-aware Android
  compatibility, with its existing regression coverage and deny-read guard.
- `arg0`, `message-history`, core installation ID, `rollout`, `execpolicy`, and
  app-server transport: retained unsupported advisory-lock handling.
- `state/src/sqlite.rs`: Android WAL fallback isolated in the common SQLite pool
  opener, with full synchronization for rollback journals; normal migrations and schema stay upstream. This also covers logs,
  memories, history, and queue pools rather than duplicating their migration logic.
- `app-server-daemon`: Android runs the current installed executable, skips desktop
  installation/update staging, and reads `/proc/<pid>/stat` through `pid_android.rs`.
- `uds`: standard desktop directory names; a shorter fixed Android directory
  preserves ownership/mode checks and full-length hashed socket names.
- `rmcp-client`: only local Termux children inherit the existing compatibility
  environment allowlist; remote executors keep their own environment policy.
- `login`: `termux-open-url` on Android. TUI upstream update checks stop on Android.

Copyright and third-party notices remain. Crate names, CLI APIs, protocol shapes,
and upstream schemas retain upstream identity. Dependencies return to upstream
pins; libc remains required by the retained lock checks. No new Rust dependency
was introduced. The public npm package is `codex-android`, maintained with the public
`Ameer-Jamal/codex-android` repository. The workspace source package contains no
compiled runtime; publish only the complete tarball produced by the packager. Upstream publication and owner-specific issue automation
workflows were removed; reusable upstream build/test workflows remain.

## Synchronizing upstream

Record and verify the upstream release/commit in `upstream.json`. On the next
update, compare against that exact release first, then port the small retained
Android delta. Do not reapply the old entire VL fork diff. Keep generated app-server
and config schemas upstream unless a deliberate API change is required.

Prefer upstream replacements for advisory locking, configurable daemon socket
roots, SQLite journal policy, Android process identity, and browser integration.
Once upstream ships sandbox-enabled Android V8 artifacts, replace the fork mirrors
and retire the Android-specific V8 producer. Do not remove sandbox verification
as a workaround for unavailable artifacts.

Use a new Codex home: VL SQLite history and fleet-specific rollouts are not a
supported migration input. Source cleanup does not delete any user data.

The input archive had no Git history. The repository was initialized against the
verified upstream commit in `upstream.json`, preserving the working files and
upstream ancestry. `upstream` points to OpenAI Codex; `origin` points to
`Ameer-Jamal/codex-android`. The suggested `original/codex-vl` and
`YOUR_USERNAME/codex-android` URLs were placeholders and were not used.

## Publishing

Use GitHub Actions for native builds and registry uploads so large transfers do
not consume a maintainer's home connection. The Android ARM64 workflow builds,
checks, and stores the runtime package. After that run succeeds, dispatch
`android-publish.yml` on the same main commit with its `build_run_id`. The staging
workflow verifies the build's repository, workflow, commit, and success, checks
the package metadata, README, licenses, and checksum, then stages it on npm.

Configure npm trusted publishing once for `Ameer-Jamal/codex-android`, workflow
`android-publish.yml`, with **stage-only** permission. It uses GitHub OIDC, with
no npm token stored in repository secrets. The workflow cannot directly publish.
A maintainer reviews the staged checksum and approves it using npm's website or
`npm stage approve <stage-id> --auth-type=web`. Keep account 2FA enabled.

Local builds remain available with `bash android/build.sh`; publish only the
complete generated tarball, never the source-only `codex-cli/` directory.
Use staged publishing for local uploads if necessary, as direct approval can
expire during a slow transfer. Future releases must use a new package version.

After approval, create a GitHub prerelease for that version until device acceptance
is complete. Mirror the exact public registry package and checksum to the release.
For slow upload connections, create the GitHub prerelease first, then manually
dispatch `android-release-assets.yml` with the published npm version and the
verified cloud build's SHA-256. It downloads the public registry package, verifies the
supplied checksum, and attaches that identical package and checksum to the
existing release. It never publishes to npm or receives npm credentials.
Desktop regression workflows remain available for manual upstream audits;
Android builds and the retained dependency-security check run automatically.

## Android interactive server default

Starting with `0.160.0-android.4`, the npm launcher passes upstream's
`--no-daemon` by default. A physical Termux user confirmed embedded sessions work
but reported repeat failures attaching to a shared daemon socket. The underlying
daemon/socket recovery issue is not resolved; this default avoids that dependency
for normal interactive sessions, resume and fork without changing security
approvals. Explicit `--no-daemon` is not duplicated, and arguments after `--` stay
prompt text. Native Codex code and protocols remain unchanged.

For maintainer testing of shared-server commands or explicit remote endpoints,
`CODEX_ANDROID_USE_DAEMON=1 codex ...` leaves native arguments unchanged. This is
an experimental opt-in, not a supported Android daemon workflow. Stop live daemons
before resetting their settings directories.

## Release control without AI

No AI scheduler is needed. GitHub starts Android CI on every main-branch push.
Use the Actions page or the small control script below to run release steps.
The script needs Bash, GitHub CLI (`gh auth login`), Node/npm and repository access.
Build, staging and mirror commands transfer only metadata locally. The optional
`test` command downloads the candidate for local emulator acceptance.

```sh
bash android/release.sh status
bash android/release.sh build
bash android/release.sh watch BUILD_RUN_ID
bash android/release.sh stage BUILD_RUN_ID
bash android/release.sh watch STAGING_RUN_ID
bash android/release.sh inspect STAGING_RUN_ID
```

Each dispatch prints its GitHub run URL. Copy the numeric run ID from that URL.
Stage only once, after the build succeeds. The staging workflow requires the
build to match main exactly; pushing another commit before staging requires a
new successful build. `inspect` shows the cloud package checksum and npm stage
ID. Never stage an already staged version again.

Review the stage, then log in if needed and approve through npm's browser:

```sh
bash android/release.sh login
bash android/release.sh approve STAGE_ID
```

The `approve` command displays npm's stage metadata before requesting browser
approval. Keep 2FA enabled. This human account approval cannot be replaced by a
scheduled job with the current stage-only trust configuration. Don't paste tokens
or recovery codes into scripts or chat.

After publication, use the version, SHA-256 and source commit from the successful
cloud build, along with a saved user-facing release notes file:

```sh
bash android/release.sh mirror VERSION SHA256 BUILT_COMMIT NOTES_FILE
bash android/release.sh watch MIRROR_RUN_ID
bash android/release.sh status
```

`mirror` creates a GitHub prerelease if it does not already exist and dispatches
the cloud asset workflow. That workflow downloads from the public npm registry,
verifies the supplied checksum and attaches the identical archive and sidecar.
It retries temporary download failures for up to six minutes and queues duplicate
runs instead of running simultaneous uploads. A checksum mismatch fails without
uploading. A successful mirror establishes that the normal registry download
works. Check the green run and release assets before announcing availability.

`watch` uses GitHub CLI's own polling and exits nonzero on a failed run. You can
close it and check `status` later, or simply enable GitHub workflow notifications.
No recurring AI follow-up is required. Never automate passkey prompts while away.

## Phone release checks

Copy `android/phone-test.sh` to the phone and run it in Termux after installing
the release:

```sh
bash phone-test.sh 0.160.0-android.4
```

The optional version argument checks the npm package revision; native Codex
reports its upstream version separately. The script checks ARM64 Android/Node,
required tools, global package identity, PATH resolution, native startup and CLI
help parsing, automatic private home creation, and basic Termux workspace tools.
It uses a temporary Codex home and removes only its own temporary workspace.
It makes no model requests, reads no existing login files, and never installs or
uninstalls anything. It deliberately stays outside the npm package for now.

Exit status 0 means automatic checks passed; 1 means a check failed. This is not
full device acceptance. Complete the printed interactive checklist for actual
agent shell execution, edits, approvals, login, terminal handling, resume and
Android lifecycle behavior. Check `type codex` in the calling terminal separately
because a child Bash process cannot inspect its parent's aliases. Test both a
clean Termux device/profile (dependency setup) and an existing installation
(upgrade/reinstall preservation). Never delete an active Codex home to test reset.

Upstream updates are manual: the `upstream` Git remote and `upstream.json` record
the source baseline, but do not synchronize it automatically. Dependabot updates
individual dependencies, not the Codex source baseline. Review and port a chosen
upstream release, update its provenance, run Android validation, and publish a new
Android package revision before users receive that update.

## Unattended Android emulator tests

The default is Android 17 / API 37 with the standard ARM64 Google Play image. Android 17's decimal API metadata needs SDK command-line tools **23+**;
older tools can silently create an unusable `android-0` device. Update the tools
and ADB, then install the image using Android Studio's SDK Manager or:

```sh
~/Library/Android/sdk/cmdline-tools/latest/bin/sdkmanager 'cmdline-tools;latest' platform-tools
~/Library/Android/sdk/cmdline-tools/latest/bin/android sdk install 'system-images/android-37.0/google_apis_playstore/arm64-v8a'
```

The separate 16 KB Android 17 image currently fails before Codex installation:
the pinned official Termux APK’s bootstrap second stage exits with code 139.
The default uses the standard image; 16 KB acceptance remains unresolved.

From the repository root, run:

```sh
python3 android/emulator-test.py
```

Without a version argument, the runner resolves npm’s current `latest` once and
pins that exact version for the whole test. With `--package`, it reads the version
from the candidate itself. An explicit version remains available when reproducing
an older release or checking an expected candidate version.

The runner creates/starts the dedicated `Codex_Android_Test_API37` (or API34 with `--api 34`) AVD if needed,
uses 4 GB RAM, resets Termux for a clean installation, downloads a pinned official
ARM64 Termux v0.118.3 APK when absent, verifies its checksum, and waits for bootstrap and a terminal acknowledgement
automatically. Test files use the disposable app’s private storage.
It then installs Node.js/npm, tests the exact release, and writes a pass/fail report
under `~/.codex/codex-android-release/emulator/reports/`. No manual prompt, account
login or live model request is required. npm 12.2.0 is the default; use
`--npm-version 11.20.0` to test that version too.

To test a built candidate **before npm publication**, supply its tarball:

```sh
python3 android/emulator-test.py --package /absolute/path/codex-android-candidate.tgz
```

Use the complete cloud-built artifact, not the source-only `codex-cli/` directory.
The runner verifies the candidate name/version, serves its exact bytes through a
temporary loopback npm registry, and connects the emulator through ADB. This uses
the normal npm registry install and script-permission path without publishing
anything. The registry and connection are removed afterward. Separate install
caches prevent previous test results from hiding installation problems.
Local testing downloads are authorized separately from the release pipeline's
requirement to keep builds and publication transfers on GitHub.

Only the dedicated AVD matching the selected API is accepted. Physical phones and other AVD names are
rejected before installing/resetting packages. Do not store personal work or login
data in the test AVD: **default runs uninstall Termux and erase its app data**.
`--reuse` keeps the test Termux installation for faster runs; it cannot certify
clean dependency setup. The suite checks first launch, PATH/tools, native CLI and
configuration loading, and uninstall/reinstall preservation with a non-secret
sentinel. A deterministic local Responses fixture also exercises native shell execution,
file patching, tool-result round trips, persisted session resume, a transient
response failure without repeating the shell mutation, and the native JavaScript
helper with code mode explicitly enabled for its fixture. Its disposable
project explicitly uses full access; it does not certify sandbox enforcement or
interactive approval prompts. Tests run through the real Termux terminal, not as ADB's shell user.

The SDK path can be overridden with `--sdk`; both `emulator` and this Mac's
`emulator-2` directory are supported. Missing SDK tools/system images produce a
clear setup error instead of silently downloading a new SDK. The runner is for
macOS/Unix with Python 3.11+, Android SDK and an ARM64 emulator-capable host.
A supplied `--termux-apk` must be an official debug APK verified by the caller;
the default download is checksum-pinned automatically.

The runner prevents concurrent runs sharing the same emulator serial, saves partial
reports on failure, and stops Termux on completion/timeout. An emulator started by
the runner is shut down afterward unless `--keep-emulator` is passed; an already
running test emulator stays open. Exit 0 means all automatic checks passed; nonzero
means setup or tests failed. Authenticated agent execution, interactive terminal,
upgrade migration, Android/OEM lifecycle and physical-phone acceptance remain
separate checks.

The command can also be a CI job: nonzero exit status fails the job, and the
reports directory can be uploaded as an artifact. For pre-publication checks,
pass the complete artifact downloaded from the exact build being released.
This Mac can run it as a self-hosted GitHub Actions runner without an additional
hosting service. Runner registration is separate setup; it is not installed by
this script. GitHub-hosted ARM64 macOS runners do not support nested virtualization,
so they cannot directly replace this Mac’s accelerated Android emulator.

## Connect local emulator acceptance to GitHub

After the Android ARM64 build succeeds, run:

```sh
bash android/release.sh test
```

Without a run ID, this selects a successful build of **current main**, and fails
clearly if that commit has not finished building. An explicit numeric run ID is
also accepted to reproduce an older build. Package versions always come from
the candidate, so no manual version substitution is needed.

This command uses your existing `gh` login, verifies the run is a successful
Android workflow on this repository's main branch, downloads its candidate and
checks the SHA-256 sidecar. It runs the clean Android 17 suite and posts
`android/emulator-api37` as pending, success, failure or error on the **built
commit**, visible alongside its pipeline checks. The exact source, checksum and
result are saved with the full local reports under
`~/.codex/codex-android-release/emulator/pipeline-RUN_ID-api37/`. The status links
to the source build; full emulator logs remain on the Mac.

Use `--api 34` for the older compatibility check; use `--no-status` for read-only
GitHub access. A successful emulator status is currently a **manual release
acceptance check**, not enforced by the npm staging workflow. Check both the
cloud build and emulator status before staging a new release. A failed test does
not publish anything or alter npm tags.

This pull-based connection needs no continuously listening self-hosted runner,
paid service or AI schedule. Run it manually before releases. Scheduling the same
command with a specific new build ID is possible through macOS launchd; avoid
repeatedly downloading/testing an unchanged build. Your Mac must be awake, have
the SDK image installed and have an authenticated `gh` session.
