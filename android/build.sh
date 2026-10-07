#!/usr/bin/env bash
# Cross-build the Termux runtime with Android NDK r28c.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "$(uname -s):$(uname -m)" in
  Linux:x86_64) ndk_host=linux-x86_64 ;;
  Darwin:arm64 | Darwin:x86_64) ndk_host=darwin-x86_64 ;;
  *)
    echo "Android cross builds require Linux x86_64 or macOS (or the Android CI workflow)." >&2
    exit 1
    ;;
esac
: "${ANDROID_NDK_HOME:?Set ANDROID_NDK_HOME to Android NDK r28c (28.2.13676358)}"
if ! grep -qx 'Pkg.Revision = 28.2.13676358' "$ANDROID_NDK_HOME/source.properties"; then
  echo "Android builds require NDK r28c (28.2.13676358)." >&2
  exit 1
fi
ndk_toolchain="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/$ndk_host"
ndk_bin="$ndk_toolchain/bin"
test -x "$ndk_bin/aarch64-linux-android29-clang"
export PATH="$ndk_bin:$PATH"
export AR_aarch64_linux_android=llvm-ar
export CC_aarch64_linux_android=aarch64-linux-android29-clang
export CXX_aarch64_linux_android=aarch64-linux-android29-clang++
export RANLIB_aarch64_linux_android=llvm-ranlib
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$root/codex-rs/target}"
# Android's system libraries cannot satisfy host pkg-config packages.
export PKG_CONFIG_ALLOW_CROSS=1
export PKG_CONFIG_LIBDIR="$ndk_toolchain/sysroot/usr/lib/pkgconfig"
export CARGO_PROFILE_RELEASE_STRIP=symbols
export CARGO_PROFILE_RELEASE_DEBUG=0
export CARGO_PROFILE_RELEASE_CODEGEN_UNITS=16
cd "$root/codex-rs"
rustup target add aarch64-linux-android
python3 "$root/scripts/fetch_rusty_v8_android.py"
v8_version="$(python3 - "$root/codex-rs/Cargo.lock" <<'PY'
import sys, tomllib
with open(sys.argv[1], 'rb') as source:
    print(next(p['version'] for p in tomllib.load(source)['package'] if p['name'] == 'v8'))
PY
)"
v8_dir="$root/.artifacts/rusty_v8/rusty-v8-v$v8_version"
export RUSTY_V8_ARCHIVE="$v8_dir/librusty_v8_ptrcomp_sandbox_release_aarch64-linux-android.a.gz"
export RUSTY_V8_SRC_BINDING_PATH="$v8_dir/src_binding_ptrcomp_sandbox_release_aarch64-linux-android.rs"
python3 "$root/scripts/check_v8_sandbox.py" "$RUSTY_V8_ARCHIVE"
builtins="$(find "$ndk_toolchain" -name libclang_rt.builtins-aarch64-android.a -print -quit)"
: "${builtins:?NDK aarch64 compiler-rt builtins archive is missing}"
# With an explicit --target, Cargo applies these flags only to target artifacts.
# Encoded arguments preserve source/NDK paths containing spaces.
printf -v CARGO_ENCODED_RUSTFLAGS '%s\x1f' \
  '-Clink-arg=-lc++_shared' "-Clink-arg=-Wl,-rpath,\$ORIGIN" \
  "-Clink-arg=$builtins" "--remap-path-prefix=$root=/codex-android"
export CARGO_ENCODED_RUSTFLAGS="${CARGO_ENCODED_RUSTFLAGS%$'\x1f'}"
cargo build --locked --release --target aarch64-linux-android -p codex-cli -p codex-code-mode-host
python3 "$root/android/package.py" \
  --binary-dir "$CARGO_TARGET_DIR/aarch64-linux-android/release" \
  --ndk-root "$ANDROID_NDK_HOME" \
  --libcxx "$ndk_toolchain/sysroot/usr/lib/aarch64-linux-android/libc++_shared.so" \
  --output-dir "$root/dist/android"
