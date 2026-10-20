import { existsSync as defaultExistsSync } from "node:fs";
import path from "node:path";
import { spawnSync as defaultSpawnSync } from "node:child_process";

const DEFAULT_TERMUX_PREFIX = "/data/data/com.termux/files/usr";
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

export async function ensureTermuxDependencies({
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
        `Termux dependency setup failed. Run pkg install ${missing.join(" ")}, then run codex again.`,
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
}
