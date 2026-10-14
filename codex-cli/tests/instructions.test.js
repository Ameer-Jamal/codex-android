import assert from "node:assert/strict";
import { test } from "node:test";
import {
  mkdtempSync,
  readFileSync,
  writeFileSync,
  rmSync,
  statSync,
  symlinkSync,
  mkdirSync,
  existsSync,
} from "node:fs";
import path from "node:path";
import os from "node:os";
import { seedAndroidInstructions } from "../lib/instructions.js";

function fixture(t) {
  const root = mkdtempSync(path.join(os.tmpdir(), "android-instructions-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const home = path.join(root, "home");
  mkdirSync(home);
  const source = path.join(root, "template.md");
  writeFileSync(source, "Android environment guidance\n");
  return { root, home, source };
}

test("seeds a private global file once and preserves edits on later launches", (t) => {
  const { home, source } = fixture(t);
  assert.equal(seedAndroidInstructions(home, source), "created");
  assert.equal(
    readFileSync(path.join(home, "AGENTS.md"), "utf8"),
    readFileSync(source, "utf8"),
  );
  assert.equal(statSync(path.join(home, "AGENTS.md")).mode & 0o777, 0o600);
  writeFileSync(path.join(home, "AGENTS.md"), "User preferences\n");
  writeFileSync(source, "New package template\n");
  assert.equal(seedAndroidInstructions(home, source), "preserved");
  assert.equal(
    readFileSync(path.join(home, "AGENTS.md"), "utf8"),
    "User preferences\n",
  );
});

test("preserves overrides, empty files and symlinks without following them", (t) => {
  for (const kind of ["override", "empty", "symlink", "directory"]) {
    const { root, home, source } = fixture(t);
    if (kind === "override")
      writeFileSync(path.join(home, "AGENTS.override.md"), "User override");
    if (kind === "empty") writeFileSync(path.join(home, "AGENTS.md"), "");
    if (kind === "directory") mkdirSync(path.join(home, "AGENTS.md"));
    if (kind === "symlink")
      symlinkSync(
        path.join(root, "absent-target"),
        path.join(home, "AGENTS.md"),
      );
    assert.equal(seedAndroidInstructions(home, source), "preserved");
    if (kind === "override")
      assert.equal(existsSync(path.join(home, "AGENTS.md")), false);
    if (kind === "empty")
      assert.equal(readFileSync(path.join(home, "AGENTS.md"), "utf8"), "");
    if (kind === "symlink")
      assert.equal(existsSync(path.join(root, "absent-target")), false);
  }
});

test("missing or oversized template never creates a partial instruction file", (t) => {
  const { home, source } = fixture(t);
  rmSync(source);
  assert.throws(() => seedAndroidInstructions(home, source));
  assert.equal(existsSync(path.join(home, "AGENTS.md")), false);
  writeFileSync(source, "a".repeat(4097));
  assert.throws(() => seedAndroidInstructions(home, source), /size limit/);
  assert.equal(existsSync(path.join(home, "AGENTS.md")), false);
});
