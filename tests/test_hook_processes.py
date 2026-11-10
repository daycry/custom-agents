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


# ------------------------------------------------- revisión intento 1 (fase 3): T-14

def _captura_directa(project, raw):
    return subprocess.run([sys.executable, str(ROOT / 'agent-kits/shared/journal-prompt.py'), '--root', str(project)],
                          input=raw, capture_output=True, timeout=60)


def test_fix1_b4_un_prompt_enorme_se_recorta_y_no_se_descarta(tmp_path):
    """B4: un payload de más de 2 MiB se descartaba entero; antes se guardaba recortado a 4.000
    caracteres, como ahora."""
    project, _ = _project(tmp_path)
    payload = json.dumps({'session_id': 'grande', 'prompt': 'decidimos ' + 'x' * (3 * 1024 * 1024)}).encode()
    result = _captura_directa(project, payload)
    assert (result.returncode, result.stdout, result.stderr) == (0, b'', b'')
    registro = json.loads((project / '.claude/session-prompts-grande.log').read_text(encoding='utf-8').splitlines()[-1])
    assert registro['prompt'].startswith('decidimos x') and registro['prompt'].endswith('[recortado]')


def test_fix1_b4_utf8_invalido_se_lee_con_reemplazo(tmp_path):
    """B4: un byte UTF-8 inválido hacía perder el turno; antes se leía con `errors=replace`."""
    project, _ = _project(tmp_path)
    raw = b'{"session_id": "roto", "prompt": "hola \xff mundo"}'
    assert _captura_directa(project, raw).returncode == 0
    registro = json.loads((project / '.claude/session-prompts-roto.log').read_text(encoding='utf-8').splitlines()[-1])
    assert registro['prompt'] == 'hola \ufffd mundo'


def test_fix1_b5_el_supervisor_conserva_el_codigo_original_si_no_marca():
    """B5: cualquier código fuera de 0..255 pasaba a 1 aunque el job no estuviera vacío (se perdía
    p. ej. 0xC0000005). Solo un código que imite la marca se normaliza."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('fix1_supervisor', ROOT / 'hooks' / 'runtime-supervisor.py')
    sup = importlib.util.module_from_spec(spec); spec.loader.exec_module(sup)
    flag = sup.JOB_EMPTY
    for vacio in (True, False):
        sup.job_is_empty = lambda vacio=vacio: vacio
        assert sup.with_empty_job(0xC0000005) == 0xC0000005
        assert sup.with_empty_job(-3) == -3
        assert sup.with_empty_job(flag | 2) == (1 | flag if vacio else 1)   # nadie imita la marca
        assert sup.with_empty_job(2) == (2 | flag if vacio else 2)


def test_fix1_bnota_subagent_stop_no_se_calla_por_la_linea_del_ledger(tmp_path):
    """B-nota: SubagentStop compartía `.progress-last` con ledger-post; tras editar el ledger dentro
    de un subagente (cuyo systemMessage puede no llegar al usuario) el cierre se callaba. Cada hook
    tiene ahora su propio último estado."""
    bundle = _bundle(tmp_path)
    project, _ = _project(tmp_path)
    (project / '.claude' / '.progress-last').write_text(_esperado(project) and json.loads(_esperado(project))['systemMessage'],
                                                       encoding='utf-8')
    result = _launch(bundle, 'subagent-progress.sh', project, {'hook_event_name': 'SubagentStop'}, sin_bash=True)
    assert result.stdout == _esperado(project), result.stderr


def test_fix1_a6_flows_describen_los_hooks_reales():
    for rel in ('docs/FLOWS.md', 'docs/en/FLOWS.md'):
        texto = (ROOT / rel).read_text(encoding='utf-8')
        assert 'journal-prompt.py' in texto and 'subagent-progress.py' in texto, rel
        assert '"journal.py capture (' not in texto, rel


# ------------------------------------------------- revisión intento 2 (fase 3): T-14

def test_fix2_5_el_ultimo_estado_de_subagent_stop_no_se_versiona():
    """5: `.claude/.progress-last-subagent` no casaba con `.claude/.progress-last.*` (exige un punto)."""
    r = subprocess.run(['git', 'check-ignore', '-q', '.claude/.progress-last-subagent'], cwd=ROOT)
    assert r.returncode == 0


def test_fix2_6_un_prompt_de_varios_mib_lleno_de_secretos_se_captura_rapido_y_redactado(tmp_path):
    """6: la captura redactaba el prompt ENTERO antes de recortarlo a 4.000 caracteres (2 MiB → 8,4 s;
    más de ~5 MiB superaba el `timeout: 5` del hook). Ahora redacta una ventana algo mayor que lo que
    guarda; ningún secreto queda visible, tampoco el que cruza el corte."""
    import importlib.util
    import time
    project, _ = _project(tmp_path)
    spec = importlib.util.spec_from_file_location('fix2_journal_prompt', ROOT / 'agent-kits/shared/journal-prompt.py')
    jp = importlib.util.module_from_spec(spec); spec.loader.exec_module(jp)
    redactados = []
    real = jp.redactar
    jp.redactar = lambda texto: redactados.append(len(texto)) or real(texto)
    secreto = 'ghp_' + 'A1b2' * 10
    trozo = f'password=hunter2xyz {secreto} '
    prompt = trozo * (6 * 1024 * 1024 // len(trozo))
    payload = json.dumps({'session_id': 'secretos', 'prompt': prompt}).encode()
    inicio = time.monotonic()
    jp.capture(str(project), json.loads(payload))
    assert max(redactados) <= jp.CAPTURA_MAX_CHARS + 64 * 1024, max(redactados)   # una ventana, no el prompt entero
    # fix3 (10): medida determinista en vez de un tope de tiempo: caracteres que pasan por `redactar`
    assert sum(redactados) <= 8 * (jp.CAPTURA_MAX_CHARS + jp.REDACCION_MARGEN), sum(redactados)
    result = _captura_directa(project, payload)
    assert result.returncode == 0
    texto = (project / '.claude/session-prompts-secretos.log').read_text(encoding='utf-8')
    registro = json.loads(texto.splitlines()[-1])
    assert 'hunter2' not in texto and 'A1b2A1b2' not in texto and 'ghp_A' not in texto
    assert registro['prompt'].endswith('[recortado]') and len(registro['prompt']) <= 4000 + 20


def test_fix2_9_observability_nombra_la_captura_real():
    for rel in ('docs/observability.md', 'docs/en/observability.md'):
        fila = next(l for l in (ROOT / rel).read_text(encoding='utf-8').splitlines() if 'UserPromptSubmit` hook' in l
                    or 'hook `UserPromptSubmit`' in l)
        assert 'journal-prompt.py' in fila and 'journal.py capture`' not in fila, rel


# ------------------------------------------------- revisión intento 3 (fase 3): T-14

def _jp():
    import importlib.util
    spec = importlib.util.spec_from_file_location('fix3_journal_prompt', ROOT / 'agent-kits/shared/journal-prompt.py')
    jp = importlib.util.module_from_spec(spec); spec.loader.exec_module(jp)
    return jp


def _pem(n):
    cuerpo = '\n'.join(('MII' + chr(65 + (n + k) % 26) * 61) for k in range(50))
    return f'-----BEGIN PRIVATE KEY-----\n{cuerpo}\n-----END PRIVATE KEY-----'


def _capturado(project, jp, sid, prompt):
    jp.capture(str(project), {'session_id': sid, 'prompt': prompt})
    return json.loads((project / f'.claude/session-prompts-{sid}.log').read_text(encoding='utf-8').splitlines()[-1])['prompt']


def _esperado_completo(jp, prompt):
    texto = jp.redactar(prompt.strip())
    return texto[:jp.CAPTURA_MAX_CHARS].rstrip() + ' …[recortado]' if len(texto) > jp.CAPTURA_MAX_CHARS else texto


@pytest.mark.parametrize('caso', ['seis_pem', 'bearer_en_el_borde', 'password_en_el_borde'])
def test_fix3_1_la_ventana_que_encoge_no_deja_ver_un_secreto_cortado(tmp_path, caso):
    """1 (CWE-532): la ventana de redacción encoge al redactar (un PEM de ~3,3 KiB queda en 19
    caracteres) y un secreto cortado en su borde acababa dentro de los 4.000 guardados sin redactar.
    El resultado es el mismo que redactar el turno entero y cortar a 4.000."""
    jp = _jp()
    project, _ = _project(tmp_path)
    borde = jp.CAPTURA_MAX_CHARS + jp.REDACCION_MARGEN
    if caso == 'seis_pem':
        cabeza = ' '.join(_pem(n) for n in range(5)) + ' relleno '
        prompt = cabeza + 'r' * (18885 - len(cabeza)) + _pem(5) + ' cola ' * 200
        fragmento = 'MII' + chr(65 + 5) * 20
    elif caso == 'bearer_en_el_borde':
        cabeza = ' '.join(_pem(n) for n in range(6)) + ' '
        prompt = cabeza + 'r' * (borde - len(cabeza) - 30) + ' Authorization: Bearer ' + 'Zq9' * 30 + ' fin'
        fragmento = 'Zq9Zq9'
    else:
        cabeza = ' '.join(_pem(n) for n in range(6)) + ' '
        prompt = cabeza + 'r' * (borde - len(cabeza) - 12) + ' password=S3cr3t!Valor#Largo fin'
        fragmento = 'S3cr3t'
    guardado = _capturado(project, jp, caso, prompt)
    assert fragmento not in guardado and 'BEGIN PRIVATE KEY-----\nMII' not in guardado
    assert guardado == _esperado_completo(jp, prompt)


def test_fix3_7_un_turno_de_31_mib_se_captura_recortado(tmp_path):
    """7: el tope de lectura de 32 MiB no tenía test (bajarlo a 2 MiB devolvía el B4 de fix1)."""
    project, _ = _project(tmp_path)
    payload = json.dumps({'session_id': 'enorme', 'prompt': 'decidimos ' + 'y' * (31 * 1024 * 1024)}).encode()
    result = _captura_directa(project, payload)
    assert (result.returncode, result.stdout, result.stderr) == (0, b'', b'')
    registro = json.loads((project / '.claude/session-prompts-enorme.log').read_text(encoding='utf-8').splitlines()[-1])
    assert registro['prompt'].startswith('decidimos y') and registro['prompt'].endswith('[recortado]')
