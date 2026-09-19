# -*- coding: utf-8 -*-
"""jira-review-comments (2026-09-19): UN solo dueño del evento Jira `revision`/`gaps` de cada intento.

El síntoma que lo motivó: `/dev-cycle` hacía todo el flujo y ningún comentario de revisión llegaba a
las tareas de Jira. El mecanismo (`jira-flow.py`) funcionaba; lo que fallaba era la PROPIEDAD: cuatro
textos (skill `adversarial-review`, tabla de `dev-cycle`, `review-publish.md`, `ROLES.md`) nombraban
cuatro dueños distintos y nadie lo ejecutaba. Estos tests leen los ficheros REALES (un fixture
inventado probaría lo que el autor cree que dicen) y, además, ejecutan `jira-flow.py` sobre un ledger
de prueba para dejar constancia de que el comentario por intento sí se genera cuando alguien lo pide.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "adversarial-review", "SKILL.md")
DEVCYCLE = os.path.join(ROOT, "commands", "dev-cycle.md")
REVIEW_PUBLISH = os.path.join(ROOT, "skills", "jira-sync", "references", "review-publish.md")
ROLES = os.path.join(ROOT, "docs", "agents", "ROLES.md")
JIRA_FLOW = os.path.join(ROOT, "skills", "jira-sync", "scripts", "jira-flow.py")
JIRA_SYNC_SKILL = os.path.join(ROOT, "skills", "jira-sync", "SKILL.md")
SHARED_README = os.path.join(ROOT, "agent-kits", "shared", "README.md")
FLOWS_ES = os.path.join(ROOT, "docs", "FLOWS.md")
FLOWS_EN = os.path.join(ROOT, "docs", "en", "FLOWS.md")


def _leer(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _seccion(texto, cabecera_regex, hasta_regex=r"^#{1,3} "):
    """Texto entre la cabecera que casa y la siguiente cabecera markdown."""
    m = re.search(cabecera_regex, texto, re.M)
    assert m, f"no encuentro la cabecera {cabecera_regex!r}"
    resto = texto[m.end():]
    n = re.search(hasta_regex, resto, re.M)
    return resto[: n.start()] if n else resto


# --- 1. La skill es la dueña y su paso es ejecutable ---------------------------------------------

def test_la_skill_ejecuta_el_evento_de_cada_intento_con_el_comando_completo():
    s6 = _seccion(_leer(SKILL), r"^### 6\. Salida y traza")
    assert "jira-flow.py" in s6 or '"$JF"' in s6, "la skill no nombra el script que publica el intento"
    assert re.search(r"--event\s+revision\|gaps", s6), "falta el evento revision|gaps en el comando"
    assert "--actor reviewer" in s6, "el comentario va firmado por el reviewer (--actor reviewer)"
    assert re.search(r"--intento\s+N", s6), "--intento N es obligatorio en revision/gaps"
    assert re.search(r"POR CADA intento", s6), "el evento es por intento, no al cierre"
    assert re.search(r"lo publica ESTA skill", s6), "la skill debe declararse dueña única del evento"


def test_la_skill_no_delega_el_evento_en_el_orquestador():
    s6 = _seccion(_leer(SKILL), r"^### 6\. Salida y traza")
    ofensivas = [l for l in s6.splitlines() if re.search(r"el orquestador dispara", l)]
    assert not ofensivas, f"segundo dueño reabierto en SKILL.md §6: {ofensivas}"


# --- 2. /dev-cycle nombra al mismo dueño y no remite a pasos inexistentes --------------------------

def test_dev_cycle_tabla_de_eventos_nombra_a_la_skill_en_revision_y_gaps():
    t = _leer(DEVCYCLE)
    for evento in ("revision", "gaps"):
        fila = next((l for l in t.splitlines() if l.startswith(f"| `{evento}` |")), None)
        assert fila, f"falta la fila `{evento}` en la tabla de eventos de dev-cycle.md"
        celdas = [c.strip() for c in fila.strip("|").split("|")]
        assert "adversarial-review" in celdas[2], f"fila `{evento}`: el dueño debe ser adversarial-review, no {celdas[2]!r}"
        assert "no" in celdas[2] and "orquestador" in celdas[2], f"fila `{evento}`: debe excluir explícitamente al orquestador"


def test_dev_cycle_no_cita_un_paso_9_ni_un_comentario_final():
    t = _leer(DEVCYCLE)
    assert "Paso 9" not in t, "jira-sync no tiene Paso 9: el ciclo de eventos es el Paso 7"
    assert "comentario FINAL en Jira" not in t, "el comentario es POR INTENTO, no final"
    assert re.search(r"lo ejecuta la propia skill", t), "dev-cycle debe decir que el comentario lo ejecuta la skill, no el orquestador"


# --- 3. La referencia de jira-sync y la matriz de roles no reabren otro dueño ----------------------

def test_review_publish_nombra_a_la_skill_como_ejecutor_unico():
    t = _leer(REVIEW_PUBLISH)
    bloque = _seccion(t, r"^## `revision` / `gaps`")
    assert "adversarial-review" in bloque, "review-publish.md debe nombrar a la skill como quien ejecuta el paso"
    assert re.search(r"dueño único", bloque), "review-publish.md debe declarar el dueño único"
    assert not re.search(r"^El agente \*\*revisor\*\*.*escribe", bloque, re.M), \
        "el agente reviewer es solo lectura: no puede ser quien publica"


def test_roles_no_atribuye_la_publicacion_al_orquestador_ni_al_implementer():
    t = _leer(ROLES)
    fila_reviewer = next(l for l in t.splitlines() if l.startswith("| **reviewer** |"))
    assert "lo publica la skill `adversarial-review`" in fila_reviewer, fila_reviewer[-200:]
    assert "lo publica el orquestador/implementer" not in fila_reviewer
    fila_skill = next(l for l in t.splitlines() if l.startswith("| **adversarial-review** |"))
    assert "publica en Jira el evento `revision`/`gaps`" in fila_skill, fila_skill[:300]


# --- 5. jira-sync SKILL.md: --actor es la FIRMA, no el ejecutor (gap #7) --------------------------

def test_jira_sync_skill_distingue_actor_firma_de_ejecutor():
    t = _leer(JIRA_SYNC_SKILL)
    s7 = _seccion(t, r"^## Paso 7")
    assert "adversarial-review" in s7, "Paso 7 debe nombrar a la skill como ejecutor de revision/gaps"
    assert re.search(r"--actor.{0,40}FIRMA", s7, re.S) or re.search(r"FIRMA.{0,40}--actor", s7, re.S), \
        "Paso 7 debe aclarar que --actor es la firma del comentario, no el ejecutor"
    ofensiva = re.search(r"dispara su actor fijo", s7)
    assert not ofensiva, "Paso 7 vuelve a decir que el actor es quien dispara el evento"


# --- 6. «Paso 9» no existe en ningún sitio del repo vivo (gap #8) ---------------------------------

def test_ningun_fichero_vivo_remite_a_un_paso_9_de_jira_sync():
    for ruta in (SKILL, DEVCYCLE, REVIEW_PUBLISH, ROLES, JIRA_SYNC_SKILL, SHARED_README, FLOWS_ES, FLOWS_EN):
        t = _leer(ruta)
        assert "Paso 9" not in t, f"{ruta}: jira-sync no tiene Paso 9 (es el Paso 7, por intento)"


def test_flows_es_y_en_nombran_a_la_skill_en_la_tabla_de_eventos(): # gap #18
    """(gap #18, jira-review-comments fix2) FLOWS.md y FLOWS.en.md tienen su PROPIA tabla de eventos
    (`revision`/`gaps`) con la columna «Quién dispara»: debe nombrar a `adversarial-review`, nunca al
    orquestador — hasta ahora ningún test cubría estos dos ficheros, así que una regresión aquí
    pasaba desapercibida aunque los otros 6 ficheros estuvieran bien."""
    for ruta in (FLOWS_ES, FLOWS_EN):
        t = _leer(ruta)
        for evento in ("revision", "gaps"):
            fila = next((l for l in t.splitlines() if l.startswith(f"| `{evento}`")), None)
            assert fila, f"{ruta}: falta la fila `{evento}` en la tabla de eventos"
            assert "adversarial-review" in fila, f"{ruta}: fila `{evento}` no nombra a adversarial-review: {fila}"


def test_paso_9_no_aparece_en_ningun_md_vivo_del_repo(): # gap #19
    """(gap #19, jira-review-comments fix2) La lista fija de 6-8 ficheros de arriba es frágil: un
    `Paso 9` colado en OTRO `.md` vivo (p. ej. `CONTINUE-HERE.md`, que se lee el primero al retomar)
    no lo detectaba nadie. Grep repo-wide de todo `.md`, excluyendo los registros fechados que NO se
    reescriben (`docs/roadmap/`, `docs/knowledge/`, `CHANGELOG*`) y lo generado (`interop/`)."""
    excluidos_dir = (
        os.path.join(ROOT, "docs", "roadmap"),
        os.path.join(ROOT, "docs", "knowledge"),
        os.path.join(ROOT, "interop"),
    )
    ofensivos = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
        if any(dirpath == d or dirpath.startswith(d + os.sep) for d in excluidos_dir):
            continue
        for fn in filenames:
            if not fn.endswith(".md") or fn.startswith("CHANGELOG"):
                continue
            ruta = os.path.join(dirpath, fn)
            lineas = _leer(ruta).splitlines()
            for i, linea in enumerate(lineas):
                # "Paso 9" a secas es legítimo como ejemplo generico de numeración (CONVENTIONS.md,
                # ADR-008: «Paso 7`, `Paso 9`…»); el hueco real de dueño era esta combinación con
                # jira-sync/adversarial-review (el bug original: "comentario FINAL en Jira, Paso
                # 9") — salvo que la MISMA ventana ya diga RESUELTO (nota histórica ya corregida,
                # p. ej. CONTINUE-HERE.md).
                if "Paso 9" not in linea or not re.search(r"jira-sync|adversarial-review|Jira", linea):
                    continue
                ventana = "\n".join(lineas[max(0, i - 3):i + 4])
                if "RESUELTO" in ventana:
                    continue
                ofensivos.append(f"{ruta}: {linea.strip()}")
    assert not ofensivos, f"«Paso 9» de jira-sync (obsoleto: ahora es el Paso 7) sigue vivo en: {ofensivos}"


def test_shared_readme_no_atribuye_review_report_template_al_comentario_de_jira():
    t = _leer(SHARED_README)
    fila = next(l for l in t.splitlines() if l.startswith("| `review-report.template.md`"))
    assert "informe de revisión" in fila.lower() and "ledger" in fila.lower(), fila
    assert "Paso 9" not in fila, fila


# --- 4. El mecanismo funciona: lo que faltaba era el dueño ---------------------------------------

LEDGER_MINIMO = """---
verificacion: obligatoria
---
# Checklist de Tareas — demo

## Fase 1 — Demo

### T-01 — Tarea demo
- **Estado**: en-progreso
- **Verificación**: `true` → ok

**Criterios de aceptación**
- [ ] algo

## Revisión de dos lentes — intento 1: Fase 1 (T-01) — 1 gap (0 Critical, 1 Important, 0 Minor), lentes A+B

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Falta validar el host del endpoint | T-01 | pendiente | Lente B |
"""


def test_jira_flow_genera_el_comentario_del_intento_con_la_tabla_de_gaps(tmp_path):
    root = tmp_path
    (root / ".claude").mkdir()
    (root / ".claude" / "jira.json").write_text(json.dumps({"enabled": True, "site": "https://example.atlassian.net", "project": "DEMO"}), encoding="utf-8")
    carpeta = root / "docs" / "roadmap" / "2026-01-01-demo"
    carpeta.mkdir(parents=True)
    ledger = carpeta / "tasks.md"
    ledger.write_text(LEDGER_MINIMO, encoding="utf-8")
    # el manifiesto vive junto a jira.json (`.claude/jira-state.json`), como lo deja el volcado real de jira-sync
    (root / ".claude" / "jira-state.json").write_text(json.dumps({"tasks": {"T-01": {"issueKey": "DEMO-7"}}}), encoding="utf-8")

    r = subprocess.run([sys.executable, JIRA_FLOW, "plan", "--ledger", str(ledger), "--event", "gaps",
                        "--actor", "reviewer", "--task", "T-01", "--intento", "1", "--root", str(root), "--json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(root))
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["jira"] == "activado" and d["issueKey"] == "DEMO-7"
    tipos = [op["tipo"] for op in d["ops"]]
    assert tipos == ["etiqueta", "transicion", "comentario"], tipos
    cuerpo = d["ops"][-1]["cuerpo"]
    assert "Revisión de dos lentes — intento 1" in cuerpo
    assert "Falta validar el host del endpoint" in cuerpo, "la tabla de gaps del intento viaja en el comentario"
    assert "intento 2 de 3" in cuerpo, "el pie anuncia el siguiente intento del bucle"
    assert "[custom-agents · reviewer]" in cuerpo, "firmado por el reviewer"
