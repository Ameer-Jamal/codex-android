"""Resolve a test version once, then keep the entire emulator run pinned to it."""

import json
import re
import urllib.request

from emulator_registry import read_manifest


def resolve_version(version=None, archive=None):
    if archive:
        detected = read_manifest(archive).get("version")
        if version and version != detected:
            raise ValueError("Candidate version does not match the requested version")
        version = detected
    elif version is None:
        with urllib.request.urlopen(
            "https://registry.npmjs.org/codex-android/latest", timeout=30
        ) as response:
            body = response.read(1024 * 1024 + 1)
        if len(body) > 1024 * 1024:
            raise ValueError("Registry metadata exceeded the size limit")
        metadata = json.loads(body)
        if metadata.get("name") != "codex-android":
            raise ValueError("Registry returned a different package")
        version = metadata.get("version")
    if not isinstance(version, str) or not re.fullmatch(
        r"\d+\.\d+\.\d+-android\.\d+", version
    ):
        raise ValueError("Expected an exact Android release version")
    return version
