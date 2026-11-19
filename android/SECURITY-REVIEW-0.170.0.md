# Dependency security review: upstream 0.170.0

Prepared November 18, 2026 for the `0.170.0-android.1` candidate. This is source and
lockfile analysis, not an exploitability certification or acceptance of residual risk.
The [0.166.0 review](SECURITY-REVIEW-0.166.0.md) and its maintainer decision do not
authorize this release.

The first worker could not reach the advisory database. The coordinator fetched primary RustSec advisory files for 0487, 0514 and 0441 and verified the fixed Hickory version (>=0.26.2) and pin-utils maintenance notice. The list is not claimed complete. Exact-source cloud dependency policy remains pending.

## Kept fixed instead of excepted

Upstream 0.170.0 adds advisory exceptions that the Android lockfile does not need.
The candidate keeps the existing Android dependency upgrades and does not import them:

- RUSTSEC-2026-0391: upstream zstd 0.13.3; candidate zstd 0.13.4.
- RUSTSEC-2026-0398 and RUSTSEC-2026-0403: upstream zstd-safe 7.2.4; candidate 7.4.0.
- RUSTSEC-2026-0410: upstream zstd-sys 2.0.16; candidate 2.1.2.
- RUSTSEC-2026-0418: upstream libz-sys 1.1.29; candidate 1.1.31, the version named
  by upstream's removal condition.

Tokio 1.53.3, tar 0.4.46, webrtc 0.21 and the `serde_norway` replacement for
`serde_yaml` are also retained from the existing Android lockfile.

## Upstream exceptions reviewed before the Android build

Upstream 0.170.0 ignores the following advisories. They were not added to
`deny.toml` or `.cargo/audit.toml`. If they still match the dependency graph,
the cloud dependency policy fails, so the Android build cannot be produced until the
maintainer chooses a remedy or explicitly accepts each risk.

- RUSTSEC-2026-0441: pin-utils 0.1.0 is unmaintained; reached through AWS Smithy
  and loom by codex-aws-auth and codex-network-proxy in the lockfile graph.
- RUSTSEC-2026-0487, 0489, 0490 and 0491: hickory-proto 0.25.2, reached through
  rama-dns by codex-network-proxy.
- RUSTSEC-2026-0504, 0505, 0511 and 0512 (hickory-proto 0.25.2) and RUSTSEC-2026-0514
  (hickory-resolver 0.25.2): described upstream as DNSSEC-only; same path.

The current `main` lockfile also contains hickory-proto 0.25.2 and pin-utils 0.1.0,
so these advisories may already fail dependency policy for unrelated branches and
pull requests. That has not been confirmed against workflow logs.

Upstream's stated remedy is a Rust 1.96+ toolchain plus a Rama release using
hickory-proto 0.26.2 or newer; it is not a lockfile-only change for this candidate.
Upstream states that DNSSEC is disabled for its feature set. That statement, and
whether these crates are reachable in the `aarch64-linux-android` CLI runtime graph,
have not been independently verified here. The next check is:

```sh
cargo tree --locked -p codex-cli --target aarch64-linux-android \
  --edges normal,build -i hickory-proto
```

## crypto-bigint: still unresolved

crypto-bigint 0.5.5 (RUSTSEC-2026-0387) remains via elliptic-curve 0.13.8, reaching
codex-aws-auth, codex-secrets, codex-user-verification and codex-voice-host in the
lockfile graph. The existing exception entry is unchanged. The November 3 decision
covered 0.166.0. On November 18 the maintainer approved carrying the documented
risk forward specifically for the 0.170.0-android.1 early-access release.

## Android lock and source protections

New upstream credential commit locking (`login/src/auth/storage_commit.rs`) and the
revised thread writer coordination (`rollout/src/writer_lock.rs`) used Rust's
standard file locks, which return Unsupported on Android without a system call.
Both now use `codex_keyring_store::file_lock` (flock on Android), keeping upstream's
deadlines, `WouldBlock` handling and genuine-error propagation. The relocated
installation ID file (`runtime-agent-instance`) now uses real shared/exclusive
locking instead of the previous unlocked fallback.

## Coordinator remediation prototype

A source-provenanced `third_party/rama-dns` path override ports the existing
0.3.0-alpha.4 adapter to exact Hickory resolver 0.26.3 without changing Rust 1.95
or the pinned Rama family. Package bytes were checksum-verified before extraction;
both license texts and source attribution are retained. The new generic Lookup
API is filtered to the requested answer-record type; tests cover mixed address
families, CNAME filtering and binary TXT chunks without live DNS. System-constructor
errors propagate; the compatibility builder gains a fallible `try_build` method.

Android's connector uses the existing native SystemDnsResolver, with the same
post-resolution address/network-policy checks. This is source review, not proven
Private DNS/VPN behavior on a device. The default resolver constructors remain
available for other platforms and explicit callers.

The old Hickory versions still exist in the pre-regeneration Cargo.lock. A
read-only cloud workflow resolves the localized override and exports the lockfile
with source SHA and checksum for coordinator review. It tests the adapter and
prints the Android dependency path. This job is not release-build acceptance;
commit the reviewed lockfile and rerun exact-source security/native checks first.

## Candidate audit and maintainer decision

GitHub run 44467476235 on `b49e7f56a7` cleared the dependency bans, licenses and
sources checks. Its advisory check failed only on the unmaintained notices for
chrono 0.4.43 (RUSTSEC-2026-0543) and pin-utils 0.1.0 (RUSTSEC-2026-0441). Both
versions are present in the previous release. Neither advisory lists a patched
release. On November 18 the maintainer approved exceptions for these two advisory
IDs for 0.170.0-android.1. Remove them when upstream and its dependencies migrate.

Run 44467476154 passed all three focused DNS adapter tests with the reviewed
cloud lockfile. It selects Hickory 0.26.3, zip 9.1.2, libz-sys 1.1.33,
quinn-proto 0.11.19 and quinn-udp 0.5.16 and 0.6.3. The exact package still needs
a successful build, emulator acceptance and fresh sign-in on the physical phone.
