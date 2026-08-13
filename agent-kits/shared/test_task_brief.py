#!/usr/bin/env python3
"""Tests de task-brief.py (brief determinista para subagentes frescos, sdd-hardening C-08).

Ejecutar:  python3 -m pytest agent-kits/shared/test_task_brief.py -q
"""
import importlib.util
import io
import contextlib
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "task_brief", Path(__file__).parent / "task-brief.py")
tb = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tb)

TASKS = """# Checklist de Tareas — juguete

| | |
|---|---|
| **Estado** | en-progreso |

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|------|------------|-------|----------|
| Fase 1 — Núcleo | 0 | 2 | 0% |
| **TOTAL** | **0** | **2** | **0%** |

## Fase 1 — Núcleo

**Estado**: en-progreso

### T-01 — primera tarea

- **Descripción**: hacer la cosa A.
- **Estado**: en-progreso

**Criterios de aceptación**
- [ ] la cosa A funciona

### T-02 — segunda tarea

- **Descripción**: hacer la cosa B.
- **Estado**: borrador

**Criterios de aceptación**
- [ ] la cosa B funciona
"""

PLAN = """# juguete

## Resumen ejecutivo

Bla.

## Arquitectura de la solución

- Pieza X habla con pieza Y.

## Riesgos

Ninguno.
"""


def _run(args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = tb.main(args)
    return rc, buf.getvalue()


@pytest.fixture()
def inic(tmp_path):
    d = tmp_path / "2026-01-01-juguete"
    d.mkdir()
    (d / "tasks.md").write_text(TASKS, encoding="utf-8")
    (d / "improvement-plan.md").write_text(PLAN, encoding="utf-8")
    return d


def test_brief_extrae_tarea_fase_y_arquitectura(inic):
    rc, out = _run([str(inic), "T-01", "--sin-lint",
                    "--constitucion", str(inic / "no-existe.md")])
    assert rc == 0
    assert "T-01 — primera tarea" in out and "la cosa A funciona" in out
    assert "T-02" not in out.split("## La tarea")[1].split("## Arquitectura")[0], \
        "el brief NO incluye otras tareas (brief-only)"
    assert "Fase 1 — Núcleo" in out
    assert "Pieza X habla con pieza Y" in out
    assert "Constitución" not in out, "sin constitución no se inventa sección"
    for estado in ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"):
        assert estado in out, f"el contrato de retorno incluye {estado}"


def test_brief_con_constitucion(inic, tmp_path):
    c = tmp_path / "CONSTITUTION.md"
    c.write_text("# Constitución\n- Prohibido el estado global.\n", encoding="utf-8")
    rc, out = _run([str(inic), "T-02", "--sin-lint", "--constitucion", str(c)])
    assert rc == 0
    assert "Prohibido el estado global" in out
    assert "la cosa B funciona" in out


def test_tarea_inexistente_error_claro(inic, capsys):
    rc, _ = _run([str(inic), "T-99", "--sin-lint",
                  "--constitucion", str(inic / "no.md")])
    assert rc == 1
    assert "T-99 no encontrada" in capsys.readouterr().err


def test_id_invalido(inic, capsys):
    rc, _ = _run([str(inic), "tarea-uno", "--sin-lint"])
    assert rc == 1


def test_ledger_invalido_detiene(inic, capsys):
    # estado fuera de vocabulario → ledger-lint debe fallar → exit 2
    t = (inic / "tasks.md").read_text(encoding="utf-8")
    (inic / "tasks.md").write_text(t.replace("- **Estado**: borrador",
                                             "- **Estado**: casi-hecho"), encoding="utf-8")
    rc, _ = _run([str(inic), "T-01", "--constitucion", str(inic / "no.md")])
    assert rc == 2
    assert "ledger inválido" in capsys.readouterr().err


def test_via_rapida_sin_plan(inic):
    (inic / "improvement-plan.md").unlink()
    rc, out = _run([str(inic), "T-01", "--sin-lint",
                    "--constitucion", str(inic / "no.md")])
    assert rc == 0
    assert "vía rápida" in out


# ------------------------------------------------- robustez (revisión lente B)

TASKS_FENCE = """# Tareas

## Fase 1 — Núcleo

### T-01 — con ejemplo en fence

- **Descripción**: documentar la plantilla.
- **Estado**: en-progreso

Ejemplo de plantilla:

```markdown
### T-02 — ejemplo DENTRO del fence (no es una tarea real)
- [ ] criterio del ejemplo
```

**Criterios de aceptación**
- [ ] criterio REAL uno de T-01
- [ ] criterio REAL dos de T-01

### T-02 — segunda tarea real

- **Descripción**: hacer B.
- **Estado**: borrador

**Criterios de aceptación**
- [ ] criterio real de T-02

## Apéndice

### T-03 — tarea fuera de fase

- **Descripción**: hacer C.
- **Estado**: borrador

**Criterios de aceptación**
- [ ] criterio de T-03
"""


@pytest.fixture()
def inic_fence(tmp_path):
    d = tmp_path / "2026-01-02-fence"
    d.mkdir()
    (d / "tasks.md").write_text(TASKS_FENCE, encoding="utf-8")
    return d


def test_fence_no_trunca_criterios(inic_fence):
    """Bug ALTA de la revisión: un encabezado de EJEMPLO dentro de ``` cortaba el
    chunk y el brief salía SIN criterios (el subagente sin contrato)."""
    rc, out = _run([str(inic_fence), "T-01", "--sin-lint",
                    "--constitucion", str(inic_fence / "no.md")])
    assert rc == 0
    assert "criterio REAL uno de T-01" in out and "criterio REAL dos de T-01" in out
    assert "segunda tarea real" not in out, "el chunk no debe comerse T-02"


def test_fence_no_confunde_tarea(inic_fence):
    """El '### T-02' de dentro del fence NO es la tarea T-02 real."""
    rc, out = _run([str(inic_fence), "T-02", "--sin-lint",
                    "--constitucion", str(inic_fence / "no.md")])
    assert rc == 0
    assert "segunda tarea real" in out and "criterio real de T-02" in out
    assert "no es una tarea real" not in out.split("## La tarea")[1].split("## Contrato")[0]


def test_tarea_bajo_seccion_no_fase_sin_contexto_enganoso(inic_fence):
    """Una tarea bajo '## Apéndice' no hereda 'Fase 1' como contexto."""
    rc, out = _run([str(inic_fence), "T-03", "--sin-lint",
                    "--constitucion", str(inic_fence / "no.md")])
    assert rc == 0
    assert "Contexto de fase" not in out, "sin fase real no se inventa contexto"


def test_prefijo_t1_vs_t13(tmp_path):
    d = tmp_path / "2026-01-03-prefijo"
    d.mkdir()
    (d / "tasks.md").write_text(
        "## Fase 1 — X\n\n### T-1 — corta\n\n- **Estado**: borrador\n\n"
        "**Criterios de aceptación**\n- [ ] a\n\n"
        "### T-13 — larga\n\n- **Estado**: borrador\n\n"
        "**Criterios de aceptación**\n- [ ] b\n", encoding="utf-8")
    rc, out = _run([str(d), "T-1", "--sin-lint", "--constitucion", str(d / "no.md")])
    assert rc == 0 and "T-1 — corta" in out and "T-13" not in out.split("## La tarea")[1]


# ---------- personas de dominio (iniciativa subagent-personas) ----------

PERSONA_DB = "Piensa en migraciones REVERSIBLES y en los datos que ya existen."


@pytest.fixture()
def inic_personas(tmp_path):
    d = tmp_path / "2026-02-01-personas"
    d.mkdir()
    pdir = tmp_path / "personas"
    pdir.mkdir()
    (pdir / "db.md").write_text(PERSONA_DB, encoding="utf-8")
    return d, pdir


def _tasks_con_tipo(tipo_linea):
    return ("## Fase 1 — X\n\n### T-01 — tarea\n\n"
            "- **Descripción**: hacer algo.\n"
            f"{tipo_linea}"
            "- **Estado**: borrador\n\n"
            "**Criterios de aceptación**\n- [ ] a\n")


def test_persona_inyectada_con_tipo(inic_personas):
    """Tarea con `- **Tipo**: db` → el brief incluye la persona del catálogo."""
    d, pdir = inic_personas
    (d / "tasks.md").write_text(_tasks_con_tipo("- **Tipo**: db\n"), encoding="utf-8")
    rc, out = _run([str(d), "T-01", "--sin-lint", "--personas-dir", str(pdir),
                    "--constitucion", str(d / "no.md")])
    assert rc == 0
    assert "## Persona de dominio (tipo: db)" in out
    assert PERSONA_DB in out
    # la persona va ANTES de la tarea (enmarca el trabajo, no lo interrumpe)
    assert out.index("Persona de dominio") < out.index("## La tarea")


def test_sin_tipo_subagente_generico(inic_personas):
    """Sin etiqueta Tipo → brief genérico, sin sección de persona (default intacto)."""
    d, pdir = inic_personas
    (d / "tasks.md").write_text(_tasks_con_tipo(""), encoding="utf-8")
    rc, out = _run([str(d), "T-01", "--sin-lint", "--personas-dir", str(pdir),
                    "--constitucion", str(d / "no.md")])
    assert rc == 0 and "Persona de dominio" not in out


def test_tipo_desconocido_degrada_con_aviso(inic_personas, capsys):
    """Tipo sin persona en el catálogo → aviso en stderr + brief genérico, exit 0
    (degradación, no bloqueo)."""
    d, pdir = inic_personas
    (d / "tasks.md").write_text(_tasks_con_tipo("- **Tipo**: cobol\n"), encoding="utf-8")
    rc, out = _run([str(d), "T-01", "--sin-lint", "--personas-dir", str(pdir),
                    "--constitucion", str(d / "no.md")])
    err = capsys.readouterr().err
    assert rc == 0 and "Persona de dominio" not in out
    assert "cobol" in err and "persona" in err.lower()


def test_tipo_placeholder_ignorado(inic_personas):
    """Un `Tipo` con placeholder de plantilla ({{...}}) se trata como ausente."""
    d, pdir = inic_personas
    (d / "tasks.md").write_text(
        _tasks_con_tipo("- **Tipo**: {{frontend / backend / db}}\n"), encoding="utf-8")
    rc, out = _run([str(d), "T-01", "--sin-lint", "--personas-dir", str(pdir),
                    "--constitucion", str(d / "no.md")])
    assert rc == 0 and "Persona de dominio" not in out


def test_tipo_case_insensitive(inic_personas):
    """`- **Tipo**: DB` (mayúsculas) encuentra personas/db.md."""
    d, pdir = inic_personas
    (d / "tasks.md").write_text(_tasks_con_tipo("- **Tipo**: DB\n"), encoding="utf-8")
    rc, out = _run([str(d), "T-01", "--sin-lint", "--personas-dir", str(pdir),
                    "--constitucion", str(d / "no.md")])
    assert rc == 0 and "## Persona de dominio (tipo: db)" in out


def test_tipo_dentro_de_fence_ignorado(inic_personas):
    """Un `- **Tipo**: db` de EJEMPLO dentro de un bloque de código de la tarea NO
    inyecta persona (hallazgo lente B: mismo bug de fences que los encabezados)."""
    d, pdir = inic_personas
    (d / "tasks.md").write_text(
        "## Fase 1 — X\n\n### T-01 — tarea\n\n"
        "- **Descripción**: hacer algo.\n"
        "- **Estado**: borrador\n\n"
        "**Criterios de aceptación**\n- [ ] a\n\n"
        "**Notas**: así se etiqueta una tarea:\n\n"
        "```markdown\n### T-99 — ejemplo\n- **Tipo**: db\n```\n",
        encoding="utf-8")
    rc, out = _run([str(d), "T-01", "--sin-lint", "--personas-dir", str(pdir),
                    "--constitucion", str(d / "no.md")])
    assert rc == 0 and "Persona de dominio" not in out


def test_catalogo_real_completo():
    """Cada etiqueta documentada tiene su persona en agent-kits/shared/personas/
    (catálogo corto por diseño: 6 personas)."""
    pdir = Path(__file__).parent / "personas"
    for tipo in ("frontend", "backend", "db", "devops", "test", "docs"):
        f = pdir / f"{tipo}.md"
        assert f.is_file(), f"falta personas/{tipo}.md"
        assert f.read_text(encoding="utf-8").strip(), f"personas/{tipo}.md vacía"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
