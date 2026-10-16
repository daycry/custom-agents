#!/usr/bin/env python3
"""Tests de ledger-view.py (proyeccion pura de un `tasks.md`, panel-redesign T-21 y T-22).

Ejecutar:  python3 -m pytest agent-kits/shared/test_ledger_view.py -q
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SCRIPT = HERE / "ledger-view.py"


def _cargar(nombre, fichero):
    spec = importlib.util.spec_from_file_location(nombre, HERE / fichero)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


lv = _cargar("ledger_view", "ledger-view.py")
ll = _cargar("ledger_lint_test", "ledger-lint.py")

LEDGER = """---
verificacion: obligatoria
creado: 2026-10-01
---

# Checklist de Tareas — demo

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-10-01 |

> **⚠️ Ledger canónico de progreso.**

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|------|------------|-------|----------|
| Fase 1 — Base | 1 | 2 | 50% |
| Fase 2 — Cableado | 0 | 3 | 0% |

## Fase 1 — Base

### T-01 — Primera tarea

- **Descripción**: Hace la primera cosa
  y sigue en la línea siguiente.
- **Estado**: completado
- **Tiempo humano**: est. 4,2h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real 1,03h (medido; ventana 19:32–19:50 UTC)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Dependencias**: ninguna
- **Verificación**: `pytest -q` → `passed`
- **Verificación ejecutada** (2026-10-15): `pytest -q` → `3 passed`

**Criterios de aceptación**
- [x] Primer criterio hecho.
- [ ] Segundo criterio pendiente.

- **Cerrada**: 2026-10-15

### T-02 — Segunda tarea

- **Estado**: en-progreso
- **Tiempo IA (ejec.)**: est. 0,3h · real 0,2h (estimado)
- **Dependencias**: T-01, T-03
- **Verificación** (ejecutada 2026-10-02 — salida: 4 passed): `pytest -q` → `passed`

**Criterios de aceptación**
- [ ] Algo.

## Fase 2 — Cableado

### T-03 — Tercera tarea

- **Estado**: 🚧 Bloqueada por terceros
- **Verificación**: `a` → 1 · `b` → 2

**Criterios de aceptación**
- [ ] Algo.

### T-04 — Cuarta tarea (sin estado)

- **Verificación**: lectura

**Criterios de aceptación**
- [ ] Algo.

### T-05 — Quinta tarea con historia archivada

- **Estado**: completado
- **Verificación**: `x` → ok. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `abcdef123456`.

**Criterios de aceptación**
- [x] Hecho.

## Revisión de dos lentes — intento 1: Fase 1 (T-02) — 2 gaps

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Falta validar la entrada vacía | T-02 | pendiente | `pytest -q` rojo |
| 2 | Minor | Mensaje poco claro | T-02 | rebatido con evidencia | `fichero:10` |
| 3 | Minor | Otro gap ya corregido | T-02 | Corregido en T-02 | verde |

## Revisión de dos lentes — intento 2 (Fase 2: T-03): sin paréntesis no se ve

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | No visible | T-03 | pendiente | x |
"""


def proyectar(texto=LEDGER):
    return lv.proyectar(texto)


def tarea(datos, ident):
    return next(t for t in datos["tareas"] if t["id"] == ident)


# --- reutilizacion de los parsers (ADR-016: dueno unico) -------------------------------------------------------

def test_reutiliza_los_parsers_de_ledger_lint_sin_regex_de_cabecera_propio():
    fuente = SCRIPT.read_text(encoding="utf-8")
    for nombre in ("parse_ledger", "secciones_revision", "ultimo_intento_para", "filas_pendientes_de_tarea"):
        assert callable(getattr(lv, nombre)), nombre
        assert getattr(lv, nombre).__code__.co_filename.endswith("ledger-lint.py"), nombre   # la MISMA funcion
    assert "REVISION_HDR" not in fuente and "dos lentes" not in fuente   # ningun tercer lector de cabeceras


def test_el_vocabulario_de_estados_es_el_de_ledger_lint():
    assert set(lv.ESTADOS) == set(ll.ESTADOS) and len(lv.ESTADOS) == 5
    assert lv.VERIFICACION_MAX == ll.VERIFICACION_MAX


# --- estados -------------------------------------------------------------------------------------------------

def test_los_estados_del_vocabulario_se_proyectan_y_los_desconocidos_van_aparte_con_su_literal():
    d = proyectar()
    assert tarea(d, "T-01")["estado"] == "completado" and tarea(d, "T-02")["estado"] == "en-progreso"
    t3 = tarea(d, "T-03")
    assert t3["estado"] is None and t3["literal"] == "bloqueada-por-terceros"
    assert {"id": "T-03", "literal": "bloqueada-por-terceros"} in d["desconocidos"]
    t4 = tarea(d, "T-04")
    assert t4["estado"] is None and t4["literal"] is None
    assert {"id": "T-04", "literal": None} in d["desconocidos"]
    assert d["desconocidos"] == [{"id": "T-03", "literal": "bloqueada-por-terceros"}, {"id": "T-04", "literal": None}]
    assert d["vocabulario"] == ["borrador", "en-progreso", "en-revision", "completado", "cancelado"]


def test_fase_titulo_y_orden_de_las_tareas():
    d = proyectar()
    assert [t["id"] for t in d["tareas"]] == ["T-01", "T-02", "T-03", "T-04", "T-05"]
    assert tarea(d, "T-01")["fase"] == "Fase 1 — Base" and tarea(d, "T-03")["fase"] == "Fase 2 — Cableado"
    assert tarea(d, "T-04")["titulo"] == "Cuarta tarea (sin estado)"
    assert [f["nombre"] for f in d["fases"]] == ["Fase 1 — Base", "Fase 2 — Cableado"]


# --- horas -----------------------------------------------------------------------------------------------------

def test_horas_real_estimado_con_procedencia_y_la_ausencia_es_null_nunca_cero():
    d = proyectar()
    h1 = tarea(d, "T-01")["horas"]
    assert h1["ia"] == {"real": 1.03, "est": 0.5, "fuente": "medido"}
    assert h1["humano"] == {"real": None, "est": 4.2}                       # `—` -> null (CA-13)
    assert h1["supervision"] == {"real": None, "est": 0.1}                  # `n/d` -> null
    assert tarea(d, "T-02")["horas"]["ia"] == {"real": 0.2, "est": 0.3, "fuente": "estimado"}
    h3 = tarea(d, "T-03")["horas"]
    assert h3["ia"] == {"real": None, "est": None, "fuente": None}
    assert h3["humano"] == {"real": None, "est": None} and h3["supervision"] == {"real": None, "est": None}


# --- criterios, verificacion, dependencias, descripcion ---------------------------------------------------------

def test_criterios_con_su_casilla_y_descripcion_con_su_continuacion():
    t = tarea(proyectar(), "T-01")
    assert t["criterios"] == [{"texto": "Primer criterio hecho.", "marcado": True},
                              {"texto": "Segundo criterio pendiente.", "marcado": False}]
    assert t["descripcion"] == "Hace la primera cosa y sigue en la línea siguiente."
    assert tarea(proyectar(), "T-02")["descripcion"] is None


def test_verificacion_con_su_salida_y_dependencias():
    d = proyectar()
    v = tarea(d, "T-01")["verificacion"]
    assert v["texto"] == "`pytest -q` → `passed`" and v["recortada"] is False
    assert v["salida"] == "`pytest -q` → `3 passed`"                       # `- **Verificación ejecutada** (…): …`
    assert tarea(d, "T-02")["verificacion"]["ejecutada"] == "ejecutada 2026-10-02 — salida: 4 passed"
    assert tarea(d, "T-01")["dependencias"] == []
    assert tarea(d, "T-02")["dependencias"] == ["T-01", "T-03"]
    assert tarea(d, "T-03")["verificacion"]["texto"] == "`a` → 1 · `b` → 2"


def test_verificacion_larga_se_recorta_a_verificacion_max_y_lo_dice():
    larga = "`x` → " + "y" * (lv.VERIFICACION_MAX + 500)
    d = proyectar(LEDGER.replace("- **Verificación**: `a` → 1 · `b` → 2", f"- **Verificación**: {larga}"))
    v = tarea(d, "T-03")["verificacion"]
    assert len(v["texto"]) == lv.VERIFICACION_MAX and v["recortada"] is True


def test_una_tarea_sin_verificacion_la_proyecta_como_null():
    d = proyectar("# L\n\n## Fase 1\n\n### T-01 — a\n\n- **Estado**: borrador\n\n**Criterios de aceptación**\n- [ ] a\n")
    assert tarea(d, "T-01")["verificacion"] is None


# --- revision y gaps ----------------------------------------------------------------------------------------

def test_ultima_revision_y_gaps_abiertos_con_su_severidad_y_la_cabecera_sin_parentesis_no_se_ve():
    d = proyectar()
    t2 = tarea(d, "T-02")
    assert t2["revision"]["intento"] == 1 and t2["revision"]["abiertos"] == 1
    assert [g["grado"] for g in t2["gaps"]] == ["Important"]               # el rebatido y el corregido no cuentan
    assert t2["gaps"][0]["gap"] == "Falta validar la entrada vacía" and t2["gaps"][0]["intento"] == 1
    assert tarea(d, "T-03")["revision"] is None and tarea(d, "T-03")["gaps"] == []   # `intento 2 (…)` invisible (GOT)


def test_una_tarea_sin_revision_no_inventa_gaps():
    t = tarea(proyectar(), "T-01")
    assert t["revision"] is None and t["gaps"] == []


# --- historia archivada ----------------------------------------------------------------------------------------

def test_una_tarea_con_historia_en_execution_history_se_marca_archivada_y_solo_enlaza(tmp_path):
    d = proyectar()
    assert tarea(d, "T-05")["archivado"] == {"enlace": "execution-history.md"}
    assert tarea(d, "T-01")["archivado"] is None
    (tmp_path / "tasks.md").write_text(LEDGER, encoding="utf-8")
    (tmp_path / "execution-history.md").write_text("## Archivado\n\nMARCADOR-SOLO-DEL-HISTORICO T-01\n", encoding="utf-8")
    salida = json.dumps(lv.leer(tmp_path), ensure_ascii=False)
    assert "MARCADOR-SOLO-DEL-HISTORICO" not in salida                     # nunca mezcla el histórico (CA-10)


# --- lectura acotada -----------------------------------------------------------------------------------------

def test_leer_un_ledger_normal(tmp_path):
    (tmp_path / "tasks.md").write_text(LEDGER, encoding="utf-8")
    d = lv.leer(tmp_path)
    assert d["status"] == "ok" and len(d["tareas"]) == 5 and d["version"] == 1


def test_leer_sin_ledger(tmp_path):
    d = lv.leer(tmp_path)
    assert d["status"] == "sin_ledger" and d["tareas"] is None


def test_un_ledger_por_encima_de_256_kib_devuelve_fuera_del_tope_sin_cifras(tmp_path):
    (tmp_path / "tasks.md").write_bytes(LEDGER.encode("utf-8") + b"\n" * (256 * 1024))
    d = lv.leer(tmp_path)
    assert d["status"] == "fuera_de_tope" and d["tareas"] is None and d["fases"] is None and d["desconocidos"] is None


def test_un_ledger_ilegible_no_inventa_datos(tmp_path):
    (tmp_path / "tasks.md").write_bytes(b"# L\n\n### T-01 \x80\x81\n- **Estado**: borrador\n")
    d = lv.leer(tmp_path)
    assert d["status"] == "ilegible" and d["tareas"] is None


def test_un_texto_sin_tareas_se_dice(tmp_path):
    d = lv.proyectar("# Nada\n")
    assert d["status"] == "sin_tareas" and d["tareas"] is None


# --- cierre de la tarea (T-22) --------------------------------------------------------------------------------

def test_cerrada_se_extrae_y_su_ausencia_es_null():
    d = proyectar()
    assert tarea(d, "T-01")["cerrada"] == "2026-10-15"
    assert tarea(d, "T-02")["cerrada"] is None
    assert tarea(d, "T-01")["cerrada_invalida"] is None


def test_cerrada_con_formato_invalido_no_se_publica_como_fecha():
    d = proyectar(LEDGER.replace("- **Cerrada**: 2026-10-15", "- **Cerrada**: ayer"))
    t = tarea(d, "T-01")
    assert t["cerrada"] is None and t["cerrada_invalida"] == "ayer"


# --- CLI ----------------------------------------------------------------------------------------------------

def _cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def test_cli_json_de_una_carpeta_y_de_un_fichero(tmp_path):
    (tmp_path / "tasks.md").write_text(LEDGER, encoding="utf-8")
    for destino in (tmp_path, tmp_path / "tasks.md"):
        r = _cli(str(destino), "--json")
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["status"] == "ok"
    texto = _cli(str(tmp_path))
    assert texto.returncode == 0 and "T-01" in texto.stdout


def test_cli_uso_incorrecto_sale_con_2(tmp_path):
    assert _cli().returncode == 2
    r = _cli(str(tmp_path / "no-existe"), "--json")
    assert r.returncode == 0 and json.loads(r.stdout)["status"] == "sin_lectura"   # carpeta inexistente


def test_la_salida_json_cabe_en_utf8_y_es_estable():
    a = json.dumps(proyectar(), ensure_ascii=False, sort_keys=True)
    b = json.dumps(proyectar(), ensure_ascii=False, sort_keys=True)
    assert a == b


def test_el_ledger_real_de_la_iniciativa_se_proyecta_sin_desconocidos():
    ruta = HERE.parents[1] / "docs/roadmap/2026-10-15-panel-redesign/tasks.md"
    if not ruta.is_file():
        pytest.skip("ledger no disponible")
    d = lv.proyectar(ruta.read_text(encoding="utf-8-sig"))
    assert d["status"] == "ok" and d["desconocidos"] == [] and len(d["tareas"]) >= 58
    t = tarea(d, "T-01")
    assert t["estado"] == "completado" and t["horas"]["ia"]["fuente"] in ("medido", "estimado", None)


def _con_revision_de_rango(cabecera, fila_tarea):
    return LEDGER + f"""
## Revisión de dos lentes — intento 1: {cabecera} — 1 gap

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Minor | Algo | {fila_tarea} | pendiente | x |
"""


@pytest.mark.parametrize("cabecera,celda", [("Fase 1 (T-01..T-05)", "T-02"), ("Fase 1 (T-01–T-05)", "T-02"),
                                             ("Fase 1", "T-01..T-05"), ("Fase 1", "T-01–T-05")])
def test_un_rango_de_tareas_cubre_las_tareas_intermedias_en_la_revision(cabecera, celda):
    """F2-7: `T-01..T-05` cita también T-03, no solo los extremos."""
    datos = lv.proyectar(_con_revision_de_rango(cabecera, celda))
    por = {t["id"]: t for t in datos["tareas"]}
    assert por["T-03"]["revision"] is not None and por["T-03"]["revision"]["intento"] == 1
    assert por["T-03"]["revision"]["cabecera"].startswith("## Revisión de dos lentes")


def test_un_rango_en_el_historial_archivado_marca_las_intermedias():
    texto = LEDGER + "\n## Historial archivado\n\n- 2026-10-15 · «Revisión (T-01..T-04)» → [execution-history.md](execution-history.md)\n"
    por = {t["id"]: t for t in lv.proyectar(texto)["tareas"]}
    assert por["T-03"]["archivado"] == {"enlace": "execution-history.md"}
    assert por["T-04"]["archivado"] == {"enlace": "execution-history.md"}


def test_un_guion_seguido_de_un_numero_no_es_un_rango():
    assert lv._expandir("Fase 1 (T-01 — 5 gaps)") == "Fase 1 (T-01 — 5 gaps)"
    assert lv._expandir("T-01..T-03 y T-07-T-08") == "T-01, T-02, T-03 y T-07, T-08"
    assert lv._expandir("T-09..T-02") == "T-09..T-02"


# --- fix2 de la Fase 2: cota agregada de la expansión de rangos (I2-3) ------------------------------------------------

def test_cinco_mil_filas_con_un_rango_enorme_se_proyectan_en_menos_de_2_s():
    """I2-3 (caso adversario de la revisión): 5.000 filas `T-1..T-499` dentro de 256 KB no bloquean la proyección."""
    import time
    filas = "".join(f"| {n} | Minor | x | T-1..T-499 | p | e |\n" for n in range(5000))
    texto = _con_revision_de_rango("Fase 1", "T-01") + filas
    assert len(texto.encode()) <= 256 * 1024
    t0 = time.perf_counter()
    datos = lv.proyectar(texto)
    assert datos["status"] == "ok" and time.perf_counter() - t0 < 2


def test_una_cabecera_con_cientos_de_rangos_no_bloquea_y_lo_marca():
    """I2-3: N copias de `T-00..T-99` agotan el presupuesto global (5.000 ids): el resto no se expande y se AVISA."""
    import time
    cabecera = "Fase 1 (" + " ".join(["T-00..T-99"] * 400) + ")"
    t0 = time.perf_counter()
    datos = lv.proyectar(_con_revision_de_rango(cabecera, "T-02"))
    assert time.perf_counter() - t0 < 2
    assert datos["avisos"] == ["rangos_sin_expandir"]
    assert "avisos" not in lv.proyectar(_con_revision_de_rango("Fase 1 (T-01..T-05)", "T-02"))


def test_el_presupuesto_de_ids_expandidos_es_global_y_el_resto_queda_tal_cual():
    presupuesto = lv._Presupuesto(150)
    assert lv._expandir("T-00..T-99", presupuesto).count("T-") == 100
    assert lv._expandir("T-00..T-99", presupuesto) == "T-00..T-99" and presupuesto.excedido


def test_un_rango_exige_t_a_la_derecha_y_dos_cifras_como_ids_de_tarea():
    assert lv._expandir("T-03… 12 gaps") == "T-03… 12 gaps"
    assert lv._expandir("T-03..12") == "T-03..12"
    assert lv._expandir("T-1..T-4") == "T-1..T-4"                     # `ids_de_tarea` solo casa `T-NN`: no se generan ids que no casan
    assert lv._expandir("T-100..T-102") == "T-100..T-102"


# --- fix3 de la Fase 2: coste de la proyección con muchas tareas y filas (I3-5) -------------------------------------

def _ledger_grande(tareas, filas, secciones=3):
    cuerpo = "## Fase 1 — Base\n\n" + "".join(f"### T-{n:02d} — Tarea {n}\n- **Estado**: borrador\n" for n in range(1, tareas + 1))
    for s in range(1, secciones + 1):
        cuerpo += (f"\n## Revisión de dos lentes — intento {s}: Fase 1 (T-01..T-09) — gaps\n\n"
                   "| # | Grado | Gap | Tarea | Corrección | Evidencia |\n|---|---|---|---|---|---|\n")
        cuerpo += "".join(f"| {n} | Minor | x | T-{(n % 90) + 1:02d} | {'pendiente' if n % 3 else 'corregido'} | e |\n"
                           for n in range(filas // secciones))
    return "# Ledger\n\n" + cuerpo


def test_mil_tareas_y_330_filas_por_seccion_se_proyectan_en_menos_de_2_s():
    """I3-5: el índice id -> secciones/filas se construye una vez por proyección (antes: tareas x filas x ids)."""
    import time
    texto = _ledger_grande(1000, 3300, secciones=10)   # 330 filas por sección
    t0 = time.perf_counter()
    datos = lv.proyectar(texto)
    assert datos["status"] == "ok" and len(datos["tareas"]) == 1000
    assert time.perf_counter() - t0 < 2


def test_el_indice_da_la_misma_revision_y_gaps_que_las_funciones_de_ledger_lint():
    """I3-5: el índice no cambia el resultado: cada tarea sale igual que con `ultimo_intento_para`,
    `seleccionar_seccion` y `filas_pendientes_de_tarea` de `ledger-lint` sobre las mismas secciones."""
    texto = _ledger_grande(30, 60, secciones=3) + (
        "\n## Revisión de dos lentes — intento 4: sin gaps\n\n## Fase 2 — Otra\n"
        "\n## Revisión de dos lentes — intento 4 (Fase 2: T-07): x\n\n"
        "| # | Grado | Gap | Tarea | Corrección | Evidencia |\n|---|---|---|---|---|---|\n| 1 | Important | y | T-07/T-12 | pendiente | e |\n")
    datos = lv.proyectar(texto)
    secciones = lv._secciones_expandidas(ll.secciones_revision(texto))
    for t in datos["tareas"]:
        ultimo = ll.ultimo_intento_para(secciones, [t["id"]])
        _, abiertas = ll.filas_pendientes_de_tarea(secciones, t["id"])
        if ultimo is None:
            assert t["revision"] is None and t["gaps"] == []
            continue
        seccion, _ = ll.seleccionar_seccion(secciones, ultimo, [t["id"]])
        assert t["revision"]["intento"] == ultimo and t["revision"]["abiertos"] == len(abiertas)
        assert t["revision"]["cabecera"] == (seccion["_original"][:160] if seccion else None)
        assert [(g["intento"], g["num"]) for g in t["gaps"]] == [(f["intento"], f["num"]) for f in abiertas]
