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
It transfers only commands, metadata and logs locally; packages stay on runners.

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
