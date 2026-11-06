import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/jira-sync/scripts/jira-flow.py'


def fixture(tmp_path):
    spec = importlib.util.spec_from_file_location('audit_jira_fixture', SCRIPT.with_name('test_jira_flow.py'))
    peer = importlib.util.module_from_spec(spec); spec.loader.exec_module(peer)
    root = tmp_path / 'project'; (root / '.claude').mkdir(parents=True)
    (root / '.claude/jira.json').write_text(json.dumps({'enabled': True, 'horasJornada': 1}), encoding='utf8')
    (root / '.claude/rates.json').write_text(json.dumps({'ratioSupervision': .5}), encoding='utf8')
    ledger = root / 'tasks.md'; ledger.write_text(peer.LEDGER, encoding='utf8')
    return root, ledger


def plan(root, ledger, *extra, cwd=None):
    result = subprocess.run([sys.executable, '-B', str(SCRIPT), 'plan', '--ledger', str(ledger),
        '--event', 'implementado', '--actor', 'implementer', '--task', 'T-01', '--issue', 'AUD-1', '--json', *extra],
        cwd=cwd or root, capture_output=True, text=True, encoding='utf8', timeout=20)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_r20_planned_comment_redacts_recognized_secret(tmp_path):
    root, ledger = fixture(tmp_path)
    secret = 'AuditSecret0123456789abcdef'
    text = ledger.read_text(encoding='utf8')
    text = text.replace('- **Descripci\u00f3n**:', '- **Descripci\u00f3n**: password=' + secret + ' ', 1)
    ledger.write_text(text, encoding='utf8')
    output = plan(root, ledger)
    assert any(op['tipo'] == 'comentario' for op in output['ops'])
    assert secret not in json.dumps(output), 'A recognized secret entered a Jira publication plan.'


def test_r22_nested_invocation_finds_parent_opt_in(tmp_path):
    root, ledger = fixture(tmp_path); nested = root / 'src/module'; nested.mkdir(parents=True)
    output = plan(root, ledger, cwd=nested)
    assert output['jira'] == 'activado' and output['ops']


def test_explicit_nested_root_does_not_inherit_parent_publication_opt_in(tmp_path):
    root, ledger = fixture(tmp_path); nested = root / 'independent'; nested.mkdir()
    output = plan(root, ledger, '--root', str(nested), cwd=nested)
    assert output['jira'] != 'activado' and output['ops'] == []


def test_r22_generated_commands_keep_config_and_state_from_foreign_cwd(tmp_path):
    root, ledger = fixture(tmp_path); selected = root / '.claude/chosen-state.json'
    foreign = tmp_path / 'foreign'; (foreign / '.claude').mkdir(parents=True)
    (foreign / '.claude/jira.json').write_text('{"enabled":true,"horasJornada":99}', encoding='utf8')
    output = plan(root, ledger, '--root', str(root), '--state', str(selected))
    worklog = next(op['comando'] for op in output['ops'] if op['tipo'] == 'worklog')
    result = subprocess.run(worklog, cwd=foreign, capture_output=True, text=True, encoding='utf8', timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['jornada'] == 1
    receipt = subprocess.run(output['confirmar'] + ['--json'], cwd=foreign, capture_output=True, text=True, encoding='utf8', timeout=20)
    assert receipt.returncode == 0, receipt.stdout + receipt.stderr
    assert json.loads(selected.read_bytes())['flow'][output['claveIdempotencia']]['estado'] == 'publicado'
    assert not (foreign / '.claude/jira-state.json').exists()
