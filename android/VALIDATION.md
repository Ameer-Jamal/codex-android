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

Acceptance of the fixed package on a physical device remains pending.
The README-only `android.2` package was staged on GitHub but is superseded by this
fix and must not be approved. Large transfers stay on GitHub.

## Completed checks

| Check                                                                  | Result                                    |
| ---------------------------------------------------------------------- | ----------------------------------------- |
| Node launcher and Termux postinstall tests                             | 14 passed                                 |
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
