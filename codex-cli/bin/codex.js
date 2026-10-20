#!/usr/bin/env node
// Android distribution shim. Native Codex retains its upstream CLI and protocols.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { ensureTermuxDependencies } from "../lib/setup.js";

import { seedAndroidInstructions } from "../lib/instructions.js";
import { sharedStorage, storageWarning } from "../lib/android.js";

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
// Complete setup before starting the native runtime;
// when dependencies are present this does not invoke the package manager.
try {
  await ensureTermuxDependencies({ log: console.error });
} catch (error) {
  console.error(`Unable to finish Codex setup: ${error.message}`);
  process.exit(1);
}
// Keep this distribution's settings and sessions separate from other installs.
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
try {
  seedAndroidInstructions(env.CODEX_HOME);
} catch {
  console.error(
    "Warning: unable to seed Android guidance; Codex will continue with existing instructions.",
  );
}
delete env.CODEX_MANAGED_BY_BUN;
delete env.CODEX_MANAGED_BY_PNPM;
delete env.CODEX_MANAGED_BY_VITE_PLUS;
// Shared daemon sockets are not yet reliable on Termux. Use upstream's embedded
// server without changing approvals or sandbox policy. Explicit opt-in retains
// access to advanced upstream commands that require a shared server.
const args = process.argv.slice(2);
if (
  storageWarning(
    args,
    process.stdin.isTTY && process.stdout.isTTY,
    sharedStorage(process.cwd()),
  )
) {
  console.error(
    "Shared Android storage limits executable files, symlinks and permissions.\nKeep development projects under ~/; shared storage remains useful for files and media.",
  );
}
const promptDelimiter = args.indexOf("--");
const options = promptDelimiter === -1 ? args : args.slice(0, promptDelimiter);
if (env.CODEX_ANDROID_USE_DAEMON !== "1" && !options.includes("--no-daemon")) {
  args.unshift("--no-daemon");
}
const child = spawn(binary, args, { stdio: "inherit", env });
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
