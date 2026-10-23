#!/usr/bin/env python3
"""Explicit optional Graphify AST build. Query never imports this producer.

The receipt verifies bytes of declared inputs, not producer identity, semantic
truth, discovery of new files or pair-atomic publication. An external library
root is explicitly trusted by the caller; nothing is installed or auto-loaded
from project configuration. Outputs must be new. Exclusive publication creates
the artifact first and its hash-bound receipt last; the pair is not atomic.
"""
import argparse
import contextlib
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import types

MAX_INPUTS = 128
MAX_INPUT_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_RECEIPT_BYTES = 512 * 1024
MAX_GRAPH_BYTES = 8 * 1024 * 1024
MAX_NODES, MAX_EDGES = 20000, 50000

class BuildError(Exception):
    def __init__(self, code):
        self.code = code

class DependencyUnavailable(Exception):
    pass

_LOCAL_READ = None

def _local_reader():
    global _LOCAL_READ
    if _LOCAL_READ is None:
        path = Path(__file__).with_name("local-read.py")
        spec = importlib.util.spec_from_file_location("producer_local_read", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _LOCAL_READ = module
    return _LOCAL_READ

def _canonical(value):
    if not isinstance(value, str) or not value or len(value) > 300 or any(c in value for c in "\\:*?\"<>|") or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise BuildError("invalid_input")
    path = PurePosixPath(value)
    parts = value.split("/")
    devices = {"con", "prn", "aux", "nul", "clock$"} | {prefix + suffix for prefix in ("com", "lpt") for suffix in "123456789" + chr(185) + chr(178) + chr(179)}
    if path.is_absolute() or any(not part or part in (".", "..") or part.endswith((".", " ")) or part.split(".")[0].casefold() in devices for part in parts) or path.as_posix() != value:
        raise BuildError("invalid_input")
    return value

def _local_root(value):
    # Check the original spelling before any UNC/device-prefix filesystem probe.
    if str(value).startswith((chr(92) * 2, "//")):
        raise BuildError("invalid_input")
    return Path(value).absolute()

def _no_links(path):
    for part in [path, *path.parents]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if _local_reader()._redirected(info):
            raise BuildError("unsafe_path")

def _regular(path):
    _no_links(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise BuildError("invalid_input")

def _read_failure(status):
    return {"too_large": "input_budget", "changed_path": "inputs_changed",
            "redirected_path": "unsafe_path"}.get(status, "invalid_input")

def _read_bounded(path, maximum):
    if maximum <= 1: raise BuildError("input_budget")
    row = _local_reader().read_bytes(path.parent, path.name, max_bytes=maximum - 1)
    if row["status"] != "ok": raise BuildError(_read_failure(row["status"]))
    return row["data"]

def _capture(project, names, excluded=()):
    records, versions = [], []
    total = 0
    physical = set(excluded)
    for name in names:
        cap = min(MAX_INPUT_BYTES, MAX_TOTAL_BYTES - total)
        if cap <= 1: raise BuildError("input_budget")
        # The common primitive reads max_bytes + 1 to detect concurrent growth.
        # Reserve that sentinel in both the per-input and remaining total cap.
        row = _local_reader().read_bytes(project, name, max_bytes=cap - 1,
                                         include_digest=True, include_identity=True)
        total += row["bytes"]
        if row["status"] != "ok": raise BuildError(_read_failure(row["status"]))
        identity = row["identity"][:2]
        if identity in physical: raise BuildError("invalid_input")
        physical.add(identity)
        if total > MAX_TOTAL_BYTES: raise BuildError("input_budget")
        records.append({"path": name, "bytes": row["bytes"], "sha256": row["sha256"]})
        versions.append((row["identity"], row["generation"]))
    return records, versions

def _new_targets(*paths):
    for path in paths:
        _no_links(path)
        try: path.lstat()
        except FileNotFoundError: continue
        raise BuildError("output_exists")

def _load_api(library_root, project):
    if library_root is None:
        raise DependencyUnavailable()
    root = _local_root(library_root)
    _no_links(root)
    root = root.resolve(strict=True)
    if root == project or root.is_relative_to(project):
        raise DependencyUnavailable()
    package = root / "graphify"
    _regular(package / "__init__.py")
    # Refuse a previously imported different library; do not silently swap it.
    for name, module in list(sys.modules.items()):
        if name == "graphify" or name.startswith("graphify."):
            filename = getattr(module, "__file__", None)
            if not filename or not Path(filename).resolve().is_relative_to(package):
                raise DependencyUnavailable()
    if "graphify" not in sys.modules:
        spec = importlib.util.spec_from_file_location("graphify", package / "__init__.py", submodule_search_locations=[str(package)])
        module = importlib.util.module_from_spec(spec)
        sys.modules["graphify"] = module
        spec.loader.exec_module(module)
    extractor = importlib.import_module("graphify.extract")
    builder = importlib.import_module("graphify.build")
    exporter = importlib.import_module("graphify.export")
    get_extractor = getattr(extractor, "_get_extractor", None)
    if not callable(get_extractor): raise DependencyUnavailable()
    api = types.SimpleNamespace(extract=extractor.extract, build=builder.build_from_json, export=exporter.to_json,
                                supports=lambda path: get_extractor(path) is not None)
    for fn, required in [(api.extract, {"root", "cache_root", "parallel"}), (api.build, {"root"}),
                         (api.export, {"force", "built_at_commit"})]:
        if not callable(fn) or not required.issubset(inspect.signature(fn).parameters):
            raise DependencyUnavailable()
    return api

@contextlib.contextmanager
def _offline():
    # Audit hooks cannot be removed. Deactivate this scoped guard on exit.
    active = [True]
    forbidden = [False]
    def audit(event, args):
        if active[0] and (event.startswith("socket.") or event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn")):
            forbidden[0] = True
            raise BuildError("external_execution_forbidden")
    def check():
        if forbidden[0]: raise BuildError("external_execution_forbidden")
    sys.addaudithook(audit)
    try:
        yield check
    finally:
        active[0] = False

def _graph_sources(raw, declared):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise BuildError("invalid_graph")
            result[key] = value
        return result
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (UnicodeError, ValueError):
        raise BuildError("invalid_graph") from None
    if not isinstance(data, dict): raise BuildError("invalid_graph")
    nodes, edges = data.get("nodes"), data.get("links", data.get("edges"))
    if not isinstance(nodes, list) or not isinstance(edges, list) or len(nodes) > MAX_NODES or len(edges) > MAX_EDGES:
        raise BuildError("invalid_graph")
    ids = set()
    for item in nodes:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or item["id"] in ids:
            raise BuildError("invalid_graph")
        ids.add(item["id"])
        if _canonical(item.get("source_file")) not in declared:
            raise BuildError("uncovered_source")
        if item.get("definition_file") is not None and _canonical(item["definition_file"]) not in declared:
            raise BuildError("uncovered_source")
    for item in edges:
        if not isinstance(item, dict) or item.get("source") not in ids or item.get("target") not in ids:
            raise BuildError("invalid_graph")
        if _canonical(item.get("source_file")) not in declared:
            raise BuildError("uncovered_source")
        if item.get("definition_file") is not None and _canonical(item["definition_file"]) not in declared:
            raise BuildError("uncovered_source")
    return data

def _sync_write(path, raw):
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())

def _publication_snapshot(path):
    _no_links(path)
    row = _local_reader().read_bytes(path.parent, path.name,
                                    max_bytes=MAX_GRAPH_BYTES - 1,
                                    include_digest=True, include_identity=True)
    if row["status"] != "ok": raise BuildError("publish_failed")
    return row["identity"], row["generation"], row["sha256"]

def _publish(staged_graph, staged_receipt, graph, receipt, artifact_sha256):
    try:
        staged = _publication_snapshot(staged_graph)
        if staged[2] != artifact_sha256: raise BuildError("publish_failed")
        _no_links(graph)
        _no_links(receipt)
        # Same-filesystem exclusive hard links never replace an existing path.
        # Unsupported links are a failure, without an overwrite fallback.
        os.link(staged_graph, graph, follow_symlinks=False)
        current = _publication_snapshot(graph)
        # Linking can change ctime; require staged identity, bytes and mtime
        # before publishing a receipt for the observed artifact.
        if current[0] != staged[0] or current[1][:2] != staged[1][:2] or current[2] != staged[2]:
            raise BuildError("publish_failed")
        _no_links(receipt)
        os.link(staged_receipt, receipt, follow_symlinks=False)
    except (OSError, BuildError):
        # Never delete or replace a final path on failure: even a matching
        # snapshot cannot close the race between comparison and destructive IO.
        # An incomplete artifact may remain; callers must use a new destination.
        # Only our private staging directory is cleaned by its context manager.
        raise BuildError("publish_failed") from None

def build_graph(project, graph, inputs, *, graphify_root=None):
    """Build only explicit paths; return an envelope without exposing source text."""
    try:
        project = _local_root(project)
        _no_links(project)
        project = project.resolve(strict=True)
        if not project.is_dir(): raise BuildError("invalid_input")
        graph_name = _canonical(graph)
        names = sorted(_canonical(name) for name in inputs)
        if not names or len(names) > MAX_INPUTS or len(names) != len({name.casefold() for name in names}):
            raise BuildError("invalid_input")
        graph_path = project / graph_name
        receipt_name = _canonical(graph_name + ".sources.json")
        receipt_path = project / receipt_name
        path_key = lambda name: name.casefold()
        if {path_key(graph_name), path_key(receipt_name)}.intersection(path_key(name) for name in names):
            raise BuildError("invalid_input")
        def capture():
            _new_targets(graph_path, receipt_path)
            return _capture(project, names)
        before = capture()
        with _offline() as check_offline:
            try:
                api = _load_api(graphify_root, project)
                if not callable(getattr(api, "supports", None)): raise DependencyUnavailable()
                unsupported = any(not api.supports(project / name) for name in names)
                check_offline()
            except BuildError:
                raise
            except Exception:
                check_offline()
                return {"status": "unavailable", "error": "graphify_unavailable", "local_memory": "available"}
            if unsupported:
                raise BuildError("unsupported_input")
            graph_path.parent.mkdir(parents=True, exist_ok=True)
            _no_links(graph_path.parent)
            with tempfile.TemporaryDirectory(prefix=".code-context-build-", dir=graph_path.parent) as directory:
                stage = Path(directory)
                staged_graph = stage / "artifact.json"
                staged_receipt = stage / "receipt.json"
                try:
                    extracted = api.extract([project / name for name in names], root=project, cache_root=stage / "cache", parallel=False)
                    check_offline()
                    if not isinstance(extracted, dict): raise BuildError("extraction_failed")
                    if extracted.get("failed_sources"):
                        # Native API combines absent grammars, parser failures
                        # and empty sources here. Do not invent a specific cause.
                        return {"status": "unavailable", "error": "ast_inputs_unavailable", "local_memory": "available"}
                    built = api.build(extracted, root=project)
                    if not api.export(built, {}, str(staged_graph), force=True, built_at_commit=""):
                        raise BuildError("extraction_failed")
                except (ImportError, ModuleNotFoundError):
                    return {"status": "unavailable", "error": "graphify_unavailable", "local_memory": "available"}
                except BuildError:
                    raise
                except Exception:
                    raise BuildError("extraction_failed") from None
                after = capture()
                if after != before: raise BuildError("inputs_changed")
                raw = _read_bounded(staged_graph, MAX_GRAPH_BYTES)
                _graph_sources(raw, set(names))
                # Flush the native staged artifact before exclusive publication.
                with staged_graph.open("r+b") as handle: os.fsync(handle.fileno())
                receipt = {"schema_version": 1, "artifact_sha256": hashlib.sha256(raw).hexdigest(),
                           "scope": "declared-inputs", "inputs": before[0]}
                receipt_raw = (json.dumps(receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                if len(receipt_raw) >= MAX_RECEIPT_BYTES: raise BuildError("receipt_budget")
                _sync_write(staged_receipt, receipt_raw)
                # Detect an observed edit while staging, too; no ABA guarantee.
                if capture() != before: raise BuildError("inputs_changed")
                check_offline()
                _publish(staged_graph, staged_receipt, graph_path, receipt_path, receipt["artifact_sha256"])
        return {"status": "ok", "artifact": graph_name, "receipt": receipt_path.relative_to(project).as_posix(),
                "scope": "declared-inputs", "inputs": len(names), "producer_authenticated": False,
                "global_coverage": "unknown", "pair_atomic": False}
    except BuildError as exc:
        return {"status": "failed", "error": exc.code, "local_memory": "available"}
    except (OSError, TypeError, ValueError):
        return {"status": "failed", "error": "invalid_input", "local_memory": "available"}

def main(argv=None):
    parser = argparse.ArgumentParser(description="Explicit offline AST build with optional external Graphify API; no installation or configuration discovery.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--graph", required=True, help="New canonical relative output path; neither it nor its receipt may exist")
    parser.add_argument("--input", action="append", required=True, dest="inputs", help="Explicit canonical relative input; repeat for all declared inputs")
    parser.add_argument("--graphify-root", help="Explicit trusted external directory containing graphify package")
    args = parser.parse_args(argv)
    result = build_graph(args.project, args.graph, args.inputs, graphify_root=args.graphify_root)
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result["status"] == "ok" else 2 if result["status"] == "unavailable" else 1

if __name__ == "__main__":
    raise SystemExit(main())
