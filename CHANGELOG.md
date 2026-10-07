# Codex for Android

## 0.160.0-android.1 (source conversion)

- Restore the OpenAI Codex 0.160.0 architecture and retain Android/Termux fixes.
- Remove Vivling, VL loops, fleet identity experiments, and VL distributions.
- Add a focused ARM64 NDK build, private local npm artifact, and Android CI.
- Preserve sandbox-enabled V8, approval checks, authentication, PTY, sockets,
  and filesystem compatibility. Isolate Android SQLite fallback and process identity.

This entry describes source changes, not a published or device-certified release.
See android/VALIDATION.md for verification status.
