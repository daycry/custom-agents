#!/usr/bin/env python3
"""Tests del generador roadmap-dashboard (sin dependencias; assert + salida).

Ejecuta:  python tests/test_dashboard.py
Sale 0 si todo pasa, 1 si algo falla. Protege el parser frente a cambios que
rompan la lectura de spec.md / evaluation.md o la coherencia de estados.
"""
import os
import sys
import contextlib
import importlib.util
import io
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "roadmap-dashboard", "scripts"))
FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "roadmap")

import build_dashboard as bd  # noqa: E402


def eq(got, exp, msg):
    assert got == exp, f"{msg}: esperado {exp!r}, obtenido {got!r}"


def contains(text, needle, msg):
    assert needle in text, f"{msg}: no contiene {needle!r}"


def check_snapshot_windows():
    """Stable measurement identities replace cumulative snapshots as a whole."""
    def snapshot(tokens, revision, source="a", window="b"):
        return {"fuente": "medido", "inicio": "2026-10-11T00:00:00Z",
                "fin": "2026-10-11T00:02:00Z", "tokens_reales": {"entrada": tokens},
                "horas_ia": tokens / 100, "eur": tokens / 10000,
                "fuente_id": "src-" + source * 64, "ventana_id": "win-" + window * 32,
                "revision_medicion": revision}
    old, latest = snapshot(150, 1), snapshot(200, 2)
    for rows in ({"plan": old, "tasks": latest}, {"tasks": latest, "plan": old}):
        stats = bd._proceso_gen_stats(rows)
        eq(stats["toks"], 200, "latest shared snapshot, independent of document order")
        eq(stats["horas"], 2, "hours belong to the latest whole snapshot")
        eq(stats["eur"], .02, "price belongs to the latest whole snapshot")
        eq(stats["ventanas"], 1, "one identified window")
    corrected = snapshot(100, 3)
    eq(bd._proceso_gen_stats({"old": latest, "corrected": corrected})["toks"], 100,
       "revision ordering permits corrected lower totals")
    for other in (snapshot(150, 1, source="c"), snapshot(150, 1, window="d")):
        eq(bd._proceso_gen_stats({"one": old, "other": other})["toks"], 300,
           "independent sources and windows retain their own identical metrics")
    eq(bd._proceso_gen_stats({"one": old, "copy": dict(old)})["toks"], 150,
       "identical copies of the same revision count once")
    conflict = snapshot(250, 2)
    stats = bd._proceso_gen_stats({"one": latest, "conflicting": conflict})
    assert stats["parcial"] and stats["avisos"] and stats["docs_con_tokens"] == 0
    view = bd.render_proceso_md([{"titulo": "Fixture", "generacion": {
        "one": latest, "conflicting": conflict}}])
    contains(view, "parcial", "contradictory revisions are visible in the report")
    invalid = {**old, "revision_medicion": True}
    assert bd._proceso_gen_stats({"invalid": invalid})["parcial"]
    recovered = bd._proceso_gen_stats({"one": latest, "conflicting": conflict,
                                      "corrected": corrected})
    assert not recovered["parcial"] and recovered["toks"] == 100
    legacy = {key: value for key, value in old.items()
              if key not in ("fuente_id", "ventana_id", "revision_medicion")}
    eq(bd._proceso_gen_stats({"one": legacy, "copy": dict(legacy)})["toks"], 150,
       "exact legacy copies retain compatibility")
    estimated = {**legacy, "fuente": "estimado"}
    eq(bd._proceso_gen_stats({"measured": legacy, "estimated": estimated})["toks"], 300,
       "different source classifications are not deduplicated")
    parsed = bd.parse_generacion("---\ngeneracion:\n  fuente: medido\n  fuente_id: "
                                 + old["fuente_id"] + "\n  ventana_id: " + old["ventana_id"]
                                 + "\n  revision_medicion: 2\n---\n")
    eq(parsed["revision_medicion"], 2, "revision survives the frontmatter parser as integer")


def check_persistence_flags():
    measured = {"fuente": "medido", "inicio": "2026-10-11T00:00:00Z",
                "fin": "2026-10-11T00:02:00Z", "tokens_reales": {"entrada": 150},
                "fuente_id": "src-" + "a" * 64, "ventana_id": "win-" + "b" * 32,
                "revision_medicion": 1, "medicion_persistida": True}
    failed = {"fuente": "medido", "tokens_reales": {"entrada": 200},
              "medicion_persistida": False}
    stats = bd._proceso_gen_stats({"plan": measured, "failed-update": failed})
    eq(stats["toks"], 150, "failed persistence does not add an unbound cumulative close")
    assert stats["parcial"] and stats["avisos"] and not stats["eur_ok"]
    report = bd.render_proceso_md([{"titulo": "Fixture", "generacion": {
        "plan": measured, "failed-update": failed}}])
    contains(report, "parcial", "failed persistence is visible in human totals")
    assert "ventana compartida" not in report, "excluded measurements do not prove a shared window"
    for invalid in ("false", 0, None):
        assert bd._proceso_gen_stats({"invalid": {**measured,
            "medicion_persistida": invalid}})["parcial"]
    missing_identity = {**failed, "medicion_persistida": True}
    assert bd._proceso_gen_stats({"unbound": missing_identity})["parcial"]
    for text, expected in (("false", False), ("true", True), ('"false"', None), ("0", None)):
        parsed = bd.parse_generacion("---\ngeneracion:\n  fuente: medido\n"
            "  medicion_persistida: " + text + "\n---\n")
        eq(parsed["medicion_persistida"], expected, "persistence flag has a typed parser")


def check_meter_to_dashboard():
    """Exercise persisted meter output through document parsing and report totals."""
    spec = importlib.util.spec_from_file_location(
        "snapshot_meter", Path(ROOT) / "agent-kits/shared/usage-meter.py")
    meter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(meter)
    with tempfile.TemporaryDirectory(prefix="dashboard-meter-") as directory:
        base = Path(directory)
        transcripts = base / "transcripts"
        transcripts.mkdir()
        transcript = transcripts / "session.jsonl"
        transcript.write_text("", encoding="utf-8")
        rates = base / "rates.json"
        rates.write_text("{}", encoding="utf-8")
        common = ["--artefacto", "shared-plan", "--state", str(base / "state.json"),
                  "--transcript-dir", str(transcripts)]

        def invoke(command):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                eq(meter.main(command), 0, "nonblocking meter invocation")
            return json.loads(output.getvalue())

        def append(message_id, tokens):
            item = {"type": "assistant", "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": {"id": message_id, "usage": {"input_tokens": tokens,
                    "output_tokens": 0, "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0}}}
            with transcript.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(item) + "\n")

        def parse(output):
            # Real producer values, serialized into the document's supported frontmatter.
            lines = ["---", "generacion:"]
            for key, value in output.items():
                if key in ("avisos", "artefacto"):
                    continue
                if isinstance(value, dict):
                    lines.append("  " + key + ": { " + ", ".join(
                        str(k) + ": " + str(v) for k, v in value.items()) + " }")
                else:
                    lines.append("  " + key + ": " + ("null" if value is None else str(value)))
            return bd.parse_generacion("\n".join([*lines, "---", ""]))

        invoke(["start", *common])
        append("one", 150)
        close = ["close", *common, "--rates", str(rates), "--ratio", "300000"]
        first = parse(invoke(close))
        append("two", 50)
        latest = parse(invoke(close))
        stats = bd._proceso_gen_stats({"plan": first, "tasks": latest})
        eq(stats["toks"], 200, "real cumulative snapshots replace rather than add")
        assert not stats["parcial"]
        append("failed-persistence-response", 25)
        replace = meter.os.replace
        def fail_replace(*args):
            raise PermissionError("synthetic state persistence failure")
        try:
            meter.os.replace = fail_replace
            failed = parse(invoke(close))
        finally:
            meter.os.replace = replace
        assert failed["medicion_persistida"] is False
        partial = bd._proceso_gen_stats({"plan": first, "tasks": latest, "failed": failed})
        eq(partial["toks"], 200, "failed producer persistence cannot silently add its snapshot")
        assert partial["parcial"]
        invoke(["start", *common])
        append("three", 50)
        independent = parse(invoke(close))
        eq(bd._proceso_gen_stats({"plan": first, "tasks": latest,
                                 "new-session": independent})["toks"], 250,
           "new real start adds an independent window")
def _eval_variantes():
    """C-05 / CA-07: las dos familias de etiquetas de evaluation.md + estado por frontmatter."""
    import tempfile
    import shutil
    tmp = tempfile.mkdtemp(prefix="dash-eval-")

    def crear(slug, fm_estado, filas):
        d = os.path.join(tmp, slug)
        os.makedirs(d)
        with open(os.path.join(d, "spec.md"), "w", encoding="utf-8") as f:
            f.write("---\nestado: aprobada\n---\n\n# Spec\n")
        cuerpo = "---\nevaluation: x\n" + (f"estado: {fm_estado}\n" if fm_estado else "") + "---\n\n# Eval\n\n"
        if filas is not None:
            cuerpo += "| Metrica | Estimado | Confianza |\n|---|---:|---|\n" + "\n".join(filas) + "\n"
        else:
            cuerpo += "Estimacion en prosa: 50h humanas, 545k tokens. Sin tabla.\n"
        with open(os.path.join(d, "evaluation.md"), "w", encoding="utf-8") as f:
            f.write(cuerpo)

    try:
        crear("2026-09-01-historica", None, ["| **Estado** | completado |", "| Esfuerzo humano | **12 h** | Alta |",
                                             "| Coste | **~605 EUR** | Alta |"])
        crear("2026-09-02-nueva-a", "completado", ["| Tiempo humano | 39.5h (33h base +20%) | Media |",
                                                   "| Coste humano a 50 EUR/h | 1,975 EUR - antes 2,050 EUR | Media |"])
        crear("2026-09-03-nueva-b", "completado", ["| Tiempo humano | 56h | Media |",
                                                   "| Coste humano (50 EUR/h) | 1,300 EUR | Media |"])
        crear("2026-09-04-sin-tabla", "completado", None)
        by = {r["slug"]: r for r in bd.scan(tmp)}
        h = by["2026-09-01-historica"]
        eq((h["eval_estado"], h["coste"], h["esfuerzo"]), ("completado", "~605 EUR", "12 h"), "variante historica")
        a = by["2026-09-02-nueva-a"]
        eq(a["esfuerzo"], "39.5h (33h base +20%)", "variante Tiempo humano")
        eq(a["coste"], "1,975 EUR - antes 2,050 EUR", "variante Coste humano a N EUR/h (coma de miles intacta)")
        eq(a["eval_estado"], "completado", "estado desde el frontmatter si no hay fila Estado")
        b = by["2026-09-03-nueva-b"]
        eq(b["coste"], "1,300 EUR", "variante Coste humano (N EUR/h): 1,300 no se lee como 1,3")
        eq(b["esfuerzo"], "56h", "esfuerzo de la variante b")
        st = by["2026-09-04-sin-tabla"]
        eq((st["coste"], st["esfuerzo"], st["eval_estado"]), (None, None, "completado"), "sin tabla: nulo, sin excepcion")
        warns = bd.warnings_for(list(by.values()))
        assert any("2026-09-04-sin-tabla" in w and "coste" in w for w in warns), f"aviso nominal esperado: {warns}"
        assert not any("eval_estado" in w for w in warns), f"el estado se lee del frontmatter: {warns}"
        assert not any("nueva-a" in w or "nueva-b" in w or "historica" in w for w in warns), warns
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_evaluaciones_con_las_dos_familias_de_etiquetas():
    _eval_variantes()


# --- Procedencia y cobertura del meter (D-086) agregadas por el dashboard -------------------
# `usage-meter.py close` emite claves planas (`tokens_procedencia`, `tokens_cobertura`,
# `transcripts_*`, `coste_procedencia`, `coste_cobertura`, `coste_sin_precio`,
# `tarifa_verificada_el`). El informe tiene que separar tokens MEDIDOS de sin medida y coste
# estimado completo de incompleto, contando artefactos por caso; un bloque antiguo sin esas
# claves es «procedencia desconocida», NUNCA medido; lo ausente es null, nunca 0.

def _bloque(**claves):
    lineas = ["---", "generacion:"]
    for k, v in claves.items():
        lineas.append(f"  {k}: {v}")
    return "\n".join(lineas + ["---", ""])


_SPEC_MEDIDA = _bloque(  # transcript completo, coste completo
    fuente="medido", inicio="2026-10-01T10:00:00Z", fin="2026-10-01T10:05:00Z",
    tokens_reales="{ entrada: 100, salida: 200, cache_creacion: 0, cache_lectura: 9000 }",
    horas_ia="0.1", eur="1.50",
    tokens_procedencia="transcript", tokens_cobertura="completa",
    transcripts_leidos="2", transcripts_subagente="1", transcripts_con_error="0",
    coste_procedencia="estimado_tarifa", coste_cobertura="completa", coste_sin_precio="[]",
    tarifa_verificada_el="2026-09-30")
_EVAL_PARCIAL = _bloque(  # transcript parcial, coste incompleto (cache_lectura sin precio)
    fuente="medido", inicio="2026-10-02T10:00:00Z", fin="2026-10-02T10:05:00Z",
    tokens_reales="{ entrada: 40, salida: 60, cache_creacion: 0, cache_lectura: 500 }",
    horas_ia="0.05", eur="0.25",
    tokens_procedencia="transcript", tokens_cobertura="parcial",
    transcripts_leidos="3", transcripts_subagente="0", transcripts_con_error="1",
    coste_procedencia="estimado_tarifa", coste_cobertura="incompleta",
    coste_sin_precio="['cache_lectura']", tarifa_verificada_el="2026-09-30")
_DESIGN_SIN_MEDIDA = _bloque(  # el meter no pudo medir: ni tokens ni coste
    fuente="estimado", tokens_reales="null", horas_ia="0.2", eur="null",
    tokens_procedencia="sin_medida", tokens_cobertura="sin_medida",
    transcripts_leidos="null", transcripts_subagente="null", transcripts_con_error="null",
    coste_procedencia="sin_coste", coste_cobertura="sin_coste", coste_sin_precio="[]",
    tarifa_verificada_el="null")
_PLAN_ANTIGUO = _bloque(  # bloque anterior a D-086: medido, pero sin claves de procedencia
    fuente="medido", inicio="2026-10-03T10:00:00Z", fin="2026-10-03T10:05:00Z",
    tokens_reales="{ entrada: 10, salida: 40, cache_creacion: 0 }", horas_ia="0.01", eur="0.10")


def _roadmap_procedencia(base):
    """Dos iniciativas: «mixta» (los cuatro casos) y «antigua» (solo bloques pre-D-086)."""
    mixta = os.path.join(base, "2026-10-01-mixta")
    antigua = os.path.join(base, "2026-10-05-antigua")
    os.makedirs(mixta)
    os.makedirs(antigua)
    ledger = "# Checklist de Tareas — {}\n\n| | |\n|---|---|\n| **Estado** | completado |\n"
    for nombre, texto in (("spec.md", _SPEC_MEDIDA + "# Mixta\n"),
                          ("evaluation.md", _EVAL_PARCIAL + "# Eval\n"),
                          ("design.md", _DESIGN_SIN_MEDIDA + "# Diseño\n"),
                          ("improvement-plan.md", _PLAN_ANTIGUO + "# Plan\n")):
        Path(mixta, nombre).write_text(texto, encoding="utf-8")
    Path(antigua, "tasks.md").write_text(_PLAN_ANTIGUO + ledger.format("Antigua"), encoding="utf-8")
    return {r["slug"]: r for r in bd.scan(base)}


def test_parser_lee_las_claves_de_procedencia():
    g = bd.parse_generacion(_EVAL_PARCIAL)
    eq(g["tokens_procedencia"], "transcript", "procedencia de tokens como texto")
    eq(g["tokens_cobertura"], "parcial", "cobertura de tokens como texto")
    eq((g["transcripts_leidos"], g["transcripts_subagente"], g["transcripts_con_error"]),
       (3, 0, 1), "contadores de transcripts como enteros")
    eq(g["coste_sin_precio"], ["cache_lectura"], "lista inline con comillas → lista")
    eq(g["tarifa_verificada_el"], "2026-09-30", "fecha de tarifa como texto")
    vacio = bd.parse_generacion(_DESIGN_SIN_MEDIDA)
    eq(vacio["transcripts_leidos"], None, "null en un contador → None, no 0 ni 'null'")
    eq(vacio["coste_sin_precio"], [], "lista vacía → []")
    eq(vacio["tarifa_verificada_el"], None, "tarifa null → None")
    for texto, esperado in (("[cache_lectura, cache_creacion]", ["cache_lectura", "cache_creacion"]),
                            ('["salida"]', ["salida"]), ("null", None), ("~", None)):
        got = bd.parse_generacion(_bloque(coste_sin_precio=texto))["coste_sin_precio"]
        eq(got, esperado, f"coste_sin_precio={texto!r}")
    bloque = bd.parse_generacion("---\ngeneracion:\n  coste_sin_precio:\n    - cache_lectura\n"
                                 "    - salida\n  fuente: medido\n---\n")
    eq(bloque["coste_sin_precio"], ["cache_lectura", "salida"], "lista en bloque YAML")
    eq(bloque["fuente"], "medido", "la lista en bloque no se come la clave siguiente")
    eq(bd.parse_generacion(_bloque(transcripts_leidos="dos"))["transcripts_leidos"], None,
       "contador no numérico → None (sin inventar)")


def test_procedencia_por_iniciativa_separa_medido_sin_medida_y_desconocido():
    with tempfile.TemporaryDirectory(prefix="dash-proc-") as base:
        by = _roadmap_procedencia(base)
    p = bd.procedencia_generacion(by["2026-10-01-mixta"]["generacion"])
    t, c = p["tokens"], p["coste"]
    eq(t["transcript_completa"], {"artefactos": 1, "tokens": 300}, "tokens medidos completos")
    eq(t["transcript_parcial"], {"artefactos": 1, "tokens": 100}, "tokens medidos parciales")
    eq(t["sin_medida"], {"artefactos": 1, "tokens": None}, "sin medida: null, nunca 0")
    eq(t["desconocida"], {"artefactos": 1, "tokens": 50},
       "un bloque antiguo es procedencia desconocida (sus tokens no pasan por medidos)")
    eq(c["estimado_completo"], {"artefactos": 1, "eur": 1.5}, "coste completo")
    eq(c["estimado_incompleto"], {"artefactos": 1, "eur": 0.25, "sin_precio": ["cache_lectura"]},
       "coste incompleto con sus clases sin precio")
    eq(c["sin_coste"], {"artefactos": 1, "eur": None}, "sin coste: null, nunca 0")
    eq(c["desconocida"], {"artefactos": 1, "eur": 0.1}, "coste de un bloque antiguo: desconocido")
    eq(p["transcripts"], {"leidos": 5, "subagente": 1, "con_error": 1},
       "contadores sumados solo de los bloques que los declaran")
    eq(p["tarifas_verificadas_el"], ["2026-09-30"], "fechas de tarifa distintas")
    # la partición cubre todos los artefactos y los tokens por caso suman el total del informe
    eq(sum(v["artefactos"] for v in t.values()), 4, "partición de artefactos por tokens")
    eq(sum(v["artefactos"] for v in c.values()), 4, "partición de artefactos por coste")
    eq(sum(v["tokens"] or 0 for v in t.values()),
       bd._proceso_gen_stats(by["2026-10-01-mixta"]["generacion"])["toks"],
       "los tokens por procedencia cuadran con el total de la fila")

    antigua = bd.procedencia_generacion(by["2026-10-05-antigua"]["generacion"])
    eq(antigua["tokens"]["transcript_completa"], {"artefactos": 0, "tokens": None},
       "una iniciativa solo con bloques antiguos no tiene NADA medido (null, no 0)")
    eq(antigua["tokens"]["desconocida"]["artefactos"], 1, "y su bloque es desconocido")
    eq(antigua["transcripts"], {"leidos": None, "subagente": None, "con_error": None},
       "sin contadores declarados → null")
    vacia = bd.procedencia_generacion(None)
    eq(vacia["tokens"]["desconocida"], {"artefactos": 0, "tokens": None}, "sin generacion")
    eq(bd.procedencia_generacion(["roto"])["tokens"]["desconocida"]["artefactos"], 1,
       "un generacion: que no es mapa cuenta como un bloque desconocido, sin reventar")


def test_procedencia_ventana_compartida_no_duplica_tokens():
    # plan y tasks declaran la MISMA ventana (diseño del planner): dos artefactos, tokens una vez
    gen = {"plan": bd.parse_generacion(_SPEC_MEDIDA), "tasks": bd.parse_generacion(_SPEC_MEDIDA)}
    p = bd.procedencia_generacion(gen)
    eq(p["tokens"]["transcript_completa"], {"artefactos": 2, "tokens": 300},
       "dos artefactos aportan, la ventana compartida se suma una vez")
    eq(p["coste"]["estimado_completo"], {"artefactos": 2, "eur": 1.5}, "coste una vez")


def test_procedencia_en_el_total_de_cartera_y_en_el_informe():
    with tempfile.TemporaryDirectory(prefix="dash-proc-") as base:
        inits = list(_roadmap_procedencia(base).values())
    tot = bd.procedencia_cartera(inits)
    eq(tot["tokens"]["desconocida"], {"artefactos": 2, "tokens": 100}, "cartera: desconocidos")
    eq(tot["tokens"]["transcript_completa"], {"artefactos": 1, "tokens": 300}, "cartera: medidos")
    eq(tot["coste"]["estimado_incompleto"]["sin_precio"], ["cache_lectura"], "cartera: sin precio")
    eq(bd.procedencia_cartera([])["tokens"]["transcript_parcial"],
       {"artefactos": 0, "tokens": None}, "cartera vacía: null, no 0")
    md = bd.render_proceso_md(inits)
    contains(md, "| Procedencia |", "columna nueva en la tabla de proceso")
    contains(md, "Procedencia (cartera)", "línea de total de cartera")
    contains(md, "medidos por transcript: 400 tok en 2 artefactos",
             "la línea separa los tokens medidos")
    contains(md, "procedencia desconocida: 2 artefactos", "y los bloques antiguos")
    contains(md, "sin precio: cache_lectura", "y el coste incompleto con sus clases")
    fila_antigua = next(line for line in md.splitlines() if line.startswith("| Antigua"))
    assert "transcript" not in fila_antigua and "desconocida" in fila_antigua, fila_antigua
    # lo de antes sigue: formato de tokens y la línea E7
    contains(md, "450 tok (3/4 docs con medida", "el formato existente de la fila no cambia")
    contains(md, "bloques `generacion:` con `fuente: estimado`", "la línea E7 sigue")


def test_procedencia_en_json_y_html():
    import subprocess
    script = os.path.join(ROOT, "skills", "roadmap-dashboard", "scripts", "build_dashboard.py")
    with tempfile.TemporaryDirectory(prefix="dash-proc-") as base:
        inits = list(_roadmap_procedencia(base).values())
        salida = subprocess.run([sys.executable, script, "--root", base, "--json"],
                                capture_output=True, text=True, encoding="utf-8", check=True)
    datos = json.loads(salida.stdout)
    assert isinstance(datos, list), "el --json sigue siendo la LISTA de iniciativas"
    by = {r["slug"]: r for r in datos}
    antigua = by["2026-10-05-antigua"]
    for clave in ("estimados", "medidos", "generacion_total"):
        assert clave in antigua, f"clave existente {clave} se conserva"
    eq(antigua["procedencia"]["tokens"]["transcript_completa"]["tokens"], None,
       "JSON: ausente = null")
    eq(by["2026-10-01-mixta"]["procedencia"]["coste"]["estimado_incompleto"]["artefactos"], 1,
       "JSON: coste incompleto por iniciativa")
    html_out = bd.render_html(inits, base)
    contains(html_out, "Medición", "la tarjeta HTML muestra la procedencia")
    contains(html_out, "1 desconocida", "y cuenta los bloques desconocidos")


def test_vista_json_es_pura_y_coincide_con_el_json_de_la_cli():
    """T-13 (panel-redesign): `vista_json(inits)` es lo que `--json` imprime, sin disco ni salida."""
    import builtins
    import subprocess
    script = os.path.join(ROOT, "skills", "roadmap-dashboard", "scripts", "build_dashboard.py")
    with tempfile.TemporaryDirectory(prefix="dash-vista-") as base:
        inits = list(_roadmap_procedencia(base).values())
        salida = subprocess.run([sys.executable, script, "--root", base, "--json"],
                                capture_output=True, text=True, encoding="utf-8", check=True)
        copia = json.loads(json.dumps(inits))
    esperado = json.loads(salida.stdout)
    real_open, volcado = builtins.open, io.StringIO()
    builtins.open = lambda *a, **k: (_ for _ in ()).throw(AssertionError("vista_json no lee ni escribe disco"))
    try:
        with contextlib.redirect_stdout(volcado):
            vista = bd.vista_json(copia)
    finally:
        builtins.open = real_open
    assert volcado.getvalue() == "", "vista_json no imprime"
    assert vista is copia, "devuelve la misma lista de iniciativas, enriquecida"
    eq(vista, esperado, "vista_json == lo que imprime --json")
    for r in vista:
        for clave in ("estimados", "medidos", "generacion_total", "generacion_otros", "procedencia"):
            assert clave in r, clave


def run():
    check_snapshot_windows()
    check_persistence_flags()
    check_meter_to_dashboard()
    inits = bd.scan(FIX)
    by = {r["slug"]: r for r in inits}

    # --- descubrimiento ---
    eq(len(inits), 3, "número de iniciativas")
    for s in ("2026-01-10-alpha", "2026-01-12-beta", "2026-01-14-gamma"):
        assert s in by, f"falta la iniciativa {s}"

    # --- parseo de alpha (spec + evaluación + plan) ---
    a = by["2026-01-10-alpha"]
    eq(a["spec_estado"], "aprobada", "alpha spec_estado")
    eq(a["eval_estado"], "completado", "alpha eval_estado")
    eq(a["prioridad"], "Alta", "alpha prioridad")
    eq(a["coste"], "1.850 €", "alpha coste")
    eq(a["multiplicador"], "×3.1", "alpha multiplicador")
    eq(a["fase"], "planificada", "alpha fase")
    contains(a["esfuerzo"], "32h", "alpha esfuerzo")
    contains(a["tokens"], "420.000", "alpha tokens")
    eq(a["titulo"], "Alpha (fixture)", "alpha título (H1)")
    eq(a["has_design"], True, "alpha con design.md (architect)")
    eq(a["design_estado"], "aprobado", "alpha design_estado")

    # --- beta: sin design.md → columna tolerada, vacía ---
    eq(by["2026-01-12-beta"]["has_design"], False, "beta sin design.md")
    eq(by["2026-01-12-beta"]["design_estado"], None, "beta design_estado None")

    # --- beta: evaluada, sin plan ---
    b = by["2026-01-12-beta"]
    eq(b["eval_estado"], "en-revision", "beta eval_estado")
    eq(b["coste"], "480 €", "beta coste")
    eq(b["fase"], "evaluada", "beta fase")

    # --- gamma: solo spec ---
    g = by["2026-01-14-gamma"]
    eq(g["has_eval"], False, "gamma sin evaluación")
    eq(g["fase"], "solo spec", "gamma fase")
    eq(g["coste"], None, "gamma sin coste")

    # --- render markdown / html ---
    md = bd.render_markdown(inits, FIX)
    contains(md, "| diseño |", "markdown: columna diseño en Artefactos")
    contains(md, "✅ aprobado", "markdown: estado del diseño de alpha")
    contains(md, "Alpha (fixture)", "markdown incluye alpha")
    contains(md, "1.850 €", "markdown incluye coste alpha")
    contains(md, "| Iniciativa |", "markdown tiene tabla")
    html = bd.render_html(inits, FIX)
    contains(html, "Alpha (fixture)", "html incluye alpha")
    contains(html, "Roadmap", "html tiene cabecera")
    assert html.strip().startswith("<!doctype html>"), "html arranca como documento"

    # --- coste de proceso (bloque generacion:, iniciativa coste-generacion) ---
    gen = a.get("generacion")
    assert gen and "spec" in gen, f"alpha debería traer generacion.spec; got {gen}"
    eq(gen["spec"]["fuente"], "medido", "alpha generacion fuente")
    eq(gen["spec"]["tokens_reales"]["salida"], 99000, "alpha generacion tokens salida")
    eq(gen["spec"]["horas_ia"], 1.0, "alpha generacion horas")
    eq(gen["spec"]["eur"], 3.5, "alpha generacion eur")
    eq(g.get("generacion"), None, "gamma sin bloque generacion → None (no 0 inventado)")
    metrics = bd.render_metrics_md(inits, FIX)
    contains(metrics, "Coste de proceso", "métricas incluyen sección de proceso")
    # facturables = 1000 + 200000 + 99000 = 300.000 (la lectura de caché NO cuenta)
    contains(metrics, "300.000 tok", "métricas suman facturables sin cache_lectura")
    contains(metrics, "1h", "métricas muestran duración XhYm")
    contains(metrics, "_sin datos_", "iniciativas sin bloque salen como 'sin datos'")
    eq(bd._xhym(1.53), "1h 32m", "formato XhYm mixto")
    eq(bd._xhym(0.53), "32m", "formato XhYm solo minutos")
    # bloque degradado (fuente: estimado, tokens null) no debe romper el render
    g_est = bd.parse_generacion(
        "---\ngeneracion:\n  fuente: estimado\n  tokens_reales: null\n"
        "  eur: null\n  horas_ia: 0.5\n  duracion: 30m\n---\n\n# x\n")
    eq(g_est["tokens_reales"], None, "tokens null → None (no la cadena 'null')")
    eq(g_est["eur"], None, "eur null → None")
    fake = [{"slug": "x", "titulo": "X", "generacion": {"spec": g_est}, "progreso": None}]
    proc = bd.render_proceso_md(fake)
    contains(proc, "estimado", "proceso renderiza bloque degradado")
    assert "0 tok" not in proc, "tokens null NO debe mostrarse como '0 tok' (0 inventado)"
    contains(proc, "sin tokens", "tokens null → celda 'sin tokens', no un número")

    # robustez del parser (revisión lente B): claves entrecomilladas (JSON pegado tal cual)
    g_json = bd.parse_generacion(
        '---\ngeneracion:\n  fuente: medido\n'
        '  tokens_reales: { "entrada": 1000, "salida": 2000, "cache_creacion": 3000 }\n'
        '  horas_ia: 0.02\n---\n\n# x\n')
    eq(g_json["tokens_reales"]["entrada"], 1000, "dict inline con comillas JSON parsea")
    # bloque anidado estilo YAML estándar
    g_nested = bd.parse_generacion(
        "---\ngeneracion:\n  fuente: medido\n  tokens_reales:\n"
        "    entrada: 111\n    salida: 222\n  horas_ia: 0.01\n---\n\n# x\n")
    eq(g_nested["tokens_reales"]["salida"], 222, "tokens_reales anidado parsea")
    assert "entrada" not in g_nested, "los hijos anidados no contaminan el bloque padre"
    # eur con texto no debe convertirse en número (p. ej. 'verificar 2026' → 2026 €)
    g_txt = bd.parse_generacion(
        "---\ngeneracion:\n  fuente: medido\n  eur: verificar 2026\n---\n\n# x\n")
    eq(g_txt["eur"], None, "eur textual no se convierte en número")
    # comentario a columna 0 dentro del bloque no corta el parseo
    g_com = bd.parse_generacion(
        "---\ngeneracion:\n  fuente: medido\n# comentario suelto\n  horas_ia: 2.0\n---\n\n# x\n")
    eq(g_com["horas_ia"], 2.0, "comentario a columna 0 no corta el bloque")


    # --- vía rápida: carpeta con SOLO tasks.md aparece en el escaneo ---
    import tempfile, shutil
    tmp = tempfile.mkdtemp()
    vr = os.path.join(tmp, "2026-02-01-rapida")
    os.makedirs(vr)
    open(os.path.join(vr, "tasks.md"), "w", encoding="utf-8").write(
        "---\ngeneracion:\n  fuente: medido\n  tokens_reales: { entrada: 5, salida: 10, cache_creacion: 1 }\n"
        "  horas_ia: 0.1\n---\n\n# Checklist de Tareas — Rapida (fixture)\n\n"
        "| | |\n|---|---|\n| **Estado** | completado |\n")
    vr_inits = bd.scan(tmp)
    eq(len(vr_inits), 1, "vía rápida detectada")
    eq(vr_inits[0]["fase"], "vía rápida", "fase derivada de vía rápida")
    contains(vr_inits[0]["titulo"], "Rapida (fixture)", "título desde el ledger")
    assert vr_inits[0]["generacion"], "generacion: de la vía rápida se agrega"
    shutil.rmtree(tmp)

    # --- vía rápida CON spec (backlog implementado): se detecta por el marcador
    # del ledger, no por la ausencia de spec, y no genera aviso espurio de plan ---
    tmp2 = tempfile.mkdtemp()
    vr2 = os.path.join(tmp2, "2026-03-01-rapida-con-spec")
    os.makedirs(vr2)
    open(os.path.join(vr2, "spec.md"), "w", encoding="utf-8").write(
        "---\nspec: rapida-con-spec\nestado: implementada\n---\n\n# Rápida con spec\n")
    open(os.path.join(vr2, "tasks.md"), "w", encoding="utf-8").write(
        "# Checklist de Tareas — Rapida con spec (fixture)\n\n"
        "| | |\n|---|---|\n| **Estado** | completado |\n"
        "| **Plan** | n/a — **vía rápida** sobre [`spec.md`](spec.md) |\n")
    vr2_inits = bd.scan(tmp2)
    eq(len(vr2_inits), 1, "iniciativa de vía rápida con spec escaneada")
    assert vr2_inits[0]["via_rapida"], \
        "vía rápida declarada en el ledger (| **Plan** | n/a — vía rápida) debe detectarse aunque HAYA spec.md"
    eq(vr2_inits[0]["fase"], "vía rápida", "fase de vía rápida con spec presente")
    w2 = bd.warnings_for(vr2_inits)
    assert not any("improvement-plan" in w for w in w2), \
        f"vía rápida declarada NO debe avisar de improvement-plan.md ausente; avisos={w2}"
    shutil.rmtree(tmp2)

    # --- coste de proceso: la ventana del plan la declaran DOS ficheros
    # (improvement-plan.md y tasks.md comparten medición, por diseño del planner):
    # debe contarse UNA vez, no dos ---
    tmp3 = tempfile.mkdtemp()
    dup = os.path.join(tmp3, "2026-04-01-ventana-compartida")
    os.makedirs(dup)
    BLOQUE = ("---\ngeneracion:\n  inicio: 2026-04-01T10:00:00Z\n  fin: 2026-04-01T10:02:00Z\n"
              "  fuente: medido\n  tokens_reales: { entrada: 100, salida: 900, cache_creacion: 0,"
              " cache_lectura: 5000 }\n  horas_ia: 0.10\n---\n\n")
    open(os.path.join(dup, "spec.md"), "w", encoding="utf-8").write(
        "---\nspec: dup\nestado: implementada\n---\n\n# Ventana compartida\n")
    open(os.path.join(dup, "improvement-plan.md"), "w", encoding="utf-8").write(
        BLOQUE + "# Plan\n")
    open(os.path.join(dup, "tasks.md"), "w", encoding="utf-8").write(
        BLOQUE + "# Checklist de Tareas — dup\n\n| | |\n|---|---|\n| **Estado** | completado |\n")
    dup_inits = bd.scan(tmp3)
    md = bd.render_proceso_md(dup_inits)
    assert "1.000 tok" in md or "1000 tok" in md, \
        f"la ventana compartida plan/tasks debe contarse UNA vez (1.000 tok facturables), no 2.000; md={md}"
    assert "2.000 tok" not in md and "2000 tok" not in md, \
        f"doble conteo de la ventana compartida detectado; md={md}"
    shutil.rmtree(tmp3)

    # --- ...pero los bloques ESTIMADOS que comparten fechas de referencia NO se
    # deduplican: son estimaciones distintas por artefacto (defecto propio detectado
    # al calibrar: colapsarlos perdía 0,8 h de coste-generacion) ---
    tmp4 = tempfile.mkdtemp()
    est = os.path.join(tmp4, "2026-05-01-estimados")
    os.makedirs(est)
    def blq(h):
        return ("---\ngeneracion:\n  inicio: 2026-05-01T12:00:00Z\n  fin: 2026-05-01T13:00:00Z\n"
                f"  fuente: estimado\n  tokens_reales: null\n  horas_ia: {h}\n---\n\n")
    open(os.path.join(est, "spec.md"), "w", encoding="utf-8").write(
        blq(0.2) + "---\nspec: est\nestado: implementada\n---\n\n# Estimados\n")
    open(os.path.join(est, "improvement-plan.md"), "w", encoding="utf-8").write(blq(0.3) + "# Plan\n")
    open(os.path.join(est, "tasks.md"), "w", encoding="utf-8").write(
        blq(0.3) + "# Checklist de Tareas — est\n\n| | |\n|---|---|\n| **Estado** | completado |\n")
    md4 = bd.render_proceso_md(bd.scan(tmp4))
    assert "48m" in md4, f"las horas estimadas por artefacto deben sumarse (0,2+0,3+0,3=0,8h=48m); md={md4}"
    shutil.rmtree(tmp4)

    # --- T-17 (E7): conteo de `fuente:` agregado y su línea en el informe de proceso ---
    tmp5 = tempfile.mkdtemp()
    def _ini(slug, fuente):
        d = os.path.join(tmp5, slug)
        os.makedirs(d)
        open(os.path.join(d, "tasks.md"), "w", encoding="utf-8").write(
            "---\ngeneracion:\n  fuente: " + fuente + "\n  horas_ia: 0.2\n"
            "  inicio: 2026-01-01T00:00:00Z\n  fin: 2026-01-01T00:10:00Z\n---\n"
            "# Checklist de Tareas — " + slug + "\n\n| | |\n|---|---|\n| **Estado** | completado |\n")
    _ini("2026-01-01-medida", "medido")
    _ini("2026-01-02-juicio-a", "estimado")
    _ini("2026-01-03-juicio-b", "estimado")
    inits5 = bd.scan(tmp5)
    f = bd.contar_fuentes(inits5)
    eq(f, {"estimados": 2, "medidos": 1, "otros": 0, "total": 3},
       "contar_fuentes tiene que contar TODOS los bloques generacion: por su campo fuente")
    # gap B-12: lo que devuelve es una PARTICION de verdad (las tres cuentas suman el total), y un
    # `generacion:` que no sea un mapa de artefactos no revienta el informe del consumidor
    for gen, esperado in (({"a": {"fuente": "medido"}, "b": {}}, {"estimados": 0, "medidos": 1, "otros": 1, "total": 2}),
                          (["roto"], {"estimados": 0, "medidos": 0, "otros": 1, "total": 1}),
                          ("medido", {"estimados": 0, "medidos": 0, "otros": 1, "total": 1}),
                          (None, {"estimados": 0, "medidos": 0, "otros": 0, "total": 0})):
        got = bd.contar_fuentes([{"generacion": gen}])
        eq(got, esperado, f"contar_fuentes con generacion={gen!r}")
        assert got["estimados"] + got["medidos"] + got["otros"] == got["total"], got
    md5 = bd.render_proceso_md(inits5)
    contains(md5, "2 de 3 bloques `generacion:` con `fuente: estimado`",
             "el informe de proceso tiene que decir el agregado, no solo la fila")
    contains(md5, "1 con `fuente: medido`", "y cuántos SÍ son una medida")
    shutil.rmtree(tmp5)

    # --- avisos: beta es incoherente (spec aprobada, eval en-revision) ---
    warns = bd.warnings_for(inits)
    assert any("2026-01-12-beta" in w and "aprobada" in w for w in warns), \
        f"se esperaba un aviso de incoherencia para beta; avisos={warns}"

    _eval_variantes()
    test_parser_lee_las_claves_de_procedencia()
    test_procedencia_por_iniciativa_separa_medido_sin_medida_y_desconocido()
    test_procedencia_ventana_compartida_no_duplica_tokens()
    test_procedencia_en_el_total_de_cartera_y_en_el_informe()
    test_procedencia_en_json_y_html()
    test_vista_json_es_pura_y_coincide_con_el_json_de_la_cli()
    print(f"OK: {len(inits)} iniciativas, {len(warns)} aviso(s) esperado(s). Todo pasa.")


if __name__ == "__main__":
    try:
        run()
    except AssertionError as e:
        print(f"FALLO: {e}", file=sys.stderr)
        sys.exit(1)
