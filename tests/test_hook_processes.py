"""Procesos por evento de hook (auditoría 2026-11-09, T-14: H-29, H-30 y H-31).

Cada caso copia el bundle (`hooks/` y `agent-kits/shared/`) a un directorio temporal y lanza
`node hooks/run-hook.mjs` como lo hace el runtime; los dobles que sustituyen a una pieza solo
escriben un marcador. Sin servidores ni procesos que sobrevivan al test.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
LEDGER_FUENTE = ROOT / 'docs' / 'roadmap' / '2026-09-02-adversarial-review' / 'tasks.md'

pytestmark = pytest.mark.skipif(NODE is None, reason='the launcher needs Node')


def _bundle(tmp_path):
    bundle = tmp_path / 'plugin'
    shutil.copytree(ROOT / 'hooks', bundle / 'hooks', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT / 'agent-kits' / 'shared', bundle / 'agent-kits' / 'shared',
                    ignore=shutil.ignore_patterns('__pycache__', 'test_*.py'))
    return bundle


def _project(tmp_path, activa=True):
    project = tmp_path / 'proj'
    ledger = project / 'docs' / 'roadmap' / '2026-01-01-demo' / 'tasks.md'
    ledger.parent.mkdir(parents=True)
    text = LEDGER_FUENTE.read_text(encoding='utf-8')
    if activa:
        text = text.replace('estado: completado', 'estado: en-progreso', 1)
    ledger.write_text(text, encoding='utf-8')
    (project / '.claude').mkdir()
    (project / '.claude' / 'dev.json').write_text('{}', encoding='utf-8')
    return project, ledger


def _launch(bundle, hook, project, payload, *, sin_bash=False, **extra_env):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project), CUSTOM_AGENTS_PYTHON=sys.executable, **extra_env)
    if sin_bash:
        absent = str(project / 'no-binaries')
        env.update(PATH=absent, Path=absent)
    return subprocess.run([NODE, str(bundle / 'hooks' / 'run-hook.mjs'), hook], cwd=project, env=env,
                          input=json.dumps(payload), capture_output=True, text=True, encoding='utf-8', timeout=60)


# ------------------------------------------------------------------ H-31: captura ligera

def test_h31_user_prompt_submit_captura_sin_cargar_journal_py(tmp_path):
    """H-31: UserPromptSubmit añadía una línea al log importando `journal.py` entero (2.978 líneas,
    ~1 s en Windows). La captura usa un módulo ligero: `journal.py` ni se carga."""
    bundle = _bundle(tmp_path)
    marca = tmp_path / 'journal-cargado'
    (bundle / 'agent-kits' / 'shared' / 'journal.py').write_text(
        'import os, pathlib\npathlib.Path(os.environ["MARCA_JOURNAL"]).write_text("cargado")\n', encoding='utf-8')
    project, _ = _project(tmp_path)
    result = _launch(bundle, 'user-prompt-capture.sh', project,
                     {'hook_event_name': 'UserPromptSubmit', 'session_id': 'h31', 'prompt': 'decidimos medir antes'},
                     MARCA_JOURNAL=str(marca))
    assert (result.returncode, result.stdout) == (0, ''), result.stderr
    assert not marca.exists(), 'la captura cargó journal.py'
    log = project / '.claude' / 'session-prompts-h31.log'
    registro = json.loads(log.read_text(encoding='utf-8').splitlines()[-1])
    assert registro['prompt'] == 'decidimos medir antes'
    assert 'session-prompts-*' in (project / '.claude' / '.gitignore').read_text(encoding='utf-8')


def test_h31_la_captura_ligera_respeta_private_y_el_opt_out(tmp_path):
    bundle = _bundle(tmp_path)
    project, _ = _project(tmp_path)
    _launch(bundle, 'user-prompt-capture.sh', project, {'session_id': 'p', 'prompt': 'algo <PRIVATE> secreto'})
    assert not (project / '.claude' / 'session-prompts-p.log').exists()
    (project / '.claude' / 'dev.json').write_text('{"sesion":{"captura":false}}', encoding='utf-8')
    _launch(bundle, 'user-prompt-capture.sh', project, {'session_id': 'q', 'prompt': 'normal'})
    assert not (project / '.claude' / 'session-prompts-q.log').exists()


# ------------------------------------------------------------------ H-30: SubagentStop en Python

def _esperado(project):
    salida = subprocess.run([sys.executable, str(ROOT / 'agent-kits' / 'shared' / 'progress-report.py'), 'active',
                             '--root', str(project / 'docs' / 'roadmap')],
                            capture_output=True, text=True, encoding='utf-8', check=True).stdout
    return json.dumps({'systemMessage': salida.rstrip('\n')}, ensure_ascii=False) + '\n'


def test_h30_subagent_stop_sin_bash_misma_salida_y_con_debounce(tmp_path):
    """H-30: SubagentStop encadenaba ~9 procesos (bash, cat, python3 dos veces…) y sin debounce
    repetía el mismo estado tras cada subagente. Ahora corre en Python, con la misma salida que el
    shell, y no repite la línea que el usuario ya vio (`.progress-last`, como `ledger-post.py`)."""
    bundle = _bundle(tmp_path)
    project, ledger = _project(tmp_path)
    payload = {'hook_event_name': 'SubagentStop', 'agent_type': 'implementer'}
    primera = _launch(bundle, 'subagent-progress.sh', project, payload, sin_bash=True)
    assert (primera.returncode, primera.stderr) == (0, ''), primera.stderr
    assert primera.stdout == _esperado(project)
    segunda = _launch(bundle, 'subagent-progress.sh', project, payload, sin_bash=True)
    assert (segunda.returncode, segunda.stdout, segunda.stderr) == (0, '', '')
    ledger.write_text(ledger.read_text(encoding='utf-8').replace('- **Estado**: completado', '- **Estado**: en-progreso', 1),
                      encoding='utf-8')
    tercera = _launch(bundle, 'subagent-progress.sh', project, payload, sin_bash=True)
    assert tercera.stdout == _esperado(project) and tercera.stdout != primera.stdout


def test_h30_subagent_stop_sin_activas_no_emite(tmp_path):
    bundle = _bundle(tmp_path)
    project, _ = _project(tmp_path, activa=False)
    result = _launch(bundle, 'subagent-progress.sh', project, {'hook_event_name': 'SubagentStop'}, sin_bash=True)
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')


# ------------------------------------------------------------------ H-29: sin Python de limpieza

def _supervisor_con_registro(bundle):
    sup = bundle / 'hooks' / 'runtime-supervisor.py'
    sup.write_text('import os as _o, sys as _s\nopen(_o.environ["SUP_LOG"], "a").write(_s.argv[1] + "\\n")\n'
                   + sup.read_text(encoding='utf-8'), encoding='utf-8')


@pytest.mark.skipif(os.name != 'nt', reason='Job Objects only exist on Windows')
def test_h29_sin_python_de_limpieza_cuando_el_job_queda_vacio(tmp_path):
    """H-29: en Windows cada hook lanzaba un segundo Python (`runtime-supervisor.py close`) aunque
    el hijo terminase limpio. El supervisor avisa de que su job quedó vacío y el lanzador no limpia."""
    bundle = _bundle(tmp_path)
    _supervisor_con_registro(bundle)
    log = tmp_path / 'supervisor.log'
    project, _ = _project(tmp_path)
    result = _launch(bundle, 'session-journal.sh', project, {}, SUP_LOG=str(log))
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')
    assert log.read_text(encoding='utf-8').split() == ['run']


@pytest.mark.skipif(os.name != 'nt', reason='Job Objects only exist on Windows')
def test_h29_con_un_descendiente_vivo_la_limpieza_sigue(tmp_path):
    bundle = _bundle(tmp_path)
    _supervisor_con_registro(bundle)
    log = tmp_path / 'supervisor.log'
    marca = tmp_path / 'huerfano.txt'
    (bundle / 'agent-kits' / 'shared' / 'journal-capture.py').write_text(
        'import subprocess, sys\n'
        'subprocess.Popen([sys.executable, "-I", "-S", "-c", "import time, pathlib; time.sleep(3); '
        'pathlib.Path(%r).write_text(\'huerfano\')"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n' % str(marca),
        encoding='utf-8')
    project, _ = _project(tmp_path)
    result = _launch(bundle, 'session-journal.sh', project, {}, SUP_LOG=str(log))
    assert result.returncode == 0, result.stderr
    assert log.read_text(encoding='utf-8').split() == ['run', 'close']
    import time
    time.sleep(3.5)
    assert not marca.exists(), 'el descendiente sobrevivió a la limpieza'
