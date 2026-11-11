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
    assert not any("git no disponible" in a for a in r["avisos"]) and r["hotspots"] is not None
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


# ------------------------------------------------------------------ ficheros versionados en exclusiones (D-063)

@pytest.mark.skipif(GIT is None, reason="sin git")
def test_versionados_bajo_exclusiones_se_cuentan_y_avisan_sin_analizarlos(tmp_path):
    root = fixture(tmp_path)                                   # vendor/lib/v.py está versionado
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}
    (root / "web" / "dist").mkdir(parents=True)
    (root / "web" / "dist" / "app.min.js").write_text("var a=1;\n", encoding="utf-8")
    (root / "web" / "dist" / "app.css").write_text("a{}\n", encoding="utf-8")   # cualquier extensión cuenta
    subprocess.run([GIT, "-C", str(root), "add", "-A"], check=True, env=env)
    subprocess.run([GIT, "-C", str(root), "commit", "-q", "-m", "dist"], check=True, env=env)
    (root / "build").mkdir()
    (root / "build" / "sin-versionar.js").write_text("x\n", encoding="utf-8")   # no versionado → no cuenta
    r = analiza(root)
    ev = r["excluidos_versionados"]
    assert ev["total"] == 3
    assert ev["por_directorio"] == {"vendor/": 1, "web/dist/": 2}
    aviso = [a for a in r["avisos"] if "versionados" in a]
    assert len(aviso) == 1 and "3 ficheros" in aviso[0] and "`web/dist/` (2)" in aviso[0] and "`vendor/` (1)" in aviso[0]
    ficheros = {f["fichero"] for f in r["tamano"]["top_ficheros"]}
    assert not any(f.startswith(("vendor/", "web/dist/")) for f in ficheros)   # siguen sin analizarse
    assert "versionados" in ch.md(r)


@pytest.mark.skipif(GIT is None, reason="sin git")
def test_versionados_bajo_exclusiones_respeta_exclude_path_y_subcarpeta(tmp_path):
    root = fixture(tmp_path)
    r = analiza(root, exclude_paths=["vendor"])                  # el usuario ya lo sacó a propósito
    assert r["excluidos_versionados"]["total"] == 0
    assert not any("versionados" in a for a in r["avisos"])
    sub = analiza(root / "src")                                  # rutas relativas a la carpeta analizada
    assert sub["excluidos_versionados"] == {"total": 0, "por_directorio": {}}


def test_versionados_bajo_exclusiones_sin_git_es_null(tmp_path):
    r = analiza(fixture(tmp_path, con_git=False))
    assert r["excluidos_versionados"] is None
    assert not any("versionados" in a for a in r["avisos"])



# ------------------------------------------------- H-37 (auditoría 2026-11-09, T-16): atajo de sin_comentario

class _LineaContada(str):
    """Cuenta los accesos por índice: el bucle carácter a carácter de `sin_comentario`."""
    accesos = 0

    def __getitem__(self, clave):
        type(self).accesos += 1
        return str.__getitem__(self, clave)


def test_h37_sin_comentario_no_recorre_las_lineas_sin_marcador_ni_comillas():
    """H-37: `sin_comentario` recorría cada carácter de cada línea (10 s del informe en este repo);
    una línea sin marcador ni comillas sale entera y una sin comillas se corta en el marcador."""
    _LineaContada.accesos = 0
    linea = _LineaContada("        resultado = calcular(a, b) + otra_funcion(c) * 2  " * 4)
    assert ch.sin_comentario(linea, "#") == str(linea)
    assert _LineaContada.accesos == 0, _LineaContada.accesos
    corta = _LineaContada("valor = 1  # comentario con texto")
    assert ch.sin_comentario(corta, "#") == "valor = 1  "
    assert _LineaContada.accesos <= 1


def test_h37_sin_comentario_igual_que_antes_en_el_codigo_del_repo():
    def referencia(line, marker):
        out, i, q = [], 0, None
        while i < len(line):
            c = line[i]
            if q:
                out.append(c)
                if c == "\\" and i + 1 < len(line):
                    out.append(line[i + 1])
                    i += 1
                elif c == q:
                    q = None
            elif c in "\"'":
                q = c
                out.append(c)
            elif line.startswith(marker, i):
                break
            else:
                out.append(c)
            i += 1
        return "".join(out)
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    vistas = 0
    for rel in ("agent-kits/shared/journal.py", "hooks/run-hook.mjs", "statusline/roadmap-statusline.sh",
                "skills/plugin-panel/assets/panel-review.js", "agent-kits/shared/ledger-lint.py"):
        marker = "//" if rel.endswith((".js", ".mjs")) else "#"
        with open(os.path.join(raiz, rel), encoding="utf-8", errors="replace") as fh:
            for line in fh.read().splitlines():
                assert ch.sin_comentario(line, marker) == referencia(line, marker), (rel, line[:80])
                vistas += 1
    assert vistas > 1000


# ------------------------- rendimiento (T-07, plugin-audit-2) -------------------------
OPS = ["+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>"]


def _repo_grande(tmp_path, n=120):
    """n ficheros DISTINTOS (secuencias de operadores pseudoaleatorias por fichero: la normalización
    reduce los identificadores y los números, así que solo los operadores distinguen unas líneas de otras)."""
    root = tmp_path / "grande"
    (root / "src").mkdir(parents=True)
    for i in range(n):
        estado, lineas = i * 7919 + 13, []
        for k in range(40):
            estado = (estado * 1103515245 + 12345) % 2147483648
            lineas.append(f"x{k} = a {OPS[(estado >> 8) % 10]} b {OPS[(estado >> 16) % 10]} {k}")
        (root / "src" / f"m{i:03d}.py").write_text(chr(10).join(lineas) + chr(10), encoding="utf-8")
    return root


def _repo_clonado(tmp_path, n):
    """n ficheros IDÉNTICOS: cada ventana de líneas aparece n × 37 veces (el caso que hacía explotar el
    emparejado, cuadrático por ventana: 120 ficheros agotaban 1 GiB)."""
    root = tmp_path / "clonado"
    (root / "src").mkdir(parents=True)
    for i in range(n):
        (root / "src" / f"c{i:03d}.py").write_text(
            chr(10).join(f"x{k} = a + b * {k}" if k % 2 else f"y{k} = a - b" for k in range(40)) + chr(10), encoding="utf-8")
    return root


def test_rendimiento_las_carpetas_ocultas_no_se_analizan(tmp_path):
    """`.pytest_cache`, `.mypy_cache`, `.tox`… son salida de herramientas: en este repo eran 7.204 de
    7.644 ficheros (3,4 M de líneas) y el informe no terminaba. Fuera por defecto."""
    root = _repo_grande(tmp_path, n=3)
    for oculta in (".pytest_cache", ".mypy_cache", "worktrees"):
        (root / oculta / "x").mkdir(parents=True)
        (root / oculta / "x" / "z.py").write_text("def z():\n    return 1\n", encoding="utf-8")
    rels = [rel for rel, _p, _e in ch.ficheros(str(root), {"py"}, False)]
    assert rels == ["src/m000.py", "src/m001.py", "src/m002.py"], rels


def test_rendimiento_el_tope_de_ficheros_avisa_y_no_inventa(tmp_path):
    root = _repo_grande(tmp_path, n=120)
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_files=50)
    assert r["resumen"]["ficheros"] == 50
    assert r["parcial"] is True
    assert any("50 de 120" in a for a in r["avisos"]), r["avisos"]
    # sin tope, el mismo repo se analiza entero y no es parcial
    entero = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10)
    assert entero["resumen"]["ficheros"] == 120 and entero["parcial"] is False


def test_rendimiento_el_tope_de_tiempo_corta_y_lo_dice(tmp_path):
    root = _repo_grande(tmp_path, n=120)
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_seconds=1e-9)
    assert r["parcial"] is True
    assert any("tiempo" in a for a in r["avisos"]), r["avisos"]
    assert r["resumen"]["ficheros"] < 120


def test_rendimiento_la_cli_acepta_los_topes(tmp_path):
    root = _repo_grande(tmp_path, n=30)
    p = subprocess.run([sys.executable, SCRIPT, str(root), "--json", "--max-files", "10", "--max-seconds", "60"],
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stderr
    r = json.loads(p.stdout)
    assert r["resumen"]["ficheros"] == 10 and r["parcial"] is True


def test_rendimiento_las_ventanas_repetidas_no_explotan_y_se_declaran(tmp_path):
    """Tope de ocurrencias por ventana: con 8 ficheros idénticos cada ventana sale > 50 veces; solo se
    emparejan las 50 primeras (memoria acotada) y el informe se declara PARCIAL, nunca un % inventado."""
    root = _repo_clonado(tmp_path, 8)
    cod = {rel: ch.lineas_codigo(ch.leer(p), e) for rel, p, e in ch.ficheros(str(root), {"py"}, False)}
    d = ch.duplicados(cod, 8, 10, max_occ=20)
    assert d["recortadas"] > 0 and d["parcial"] is True
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10)
    assert r["parcial"] is True and any("ocurrencias" in a for a in r["avisos"]), r["avisos"]
    assert r["resumen"]["duplicado_pct"] > 0



# ------------------------- T-07 fix1 (revisión intento 1, gaps 5-7, 12, 13, 17, 18) -------------------------
import time
import tracemalloc


def _clon_de_plantilla(tmp_path, copias, lineas):
    root = tmp_path / "plantilla"
    (root / "src").mkdir(parents=True)
    estado, filas = 4242, []
    for k in range(lineas):          # secuencia pseudoaleatoria de operadores: las ventanas de 8 líneas son distintas
        estado = (estado * 1103515245 + 12345) % 2147483648
        filas.append(f"x{k} = a {OPS[(estado >> 8) % 10]} b {OPS[(estado >> 16) % 10]} {k}")
    cuerpo = chr(10).join(filas) + chr(10)
    for i in range(copias):
        (root / "src" / f"p{i:03d}.py").write_text(cuerpo, encoding="utf-8")
    return root


def _cod(root):
    return {rel: ch.lineas_codigo(ch.leer(p), e) for rel, p, e in ch.ficheros(str(root), {"py"}, False)}


def test_fix1_gap5_baseline_parcial_contra_completo_no_es_comparable_en_los_dos_sentidos(tmp_path):
    root = _repo_grande(tmp_path, n=30)
    completo = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10)
    parcial = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_files=10)
    assert parcial["parcial"] is True and completo["parcial"] is False
    for actual, base in ((parcial, completo), (completo, parcial)):
        comp = ch.comparar(actual, base)
        assert comp and all(c["tendencia"].startswith("no comparable") for c in comp), comp
    assert not any(c["tendencia"].startswith("no comparable") for c in ch.comparar(completo, completo))


def test_fix1_gap5_la_cli_avisa_de_la_comparacion_parcial(tmp_path):
    root = _repo_grande(tmp_path, n=30)
    rc, js_parcial, _ = run(str(root), "--json", "--max-files", "10")
    base = tmp_path / "base.json"
    base.write_text(js_parcial, encoding="utf-8")
    rc, out, _ = run(str(root), "--json", "--baseline", str(base))
    r = json.loads(out)
    assert rc == 0 and all(c["tendencia"].startswith("no comparable") for c in r["baseline"])
    assert any("baseline" in a and "parcial" in a for a in r["avisos"]), r["avisos"]


def test_fix1_gap6_la_memoria_del_emparejado_esta_acotada_con_copias_de_una_plantilla(tmp_path):
    """60 copias de una plantilla de 500 líneas: 493 ventanas × C(50,2) pares = 604 K pares en un `set` de
    tuplas (75 MiB medidos). Con el tope total de pares la memoria no crece y el informe se declara parcial."""
    root = _clon_de_plantilla(tmp_path, 60, 500)
    cod = _cod(root)
    tracemalloc.start()
    d = ch.duplicados(cod, 8, 10)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert pico < 40 * 1024 * 1024, f"pico {pico / 1048576:.1f} MiB"
    assert d["parcial"] is True and d["pares_tope"] is True and d["pares"] <= ch.MAX_PARES_DEFAULT, d


def test_fix1_gap6_el_tope_de_pares_es_un_parametro_y_el_aviso_lo_cita(tmp_path):
    root = _clon_de_plantilla(tmp_path, 20, 60)
    d = ch.duplicados(_cod(root), 8, 10, max_occ=0, max_pares=100)
    assert d["pares_tope"] is True and d["pares"] <= 100 and d["parcial"] is True
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_pares=100)
    assert r["parcial"] is True and any("100 pares" in a for a in r["avisos"]), r["avisos"]


@pytest.mark.skipif(GIT is None, reason="sin git")
def test_fix1_gap7_git_blame_respeta_el_plazo_y_lo_declara(tmp_path, monkeypatch):
    root = tmp_path / "todos"
    (root / "src").mkdir(parents=True)
    for i in range(12):
        (root / "src" / f"t{i:02d}.py").write_text(f"x = {i}\n# TODO: pendiente {i}\n", encoding="utf-8")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@x"}
    subprocess.run([GIT, "-C", str(root), "init", "-q"], check=True, env=env)
    subprocess.run([GIT, "-C", str(root), "add", "-A"], check=True, env=env)
    subprocess.run([GIT, "-C", str(root), "commit", "-q", "-m", "base"], check=True, env=env)
    original, blames = ch.git, []

    def lento(r, *a, **kw):
        if a and a[0] == "blame":
            blames.append(a)
            time.sleep(0.5)
        return original(r, *a, **kw)
    monkeypatch.setattr(ch, "git", lento)
    t0 = time.monotonic()
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_seconds=3.0)
    dur = time.monotonic() - t0
    assert len(blames) < 12, len(blames)
    assert dur < 5.5, dur   # sin plazo serían 12 × 0,5 s
    assert r["parcial"] is True and any("antigüedad" in a for a in r["avisos"]), r["avisos"]
    assert r["marcadores"]["total"] == 12 and r["marcadores"]["edad_parcial"] > 0


def test_fix1_gap12_la_cli_permite_quitar_o_cambiar_el_tope_por_ventana(tmp_path):
    root = _clon_de_plantilla(tmp_path, 60, 40)
    rc, out, _ = run(str(root), "--json")
    assert rc == 0 and json.loads(out)["duplicados"]["recortadas"] > 0
    rc, out, _ = run(str(root), "--json", "--max-occ", "0")
    r = json.loads(out)
    assert rc == 0 and r["duplicados"]["recortadas"] == 0 and r["duplicados"]["pct"] > 0, r["duplicados"]
    rc, out, _ = run(str(root), "--json", "--max-occ", "7")
    r = json.loads(out)
    assert any("más de 7 veces" in a for a in r["avisos"]), r["avisos"]      # gap 18: el aviso cita el tope REAL


@pytest.mark.skipif(GIT is None, reason="sin git")
def test_fix1_gap13_las_carpetas_ocultas_versionadas_se_cuentan_y_avisan(tmp_path):
    root = fixture(tmp_path)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}
    (root / ".oculta" / "src").mkdir(parents=True)
    (root / ".oculta" / "src" / "z.py").write_text("def z():\n    return 1\n", encoding="utf-8")
    (root / ".oculta" / "notas.txt").write_text("no es código\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(root), "add", "-A"], check=True, env=env)
    subprocess.run([GIT, "-C", str(root), "commit", "-q", "-m", "oculta"], check=True, env=env)
    r = analiza(root)
    assert r["excluidos_versionados"]["por_directorio"].get(".oculta/") == 1, r["excluidos_versionados"]
    assert any("`.oculta/`" in a for a in r["avisos"]), r["avisos"]
    assert not any(f["fichero"].startswith(".oculta/") for f in r["tamano"]["top_ficheros"])


def test_fix1_gap17_un_fichero_enorme_se_omite_y_lineas_codigo_respeta_el_plazo(tmp_path):
    root = tmp_path / "enorme"
    (root / "src").mkdir(parents=True)
    (root / "src" / "pequeno.py").write_text("x = 1\n", encoding="utf-8")
    (root / "src" / "enorme.py").write_text("y = 2\n" + "z = 3\n" * 50000, encoding="utf-8")
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_bytes=10000)
    assert r["resumen"]["ficheros"] == 1 and r["parcial"] is True
    assert any("enorme.py" in a and "bytes" in a for a in r["avisos"]), r["avisos"]
    with pytest.raises(ch.PlazoAgotado):
        ch.lineas_codigo(["x = 1"] * 10000, "py", plazo=time.monotonic() - 1)
    r2 = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_seconds=1e-9)
    assert r2["parcial"] is True


def test_fix1_gap18_el_tope_por_ventana_no_pierde_la_duplicacion_entre_ficheros():
    """Las 50 primeras ocurrencias eran todas del fichero `a` (el mismo bloque repetido): el par a↔b se perdía."""
    a = [(i, f"L{i % 8}") for i in range(800)]
    b = [(i, f"L{i % 8}") for i in range(8)]
    d = ch.duplicados({"a": a, "b": b}, 8, 10, max_occ=50)
    assert d["bloques"] >= 1 and any(x["b"].startswith("b:") for x in d["top"]), d


def test_fix1_gap18_con_el_plazo_vencido_los_duplicados_no_se_dan_como_cero(tmp_path):
    root = _repo_grande(tmp_path, n=20)
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_seconds=1e-9)
    assert r["duplicados"]["pct"] is None and r["resumen"]["duplicado_pct"] is None
    texto = ch.md(r)
    assert "n/d" in texto and "None" not in texto


# ---- T-07 fix2 (intento 2: gaps 2, 3 y 4) ----
def test_fix2_gap2_dos_parciales_con_distinta_cobertura_no_son_comparables(tmp_path):
    root = _repo_grande(tmp_path, n=30)
    p10 = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_files=10)
    p10b = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_files=10)
    p12 = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10, max_files=12)
    assert p10["parcial"] and p12["parcial"] and p10b["parcial"]
    comp = ch.comparar(p12, p10)
    assert comp and all(c["tendencia"].startswith("no comparable") for c in comp), comp
    # cobertura idéntica (mismos ficheros y líneas): comparable aunque ambos sean parciales
    assert not any(c["tendencia"].startswith("no comparable") for c in ch.comparar(p10b, p10))


def test_fix2_gap2_la_cli_avisa_cuando_los_dos_son_parciales_con_distinta_cobertura(tmp_path):
    root = _repo_grande(tmp_path, n=30)
    rc, js, _ = run(str(root), "--json", "--max-files", "10")
    base = tmp_path / "base.json"
    base.write_text(js, encoding="utf-8")
    rc, out, _ = run(str(root), "--json", "--max-files", "12", "--baseline", str(base))
    r = json.loads(out)
    assert rc == 0 and all(c["tendencia"].startswith("no comparable") for c in r["baseline"])
    assert any("baseline" in a and "cobertura" in a for a in r["avisos"]), r["avisos"]


def _repo_con_todos(tmp_path, ficheros=1, por_fichero=1, git_commit=True):
    root = tmp_path / "todos2"
    (root / "src").mkdir(parents=True)
    for i in range(ficheros):
        cuerpo = "".join(f"# TODO: pendiente {i}-{k}\nx{k} = {k}\n" for k in range(por_fichero))
        (root / "src" / f"t{i:02d}.py").write_text(cuerpo, encoding="utf-8")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@x"}
    subprocess.run([GIT, "-C", str(root), "init", "-q"], check=True, env=env)
    if git_commit:
        subprocess.run([GIT, "-C", str(root), "add", "-A"], check=True, env=env)
        subprocess.run([GIT, "-C", str(root), "commit", "-q", "-m", "base"], check=True, env=env)
    return root


@pytest.mark.skipif(GIT is None, reason="sin git")
@pytest.mark.parametrize("fallo", [OSError(206, "línea de comandos demasiado larga"),
                                   subprocess.TimeoutExpired("git", 1)])
def test_fix2_gap3_un_blame_cortado_o_con_oserror_marca_parcial_y_avisa(tmp_path, monkeypatch, fallo):
    root = _repo_con_todos(tmp_path, ficheros=2, por_fichero=3)
    original = subprocess.run

    def roto(cmd, *a, **kw):
        if "blame" in cmd:
            raise fallo
        return original(cmd, *a, **kw)
    monkeypatch.setattr(ch.subprocess, "run", roto)
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10)
    assert r["marcadores"]["total"] == 6 and r["marcadores"]["edad_parcial"] == 6, r["marcadores"]
    assert r["parcial"] is True and any("antigüedad" in a for a in r["avisos"]), r["avisos"]


@pytest.mark.skipif(GIT is None, reason="sin git")
def test_fix2_gap3_un_fichero_sin_seguimiento_no_es_un_informe_parcial(tmp_path):
    """`git blame` sale con error en un fichero sin versionar: no es un corte por tiempo ni por la línea de comandos."""
    root = _repo_con_todos(tmp_path, ficheros=1, por_fichero=1)
    (root / "src" / "nuevo.py").write_text("# TODO: sin versionar\nx = 1\n", encoding="utf-8")
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 10)
    assert r["marcadores"]["total"] == 2 and r["marcadores"]["edad_parcial"] == 0
    assert sorted(t["edad_dias"] is None for t in r["marcadores"]["top"]) == [False, True]
    assert r["parcial"] is False, r["avisos"]


@pytest.mark.skipif(GIT is None, reason="sin git")
def test_fix2_gap3_los_L_del_blame_se_trocean_y_todas_las_edades_se_calculan(tmp_path, monkeypatch):
    root = _repo_con_todos(tmp_path, ficheros=1, por_fichero=450)
    original, llamadas = ch.git, []

    def espia(r, *a, **kw):
        if a and a[0] == "blame":
            llamadas.append(a)
        return original(r, *a, **kw)
    monkeypatch.setattr(ch, "git", espia)
    r = ch.analizar(str(root), {"py"}, 8, 6, False, 90, 450)
    assert len(llamadas) > 1, len(llamadas)
    assert max(sum(1 for t in a if t == "-L") for a in llamadas) <= ch.BLAME_L_POR_LLAMADA
    assert max(sum(len(t) + 1 for t in a) for a in llamadas) < 12000     # holgado bajo los 32 K de Windows
    assert r["marcadores"]["total"] == 450 and r["marcadores"]["edad_parcial"] == 0
    assert all(t["edad_dias"] is not None for t in r["marcadores"]["top"])
    assert not any("antigüedad" in a for a in r["avisos"]), r["avisos"]


def test_fix2_gap4_sin_tope_por_ventana_el_plazo_acota_tambien_el_doble_bucle():
    """150 copias de 300 líneas, `max_occ=0`: 11 K pares × 293 ventanas = 3,3 M iteraciones en UNA pasada por
    ventana; el plazo solo se miraba cada 512 ventanas, es decir, nunca."""
    cod = {f"f{i:03d}.py": [(k, f"x{k} = a + {k}") for k in range(300)] for i in range(150)}
    t0 = time.monotonic()
    d = ch.duplicados(cod, 8, 10, plazo=time.monotonic() + 0.3, max_occ=0, max_pares=0)
    dur = time.monotonic() - t0
    assert d["parcial"] is True and dur < 1.5, (dur, d["parcial"])


def test_fix2_gap4_los_pares_del_mismo_fichero_cuentan_para_el_tope():
    """Un fichero con 3000 líneas idénticas: 1 ventana con 3000 ocurrencias del MISMO fichero (4,5 M pares que
    nunca se retienen). El tope de pares tiene que cortar este trabajo también."""
    cod = {"a.py": [(k, "x = 1") for k in range(3000)]}
    t0 = time.monotonic()
    d = ch.duplicados(cod, 8, 10, max_occ=0, max_pares=100)
    dur = time.monotonic() - t0
    assert d["pares_tope"] is True and d["parcial"] is True and dur < 1.0, (dur, d)
