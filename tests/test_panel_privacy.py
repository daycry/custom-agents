"""CA-41 on the activity history (panel-redesign T-51): no home path, user name or e-mail in `events.json`, in the
served activity APIs or in the exported panel.

The account name is anonymized as a whole word, as `redact.anonimizar` defines it (T-04): a name glued to other word
characters or hyphens (`notes-jdoe.txt`) is outside that rule, so the corpus uses it as a word and as a path component.

The tool events are captured by the REAL store (`agent-activity-store.capture`) with arguments that carry the
project root, a home outside the project, the account name and e-mails. The served answers use the panel's single
scrubber (`build_panel._scrubber`), the same one `--serve` passes to the server.
"""
import importlib.util
import json
import os
from pathlib import Path
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
USER = 'jdoeprivacy'
MAIL = 'ana.lopez@example.com'


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def world(tmp_path, monkeypatch):
    home = tmp_path / ('home-' + USER)
    project = home / 'work' / 'proyecto'
    (project / '.claude').mkdir(parents=True)
    (project / '.claude/dev.json').write_text('{"sesion":{"actividad":true}}', encoding='utf-8')
    for name in ('HOME', 'USERPROFILE'):
        monkeypatch.setenv(name, str(home))
    for name in ('USERNAME', 'USER', 'LOGNAME'):
        monkeypatch.setenv(name, USER)
    store = load('privacy_activity_store', 'agent-kits/shared/agent-activity-store.py')
    payloads = [
        ('Bash', {'command': 'cat %s/notes.txt && mail %s && echo hola %s' % (home, MAIL, USER)}),
        ('Read', {'file_path': str(project / 'docs' / USER / 'informe.md')}),
        ('Grep', {'pattern': MAIL, 'path': str(home / 'otros')}),
        ('Edit', {'file_path': str(home / '.ssh' / 'config')}),
        ('WebFetch', {'url': 'https://%s:secret@intranet.example/%s' % (USER, MAIL)}),
        ('Agent', {'subagent_type': 'custom-agents:qa', 'prompt': 'PRIVATE PROMPT %s %s' % (USER, MAIL)}),
        ('Bash', {'command': 'python3 %s/agent-kits/shared/usage-meter.py start --artefacto panel/T-07' % home}),
    ]
    for tool, arguments in payloads:
        payload = {'hook_event_name': 'PostToolUse', 'session_id': 'session-%s' % USER, 'cwd': str(project),
                   'tool_name': tool, 'tool_input': arguments, 'tool_response': {'stdout': 'RAW %s %s' % (USER, MAIL)}}
        assert store.capture(project, runtime='claude', payload=payload)['status'] == 'ok', tool
    return types.SimpleNamespace(home=home, project=project, store=store)


def personal(world):
    """Every spelling of the personal data that must never leave the machine."""
    values = {str(world.home), str(world.home).replace('\\', '/'), str(world.project), str(world.project).replace('\\', '/'),
              USER, USER.upper(), MAIL}
    return [value.encode('utf-8') for value in values]


def assert_clean(blob, world, where):
    for value in personal(world):
        assert value.lower() not in blob.lower(), (where, value)


def test_events_json_has_no_personal_data(world):
    raw = (world.project / '.claude/agent-activity/events.json').read_bytes()
    doc = json.loads(raw)
    assert len(doc['events']) == 7
    assert_clean(raw, world, 'events.json')
    assert b'PRIVATE PROMPT' not in raw and b'RAW ' not in raw


def test_served_activity_apis_have_no_personal_data(world):
    builder = load('privacy_build_panel', 'skills/plugin-panel/scripts/build_panel.py')
    server_module = load('privacy_serve_panel', 'skills/plugin-panel/scripts/serve_panel.py')
    args = types.SimpleNamespace(project=str(world.project), root=str(ROOT), home=None)
    scrub = builder._scrubber(args)
    data = builder.build_inventory(ROOT / 'tests/fixtures/panel-redesign/bundle', runtime='all', scrub=scrub)
    server = server_module.create_server(world.project, data, scrub=scrub)
    try:
        runs = server.actividad_runs()
        listing = json.loads(runs)
        assert listing['status'] == 'ok' and len(listing['recientes']) == 7
        assert_clean(runs, world, 'api/actividad-runs')
        for row in listing['runs']:
            timeline = server.actividad_run(row['key16'])
            assert json.loads(timeline)['status'] == 'ok'
            assert_clean(timeline, world, 'api/actividad-run-' + row['key16'])
            assert b'PRIVATE PROMPT' not in timeline and b'RAW ' not in timeline
        for name, page in server.pages.items():
            assert_clean(page, world, name)
    finally:
        server.server_close()


def test_exported_panel_has_no_personal_data_and_no_events(world, tmp_path):
    builder = load('privacy_build_panel_export', 'skills/plugin-panel/scripts/build_panel.py')
    out = tmp_path / 'export'
    assert builder.main(['--root', str(ROOT / 'tests/fixtures/panel-redesign/bundle'), '--project', str(world.project),
                         '--export', str(out)]) == 0
    files = [path for path in out.rglob('*') if path.is_file() and 'vendor' not in path.parts]
    assert files
    for path in files:
        blob = path.read_bytes()
        assert_clean(blob, world, path.name)
        assert b'git status' not in blob and b'usage-meter.py start' not in blob  # no event crosses to the static copy
