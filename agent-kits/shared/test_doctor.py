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
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(HERE, "doctor.py")

spec = importlib.util.spec_from_file_location("doctor", SCRIPT)
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)

ICONOS = {v: k for k, v in doctor.ICONO.items()}


# ------------------------------------------------------------------ utilidades

def run(*args, root=None):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}
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

# ------------------------------------------------------------------ tests

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


def test_repo_real_usa_el_criterio_del_linter_para_los_hooks():
    """Con el plugin real (que sí trae `scripts/lint_plugin.py`) el veredicto de hooks se delega
    en `lint_hook_commands` — una sola definición de «hook roto» en el repo."""
    inf = diag(ROOT, ROOT)
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


@pytest.mark.parametrize("bloque", ["herramientas", "plugin", "configs", "estado", "memoria", "version"])
def test_los_seis_bloques_estan_siempre(tmp_path, bloque):
    inf = diag(proyecto(tmp_path))
    claves = [b["clave"] for b in inf["bloques"]]
    assert bloque in claves and len(claves) == 6
    assert doctor.render_md(inf).count("| | Comprobación |") == 6


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
    assert inf["exit"] == 0 and "Instalación sana" in doctor.render_md(inf)


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


def test_repo_real_la_memoria_ya_no_pasa_en_silencio():
    """Sobre este repo (≥ 31 curadas, journal a 0, CALIBRATION.md > 14 días): no «Instalación sana»."""
    inf = diag(ROOT, ROOT)
    cur = por_que(inf, "memoria curada", doctor.OK)
    assert cur and int(re.search(r"(\d+) entrada", cur[0]["detalle"]).group(1)) >= 31
    assert por_que(inf, "índice de memoria (README)", doctor.OK), "el índice real pasa el lint de T-04"
    ques = {l["que"] for l in lineas(inf, doctor.AVISO)}
    assert "journal de sesión" in ques or "calibración (CALIBRATION.md)" in ques
    assert "Instalación sana" not in doctor.render_md(inf)


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
        {"plugin": ["./.opencode/plugins/custom-agents-hooks.js"]}), encoding="utf-8")
    oc = fila(diag(proj, plug), "registro en OpenCode")
    assert oc["estado"] == doctor.OK and "custom-agents-hooks.js" in oc["detalle"]

    # copiado pero sin alta: ⚠️ con el comando que lo arregla
    (proj / "opencode.json").write_text(json.dumps({"plugin": ["otro.js"]}), encoding="utf-8")
    (proj / ".opencode" / "plugins").mkdir(parents=True)
    (proj / ".opencode" / "plugins" / "custom-agents-hooks.js").write_text("//", encoding="utf-8")
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
    """Casar por basename daba OK a cualquier `custom-agents-hooks.js` de cualquier sitio, y
    `status` (ruta exacta) decia lo contrario sobre el MISMO `opencode.json`."""
    _cfg_vacio(tmp_path, monkeypatch)
    proj = proyecto(tmp_path)
    plug = plugin(tmp_path)
    (proj / ".opencode" / "plugins").mkdir(parents=True)
    (proj / ".opencode" / "plugins" / "custom-agents-hooks.js").write_text("//", encoding="utf-8")

    # mismo nombre, otra carpeta: NO es el adaptador instalado
    (proj / "opencode.json").write_text(json.dumps(
        {"plugin": ["./vendor/custom-agents-hooks.js"]}), encoding="utf-8")
    oc = fila(diag(proj, plug), "registro en OpenCode")
    assert oc["estado"] == doctor.AVISO and "NO es el adaptador instalado" in oc["detalle"]
    assert oc["arreglo"]

    # escalar: `status` no lo cuenta como alta (`json-array`), asi que `/doctor` tampoco
    (proj / "opencode.json").write_text(json.dumps(
        {"plugin": "./.opencode/plugins/custom-agents-hooks.js"}), encoding="utf-8")
    oc = fila(diag(proj, plug), "registro en OpenCode")
    assert oc["estado"] == doctor.AVISO and "no es una lista" in oc["detalle"] and oc["arreglo"]

    # la ruta que escribe el instalador (relativa al fichero de config): OK
    (proj / "opencode.json").write_text(json.dumps(
        {"plugin": ["./.opencode/plugins/custom-agents-hooks.js"]}), encoding="utf-8")
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
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg), NO_COLOR="1", **(env_extra or {}))
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
    (proj / ".opencode" / "plugins").mkdir(parents=True)
    (proj / ".opencode" / "plugins" / "custom-agents-hooks.js").write_text("//", encoding="utf-8")
    spec = {"alta-exacta": ["./.opencode/plugins/custom-agents-hooks.js"],
            "mismo-nombre-otra-ruta": ["./vendor/custom-agents-hooks.js"],
            "escalar": "./.opencode/plugins/custom-agents-hooks.js",
            "sin-plugin": []}[caso]
    (proj / "opencode.json").write_text(json.dumps({"plugin": spec}), encoding="utf-8")

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
