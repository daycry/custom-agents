"""Keep the memory reader's contracts intact when its governed detail is deferred."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / 'agent-kits/shared'
BASELINE = ROOT / 'tests/fixtures/knowledge-check-paragraphs.json'


def paragraphs(text):
    return [' '.join(part.split()) for part in re.split(r'\n\s*\n', text) if part.strip()]


def test_memory_detail_has_a_conditional_same_kit_reference():
    core = (SHARED / 'knowledge-check.md').read_text(encoding='utf-8')
    detail = SHARED / 'knowledge-check-governed.md'
    assert detail.is_file(), 'governed memory detail has not been extracted'
    assert 'docs/knowledge/' in core and 'knowledge-check-governed.md' in core
    assert '**Si existe' in core and '**Si no existe' in core
    assert '**Reparto de qué lee cada agente**' not in core
    assert '**Reparto de qué lee cada agente**' in detail.read_text(encoding='utf-8')


def test_no_original_paragraph_is_lost():
    baseline = json.loads(BASELINE.read_text(encoding='utf-8'))
    corpus = (SHARED / 'knowledge-check.md').read_text(encoding='utf-8')
    corpus += '\n\n' + (SHARED / 'knowledge-check-governed.md').read_text(encoding='utf-8')
    hashes = {hashlib.sha256(p.encode('utf-8')).hexdigest() for p in paragraphs(corpus)}
    assert not set(baseline['paragraph_sha256']) - hashes


def test_journal_code_context_and_plugin_doctrine_remain_available_without_governed_detail():
    core = (SHARED / 'knowledge-check.md').read_text(encoding='utf-8')
    assert 'code-context.py' in core and 'unapproved-context' in core
    assert 'journal.py latest --n 1 --initiative' in core
    assert '--doctrina --area estimacion --limit 0' in core
    assert 'incluso sin `docs/knowledge/`' in core


def test_governed_detail_does_not_depend_on_a_remote_backend():
    detail = (SHARED / 'knowledge-check-governed.md').read_text(encoding='utf-8')
    assert 'candidates/**' in detail and 'estado: aceptada' in detail and 'estado: aprobado' in detail
    assert '--tipo adr' in detail and '--tipo gotcha' in detail
    assert not re.search(r'(?:kwipu|graphiti).*enabled', detail, flags=re.I)


def test_portable_dependency_closure_keeps_detail_when_router_is_selected():
    spec = importlib.util.spec_from_file_location('memory_prompt_portable_test', ROOT / 'scripts/export-skills.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    paths = exporter.fragmentos_shared(str(ROOT), ['agent-kits/shared/knowledge-check.md'])
    assert 'agent-kits/shared/knowledge-check.md' in paths
    assert 'agent-kits/shared/knowledge-check-governed.md' in paths
