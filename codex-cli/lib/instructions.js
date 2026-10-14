import { lstatSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const template = fileURLToPath(
  new URL("../assets/AGENTS.android.md", import.meta.url),
);

// Seed once. An existing file, directory or symlink is always user-owned.
export function seedAndroidInstructions(home, source = template) {
  for (const name of ["AGENTS.override.md", "AGENTS.md"]) {
    try {
      lstatSync(path.join(home, name));
      return "preserved";
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
  }
  const contents = readFileSync(source, "utf8");
  if (Buffer.byteLength(contents, "utf8") > 4096) {
    throw new Error("Android instructions exceed the startup size limit");
  }
  try {
    writeFileSync(path.join(home, "AGENTS.md"), contents, {
      flag: "wx",
      mode: 0o600,
    });
    return "created";
  } catch (error) {
    if (error.code === "EEXIST") return "preserved";
    throw error;
  }
}
