# Android runtime smoke checks

Run `bash qa/runtime-suite/run_cli_runtime_suite.sh` in ARM64 Termux after
installing the built tarball and signing in. Set `CODEX_CMD` to select a binary.
The default checks exercise startup, CLI parsing, and authentication status.
Add `--live` to make one authenticated model request, subject to normal usage
charges. The suite preserves the configured approval and sandbox policy.

Also verify interactively: portrait/landscape resizing, Ctrl-C, shell execution,
patch application, resume, browser or device-code login, and a local MCP server.
Cross-compilation cannot verify these device behaviors.
