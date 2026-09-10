#!/usr/bin/env python3
"""Tests de code-health.py (memory-health T-02). Ejecutar: python3 -m pytest -q skills/code-health/scripts

Fixture multi-lenguaje generada en tmp (py + js + php): un bloque duplicado py↔py, una función larga,
un TODO viejo (con git real si está en PATH), tests que `--exclude-tests` saca, `vendor/` siempre fuera.
Se afirma cada una de las 4 medidas, la equivalencia MD/JSON, `--baseline`, la degradación sin git y
los exit codes (0 informe · 2 uso)."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "code-health.py")
GIT = shutil.which("git")

spec = importlib.util.spec_from_file_location("code_health", SCRIPT)
ch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ch)

BLOQUE_PY = "\n".join([
    "def calcular_total(items):",
    "    total = 0",
    "    for item in items:",
    "        if item.activo:",
    "            total += item.precio * item.cantidad",
    "        else:",
    "            total -= item.descuento",
    "    if total < 0:",
    "        total = 0",
    "    return round(total, 2)",
])
BLOQUE_PY_RENOMBRADO = BLOQUE_PY.replace("calcular_total", "sumar_carrito").replace("items", "lineas") \
    .replace("total", "acumulado").replace("item", "linea").replace("2)", "3)")


def fixture(tmp_path, con_git=True):
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "vendor" / "lib").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "a.py").write_text(BLOQUE_PY + "\n\n# TODO: revisar redondeo\n", encoding="utf-8")
    (root / "src" / "b.py").write_text("import os\n\n" + BLOQUE_PY_RENOMBRADO + "\n", encoding="utf-8")
    larga = ["function procesar(pedido) {"] + [f"  const v{i} = pedido.items[{i}]; // paso {i}" for i in range(34)] + ["  return pedido;", "}"]
    (root / "src" / "c.js").write_text("\n".join(larga) + "\n\nconst corta = (x) => x + 1;\n// FIXME: quitar\n", encoding="utf-8")
    (root / "src" / "d.php").write_text(
        "<?php\nclass Foo {\n    public function bar($x) {\n        if ($x) {\n            while ($x--) {\n                echo 'hack en minúsculas no cuenta';\n            }\n        }\n        return $x; // XXX temporal\n    }\n}\n", encoding="utf-8")
    (root / "tests" / "test_a.py").write_text(BLOQUE_PY + "\n", encoding="utf-8")
    (root / "vendor" / "lib" / "v.py").write_text(BLOQUE_PY + "\n", encoding="utf-8")
    (root / "README.md").write_text("# no es código\nTODO: no cuenta\n", encoding="utf-8")
    if con_git and GIT:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@x", "GIT_AUTHOR_DATE": "2020-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00Z"}
        subprocess.run([GIT, "-C", str(root), "init", "-q"], check=True, env=env)
        subprocess.run([GIT, "-C", str(root), "add", "-A"], check=True, env=env)
        subprocess.run([GIT, "-C", str(root), "commit", "-q", "-m", "base"], check=True, env=env)
        # segundo commit reciente que toca c.js dos veces → hotspot
        env2 = {k: v for k, v in env.items() if not k.endswith("_DATE")}
        for i in range(2):
            with open(root / "src" / "c.js", "a", encoding="utf-8") as fh:
                fh.write(f"// cambio {i}\n")
            subprocess.run([GIT, "-C", str(root), "commit", "-q", "-am", f"c{i}"], check=True, env=env2)
    return root


def run(*args):
    r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return r.returncode, r.stdout, r.stderr


def analiza(root, **kw):
    langs = set(ch.LANGS_DEFAULT.split(","))
    params = dict(langs=langs, window=8, min_lines=6, exclude_tests=True, since=90, top=10, exclude_paths=())
    params.update(kw)
    return ch.analizar(str(root), params["langs"], params["window"], params["min_lines"],
                       params["exclude_tests"], params["since"], params["top"],
                       exclude_paths=params["exclude_paths"])


# ------------------------------------------------------------------ 1. duplicados

def test_duplicado_py_py_con_identificadores_renombrados(tmp_path):
    r = analiza(fixture(tmp_path, con_git=False))
    d = r["duplicados"]
    assert d["bloques"] == 1 and d["top"][0]["lineas"] == 10
    assert d["top"][0]["a"] == "src/a.py:1" and d["top"][0]["b"] == "src/b.py:3"
    assert d["pct"] > 0 and d["lineas_duplicadas"] == 20


def test_ventana_mayor_que_el_bloque_no_encuentra_duplicados(tmp_path):
    r = analiza(fixture(tmp_path, con_git=False), window=12)
    assert r["duplicados"]["bloques"] == 0 and r["duplicados"]["pct"] == 0.0


def test_normaliza_identificadores_numeros_y_cadenas():
    assert ch.normaliza('total = precio * 3 + "x"') == ch.normaliza("suma = coste * 42 + 'y'")
    assert ch.normaliza("return a") != ch.normaliza("return a + b")


def test_exclude_tests_y_vendor(tmp_path):
    root = fixture(tmp_path, con_git=False)
    con = analiza(root, exclude_tests=False)
    sin = analiza(root, exclude_tests=True)
    ficheros_con = {f["fichero"] for f in con["tamano"]["top_ficheros"]}
    ficheros_sin = {f["fichero"] for f in sin["tamano"]["top_ficheros"]}
    assert "tests/test_a.py" in ficheros_con and "tests/test_a.py" not in ficheros_sin
    assert not any(f.startswith("vendor/") for f in ficheros_con)            # vendor SIEMPRE fuera
    assert con["duplicados"]["bloques"] > sin["duplicados"]["bloques"]         # el test duplica a.py


# ------------------------------------------------------------------ 2. tamaño / complejidad

def test_funcion_larga_detectada_y_corta_no(tmp_path):
    r = analiza(fixture(tmp_path, con_git=False))
    largas = r["tamano"]["top_funciones"]
    assert len(largas) == 1 and largas[0]["fichero"] == "src/c.js:1" and largas[0]["lineas"] == 35
    assert "procesar" in largas[0]["funcion"]
    assert r["tamano"]["umbral_funcion"] == 30
    assert analiza(fixture(tmp_path / "b", con_git=False), min_lines=8)["tamano"]["funciones_largas"] == 0


def test_anidamiento_por_llaves_e_indentacion(tmp_path):
    r = analiza(fixture(tmp_path, con_git=False))
    por = {f["fichero"]: f["anidamiento"] for f in r["tamano"]["top_ficheros"]}
    assert por["src/d.php"] == 4                     # class { function { if { while {
    assert por["src/a.py"] == 3                      # def → for → if
    assert por["src/c.js"] == 1


def test_profundidad_python_ignora_docstrings_y_continuaciones():
    lines = ['def f(x):', '    """Doc:', '      con dos puntos al final:', '    """',
             '    valor = llamada(a,', '                    b)', '    if x:', '        return 1', '    return 0']
    assert ch.profundidad(lines, "py") == 2


# ------------------------------------------------------------------ 3/4. git

@pytest.mark.skipif(GIT is None, reason="sin git")
def test_hotspots_y_antiguedad_de_todo_con_git(tmp_path):
    r = analiza(fixture(tmp_path))
    assert r["avisos"] == [] and r["hotspots"] is not None
    top = r["hotspots"]["top"]
    assert top and top[0]["fichero"] == "src/c.js" and top[0]["cambios"] >= 2 and top[0]["puntuacion"] > 0
    m = r["marcadores"]
    assert m["total"] == 3 and m["por_tipo"] == {"FIXME": 1, "TODO": 1, "XXX": 1}   # README.md (no es código) no cuenta
    tod = next(t for t in m["top"] if t["tipo"] == "TODO")
    assert tod["fichero"] == "src/a.py:12" and tod["edad_dias"] is not None and tod["edad_dias"] > 2000
    assert m["edad_max_dias"] == tod["edad_dias"] and m["antiguedad"] == "git"


def test_sin_git_omite_hotspots_y_avisa(tmp_path):
    r = analiza(fixture(tmp_path, con_git=False))
    assert r["hotspots"] is None and r["resumen"]["hotspots"] is None
    assert any("git" in a for a in r["avisos"])
    assert r["marcadores"]["total"] >= 3 and all(t["edad_dias"] is None for t in r["marcadores"]["top"])
    texto = ch.md(r)
    assert "Omitido: sin git" in texto and "⚠️" in texto


# ------------------------------------------------------------------ CLI / salida

def test_cli_md_y_json_mismo_contenido(tmp_path):
    root = fixture(tmp_path, con_git=False)
    rc, md_out, _ = run(str(root), "--exclude-tests")
    rc2, js_out, _ = run(str(root), "--exclude-tests", "--json")
    assert rc == 0 and rc2 == 0
    j = json.loads(js_out)
    assert md_out.startswith("# Salud del código") and "## 1. Duplicados" in md_out and "## 4. TODO/FIXME" in md_out
    assert f"duplicado **{j['resumen']['duplicado_pct']} %**" in md_out
    assert "`src/a.py:1`" in md_out and "`src/b.py:3`" in md_out
    assert j["parametros"]["exclude_tests"] is True and j["resumen"]["funciones_largas"] == 1


def test_baseline_marca_mejora_y_empeora(tmp_path):
    root = fixture(tmp_path, con_git=False)
    rc, js_out, _ = run(str(root), "--json")
    base = tmp_path / "base.json"
    base.write_text(js_out, encoding="utf-8")
    (root / "src" / "b.py").write_text("x = 1\n", encoding="utf-8")            # desaparece el duplicado
    (root / "src" / "a.py").write_text((root / "src" / "a.py").read_text(encoding="utf-8") + "# TODO: otro\n", encoding="utf-8")
    rc, md_out, _ = run(str(root), "--baseline", str(base))
    assert rc == 0 and "## Comparación con baseline" in md_out
    assert "| % duplicado |" in md_out and "↓ mejora" in md_out and "↑ empeora" in md_out
    rc, js2, _ = run(str(root), "--baseline", str(base), "--json")
    comp = {c["metrica"]: c for c in json.loads(js2)["baseline"]}
    assert comp["bloques duplicados"]["tendencia"] == "↓ mejora" and comp["TODO/FIXME/HACK"]["tendencia"] == "↑ empeora"


def test_exit_2_ruta_inexistente_y_baseline_ilegible(tmp_path):
    rc, _, err = run(str(tmp_path / "no-existe"))
    assert rc == 2 and "no existe" in err
    root = fixture(tmp_path, con_git=False)
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    rc, _, err = run(str(root), "--baseline", str(bad))
    assert rc == 2 and "baseline" in err


def test_langs_filtra_extensiones(tmp_path):
    root = fixture(tmp_path, con_git=False)
    r = analiza(root, langs={"php"})
    assert r["tamano"]["ficheros"] == 1 and r["tamano"]["top_ficheros"][0]["fichero"] == "src/d.php"
    rc, out, _ = run(str(root), "--langs", "php,.PY", "--json")
    assert rc == 0 and json.loads(out)["parametros"]["langs"] == ["php", "py"]


# ------------------------------------------------------------------ TODO_RE — falsos positivos (T-01)

def test_prosa_castellana_todo_con_parentesis_no_cuenta(tmp_path):
    """«TODO (ADRs, arquitectura,…» (confluence-scope.py:113) no es una anotación de código: `(` ya
    NO es un separador válido tras la palabra (solo `:`/`-`/`—`/fin de línea)."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text(
        "x = 1\n# del árbol. Los agentes siguen escribiendo TODO (ADRs, arquitectura,\n", encoding="utf-8")
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 0


def test_linea_que_enumera_marcadores_entre_backticks_no_cuenta(tmp_path):
    """Una línea de documentación que enumera marcadores CITADOS entre backticks (`journal.py:41`:
    «`más tarde`, `TODO:`, `remind me`…») describe un patrón, no es un TODO real (B-2, revisión R1:
    el marcador está DENTRO de un backtick, como un ítem más de la lista)."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text(
        "x = 1\n# léxico (`pendiente`, `TODO:`, `remind me`…), deduplicadas\n", encoding="utf-8")
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 0


def test_todo_seguido_de_referencias_entre_backticks_si_cuenta(tmp_path):
    """B-2 (revisión R1): la regla vieja excluía CUALQUIER línea con 2 backtick-spans separados
    por coma, sin mirar si el propio marcador estaba entre backticks — suprimía anotaciones reales
    como «TODO: unificar `a.py`, `b.py`» (el marcador está FUERA de los backticks: cita ficheros,
    no se enumera a sí mismo). Oráculo de la revisión: 2, no 0."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text(
        "x = 1\n# TODO: unificar `a.py`, `b.py`\n", encoding="utf-8")
    (root / "src" / "b.py").write_text(
        "y = 2\n# FIXME: el parser rompe con `foo`, `bar`\n", encoding="utf-8")
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 2
    assert r["marcadores"]["por_tipo"] == {"FIXME": 1, "TODO": 1}


def test_prosa_castellana_tras_marcador_al_comienzo_no_cuenta(tmp_path):
    """A-1/B-9 (revisión R1): «# TODO el histórico como ventana» es prosa castellana partida en
    dos comentarios (`usage-meter.py:454-455`), no una anotación — la palabra que sigue al
    marcador al comienzo del comentario («el») es un artículo, no un identificador de tarea."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text(
        "x = 1\n"
        "# marcador sin offsets (escrito a mano o de otra versión): medir sería contar\n"
        "# TODO el histórico como ventana → degradar con aviso, no mentir\n",
        encoding="utf-8")
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 0


def test_todo_al_comienzo_sin_separador_pero_sin_prosa_si_cuenta(tmp_path):
    """El mismo hueco al comienzo del comentario, sin separador, SÍ cuenta cuando la palabra
    siguiente no es un artículo/preposición/pronombre castellano (p. ej. «TODO revisar esto»)."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text("x = 1\n# TODO revisar esto\n", encoding="utf-8")
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 1


def test_el_propio_fichero_del_detector_se_excluye_por_ruta_real(tmp_path, monkeypatch):
    """B-6 (revisión R1): la exclusión es por RUTA REAL del script (`os.path.realpath(__file__)`),
    no por basename — así un `code-health.py` de un proyecto consumidor (incluida esta fixture, que
    NO es el script real) SÍ se cuenta; solo la ruta real del detector se excluye."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    fixture_detector = root / "src" / "code-health.py"
    fixture_detector.write_text("x = 1\n# TODO: revisar\n", encoding="utf-8")
    (root / "src" / "otro.py").write_text("y = 2\n# TODO: revisar\n", encoding="utf-8")
    # Sin parchear: el "code-health.py" de la fixture NO es la ruta real del script → SÍ se cuenta
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 2
    assert {t["fichero"] for t in r["marcadores"]["top"]} == {"src/code-health.py:2", "src/otro.py:2"}
    # Con DETECTOR_PROPIO apuntando a la ruta real de la fixture (simula que ES el detector) → excluida
    monkeypatch.setattr(ch, "DETECTOR_PROPIO", ch.os.path.realpath(str(fixture_detector)))
    r2 = analiza(root, exclude_tests=False)
    assert r2["marcadores"]["total"] == 1
    assert r2["marcadores"]["top"][0]["fichero"] == "src/otro.py:2"


def test_mutante_detector_propio_nunca_coincide_sube_el_recuento(tmp_path, monkeypatch):
    """Mutante acotado (B-8): en vez de parchear `os.path.basename` GLOBAL del intérprete (que
    también afectaría al `subprocess` de `git log`), se parchea `ch.DETECTOR_PROPIO` a una ruta
    que nunca coincide — evidencia del rojo: el recuento sube porque el detector deja de excluirse."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    fixture_detector = root / "src" / "code-health.py"
    fixture_detector.write_text("x = 1\n# TODO: revisar\n", encoding="utf-8")
    monkeypatch.setattr(ch, "DETECTOR_PROPIO", ch.os.path.realpath(str(fixture_detector)))
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 0        # excluido: DETECTOR_PROPIO coincide
    monkeypatch.setattr(ch, "DETECTOR_PROPIO", "/nunca/coincide/code-health.py")
    r_mutado = analiza(root, exclude_tests=False)
    assert r_mutado["marcadores"]["total"] == 1  # mutante: sube el recuento (rojo esperado)


def test_copia_real_del_detector_en_otra_ruta_se_excluye_por_firma(tmp_path):
    """R2-1 (residual de B-6): un agente ejecuta el kit desde la caché del plugin mientras este
    repo tiene SU PROPIA copia de `code-health.py` en otra ruta — `realpath(__file__)` NUNCA las
    iguala (son ficheros distintos), así que la copia del árbol solo se excluye por la FIRMA de
    su docstring. Se copia el script REAL (no una fixture a mano) para no divergir si el docstring
    cambia; el módulo `ch` bajo test sigue siendo el que importa pytest (otra ruta real más)."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    shutil.copy(SCRIPT, root / "src" / "code-health.py")
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 0


def test_mutante_firma_detector_no_coincide_sube_el_recuento(tmp_path, monkeypatch):
    """Mutante 'sin firma' (R2-1): si `FIRMA_DETECTOR` deja de coincidir con lo que lleva la copia
    del árbol (p. ej. un typo al tocar el docstring, o el mutante que borra la exclusión), esa
    copia deja de reconocerse como detector y sus propios TODO/FIXME/HACK del docstring y los
    comentarios empiezan a contar — evidencia del rojo (no se afirma un número exacto porque
    depende del contenido real del script, solo que deja de ser 0)."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    shutil.copy(SCRIPT, root / "src" / "code-health.py")
    monkeypatch.setattr(ch, "FIRMA_DETECTOR", "nunca-coincide-firma-xyz")
    r_mutado = analiza(root, exclude_tests=False)
    assert r_mutado["marcadores"]["total"] > 0


# ------------------------------------------------------------------ enumeración de marcadores encadenados (R2-2)

def test_enumeracion_de_marcadores_encadenados_no_cuenta(tmp_path):
    """R2-2 (residual de B-2): «# Busca marcadores TODO/FIXME/HACK en el código» enumera la
    convención léxica (tres palabras-marcador seguidas separadas solo por `/`), no anota nada."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text(
        "x = 1\n# Busca marcadores TODO/FIXME/HACK en el codigo\n", encoding="utf-8")
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 0


def test_marcador_real_seguido_de_otro_marcador_en_prosa_si_cuenta(tmp_path):
    """R2-2: «# TODO: quitar el FIXME de abajo» NO encadena (hay prosa entre TODO y FIXME) — sigue
    siendo un TODO real, no una enumeración."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text(
        "x = 1\n# TODO: quitar el FIXME de abajo\n", encoding="utf-8")
    r = analiza(root, exclude_tests=False)
    assert r["marcadores"]["total"] == 1
    assert r["marcadores"]["por_tipo"] == {"TODO": 1}


def test_mutante_enumeracion_encadenada_sin_regla_cuenta_de_mas(tmp_path, monkeypatch):
    """Mutante: sin la regla de encadenados, la línea de convención cuenta como marcador real
    (rojo esperado)."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text(
        "x = 1\n# Busca marcadores TODO/FIXME/HACK en el codigo\n", encoding="utf-8")
    monkeypatch.setattr(ch, "_es_enumeracion_de_palabras_marcador", lambda raw: False)
    r_mutado = analiza(root, exclude_tests=False)
    assert r_mutado["marcadores"]["total"] > 0


# ------------------------------------------------------------------ --exclude-path (T-02)

def test_exclude_path_saca_el_prefijo_y_default_no_cambia(tmp_path):
    root = fixture(tmp_path, con_git=False)
    (root / "interop" / "opencode").mkdir(parents=True)
    (root / "interop" / "opencode" / "gen.py").write_text(BLOQUE_PY_RENOMBRADO + "\n", encoding="utf-8")
    sin_flag = analiza(root, exclude_tests=True)
    con_flag = analiza(root, exclude_tests=True, exclude_paths=["interop"])
    ficheros_sin = {f["fichero"] for f in sin_flag["tamano"]["top_ficheros"]}
    ficheros_con = {f["fichero"] for f in con_flag["tamano"]["top_ficheros"]}
    assert "interop/opencode/gen.py" in ficheros_sin
    assert "interop/opencode/gen.py" not in ficheros_con
    assert con_flag["tamano"]["ficheros"] == sin_flag["tamano"]["ficheros"] - 1


def test_exclude_path_repetible_con_dos_prefijos(tmp_path):
    root = fixture(tmp_path, con_git=False)
    (root / "interop" / "opencode").mkdir(parents=True)
    (root / "otro-generado").mkdir(parents=True)
    (root / "interop" / "opencode" / "gen.py").write_text("x = 1\n", encoding="utf-8")
    (root / "otro-generado" / "gen2.py").write_text("y = 2\n", encoding="utf-8")
    r = analiza(root, exclude_tests=True, exclude_paths=["interop/opencode", "otro-generado"])
    ficheros = {f["fichero"] for f in r["tamano"]["top_ficheros"]}
    assert "interop/opencode/gen.py" not in ficheros and "otro-generado/gen2.py" not in ficheros
    rc, out, _ = run(str(root), "--exclude-tests", "--exclude-path", "interop/opencode",
                      "--exclude-path", "otro-generado", "--json")
    assert rc == 0
    fs = {f["fichero"] for f in json.loads(out)["tamano"]["top_ficheros"]}
    assert "interop/opencode/gen.py" not in fs and "otro-generado/gen2.py" not in fs


def test_directorio_vacio_informe_sin_error(tmp_path):
    vacio = tmp_path / "vacio"
    vacio.mkdir()
    rc, out, _ = run(str(vacio))
    assert rc == 0 and "0 ficheros · 0 líneas" in out and "Sin bloques duplicados" in out
