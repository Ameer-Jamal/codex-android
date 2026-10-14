#!/usr/bin/env node
import path from "node:path";
import { fileURLToPath } from "node:url";
import { collectDoctor, renderDoctor, setupStorage } from "../lib/android.js";
const args = process.argv.slice(2);
const usage =
  "Usage: codex-android doctor [--json]\n       codex-android setup storage";
if (
  args[0] === "doctor" &&
  (args.length === 1 || (args.length === 2 && args[1] === "--json"))
) {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const report = collectDoctor({ root });
  console.log(
    args[1] === "--json"
      ? JSON.stringify(report, null, 2)
      : renderDoctor(report),
  );
  process.exitCode = report.exitCode;
} else if (args.join(" ") === "setup storage") {
  if (process.platform !== "android" || process.arch !== "arm64") {
    console.error("Storage setup requires ARM64 Termux on Android.");
    process.exitCode = 1;
  } else process.exitCode = setupStorage();
} else {
  console.error(usage);
  process.exitCode =
    args.length === 1 && ["--help", "-h"].includes(args[0]) ? 0 : 2;
}
