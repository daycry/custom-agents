#!/usr/bin/env python3
"""Tests de redact.py (session-end-durable-capture T-02, CA-11). Ejecutar:
python3 -m pytest -q agent-kits/shared/test_redact.py

Extraído de `journal.py:redactar` (única fuente): mismos casos de redacción que ya cubría
`test_journal.py` — claves de API con prefijo conocido, JWT, bloques PEM, `Bearer`, `clave|token|
password… = valor`, sin falsos positivos evidentes."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "redact.py")

spec = importlib.util.spec_from_file_location("redact", SCRIPT)
redact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(redact)


def test_redacta_api_key_con_prefijo_conocido():
    assert redact.redactar("api_key=AKIAIOSFODNN7EXAMPLE1") == f"api_key={redact.REDACTADO}"


def test_redacta_bearer():
    assert redact.redactar("Bearer AbCdEfGhIjKlMnOpQrStUvWxYz0123456789") == f"Bearer {redact.REDACTADO}"


def test_redacta_jwt():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dQw4w9WgXcQ_abcdefghij"
    assert redact.REDACTADO in redact.redactar(f"token: {jwt}")


def test_redacta_bloque_pem():
    pem = "-----BEGIN PRIVATE KEY-----\nMIIBVQ==\n-----END PRIVATE KEY-----"
    assert redact.redactar(pem) == redact.REDACTADO


def test_sin_falsos_positivos():
    for limpio in ("tokens por hora (479326)", "password reset flow", "hola mundo"):
        assert redact.redactar(limpio) == limpio


def test_solo_stdlib():
    src = open(SCRIPT, encoding="utf-8").read()
    for prohibido in ("import requests", "import urllib.request"):
        assert prohibido not in src


@pytest.mark.parametrize('case', ['pem', 'assignment', 'quoted_json', 'show'])
def test_bounded_memory_inputs_redact_without_superlinear_delay(tmp_path, case):
    """A pathological owned input cannot occupy the serial memory endpoint."""
    pem = '-----BEGIN PRIVATE KEY-----\nx' * 9000
    payload = {'pem': pem, 'assignment': 'token=' * 43000,
               'quoted_json': '"token":"' + '\\a' * 125000}.get(case, pem)
    own = tmp_path / 'owned'
    own.mkdir()
    fixture = own / 'input.txt'
    fixture.write_text(payload, encoding='utf8', newline='')
    root = own / 'project'
    entry = root / 'docs/knowledge/adr/ADR-001.md'
    if case == 'show':
        entry.parent.mkdir(parents=True)
        entry.write_text('---\nid: ADR-001\nestado: aceptada\ntitulo: Owned\narea: Cache\n---\n' + payload,
                         encoding='utf8', newline='')
        assert entry.stat().st_size <= 256 * 1024
    for variable in ('HOME','USERPROFILE','PROGRAMDATA','APPDATA','LOCALAPPDATA','TEMP','TMP',
                     'CODEX_HOME','CLAUDE_CONFIG_DIR','XDG_CONFIG_HOME'):
        (own / variable.lower()).mkdir()
    env = {'PATH': os.environ.get('PATH',''), 'SystemRoot': os.environ.get('SystemRoot','C:/Windows'),
           'PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONIOENCODING':'utf8',
           **{name:str(own / name.lower()) for name in ('HOME','USERPROFILE','PROGRAMDATA','APPDATA',
                'LOCALAPPDATA','TEMP','TMP','CODEX_HOME','CLAUDE_CONFIG_DIR','XDG_CONFIG_HOME')}}
    program = '''import importlib.util,pathlib,sys,time
script,fixture,case,root=sys.argv[1:]
spec=importlib.util.spec_from_file_location('owned_redactor',script)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
started=time.monotonic()
if case=='show':
    result=module.query(root,operation='show',id='ADR-001')
    assert result['selected']['id']=='ADR-001' and len(result['selected']['texto'])<=12000
    assert result['status']=='partial' and 'text_budget' in result['issues']
else:
    text=pathlib.Path(fixture).read_text(encoding='utf8')
    assert module.redactar(text)==text
print(round(time.monotonic()-started,4))
'''
    script = str(Path(HERE) / ('knowledge-view.py' if case == 'show' else 'redact.py'))
    try:
        result = subprocess.run([sys.executable,'-X','utf8','-B','-c',program,script,str(fixture),case,str(root)],
                                cwd=own,env=env,capture_output=True,encoding='utf8',errors='replace',timeout=3)
    except subprocess.TimeoutExpired:
        pytest.fail('owned bounded input exceeded 3s redaction deadline: ' + case)
    assert result.returncode == 0, result.stdout + result.stderr
    assert float(result.stdout.strip()) < 1.5


@pytest.mark.parametrize('text', [
    'before -----BEGIN PRIVATE KEY-----\ndata\n-----END PRIVATE KEY----- after',
    '-----BEGIN RSA PRIVATE KEY-----x-----END OPENSSH PRIVATE KEY-----',
    '-----BEGIN  PRIVATE KEY-----x-----END EC PRIVATE KEY-----',
    '-----BEGIN PRIVATE KEY-----a-----BEGIN EC PRIVATE KEY-----b-----END PRIVATE KEY-----c-----END EC PRIVATE KEY-----',
    '-----BEGIN PRIVATE KEY-----x-----END PRIVATE KEY----- -----BEGIN DSA PRIVATE KEY-----y-----END DSA PRIVATE KEY-----',
    '-----END PRIVATE KEY----- -----BEGIN PRIVATE KEY-----unterminated',
    '-----BEGIN private key-----unchanged-----END private key-----',
    '-----BEGIN RSA2 PRIVATE KEY-----unchanged-----END RSA2 PRIVATE KEY-----',
    '-----BEGIN PRIVATE KEY-----unfinished -----BEGIN EC PRIVATE KEY-----x-----END EC PRIVATE KEY-----',
])
def test_linear_pem_preserves_previous_marker_semantics(text):
    import re
    previous = re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----', re.S)
    assert redact.redactar(text) == previous.sub(redact.REDACTADO, text)


def test_linear_assignment_preserves_previous_precision_and_greedy_values():
    import random
    import re
    previous = re.compile(r'(?i)(?P<pre>\b(?:' + redact._CLAVES_SENSIBLES + r')\b\s*[:=]\s*["\']?)'
                          r'(?P<sec>(?=[^\s"\']*[A-Za-z])(?=[^\s"\']*[0-9!@#$%^&*])[^\s"\']{8,})')
    rng = random.Random(20261009)
    keys = ['token','secret','api_key','password','pwd','contraseña','Password','token_hint']
    values = ['abcdef1234','abcdefghi','token=token=','token=123','İıſK1111','áéíóú1234','abcdefgh١٢٣٤',
              '1234567890','a!bcdefgh','a=bcdefgh','abc','\\abc123456','abcDEF$%&*','""abc12345']
    for _ in range(500):
        text = ''.join(rng.choice(keys) + rng.choice(['=',' = ',':\n','="',"='"]) +
                       rng.choice(values) + rng.choice([' ','\n',';','/']) for _ in range(8))
        expected = previous.sub(lambda match: match['pre'] + redact.REDACTADO, text)
        assert redact.redactar(text) == expected, repr(text)


def test_unterminated_pem_preserves_content_but_later_secret_is_redacted_before_clip():
    secret = 'sk-' + 'A' * 30
    text = '-----BEGIN PRIVATE KEY-----\n' + 'x' * 11965 + ' ' + secret + ' suffix'
    result = redact.redactar(text)
    assert result.startswith('-----BEGIN PRIVATE KEY-----\n')
    assert secret not in result and redact.REDACTADO in result
    assert 'sk-' not in result[:12000]


def test_journal_standalone_backup_has_helpers_in_its_own_globals():
    import re
    source = Path(HERE,'journal.py').read_text(encoding='utf8')
    start = source.index('# --8<-- redact (redactar + constantes)')
    end = source.index('# --8<-- fin redact (redactar + constantes)',start)
    namespace = {'re':re}
    exec(compile(source[start:end],'owned_journal_backup','exec'),namespace)
    text = '-----BEGIN RSA PRIVATE KEY-----x-----END EC PRIVATE KEY----- token=abc1234567'
    assert namespace['redactar'](text) == redact.redactar(text)


def test_journal_real_fallback_without_redact_module(tmp_path):
    """The shipped backup executes in journal's globals when its sibling is absent."""
    bundle = tmp_path / 'owned-journal'
    bundle.mkdir()
    for filename in ('journal.py', 'journal-capture.py'):
        (bundle / filename).write_bytes(Path(HERE, filename).read_bytes())
    assert not (bundle / 'redact.py').exists()
    spec = importlib.util.spec_from_file_location('owned_journal_fallback', bundle / 'journal.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._redact_mod is None
    assert module._capture_mod is not None
    assert module.redactar.__globals__ is module.__dict__
    for text in (
        '-----BEGIN RSA PRIVATE KEY-----x-----END EC PRIVATE KEY----- token=abc1234567',
        '-----BEGIN PRIVATE KEY-----\nx' * 9000,
        'token=' * 43000,
        '{"token":"a\\\"b c"}',
    ):
        assert module.redactar(text) == redact.redactar(text)


def test_139_redacta_el_par_json_de_una_clave_sensible():
    """#139 (training-data-services fix2, CWE-312): la forma JSON `"password": "…"` no casaba con
    `password=`/`password:` (la comilla de cierre de la clave va antes de los dos puntos)."""
    import json
    for clave in ("password", "api_key", "token", "secret", "Password", "API-KEY", "contraseña", "pwd"):
        texto = json.dumps({clave: "hunter2", "otro": "valor"}, ensure_ascii=False)
        salida = redact.redactar(texto)
        assert "hunter2" not in salida, clave
        assert json.loads(salida) == {clave: redact.REDACTADO, "otro": "valor"}, clave
    assert redact.redactar('{"token" :  "a\\"b c"}') == '{"token" :  "' + redact.REDACTADO + '"}'
    assert redact.redactar("{'password': 'hunter2'}") == "{'password': '" + redact.REDACTADO + "'}"


def test_139_par_json_de_una_clave_no_sensible_no_se_toca():
    for limpio in ('{"tokens": "479326"}', '{"passwordless": "si"}', '{"nota": "password"}',
                   '{"password_hint": "el perro"}', '{"password": ""}', '{"token": 5}'):
        assert redact.redactar(limpio) == limpio, limpio


def test_139_es_clave_sensible():
    for k in ("password", "PASSWD", "api_key", "api-key", "apikey", "secret_key", "access_key", "token", "clave"):
        assert redact.es_clave_sensible(k), k
    for k in ("tokens", "my_password", "passwordless", "clave_foranea", "", "nota"):
        assert not redact.es_clave_sensible(k), k


# ------------------------------------------------------------------ training-data-services T-10 fix2 #178
# `journal.py` es fichero de la iniciativa `training-data-services` (copia declarada de `redactar`,
# `copias.json` `redact_redactar`, #139) y el gate de cobertura de la iniciativa —sin `[run] patch =
# subprocess`— lo mide: su CLI solo lo ejercitaban subprocesos (`test_journal.py`). Estos tests lo llaman
# EN PROCESO; los helpers vienen de `test_journal.py`, cargado por ruta (sus tests no se recogen aqui).
import json  # noqa: E402

_TJ_SPEC = importlib.util.spec_from_file_location("test_journal_helpers_178", os.path.join(HERE, "test_journal.py"))
_tj = importlib.util.module_from_spec(_TJ_SPEC)
_TJ_SPEC.loader.exec_module(_tj)
journal = _tj.journal
proyecto, _payload, session_end_payload, _entrada = _tj.proyecto, _tj._payload, _tj.session_end_payload, _tj._entrada


def _main(monkeypatch, capsys, *args, stdin=None):
    import io
    if stdin is not None:
        monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    rc = journal.main([str(a) for a in args])
    salida = capsys.readouterr()
    return rc, salida.out, salida.err


def test_t10fix2_178_cli_en_proceso_capture_replay_status_recover_purge(tmp_path, monkeypatch, capsys):
    proj, _ = proyecto(tmp_path, con_git=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    assert _main(monkeypatch, capsys, "capture", "--root", proj,
                 stdin=json.dumps(_payload(prompt="decidimos usar FTS5"))) == (0, "", "")
    assert _main(monkeypatch, capsys, "capture", "--root", proj, stdin="{roto") == (0, "", "")
    assert _main(monkeypatch, capsys, "capture-end", "--root", proj,
                 stdin=json.dumps(session_end_payload(proj))) == (0, "", "")
    assert _main(monkeypatch, capsys, "capture-end", stdin="[1]") == (0, "", "")
    rc, out, _ = _main(monkeypatch, capsys, "replay", "--root", proj, "--ia", "no")
    assert rc == 0 and json.loads(out)["materializados"] == 1
    real = journal.replay

    def roto(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(journal, "replay", roto)
    rc, out, _ = _main(monkeypatch, capsys, "replay", "--root", proj)
    assert rc == 0 and json.loads(out)["errores"][0]["causa"] == "boom"
    monkeypatch.setattr(journal, "replay", real)
    rc, out, _ = _main(monkeypatch, capsys, "status", "--root", proj)
    assert rc == 0 and out.strip()
    rc, out, _ = _main(monkeypatch, capsys, "status", "--root", proj, "--json")
    assert rc == 0 and isinstance(json.loads(out), dict)
    rc, out, _ = _main(monkeypatch, capsys, "recover", "--root", proj)
    assert rc == 0 and isinstance(json.loads(out), dict)
    assert _main(monkeypatch, capsys, "purge", "--root", proj)[0] == 2
    rc, out, _ = _main(monkeypatch, capsys, "purge", "--root", proj, "--confirm")
    assert rc == 0 and "purgado" in json.loads(out)
    monkeypatch.setattr(journal, "_outbox_mod", lambda: None)
    rc, _out, err = _main(monkeypatch, capsys, "purge", "--root", proj, "--confirm")
    assert rc == 0 and "degradado" in err


def test_t10fix2_178_cli_en_proceso_draft_write_latest_index_candidatas(tmp_path, monkeypatch, capsys):
    proj, _ = proyecto(tmp_path, con_git=False)
    rc, out, _ = _main(monkeypatch, capsys, "draft", "--root", proj, "--session-id", "s1", "--reason", "other")
    assert rc == 0 and json.loads(out)["session_id"] == "s1"
    borrador = tmp_path / "draft.json"
    borrador.write_text(out, encoding="utf-8")
    rc, out, _ = _main(monkeypatch, capsys, "write", "--root", proj, "--session-id", "s1", "--draft", borrador,
                       "--reason", "clear", "--ia", "off")
    assert rc == 0 and "journal" in out
    rc, out, _ = _main(monkeypatch, capsys, "write", "--root", proj, "--session-id", "s2", "--draft", "-", "--ia", "off",
                       stdin=json.dumps(dict(json.loads(borrador.read_text(encoding="utf-8")), resumen="desde stdin")))
    assert rc == 0 and "journal" in out
    assert _main(monkeypatch, capsys, "write", "--root", proj, "--session-id", "s3", "--draft",
                 tmp_path / "no-existe.json")[0] == 2
    rc, out, _ = _main(monkeypatch, capsys, "write", "--root", proj, "--session-id", "s4", "--ia", "off")
    assert rc == 0 and "journal" in out
    vacio = tmp_path / "sin-plugin"
    vacio.mkdir()
    assert _main(monkeypatch, capsys, "write", "--root", vacio, "--session-id", "s5", "--ia", "off") == (0, "", "")
    rc, out, _ = _main(monkeypatch, capsys, "latest", "--root", proj, "--n", "1")
    assert rc == 0 and out.strip()
    rc, out, _ = _main(monkeypatch, capsys, "index", "--root", proj)
    assert rc == 0 and "README" in out
    assert _main(monkeypatch, capsys, "candidatas", "--root", proj) == (0, "", "")
    _entrada(proj, "c1", "2026-09-01", pendientes=["Revisar la CI en Windows"])
    _entrada(proj, "c2", "2026-09-02", pendientes=["Revisar la CI en Windows"])
    rc, out, _ = _main(monkeypatch, capsys, "candidatas", "--root", proj)
    assert rc == 0 and "Revisar la CI en Windows" in out
    rc, out, _ = _main(monkeypatch, capsys, "candidatas", "--root", proj, "--json")
    assert rc == 0 and json.loads(out)[0]["estado"] == "propuesta"

    def roto(a):
        raise RuntimeError("inesperado")
    monkeypatch.setattr(journal, "cmd_latest", roto)
    rc, _out, err = _main(monkeypatch, capsys, "latest", "--root", proj)
    assert rc == 0 and "inesperado" in err


def test_t10fix2_178_status_con_cola_degradada_y_sin_outbox(tmp_path, monkeypatch):
    """#178: `status` nombra el remedio de cada degradacion y no lanza aunque `en_backoff`/`recover`
    fallen; sin `outbox.py`, contadores en 0 con el aviso."""
    proj, _ = proyecto(tmp_path, con_git=False)

    class _Ob:
        @staticmethod
        def estado(dir_):
            return {"outbox": 0, "processing": 1, "done": 0, "dead-letter": 1, "durabilidad": "degradada",
                    "permisos": "degradados", "reclamacion": "degradada", "en_backoff": 2}

        @staticmethod
        def en_backoff(dir_):
            raise RuntimeError("roto")

    def recover_roto(*a, **k):
        raise RuntimeError("roto")
    monkeypatch.setattr(journal, "_outbox_mod", lambda: _Ob())
    monkeypatch.setattr(journal, "recover", recover_roto)
    st = journal.status(str(proj))
    texto = " ".join(st["avisos"])
    for trozo in ("durabilidad", "permisos", "reclamacion", "backoff", "dead-letter", "processing"):
        assert trozo in texto, (trozo, texto)
    assert st["huerfanas"] == 0 and st["proxima_backoff"] is None
    monkeypatch.setattr(journal, "_outbox_mod", lambda: None)
    st = journal.status(str(proj))
    assert st["outbox"] == 0 and "degradado" in st["avisos"][0]


def test_t10fix2_178_ultimo_dead_letter_ramas(tmp_path):
    d = tmp_path / "cola"
    assert journal._ultimo_dead_letter(str(d)) is None
    (d / "dead-letter").mkdir(parents=True)
    assert journal._ultimo_dead_letter(str(d)) is None
    (d / "dead-letter" / "a.causa.json").write_text("{roto", encoding="utf-8")
    assert journal._ultimo_dead_letter(str(d)) is None
    (d / "dead-letter" / "a.causa.json").write_text("[1]", encoding="utf-8")
    assert journal._ultimo_dead_letter(str(d)) is None
    (d / "dead-letter" / "a.causa.json").write_text(json.dumps({"causa": "x", "intentos": 3}), encoding="utf-8")
    assert journal._ultimo_dead_letter(str(d)) == {"clave": "a", "causa": "x", "intentos": 3, "en": None}


def test_t10fix2_178_transcript_seguro_ramas(tmp_path, monkeypatch):
    permitido = tmp_path / "transcripts"
    permitido.mkdir()
    monkeypatch.setattr(journal, "_transcripts_permitidos_root", lambda: str(permitido))
    bueno = permitido / "s1.jsonl"
    bueno.write_text("{}\n", encoding="utf-8")
    assert journal._transcript_seguro(str(bueno), "s1") == str(bueno)
    assert journal._transcript_seguro("rel/s1.jsonl", "s1") is None
    assert journal._transcript_seguro(str(bueno), "otro") is None
    fuera = tmp_path / "fuera" / "s1.jsonl"
    fuera.parent.mkdir()
    fuera.write_text("{}\n", encoding="utf-8")
    assert journal._transcript_seguro(str(fuera), "s1") is None
    monkeypatch.setattr(journal.os.path, "islink", lambda p: True)
    assert journal._transcript_seguro(str(bueno), "s1") is None
    monkeypatch.undo()
    monkeypatch.setattr(journal, "_transcripts_permitidos_root", lambda: str(permitido))

    def islink_roto(p):
        raise OSError("no")
    monkeypatch.setattr(journal.os.path, "islink", islink_roto)
    assert journal._transcript_seguro(str(bueno), "s1") is None
    monkeypatch.undo()
    monkeypatch.setattr(journal, "_transcripts_permitidos_root", lambda: str(permitido))

    def commonpath_roto(ps):
        raise ValueError("otra unidad")
    monkeypatch.setattr(journal.os.path, "commonpath", commonpath_roto)
    assert journal._transcript_seguro(str(bueno), "s1") is None


def test_t10fix2_178_redactar_y_cerrojos(tmp_path, monkeypatch):
    assert "abc123XYZ789" not in journal.redactar("usa token=abc123XYZ789 ya")
    f = tmp_path / "cerrojo"
    f.write_bytes(b"x")
    fd = os.open(str(f), os.O_RDWR)
    try:
        assert journal._bloquear(fd) is True
        journal._desbloquear(fd)
    finally:
        os.close(fd)
    monkeypatch.setattr(journal.time, "sleep", lambda s: None)
    assert journal._bloquear(10 ** 6) is False                 # fd que no existe: degrada, no bloquea
    journal._desbloquear(10 ** 6)


def test_t10fix2_178_dir_de_la_cola_y_enrich_ramas(tmp_path, monkeypatch, capsys):
    """#178: `sesion.journal.dir` absoluto o fuera del proyecto cae al default con aviso; `--enrich`
    ilegible o que no es un objeto se ignora con aviso."""
    proj, _ = proyecto(tmp_path, con_git=False)
    dev = proj / ".claude" / "dev.json"
    for d in (str(tmp_path / "abs"), "C:x", "../fuera"):
        dev.write_text(json.dumps({"sesion": {"journal": {"dir": d}}}), encoding="utf-8")
        assert journal._journal_queue_dir(str(proj)).endswith(journal._DIR_DEFAULT), d
    capsys.readouterr()
    dev.write_text(json.dumps({"sesion": {"journal": {"dir": "cola-propia"}}}), encoding="utf-8")
    assert journal._journal_queue_dir(str(proj)) == os.path.join(str(proj), "cola-propia")
    avisos = []
    assert journal.cargar_enrich(None, avisos) == {}
    assert journal.cargar_enrich(str(tmp_path / "no-existe.json"), avisos) == {} and "ilegible" in avisos[0]
    lista = tmp_path / "lista.json"
    lista.write_text("[1]", encoding="utf-8")
    assert journal.cargar_enrich(str(lista), avisos) == {}
