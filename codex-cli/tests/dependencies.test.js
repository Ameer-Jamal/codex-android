import assert from "node:assert/strict";
import test from "node:test";
import { ensureTermuxDependencies } from "../lib/setup.js";

const prefix = "/data/data/com.termux/files/usr";
function options() {
  return {
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
  await ensureTermuxDependencies({
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
  await ensureTermuxDependencies({
    ...options(t),
    existsSync: () => true,
    spawnSync: () => {
      throw new Error("unexpected package installation");
    },
  });
});

test("package manager failures fail startup setup with a recovery command", async (t) => {
  await assert.rejects(
    ensureTermuxDependencies({
      ...options(t),
      existsSync: (file) => file !== `${prefix}/etc/tls/cert.pem`,
      spawnSync: () => ({ status: 100 }),
    }),
    /Run pkg install ca-certificates, then run codex again/,
  );
});

test("a successful package manager exit must actually supply the dependencies", async (t) => {
  await assert.rejects(
    ensureTermuxDependencies({
      ...options(t),
      existsSync: (file) => file !== `${prefix}/bin/termux-open-url`,
      spawnSync: () => ({ status: 0 }),
    }),
    /still missing: termux-tools/,
  );
});

test("invalid prefixes use the Termux default for dependency installation", async () => {
  for (const value of [
    "relative",
    "/tmp/x",
    `${prefix}/../other`,
    `${prefix}\nnode`,
  ]) {
    let installed = false;
    await ensureTermuxDependencies({
      ...options(),
      env: { PREFIX: value },
      existsSync: () => installed,
      spawnSync: (command) => {
        assert.equal(command, `${prefix}/bin/pkg`);
        installed = true;
        return { status: 0 };
      },
    });
  }
});

test("non-Termux setup does not install anything", async () => {
  await ensureTermuxDependencies({
    platform: "linux",
    env: {},
    spawnSync: () => {
      throw new Error("unexpected install");
    },
  });
});
