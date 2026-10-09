"""Pure approved-snapshot validation shares full-index authority rules."""
import importlib.util
from pathlib import Path


def test_snapshot_validation_no_filesystem(tmp_path):
    spec = importlib.util.spec_from_file_location('kl_test', Path(__file__).with_name('knowledge-local.py'))
    local = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(local)
    cfg = local._TAXONOMY.default_taxonomy()
    text = '---\nid: custom.DECISION.1\nversion: 1\ncategory: DECISION\nestado: aprobado\n---\nBody'
    entries, errors = local.index_snapshot([(str(tmp_path/'absent.md'), 'adr', text)], cfg, include_source=True, root=str(tmp_path))
    assert not errors and entries['custom.DECISION.1']['texto'] == text
    entries, errors = local.index_snapshot([(str(tmp_path/'absent.md'), 'adr', text.replace('aprobado','propuesta'))], cfg)
    assert errors and any(e['campo'] == 'estado' for e in errors)
