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

After completing validation, build with `bash android/build.sh`. Inspect the
package contents with `npm publish --dry-run --ignore-scripts dist/android/*.tgz`.
Publish the complete tarball, never the source-only `codex-cli/` directory:

```sh
npm publish dist/android/codex-android-0.160.0-android.1.tgz --access public --tag latest
```

Use browser npm login and keep 2FA enabled. Do not commit credentials. Upload the
same package and checksum to a GitHub release tagged `v0.160.0-android.1`; mark the
initial GitHub release as a prerelease until device acceptance is complete.
Future releases must use a new npm version and regenerate their checksum.
For large packages on slow connections, use npm 11.15 or newer's
[staged publishing](https://docs.npmjs.com/staged-publishing/) so approval happens
after the upload. Direct publishing approval can expire while uploading:

```sh
npm stage publish dist/android/codex-android-0.160.0-android.1.tgz --access public --tag latest
npm stage view <stage-id>
npm stage approve <stage-id> --auth-type=web
```

Verify the staged version, tag, and checksum before approval, then download the
public registry tarball and compare its SHA-256 with the release sidecar.
For slow upload connections, create the GitHub prerelease first, then manually
dispatch `android-release-assets.yml` with the published npm version and the
local tarball's SHA-256. It downloads the public registry package, verifies the
supplied checksum, and attaches that identical package and checksum to the
existing release. It never publishes to npm or receives npm credentials.
Desktop regression workflows remain available for manual upstream audits;
Android builds and the retained dependency-security check run automatically.
