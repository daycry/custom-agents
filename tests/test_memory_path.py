#!/usr/bin/env python3
"""El camino de la memoria SE RECORRE — gate determinista y barato (memory-retrieval T-08, spec CA-12).

Afirma que un agente con una tarea de ÁREA X **recibe** la entrada de área X por los dos caminos por
los que le llega contexto, y que NO recibe las de otras áreas (si recibe todo, no hay enrutado):

  1. el BRIEF del subagente (`agent-kits/shared/task-brief.py`, sección «Memoria técnica del proyecto»,
     T-05): una tarea `- **Tipo**: devops` trae el ADR de área «Hooks / …»; una `- **Tipo**: test` trae
     el gotcha de área «Tests / …»; ninguna trae la lección de «Estimación / calibración»;
  2. el ARRANQUE de sesión (`hooks/session-context.sh`, bloque «Memoria técnica del área activa», T-06):
     con una iniciativa activa cuyo título habla de hooks, el `additionalContext` trae ese ADR y no la
     lección.

Y afirma el TOPE de cada camino (≤ 2.400 caracteres en el brief, ≤ 1.200 en el hook) como constante y
como medida, no solo la presencia.

El enrutado del brief que se cubre es el del campo `- **Tipo**:` DE VERDAD: los títulos de las dos tareas
del ledger de fixture no contienen ningún token de área («El arranque de sesión inyecta contexto»,
«Comprobar el comportamiento del arranque»: ni «hook» ni «fixture» ni «test»), así que la ÚNICA vía por la
que ADR-001 y GOT-001 llegan a su brief es `--tipo-tarea devops|test`. Antes (revisión intento 1, gap 11)
los títulos eran «El hook de arranque…» y «Suite del fixture» y el brief los enrutaba por el título:
quitar `--tipo-tarea` de `task-brief.py` dejaba la suite en 7 passed. El H1 del ledger sí habla de hooks,
porque ese es el camino del hook de sesión (título + slug, sin `Tipo`).

Todo sobre un corpus de `tmp_path` (dos áreas + una ajena y una iniciativa de mentira), sin red, sin
`claude` en PATH y sin clave: los dos caminos son scripts locales lanzados como subproceso, igual que
los lanza el orquestador.

MUTANTES (cómo verlo rojo — un test que pasa con y sin la inyección no prueba nada):
  - brief:  en `task-brief.py`, haz que `_memoria_tecnica()` devuelva `None` en su primera línea (o
    comenta la llamada `memoria = _memoria_tecnica(...)` en `main()`). `test_el_brief_de_una_tarea_de_area_x_trae_la_entrada_de_area_x`
    falla con «brief de T-01 (tipo devops, área Hooks / implementer): no llegó ADR-001».
  - hook:   en `session-context.sh`, borra el bloque `(4)` (o pon `MEMORIA_TOPE_CHARS = 0`).
    `test_el_arranque_con_una_iniciativa_activa_de_area_x_inyecta_la_entrada_de_area_x` falla con
    «additionalContext (área Hooks / implementer): no llegó ADR-001».
  - tope:   sube `MEMORIA_TOPE_CHARS` en cualquiera de los dos → el test del tope falla por la constante.
  - Tipo:   en `task-brief.py`, quita `["--tipo-tarea", tipo]` de la orden a `knowledge-find.py` →
    `test_el_brief_de_una_tarea_de_area_x_trae_la_entrada_de_area_x` y el negativo fallan («no llegó
    ADR-001» / «no llegó GOT-001»): el brief ya no enruta por `Tipo` y los títulos no lo rescatan.

Ejecutar: python3 -m pytest -q tests/test_memory_path.py
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEF = os.path.join(ROOT, "agent-kits", "shared", "task-brief.py")
HOOK = os.path.join(ROOT, "hooks", "session-context.sh")
BASH = shutil.which("bash")

BRIEF_TOPE = 2400      # spec CA-08: ≤ 600 tokens de memoria en el brief
HOOK_TOPE = 1200       # spec CA-10: ≤ 300 tokens de memoria al arrancar
HOOK_TOTAL = 9500      # TOPE_CHARS del hook (bajo los 10.000 del contrato oficial)

AREA_X, ID_X = "Hooks / implementer", "ADR-001"          # área de la tarea devops y de la iniciativa activa
AREA_T, ID_T = "Tests / fixtures", "GOT-001"             # área de la tarea test
AREA_AJENA, ID_AJENA = "Estimación / calibración", "LES-001"   # nadie la pide: no debe llegar

LEDGER = """---
tasks: hooks-de-sesion
estado: en-progreso
creado: 2026-01-01
actualizado: 2026-01-02
---

# Checklist de Tareas — Hooks de sesión con memoria del área

| | |
|---|---|
| **Estado** | en-progreso |

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|------|------------|-------|----------|
| Fase 1 — Hooks | 0 | 2 | 0% |
| **TOTAL** | **0** | **2** | **0%** |

## Fase 1 — Hooks

**Estado**: en-progreso

### T-01 — El arranque de sesión inyecta contexto

- **Descripción**: añadir el bloque al arranque.
- **Estado**: en-progreso
- **Tipo**: devops
- **Verificación**: `bash hooks/x.sh < payload` → JSON válido

**Criterios de aceptación**
- [ ] el hook emite JSON

### T-02 — Comprobar el comportamiento del arranque

- **Descripción**: probarlo.
- **Estado**: borrador
- **Tipo**: test
- **Verificación**: `pytest -q` → passed

**Criterios de aceptación**
- [ ] la suite pasa
"""


def _fm(**kv):
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in kv.items()) + "---\n"


def corpus(raiz):
    """`docs/knowledge/` con tres entradas de tres áreas; el área del ADR vive SOLO en el índice (como los reales)."""
    kn = raiz / "docs" / "knowledge"
    for d in ("adr", "gotchas", "lessons"):
        (kn / d).mkdir(parents=True)
    (kn / "adr" / "ADR-001-deny-solo-agente.md").write_text(
        _fm(id="ADR-001", titulo="Un deny solo con alcance de agente", estado="aceptada (validada: usuario, 2026-01-02)",
            fecha="2026-01-02") + "\n# ADR-001\n\nEl deny va en el frontmatter del agente.\n", encoding="utf-8")
    (kn / "gotchas" / "GOT-001-fixture-git.md").write_text(
        _fm(id="GOT-001", tipo="gotcha", area=AREA_T, estado="aceptada (validada: usuario, 2026-01-03)",
            fuente="2026-01-03-otra/tasks.md") + "\n## Una fixture con git sin identidad revienta en CI\n\n- Causa: sin user.name.\n",
        encoding="utf-8")
    (kn / "lessons" / "LES-001-evaluator-revision-cara.md").write_text(
        _fm(id="LES-001", tipo="leccion", area=AREA_AJENA, estado="aceptada (validada: usuario, 2026-01-04)",
            fuente="2026-01-04-estimacion/retro.md") + "\n## evaluator\n\n- El coste está en la revisión.\n", encoding="utf-8")
    (kn / "README.md").write_text(
        "# índice\n\n| Entrada | ID | Tipo | Área | Estado | Fuente |\n|---|---|---|---|---|---|\n"
        f"| [`adr/ADR-001-deny-solo-agente.md`](adr/ADR-001-deny-solo-agente.md) — un deny solo con alcance de agente | ADR-001 | ADR | {AREA_X} | aceptada (validada: usuario, 2026-01-02) | `2026-01-02-otra/tasks.md` |\n"
        f"| [`gotchas/GOT-001-fixture-git.md`](gotchas/GOT-001-fixture-git.md) — una fixture con git sin identidad revienta en CI | GOT-001 | Gotcha | {AREA_T} | aceptada (validada: usuario, 2026-01-03) | `2026-01-03-otra/tasks.md` |\n"
        f"| [`lessons/LES-001-evaluator-revision-cara.md`](lessons/LES-001-evaluator-revision-cara.md) — el coste está en la revisión | LES-001 | Lección | {AREA_AJENA} | aceptada (validada: usuario, 2026-01-04) | `2026-01-04-estimacion/retro.md` |\n",
        encoding="utf-8")
    return kn


@pytest.fixture
def proyecto(tmp_path):
    raiz = tmp_path / "proj"
    inic = raiz / "docs" / "roadmap" / "2026-01-01-hooks-de-sesion"
    inic.mkdir(parents=True)
    (inic / "tasks.md").write_text(LEDGER, encoding="utf-8")
    (raiz / ".claude").mkdir()
    corpus(raiz)
    return raiz, inic


def _env(raiz, tmp_path):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return {"CLAUDE_PLUGIN_ROOT": ROOT, "CLAUDE_PROJECT_DIR": str(raiz), "HOME": str(home),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}


def brief(inic, tid):
    r = subprocess.run([sys.executable, BRIEF, str(inic), tid], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout


def seccion_memoria(texto):
    """La sección que añade el brief (un elemento que acaba en línea en blanco), o ''."""
    m = re.search(r"^## Memoria técnica del proyecto.*?(?=\n\n## |\n\n> \(Sin improvement|\Z)", texto, re.S | re.M)
    return m.group(0) if m else ""


def arranque(raiz, tmp_path, source="startup"):
    r = subprocess.run([BASH, HOOK], input=json.dumps({"hook_event_name": "SessionStart", "source": source}),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=_env(raiz, tmp_path),
                       cwd=str(raiz), timeout=60)
    assert r.returncode == 0, r.stderr
    lineas = [l for l in r.stdout.splitlines() if l.strip()]
    assert len(lineas) == 1, r.stdout
    return json.loads(lineas[0])["hookSpecificOutput"]["additionalContext"]


def bloque_memoria(ctx):
    i = ctx.find("Memoria técnica del área activa")
    return "" if i < 0 else ctx[ctx.rfind("\n", 0, i) + 1:]


# ------------------------------------------------------------------ camino 1: el brief

def test_el_brief_de_una_tarea_de_area_x_trae_la_entrada_de_area_x(proyecto):
    _raiz, inic = proyecto
    sec = seccion_memoria(brief(inic, "T-01"))
    assert ID_X in sec, f"brief de T-01 (tipo devops, área {AREA_X}): no llegó {ID_X} — el camino brief no se recorre"
    assert AREA_X in sec and "aceptada" in sec, "cada acierto lleva su área y el estado delante"
    assert "--show" in sec, "el detalle se abre por ID: progressive disclosure, no la entrada entera"


def test_el_brief_de_una_tarea_de_area_y_no_recibe_la_entrada_de_area_x(proyecto):
    """Aserto NEGATIVO: si una tarea de test recibiera el ADR de hooks (o la lección de estimación),
    no habría enrutado, solo un volcado."""
    _raiz, inic = proyecto
    sec_test = seccion_memoria(brief(inic, "T-02"))
    assert ID_T in sec_test, f"brief de T-02 (tipo test, área {AREA_T}): no llegó {ID_T}"
    assert ID_X not in sec_test, f"brief de T-02 (área {AREA_T}) recibió {ID_X} (área {AREA_X}): no hay enrutado"
    sec_devops = seccion_memoria(brief(inic, "T-01"))
    assert ID_T not in sec_devops, f"brief de T-01 (área {AREA_X}) recibió {ID_T} (área {AREA_T}): no hay enrutado"
    for sec in (sec_test, sec_devops):
        assert ID_AJENA not in sec, f"{ID_AJENA} ({AREA_AJENA}) no la pidió nadie y llegó: no hay enrutado"


def test_el_brief_respeta_el_tope_de_600_tokens(proyecto):
    spec = importlib.util.spec_from_file_location("task_brief_mp", BRIEF)
    tb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tb)
    assert tb.MEMORIA_TOPE_CHARS == BRIEF_TOPE, "el tope del brief es una constante con test (spec CA-08)"
    _raiz, inic = proyecto
    sec = seccion_memoria(brief(inic, "T-01"))
    assert 0 < len(sec) <= BRIEF_TOPE, len(sec)


# ------------------------------------------------------------------ camino 2: el arranque de sesión

pytestmark_hook = pytest.mark.skipif(BASH is None, reason="sin bash: el hook no se puede lanzar")


@pytestmark_hook
def test_el_arranque_con_una_iniciativa_activa_de_area_x_inyecta_la_entrada_de_area_x(proyecto, tmp_path):
    raiz, _inic = proyecto
    for source in ("startup", "resume", "compact"):
        ctx = arranque(raiz, tmp_path, source)
        bloque = bloque_memoria(ctx)
        assert ID_X in bloque, f"[{source}] additionalContext (área {AREA_X}): no llegó {ID_X} — el camino del hook no se recorre"
        assert ID_AJENA not in bloque, f"[{source}] llegó {ID_AJENA} ({AREA_AJENA}), que no es del área de la iniciativa activa"
        assert "aceptada" in bloque and "--show" in bloque


@pytestmark_hook
def test_el_arranque_respeta_el_tope_de_300_tokens_y_el_total_del_hook(proyecto, tmp_path):
    src = open(HOOK, encoding="utf-8").read()
    m = re.search(r"^MEMORIA_TOPE_CHARS\s*=\s*(\d+)", src, re.M)
    assert m and int(m.group(1)) == HOOK_TOPE, "el tope del hook es una constante con test (spec CA-10)"
    raiz, _inic = proyecto
    ctx = arranque(raiz, tmp_path)
    bloque = bloque_memoria(ctx)
    assert 0 < len(bloque) <= HOOK_TOPE, len(bloque)
    assert len(ctx) <= HOOK_TOTAL


@pytestmark_hook
def test_sin_iniciativa_activa_el_arranque_no_inyecta_memoria(proyecto, tmp_path):
    """El enrutado del hook es por la iniciativa ACTIVA: con el ledger cerrado, nada que enrutar."""
    raiz, inic = proyecto
    (inic / "tasks.md").write_text(LEDGER.replace("estado: en-progreso", "estado: completado", 1)
                                   .replace("| **Estado** | en-progreso |", "| **Estado** | completado |", 1)
                                   .replace("- **Estado**: en-progreso", "- **Estado**: completado", 1)
                                   .replace("- **Estado**: borrador", "- **Estado**: completado", 1)
                                   .replace("- [ ]", "- [x]").replace("| 0 | 2 | 0% |", "| 2 | 2 | 100% |")
                                   .replace("| **0** | **2** | **0%** |", "| **2** | **2** | **100%** |")
                                   .replace("**Estado**: en-progreso", "**Estado**: completado"), encoding="utf-8")
    r = subprocess.run([BASH, HOOK], input=json.dumps({"hook_event_name": "SessionStart", "source": "startup"}),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=_env(raiz, tmp_path),
                       cwd=str(raiz), timeout=60)
    assert r.returncode == 0
    assert "Memoria técnica del área activa" not in r.stdout


def test_los_dos_caminos_no_usan_red_ni_claude():
    """Los dos scripts del camino son locales: ningún `claude`, `urllib`, `requests` ni socket en su fuente."""
    for p in (BRIEF, HOOK, os.path.join(ROOT, "agent-kits", "shared", "knowledge-find.py")):
        src = open(p, encoding="utf-8").read()
        for prohibido in ("import urllib", "import requests", "import socket", "claude -p", "http://", "https://"):
            assert prohibido not in src.replace("code.claude.com/docs", ""), f"{os.path.basename(p)} usa {prohibido!r}"
