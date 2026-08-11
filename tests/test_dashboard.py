#!/usr/bin/env python3
"""Tests del generador roadmap-dashboard (sin dependencias; assert + salida).

Ejecuta:  python tests/test_dashboard.py
Sale 0 si todo pasa, 1 si algo falla. Protege el parser frente a cambios que
rompan la lectura de spec.md / evaluation.md o la coherencia de estados.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "roadmap-dashboard", "scripts"))
FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "roadmap")

import build_dashboard as bd  # noqa: E402


def eq(got, exp, msg):
    assert got == exp, f"{msg}: esperado {exp!r}, obtenido {got!r}"


def contains(text, needle, msg):
    assert needle in text, f"{msg}: no contiene {needle!r}"


def run():
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

    # --- avisos: beta es incoherente (spec aprobada, eval en-revision) ---
    warns = bd.warnings_for(inits)
    assert any("2026-01-12-beta" in w and "aprobada" in w for w in warns), \
        f"se esperaba un aviso de incoherencia para beta; avisos={warns}"

    print(f"OK: {len(inits)} iniciativas, {len(warns)} aviso(s) esperado(s). Todo pasa.")


if __name__ == "__main__":
    try:
        run()
    except AssertionError as e:
        print(f"FALLO: {e}", file=sys.stderr)
        sys.exit(1)
