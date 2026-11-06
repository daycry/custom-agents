#!/usr/bin/env python3
"""Explicit, optional installs from reviewed pins, outside project repositories.

Integrity is anchored in the installed plugin, not in runtime checksum discovery.
No downloaded executable is run for verification. Locks protect cooperating writers,
not an adversary concurrently replacing directories with the same account.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

HERE = Path(__file__).resolve().parent
MAX_DOWNLOAD = 256 * 1024 * 1024
MAX_FILES = 20000
MAX_METADATA = 4 * 1024 * 1024

def require(value, code):
    if not value:
        raise ValueError(code)

def guard(deadline):
    require(time.monotonic() < deadline, "deadline")

def shared(name):
    path = HERE.parents[1] / "shared" / (name + ".py")
    spec = importlib.util.spec_from_file_location("nemesis_" + name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

READER = shared("local-read")
STATE = shared("local-state")
IO = STATE.StateIO(READER, require, guard, maximum=MAX_DOWNLOAD)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")

def read_catalog():
    raw, _ = IO.read(HERE / "tools-lock.json", MAX_METADATA)
    catalog = json.loads(raw)
    require(catalog.get("schema_version") == 1 and type(catalog.get("tools")) is dict, "catalog_schema")
    for name, tool in catalog["tools"].items():
        require(re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name), "catalog_name")
        require(tool.get("kind") in ("binary", "source", "python"), "catalog_kind")
    return catalog

def platform_key():
    systems = {"Linux":"linux", "Darwin":"darwin", "Windows":"windows"}
    arches = {"x86_64":"amd64", "amd64":"amd64", "aarch64":"arm64", "arm64":"arm64"}
    system = systems.get(platform.system())
    arch = arches.get(platform.machine().lower())
    require(system and arch, "unsupported_platform")
    return system + "-" + arch

def allowed_url(url):
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    require(parsed.scheme == "https" and not parsed.username and not parsed.password
            and parsed.port in (None, 443), "download_origin")
    require(host in ("github.com", "codeload.github.com", "pypi.org", "files.pythonhosted.org")
            or host.endswith(".githubusercontent.com"), "download_origin")

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def download(url):
    allowed_url(url)
    deadline = time.monotonic() + 120
    request = urllib.request.Request(url, headers={"User-Agent":"custom-agents-pinned-tools"})
    opener = urllib.request.build_opener(SafeRedirect())
    data = bytearray()
    with opener.open(request, timeout=30) as response:
        allowed_url(response.geturl())
        while True:
            guard(deadline)
            block = response.read(min(65536, MAX_DOWNLOAD + 1 - len(data)))
            if not block:
                break
            data.extend(block)
            require(len(data) <= MAX_DOWNLOAD, "download_budget")
    return bytes(data)

def safe_name(name):
    require(type(name) is str and name and "\\" not in name and ":" not in name
            and not any(ord(c) < 32 for c in name), "archive_path")
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts and bool(path.parts), "archive_path")
    # Avoid Windows device aliases, trailing-dot aliases and case collisions on all OSes.
    for part in path.parts:
        require(part.rstrip(" .") == part and not re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part), "archive_path")
    return path.as_posix()

def unpack(raw, kind):
    """Return bounded regular-file bytes; never delegate archive extraction to a shell."""
    files, seen, total = {}, set(), 0
    deadline = time.monotonic() + 120
    def add(name, size, mode, is_dir, read):
        nonlocal total
        guard(deadline)
        name = safe_name(name)
        require(name.casefold() not in seen and len(seen) < MAX_FILES, "archive_duplicates")
        seen.add(name.casefold())
        require(0 <= size <= MAX_DOWNLOAD, "archive_budget")
        total += size
        require(total <= MAX_DOWNLOAD, "archive_budget")
        if not is_dir:
            content = read(size + 1)
            require(len(content) == size, "archive_size")
            files[name] = (content, 0o700 if mode & 0o111 else 0o600)
    if kind == "zip":
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            require(len(archive.infolist()) <= MAX_FILES, "archive_budget")
            for member in archive.infolist():
                mode = member.external_attr >> 16
                require(not stat.S_ISLNK(mode) and stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR), "archive_type")
                with archive.open(member) as stream:
                    add(member.filename, member.file_size, mode, member.is_dir(), stream.read)
    elif kind == "tar.gz":
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            for member in archive:
                require(member.isfile() or member.isdir(), "archive_type")
                if member.isdir():
                    add(member.name, 0, member.mode, True, lambda n:b"")
                else:
                    with archive.extractfile(member) as stream:
                        add(member.name, member.size, member.mode, False, stream.read)
    else:
        raise ValueError("archive_format")
    require(files, "archive_empty")
    return files

def directory(path):
    if not path.exists() and not path.is_symlink():
        directory(path.parent)
        path.mkdir(mode=0o700)
    IO.dirs(path)

def shell_path(path):
    # MSYS bash accepts C:/ paths; backslashes would be interpreted by bash.
    return str(path).replace("\\", "/")

def shim(argv):
    return ("#!/usr/bin/env bash\nexec " + " ".join(shlex.quote(str(a)) for a in argv) + ' "$@"\n').encode("utf-8")

class Installer:
    def __init__(self, root, catalog, *, target=None, fetch=download, run=subprocess.run):
        self.root = STATE.physical_system_path(Path(os.path.abspath(os.path.expanduser(root))))
        self.catalog, self.target, self.fetch, self.run = catalog, target or platform_key(), fetch, run
        self.deadline = time.monotonic() + 1200
        self.receipt = self.root / "installed-v1.json"
        self.bin, self.vendor = self.root / "bin", self.root / "vendor"

    def prepare(self):
        # Validate before creating anything. A .git file also marks a worktree.
        for path in [*reversed(self.root.parents), self.root]:
            require(not (path / ".git").exists(), "project_install_root")
            if path.exists() or path.is_symlink():
                IO.dirs(path)
        directory(self.root)
        require(os.name == "nt" or not (self.root.stat().st_mode & 0o022), "writable_install_root")
        directory(self.bin)
        directory(self.vendor)
        ignored = self.root / ".gitignore"
        if not ignored.exists():
            IO.write(ignored, b"*\n", self.deadline, mode=0o600)

    def state(self):
        if not self.receipt.exists():
            return {"schema_version":1, "tools":{}}, None
        raw, identity = IO.read(self.receipt, MAX_METADATA)
        value = json.loads(raw)
        require(value.get("schema_version") == 1 and type(value.get("tools")) is dict, "receipt_schema")
        return value, identity

    def inventory(self, base):
        result, total = {}, 0
        IO.dirs(base)
        for current, dirs, names in os.walk(base, followlinks=False):
            guard(self.deadline)
            IO.dirs(Path(current))
            for name in dirs:
                IO.dirs(Path(current) / name)
            for name in names:
                path = Path(current) / name
                raw, _ = IO.read(path, MAX_DOWNLOAD)
                total += len(raw)
                require(len(result) < MAX_FILES and total <= MAX_DOWNLOAD, "vendor_budget")
                result[path.relative_to(base).as_posix()] = digest(raw)
        return result

    def verified_current(self, name, destination, record):
        require(type(record) is dict and record.get("bin") == destination.name, "receipt_schema")
        raw, identity = IO.read(destination, MAX_DOWNLOAD)
        require(digest(raw) == record.get("bin_sha256"), "modified_installation")
        vendor = record.get("vendor")
        if vendor is not None:
            require(re.fullmatch(re.escape(name) + r"-[a-f0-9]{12}-[a-z0-9_]+", vendor), "receipt_schema")
            require(self.inventory(self.vendor / vendor) == record.get("inventory"), "modified_installation")
        return identity

    def install(self, name, force=False):
        require(name in self.catalog["tools"] and re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name), "unknown_tool")
        tool = self.catalog["tools"][name]
        asset = tool.get("assets", {}).get(self.target) if tool["kind"] == "binary" else tool
        require(asset is not None, "unsupported_platform")
        fingerprint = digest(json_bytes(tool))
        filename = name + (".exe" if self.target.startswith("windows-") and tool["kind"] == "binary" else "")
        destination = self.bin / filename
        self.prepare()
        with IO.locked(self.root, self.deadline, initialize=True, wait=0):
            state, identity = self.state()
            record = state["tools"].get(name)
            expected = None
            if record is not None:
                expected = self.verified_current(name, destination, record)
                if record.get("fingerprint") == fingerprint and not force:
                    return "present"
            else:
                require(not destination.exists() and not destination.is_symlink(), "unmanaged_installation")
            vendor_path = None
            if tool["kind"] == "binary":
                raw = self.fetch(asset["url"])
                require(type(raw) is bytes and len(raw) <= MAX_DOWNLOAD and digest(raw) == asset["sha256"], "integrity")
                if asset["format"] == "raw":
                    output = raw
                else:
                    files = unpack(raw, asset["format"])
                    matches = [value[0] for path, value in files.items() if PurePosixPath(path).name == asset["binary"]]
                    require(len(matches) == 1, "binary_count")
                    output = matches[0]
            else:
                vendor_path = Path(tempfile.mkdtemp(prefix=name + "-" + fingerprint[:12] + "-", dir=self.vendor))
                if tool["kind"] == "source":
                    raw = self.fetch(tool["url"])
                    require(type(raw) is bytes and len(raw) <= MAX_DOWNLOAD and digest(raw) == tool["sha256"], "integrity")
                    files = unpack(raw, "tar.gz")
                    roots = {PurePosixPath(path).parts[0] for path in files}
                    require(len(roots) == 1 and all(len(PurePosixPath(path).parts) > 1 for path in files), "source_root")
                    for path, (content, mode) in files.items():
                        relative = PurePosixPath(*PurePosixPath(path).parts[1:])
                        dest = vendor_path / relative
                        directory(dest.parent)
                        IO.write(dest, content, self.deadline, mode=mode)
                    entry = vendor_path / safe_name(tool["entry"])
                    IO.file(entry)
                    if tool["runner"] == "python":
                        # Preserve environment isolation while restoring only this verified tree.
                        code = ("import runpy,sys; sys.path.insert(0," + repr(str(vendor_path))
                                + "); sys.argv=[" + repr(str(entry))
                                + ",*sys.argv[1:]]; runpy.run_path(" + repr(str(entry))
                                + ",run_name='__main__')")
                        argv = [shell_path(sys.executable), "-I", "-B", "-c", code]
                    else:
                        require(tool["runner"] in ("bash", "perl"), "runner")
                        runner = shutil.which(tool["runner"])
                        require(runner, "missing_runtime")
                        argv = [shell_path(runner), shell_path(entry)]
                elif tool["kind"] == "python":
                    requirements = HERE / tool["requirements"]
                    raw, _ = IO.read(requirements, MAX_METADATA)
                    require(digest(raw) == tool["requirements_sha256"], "integrity")
                    pinned = vendor_path / "requirements.txt"
                    IO.write(pinned, raw, self.deadline, mode=0o600)
                    # Only prebuilt hashed wheels. A private target avoids global Python changes.
                    environment = {key:value for key,value in os.environ.items()
                                   if not key.upper().startswith(("PIP_", "PYTHON"))}
                    environment["PIP_CONFIG_FILE"] = os.devnull
                    self.run([sys.executable, "-I", "-B", "-m", "pip", "--isolated", "install",
                              "--disable-pip-version-check", "--no-input", "--no-cache-dir",
                              "--index-url", "https://pypi.org/simple", "--require-hashes",
                              "--only-binary=:all:", "--no-deps", "--no-compile",
                              "--target", str(vendor_path), "-r", str(pinned)],
                             check=True, timeout=min(180, max(1, self.deadline-time.monotonic())),
                             env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    require((vendor_path / "wafw00f/__init__.py").is_file(), "python_entry")
                    code = "import sys; sys.path.insert(0," + repr(str(vendor_path)) + "); from wafw00f.main import main; main()"
                    argv = [shell_path(sys.executable), "-I", "-B", "-c", code]
                else:
                    raise ValueError("catalog_kind")
                output = shim(argv)
            row = {"fingerprint":fingerprint, "version":tool["version"],
                   "bin":filename, "bin_sha256":digest(output)}
            if vendor_path is not None:
                row.update(vendor=vendor_path.name, inventory=self.inventory(vendor_path))
            # Publish shim only after complete preparation. If receipt publication fails,
            # preserve files for inspection; a later run will refuse untracked files.
            IO.write(destination, output, self.deadline, expected=expected, mode=0o700)
            state["tools"][name] = row
            raw = json_bytes(state)
            require(len(raw) <= MAX_METADATA, "receipt_budget")
            IO.write(self.receipt, raw, self.deadline, expected=identity, mode=0o600)
            return "installed"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="comma-separated catalog names")
    parser.add_argument("--force", action="store_true", help="replace only an unchanged managed installation")
    parser.add_argument("--list", action="store_true", help="show reviewed versions; no installation or network")
    args = parser.parse_args()
    try:
        catalog = read_catalog()
        names = args.only.split(",") if args.only else list(catalog["tools"])
        require(names and all(name in catalog["tools"] for name in names), "unknown_tool")
        if args.list:
            for name in names:
                print(name + " " + catalog["tools"][name]["version"])
            return 0
        root = os.environ.get("SECURITY_TOOLS_DIR", str(Path.home() / ".claude/security-tools"))
        installer = Installer(root, catalog)
        failures = 0
        for name in names:
            try:
                print(name + ": " + installer.install(name, force=args.force))
            except (ValueError, OSError, subprocess.SubprocessError, tarfile.TarError, zipfile.BadZipFile):
                failures += 1
                print(name + ": failed (integrity, ownership, runtime or platform); existing files preserved", file=sys.stderr)
        return 1 if failures else 0
    except (ValueError, OSError, KeyError, TypeError):
        print("Nemesis tools: invalid catalog, platform or install root; nothing installed", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
