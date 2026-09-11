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
import re
import json
import os
import shutil
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
    assert set(data) - {"indice_motivo"} == {"version", "indice", "corpus", "consulta", "total", "aciertos"}, \
        "`indice_motivo` es la única clave opcional (solo con `indice: degradado`)"
    assert data["version"] == 1 and data["corpus"] == "proyecto"          # `corpus`/`origen`: T-16 (la doctrina se distingue)
    assert data["indice"] in {"construido", "reconstruido", "cache", "degradado"}
    assert data["consulta"] == {"texto": "", "area": "estimacion", "tipo": "", "limit": 10}
    a = data["aciertos"][0]
    assert list(a) == ["id", "tipo", "estado", "estado_detalle", "area", "titular", "ruta", "linea",
                       "puntuacion", "iniciativa", "fecha", "origen"]
    assert a["origen"] == "proyecto"
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


# --------------------------------------------------------------- consulta libre: solo puntúan los tokens con contenido
#
# Revisión de dos lentes, intento 1 (IMPORTANT 1): la consulta libre no filtraba stopwords y puntuaba las
# 32 entradas con «cual es el ratio de tokens por hora que uso para estimar» (las 9 lecciones de estimación
# en las posiciones 15-32: con `--limit 10` no llegaba ninguna), «de» traía 10 líneas y «quiero saber si el
# pato vuela hacia marte» las 32. Solo devolvía 0 con tokens inventados, que era el único caso probado.

def test_una_sola_lista_de_stopwords_para_los_tres_caminos():
    """El criterio vive UNA vez: `STOPWORDS` la usan la consulta libre, el enrutado y «misma área»."""
    src = open(SCRIPT, encoding="utf-8").read()
    assert "CONTEXTO_STOPWORDS" not in src and "AREA_STOPWORDS" not in src, "quedó una lista paralela"
    assert isinstance(kf.STOPWORDS, frozenset) and len(kf.STOPWORDS) > 150
    # ES + EN, normalizadas como salen de `tokens()` (sin acentos): las dos lenguas de la doc del repo
    assert {"de", "el", "cual", "es", "que", "para", "the", "of", "what", "is", "how"} <= kf.STOPWORDS
    assert not {"estimacion", "tokens", "hooks", "cp1252", "ci", "qa"} & kf.STOPWORDS, "contenido, no relleno"
    assert kf.tokens_consulta("cual es el ratio de tokens por hora que uso para estimar") == ["ratio", "token", "hora", "estim"]
    assert kf.tokens_consulta("de") == [] and kf.tokens_consulta("cual es el") == []
    assert kf.claves_enrutado("Presupuestar la estimación de la iniciativa")[0] == ["presupuestar", "estimacion"]
    assert kf._area_significativa("Proceso / desarrollo del plugin") == {"proceso", "desarrollo", "plugin"}


def test_raiz_reduce_la_misma_palabra_en_otra_forma_a_la_misma_raiz():
    assert kf.raiz("estimar") == kf.raiz("estimacion") == kf.raiz("estimaciones") == "estim"
    assert kf.raiz("tokens") == "token" and kf.raiz("horas") == "hora" and kf.raiz("hooks") == "hook"
    assert kf.raiz("cp1252") == "cp1252" and kf.raiz("hora") == "hora", "sin sufijo que quitar, intacto"
    assert kf.raiz("es") == "es" and kf.raiz("tres") == "tres", f"la raíz conserva ≥ {kf.RAIZ_MIN} caracteres"
    # la raíz casa por PREFIJO con el campo, igual que `"raiz"*` en la FTS5
    assert kf.casa("estim", kf.tokens("Estimación / calibración"))
    assert kf.casa("token", kf.tokens("tokens facturables por hora"))


def test_consulta_de_solo_stopwords_devuelve_cero_y_no_el_corpus(proyecto):
    for texto in ("de", "cual es el", "the of", "que es lo que hay"):
        code, out, err = run(texto, "--root", str(proyecto))
        assert (code, out) == (0, ""), (texto, code, out, err)
        d = json.loads(run(texto, "--json", "--limit", "0", "--root", str(proyecto))[1])
        assert d["aciertos"] == [] and d["total"] == 0 and d["consulta"]["tokens"] == [], texto


def test_consulta_con_contenido_que_no_casa_nada_devuelve_cero(proyecto):
    code, out, _ = run("quiero saber si el pato vuela hacia marte", "--limit", "0", "--root", str(proyecto))
    assert (code, out) == (0, "")
    d = json.loads(run("quiero saber si el pato vuela hacia marte", "--json", "--root", str(proyecto))[1])
    assert d["consulta"]["tokens"] == ["pato", "vuela", "marte"], "las stopwords no llegan ni al JSON"
    assert d["total"] == 0


def test_titulo_area_e_id_pesan_por_encima_del_cuerpo(proyecto):
    """Una raíz que solo está en el cuerpo (por muchas veces que aparezca) no puede ordenar el corpus:
    «revisión» está en el TITULAR de LES-001 y en el cuerpo de otras (ADR-003, LES-002)."""
    d = json.loads(run("revisión", "--json", "--root", str(proyecto))[1])
    ids = [a["id"] for a in d["aciertos"]]
    assert ids[0] == "LES-001", ids
    e_cuerpo = dict(id="X-001", titular="nada", area="nada", texto="revisión " * 50)
    e_titulo = dict(id="X-002", titular="la revisión", area="nada", texto="")
    assert kf.puntuacion(e_titulo, ["revi"]) > kf.puntuacion(e_cuerpo, ["revi"]) > 0
    assert kf.puntuacion(e_cuerpo, ["revi"]) == kf.PESO_CUERPO * 2, "el cuerpo suma +1 y +1 más si se repite, nada más"
    assert (kf.PESO_ID, kf.PESO_TITULAR, kf.PESO_AREA) == (12, 6, 4) and kf.PESO_CUERPO == 1


def test_real_tokens_por_hora_trae_las_lecciones_de_estimacion_arriba(real):
    """La consulta que motivó el arreglo: con `--limit 10` (el default) llegan las 9 de estimación."""
    code, out, err = run("cual es el ratio de tokens por hora que uso para estimar", "--json")
    assert code == 0, err
    d = json.loads(out)
    assert d["consulta"]["tokens"] == ["ratio", "token", "hora", "estim"]
    ids = [a["id"] for a in d["aciertos"]]
    estimacion = [i for i in ids if a_area(d, i) == "Estimación / calibración"]
    # El corpus CRECE: una entrada que no es del área de estimación pero habla de medir tokens
    # (GOT-010, el meter que no encontraba las transcripciones) puede colarse arriba con razón.
    # Lo que este test defiende es que la consulta sigue trayendo la doctrina de estimación, no
    # una posición exacta ni un número que caduca cada vez que se escribe una lección nueva.
    assert len(estimacion) >= 8, (len(estimacion), ids)
    assert ids.index(estimacion[0]) <= 1, ("la doctrina de estimación no lidera", ids)
    # y con un hueco más entran TODAS las de estimación del corpus
    code12, out12, err12 = run("cual es el ratio de tokens por hora que uso para estimar", "--json", "--limit", "12")
    assert code12 == 0, err12
    d12 = json.loads(out12)
    est12 = [a["id"] for a in d12["aciertos"] if a_area(d12, a["id"]) == "Estimación / calibración"]
    assert len(est12) == 9, (len(est12), [a["id"] for a in d12["aciertos"]])
    assert d["total"] < 32, "ya no puntúa el corpus entero"


def a_area(d, id_):
    return next(a["area"] for a in d["aciertos"] if a["id"] == id_)


def test_real_de_y_pato_devuelven_cero(real):
    for texto in ("de", "quiero saber si el pato vuela hacia marte"):
        code, out, err = run(texto, "--limit", "0")
        assert (code, out) == (0, ""), (texto, code, out, err)


# =============================================================== T-02 · capa 2: --related <ID> (grafo curado)

def _related(proyecto, id_, *extra):
    return run("--related", id_, *extra, "--root", str(proyecto))


def test_related_agrupa_las_tres_relaciones_etiquetadas_y_separadas(proyecto):
    code, out, err = _related(proyecto, "ADR-003")
    assert code == 0, err
    assert out.startswith("ADR-003 · aceptada · Scripts / consola y codificación · "), out
    etiquetas = [l for l in out.split("\n") if l.endswith(":") or l.startswith(("Sucesión", "Misma iniciativa", "Misma área"))]
    assert [l.split(" (")[0].rstrip(":") for l in etiquetas] == ["Sucesión", "Misma iniciativa", "Misma área"], out
    # y en ese orden dentro del texto
    assert out.index("Sucesión") < out.index("Misma iniciativa") < out.index("Misma área")


def test_related_una_aceptada_que_sustituyo_a_otra_muestra_a_quien_sustituyo(proyecto):
    code, out, _ = _related(proyecto, "ADR-003")
    bloque = out.split("Sucesión")[1].split("Misma iniciativa")[0]
    assert "sustituye a" in bloque and "ADR-002 · obsoleta · " in bloque, bloque


def test_related_una_obsoleta_muestra_su_sucesor(proyecto):
    code, out, _ = _related(proyecto, "ADR-002")
    assert code == 0
    bloque = out.split("Sucesión")[1].split("Misma iniciativa")[0]
    assert "sustituida por" in bloque and "ADR-003 · aceptada · " in bloque, bloque


def test_related_la_sucesion_se_deduce_tambien_desde_el_otro_extremo(proyecto):
    """Si solo ADR-003 declarara `sustituye: ADR-002`, el grafo de ADR-002 igual muestra a su sucesor."""
    p = proyecto / "docs" / "knowledge" / "adr" / "ADR-002-consola-ascii.md"
    p.write_text(p.read_text(encoding="utf-8").replace("sucesor: ADR-003\n", "").replace(
        "estado: obsoleta (sustituida por ADR-003)", "estado: obsoleta"), encoding="utf-8")
    code, out, _ = _related(proyecto, "ADR-002")
    bloque = out.split("Sucesión")[1].split("Misma iniciativa")[0]
    assert "sustituida por" in bloque and "ADR-003" in bloque, bloque


def test_related_misma_iniciativa_sale_del_frontmatter_o_de_la_fuente(proyecto):
    """`iniciativa:` en los ADR; en gotchas/lecciones se deduce del `<fecha>-<slug>/tasks.md` de la fuente."""
    code, out, _ = _related(proyecto, "ADR-003")
    bloque = out.split("Misma iniciativa")[1].split("Misma área")[0]
    assert "(demo-dos)" in out.split("Misma iniciativa")[1].split("\n")[0]
    ids = [l.split(" · ")[0] for l in bloque.split("\n") if " · " in l]
    assert ids == ["GOT-001", "ADR-002"], ids       # doctrina antes que obsoleta; nunca la propia entrada
    assert "ADR-003" not in ids


def test_related_misma_area_casa_normalizada_y_no_incluye_la_propia_entrada(proyecto):
    code, out, _ = _related(proyecto, "GOT-001")
    bloque = out.split("Misma área")[1]
    ids = [l.split(" · ")[0] for l in bloque.split("\n") if " · " in l]
    assert ids == ["ADR-003", "ADR-002"], ids
    assert "GOT-001" not in ids and "LES-001" not in ids


def test_related_sin_relaciones_lo_dice_en_una_linea_por_grupo_y_no_inventa(proyecto):
    code, out, _ = _related(proyecto, "LES-002")
    assert code == 0
    bloque = out.split("Sucesión")[1].split("Misma iniciativa")[0]
    assert "ninguna" in bloque.lower()
    # misma área: LES-001; misma iniciativa (demo-uno): LES-001 y ADR-001
    assert "LES-001 · aceptada" in out.split("Misma área")[1]


def test_related_no_es_una_cronologia(proyecto):
    """Decisión de diseño (spec): grafo curado, no `timeline`. Ni fechas por línea ni «antes/después»."""
    code, out, _ = _related(proyecto, "ADR-003")
    assert code == 0 and out
    for l in out.split("\n"):
        assert not re.match(r"^\s*\d{4}-\d{2}-\d{2}", l), f"línea cronológica: {l!r}"
    assert not re.search(r"(?i)cronolog|timeline|anterior:|siguiente:|antes de|después de", out), out


def test_related_json_es_estructurado(proyecto):
    code, out, _ = _related(proyecto, "ADR-002", "--json")
    data = json.loads(out)
    assert code == 0
    assert set(data) - {"indice_motivo"} == {"version", "indice", "corpus", "entrada", "relaciones"}
    assert data["entrada"]["id"] == "ADR-002"
    assert list(data["relaciones"]) == ["sucesion", "iniciativa", "area"]
    suc = data["relaciones"]["sucesion"]
    assert [(s["relacion"], s["id"]) for s in suc] == [("sustituida por", "ADR-003")]
    assert data["relaciones"]["iniciativa"]["clave"] == "demo-dos"
    assert [a["id"] for a in data["relaciones"]["iniciativa"]["aciertos"]] == ["ADR-003", "GOT-001"]
    assert data["relaciones"]["area"]["clave"] == "Scripts / consola y codificación"
    assert list(suc[0]) == ["relacion"] + list(kf.acierto_json(dict(kf.cargar_corpus(str(proyecto))[0])))


def test_related_con_id_inexistente_exit_1_y_una_linea_en_stderr(proyecto):
    code, out, err = _related(proyecto, "ID-INEXISTENTE")
    assert code == 1 and out == "" and err.count("\n") == 1 and "ID-INEXISTENTE" in err, (code, out, err)
    code, out, err = _related(proyecto, "ADR-999", "--json")
    assert code == 1 and out == "" and err.count("\n") == 1, (code, out, err)


def test_related_acepta_el_id_en_minusculas(proyecto):
    code, out, _ = _related(proyecto, "adr-003")
    assert code == 0 and out.startswith("ADR-003 · ")


def test_related_se_topa_a_1600_caracteres_y_lo_dice(tmp_path):
    """Un área con muchas entradas no puede reventar el presupuesto de la capa 2 (≤ 400 tokens)."""
    kn = tmp_path / "docs" / "knowledge" / "lessons"
    kn.mkdir(parents=True)
    filas = []
    for i in range(1, 41):
        (kn / f"LES-{i:03d}-evaluator-leccion-{i}.md").write_text(_fm(
            id=f"LES-{i:03d}", tipo="leccion", area="Estimación / calibración", estado="aceptada",
            fuente="2026-01-01-demo/retro.md") + f"\n## evaluator\n\n- **Lección número {i} con un titular largo "
            f"para ocupar la línea entera del acierto compacto.**\n", encoding="utf-8")
        filas.append(f"| [`lessons/LES-{i:03d}-evaluator-leccion-{i}.md`](lessons/LES-{i:03d}-evaluator-leccion-{i}.md) "
                     f"— \"Lección número {i} con un titular largo para ocupar la línea entera del acierto compacto.\" "
                     f"| LES-{i:03d} | Lección | Estimación / calibración | aceptada | `2026-01-01-demo/retro.md` |")
    (tmp_path / "docs" / "knowledge" / "README.md").write_text(
        "| Entrada | ID | Tipo | Área | Estado | Fuente |\n|---|---|---|---|---|---|\n" + "\n".join(filas) + "\n",
        encoding="utf-8")
    code, out, err = run("--related", "LES-001", "--root", str(tmp_path))
    assert code == 0, err
    assert len(out) <= kf.RELATED_TOPE_CHARS == 1600, len(out)
    assert re.search(r"… y \d+ más", out), "el recorte se declara, no se esconde"


def test_ca03_related_adr010_grafo_curado_en_menos_de_1600_caracteres(real):
    code, out, err = run("--related", "ADR-010")
    assert code == 0, err
    assert len(out) <= 1600, len(out)
    assert out.startswith("ADR-010 · aceptada · Memoria técnica / hooks · ")
    assert "Sucesión" in out and "Misma iniciativa (memory-health)" in out and "Misma área" in out
    # comparte «Memoria técnica» con ADR-006 y «hooks» con ADR-007: eso es el grafo, no la fecha
    area = out.split("Misma área")[1]
    assert "ADR-006 · " in area and "ADR-007 · " in area, area
    for l in out.split("\n"):
        assert not re.match(r"^\s*\d{4}-\d{2}-\d{2}", l), l


# =============================================================== T-03 · capa 3: --show <ID> + índice SQLite FTS5 reconstruible

def _indice(proyecto):
    return proyecto / ".claude" / kf.INDICE_NOMBRE


def _consulta_json(proyecto, *args):
    code, out, err = run(*args, "--json", "--root", str(proyecto))
    assert code == 0, err
    return json.loads(out)


def test_show_imprime_la_entrada_completa_tal_cual(proyecto):
    code, out, err = run("--show", "ADR-003", "--root", str(proyecto))
    assert code == 0, err
    assert out == ENTRADAS["adr/ADR-003-reconfigurar-utf8.md"], "byte a byte lo que hay en el fichero"
    code, out, _ = run("--show", "got-001", "--root", str(proyecto))          # el ID no distingue mayúsculas
    assert code == 0 and out == ENTRADAS["gotchas/GOT-001-consola-windows-cp1252.md"]


def test_show_json_envuelve_el_contenido_con_su_ficha(proyecto):
    data = _consulta_json(proyecto, "--show", "LES-001")
    assert set(data) - {"indice_motivo"} == {"version", "indice", "corpus", "origen", "id", "tipo", "estado", "estado_detalle",
                                             "area", "titular", "ruta", "contenido"}
    assert data["id"] == "LES-001" and data["ruta"] == "docs/knowledge/lessons/LES-001-evaluator-revision-cara.md"
    assert data["contenido"] == ENTRADAS["lessons/LES-001-evaluator-revision-cara.md"]


def test_show_con_id_inexistente_exit_1_y_una_linea_en_stderr(proyecto):
    code, out, err = run("--show", "NO-EXISTE", "--root", str(proyecto))
    assert code == 1 and out == "" and err.count("\n") == 1 and "NO-EXISTE" in err, (code, out, err)


def test_show_y_related_son_excluyentes(proyecto):
    code, _out, err = run("--show", "ADR-001", "--related", "ADR-001", "--root", str(proyecto))
    assert code == 2 and "not allowed" in err


def test_ca04_show_adr012_la_entrada_mas_grande_cabe_en_10800_caracteres(real):
    code, out, err = run("--show", "ADR-012")
    assert code == 0, err
    ruta = next(f for f in os.listdir(os.path.join(KNOWLEDGE_REAL, "adr")) if f.startswith("ADR-012-"))
    assert out == open(os.path.join(KNOWLEDGE_REAL, "adr", ruta), encoding="utf-8").read()
    assert len(out) <= 10800, len(out)
    code, out, err = run("--show", "NO-EXISTE")
    assert code == 1 and out == "" and err.count("\n") == 1


# --- los tres estados del índice

def test_indice_ausente_se_construye_y_lo_dice(proyecto):
    assert not _indice(proyecto).exists()
    data = _consulta_json(proyecto, "--area", "estimacion")
    assert data["indice"] == "construido" and "indice_motivo" not in data
    assert _indice(proyecto).is_file()
    assert [a["id"] for a in data["aciertos"]] == ["LES-001", "LES-002"]


def test_indice_valido_se_reutiliza_como_cache(proyecto):
    _consulta_json(proyecto, "--area", "estimacion")
    antes = _indice(proyecto).read_bytes()
    data = _consulta_json(proyecto, "--area", "estimacion")
    assert data["indice"] == "cache"
    assert _indice(proyecto).read_bytes() == antes, "en modo caché el fichero no se toca"
    # tocar el mtime de una entrada NO invalida: el hash es del CONTENIDO del corpus
    p = proyecto / "docs" / "knowledge" / "adr" / "ADR-001-guardia-solo-agente.md"
    os.utime(p, (0, 0))
    assert _consulta_json(proyecto, "--area", "estimacion")["indice"] == "cache"


def test_indice_corrupto_se_reconstruye_con_los_mismos_aciertos(proyecto):
    ref = _consulta_json(proyecto, "consola cp1252")
    _indice(proyecto).write_bytes(b"basura")
    data = _consulta_json(proyecto, "consola cp1252")
    assert data["indice"] == "reconstruido"
    assert [a["id"] for a in data["aciertos"]] == [a["id"] for a in ref["aciertos"]] == ["GOT-001", "ADR-002", "ADR-003"]
    assert _indice(proyecto).read_bytes()[:16] == b"SQLite format 3\x00"


def test_hash_que_no_cuadra_se_reconstruye(proyecto):
    _consulta_json(proyecto, "--tipo", "adr")
    # alguien añade una entrada: el hash del corpus cambia y el índice viejo ya no vale
    (proyecto / "docs" / "knowledge" / "gotchas" / "GOT-002-nuevo.md").write_text(
        _fm(id="GOT-002", tipo="gotcha", area="Tests / CI", estado="propuesta", fuente="x") + "\n## Un gotcha nuevo\n",
        encoding="utf-8")
    data = _consulta_json(proyecto, "--tipo", "gotcha")
    assert data["indice"] == "reconstruido"
    assert [a["id"] for a in data["aciertos"]] == ["GOT-001", "GOT-002"]
    assert _consulta_json(proyecto, "--tipo", "gotcha")["indice"] == "cache"


# --- las dos degradaciones: mismo contrato, exit 0

def test_claude_no_escribible_degrada_a_recorrido_plano_con_los_mismos_aciertos(proyecto):
    ref = _consulta_json(proyecto, "consola cp1252")
    shutil.rmtree(proyecto / ".claude")
    (proyecto / ".claude").write_text("soy un fichero, no un directorio", encoding="utf-8")   # falla también como root
    code, out, err = run("consola cp1252", "--json", "--root", str(proyecto))
    assert code == 0, "el índice NUNCA cambia el exit code"
    data = json.loads(out)
    assert data["indice"] == "degradado" and data["indice_motivo"]
    assert [a["id"] for a in data["aciertos"]] == [a["id"] for a in ref["aciertos"]]
    assert [a["linea"] for a in data["aciertos"]] == [a["linea"] for a in ref["aciertos"]]
    code, out, err = run("consola cp1252", "--root", str(proyecto))
    assert code == 0 and out.startswith("GOT-001 · ") and err == "", "y sin ruido en la salida humana"


def test_sqlite_sin_fts5_degrada_a_recorrido_plano(proyecto, monkeypatch, capsys):
    monkeypatch.setattr(kf, "fts5_disponible", lambda: False)
    assert kf.main(["consola", "cp1252", "--json", "--root", str(proyecto)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["indice"] == "degradado" and "FTS5" in data["indice_motivo"]
    assert [a["id"] for a in data["aciertos"]] == ["GOT-001", "ADR-002", "ADR-003"]
    assert not _indice(proyecto).exists(), "sin FTS5 no se deja un índice a medias"


def test_no_index_fuerza_el_recorrido_plano(proyecto):
    data = _consulta_json(proyecto, "--no-index", "--area", "estimacion")
    assert data["indice"] == "degradado" and data["indice_motivo"] == "--no-index"
    assert not _indice(proyecto).exists()


@pytest.mark.parametrize("consulta", [["consola windows cp1252"], ["--area", "estimacion"], ["hook deny"],
                                      ["--tipo", "adr"], ["revision"], ["cp1252", "--tipo", "adr"], []])
def test_el_camino_con_indice_y_el_plano_dan_aciertos_identicos(proyecto, consulta):
    con = _consulta_json(proyecto, *consulta)
    sin = _consulta_json(proyecto, *consulta, "--no-index")
    assert con["indice"] in ("construido", "cache") and sin["indice"] == "degradado"
    assert [(a["id"], a["puntuacion"]) for a in con["aciertos"]] == [(a["id"], a["puntuacion"]) for a in sin["aciertos"]]
    assert con["total"] == sin["total"]


@pytest.mark.parametrize("consulta", [["consola windows cp1252"], ["--area", "estimacion"], ["hook de guardia"],
                                      ["jira transición", "--limit", "0"], ["changelog"], ["--tipo", "gotcha"]])
def test_sobre_el_corpus_real_indice_y_plano_coinciden(real, consulta):
    code, out, err = run(*consulta, "--json")
    assert code == 0, err
    con = json.loads(out)
    code, out, err = run(*consulta, "--json", "--no-index")
    sin = json.loads(out)
    assert [a["id"] for a in con["aciertos"]] == [a["id"] for a in sin["aciertos"]]
    assert con["indice"] in ("construido", "reconstruido", "cache")


def test_el_indice_esta_en_gitignore():
    r = subprocess.run(["git", "check-ignore", "-v", ".claude/" + kf.INDICE_NOMBRE], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0 and r.stdout.count("\n") == 1, r.stdout + r.stderr
    assert ".gitignore" in r.stdout


def test_sin_corpus_tampoco_se_crea_indice(tmp_path):
    (tmp_path / ".claude").mkdir()
    code, out, _ = run("--area", "x", "--json", "--root", str(tmp_path))
    assert code == 0 and json.loads(out)["aciertos"] == []
    assert not (tmp_path / ".claude" / kf.INDICE_NOMBRE).exists()


# =============================================================== T-05/T-06 · capa 1 ENRUTADA (llegada)
#
# `--contexto TEXTO` · `--tipo-tarea TIPO` · `--iniciativa SLUG`: la variante de la capa 1 que consumen
# `task-brief.py` (T-05) y `session-context.sh` (T-06). El enrutado es POR ÁREA (nunca por texto libre,
# que con tokens genéricos puntúa todo el corpus): una entrada entra si su `iniciativa` es la pedida o
# si alguna CLAVE (palabras del tipo de tarea + tokens significativos del contexto) casa, por prefijo,
# con un token de su área. Sin ninguna clave que case → 0 aciertos, nunca el corpus entero.

def _enrutado(proyecto, *args):
    return _consulta_json(proyecto, *args)


def test_enrutado_por_tipo_de_tarea_devops_trae_hooks_y_consola_y_no_estimacion(proyecto):
    d = _enrutado(proyecto, "--tipo-tarea", "devops")
    ids = [a["id"] for a in d["aciertos"]]
    assert "ADR-001" in ids, "«Hooks / implementer» casa con la clave `hooks` de devops"
    assert "GOT-001" in ids and "ADR-003" in ids, "«Scripts / consola y codificación» casa con `consola`"
    assert not any(i.startswith("LES-") for i in ids), "«Estimación / calibración» no es área de devops"
    assert d["consulta"]["tipo_tarea"] == "devops" and "hooks" in d["consulta"]["claves"]
    assert set(kf.TIPO_TAREA_AREAS) == {"frontend", "backend", "db", "devops", "test", "docs"}, \
        "las seis etiquetas del catálogo de personas (subagent-personas)"


def test_enrutado_por_contexto_casa_tokens_significativos_con_el_area(proyecto):
    d = _enrutado(proyecto, "--contexto", "Presupuestar la estimación de la iniciativa")
    ids = [a["id"] for a in d["aciertos"]]
    assert ids == ["LES-001", "LES-002"], ids               # aceptada antes que propuesta
    assert "estimacion" in d["consulta"]["claves"]
    assert not {"la", "de"} & set(d["consulta"]["claves"]), "los tokens cortos no son claves"


def test_enrutado_por_iniciativa_trae_las_entradas_nacidas_en_ella(proyecto):
    d = _enrutado(proyecto, "--iniciativa", "demo-uno")
    assert [a["id"] for a in d["aciertos"]] == ["ADR-001", "LES-001", "LES-002"]
    d2 = _enrutado(proyecto, "--iniciativa", "2026-01-05-demo-dos")     # con fecha delante también
    assert {a["id"] for a in d2["aciertos"]} == {"ADR-002", "ADR-003", "GOT-001"}


def test_enrutado_sin_clave_que_case_devuelve_cero_y_nunca_el_corpus_entero(proyecto):
    for args in (["--contexto", "de la con por"], ["--contexto", "sobre nada relevante aquí"],
                 ["--tipo-tarea", "db"], ["--iniciativa", "no-existe"]):
        d = _enrutado(proyecto, *args)
        assert d["aciertos"] == [] and d["total"] == 0, args
    code, out, _ = run("--contexto", "sobre nada relevante aquí", "--root", str(proyecto))
    assert code == 0 and out == ""


def test_enrutado_combina_claves_y_puntua_iniciativa_por_encima_de_area(proyecto):
    d = _enrutado(proyecto, "--tipo-tarea", "devops", "--iniciativa", "demo-uno", "--contexto", "calibración")
    ids = [a["id"] for a in d["aciertos"]]
    assert ids[0] == "ADR-001", "casa por iniciativa Y por área (hooks): la más puntuada"
    assert set(ids) == {"ADR-001", "LES-001", "LES-002", "GOT-001", "ADR-003", "ADR-002"}
    assert all(a["puntuacion"] > 0 for a in d["aciertos"])
    assert ids.index("LES-001") < ids.index("GOT-001"), "iniciativa (+) antes que solo área"


def test_enrutado_respeta_limit_tipo_y_el_esquema_de_la_capa_1(proyecto):
    d = _enrutado(proyecto, "--tipo-tarea", "devops", "--tipo", "gotcha", "--limit", "1")
    assert [a["id"] for a in d["aciertos"]] == ["GOT-001"] and d["total"] == 1
    assert set(d) - {"indice_motivo"} == {"version", "indice", "corpus", "consulta", "total", "aciertos"}
    assert list(d["aciertos"][0]) == ["id", "tipo", "estado", "estado_detalle", "area", "titular", "ruta", "linea",
                                      "puntuacion", "iniciativa", "fecha", "origen"], "mismo esquema por acierto que la capa 1"
    assert set(d["consulta"]) == {"texto", "area", "tipo", "limit", "contexto", "tipo_tarea", "iniciativa", "claves"}


def test_enrutado_con_filtros_presentes_pero_vacios_es_un_filtro_no_su_ausencia(proyecto):
    """Intento 1, MINOR 5: `--contexto "" --iniciativa ""` caía a la consulta libre vacía y devolvía el
    corpus ENTERO (32). Es el caso de un ledger sin H1 y sin slug: el brief/hook no debe recibir todo."""
    for args in (["--contexto", ""], ["--iniciativa", ""], ["--contexto", "", "--iniciativa", ""],
                 ["--tipo-tarea", ""], ["--contexto", "", "--tipo-tarea", "", "--iniciativa", ""]):
        code, out, err = run(*args, "--limit", "0", "--root", str(proyecto))
        assert (code, out) == (0, ""), (args, code, out, err)
        d = json.loads(run(*args, "--json", "--root", str(proyecto))[1])
        assert d["aciertos"] == [] and d["total"] == 0 and d["consulta"]["claves"] == [], args
        assert {"contexto", "tipo_tarea", "iniciativa"} <= set(d["consulta"]), "sigue siendo la consulta enrutada"
    # y sin ningún filtro de enrutado, la capa 1 sin consulta sigue listando (doctrina primero, por ID)
    d = json.loads(run("--json", "--limit", "0", "--root", str(proyecto))[1])
    assert d["total"] == 6 and "claves" not in d["consulta"]


def test_limit_negativo_es_error_de_uso_exit_2(proyecto):
    """Intento 1, MINOR 8: `--limit -1` era «sin tope» en silencio; el sin tope explícito es `--limit 0`."""
    for v in ("-1", "-10"):
        code, out, err = run("--limit", v, "--root", str(proyecto))
        assert code == 2 and out == "", (v, code, out)
        assert "negativo" in err and "--limit" in err and "usage" in err.lower(), err
        code, _, _ = run("--tipo-tarea", "devops", "--limit", v, "--root", str(proyecto))
        assert code == 2, "también en el camino enrutado"
    code, _, err = run("--limit", "x", "--root", str(proyecto))
    assert code == 2 and "entero" in err
    code, out, _ = run("--limit", "0", "--json", "--root", str(proyecto))
    assert code == 0 and json.loads(out)["total"] == len(json.loads(out)["aciertos"]) == 6, "0 = sin tope"


def test_enrutado_tipo_de_tarea_desconocido_avisa_y_no_bloquea(proyecto):
    code, out, err = run("--tipo-tarea", "cobol", "--json", "--root", str(proyecto))
    assert code == 0 and json.loads(out)["aciertos"] == []
    assert "cobol" in err


def test_enrutado_sobre_el_corpus_real_devops_trae_hooks_y_consola(real):
    code, out, _ = run("--tipo-tarea", "devops", "--json")
    assert code == 0
    ids = {a["id"] for a in json.loads(out)["aciertos"]}
    assert {"ADR-007", "ADR-010", "GOT-005"} <= ids, ids
    assert not any(i in ids for i in ("LES-001", "LES-005", "LES-009")), "la estimación no es área de devops"
