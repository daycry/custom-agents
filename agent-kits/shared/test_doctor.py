#!/usr/bin/env python3
"""Tests de doctor.py (superiority T-01). Ejecutar: python3 -m pytest -q agent-kits/shared/test_doctor.py

Proyectos TEMPORALES (nunca el repo real como sujeto de escritura) y, cuando hace falta comprobar
hooks roto/no ejecutable, un plugin temporal mínimo (`agents/` + `hooks/hooks.json`). Se afirma:
sin `.claude/` no hay ❌ y exit 0; `dev.json` corrupto o con valor fuera de vocabulario → ❌ con
arreglo; clave desconocida → ⚠️; hook sin script → ❌ y hook sin bit ejecutable → ⚠️; marcador del
meter sin cerrar → ⚠️ con `usage-meter.py close`; `precioTokens` a 0 → ⚠️ con `rates-verify`;
`--json` y MD llevan los MISMOS veredictos; exit 1 SOLO con ❌; el bloque de versión compara con
`.plugin-version-seen` sin afirmar nunca que haya actualización; y el diagnóstico no escribe nada
en el proyecto."""
import importlib.util
import json
import os
import re
import shutil
import shlex
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(HERE, "doctor.py")
_NODE_EXECUTABLE = shutil.which("node")

spec = importlib.util.spec_from_file_location("doctor", SCRIPT)
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)
_NATIVE_CODEX_QUERY = doctor._estado_codex_nativo


def test_panel_json_is_explicit_and_uses_portable_contract(monkeypatch, tmp_path, capsys):
    source = {'proyecto': str(tmp_path), 'bloques': [{'clave': 'plugin', 'titulo': 'PRIVATE',
              'lineas': [{'estado': 'error', 'que': 'registro en Codex', 'detalle': 'SECRET', 'arreglo': 'PRIVATE COMMAND'}]}],
              'acciones_prioritarias': {'acciones': [{'bloque': 'plugin', 'linea': 1}]}, 'exit': 1}
    calls = []
    monkeypatch.setattr(doctor, 'diagnostico', lambda *a, **k: calls.append(a) or source)
    assert doctor.main(['--root', str(tmp_path), '--panel-json']) == 1
    output = capsys.readouterr().out
    report = json.loads(output)
    assert report['producer'] == 'doctor' and report['summary']['error'] == 1
    assert report['checked_at'].endswith('Z') and len(calls) == 1
    assert 'SECRET' not in output and 'PRIVATE' not in output and str(tmp_path) not in output


def test_json_modes_are_mutually_exclusive(tmp_path):
    with pytest.raises(SystemExit) as result:
        doctor.main(['--root', str(tmp_path), '--json', '--panel-json'])
    assert result.value.code == 2


def test_panel_json_missing_helper_is_opaque_and_does_not_break_normal_json(monkeypatch, tmp_path, capsys):
    source = {'proyecto': str(tmp_path), 'bloques': [],
              'acciones_prioritarias': {'acciones': []}, 'exit': 0}
    monkeypatch.setattr(doctor, 'diagnostico', lambda *a, **k: source)
    monkeypatch.setattr(doctor, 'HERE', str(tmp_path/'PRIVATE_MISSING_HELPER'))
    assert doctor.main(['--root', str(tmp_path), '--panel-json']) == 2
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err.strip() == 'doctor: portable panel report unavailable'
    assert doctor.main(['--root', str(tmp_path), '--json']) == 0
    assert json.loads(capsys.readouterr().out) == source


def test_panel_json_uses_canonical_redactor_before_export(monkeypatch, tmp_path, capsys):
    toolkit = tmp_path/'trusted-kit'; toolkit.mkdir()
    shutil.copyfile(os.path.join(HERE, 'diagnostic-report.py'), toolkit/'diagnostic-report.py')
    (toolkit/'redact.py').write_text(
        "def redactar(text):\n    return text.replace('registro en Codex', 'git')\n", encoding='utf8')
    source = {'proyecto': str(tmp_path), 'bloques': [{'clave': 'plugin', 'lineas': [
        {'estado': 'error', 'que': 'registro en Codex'}]}],
        'acciones_prioritarias': {'acciones': [{'bloque': 'plugin', 'linea': 1}]}, 'exit': 1}
    monkeypatch.setattr(doctor, 'diagnostico', lambda *a, **k: source)
    monkeypatch.setattr(doctor, 'HERE', str(toolkit))
    assert doctor.main(['--root', str(tmp_path), '--panel-json']) == 1
    output = json.loads(capsys.readouterr().out)
    assert output['blocks'][0]['rows'][0]['label'] == 'git'


def test_panel_json_missing_redactor_does_not_export(monkeypatch, tmp_path, capsys):
    toolkit = tmp_path/'trusted-kit'; toolkit.mkdir()
    shutil.copyfile(os.path.join(HERE, 'diagnostic-report.py'), toolkit/'diagnostic-report.py')
    source = {'proyecto': str(tmp_path), 'bloques': [],
              'acciones_prioritarias': {'acciones': []}, 'exit': 0}
    monkeypatch.setattr(doctor, 'diagnostico', lambda *a, **k: source)
    monkeypatch.setattr(doctor, 'HERE', str(toolkit))
    assert doctor.main(['--root', str(tmp_path), '--panel-json']) == 2
    captured = capsys.readouterr()
    assert captured.out == '' and captured.err.strip() == 'doctor: portable panel report unavailable'

ICONOS = {v: k for k, v in doctor.ICONO.items()}


# ------------------------------------------------------------------ utilidades

def _isolated_subprocess_env(extra=None):
    keys = {"SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "PROCESSOR_ARCHITECTURE",
            "NUMBER_OF_PROCESSORS", "HOME", "USERPROFILE", "CODEX_HOME", "CLAUDE_CONFIG_DIR",
            "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME",
            "XDG_STATE_HOME", "TEMP", "TMP", "NO_COLOR", "PYTHONIOENCODING"}
    env = {k: v for k, v in os.environ.items() if k.upper() in keys}
    env["PATH"] = os.environ["CUSTOM_AGENTS_TEST_PATH"]
    env.update(extra or {})
    if os.name == "nt":
        env["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"
    return env


def run(*args, root=None):
    env = _isolated_subprocess_env()
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=root or ROOT, env=env)


def proyecto(tmp_path, **configs):
    """Proyecto temporal; cada kwarg `fichero=contenido` se escribe en `.claude/<fichero>`
    (str tal cual, dict serializado a JSON)."""
    proj = tmp_path / "proj"
    proj.mkdir(parents=True, exist_ok=True)
    if configs:
        (proj / ".claude").mkdir(exist_ok=True)
        for nombre, cont in configs.items():
            fn = nombre.replace("__", ".")
            (proj / ".claude" / fn).write_text(
                cont if isinstance(cont, str) else json.dumps(cont, indent=2), encoding="utf-8")
    return proj


def plugin(tmp_path, *, script_existe=True, ejecutable=True, version="9.9.9", dest=None):
    """Plugin temporal mínimo con un hook registrado (sin `scripts/lint_plugin.py`: fuerza la
    comprobación LOCAL equivalente del doctor). `dest` coloca la raíz donde haga falta (un
    `.claude/` copiado, el caché de plugins…) en vez de en `tmp_path/plug`."""
    plug = dest if dest is not None else tmp_path / "plug"
    (plug / "agents").mkdir(parents=True)
    (plug / "agents" / "demo.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
    (plug / ".claude-plugin").mkdir()
    (plug / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "custom-agents", "version": version}), encoding="utf-8")
    (plug / "hooks").mkdir()
    (plug / "hooks" / "hooks.json").write_text(json.dumps({"hooks": {"PostToolUse": [
        {"hooks": [{"type": "command", "command": 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/demo.sh"'}]}]}}),
        encoding="utf-8")
    if script_existe:
        h = plug / "hooks" / "demo.sh"
        h.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        os.chmod(h, 0o755 if ejecutable else 0o644)
    return plug


def lineas(inf, estado=None):
    out = [l for b in inf["bloques"] for l in b["lineas"]]
    return [l for l in out if estado is None or l["estado"] == estado]


def diag(proj, plug=None):
    return doctor.diagnostico(str(proj), str(plug) if plug else None)


def veredictos_md(texto):
    """Estados en orden de aparición leídos de las tablas MD (para comparar con el JSON)."""
    out = []
    for ln in texto.splitlines():
        m = re.match(r"^\|\s*(✅|⚠️|❌|ℹ️)\s*\|", ln)
        if m:
            out.append(ICONOS[m.group(1)])
    return out


def snapshot(d):
    out = {}
    for dirpath, dirnames, files in os.walk(d):
        dirnames.sort()
        for f in sorted(files):
            p = os.path.join(dirpath, f)
            out[os.path.relpath(p, d)] = (os.path.getsize(p), open(p, "rb").read())
    return out



@pytest.fixture(autouse=True)
def _registro_de_la_maquina_fuera(tmp_path_factory, monkeypatch):
    """Gap B-3: NINGÚN test de esta suite puede leer el registro real de la máquina.

    `CLAUDE_CONFIG_DIR`, el HOME (de donde salen `~/.codex` y `~/.config/opencode`) y `CODEX_HOME`
    apuntan a temporales vacíos. Antes solo lo hacían los tests nuevos del registro y, en una
    máquina con `custom-agents@otro: false` en su `settings.json`, los rojos de esta suite pasaban
    de 2 a 14: el veredicto dependía de quién la corriera. Los tests que necesitan un `cfg`
    concreto lo vuelven a fijar con `_cfg_vacio`.
    """
    base = tmp_path_factory.mktemp("entorno-limpio")
    for sub in ("claude", "home"):
        (base / sub).mkdir(exist_ok=True)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(base / "claude"))
    monkeypatch.setenv("CODEX_HOME", str(base / "codex"))
    for var in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(var, str(base / "home"))
    for var, sub in {"APPDATA": "appdata", "LOCALAPPDATA": "localappdata", "PROGRAMDATA": "programdata",
                     "XDG_CONFIG_HOME": "xdg-config", "XDG_DATA_HOME": "xdg-data",
                     "XDG_CACHE_HOME": "xdg-cache", "XDG_STATE_HOME": "xdg-state",
                     "TEMP": "temp", "TMP": "temp"}.items():
        (base / sub).mkdir(exist_ok=True)
        monkeypatch.setenv(var, str(base / sub))
    own_bin = base / "bin"
    own_bin.mkdir()
    shim = own_bin / "runtime-stub.mjs"
    shim.write_text('console.log(JSON.stringify({installed:[],available:[]}));\n', encoding="utf-8")
    if _NODE_EXECUTABLE:
        for name in ("codex", "claude", "opencode"):
            stub = own_bin / (name + ".cmd" if os.name == "nt" else name)
            text = (f'@echo off\n"{_NODE_EXECUTABLE}" "{shim}"\n' if os.name == "nt" else
                    f'#!/bin/sh\nexec {shlex.quote(_NODE_EXECUTABLE)} {shlex.quote(str(shim))}\n')
            stub.write_text(text, encoding="utf-8")
            stub.chmod(0o755)
    tool_dirs = [str(own_bin), os.path.dirname(sys.executable)]
    if _NODE_EXECUTABLE:
        tool_dirs.append(os.path.dirname(_NODE_EXECUTABLE))
    if os.name == "nt":
        tool_dirs.append(os.path.join(os.environ.get("SYSTEMROOT", "C:\\Windows"), "System32"))
    monkeypatch.setenv("CUSTOM_AGENTS_TEST_PATH", os.pathsep.join(tool_dirs))
    monkeypatch.setattr(doctor, "_estado_codex_nativo", lambda project: {
        "state": "unknown", "enabled": None, "version": None, "reason": "own-fixture"})
    monkeypatch.setattr(doctor, "managed_settings_path", lambda: "")

# ------------------------------------------------------------------ tests

@pytest.mark.parametrize("native,level,fragment", [
    ({"state": "absent", "enabled": None, "version": None, "reason": ""}, doctor.AVISO, "no figura"),
    ({"state": "installed", "enabled": False, "version": "1.22.0", "reason": ""}, doctor.AVISO, "desactivado"),
    ({"state": "installed", "enabled": True, "version": "1.22.0", "reason": ""}, doctor.OK, "confianza"),
    ({"state": "unknown", "enabled": None, "version": None, "reason": "cli-unavailable"}, doctor.INFO, "desconocido"),
])
def test_codex_declaracion_no_acredita_instalacion_ni_ejecucion(tmp_path, monkeypatch, native, level, fragment):
    proj = proyecto(tmp_path)
    (proj / ".codex").mkdir()
    (proj / ".codex" / "config.toml").write_text(
        '[plugins."custom-agents@daycry"]\nenabled = true\n', encoding="utf-8")
    monkeypatch.setattr(doctor, "_estado_codex_nativo", lambda project: native)
    rows = doctor._bloque_registro_codex(str(proj), "custom-agents@daycry")
    declared = next(row for row in rows if row["que"] == "registro en Codex")
    actual = next(row for row in rows if row["que"] == "estado nativo en Codex")
    assert declared["estado"] == doctor.OK
    assert actual["estado"] == level
    assert fragment in actual["detalle"]
    assert "hooks ejecutados" not in actual["detalle"]

def test_codex_native_wrapper_falla_sin_exponer_error_ni_config(tmp_path, monkeypatch):
    proj = proyecto(tmp_path)
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "node")
    def fake_run(args, **kwargs):
        assert args[1].endswith("codex-plugin-state.mjs")
        assert kwargs["cwd"] == str(proj)
        assert kwargs["encoding"] == "utf-8"
        assert kwargs["timeout"] <= 10
        return subprocess.CompletedProcess(args, 1, '{"secret":"PRIVATE_SENTINEL"}', "PRIVATE_SENTINEL")
    monkeypatch.setattr(doctor.subprocess, "run", fake_run)
    native = _NATIVE_CODEX_QUERY(str(proj))
    assert native["state"] == "unknown"
    assert "PRIVATE_SENTINEL" not in json.dumps(native)

@pytest.mark.parametrize("output,expected", [
    ('{"state":"installed","enabled":true,"version":"1.22.0","source":"PRIVATE_SENTINEL"}', "installed"),
    ('{"state":"absent","enabled":null,"version":null}', "absent"),
    ('{"state":"installed","enabled":"true","version":"1.22.0"}', "unknown"),
    ('{"state":"installed","enabled":true,"version":"PRIVATE_SENTINEL\\n"}', "unknown"),
    ('{"state":"absent","enabled":true,"version":null}', "unknown"),
    ('[]', "unknown"),
    ('not json PRIVATE_SENTINEL', "unknown"),
    ('x' * 4097, "unknown"),
])
def test_codex_native_wrapper_valida_y_filtra_respuesta(tmp_path, monkeypatch, output, expected):
    proj = proyecto(tmp_path)
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "node")
    monkeypatch.setattr(doctor.subprocess, "run", lambda args, **kwargs:
                        subprocess.CompletedProcess(args, 0, output, "PRIVATE_SENTINEL"))
    native = _NATIVE_CODEX_QUERY(str(proj))
    assert native["state"] == expected
    assert "PRIVATE_SENTINEL" not in json.dumps(native)

def test_codex_native_wrapper_sin_node_o_timeout_es_desconocido(tmp_path, monkeypatch):
    proj = proyecto(tmp_path)
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    assert _NATIVE_CODEX_QUERY(str(proj))["reason"] == "node-unavailable"
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "node")
    def timeout(args, **kwargs):
        raise subprocess.TimeoutExpired(args, kwargs["timeout"])
    monkeypatch.setattr(doctor.subprocess, "run", timeout)
    assert _NATIVE_CODEX_QUERY(str(proj))["state"] == "unknown"

def test_codex_native_wrapper_resuelve_root_relativo_una_sola_vez(tmp_path, monkeypatch):
    proj = proyecto(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "node")
    def fake_run(args, **kwargs):
        assert args[-1] == str(proj)
        assert kwargs["cwd"] == str(proj)
        return subprocess.CompletedProcess(args, 0,
            '{"state":"installed","enabled":true,"version":"1.22.0"}', "")
    monkeypatch.setattr(doctor.subprocess, "run", fake_run)
    assert _NATIVE_CODEX_QUERY("proj")["state"] == "installed"

def test_proyecto_sin_config_no_tiene_errores_y_exit_0(tmp_path):
    """Un proyecto virgen (sin `.claude/`) no está roto: todo ✅ o informativo, exit 0."""
    proj = proyecto(tmp_path)
    inf = diag(proj)
    assert inf["resumen"][doctor.ERROR] == 0, [l["detalle"] for l in lineas(inf, doctor.ERROR)]
    assert inf["exit"] == 0
    detalles = " ".join(l["detalle"] for l in lineas(inf))
    for esperado in ("rates.json", "dev.json", "jira.json", "confluence.json"):
        assert esperado in " ".join(l["que"] for l in lineas(inf)), esperado
    assert "no configurado" in detalles
    r = run("--root", str(proj))
    assert r.returncode == 0, r.stdout + r.stderr
    # el resumen SIEMPRE imprime el recuento «0 ❌»: lo que se comprueba es que no haya
    # ninguna FILA de error (celda «| ❌ |») ni exit 1.
    assert "| ❌ |" not in r.stdout


def test_dev_json_corrupto_es_error_con_arreglo_y_exit_1(tmp_path):
    proj = proyecto(tmp_path, dev__json="{esto no es json")
    inf = diag(proj)
    errores = [l for l in lineas(inf, doctor.ERROR) if l["que"] == "dev.json"]
    assert len(errores) == 1
    assert "no es JSON válido" in errores[0]["detalle"]
    assert "/setup" in errores[0]["arreglo"]
    assert inf["exit"] == 1
    r = run("--root", str(proj))
    assert r.returncode == 1
    assert "❌" in r.stdout


def test_dev_json_valor_fuera_de_vocabulario_es_error_con_el_valor_esperado(tmp_path):
    proj = proyecto(tmp_path, dev__json={"tdd": "si",
                                         "revision": {"lenteSeguridad": "siempre-que-pueda"},
                                         "sesion": {"journal": "no"},
                                         "tests": {"coberturaMinima": 130}})
    inf = diag(proj)
    errores = {l["que"]: l for l in lineas(inf, doctor.ERROR)}
    assert "dev.json `tdd`" in errores and "true" in errores["dev.json `tdd`"]["arreglo"]
    lente = errores["dev.json `revision.lenteSeguridad`"]
    assert "auto" in lente["arreglo"] and "siempre" in lente["arreglo"] and "nunca" in lente["arreglo"]
    assert "dev.json `sesion.journal`" in errores
    assert "entre 0 y 100" in errores["dev.json `tests.coberturaMinima`"]["arreglo"]
    assert inf["exit"] == 1


def test_dev_json_clave_desconocida_es_aviso_no_error(tmp_path):
    proj = proyecto(tmp_path, dev__json={"tdd": True, "tddd": True,
                                         "revision": {"lenteZ": "auto"}})
    inf = diag(proj)
    avisos = {l["que"] for l in lineas(inf, doctor.AVISO)}
    assert "dev.json `tddd`" in avisos and "dev.json `revision.lenteZ`" in avisos
    assert not [l for l in lineas(inf, doctor.ERROR)]
    assert inf["exit"] == 0


def test_dev_json_lente_rendimiento_es_vocabulario_conocido(tmp_path):
    """`revision.lenteRendimiento` (lente D) NO debe salir como clave desconocida."""
    proj = proyecto(tmp_path, dev__json={"revision": {"lenteRendimiento": "auto"}})
    inf = diag(proj)
    assert not lineas(inf, doctor.ERROR) and not lineas(inf, doctor.AVISO)
    proj2 = proyecto(tmp_path / "b", dev__json={"revision": {"lenteRendimiento": "a-veces"}})
    inf2 = diag(proj2)
    assert [l for l in lineas(inf2, doctor.ERROR) if l["que"] == "dev.json `revision.lenteRendimiento`"]


def test_dev_json_sesion_memoria_es_vocabulario_conocido(tmp_path):
    """`sesion.memoria` (opt-out del bloque de memoria de `session-context.sh`, memory-retrieval T-06) NO
    debe salir como clave desconocida; un valor no booleano sí es ❌."""
    inf = diag(proyecto(tmp_path, dev__json={"sesion": {"memoria": False}}))
    assert not lineas(inf, doctor.ERROR) and not lineas(inf, doctor.AVISO)
    inf2 = diag(proyecto(tmp_path / "b", dev__json={"sesion": {"memoria": "no"}}))
    assert [l for l in lineas(inf2, doctor.ERROR) if l["que"] == "dev.json `sesion.memoria`"]


def test_dev_json_sesion_captura_y_resumen_son_vocabulario_conocido(tmp_path):
    """`sesion.captura` (opt-out del log crudo de UserPromptSubmit) y `sesion.resumen` (resumen por IA opt-in),
    memory-retrieval T-11/T-13, NO deben salir como clave desconocida; un valor no booleano sí es ❌ y el
    arreglo de `sesion` mal formado nombra las claves nuevas (revisión F4, Lente A gap 6)."""
    inf = diag(proyecto(tmp_path, dev__json={"sesion": {"captura": False, "resumen": True}}))
    assert not lineas(inf, doctor.ERROR) and not lineas(inf, doctor.AVISO)
    inf2 = diag(proyecto(tmp_path / "b", dev__json={"sesion": {"captura": "no", "resumen": 1}}))
    assert [l for l in lineas(inf2, doctor.ERROR) if l["que"] == "dev.json `sesion.captura`"]
    assert [l for l in lineas(inf2, doctor.ERROR) if l["que"] == "dev.json `sesion.resumen`"]
    inf3 = diag(proyecto(tmp_path / "c", dev__json={"sesion": "si"}))
    err = [l for l in lineas(inf3, doctor.ERROR) if l["que"] == "dev.json `sesion`"]
    assert err and "captura" in err[0]["arreglo"] and "resumen" in err[0]["arreglo"]


def test_hook_con_script_inexistente_es_error(tmp_path):
    plug = plugin(tmp_path, script_existe=False)
    inf = diag(proyecto(tmp_path), plug)
    errores = [l for l in lineas(inf, doctor.ERROR) if l["que"] == "hook sin script"]
    assert len(errores) == 1, [l["que"] for l in lineas(inf)]
    assert "hooks/demo.sh" in errores[0]["detalle"]
    assert "reinstala" in errores[0]["arreglo"] or "actualiza" in errores[0]["arreglo"]
    assert inf["exit"] == 1
    # y la comprobación es la LOCAL (este plugin temporal no trae scripts/lint_plugin.py)
    assert any("comprobación local" in l["detalle"] for l in lineas(inf))


def test_hook_exec_form_con_script_inexistente_en_args_es_error(tmp_path):
    """Gap 11 de la revisión intento 1: `doctor.py` solo escaneaba `command`; con exec form
    (`command: bash`, `args: [...]`, session-end-durable-capture T-03) el script inexistente vive
    en `args` y antes no se detectaba."""
    plug = tmp_path / "plug"
    (plug / "agents").mkdir(parents=True)
    (plug / "agents" / "demo.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
    (plug / ".claude-plugin").mkdir()
    (plug / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "custom-agents", "version": "9.9.9"}), encoding="utf-8")
    (plug / "hooks").mkdir()
    (plug / "hooks" / "hooks.json").write_text(json.dumps({"hooks": {"SessionEnd": [
        {"hooks": [{"type": "command", "command": "bash",
                    "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/no-existe.sh"], "timeout": 5}]}]}}),
        encoding="utf-8")
    inf = diag(proyecto(tmp_path), plug)
    errores = [l for l in lineas(inf, doctor.ERROR) if l["que"] == "hook sin script"]
    assert len(errores) == 1, [l["que"] for l in lineas(inf)]
    assert "hooks/no-existe.sh" in errores[0]["detalle"]
    assert inf["exit"] == 1


# Windows no puede afirmar esto: `os.chmod(path, 0o644)` deja el fichero en `0o666` y
# `os.access(path, X_OK)` devuelve siempre True (el execute allí es por extensión de fichero), así
# que el doctor NO puede ver el bit y el aviso no puede aparecer — el chequeo es POSIX puro.
@pytest.mark.skipif(sys.platform == "win32",
                    reason="el bit +x por fichero no existe en Windows: chmod no lo quita y "
                           "os.access(X_OK) miente; CI Linux es la puerta")
def test_hook_sin_bit_ejecutable_es_aviso_con_chmod(tmp_path):
    plug = plugin(tmp_path, ejecutable=False)
    inf = diag(proyecto(tmp_path), plug)
    avisos = [l for l in lineas(inf, doctor.AVISO) if l["que"] == "hook no ejecutable"]
    assert len(avisos) == 1
    assert "chmod +x hooks/demo.sh" in avisos[0]["arreglo"]
    assert inf["resumen"][doctor.ERROR] == 0 and inf["exit"] == 0


# --- registro real del plugin (installer-registro-real T-05) -----------------------------
#
# El falso positivo que motiva estos tests: con el bundle COPIADO a `.claude/` (la vía 1/2 de
# INSTALL.md, hoy `--mode copy`) el doctor decía «hooks registrados ✅» porque los ficheros
# estaban ahí, cuando Claude Code no lee `hooks/hooks.json` fuera de un plugin instalado.

def _cfg_vacio(tmp_path, monkeypatch, nombre="cfg"):
    """`CLAUDE_CONFIG_DIR` temporal: ningún test puede depender del `~/.claude` de la máquina."""
    cfg = tmp_path / nombre
    cfg.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    return cfg


def fila(inf, que):
    hits = [l for l in lineas(inf) if l["que"] == que]
    assert len(hits) == 1, [l["que"] for l in lineas(inf)]
    return hits[0]


def test_bundle_copiado_los_hooks_no_estan_registrados_y_el_arreglo_lo_dice(tmp_path, monkeypatch):
    """Modo copia: la fila de hooks pasa de ✅ a ⚠️ y nombra lo que NO se tiene."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = plugin(tmp_path, dest=proj / ".claude")
    inf = diag(proj, plug)

    hooks = fila(inf, "hooks registrados")
    assert hooks["estado"] == doctor.AVISO, hooks
    assert "NO lee `hooks/hooks.json` fuera de un plugin" in hooks["detalle"]
    for pieza in ("hooks", "statusline", "namespace"):
        assert pieza in hooks["detalle"]
    assert "npx @daycry/custom-agents install -p claude-code" in hooks["arreglo"]

    registro = fila(inf, "registro del plugin")
    assert registro["estado"] == doctor.AVISO and "copiado, no instalado" in registro["detalle"]
    assert "install -p claude-code" in registro["arreglo"]
    # un bundle copiado no está ROTO: degrada, no bloquea
    assert inf["resumen"][doctor.ERROR] == 0 and inf["exit"] == 0
    assert fila(inf, "raíz del plugin")["detalle"].endswith("instalación: copia")


def test_plugin_registrado_hooks_ok_y_la_fila_de_registro_dice_fichero_y_scope(tmp_path, monkeypatch):
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    cache = cfg / "plugins" / "cache" / "daycry" / "custom-agents" / "9.9.9"
    plug = plugin(tmp_path, dest=cache)
    (cfg / "plugins" / "installed_plugins.json").write_text(json.dumps(
        {"version": 2, "plugins": {"custom-agents@daycry": [
            {"scope": "user", "installPath": str(cache), "version": "9.9.9"}]}}), encoding="utf-8")
    inf = diag(proyecto(tmp_path), plug)

    assert fila(inf, "hooks registrados")["estado"] == doctor.OK
    registro = fila(inf, "registro del plugin")
    assert registro["estado"] == doctor.OK
    assert "custom-agents@daycry" in registro["detalle"]
    assert "installed_plugins.json" in registro["detalle"] and "scope user" in registro["detalle"]
    assert fila(inf, "raíz del plugin")["detalle"].endswith("instalación: plugin")
    assert inf["exit"] == 0


def test_enabled_plugins_en_false_es_error_con_el_arreglo(tmp_path, monkeypatch):
    """Registrado pero APAGADO es el caso peor: todo en su sitio y Claude Code lo ignora."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    (cfg / "settings.json").write_text(json.dumps(
        {"enabledPlugins": {"custom-agents@daycry": False}}), encoding="utf-8")
    proj = proyecto(tmp_path)
    inf = diag(proj, plugin(tmp_path, dest=proj / ".claude"))
    registro = fila(inf, "registro del plugin")
    assert registro["estado"] == doctor.ERROR and "`false`" in registro["detalle"]
    assert "custom-agents@daycry" in registro["arreglo"]
    assert inf["exit"] == 1


def test_registro_del_scope_project_tambien_cuenta(tmp_path, monkeypatch):
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path, settings__json={"enabledPlugins": {"custom-agents@daycry": True}})
    inf = diag(proj, plugin(tmp_path))
    registro = fila(inf, "registro del plugin")
    assert registro["estado"] == doctor.OK and "scope project" in registro["detalle"]
    assert fila(inf, "hooks registrados")["estado"] == doctor.OK


def test_checkout_de_desarrollo_no_es_copia_ni_se_le_grita(tmp_path, monkeypatch):
    """Sin registro y con la raíz fuera de `.claude/`: informativo, y los hooks siguen ✅."""
    _cfg_vacio(tmp_path, monkeypatch)
    inf = diag(proyecto(tmp_path), plugin(tmp_path))
    registro = fila(inf, "registro del plugin")
    assert registro["estado"] == doctor.INFO and registro["arreglo"] == ""
    assert fila(inf, "hooks registrados")["estado"] == doctor.OK
    assert inf["exit"] == 0


def test_json_gana_modo_y_registro_sin_perder_ninguna_clave(tmp_path, monkeypatch):
    """Compatibilidad hacia atrás del `--json`: las claves nuevas se SUMAN."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    (cfg / "settings.json").write_text(json.dumps(
        {"enabledPlugins": {"custom-agents@daycry": True}}), encoding="utf-8")
    r = run("--root", str(proyecto(tmp_path)), "--plugin-root", str(plugin(tmp_path)), "--json")
    d = json.loads(r.stdout)
    assert set(d) >= {"proyecto", "plugin_root", "bloques", "resumen", "exit"}
    plug_b = [b for b in d["bloques"] if b["clave"] == "plugin"][0]
    assert set(plug_b) == {"clave", "titulo", "lineas", "modo", "registro"}
    assert plug_b["modo"] == "plugin"
    assert all(set(l) == {"estado", "que", "detalle", "arreglo"} for l in plug_b["lineas"])
    assert plug_b["registro"][0]["clave"] == "custom-agents@daycry"
    assert plug_b["registro"][0]["habilitado"] is True


def test_repo_real_usa_el_criterio_del_linter_para_los_hooks(tmp_path):
    """Con el plugin real (que sí trae `scripts/lint_plugin.py`) el veredicto de hooks se delega
    en `lint_hook_commands` — una sola definición de «hook roto» en el repo."""
    inf = diag(proyecto(tmp_path), ROOT)
    hooks = [l for l in lineas(inf) if l["que"] == "hooks registrados"]
    assert len(hooks) == 1
    assert "lint_plugin.py" in hooks[0]["detalle"]


def test_marcador_huerfano_es_aviso_con_el_comando_de_cierre(tmp_path):
    proj = proyecto(tmp_path, **{"usage-state__json": {"docs/roadmap/x/spec.md": {"inicio": "2026-01-01T00:00:00Z"}}})
    inf = diag(proj)
    avisos = [l for l in lineas(inf, doctor.AVISO) if l["que"] == "marcador huérfano"]
    assert len(avisos) == 1
    assert "usage-meter.py close" in avisos[0]["arreglo"]
    assert inf["exit"] == 0


def test_marcador_cerrado_no_avisa(tmp_path):
    proj = proyecto(tmp_path, **{"usage-state__json": {
        "docs/roadmap/x/spec.md": {"inicio": "2026-01-01T00:00:00Z", "ultimoCierre": "2026-01-01T01:00:00Z"}}})
    inf = diag(proj)
    assert not [l for l in lineas(inf, doctor.AVISO) if l["que"] == "marcador huérfano"]
    assert [l for l in lineas(inf, doctor.OK) if l["que"] == "marcadores de medición"]


def test_rates_con_precio_a_cero_es_aviso_con_rates_verify(tmp_path):
    proj = proyecto(tmp_path, rates__json={"tarifaHora": 50, "precioTokens": {
        "input": 0, "output": 0, "verificadoEl": "2026-01-01"}})
    inf = diag(proj)
    avisos = [l for l in lineas(inf, doctor.AVISO) if l["que"] == "rates.json"]
    assert len(avisos) == 1 and "precio a 0" in avisos[0]["detalle"]
    assert "rates-verify" in avisos[0]["arreglo"]
    assert inf["exit"] == 0
    # sin fecha de verificación: mismo aviso, otro motivo
    inf2 = diag(proyecto(tmp_path / "b", rates__json={"precioTokens": {"input": 5, "output": 25}}))
    a2 = [l for l in lineas(inf2, doctor.AVISO) if l["que"] == "rates.json"]
    assert a2 and "sin fecha de verificación" in a2[0]["detalle"]


def test_optin_habilitado_sin_campos_obligatorios_es_aviso(tmp_path):
    proj = proyecto(tmp_path, jira__json={"enabled": True}, confluence__json={"enabled": False})
    inf = diag(proj)
    jira = [l for l in lineas(inf, doctor.AVISO) if l["que"] == "jira.json"]
    assert jira and "cloudId" in jira[0]["detalle"]
    conf = [l for l in lineas(inf, doctor.INFO) if l["que"] == "confluence.json"]
    assert conf and "desactivado" in conf[0]["detalle"]
    assert inf["exit"] == 0


def test_json_y_md_llevan_los_mismos_veredictos(tmp_path):
    proj = proyecto(tmp_path, dev__json={"tdd": "si", "tddd": True},
                    rates__json={"precioTokens": {"input": 0, "output": 0}})
    md = run("--root", str(proj))
    js = run("--root", str(proj), "--json")
    assert md.returncode == js.returncode == 1
    d = json.loads(js.stdout)
    assert veredictos_md(md.stdout) == [l["estado"] for l in lineas(d)]
    assert d["resumen"][doctor.ERROR] >= 1 and d["resumen"][doctor.AVISO] >= 1
    for estado, icono in doctor.ICONO.items():
        assert f"{d['resumen'][estado]} {icono}" in md.stdout


def test_exit_1_solo_con_error(tmp_path):
    """Avisos e informativos NO cambian el exit; un solo ❌ sí."""
    solo_avisos = proyecto(tmp_path, dev__json={"tddd": True})
    assert run("--root", str(solo_avisos)).returncode == 0
    con_error = proyecto(tmp_path / "b", dev__json="{roto")
    assert run("--root", str(con_error)).returncode == 1


def test_version_seen_compara_sin_afirmar_actualizacion(tmp_path):
    plug = plugin(tmp_path, version="9.9.9")
    proj = proyecto(tmp_path, **{"__plugin-version-seen": "9.9.8\n"})
    inf = diag(proj, plug)
    ver = [l for l in lineas(inf) if l["que"] == "versión vista en este proyecto"]
    assert len(ver) == 1
    assert "9.9.8" in ver[0]["detalle"] and "9.9.9" in ver[0]["detalle"]
    assert all(l["estado"] == doctor.INFO for b in inf["bloques"] if b["clave"] == "version"
               for l in b["lineas"])
    texto = doctor.render_md(inf).lower()
    for prohibido in ("actualización disponible", "hay una actualización", "hay actualización",
                      "actualiza el plugin a"):
        assert prohibido not in texto, prohibido
    assert "no consulta el marketplace" in texto
    # sin registro previo: lo dice, no lo inventa
    sin = diag(proyecto(tmp_path / "b"), plug)
    assert any("sin registro previo" in l["detalle"] for l in lineas(sin))


def test_version_sin_manifiesto_es_aviso_de_ausente_no_de_campo(tmp_path):
    """Raíz válida sin NINGÚN manifiesto (las instalaciones de OpenCode anteriores a v1.21.x): el
    diagnóstico no puede ser «sin campo `version`», porque su remedio («añade el campo») apuntaba a
    un fichero que NO existía. El aviso nombra el manifiesto ausente y degrada sin bloquear."""
    plug = plugin(tmp_path)
    os.remove(os.path.join(plug, ".claude-plugin", "plugin.json"))
    inf = diag(proyecto(tmp_path), plug)
    aviso = [l for l in lineas(inf, doctor.AVISO) if l["que"] == "versión del plugin"]
    assert len(aviso) == 1, aviso
    assert "manifiesto" in aviso[0]["detalle"]
    assert "sin campo" not in aviso[0]["detalle"]
    assert "install" in aviso[0]["arreglo"]
    assert inf["exit"] == 0


def test_version_lee_el_manifiesto_de_codex_si_falta_el_de_claude(tmp_path):
    """Instalación de Codex: solo `.codex-plugin/plugin.json` → la versión sale (nombrando su
    origen); era el MISMO falso «sin campo version» que en OpenCode."""
    plug = plugin(tmp_path)
    os.remove(os.path.join(plug, ".claude-plugin", "plugin.json"))
    codex = plug / ".codex-plugin"
    codex.mkdir()
    (codex / "plugin.json").write_text(
        json.dumps({"name": "custom-agents", "version": "8.8.8"}), encoding="utf-8")
    inf = diag(proyecto(tmp_path), plug)
    ver = [l for l in lineas(inf) if l["que"] == "versión del plugin"]
    assert len(ver) == 1, ver
    assert ver[0]["estado"] == doctor.INFO
    assert "8.8.8" in ver[0]["detalle"] and ".codex-plugin" in ver[0]["detalle"]
    assert inf["exit"] == 0


def test_version_manifiesto_roto_es_error_y_no_tapa_el_bueno(tmp_path):
    """Un manifiesto ROTO sigue siendo ❌ (no es un aviso), pero un `.codex-plugin` sano que trae la
    MISMA versión manda sobre él: los dos manifiestos llevan el mismo número por construcción."""
    plug = plugin(tmp_path)
    (plug / ".claude-plugin" / "plugin.json").write_text("{roto", encoding="utf-8")
    roto = diag(proyecto(tmp_path), plug)
    errores = [l for l in lineas(roto, doctor.ERROR) if l["que"] == "plugin.json"]
    assert len(errores) == 1, errores

    codex = plug / ".codex-plugin"
    codex.mkdir()
    (codex / "plugin.json").write_text(
        json.dumps({"name": "custom-agents", "version": "9.9.9"}), encoding="utf-8")
    bueno = diag(proyecto(tmp_path), plug)
    ver = [l for l in lineas(bueno) if l["que"] == "versión del plugin"]
    assert len(ver) == 1 and ver[0]["estado"] == doctor.INFO and "9.9.9" in ver[0]["detalle"]
    assert not [l for l in lineas(bueno, doctor.ERROR) if l["que"] == "plugin.json"]


def test_plugin_no_localizable_es_error_con_arreglo(tmp_path):
    vacio = tmp_path / "no-plugin"
    vacio.mkdir()
    inf = diag(proyecto(tmp_path), vacio)
    errores = [l for l in lineas(inf, doctor.ERROR) if l["que"] == "raíz del plugin"]
    assert len(errores) == 1 and "--plugin-root" in errores[0]["arreglo"]
    assert inf["exit"] == 1
    assert any(l["que"] == "versión del plugin" and l["estado"] == doctor.INFO for l in lineas(inf))


def test_uso_incorrecto_exit_2(tmp_path):
    assert run("--root", str(tmp_path / "no-existe")).returncode == 2
    assert run("--root", str(proyecto(tmp_path)), "--plugin-root", str(tmp_path / "nada")).returncode == 2


def test_no_escribe_nada_en_el_proyecto(tmp_path):
    proj = proyecto(tmp_path, dev__json={"tdd": True, "modelos": {"implementer": {"model": "opus"}}},
                    rates__json={"precioTokens": {"input": 5, "output": 25, "verificadoEl": "2026-01-01"}})
    antes = snapshot(proj)
    assert run("--root", str(proj)).returncode == 0
    assert run("--root", str(proj), "--json").returncode == 0
    assert snapshot(proj) == antes


def test_toda_linea_de_aviso_o_error_trae_arreglo(tmp_path):
    proj = proyecto(tmp_path, dev__json={"tdd": "si", "tddd": True, "guardrails": 3,
                                         "revision": "auto", "sesion": [], "tests": 80},
                    rates__json="{roto", jira__json={"enabled": True},
                    confluence__json={"enabled": True, "cloudId": "x"})
    inf = diag(proj)
    problemas = lineas(inf, doctor.AVISO) + lineas(inf, doctor.ERROR)
    assert len(problemas) >= 8
    for l in problemas:
        assert l["arreglo"].strip(), l


@pytest.mark.parametrize("bloque", ["herramientas", "plugin", "configs", "estado", "capacidades", "memoria", "version", "journal"])
def test_los_ocho_bloques_estan_siempre(tmp_path, bloque):
    inf = diag(proyecto(tmp_path))
    claves = [b["clave"] for b in inf["bloques"]]
    assert bloque in claves and len(claves) == 8
    assert doctor.render_md(inf).count("| | Comprobación |") == 8


# ------------------------------------------------------------------ Journal (session-end-durable-capture T-06)

def test_journal_sin_pendientes_ni_huerfanas_es_informativo_y_exit_0(tmp_path):
    proj = proyecto(tmp_path)
    inf = diag(proj)
    journ = [b for b in inf["bloques"] if b["clave"] == "journal"][0]
    assert not [l for l in journ["lineas"] if l["estado"] == doctor.ERROR]
    assert inf["exit"] == 0


def test_journal_con_dead_letter_avisa_con_el_remedio_nombrado(tmp_path):
    proj = proyecto(tmp_path)
    d = proj / ".claude" / "journal" / "dead-letter"
    d.mkdir(parents=True)
    (d / "ev1.json").write_text(json.dumps({"session_id": "s1"}), encoding="utf-8")
    (d / "ev1.json.causa.json").write_text(
        json.dumps({"causa": "esquema inválido", "intentos": 3, "en": "2026-09-17T00:00:00Z"}), encoding="utf-8")
    inf = diag(proj)
    avisos = [l for l in lineas(inf, doctor.AVISO) if "dead-letter" in l["que"]]
    assert avisos and "reintentar-dead-letter" in avisos[0]["arreglo"]


def test_journal_con_huerfana_dice_perdida_posible_y_nombra_recover(tmp_path):
    proj = proyecto(tmp_path, **{"dev__json": {"sesion": {"journal": {"ventanaHuerfanaMin": 1}}}})
    p = proj / ".claude" / "session-prompts-huerfana1.log"
    p.write_text(json.dumps({"ts": "2026-09-17T00:00:00Z", "prompt": "hola"}) + "\n", encoding="utf-8")
    t = _dt.datetime.now().timestamp() - 5 * 60
    os.utime(p, (t, t))
    inf = diag(proj)
    # Gap 77 de la revisión tramo 2: UN solo bloque de triage (antes salían dos avisos redundantes,
    # "sesiones huérfanas" + "Hook cancelled (triage)", diciendo lo mismo dos veces).
    avisos = [l for l in lineas(inf, doctor.AVISO) if "huérfana" in l["detalle"]]
    assert len(avisos) == 1
    assert "pérdida posible" in avisos[0]["detalle"].lower() and "recover" in avisos[0]["arreglo"]


def test_journal_dead_letter_menciona_perdida_posible_y_los_dos_remedios(tmp_path):
    """Gap 68 (parte doctor): el triage de dead-letter dice «pérdida posible» y nombra AMBOS
    remedios (`recover` y `replay --reintentar-dead-letter`), no solo el segundo."""
    proj = proyecto(tmp_path)
    d = proj / ".claude" / "journal" / "dead-letter"
    d.mkdir(parents=True)
    (d / "ev1.json").write_text(json.dumps({"session_id": "s1"}), encoding="utf-8")
    (d / "ev1.json.causa.json").write_text(
        json.dumps({"causa": "esquema inválido", "intentos": 3, "en": "2026-09-17T00:00:00Z"}), encoding="utf-8")
    inf = diag(proj)
    avisos = [l for l in lineas(inf, doctor.AVISO) if "dead-letter" in l["que"]]
    assert avisos
    assert "pérdida posible" in avisos[0]["detalle"].lower()
    assert "recover" in avisos[0]["arreglo"] and "reintentar-dead-letter" in avisos[0]["arreglo"]


def test_journal_triage_no_habla_de_esta_sesion(tmp_path):
    """Gap 77: los contadores de `status` son GLOBALES a la cola, no de «esta sesión» — el triage
    no debe insinuar que son por sesión."""
    proj = proyecto(tmp_path)
    d = proj / ".claude" / "journal" / "outbox"
    d.mkdir(parents=True)
    (d / "ev1.json").write_text(json.dumps({
        "session_id": "s1", "schema_version": 1, "reason": "other", "cwd": str(proj),
        "transcript_path": "", "captured_at": "2026-09-17T00:00:00Z",
        "hook_event_name": "SessionEnd", "sequence": 0}), encoding="utf-8")
    inf = diag(proj)
    journ = [b for b in inf["bloques"] if b["clave"] == "journal"][0]
    textos = " ".join(l["detalle"] for l in journ["lineas"])
    assert "de esta sesión" not in textos


def test_journal_con_pendiente_en_outbox_dice_aviso_del_runtime_sin_perdida(tmp_path):
    proj = proyecto(tmp_path)
    d = proj / ".claude" / "journal" / "outbox"
    d.mkdir(parents=True)
    (d / "ev1.json").write_text(json.dumps({
        "session_id": "s1", "schema_version": 1, "reason": "other", "cwd": str(proj),
        "transcript_path": "", "captured_at": "2026-09-17T00:00:00Z",
        "hook_event_name": "SessionEnd", "sequence": 0}), encoding="utf-8")
    inf = diag(proj)
    journ = [b for b in inf["bloques"] if b["clave"] == "journal"][0]
    hc = [l for l in journ["lineas"] if "hook cancelled" in l["que"].lower()]
    assert hc and "sin pérdida" in hc[0]["detalle"].lower()


# ------------------------------------------------------------------ salud de la memoria (memory-retrieval T-10)
#
# Hasta aquí `/doctor` decía «Instalación sana» con 0 entradas de journal, sin contar las curadas, sin
# validar el índice y sin avisar de que CALIBRATION.md llevaba semanas sin fila. Bloque nuevo «Memoria
# técnica»: entradas curadas por familia y estado (✅/ℹ️), índice `README.md` (❌ si la biyección o el
# «Área» fallan — delega en `lint_knowledge_index` de lint_plugin.py), índice FTS5 (ℹ️ ausente/desfasado,
# ⚠️ corrupto o sin FTS5), journal a 0 CON memoria curada (⚠️) y CALIBRATION.md (> CALIBRACION_DIAS_MAX
# días sin fila con iniciativas cerradas después → ⚠️ con cuántas y cuáles). Solo lectura: no crea el índice.

import datetime as _dt


def _fm(**kv):
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in kv.items()) + "---\n"


def memoria(proj, propuesta=False, sin_fila=None, journal=None):
    """`docs/knowledge/` de mentira: 2 ADR + 1 gotcha + 1 lección (una `propuesta` si se pide)."""
    kn = proj / "docs" / "knowledge"
    for d in ("adr", "gotchas", "lessons"):
        (kn / d).mkdir(parents=True, exist_ok=True)
    entradas = {
        "adr/ADR-001-a.md": (_fm(id="ADR-001", titulo="A", estado="aceptada (validada: usuario, 2026-01-01)") + "\n# A\n", "ADR", "Hooks / x"),
        "adr/ADR-002-b.md": (_fm(id="ADR-002", titulo="B", estado="aceptada (validada: usuario, 2026-01-01)") + "\n# B\n", "ADR", "Hooks / y"),
        "gotchas/GOT-001-c.md": (_fm(id="GOT-001", tipo="gotcha", area="Tests / fixtures",
                                     estado="aceptada (validada: usuario, 2026-01-01)") + "\n## C\n", "Gotcha", "Tests / fixtures"),
        "lessons/LES-001-evaluator-d.md": (_fm(id="LES-001", tipo="leccion", area="Estimación / calibración",
                                               estado="propuesta" if propuesta else "aceptada (validada: usuario, 2026-01-01)")
                                           + "\n## evaluator\n\n- D.\n", "Lección", "Estimación / calibración"),
    }
    filas = ["# índice\n", "| Entrada | ID | Tipo | Área | Estado | Fuente |", "|---|---|---|---|---|---|"]
    for rel, (texto, tipo, area) in entradas.items():
        (kn / rel).write_text(texto, encoding="utf-8")
        id_ = rel.split("/")[1][:7]
        if id_ != sin_fila:
            estado = "propuesta" if (propuesta and id_ == "LES-001") else "aceptada (validada: usuario, 2026-01-01)"
            filas.append(f"| [`{rel}`]({rel}) — {id_} | {id_} | {tipo} | {area} | {estado} | `x/tasks.md` |")
    (kn / "README.md").write_text("\n".join(filas) + "\n", encoding="utf-8")
    if journal is not None:
        (kn / "journal").mkdir(exist_ok=True)
        (kn / "journal" / "README.md").write_text("# journal\n", encoding="utf-8")
        for i in range(journal):
            (kn / "journal" / f"2026-01-0{i + 1}-demo.md").write_text("---\nsesion: x\n---\n", encoding="utf-8")
    return kn


def ledger_cerrado(proj, slug, actualizado):
    d = proj / "docs" / "roadmap" / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "tasks.md").write_text(
        f"---\ntasks: {slug[11:]}\nestado: completado\ncreado: {actualizado}\nactualizado: {actualizado}\n---\n\n"
        f"# Checklist — {slug}\n\n## Fase 1 — X\n\n**Estado**: completado\n\n### T-01 — x\n\n- **Estado**: completado\n\n"
        "**Criterios de aceptación**\n- [x] a\n", encoding="utf-8")


def calibracion(proj, ultima_fecha, slugs=("una",)):
    filas = "\n".join(f"| {ultima_fecha} | {s} | −90 % | −90 % | 400000 | causa | ajuste |" for s in slugs)
    (proj / "docs" / "roadmap").mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "roadmap" / "CALIBRATION.md").write_text(
        "# CALIBRATION\n\n| Fecha | Iniciativa | Desv. producción | Desv. tokens | tokens/hora (medido) | Causa principal | Ajuste sugerido |\n"
        "|---|---|---|---|---|---|---|\n" + filas + "\n", encoding="utf-8")


def bloque(inf, clave):
    return next(b for b in inf["bloques"] if b["clave"] == clave)


def por_que(inf, que, estado=None):
    return [l for l in lineas(inf, estado) if l["que"] == que]


def test_memoria_sin_docs_knowledge_es_informativa_y_exit_0(tmp_path):
    """Un proyecto recién instalado nace sin memoria: no está roto."""
    inf = diag(proyecto(tmp_path))
    mem = bloque(inf, "memoria")
    assert mem["titulo"].lower().startswith("memoria")
    assert all(l["estado"] == doctor.INFO for l in mem["lineas"]), mem["lineas"]
    assert any("docs/knowledge/" in l["detalle"] for l in mem["lineas"])
    assert inf["exit"] == 0 and "Sin errores ni avisos en las comprobaciones realizadas" in doctor.render_md(inf)


def test_memoria_curada_se_cuenta_por_familia_y_por_estado(tmp_path):
    proj = proyecto(tmp_path)
    memoria(proj, propuesta=True, journal=1)
    inf = diag(proj)
    cur = por_que(inf, "memoria curada")
    assert len(cur) == 1 and cur[0]["estado"] == doctor.OK
    det = cur[0]["detalle"]
    assert "4 entrada" in det and "2 ADR" in det and "1 gotcha" in det and "1 lecci" in det, det
    assert "3 aceptada" in det and "1 propuesta" in det, det
    idx = por_que(inf, "índice de memoria (README)")
    assert idx and idx[0]["estado"] == doctor.OK and "4" in idx[0]["detalle"]


def test_indice_readme_invalido_es_error_y_ya_no_dice_instalacion_sana(tmp_path):
    """Spec CA-14: una entrada sin fila (biyección rota) es ❌, nombra el fichero, exit 1."""
    proj = proyecto(tmp_path)
    memoria(proj, sin_fila="GOT-001", journal=1)
    inf = diag(proj)
    errs = por_que(inf, "índice de memoria (README)", doctor.ERROR)
    assert len(errs) == 1, [l for l in lineas(inf) if "memoria" in l["que"]]
    assert "GOT-001" in errs[0]["detalle"] and "sin fila" in errs[0]["detalle"]
    assert "README.md" in errs[0]["arreglo"]
    assert inf["exit"] == 1
    md = doctor.render_md(inf)
    assert "Instalación sana" not in md and "❌" in md


def test_indice_readme_fila_hacia_fichero_inexistente_es_error_aunque_el_plugin_root_sea_una_copia_vieja(tmp_path):
    """Revisión intento 1 (MINOR 6): la «comprobación local equivalente» solo veía fichero-sin-fila y fila-sin-Área;
    con `plugin_root` resuelto a una copia instalada anterior (sin `lint_knowledge_index`) una fila fantasma pasaba
    ✅ (medido sobre e08fc05: «✅ … (comprobación local)»). Ahora el doctor lleva el criterio del linter como copia
    LITERAL (bloque `--8<--`, identidad con test) y no depende de lo que traiga `plugin_root`."""
    proj = proyecto(tmp_path)
    kn = memoria(proj, journal=1)
    readme = kn / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8")
                      + "| [`adr/ADR-099-fantasma.md`](adr/ADR-099-fantasma.md) — fantasma | ADR-099 | ADR | Hooks / z | aceptada | `x` |\n",
                      encoding="utf-8")
    for plug in (None, plugin(tmp_path)):                  # sin plugin y con un plugin SIN scripts/lint_plugin.py
        inf = diag(proj, plug)
        errs = por_que(inf, "índice de memoria (README)", doctor.ERROR)
        assert len(errs) == 1, [l for l in lineas(inf) if "memoria" in l["que"]]
        assert "ADR-099" in errs[0]["detalle"] and "no existe" in errs[0]["detalle"], errs[0]["detalle"]
        assert inf["exit"] == 1
    # y el criterio es literalmente el del linter (el test de identidad vive en tests/test_knowledge_index.py)
    assert "# --8<-- criterio del índice de knowledge COMPARTIDO" in open(SCRIPT, encoding="utf-8").read()
    assert por_que(diag(proyecto(tmp_path / "b")), "índice de memoria (README)") == []      # sin memoria: nada que juzgar


def test_journal_a_cero_con_memoria_curada_es_aviso_y_sin_memoria_sigue_informativo(tmp_path):
    proj = proyecto(tmp_path)
    memoria(proj, journal=0)                          # carpeta journal/ vacía
    inf = diag(proj)
    av = por_que(inf, "journal de sesión", doctor.AVISO)
    assert len(av) == 1 and "0" in av[0]["detalle"] and "curada" in av[0]["detalle"], av
    assert "SessionEnd" in av[0]["arreglo"] and "sesion.journal" in av[0]["arreglo"]
    assert inf["exit"] == 0 and "Instalación sana" not in doctor.render_md(inf)
    # sin carpeta journal/ pero con memoria curada → mismo aviso
    import shutil as _sh
    _sh.rmtree(proj / "docs" / "knowledge" / "journal")
    assert por_que(diag(proj), "journal de sesión", doctor.AVISO)
    # con una entrada → informativo, como antes
    memoria(proj, journal=1)
    assert por_que(diag(proj), "journal de sesión", doctor.INFO)
    # sin docs/knowledge/ → informativo (comportamiento de siempre: un proyecto nuevo no está roto)
    assert por_que(diag(proyecto(tmp_path / "b")), "journal de sesión", doctor.INFO)


def test_calibracion_desfasada_avisa_con_dias_e_iniciativas_cerradas(tmp_path):
    proj = proyecto(tmp_path)
    memoria(proj, journal=1)
    calibracion(proj, "2026-01-01", slugs=("una",))
    ledger_cerrado(proj, "2026-01-01-una", "2026-01-01")          # ya tiene fila
    ledger_cerrado(proj, "2026-01-10-dos", "2026-01-10")          # cerrada después, sin fila
    ledger_cerrado(proj, "2026-01-12-tres", "2026-01-12")         # ídem
    hoy = _dt.date(2026, 1, 20)
    inf = doctor.diagnostico(str(proj), None, hoy=hoy)
    av = por_que(inf, "calibración (CALIBRATION.md)", doctor.AVISO)
    assert len(av) == 1, [l for l in lineas(inf) if "calibraci" in l["que"]]
    assert "19 día" in av[0]["detalle"] and "2 iniciativa" in av[0]["detalle"], av[0]["detalle"]
    assert "dos" in av[0]["detalle"] and "tres" in av[0]["detalle"] and "una" not in av[0]["detalle"].split("cerrada")[1]
    assert "/retro" in av[0]["arreglo"]
    assert doctor.CALIBRACION_DIAS_MAX == 14
    # 9 días → todavía no avisa (ℹ️ con las cerradas pendientes), y con fila reciente → ✅
    inf9 = doctor.diagnostico(str(proj), None, hoy=_dt.date(2026, 1, 10))
    assert not por_que(inf9, "calibración (CALIBRATION.md)", doctor.AVISO)
    calibracion(proj, "2026-01-19", slugs=("una", "dos", "tres"))
    ok = por_que(doctor.diagnostico(str(proj), None, hoy=hoy), "calibración (CALIBRATION.md)", doctor.OK)
    assert ok, "con fila reciente y sin cerradas pendientes, ✅"
    # sin CALIBRATION.md pero con iniciativas cerradas → ⚠️ (nunca se ha hecho una retro)
    (proj / "docs" / "roadmap" / "CALIBRATION.md").unlink()
    sin = por_que(doctor.diagnostico(str(proj), None, hoy=hoy), "calibración (CALIBRATION.md)", doctor.AVISO)
    assert sin and "3 iniciativa" in sin[0]["detalle"]


def test_indice_fts5_ausente_informa_valido_ok_y_corrupto_avisa_sin_escribir(tmp_path):
    proj = proyecto(tmp_path)
    memoria(proj, journal=1)
    antes = snapshot(proj)
    inf = diag(proj)
    fts = por_que(inf, "índice de búsqueda (FTS5)")
    assert fts and fts[0]["estado"] == doctor.INFO and "primera consulta" in fts[0]["arreglo"] + fts[0]["detalle"]
    assert snapshot(proj) == antes, "el doctor NO construye el índice: es de solo lectura"
    # lo construye una consulta real → válido
    subprocess.run([sys.executable, os.path.join(HERE, "knowledge-find.py"), "--root", str(proj), "--limit", "0"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    assert por_que(diag(proj), "índice de búsqueda (FTS5)", doctor.OK)
    # corrupto → ⚠️ con el arreglo (se reconstruye solo; si no, bórralo)
    (proj / ".claude" / "knowledge-index.sqlite").write_bytes(b"basura")
    av = por_que(diag(proj), "índice de búsqueda (FTS5)", doctor.AVISO)
    assert av and "knowledge-index.sqlite" in av[0]["arreglo"]


def test_repo_real_la_memoria_curada_se_ve_y_su_indice_pasa_el_lint(tmp_path):
    """Humo con el PLUGIN real (`plugin_root` = este repo, con su `scripts/lint_plugin.py`) sobre un
    proyecto consumidor realista: la memoria curada se cuenta y su índice pasa el lint de T-04.

    El proyecto es una copia del fixture de evals (`evals/fixtures/project/`, contenido inventado),
    no la memoria de ESTE repo: `docs/knowledge/` del propio repo es solo local y no está versionada,
    así que en CI no existe. Antes el test afirmaba además avisos de journal/calibración, que eran
    ESTADO DEL REPO, no comportamiento; esos avisos tienen cobertura propia con fixture más arriba."""
    import shutil
    proj = tmp_path / "proj"
    shutil.copytree(os.path.join(ROOT, "evals", "fixtures", "project", "docs", "knowledge"),
                    proj / "docs" / "knowledge")
    inf = diag(proj, ROOT)
    cur = por_que(inf, "memoria curada", doctor.OK)
    assert cur and int(re.search(r"(\d+) entrada", cur[0]["detalle"]).group(1)) == 2, cur
    assert por_que(inf, "índice de memoria (README)", doctor.OK), "el índice del fixture pasa el lint de T-04"


# --- estado efectivo del registro: los gaps de la revision I2 -----------------------------
#
# Todos miran lo MISMO: «hay un apunte en algun fichero» no es «este plugin esta activo para esta
# raiz». La regla la resuelve `estado_plugin()` y `install.mjs status` la repite (test de
# coherencia al final de la seccion).

def _instalados(cfg, entradas, clave="custom-agents@daycry"):
    (cfg / "plugins").mkdir(parents=True, exist_ok=True)
    (cfg / "plugins" / "installed_plugins.json").write_text(
        json.dumps({"version": 2, "plugins": {clave: entradas}}), encoding="utf-8")


def test_gap_b1_un_alta_de_otro_proyecto_no_registra_esta_raiz(tmp_path, monkeypatch):
    """Una entrada de scope `project` vale para SU `projectPath`, no para cualquiera."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    otro = tmp_path / "otro-proyecto"
    otro.mkdir()
    _instalados(cfg, [{"scope": "project", "projectPath": str(otro), "version": "9.9.9"}])
    inf = diag(proj, plugin(tmp_path, dest=proj / ".claude"))
    registro = fila(inf, "registro del plugin")
    assert registro["estado"] == doctor.AVISO and "copiado, no instalado" in registro["detalle"]
    assert fila(inf, "hooks registrados")["estado"] == doctor.AVISO
    assert doctor.registro_plugin(str(proj), str(cfg)) == [], "no aplica a esta raiz: no se cuenta"


def test_gap_b1_el_alta_de_ESTE_proyecto_si_cuenta_y_dice_su_scope_real(tmp_path, monkeypatch):
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    _instalados(cfg, [{"scope": "project", "projectPath": str(proj), "version": "9.9.9"}])
    inf = diag(proj, plugin(tmp_path))
    registro = fila(inf, "registro del plugin")
    assert registro["estado"] == doctor.OK
    assert "scope project" in registro["detalle"], "el scope es el que declara la entrada"
    assert fila(inf, "raíz del plugin")["detalle"].endswith("instalación: plugin")


def test_gap_b3_otro_marketplace_no_influye_ni_para_bien_ni_para_mal(tmp_path, monkeypatch):
    """`custom-agents@otro: false` no dice NADA de `custom-agents@daycry`."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    (cfg / "settings.json").write_text(json.dumps({"enabledPlugins": {
        "custom-agents@otro": False, "custom-agents@daycry": True}}), encoding="utf-8")
    plug = plugin(tmp_path)
    inf = diag(proyecto(tmp_path), plug)
    registro = fila(inf, "registro del plugin")
    assert registro["estado"] == doctor.OK and "custom-agents@daycry" in registro["detalle"]
    assert "custom-agents@otro" not in registro["detalle"]
    assert inf["exit"] == 0

    # y a la inversa: un `false` ajeno con el nuestro ausente no inventa un error
    (cfg / "settings.json").write_text(json.dumps({"enabledPlugins": {
        "custom-agents@otro": False}}), encoding="utf-8")
    inf2 = diag(proyecto(tmp_path), plug)
    assert fila(inf2, "registro del plugin")["estado"] == doctor.INFO and inf2["exit"] == 0


def test_gap_a3_un_false_del_scope_que_manda_gana_a_cualquier_alta(tmp_path, monkeypatch):
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    _instalados(cfg, [{"scope": "user", "version": "9.9.9"}])
    (cfg / "settings.json").write_text(json.dumps(
        {"enabledPlugins": {"custom-agents@daycry": False}}), encoding="utf-8")
    proj = proyecto(tmp_path)
    inf = diag(proj, plugin(tmp_path))
    assert fila(inf, "registro del plugin")["estado"] == doctor.ERROR
    assert inf["exit"] == 1
    est = doctor.estado_plugin(None, str(proj), str(cfg))
    assert est["habilitado"] is False, "el alta de installed_plugins no resucita un apagado"


def test_gap_a3_el_scope_project_manda_sobre_el_de_usuario(tmp_path, monkeypatch):
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    (cfg / "settings.json").write_text(json.dumps(
        {"enabledPlugins": {"custom-agents@daycry": False}}), encoding="utf-8")
    proj = proyecto(tmp_path, settings__json={"enabledPlugins": {"custom-agents@daycry": True}})
    est = doctor.estado_plugin(None, str(proj), str(cfg))
    assert est["habilitado"] is True and est["mandan"][0]["scope"] == "project"
    assert fila(diag(proj, plugin(tmp_path)), "registro del plugin")["estado"] == doctor.OK


def test_gap_a4_con_el_registro_en_error_los_hooks_no_pueden_salir_en_verde(tmp_path, monkeypatch):
    """El caso peor: plugin instalado en el cache, APAGADO, y el informe diciendo «plugin» y ✅."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    cache = cfg / "plugins" / "cache" / "daycry" / "custom-agents" / "9.9.9"
    plug = plugin(tmp_path, dest=cache)
    _instalados(cfg, [{"scope": "user", "installPath": str(cache), "version": "9.9.9"}])
    (cfg / "settings.json").write_text(json.dumps(
        {"enabledPlugins": {"custom-agents@daycry": False}}), encoding="utf-8")
    inf = diag(proyecto(tmp_path), plug)
    assert fila(inf, "registro del plugin")["estado"] == doctor.ERROR
    hooks = fila(inf, "hooks registrados")
    assert hooks["estado"] == doctor.AVISO and "NO está activo en el registro" in hooks["detalle"]
    assert hooks["arreglo"], "un aviso sin arreglo no vale"
    assert not fila(inf, "raíz del plugin")["detalle"].endswith("instalación: plugin")
    assert inf["exit"] == 1


def test_gap_b7_en_enabled_plugins_solo_true_habilita(tmp_path, monkeypatch):
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj, plug = proyecto(tmp_path), plugin(tmp_path)
    for valor in (0, None, "", "false", "true"):
        (cfg / "settings.json").write_text(json.dumps(
            {"enabledPlugins": {"custom-agents@daycry": valor}}), encoding="utf-8")
        inf = diag(proj, plug)
        assert doctor.estado_plugin(None, str(proj), str(cfg))["habilitado"] is False, valor
        aviso = fila(inf, "registro con valor inválido")
        assert aviso["estado"] == doctor.AVISO and "solo `true` habilita" in aviso["detalle"]
        assert aviso["arreglo"]


def test_gap_b6_el_json_trae_modo_y_registro_tambien_sin_raiz(tmp_path, monkeypatch):
    """La rama corta (raíz no localizable) tenía OTRA forma: `bloque["modo"]` reventaba."""
    _cfg_vacio(tmp_path, monkeypatch)
    vacia = tmp_path / "sin-plugin"
    vacia.mkdir()
    r = run("--root", str(proyecto(tmp_path)), "--plugin-root", str(vacia), "--json")
    d = json.loads(r.stdout)
    plug_b = [b for b in d["bloques"] if b["clave"] == "plugin"][0]
    assert set(plug_b) == {"clave", "titulo", "lineas", "modo", "registro"}
    assert plug_b["modo"] == "desconocido" and plug_b["registro"] == []


def test_gap_a2_codex_y_opencode_tienen_su_fila_de_registro(tmp_path, monkeypatch):
    """D5 pedía comprobar el registro en los tres runtimes, no solo en Claude Code."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj, plug = proyecto(tmp_path), plugin(tmp_path)
    # sin nada de Codex/OpenCode: informativo, sin arreglo que exigir
    inf = diag(proj, plug)
    assert fila(inf, "registro en Codex")["estado"] == doctor.INFO
    assert fila(inf, "registro en OpenCode")["estado"] == doctor.INFO

    # Codex: las cinco formas de escribir la tabla valen (es el `config.toml` lo que lo habilita)
    (proj / ".codex").mkdir()
    formas = (
        '[plugins."custom-agents@daycry"]\nenabled = true\n',
        '[plugins]\n"custom-agents@daycry" = { enabled = true }\n',
        'plugins."custom-agents@daycry".enabled = true\n',
        '[plugins."custom-agents@daycry"]  # comentario\nenabled   =   true\n',
        'plugins = { "custom-agents@daycry" = { enabled = true } }\n',
    )
    for forma in formas:
        (proj / ".codex" / "config.toml").write_text(forma, encoding="utf-8")
        codex = fila(diag(proj, plug), "registro en Codex")
        assert codex["estado"] == doctor.OK, forma
        assert "scope project" in codex["detalle"]

    (proj / ".codex" / "config.toml").write_text(
        '[plugins."custom-agents@daycry"]\nenabled = false\n', encoding="utf-8")
    codex = fila(diag(proj, plug), "registro en Codex")
    assert codex["estado"] == doctor.AVISO and "enabled = false" in codex["detalle"] and codex["arreglo"]

    # OpenCode: el adaptador dado de alta en `plugin` de `opencode.json`
    (proj / "opencode.json").write_text(json.dumps(
        {"plugins": ["./.opencode/plugins/custom-agents"]}), encoding="utf-8")
    oc = fila(diag(proj, plug), "registro en OpenCode")
    assert oc["estado"] == doctor.OK and "custom-agents" in oc["detalle"]

    # copiado pero sin alta: ⚠️ con el comando que lo arregla
    (proj / "opencode.json").write_text(json.dumps({"plugins": ["otro.js"]}), encoding="utf-8")
    (proj / ".opencode" / "plugins" / "custom-agents").mkdir(parents=True)
    (proj / ".opencode" / "plugins" / "custom-agents" / "index.js").write_text("//", encoding="utf-8")
    oc = fila(diag(proj, plug), "registro en OpenCode")
    assert oc["estado"] == doctor.AVISO and oc["arreglo"]

# --- gaps del intento 2 de la revision I2 --------------------------------------------------
#
# La pila de precedencia ENTERA, no dos de sus cuatro niveles: `enabledPlugins` se puede escribir
# en cualquier fichero de ajustes (`settings-reference#enabledplugins`, «Scope: Any file») y manda
# el de mas arriba (`settings#settings-precedence`: «Managed > command line > Project local >
# Shared project > User»). `.claude/settings.local.json` es donde escribe `claude plugin disable
# --scope local`: no leerlo daba `modo: plugin`, registro OK y hooks OK con el plugin APAGADO.

def _enabled(path, valor, clave="custom-agents@daycry"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"enabledPlugins": {clave: valor}}), encoding="utf-8")


def test_gap_i2_1_el_apagado_en_settings_local_manda_sobre_el_alta_de_user_y_de_project(tmp_path, monkeypatch):
    """El falso positivo de la iniciativa, en el fichero que mas manda de los tres del usuario."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    cache = cfg / "plugins" / "cache" / "daycry" / "custom-agents" / "9.9.9"
    plug = plugin(tmp_path, dest=cache)
    _instalados(cfg, [{"scope": "user", "installPath": str(cache), "version": "9.9.9"}])
    _enabled(cfg / "settings.json", True)
    proj = proyecto(tmp_path, settings__json={"enabledPlugins": {"custom-agents@daycry": True}})
    _enabled(proj / ".claude" / "settings.local.json", False)

    est = doctor.estado_plugin(str(plug), str(proj), str(cfg))
    assert est["habilitado"] is False, "un `false` en `local` gana a las altas de `project` y `user`"
    assert est["mandan"][0]["scope"] == "local"

    inf = diag(proj, plug)
    registro = fila(inf, "registro del plugin")
    assert registro["estado"] == doctor.ERROR
    # la fila NOMBRA el fichero que manda: con cuatro niveles, el veredicto solo no sirve de nada
    assert "settings.local.json" in registro["detalle"] and "scope local" in registro["detalle"]
    assert "settings.local.json" in registro["arreglo"]
    assert fila(inf, "hooks registrados")["estado"] == doctor.AVISO, "apagado => los hooks no cargan"
    assert not fila(inf, "raíz del plugin")["detalle"].endswith("instalación: plugin")
    assert inf["exit"] == 1


def test_gap_i2_1_el_alta_en_settings_local_gana_al_false_del_settings_compartido(tmp_path, monkeypatch):
    """Y al reves: `local` manda tambien para ACTIVAR (`claude plugin enable --scope local`)."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path, settings__json={"enabledPlugins": {"custom-agents@daycry": False}})
    _enabled(proj / ".claude" / "settings.local.json", True)

    est = doctor.estado_plugin(None, str(proj), str(cfg))
    assert est["habilitado"] is True and est["mandan"][0]["scope"] == "local"
    registro = fila(diag(proj, plugin(tmp_path)), "registro del plugin")
    assert registro["estado"] == doctor.OK
    assert "manda" in registro["detalle"] and "settings.local.json" in registro["detalle"]


def test_gap_i2_1_managed_settings_manda_sobre_todos_los_demas(tmp_path, monkeypatch):
    """El nivel de la plataforma esta por encima de todo; su ruta depende del sistema, asi que se
    declara (`managed_settings_path`) y se puede inyectar."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    _enabled(proj / ".claude" / "settings.local.json", True)
    gestionado = tmp_path / "managed-settings.json"
    _enabled(gestionado, False)
    monkeypatch.setattr(doctor, "managed_settings_path", lambda: str(gestionado))

    est = doctor.estado_plugin(None, str(proj), str(cfg))
    assert est["habilitado"] is False and est["mandan"][0]["scope"] == "managed"
    registro = fila(diag(proj, plugin(tmp_path)), "registro del plugin")
    assert registro["estado"] == doctor.ERROR and str(gestionado) in registro["detalle"]


def test_gap_i2_1_sin_managed_settings_la_ruta_es_una_cadena_y_no_estorba(tmp_path, monkeypatch):
    """En una maquina sin ajustes gestionados (lo normal) la funcion no lanza ni inventa fuentes."""
    assert isinstance(doctor.managed_settings_path(), str)
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    niveles = [s for s, _p in doctor._niveles_settings(str(proj), str(cfg))]
    assert niveles[:3] == ["user", "project", "local"]


@pytest.mark.parametrize("ruta", [123, None, ["x"], {"a": 1}, True])
def test_gap_i2_2_un_project_path_que_no_es_cadena_no_tumba_el_doctor(tmp_path, monkeypatch, ruta):
    """`os.path.abspath(123)` lanzaba y el informe ENTERO se quedaba sin salir (stdout vacio,
    exit 1) por un fichero del usuario mal formado, que es justo cuando se usa `/doctor`."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    _instalados(cfg, [{"scope": "project", "projectPath": ruta, "version": "9.9.9"}])

    assert doctor.estado_plugin(None, str(proj), str(cfg))["habilitado"] is False
    assert doctor._misma_ruta(ruta, str(proj)) is False, "no casa y no lanza"
    inf = diag(proj, plugin(tmp_path))
    aviso = fila(inf, "registro sin proyecto atribuible")
    assert aviso["estado"] == doctor.AVISO and aviso["arreglo"]
    assert "no es una cadena" in aviso["detalle"]

    # y el proceso entero: sale el informe, sin traceback y con exit 0 (es un aviso, no un error)
    r = run("--root", str(proj), "--plugin-root", str(plugin(tmp_path, dest=tmp_path / "p2")))
    assert r.returncode == 0, r.stderr
    assert "Traceback" not in r.stderr and len(r.stdout.splitlines()) > 5


def test_gap_i2_6_local_es_scope_de_proyecto_y_un_scope_desconocido_no_cuenta(tmp_path, monkeypatch):
    """Caer a `user` era el lado permisivo: una entrada con un scope raro valia para TODOS."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = plugin(tmp_path)

    _instalados(cfg, [{"scope": "raro", "version": "9.9.9"}])
    assert doctor.estado_plugin(None, str(proj), str(cfg))["habilitado"] is False
    aviso = fila(diag(proj, plug), "registro con scope desconocido")
    assert aviso["estado"] == doctor.AVISO and aviso["arreglo"] and "raro" in aviso["detalle"]

    # `local` SI es un scope documentado, y como `project` exige su `projectPath`
    _instalados(cfg, [{"scope": "local", "version": "9.9.9"}])
    assert doctor.estado_plugin(None, str(proj), str(cfg))["habilitado"] is False
    _instalados(cfg, [{"scope": "local", "projectPath": str(proj), "version": "9.9.9"}])
    est = doctor.estado_plugin(None, str(proj), str(cfg))
    assert est["habilitado"] is True and est["aplican"][0]["scope"] == "local"


def test_gap_i2_7_la_misma_carpeta_por_un_enlace_casa(tmp_path, monkeypatch):
    """Junction, `subst` o symlink: el `projectPath` grabado y el `--root` son la MISMA carpeta."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    # lo que se afirma SIEMPRE (no necesita privilegios): resolver no puede romper nada
    assert doctor._ruta_real("") == os.path.abspath("")
    inexistente = str(tmp_path / "no-existe")
    assert doctor._ruta_real(inexistente) == os.path.abspath(inexistente), "caida al valor original"
    assert doctor._misma_ruta(str(proj) + os.sep, str(proj))

    enlace = tmp_path / "enlace"
    try:
        os.symlink(str(proj), str(enlace), target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        # Windows sin «modo desarrollador»: los junctions NO piden permisos de administrador.
        hecho = os.name == "nt" and subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(enlace), str(proj)],
            capture_output=True, text=True, encoding="utf-8", errors="replace").returncode == 0
        if not hecho:
            pytest.skip("esta maquina no deja crear enlaces (ni symlink ni junction)")
    _instalados(cfg, [{"scope": "project", "projectPath": str(enlace), "version": "9.9.9"}])
    assert doctor.estado_plugin(None, str(proj), str(cfg))["habilitado"] is True
    assert doctor._misma_ruta(str(enlace), str(proj))


def test_gap_i2_10_el_mismo_settings_por_dos_caminos_se_cuenta_una_vez(tmp_path, monkeypatch):
    """Con `CLAUDE_CONFIG_DIR` en el `.claude/` del proyecto, `user` y `project` son el MISMO
    fichero: se lista una vez y con el scope mas especifico, no como si fueran dos altas."""
    proj = proyecto(tmp_path, settings__json={"enabledPlugins": {"custom-agents@daycry": True}})
    cfg = proj / ".claude"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    est = doctor.estado_plugin(None, str(proj), str(cfg))
    assert len(est["aplican"]) == 1, est["aplican"]
    assert est["mandan"][0]["scope"] == "project"
    registro = fila(diag(proj, plugin(tmp_path)), "registro del plugin")
    assert registro["estado"] == doctor.OK and "scope user" not in registro["detalle"]


def test_gap_i2_5_la_fila_de_codex_mira_la_clave_que_escribe_el_instalador(tmp_path, monkeypatch):
    """Con un fork, la clave deducida de la raiz de Claude Code no es la que el instalador escribe
    en `config.toml` (siempre `custom-agents@daycry`): se miran las dos y se dice cual se vio."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    cache = cfg / "plugins" / "cache" / "fork" / "custom-agents" / "9.9.9"
    plug = plugin(tmp_path, dest=cache)
    assert doctor.clave_plugin(str(plug), str(cfg)) == "custom-agents@fork"
    proj = proyecto(tmp_path)
    (proj / ".codex").mkdir()
    (proj / ".codex" / "config.toml").write_text(
        '[plugins."custom-agents@daycry"]\nenabled = true\n', encoding="utf-8")
    codex = fila(diag(proj, plug), "registro en Codex")
    assert codex["estado"] == doctor.OK and "custom-agents@daycry" in codex["detalle"]


def test_gap_i2_11_la_fila_informativa_de_codex_nombra_lo_detectado(tmp_path, monkeypatch):
    """Se afirmaba «Codex esta en esta maquina (<CODEX_HOME>)» mirando un directorio que puede no
    existir: lo detectado es el `.codex` del proyecto."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    (proj / ".codex").mkdir()
    codex = fila(diag(proj, plugin(tmp_path)), "registro en Codex")
    assert codex["estado"] == doctor.INFO
    assert str(proj / ".codex") in codex["detalle"]
    assert os.environ["CODEX_HOME"] not in codex["detalle"], "no se nombra lo que no se ha visto"


def test_gap_i2_3_el_alta_de_opencode_se_compara_por_ruta_resuelta_no_por_nombre(tmp_path, monkeypatch):
    """Casar por basename daba OK a cualquier `custom-agents` de cualquier sitio, y
    `status` (ruta exacta) decia lo contrario sobre el MISMO `opencode.json`."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = plugin(tmp_path)
    (proj / ".opencode" / "plugins" / "custom-agents").mkdir(parents=True)
    (proj / ".opencode" / "plugins" / "custom-agents" / "index.js").write_text("//", encoding="utf-8")

    # mismo nombre, otra carpeta: NO es el adaptador instalado
    (proj / "opencode.json").write_text(json.dumps(
        {"plugins": ["./vendor/custom-agents"]}), encoding="utf-8")
    oc = fila(diag(proj, plug), "registro en OpenCode")
    assert oc["estado"] == doctor.AVISO and "NO es el adaptador instalado" in oc["detalle"]
    assert oc["arreglo"]

    # escalar: `status` no lo cuenta como alta (`json-array`), asi que `/doctor` tampoco
    (proj / "opencode.json").write_text(json.dumps(
        {"plugins": "./.opencode/plugins/custom-agents"}), encoding="utf-8")
    oc = fila(diag(proj, plug), "registro en OpenCode")
    assert oc["estado"] == doctor.AVISO and "no es una lista" in oc["detalle"] and oc["arreglo"]

    # la ruta que escribe el instalador (relativa al fichero de config): OK
    (proj / "opencode.json").write_text(json.dumps(
        {"plugins": ["./.opencode/plugins/custom-agents"]}), encoding="utf-8")
    assert fila(diag(proj, plug), "registro en OpenCode")["estado"] == doctor.OK


def test_gap_i2_8_un_opencode_json_ilegible_se_distingue_de_uno_ausente(tmp_path, monkeypatch):
    """«Reinstala» no arregla un JSON roto del usuario; el gemelo de Codex ya lo distinguia."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    (proj / "opencode.json").write_text("{roto", encoding="utf-8")
    oc = fila(diag(proj, plugin(tmp_path)), "registro en OpenCode")
    assert oc["estado"] == doctor.AVISO and "no es JSON válido" in oc["detalle"]
    assert "corrige tu `opencode.json`" in oc["arreglo"] and "install -p opencode" not in oc["arreglo"]


# --- coherencia /doctor <-> status ---------------------------------------------------------
#
# La invariante de la iniciativa: las dos herramientas NO pueden contradecirse sobre el mismo
# estado. La mitad de python se afirma SIEMPRE (no necesita node); si no hay node, se salta solo
# la comparacion con `status`. Y se comprueba en los TRES runtimes, no solo en Claude Code.

def _status(proj, cfg, env_extra=None):
    """`install.mjs status` agrupado por proveedor: `{label: [filas]}` (o `None` sin node)."""
    import shutil
    node = shutil.which("node")
    if not node:
        return None
    env = _isolated_subprocess_env(dict(CLAUDE_CONFIG_DIR=str(cfg), NO_COLOR="1", **(env_extra or {})))
    r = subprocess.run([node, os.path.join(ROOT, "install", "install.mjs"), "status", "--dir", str(proj)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert r.returncode == 0, r.stderr
    out, actual = {}, None
    for l in r.stdout.splitlines():
        if re.match(r"^ {6}\S", l):
            if actual:
                out.setdefault(actual, []).append(l.strip())
        elif re.match(r"^ {2}\S", l):
            actual = re.split(r"\s{2,}", l.strip())[0]
    return out


def test_status_subprocess_no_hereda_cli_ni_credenciales_del_host(tmp_path, monkeypatch):
    """B-I5: el mock del doctor no aísla el subprocess del instalador."""
    import shutil
    node = shutil.which("node")
    if not node:
        pytest.skip("sin Node para el subprocess propio")
    host_bin = tmp_path / "host-bin"
    host_bin.mkdir()
    monkeypatch.setenv("PATH", str(host_bin) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("ANTHROPIC_API_KEY", "OWN_TEST_SENTINEL")
    def own_run(args, **kwargs):
        cli_env = kwargs["env"]
        assert str(host_bin) not in cli_env["PATH"]
        assert "ANTHROPIC_API_KEY" not in cli_env
        assert os.path.isfile(os.path.join(cli_env["PATH"].split(os.pathsep)[0],
                                           "codex.cmd" if os.name == "nt" else "codex"))
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(subprocess, "run", own_run)
    assert _status(proyecto(tmp_path), tmp_path / "cfg") == {}


@pytest.mark.skipif(os.name != "nt", reason="PATHEXT is a Windows executable selector")
def test_status_stubs_no_dependen_de_pathext_del_host(tmp_path, monkeypatch):
    """B-I5: .EXE solo omitía nuestros .cmd y alcanzaba un runtime vecino a Node."""
    if not _NODE_EXECUTABLE:
        pytest.skip("sin Node")
    monkeypatch.setenv("PATHEXT", ".EXE")
    def own_run(args, **kwargs):
        env = kwargs["env"]
        assert ".CMD" in env["PATHEXT"].upper().split(";")
        assert os.path.isfile(os.path.join(env["PATH"].split(os.pathsep)[0], "codex.cmd"))
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(subprocess, "run", own_run)
    assert _status(proyecto(tmp_path), tmp_path / "cfg") == {}


def _registrado(filas):
    return any("registrado: sí" in f for f in filas or [])


def _montar_estado(estado, nivel, cfg, proj, otro):
    ajustes = {"user": cfg / "settings.json",
               "project": proj / ".claude" / "settings.json",
               "local": proj / ".claude" / "settings.local.json"}[nivel]
    entrada = {"scope": "user" if nivel == "user" else nivel, "version": "9.9.9"}
    if nivel != "user":
        entrada["projectPath"] = str(proj)
    if estado == "alta":
        _instalados(cfg, [entrada])
    elif estado == "apagado":
        _instalados(cfg, [entrada])
        _enabled(ajustes, False)
    elif estado == "alta-de-otro-proyecto":
        _instalados(cfg, [{"scope": "project" if nivel == "user" else nivel,
                           "projectPath": str(otro), "version": "9.9.9"}])
    else:
        _enabled(ajustes, "true")


@pytest.mark.parametrize("nivel", ["user", "local"])
@pytest.mark.parametrize("estado,activo", [
    ("alta", True),
    ("apagado", False),
    ("alta-de-otro-proyecto", False),
    ("valor-invalido", False),
])
def test_doctor_y_status_dan_el_MISMO_veredicto_sobre_el_MISMO_estado(tmp_path, monkeypatch,
                                                                     estado, activo, nivel):
    """Gap A-3: `status` decia «registrado: sí» donde `/doctor` decia error. Se monta un estado y
    se comprueba que las dos herramientas coinciden — la del usuario (`status`, que M-01 usa como
    prueba de la instalacion) y la de dentro de la sesion (`/doctor`). Los cuatro estados, en el
    nivel `user` y en `local` (gap I2-1)."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    otro = tmp_path / "otro-proyecto"
    otro.mkdir()
    _montar_estado(estado, nivel, cfg, proj, otro)

    # la mitad de python se afirma SIEMPRE: no depende de node (gap I2-9)
    doctor_activo = doctor.estado_plugin(None, str(proj), str(cfg))["habilitado"]
    assert doctor_activo == activo, f"{estado}/{nivel}: /doctor dice {doctor_activo}"

    filas = _status(proj, cfg)
    if filas is None:
        pytest.skip("sin `node`: la mitad `status` de la comparacion no se puede correr")
    status_activo = _registrado(filas.get("Claude Code"))
    assert status_activo == activo, f"{estado}/{nivel}: status dice {status_activo} en {filas}"
    assert doctor_activo == status_activo, "las dos herramientas NO pueden contradecirse"


@pytest.mark.parametrize("caso,activo", [
    ("alta-exacta", True),
    ("mismo-nombre-otra-ruta", False),
    ("escalar", False),
    ("sin-plugin", False),
])
def test_doctor_y_status_coinciden_tambien_en_opencode(tmp_path, monkeypatch, caso, activo):
    """Gap I2-3: la invariante estaba impuesta SOLO para Claude Code, y la fila de OpenCode casaba
    por basename mientras `status` comparaba la ruta exacta."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = plugin(tmp_path)
    (proj / ".opencode" / "plugins" / "custom-agents").mkdir(parents=True)
    (proj / ".opencode" / "plugins" / "custom-agents" / "index.js").write_text("//", encoding="utf-8")
    spec = {"alta-exacta": ["./.opencode/plugins/custom-agents"],
            "mismo-nombre-otra-ruta": ["./vendor/custom-agents"],
            "escalar": "./.opencode/plugins/custom-agents",
            "sin-plugin": []}[caso]
    (proj / "opencode.json").write_text(json.dumps({"plugins": spec}), encoding="utf-8")

    doctor_activo = fila(diag(proj, plug), "registro en OpenCode")["estado"] == doctor.OK
    assert doctor_activo == activo, f"{caso}: /doctor dice {doctor_activo}"
    filas = _status(proj, cfg)
    if filas is None:
        pytest.skip("sin `node`: la mitad `status` de la comparacion no se puede correr")
    assert _registrado(filas.get("OpenCode")) == activo, filas
    assert _registrado(filas.get("OpenCode")) == doctor_activo, "no pueden contradecirse"


@pytest.mark.parametrize("toml,activo", [
    ('[plugins."custom-agents@daycry"]\nenabled = true\n', True),
    ('[plugins."custom-agents@daycry"]\nenabled = false\n', False),
    ('[plugins."custom-agents@otro"]\nenabled = true\n', False),
    ("", False),
])
def test_doctor_y_status_coinciden_tambien_en_codex(tmp_path, monkeypatch, toml, activo):
    """Misma invariante en el tercer runtime: es `enabled` del `config.toml`, y solo eso."""
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = plugin(tmp_path)
    (proj / ".codex").mkdir()
    (proj / ".codex" / "config.toml").write_text(toml, encoding="utf-8")

    doctor_activo = fila(diag(proj, plug), "registro en Codex")["estado"] == doctor.OK
    assert doctor_activo == activo, f"/doctor dice {doctor_activo} para {toml!r}"
    filas = _status(proj, cfg)
    if filas is None:
        pytest.skip("sin `node`: la mitad `status` de la comparacion no se puede correr")
    assert _registrado(filas.get("Codex")) == activo, filas
    assert _registrado(filas.get("Codex")) == doctor_activo, "no pueden contradecirse"


# ----------------------------------- T-12 (E5): nombre real de los comandos ----

def _con_comandos(plug, *nombres, doc=None):
    """Añade `commands/<n>.md` al plugin de fixture y, opcionalmente, ficheros de doc viva
    (`{ruta_relativa: texto}`) para la comprobación de espacio de nombres."""
    (plug / "commands").mkdir(exist_ok=True)
    for n in nombres:
        (plug / "commands" / f"{n}.md").write_text(f"---\nname: {n}\n---\n", encoding="utf-8")
    for rel, texto in (doc or {}).items():
        p = plug / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")
    return plug


def test_t12_plugin_instalado_la_fila_dice_el_nombre_con_espacio_de_nombres(tmp_path, monkeypatch):
    cfg = _cfg_vacio(tmp_path, monkeypatch)
    cache = cfg / "plugins" / "cache" / "daycry" / "custom-agents" / "9.9.9"
    plug = _con_comandos(plugin(tmp_path, dest=cache), "dev-cycle", "doctor")
    (cfg / "plugins" / "installed_plugins.json").write_text(json.dumps(
        {"version": 2, "plugins": {"custom-agents@daycry": [
            {"scope": "user", "installPath": str(cache), "version": "9.9.9"}]}}), encoding="utf-8")
    inf = diag(proyecto(tmp_path), plug)

    f = fila(inf, "nombre de los comandos")
    assert f["estado"] == doctor.INFO, f          # informativa: no hay nada que arreglar
    assert "/custom-agents:dev-cycle" in f["detalle"]
    assert "Unknown command" in f["detalle"]
    # aditiva: ni un ❌ ni un ⚠️ nuevos, mismo exit code
    assert [l["que"] for l in lineas(inf, doctor.AVISO)] == []
    assert inf["resumen"][doctor.ERROR] == 0 and inf["exit"] == 0


def test_t12_bundle_local_no_genera_ruido_y_dice_la_forma_corta(tmp_path, monkeypatch):
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = _con_comandos(plugin(tmp_path, dest=proj / ".claude"), "dev-cycle")
    inf = diag(proj, plug)

    f = fila(inf, "nombre de los comandos")
    assert f["estado"] == doctor.INFO and f["arreglo"] == ""
    assert "/dev-cycle" in f["detalle"] and "/custom-agents:dev-cycle" in f["detalle"]
    # sin ⚠️ de doc viva: en modo copia no hay doc viva del plugin que revisar aquí
    assert [l for l in lineas(inf, doctor.AVISO) if l["que"] == "doc viva sin el espacio de nombres"] == []
    assert inf["exit"] == 0


def test_t12_doc_viva_que_solo_cita_la_forma_corta_es_aviso_con_el_fichero(tmp_path, monkeypatch):
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = _con_comandos(
        plugin(tmp_path), "dev-cycle", "doctor",
        doc={"README.md": "Arranca con `/dev-cycle` y listo.\n",              # solo forma corta -> ⚠️
             "CLAUDE.md": "Instalado como plugin: `/custom-agents:dev-cycle`.\n",   # menciona -> ok
             "docs/README.md": "Sin comandos aquí.\n"})                       # no cita -> ok
    inf = diag(proj, plug)

    f = fila(inf, "doc viva sin el espacio de nombres")
    assert f["estado"] == doctor.AVISO
    assert f["detalle"].startswith("README.md:"), f["detalle"]
    assert "CLAUDE.md" not in f["detalle"] and "docs/README.md" not in f["detalle"]
    assert "/custom-agents:<comando>" in f["arreglo"]
    # un aviso no rompe la instalación
    assert inf["resumen"][doctor.ERROR] == 0 and inf["exit"] == 0


def test_t12_la_doc_viva_de_ESTE_repo_no_deja_aviso(tmp_path):
    """La puerta de no-regresión: los 7 ficheros de doc viva del repo citan la forma que funciona
    EN SU PRIMERA mención de un comando, no en una nota al pie (gap R4a-3)."""
    cmds = doctor._comandos_del_plugin(ROOT)
    assert "dev-cycle" in cmds and "doctor" in cmds
    assert doctor._doc_viva_sin_namespace(ROOT, cmds) == []


def test_r4a3_la_nota_al_pie_ya_no_satisface_la_comprobacion(tmp_path, monkeypatch):
    """Gap R4a-3: antes bastaba con que `/custom-agents:` apareciera UNA vez en cualquier sitio, así
    que una nota decenas de líneas por debajo del primer comando tecleable colaba. Ahora se exige
    que la PRIMERA mención lo lleve (misma línea o antes)."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    nota_al_pie = "Arranca con `/dev-cycle`.\n" + "relleno\n" * 40 + "Nota: `/custom-agents:dev-cycle`.\n"
    antes = "Instalado como plugin: `/custom-agents:dev-cycle`.\n\nArranca con `/dev-cycle`.\n"
    misma_linea = "Teclea `/custom-agents:dev-cycle` (o `/dev-cycle` con el bundle copiado).\n"
    plug = _con_comandos(plugin(tmp_path), "dev-cycle", "doctor",
                         doc={"README.md": nota_al_pie,       # namespace DESPUÉS → ⚠️
                              "CLAUDE.md": antes,             # namespace ANTES → ok
                              "docs/README.md": misma_linea})  # misma línea → ok
    inf = diag(proj, plug)

    f = fila(inf, "doc viva sin el espacio de nombres")
    assert f["estado"] == doctor.AVISO
    assert f["detalle"].startswith("README.md:"), f["detalle"]
    assert "CLAUDE.md" not in f["detalle"] and "docs/README.md" not in f["detalle"]
    assert "PRIMERA" in f["detalle"], f["detalle"]
    assert "nota al pie" in f["arreglo"], f["arreglo"]
    assert inf["resumen"][doctor.ERROR] == 0 and inf["exit"] == 0


def test_r4a10_sin_carpeta_commands_la_fila_lo_dice_y_no_inventa_un_nombre(tmp_path, monkeypatch):
    """Gap R4a-10: con un `plugin_root` sin `commands/` (instalación truncada, justo el caso para el
    que existe `/doctor`) la fila afirmaba `/custom-agents:dev-cycle` igual. Ahora dice que no
    puede confirmarlo."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = plugin(tmp_path)                       # sin _con_comandos: no hay commands/
    assert doctor._comandos_del_plugin(str(plug)) == []
    inf = diag(proj, plug)

    f = fila(inf, "nombre de los comandos")
    assert f["estado"] == doctor.INFO and f["arreglo"] == ""
    assert "no hay carpeta `commands/`" in f["detalle"], f["detalle"]
    assert "/custom-agents:<comando>" in f["detalle"], f["detalle"]
    assert "/custom-agents:dev-cycle" not in f["detalle"], "no se inventa un comando que no existe"
    # y sin comandos tampoco se acusa a la doc viva de nada
    assert [l for l in lineas(inf, doctor.AVISO)
            if l["que"] == "doc viva sin el espacio de nombres"] == []
    assert inf["exit"] == 0


def test_r4a18_la_fila_dice_de_que_runtime_es_el_espacio_de_nombres(tmp_path, monkeypatch):
    """Gap R4a-18 (multi-runtime): el prefijo `custom-agents:` es de Claude Code; en Codex y
    OpenCode el mismo comando se invoca sin prefijo. La fila lo dice en los tres modos."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = _con_comandos(plugin(tmp_path), "dev-cycle")
    for modo in ("plugin", "copia", "inactivo", "desconocido"):
        ls = doctor.comprobar_nombre_comandos(str(plug), modo)
        det = ls[0]["detalle"]
        assert "Claude Code" in det, (modo, det)
        assert ls[0]["estado"] == doctor.INFO and ls[0]["arreglo"] == ""


def test_r4a25_una_ruta_con_glob_no_cuenta_como_mencion_de_comando(tmp_path, monkeypatch):
    """Gap R4a-25: el lookbehind dejaba pasar el `*`, así que una RUTA con glob
    (`commands/*/dev-cycle.md`) contaba como «mención corta de un comando» y sacaba un ⚠️ falso.
    Una ruta no es un comando tecleable: nadie escribe `commands/*/dev-cycle.md` en el picker."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = _con_comandos(
        plugin(tmp_path), "dev-cycle", "doctor",
        doc={"README.md": "Los comandos viven en `commands/*/dev-cycle.md` y se generan solos.\n",
             "CLAUDE.md": "Nada que ver aquí.\n",
             "docs/README.md": "Tampoco aquí.\n"})
    inf = diag(proj, plug)

    assert [l for l in lineas(inf, doctor.AVISO)
            if l["que"] == "doc viva sin el espacio de nombres"] == []
    assert doctor._doc_viva_sin_namespace(str(plug), ["dev-cycle", "doctor"]) == []
    assert inf["exit"] == 0


def test_r4a37_una_ruta_relativa_o_del_home_tampoco_es_un_comando(tmp_path, monkeypatch):
    """Gap R4a-37: el lookbehind cerraba `*` pero no `.` ni `~`, así que `./dev-cycle` y
    `~/dev-cycle` —rutas, no comandos tecleables— seguían contando como mención corta."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = _con_comandos(
        plugin(tmp_path), "dev-cycle", "doctor",
        doc={"README.md": "El script vive en `./dev-cycle` y su copia en `~/dev-cycle`.\n",
             "CLAUDE.md": "Nada que ver aquí.\n",
             "docs/README.md": "Tampoco aquí.\n"})
    inf = diag(proj, plug)

    assert [l for l in lineas(inf, doctor.AVISO)
            if l["que"] == "doc viva sin el espacio de nombres"] == []
    assert doctor._doc_viva_sin_namespace(str(plug), ["dev-cycle", "doctor"]) == []
    assert inf["exit"] == 0
    # …y un comando de verdad SIGUE saliendo (el lookbehind no se ha comido la detección)
    plug2 = _con_comandos(
        plugin(tmp_path / "otro"), "dev-cycle", "doctor",
        doc={"README.md": "Ejecuta `/dev-cycle` y listo.\n"})
    assert doctor._doc_viva_sin_namespace(str(plug2), ["dev-cycle", "doctor"]) == ["README.md"]
def test_b45_la_mención_en_negrita_markdown_si_es_un_comando_tecleable(tmp_path, monkeypatch):
    """Gap B4-5: el lookbehind que cierra `*` (R4a-25/R4a-37) se llevaba por delante la mención en
    NEGRITA —`**/dev-cycle**`, la forma que usan `docs/INSTALL.md` y su espejo en inglés—, que sí
    es tecleable. El `**` ahí es marcado markdown, no parte de una ruta."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = _con_comandos(
        plugin(tmp_path), "dev-cycle", "doctor",
        doc={"README.md": "Comandos: **/dev-cycle**, **/doctor**.\n",
             "CLAUDE.md": "Nada que ver aquí.\n",
             "docs/README.md": "Tampoco aquí.\n"})
    inf = diag(proj, plug)

    assert doctor._doc_viva_sin_namespace(str(plug), ["dev-cycle", "doctor"]) == ["README.md"]
    assert [l for l in lineas(inf, doctor.AVISO)
            if l["que"] == "doc viva sin el espacio de nombres"] != []
    # …y con el espacio de nombres ANTES, la negrita deja de ser un aviso
    plug2 = _con_comandos(
        plugin(tmp_path / "ok"), "dev-cycle", "doctor",
        doc={"README.md": "Se teclea `/custom-agents:dev-cycle`.\nComandos: **/dev-cycle**.\n"})
    assert doctor._doc_viva_sin_namespace(str(plug2), ["dev-cycle", "doctor"]) == []
    # …y el glob de ruta `docs/**/*.md` NO se convierte en mención por el camino
    plug3 = _con_comandos(
        plugin(tmp_path / "glob"), "dev-cycle", "doctor",
        doc={"README.md": "Los ficheros `docs/**/dev-cycle.md` se generan solos.\n"})
    assert doctor._doc_viva_sin_namespace(str(plug3), ["dev-cycle", "doctor"]) == []


# ------------------------------------------------------------------ capacidades opcionales (T-09)
# El registro `capabilities.py` (T-13) y el cargador GENERICO de adaptadores de `knowledge-services`
# (`backends/__init__.py`) son los REALES: nada aqui simula `capabilities.py`. Solo el contrato
# de adaptador (`health`/`verify`) se dobla con fakes cuando hace falta controlar un estado que el
# adaptador real (red) no puede dar deterministamente en un test (timeout/degradado/error/excepcion).

BACKENDS_INIT_REAL = os.path.join(ROOT, "skills", "knowledge-services", "backends", "__init__.py")
FIXTURES_BACKENDS = os.path.join(ROOT, "evals", "fixtures", "knowledge-services")

_spec_b = importlib.util.spec_from_file_location("backends_init_doctor_test", BACKENDS_INIT_REAL)
backends_real = importlib.util.module_from_spec(_spec_b)
_spec_b.loader.exec_module(backends_real)


def _cap(id_="x", enabled=True, health=None, config_path=None, doctor_txt=None):
    return {"id": id_, "config_path": config_path, "enabled": enabled,
            "health": health if health is not None else {"estado": "declarado"},
            "doctor": doctor_txt if doctor_txt is not None else f"{id_}: activa",
            "setup_step": "..."}


def _taxonomy_con_backend(tmp_path, cap_id, tipo, config, enabled=True):
    """`.claude/knowledge-services/taxonomy.json` con SOLO el backend que hace falta para el test
    (no se valida contra el esquema completo: `_leer_backend_entry` solo lee `backends.<id>`,
    igual que hace `knowledge-sync.py` -- no pasa por `knowledge-schema.py`)."""
    d = tmp_path / ".claude" / "knowledge-services"
    d.mkdir(parents=True, exist_ok=True)
    datos = {"backends": {cap_id: {"type": tipo, "enabled": enabled, "config": config}}}
    (d / "taxonomy.json").write_text(json.dumps(datos), encoding="utf-8")
    return os.path.join(".claude", "knowledge-services", "taxonomy.json")


class _AdaptadorNoDisponibleFake(Exception):
    pass


class _BackendsModFake:
    """Doble del contrato de `backends/__init__.py` con el estado de `health`/`verify` fijado a
    mano -- solo para las ramas que un adaptador real no puede dar de forma determinista sin red
    (timeout/degradado/error/excepcion). Las ramas sano/export atrasado/adaptador no disponible
    se prueban con el cargador y el adaptador REALES mas abajo."""
    AdaptadorNoDisponible = _AdaptadorNoDisponibleFake

    def __init__(self, salud=None, verificacion=None, lanza_health=False, lanza_verify=False, no_disponible=False):
        self._salud = salud or {}
        self._verificacion = verificacion
        self._lanza_health = lanza_health
        self._lanza_verify = lanza_verify
        self._no_disponible = no_disponible
        self.cfg_recibido_por_health = None  # gap 94: espia para comprobar el timeout topado

    def cargar_adaptador(self, tipo, directorios):
        if self._no_disponible:
            raise self.AdaptadorNoDisponible(f"sin adaptador para `{tipo}`")
        return self

    def health(self, cfg):
        self.cfg_recibido_por_health = cfg
        if self._lanza_health:
            raise RuntimeError("boom-health")
        return self._salud

    def verify(self, cfg):
        if self._lanza_verify:
            raise RuntimeError("boom-verify")
        return self._verificacion


def test_capacidad_backend_sin_tipo_declarado_devuelve_none():
    assert doctor._linea_capacidad_backend("x", None, {}, _BackendsModFake(), "d") is None


def test_capacidad_backend_topa_el_timeout_antes_de_llamar_health():
    """gap 94: un `timeout_ms` generoso en `taxonomy.json` (pensado para una publicacion real, no
    para un diagnostico rapido) se recorta a `CAPACIDAD_TIMEOUT_MS_TOPE` antes de llegar a
    `health()` — sin esto, una capacidad con `timeout_ms: 30000` podria colgar /doctor 30s."""
    fake = _BackendsModFake(salud={"estado": "sano"})
    doctor._linea_capacidad_backend("x", "t", {"health": {"url": "http://x", "timeout_ms": 30000}}, fake, "d")
    assert fake.cfg_recibido_por_health["health"]["timeout_ms"] == doctor.CAPACIDAD_TIMEOUT_MS_TOPE


def test_capacidad_backend_respeta_timeout_por_debajo_del_tope():
    fake = _BackendsModFake(salud={"estado": "sano"})
    doctor._linea_capacidad_backend("x", "t", {"health": {"url": "http://x", "timeout_ms": 500}}, fake, "d")
    assert fake.cfg_recibido_por_health["health"]["timeout_ms"] == 500


def test_capacidad_backend_inyecta_root_del_proyecto_antes_de_health(tmp_path):
    """gap 111: `doctor.py` conoce `project` (la raiz real donde vive `taxonomy.json`) pero no lo
    pasaba al adaptador -- un backend cuya `health()`/`verify()` necesite resolver rutas relativas
    (p. ej. `export_dir` de markdown_export.py, gap 88) recibia un `cfg` sin `_root` y resolvia
    contra el CWD del proceso, no la raiz del proyecto diagnosticado."""
    fake = _BackendsModFake(salud={"estado": "sano"})
    doctor._linea_capacidad_backend("x", "t", {"health": {"url": "http://x"}}, fake, "d",
                                    project=str(tmp_path))
    assert fake.cfg_recibido_por_health["_root"] == os.path.abspath(str(tmp_path))


def test_bloque_capacidades_recorta_por_presupuesto_total(monkeypatch):
    """gap 94: con muchas capacidades activas y una red lenta, `bloque_capacidades` no debe
    convertirse en un diagnostico de minutos — al superar el presupuesto TOTAL, el resto se
    reporta como recortado en vez de seguir esperando una a una."""
    import time as time_mod

    class _CapMod:
        @staticmethod
        def enumerar(project):
            return [{"id": f"cap{i}", "enabled": True, "health": None} for i in range(5)]

    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _CapMod())
    # fix2 (#167): el presupuesto solo acota las capacidades que REQUIEREN red (backend declarado)
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (object(), "d"))
    monkeypatch.setattr(doctor, "_leer_backend_entry", lambda project, cap, backend_id=None: {"type": "t"})
    monkeypatch.setattr(doctor, "CAPACIDADES_PRESUPUESTO_S", 0.05)

    llamadas = []

    def _linea_lenta(project, cap, backends_mod, backends_dir, **kwargs):
        llamadas.append(cap["id"])
        time_mod.sleep(0.03)
        return doctor.linea(doctor.INFO, cap["id"], "activa")

    monkeypatch.setattr(doctor, "_linea_capacidad", _linea_lenta)
    bloque = doctor.bloque_capacidades("plugin", "project")
    assert len(llamadas) < 5
    avisos = [l for l in bloque["lineas"] if l["estado"] == doctor.AVISO and "recortada" in l["detalle"]]
    assert len(avisos) == 1


def test_bloque_capacidades_topa_tope_ms_al_presupuesto_restante(monkeypatch):
    """gap 124: `tope_ms` no es la constante ESTATICA `CAPACIDAD_TIMEOUT_MS_TOPE` para todas las
    capacidades del bloque -- si ya se gasto la mayor parte del presupuesto TOTAL en las
    anteriores, la que queda por comprobar recibe el PRESUPUESTO RESTANTE (mas corto), no el tope
    fijo completo, para que la suma nunca rebase `CAPACIDADES_PRESUPUESTO_S`."""
    import time as time_mod

    class _CapMod:
        @staticmethod
        def enumerar(project):
            return [{"id": "cap0", "enabled": True, "health": None},
                    {"id": "cap1", "enabled": True, "health": None}]

    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _CapMod())
    # fix2 (#167): el presupuesto solo acota las capacidades que REQUIEREN red (backend declarado)
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (object(), "d"))
    monkeypatch.setattr(doctor, "_leer_backend_entry", lambda project, cap, backend_id=None: {"type": "t"})
    monkeypatch.setattr(doctor, "CAPACIDADES_PRESUPUESTO_S", 2.02)

    topes_recibidos = []

    def _linea_espia(project, cap, backends_mod, backends_dir, tope_ms=None, **kwargs):
        topes_recibidos.append(tope_ms)
        time_mod.sleep(0.05)
        return doctor.linea(doctor.INFO, cap["id"], "activa")

    monkeypatch.setattr(doctor, "_linea_capacidad", _linea_espia)
    doctor.bloque_capacidades("plugin", "project")
    assert len(topes_recibidos) == 2
    assert topes_recibidos[0] == doctor.CAPACIDAD_TIMEOUT_MS_TOPE
    # tras gastar ~50ms del presupuesto total (2.02s), a la segunda capacidad le queda menos
    # margen que el tope fijo de 2000ms -- se recorta al presupuesto restante.
    assert topes_recibidos[1] < doctor.CAPACIDAD_TIMEOUT_MS_TOPE


def test_bloque_capacidades_aviso_de_recorte_cita_el_tiempo_transcurrido_real(monkeypatch):
    """gap 124: el mensaje de recorte citaba siempre el tope CONFIGURADO
    (`CAPACIDADES_PRESUPUESTO_S`), no el tiempo REAL transcurrido -- con una sola capacidad lenta
    que ya rebasa el presupuesto, el tiempo transcurrido real es mayor que el tope nominal."""
    import time as time_mod

    class _CapMod:
        @staticmethod
        def enumerar(project):
            return [{"id": f"cap{i}", "enabled": True, "health": None} for i in range(3)]

    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _CapMod())
    # fix2 (#167): el presupuesto solo acota las capacidades que REQUIEREN red (backend declarado)
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (object(), "d"))
    monkeypatch.setattr(doctor, "_leer_backend_entry", lambda project, cap, backend_id=None: {"type": "t"})
    monkeypatch.setattr(doctor, "CAPACIDADES_PRESUPUESTO_S", 0.05)

    def _linea_lenta(project, cap, backends_mod, backends_dir, **kwargs):
        time_mod.sleep(0.08)
        return doctor.linea(doctor.INFO, cap["id"], "activa")

    monkeypatch.setattr(doctor, "_linea_capacidad", _linea_lenta)
    bloque = doctor.bloque_capacidades("plugin", "project")
    aviso = next(l for l in bloque["lineas"] if l["estado"] == doctor.AVISO and "recortada" in l["detalle"])
    assert "0s" not in aviso["detalle"].split("tope de ")[0]
    assert "transcurrid" in aviso["detalle"].lower()


def test_bloque_capacidades_no_comprueba_con_tope_ms_por_debajo_del_suelo(monkeypatch):
    """gap 133: cuando lo que queda de presupuesto TOTAL cae por debajo del SUELO
    (`_CAPACIDAD_TOPE_MS_MINIMO`), la capacidad restante NO se comprueba con un timeout de pocos
    ms -- un timeout asi de corto sobre una red local normal declara «apagado»/«error» un backend
    SANO (falso negativo) con un remedio inutil. Se cuenta como recortada, igual que si el
    presupuesto ya estuviera agotado del todo."""
    import time as time_mod

    class _CapMod:
        @staticmethod
        def enumerar(project):
            return [{"id": "cap0", "enabled": True, "health": None},
                    {"id": "cap1", "enabled": True, "health": None}]

    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _CapMod())
    # fix2 (#167): el presupuesto solo acota las capacidades que REQUIEREN red (backend declarado)
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (object(), "d"))
    monkeypatch.setattr(doctor, "_leer_backend_entry", lambda project, cap, backend_id=None: {"type": "t"})
    # presupuesto total suficiente para que cap0 arranque por encima del suelo, pero que tras
    # gastar los 50ms de cap0 deja a cap1 un resto por debajo de `_CAPACIDAD_TOPE_MS_MINIMO`.
    monkeypatch.setattr(doctor, "CAPACIDADES_PRESUPUESTO_S", 0.32)

    topes_recibidos = []

    def _linea_espia(project, cap, backends_mod, backends_dir, tope_ms=None, **kwargs):
        topes_recibidos.append(tope_ms)
        time_mod.sleep(0.05)
        return doctor.linea(doctor.INFO, cap["id"], "activa")

    monkeypatch.setattr(doctor, "_linea_capacidad", _linea_espia)
    bloque = doctor.bloque_capacidades("plugin", "project")
    # cap0 se comprueba con su tope normal; cap1 NUNCA se comprueba con un tope por debajo del
    # suelo -- o no aparece, o si aparece es con un tope >= al suelo.
    assert len(topes_recibidos) == 1
    for tope in topes_recibidos:
        assert tope >= doctor._CAPACIDAD_TOPE_MS_MINIMO
    avisos = [l for l in bloque["lineas"] if l["estado"] == doctor.AVISO and "recortada" in l["detalle"]]
    assert len(avisos) == 1


def test_cfg_con_timeout_topado_nunca_produce_timeout_ms_cero():
    """gap 133: `tope_ms=0` (o negativo) escrito tal cual en `health.timeout_ms` es indistinguible
    de "no configurado" para `markdown_export._timeout_s()` (que trata `valor <= 0` como
    "usa el default de 800 ms") -- el recorte de `/doctor` desaparecia SILENCIOSAMENTE justo en el
    caso limite en el que mas hace falta (presupuesto ya agotado)."""
    cfg = doctor._cfg_con_timeout_topado({}, tope_ms=0)
    assert cfg["health"]["timeout_ms"] > 0
    assert cfg["health"]["timeout_ms"] >= doctor._CAPACIDAD_TOPE_MS_MINIMO

    cfg_negativo = doctor._cfg_con_timeout_topado({}, tope_ms=-50)
    assert cfg_negativo["health"]["timeout_ms"] >= doctor._CAPACIDAD_TOPE_MS_MINIMO


def test_capacidad_backend_nunca_sincronizado_no_dice_export_atrasado():
    """gap 119: `verify()` distingue `razon: "nunca_sincronizado"` (gap 87, aun no hay ninguna
    publicacion) de un desfase real -- antes ambos caian en el mismo texto generico "export
    atrasado (0 desfase(s))", que es enganoso cuando `desfase` esta vacio precisamente porque
    todavia no se ha publicado nada."""
    fake = _BackendsModFake(salud={"estado": "sano"},
                            verificacion={"ok": False, "desfase": [], "razon": "nunca_sincronizado"})
    l = doctor._linea_capacidad_backend("x", "t", {}, fake, "d")
    assert l["estado"] == doctor.AVISO
    assert "export atrasado" not in l["detalle"]
    assert "nunca" in l["detalle"].lower() or "sin publicar" in l["detalle"].lower()


def test_capacidad_backend_off_con_timeout_es_informativo():
    fake = _BackendsModFake(salud={"estado": "off", "detalle": "sin conexion a http://x: TimeoutError: timed out"})
    l = doctor._linea_capacidad_backend("x", "t", {}, fake, "d")
    assert l["estado"] == doctor.INFO
    assert "timeout" in l["detalle"].lower()
    assert l["arreglo"]


def test_capacidad_backend_off_sin_timeout_es_informativo():
    fake = _BackendsModFake(salud={"estado": "off", "detalle": "sin `health.url` configurada"})
    l = doctor._linea_capacidad_backend("x", "t", {}, fake, "d")
    assert l["estado"] == doctor.INFO


def test_capacidad_backend_degradado_es_aviso():
    fake = _BackendsModFake(salud={"estado": "degradado", "detalle": "status=degraded"})
    l = doctor._linea_capacidad_backend("x", "t", {}, fake, "d")
    assert l["estado"] == doctor.AVISO
    assert l["arreglo"]


def test_capacidad_backend_error_es_aviso_no_error():
    """gap 100 (fix1 knowledge-services): un backend EXTERNO en error (stack caído, respuesta
    invalida) no debe tumbar /doctor con exit 1 — el ERROR se reserva para un fallo de
    configuracion de la propia capacidad (`taxonomy.json` invalido, ver `_linea_capacidad`)."""
    fake = _BackendsModFake(salud={"estado": "error", "detalle": "respuesta no valida"})
    l = doctor._linea_capacidad_backend("x", "t", {}, fake, "d")
    assert l["estado"] == doctor.AVISO
    assert l["arreglo"]


def test_capacidad_backend_health_lanza_excepcion_degrada_a_aviso():
    fake = _BackendsModFake(lanza_health=True)
    l = doctor._linea_capacidad_backend("x", "t", {}, fake, "d")
    assert l["estado"] == doctor.AVISO
    assert "health()" in l["detalle"]


def test_capacidad_backend_verify_lanza_excepcion_degrada_a_aviso():
    fake = _BackendsModFake(salud={"estado": "sano"}, lanza_verify=True)
    l = doctor._linea_capacidad_backend("x", "t", {}, fake, "d")
    assert l["estado"] == doctor.AVISO
    assert "verify()" in l["detalle"]


def test_capacidad_backend_real_sano_sin_desfase_via_adaptador_de_fixture():
    """Adaptador REAL (`backends/__init__.py`, `cargar_adaptador`) sobre el `type: "test"` de
    `evals/fixtures/knowledge-services/backend_test.py` (el mismo que usa knowledge-sync)."""
    l = doctor._linea_capacidad_backend("x", "test", {"estado_salud": "sano", "desfase": []},
                                        backends_real, FIXTURES_BACKENDS)
    assert l["estado"] == doctor.OK
    assert "sano" in l["detalle"]


def test_capacidad_backend_real_export_atrasado_via_adaptador_de_fixture():
    cfg = {"estado_salud": "sano",
           "desfase": [{"knowledge_id": "a.pattern.x", "motivo": "no indexado", "remedio": "reindexa: build_view"}]}
    l = doctor._linea_capacidad_backend("x", "test", cfg, backends_real, FIXTURES_BACKENDS)
    assert l["estado"] == doctor.AVISO
    assert "export atrasado" in l["detalle"]
    assert l["arreglo"] == "reindexa: build_view"


def test_capacidad_backend_real_tipo_sin_adaptador_es_aviso():
    l = doctor._linea_capacidad_backend("x", "tipo-que-no-existe", {}, backends_real, FIXTURES_BACKENDS)
    assert l["estado"] == doctor.AVISO
    assert "no disponible" in l["detalle"]


def test_linea_capacidad_desactivada_es_informativa():
    l = doctor._linea_capacidad(".", _cap(enabled=False), None, None)
    assert l["estado"] == doctor.INFO
    assert l["detalle"] == "desactivado"
    assert l["arreglo"]


def test_linea_capacidad_taxonomy_invalida_reporta_fichero_y_campo():
    cap = _cap(health={"estado": "error", "detalle": "categories: la lista no puede estar vacia",
                       "fichero": "taxonomy.json"})
    l = doctor._linea_capacidad(".", cap, None, None)
    assert l["estado"] == doctor.ERROR
    assert "categories" in l["detalle"] and "taxonomy.json" in l["detalle"]
    assert "taxonomy.json" in l["arreglo"]


def test_linea_capacidad_activa_sin_backend_usa_el_texto_generico_de_la_propia_capacidad():
    l = doctor._linea_capacidad(".", _cap(doctor_txt="x: activa, sin comprobacion de red"), None, None)
    assert l["estado"] == doctor.INFO
    assert l["detalle"] == "x: activa, sin comprobacion de red"


def test_linea_capacidad_activa_con_backend_en_vivo_via_taxonomy_json(tmp_path):
    config_path = _taxonomy_con_backend(tmp_path, "midbackend", "test", {"estado_salud": "sano", "desfase": []})
    cap = _cap(id_="midbackend", config_path=config_path)
    l = doctor._linea_capacidad(str(tmp_path), cap, backends_real, FIXTURES_BACKENDS)
    assert l["estado"] == doctor.OK


def test_doctor_py_no_menciona_kwipu_literalmente():
    """T-09: todo lo que sabe este fichero sobre una capacidad concreta llega por el contrato
    `{id, config_path, enabled, health, doctor, setup_step}` de `capabilities.py` -- nunca un
    literal de backend en el propio codigo de /doctor."""
    texto = open(SCRIPT, encoding="utf-8").read()
    assert "kwipu" not in texto.lower()


def test_bloque_capacidades_via_capabilities_real_proyecto_sin_config(tmp_path):
    """`capabilities.py` REAL (no un doble): sin `taxonomy.json` de proyecto, `knowledge-gate`
    usa la plantilla por defecto (ok) y la capacidad opcional aparece desactivada."""
    proj = proyecto(tmp_path)
    # fix1 gap #9: las desactivadas SIN su fichero de config solo salen con `verbose`
    b = doctor.bloque_capacidades(None, str(proj), verbose=True)
    ids = {l["que"] for l in b["lineas"]}
    assert "knowledge-gate" in ids
    assert any(i for i in ids if i != "knowledge-gate")   # al menos una capacidad opcional mas
    otra = next(l for l in b["lineas"] if l["que"] != "knowledge-gate")
    assert otra["estado"] == doctor.INFO
    assert otra["detalle"] == "desactivado"


def test_bloque_capacidades_via_capabilities_real_taxonomy_invalida(tmp_path):
    """`categories` vacia (esquema real, `knowledge-schema.py`) -> knowledge-gate en error con
    fichero + campo + arreglo, via el pipeline REAL `capabilities.enumerar()` -> `_linea_capacidad`."""
    proj = tmp_path / "proj"
    d = proj / ".claude" / "knowledge-services"
    d.mkdir(parents=True, exist_ok=True)
    (d / "taxonomy.json").write_text(json.dumps({"version": 1, "categories": []}), encoding="utf-8")
    b = doctor.bloque_capacidades(None, str(proj))
    kg = next(l for l in b["lineas"] if l["que"] == "knowledge-gate")
    assert kg["estado"] == doctor.ERROR
    assert "taxonomy.json" in kg["detalle"] or "taxonomy.json" in kg["arreglo"]
    assert kg["arreglo"]


def test_bloque_capacidades_capabilities_no_disponible_degrada_a_informativo(monkeypatch):
    """`capabilities.py` ausente (instalacion parcial): el bloque no rompe /doctor, informa."""
    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: None)
    b = doctor.bloque_capacidades(None, ".")
    assert len(b["lineas"]) == 1
    assert b["lineas"][0]["estado"] == doctor.INFO


def test_bloque_capacidades_esta_en_diagnostico(tmp_path):
    proj = proyecto(tmp_path)
    inf = diag(proj)
    claves = {b["clave"] for b in inf["bloques"]}
    assert "capacidades" in claves


# ------------------------------------------------------------------ fix1 gap #9 (training-data-services)

def test_f1fix1_gap09_optin_sin_su_config_se_omite_salvo_verbose(tmp_path, monkeypatch):
    """Regla GENERICA del contrato de capacidades: una capacidad desactivada cuyo `config_path` no
    existe en el proyecto no pinta nada en /doctor (cero impacto de un opt-in no configurado) salvo
    con `--verbose`; con su fichero, activa, o en error, sale siempre. Sin nombres de capacidad."""
    proj = tmp_path / "proj"
    (proj / "cfg").mkdir(parents=True)
    (proj / "cfg" / "b.json").write_text("{}", encoding="utf-8")
    caps = [_cap("a", enabled=False, config_path=os.path.join("cfg", "a.json")),
            _cap("b", enabled=False, config_path=os.path.join("cfg", "b.json")),
            _cap("c", enabled=True, config_path=os.path.join("cfg", "c.json")),
            _cap("d", enabled=False, config_path=os.path.join("cfg", "d.json"),
                 health={"estado": "error", "detalle": "roto", "fichero": "cfg/d.json"}),
            _cap("e", enabled=False, config_path=None)]

    class _CapMod:
        @staticmethod
        def enumerar(project):
            return caps

    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _CapMod())
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (None, "d"))
    normal = {l["que"] for l in doctor.bloque_capacidades(None, str(proj))["lineas"]}
    assert normal == {"b", "c", "d", "e"}
    verbose = {l["que"] for l in doctor.bloque_capacidades(None, str(proj), verbose=True)["lineas"]}
    assert verbose == {"a", "b", "c", "d", "e"}


def test_f1fix1_gap09_todas_omitidas_deja_una_linea_informativa(tmp_path, monkeypatch):
    class _CapMod:
        @staticmethod
        def enumerar(project):
            return [_cap("a", enabled=False, config_path="no-existe.json")]

    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _CapMod())
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (None, "d"))
    b = doctor.bloque_capacidades(None, str(tmp_path))
    assert [l["que"] for l in b["lineas"]] == ["capacidades opcionales"]
    assert b["lineas"][0]["estado"] == doctor.INFO and "--verbose" in b["lineas"][0]["arreglo"]


def test_f1fix1_gap09_proyecto_sin_config_no_pinta_desactivadas_y_verbose_si(tmp_path):
    """Pipeline REAL (`capabilities.enumerar()`): sin ficheros de config de proyecto, ninguna fila
    `desactivado`; `--verbose` (CLI) las muestra."""
    proj = proyecto(tmp_path)
    b = doctor.bloque_capacidades(None, str(proj))
    assert not [l for l in b["lineas"] if l["detalle"] == "desactivado"]
    for flag in ("--verbose", "--all"):
        r = run("--root", str(proj), "--json", flag)
        inf = json.loads(r.stdout)
        cap = next(x for x in inf["bloques"] if x["clave"] == "capacidades")
        assert [l for l in cap["lineas"] if l["detalle"] == "desactivado"], flag
    r = run("--root", str(proj), "--json")
    cap = next(x for x in json.loads(r.stdout)["bloques"] if x["clave"] == "capacidades")
    assert not [l for l in cap["lineas"] if l["detalle"] == "desactivado"]


# ------------------------------------------------------------------ T-10 (training-data-services): capacidad real

def _training_json(proj, **cfg):
    d = proj / ".claude" / "knowledge-services"
    d.mkdir(parents=True, exist_ok=True)
    datos = {"version": 1}
    datos.update(cfg)
    (d / "training.json").write_text(json.dumps(datos), encoding="utf-8")
    return d / "training.json"


def _filas(proj, que, verbose=False):
    b = doctor.bloque_capacidades(None, str(proj), verbose=verbose)
    return [l for l in b["lineas"] if l["que"] == que]


def test_t10_sin_training_json_doctor_no_reporta_nada_de_la_capacidad(tmp_path):
    proj = proyecto(tmp_path)
    antes = sorted(os.listdir(str(proj)))
    assert _filas(proj, "training") == []
    inf = diag(proj)
    lineas = [l for b in inf["bloques"] for l in b["lineas"]]
    assert not [l for l in lineas if "training" in f"{l['que']} {l['detalle']} {l['arreglo']}"]
    assert sorted(os.listdir(str(proj))) == antes


def test_t10_training_desactivado_con_fichero_es_informativo(tmp_path):
    proj = proyecto(tmp_path)
    _training_json(proj, enabled=False, root="../store", id_prefix="geo")
    [l] = _filas(proj, "training")
    assert l["estado"] == doctor.INFO and l["detalle"] == "desactivado"


def test_t10_training_activo_informa_recuento_y_dataset_sin_bloquear(tmp_path):
    proj = proyecto(tmp_path)
    _training_json(proj, enabled=True, root="../store", id_prefix="geo")
    v = tmp_path / "store" / "cases" / "ramp.steep" / "v001"
    ejemplo = os.path.join(ROOT, "skills", "training-data-services", "assets", "case-store-example",
                           "cases", "ramp.steep", "v002")
    import shutil
    shutil.copytree(ejemplo, str(v))
    (v / "metadata.json").write_text(json.dumps({"case_id": "geo-ramp.steep", "family": "ramp", "variant": "steep",
                                                  "version": 1, "created_at": "2026-09-23T10:00:00Z",
                                                  "outcome": "success"}), encoding="utf-8")
    [l] = _filas(proj, "training")
    assert l["estado"] == doctor.INFO
    assert "approved 1" in l["detalle"] and "(1 versiones)" in l["detalle"]
    assert "dataset: desactualizado" in l["detalle"]
    assert doctor.diagnostico(str(proj))["exit"] in (0, 1)
    assert not [x for x in diag(proj)["bloques"] for y in x["lineas"]
                if y["que"] == "training" and y["estado"] == doctor.ERROR]


def test_t10_training_config_invalida_es_error_con_fichero_y_campo(tmp_path):
    proj = proyecto(tmp_path)
    ruta = _training_json(proj, enabled=True, root="../store")          # sin id_prefix
    [l] = _filas(proj, "training")
    assert l["estado"] == doctor.ERROR
    assert "training.json" in l["detalle"] and "id_prefix" in l["detalle"]
    assert "training.json" in l["arreglo"]
    assert ruta.exists() and not (tmp_path / "store").exists()


def test_t10_doctor_py_no_nombra_ninguna_capacidad_concreta():
    """CA-14: la capacidad llega por el registro; `doctor.py` no tiene codigo de `training`."""
    with open(SCRIPT, encoding="utf-8") as f:
        assert "training" not in f.read()


def test_t10fix1_164_el_reloj_del_bloque_arranca_antes_de_enumerar(monkeypatch):
    """#164 (regla GENERICA del contrato de capacidades): lo que tarda `enumerar()` (una capacidad que
    recuenta al evaluarse) cuenta dentro del presupuesto TOTAL del bloque, y `enumerar()` recibe el
    plazo que queda (`plazo_s`) si lo acepta; un registro antiguo sin ese parametro sigue funcionando."""
    import time as time_mod
    recibidos = []

    class _CapMod:
        @staticmethod
        def enumerar(project, plazo_s=None):
            recibidos.append(plazo_s)
            time_mod.sleep(0.3)
            return [{"id": f"cap{i}", "enabled": True, "health": None} for i in range(3)]

    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _CapMod())
    # fix2 (#167): el recorte solo afecta a las capacidades que REQUIEREN red (backend declarado)
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (object(), "d"))
    monkeypatch.setattr(doctor, "_leer_backend_entry", lambda project, cap, backend_id=None: {"type": "t"})
    monkeypatch.setattr(doctor, "CAPACIDADES_PRESUPUESTO_S", 0.32)
    comprobadas = []

    def _linea(project, cap, backends_mod, backends_dir, **kwargs):
        comprobadas.append(cap["id"])
        return doctor.linea(doctor.INFO, cap["id"], "activa")
    monkeypatch.setattr(doctor, "_linea_capacidad", _linea)
    bloque = doctor.bloque_capacidades("plugin", "project")
    assert recibidos and 0 < recibidos[0] <= 0.32
    assert comprobadas == [], comprobadas
    assert any(l["estado"] == doctor.AVISO and "recortada" in l["detalle"] for l in bloque["lineas"])

    class _CapModAntiguo:
        @staticmethod
        def enumerar(project):
            return [{"id": "cap0", "enabled": True, "health": None}]
    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _CapModAntiguo())
    monkeypatch.setattr(doctor, "CAPACIDADES_PRESUPUESTO_S", 5.0)
    doctor.bloque_capacidades("plugin", "project")
    assert comprobadas == ["cap0"]


# ------------------------------------------------------------------ T-10 fix1 #161: cobertura de doctor.py >= 90 %
# (gate `coverage-gate.py --changed-only --min 90`): las ramas de degradacion que ningun test pisaba.

def test_t10fix1_161_leer_json_correr_y_json_de_degradan_sin_lanzar(tmp_path, monkeypatch):
    roto = tmp_path / "roto.json"
    roto.write_text("{no es json", encoding="utf-8")
    datos, err = doctor._leer_json(str(roto))
    assert datos is None and "no es JSON válido" in err
    real_open = open

    def _sin_permiso(ruta, *a, **k):
        if str(ruta) == str(roto):
            raise PermissionError(13, "denegado")
        return real_open(ruta, *a, **k)
    monkeypatch.setattr("builtins.open", _sin_permiso)
    datos, err = doctor._leer_json(str(roto))
    monkeypatch.undo()
    assert datos is None and err == "no se puede leer (PermissionError)"
    assert doctor._correr(["/no/existe/binario-inexistente-xyz"]) == ("", False)
    assert doctor._json_de("{roto") is None and doctor._json_de(None) is None


def test_t10fix1_161_cargar_linter_sin_plugin_o_roto_es_none(tmp_path):
    assert doctor._cargar_linter(None) is None
    assert doctor._cargar_linter(str(tmp_path)) is None
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "lint_plugin.py").write_text("raise RuntimeError('roto')\n", encoding="utf-8")
    assert doctor._cargar_linter(str(tmp_path)) is None


def test_t10fix1_161_hooks_json_roto_ausente_o_sin_raiz(tmp_path):
    assert doctor._bloque_plugin_hooks(str(tmp_path))[0]["estado"] == doctor.AVISO
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "hooks.json").write_text("{roto", encoding="utf-8")
    assert doctor._bloque_plugin_hooks(str(tmp_path))[0]["estado"] == doctor.ERROR
    (tmp_path / "hooks" / "hooks.json").write_text('{"hooks": []}', encoding="utf-8")
    l = doctor._bloque_plugin_hooks(str(tmp_path))[0]
    assert l["estado"] == doctor.ERROR and "raíz `hooks`" in l["detalle"]


def test_t10fix1_161_entradas_plugin_y_ruta_real(monkeypatch):
    datos = {"a": {"b": {doctor.PLUGIN_PREFIJO + "x": 1, "otro@y": 2}}}
    assert doctor._entradas_plugin(datos, "a", "b") == {doctor.PLUGIN_PREFIJO + "x": 1}
    assert doctor._entradas_plugin(datos, "a", "b", "c") == {}
    assert doctor._entradas_plugin({"a": 3}, "a") == {}

    def _falla(_p):
        raise OSError("no se puede resolver")
    monkeypatch.setattr(doctor.os.path, "realpath", _falla)
    assert doctor._ruta_real("x") == os.path.abspath("x")
    monkeypatch.setattr(doctor.os.path, "abspath", _falla)
    assert doctor._ruta_real("x") == ""


def test_t10fix1_161_dev_guardrails_regla_desconocida_y_no_booleana():
    ls = doctor._dev_valida_guardrails([1])
    assert ls[0]["estado"] == doctor.ERROR
    ls = doctor._dev_valida_guardrails({"alcance": "si", "inventada": True})
    estados = {l["que"]: l["estado"] for l in ls}
    assert estados == {"dev.json `guardrails.alcance`": doctor.ERROR, "dev.json `guardrails.inventada`": doctor.AVISO}


def test_t10fix1_161_marcadores_degradan_a_leer_el_estado(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "_correr", lambda cmd, cwd=None: ("", False))
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "usage-state.json").write_text("{roto", encoding="utf-8")
    l = doctor._marcadores(None, str(tmp_path))[0]
    assert l["estado"] == doctor.AVISO and "usage-state.json" in l["detalle"]
    (tmp_path / ".claude" / "usage-state.json").write_text(json.dumps({"x/T-01": {}}), encoding="utf-8")
    l = doctor._marcadores(None, str(tmp_path))[0]
    assert l["estado"] == doctor.AVISO and "x/T-01" in l["detalle"]


def test_t10fix1_161_informes_de_evals(tmp_path):
    assert "sin `evals/reports/`" in doctor._informes(str(tmp_path))[0]["detalle"]
    d = tmp_path / "evals" / "reports"
    d.mkdir(parents=True)
    assert doctor._informes(str(tmp_path))[0]["detalle"] == "sin informes"
    (d / "2026-09-01.json").write_text("{}", encoding="utf-8")
    (d / "zz.json").write_text("{}", encoding="utf-8")
    det = doctor._informes(str(tmp_path))[0]["detalle"]
    assert "2 informe(s)" in det and "fecha no legible" in det


def test_t10fix1_161_lint_knowledge_index_ramas_de_error(tmp_path):
    base = tmp_path / "docs" / "knowledge"
    (base / "adr").mkdir(parents=True)
    (base / "adr" / "ADR-001-x.md").write_text("---\nestado: aceptada\n---\n", encoding="utf-8")
    assert "no existe" in doctor.lint_knowledge_index(str(tmp_path))[0]
    (base / "README.md").write_text("# indice\n\nsin tabla\n", encoding="utf-8")
    assert "no encuentro la tabla" in doctor.lint_knowledge_index(str(tmp_path))[0]
    tabla = ("| Entrada | ID | Tipo | Área |\n|---|---|---|---|\n"
             "| [a](adr/ADR-001-x.md) | ADR-001 | adr | |\n"
             "| [b](adr/ADR-001-x.md) | ADR-001 | adr | x |\n"
             "| sin enlace | | adr | x |\n"
             "| [c](adr/no-existe.md) | ADR-003 | adr | x |\n"
             "\n| [d](adr/ADR-001-x.md) | ADR-009 | adr | x |\n")
    (base / "README.md").write_text(tabla, encoding="utf-8")
    errs = " ".join(doctor.lint_knowledge_index(str(tmp_path)))
    for trozo in ("fuera de la tabla", "fila sin «Área»", "ID repetido", "ruta repetida", "fila sin ID",
                  "no enlaza a ningún fichero", "que no existe"):
        assert trozo in errs, trozo


def test_t10fix1_161_curadas_sin_knowledge_find_usa_el_parser_local(tmp_path):
    base = tmp_path / "docs" / "knowledge"
    for carpeta, fichero, estado in (("adr", "ADR-001-x.md", "aceptada"), ("gotchas", "GOT-001-y.md", None),
                                     ("lessons", "LES-001-z.md", "Propuesta")):
        (base / carpeta).mkdir(parents=True)
        (base / carpeta / fichero).write_text(f"---\nestado: {estado}\n---\n" if estado else "sin frontmatter\n",
                                              encoding="utf-8")
        (base / carpeta / "README.md").write_text("indice\n", encoding="utf-8")

    class _KfRoto:
        @staticmethod
        def cargar_corpus(_project):
            raise RuntimeError("roto")
    assert sorted(doctor._curadas(str(tmp_path), _KfRoto())) == [("adr", "aceptada"), ("gotcha", "?"),
                                                                 ("leccion", "propuesta")]
    assert doctor._frontmatter_estado(str(tmp_path / "no-existe.md")) == ""


def test_t10fix1_161_main_rechaza_argumentos_invalidos(tmp_path, capsys):
    assert doctor.main(["--hoy", "ayer"]) == 2
    assert doctor.main(["--root", str(tmp_path / "no-existe")]) == 2
    assert doctor.main(["--root", str(tmp_path), "--plugin-root", str(tmp_path / "no-existe")]) == 2
    assert "❌ uso" in capsys.readouterr().err


def test_t10fix1_161_acepta_plazo_por_firma():
    def con(project, plazo_s=None):
        return project

    def kw(project, **k):
        return project

    def sin(project):
        return project
    assert doctor._acepta_plazo(con) and doctor._acepta_plazo(kw) and not doctor._acepta_plazo(sin)
    assert doctor._acepta_plazo(object()) is False            # sin firma inspeccionable: no lanza


# ------------------------------------------------------------------ T-10 fix2 (#167, #179, M7): regla GENERICA

def _cap_mod_lento(capacidades, segundos):
    import time as time_mod

    class _CapMod:
        @staticmethod
        def enumerar(project, plazo_s=None):
            time_mod.sleep(segundos)
            return [dict(c) for c in capacidades]
    return _CapMod()


def test_t10fix2_167_un_error_de_config_nunca_se_pierde_por_el_presupuesto(monkeypatch):
    """#167: si `enumerar()` gasta el presupuesto del bloque (una capacidad que recuenta), las
    capacidades SIN red se pintan igual (su fila ya esta calculada: coste cero) y un error de
    configuracion nunca se descarta. El recorte solo cuenta y nombra las que requieren red (backend
    declarado) y quedan sin comprobar."""
    caps = [{"id": "gate", "enabled": False, "config_path": "t.json",
             "health": {"estado": "error", "detalle": "categories: vacia", "fichero": "t.json"}},
            {"id": "sinred", "enabled": True, "health": {"estado": "ok"}, "doctor": "sinred: activa"},
            {"id": "conred", "enabled": True, "health": {"estado": "declarado"}, "doctor": "conred: activa"}]
    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _cap_mod_lento(caps, 0.3))
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (object(), "d"))
    monkeypatch.setattr(doctor, "_leer_backend_entry",
                        lambda project, cap, backend_id=None: {"type": "t"} if cap["id"] == "conred" else {})
    monkeypatch.setattr(doctor, "CAPACIDADES_PRESUPUESTO_S", 0.32)
    red = []
    monkeypatch.setattr(doctor, "_linea_capacidad_backend",
                        lambda cap_id, tipo, *a, **k: red.append(cap_id) if tipo else None)
    bloque = doctor.bloque_capacidades("plugin", "project", verbose=True)
    por_id = {l["que"]: l for l in bloque["lineas"]}
    assert por_id["gate"]["estado"] == doctor.ERROR and "t.json" in por_id["gate"]["detalle"]
    assert por_id["sinred"]["estado"] == doctor.INFO and por_id["sinred"]["detalle"] == "sinred: activa"
    assert red == [], red
    recorte = [l for l in bloque["lineas"] if l["estado"] == doctor.AVISO and "recortada" in l["detalle"]]
    assert len(recorte) == 1 and "conred" in recorte[0]["detalle"] and "sinred" not in recorte[0]["detalle"]
    assert "1 capacidad(es)" in recorte[0]["detalle"]


def test_t10fix2_167_exit_1_con_config_invalida_aunque_el_bloque_se_agote(monkeypatch, tmp_path):
    """#167 (el escenario de la Lente B): config de una capacidad rota + un bloque que se agota en
    `enumerar()` -> el error sale y `/doctor` sale con exit 1 (antes: exit 0 y una sola linea de recorte)."""
    caps = [{"id": "gate", "enabled": False, "config_path": "t.json",
             "health": {"estado": "error", "detalle": "JSON ilegible", "fichero": "t.json"}}]
    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _cap_mod_lento(caps, 0.2))
    monkeypatch.setattr(doctor, "CAPACIDADES_PRESUPUESTO_S", 0.1)
    inf = doctor.diagnostico(str(tmp_path), None, None, verbose=True)
    capas = next(b for b in inf["bloques"] if b["clave"] == "capacidades")
    assert any(l["estado"] == doctor.ERROR and l["que"] == "gate" for l in capas["lineas"]), capas
    assert inf["exit"] == 1


def test_t10fix2_167_una_capacidad_sin_red_detras_de_una_lenta_sale(monkeypatch):
    """#167: una capacidad sin red detras de una lenta (que ya gasto el presupuesto) pinta su fila."""
    import time as time_mod
    caps = [{"id": "lenta", "enabled": True, "health": {"estado": "declarado"}, "doctor": "lenta"},
            {"id": "local", "enabled": True, "health": {"estado": "ok"}, "doctor": "local: 3 casos"}]
    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _cap_mod_lento(caps, 0.0))
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (object(), "d"))
    monkeypatch.setattr(doctor, "_leer_backend_entry",
                        lambda project, cap, backend_id=None: {"type": "t"} if cap["id"] == "lenta" else {})
    monkeypatch.setattr(doctor, "CAPACIDADES_PRESUPUESTO_S", 0.5)

    def backend(cap_id, tipo, *a, **k):
        if not tipo:
            return None
        time_mod.sleep(0.5)
        return doctor.linea(doctor.INFO, f"{cap_id} (backend)", "timeout")
    monkeypatch.setattr(doctor, "_linea_capacidad_backend", backend)
    bloque = doctor.bloque_capacidades("plugin", "project", verbose=True)
    nombres = [l["que"] for l in bloque["lineas"]]
    assert "local" in nombres and "lenta (backend)" in nombres, nombres
    assert not any("recortada" in l["detalle"] for l in bloque["lineas"]), bloque


def test_t10fix2_m7_requiere_red_es_la_misma_condicion_de_linea_capacidad():
    """M7: `_requiere_red` = activa, sin `health` en `error`, con backend declarado (`type`) y con el
    cargador de backends disponible (`backends_mod is not None`)."""
    assert doctor._requiere_red(_cap(), {"type": "t"}, object()) is True
    assert doctor._requiere_red(_cap(), {"type": "t"}, None) is False
    assert doctor._requiere_red(_cap(), {}, object()) is False
    assert doctor._requiere_red(_cap(enabled=False), {"type": "t"}, object()) is False
    assert doctor._requiere_red(_cap(health={"estado": "error"}), {"type": "t"}, object()) is False
    assert doctor._requiere_red(_cap(), doctor._EntradaInvalida("x"), object()) is False


def test_t10fix2_m7_la_entrada_del_backend_se_lee_una_vez_por_capacidad(monkeypatch):
    """M7 (D3-6): `bloque_capacidades` lee la entrada del backend UNA vez por capacidad y la pasa a
    `_requiere_red` y a `_linea_capacidad`."""
    caps = [{"id": f"c{i}", "enabled": True, "health": {"estado": "declarado"}, "doctor": f"c{i}"} for i in range(3)]
    monkeypatch.setattr(doctor, "_cargar_capabilities", lambda plugin_root: _cap_mod_lento(caps, 0.0))
    monkeypatch.setattr(doctor, "_cargar_backends_loader", lambda plugin_root: (object(), "d"))
    leidas = []

    def leer(project, cap, backend_id=None):
        leidas.append(cap["id"])
        return {}
    monkeypatch.setattr(doctor, "_leer_backend_entry", leer)
    doctor.bloque_capacidades("plugin", "project", verbose=True)
    assert leidas == ["c0", "c1", "c2"], leidas


@pytest.mark.parametrize("datos", [{"backends": []}, {"backends": {"midbackend": 1}}, {"backends": "x"},
                                   {"backends": {"midbackend": [1]}}])
def test_t10fix2_179_backends_que_no_son_objetos_es_error_de_config(tmp_path, datos):
    """#179: `backends` o `backends.<id>` de la config que no son objetos -> error de configuracion de
    ESA capacidad (fichero y campo, sin traceback): `/doctor` sale con exit 1."""
    d = tmp_path / ".claude" / "knowledge-services"
    d.mkdir(parents=True)
    (d / "taxonomy.json").write_text(json.dumps(datos), encoding="utf-8")
    cap = _cap(id_="midbackend", config_path=os.path.join(".claude", "knowledge-services", "taxonomy.json"))
    entrada = doctor._leer_backend_entry(str(tmp_path), cap)
    assert isinstance(entrada, doctor._EntradaInvalida), entrada
    l = doctor._linea_capacidad(str(tmp_path), cap, backends_real, FIXTURES_BACKENDS)
    assert l["estado"] == doctor.ERROR and "taxonomy.json" in l["detalle"] and "backends" in l["detalle"], l
    assert "corrige" in l["arreglo"]
    assert doctor._leer_backend_entry(str(tmp_path), _cap(id_="midbackend")) == {}


# ------------------------------------------------------------------ T-10/T-11 fix3 (#185): EN PROCESO
# Las lineas que en el checkout principal solo cubria su `.claude/` local sin versionar (modelos de
# `dev.json`, `find` de `localizar_plugin`, errores de uso de `main`), con `tmp_path` y configs
# sinteticas: nunca el `.claude/` del checkout.

def test_t10fix3_185_modelos_sin_objeto_sin_script_y_sin_json(tmp_path, monkeypatch):
    """#185: `_modelos` con `modelos` que no es un objeto (❌), sin `model-tier.py` (ℹ️), con una salida
    que no es JSON (⚠️) y con JSON (avisos -> ⚠️; sin avisos -> ✅ con los aplicados)."""
    assert doctor._modelos({}, None, str(tmp_path)) == []
    assert doctor._modelos_localizar_script(str(tmp_path)) == os.path.join(doctor.HERE, "model-tier.py")
    [l] = doctor._modelos({"modelos": ["x"]}, None, str(tmp_path))
    assert l["estado"] == doctor.ERROR and "no es un objeto" in l["detalle"]
    monkeypatch.setattr(doctor, "_modelos_localizar_script", lambda _p: None)
    [l] = doctor._modelos({"modelos": {"implementer": {"model": "opus"}}}, None, str(tmp_path))
    assert l["estado"] == doctor.INFO and "no está para resolverlos" in l["detalle"]
    monkeypatch.setattr(doctor, "_modelos_localizar_script", lambda _p: "model-tier.py")
    monkeypatch.setattr(doctor, "_correr", lambda cmd, cwd=None: ("no es json", False))
    [l] = doctor._modelos({"modelos": {"implementer": {"model": "opus"}}}, str(tmp_path), str(tmp_path))
    assert l["estado"] == doctor.AVISO and "no devolvió JSON" in l["detalle"]
    salida = json.dumps({"avisos": [], "agentes": [{"agente": "implementer", "fuente": {"model": "dev.json"}},
                                                   {"agente": "qa", "fuente": {"model": "frontmatter"}}]})
    monkeypatch.setattr(doctor, "_correr", lambda cmd, cwd=None: (salida, True))
    [l] = doctor._modelos({"modelos": {"implementer": {"model": "opus"}}}, None, str(tmp_path))
    assert l["estado"] == doctor.OK and "aplicados: implementer" in l["detalle"], l
    ls = doctor._modelos_lineas_de_json({"avisos": ["modelo raro"]}, {"x": {}})
    assert [x["estado"] for x in ls] == [doctor.AVISO] and "modelo raro" in ls[0]["detalle"]


def test_t10fix3_185_localizar_plugin_por_find_en_el_claude_del_proyecto(tmp_path, monkeypatch):
    """#185: `localizar_plugin` sin `--plugin-root` ni `CLAUDE_PLUGIN_ROOT` y fuera del plugin busca con
    `find` bajo `$PWD/.claude` (y `$HOME/.claude`); un candidato que no es plugin se descarta."""
    plugin = tmp_path / "proj" / ".claude" / "plugins" / "ca"
    (plugin / "agents").mkdir(parents=True)
    (plugin / "agent-kits" / "shared").mkdir(parents=True)
    monkeypatch.chdir(str(tmp_path / "proj"))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.setattr(doctor, "HERE", str(tmp_path / "fuera" / "agent-kits" / "shared"))
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path / "home") if p == "~" else p)
    salida = f"{tmp_path / 'no-plugin' / 'agent-kits' / 'shared'}\n{plugin / 'agent-kits' / 'shared'}\n"
    monkeypatch.setattr(doctor, "_correr", lambda cmd, cwd=None: (salida, True))
    assert os.path.normcase(doctor.localizar_plugin()) == os.path.normcase(str(plugin))
    monkeypatch.setattr(doctor, "_correr", lambda cmd, cwd=None: ("", True))
    assert doctor.localizar_plugin() is None
    assert doctor.localizar_plugin(str(tmp_path / "no-plugin")) is None


def test_t10fix3_185_main_errores_de_uso(tmp_path, capsys):
    """#185: `main` con `--hoy` que no es una fecha, `--root` que no es un directorio y `--plugin-root`
    que no es un directorio -> exit 2 con el motivo en stderr, sin diagnosticar nada."""
    assert doctor.main(["--root", str(tmp_path), "--hoy", "ayer"]) == 2
    assert "no es una fecha" in capsys.readouterr().err
    assert doctor.main(["--root", str(tmp_path / "no-existe")]) == 2
    assert "no es un directorio" in capsys.readouterr().err
    assert doctor.main(["--root", str(tmp_path), "--plugin-root", str(tmp_path / "no-existe")]) == 2
    assert "--plugin-root" in capsys.readouterr().err


# ------------------------------------------------------------------ graphiti-memory T-08 (CA-14)

def test_doctor_no_nombra_la_capacidad_graphiti():
    """CA-14: una capacidad opcional entra por `capabilities.py`; `/doctor` la recorre sin codigo
    propio — este fichero no puede mencionarla."""
    with open(os.path.join(HERE, "doctor.py"), encoding="utf-8") as f:
        assert "graphiti" not in f.read().lower()


def test_doctor_pinta_una_capacidad_nueva_sin_tocar_doctor_py(tmp_path):
    """La prueba de que el registro basta: una capacidad inventada al vuelo sale en el bloque."""
    cap = {"id": "capacidad-inventada", "config_path": None, "enabled": True,
           "health": {"estado": "shadow", "detalle": "escribe pero no lee",
                      "remedio": "pon `mode: read` cuando quieras leer"},
           "doctor": "capacidad-inventada: shadow (escribe, no lee)", "setup_step": "-"}
    l = doctor._linea_capacidad(str(tmp_path), cap, None, None)
    assert "capacidad-inventada" in json.dumps(l, ensure_ascii=False)


def test_f3fix1_gap99_la_fila_de_backend_usa_el_id_que_declara_la_capacidad(tmp_path):
    """Gap #99: `/doctor` leia `backends.<cap_id>` de `taxonomy.json` (la clave literal de la
    capacidad), asi que con el backend declarado con OTRA clave no habia fila `(backend)` ni
    comprobacion en vivo. Ahora usa el `backend` que devuelve la propia capacidad."""
    destino = tmp_path / ".claude" / "knowledge-services"
    destino.mkdir(parents=True)
    (destino / "taxonomy.json").write_text(json.dumps({"backends": {
        "mi_backend": {"type": "test", "enabled": True, "config": {"estado_salud": "sano"}}}}),
        encoding="utf-8")
    cap = {"id": "capacidad-x", "config_path": os.path.join(".claude", "knowledge-services",
                                                            "taxonomy.json"),
           "enabled": True, "health": {"estado": "read", "backend": "mi_backend"},
           "doctor": "capacidad-x: activa", "setup_step": "-"}
    l = doctor._linea_capacidad(str(tmp_path), cap, backends_real, FIXTURES_BACKENDS)
    texto = json.dumps(l, ensure_ascii=False)
    assert "(backend)" in texto and "sano" in texto


def test_f3fix1_gap99_una_fila_por_backend_habilitado(tmp_path):
    destino = tmp_path / ".claude" / "knowledge-services"
    destino.mkdir(parents=True)
    (destino / "taxonomy.json").write_text(json.dumps({"backends": {
        "uno": {"type": "test", "enabled": True, "config": {"estado_salud": "sano"}},
        "dos": {"type": "test", "enabled": True, "config": {"estado_salud": "sano"}}}}),
        encoding="utf-8")
    cap = {"id": "capacidad-x", "config_path": os.path.join(".claude", "knowledge-services",
                                                            "taxonomy.json"),
           "enabled": True, "health": {"estado": "read", "backends": ["uno", "dos"]},
           "doctor": "capacidad-x: activa", "setup_step": "-"}
    ls = doctor._linea_capacidad(str(tmp_path), cap, backends_real, FIXTURES_BACKENDS)
    assert isinstance(ls, list) and len(ls) == 2
    texto = json.dumps(ls, ensure_ascii=False)
    assert "uno" in texto and "dos" in texto


# ------------------------------------------------------------------ fix2 Fase 3 (#119, #122)

def test_f3fix2_gap119_el_presupuesto_se_reevalua_dentro_del_bucle_por_backend(monkeypatch):
    """Gap #119: el bucle por backend de #99 hacia `health()`+`verify()` de red por CADA backend
    declarado, pero el presupuesto del bloque solo se miraba una vez por CAPACIDAD -> N x coste
    sin aviso (medido con blackhole TCP: 1 backend 3,14s, 2 -> 6,19s, 3 -> 9,24s)."""
    import time as time_mod
    destino = None
    cap = {"id": "capacidad-x", "config_path": None, "enabled": True,
           "health": {"estado": "read", "backends": ["uno", "dos", "tres"]},
           "doctor": "capacidad-x: activa", "setup_step": "-"}
    comprobados = []

    def _backend_lento(cap_id, tipo, cfg, backends_mod, backends_dir, project=None, tope_ms=None):
        comprobados.append(cap_id)
        time_mod.sleep(0.05)
        return doctor.linea(doctor.OK, f"{cap_id} (backend)", "sano, sin desfase")

    monkeypatch.setattr(doctor, "_linea_capacidad_backend", _backend_lento)
    monkeypatch.setattr(doctor, "_leer_backend_entry", lambda p, c, b=None: {"type": "test", "config": {}})
    deadline = time_mod.monotonic() + 0.06
    ls = doctor._linea_capacidad("proj", cap, object(), "d", deadline=deadline)
    assert isinstance(ls, list)
    assert len(comprobados) < 3, comprobados
    texto = json.dumps(ls, ensure_ascii=False)
    assert "presupuesto" in texto, texto


def test_f3fix2_gap119_el_tope_de_timeout_alcanza_al_timeout_ms_de_nivel_superior():
    """`_cfg_con_timeout_topado` recortaba SOLO `health.timeout_ms`; el `timeout_ms` de nivel
    superior (el que usan `initialize`/`get_status` del adaptador) se colaba entero."""
    cfg = doctor._cfg_con_timeout_topado({"timeout_ms": 30000, "health": {"timeout_ms": 30000}})
    assert cfg["timeout_ms"] <= doctor.CAPACIDAD_TIMEOUT_MS_TOPE, cfg
    assert cfg["health"]["timeout_ms"] <= doctor.CAPACIDAD_TIMEOUT_MS_TOPE, cfg


def test_f3fix2_gap119_la_ventana_de_lectura_se_acota_para_el_diagnostico():
    """`/doctor` es un diagnostico, no una verificacion exhaustiva: la ventana de lectura que el
    adaptador use en `verify()` se recorta (15 MiB por backend en el escenario de referencia)."""
    cfg = doctor._cfg_con_timeout_topado({"max_episodes": 5000})
    assert cfg["max_episodes"] <= doctor.CAPACIDAD_VENTANA_TOPE, cfg
    cfg_sin = doctor._cfg_con_timeout_topado({})
    assert cfg_sin["max_episodes"] <= doctor.CAPACIDAD_VENTANA_TOPE, cfg_sin


def test_f3fix2_gap122_la_etiqueta_multi_backend_sanea_la_clave(monkeypatch):
    """Gap #107 reabierto por el camino NUEVO de #99: con UN backend la etiqueta es `cap["id"]`
    (saneado en origen), pero con VARIOS se interpola la clave CRUDA del backend."""
    hostil = "aaa\x1b[31m‮EVIL"
    cap = {"id": "capacidad-x", "config_path": None, "enabled": True,
           "health": {"estado": "read", "backends": [hostil, "otro"]},
           "doctor": "capacidad-x: activa", "setup_step": "-"}
    monkeypatch.setattr(doctor, "_leer_backend_entry", lambda p, c, b=None: {"type": "test", "config": {}})
    monkeypatch.setattr(doctor, "_linea_capacidad_backend",
                        lambda cap_id, *a, **k: doctor.linea(doctor.OK, f"{cap_id} (backend)", "sano"))
    ls = doctor._linea_capacidad("proj", cap, object(), "d")
    texto = json.dumps(ls, ensure_ascii=False)
    assert "\\u001b" not in texto and "\x1b" not in texto, texto
    assert "\\u202e" not in texto and "‮" not in texto, texto


# ------------------------------------------------------------------ fix3 Fase 3 (#133, #137)

def _cap_backend(tmp_path, cfg_backend):
    destino = tmp_path / ".claude" / "knowledge-services"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "taxonomy.json").write_text(json.dumps({"backends": {
        "mi_backend": {"type": "test", "enabled": True, "config": cfg_backend}}}), encoding="utf-8")
    return {"id": "capacidad-x",
            "config_path": os.path.join(".claude", "knowledge-services", "taxonomy.json"),
            "enabled": True, "health": {"estado": "read", "backend": "mi_backend"},
            "doctor": "capacidad-x: activa", "setup_step": "-"}


def test_f3fix3_gap133_la_verificacion_incompleta_es_un_aviso_con_el_conteo(tmp_path):
    """Gap #133: `/doctor` leia `verify().ok` y pintaba «OK — sano, sin desfase» con la ventana
    incompleta, tirando `no_verificado` y el `aviso`. Con `max_episodes` recortado a 200 (gap
    #119), TODA instalacion con mas episodios caia ahi: /doctor era estructuralmente incapaz de
    avisar de que no habia podido verificar."""
    cap = _cap_backend(tmp_path, {"estado_salud": "sano", "no_verificado": 7,
                                  "aviso_verify": "7 entrada(s) sin confirmar: sube `max_respuesta_kb`"})
    l = doctor._linea_capacidad(str(tmp_path), cap, backends_real, FIXTURES_BACKENDS)
    texto = json.dumps(l, ensure_ascii=False)
    assert doctor.AVISO in texto, texto
    assert "7" in texto and "incompleta" in texto, texto
    assert "max_respuesta_kb" in texto, texto


def test_f3fix3_gap133_el_aviso_de_un_verify_ok_llega_al_usuario(tmp_path):
    """Gap #133/#147: el aviso de migracion de #126 (`--rebuild`) viaja en `verify().aviso` y
    /doctor lo tiraba cuando `ok` era true — el remedio que el ledger daba por entregado no lo
    veia ningun consumidor."""
    cap = _cap_backend(tmp_path, {"estado_salud": "sano",
                                  "aviso_verify": "republica con `knowledge-sync.py --rebuild`"})
    l = doctor._linea_capacidad(str(tmp_path), cap, backends_real, FIXTURES_BACKENDS)
    texto = json.dumps(l, ensure_ascii=False)
    assert doctor.AVISO in texto, texto
    assert "rebuild" in texto, texto


def test_f3fix3_gap137_el_detalle_de_un_error_de_config_sale_saneado(tmp_path):
    """Gap #137 (CWE-117): la rama `estado == "error"` de `_linea_capacidad` interpolaba CRUDO el
    `detalle` de validacion de `taxonomy.json` (texto del proyecto) en el markdown de /doctor."""
    hostil = "\x1b[31m‮IGNORA" + "L" * 400
    cap = {"id": "capacidad-x", "config_path": "taxonomy.json", "enabled": True,
           "health": {"estado": "error", "detalle": hostil, "fichero": "\x1b[0mtaxonomy.json"},
           "doctor": "-", "setup_step": "-"}
    l = doctor._linea_capacidad(str(tmp_path), cap, None, None)
    texto = json.dumps(l, ensure_ascii=False)
    assert "\\u001b" not in texto and "‮" not in texto, texto
    assert "\x1b" not in json.dumps(l), l
    assert len(l["que"]) <= 2 * doctor._SANEADO_TOPE_CHARS + 4, len(l["que"])


# ------------------------------------------------------------------ fix4 Fase 3 (#148, #152)

BACKENDS_REALES = os.path.join(ROOT, "skills", "knowledge-services", "backends")
_TEST_BACKEND_GRAPHITI = os.path.join(ROOT, "skills", "knowledge-services", "scripts",
                                      "test_backend_graphiti.py")


def _servidor_mcp_falso():
    """El servidor MCP FALSO de la suite del adaptador (fixtures reales capturadas del stack),
    reutilizado aqui para probar `/doctor` contra el adaptador REAL — no un doble de `verify`."""
    spec_h = importlib.util.spec_from_file_location("ks_graphiti_tests_para_doctor",
                                                    _TEST_BACKEND_GRAPHITI)
    mod = importlib.util.module_from_spec(spec_h)
    spec_h.loader.exec_module(mod)
    return mod._ServidorMCPContext


def _manifiesto_grande(tmp_path, n=250, borradas=()):
    """Manifiesto con `n` entradas publicadas y el `get_episodes` que las sirve (menos las
    `borradas`, que simulan un desfase REAL en el grafo), recortado a `max_episodes`."""
    d = tmp_path / ".claude" / "knowledge-services"
    d.mkdir(parents=True, exist_ok=True)
    entradas = {f"mem.pattern.x{i:03d}": {"version": 1, "hash": "h"} for i in range(n)}
    (d / "graphiti-manifest.json").write_text(
        json.dumps({"group_id": "proy-test", "entradas": entradas}), encoding="utf-8")
    vivos = [f"{id_}@1" for id_ in sorted(entradas) if id_ not in borradas]

    def _get_episodes(args):
        tope = int((args or {}).get("max_episodes") or 0)
        return {"structuredContent": {"episodes": [
            {"name": nombre, "group_id": "proy-test", "uuid": nombre} for nombre in vivos[:tope]]}}

    return _get_episodes


def _linea_graphiti(tmp_path, get_episodes):
    ctx = _servidor_mcp_falso()
    with ctx(respuestas_tools={"get_episodes": get_episodes}) as srv:
        return doctor._linea_capacidad_backend(
            "kb", "graphiti",
            {"endpoint": srv.endpoint, "group_id": "proy-test", "mode": "read",
             "timeout_ms": 5000, "max_episodes": 50000},
            backends_real, BACKENDS_REALES, project=str(tmp_path))


def test_f3fix4_gap148_grafo_sano_mas_grande_que_la_ventana_de_doctor_no_es_aviso(tmp_path):
    """Gap #148 (Important): con el recorte de ventana de /doctor (`CAPACIDAD_VENTANA_TOPE`, gap
    #119) TODA instalacion con mas entradas que la ventana caia en la rama `incompleto` de #133 y
    salia ⚠️ «verificacion incompleta» con un remedio (`max_respuesta_kb`/`max_episodes`) que el
    propio /doctor pisa. Un grafo SANO no puede dar ⚠️ por el recorte del diagnostico."""
    linea = _linea_graphiti(tmp_path, _manifiesto_grande(tmp_path, 250))
    texto = json.dumps(linea, ensure_ascii=False)
    assert linea["estado"] in (doctor.OK, doctor.INFO), texto
    assert "200" in texto and "250" in texto, texto
    assert "--check" in texto, texto
    assert "max_respuesta_kb" not in texto and "max_episodes" not in texto, texto


def test_f3fix4_gap148_la_linea_acotada_dice_que_no_ve_desfases_fuera_de_la_ventana(tmp_path):
    """Gap #148: con la ventana recortada, un desfase REAL fuera de ella es indistinguible de lo
    sano — la fila lo DICE (y manda a la verificacion completa) en vez de prometer lo que no
    puede ver. 250 entradas, una borrada del grafo: mismo veredicto acotado, honesto."""
    linea = _linea_graphiti(tmp_path, _manifiesto_grande(tmp_path, 250, borradas={"mem.pattern.x000"}))
    texto = json.dumps(linea, ensure_ascii=False)
    assert linea["estado"] in (doctor.OK, doctor.INFO), texto
    assert "desfase" in texto.lower(), texto
    assert "--check" in texto, texto


def test_f3fix4_gap148_el_detalle_no_repite_el_conteo_de_sin_confirmar(tmp_path):
    """Gap #148: el `detalle` interpolaba su propio conteo Y el `aviso` del adaptador, que lo
    repite («N entrada(s) sin confirmar · N entrada(s) sin confirmar: la ventana…»)."""
    cap = _cap_backend(tmp_path, {"estado_salud": "sano", "no_verificado": 7, "total": 7,
                                  "aviso_verify": "7 entrada(s) sin confirmar: sube `max_respuesta_kb`"})
    linea = doctor._linea_capacidad(str(tmp_path), cap, backends_real, FIXTURES_BACKENDS)
    assert linea["estado"] == doctor.AVISO, linea
    assert linea["detalle"].count("sin confirmar") == 1, linea["detalle"]


def test_f3fix4_gap148_incompleto_dentro_de_la_ventana_de_doctor_sigue_siendo_aviso(tmp_path):
    """Gap #148 no puede tapar #133: si el manifiesto CABIA en la ventana de /doctor y aun asi la
    verificacion sale incompleta, el limite es del backend (su tope de lectura) y eso SI es ⚠️."""
    cap = _cap_backend(tmp_path, {"estado_salud": "sano", "no_verificado": 3, "total": 10,
                                  "aviso_verify": "3 entrada(s) sin confirmar: tope de lectura"})
    linea = doctor._linea_capacidad(str(tmp_path), cap, backends_real, FIXTURES_BACKENDS)
    assert linea["estado"] == doctor.AVISO, linea
    assert "incompleta" in linea["detalle"], linea


def test_f3fix4_gap152_verify_no_verificable_es_informativo_con_su_razon(tmp_path):
    """Gap #152: `verify()` tiene CUATRO veredictos (`ok`/`desfase`/`incompleto`/`no_verificable`)
    y /doctor no leia el cuarto: `mode: off` o un endpoint ausente caian en la rama de desfase y
    se pintaban como «export atrasado (0 desfase(s)): sin motivo detallado»."""
    cap = _cap_backend(tmp_path, {"estado_salud": "sano", "no_verificable": "mode: off"})
    linea = doctor._linea_capacidad(str(tmp_path), cap, backends_real, FIXTURES_BACKENDS)
    assert linea["estado"] == doctor.INFO, linea
    assert "mode: off" in linea["detalle"], linea
    assert "export atrasado" not in linea["detalle"], linea


# ------------------------------------------------------------------ acciones prioritarias: contrato de presentación

def _diagnostico_con_filas(monkeypatch, bloques):
    """Informe real con comprobaciones propias en memoria: no lee configuración del host."""
    monkeypatch.setattr(doctor, "localizar_plugin", lambda explicit=None: None)
    nombres = ("bloque_herramientas", "bloque_plugin", "bloque_configs", "bloque_estado",
               "bloque_capacidades", "bloque_memoria", "bloque_journal", "bloque_version")
    for i, nombre in enumerate(nombres):
        bloque = bloques[i] if i < len(bloques) else {
            "clave": f"vacio-{i}", "titulo": "Vacío", "lineas": []}
        monkeypatch.setattr(doctor, nombre, lambda *args, _b=bloque, **kwargs: _b)
    return doctor.diagnostico(".")


def test_prioridades_errores_antes_de_avisos_empates_estables_y_limite(monkeypatch):
    bloques = [
        {"clave": "herramientas", "titulo": "Herramientas", "lineas": [
            doctor.linea(doctor.AVISO, "aviso inicial", "aviso", "arreglo común"),
            doctor.linea(doctor.INFO, "opcional", "información", "opcional"),
            doctor.linea(doctor.ERROR, "primer error", "roto uno", "arreglo común")]},
        {"clave": "plugin", "titulo": "Plugin", "lineas": [
            doctor.linea(doctor.ERROR, "segundo error", "roto dos", "reinstala"),
            doctor.linea(doctor.AVISO, "aviso posterior", "aviso dos", "revisa")]},
    ]
    antes = json.dumps(bloques, ensure_ascii=False)
    inf = _diagnostico_con_filas(monkeypatch, bloques)
    prioridades = inf["acciones_prioritarias"]
    assert prioridades["total"] == 4 and prioridades["limite"] == 3
    assert [(a["bloque"], a["linea"], a["que"]) for a in prioridades["acciones"]] == [
        ("herramientas", 3, "primer error"), ("plugin", 1, "segundo error"),
        ("herramientas", 1, "aviso inicial")]
    assert [a["arreglo"] for a in prioridades["acciones"]] == [
        "arreglo común", "reinstala", "arreglo común"]
    assert all(set(a) == {"bloque", "linea", "estado", "que", "detalle", "arreglo"}
               for a in prioridades["acciones"])
    assert json.dumps(bloques, ensure_ascii=False) == antes
    assert all(set(l) == {"estado", "que", "detalle", "arreglo"} for l in lineas(inf))
    assert inf["resumen"] == {"ok": 0, "aviso": 2, "error": 2, "info": 1}
    assert inf["exit"] == 1


@pytest.mark.parametrize("filas,total,exit_code", [
    ([], 0, 0),
    ([doctor.linea(doctor.INFO, "opcional", "no configurado", "activa si quieres")], 0, 0),
    ([doctor.linea(doctor.OK, "declarado", "sin prueba de ejecución", "comprueba")], 0, 0),
    ([doctor.linea(doctor.ERROR, "sin arreglo", "roto", "")], 0, 1),
    ([doctor.linea(doctor.AVISO, "sin arreglo", "degradado", " \t\r\n")], 0, 0),
    ([doctor.linea(doctor.AVISO, "con arreglo", "degradado", "  revisa  ")], 1, 0),
])
def test_prioridades_vacias_y_sin_remedio_no_cambian_exit(monkeypatch, filas, total, exit_code):
    inf = _diagnostico_con_filas(monkeypatch, [
        {"clave": "plugin", "titulo": "Plugin", "lineas": filas}])
    assert inf["acciones_prioritarias"]["total"] == total
    assert len(inf["acciones_prioritarias"]["acciones"]) == total
    if total:
        assert inf["acciones_prioritarias"]["acciones"][0]["arreglo"] == "  revisa  "
    assert inf["exit"] == exit_code


def test_prioridades_markdown_y_json_comparten_seleccion_y_texto_hostil(monkeypatch):
    filas = [doctor.linea(doctor.AVISO, f"aviso-{i}", "detalle", f"remedio-{i}")
             for i in range(4)]
    filas.append(doctor.linea(doctor.ERROR, "error|propio\nnombre", "detalle|A\nB", "  arregla|C\nD  "))
    inf = _diagnostico_con_filas(monkeypatch, [{"clave": "plugin", "titulo": "Plugin", "lineas": filas}])
    js = json.loads(json.dumps(inf, ensure_ascii=False))
    acciones = js["acciones_prioritarias"]["acciones"]
    assert [a["linea"] for a in acciones] == [5, 1, 2]
    assert acciones[0]["arreglo"] == "  arregla|C\nD  "
    md = doctor.render_md(inf)
    resumen = md.split("## Acciones prioritarias", 1)[1].split("\n## ", 1)[0]
    assert "3 de 5" in resumen
    assert "error\\|propio nombre" in resumen
    assert "detalle\\|A B" in resumen and "arregla\\|C D" in resumen
    assert "remedio-0" in resumen and "remedio-1" in resumen
    assert "remedio-2" not in resumen and "remedio-3" not in resumen
    assert veredictos_md(md) == [l["estado"] for l in lineas(js)]


def test_prioridades_no_afirma_salud_global_con_comprobaciones_vacias(monkeypatch):
    inf = _diagnostico_con_filas(monkeypatch, [])
    md = doctor.render_md(inf)
    assert "Instalación sana" not in md and "Nada roto" not in md
    assert "comprobaciones realizadas" in md
    assert "0 de 0" in md


def test_prioridades_markdown_muestra_arreglos_antes_de_tablas(monkeypatch):
    inf = _diagnostico_con_filas(monkeypatch, [{"clave": "plugin", "titulo": "Plugin", "lineas": [
        doctor.linea(doctor.ERROR, "configuración rota", "config ilegible", "corrige configuración")]}])
    md = doctor.render_md(inf)
    assert md.index("**Proyecto**") < md.index("## Acciones prioritarias")
    assert md.index("## Acciones prioritarias") < md.index("## Plugin")
    assert md.count("## Acciones prioritarias") == 1


def test_prioridades_cli_json_md_sin_escrituras_ni_remedios(tmp_path):
    proj = proyecto(tmp_path, dev__json={"tdd": "sí", "tddd": True},
                    rates__json={"precioTokens": {"input": 0, "output": 0}})
    antes = snapshot(proj)
    cfg = os.environ["CLAUDE_CONFIG_DIR"]
    home = os.environ["HOME"]
    antes_cfg, antes_home = snapshot(cfg), snapshot(home)
    js = run("--root", str(proj), "--json")
    md = run("--root", str(proj))
    assert js.returncode == md.returncode == 1
    inf = json.loads(js.stdout)
    assert inf["acciones_prioritarias"]["total"] >= 3
    seleccion = md.stdout.split("## Acciones prioritarias", 1)[1].split("\n## ", 1)[0]
    for accion in inf["acciones_prioritarias"]["acciones"]:
        assert doctor._celda(accion["que"]) in seleccion
        assert doctor._celda(accion["arreglo"]) in seleccion
    assert snapshot(proj) == antes
    assert snapshot(cfg) == antes_cfg and snapshot(home) == antes_home
