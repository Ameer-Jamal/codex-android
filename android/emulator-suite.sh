#!/usr/bin/env bash
# Only invoked by emulator-test.py on the dedicated disposable test AVD.
set -euo pipefail
version=$1
report_dir=$2
registry_args=()
if [[ -n ${4:-} ]]; then
  registry_args=("--registry=$4")
fi
# Keep the visible emulator useful while retaining a complete report.
exec > >(tee "$report_dir/report.txt") 2>&1
finish() {
  local result=$?
  printf '\nSUITE_EXIT=%s\n' "$result"
  printf '%s\n' "$result" >"$report_dir/exit.tmp"
  mv "$report_dir/exit.tmp" "$report_dir/exit.txt"
}
trap finish EXIT
export DEBIAN_FRONTEND=noninteractive
printf 'Android emulator release test: %s\n' "$version"
uname -m
getprop ro.build.version.release
printf 'API: '
getprop ro.build.version.sdk
printf 'Page size: '
/system/bin/getconf PAGESIZE
# Bootstrap has finished before the host injects this command.
apt_options=(-o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30)
apt-get "${apt_options[@]}" update
apt-get "${apt_options[@]}" install -y nodejs-lts
node --version
if [[ -n ${3:-} ]]; then
  npm install -g "npm@$3"
fi
npm --version
# This AVD is exclusively for package tests, not a user's environment.
npm uninstall -g codex-android
npm install -g --cache "$report_dir/npm-cache-first" "${registry_args[@]}" "codex-android@$version"
# Reject lifecycle hooks in the installed release, not just ignored execution.
node -e 'const p=require(process.argv[1]); for(const hook of ["preinstall","install","postinstall","prepare"]) if(p.scripts?.[hook]) throw new Error(`Unexpected npm hook: ${hook}`)' "$(npm root -g)/codex-android/package.json"
# Doctor runs before setup and must not create a settings directory or install tools.
if [[ -n ${4:-} ]]; then
  before_git=$(command -v git || true)
  before_rg=$(command -v rg || true)
  before_home=0
  [[ -d "$HOME/.codex-android" ]] && before_home=1
  doctor_status=0
  codex-android doctor --json > "$report_dir/doctor-before-setup.json" || doctor_status=$?
  [[ "$doctor_status" == 0 || "$doctor_status" == 1 ]]
  [[ "$(command -v git || true)" == "$before_git" ]]
  [[ "$(command -v rg || true)" == "$before_rg" ]]
  if [[ "$before_home" == 0 ]]; then test ! -d "$HOME/.codex-android"; fi
fi
# Exercise the actual npm-created command before any diagnostic can repair setup.
codex --version
if [[ -n ${4:-} ]]; then
  test -f "$HOME/.codex-android/AGENTS.md"
  export CODEX_ANDROID_EXPECT_INSTRUCTIONS=1
fi
codex-android doctor --json > "$report_dir/doctor.json"
node -e 'const r=require(process.argv[1]); if(r.formatVersion!==1 || r.exitCode!==0) process.exit(1)' "$report_dir/doctor.json"
bash "$report_dir/phone-test.sh" "$version"
if [[ -n ${4:-} ]]; then
  echo 'PASS: script-free installation completes setup on first launch'
else
  echo 'PASS: published release installs without lifecycle hooks'
fi

# Deterministic preservation test; no real account credentials are involved.
export CODEX_HOME="$HOME/.codex-android-emulator-test"
unset CODEX_ANDROID_USE_DAEMON
codex --version
printf 'preserve-settings\n' >"$CODEX_HOME/preservation-sentinel"
if [[ -n ${4:-} ]]; then
  printf 'User-owned Android instructions\n' >"$CODEX_HOME/AGENTS.md"
fi
npm uninstall -g codex-android
hash -r
if command -v codex >/dev/null 2>&1 || command -v codex-android >/dev/null 2>&1; then
  echo 'FAIL: codex command remained after uninstall'
  exit 1
fi
test "$(cat "$CODEX_HOME/preservation-sentinel")" = preserve-settings
npm install -g --cache "$report_dir/npm-cache-reinstall" "${registry_args[@]}" "codex-android@$version"
test "$(cat "$CODEX_HOME/preservation-sentinel")" = preserve-settings
codex-android doctor --json > "$report_dir/doctor.json"
node -e 'const r=require(process.argv[1]); if(r.formatVersion!==1 || r.exitCode!==0) process.exit(1)' "$report_dir/doctor.json"
if [[ -n ${4:-} ]]; then
  test "$(cat "$CODEX_HOME/AGENTS.md")" = 'User-owned Android instructions'
fi
bash "$report_dir/phone-test.sh" "$version"
for iteration in 1 2 3; do
  timeout --kill-after=5 30 codex --help >/dev/null
done
echo 'PASS: uninstall/reinstall preserves test settings; repeated startup works'
node "$report_dir/runtime-e2e.cjs"
echo 'No live model requests or login performed. Interactive/device lifecycle acceptance remains separate.'
