"""Serve one built candidate as a private loopback npm registry for emulator tests."""

import hashlib
import json
import shutil
import tarfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class CandidateRegistry:
    def __init__(self, archive, version):
        with tarfile.open(archive, "r:gz") as package:
            manifest = json.load(package.extractfile("package/package.json"))
        if (
            manifest.get("name") != "codex-android"
            or manifest.get("version") != version
        ):
            raise ValueError("Candidate package name/version does not match the test")
        with archive.open("rb") as source:
            checksum = hashlib.file_digest(source, "sha1").hexdigest()
        tarball_path = f"/codex-android/-/codex-android-{version}.tgz"

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.split("?")[0] == tarball_path:
                    self.send_response(200)
                    self.send_header("Content-Length", str(archive.stat().st_size))
                    self.end_headers()
                    with archive.open("rb") as source:
                        shutil.copyfileobj(source, self.wfile)
                elif self.path.split("?")[0] == "/codex-android":
                    body = json.dumps(metadata).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_error(404)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_port
        self.url = f"http://127.0.0.1:{self.port}"
        manifest["dist"] = {"tarball": self.url + tarball_path, "shasum": checksum}
        metadata = {
            "name": "codex-android",
            "dist-tags": {"latest": version},
            "versions": {version: manifest},
        }
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
