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
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
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


def plugin(tmp_path, *, script_existe=True, ejecutable=True, version="9.9.9"):
    """Plugin temporal mínimo con un hook registrado (sin `scripts/lint_plugin.py`: fuerza la
    comprobación LOCAL equivalente del doctor)."""
    plug = tmp_path / "plug"
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


@pytest.mark.parametrize("bloque", ["herramientas", "plugin", "configs", "estado", "version"])
def test_los_cinco_bloques_estan_siempre(tmp_path, bloque):
    inf = diag(proyecto(tmp_path))
    claves = [b["clave"] for b in inf["bloques"]]
    assert bloque in claves and len(claves) == 5
    assert doctor.render_md(inf).count("| | Comprobación |") == 5
