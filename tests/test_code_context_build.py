"""Unit fault cases for explicit producer; native acceptance is separate."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "agent-kits/shared/code-context-build.py"

def load():
    if not SCRIPT.exists():
        return types.SimpleNamespace(build_graph=lambda *a, **kw: {"status": "missing_producer", "error": "not_implemented"})
    spec = importlib.util.spec_from_file_location("producer_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class ProducerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "a.py").write_bytes(b"def first(): return 1\n")
        (self.project / "extra.py").write_bytes(b"def extra(): return 2\n")
        self.graph = self.project / "graph.json"
        self.receipt = self.project / "graph.json.sources.json"
        self.module = load()
        self.extract_hook = None
        self.export_fail = False
        self.export_hook = None
        self.foreign = False
        self.failed_sources = []
        self.edges = []
        self.definition = None
    def api(self):
        def extract(paths, *, root, cache_root, parallel):
            self.assertFalse(parallel)
            if self.extract_hook: self.extract_hook()
            node = {"id": "first", "source_file": "foreign.py" if self.foreign else "a.py", "_origin": "ast"}
            if self.definition is not None: node["definition_file"] = self.definition
            return {"nodes": [node], "edges": self.edges, "failed_sources": self.failed_sources}
        def build(data, *, root): return data
        def export(graph, communities, path, *, force, built_at_commit):
            self.assertEqual(built_at_commit, "")
            self.assertTrue(force)
            if self.export_fail: raise OSError("export failed")
            Path(path).write_text(json.dumps({"nodes": graph["nodes"], "links": graph["edges"]}), encoding="utf-8")
            if self.export_hook: self.export_hook()
            return True
        return types.SimpleNamespace(extract=extract, build=build, export=export, supports=lambda path: path.suffix in (".py", ".js"))
    def invoke(self, inputs=None):
        if not hasattr(self.module, "_load_api"):
            return self.module.build_graph(self.project, "graph.json", inputs or ["a.py"])
        with patch.object(self.module, "_load_api", return_value=self.api()):
            return self.module.build_graph(self.project, "graph.json", inputs or ["a.py"], graphify_root=self.root / "lib")
    def test_explicit_build_receipt_covers_all_inputs(self):
        result = self.invoke(["a.py", "extra.py"])
        self.assertEqual(result["status"], "ok")
        data = json.loads(self.receipt.read_text())
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["scope"], "declared-inputs")
        self.assertEqual(data["artifact_sha256"], hashlib.sha256(self.graph.read_bytes()).hexdigest())
        self.assertEqual([x["path"] for x in data["inputs"]], ["a.py", "extra.py"])
        for row in data["inputs"]:
            raw = (self.project / row["path"]).read_bytes()
            self.assertEqual(row["bytes"], len(raw))
            self.assertEqual(row["sha256"], hashlib.sha256(raw).hexdigest())
    def test_edit_during_extraction_does_not_publish_pair(self):
        self.extract_hook = lambda: (self.project / "extra.py").write_bytes(b"changed")
        result = self.invoke(["a.py", "extra.py"])
        self.assertEqual(result.get("error"), "inputs_changed")
        self.assertFalse(self.graph.exists())
        self.assertFalse(self.receipt.exists())
    def test_export_failure_does_not_publish_receipt(self):
        self.export_fail = True
        result = self.invoke()
        self.assertEqual(result.get("error"), "extraction_failed")
        self.assertFalse(self.receipt.exists())
        self.assertFalse(self.graph.exists())
    def test_uncovered_graph_source_rejected(self):
        self.foreign = True
        result = self.invoke()
        self.assertEqual(result.get("error"), "uncovered_source")
        self.assertFalse(self.graph.exists())
    def test_unsupported_input_rejected(self):
        (self.project / "data.xyz").write_bytes(b"unparsed")
        result = self.invoke(["data.xyz"])
        self.assertEqual(result.get("error"), "unsupported_input")
    def test_missing_dependency_local_memory_continues(self):
        result = self.module.build_graph(self.project, "graph.json", ["a.py"], graphify_root=self.root / "absent")
        self.assertEqual(result.get("status"), "unavailable")
        self.assertEqual(result.get("error"), "graphify_unavailable")
        self.assertFalse(self.receipt.exists())
    def test_unsafe_paths_duplicate_and_input_budget_rejected(self):
        for inputs in (["../escape.py"], ["a.py", "a.py"], ["./a.py"]):
            with self.subTest(inputs=inputs):
                self.assertEqual(self.invoke(inputs).get("error"), "invalid_input")
        (self.project / "large.py").write_bytes(b"x" * (1024 * 1024 + 1))
        self.assertEqual(self.invoke(["large.py"]).get("error"), "input_budget")
    def test_receipt_link_failure_retains_partial_own_graph(self):
        link = self.module.os.link
        def fail_receipt(src, dst, **kwargs):
            if Path(dst) == self.receipt: raise OSError("receipt publication blocked")
            return link(src, dst, **kwargs)
        with patch.object(self.module.os, "link", side_effect=fail_receipt):
            result = self.invoke()
        self.assertEqual(result.get("error"), "publish_failed")
        self.assertTrue(self.graph.exists())
        self.assertFalse(self.receipt.exists())
    def test_native_supported_non_python_is_not_python_only(self):
        (self.project / "a.js").write_bytes(b"function first() { return 1; }\n")
        result = self.invoke(["a.py", "a.js"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(json.loads(self.receipt.read_text())["inputs"]), 2)

    def test_native_partial_extraction_degrades_without_receipt(self):
        self.failed_sources = [str(self.project / "a.py")]
        result = self.invoke()
        self.assertEqual(result.get("status"), "unavailable")
        self.assertEqual(result.get("error"), "ast_inputs_unavailable")
        self.assertFalse(self.graph.exists())
        self.assertFalse(self.receipt.exists())
    def test_caught_external_attempt_still_blocks_publication(self):
        import socket
        def swallowed_attempt():
            try: socket.socket()
            except Exception: pass
        self.extract_hook = swallowed_attempt
        result = self.invoke()
        self.assertEqual(result.get("error"), "external_execution_forbidden")
        self.assertFalse(self.graph.exists())
        self.assertFalse(self.receipt.exists())
    def test_uncovered_edge_is_rejected(self):
        self.edges = [{"source": "first", "target": "first", "source_file": "undeclared.py", "_origin": "ast"}]
        result = self.invoke()
        self.assertEqual(result.get("error"), "uncovered_source")
        self.assertFalse(self.receipt.exists())
    def test_total_and_count_budgets_reject_before_extraction(self):
        self.assertEqual(self.invoke([str(i) + ".py" for i in range(129)]).get("error"), "invalid_input")
        inputs = []
        for index in range(9):
            name = str(index) + ".py"
            (self.project / name).write_bytes(b"x" * (1024 * 1024))
            inputs.append(name)
        self.assertEqual(self.invoke(inputs).get("error"), "input_budget")
        self.assertFalse(self.graph.exists())
    def test_receipt_is_linked_last_with_artifact_hash_already_matching(self):
        link = self.module.os.link
        order = []
        def observe(src, dst, **kwargs):
            if Path(dst) == self.receipt:
                row = json.loads(Path(src).read_bytes())
                self.assertEqual(row["artifact_sha256"], hashlib.sha256(self.graph.read_bytes()).hexdigest())
            order.append(Path(dst).name)
            return link(src, dst, **kwargs)
        with patch.object(self.module.os, "link", side_effect=observe):
            result = self.invoke()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(order, ["graph.json", "graph.json.sources.json"])
    def test_symlink_or_redirected_input_is_rejected(self):
        linked = self.project / "linked.py"
        try:
            linked.symlink_to(self.project / "a.py")
        except OSError:
            # Windows may not grant symlink creation. Exercise its native
            # redirection metadata as a unit fault; native fixture acceptance
            # never substitutes fake extraction or metadata.
            linked.write_bytes(b"def linked(): return 1\n")
            lstat = self.module.os.lstat
            def redirected(path, *args, **kwargs):
                if Path(path) == linked:
                    import stat
                    return types.SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400, st_reparse_tag=0xA000000C)
                return lstat(path, *args, **kwargs)
            with patch.object(self.module.os, "lstat", side_effect=redirected):
                result = self.invoke(["linked.py"])
        else:
            result = self.invoke(["linked.py"])
        self.assertEqual(result.get("error"), "unsafe_path")
        self.assertFalse(self.receipt.exists())
    def test_non_utf8_source_bytes_are_hashed_without_decoding(self):
        raw = b"\xff\xfe"
        (self.project / "a.py").write_bytes(raw)
        result = self.invoke()
        # The trusted native parser owns supported encodings. This unit fault
        # API accepts bytes; the producer must not impose its own text parser.
        self.assertEqual(result["status"], "ok")
        row = json.loads(self.receipt.read_bytes())["inputs"][0]
        self.assertEqual(row["bytes"], len(raw))
        self.assertEqual(row["sha256"], hashlib.sha256(raw).hexdigest())
    def test_bom_is_included_in_declared_raw_digest(self):
        raw = b"\xef\xbb\xbfdef first(): return 1\n"
        (self.project / "a.py").write_bytes(raw)
        self.assertEqual(self.invoke()["status"], "ok")
        row = json.loads(self.receipt.read_bytes())["inputs"][0]
        self.assertEqual(row["bytes"], len(raw))
        self.assertEqual(row["sha256"], hashlib.sha256(raw).hexdigest())

    def test_uncovered_definition_file_rejected(self):
        self.definition = "undeclared.py"
        result = self.invoke()
        self.assertEqual(result.get("error"), "uncovered_source")
        self.assertFalse(self.receipt.exists())

    def test_capture_aggregate_bytes_are_never_read_past_budget(self):
        (self.project / "a.py").write_bytes(b"aaa")
        (self.project / "extra.py").write_bytes(b"bbb")
        reader = self.module._local_reader()
        original = reader.read_bytes
        spent = [0]
        requests = []
        def count(*args, **kwargs):
            requests.append(kwargs["max_bytes"])
            row = original(*args, **kwargs)
            spent[0] += row["bytes"]
            return row
        with patch.object(self.module, "MAX_INPUT_BYTES", 4), patch.object(self.module, "MAX_TOTAL_BYTES", 5), patch.object(reader, "read_bytes", side_effect=count):
            result = self.invoke(["a.py", "extra.py"])
        self.assertEqual(result.get("error"), "input_budget")
        self.assertLessEqual(spent[0], 5)
        self.assertLessEqual(requests[0] + 1, 4)
        self.assertLessEqual(requests[1] + 1, 2)
        self.assertFalse(self.graph.exists())
    def test_capture_zero_budget_does_not_open_input(self):
        reader = self.module._local_reader()
        with patch.object(self.module, "MAX_TOTAL_BYTES", 0), patch.object(reader, "read_bytes", wraps=reader.read_bytes) as read:
            result = self.invoke()
        self.assertEqual(result.get("error"), "input_budget")
        self.assertEqual(read.call_count, 0)
    def test_windows_alias_paths_are_rejected_lexically(self):
        invalid = ['trailing./x.py', 'trailing /x.py', 'con.py', 'NUL/data.py', 'COM1.py', 'lpt9.py', 'clock$.py', 'a?.py', 'a|b.py', 'a\x7fb.py', 'a\x01b.py', 'x' * 301]
        invalid.append('COM' + chr(185) + '.py')
        for path in invalid:
            with self.subTest(path=path):
                with self.assertRaises(self.module.BuildError): self.module._canonical(path)
    @unittest.skipUnless(__import__("os").name == "nt", "case aliases are Windows identities")
    def test_windows_case_alias_inputs_rejected_before_open(self):
        reader = self.module._local_reader()
        with patch.object(reader, "read_bytes", wraps=reader.read_bytes) as read:
            result = self.invoke(["a.py", "A.py"])
        self.assertEqual(result.get("error"), "invalid_input")
        self.assertEqual(read.call_count, 0)
    def test_unc_roots_rejected_before_filesystem_probe(self):
        for root in ('//invalid.test/share', chr(92)*2 + 'invalid.test' + chr(92) + 'share'):
            with self.subTest(root=root), patch.object(self.module.Path, "lstat", side_effect=AssertionError("UNC probed")) as probe:
                result = self.module.build_graph(root, "graph.json", ["a.py"])
                self.assertEqual(result.get("error"), "invalid_input")
                self.assertEqual(probe.call_count, 0)
    def test_hardlink_aliases_inputs_and_outputs_rejected(self):
        import os
        os.link(self.project / "a.py", self.project / "alias.py")
        self.assertEqual(self.invoke(["a.py", "alias.py"]).get("error"), "invalid_input")
        os.link(self.project / "a.py", self.graph)
        self.assertEqual(self.invoke().get("error"), "output_exists")
        self.graph.unlink()
        os.link(self.project / "a.py", self.receipt)
        self.assertEqual(self.invoke().get("error"), "output_exists")
        self.receipt.unlink()
        self.graph.write_bytes(b"old")
        os.link(self.graph, self.receipt)
        self.assertEqual(self.invoke().get("error"), "output_exists")
        self.assertEqual(self.graph.read_bytes(), b"old")
        self.assertEqual(self.receipt.read_bytes(), b"old")

    def test_preexisting_destinations_refused_before_api_import(self):
        for existing in ((self.graph,), (self.receipt,), (self.graph, self.receipt)):
            with self.subTest(existing=[p.name for p in existing]):
                for path in (self.graph, self.receipt):
                    if path.exists(): path.unlink()
                for path in existing: path.write_bytes(b"foreign sentinel " + path.name.encode())
                before = {p: p.read_bytes() for p in existing}
                with patch.object(self.module, "_load_api", side_effect=AssertionError("API imported for foreign destination")) as load:
                    result = self.module.build_graph(self.project, "graph.json", ["a.py"], graphify_root=self.root / "lib")
                self.assertEqual(result.get("error"), "output_exists")
                self.assertEqual(load.call_count, 0)
                self.assertEqual({p: p.read_bytes() for p in existing}, before)
    def test_target_appearing_during_export_is_preserved(self):
        self.export_hook = lambda: self.graph.write_bytes(b"foreign appeared during export")
        result = self.invoke()
        self.assertEqual(result.get("error"), "output_exists")
        self.assertEqual(self.graph.read_bytes(), b"foreign appeared during export")
        self.assertFalse(self.receipt.exists())
    def test_receipt_appearing_at_publication_is_preserved(self):
        originals = {name: getattr(self.module.os, name) for name in ("link", "replace")}
        def intercept(name):
            def call(src, dst, *args, **kwargs):
                if Path(dst) == self.graph: self.receipt.write_bytes(b"foreign appeared at publication")
                return originals[name](src, dst, *args, **kwargs)
            return call
        with patch.object(self.module.os, "link", side_effect=intercept("link")), patch.object(self.module.os, "replace", side_effect=intercept("replace")):
            result = self.invoke()
        self.assertEqual(result.get("error"), "publish_failed")
        self.assertEqual(self.receipt.read_bytes(), b"foreign appeared at publication")
        self.assertTrue(self.graph.exists())
    def test_concurrent_content_is_retained_on_failure(self):
        originals = {name: getattr(self.module.os, name) for name in ("link", "replace")}
        def intercept(name):
            def call(src, dst, *args, **kwargs):
                if Path(dst) == self.receipt:
                    self.graph.write_bytes(b"foreign concurrent edit")
                    raise OSError("receipt blocked")
                return originals[name](src, dst, *args, **kwargs)
            return call
        with patch.object(self.module.os, "link", side_effect=intercept("link")), patch.object(self.module.os, "replace", side_effect=intercept("replace")):
            result = self.invoke()
        self.assertEqual(result.get("error"), "publish_failed")
        self.assertTrue(self.graph.exists())
        self.assertEqual(self.graph.read_bytes(), b"foreign concurrent edit")
        self.assertFalse(self.receipt.exists())
    def test_concurrent_identity_is_retained_on_failure(self):
        originals = {name: getattr(self.module.os, name) for name in ("link", "replace")}
        replacement = []
        def intercept(name):
            def call(src, dst, *args, **kwargs):
                if Path(dst) == self.receipt:
                    raw = self.graph.read_bytes();self.graph.unlink();self.graph.write_bytes(raw)
                    replacement.append((self.graph.stat().st_dev, self.graph.stat().st_ino))
                    raise OSError("receipt blocked")
                return originals[name](src, dst, *args, **kwargs)
            return call
        with patch.object(self.module.os, "link", side_effect=intercept("link")), patch.object(self.module.os, "replace", side_effect=intercept("replace")):
            result = self.invoke()
        self.assertEqual(result.get("error"), "publish_failed")
        self.assertTrue(self.graph.exists())
        self.assertEqual((self.graph.stat().st_dev, self.graph.stat().st_ino), replacement[0])
        self.assertFalse(self.receipt.exists())
    def test_supports_exception_degrades_before_extraction(self):
        api = self.api()
        def broken(path): raise AttributeError("missing helper")
        api.supports = broken
        with patch.object(self.module, "_load_api", return_value=api), patch.object(api, "extract", side_effect=AssertionError("extract called")) as extract:
            result = self.module.build_graph(self.project, "graph.json", ["a.py"], graphify_root=self.root / "lib")
        self.assertEqual(result.get("status"), "unavailable")
        self.assertEqual(result.get("error"), "graphify_unavailable")
        self.assertEqual(extract.call_count, 0)
        self.assertFalse(self.graph.exists())
        self.assertFalse(self.receipt.exists())
    def test_compatible_native_api_missing_support_helper_degrades(self):
        import sys
        library = self.root / "optional-library";package = library / "graphify";package.mkdir(parents=True)
        (package / "__init__.py").write_bytes(b"")
        (package / "extract.py").write_text("def extract(paths, *, root, cache_root, parallel):\n    raise AssertionError('should not extract')\n",encoding="utf-8")
        (package / "build.py").write_text("def build_from_json(data, *, root): return data\n",encoding="utf-8")
        (package / "export.py").write_text("def to_json(graph, communities, path, *, force, built_at_commit): return True\n",encoding="utf-8")
        saved = {name:module for name,module in sys.modules.items() if name == "graphify" or name.startswith("graphify.")}
        for name in saved: sys.modules.pop(name)
        try:
            result = self.module.build_graph(self.project, "graph.json", ["a.py"], graphify_root=library)
        finally:
            for name in list(sys.modules):
                if name == "graphify" or name.startswith("graphify."): sys.modules.pop(name)
            sys.modules.update(saved)
        self.assertEqual(result.get("status"), "unavailable")
        self.assertEqual(result.get("error"), "graphify_unavailable")
        self.assertFalse(self.graph.exists())
        self.assertFalse(self.receipt.exists())

    def test_graph_appearing_at_publication_is_preserved(self):
        originals = {name: getattr(self.module.os, name) for name in ("link", "replace")}
        def intercept(name):
            def call(src, dst, *args, **kwargs):
                if Path(dst) == self.graph: self.graph.write_bytes(b"foreign at link")
                return originals[name](src, dst, *args, **kwargs)
            return call
        with patch.object(self.module.os, "link", side_effect=intercept("link")), patch.object(self.module.os, "replace", side_effect=intercept("replace")):
            result = self.invoke()
        self.assertEqual(result.get("error"), "publish_failed")
        self.assertEqual(self.graph.read_bytes(), b"foreign at link")
        self.assertFalse(self.receipt.exists())
    def test_concurrent_generation_is_retained_on_failure(self):
        originals = {name: getattr(self.module.os, name) for name in ("link", "replace")}
        def intercept(name):
            def call(src, dst, *args, **kwargs):
                if Path(dst) == self.receipt:
                    info = self.graph.stat()
                    self.module.os.utime(self.graph, ns=(info.st_atime_ns, info.st_mtime_ns + 1000000000))
                    raise OSError("receipt blocked")
                return originals[name](src, dst, *args, **kwargs)
            return call
        with patch.object(self.module.os, "link", side_effect=intercept("link")), patch.object(self.module.os, "replace", side_effect=intercept("replace")):
            result = self.invoke()
        self.assertEqual(result.get("error"), "publish_failed")
        self.assertTrue(self.graph.exists())
        self.assertFalse(self.receipt.exists())
    def test_noncallable_supports_degrades_before_extraction(self):
        api = self.api();api.supports = None
        with patch.object(self.module, "_load_api", return_value=api), patch.object(api, "extract", side_effect=AssertionError("extract called")) as extract:
            result = self.module.build_graph(self.project, "graph.json", ["a.py"], graphify_root=self.root / "lib")
        self.assertEqual(result.get("status"), "unavailable")
        self.assertEqual(extract.call_count, 0)
        self.assertFalse(self.graph.exists())
        self.assertFalse(self.receipt.exists())

    def test_final_path_is_never_unlinked_after_receipt_failure(self):
        link = self.module.os.link
        unlink = self.module.Path.unlink
        final_unlinks = []
        def fail_receipt(src, dst, **kwargs):
            if Path(dst) == self.receipt: raise OSError("receipt blocked")
            return link(src, dst, **kwargs)
        def foreign_just_before_unlink(path, *args, **kwargs):
            if path == self.graph:
                final_unlinks.append(str(path))
                path.write_bytes(b"foreign just before unlink")
            return unlink(path, *args, **kwargs)
        with patch.object(self.module.os, "link", side_effect=fail_receipt), patch.object(self.module.Path, "unlink", new=foreign_just_before_unlink):
            result = self.invoke()
        self.assertEqual(result.get("error"), "publish_failed")
        self.assertTrue(self.graph.exists())
        self.assertEqual(final_unlinks, [])
        self.assertFalse(self.receipt.exists())

    def assert_no_publication_or_staging(self):
        self.assertFalse(self.graph.exists())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(list(self.project.glob('.code-context-build-*')), [])

    def test_extractor_contract_failures_leave_inputs_and_destinations_intact(self):
        before = (self.project / 'a.py').read_bytes()
        for fault in ('not_object', 'import_failure', 'exception', 'export_false'):
            with self.subTest(fault=fault):
                api = self.api()
                if fault == 'not_object': api.extract = lambda *a, **kw: []
                elif fault == 'import_failure':
                    def missing(*a, **kw): raise ImportError('PRIVATE_DEPENDENCY_PATH')
                    api.extract = missing
                elif fault == 'exception':
                    def broken(*a, **kw): raise RuntimeError('PRIVATE_SOURCE_TEXT')
                    api.extract = broken
                else: api.export = lambda *a, **kw: False
                with patch.object(self.module, '_load_api', return_value=api):
                    result = self.module.build_graph(self.project, 'graph.json', ['a.py'])
                self.assertEqual(result['local_memory'], 'available')
                self.assertEqual(result['error'], 'graphify_unavailable' if fault == 'import_failure' else 'extraction_failed')
                self.assertNotIn('PRIVATE_', json.dumps(result))
                self.assertEqual((self.project / 'a.py').read_bytes(), before)
                self.assert_no_publication_or_staging()

    def test_invalid_native_graph_never_acquires_an_authorizing_receipt(self):
        graphs = [b'\xff', b'{', b'[]', b'{"nodes":[],"nodes":[],"links":[]}',
                  b'{"nodes":{},"links":[]}',
                  b'{"nodes":[null],"links":[]}',
                  b'{"nodes":[{"id":"x","source_file":"a.py"},{"id":"x","source_file":"a.py"}],"links":[]}',
                  b'{"nodes":[{"id":"x","source_file":"a.py"}],"links":[{"source":"x","target":"absent","source_file":"a.py"}]}']
        for raw in graphs:
            with self.subTest(raw=raw):
                api = self.api()
                def export(*args, **kwargs):
                    Path(args[2]).write_bytes(raw)
                    return True
                api.export = export
                with patch.object(self.module, '_load_api', return_value=api):
                    result = self.module.build_graph(self.project, 'graph.json', ['a.py'])
                self.assertEqual(result['error'], 'invalid_graph')
                self.assert_no_publication_or_staging()

    def test_staged_output_budgets_abort_and_remove_only_private_staging(self):
        for bound in ('MAX_GRAPH_BYTES', 'MAX_RECEIPT_BYTES'):
            with self.subTest(bound=bound), patch.object(self.module, bound, 1):
                result = self.invoke()
                self.assertEqual(result['error'], 'input_budget' if bound == 'MAX_GRAPH_BYTES' else 'receipt_budget')
                self.assertEqual((self.project / 'a.py').read_bytes(), b'def first(): return 1\n')
                self.assert_no_publication_or_staging()

    def test_input_permission_denial_does_not_import_optional_library(self):
        reader = self.module._local_reader()
        original = reader.os.open
        def denied(path, *args, **kwargs):
            if Path(path) == self.project / 'a.py': raise PermissionError('PRIVATE_DENIAL_PATH')
            return original(path, *args, **kwargs)
        with patch.object(reader.os, 'open', side_effect=denied), patch.object(self.module, '_load_api') as imported:
            result = self.module.build_graph(self.project, 'graph.json', ['a.py'])
        self.assertEqual(result['error'], 'invalid_input')
        self.assertEqual(imported.call_count, 0)
        self.assertNotIn('PRIVATE_', json.dumps(result))
        self.assert_no_publication_or_staging()

    def test_output_cannot_be_declared_input_and_file_cannot_be_project(self):
        reader = self.module._local_reader()
        with patch.object(reader, 'read_bytes', wraps=reader.read_bytes) as read:
            for name in ('graph.json', 'graph.json.sources.json'):
                self.assertEqual(self.module.build_graph(self.project, 'graph.json', [name])['error'], 'invalid_input')
            result = self.module.build_graph(self.project / 'a.py', 'graph.json', ['a.py'])
        self.assertEqual(result['error'], 'invalid_input')
        self.assertEqual(read.call_count, 0)
        self.assert_no_publication_or_staging()

    def test_missing_or_project_local_library_remains_optional(self):
        for library in (None, self.project):
            with self.subTest(library=library):
                result = self.module.build_graph(self.project, 'graph.json', ['a.py'], graphify_root=library)
                self.assertEqual(result['status'], 'unavailable')
                self.assertEqual(result['error'], 'graphify_unavailable')
                self.assert_no_publication_or_staging()

    def test_edge_definition_requires_the_same_explicit_input_allowlist(self):
        self.edges = [{'source': 'first', 'target': 'first', 'source_file': 'a.py',
                       'definition_file': 'extra.py'}]
        self.assertEqual(self.invoke()['error'], 'uncovered_source')
        self.assert_no_publication_or_staging()
        self.assertEqual(self.invoke(['a.py', 'extra.py'])['status'], 'ok')
        receipt = json.loads(self.receipt.read_bytes())
        self.assertEqual({entry['path'] for entry in receipt['inputs']}, {'a.py', 'extra.py'})

    def test_late_input_edit_after_receipt_staging_still_blocks_publication(self):
        original = self.module._sync_write
        def edited_after_staging(path, raw):
            original(path, raw)
            (self.project / 'a.py').write_bytes(b'concurrent late edit')
        with patch.object(self.module, '_sync_write', side_effect=edited_after_staging):
            result = self.invoke()
        self.assertEqual(result['error'], 'inputs_changed')
        self.assertEqual((self.project / 'a.py').read_bytes(), b'concurrent late edit')
        self.assert_no_publication_or_staging()

    def test_case_alias_source_names_rejected_portably_before_input_io(self):
        # These are two real files on case-sensitive filesystems; portable
        # artifacts must not admit an ambiguous identity on case-insensitive ones.
        (self.project / 'worker.py').write_bytes(b'def lower(): return 1\n')
        (self.project / 'WORKER.py').write_bytes(b'def upper(): return 2\n')
        reader = self.module._local_reader()
        with patch.object(reader, 'read_bytes', wraps=reader.read_bytes) as read, \
                patch.object(self.module, '_load_api', side_effect=AssertionError('alias reached optional API')) as imported:
            result = self.module.build_graph(self.project, 'graph.json', ['worker.py', 'WORKER.py'])
        self.assertEqual(result['error'], 'invalid_input')
        self.assertEqual(read.call_count, 0)
        self.assertEqual(imported.call_count, 0)
        self.assert_no_publication_or_staging()

    def test_case_alias_output_names_rejected_portably_before_input_io(self):
        reader = self.module._local_reader()
        for name in ('GRAPH.json', 'GRAPH.json.sources.json'):
            with self.subTest(input=name):
                input_path = self.project / name
                input_path.write_bytes(b'owned input sentinel')
                with patch.object(reader, 'read_bytes', wraps=reader.read_bytes) as read, \
                        patch.object(self.module, '_load_api', side_effect=AssertionError('alias reached optional API')) as imported:
                    result = self.module.build_graph(self.project, 'graph.json', [name])
                self.assertEqual(result['error'], 'invalid_input')
                self.assertEqual(read.call_count, 0)
                self.assertEqual(imported.call_count, 0)
                self.assertEqual(input_path.read_bytes(), b'owned input sentinel')
                self.assertEqual(list(self.project.glob('.code-context-build-*')), [])
                input_path.unlink()

if __name__ == "__main__":
    unittest.main()
