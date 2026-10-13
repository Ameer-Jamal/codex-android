# Workflow Strategy

`android.yml` is the primary distribution workflow: Linux NDK cross-compilation
for ARM64 Termux and artifact upload, with no package publication.
`rusty-v8-android-release.yml` builds the matching V8 artifact independently.
The inherited desktop workflows remain available for manual upstream regression
audits through `blocking-ci.yml` and `postmerge-ci.yml`. They include upstream
private runner groups and desktop-only infrastructure, so they are not automatic
requirements for this community Android project.

Android CI runs launcher/package tests, shell and workspace checks, the retained
`cargo-deny.yml` dependency-security check, and the NDK ARM64 build. The result is
uploaded as a downloadable artifact. After exact-artifact Android 17 emulator acceptance, dispatch `android-publish.yml`
to publish via OIDC and attach verified registry bytes to a GitHub prerelease.
The npm trusted publisher must allow direct publishing; no npm tokens or recurring
passkey approvals are needed. See `android/MAINTENANCE.md` for commands and caching.
