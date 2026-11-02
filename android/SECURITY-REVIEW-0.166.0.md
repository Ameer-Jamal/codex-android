# Dependency security review: upstream 0.166.0

Reviewed November 2, 2026. This is source/dependency analysis, not an exploitability
certification or acceptance of residual risk. Tests and publication gates remain separate.

## Fixed instead of excepted

The advisory database now lists compatible backports:

| Advisory                                                                   | Affected locked version | Candidate fix |
| -------------------------------------------------------------------------- | ----------------------- | ------------- |
| [RUSTSEC-2026-0391](https://rustsec.org/advisories/RUSTSEC-2026-0391.html) | zstd 0.13.3             | 0.13.4        |
| [RUSTSEC-2026-0398](https://rustsec.org/advisories/RUSTSEC-2026-0398.html) | zstd-safe 7.2.4         | 7.4.0         |
| [RUSTSEC-2026-0403](https://rustsec.org/advisories/RUSTSEC-2026-0403.html) | zstd-safe 7.2.4         | 7.4.0         |
| [RUSTSEC-2026-0410](https://rustsec.org/advisories/RUSTSEC-2026-0410.html) | zstd-sys 2.0.16         | 2.1.2         |

All four exceptions are removed from both advisory policies. Native Android is
not wasm32 (0410), and rollout code uses the read decoder rather than the affected
write decoder (0403). Those observations no longer need to justify retaining
affected versions, because the candidate upgrades the shared dependency graph.

A fresh check additionally identified
[RUSTSEC-2026-0386](https://rustsec.org/advisories/RUSTSEC-2026-0386.html):
Tokio 1.52.3 permits unsound safe Unix descriptor registration. The candidate
updates to 1.53.3 and uses the replacement registration API for PTY I/O, mount
watching and the pidfd test fixture. Each registration transfers an owned File
or OwnedFd into AsyncFd, keeping that descriptor open and unchanged for its
lifetime; errors still propagate. PTY regression tests are included in cloud
native checks. No exception was added for this advisory.

## crypto-bigint: unresolved release decision

[RUSTSEC-2026-0387](https://rustsec.org/advisories/RUSTSEC-2026-0387.html)
reports secret-dependent timing in arithmetic intended to be constant-time.
Exploitability depends on the downstream algorithm, compiler, CPU and observable
side channel. The advisory does not establish a same-device-only attacker model.

`cargo tree --locked -p codex-cli --target aarch64-linux-android --edges normal,build
-i crypto-bigint` confirms 0.5.5 remains in the Android CLI runtime dependency
graph through elliptic-curve 0.13.8 / p256 and other consumers. Dependency presence
alone does not prove that secret-bearing affected operations are invoked.
For example, local secrets use age's scrypt recipient/identity, and the credential
parser in user-verification handles public keys; neither observation establishes
safety of every consumer.

The advisory only lists >=0.7.6 as patched. That is incompatible with the current
elliptic-curve dependency constraint, so changing one lockfile version is not a
valid remedy. A broader dependency migration, reviewed upstream backport, or an
explicit residual-risk decision remains necessary. No Android-specific side-channel
analysis or constant-time binary verification has been performed.

**Recommendation: hold publication.** The existing upstream-carried crypto
exception is not an Android risk acceptance. Passing cargo-deny with that exception
and passing functional tests do not resolve this issue.
