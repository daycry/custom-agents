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


# --------------------------------------------------- Verificación por tarea (plan-and-diet T-02)

def test_brief_incluye_verificacion(inic):
    """La tarea declara `- **Verificación**: …` → el brief la reproduce literal en su propia sección y
    exige ejecutarla y pegar la salida antes de `DONE`."""
    t = (inic / "tasks.md").read_text(encoding="utf-8")
    t = t.replace("- **Descripción**: hacer la cosa A.\n",
                  "- **Descripción**: hacer la cosa A.\n"
                  "- **Verificación**: `python3 -m pytest -q tests/test_a.py` → `2 passed`\n", 1)
    (inic / "tasks.md").write_text(t, encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    assert "## Verificación (ejecútala al terminar y pega la salida)" in out
    assert "- `python3 -m pytest -q tests/test_a.py` → `2 passed`" in out   # un ítem por línea (T-fix1)
    assert "pega su salida real" in out
    assert "Verificación ejecutada" in out, "el contrato DONE exige la verificación ejecutada"
    assert "no declara `Verificación`" not in out


def test_brief_sin_verificacion_avisa(inic):
    """Sin el campo → sección con la nota «no declara Verificación: propón una» (no se inventa un comando).
    Un `- **Verificación**:` de EJEMPLO dentro de un fence no cuenta."""
    rc, out = _run([str(inic), "T-02", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    assert "la tarea no declara `Verificación`: propón una en tu informe" in out
    assert "## Verificación (ejecútala" not in out
    t = (inic / "tasks.md").read_text(encoding="utf-8")
    t = t.replace("- **Descripción**: hacer la cosa B.\n",
                  "- **Descripción**: hacer la cosa B.\n```md\n- **Verificación**: `falso` → x\n```\n", 1)
    (inic / "tasks.md").write_text(t, encoding="utf-8")
    rc, out = _run([str(inic), "T-02", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0 and "no declara `Verificación`" in out and "> `falso`" not in out


def test_brief_verificacion_sublista_y_ejecutada(inic):
    """[T-fix1, gaps Important #1 y #2] (a) sub-lista bajo el campo → TODOS los ítems en el brief (no solo el
    primero); (b) variante real de plan-and-diet `- **Verificación** (ejecutada … — salida: …): <cmd> → …`
    → se inyecta el COMANDO (no la salida grabada) y se pide re-ejecutarla."""
    t = (inic / "tasks.md").read_text(encoding="utf-8")
    t = t.replace("- **Descripción**: hacer la cosa A.\n",
                  "- **Descripción**: hacer la cosa A.\n- **Verificación**:\n  - `pytest -q tests/a` → `2 passed`\n"
                  "  - `python3 lint.py` → `0 errores`\n", 1)
    t = t.replace("- **Descripción**: hacer la cosa B.\n",
                  "- **Descripción**: hacer la cosa B.\n- **Verificación** (ejecutada 2026-09-03 — salida: `cmp` sin salida · "
                  "`3/3 OK` (7.472 bytes)): `cmp a.yml b.yml` → sin salida · `python3 tests/test_x.py` → `3/3 OK`\n", 1)
    (inic / "tasks.md").write_text(t, encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    sec = out.split("## Verificación (ejecútala")[1].split("## ")[0]
    assert "- `pytest -q tests/a` → `2 passed`" in sec and "- `python3 lint.py` → `0 errores`" in sec, sec
    assert "re-ejecútala" not in sec
    rc, out = _run([str(inic), "T-02", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    sec = out.split("## Verificación (ejecútala")[1].split("## ")[0]
    assert "- `cmp a.yml b.yml` → sin salida" in sec and "- `python3 tests/test_x.py` → `3/3 OK`" in sec, sec
    assert "salida: `cmp` sin salida" not in sec, "la salida grabada NO se inyecta como comando"
    assert "ya ejecutada antes (ejecutada 2026-09-03)" in sec and "re-ejecútala" in sec, sec
    # campo vacío (`- **Verificación**:` sin nada) → nota de «no declara», no una sección vacía
    t2 = (inic / "tasks.md").read_text(encoding="utf-8").replace(
        "- **Verificación**:\n  - `pytest -q tests/a` → `2 passed`\n  - `python3 lint.py` → `0 errores`\n",
        "- **Verificación**:\n", 1)
    (inic / "tasks.md").write_text(t2, encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0 and "no declara `Verificación`" in out


# --- TDD (parity-core T-03): con dev.json `tdd: true` el brief manda seguir la skill `tdd` ---

def _dev_json(tmp_path, data):
    """El proyecto es <raíz>/docs/roadmap/<inic>; la config vive en <raíz>/.claude/dev.json."""
    raiz = tmp_path / "proj"
    (raiz / "docs" / "roadmap" / "2026-01-01-juguete").mkdir(parents=True)
    (raiz / ".claude").mkdir()
    (raiz / ".claude" / "dev.json").write_text(data, encoding="utf-8")
    d = raiz / "docs" / "roadmap" / "2026-01-01-juguete"
    (d / "tasks.md").write_text(TASKS, encoding="utf-8")
    return d


def test_tdd_true_en_dev_json_inyecta_la_skill(tmp_path):
    d = _dev_json(tmp_path, '{"tdd": true}')
    rc, out = _run([str(d), "T-01", "--sin-lint", "--constitucion", str(d / "no.md")])
    assert rc == 0
    assert "## TDD" in out and "skill `tdd`" in out
    assert "RED:" in out, "el brief recuerda la evidencia del rojo que debe devolver"


def test_tdd_false_o_ausente_no_inyecta(tmp_path, inic):
    d = _dev_json(tmp_path, '{"tdd": false}')
    rc, out = _run([str(d), "T-01", "--sin-lint", "--constitucion", str(d / "no.md")])
    assert rc == 0 and "skill `tdd`" not in out
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0 and "skill `tdd`" not in out, "sin dev.json no hay sección TDD"


def test_flag_tdd_fuerza_y_dev_json_corrupto_degrada(tmp_path, inic, capsys):
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--tdd", "--constitucion", str(inic / "no.md")])
    assert rc == 0 and "skill `tdd`" in out, "--tdd fuerza la sección aunque no haya dev.json"
    d = _dev_json(tmp_path, "{ roto")
    rc, out = _run([str(d), "T-01", "--sin-lint", "--constitucion", str(d / "no.md")])
    assert rc == 0 and "skill `tdd`" not in out, "dev.json corrupto → sin TDD, sin bloquear"
    assert "dev.json" in capsys.readouterr().err


# --- design.md (parity-core T-fix1): solo la sección «opción elegida», token-diet ---

DESIGN = """---
design: juguete
estado: aprobado
opcion_elegida: O2
---

# Diseño — juguete

## 1. Contexto y restricciones

Mucho texto de contexto que NO debe viajar al brief.

## 2. Opciones (2-3)

### O1 — Monolito
Descripción larga de O1.

### O2 — Adaptador
Descripción larga de O2.

## 3. Criterios de decisión

1. Reversibilidad.

## 4. Recomendación · opción elegida y por qué

**O2 — Adaptador.** Aísla la integración tras una interfaz; reversible en un sprint.

Descartadas: O1 (acopla el dominio al proveedor).

## 5. Impacto en módulos y ficheros

| Módulo | Cambio |
|---|---|
| `src/adapter.py` | nuevo |
"""


def test_design_inyecta_solo_opcion_elegida(inic):
    (inic / "design.md").write_text(DESIGN, encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    assert "## Diseño (design.md · opción elegida O2)" in out
    assert "O2 — Adaptador" in out and "reversible en un sprint" in out
    assert "Mucho texto de contexto" not in out and "Descripción larga de O1" not in out, "token-diet: solo la sección 4"
    assert "src/adapter.py" not in out


def test_sin_design_no_hay_seccion(inic):
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0 and "## Diseño" not in out


def test_design_borrador_avisa_y_no_inyecta(inic, capsys):
    (inic / "design.md").write_text(DESIGN.replace("estado: aprobado", "estado: borrador").replace("opcion_elegida: O2", "opcion_elegida: pendiente"), encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0 and "## Diseño" not in out
    assert "design.md" in capsys.readouterr().err


# ---------------------------------------------------------------- gaps pendientes (T-03, roles-and-jira-flow)

TASKS_CON_GAPS = TASKS + """
## Revisión de dos lentes — intento 1: 2 gaps (0 Critical, 1 Important, 1 Minor)

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Falta manejar el caso vacío | T-01 | Añadir guard clause | `test_caso_vacio` |
| 2 | Minor | Regex sin anclar: `` `(?:a|b|c)` `` colisiona con `abc` | T-01 | Anclar con `$` | `test_no_colisiona` |
| 3 | Important | Falta la sección de errores | T-02 | Añadir sección | `grep -c errores README.md` |
"""

TASKS_INTENTO_2_LIMPIO = TASKS_CON_GAPS + """
## Revisión de dos lentes — intento 2: sin gaps

Todo corregido y reverificado.
"""


def test_gaps_pendientes_se_inyectan_desde_el_ultimo_intento(inic):
    (inic / "tasks.md").write_text(TASKS_CON_GAPS, encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    assert "## Gaps pendientes de revisión (intento 1" in out
    assert "Falta manejar el caso vacío" in out and "Añadir guard clause" in out
    assert "test_caso_vacio" in out


def test_gaps_solo_de_la_tarea_pedida(inic):
    (inic / "tasks.md").write_text(TASKS_CON_GAPS, encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    assert "Falta la sección de errores" not in out, "ese gap es de T-02, no debe colarse en el brief de T-01"


def test_gaps_pipes_en_backticks_no_trocean_la_fila(inic):
    """Regresión: una celda `` `(?:a|b|c)` `` con `|` internos no debe fragmentar la fila."""
    (inic / "tasks.md").write_text(TASKS_CON_GAPS, encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    assert "`(?:a|b|c)`" in out
    assert "test_no_colisiona" in out, "celda Evidencia de esa misma fila, intacta"


def test_gaps_intento_mas_reciente_sin_gaps_no_inyecta_los_del_anterior(inic):
    (inic / "tasks.md").write_text(TASKS_INTENTO_2_LIMPIO, encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    assert "## Gaps pendientes" not in out, "el intento 2 (el último) está limpio: no reabre el intento 1"


def test_gaps_cabecera_sin_dos_puntos_se_lee_igual_que_jira_flow(inic):
    """Criterio ÚNICO de la cabecera (`REVISION_HDR_PATTERN` de ledger-lint.py): con `:` y sin `:` el
    brief inyecta lo mismo. Antes este parser era laxo y el de `jira-flow.py` exigía `:`, así que una
    cabecera sin `:` daba brief CON gaps y Jira exit 2 sobre el MISMO ledger (T-fix1)."""
    (inic / "tasks.md").write_text(
        TASKS_CON_GAPS.replace("— intento 1: 2 gaps (0 Critical, 1 Important, 1 Minor)",
                               "— intento 1"), encoding="utf-8")
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0
    assert "## Gaps pendientes de revisión (intento 1" in out
    assert "Falta manejar el caso vacío" in out


def test_la_regex_de_cabecera_es_la_canonica_del_kit():
    """El fallback local debe ser copia LITERAL del patrón de ledger-lint.py: si divergen, este test
    lo caza antes de que los dos consumidores vuelvan a leer cabeceras distintas."""
    spec = importlib.util.spec_from_file_location(
        "ledger_lint_t", Path(__file__).parent / "ledger-lint.py")
    ll = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ll)
    assert tb._REVISION_HDR_FALLBACK == ll.REVISION_HDR_PATTERN


def test_gaps_sin_seccion_de_revision_no_inyecta(inic):
    rc, out = _run([str(inic), "T-01", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0 and "## Gaps pendientes" not in out


def test_gaps_tarea_sin_gaps_en_el_ultimo_intento_no_inyecta(inic):
    """T-02 no aparece en la tabla del intento 1 salvo el gap #3 (que sí es suyo) — comprueba el caso
    inverso: pedir el brief de una tarea limpia en un ledger que SÍ tiene gaps (de otra tarea)."""
    tasks_solo_t01 = TASKS_CON_GAPS.replace(
        "| 3 | Important | Falta la sección de errores | T-02 | Añadir sección | `grep -c errores README.md` |\n",
        "")
    (inic / "tasks.md").write_text(tasks_solo_t01, encoding="utf-8")
    rc, out = _run([str(inic), "T-02", "--sin-lint", "--constitucion", str(inic / "no.md")])
    assert rc == 0 and "## Gaps pendientes" not in out
