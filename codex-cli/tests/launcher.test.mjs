import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import {
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const sourceRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
const androidPlatform =
  "data:text/javascript,Object.defineProperty(process,'platform',{value:'android'});Object.defineProperty(process,'arch',{value:'arm64'});";

function fixture(t, body) {
  const root = mkdtempSync(path.join(tmpdir(), "codex-android-launcher-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(path.join(root, "bin"));
  copyFileSync(
    path.join(sourceRoot, "bin/codex.js"),
    path.join(root, "bin/codex.js"),
  );
  writeFileSync(path.join(root, "package.json"), '{"type":"module"}');
  const binaries = path.join(root, "vendor/aarch64-linux-android/bin");
  mkdirSync(binaries, { recursive: true });
  if (body)
    writeFileSync(
      path.join(binaries, "codex"),
      `#!/usr/bin/env node\n${body}`,
      { mode: 0o755 },
    );
  return { root, launcher: path.join(root, "bin/codex.js") };
}

test("launcher forwards arguments, status, and an explicit Codex home", (t) => {
  const { root, launcher } = fixture(
    t,
    "console.log(JSON.stringify({args:process.argv.slice(2),home:process.env.CODEX_HOME})); process.exit(23);",
  );
  const home = path.join(root, "private-home");
  const result = spawnSync(
    process.execPath,
    ["--import", androidPlatform, launcher, "exec", "a prompt with spaces"],
    { encoding: "utf8", env: { ...process.env, CODEX_HOME: home } },
  );
  assert.equal(result.status, 23, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout), {
    args: ["exec", "a prompt with spaces"],
    home,
  });
});

test("missing Android runtime fails locally with actionable instructions", (t) => {
  const { launcher } = fixture(t);
  const result = spawnSync(
    process.execPath,
    ["--import", androidPlatform, launcher],
    { encoding: "utf8" },
  );
  assert.equal(result.status, 1);
  assert.match(
    result.stderr,
    /Install the tarball produced by android\/build.sh/,
  );
});

test(
  "launcher mirrors child signal termination",
  { timeout: 10000 },
  async (t) => {
    const { launcher } = fixture(
      t,
      'console.log("ready"); setInterval(() => {}, 1000);',
    );
    const child = spawn(
      process.execPath,
      ["--import", androidPlatform, launcher],
      { stdio: ["ignore", "pipe", "pipe"] },
    );
    t.after(() => {
      if (!child.killed) child.kill("SIGTERM");
    });
    const exited = new Promise((resolve, reject) => {
      child.once("error", reject);
      child.once("exit", (code, signal) => resolve({ code, signal }));
    });
    await new Promise((resolve, reject) => {
      child.stdout.once("data", resolve);
      child.once("error", reject);
      child.once("exit", () =>
        reject(new Error("launcher exited before ready")),
      );
    });
    child.kill("SIGTERM");
    assert.deepEqual(await exited, { code: null, signal: "SIGTERM" });
  },
);
