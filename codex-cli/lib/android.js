import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

export function sharedStorage(cwd, realpath = fs.realpathSync) {
  try {
    const resolved = realpath(cwd);
    return ["/sdcard", "/storage", "/mnt/media_rw", "/mnt/runtime"].some(
      (root) => resolved === root || resolved.startsWith(`${root}/`),
    );
  } catch {
    return false;
  }
}

export function storageWarning(args, tty, shared) {
  if (
    !tty ||
    !shared ||
    args.some((arg) => ["--help", "-h", "--version", "-V"].includes(arg))
  )
    return false;
  const commands = [
    "review",
    "remote-control",
    "exec",
    "e",
    "login",
    "logout",
    "app-server",
    "debug",
    "completion",
    "mcp",
    "mcp-server",
    "features",
    "sandbox",
    "apply",
  ];
  const delimiter = args.indexOf("--");
  const options = delimiter === -1 ? args : args.slice(0, delimiter);
  return !options.some((arg) => commands.includes(arg));
}

export function collectDoctor({
  root,
  platform = process.platform,
  arch = process.arch,
  node = process.versions.node,
  env = process.env,
  cwd = process.cwd(),
  exists = fs.existsSync,
  access = fs.accessSync,
  realpath = fs.realpathSync,
  run = spawnSync,
} = {}) {
  const checks = [];
  const add = (id, status, detail, recovery = "") =>
    checks.push({ id, status, detail, recovery });
  add(
    "platform",
    platform === "android" && arch === "arm64" ? "pass" : "fail",
    `${platform}/${arch}`,
    "Use ARM64 Termux on Android.",
  );
  add(
    "node",
    Number(node.split(".")[0]) >= 22 ? "pass" : "fail",
    node,
    "pkg install nodejs-lts",
  );
  const prefix = "/data/data/com.termux/files/usr";
  const bounded = (command, args) => {
    try {
      return run(command, args, {
        encoding: "utf8",
        timeout: 5000,
        killSignal: "SIGKILL",
        maxBuffer: 65536,
        env,
      });
    } catch {
      return { status: null };
    }
  };
  for (const [pkg, file] of [
    ["git", "bin/git"],
    ["ripgrep", "bin/rg"],
    ["termux-tools", "bin/termux-open-url"],
    ["ca-certificates", "etc/tls/cert.pem"],
  ]) {
    let available = false;
    try {
      access(
        path.join(prefix, file),
        file.startsWith("bin/") ? fs.constants.X_OK : fs.constants.R_OK,
      );
      available = true;
    } catch {
      /* Missing or inaccessible dependency. */
    }
    add(
      pkg,
      available ? "pass" : "fail",
      available ? "Available" : "Missing or inaccessible",
      `pkg install ${pkg}`,
    );
  }
  let manifest;
  try {
    manifest = JSON.parse(
      fs.readFileSync(path.join(root, "package.json"), "utf8"),
    );
  } catch {
    manifest = {};
  }
  add(
    "package",
    manifest.name === "codex-android" ? "pass" : "fail",
    manifest.version || "Unavailable",
    "npm i -g codex-android",
  );
  const binary = path.join(root, "vendor/aarch64-linux-android/bin/codex");
  // Call the native binary directly: the normal launcher can install dependencies.
  const native =
    platform === "android" && arch === "arm64" && exists(binary)
      ? bounded(binary, ["--version"])
      : { status: null };
  const version =
    native.status === 0
      ? native.stdout
          ?.trim()
          .match(/^codex(?:-cli)? ([0-9]+\.[0-9]+\.[0-9]+)$/)?.[1]
      : undefined;
  add(
    "native",
    version ? "pass" : "fail",
    version || "Missing, failed or timed out",
    "npm i -g codex-android",
  );
  const page = bounded("/system/bin/getconf", ["PAGESIZE"]);
  const size = page.status === 0 ? page.stdout?.trim() : "";
  add(
    "page-size",
    size === "4096" ? "pass" : "warn",
    size === "16384"
      ? "16384; compatibility unverified"
      : size === "4096"
        ? "4096"
        : "Unknown",
  );
  const executable = (env.PATH || "")
    .split(path.delimiter)
    .map((dir) => path.join(dir, "codex"))
    .find((file) => {
      try {
        fs.accessSync(file, fs.constants.X_OK);
        return true;
      } catch {
        return false;
      }
    });
  let matches = false;
  try {
    matches =
      realpath(executable) === realpath(path.join(root, "bin/codex.js"));
  } catch {
    /* Missing PATH entry. */
  }
  add(
    "path",
    matches ? "pass" : "fail",
    matches
      ? "This package is on PATH"
      : "Missing or conflicting codex executable",
    "Run type codex in your terminal; remove old aliases or conflicting installations.",
  );
  add(
    "workspace",
    sharedStorage(cwd, realpath) ? "warn" : "pass",
    sharedStorage(cwd, realpath)
      ? "Shared storage limits executable files, symlinks and permissions"
      : "Private or other filesystem",
    "Keep development projects under ~/.",
  );
  let accessible = false;
  try {
    fs.accessSync(
      path.join(env.HOME || "", "storage/shared"),
      fs.constants.R_OK,
    );
    accessible = true;
  } catch {
    /* Optional permission. */
  }
  add(
    "shared-storage",
    accessible ? "pass" : "warn",
    accessible ? "Accessible" : "Not configured or inaccessible",
    "codex-android setup storage",
  );
  return {
    formatVersion: 1,
    checks,
    exitCode: checks.some((check) => check.status === "fail") ? 1 : 0,
  };
}

export function renderDoctor(report) {
  return [
    "## Codex for Android diagnostics",
    "",
    ...report.checks.map(
      (c) =>
        `- ${c.status.toUpperCase()} ${c.id}: ${c.detail}${c.status !== "pass" && c.recovery ? ` — ${c.recovery}` : ""}`,
    ),
    "",
    "Run `type codex` in your own terminal to check shell aliases.",
    "These checks do not prove login, interactive approvals or physical-device acceptance.",
  ].join("\n");
}

export function setupStorage({
  run = spawnSync,
  accessible = () => {
    try {
      fs.accessSync(
        path.join(process.env.HOME || "", "storage/shared"),
        fs.constants.R_OK,
      );
      return true;
    } catch {
      return false;
    }
  },
  log = console.log,
} = {}) {
  log(
    "Requesting Termux shared-storage access. Grant permission in Android if prompted. This does not grant unrestricted phone access.",
  );
  let result;
  try {
    result = run("termux-setup-storage", [], {
      stdio: "inherit",
      timeout: 60000,
      killSignal: "SIGKILL",
    });
  } catch {
    result = { status: null };
  }
  if (result.status !== 0) {
    log(
      "Storage setup failed or timed out. Check Termux permissions, then run codex-android setup storage again.",
    );
    return 1;
  }
  if (!accessible()) {
    log(
      "Shared storage is not accessible yet. Finish the Android permission prompt, then rerun codex-android setup storage.",
    );
    return 1;
  }
  log(
    "Shared storage is accessible at ~/storage/shared. Keep development projects under ~/.",
  );
  return 0;
}
