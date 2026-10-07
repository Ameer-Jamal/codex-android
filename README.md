<p align="center">
  <img src="https://raw.githubusercontent.com/Ameer-Jamal/codex-android/main/assets/icon.png" width="112" alt="Codex for Android icon" />
</p>

# Codex for Android

OpenAI Codex for ARM64 Android phones and tablets running Termux. This community
project keeps the upstream Rust CLI, TUI, app-server, protocols, and SDKs, with a
small Android compatibility layer. It is not an Android APK or an official
OpenAI distribution.

**Early access:** ARM64 release binaries are available. Real-device acceptance is
still pending; see the [validation record](android/VALIDATION.md).

The source baseline is [OpenAI Codex `rust-v0.160.0`](https://github.com/openai/codex/releases/tag/rust-v0.160.0).
Vivling, VL loop scheduling, fleet identity experiments, and VL branding have
been removed. Standard upstream tools, image inputs, goals, and experimental
protocols remain upstream-compatible; their presence is not Android certification.

## Supported environment

- Android ARM64 (`aarch64-linux-android`), Android 10/API 29 or newer.
- Standard Termux installation using the `com.termux` application directory.
- 32-bit ARM, x86 Android, renamed Termux packages, proot distributions, and
  native APK embedding are not supported by this build path.

Use the [Termux project's installation instructions](https://github.com/termux/termux-app#installation).
Install Termux and any Termux plugins from the same source, as their signatures
must match. In Termux:

```sh
pkg update
pkg upgrade
pkg install nodejs-lts git ripgrep python termux-tools ca-certificates
node --version  # Node 22 or newer
uname -m       # aarch64
```

Keep projects and runtime state in Termux's private home. Shared Android storage
can reject executable permissions, Unix sockets, locks, and SQLite journal files.

## Installation

Install the public npm package in Termux:

```sh
npm install -g codex-android
codex --version
```

The package includes the Android ARM64 runtime, its code-mode helper, and the
required C++ shared library. Installation does not compile Rust or fetch a separate
runtime. npm's postinstall repairs the launcher shebang for Termux.
If npm blocks lifecycle scripts, explicitly permit this package's script using
your npm version's script policy.

To update:

```sh
npm install -g codex-android@latest
```

For a manual or offline installation, download the `.tgz` and matching `.sha256`
from [GitHub releases](https://github.com/Ameer-Jamal/codex-android/releases), transfer
both to Termux's private home, and run:

```sh
sha256sum -c codex-android-0.160.0-android.1.tgz.sha256
npm install -g ./codex-android-0.160.0-android.1.tgz --foreground-scripts
```

The package is named `codex-android`; it installs the normal `codex` command.
It can replace an existing command with that name. Do not install the source-only
`codex-cli/` directory: it does not contain a compiled runtime.

The launcher defaults to `~/.codex-android`; `CODEX_HOME` overrides it. Use a fresh
home rather than reusing a Codex VL database, which has incompatible migrations.
Existing VL databases are not modified or migrated. Reauthenticate in the new
home. Stop running Codex processes before replacing an installed artifact.

## Authentication and use

```sh
codex login --device-auth
codex login status
cd ~/my-project
codex
```

Device-code authentication avoids a local browser callback. Browser login with
`codex login` uses `termux-open-url`. For API-key authentication, supply the key
through standard input rather than a command-line argument:

```sh
printenv OPENAI_API_KEY | codex login --with-api-key
codex exec 'Explain this repository'
codex resume
```

Account access and device-code availability follow the
[upstream authentication requirements](https://developers.openai.com/codex/auth/).
Authentication files contain credentials; keep the Codex home private.

Android does not provide the desktop filesystem sandbox backends. The retained
Android execution fix only permits an unsandboxed first attempt after an actual
approval and refuses to discard deny-read policy. Unenforceable policies still
fail closed. Review command approvals; this project does not configure bypass
flags or turn approvals off.

## Build from source

The build script supports cross-compilation on Linux x86_64 and macOS. Install Rust
through rustup, Node/npm, Python 3.11+, Clang, CMake, Ninja, pkg-config, Perl, and
Android NDK r28c (`28.2.13676358`) for your build host. On macOS, install the
Command Line Tools and select an accepted developer toolchain. The workspace pins Rust in
`codex-rs/rust-toolchain.toml`. From the extracted repository root:

```sh
export ANDROID_NDK_HOME=/absolute/path/to/android-ndk-r28c
bash android/build.sh
```

Outputs are under `dist/android/`. The build includes `codex`,
`codex-code-mode-host`, and `libc++_shared.so`, with `$ORIGIN` runtime lookup.
It downloads checksum-pinned Android V8 artifacts and verifies that V8's sandbox
is enabled before linking. Missing or mismatched artifacts stop the build.

The [Android workflow](.github/workflows/android.yml) performs the same build and
uploads an artifact; it never publishes a package. Building V8 itself uses
[the separate Android V8 workflow](.github/workflows/rusty-v8-android-release.yml).
Native source builds inside Termux and cross builds on Windows are not
currently supported by these scripts.

## Limitations and validation

Cross-compilation is not a device test. See [the validation record](android/VALIDATION.md)
for actual results and [the runtime checks](qa/runtime-suite/README.md) for device
acceptance. In particular, verify login, PTY resizing, Ctrl-C, shell execution,
patching, resume, MCP, and code-mode execution on a real ARM64 device before
releasing a build.

Android can terminate background or CPU-heavy processes; see the
[Termux Android process-limit note](https://github.com/termux/termux-app#readme).
Desktop voice/WebRTC integration is not supported in a plain Termux CLI.
Advisory-lock fallback on filesystems without locking cannot guarantee concurrent
writer exclusion. Prefer private storage and one writer per session. SQLite falls
back to a single connection with fully synchronized rollback journaling if WAL initialization fails.
Automatic desktop update paths are disabled on Android; update by installing a
new verified local artifact. Upstream remote-control APIs remain available for
compatibility, but remote pairing and persistent daemon operation are not certified.

## Maintenance and attribution

[Android maintenance notes](android/MAINTENANCE.md) describe the remaining upstream
delta, the repository assessment, and synchronization procedure. General upstream
source documentation remains under `docs/` and `codex-rs/`; its desktop installation
and publishing instructions do not distribute this Android build.

Based on [OpenAI Codex](https://github.com/openai/codex), with Android/Termux work
from [Codex VL](https://github.com/DioNanos/codex-vl) and
[codex-termux](https://github.com/DioNanos/codex-termux) by Davide A. Guglielmi.
V8 is from [denoland/rusty_v8](https://github.com/denoland/rusty_v8).
Apache-2.0; see [LICENSE](LICENSE), [NOTICE](NOTICE), and retained third-party
licenses and notices. This project is not affiliated with or endorsed by OpenAI.
