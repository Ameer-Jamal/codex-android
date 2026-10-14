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
npm i -g codex-android
codex
```

Follow the sign-in instructions, then open a project:

```sh
cd ~/my-project
codex
```

The npm package installs the `codex` command and includes the Android runtime.
Starting with version `0.160.0-android.5`, first launch completes setup even if
npm reports that install scripts were blocked. You can run `codex` normally after
installation; no script-permission flag is required.
Setup adds missing Git, ripgrep, browser-opening tools, and CA certificates
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

Devices using 16 KB memory pages still need compatibility testing. The tested
Termux v0.118.3 failed during its own setup on an Android 17 emulator with 16 KB
pages, before Codex could be installed. Standard 4 KB emulator checks passed;
see the [validation record](android/VALIDATION.md) for the tested environments.

## Using Codex

Start an interactive session with `codex`, or give it a task:

```sh
codex 'Explain how this project works'
codex exec 'Find potential bugs in this repository'
codex resume
```

On Android, `codex` uses the embedded server by default, including `resume` and
`fork`. You don't need to start a background daemon. This keeps normal command
approvals enabled.

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
npm i -g codex-android@latest
```

### Uninstall

Exit all running Codex sessions, then run:

```sh
npm uninstall -g codex-android
```

This removes the package and its `codex` command. Your login, settings, and
conversations stay in `~/.codex-android`, ready for a reinstall. Your projects and
Termux tools such as Node.js, Git, and ripgrep are kept too. Use the package name
without `@latest`; `-g` removes the global installation used by the `codex` command.

If `codex` still launches something afterward, run `type codex` and check for an
old alias or another installation. Remove an old alias from your shell startup
file and run `unalias codex` in the current shell.

To also erase saved login, settings, and conversations, after exiting all Codex
sessions, run this **optional, permanent deletion**:

```sh
rm -rf -- "$HOME/.codex-android"
```

This deletes the default data directory. If you set a custom `CODEX_HOME`, its
data remains in that directory; remove it separately only if you want to erase it.

## Troubleshooting and limitations

- **Unsupported platform:** install from inside ARM64 Termux, with Node.js 22+.
- **Permission or storage errors:** keep projects in `~/`, rather than shared
  Android storage such as `/sdcard`. Shared storage can prevent programs from
  executing or saving session data correctly.
- **Setup fails:** check your connection and the Termux package mirror, then run
  the `pkg install` command shown in the error and try `codex` again. Version
  `0.160.0-android.5` completes setup at first launch even when npm blocks scripts.
  Older versions need `--allow-scripts=codex-android` during installation.
- **Another `codex` is installed:** both packages use the same command name.
  Remove the previous installation before installing this one.
- **An old shell alias launches another package:** run `type codex`. Remove the old
  alias from your shell startup file and run `unalias codex` in the current shell.
- **App server did not become ready / socket already in use:** run
  `codex --no-daemon` to work with the embedded server and normal approvals.
  Version `0.160.0-android.4` defaults to this mode; older versions need the flag.
  Deleting settings while a daemon is running can leave a live socket without its
  connection path. Stop the daemon before resetting settings; don't delete your
  settings directory to troubleshoot this error.
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
npm i -g ./codex-android-*.tgz
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

## Android diagnostics and optional storage access

Run `codex-android doctor` for a copyable diagnostic report, or
`codex-android doctor --json` for structured results. It checks runtime versions,
dependencies, PATH, page size and storage without installing anything, reading
login files or sending model requests. Reports omit personal paths and command
logs. Run `type codex` separately in your terminal to check old shell aliases.
Warnings do not prove a device is compatible: 16 KB and physical-device acceptance
remain pending.

To optionally request access to shared files and media:

```sh
codex-android setup storage
```

Approve the Android permission prompt if you want that access. The command uses
Termux's existing storage setup; it cannot silently grant permissions or access
other apps' private data. Shared files appear under `~/storage/shared`. Keep
Git/build projects under `~/` because shared storage limits executable files,
symlinks and Unix permissions. Interactive Codex warns when started there but
still allows file and media tasks.

### Advanced Android tasks with Shizuku

Shizuku is optional and does not automatically elevate Codex. Its
[official setup guide](https://shizuku.rikka.app/guide/setup/) explains wireless
ADB pairing and startup; restarting after a phone reboot is generally required.
An explicitly configured [rish bridge](https://github.com/RikkaApps/Shizuku-API/blob/master/rish/README.md)
can execute selected commands with ADB shell privileges when Shizuku is started
through debugging. Those privileges are not root and remain subject to Android
and manufacturer restrictions. This package does not install the bridge, enable
debugging or route ordinary Codex commands through it. Review privileged commands
and keep normal command approvals enabled.

`npm uninstall -g codex-android` removes both `codex` and `codex-android` commands.
Login, settings and conversations remain in your Codex home.

### Android-aware agent instructions (next release)

On first launch, the launcher seeds a short Android/Termux guide in
`$CODEX_HOME/AGENTS.md` (normally `~/.codex-android/AGENTS.md`) if neither global
`AGENTS.md` nor `AGENTS.override.md` exists. It helps Codex select available tools,
use appropriate storage, understand permission boundaries and offer practical
alternatives for desktop-only workflows. It does not grant permissions or claim
official OpenAI Android support.

The file is yours to edit. Existing files, including empty files and overrides,
are preserved; package upgrades never rewrite them. Keep an empty `AGENTS.md`
if you do not want the default guidance. If you already have global instructions,
merge any useful parts from the packaged `assets/AGENTS.android.md` yourself.
Project instructions and your requests remain applicable. Restart Codex to load
new global instructions. Doctor does not create or modify this file.
