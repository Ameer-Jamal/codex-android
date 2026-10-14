#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build/classes build/dex
java -version
javac -version
aapt2 version
apksigner version
javac --release 8 -classpath tools/android.jar -d build/classes src/MainActivity.java
mapfile -t classes < <(find build/classes -name '*.class')
java -cp tools/d8.jar com.android.tools.r8.D8 --lib tools/android.jar --min-api 26 --output build/dex "${classes[@]}"
aapt2 link -I tools/android.jar --manifest AndroidManifest.xml -o build/resources.apk
cp build/resources.apk build/unsigned.apk
(cd build/dex && zip -q -j ../unsigned.apk classes.dex)
zipalign -f 4 build/unsigned.apk build/aligned.apk
if [[ ! -f debug.keystore ]]; then
  keytool -genkeypair -keystore debug.keystore -storepass android -keypass android -alias androiddebugkey -dname 'CN=Android Debug,O=Codex Android Demo,C=US' -keyalg RSA -keysize 2048 -validity 3650
fi
apksigner sign --ks debug.keystore --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out build/hello-world.apk build/aligned.apk
apksigner verify --verbose build/hello-world.apk
zipalign -c 4 build/hello-world.apk
sha256sum build/hello-world.apk
