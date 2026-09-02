#!/usr/bin/env python3
"""Tests de progress-report.py (línea de progreso determinista del ledger, live-visibility).

Ejecutar:  python3 -m pytest agent-kits/shared/test_progress_report.py -q
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SCRIPT = HERE / "progress-report.py"

_SPEC = importlib.util.spec_from_file_location("progress_report", SCRIPT)
pr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pr)

DOS_FASES = """---
tasks: demo
estado: en-progreso       # comentario
---
# Checklist de Tareas — demo

| | |
|---|---|
| **Estado** | en-progreso |

> **⚠️ Ledger canónico de progreso.**

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|------|------------|-------|----------|
| Fase 1 — Núcleo | 2 | 2 | 100% |
| Fase 2 — Cableado | 0 | 2 | 0% |

## Fase 1 — Núcleo

### T-01 — primera tarea

- **Estado**: completado
- **Tiempo IA (ejec.)**: est. 0,5h · real 0,7h (medido)

**Criterios de aceptación**
- [x] a

### T-02 — segunda tarea

- **Estado**: completado
- **Tiempo IA (ejec.)**: est. 0,5h · real 0,5h (medido)

**Criterios de aceptación**
- [x] b

## Fase 2 — Cableado

### T-03 — tercera tarea

- **Estado**: en-progreso
- **Tiempo IA (ejec.)**: est. 0,3h · real —

**Criterios de aceptación**
- [ ] c

### T-04 — cuarta tarea

- **Estado**: borrador

**Criterios de aceptación**
- [ ] d
"""

SIN_REALES = """# Checklist — sin reales

| **Estado** | borrador |

## Fase 1 — Única

### T-01 — algo

- **Estado**: borrador
- **Tiempo IA (ejec.)**: est. 0,3h · real —

**Criterios de aceptación**
- [ ] x
"""

COMPLETADO = """---
estado: completado
---
## Fase 1 — Cierre

### T-01 — fin

- **Estado**: completado

**Criterios de aceptación**
- [x] x
"""

CORRUPTO = "esto no es un ledger\n| tabla rota | \n### sin id\n"

ESTIMADO = """---
estado: en-progreso
---
## Fase 1 — Cierre

### T-01 — hecho

- **Estado**: completado
- **Tiempo IA (ejec.)**: est. 0,5h · real 0,5h (estimado)

**Criterios de aceptación**
- [x] x

### T-02 — mixto

- **Estado**: en-progreso
- **Tiempo IA (ejec.)**: est: 1h · real: 1h30m (estimado)

**Criterios de aceptación**
- [ ] y
"""


def run(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def ledger(tmp_path, nombre, texto):
    d = tmp_path / "docs" / "roadmap" / nombre
    d.mkdir(parents=True)
    p = d / "tasks.md"
    p.write_text(texto, encoding="utf-8")
    return p


# ------------------------------------------------------------------ line

def test_line_dos_fases_formato_exacto(tmp_path):
    p = ledger(tmp_path, "2026-09-02-demo", DOS_FASES)
    code, out, _ = run("line", str(p))
    assert code == 0
    assert out.strip() == ("📋 demo · T-02/4 completadas (50%) · fase 2/2 «Cableado» · "
                           "en curso: T-03 tercera tarea · IA real 1h 12m")


def test_line_sin_reales_omite_tramo_ia(tmp_path):
    p = ledger(tmp_path, "2026-09-02-vacio", SIN_REALES)
    code, out, _ = run("line", str(p))
    assert code == 0
    assert "IA real" not in out
    assert "en curso" not in out           # ninguna tarea en-progreso
    assert out.strip() == "📋 vacio · T-00/1 completadas (0%) · fase 1/1 «Única»"


def test_line_json(tmp_path):
    p = ledger(tmp_path, "2026-09-02-demo", DOS_FASES)
    code, out, _ = run("line", str(p), "--json")
    assert code == 0
    d = json.loads(out)
    assert (d["completadas"], d["total"], d["pct"]) == (2, 4, 50)
    assert d["fase"] == {"indice": 2, "total": 2, "nombre": "Cableado"}
    assert d["en_curso"] == {"id": "T-03", "titulo": "tercera tarea"}
    assert d["ia_real_h"] == 1.2 and d["ia_real_fmt"] == "1h 12m"
    assert d["linea"].startswith("📋 demo ·")


def test_line_corrupto_no_explota(tmp_path):
    p = ledger(tmp_path, "2026-09-02-roto", CORRUPTO)
    code, out, err = run("line", str(p))
    assert code == 2 and out == "" and "roto" in err


def test_line_fichero_inexistente():
    code, _, err = run("line", "/no/existe/tasks.md")
    assert code == 1 and "no existe" in err


def test_slug_desde_directorio_o_frontmatter(tmp_path):
    p = ledger(tmp_path, "2026-09-02-mi-slug", DOS_FASES)
    assert pr.resumir(str(p))["slug"] == "mi-slug"
    q = tmp_path / "tasks.md"           # sin carpeta con fecha → frontmatter `tasks:`
    q.write_text(DOS_FASES, encoding="utf-8")
    assert pr.resumir(str(q))["slug"] in ("demo", tmp_path.name)


# ------------------------------------------------------------------ active

def test_active_lista_solo_en_progreso_y_salta_corruptos(tmp_path):
    ledger(tmp_path, "2026-09-01-a", DOS_FASES)
    ledger(tmp_path, "2026-09-02-b", COMPLETADO)
    ledger(tmp_path, "2026-09-03-c", CORRUPTO)
    root = tmp_path / "docs" / "roadmap"
    code, out, err = run("active", "--root", str(root))
    assert code == 0
    lines = out.strip().splitlines()
    assert len(lines) == 1 and lines[0].startswith("📋 a ·")
    assert "saltado" in err and "2026-09-03-c" in err


def test_active_sin_activas(tmp_path):
    ledger(tmp_path, "2026-09-02-b", COMPLETADO)
    root = tmp_path / "docs" / "roadmap"
    code, out, _ = run("active", "--root", str(root))
    assert code == 0 and out.strip() == "sin iniciativas en progreso"
    code, out, _ = run("active", "--root", str(root), "--json")
    assert code == 0 and json.loads(out) == {"activas": []}


def test_active_root_inexistente_exit_0(tmp_path):
    code, out, _ = run("active", "--root", str(tmp_path / "nada"))
    assert code == 0 and out.strip() == "sin iniciativas en progreso"


def test_active_estado_por_tabla_si_no_hay_frontmatter(tmp_path):
    texto = DOS_FASES.split("---\n", 2)[2]     # quita el frontmatter → manda la tabla
    assert not texto.startswith("---")
    ledger(tmp_path, "2026-09-02-t", texto)
    code, out, _ = run("active", "--root", str(tmp_path / "docs" / "roadmap"))
    assert code == 0 and out.startswith("📋 t ·")


# ------------------------------------------------------------------ session

def test_session_sin_activas_linea_neutra(tmp_path):
    ledger(tmp_path, "2026-09-02-b", COMPLETADO)
    code, out, _ = run("session", "--root", str(tmp_path))
    assert code == 0 and out.strip() == pr.LINEA_NEUTRA
    assert len(out.strip().splitlines()) == 1


def test_session_con_activas_bloque_acotado(tmp_path):
    ledger(tmp_path, "2026-09-02-demo", DOS_FASES)
    code, out, _ = run("session", "--root", str(tmp_path))
    assert code == 0
    lines = out.strip().splitlines()
    assert len(lines) <= 15
    assert lines[0].startswith("Roadmap en progreso")
    assert any(l.startswith("- 📋 demo ·") for l in lines)
    assert any("en-progreso: T-03 tercera tarea" in l for l in lines)
    assert lines[-1].startswith("Ledger canónico: docs/roadmap/2026-09-02-demo/tasks.md")
    assert "retoma desde la tarea en-progreso" in lines[-1]


def test_session_sin_roadmap_exit_0(tmp_path):
    code, out, _ = run("session", "--root", str(tmp_path))
    assert code == 0 and out.strip() == pr.LINEA_NEUTRA


# ------------------------------------------------------------------ revisión intento 1

def test_bom_utf8_no_oculta_la_iniciativa(tmp_path):
    p = ledger(tmp_path, "2026-09-02-bom", DOS_FASES)
    p.write_bytes(b"\xef\xbb\xbf" + DOS_FASES.encode("utf-8"))
    assert pr.resumir(str(p))["estado"] == "en-progreso"
    code, out, _ = run("active", "--root", str(tmp_path / "docs" / "roadmap"))
    assert code == 0 and out.startswith("📋 bom ·")


def test_horas_estimadas_se_rotulan_ia_est(tmp_path):
    p = ledger(tmp_path, "2026-09-02-est", ESTIMADO)
    r = pr.resumir(str(p))
    assert r["ia_fuente"] == "estimado" and r["ia_real_h"] == 2.0     # 0,5 + 1h30m
    assert pr.linea(r).endswith("IA est. 2h")
    assert "IA real" not in pr.linea(r)


def test_horas_medidas_ignoran_las_estimadas():
    ll = pr._ll
    parsed = ll.parse_ledger(DOS_FASES.replace(
        "real 0,5h (medido)", "real 0,5h (estimado)"))
    t1, t2 = parsed["tareas"][0], parsed["tareas"][1]
    assert (t1["ia_real_h"], t1["ia_real_fuente"]) == (0.7, "medido")
    assert (t2["ia_real_h"], t2["ia_real_fuente"]) == (0.5, "estimado")


@pytest.mark.parametrize("campo,esperado", [
    ("est. 0,3h · real 1,2h (medido)", (0.3, 1.2)),
    ("est. 1h30m · real 1h30m", (1.5, 1.5)),
    ("est: 2h · real: 2h", (2.0, 2.0)),
    ("est. 0,35h · real —", (0.35, None)),
    ("real 45m", (None, None)),          # sin horas → no se interpreta
])
def test_parse_horas(campo, esperado):
    assert pr._ll._parse_horas(campo) == esperado


def test_session_lee_usage_state_del_root_no_del_cwd(tmp_path):
    ledger(tmp_path, "2026-09-02-demo", DOS_FASES)
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "usage-state.json").write_text(json.dumps({
        "docs/roadmap/2026-09-02-demo/T-03": {"inicio": "2026-09-02T08:00:00Z", "offsets": {}},
        "docs/roadmap/2026-09-02-demo/T-01": {"inicio": "2026-09-01T08:00:00Z", "ultimoCierre": "x"},
    }), encoding="utf-8")
    code, out, _ = run("session", "--root", str(tmp_path))   # cwd = repo, root = tmp_path
    assert code == 0
    assert "usage-meter: marcadores abiertos → docs/roadmap/2026-09-02-demo/T-03" in out
    assert "T-01" not in [l for l in out.splitlines() if "marcadores" in l][0]


# ------------------------------------------------------------------ unidades

@pytest.mark.parametrize("nombre,esperado", [
    ("Fase 2 — Núcleo", "Núcleo"),
    ("Fase única — visibilidad en vivo", "visibilidad en vivo"),
    ("Fase 3: cierre", "cierre"),
    ("Fase 4", "Fase 4"),
])
def test_nombre_fase(nombre, esperado):
    assert pr.nombre_fase(nombre) == esperado


def test_fmt_horas():
    assert pr.fmt_horas(1.2) == "1h 12m"
    assert pr.fmt_horas(0.15) == "9m"
    assert pr.fmt_horas(2.0) == "2h"


def test_titulo_con_negrita_interior_sale_sin_asteriscos(tmp_path):
    """Deuda de live-visibility (saldada en debt-cleanup T-01b): `### T-XX — **Bold** resto` se
    mostraba con los `**` en la línea de progreso. Ahora el parser quita el énfasis interior."""
    ledger = DOS_FASES.replace("### T-03 — tercera tarea", "### T-03 — **Bold** resto del título")
    p = tmp_path / "docs" / "roadmap" / "2026-01-01-demo" / "tasks.md"
    p.parent.mkdir(parents=True)
    p.write_text(ledger, encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "line", str(p)], capture_output=True, text=True)
    assert r.returncode == 0
    assert "T-03 Bold resto del título" in r.stdout, r.stdout
    assert "**" not in r.stdout
    # también en el parser compartido (ledger-lint.parse_ledger), que es la fuente del título
    data = pr.resumir(p)
    assert data["en_curso"] == {"id": "T-03", "titulo": "Bold resto del título"}
