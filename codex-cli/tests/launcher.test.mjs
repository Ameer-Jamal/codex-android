import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import {
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  statSync,
  readFileSync,
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
    "if (!(await import('node:fs')).statSync(process.env.CODEX_HOME).isDirectory()) process.exit(99); console.log(JSON.stringify({args:process.argv.slice(2),home:process.env.CODEX_HOME})); process.exit(23);",
  );
  const home = path.join(root, "private-home");
  const result = spawnSync(
    process.execPath,
    ["--import", androidPlatform, launcher, "exec", "a prompt with spaces"],
    { encoding: "utf8", env: { ...process.env, CODEX_HOME: home } },
  );
  assert.equal(result.status, 23, result.stderr);
  assert.equal(statSync(home).mode & 0o777, 0o700);
  assert.deepEqual(JSON.parse(result.stdout), {
    args: ["--no-daemon", "exec", "a prompt with spaces"],
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
    const { root, launcher } = fixture(
      t,
      'console.log("ready"); setInterval(() => {}, 1000);',
    );
    const child = spawn(
      process.execPath,
      ["--import", androidPlatform, launcher],
      {
        stdio: ["ignore", "pipe", "pipe"],
        env: { ...process.env, CODEX_HOME: path.join(root, "home") },
      },
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

test("first launch creates the default home and preserves it on later launches", (t) => {
  const { root, launcher } = fixture(
    t,
    "console.log(process.env.CODEX_HOME); if (!(await import('node:fs')).statSync(process.env.CODEX_HOME).isDirectory()) process.exit(99);",
  );
  const env = { ...process.env, HOME: root };
  delete env.CODEX_HOME;
  const home = path.join(root, ".codex-android");
  const run = () =>
    spawnSync(process.execPath, ["--import", androidPlatform, launcher], {
      encoding: "utf8",
      env,
    });
  const first = run();
  assert.equal(first.status, 0, first.stderr);
  assert.equal(first.stdout.trim(), home);
  assert.equal(statSync(home).mode & 0o777, 0o700);
  writeFileSync(path.join(home, "config.toml"), "keep my settings");
  assert.equal(run().status, 0);
  assert.equal(
    readFileSync(path.join(home, "config.toml"), "utf8"),
    "keep my settings",
  );
});

test("home creation failure stops before launching Codex", (t) => {
  const { root, launcher } = fixture(t, 'console.log("must not run");');
  const home = path.join(root, "file");
  writeFileSync(home, "existing file");
  const result = spawnSync(
    process.execPath,
    ["--import", androidPlatform, launcher],
    {
      encoding: "utf8",
      env: { ...process.env, CODEX_HOME: home },
    },
  );
  assert.equal(result.status, 1);
  assert.equal(result.stdout, "");
  assert.match(result.stderr, /Unable to create Codex home/);
  assert.equal(readFileSync(home, "utf8"), "existing file");
});

test("Android uses the embedded server by default and preserves explicit daemon opt-in", async (t) => {
  const { root, launcher } = fixture(
    t,
    "console.log(JSON.stringify(process.argv.slice(2)));",
  );
  for (const { args, daemon, expected } of [
    { args: [], expected: ["--no-daemon"] },
    {
      args: ["resume", "--last"],
      expected: ["--no-daemon", "resume", "--last"],
    },
    {
      args: ["fork", "session-id"],
      expected: ["--no-daemon", "fork", "session-id"],
    },
    { args: ["--", "a prompt"], expected: ["--no-daemon", "--", "a prompt"] },
    {
      args: ["--", "--no-daemon"],
      expected: ["--no-daemon", "--", "--no-daemon"],
    },
    { args: ["--no-daemon", "resume"], expected: ["--no-daemon", "resume"] },
    {
      args: ["login", "--device-auth"],
      expected: ["--no-daemon", "login", "--device-auth"],
    },
    {
      args: ["app-server", "daemon", "status"],
      daemon: "1",
      expected: ["app-server", "daemon", "status"],
    },
    {
      args: ["--remote", "ws://localhost:9000"],
      daemon: "1",
      expected: ["--remote", "ws://localhost:9000"],
    },
  ]) {
    await t.test(
      JSON.stringify(args) + (daemon ? " opt-in" : " default"),
      () => {
        const env = { ...process.env, CODEX_HOME: path.join(root, "home") };
        delete env.CODEX_ANDROID_USE_DAEMON;
        if (daemon) env.CODEX_ANDROID_USE_DAEMON = daemon;
        const result = spawnSync(
          process.execPath,
          ["--import", androidPlatform, launcher, ...args],
          { encoding: "utf8", env },
        );
        assert.equal(result.status, 0, result.stderr);
        assert.deepEqual(JSON.parse(result.stdout), expected);
      },
    );
  }
});
