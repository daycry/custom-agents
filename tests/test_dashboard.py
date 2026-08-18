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
