"""Native command projections preserve canonical workflows and literal shell syntax."""
import importlib.util
import json
from pathlib import Path
import re
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('command_transport_export', ROOT / 'scripts/export-interop.py')
MOD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MOD)
ADAPTER_ROOT = 'interop/codex/command-skills'


def test_plugin_keeps_canonical_skills_and_registers_command_adapter_root():
    manifest = json.loads(MOD.codex_plugin_json(str(ROOT)))
    assert manifest['skills'] == ['./skills/', './' + ADAPTER_ROOT + '/']


@pytest.mark.parametrize('body', [
    'Use $ARGUMENTS as input. Keep $HOME, ${HOME}, $PWD and $$ literally.\n',
    'PowerShell: $env:USERPROFILE; $ReviewPython; $REVIEW_RUNTIME; Unicode ü.\n',
])
def test_native_adapter_preserves_literal_body_and_uses_explicit_invocation(body):
    files = MOD.codex_command_skill('demo', 'description: Demo: literal\nargument-hint: [initiative]', body)
    assert set(files) == {'SKILL.md', 'agents/openai.yaml', 'references/command.md'}
    frontmatter, wrapper = MOD.partir_frontmatter(files['SKILL.md'])
    assert MOD.campo(frontmatter, 'name') == 'custom-agents-demo'
    assert MOD.campo(frontmatter, 'description')
    assert len(files['SKILL.md'].splitlines()) <= 200
    assert 'references/command.md' in wrapper and '$custom-agents:custom-agents-demo' in wrapper
    assert '[initiative]' in wrapper
    assert files['references/command.md'].endswith(body)
    assert re.search(r'(?m)^policy:\n  allow_implicit_invocation: false$', files['agents/openai.yaml'])


def test_all_commands_have_one_distinct_native_adapter_and_no_personal_prompt_projection():
    plan = MOD.generar(str(ROOT))
    commands = [name for name, _, _ in MOD.piezas(str(ROOT), 'commands')]
    assert not any(path.startswith('interop/codex/prompts/') for path in plan)
    adapter_names = set()
    for name in commands:
        directory = ADAPTER_ROOT + '/custom-agents-' + name
        assert all(directory + '/' + part in plan
                   for part in ('SKILL.md', 'agents/openai.yaml', 'references/command.md'))
        frontmatter, _ = MOD.partir_frontmatter(plan[directory + '/SKILL.md'])
        adapter_names.add(MOD.campo(frontmatter, 'name'))
    canonical_names = {
        MOD.campo(MOD.partir_frontmatter(path.read_text(encoding='utf-8'))[0], 'name')
        for path in (ROOT / 'skills').glob('*/SKILL.md')
    }
    assert len(adapter_names) == len(commands) and not adapter_names.intersection(canonical_names)
    assert 'confluence-pull' in canonical_names and 'custom-agents-confluence-pull' in adapter_names


def test_retire_only_owned_personal_prompt_exports(tmp_path, capsys):
    folder = tmp_path / 'interop/codex/prompts'
    folder.mkdir(parents=True)
    owned = folder / 'demo.md'
    owned.write_text('---\ndescription: Legacy\n---\n' +
                     MOD.cabecera('html', 'commands/demo.md') + 'legacy body\n', encoding='utf-8')
    foreign = folder / 'personal.md'
    foreign.write_text('My personal prompt.\n', encoding='utf-8')
    assert MOD.comprobar(str(tmp_path), {}) == 1
    assert 'OBSOLETO' in capsys.readouterr().out
    assert MOD.escribir(str(tmp_path), {}, quiet=True) == 0
    assert not owned.exists() and foreign.read_text(encoding='utf-8') == 'My personal prompt.\n'


@pytest.mark.parametrize('name', ['../escape', 'Bad Name', '', 'double--dash', 'a' * 51])
def test_invalid_command_name_cannot_become_a_native_path(name):
    with pytest.raises(ValueError, match='command'):
        MOD.codex_command_skill(name, 'description: Demo', 'Body\n')


def transport_repository(tmp_path):
    for relative in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json',
                     'hooks/hooks.json', 'hooks/opencode-plugin.js'):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    (tmp_path / 'agents').mkdir()
    (tmp_path / 'commands').mkdir()
    (tmp_path / 'commands/demo.md').write_text('---\ndescription: Demo\n---\nBody\n', encoding='utf-8')
    (tmp_path / 'skills/different-folder').mkdir(parents=True)
    return tmp_path


def test_collision_uses_declared_skill_name_not_directory_name(tmp_path):
    root = transport_repository(tmp_path)
    (root / 'skills/different-folder/SKILL.md').write_text(
        '---\nname: "custom-agents-demo"\ndescription: Personal skill\n---\nBody\n', encoding='utf-8')
    with pytest.raises(ValueError, match='collision'):
        MOD.generar(str(root))


def test_deleted_command_retires_its_three_owned_exports_only(tmp_path):
    directory = tmp_path / ADAPTER_ROOT / 'custom-agents-demo'
    for relative, style in [('SKILL.md', 'html'), ('agents/openai.yaml', 'toml'),
                            ('references/command.md', 'html')]:
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(MOD.cabecera(style, 'commands/demo.md') + 'old body\n', encoding='utf-8')
    personal = directory / 'personal.txt'
    personal.write_text('keep me', encoding='utf-8')
    assert set(MOD.obsoletos(str(tmp_path), {})) == {
        ADAPTER_ROOT + '/custom-agents-demo/' + part
        for part in ('SKILL.md', 'agents/openai.yaml', 'references/command.md')}
    assert MOD.escribir(str(tmp_path), {}, quiet=True) == 0
    assert personal.read_text(encoding='utf-8') == 'keep me'
    assert not (directory / 'SKILL.md').exists()


def test_retirement_does_not_follow_linked_export_directory(tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    target = outside / 'demo.md'
    target.write_text(MOD.cabecera('html', 'commands/demo.md') + 'keep me\n', encoding='utf-8')
    parent = tmp_path / 'interop/codex'
    parent.mkdir(parents=True)
    try:
        (parent / 'prompts').symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip('Directory symlink unavailable: ' + str(error))
    assert MOD.obsoletos(str(tmp_path), {}) == []
    assert target.read_text(encoding='utf-8').endswith('keep me\n')


@pytest.mark.parametrize('document', ['README.md', 'README.es.md', 'docs/README.md',
                                    'docs/en/README.md', 'docs/INSTALL.md', 'docs/en/INSTALL.md',
                                    'docs/INTEROP.md', 'docs/en/INTEROP.md'])
def test_A22_1_documented_native_invocations_resolve_to_packaged_adapters(document):
    text = (ROOT / document).read_text(encoding='utf-8')
    assert '/prompt:' not in text and '/prompts:' not in text, 'A22-1: obsolete personal prompt invocation'
    namespace = json.loads(MOD.codex_plugin_json(str(ROOT)))['name']
    names = re.findall(r'\$' + re.escape(namespace) + r':(custom-agents-[a-z0-9]+(?:-[a-z0-9]+)*)', text)
    assert names, 'A22-1: missing native invocation example'
    plan = MOD.generar(str(ROOT))
    assert all(ADAPTER_ROOT + '/' + name + '/SKILL.md' in plan for name in names)


@pytest.mark.parametrize('repair_header_only', [False, True])
def test_A22_2_block22_review_header_and_rows_reach_ledger_consumers(repair_header_only):
    path = ROOT / 'agent-kits/shared/ledger-lint.py'
    spec = importlib.util.spec_from_file_location('transport_ledger_reader', path)
    ledger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ledger)
    text = (ROOT / 'docs/roadmap/2026-10-07-catalog-capabilities/tasks.md').read_text(encoding='utf-8')
    text = text.split('## Transporte nativo de comandos — Bloque22 en preparación', 1)[1]
    if repair_header_only:
        text = text.replace('intento 1 de 3: Bloque22', 'intento 1: Bloque22')
    sections = ledger.secciones_revision(text)
    first = next((section for section in sections if section['intento'] == 1), None)
    assert first is not None, 'A22-2: review header is invisible to the shared ledger reader'
    assert len(first['filas']) == 2, 'A22-2: shared reader must recover both recorded findings'
    assert {row['grado'] for row in first['filas']} == {'Critical', 'Important'}
    assert all(ledger.ids_de_tarea(row['tarea']) for row in first['filas'])
    assert any('B-01' in row['gap'] for row in first['filas'])
    assert any('A22-1' in row['gap'] for row in first['filas'])
