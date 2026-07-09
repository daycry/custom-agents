#!/usr/bin/env python3
"""Select the best GitHub release asset URL for a given OS/arch.

Usage:  gh_release_json | pick_asset.py <os> <arch> [--raw]
  os:   linux | darwin | windows
  arch: amd64 | arm64
  --raw: the asset IS the binary (no .zip/.tar.gz), e.g. hadolint.
Reads the release JSON from stdin, prints the chosen browser_download_url.
Exit 2 if no suitable asset is found. Tolerant of the varied naming schemes
used across projects (amd64/x86_64/x64/64bit, darwin/macOS/osx, .zip/.tar.gz).
"""
import sys
import json
import re

OS_TOKENS = {
    "linux": ["linux"],
    "darwin": ["darwin", "macos", "osx", "apple", "mac"],
    "windows": ["windows", "win"],
}
ARCH_TOKENS = {
    "amd64": ["amd64", "x86_64", "x64", "64bit", "64-bit"],
    "arm64": ["arm64", "aarch64"],
}
# Extensiones que NUNCA son el binario (para el modo --raw).
BAD_RAW = (".sig", ".pem", ".asc", ".sha256", ".sha256sum", ".sbom",
           ".txt", ".json", ".deb", ".rpm", ".apk", ".spdx", ".cyclonedx")


def has_token(name, token):
    return re.search(r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])", name) is not None


def score(name, os_name, arch, raw=False):
    n = name.lower()
    if not any(t in n for t in OS_TOKENS[os_name]):
        return -1
    if not any(has_token(n, t) for t in ARCH_TOKENS[arch]):
        return -1
    is_archive = n.endswith(".zip") or n.endswith(".tar.gz") or n.endswith(".tgz")
    if not raw:
        if not is_archive:
            return -1
    else:
        if is_archive:
            return -1
        if any(n.endswith(b) for b in BAD_RAW):
            return -1
    s = 0
    if any(has_token(n, t) for t in ("amd64", "x86_64", "x64", "64bit", "64-bit")) and arch == "amd64":
        s += 2
    if not raw and os_name == "windows" and n.endswith(".zip"):
        s += 1
    if not raw and os_name != "windows" and (n.endswith(".tar.gz") or n.endswith(".tgz")):
        s += 1
    if raw and os_name == "windows" and n.endswith(".exe"):
        s += 1
    if "sdk" in n or "docs" in n:
        s -= 5
    return s


def main():
    args = [a for a in sys.argv[1:] if a != "--raw"]
    raw = "--raw" in sys.argv[1:]
    if len(args) < 2:
        sys.exit("usage: pick_asset.py <os> <arch> [--raw]")
    os_name, arch = args[0], args[1]
    if os_name not in OS_TOKENS or arch not in ARCH_TOKENS:
        sys.exit("unsupported os/arch: %s/%s" % (os_name, arch))
    try:
        data = json.load(sys.stdin)
    except Exception as e:  # noqa: BLE001
        sys.exit("bad json: %s" % e)
    best, best_score = None, -1
    for a in data.get("assets", []):
        sc = score(a.get("name", ""), os_name, arch, raw)
        if sc > best_score:
            best_score, best = sc, a
    if best and best_score >= 0:
        print(best["browser_download_url"])
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
