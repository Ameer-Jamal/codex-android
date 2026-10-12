#!/usr/bin/env bash
# Only invoked by emulator-test.py on the dedicated disposable test AVD.
set -euo pipefail
version=$1
report_dir=$2
registry_args=()
if [[ -n ${4:-} ]]; then
  registry_args=("--registry=$4")
fi
exec >"$report_dir/report.txt" 2>&1
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
apt-get update
apt-get install -y nodejs-lts
node --version
if [[ -n ${3:-} ]]; then
  npm install -g "npm@$3"
fi
npm --version
# This AVD is exclusively for package tests, not a user's environment.
npm uninstall -g codex-android
npm install -g --cache "$report_dir/npm-cache-first" --ignore-scripts "${registry_args[@]}" "codex-android@$version"
# Exercise the actual npm-created command before any diagnostic can repair setup.
codex --version
echo 'PASS: installation with scripts blocked recovers on first launch'
bash "$report_dir/phone-test.sh" "$version"

# Deterministic preservation test; no real account credentials are involved.
export CODEX_HOME="$HOME/.codex-android-emulator-test"
unset CODEX_ANDROID_USE_DAEMON
codex --version
printf 'preserve-settings\n' >"$CODEX_HOME/preservation-sentinel"
npm uninstall -g codex-android
hash -r
if command -v codex >/dev/null 2>&1; then
  echo 'FAIL: codex command remained after uninstall'
  exit 1
fi
test "$(cat "$CODEX_HOME/preservation-sentinel")" = preserve-settings
npm install -g --cache "$report_dir/npm-cache-reinstall" --allow-scripts=codex-android "${registry_args[@]}" "codex-android@$version"
test "$(cat "$CODEX_HOME/preservation-sentinel")" = preserve-settings
bash "$report_dir/phone-test.sh" "$version"
for iteration in 1 2 3; do
  timeout --kill-after=5 30 codex --help >/dev/null
done
echo 'PASS: uninstall/reinstall preserves test settings; repeated startup works'
node "$report_dir/runtime-e2e.cjs"
echo 'No live model requests or login performed. Interactive/device lifecycle acceptance remains separate.'
