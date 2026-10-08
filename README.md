<p align="center">
  <img src="https://raw.githubusercontent.com/Ameer-Jamal/codex-android/main/assets/icon.png" width="112" alt="Codex for Android icon" />
</p>

# Codex for Android

Bring OpenAI Codex to your Android terminal. Ask questions about your code, make
changes, and run commands in your projects, right from Termux.

**Early access:** available for ARM64 devices running Android 10 or newer.
Real-device testing is still in progress. This is a community project based on
[OpenAI Codex](https://github.com/openai/codex), independently maintained and not
affiliated with OpenAI.

## Get started

Install [Termux](https://github.com/termux/termux-app#installation), then run these
commands inside it. Use Termux's private home directory for your projects.

```sh
pkg update && pkg upgrade
pkg install nodejs-lts
npm install -g codex-android
codex login --device-auth
```

Follow the sign-in instructions, then open a project:

```sh
cd ~/my-project
codex
```

The npm package installs the `codex` command and includes the Android runtime.
The installer adds missing Git, ripgrep, browser-opening tools, and CA certificates
through Termux's package manager. First launch creates your private settings
directory automatically. You don't need Rust or a source build. Install project
tools such as Python separately when your work needs them.

## What you need

- An ARM64 Android phone or tablet with Android 10 or newer.
- Standard Termux, with Node.js 22 or newer (`node --version`).
- Internet access and a supported ChatGPT account or OpenAI API key.
- At least 1 GB of free space for installation, plus room for projects and caches.
  The download is about 147 MB.

Run `uname -m` in Termux to check your architecture; it should say `aarch64`.
32-bit devices, x86 Android, proot environments, and APK installation are not
currently supported. Install Termux and its plugins from the same source.

## Using Codex

Start an interactive session with `codex`, or give it a task:

```sh
codex 'Explain how this project works'
codex exec 'Find potential bugs in this repository'
codex resume
```

Codex can read and edit files and run commands. Review its proposed changes and
command approvals. Android does not offer the same filesystem sandbox as desktop
platforms; use projects you trust and keep approvals enabled.

### Sign in

Device-code login lets you sign in through a browser without a local callback:

```sh
codex login --device-auth
codex login status
```

If device-code login isn't available for your account, try `codex login` to open
browser sign-in. You can also use an API key through standard input:

```sh
printenv OPENAI_API_KEY | codex login --with-api-key
```

See [Codex authentication](https://developers.openai.com/codex/auth/) for account
requirements. Keep API keys and sign-in files private.

### Update

Exit running Codex sessions, then install the latest package:

```sh
npm install -g codex-android@latest
```

## Troubleshooting and limitations

- **Unsupported platform:** install from inside ARM64 Termux, with Node.js 22+.
- **Permission or storage errors:** keep projects in `~/`, rather than shared
  Android storage such as `/sdcard`. Shared storage can prevent programs from
  executing or saving session data correctly.
- **Launcher won't start:** installation needs the package's postinstall script.
  If your npm settings block scripts, allow this package's script and reinstall.
- **Another `codex` is installed:** both packages use the same command name.
  Remove the previous installation before installing this one.
- **Background sessions stop:** Android may terminate background or CPU-heavy
  processes. Persistent background operation is not guaranteed.

Settings and sessions are stored in `~/.codex-android`. Set `CODEX_HOME` to use a
different directory. Start with a fresh directory when switching distributions.

This release still needs physical-device checks for login, terminal resizing,
Ctrl-C, command execution, editing, session recovery, MCP, and code-mode. Voice
integration and remote pairing are not supported Android workflows. See the
[validation record](https://github.com/Ameer-Jamal/codex-android/blob/main/android/VALIDATION.md)
for test results and known issues.

## Downloads and source

For manual or offline installation, get the `.tgz` and matching `.sha256` from
[GitHub releases](https://github.com/Ameer-Jamal/codex-android/releases). Copy both
to Termux's private home, verify the checksum, and install the downloaded file:

```sh
sha256sum -c codex-android-*.tgz.sha256
npm install -g ./codex-android-*.tgz
```

To build from source, use Linux x86_64 or macOS with Rust (the pinned toolchain),
Node.js 22+, Python 3.11+, Clang, CMake, Ninja, pkg-config, Perl, and Android NDK
r28c. On macOS, install the Command Line Tools. From the repository root:

```sh
export ANDROID_NDK_HOME=/absolute/path/to/android-ndk-r28c
bash android/build.sh
```

Packages are written to `dist/android/`. Building inside Termux is not currently
supported. Contributor details are in the
[maintenance guide](https://github.com/Ameer-Jamal/codex-android/blob/main/android/MAINTENANCE.md).

[Report an issue](https://github.com/Ameer-Jamal/codex-android/issues) ·
[npm package](https://www.npmjs.com/package/codex-android) ·
[Source code](https://github.com/Ameer-Jamal/codex-android)

Licensed under Apache-2.0. See
[LICENSE](https://github.com/Ameer-Jamal/codex-android/blob/main/LICENSE) and
[NOTICE](https://github.com/Ameer-Jamal/codex-android/blob/main/NOTICE) for copyright,
attribution, and third-party notices.
