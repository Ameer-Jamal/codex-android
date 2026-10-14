#!/data/data/com.termux/files/usr/bin/bash
# This fixture builds locally without invoking Codex or any model.
set -euo pipefail
transport=$1
run_id=$2
project="$HOME/codex-app-e2e-$run_id"
mkdir "$project"
mkdir -p "$project/tools" "$project/src" "$project/build/classes" "$project/build/dex"
cp "$transport/MainActivity.java" "$project/src/"
cp "$transport/AndroidManifest.xml" "$project/"
cp "$transport/android.jar" "$transport/d8.jar" "$project/tools/"
cp "$transport/rebuild.sh" "$project/"
printf '%s\n' "$project" > "$transport/project-path.txt"
exec > >(tee "$project/build.log" "$transport/build.log") 2>&1
finish() { result=$?; printf '%s\n' "$result" > "$transport/exit.txt"; }
trap finish EXIT
uname -sm
id
if ! command -v javac >/dev/null; then pkg install -y openjdk-21; fi
# Native packaging tools need the repository's matching C++ runtime, including
# when an older Termux bootstrap already provided libc++.
pkg install -y libc++
missing=()
for pair in 'aapt2:aapt2' 'apksigner:apksigner' 'zip:zip' 'zipalign:aapt'; do
  tool=${pair%%:*}
  package=${pair#*:}
  if ! command -v "$tool" >/dev/null; then missing+=("$package"); fi
done
if (( ${#missing[@]} )); then pkg install -y "${missing[@]}"; fi
cd "$project"
bash ./rebuild.sh
cp build/hello-world.apk "$transport/hello-world.apk"
sha256sum build/hello-world.apk > "$transport/sha256.txt"
echo BUILD_SUCCEEDED_ON_PHONE
