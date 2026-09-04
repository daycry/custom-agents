#!/usr/bin/env python3
"""Tests de `jira-flow.py` (roles-and-jira-flow T-02). Sin red, sin modelo: ledger fixture en
tmp_path; el script solo LEE el ledger y rellena plantillas fijas — nunca llama al conector.

Ejecutar: python3 -m pytest -q skills/jira-sync/scripts/test_jira_flow.py
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "jira-flow.py")


def _mod():
    spec = importlib.util.spec_from_file_location("jira_flow", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


jf = _mod()

LEDGER = """---
tasks: demo
descripcion: Iniciativa de prueba para jira-flow.
estado: en-progreso
creado: 2026-09-03
actualizado: 2026-09-03
via: rapida
verificacion: obligatoria
generacion:
  fuente: estimado
---

# Checklist de Tareas — demo (vía rápida)

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|------|------------|-------|----------|
| Fase única | 2 | 2 | 100% |

## Fase única

### T-01 — Endpoint de health-check

- **Descripción**: Añade `GET /health` que devuelve 200 con el estado de la base de datos. Cubre el criterio CA-01.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 1,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,20h · real 0,25h (medido)
- **Supervisión**: est. 0,05h · real 0,06h (medido)
- **Archivos**: `app/health.py` (nuevo), `tests/test_health.py` (nuevo), `app/routes.py`
- **Verificación** (ejecutada 2026-09-03 — salida: `3 passed`): `python3 -m pytest -q tests/test_health.py` → 3 passed.

**Criterios de aceptación**
- [x] `GET /health` devuelve 200 con `{"status":"ok"}`.

### T-02 — Actualizar el README con el nuevo endpoint

- **Descripción**: Documenta `GET /health` en el README del proyecto, sin código.
- **Estado**: completado
- **Tiempo humano**: est. 0,3h · real 0,3h (estimado)
- **Archivos**: `README.md`
- **Verificación**: `grep -c health README.md` → 1.

**Criterios de aceptación**
- [x] El README menciona `/health`.

## Revisión de dos lentes — intento 1: 3 gaps corregidos (0 Critical, 2 Important, 1 Minor)

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Falta validar que la DB responde antes de devolver 200 | T-01 | Añadido `db.ping()` con timeout | `test_health_falla_si_db_cae` |
| 2 | Minor | Regex de rutas con alternancia sin anclar: `` `(?:health|ready|live)` `` colisiona con `/healthcheck` | T-01 | Ancla con `$` al final del patrón | `test_ruta_no_colisiona_con_healthcheck` |
| 3 | Important | El README no explica el código 503 | T-02 | Añadido párrafo sobre 503 | `grep -c 503 README.md` |

## Revisión de dos lentes — intento 2: sin gaps

Todo corregido y reverificado; 3 ejecuciones de la suite en verde.
"""


@pytest.fixture
def ledger(tmp_path):
    """Ledger fixture + `.claude/jira.json` con `enabled: true` al lado: el script solo publica con
    el opt-in puesto (T-fix1), así que sin esta config todo evento daría `ops: []`."""
    (tmp_path / ".claude").mkdir(exist_ok=True)
    (tmp_path / ".claude" / "jira.json").write_text('{"enabled": true}', encoding="utf-8")
    p = tmp_path / "tasks.md"
    p.write_text(LEDGER, encoding="utf-8")
    return str(p)


def _run(*args, cwd=None):
    """El script resuelve `.claude/jira.json` desde cwd hacia arriba (misma resolución que
    `worklog.py`). Los tests corren con cwd = carpeta del ledger, donde la fixture deja el opt-in;
    `cwd=` explícito para los casos que prueban otra resolución."""
    if cwd is None:
        for i, a in enumerate(args):
            if a == "--ledger" and i + 1 < len(args):
                cwd = os.path.dirname(os.path.abspath(args[i + 1]))
    r = subprocess.run([sys.executable, SCRIPT, "plan", *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=cwd)
    return r.returncode, r.stdout, r.stderr


def _state_con_claves(ledger, **claves):
    """Manifiesto `jira-state.json` junto al ledger con `T-XX → issueKey` (en `--batch` el issue no
    se pasa por `--issue`: sale del manifiesto, como en el volcado real)."""
    claves = claves or {"T-01": "PROJ-59", "T-02": "PROJ-60"}
    p = os.path.join(os.path.dirname(os.path.abspath(ledger)), "jira-state.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"tasks": {k: {"issueKey": v} for k, v in claves.items()}}, f)
    return p


def _plan_json(*args, cwd=None):
    code, out, err = _run(*args, "--json", cwd=cwd)
    assert code == 0, f"exit {code}\n{out}\n{err}"
    return json.loads(out)


# ---------------------------------------------------------------- implementado

def test_implementado_comentario_firmado_con_datos_del_ledger(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01", "--fecha", "2026-09-03")
    assert plan["evento"] == "implementado" and plan["tareas"] == ["T-01"]
    cuerpo = next(o for o in plan["ops"] if o["tipo"] == "comentario")["cuerpo"]
    assert "> 🤖 **[custom-agents · implementer]** · implementador · 2026-09-03" in cuerpo
    assert "GET /health" in cuerpo and "app/health.py" in cuerpo and "3 passed" in cuerpo
    assert "pendiente de revisión de dos lentes y `qa`" in cuerpo


def test_implementado_worklog_usa_horas_medidas_del_ledger(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01", "--issue", "PROJ-59")
    wl = next(o for o in plan["ops"] if o["tipo"] == "worklog")
    cmd = wl["comando"]
    assert "--ia-real" in cmd and cmd[cmd.index("--ia-real") + 1] == "0.25"
    assert "--sup-real" in cmd and cmd[cmd.index("--sup-real") + 1] == "0.06"
    assert "--apply" not in cmd, "el plan es una previsualización; --apply lo añade el orquestador tras confirmar"


def test_implementado_tarea_sin_tiempo_ia_usa_fallback_humano(ledger):
    """T-02 no declara «Tiempo IA (ejec.)»: el worklog cae al tiempo humano (real→est)."""
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-02", "--issue", "PROJ-60")
    wl = next(o for o in plan["ops"] if o["tipo"] == "worklog")
    cmd = wl["comando"]
    assert "--human-real" in cmd and cmd[cmd.index("--human-real") + 1] == "0.3"
    assert "--ia-real" not in cmd and "--ia-est" not in cmd


def test_implementado_etiqueta_por_agente(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01")
    et = next(o for o in plan["ops"] if o["tipo"] == "etiqueta")
    assert et["add"] == ["ca-implementer"]


def test_implementado_batch_agrupa_un_comentario_y_dos_worklogs(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01,T-02", "--batch")
    comentarios = [o for o in plan["ops"] if o["tipo"] == "comentario"]
    worklogs = [o for o in plan["ops"] if o["tipo"] == "worklog"]
    assert len(comentarios) == 1, "UNA llamada agrupada por evento, no un comentario por tarea"
    assert len(worklogs) == 2
    assert "T-01" in comentarios[0]["cuerpo"] and "T-02" in comentarios[0]["cuerpo"]


# ---------------------------------------------------------------- arrancar / aprobado

def test_arrancar_transiciona_a_en_curso_sin_comentario(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "arrancar", "--actor", "implementer", "--task", "T-01")
    assert not any(o["tipo"] == "comentario" for o in plan["ops"])
    trans = next(o for o in plan["ops"] if o["tipo"] == "transicion")
    assert trans["objetivo_statuscategory"] == "indeterminate"


def test_aprobado_lo_dispara_el_orquestador_con_evidencia_y_cierra_firmando(ledger):
    """`aprobado` es del ORQUESTADOR (no de `qa`) y exige evidencia: revisión limpia + `--qa-verde`.
    Orden fijo etiqueta → transición → comentario, y el cierre firmado `ca-orquestador` (T-fix1)."""
    plan = _plan_json("--ledger", ledger, "--event", "aprobado", "--actor", "orquestador",
                      "--task", "T-01", "--qa-verde", "--fecha", "2026-09-03")
    assert [o["tipo"] for o in plan["ops"]] == ["etiqueta", "transicion", "comentario"]
    assert plan["ops"][0]["add"] == ["ca-orquestador"]
    assert plan["ops"][1]["objetivo_statuscategory"] == "done"
    assert plan["ops"][1]["objetivo_logico"] == "done"
    assert "statusCategory" in plan["ops"][1]["regla"]  # GOT-004: nunca por nombre/id
    cuerpo = plan["ops"][2]["cuerpo"]
    assert "> 🤖 **[custom-agents · orquestador]**" in cuerpo
    assert "intento 2" in cuerpo   # el ÚLTIMO intento del ledger, el que está limpio


def test_aprobado_con_actor_qa_es_rechazado_diciendo_que_actor_espera(ledger):
    code, out, err = _run("--ledger", ledger, "--event", "aprobado", "--actor", "qa",
                          "--task", "T-01", "--qa-verde")
    assert code == 2
    assert "lo dispara `orquestador`" in err and "actor esperado para `aprobado`" in err


def test_aprobado_sin_qa_verde_no_emite_nada(ledger):
    """Antes `aprobado` emitía la transición a Done SIEMPRE, sin comprobar nada."""
    code, out, err = _run("--ledger", ledger, "--event", "aprobado", "--actor", "orquestador",
                          "--task", "T-01", "--json")
    assert code == 2
    payload = json.loads(out)
    assert payload["ops"] == []
    assert "qa-gate.py" in payload["error"][0] and "--qa-verde" in payload["error"][0]


def test_aprobado_bloqueado_si_el_ultimo_intento_deja_gaps_pendientes(ledger, tmp_path):
    """Último intento con una fila de gap sin corrección → nada de Done; con `descartado
    (rebatido)` sí se puede cerrar (es una decisión tomada, no un gap abierto)."""
    texto = LEDGER.replace(
        "## Revisión de dos lentes — intento 2: sin gaps\n\n"
        "Todo corregido y reverificado; 3 ejecuciones de la suite en verde.\n",
        "## Revisión de dos lentes — intento 2: 2 gaps\n\n"
        "| # | Grado | Gap | Tarea | Corrección | Evidencia |\n|---|---|---|---|---|---|\n"
        "| 1 | Critical | Sigue sin validar el timeout | T-01 | pendiente | — |\n"
        "| 2 | Minor | Nombre poco claro | T-02 | descartado (rebatido) | `app/health.py:12` |\n")
    p = tmp_path / "tasks.md"
    p.write_text(texto, encoding="utf-8")
    code, out, err = _run("--ledger", str(p), "--event", "aprobado", "--actor", "orquestador",
                          "--task", "T-01", "--qa-verde", "--json")
    assert code == 2
    payload = json.loads(out)
    assert payload["ops"] == [] and "sin corrección registrada" in payload["error"][0]
    assert "Critical" in payload["error"][0]
    plan = _plan_json("--ledger", str(p), "--event", "aprobado", "--actor", "orquestador",
                      "--task", "T-02", "--qa-verde")
    assert [o["tipo"] for o in plan["ops"]] == ["etiqueta", "transicion", "comentario"]


def test_aprobado_sin_seccion_de_revision_en_el_ledger_es_rechazado(ledger, tmp_path):
    p = tmp_path / "tasks.md"
    p.write_text(LEDGER.split("## Revisión de dos lentes")[0], encoding="utf-8")
    code, out, err = _run("--ledger", str(p), "--event", "aprobado", "--actor", "orquestador",
                          "--task", "T-01", "--qa-verde")
    assert code == 2 and "ninguna sección" in err


# ---------------------------------------------------------------- revision / gaps

def test_revision_sin_gaps_usa_el_resumen_del_ledger(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "revision", "--actor", "reviewer",
                      "--task", "T-01", "--intento", "2", "--fecha", "2026-09-03")
    cuerpo = next(o for o in plan["ops"] if o["tipo"] == "comentario")["cuerpo"]
    assert "intento 2: sin gaps" in cuerpo
    assert "3 ejecuciones de la suite en verde" in cuerpo  # resumen real del ledger, no inventado


def test_gaps_filtra_solo_las_filas_de_la_tarea_pedida(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "gaps", "--actor", "reviewer",
                      "--task", "T-01", "--intento", "1")
    cuerpo = next(o for o in plan["ops"] if o["tipo"] == "comentario")["cuerpo"]
    assert "db.ping()" in cuerpo and "healthcheck" in cuerpo   # gaps 1 y 2, de T-01
    assert "El README no explica el código 503" not in cuerpo  # gap 3 es de T-02, no debe salir
    assert "2 gap(s)" in cuerpo


def test_gaps_tabla_no_se_trocea_por_pipes_dentro_de_backticks(ledger):
    """Regresión: una celda `` `(?:health|ready|live)` `` con `|` internos no debe fragmentar la fila."""
    plan = _plan_json("--ledger", ledger, "--event", "gaps", "--actor", "reviewer",
                      "--task", "T-01", "--intento", "1")
    cuerpo = next(o for o in plan["ops"] if o["tipo"] == "comentario")["cuerpo"]
    assert "`(?:health|ready|live)`" in cuerpo
    assert "test_ruta_no_colisiona_con_healthcheck" in cuerpo   # celda Evidencia de esa misma fila, intacta


def test_gaps_worklog_horas_de_revision_se_imputan_si_se_pasan(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "gaps", "--actor", "reviewer", "--task", "T-01",
                      "--intento", "1", "--ia-real", "0.4", "--sup-real", "0.1", "--issue", "PROJ-59")
    worklogs = [o for o in plan["ops"] if o["tipo"] == "worklog"]
    assert len(worklogs) == 1
    cmd = worklogs[0]["comando"]
    assert cmd[cmd.index("--task") + 1] == "T-01"
    assert "--ia-real" in cmd and "0.4" in cmd
    assert "--attempt" in cmd and "1" in cmd
    assert not any("solo el comentario" in a for a in plan["avisos"])  # sí se imputa: no es el fallback


def test_gaps_batch_agrupa_las_horas_en_una_clave_sintetica_sin_duplicar(ledger):
    """Regresión: una sola pasada de revisión cubre T-01 y T-02 a la vez (--batch) — las horas NO se
    deben duplicar en dos entradas de worklog (doblaría el tiempo real de esa pasada)."""
    plan = _plan_json("--ledger", ledger, "--event", "gaps", "--actor", "reviewer",
                      "--task", "T-01,T-02", "--batch", "--intento", "1", "--ia-real", "0.4",
                      "--state", str(_state_con_claves(ledger)))
    worklogs = [o for o in plan["ops"] if o["tipo"] == "worklog"]
    assert len(worklogs) == 1, "una pasada de revisión = UNA entrada de worklog, no una por tarea"
    cmd = worklogs[0]["comando"]
    clave = cmd[cmd.index("--task") + 1]
    assert clave == "rev-T-01-T-02"
    assert any("clave sintética" in a for a in plan["avisos"])
    # la clave SINTÉTICA del worklog no debe pisar la de idempotencia del evento (T-fix1)
    assert plan["claveIdempotencia"].endswith("|gaps|T-01,T-02|1")
    assert "rev-T-01-T-02" not in plan["claveIdempotencia"]


def test_gaps_reabre_el_issue_a_en_curso(ledger):
    """Un intento CON gaps devuelve la tarea a `en-progreso`: el issue tiene que reabrirse o Jira
    miente (antes el script no emitía ninguna transición aquí, T-fix1)."""
    plan = _plan_json("--ledger", ledger, "--event", "gaps", "--actor", "reviewer",
                      "--task", "T-01", "--intento", "1")
    assert [o["tipo"] for o in plan["ops"]] == ["etiqueta", "transicion", "comentario"]
    trans = plan["ops"][1]
    assert trans["objetivo_logico"] == "reabrir"
    assert trans["objetivo_statuscategory"] == "indeterminate"
    assert "statusCategory" in trans["regla"]   # GOT-004, igual que las demás


def test_revision_sin_gaps_no_transiciona(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "revision", "--actor", "reviewer",
                      "--task", "T-01", "--intento", "2")
    assert not any(o["tipo"] == "transicion" for o in plan["ops"])


def test_intento_obligatorio_en_revision_y_gaps(ledger):
    """Antes caía a 1 en silencio: con dos intentos en el ledger publicaba los gaps del 1 con el pie
    «intento 2 de 3» mientras el brief del implementer inyectaba los del 2."""
    for evento in ("gaps", "revision"):
        code, out, err = _run("--ledger", ledger, "--event", evento, "--actor", "reviewer",
                              "--task", "T-01")
        assert code == 2, f"{evento} sin --intento debería fallar\n{out}{err}"
        assert "--intento" in err and "no se adivina" in err


def test_cada_intento_publica_su_propia_seccion(ledger):
    """La contradicción resuelta: `--intento 1` trae los gaps del 1 (y el pie «intento 2 de 3»);
    `--intento 2`, la sección limpia del 2 — nunca una mezcla."""
    uno = _plan_json("--ledger", ledger, "--event", "gaps", "--actor", "reviewer",
                     "--task", "T-01", "--intento", "1")
    cuerpo_uno = next(o for o in uno["ops"] if o["tipo"] == "comentario")["cuerpo"]
    assert "intento 1: 2 gap(s)" in cuerpo_uno and "intento 2 de 3" in cuerpo_uno
    dos = _plan_json("--ledger", ledger, "--event", "revision", "--actor", "reviewer",
                     "--task", "T-01", "--intento", "2")
    cuerpo_dos = next(o for o in dos["ops"] if o["tipo"] == "comentario")["cuerpo"]
    assert "intento 2: sin gaps" in cuerpo_dos and "db.ping()" not in cuerpo_dos


def test_cabecera_de_intento_sin_dos_puntos_se_parsea_igual(ledger, tmp_path):
    """Criterio ÚNICO con `task-brief.py`: antes esta regex exigía `:` tras el número y la del brief
    no, así que la misma cabecera daba brief CON gaps y Jira exit 2 (T-fix1)."""
    p = tmp_path / "tasks.md"
    p.write_text(LEDGER.replace("— intento 1: 3 gaps corregidos (0 Critical, 2 Important, 1 Minor)",
                                "— intento 1"), encoding="utf-8")
    plan = _plan_json("--ledger", str(p), "--event", "gaps", "--actor", "reviewer",
                      "--task", "T-01", "--intento", "1")
    cuerpo = next(o for o in plan["ops"] if o["tipo"] == "comentario")["cuerpo"]
    assert "2 gap(s)" in cuerpo and "db.ping()" in cuerpo


def test_la_regex_de_cabecera_es_la_canonica_del_kit():
    """El fallback local debe ser copia LITERAL de `REVISION_HDR_PATTERN` de ledger-lint.py: si
    alguien toca una de las dos, este test lo caza."""
    ll = jf._cargar_ledger_lint()
    assert ll is not None and hasattr(ll, "REVISION_HDR_PATTERN")
    assert jf._REVISION_HDR_FALLBACK == ll.REVISION_HDR_PATTERN


def test_evento_revision_con_gaps_reales_es_rechazado(ledger):
    code, out, err = _run("--ledger", ledger, "--event", "revision", "--actor", "reviewer",
                          "--task", "T-01", "--intento", "1")
    assert code == 2 and "usa `--event gaps`" in err


def test_evento_gaps_sin_gaps_reales_es_rechazado(ledger):
    code, out, err = _run("--ledger", ledger, "--event", "gaps", "--actor", "reviewer",
                          "--task", "T-01", "--intento", "2")
    assert code == 2 and "usa `--event revision`" in err


def test_gaps_intento_inexistente_exit_2(ledger):
    code, out, err = _run("--ledger", ledger, "--event", "gaps", "--actor", "reviewer",
                          "--task", "T-01", "--intento", "9")
    assert code == 2 and "intento 9" in err


# ---------------------------------------------------------------- qa-verde / qa-rojo

def test_qa_verde_incluye_resumen_y_evidencia_derivada_del_slug(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "qa-verde", "--actor", "qa", "--task", "T-01",
                      "--resumen", "6/6 escenarios E2E verdes")
    cuerpo = next(o for o in plan["ops"] if o["tipo"] == "comentario")["cuerpo"]
    assert "6/6 escenarios E2E verdes" in cuerpo
    slug = os.path.basename(os.path.dirname(ledger))
    assert f"docs/roadmap/{slug}/testing/" in cuerpo


def test_qa_rojo_sin_worklog_ni_transicion(ledger):
    plan = _plan_json("--ledger", ledger, "--event", "qa-rojo", "--actor", "qa", "--task", "T-01",
                      "--resumen", "2/6 fallos")
    tipos = {o["tipo"] for o in plan["ops"]}
    assert tipos == {"etiqueta", "comentario"}


# ---------------------------------------------------------------- validaciones de uso

def test_actor_no_coincide_con_el_evento_exit_2(ledger):
    code, out, err = _run("--ledger", ledger, "--event", "implementado", "--actor", "reviewer", "--task", "T-01")
    assert code == 2 and "lo dispara `implementer`" in err


def test_tarea_inexistente_exit_2(ledger):
    code, out, err = _run("--ledger", ledger, "--event", "implementado", "--actor", "implementer", "--task", "T-99")
    assert code == 2 and "T-99" in err


def test_varias_tareas_sin_batch_exit_2(ledger):
    code, out, err = _run("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                          "--task", "T-01,T-02")
    assert code == 2 and "--batch" in err


def test_ledger_inexistente_exit_2(tmp_path):
    code, out, err = _run("--ledger", str(tmp_path / "no-existe.md"), "--event", "arrancar",
                          "--actor", "implementer", "--task", "T-01")
    assert code == 2


# ---------------------------------------------------------------- issueKey e idempotencia de estado

def test_issue_key_se_resuelve_del_state_y_viaja_al_worklog(ledger, tmp_path):
    state = tmp_path / "jira-state.json"
    state.write_text(json.dumps({"tasks": {"T-01": {"issueKey": "PROJ-59"}}}), encoding="utf-8")
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01", "--state", str(state))
    assert plan["issueKey"] == "PROJ-59"
    assert plan["avisos"] == []
    wl = next(o for o in plan["ops"] if o["tipo"] == "worklog")
    assert "PROJ-59" in wl["comando"]


def test_sin_issue_mapeado_degrada_con_aviso_sin_bloquear(ledger, tmp_path):
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01", "--state", str(tmp_path / "no-existe.json"))
    assert plan["issueKey"] is None
    assert any("vuelca el plan a Jira" in a for a in plan["avisos"])


def test_worklog_sin_issue_no_emite_comando_ejecutable(ledger, tmp_path):
    """`worklog.py` acepta `--issue "<issueKey>"` y devuelve exit 0, así que un comando con el
    placeholder PARECÍA listo y grababa estado bajo una clave inventada (T-fix1)."""
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01", "--state", str(tmp_path / "no-existe.json"))
    wl = next(o for o in plan["ops"] if o["tipo"] == "worklog")
    assert "comando" not in wl, "sin issueKey no se emite comando"
    assert wl["requiereIssue"] is True and wl["pendiente"] == "issueKey"
    assert "jira-sync Paso 5" in wl["instruccion"]
    assert "<issueKey>" not in json.dumps(plan)


# ---------------------------------------------------------------- idempotencia del evento

def test_repetir_el_mismo_evento_no_publica_dos_veces(ledger):
    primero = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                         "--task", "T-01", "--issue", "PROJ-59")
    assert len(primero["ops"]) == 3 and primero["yaRealizado"] is False
    segundo = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                         "--task", "T-01", "--issue", "PROJ-59")
    assert segundo["ops"] == [] and segundo["yaRealizado"] is True
    assert any("ya publicado" in a and "--force" in a for a in segundo["avisos"])
    # otro evento sobre la misma tarea NO está bloqueado: la clave incluye el evento
    otro = _plan_json("--ledger", ledger, "--event", "arrancar", "--actor", "implementer",
                      "--task", "T-01", "--issue", "PROJ-59")
    assert len(otro["ops"]) == 2


def test_force_repite_el_evento_a_proposito(ledger):
    _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
               "--task", "T-01", "--issue", "PROJ-59")
    forzado = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                         "--task", "T-01", "--issue", "PROJ-59", "--force")
    assert len(forzado["ops"]) == 3 and forzado["yaRealizado"] is False


def test_estado_corrupto_degrada_con_aviso_sin_bloquear(ledger, tmp_path):
    state = tmp_path / "jira-state.json"
    state.write_text("{esto no es json", encoding="utf-8")
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01", "--issue", "PROJ-59", "--state", str(state))
    assert len(plan["ops"]) == 3, "un estado corrupto nunca bloquea el ciclo"
    assert any("corrupto" in a for a in plan["avisos"])


def test_la_clave_de_idempotencia_distingue_intento_y_tareas(ledger):
    uno = _plan_json("--ledger", ledger, "--event", "gaps", "--actor", "reviewer", "--task", "T-01",
                     "--intento", "1", "--issue", "PROJ-59")
    assert uno["claveIdempotencia"] == "PROJ-59|gaps|T-01|1"
    lote = _plan_json("--ledger", ledger, "--event", "gaps", "--actor", "reviewer",
                      "--task", "T-01,T-02", "--batch", "--intento", "1")
    assert lote["claveIdempotencia"].endswith("|gaps|T-01,T-02|1")


# ---------------------------------------------------------------- opt-in: Jira apagado

def test_jira_desactivado_no_devuelve_ninguna_op(ledger, tmp_path):
    """Con `{"enabled": false}` el ciclo es idéntico pero no publica nada: antes devolvía 3 ops y el
    agente las ejecutaba en el Jira del equipo (T-fix1)."""
    (tmp_path / ".claude" / "jira.json").write_text('{"enabled": false}', encoding="utf-8")
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01")
    assert plan["ops"] == [] and plan["jira"] == "desactivado"
    assert any("enabled" in a for a in plan["avisos"])


def test_sin_config_de_jira_tampoco_publica(ledger, tmp_path):
    """Opt-in que falla CERRADO: sin `.claude/jira.json` no hay nada que publicar."""
    os.remove(str(tmp_path / ".claude" / "jira.json"))
    plan = _plan_json("--ledger", ledger, "--event", "implementado", "--actor", "implementer",
                      "--task", "T-01")
    assert plan["ops"] == [] and plan["jira"] == "desactivado"


def test_root_resuelve_la_config_desde_otra_carpeta(ledger, tmp_path):
    """`--root` es la misma resolución que `worklog.py` (hacia arriba buscando `.claude/`), solo con
    el punto de partida explícito: desde un cwd ajeno, sin `--root` no hay opt-in y con él sí."""
    with tempfile.TemporaryDirectory() as ajeno:
        apagado = _plan_json("--ledger", ledger, "--event", "arrancar", "--actor", "implementer",
                             "--task", "T-01", cwd=ajeno)
        assert apagado["ops"] == [] and apagado["jira"] == "desactivado"
        plan = _plan_json("--ledger", ledger, "--event", "arrancar", "--actor", "implementer",
                          "--task", "T-01", "--root", str(tmp_path), cwd=ajeno)
        assert len(plan["ops"]) == 2 and plan["jira"] == "activado"


# ---------------------------------------------------------------- unidad: split de fila Markdown

def test_split_fila_md_respeta_pipes_dentro_de_backticks():
    fila = "| 6 | Minor | texto | T-02 | `a|b|c` regla | `evidencia:1` |"
    celdas = jf._split_fila_md(fila)
    assert celdas == ["6", "Minor", "texto", "T-02", "`a|b|c` regla", "`evidencia:1`"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
