import { existsSync as defaultExistsSync, promises as fs } from "node:fs";
import path from "node:path";
import { spawnSync as defaultSpawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const DEFAULT_TERMUX_PREFIX = "/data/data/com.termux/files/usr";
const DEFAULT_BIN_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "bin",
);
const LAUNCHERS = ["codex.js"];
const DEFAULT_SHEBANG = "#!/usr/bin/env node";
const TERMUX_ROOT = "/data/data/com.termux";

function isTermux(env, platform) {
  return (
    Boolean(env.TERMUX_VERSION) ||
    env.PREFIX === DEFAULT_TERMUX_PREFIX ||
    platform === "android"
  );
}

function validatedTermuxPrefix(rawPrefix, warn) {
  if (!rawPrefix) {
    return DEFAULT_TERMUX_PREFIX;
  }

  const normalized =
    typeof rawPrefix === "string" ? path.posix.normalize(rawPrefix) : "";
  const hasParentSegment =
    typeof rawPrefix === "string" && rawPrefix.split("/").includes("..");
  const isAllowed =
    typeof rawPrefix === "string" &&
    path.posix.isAbsolute(rawPrefix) &&
    !/\s/.test(rawPrefix) &&
    !hasParentSegment &&
    (normalized === TERMUX_ROOT || normalized.startsWith(`${TERMUX_ROOT}/`));

  if (!isAllowed) {
    warn("Warning: invalid Termux PREFIX; using the default Termux prefix.");
    return DEFAULT_TERMUX_PREFIX;
  }

  return normalized;
}

async function fixLauncherShebang(filePath, prefix, warn) {
  try {
    const contents = await fs.readFile(filePath, "utf8");
    const newlineIndex = contents.indexOf("\n");
    const firstLineEnd = newlineIndex === -1 ? contents.length : newlineIndex;
    const hasCarriageReturn =
      newlineIndex > 0 && contents[newlineIndex - 1] === "\r";
    const firstLine = contents.slice(
      0,
      hasCarriageReturn ? firstLineEnd - 1 : firstLineEnd,
    );

    if (firstLine !== DEFAULT_SHEBANG) {
      return;
    }

    const replacement = `#!${prefix}/bin/env node`;
    const lineEnding =
      newlineIndex === -1 ? "" : hasCarriageReturn ? "\r\n" : "\n";
    const rest = newlineIndex === -1 ? "" : contents.slice(newlineIndex + 1);
    await fs.writeFile(filePath, `${replacement}${lineEnding}${rest}`);
  } catch (error) {
    warn(`Warning: unable to fix shebang in ${filePath}: ${error.message}`);
  }
}

export async function runPostinstall({
  binDir = DEFAULT_BIN_DIR,
  env = process.env,
  platform = process.platform,
  warn = console.warn,
  existsSync = defaultExistsSync,
  spawnSync = defaultSpawnSync,
  log = console.log,
} = {}) {
  if (!isTermux(env, platform)) {
    return;
  }

  const prefix = validatedTermuxPrefix(env.PREFIX, warn);
  const envPath = path.posix.join(prefix, "bin", "env");
  try {
    if (!existsSync(envPath)) {
      warn(
        `Warning: ${envPath} does not exist; launcher shebangs were left unchanged.`,
      );
      return;
    }
  } catch (error) {
    warn(
      `Warning: unable to check ${envPath}; launcher shebangs were left unchanged: ${error.message}`,
    );
    return;
  }

  const dependencies = [
    ["git", "bin/git"],
    ["ripgrep", "bin/rg"],
    ["termux-tools", "bin/termux-open-url"],
    ["ca-certificates", "etc/tls/cert.pem"],
  ];
  const missing = dependencies
    .filter(([, file]) => !existsSync(path.join(prefix, file)))
    .map(([name]) => name);
  if (missing.length) {
    log(`Installing missing Termux dependencies: ${missing.join(", ")}`);
    const result = spawnSync(
      path.join(prefix, "bin/pkg"),
      ["install", "-y", ...missing],
      {
        stdio: "inherit",
        env,
      },
    );
    if (result.error || result.status !== 0) {
      throw new Error(
        `Termux dependency setup failed. Run pkg install ${missing.join(" ")} and reinstall codex-android.`,
        { cause: result.error },
      );
    }
    const unavailable = dependencies
      .filter(([, file]) => !existsSync(path.join(prefix, file)))
      .map(([name]) => name);
    if (unavailable.length) {
      throw new Error(
        `Termux dependencies are still missing: ${unavailable.join(", ")}`,
      );
    }
  }

  for (const launcher of LAUNCHERS) {
    await fixLauncherShebang(path.join(binDir, launcher), prefix, warn);
  }
}

const scriptPath = fileURLToPath(import.meta.url);
if (process.argv[1] && path.resolve(process.argv[1]) === scriptPath) {
  await runPostinstall();
}
