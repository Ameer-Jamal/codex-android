#!/usr/bin/env bash
# Run on the phone after installing a release. No model requests or user-data reset.
set -u

if [[ $# -gt 1 || ${1:-} == --help ]]; then
  echo 'Usage: bash phone-test.sh [expected-npm-version]'
  echo 'Checks the global installation in a temporary workspace; makes no model requests.'
  exit 0
fi
expected=${1:-}
failures=0
pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failures=$((failures + 1)); }

printf 'Codex for Android — phone checks\n\n'
for tool in node npm bash timeout mktemp; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    fail "Missing $tool. Install Node.js and Termux coreutils before testing."
  fi
done
if (( failures )); then exit 1; fi

if node -e 'process.exit(process.platform === "android" && process.arch === "arm64" && Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
  pass 'ARM64 Android with Node.js 22+'
else
  fail 'Requires ARM64 Android with Node.js 22+ (standard Termux).'
  exit 1
fi

for tool in git rg termux-open-url; do
  if command -v "$tool" >/dev/null 2>&1; then
    pass "$tool available"
  else
    fail "Missing $tool. Run codex once to complete setup, then retry."
  fi
done

if ! global_root=$(timeout 30 npm root -g 2>/dev/null); then
  fail 'Cannot locate global npm installation.'
  exit 1
fi
package="$global_root/codex-android"
if ! version=$(node -e 'const p = require(process.argv[1]); if (p.name !== "codex-android") process.exit(1); console.log(p.version)' "$package/package.json" 2>/dev/null); then
  fail 'codex-android is not installed globally. Install with npm install -g codex-android.'
  exit 1
fi
printf 'Installed npm release: %s\n' "$version"
if [[ -n "$expected" && "$version" != "$expected" ]]; then
  fail "Expected $expected; installed $version."
else
  pass 'Package version'
fi

launcher=$(type -P codex || true)
if [[ -z "$launcher" ]] || ! node -e 'const fs = require("fs"); process.exit(fs.realpathSync(process.argv[1]) === fs.realpathSync(process.argv[2]) ? 0 : 1)' "$launcher" "$package/bin/codex.js" 2>/dev/null; then
  fail 'The codex command on PATH does not point to this package.'
  exit 1
fi
pass 'codex on PATH points to codex-android'
echo 'Also run type codex in your normal terminal: this script cannot see its aliases.'

work=$(mktemp -d "${TMPDIR:-$HOME}/codex-phone-test.XXXXXX") || exit 1
trap 'rm -rf -- "$work"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
# Use a nonexistent home to exercise automatic creation. Never read real auth/config.
export CODEX_HOME="$work/home"
unset CODEX_ANDROID_USE_DAEMON
mkdir "$work/project" || exit 1
cd "$work/project" || exit 1

check_cli() {
  local label=$1
  shift
  if timeout --kill-after=5 30 "$launcher" "$@" >"$work/output" 2>&1; then
    pass "$label"
  else
    fail "$label (failed or timed out)."
    # Do not dump logs: diagnostics should not inadvertently expose private data.
  fi
}
check_cli 'Native runtime starts' --version
check_cli 'Plain launcher help' --help
check_cli 'Embedded-mode option parsing' --no-daemon --help
check_cli 'Exec help' exec --help
check_cli 'Resume help' resume --help
check_cli 'Fork help' fork --help
check_cli 'Login help' login --help
# Exercise native configuration loading, not just argument parsing. A fresh home
# has no stored login; expected exit 1 is a successful diagnostic here.
timeout --kill-after=5 30 "$launcher" login status >"$work/output" 2>&1
login_result=$?
if [[ "$login_result" == 1 ]] && rg -q '^Not logged in$' "$work/output"; then
  pass 'Fresh-home configuration loads without stored credentials'
else
  fail 'Fresh-home login status failed unexpectedly (no login is required).'
fi
if [[ -d "$CODEX_HOME" ]] && node -e 'const fs = require("fs"); process.exit((fs.statSync(process.argv[1]).mode & 0o777) === 0o700 ? 0 : 1)' "$CODEX_HOME"; then
  pass 'First launch creates a private Codex home'
else
  fail 'First launch did not create a home with permissions 0700.'
fi

if printf 'phone-test\n' > sample.txt && bash -c 'test "$(cat sample.txt)" = phone-test' && git init -q && rg -q '^phone-test$' sample.txt; then
  pass 'Termux workspace: file write/read, shell, Git and ripgrep'
else
  fail 'Termux workspace tools failed.'
fi

printf '\nAutomatic checks: %s failure(s).\n' "$failures"
cat <<'CHECKLIST'
These checks do not prove interactive sessions or agent tool execution work.
In your normal terminal, using a disposable project, verify:
  [ ] type codex shows no old alias; plain codex opens without a socket error
  [ ] login works; Codex can read/edit a file and run a project command
  [ ] required command approvals work, including declining an approval
  [ ] keyboard, scrolling, rotation, Ctrl-C and exit work
  [ ] codex resume restores a session after exit
  [ ] screen lock / switching apps / lost network recover sensibly
  [ ] upgrading and reinstalling preserve login, settings and conversations
Model-assisted checks above are manual and may use your account's allowance.
A clean Termux device/profile is still needed to test missing-dependency setup.
No saved sessions, login files or installed packages were removed by this script.
CHECKLIST
(( failures == 0 ))
