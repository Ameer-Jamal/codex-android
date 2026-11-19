# Rama DNS compatibility patch

Source: crates.io `rama-dns 0.3.0-alpha.4`, package SHA-256
`e340fef2799277e204260b17af01bc23604712092eacd6defe40167f304baed8`; upstream commit
`4733273a10a791762e2b7727850032b0c9b8536d`, directory `rama-dns`.
Original crate bytes were verified before extraction. MIT and Apache-2.0 license
texts are retained from that exact upstream commit.

Local changes pin Rama dependencies to the existing alpha version and port the
Hickory adapter to exact `hickory-resolver 0.26.3` (MSRV 1.88), retaining Rust 1.95
and Rama's public resolver interface. Builder errors propagate from the system
constructor. The existing infallible builder remains compatible; additive
`try_build` exposes new Hickory initialization errors. TLS features are disabled.
Hickory's new untyped answer records are filtered by family/type, preserving TXT
binary chunks; focused tests include mixed records and no network queries.

Android's managed proxy uses the platform resolver rather than the library's
existing public-resolver defaults. Post-resolution address policy is preserved.
This is a source prototype until the regenerated lockfile, cloud tests, Android
build and exact-artifact acceptance pass. No vulnerability exception is added.

## Test lock scope

This crate is a `[patch.crates-io]` override and is not a workspace member, so
Cargo refuses to test its library through `codex-rs` when it requires
dev-dependencies. The root dependency override still selects the patched
source for production compilation. The focused Hickory tests are therefore run standalone:
the crate is copied to an isolated directory and built as its own workspace
with a dedicated test lockfile resolved at the exact pinned versions
(`rama-core`/`rama-net`/`rama-utils` `0.3.0-alpha.4`, `hickory-resolver` and
`hickory-proto` `0.26.3`).

That test lockfile is scoped to this adapter crate alone. It is not
`codex-rs/Cargo.lock`, it is not committed, and it is not evidence that
`codex-rs` builds against the patched crate; the exact-source workspace build
and the root `--locked` production and Android native dependency gates remain
separate checks.

Remove this override when a compatible upstream Rama version includes patched
Hickory. Upgrade the whole Rama stack/toolchain deliberately, not implicitly.
