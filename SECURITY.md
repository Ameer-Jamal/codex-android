# Security

Codex for Android is a community derivative of OpenAI Codex. Report upstream
vulnerabilities through [OpenAI's security policy](https://github.com/openai/codex/security/policy).
For Android-specific issues, use the private security reporting channel of the
repository that distributes your build; this source archive has no configured
maintainer or disclosure address. Do not post credentials in public issues.

Android execution retains upstream approval and deny-read policy checks. Android
has no supported desktop filesystem sandbox backend; approval does not create OS
isolation. TLS verification, socket ownership and permission checks, and V8
sandbox requirements are preserved. Existing 8 KiB model-instruction and Guardian
policy limits are retained. Android V8 downloads use committed checksums.

Install only artifacts from a build you trust and verify their digest. Update by
reinstalling the locally built artifact. Keep projects, authentication, and state
in Termux private storage. Unsupported advisory locking provides reduced writer
coordination; avoid simultaneous writers to the same session on such filesystems.
