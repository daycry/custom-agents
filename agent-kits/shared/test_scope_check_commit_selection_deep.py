"""S25-B01: malformed/deep snapshots must fail closed before Git/filesystem reads."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

own = Path(__file__).resolve().parent
candidate = Path(__file__).resolve().with_name('scope-check.py')
spec = importlib.util.spec_from_file_location('scope_deep_focal', candidate)
scope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope)

def snapshot():
    return {'schema_version': 1, 'head': 'a' * 40, 'index_sha256': 'b' * 64,
            'seleccionados': [{'path': 'selected.txt', 'estado': 'modificado',
                'head_blob': 'c' * 40, 'index_blob': 'c' * 40, 'blob_commit': 'd' * 40,
                'head_mode': '100644', 'index_mode': '100644', 'worktree_mode': '100644',
                'worktree_sha256': 'e' * 64}],
            'no_seleccionados': [], 'staged_ajenos': [], 'conflictos': [], 'limites': [],
            'patch': '', 'patch_base64': '', 'patch_sha256': hashlib.sha256(b'').hexdigest(),
            'patch_display_lossless': True, 'snapshot_id': 'f' * 64}

class TestMalformed(unittest.TestCase):
    def reject_without_io(self, value):
        with patch.object(scope, 'proyectar_commit', side_effect=AssertionError('projection/IO forbidden')), \
             patch.object(scope, '_commit_paths', side_effect=AssertionError('path IO forbidden')), \
             patch.object(scope.subprocess, 'Popen', side_effect=AssertionError('Git forbidden')):
            result = scope.validar_seleccion_commit(str(own / 'nonexistent-root'), value)
        self.assertEqual(result, {'valido': False, 'motivos': [{'code': 'invalid_snapshot'}]})

    def deep(self, field):
        value = snapshot()
        nested = []
        for _ in range(sys.getrecursionlimit() * 10):
            nested = [nested]
        value[field] = nested
        with self.assertRaises(RecursionError):
            scope._commit_digest(value)
        with patch.object(scope, '_commit_digest', wraps=scope._commit_digest) as digest:
            self.reject_without_io(value)
            digest.assert_called_once()

    def test_deep_unselected(self):
        self.deep('no_seleccionados')

    def test_deep_limits(self):
        self.deep('limites')

    def test_missing_field(self):
        value = snapshot()
        del value['patch_base64']
        self.reject_without_io(value)

    def test_bool_schema(self):
        value = snapshot()
        value['schema_version'] = True
        self.reject_without_io(value)

if __name__ == '__main__':
    unittest.main()
