"""Optional TOML support must not break Python 3.9/3.10 bundle consumers."""
import builtins
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def without_tomllib(monkeypatch):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name == 'tomllib':
            raise ModuleNotFoundError('optional TOML parser unavailable', name=name)
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)


def load(relative):
    spec = importlib.util.spec_from_file_location('compat_' + Path(relative).stem.replace('-', '_'), ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selector_without_tomllib_keeps_json_stacks_and_reports_toml_limit(without_tomllib, tmp_path):
    route = load('agent-kits/shared/capability-route.py')
    (tmp_path / 'composer.json').write_text('{"require":{"php":"*"}}', encoding='utf-8')
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="example"\n', encoding='utf-8')
    detected = route.detect(tmp_path)
    assert detected['stacks'] == ['php']
    assert detected['sources'] == ['composer.json']
    assert len(detected['warnings']) == 1 and 'pyproject.toml' in detected['warnings'][0]
    assert route.validate_catalog(route.load_catalog()) == []


def test_brief_optional_guidance_works_without_tomllib(without_tomllib):
    brief = load('agent-kits/shared/task-brief.py')
    output = '\n'.join(brief._seccion_capacidades('- **Capacidades**: stack-practices'))
    assert 'stack-practices' in output and '## Capacidades' in output


def test_panel_workflow_works_without_tomllib(without_tomllib):
    panel = load('skills/plugin-panel/scripts/build_panel.py')
    inventory = panel.build_inventory(ROOT)
    assert inventory['workflow']['roles']['implementer']
    assert inventory['counts']['skills'] == len(list((ROOT / 'skills').glob('*/SKILL.md')))


def test_structural_reader_works_without_tomllib(without_tomllib):
    context = load('agent-kits/shared/code-context.py')
    fixture = ROOT / 'docs/roadmap/2026-10-06-workflow-integration/testing/fixtures/code-context'
    assert context.query_graph(fixture, fixture / 'graph.json', 'OrderService')['status'] == 'matches'
