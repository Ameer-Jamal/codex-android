# Validation record

Validation host: ARM64 macOS with the standalone Command Line Tools selected by
`DEVELOPER_DIR`. Rust 1.95.0, the repository's pinned toolchain, was used. The input
was an archive without Git metadata. The publication preparation attaches the
verified OpenAI upstream history and targets `Ameer-Jamal/codex-android` and the
public npm package `codex-android`. Publication status is shown by the linked
GitHub release and npm registry, rather than inferred from local build files.

The source and GitHub prerelease are public. On October 8, 2026, npm published
`codex-android@0.160.0-android.1` with the `latest` tag. The downloaded public
registry tarball matches the GitHub release tarball byte for byte (SHA-256 below);
its executable permissions, icon, and NDK notices were also verified.
Initial direct publishing attempts failed before account 2FA was enabled and
then because approval expired during the slow upload. Official staged publishing
completed the upload before browser approval, without weakening account security.
A physical Termux user subsequently found the first-launch failure documented
below. Full device acceptance remains pending.

## First-run setup release revision

A physical Termux user reported that the published `android.1` launcher failed
when its default `~/.codex-android` directory did not exist. The launcher now
creates the selected Codex home before starting the native process, with private
permissions for newly created directories. Existing settings are preserved.

`0.160.0-android.3` also installs missing Git, ripgrep, browser-opening tools and
CA certificates through Termux's `pkg` during npm postinstall. Failed dependency
setup fails installation with a recovery command. Node/npm must already be
installed; project-specific tools such as Python remain optional.

Node launcher and installer tests (14) and packaging tests (4) passed locally,
including first launch, repeat launch preserving settings, unusable home paths,
missing dependencies, package-manager errors and dependency verification.
On October 8, 2026, `codex-android@0.160.0-android.3` was published as npm's
`latest` after browser approval. Public registry metadata confirms the Android
ARM64 package, command mapping, updated user-facing README and SHA-1
`85dbb420e88255c51f7eba1f74e768a5feb14d28`.

The [full Linux Android CI run](https://github.com/Ameer-Jamal/codex-android/actions/runs/37799256766)
passed security, checks and native compilation for source
`a2e6524087907b13ea608b1a30b49cc829e4b665`. The
[trusted staging workflow](https://github.com/Ameer-Jamal/codex-android/actions/runs/37806150577)
verified the package against that source and uploaded it through npm OIDC.
The cloud-built package SHA-256 is
`c83c73af5ac2d5b70f0ab815ee71e433640cf127326b31f0689f66cb6cea4899`.

The [release asset workflow](https://github.com/Ameer-Jamal/codex-android/actions/runs/37810129561)
passed: standard `npm pack --ignore-scripts` downloaded the public registry
archive on GitHub, verified its SHA-256 and mirrored it with its checksum to the
[GitHub prerelease](https://github.com/Ameer-Jamal/codex-android/releases/tag/v0.160.0-android.3).
GitHub's asset digest matches the cloud package checksum; the checksum asset's
digest also matches the expected sidecar contents. No full package was transferred
through the maintainer's computer for this release.

A physical Termux report confirmed `android.3` gets past the missing-home error
and reaches daemon startup. npm 12.2.0 blocked postinstall without an explicit
package approval, so README installation commands now include
`--allow-scripts=codex-android`. The same report showed a live physical socket
with a missing advertised path after the user deleted the home directory.
An orphaned daemon is a plausible cause, not yet confirmed; embedded startup
with `--no-daemon` is the documented recovery. Full device acceptance remains
pending.
The README-only `android.2` package was staged on GitHub but is superseded by this
fix and must not be approved. Large transfers stay on GitHub.

## Embedded-server default revision

A further physical Termux report showed plain `codex` again failing to attach to
the managed daemon, with a physical socket occupied and advertised path missing.
The user previously confirmed `codex --no-daemon` works. The exact daemon recovery
cause remains unconfirmed; the installation is not certified for shared daemons.

`0.160.0-android.4` makes the package launcher use upstream's embedded server by
default. It preserves explicit arguments, settings, approvals and sandbox policy.
The native runtime source is unchanged. A maintainer-only environment opt-in
leaves arguments unchanged for testing shared-server commands.

Node tests (24, including nested cases) and packaging tests (4) passed locally.
Coverage includes default launch, resume, fork, prompt delimiters, explicit
`--no-daemon`, login and daemon opt-in. Native host CLI help parsing confirmed
`--no-daemon` is accepted with login and exec.

On October 9, 2026, npm published `codex-android@0.160.0-android.4` as `latest`
after browser approval. Public registry metadata confirms the updated README,
Android ARM64 target, `codex` command and SHA-1
`7b78ac94924c151268a5e63608e073cbdd120539`.

The [full Linux Android build](https://github.com/Ameer-Jamal/codex-android/actions/runs/37830989571)
passed security, checks and native compilation for source
`bf395a4d934c66016a2db43da7d26b47b882d67b`. The
[trusted staging workflow](https://github.com/Ameer-Jamal/codex-android/actions/runs/37838547298)
verified the package against its source and uploaded it through npm OIDC. Its
SHA-256 is
`e449ebf668f375542ab14d1c31beb8452b32d7ba0674b4c0694b7e673a6770ec`.

The [registry mirror workflow](https://github.com/Ameer-Jamal/codex-android/actions/runs/38002404479)
passed: normal `npm pack --ignore-scripts` downloaded the public archive on
GitHub, verified its SHA-256 and attached it with its checksum to the
[prerelease](https://github.com/Ameer-Jamal/codex-android/releases/tag/v0.160.0-android.4).
The GitHub package asset digest matches the build checksum, and the checksum
asset digest matches its expected contents. The initial mirror failed during
npm's temporary cached 404; the retry passed after cache expiration.

Release management now uses `android/release.sh` and GitHub workflows instead
of AI polling. Six release-control tests and four packaging tests passed, as did
Python lint, Bash syntax, workflow YAML and embedded Bash syntax checks.
The mirror workflow has bounded download retries, serialized uploads per version
and a 20-minute job timeout. It never uploads on a checksum mismatch.

Physical-device acceptance of the default launcher remains pending. This revision
avoids the daemon; it does not repair shared-socket recovery.

## Completed checks

| Check                                                                  | Result                                    |
| ---------------------------------------------------------------------- | ----------------------------------------- |
| Node launcher and Termux postinstall tests                             | 24 passed                                 |
| Android runtime packaging unit tests                                   | 4 passed                                  |
| Upstream package tooling tests                                         | 28 passed                                 |
| App-server protocol tests                                              | 313 passed, 1 skipped                     |
| Daemon tests after parser refactor                                     | 71 passed                                 |
| SQLite/state tests after rollback synchronization change               | 208 passed                                |
| GitHub tooling tests                                                   | 74 passed                                 |
| Config schema generation                                               | Passed; matches upstream                  |
| Standard app-server schema generation                                  | Passed                                    |
| Experimental app-server schema fixture generation                      | Passed                                    |
| Workspace manifest and TUI/core boundary checks                        | Passed                                    |
| Cargo metadata                                                         | Passed                                    |
| Bazel dependency lock regeneration                                     | Passed; no upstream lockfile drift        |
| Python lint and compilation checks                                     | Passed for Android/V8 scripts             |
| Shell syntax and ShellCheck                                            | Passed                                    |
| JavaScript syntax checks                                               | Passed                                    |
| Native CLI and code-mode host builds                                   | Passed                                    |
| Native CLI version, help, exec help, clean-home login status           | Passed                                    |
| Android target checks: uds, PTY, process hardening, terminal detection | Passed                                    |
| Android V8 download and SHA-256 verification                           | Passed for archive and binding            |
| Android V8 sandbox verification                                        | Passed; sandbox-enabled wrapper returns 1 |

The native code-mode host needs the Codex-built sandbox-enabled V8 pair. A direct
Cargo build first tried the denoland default URL, which returned HTTP 404. The
successful build used upstream `scripts/codex_package/v8.py` to fetch and verify
the OpenAI artifacts. The Android build uses its separate pinned Android pair.

The packaging smoke check also exercised `npm pack` and its checksum sidecar with
fixture ELF headers. That checks package composition and required runtime files;
it is not an executable Android artifact or a device execution test.

## Affected-crate test run

The scoped run covered 16 affected packages (12,827 tests): 12,598 passed,
209 failed, 20 timed out, and 45 were skipped. After building the required native
code-mode helper, exposing it alongside the test executables, and using a
true-color terminal environment, 210 of the 229 failed/timed-out cases passed.
A serial retry passed 13 of the remaining 19. One additional reviewed release
version snapshot was updated and passed its final retry. Across those runs,
12,822 distinct tests passed; five cases remain unresolved:

- `codex-app-server-transport`: `response_body_timeout_is_transient` and
  `remote_control_waits_for_account_id_before_enrolling` miss short deadlines.
- `codex-cli`: `packaged_daemon_bootstrap_seeds_local_package` expects desktop
  `autoUpdateEnabled=false` but receives `true`.
- `codex-core`: the optional MCP startup grace case
  `zero_grace_respects_server_startup_timeout` times out waiting for initialization.
- `codex-tui`: `lost_mutation_reply_preserves_work_without_resubmitting` renders
  a reconnect timer at 1 second rather than the snapshot's 0 seconds.

These cases exercise retained upstream desktop/transport behavior. They are not
certified as upstream defects: a separate clean-upstream reproduction has not
been completed. Their assertions were not weakened. The timer snapshot was not
accepted. Reviewed snapshots update the upstream tag's stale `0.0.0` display to
its actual `0.160.0` release version, resulting layout/compatibility output, and
the normal MCP resource tools in the executor-ready tool catalog.

The full workspace suite was not run; the repository requires confirmation
before that larger run. This record does not claim a fully passing test suite.

## Final lint and Android release build

Scoped `just fix` and strict `just clippy` passed for all 16 affected packages;
Clippy reported no warnings with `-D warnings`. Repository `just fmt` and
Prettier formatting passed.

The initial emulated Linux ARM64 release build was killed while optimizing
`codex-core` under Docker's approximately 6 GiB memory limit (signal 9, without a
Rust source diagnostic). A lower-concurrency retry and a native macOS NDK build
were started. Temporary logs from those builds are no longer available, so this
record does not claim that the Linux retry completed.

A complete ARM64 release package was produced and inspected during publication
preparation. Both executables contain Android API 29 notes, use
`/system/bin/linker64`, and have `$ORIGIN` runtime paths. All three runtime files
are ARM64 ELF binaries; their dynamic dependencies are Android system libraries.
The archive checksum matches its sidecar. This is an actual runtime package,
separate from the earlier fixture-header packaging smoke check.
All load segments in the three bundled ELF files have 16 KiB alignment, with
congruent file offsets and virtual addresses. This checks their binary layout;
execution on a device with 16 KiB pages is still unverified.

Native runtime SHA-256 values before final metadata/artwork repackaging:

| File                   | SHA-256                                                            |
| ---------------------- | ------------------------------------------------------------------ |
| `codex`                | `4f8d11c94f5e0989cb629dfaa2ca45dce8b2ae7785787ebd94b31ea84c819b7f` |
| `codex-code-mode-host` | `aac028826cad981c206e04a987c5498429367a300573ed72bc23de84956ac9be` |
| `libc++_shared.so`     | `ab4e6c71b96b851de45a8a9bd86369e7dbc2130a44b3b4520564be94847910f2` |

Publication preparation passed the launcher tests (8), packaging tests (4),
Python lint, shell syntax/ShellCheck, workspace manifest checks, and TUI/core
boundary checks. The final npm publish dry run contains 16 files, including the
icon, runtime, V8 licenses, and NDK notices (146.8 MB compressed, 382.3 MB unpacked).
The release tarball SHA-256 is
`a91df614e20677ca9cc5987e5c4ec1efcee0253d15927c29a20f44ce4ec1eb4b`.
Repackaging retains the inspected native binary bytes. No physical device was available.

The build script supports Linux x86_64 and macOS NDK hosts. Linux NDK files must
be extracted on a case-sensitive filesystem. CI performs a fresh Linux build
from the published source and uploads its independently built artifact.

The initial main-branch CI run passed security and packaging checks, but its build
job was cancelled after remaining in prerequisite installation for two hours.
A subsequent [full Linux Android build](https://github.com/Ameer-Jamal/codex-android/actions/runs/37753271732)
passed security, packaging checks and native compilation for commit `7589cd068`.
Its [cloud staging workflow](https://github.com/Ameer-Jamal/codex-android/actions/runs/37761618532)
also passed. These results precede the first-run setup fix; the fixed source
requires its own successful build before publication.

## Device acceptance and limitations

No ARM64 Android device is attached. Authentication against a live account,
interactive rendering, PTY resize/Ctrl-C, shell execution, patching, persistence,
MCP, code-mode execution, and daemon restart still need device acceptance. Follow
`qa/runtime-suite/README.md`; live checks require the user's authentication.

Only standard ARM64 Termux on Android 10/API 29 or newer is supported by this build
path. Native Termux source builds, other architectures, renamed Termux packages,
APK embedding, desktop voice/WebRTC, and persistent background daemon operation
are not certified. Android may terminate long-running processes.

Use private Termux storage and a fresh Codex home. VL SQLite databases are not
migration inputs. Unsupported advisory locks cannot guarantee exclusion between
concurrent writers; the SQLite rollback fallback uses one connection and full
synchronization. Desktop update paths are disabled on Android. See
`MAINTENANCE.md` for the retained delta and upstream replacement candidates.

## Automated ARM64 emulator checks — 2026-10-10

Public `codex-android@0.160.0-android.4` passed wrapper/installation checks in a
new dedicated Android 14/API 34 ARM64 emulator running official Termux v0.118.3
and Node.js v24.18.0. The Termux ARM64 APK matched its official release checksum
`72fdb596045116bf5ba1b5bdf5b26fddb9acc0bd074ad9f2da9eb0ae85e83a4e`.
The first boot needed 4 GB emulator RAM after the default 2 GB caused Android
system-service memory pressure; this was test-environment setup, not a Codex failure.

- npm 11.20.0: clean Termux setup, missing-tool installation, package identity,
  PATH resolution, native version/help, exec/resume/fork/login argument parsing,
  private home creation, workspace tools, uninstall/reinstall preservation and
  repeated launcher startup passed.
- npm 12.2.0: explicit `--allow-scripts=codex-android` installation, all the above
  checks, and native fresh-home `login status` configuration loading passed.
  The expected unauthenticated result was `Not logged in`, exit status 1.
- Both complete suite runs returned exit status 0. Reports were saved externally
  under `~/.codex/codex-android-release/emulator/reports/`; no account login or
  model request was used. The npm 12 run reused the already installed dependencies.
- Host tests cover failure reporting, temporary-home isolation, preservation of
  existing login data, wrong-command detection, and rejection of physical phones,
  unrelated AVDs and invalid version arguments before emulator mutations.

These checks do not certify authenticated agent shell/edit operations, command
approvals, interactive terminal rendering, resume content, upgrade migration,
network recovery or Android/OEM background behavior. Physical-device acceptance
and the five retained regression failures remain unresolved. No package version,
publication state or native Rust source was changed by this testing work.

## Unattended candidate acceptance — 2026-10-10

The final one-command runner passed from a stopped dedicated emulator with a
clean Termux install and npm 12.2.0. It tested the complete cloud-built Android.4
archive before publication simulation through a temporary loopback registry;
its SHA-256 remained
`e449ebf668f375542ab14d1c31beb8452b32d7ba0674b4c0694b7e673a6770ec`.
No manual readiness prompt, account login or model request was used.

Automatic emulator startup, Termux bootstrap, missing dependencies, exact package
version/PATH, private home creation, native help/configuration checks, repeated
startup and uninstall/reinstall settings preservation all passed. The runner
saved `0.160.0-android.4-1791688022198341000.txt` externally in the emulator reports
directory with `SUITE_EXIT=0`, removed the test files/local registry connection,
and shut down the emulator it started. Twenty-two host Python tests passed,
including candidate identity and identical archive delivery checks.

This is wrapper and installation acceptance on an emulator. Authenticated agent
execution, interactive sessions, actual upgrade migration and physical Android
lifecycle acceptance remain pending; the five retained regressions are unchanged.

## Android 17 native end-to-end acceptance — 2026-10-10

The Mac-driven pipeline command passed on a clean official Termux v0.118.3
installation in the dedicated Android 17/API 37 ARM64 Google Play emulator,
using the standard **4 KB page-size image**. The SDK command-line tools were
updated to 23.0 and the emulator to 37.2.12. The final run used a headless
emulator and explicit SwiftShader rendering; earlier automatic-renderer runs
became unresponsive during bootstrap. The precise cause is not established.

The tested candidate came from successful
[Android build 38002535858](https://github.com/Ameer-Jamal/codex-android/actions/runs/38002535858),
source `ea2b81e2dd15e6218bba639fdc585d7b79f3f023`. Its version was read from the
archive as `0.160.0-android.4`, and its verified SHA-256 was
`b3c636636795d1d1ed92e59b630c00eb278deb5226aed16bd6de157c6bb174ea`.
This is a later cloud candidate, not a claim of byte identity with the previously
published npm tarball. The harness source was
`fae3320e1135a3d4a1d7879f5c24c7d3e609f531`, with no uncommitted harness changes
at invocation. GitHub recorded `android/emulator-api37=success` on the built source.

The report `0.160.0-android.4-1791692901861855000.txt` and `result.json` are saved
under `~/.codex/codex-android-release/emulator/pipeline-38002535858-api37/`.
It records `SUITE_EXIT=0`, Node 24.18.0 and npm 12.2.0. Checks covered clean
installation and automatic missing dependencies, first/private-home creation,
CLI/configuration loading, repeated startup, uninstall/reinstall preserving a
non-secret settings sentinel, native shell execution and file patching,
serialized tool results, persisted session resume, the native JavaScript helper
with code mode explicitly enabled, and retrying one injected HTTP 503 without
repeating the shell mutation. A local deterministic Responses fixture was used;
there was no account login or live model request.

Thirty-four host Python tests and 24 Node launcher/installer tests passed.
The expanded native fixture also passed against the macOS executable, and the
prior Android 14 run passed shell, patch and resume checks. Prettier, Python lint,
shell syntax checks and required `just fmt` passed.

The separate Android 17 **16 KB image did not pass**: the pinned Termux APK
showed its compatibility-mode warning, then its bootstrap second stage exited
with code 139 before Codex installation. This is an observed Termux environment
blocker, not proof that Codex works or fails on that page size. Strict 16 KB
acceptance remains unresolved. Physical-phone login, interactive approval
accept/deny, terminal controls, Android/OEM lifecycle and actual upgrade migration
remain pending. The five retained test failures listed above remain unresolved;
no assertion or snapshot was weakened to declare stability.

## First-launch setup with install scripts blocked — 2026-10-12

The launcher now repeats the idempotent Termux dependency check before starting
the native runtime. Packaging writes the Termux interpreter path into the npm
bin in advance, so blocked postinstall does not prevent the launcher from running.
Setup failures stop native startup and provide a manual `pkg install` recovery
command followed by rerunning `codex`; a reinstall is not required.

A clean Android 17/API 37 ARM64, 4 KB emulator run passed with Node 24.18.0 and
npm 12.2.0. The first npm installation explicitly used `--ignore-scripts`, then
invoked the actual `codex` command before diagnostics. First launch installed
missing Git and ripgrep and created the private settings directory. The suite
also passed explicit-script-approval reinstall, settings preservation, repeated
startup, shell execution, file patching, persisted resume, native JavaScript
helper execution and transient-response retry. No live account or model request
was used. Twenty-six Node tests and 34 Python host tests passed.

This was a local wrapper candidate assembled from the existing Android runtime
and the modified launcher/setup sources, not a new native build or npm release.
It retained version `0.160.0-android.4` solely for local testing; its SHA-256 was
`eefa6b2047aa6e50197a1bb7b0abb565dd56c2136591e58ea8a76f81b4c4fd12`.
The report `0.160.0-android.4-1791789806780350000.txt` records `SUITE_EXIT=0`
under `~/.codex/codex-android-release/emulator/first-launch-candidate/reports/`.
Published `android.4` is unchanged and still uses the documented installation
permission flag. Physical-phone acceptance, 16 KB support and the five retained
regression failures remain unresolved.

## Published first-launch setup release — 2026-10-12

`codex-android@0.160.0-android.5` is published with npm's `latest` tag. Public
registry metadata and README confirm the shorter `npm i -g codex-android`
installation and first-launch setup when npm blocks install scripts. The registry
SHA-1 is `b0881e45223d1de062847110883386bc8d631f82`.

The [full Android build](https://github.com/Ameer-Jamal/codex-android/actions/runs/38292648473)
and dependency-security checks passed for source
`6f97b314e12cb23221a76f59c16d388b3ecc8af1`. QUIC was updated to
`quinn-proto` 0.11.18 and the YAML dependency migrated to `serde_norway` 0.9.42
without relaxing advisory checks. Required Bazel lock regeneration passed.
The five affected Rust packages passed 873 tests across seven binaries, including
one automatic retry; this was not a complete workspace test run. Twenty-six
Node tests and 34 Python host tests passed before release preparation.

The exact cloud artifact passed the Android 17/API 37 ARM64, 4 KB emulator
suite with Node 24.18.0 and npm 12.2.0. Installation with scripts blocked,
first-launch dependency setup, private-home creation, settings-preserving
reinstall, native shell execution, file patching, session resume, JavaScript
helper execution and transient-response retry passed. The report records
`SUITE_EXIT=0` at
`~/.codex/codex-android-release/emulator/pipeline-38292648473-api37/0.160.0-android.5-1791833942641341000.txt`.
Tests used deterministic local fixtures without account login or live model requests.

The [staging workflow](https://github.com/Ameer-Jamal/codex-android/actions/runs/38299205789)
staged this same artifact, and maintainer browser approval published it. Its
SHA-256 is
`863336839cf54400060ebb61c1dcd6f1664fa803d30c503686d17e6a9026a3af`.
The [GitHub prerelease](https://github.com/Ameer-Jamal/codex-android/releases/tag/v0.160.0-android.5)
targets the built source. The
[cloud mirror workflow](https://github.com/Ameer-Jamal/codex-android/actions/runs/38303167889)
succeeded, and the GitHub API tarball asset digest matches the SHA-256 above.
Release uploads and registry mirroring run on GitHub;
the local artifact download was solely for the authorized emulator test.

Early access remains appropriate: physical-phone acceptance, 16 KB compatibility,
the five retained regression failures, and shared-daemon socket recovery remain
unresolved. Normal command approvals and required LICENSE/NOTICE are preserved.

## Android diagnostics release — 2026-10-14

`0.160.0-android.6` is published as npm latest. The [Android build](https://github.com/Ameer-Jamal/codex-android/actions/runs/38574278554) passed security and native compilation for `6c703c64df92d9e63fd71bb612fe1093b45e78c0`. Rustls 0.23.46 resolves four new security advisories; Bazel lock regeneration and advisory checks passed. Thirty-two Node and 34 Python tests passed. All 150 tests across HTTP client, TCP tunnel, WebSocket client and Rustls provider passed serially after the parallel run encountered local socket timeouts. No complete Rust workspace run is claimed.

The exact artifact passed Android 17/API 37 ARM64, 4 KB emulator acceptance: blocked-script install, read-only doctor before first-launch setup, JSON diagnostics, both launcher links, uninstall/reinstall preservation, native shell/patch/resume/JavaScript helper and transient-response retry. Native version probes use a disposable home and never the real settings home. Storage permission success/denial/missing utility/failure were tested with controlled fixtures; physical permission dialogs were not certified. Reports use deterministic local fixtures without live model requests.

[Direct OIDC publication](https://github.com/Ameer-Jamal/codex-android/actions/runs/38585345504) completed without maintainer npm approval, verified the public registry tarball in the cloud and attached matching [GitHub assets](https://github.com/Ameer-Jamal/codex-android/releases/tag/v0.160.0-android.6). The API asset digest matches SHA-256 `fe84c54bd339901a4682c2dd7635ae049d2bf2e569b0cfa1857710a9d830c609`. README metadata contains both companion commands. Release uploads and registry mirroring stayed on GitHub; the local download was for authorized emulator testing only.

Early access, physical-phone acceptance, 16 KB compatibility, the five retained regressions and underlying shared-daemon recovery remain unresolved. Normal approvals and LICENSE/NOTICE are preserved.

## Physical-phone observations — 2026-10-14

The maintainer supplied Termux screenshots and reported that Codex works on their
phone with `0.160.0-android.6`. The screenshots confirm a successful global npm
update despite blocked postinstall, successful shared-storage setup after the
Termux confirmation, and doctor PASS results for Android/ARM64, Node 26.3.1,
dependencies/certificates, native 0.160.0, executable PATH and 4096-byte pages.
A Codex session exit summary and resume instructions are visible.

An old shell alias initially redirected `codex` to the removed `codex-vl` command;
`unalias codex` fixed the current terminal. Persistent startup-file alias cleanup
was not independently verified. The incorrect package specification
`codex@android-latest` and `codex-android --doctor` were corrected by the user.
These are command-entry issues, not evidence of a runtime failure.

This records basic physical-device installation/startup/diagnostic/storage
observations, not complete device acceptance. Phone model, Android version,
fresh login, interactive approval accept/deny, actual resumed session, lifecycle,
16 KB compatibility and complete upgrade/data-preservation checks remain pending.

## Deterministic on-phone app build — 2026-10-14

`python3 android/app-build-e2e.py` passed on the connected Android 16 ARM64
phone using Termux's existing Java 21 toolchain. The script transferred the Java
fixture and API 34/D8 jars, then compiled Java and DEX, packaged, aligned and
signed the APK inside Termux. Authorized USB ADB installed the unique demo app;
the automated UI check verified its counter changed from 0 to 1. The app-specific
log contained no fatal exception. No Codex command or model request was made.

Run `20261014174647a5db` produced SHA-256
`8f8bd42dee55d751e45922bc7a969f5f31378d79da8f18a1d0bf89e3eb8a9fc0`, matching
the APK pulled from the phone. Source and the installed demo remain available.
The host report includes build output, the checksum, app logs and a screenshot.
Initial attempts exposed a locked screen and dropped input; the driver now
rejects a visible lock screen, paces command input and checks build startup.
All 38 Python tests, shell syntax checks and Ruff passed for the harness.

This validates the physical on-phone build toolchain and ADB installation, not
Termux's installer handoff or autonomous model behavior. Dependencies were already
present on this phone; fresh dependency provisioning remains unverified. See
[the reproducible test instructions](demos/hello-world/README.md).

The same harness subsequently passed on the Android 17/API 37 ARM64 emulator
(`20261014194020003d`), with automatic running-device selection and missing
packaging-tool installation. Updating Termux's C++ runtime resolved an `aapt2`
linker failure from the older bootstrap. Compilation/signing happened inside the
emulator; ADB installation and the 0-to-1 counter check passed with zero model
requests. Emulator startup also selected and booted the installed dedicated AVD;
existing data was preserved. Forty Python tests passed. This does not extend
physical-phone or 16 KB compatibility acceptance.

## Upstream 0.162.1 candidate — 2026-10-16

Candidate `0.162.1-android.1` is isolated on `feature/upstream-0.162.1`
([draft PR #14](https://github.com/Ameer-Jamal/codex-android/pull/14)).
It imports official `rust-v0.162.1`, commit
`092d3acd6bec3e3a14bdc7e7a2810ab628ab759d`. It has not been published.

[Android build 38765050653](https://github.com/Ameer-Jamal/codex-android/actions/runs/38765050653)
passed security, checks and cross-compilation for source
`889e0f05de2185ac8e968425a7c0eaf2501860c7`. The downloaded candidate matches
its cloud checksum:
`3b073342b1f782bce4bf7cc598d595062e2df98d747a6aa20406cd167903b8a5`.

Local wrapper/setup tests (35), Android Python tests (40), and GitHub script
Python tests (80) passed, as did shell syntax, boundary/workspace checks and
Bazel lock regeneration. Native state/protocol/transport testing ran 758 cases:
756 passed and two transport tests failed, including serial and certificate
retries. The larger native core/TUI/CLI/app-server/daemon run executed 13,288
cases: 13,075 passed, 148 failed, 65 timed out and 37 were skipped; 77 passing
cases required retries. Failures include MCP/Guardian, worktree, proxy, timing
and snapshot cases. Their causes have not all been established; they must not
be treated as harmless or as proven upstream defects.

Four retained Android apply-patch tests were adapted to the new upstream API.
Thirty-two snapshots were updated only where the version display was the sole
content difference (0.160.0 to 0.162.1); other snapshot differences were not
accepted. A focused follow-up was cancelled during recompilation to reduce host
load, so no passing rerun is claimed for these updates.

The initial exact-package Android 17 attempt stopped on an ADB report-read
timeout during Termux dependency provisioning. A clean retry without concurrent
Rust compilation passed (`SUITE_EXIT=0`), report
`0.162.1-android.1-1792159079510005000.txt`. It used the same cloud package and
checksum above. Installation with scripts blocked recovered on first launch;
uninstall/reinstall preserved test settings and repeated startup worked.
Native exec, shell, file patch, tool-result round trips, persisted session,
resume, native JavaScript helper and transient network retry checks passed.
These are deterministic fixture checks, with no live model requests. The ADB
timeout did not recur; its cause is not established.

No physical-device or 16 KB acceptance is claimed. Main and the published npm
release remain unchanged; the candidate is blocked from release pending
native failure triage.

### Native failure triage completed — 2026-10-16

Every one of the 213 failed or timed-out cases from the initial 13,288-case
runtime run subsequently passed in scoped reruns. The first lower-concurrency
retry ran 216 cases: 183 passed, 27 failed and six timed out. After fixture fixes,
a 76-case follow-up passed 70; its remaining six plugin-startup cases then all
passed after allowing remote discovery before waiting for the PID file. This
is a record of combined scoped results, not a new complete-workspace green run.

The retained Android apply-patch tests passed unchanged assertions. Thirty-six
native version-display snapshots and one daemon version-display snapshot were
updated. Reconnect, Guardian and hook screenshots reset their display clocks
before capture instead of accepting varying elapsed times or animation frames.
Cursor tests passed with the host's `NO_COLOR` override removed. Local TUI matrix
cases now have a bounded three-minute nextest budget; observed successful runs
took 84–116 seconds. CI budgets and functional assertions were retained.

Other corrections are confined to test setup: bootstrap explicitly disables its
updater, missing-host tests explicitly select a missing executable (including
when fallback is prohibited), HTTP fixtures consume requests before responding,
and startup deadlines include platform client setup. The auth notification's
immediate wakeup is checked independently with a paused clock. Rebuilding the
current `test_stdio_server` fixture is required before scoped MCP tests.

The 759-case state/protocol/transport run passed 758; its remaining body-timeout
case then passed in the four-case transport/auth follow-up. The new immediate
notification test also passed. Existing timeout/error-classification assertions
remain. Together these reruns resolve the five previously retained regressions;
no production security restriction or approval behavior was relaxed.

All 35 Node wrapper tests and 40 Android Python tests passed again. The previous
80 GitHub-script tests, workspace/TUI boundary checks and candidate Android 17
acceptance remain recorded above. No live model request or physical-phone
acceptance is claimed. Publication still requires the successful exact main
build and Android 17 acceptance of that main artifact.

### Published upstream upgrade — 2026-10-16

`codex-android@0.162.1-android.1` is published as npm latest. The
[exact main build](https://github.com/Ameer-Jamal/codex-android/actions/runs/38920797169)
passed checks, security and native compilation for `5a6496becbf3d3daffaa5e81b0f274b47e2190a0`. Its exact
package passed clean Android 17 emulator acceptance before publication; the
checksum-bound success status was posted on the built commit. The local result
is saved under `emulator/pipeline-38920797169-api37/result.json` in the
external release logs. No live model request was made.

[Direct OIDC publication](https://github.com/Ameer-Jamal/codex-android/actions/runs/38929527067)
verified the registry download in the cloud and attached matching
[GitHub release assets](https://github.com/Ameer-Jamal/codex-android/releases/tag/v0.162.1-android.1). Public version, latest tag and README
metadata were checked; GitHub's package and checksum-file asset digests match.
Package SHA-256: `6efed6c48aa00082c1b402a5b892d60904bc4cce79d7a4878d21271e93553b79`. Registry SHA-1: `56b59ac54477525a4d4adf6332b41a3ee1be423a`.

The README identifies the bundled Codex 0.162.1 engine and update command. Local
package downloads were confined to authorized emulator testing; publication and
registry mirroring remained on GitHub. Early access continues: physical-phone
acceptance of this version, 16 KB support and shared-daemon recovery are pending.
The scoped native regression evidence and test-fixture changes are recorded
above; no complete native workspace test run is claimed.

## Script-free installation candidate — 2026-10-20

`0.162.1-android.2` removes the npm postinstall hook and obsolete launcher-rewriting
code. Both Termux interpreter paths are set during packaging. Missing Termux
dependencies are still installed at first launch, with the same recovery commands.
The emulator harness uses ordinary global installation and rejects lifecycle hooks
in the installed manifest. Uninstall continues to preserve settings and sessions.

Local verification: 32 Node tests, 40 Android Python tests, shell syntax, Prettier
and required `just fmt` passed. Cloud and exact-artifact emulator acceptance are
pending before publication. Native Codex remains 0.162.1; early-access limitations
remain. The user's greeting on android.1 is a basic phone smoke test, not physical
acceptance of this new package.
