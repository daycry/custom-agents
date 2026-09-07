#!/usr/bin/env python3
"""Tests de `agent-kits/shared/knowledge-find.py` — las tres capas de recuperación de la memoria
técnica (iniciativa `memory-retrieval`, Fase 1: T-01 capa 1 · T-02 `--related` · T-03 `--show` +
índice FTS5 reconstruible).

Dos planos, a propósito:
  - un corpus SINTÉTICO en `tmp_path` para lo estructural (formato, orden, filtros, grafo, los tres
    estados del índice y las dos degradaciones): la regla se prueba sin depender del repo;
  - el `docs/knowledge/` REAL para las cifras que la spec fija con línea base (9 entradas de
    «Estimación / calibración», `GOT-005` primero para «consola windows cp1252», `ADR-012` la más
    grande, `--related ADR-010` ≤ 1.600 caracteres).

Ningún test usa red, `claude` ni una clave. Ejecutar: python3 -m pytest -q tests/test_knowledge_find.py
"""
import importlib.util
import json
import os
import subprocess
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "agent-kits", "shared", "knowledge-find.py")
KNOWLEDGE_REAL = os.path.join(ROOT, "docs", "knowledge")


def _cargar():
    spec = importlib.util.spec_from_file_location("knowledge_find", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kf = _cargar()


def run(*args, cwd=None, env_extra=None):
    """Lanza el script como lo haría un agente (`python3 <ruta> …`); decodifica UTF-8 (GOT-005)."""
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run([sys.executable, SCRIPT, *args], cwd=cwd or ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return r.returncode, r.stdout, r.stderr


# --------------------------------------------------------------- corpus sintético

def _fm(**kv):
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in kv.items()) + "---\n"


ENTRADAS = {
    # ADR: el `area` NO está en el fichero — solo en la fila del índice (como los 12 ADR reales).
    "adr/ADR-001-guardia-solo-agente.md": _fm(
        id="ADR-001", titulo="Un hook de guardia (deny) solo con alcance de agente",
        estado="aceptada (validada: usuario, 2026-01-02)", fecha="2026-01-02", iniciativa="demo-uno")
        + "\n# ADR-001: Un hook de guardia solo con alcance de agente\n\n## Contexto\n\nUn deny global rompería "
          "a planner y evaluator, que escriben en docs/roadmap legítimamente.\n\n## Decisión\n\nEl deny va en el "
          "frontmatter hooks del agente.\n",
    "adr/ADR-002-consola-ascii.md": _fm(
        id="ADR-002", titulo="Modo ASCII para consolas sin UTF-8",
        estado="obsoleta (sustituida por ADR-003)", fecha="2026-01-03", iniciativa="demo-dos", sucesor="ADR-003")
        + "\n# ADR-002: Modo ASCII\n\n## Decisión\n\nLos scripts ofrecen un modo ASCII para la consola.\n",
    "adr/ADR-003-reconfigurar-utf8.md": _fm(
        id="ADR-003", titulo="Reconfigurar los tres streams a UTF-8 al arrancar",
        estado="aceptada (validada: revisión de dos lentes, 2026-01-04, intento 1)", fecha="2026-01-04",
        iniciativa="demo-dos", sustituye="ADR-002")
        + "\n# ADR-003: Reconfigurar a UTF-8\n\n## Decisión\n\nCada script reconfigura stdin, stdout y stderr; "
          "no hay modo ASCII.\n",
    "gotchas/GOT-001-consola-windows-cp1252.md": _fm(
        id="GOT-001", tipo="gotcha", area="Scripts / consola y codificación",
        estado="aceptada (validada: usuario, 2026-01-05)",
        fuente="docs/roadmap/2026-01-05-demo-dos/tasks.md (T-01, traceback del usuario)")
        + "\n## En la consola de Windows (cp1252) revienta el hijo del pipe\n\n- **Síntoma:** UnicodeEncodeError "
          "al imprimir un símbolo en la consola cp1252 de Windows.\n- **Causa:** Python cae al codepage del "
          "locale.\n- **Qué hacer:** reconfigurar los streams (ADR-003).\n",
    "lessons/LES-001-evaluator-revision-cara.md": _fm(
        id="LES-001", tipo="leccion", area="Estimación / calibración",
        estado="aceptada (validada: revisión de dos lentes, 2026-01-06, intento 2)",
        fuente="2026-01-01-demo-uno/retro.md#aprendizajes")
        + "\n## evaluator\n\n- **El coste real se va en la revisión, no en escribir.** Presupuesta la revisión "
          "como línea propia.\n",
    "lessons/LES-002-evaluator-medir-cambia.md": _fm(
        id="LES-002", tipo="leccion", area="Estimación / calibración", estado="propuesta",
        fuente="2026-01-01-demo-uno/retro.md#estimado-vs-real")
        + "\n## evaluator\n\n- **Medir cambia el diagnóstico.** Calibrar con datos reales mueve las cifras.\n",
}

README = textwrap.dedent("""\
    # `docs/knowledge/` — memoria técnica del proyecto (fixture)

    Texto de cabecera con una barra | suelta que no es tabla.

    ## Índice

    | Entrada | ID | Tipo | Área | Estado | Fuente |
    |---|---|---|---|---|---|
    | [`lessons/LES-001-evaluator-revision-cara.md`](lessons/LES-001-evaluator-revision-cara.md) — "El coste real se va en la revisión, no en escribir." | LES-001 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-01-06, intento 2) | `2026-01-01-demo-uno/retro.md#aprendizajes` |
    | [`lessons/LES-002-evaluator-medir-cambia.md`](lessons/LES-002-evaluator-medir-cambia.md) — "Medir cambia el diagnóstico." | LES-002 | Lección | Estimación / calibración | propuesta | `2026-01-01-demo-uno/retro.md#estimado-vs-real` |
    | [`adr/ADR-001-guardia-solo-agente.md`](adr/ADR-001-guardia-solo-agente.md) | ADR-001 | ADR | Hooks / implementer | aceptada (validada: usuario, 2026-01-02) | `2026-01-02-demo-uno/tasks.md` |
    | [`adr/ADR-002-consola-ascii.md`](adr/ADR-002-consola-ascii.md) — modo ASCII para consolas sin UTF-8 | ADR-002 | ADR | Scripts / consola y codificación | obsoleta (sustituida por ADR-003) | `2026-01-05-demo-dos/tasks.md` |
    | [`adr/ADR-003-reconfigurar-utf8.md`](adr/ADR-003-reconfigurar-utf8.md) — reconfigurar `stdin`/`stdout`/`stderr` a UTF-8 al arrancar; sin modo ASCII | ADR-003 | ADR | Scripts / consola y codificación | aceptada (validada: revisión de dos lentes, 2026-01-04, intento 1) | `2026-01-05-demo-dos/tasks.md` (T-02) |
    | [`gotchas/GOT-001-consola-windows-cp1252.md`](gotchas/GOT-001-consola-windows-cp1252.md) — imprimir símbolos sin reconfigurar revienta con `UnicodeEncodeError` en la consola cp1252<!--m:base=1--> | GOT-001 | Gotcha | Scripts / consola y codificación | aceptada (validada: usuario, 2026-01-05) | `2026-01-05-demo-dos/tasks.md` (T-01) |

    Texto de cola.
    """)


@pytest.fixture
def proyecto(tmp_path):
    """Un proyecto consumidor de mentira: `docs/knowledge/` con 6 entradas y `.claude/`."""
    kn = tmp_path / "docs" / "knowledge"
    for rel, contenido in ENTRADAS.items():
        p = kn / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")
    (kn / "README.md").write_text(README, encoding="utf-8")
    (tmp_path / ".claude").mkdir()
    return tmp_path


# =============================================================== T-01 · capa 1: consulta → aciertos compactos

def test_el_script_lleva_el_snippet_de_consola_al_arrancar():
    """GOT-005 / CONVENTIONS 8: imprime `·` y áreas con acentos → reconfigura los tres streams."""
    src = open(SCRIPT, encoding="utf-8").read()
    assert 'reconfigure(encoding="utf-8", errors="replace")' in src
    assert "for _s in (sys.stdin, sys.stdout, sys.stderr):" in src


def test_area_normalizada_casa_con_acentos_barras_y_por_token(proyecto):
    """`--area estimacion` tiene que encontrar «Estimación / calibración» (21 áreas para 31 entradas,
    casi todas singleton y con `/` y acentos: una comparación exacta no enrutaría nada)."""
    for area in ("estimacion", "Estimación", "ESTIMACION", "calibracion", "estimacion calibracion", "estim"):
        code, out, err = run("--area", area, "--json", "--root", str(proyecto))
        assert code == 0, err
        ids = [a["id"] for a in json.loads(out)["aciertos"]]
        assert ids == ["LES-001", "LES-002"], (area, ids)


def test_cada_acierto_es_una_linea_compacta_con_el_estado_delante(proyecto):
    code, out, err = run("--area", "estimacion", "--root", str(proyecto))
    assert code == 0, err
    lineas = out.rstrip("\n").split("\n")
    assert len(lineas) == 2
    for l in lineas:
        assert len(l) <= kf.LINEA_MAX == 120, l
        partes = l.split(" · ")
        assert len(partes) == 5, f"esperaba `ID · estado · área · titular · ruta`: {l!r}"
    id_, estado, area, titular, ruta = lineas[0].split(" · ")
    assert id_ == "LES-001"
    assert estado == "aceptada", "el estado va DELANTE, y compacto (doctrina/indicio/obsoleta)"
    assert area == "Estimación / calibración", "el área sale tal cual está escrita, no normalizada"
    assert titular.startswith("El coste real se va en la revisión")
    assert ruta.startswith("lessons/LES-001-"), "la ruta es relativa a docs/knowledge/"
    assert lineas[1].split(" · ")[1] == "propuesta", "un indicio se distingue de la doctrina en la propia línea"


def test_la_consulta_libre_ordena_por_relevancia(proyecto):
    code, out, err = run("consola windows cp1252", "--limit", "5", "--root", str(proyecto))
    assert code == 0, err
    lineas = out.rstrip("\n").split("\n")
    assert lineas[0].startswith("GOT-001 · "), lineas
    assert len(lineas) <= 5
    # los ADR de consola también salen (misma área, «consola» en el titular), detrás del gotcha
    ids = [l.split(" · ")[0] for l in lineas]
    assert "ADR-003" in ids and "ADR-002" in ids
    assert "LES-001" not in ids, "una lección de estimación no casa con ninguna palabra de la consulta"


def test_el_area_de_un_adr_sale_del_indice_porque_no_vive_en_su_fichero(proyecto):
    code, out, err = run("--area", "hooks", "--json", "--root", str(proyecto))
    assert code == 0, err
    aciertos = json.loads(out)["aciertos"]
    assert [a["id"] for a in aciertos] == ["ADR-001"]
    assert aciertos[0]["area"] == "Hooks / implementer"
    assert aciertos[0]["titular"] == "Un hook de guardia (deny) solo con alcance de agente", \
        "sin descripción en la fila del índice, el titular es el `titulo` del frontmatter"


def test_tipo_filtra_y_admite_sinonimos(proyecto):
    for tipo in ("gotcha", "gotchas", "got", "GOTCHA"):
        code, out, _ = run("--tipo", tipo, "--json", "--root", str(proyecto))
        assert code == 0 and [a["id"] for a in json.loads(out)["aciertos"]] == ["GOT-001"], tipo
    for tipo in ("lesson", "lessons", "leccion", "lección", "les"):
        code, out, _ = run("--tipo", tipo, "--json", "--root", str(proyecto))
        assert code == 0 and [a["id"] for a in json.loads(out)["aciertos"]] == ["LES-001", "LES-002"], tipo
    code, out, _ = run("--tipo", "adr", "--json", "--root", str(proyecto))
    assert [a["id"] for a in json.loads(out)["aciertos"]] == ["ADR-001", "ADR-003", "ADR-002"], \
        "sin consulta libre: doctrina (aceptada) antes que obsoleta, y por ID dentro de cada estado"


def test_limit_recorta_pero_total_dice_cuantos_habia(proyecto):
    code, out, _ = run("--tipo", "adr", "--limit", "1", "--json", "--root", str(proyecto))
    data = json.loads(out)
    assert code == 0 and len(data["aciertos"]) == 1 and data["total"] == 3


def test_sin_carpeta_o_sin_aciertos_cero_lineas_y_exit_0(tmp_path, proyecto):
    # sin docs/knowledge/: ni una línea de relleno (no gastar contexto para decir que no hay nada)
    code, out, err = run("--area", "estimacion", "--root", str(tmp_path / "vacio"))
    assert (code, out) == (0, ""), (code, out, err)
    # con carpeta pero sin aciertos: igual
    code, out, err = run("--area", "no-existe-esta-area", "--root", str(proyecto))
    assert (code, out) == (0, ""), (code, out, err)
    code, out, err = run("zzzz qqqq", "--root", str(proyecto))
    assert (code, out) == (0, ""), (code, out, err)
    # y en JSON, la estructura sigue siendo la misma (los consumidores no tienen que adivinar)
    code, out, _ = run("--area", "no-existe-esta-area", "--json", "--root", str(proyecto))
    data = json.loads(out)
    assert code == 0 and data["aciertos"] == [] and data["total"] == 0


def test_el_esquema_json_es_contrato(proyecto):
    """Lo consumen `task-brief.py` (T-05) y `session-context.sh` (T-06): cambiarlo rompe dos piezas."""
    code, out, _ = run("--area", "estimacion", "--json", "--root", str(proyecto))
    data = json.loads(out)
    assert set(data) - {"indice_motivo"} == {"version", "indice", "consulta", "total", "aciertos"}, \
        "`indice_motivo` es la única clave opcional (solo con `indice: degradado`)"
    assert data["version"] == 1
    assert data["indice"] in {"construido", "reconstruido", "cache", "degradado"}
    assert data["consulta"] == {"texto": "", "area": "estimacion", "tipo": "", "limit": 10}
    a = data["aciertos"][0]
    assert list(a) == ["id", "tipo", "estado", "estado_detalle", "area", "titular", "ruta", "linea",
                       "puntuacion", "iniciativa", "fecha"]
    assert a["ruta"] == "docs/knowledge/lessons/LES-001-evaluator-revision-cara.md", "ruta relativa al proyecto"
    assert a["linea"].split(" · ")[0] == "LES-001" and len(a["linea"]) <= 120
    assert a["estado"] == "aceptada" and a["estado_detalle"].startswith("aceptada (validada:")
    assert a["tipo"] == "leccion" and a["iniciativa"] == "demo-uno"


def test_el_root_se_resuelve_por_claude_project_dir_y_luego_por_cwd(proyecto, tmp_path):
    code, out, _ = run("--area", "estimacion", cwd=str(tmp_path), env_extra={"CLAUDE_PROJECT_DIR": str(proyecto)})
    assert code == 0 and out.count("\n") == 2
    code, out, _ = run("--area", "estimacion", cwd=str(proyecto))
    assert code == 0 and out.count("\n") == 2


def test_linea_compacta_nunca_pasa_de_120_ni_pierde_el_id_ni_la_ruta():
    """Con un titular y un área desmedidos, se recorta el titular (en palabra, con «…»), luego la ruta
    se abrevia a `carpeta/ID-…` (el detalle se abre por ID con --show) y por último el área."""
    e = {"id": "LES-099", "estado": "aceptada", "area": "Proceso / desarrollo del plugin " * 3,
         "titular": "Una lección con un titular interminable que no cabe en ninguna línea razonable " * 3,
         "ruta_corta": "lessons/LES-099-" + "x" * 90 + ".md"}
    l = kf.linea_compacta(e)
    assert len(l) <= 120 and l.startswith("LES-099 · aceptada · ") and " · lessons/LES-099-…" in l
    assert l.count(" · ") == 4
    corto = {"id": "GOT-001", "estado": "aceptada", "area": "Tests / CI", "titular": "corto",
             "ruta_corta": "gotchas/GOT-001-corto.md"}
    assert kf.linea_compacta(corto) == "GOT-001 · aceptada · Tests / CI · corto · gotchas/GOT-001-corto.md"


# --------------------------------------------------------------- las cifras sobre el corpus REAL

@pytest.fixture(scope="module")
def real():
    if not os.path.isdir(KNOWLEDGE_REAL):
        pytest.skip("no hay docs/knowledge/ real")
    return ROOT


def _filas_de_area_en_el_indice(area_literal):
    with open(os.path.join(KNOWLEDGE_REAL, "README.md"), encoding="utf-8") as f:
        return sum(1 for l in f if l.startswith("|") and f"| {area_literal} |" in l)


def test_ca01_area_estimacion_devuelve_las_9_entradas_en_menos_de_1200_caracteres(real):
    esperadas = _filas_de_area_en_el_indice("Estimación / calibración")
    assert esperadas == 9, "la línea base de la spec (CA-01) son 9; si el corpus cambió, revisa la cifra"
    code, out, err = run("--area", "estimacion", "--json")
    assert code == 0, err
    data = json.loads(out)
    ids = [a["id"] for a in data["aciertos"]]
    assert ids == [f"LES-00{i}" for i in range(1, 10)], ids
    assert all(a["area"] == "Estimación / calibración" for a in data["aciertos"])
    # la salida humana (lo que se inyecta) cabe en el tope de la spec: ≤ 300 tokens ≈ 1.200 caracteres
    code, out, _ = run("--area", "estimacion")
    assert code == 0 and len(out) <= 1200, len(out)
    assert out.count("\n") == 9


def test_ca02_consola_windows_cp1252_pone_got005_primero(real):
    code, out, err = run("consola windows cp1252", "--limit", "5")
    assert code == 0, err
    lineas = out.rstrip("\n").split("\n")
    assert lineas[0].startswith("GOT-005 · aceptada · "), lineas
    assert len(lineas) <= 5
    assert all(len(l) <= 120 for l in lineas), [len(l) for l in lineas]


def test_todas_las_entradas_reales_caben_en_120_caracteres_por_linea(real):
    code, out, _ = run("--limit", "0")
    lineas = out.rstrip("\n").split("\n")
    n_ficheros = sum(len([f for f in os.listdir(os.path.join(KNOWLEDGE_REAL, d)) if f.endswith(".md")])
                     for d in ("adr", "gotchas", "lessons"))
    assert len(lineas) == n_ficheros, "`--limit 0` = sin tope: una línea por entrada del corpus"
    largas = [l for l in lineas if len(l) > 120]
    assert not largas, largas
    assert all(l.count(" · ") == 4 for l in lineas)


def test_area_inexistente_sobre_el_corpus_real_no_imprime_nada(real):
    code, out, err = run("--area", "no-existe-esta-area")
    assert (code, out) == (0, ""), (code, out, err)
