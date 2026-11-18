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

Remove this override when a compatible upstream Rama version includes patched
Hickory. Upgrade the whole Rama stack/toolchain deliberately, not implicitly.
