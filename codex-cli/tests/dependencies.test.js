import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";
import { runPostinstall } from "../scripts/postinstall.js";

const prefix = "/data/data/com.termux/files/usr";
function options(t) {
  const binDir = mkdtempSync(path.join(tmpdir(), "codex-dependencies-"));
  t.after(() => rmSync(binDir, { recursive: true, force: true }));
  return {
    binDir,
    platform: "android",
    env: { PREFIX: prefix },
    warn: () => {},
    log: () => {},
  };
}

test("installs only missing Termux packages and verifies their files", async (t) => {
  const missing = new Set([`${prefix}/bin/git`, `${prefix}/bin/rg`]);
  const calls = [];
  const config = options(t);
  await runPostinstall({
    ...config,
    existsSync: (file) => !missing.has(file),
    spawnSync: (command, args, settings) => {
      calls.push({ command, args, settings });
      missing.clear();
      return { status: 0 };
    },
  });
  assert.deepEqual(calls, [
    {
      command: `${prefix}/bin/pkg`,
      args: ["install", "-y", "git", "ripgrep"],
      settings: { stdio: "inherit", env: config.env },
    },
  ]);
});

test("does not invoke the package manager when dependencies are present", async (t) => {
  await runPostinstall({
    ...options(t),
    existsSync: () => true,
    spawnSync: () => {
      throw new Error("unexpected package installation");
    },
  });
});

test("package manager failures fail installation with a recovery command", async (t) => {
  await assert.rejects(
    runPostinstall({
      ...options(t),
      existsSync: (file) => file !== `${prefix}/etc/tls/cert.pem`,
      spawnSync: () => ({ status: 100 }),
    }),
    /Run pkg install ca-certificates and reinstall codex-android/,
  );
});

test("a successful package manager exit must actually supply the dependencies", async (t) => {
  await assert.rejects(
    runPostinstall({
      ...options(t),
      existsSync: (file) => file !== `${prefix}/bin/termux-open-url`,
      spawnSync: () => ({ status: 0 }),
    }),
    /still missing: termux-tools/,
  );
});
