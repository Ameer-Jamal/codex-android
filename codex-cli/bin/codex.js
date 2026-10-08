#!/usr/bin/env node
// Android distribution shim. Native Codex retains its upstream CLI and protocols.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
if (process.platform !== "android" || process.arch !== "arm64") {
  throw new Error("Codex for Android requires ARM64 Termux on Android.");
}
const binary = path.join(
  root,
  "vendor",
  "aarch64-linux-android",
  "bin",
  "codex",
);
if (!existsSync(binary)) {
  throw new Error(
    "Android runtime is missing. Install the tarball produced by android/build.sh.",
  );
}
// A fresh home avoids importing incompatible VL SQLite migration history.
const env = {
  ...process.env,
  CODEX_HOME:
    process.env.CODEX_HOME || path.join(os.homedir(), ".codex-android"),
  CODEX_MANAGED_BY_NPM: "1",
  CODEX_MANAGED_PACKAGE_ROOT: root,
};
try {
  mkdirSync(env.CODEX_HOME, { recursive: true, mode: 0o700 });
} catch (error) {
  console.error(
    `Unable to create Codex home ${env.CODEX_HOME}: ${error.message}`,
  );
  process.exit(1);
}
delete env.CODEX_MANAGED_BY_BUN;
delete env.CODEX_MANAGED_BY_PNPM;
delete env.CODEX_MANAGED_BY_VITE_PLUS;
const child = spawn(binary, process.argv.slice(2), { stdio: "inherit", env });
child.on("error", (error) => {
  console.error(`Unable to start Codex: ${error.message}`);
  process.exit(1);
});
for (const signal of ["SIGINT", "SIGTERM", "SIGHUP"]) {
  process.on(signal, () => {
    if (!child.killed) {
      try {
        child.kill(signal);
      } catch {
        // The child may have exited between checking and forwarding.
      }
    }
  });
}
child.on("exit", (code, signal) => {
  if (signal) {
    process.removeAllListeners(signal);
    process.kill(process.pid, signal);
  } else process.exit(code ?? 1);
});
