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
