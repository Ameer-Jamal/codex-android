import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  collectDoctor,
  renderDoctor,
  setupStorage,
  sharedStorage,
  storageWarning,
} from "../lib/android.js";

test("doctor bounds native checks and sanitizes command failures", (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "android-doctor-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.writeFileSync(
    path.join(root, "package.json"),
    JSON.stringify({ name: "codex-android", version: "0.160.0-android.6" }),
  );
  const calls = [];
  const report = collectDoctor({
    root,
    platform: "android",
    arch: "arm64",
    node: "24.0.0",
    env: { HOME: "/secret-home", PATH: "", SECRET: "private-token" },
    cwd: "/secret-project",
    exists: () => true,
    run(command, args, options) {
      calls.push({ command, args, timeout: options.timeout });
      if (args[0] === "--version")
        assert.notEqual(options.env.CODEX_HOME, "/secret-home");
      return args[0] === "--version"
        ? { status: null, stderr: "private-token /secret-home" }
        : { status: 0, stdout: "16384\n" };
    },
  });
  assert.equal(report.exitCode, 1);
  assert.equal(report.checks.find((c) => c.id === "native").status, "fail");
  assert.equal(report.checks.find((c) => c.id === "page-size").status, "warn");
  assert.equal(calls.length, 2);
  assert.ok(calls.every((c) => c.timeout === 5000));
  assert.doesNotMatch(
    JSON.stringify(report) + renderDoctor(report),
    /private-token|secret-home|secret-project/,
  );
});

test("doctor reports missing dependencies and unsupported platform without native invocation", () => {
  const calls = [];
  const report = collectDoctor({
    root: "/missing",
    platform: "linux",
    arch: "x64",
    node: "20.0.0",
    exists: () => false,
    access: () => {
      throw new Error();
    },
    run(command) {
      calls.push(command);
      throw new Error("private");
    },
  });
  assert.equal(report.exitCode, 1);
  for (const id of [
    "platform",
    "node",
    "git",
    "ripgrep",
    "termux-tools",
    "ca-certificates",
    "package",
    "native",
    "path",
  ])
    assert.equal(report.checks.find((c) => c.id === id).status, "fail");
  assert.deepEqual(calls, ["/system/bin/getconf"]);
});

test("storage detection resolves aliases and warning stays out of noninteractive commands", () => {
  assert.equal(
    sharedStorage("/home/storage/shared", () => "/storage/emulated/0/photos"),
    true,
  );
  assert.equal(
    sharedStorage("/private", () => "/data/data/com.termux/files/home/project"),
    false,
  );
  assert.equal(
    sharedStorage("/missing", () => {
      throw new Error();
    }),
    false,
  );
  for (const args of [
    ["exec", "hello"],
    ["--help"],
    ["--version"],
    ["login"],
    ["mcp"],
  ])
    assert.equal(storageWarning(args, true, true), false);
  assert.equal(storageWarning([], true, true), true);
  assert.equal(storageWarning(["resume"], true, true), true);
  assert.equal(storageWarning([], false, true), false);
});

test("storage setup handles success, denied permission, missing utility and failed command", () => {
  for (const [status, accessible, expected] of [
    [0, true, 0],
    [0, false, 1],
    [null, false, 1],
    [1, true, 1],
  ]) {
    const log = [];
    const result = setupStorage({
      accessible: () => accessible,
      log: (text) => log.push(text),
      run(command, args, options) {
        assert.equal(command, "termux-setup-storage");
        assert.deepEqual(args, []);
        assert.equal(options.timeout, 60000);
        return { status };
      },
    });
    assert.equal(result, expected);
    assert.match(log[0], /does not grant unrestricted/);
  }
});

test("doctor succeeds with optional warnings and a matching executable", (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "android-doctor-pass-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, "bin"));
  fs.writeFileSync(path.join(root, "bin/codex.js"), "", { mode: 0o755 });
  fs.symlinkSync("codex.js", path.join(root, "bin/codex"));
  fs.writeFileSync(
    path.join(root, "package.json"),
    JSON.stringify({ name: "codex-android", version: "0.160.0-android.6" }),
  );
  const report = collectDoctor({
    root,
    platform: "android",
    arch: "arm64",
    node: "24.0.0",
    env: { PATH: path.join(root, "bin"), HOME: path.join(root, "absent") },
    exists: () => true,
    access: () => {},
    run(command, args) {
      return {
        status: 0,
        stdout: args[0] === "--version" ? "codex-cli 0.160.0\n" : "4096\n",
      };
    },
  });
  assert.equal(report.exitCode, 0);
  assert.equal(report.checks.find((c) => c.id === "path").status, "pass");
  assert.equal(fs.existsSync(path.join(root, "absent")), false);
});

test("companion CLI emits JSON and rejects invalid arguments", () => {
  const cli = new URL("../bin/codex-android.js", import.meta.url);
  const invalid = spawnSync(
    process.execPath,
    [cli.pathname, "doctor", "--invalid"],
    { encoding: "utf8" },
  );
  assert.equal(invalid.status, 2);
  const help = spawnSync(process.execPath, [cli.pathname, "--help"], {
    encoding: "utf8",
  });
  assert.equal(help.status, 0);
  const doctor = spawnSync(
    process.execPath,
    [cli.pathname, "doctor", "--json"],
    { encoding: "utf8", timeout: 15000 },
  );
  const report = JSON.parse(doctor.stdout);
  assert.equal(report.formatVersion, 1);
  assert.equal(doctor.status, report.exitCode);
  assert.equal(doctor.stderr, "");
});
