#!/usr/bin/env python3
"""Tests de `changelog-sync.py` (superiority T-02). Sin red, sin modelo: fixtures en tmp."""
import importlib.util
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "changelog-sync.py")
# raíz del repo cuando la skill vive dentro de él (en el paquete portable no existe: se salta)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LEDGER_LINT = os.path.join(REPO, "agent-kits", "shared", "ledger-lint.py")


def _mod(ruta=SCRIPT, nombre="changelog_sync"):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


cs = _mod()

EN = """# Changelog

## [Unreleased]

## [1.0.0] - 2026-01-01

### Added

- algo previo con `viejo-slug`

[1.0.0]: https://example.invalid/releases/tag/v1.0.0
"""
ES = EN.replace("## [Unreleased]", "## [Sin publicar]")

LEDGER = """---
tasks: {slug}
descripcion: {desc}
estado: {estado}
{extra}---

# Checklist de Tareas — {slug}

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase única — x | 1 | 1 | 100% |

## Fase única — x

**Estado**: completado

### T-01 — Hacer la cosa

- **Descripción**: {tdesc}
- **Estado**: completado
{tcampos}- **Archivos**: {tarch}
- **Verificación**: `pytest -q` → verde

**Criterios de aceptación**
- [x] hecho
"""


DESC_DEFECTO = "Primera frase de la tarea. Segunda frase que NO debe salir."
ARCH_DEFECTO = "`a.py` (nuevo), `b.md`, `c.json`, `d.sh`, `e.txt`, `f.ini`"


def proyecto(tmp, slug="demo", estado="completado", desc="Añade la cosa nueva.", extra="",
             fecha="2026-05-05", tdesc=DESC_DEFECTO, tcampos="", tarch=ARCH_DEFECTO):
    d = os.path.join(tmp, "docs", "roadmap", f"{fecha}-{slug}")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "tasks.md"), "w", encoding="utf-8") as fh:
        fh.write(LEDGER.format(slug=slug, estado=estado, desc=desc, extra=extra,
                               tdesc=tdesc, tcampos=tcampos, tarch=tarch))
    for fn, body in (("CHANGELOG.md", EN), ("CHANGELOG.es.md", ES)):
        p = os.path.join(tmp, fn)
        if not os.path.exists(p):
            open(p, "w", encoding="utf-8").write(body)
    return tmp


def run(*args, root=None):
    cmd = [sys.executable, SCRIPT] + (["--root", root] if root else []) + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_genera_en_y_es_con_un_bullet_por_tarea(tmp_path):
    root = proyecto(str(tmp_path))
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    es = open(os.path.join(root, "CHANGELOG.es.md"), encoding="utf-8").read()
    assert "### Added — `demo` initiative (2026-05-05)" in en
    assert "### Added — iniciativa `demo` (2026-05-05)" in es
    assert "**T-01 — Hacer la cosa** Primera frase de la tarea." in en
    assert "Segunda frase" not in en, "solo la primera frase de la Descripción"
    # como mucho ARCHIVOS_MAX (3) archivos, sin la anotación entre paréntesis
    assert "`a.py`, `b.md`, `c.json`" in en and "`d.sh`" not in en and "`f.ini`" not in en
    assert "(nuevo)" not in en.split("### Added")[1].split("\n\n")[1]
    # la entrada va DENTRO de la sección abierta, antes de la versión publicada
    assert en.index("### Added — `demo`") < en.index("## [1.0.0]")


def test_idempotente_segunda_ejecucion_no_cambia_nada(tmp_path):
    root = proyecto(str(tmp_path))
    run(root=root)
    antes = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    r = run(root=root)
    assert r.returncode == 0 and "sin entradas pendientes" in r.stdout
    assert open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read() == antes


def test_dry_run_no_escribe_pero_muestra(tmp_path):
    root = proyecto(str(tmp_path))
    antes = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    r = run("--dry-run", root=root)
    assert r.returncode == 0 and "--dry-run" in r.stdout and "`demo` initiative" in r.stdout
    assert open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read() == antes


def test_check_exit_1_pendiente_y_0_tras_sincronizar(tmp_path):
    root = proyecto(str(tmp_path))
    r = run("--check", root=root)
    assert r.returncode == 1 and "PENDIENTES" in r.stdout
    run(root=root)
    r = run("--check", root=root)
    assert r.returncode == 0 and "sin entradas pendientes" in r.stdout


def test_slug_ya_presente_no_se_duplica(tmp_path):
    root = proyecto(str(tmp_path), slug="viejo-slug")   # ya citado en el CHANGELOG fixture
    r = run("--check", root=root)
    assert r.returncode == 0, r.stdout


def test_ledger_no_cerrado_se_ignora(tmp_path):
    root = proyecto(str(tmp_path), estado="en-progreso")
    r = run("--check", root=root)
    assert r.returncode == 0 and "sin entradas pendientes" in r.stdout


def test_only_limita_a_una_iniciativa_y_slug_inexistente_es_uso(tmp_path):
    root = proyecto(str(tmp_path), slug="uno", fecha="2026-05-05")
    proyecto(root, slug="dos", fecha="2026-05-06")
    r = run("--only", "uno", root=root)
    assert r.returncode == 0
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "`uno`" in en and "`dos`" not in en
    r = run("--only", "fantasma", root=root)
    assert r.returncode == 2 and "fantasma" in r.stderr


def test_categoria_heuristica_y_override(tmp_path):
    r1 = proyecto(str(tmp_path / "a"), slug="fx", desc="Corrige el bug del parser.")
    assert run("--check", "--json", root=r1).stdout.count('"categoria": "Fixed"') == 1
    r2 = proyecto(str(tmp_path / "b"), slug="ch", desc="Retira el agente duplicado.")
    assert run("--check", "--json", root=r2).stdout.count('"categoria": "Changed"') == 1
    r3 = proyecto(str(tmp_path / "c"), slug="ov", desc="Corrige el bug.", extra="changelog: Added\n")
    assert run("--check", "--json", root=r3).stdout.count('"categoria": "Added"') == 1


def test_sin_changelog_es_error_de_uso(tmp_path):
    root = proyecto(str(tmp_path))
    os.remove(os.path.join(root, "CHANGELOG.es.md"))
    r = run("--check", root=root)
    assert r.returncode == 2 and "CHANGELOG.es.md" in r.stderr


def test_ledger_legacy_sin_frontmatter_avisa_y_no_rompe(tmp_path):
    root = proyecto(str(tmp_path))
    d = os.path.join(root, "docs", "roadmap", "2026-01-01-legacy")
    os.makedirs(d)
    open(os.path.join(d, "tasks.md"), "w", encoding="utf-8").write("# Checklist\n\n### T-01 — x\n")
    r = run("--check", root=root)
    assert "legacy" in r.stdout and r.returncode == 1


def test_json_coherente_con_el_texto(tmp_path):
    root = proyecto(str(tmp_path))
    r = run("--check", "--json", root=root)
    d = json.loads(r.stdout)
    assert d["pendientes"][0]["slug"] == "demo" and d["pendientes"][0]["tareas"] == 1
    assert d["pendientes"][0]["ficheros"] == ["CHANGELOG.md", "CHANGELOG.es.md"]


def test_orden_por_fecha_lo_mas_reciente_arriba(tmp_path):
    root = proyecto(str(tmp_path), slug="viejo", fecha="2026-05-01")
    proyecto(root, slug="nuevo", fecha="2026-05-09")
    run(root=root)
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert en.index("`nuevo`") < en.index("`viejo`")


def test_primera_frase_no_corta_abreviaturas():
    assert cs.primera_frase("Usa `p. ej.` esto. Y otra cosa.") == "Usa `p. ej.` esto."




# ---------------------------------------------------------------------------------------------
# La ESCALERA del resumen (changelog-brief T-01/T-02): campo `Changelog:` → primera frase →
# oración principal → solo el título. Un bullet de una o dos frases, sin truncar a lo bruto.
# ---------------------------------------------------------------------------------------------

DESC_LARGA = (
    "`agent-kits/shared/loquesea.py` gana tres subcomandos nuevos que hacen cosas distintas: "
    "el primero calcula, el segundo valida y el tercero imprime, y cada uno tiene su propio "
    "formato de salida, su propio exit code y su propia batería de tests, porque el criterio "
    "de cada uno es independiente del de los otros dos y mezclarlos sería un error."
)
# El patrón REAL dominante en los ledgers de este repo: la Descripción empieza por la ruta del
# fichero entre acentos graves y un `:`. Cortar ahí da una LISTA DE FICHEROS, no un resumen.
DESC_SOLO_RUTAS = (
    "`docs/README.md` + `docs/en/README.md`: la tabla de skills gana su fila, la de comandos "
    "otra, y además hay que tocar el índice, el `CLAUDE.md`, el `FLOWS.md` y las dos versiones "
    "de `INSTALL.md`, porque el flujo cambia de forma visible para quien instala el plugin."
)


def test_campo_changelog_se_usa_tal_cual_y_manda_sobre_la_descripcion(tmp_path):
    root = proyecto(str(tmp_path), tdesc=DESC_LARGA,
                    tcampos="- **Changelog**: El plugin ya no revienta al arrancar sin config.\n")
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "**T-01 — Hacer la cosa** El plugin ya no revienta al arrancar sin config." in en
    assert "subcomandos nuevos" not in en, "el campo Changelog manda sobre la Descripción"


def test_campo_changelog_con_tres_frases_se_recorta_a_dos_y_avisa(tmp_path):
    root = proyecto(str(tmp_path), tcampos=(
        "- **Changelog**: Primera. Segunda. Tercera que sobra.\n"))
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "Primera. Segunda." in en and "Tercera" not in en
    assert "T-01" in r.stdout and "recortado a las 2 primeras frases" in r.stdout, r.stdout


def test_campo_changelog_pasado_de_tope_avisa_pero_no_falla_ni_trunca(tmp_path):
    largo = "Cambia " + "mucho y mucho " * 20 + "de golpe."
    assert len(largo) > cs.RESUMEN_MAX
    root = proyecto(str(tmp_path), tcampos=f"- **Changelog**: {largo}\n")
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert largo in en, "no se trunca lo que escribió una persona"
    assert "…" not in en and "..." not in en
    assert f"{cs.RESUMEN_MAX}" in r.stdout and "T-01" in r.stdout, r.stdout


def test_primera_frase_corta_se_sigue_usando_como_hoy(tmp_path):
    root = proyecto(str(tmp_path))          # descripción de fixture: primera frase corta
    r = run(root=root)
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "**T-01 — Hacer la cosa** Primera frase de la tarea." in en
    assert "Segunda frase" not in en


def test_la_primera_frase_tambien_entra_normalizada(tmp_path):
    """Las Descripciones de este repo empiezan en minúscula; tras `**T-XX — Título**` eso se lee
    mal. La mayúscula inicial la pone `normaliza_resumen()`, igual en los dos caminos automáticos."""
    root = proyecto(str(tmp_path), tdesc="la cosa deja de reventar al arrancar. Y otra frase.")
    run(root=root)
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "**T-01 — Hacer la cosa** La cosa deja de reventar al arrancar." in en


def test_el_campo_changelog_se_respeta_literal_sin_normalizar(tmp_path):
    root = proyecto(str(tmp_path), tcampos="- **Changelog**: en minúscula a propósito.\n")
    run(root=root)
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "**T-01 — Hacer la cosa** en minúscula a propósito." in en, "tal cual = tal cual"


def test_primera_frase_larga_degrada_a_la_oracion_principal(tmp_path):
    root = proyecto(str(tmp_path), tdesc=(
        "El comando pasa a leer la config del proyecto antes de decidir, y no al revés: "
        "sin eso el default se aplicaba siempre, con o sin fichero, y nadie lo notaba hasta "
        "que el proyecto traía una config distinta de la de fábrica y el comando la ignoraba."))
    r = run(root=root)
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "El comando pasa a leer la config del proyecto antes de decidir, y no al revés." in en
    assert "sin eso el default" not in en


def test_sin_corte_util_degrada_al_titulo_con_puntero_al_ledger(tmp_path):
    # Descripción que EMPIEZA por la ruta del fichero: cortar en el `:` daría una lista de
    # ficheros, no un resumen. Se degrada al título (honesto) con el puntero al ledger.
    root = proyecto(str(tmp_path), tdesc=DESC_SOLO_RUTAS)
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "- **T-01 — Hacer la cosa** ([ledger](docs/roadmap/2026-05-05-demo/tasks.md))" in en
    assert "tabla de skills" not in en and "`a.py`" not in en


def test_ningun_camino_trunca_con_elipsis(tmp_path):
    """Los CUATRO caminos, no solo el que ya no podía llevar `…` por construcción: con un solo caso
    del camino `titulo` este test pasaba también contra el script viejo, así que no fijaba nada."""
    campo_largo = "Cambia " + "mucho y mucho " * 20 + "de golpe."      # camino changelog, > tope
    casos = [("changelog", DESC_LARGA, f"- **Changelog**: {campo_largo}\n"),
             ("frase", "La cosa deja de reventar al arrancar. Y otra frase.", ""),
             ("corte", "`x.py` deja de reventar al arrancar: " + "y aqui el detalle " * 15, ""),
             ("titulo", DESC_SOLO_RUTAS, "")]
    for i, (camino, desc, campos) in enumerate(casos):
        root = proyecto(str(tmp_path / f"c{i}"), slug=f"s{i}", tdesc=desc, tcampos=campos)
        r = run(root=root)
        assert r.returncode == 0, r.stdout + r.stderr
        d = json.loads(run("--check", "--json", root=root).stdout)
        assert d["degradacion"]["caminos"] == {camino: 1}, (camino, d["degradacion"])
        for fn in ("CHANGELOG.md", "CHANGELOG.es.md"):
            t = open(os.path.join(root, fn), encoding="utf-8").read()
            assert "…" not in t and "..." not in t, (camino, fn)


def test_un_elipsis_del_ledger_pasa_tal_cual_pero_el_script_no_anade_ninguno(tmp_path):
    """`…` en la salida solo puede venir del ledger (una cadena de uso como `[--files f1 f2 …]`).
    El contrato es «el script no AÑADE `…`», no «no hay `…`»: pasa 2 de los 126 bullets reales."""
    root = proyecto(str(tmp_path), tdesc="Acepta `--files f1 f2 …` y decide.", tarch="`x.py`")
    run(root=root)
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "**T-01 — Hacer la cosa** Acepta `--files f1 f2 …` y decide." in en
    assert en.count("…") == 1, "el del ledger, y ninguno más"


def test_un_campo_ARCHIVOS_vacio_no_inventa_ficheros(tmp_path):
    r"""Mutante superviviente (era el CRITICAL 1 del intento 1 aplicado a `Archivos`): con `\s*` en
    vez de `[^\S\n]*`, `re.M` se come el salto de línea y un `- **Archivos**:` VACÍO captura la
    línea siguiente entera. Medido con el mutante: una fila de tabla `| \`x.py\` | \`y.py\` |` daba
    `['x.py', 'y.py']` —ficheros INVENTADOS en el CHANGELOG— y un `- **Verificación**: \`pytest -q\``
    daba `['pytest -q']`. Estaba arreglado en el código y sin test, así que nada impedía que
    volviese."""
    # (una línea indentada de PROSA sí se absorbe a propósito: es la continuación del campo, T-06)
    for debajo, invento in (("| `x.py` | `y.py` |", ["x.py", "y.py"]),
                            ("- **Verificación**: `pytest -q` → verde", ["pytest -q"]),
                            ("  1. `pytest -q`", ["pytest -q"])):
        bloque = (f"### T-01 — x\n\n- **Descripción**: Frase corta de prueba.\n"
                  f"- **Archivos**:\n{debajo}\n- **Estado**: completado\n")
        assert cs.tareas(bloque)[0]["archivos"] == [], (debajo, invento)
    # de punta a punta: el bullet no lleva paréntesis de ficheros
    root = proyecto(str(tmp_path), tarch="", tdesc="Frase corta de prueba.")
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    linea = [l for l in open(os.path.join(root, "CHANGELOG.md"),
                             encoding="utf-8").read().split("\n") if "T-01" in l][0]
    assert linea == "- **T-01 — Hacer la cosa** Frase corta de prueba.", linea


def test_la_guarda_de_abreviatura_exige_frontera_de_palabra():
    """Mutante superviviente: sin la frontera, `antes.endswith("ed.")` casa «la red.» y ninguna
    frase normal cierra. Medido con el mutante:
    `primera_frase("Mejora la red. Ahora va más rápido. Y una tercera.")` pasaba de
    `'Mejora la red.'` a DOS frases. Igual con `start.` (`art.`), `recap.` (`cap.`) e `IEEE.`
    (`ee.`)."""
    for texto, esperado in (
            ("Mejora la red. Ahora va más rápido. Y una tercera.", "Mejora la red."),
            ("Arranca el start. Luego sigue.", "Arranca el start."),
            ("Haz el recap. Y sigue.", "Haz el recap."),
            ("Usa el IEEE. Y luego otro.", "Usa el IEEE."),
            ("Sube el volumen. Y baja el brillo.", "Sube el volumen.")):
        assert cs.primera_frase(texto) == esperado, texto
    # …y la abreviatura de verdad, en frontera, sigue sin cerrar frase
    assert cs.primera_frase("Compara el hook vs. Claude nativo. Y gana el nativo.") == \
        "Compara el hook vs. Claude nativo."
    assert not cs._es_abreviatura("Mejora la red.", len("Mejora la red."))
    assert cs._es_abreviatura("Compara el hook vs.", len("Compara el hook vs."))


def test_corte_no_entra_en_un_tramo_de_doble_acento_grave_con_uno_dentro():
    """Mutante superviviente (`elif cerco == run:` → `else:`): con el toggle de uno en uno, el
    acento grave interior de `` ``a`b:c`` `` «cierra» el tramo y el corte entra dentro del código.
    Medido con el mutante: `corte_principal("Cambia el flag ``a`b:c`` del script y ya está")`
    pasaba de `None` a `'Cambia el flag ``a`b'`."""
    assert cs.corte_principal("Cambia el flag ``a`b:c`` del script y ya está") is None
    assert cs.corte_principal("Usa ``a`b:c`` y decide: el resto") == "Usa ``a`b:c`` y decide"
    assert cs.corte_principal("El literal ```x`y;z``` no corta") is None


def test_fin_de_frase_reconoce_la_apertura_con_asterisco():
    """Mutante superviviente: quitar `*` de la clase de apertura de `FIN_FRASE`. El patrón
    `. **(1) …` es MUY común en las `Descripción` de este repo (T-01 lo añadió a propósito), y sin
    él una descripción enumerada se lee como UNA sola frase."""
    t = "Arregla el parseo. **(1)** El campo vacío. **(2)** La cola del ledger."
    assert cs.primera_frase(t) == "Arregla el parseo."
    assert len(cs.separa_frases(t)) == 3, cs.separa_frases(t)
    assert "*" in cs.FIN_FRASE.pattern


def test_el_aviso_de_recorte_no_lo_dispara_el_espaciado(tmp_path):
    """El aviso se deduce del RECUENTO de frases, no de «el texto cambió»: un campo de dos frases
    con espaciado irregular se normaliza (el texto cambia) y NO se ha recortado nada."""
    campo = "Una  frase   con espacios.   Y la segunda."
    texto, camino, avisos = cs.resumen(None, campo)
    assert camino == "changelog" and avisos == [], (texto, avisos)
    assert texto == "Una frase con espacios. Y la segunda."


def test_los_dos_caminos_automaticos_respetan_el_tope():
    for desc in (DESC_LARGA, DESC_SOLO_RUTAS, "Frase normal y corta.",
                 "Algo larguísimo " * 40 + "que no cabe: y aquí el detalle."):
        texto, camino, _avisos = cs.resumen(desc, None)
        assert camino in ("frase", "corte", "titulo")
        if camino != "titulo":
            assert len(texto) <= cs.RESUMEN_MAX, (camino, len(texto), texto)


def test_archivos_se_omiten_con_mas_de_SEIS_ficheros_tocados(tmp_path):
    """Umbral con LITERAL: 7 ficheros → sin paréntesis. Antes la entrada se construía con
    `cs.ARCHIVOS_MAX_TOCADOS`, así que el test pasaba con cualquier valor de la constante."""
    assert cs.ARCHIVOS_MAX_TOCADOS == 6, "el contrato documentado es 6 (2 × ARCHIVOS_MAX)"
    siete = ", ".join(f"`f{i}.py`" for i in range(7))
    root = proyecto(str(tmp_path), tarch=siete)
    run(root=root)
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    linea = [l for l in en.split("\n") if "T-01" in l][0]
    assert "`f0.py`" not in linea, "con tantos ficheros la lista no informa: sin paréntesis"
    assert linea.endswith("Primera frase de la tarea.")


def test_archivos_justo_en_SEIS_se_listan_los_TRES_primeros(tmp_path):
    """Los dos topes con literales: 6 ficheros tocados aún se listan, y se listan 3."""
    assert cs.ARCHIVOS_MAX == 3 and cs.ARCHIVOS_MAX_TOCADOS == 6
    seis = ", ".join(f"`f{i}.py`" for i in range(6))
    root = proyecto(str(tmp_path), tarch=seis)
    run(root=root)
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    linea = [l for l in en.split("\n") if "T-01" in l][0]
    assert linea.endswith("(`f0.py`, `f1.py`, `f2.py`)"), linea


def test_check_avisa_de_las_tareas_sin_campo_changelog_sin_tocar_el_exit_code(tmp_path):
    root = proyecto(str(tmp_path))
    r = run("--check", root=root)
    assert r.returncode == 1 and "PENDIENTES" in r.stdout        # el 1 sigue siendo por lo pendiente
    assert "sin `- **Changelog**:`" in r.stdout and "T-01" in r.stdout, r.stdout
    run(root=root)                                               # ya sincronizado
    r = run("--check", root=root)
    assert r.returncode == 0, r.stdout                            # el aviso NO cambia el exit code


def test_check_no_repite_el_aviso_por_iniciativa_ya_publicada(tmp_path):
    """Una iniciativa YA en el CHANGELOG la salta `pendientes()` para siempre: escribir su campo no
    cambiaría un byte de salida, así que su aviso era ruido puro. Queda UNA línea con el total."""
    root = proyecto(str(tmp_path))
    run(root=root)                                               # publica la entrada
    r = run("--check", root=root)
    assert r.returncode == 0, r.stdout
    assert "sin `- **Changelog**:`" not in r.stdout, r.stdout
    assert "1/1 tarea(s) de 1/1 ledger(s) cerrados no lo traen" in r.stdout, r.stdout
    assert "0 bullet(s) degradan al título" in r.stdout, r.stdout   # esta tarea va por `frase`
    root2 = proyecto(str(tmp_path / "deg"), slug="deg", tdesc=DESC_SOLO_RUTAS)
    run(root=root2)
    r = run("--check", root=root2)
    assert "1 bullet(s) degradan al título" in r.stdout, r.stdout


def test_el_aviso_del_campo_no_lo_confunde_el_slug_pendiente_de_release(tmp_path):
    """Criterio T-03#6. `release.py` reconoce las iniciativas pendientes con `SLUG_PENDIENTE`
    (`<viñeta> <slug> (AAAA-MM-DD)`); ninguna línea de aviso del campo debe casar, o el resumen de
    pendientes del release se contaminaría con slugs inventados.

    Este test era TAUTOLÓGICO hasta el cierre de los gaps del intento 2: filtraba las líneas por
    `startswith("⚠️")` y luego afirmaba que ninguna casa. Pero `⚠️` es `U+26A0 U+FE0F` y el `\\s+`
    de la regex no puede consumir el selector de variación, así que **ninguna línea con ese prefijo
    casa jamás**, sea cual sea el cuerpo — el contrato que la docstring dice garantizar («aquí el
    slug lleva `:` detrás, no una fecha entre paréntesis») no estaba fijado. Ahora se comprueba el
    CUERPO del aviso, sin la decoración, y con un control positivo que prueba que la regex casa lo
    que debe casar."""
    slug_pendiente = re.compile(r"^\s*\S\s+([\w.-]+)\s+\(\d{4}-\d{2}-\d{2}\)")
    if os.path.isfile(os.path.join(REPO, "scripts", "release.py")):     # copia literal verificada
        fuente = open(os.path.join(REPO, "scripts", "release.py"), encoding="utf-8").read()
        assert slug_pendiente.pattern in fuente, "la regex de release.py cambió: actualiza el test"
    # CONTROL POSITIVO: la línea de iniciativa pendiente SÍ casa (si no, el test no prueba nada)
    m = slug_pendiente.match("  · demo (2026-05-05) — Changed, 1 tarea(s) → falta en CHANGELOG.md")
    assert m and m.group(1) == "demo", "el control positivo debe casar: la regex no está viva"
    # …y el prefijo `⚠️` por sí solo impide cualquier match, así que hay que quitarlo para probar
    assert not slug_pendiente.match("⚠️  demo (2026-05-05) — lo que sea"), \
        "si esto casara, el filtro por prefijo del test viejo no habría sido tautológico"
    root = proyecto(str(tmp_path))
    vistos = 0
    for args in (("--check",), ()):
        salida = run(*args, root=root).stdout
        avisos = [l for l in salida.split("\n") if l.startswith("⚠️")]
        assert avisos, salida
        for ln in avisos:
            cuerpo = ln.lstrip("⚠️ \ufe0f")          # el CUERPO, sin la decoración del aviso
            assert cuerpo, ln
            assert not slug_pendiente.match(cuerpo), cuerpo
            assert not slug_pendiente.match(ln), ln
            vistos += 1
    assert vistos >= 2, f"solo {vistos} avisos comprobados"


def test_json_cuenta_los_caminos_de_la_escalera(tmp_path):
    root = proyecto(str(tmp_path), tcampos="- **Changelog**: Una frase.\n")
    d = json.loads(run("--check", "--json", root=root).stdout)
    assert d["pendientes"][0]["caminos"] == {"changelog": 1}


def test_json_expone_la_degradacion_de_TODO_ledger_cerrado(tmp_path):
    """`pendientes[]` solo lista lo que FALTA en el CHANGELOG, así que la degradación de las
    iniciativas ya publicadas no se veía en `pendientes[].caminos` (se afirmaba que sí). El dato
    vive en `degradacion`, que recorre todo ledger cerrado esté publicado o no."""
    root = proyecto(str(tmp_path), slug="pub", tdesc=DESC_SOLO_RUTAS)
    run(root=root)                                                # `pub` queda publicada
    proyecto(root, slug="nueva", fecha="2026-05-06",
             tcampos="- **Changelog**: Una frase escrita.\n")
    d = json.loads(run("--check", "--json", root=root).stdout)
    assert [p["slug"] for p in d["pendientes"]] == ["nueva"]
    assert d["degradacion"]["ledgers"] == 2 and d["degradacion"]["tareas"] == 2
    assert d["degradacion"]["caminos"] == {"titulo": 1, "changelog": 1}, d["degradacion"]
    assert d["degradacion"]["sin_campo"] == 1 and d["degradacion"]["ledgers_sin_campo"] == 1
    assert d["degradacion"]["sin_campo_por_motivo"] == {"ausente": 1, "vacio": 0,
                                                        "placeholder": 0}, d["degradacion"]


def test_un_placeholder_cuenta_como_campo_SIN_escribir_en_la_deuda(tmp_path):
    """Gaps del intento 2: los tres sitios que miden la deuda usaban `not
    t["changelog"].strip()`, y un `{{…}}` no está vacío. Con un ledger cerrado y ya publicado cuya
    única tarea trae el placeholder de la plantilla, `--check` decía «sin entradas pendientes ✅» y
    nada más, y el `--json` daba `sin_campo: 0` / `ledgers_sin_campo: 0`: el bloque que existe para
    hacer VISIBLE la deuda reportaba cero justo en el caso que la plantilla crea."""
    ph = "{{qué cambia para quien USA el proyecto, en una frase}}"
    root = proyecto(str(tmp_path), slug="pub", tcampos=f"- **Changelog**: {ph}\n")
    run(root=root)                                                # `pub` queda publicada
    r = run("--check", root=root)
    assert r.returncode == 0 and "sin entradas pendientes" in r.stdout, r.stdout
    assert "1/1 tarea(s) de 1/1 ledger(s) cerrados no lo traen (1 placeholder)" in r.stdout, r.stdout
    d = json.loads(run("--check", "--json", root=root).stdout)
    assert d["degradacion"]["sin_campo"] == 1 and d["degradacion"]["ledgers_sin_campo"] == 1
    assert d["degradacion"]["sin_campo_por_motivo"] == {"ausente": 0, "vacio": 0,
                                                        "placeholder": 1}, d["degradacion"]
    # el campo VACÍO se distingue del placeholder (los dos cuentan, pero por motivos distintos)
    root2 = proyecto(str(tmp_path / "vacio"), slug="vac", tcampos="- **Changelog**:\n")
    run(root=root2)
    d2 = json.loads(run("--check", "--json", root=root2).stdout)
    assert d2["degradacion"]["sin_campo_por_motivo"] == {"ausente": 0, "vacio": 1,
                                                         "placeholder": 0}, d2["degradacion"]
    # …y una tarea sin el campo sigue contando como `ausente`
    root3 = proyecto(str(tmp_path / "ausente"), slug="aus")
    run(root=root3)
    d3 = json.loads(run("--check", "--json", root=root3).stdout)
    assert d3["degradacion"]["sin_campo_por_motivo"] == {"ausente": 1, "vacio": 0,
                                                         "placeholder": 0}, d3["degradacion"]


def test_el_aviso_por_iniciativa_pendiente_nombra_la_tarea_con_placeholder(tmp_path):
    """El otro sitio que medía la deuda: `aviso_sin_changelog()`. Con el placeholder no nombraba la
    tarea, así que la iniciativa pendiente parecía tener el campo escrito."""
    ph = "{{qué cambia para quien USA el proyecto, en una frase}}"
    root = proyecto(str(tmp_path), tcampos=f"- **Changelog**: {ph}\n")
    r = run("--check", root=root)
    assert r.returncode == 1, r.stdout
    assert "demo: 1/1 tarea(s) sin `- **Changelog**:` [T-01]" in r.stdout, r.stdout


# --- unidades de la escalera (sin ficheros: criterio puro) ---

def test_corte_principal_no_parte_dentro_de_codigo_ni_de_comillas():
    assert cs.corte_principal("Usa `a:b` y luego decide: el resto") == "Usa `a:b` y luego decide"
    assert cs.corte_principal("La sección «Coste (por qué)» del doc: detalle") == \
        "La sección «Coste (por qué)» del doc"
    assert cs.corte_principal("Sin ningún corte aquí") is None


# --- un caso por DELIMITADOR y por PAREJA, con literales: los cuatro delimitadores que enumeran
# el criterio T-01#4, `ADR-012` y `SKILL.md` estaban documentados y solo `:` estaba fijado por un
# test, así que sacar `;`, `—`, `–`, `[` o `{` de sus constantes no rompía nada. ---

def test_corte_por_punto_y_coma_y_pareja_de_corchetes():
    assert cs.corte_principal("Usa [el flag: activo] y decide; el resto sobra") == \
        "Usa [el flag: activo] y decide"


def test_corte_por_punto_y_coma_y_pareja_de_llaves():
    assert cs.corte_principal("El objeto {a: 1} se pasa entero; nada más") == \
        "El objeto {a: 1} se pasa entero"


def test_corte_por_raya_em_dash():
    assert cs.corte_principal("La regla vale — y aquí el detalle") == "La regla vale"


def test_corte_por_raya_en_dash():
    assert cs.corte_principal("La regla vale – y aquí el detalle") == "La regla vale"


def test_corte_por_parentesis_de_nivel_superior():
    assert cs.corte_principal("Mira (el caso: raro) y decide") == "Mira"


def test_corte_no_parte_un_enlace_markdown():
    """`[` sube el nivel y `]` lo baja, así que el `(` del destino parecía una apertura de nivel
    superior y el corte devolvía `[texto]` con la referencia colgando. El bullet del formato nuevo
    lleva `[ledger](…)`, así que no es hipotético."""
    assert cs.corte_principal("Añade el enlace [ledger](docs/x.md) al bullet y lo prueba") is None
    assert cs.corte_principal("Mira [el ADR](docs/adr/ADR-012.md): ahí está el motivo") == \
        "Mira [el ADR](docs/adr/ADR-012.md)"


def test_corte_no_parte_dentro_de_un_tramo_de_doble_acento_grave():
    """Los delimitadores de código se cuentan por RUNS (CommonMark): con el toggle de uno en uno,
    ``` ``a:b`` ``` quedaba abierto y cerrado antes del `:` y el corte entraba dentro."""
    assert cs.corte_principal("Cambia el flag ``a:b`` del script y ya está") is None
    assert cs.corte_principal("Cambia el flag ``a:b`` del script: y el detalle") == \
        "Cambia el flag ``a:b`` del script"


def test_resumen_max_es_200_con_literales():
    """El tope como LITERAL, no como `cs.RESUMEN_MAX`: una frase de 200 entra por `frase` y una de
    201 no. Antes ningún test distinguía 120 de 200 de 400."""
    def frase_de(n):
        return "Cambia " + "x" * (n - 8) + "."
    assert len(frase_de(200)) == 200 and len(frase_de(201)) == 201
    texto, camino, _av = cs.resumen(frase_de(200), None)
    assert (camino, texto) == ("frase", frase_de(200))
    _texto, camino, _av = cs.resumen(frase_de(201), None)
    assert camino == "titulo", camino


def test_corte_min_palabras_es_5_con_literales():
    """5 palabras de prosa se aceptan, 4 no. Antes ni 1 ni 9 rompían ningún test."""
    relleno = "y aquí viene el detalle largo que no cabe en el tope de doscientos caracteres " * 3
    assert cs.palabras_de_prosa("`x.py` deja de reventar al arrancar") == 5
    assert cs.palabras_de_prosa("`x.py` deja de reventar hoy") == 4
    texto, camino, _av = cs.resumen("`x.py` deja de reventar al arrancar: " + relleno, None)
    assert (camino, texto) == ("corte", "`x.py` deja de reventar al arrancar.")
    _texto, camino, _av = cs.resumen("`x.py` deja de reventar hoy: " + relleno, None)
    assert camino == "titulo", camino


def test_palabras_de_prosa_cuenta_dieresis_y_cedilla():
    """`lingüística` y `argüir` YA contaban antes de tocar nada (basta una racha de DOS letras de
    la clase, y las tienen en `ling` y `arg`). Lo que no contaba es una palabra cuyas únicas
    rachas incluyan `ü`/`ç`, así que la clase los incorpora y la cuenta deja de depender de dónde
    caen los signos."""
    assert cs.palabras_de_prosa("La lingüística y el argüir pesan mucho aquí") == 7
    assert cs.palabras_de_prosa("güe açi") == 2


def test_normaliza_cierra_la_negrita_que_el_corte_dejo_abierta():
    """CIERRA, no borra: el docstring, el nombre de este test y el ejemplo de la referencia decían
    «cierra» y la implementación quitaba los `**` (`los **27 scripts` → `Los 27 scripts.`)."""
    assert cs.normaliza_resumen("los **27 scripts") == "Los **27 scripts**."
    assert cs.normaliza_resumen("a **b** y **c") == "A **b** y **c**."
    assert cs.normaliza_resumen("los **27 scripts**") == "Los **27 scripts**."
    assert cs.normaliza_resumen("algo que pasó. **") == "Algo que pasó."   # nada detrás: colgante
    assert cs.normaliza_resumen("`ruta.py` cambia") == "`ruta.py` cambia."


def test_normaliza_no_cuenta_la_negrita_de_DENTRO_de_un_tramo_de_codigo(tmp_path):
    """Gaps del intento 2: `t.count("**")` sobre el texto CRUDO cuenta el `**` literal de un glob
    (`` `evals/**` ``), así que la cuenta salía impar y la función añadía un `**` huérfano — que
    abre una negrita sin cerrar y se come el resto del párrafo al renderizar, con exit 0 y sin
    aviso. La docstring de la función citaba justo ese literal como el que NO debe corromper, y su
    propio test de equilibrio ya quitaba los tramos de código antes de contar."""
    assert cs.normaliza_resumen("`evals/**` y el resto de piezas") == \
        "`evals/**` y el resto de piezas."
    assert cs.normaliza_resumen("Cubre `docs/*` y `evals/**` sin tocar nada") == \
        "Cubre `docs/*` y `evals/**` sin tocar nada."
    # la negrita que el corte SÍ dejó abierta se sigue cerrando
    assert cs.normaliza_resumen("los **27 scripts Python") == "Los **27 scripts Python**."
    # …y con las dos cosas a la vez: se cierra la de prosa, no la del glob
    assert cs.normaliza_resumen("los **27 de `evals/**` y") == "Los **27 de `evals/**` y**."
    # de punta a punta, por el camino `frase` (el que pasa por `normaliza_resumen`)
    root = proyecto(str(tmp_path),
                    tdesc="Cubre `evals/**` y los tres kits del plugin sin tocar nada más.")
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    linea = [l for l in en.split("\n") if "T-01" in l][0]
    assert linea.endswith("(`a.py`, `b.md`, `c.json`)"), linea
    assert "nada más**." not in linea, linea
    assert cs.sin_codigo(linea).count("**") % 2 == 0, linea


def test_sin_codigo_empareja_los_acentos_graves_por_RUNS():
    """Criterio único de «esto es código»: runs, como en `corte_principal()`. Un run sin pareja se
    deja tal cual — si se tragase el resto de la línea, esconderría los `**` de detrás."""
    assert cs.sin_codigo("a `x` b") == "a   b"
    assert cs.sin_codigo("a ``x`y`` b") == "a   b"              # el doble run no se abre de uno en uno
    assert cs.sin_codigo("un `acento suelto y **negrita**") == "un `acento suelto y **negrita**"
    assert cs.palabras_de_prosa("`docs/README.md` + `docs/en/README.md`") == 0


def test_normaliza_pone_mayuscula_inicial_pero_no_toca_codigo_ni_negrita():
    assert cs.normaliza_resumen("la cosa cambia").startswith("La cosa")
    assert cs.normaliza_resumen("`x.py` cambia").startswith("`x.py`")
    assert cs.normaliza_resumen("**x** cambia").startswith("**x**")


def test_frases_devuelve_las_n_primeras():
    assert cs.frases("Una. Dos. Tres.", 2) == "Una. Dos."
    assert cs.frases("Una sola sin punto final", 2) == "Una sola sin punto final"
    assert cs.frases("Usa `p. ej.` esto. Y otra. Y otra más.", 2) == "Usa `p. ej.` esto. Y otra."


def test_resumen_frases_max_es_2_con_literales():
    """El tope como literal: dos frases pasan enteras, tres se recortan a dos."""
    assert cs.frases("Una. Dos. Tres.", 2) == "Una. Dos."
    texto, camino, avisos = cs.resumen(None, "Una. Dos.")
    assert (camino, texto, avisos) == ("changelog", "Una. Dos.", [])
    texto, _camino, avisos = cs.resumen(None, "Una. Dos. Tres.")
    assert texto == "Una. Dos." and len(avisos) == 1 and "2 primeras frases" in avisos[0]


# ---------------------------------------------------------------------------------------------
# Cierre de los gaps del intento 1 (T-06): el campo vacío, la cola del ledger, los dos parsers,
# las abreviaturas, el placeholder de la plantilla y la continuación indentada.
# ---------------------------------------------------------------------------------------------

def test_campo_changelog_VACIO_no_publica_la_linea_siguiente(tmp_path):
    """`\\s*` tras los dos puntos, con `re.M`, se come el `\\n`: un `- **Changelog**:` sin texto
    capturaba la línea de debajo y la publicaba como resumen (`- **Estado**: completado`, un
    criterio, o una fila de tabla). Y era el caso que el diseño declara TOLERABLE, así que
    `ledger-lint` solo avisaba y `aviso_sin_changelog()` no podía ver que faltaba."""
    root = proyecto(str(tmp_path), tdesc=DESC_SOLO_RUTAS, tcampos="- **Changelog**:\n")
    r = run("--check", root=root)          # el único camino de detección, antes cegado
    assert "T-01" in r.stdout and "sin `- **Changelog**:`" in r.stdout, r.stdout
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    linea = [l for l in en.split("\n") if "T-01" in l][0]
    assert linea == "- **T-01 — Hacer la cosa** ([ledger](docs/roadmap/2026-05-05-demo/tasks.md))"
    assert "**Estado**" not in en and "Criterios" not in en and "| " not in linea


def test_campo_descripcion_VACIO_tampoco_publica_la_linea_siguiente(tmp_path):
    """El mismo `\\s*` estaba en el campo `Descripción` desde antes de esta iniciativa."""
    root = proyecto(str(tmp_path), tdesc="")
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    linea = [l for l in en.split("\n") if "T-01" in l][0]
    assert linea == "- **T-01 — Hacer la cosa** ([ledger](docs/roadmap/2026-05-05-demo/tasks.md))"
    assert "**Estado**" not in en


def test_el_bloque_de_la_tarea_termina_en_la_cola_del_ledger(tmp_path):
    """El split solo partía en `### T-XX`/`### Fase`, así que `## Notas de cierre` y todo lo que
    viene después quedaba DENTRO del bloque de la ÚLTIMA tarea: un `- **Changelog**:` citado ahí
    como ejemplo se publicaba como su resumen. `ledger-lint` ya cerraba en cualquier `^## `."""
    cola = ("\n---\n\n## Notas de cierre\n\n### Ejemplo de documentación del campo\n\n"
            "- **Changelog**: EJEMPLO DE DOCUMENTACIÓN — no es el resumen de ninguna tarea.\n")
    root = proyecto(str(tmp_path), tdesc=DESC_SOLO_RUTAS)
    p = os.path.join(root, "docs", "roadmap", "2026-05-05-demo", "tasks.md")
    open(p, "a", encoding="utf-8").write(cola)
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "EJEMPLO DE DOCUMENTACIÓN" not in en, "la cola del ledger no es de la última tarea"
    assert "- **T-01 — Hacer la cosa** ([ledger](" in en


@pytest.mark.skipif(not os.path.isfile(LEDGER_LINT), reason="paquete portable: sin el kit shared")
def test_el_patron_del_campo_es_el_canonico_del_kit():
    """Copia LITERAL de `CHANGELOG_FIELD_PATTERN` de `ledger-lint.py`: si divergen, este test lo
    caza antes de que los dos vuelvan a reconocer campos distintos."""
    ll = _mod(LEDGER_LINT, "ledger_lint_t")
    assert cs.CHANGELOG_FIELD_PATTERN == ll.CHANGELOG_FIELD_PATTERN


# Bloques de ledger REALES con los que se enfrentan los dos parsers. El test del intento 1
# comparaba las dos REGEX sobre una línea suelta, y por eso no cazó el caso 1 de aquí: con el campo
# indentado bajo `- **Verificación**:`, `cs.tareas()` lo publicaba y `ll.parse_ledger()` avisaba de
# «sin campo Changelog» sobre el MISMO ledger (el bug del intento 1 con los papeles invertidos).
BLOQUES_LEDGER = {
    "campo indentado bajo Verificación con sub-lista": """### T-01 — Una tarea

- **Descripción**: Hace algo.
- **Estado**: completado
- **Verificación** (`pytest`):
  - `pytest -q` → verde
  - **Changelog**: El script deja de reventar al arrancar sin config.

**Criterios de aceptación**
- [x] ok
""",
    "Verificación con sub-lista y campo DESPUÉS": """### T-01 — Una tarea

- **Descripción**: Hace algo.
- **Verificación**:
  - `pytest -q` → verde
  - `lint` → 0 errores
- **Changelog**: Una frase de release.
- **Estado**: completado

**Criterios de aceptación**
- [x] ok
""",
    "campo bajo `### Fase 2`": """## Fase 1 — Uno

### T-01 — Tarea uno

- **Descripción**: Hace algo.
- **Estado**: completado

### Fase 2 — subtítulo raro

- **Changelog**: ESTO NO ES DE T-01

**Criterios de aceptación**
- [x] ok
""",
    "`## Ejemplo` citado dentro de una valla de código": """### T-01 — Tarea uno

- **Descripción**: Hace algo con el ejemplo de abajo.

```markdown
## Ejemplo de sección
- **Changelog**: ESTE ES UN EJEMPLO, NO EL CAMPO
```

- **Changelog**: Este campo es el real y está debajo de la valla.
- **Estado**: completado

**Criterios de aceptación**
- [x] ok
""",
    "cola tras la última tarea": """### T-01 — Tarea uno

- **Descripción**: Hace algo.
- **Estado**: completado

**Criterios de aceptación**
- [x] ok

## Notas de cierre

- **Changelog**: EJEMPLO DE DOCUMENTACIÓN — no es el resumen de ninguna tarea.
""",
    "continuación indentada de prosa": """### T-01 — Tarea uno

- **Descripción**: Hace algo.
- **Changelog**: El script deja de reventar al arrancar sin config
  y en su lugar aplica los defaults documentados.
- **Estado**: completado

**Criterios de aceptación**
- [x] ok
""",
    "lista numerada indentada bajo el campo": """### T-01 — Tarea uno

- **Descripción**: Hace algo.
- **Changelog**: Una frase de release.
  1. `pytest -q`
  2. `ruff`
- **Estado**: completado

**Criterios de aceptación**
- [x] ok
""",
    "campo con dos espacios tras la viñeta": """### T-01 — Tarea uno

- **Descripción**: Hace algo.
-  **Changelog**: Dos espacios tras la viñeta.
- **Estado**: completado

**Criterios de aceptación**
- [x] ok
""",
    "campo VACÍO seguido de otro campo": """### T-01 — Tarea uno

- **Descripción**: Hace algo.
- **Changelog**:
- **Estado**: completado

**Criterios de aceptación**
- [x] ok
""",
    "campo que ES el placeholder de la plantilla": """### T-01 — Tarea uno

- **Descripción**: Hace algo.
- **Changelog**: {{qué cambia para quien USA el proyecto, en una frase}}
- **Estado**: completado

**Criterios de aceptación**
- [x] ok
""",
    "campo que CITA un placeholder": """### T-01 — Tarea uno

- **Descripción**: Hace algo.
- **Changelog**: Ahora la plantilla trae `{{qué cambia}}` en vez del párrafo largo.
- **Estado**: completado

**Criterios de aceptación**
- [x] ok
""",
    "sin campo": """### T-01 — Tarea uno

- **Descripción**: Hace algo.
- **Estado**: completado

**Criterios de aceptación**
- [x] ok
""",
}


@pytest.mark.skipif(not os.path.isfile(LEDGER_LINT), reason="paquete portable: sin el kit shared")
@pytest.mark.parametrize("nombre", sorted(BLOQUES_LEDGER))
def test_los_dos_PARSERS_leen_el_mismo_campo_en_un_bloque_real(nombre):
    """Enfrenta `changelog-sync.tareas()` contra `ledger-lint.parse_ledger()` sobre BLOQUES de
    ledger completos (con `Verificación` + sub-lista, `### Fase`, valla de código y cola tras la
    última tarea), que es donde discrepaban. Comparar dos regex sobre un `str` —lo que hacía el
    test del intento 1— no puede cazar ninguno de estos casos: el desacuerdo lo producían el
    RECORRIDO (`idx = nxt` de `parse_verificacion` se comía el campo) y el criterio de cierre del
    bloque, no el patrón del campo."""
    ll = _mod(LEDGER_LINT, "ledger_lint_t")
    texto = BLOQUES_LEDGER[nombre]
    mias = {t["id"]: t["changelog"] for t in cs.tareas(texto)}
    suyas = {t["id"]: t["changelog"] for t in ll.parse_ledger(texto)["tareas"]}
    assert set(mias) == set(suyas), (nombre, sorted(mias), sorted(suyas))
    for tid in mias:
        # `None` (campo ausente) y `""` (presente y vacío) se comparan por separado: los dos
        # degradan, pero el desglose de la deuda los distingue y los dos parsers deben coincidir.
        assert mias[tid] == suyas[tid], (nombre, tid, repr(mias[tid]), repr(suyas[tid]))
        # …y también coinciden en si el campo cuenta como ESCRITO (el criterio del placeholder)
        assert cs.es_placeholder(mias[tid]) == ll.es_placeholder(suyas[tid]), (nombre, tid)


@pytest.mark.skipif(not os.path.isfile(LEDGER_LINT), reason="paquete portable: sin el kit shared")
def test_los_dos_parsers_comparten_los_criterios_de_bloque_byte_a_byte():
    """Los tres criterios replicados: valla de código, campo del ledger y continuación de prosa.
    Si divergen, los dos parsers vuelven a leer bloques distintos."""
    ll = _mod(LEDGER_LINT, "ledger_lint_t")
    assert cs.VALLA_PATTERN == ll.VALLA_PATTERN
    assert cs.CAMPO_LEDGER_PATTERN == ll.CAMPO_LEDGER_PATTERN
    assert cs.CONTINUACION_PATTERN == ll.CONTINUACION_PATTERN
    for texto in BLOQUES_LEDGER.values():
        assert cs.sin_vallas(texto) == ll.sin_vallas(texto)
    for ln in ("  y sigue la frase", "  1. `pytest -q`", "  - `pytest -q` → verde",
               "  **Estado**: completado", "  - **Changelog**: x", "  | a | b |", "  > cita",
               "  <!-- comentario -->", "    codigo a cuatro espacios", "no indentado"):
        assert cs.es_continuacion(ln) == ll.es_continuacion(ln), ln


@pytest.mark.skipif(not os.path.isfile(LEDGER_LINT), reason="paquete portable: sin el kit shared")
def test_los_dos_parsers_del_campo_reconocen_LOS_MISMOS_casos():
    """El patrón del campo, línea a línea (se conserva del intento 1: sigue siendo cierto, pero NO
    es suficiente — el desacuerdo real estaba en el recorrido del bloque, ver el test de arriba)."""
    ll = _mod(LEDGER_LINT, "ledger_lint_t")
    casos = ["- **Changelog**: Frase.", "-  **Changelog**: Frase.", "  - **Changelog**: Frase.",
             "-\t**Changelog**: Frase.", "- **Changelog** : Frase.", "- **changelog**: Frase.",
             "- **Changelog**:", "- **Changelog**:   ", "- **Verificación**: no es este campo",
             "  - `pytest -q` → verde", "texto suelto"]
    for ln in casos:
        bloque = f"### T-01 — x\n\n- **Descripción**: algo.\n{ln}\n- **Estado**: completado\n"
        mio = cs.RE_CAMPO_CHANGELOG.search(bloque)
        suyo = ll.CHANGELOG_RE.match(ln)
        assert bool(mio) == bool(suyo), ln
        if mio:
            assert mio.group("txt").strip() == suyo.group("txt").strip(), ln


def test_frases_NUNCA_devuelve_mas_de_n_ni_el_texto_entero(tmp_path):
    """REGRESIÓN (gaps del intento 2): la guarda de abreviaturas descartaba el candidato, `frases()`
    agotaba su bucle y caía en `return s` — el texto ENTERO — así que el tope se incumplía en
    silencio y el aviso mentía. Medido antes del arreglo: un campo de tres frases con `etc.` al
    final de la segunda se publicaba COMPLETO y sin ningún aviso."""
    tres = ("Primera frase corta. Añade soporte para rutas, globs, etc. "
            "Tercera frase que NO debería publicarse.")
    texto, camino, avisos = cs.resumen(None, tres)
    assert camino == "changelog"
    assert "Tercera frase" not in texto, texto
    assert texto == "Primera frase corta. Añade soporte para rutas, globs, etc."
    assert avisos == ["campo `Changelog:` recortado a las 2 primeras frases (traía 3)"], avisos
    # …y el aviso dice la verdad también con cuatro frases (antes publicaba TRES diciendo «2»)
    cuatro = "Uno de prueba. Dos con etc. Tres de prueba. Cuatro de prueba."
    texto, _c, avisos = cs.resumen(None, cuatro)
    assert texto == "Uno de prueba. Dos con etc." and "(traía 4)" in avisos[0], (texto, avisos)
    # propiedad general: el tope se cumple SIEMPRE, cualquiera que sea la abreviatura de en medio
    for c in (tres, cuatro, "A. B. C. D.", "Usa `p. ej.` esto. Y otra. Y otra más.",
              "Cuesta aprox. Diez euros. Y sube. Y sube más.",
              "Ver cap. Tercero del libro. Luego el cuarto. Y el quinto."):
        assert len(cs.separa_frases(cs.frases(c, 2))) <= 2, c
        assert len(cs.separa_frases(cs.frases(c, 1))) <= 1, c
    # y de punta a punta: lo publicado no lleva la tercera frase
    root = proyecto(str(tmp_path), tcampos=f"- **Changelog**: {tres}\n")
    r = run(root=root)
    assert r.returncode == 0 and "Tercera frase" not in \
        open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read(), r.stdout


def test_etc_cierra_frase_como_ee_uu_no_lo_hace():
    """Contrato explícito de la guarda: cubre abreviaturas de EN MEDIO de la frase (`Sr. Pérez`,
    `vs.`, `p. ej.`), no las que la TERMINAN. `etc.` termina frase en español técnico —igual que
    `EE. UU.`— así que está FUERA de `ABREVIATURAS`; tenerlo dentro es lo que rompía el tope."""
    assert "etc." not in cs.ABREVIATURAS
    assert cs.separa_frases("Rutas, globs, etc. Y una segunda.") == \
        ["Rutas, globs, etc.", "Y una segunda."]
    for ab in ("sr.", "vs.", "p. ej.", "pág.", "ee."):
        assert ab in cs.ABREVIATURAS, ab
    assert cs.separa_frases("Compara el hook vs. Claude Code nativo.") == \
        ["Compara el hook vs. Claude Code nativo."]


def test_una_frase_que_SI_termina_en_ee_uu_sigue_terminando():
    """`ee.` está en la guarda para no partir «EE. UU.»; `uu.` NO, porque una frase que acaba en
    «EE. UU.» acaba ahí y ese caso es el frecuente. Contrato explícito, no accidente."""
    assert cs.frases("Funciona en EE. UU. Ahora también en Canadá. Y en México.", 2) == \
        "Funciona en EE. UU. Ahora también en Canadá."
    assert cs.primera_frase("Solo en EE. UU. de momento. Luego más.") == "Solo en EE. UU. de momento."


def test_placeholder_de_plantilla_sin_sustituir_no_llega_al_changelog(tmp_path):
    """La plantilla de tarea trae el campo con un `{{…}}` que por diseño se rellena MÁS TARDE, y
    nada lo detectaba: se publicaba literal (y si medía menos de 200 caracteres, sin un aviso)."""
    ph = "{{OPCIONAL, lo rellena quien CIERRA la tarea: una frase con qué cambia}}"
    root = proyecto(str(tmp_path), tdesc=DESC_SOLO_RUTAS, tcampos=f"- **Changelog**: {ph}\n")
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "{{" not in en and "OPCIONAL" not in en
    assert "- **T-01 — Hacer la cosa** ([ledger](" in en, "degrada como si no hubiera campo"
    assert "sin sustituir" in r.stdout and "T-01" in r.stdout, r.stdout


# Tabla ÚNICA del criterio de placeholder: la comparten los dos scripts y el test los enfrenta.
# `escrito` = texto de una persona que CITA un `{{…}}`; `plantilla` = el campo sin sustituir.
PLACEHOLDER_ESCRITO = [
    "Ahora la plantilla del planner trae `{{qué cambia para quien USA el proyecto}}` en vez del "
    "párrafo largo.",
    "El generador acepta {{slug}} y {{fecha}} en el nombre de la sección.",
    "El aviso cita `{{…}}` para que se vea qué falta.",
    "Documenta `{{slug}}`, `{{fecha}}` y `{{cat}}` en la plantilla de subsección.",
    "Una frase normal, sin llaves de ningún tipo.",
]
PLACEHOLDER_PLANTILLA = [
    "{{qué cambia para quien USA el proyecto, en una frase}}",
    "{{OPCIONAL, lo rellena quien CIERRA la tarea: una frase con qué cambia}}",
    "  {{sin sustituir}}  ",
    "{{uno}} {{dos}}",
    "**{{en negrita y sin sustituir}}**",
]


def test_un_placeholder_CITADO_es_texto_humano_y_se_publica(tmp_path):
    r"""Gaps del intento 2: `RE_PLACEHOLDER = \{\{.*?\}\}` no distinguía una plantilla sin
    sustituir de una CITA, y en un repo cuyas plantillas van llenas de `{{…}}` eso descartaba texto
    escrito a mano — pérdida silenciosa, justo lo que la escalera declara no hacer. Es además la
    frase que T-06 escribiría sobre su propio cambio. Criterio nuevo: «el campo ES el placeholder»
    (quitando código y bloques `{{…}}` no queda prosa propia), no «lo menciona»."""
    for escrito in PLACEHOLDER_ESCRITO:
        assert not cs.es_placeholder(escrito), escrito
        texto, camino, avisos = cs.resumen("Una descripción cualquiera.", escrito)
        assert (texto, camino, avisos) == (escrito, "changelog", []), escrito
    for plantilla in PLACEHOLDER_PLANTILLA:
        assert cs.es_placeholder(plantilla), plantilla
        _t, camino, avisos = cs.resumen(None, plantilla)
        assert camino == "titulo" and any("sin sustituir" in a for a in avisos), plantilla
    # de punta a punta: el texto que cita el placeholder SÍ se publica
    root = proyecto(str(tmp_path), tcampos=f"- **Changelog**: {PLACEHOLDER_ESCRITO[0]}\n")
    r = run(root=root)
    assert r.returncode == 0 and "sin sustituir" not in r.stdout, r.stdout
    assert PLACEHOLDER_ESCRITO[0] in open(os.path.join(root, "CHANGELOG.md"),
                                          encoding="utf-8").read()


@pytest.mark.skipif(not os.path.isfile(LEDGER_LINT), reason="paquete portable: sin el kit shared")
def test_el_criterio_de_placeholder_es_el_MISMO_en_los_dos_scripts():
    """Mismo patrón (byte a byte) y misma DECISIÓN sobre la misma tabla: si divergen, un campo que
    el linter da por escrito lo descarta el generador (o al revés) en silencio."""
    ll = _mod(LEDGER_LINT, "ledger_lint_t")
    assert cs.PLACEHOLDER_PATTERN == ll.PLACEHOLDER_PATTERN
    assert cs.PLACEHOLDER_RELLENO == ll.PLACEHOLDER_RELLENO
    for caso in PLACEHOLDER_ESCRITO + PLACEHOLDER_PLANTILLA + ["", "   ", "{{", "}}", "`{{x}}`"]:
        assert cs.es_placeholder(caso) == ll.es_placeholder(caso), caso
        assert cs.sin_codigo(caso) == ll.sin_codigo(caso), caso


def test_un_placeholder_en_la_DESCRIPCION_tampoco_llega_al_changelog(tmp_path):
    """MINOR 11: la guarda cubría solo `Changelog:`, así que
    `resumen("{{Qué hay que hacer y por qué, en 1-3 frases.}}", None)` publicaba el placeholder de
    la plantilla LITERAL, sin aviso y por el camino `frase`."""
    ph = "{{Qué hay que hacer y por qué, en 1-3 frases.}}"
    texto, camino, avisos = cs.resumen(ph, None)
    assert (texto, camino) == ("", "titulo"), (texto, camino)
    assert any("Descripción" in a and "sin sustituir" in a for a in avisos), avisos
    root = proyecto(str(tmp_path), tdesc=ph)
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "{{" not in en and "- **T-01 — Hacer la cosa** ([ledger](" in en, en
    assert "T-01: campo `Descripción:` sin sustituir" in r.stdout, r.stdout


def test_la_plantilla_de_tarea_del_planner_trae_un_placeholder_CORTO():
    """El placeholder viaja al CHANGELOG si nadie lo sustituye, así que su longitud importa: por
    debajo del tope del resumen no saltaba ni el aviso de longitud."""
    plantilla = os.path.join(REPO, "agent-kits", "planner", "templates", "tasks.md")
    if not os.path.isfile(plantilla):
        pytest.skip("paquete portable: sin el kit del planner")
    texto = open(plantilla, encoding="utf-8").read()
    m = cs.RE_CAMPO_CHANGELOG.search(texto)
    assert m, "la plantilla de tarea debe traer el campo `- **Changelog**:`"
    campo = m.group("txt").strip()
    assert cs.RE_PLACEHOLDER.fullmatch(campo), campo
    assert len(campo) <= 80, f"{len(campo)} caracteres: el placeholder debe ser una pista corta"


def test_campo_multilinea_absorbe_la_continuacion_indentada(tmp_path):
    """Una persona parte una frase larga en dos líneas y el Markdown la lee como un párrafo. Antes
    la continuación se perdía en silencio y el bullet se quedaba sin punto final (el camino 1 no
    pasa por `normaliza_resumen()` a propósito: el texto es de una persona)."""
    campo = ("- **Changelog**: El script deja de reventar al arrancar sin config\n"
             "  y en su lugar aplica los defaults documentados.\n")
    root = proyecto(str(tmp_path), tcampos=campo)
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    esperado = ("- **T-01 — Hacer la cosa** El script deja de reventar al arrancar sin config "
                "y en su lugar aplica los defaults documentados.")
    assert esperado in en, [l for l in en.split("\n") if "T-01" in l]


MUTANTES = os.path.join(HERE, "mutantes.py")


@pytest.mark.skipif(not os.path.isfile(MUTANTES), reason="sin el arnés de mutantes")
def test_el_arnes_de_mutantes_esta_al_dia():
    """La campaña completa NO corre en `pytest -q` (un pytest por mutante, ~2 min). Lo que sí corre
    es esta comprobación barata: que cada `busca` de la lista siga apareciendo EXACTAMENTE UNA VEZ
    en su fichero, y que cada mutante tenga motivo. Un mutante que dejó de aplicarse en silencio
    contaría como «muerto» sin haber probado nada — que es cómo se podre un arnés, y es la razón
    por la que «14 de 25 → 0 de 40» no reproducía. Ejecuta la campaña con
    `python3 skills/changelog-sync/scripts/mutantes.py`."""
    mut = _mod(MUTANTES, "mutantes_t")
    problemas = mut.comprueba_lista()
    assert problemas == [], problemas
    assert len(mut.MUTANTES) >= 50, f"solo {len(mut.MUTANTES)} mutantes en la lista"


@pytest.mark.skipif(not os.path.isdir(os.path.join(REPO, "docs", "roadmap")),
                    reason="paquete portable: sin el roadmap del repo")
def test_los_bullets_reales_del_repo_estan_equilibrados_en_markdown():
    """Chequeo adversarial que el ledger de la iniciativa hizo a mano («0 problemas») y nadie
    fijaba: sobre los bullets de TODOS los ledgers cerrados del repo, acentos graves por runs
    pareados, `**` pares, parejas equilibradas y ningún `…` que no venga del ledger. Los `**` y los
    paréntesis DENTRO de un tramo de código son literales (`` `evals/**` `` es un glob), así que se
    quitan antes de contar: era el falso positivo del detector, no un bullet roto. El criterio de
    «quitar los tramos de código» es ahora el del propio script (`cs.sin_codigo`), no una copia
    local: la copia local es lo que hizo que este test tuviera razón y `normaliza_resumen()` no."""
    regs, _av = cs.ledgers(REPO)
    assert regs, "el repo tiene ledgers cerrados"
    for _f, slug, ledger, _fm, ts in regs:
        lineas, _caminos, _avisos = cs.bullets(ts, ledger)
        for t, ln in zip(ts, lineas):
            runs = re.findall(r"`+", ln)
            for r in set(runs):
                assert runs.count(r) % 2 == 0, f"{slug}/{t['id']}: `{r}` desparejado en {ln}"
            prosa = cs.sin_codigo(ln)          # MISMO criterio que la función que se prueba
            assert prosa.count("**") % 2 == 0, f"{slug}/{t['id']}: `**` desparejado en {ln}"
            for a, c in (("(", ")"), ("[", "]"), ("«", "»")):
                assert prosa.count(a) == prosa.count(c), f"{slug}/{t['id']}: {a}{c} en {ln}"
            fuente = (t["changelog"] or "") + (t["desc"] or "") + t["titulo"]
            assert ln.count("…") <= fuente.count("…"), f"{slug}/{t['id']}: `…` añadido en {ln}"



def main():
    sys.exit(pytest.main([os.path.abspath(__file__), "-q"]))


if __name__ == "__main__":
    main()
