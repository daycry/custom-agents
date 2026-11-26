"""Tests de roadmap-sync.py (plugin-audit-2 T-42): el plugin mantiene el roadmap al día por sí mismo.

Estado del ledger, del plan, de la spec y de la evaluación, y la fila del índice `docs/roadmap/README.md`,
derivados de los estados de las tareas y de los artefactos (tabla de transiciones de `phase6-close.md`).
Disparadores: `ledger-write.py verdict`, `retro-gate.py --sync` y la puerta de `/pm-cycle` (`gate`).
fix1: el ledger solo se cierra con `--cerrar` (Fase 6) y la evaluación solo la mueve `gate` (gaps 1-2).
Ejecutar: python -m pytest -q agent-kits/shared/test_roadmap_sync.py
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

KIT = Path(__file__).resolve().parent
SCRIPT = KIT / "roadmap-sync.py"

INDICE = """# Roadmap

| Fecha | Iniciativa | Tiempo | Coste | Artefactos |
|-------|-----------|--------|-------|-----------|
{filas}
**Calibración:** texto que no se toca.
"""
CALIBRATION = """# CALIBRATION

| Fecha | Iniciativa | Desv. producción | Desv. tokens | tokens/hora (medido) | Causa principal | Ajuste sugerido |
|---|---|---|---|---|---|---|
{filas}"""
RETRO = "# Retro — demo\n\n## Causas\n\n- una causa real\n"


def ledger(estado="en-progreso", estados=("completado", "completado"), comentario=""):
    tareas = "".join(
        f"### T-0{i} — tarea {i}\n\n- **Estado**: {e}\n\n**Criterios de aceptación**\n- [{'x' if e == 'completado' else ' '}] c{i}\n\n"
        for i, e in enumerate(estados, 1))
    return (f"---\ntasks: demo\nestado: {estado}{comentario}\n---\n\n# Demo\n\n"
            f"## Fase 1 — Única\n\n{tareas}")


def artefacto(clave, estado, comentario=""):
    return f"---\n{clave}: demo\nestado: {estado}{comentario}\n---\n\n# {clave.capitalize()} demo\n\nCuerpo.\n"


def proyecto(tmp_path, filas_indice="", filas_cal=""):
    roadmap = tmp_path / "docs" / "roadmap"
    roadmap.mkdir(parents=True)
    (roadmap / "README.md").write_text(INDICE.format(filas=filas_indice), encoding="utf-8")
    (roadmap / "CALIBRATION.md").write_text(CALIBRATION.format(filas=filas_cal), encoding="utf-8")
    return roadmap


def iniciativa(roadmap, nombre, **ficheros):
    carpeta = roadmap / nombre
    carpeta.mkdir()
    nombres = {"spec": "spec.md", "evaluation": "evaluation.md", "design": "design.md",
               "plan": "improvement-plan.md", "tasks": "tasks.md", "retro": "retro.md"}
    for clave, texto in ficheros.items():
        (carpeta / nombres[clave]).write_text(texto, encoding="utf-8")
    return carpeta


def run(*args, cwd=None):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True,
                       encoding="utf-8", errors="replace", cwd=cwd, timeout=30)
    return r.returncode, r.stdout, r.stderr


def run_json(*args, **kw):
    code, out, err = run(*args, "--json", **kw)
    assert out.strip(), err
    return code, json.loads(out)


def snapshot(root):
    return {p: p.read_bytes() for p in sorted(Path(root).rglob("*")) if p.is_file()}


def fila(nombre, iniciativa_txt, enlaces):
    return f"| {nombre[:10]} | {iniciativa_txt} | No estimado | No medido | {enlaces} |"


# ---------------------------------------------------------------- derivación de estados

def test_ledger_al_100_pasa_a_completado_conserva_comentario_y_es_idempotente(tmp_path):
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger(comentario="   # comentario"))
    code, out = run_json(c, "--cerrar")
    assert code == 0
    assert "estado: completado   # comentario" in (c / "tasks.md").read_text(encoding="utf-8")
    assert {"iniciativa": "2026-01-01-demo", "tipo": "ledger", "artefacto": "tasks.md",
            "de": "en-progreso", "a": "completado"} in out["cambios"]
    antes = snapshot(tmp_path)
    code, out = run_json(c, "--cerrar")
    assert code == 0 and out["changed"] is False and snapshot(tmp_path) == antes


def test_ledger_tabla_de_cabecera_sin_frontmatter(tmp_path):
    roadmap = proyecto(tmp_path)
    texto = ("# Checklist — demo\n\n| | |\n|---|---|\n| **Estado** | en-progreso |\n\n## Fase 1 — Única\n\n"
             "### T-01 — t\n\n- **Estado**: completado\n\n**Criterios de aceptación**\n- [x] a\n")
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=texto)
    assert run(c, "--cerrar")[0] == 0
    assert "| **Estado** | completado |" in (c / "tasks.md").read_text(encoding="utf-8")


def test_retro_hecha_cierra_plan_y_spec(tmp_path):
    roadmap = proyecto(tmp_path, filas_cal="| 2026-01-09 | demo | −1 % | −1 % | 1 | causa | ajuste |\n")
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("completado"), retro=RETRO,
                   spec=artefacto("spec", "aprobada"), evaluation=artefacto("evaluacion", "completado"),
                   plan=artefacto("plan", "en-progreso", "       # F1 completada"))
    code, out = run_json(c)
    assert code == 0
    assert "estado: implementada" in (c / "spec.md").read_text(encoding="utf-8")
    assert "estado: completado       # F1 completada" in (c / "improvement-plan.md").read_text(encoding="utf-8")
    assert not [a for a in out["avisos"] if a["tipo"] == "retro-pendiente"]


def test_sin_retro_no_cierra_spec_y_avisa_retro_pendiente(tmp_path):
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger(), spec=artefacto("spec", "aprobada"),
                   plan=artefacto("plan", "en-progreso"))
    code, out = run_json(c, "--cerrar")
    assert code == 0
    assert "estado: aprobada" in (c / "spec.md").read_text(encoding="utf-8")
    assert "estado: en-progreso" in (c / "improvement-plan.md").read_text(encoding="utf-8")
    assert "estado: completado" in (c / "tasks.md").read_text(encoding="utf-8")
    assert [a["tipo"] for a in out["avisos"] if a["iniciativa"] == "2026-01-01-demo"] == ["retro-pendiente"]


def test_t42_fix1_gap1_sync_no_cierra_la_evaluacion_sin_go(tmp_path):
    """Gap 1: con la spec `aprobada` (la aprueba el analyst ANTES de evaluar) la evaluación espera la puerta;
    el sync no la deriva ni la cuenta como desfase, y `gate --decision no-go` sigue funcionando."""
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", spec=artefacto("spec", "aprobada"),
                   evaluation=artefacto("evaluacion", "en-revision"))
    code, out = run_json(roadmap, "--check")
    assert not [d for d in out["desfases"] if d["tipo"] == "evaluacion"]
    assert run(roadmap)[0] == 0
    assert "estado: en-revision" in (c / "evaluation.md").read_text(encoding="utf-8")
    code, out = run_json("gate", c, "--decision", "no-go")
    assert code == 0, out
    assert "estado: cancelado" in (c / "evaluation.md").read_text(encoding="utf-8")


def test_nunca_rebaja_un_estado_y_reporta_el_adelantado(tmp_path):
    # fix1 (gap 2): un ledger `completado` con una tarea reabierta SÍ vuelve a `en-progreso` (única excepción,
    # con la tarea como evidencia); lo adelantado sin evidencia —spec `implementada` con el ledger abierto— no.
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("en-progreso", ("completado", "en-progreso")),
                   spec=artefacto("spec", "implementada"))
    antes = (c / "spec.md").read_bytes()
    code, out = run_json(c)
    assert (c / "spec.md").read_bytes() == antes
    assert [a["tipo"] for a in out["avisos"]] == ["adelantado"]
    assert not [d for d in out["desfases"] if d["artefacto"] == "spec.md"]


def test_via_rapida_solo_tasks(tmp_path):
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-rapida", tasks=ledger())
    assert run(c, "--cerrar")[0] == 0
    assert "estado: completado" in (c / "tasks.md").read_text(encoding="utf-8")
    assert "[tasks](2026-01-01-rapida/tasks.md)" in (roadmap / "README.md").read_text(encoding="utf-8")


def test_dry_run_no_escribe_nada(tmp_path):
    roadmap = proyecto(tmp_path)
    iniciativa(roadmap, "2026-01-01-demo", tasks=ledger())
    antes = snapshot(tmp_path)
    code, out = run_json(roadmap, "--dry-run")
    assert code == 0 and out["cambios"] and snapshot(tmp_path) == antes


def test_sin_indice_no_lo_crea(tmp_path):
    roadmap = proyecto(tmp_path)
    (roadmap / "README.md").unlink()
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger())
    code, out = run_json(c, "--cerrar")
    assert code == 0 and not (roadmap / "README.md").exists()
    assert "estado: completado" in (c / "tasks.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------- índice

def test_indice_regenera_solo_su_fila(tmp_path):
    otra = fila("2026-01-02-otra", "otra — algo `con | pipe`", "[tasks](2026-01-02-otra/tasks.md)")
    propia = fila("2026-01-01-demo", "demo — texto del autor", "[tasks](2026-01-01-demo/tasks.md)")
    roadmap = proyecto(tmp_path, filas_indice=otra + "\n" + propia)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger(), spec=artefacto("spec", "aprobada"))
    assert run(c, "--cerrar")[0] == 0
    lineas = (roadmap / "README.md").read_text(encoding="utf-8").splitlines()
    assert otra in lineas, "la fila de otra iniciativa no se toca"
    nueva = next(l for l in lineas if "2026-01-01-demo/" in l)
    assert "demo — texto del autor · estado: completada, retro pendiente |" in nueva
    assert nueva.endswith("[tasks](2026-01-01-demo/tasks.md) · [spec](2026-01-01-demo/spec.md) |")
    assert "**Calibración:** texto que no se toca." in lineas
    antes = snapshot(tmp_path)
    assert run(c, "--cerrar")[0] == 0 and snapshot(tmp_path) == antes


def test_indice_respeta_el_separador_de_la_fila(tmp_path):
    propia = fila("2026-01-01-demo", "demo · estado: en curso", "[tasks](2026-01-01-demo/tasks.md)")
    propia = propia.replace("[tasks](2026-01-01-demo/tasks.md)",
                            "[plan](2026-01-01-demo/improvement-plan.md) / [tasks](2026-01-01-demo/tasks.md)")
    roadmap = proyecto(tmp_path, filas_indice=propia)
    iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("en-progreso", ("en-progreso",)),
               plan=artefacto("plan", "en-progreso"), spec=artefacto("spec", "aprobada"))
    assert run(roadmap)[0] == 0
    texto = (roadmap / "README.md").read_text(encoding="utf-8")
    assert "/ [tasks](2026-01-01-demo/tasks.md) / [spec](2026-01-01-demo/spec.md) |" in texto
    assert texto.count("estado: en curso") == 1


def test_indice_anade_la_fila_que_falta(tmp_path):
    roadmap = proyecto(tmp_path)
    iniciativa(roadmap, "2026-01-05-nueva", spec=artefacto("spec", "borrador"))
    assert run(roadmap)[0] == 0
    texto = (roadmap / "README.md").read_text(encoding="utf-8")
    assert ("| 2026-01-05 | nueva — Spec demo · estado: solo spec | No estimado | No medido | "
            "[spec](2026-01-05-nueva/spec.md) |") in texto


# ---------------------------------------------------------------- --check

def test_check_detecta_los_cinco_tipos_y_la_puesta_al_dia_los_deja_en_cero(tmp_path):
    cal = "".join(f"| 2026-01-09 | {s} | −1 % | −1 % | 1 | c | a |\n" for s in ("plan-rancio", "spec-rancia"))
    roadmap = proyecto(tmp_path, filas_cal=cal)
    iniciativa(roadmap, "2026-01-01-ledger-rancio", tasks=ledger("borrador", ("completado", "en-progreso")))
    iniciativa(roadmap, "2026-01-02-plan-rancio", tasks=ledger("completado"), retro=RETRO,
               plan=artefacto("plan", "en-progreso"))
    iniciativa(roadmap, "2026-01-03-spec-rancia", tasks=ledger("completado"), retro=RETRO,
               spec=artefacto("spec", "aprobada"))
    # fix1 (gap 1): la evaluación ya no es un desfase del sync — la mueve solo la puerta (`gate`).
    iniciativa(roadmap, "2026-01-04-eval-rancia", spec=artefacto("spec", "aprobada"),
               evaluation=artefacto("evaluacion", "en-revision"))
    code, out = run_json(roadmap, "--check")
    assert code == 1
    tipos = {d["tipo"] for d in out["desfases"]}
    assert tipos == {"ledger", "plan", "spec", "indice"}
    code, out_text, _ = run(roadmap, "--check")
    assert code == 1 and "desfase ledger" in out_text
    assert run(roadmap)[0] == 0
    code, out = run_json(roadmap, "--check")
    assert code == 0 and out["desfases"] == []
    assert "estado: en-progreso" in (roadmap / "2026-01-01-ledger-rancio" / "tasks.md").read_text(encoding="utf-8")


def test_carpeta_inexistente_exit_2(tmp_path):
    proyecto(tmp_path)
    assert run(tmp_path / "docs" / "roadmap" / "2026-01-01-nada", "--check")[0] == 2


# ---------------------------------------------------------------- disparadores

def _escritor(ledger_path, *args):
    return subprocess.run([sys.executable, str(KIT / "ledger-write.py"), args[0], str(ledger_path), *args[1:], "--json"],
                          capture_output=True, encoding="utf-8", timeout=30, cwd=ledger_path.parents[3])


def test_disparador_verdict_limpio_al_100_sincroniza_ledger_e_indice(tmp_path):
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("en-progreso", ("en-progreso", "en-progreso")).replace(
        "- [ ] c1", "- [x] c1").replace("- [ ] c2", "- [x] c2"))
    tareas = ("--tasks", "T-01,T-02", "--attempt", "1")
    r = _escritor(c / "tasks.md", "review", *tareas, "--summary", "Demo")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "estado: en-progreso" in (c / "tasks.md").read_text(encoding="utf-8")
    r = _escritor(c / "tasks.md", "verdict", *tareas, "--result", "limpio")
    assert r.returncode == 0, r.stdout + r.stderr
    # fix1 (gap 2): el veredicto de la Fase 3 no cierra el ledger (falta qa y la Fase 6); el índice sí.
    assert "estado: en-progreso" in (c / "tasks.md").read_text(encoding="utf-8")
    assert "· estado: en curso" in (roadmap / "README.md").read_text(encoding="utf-8")
    assert json.loads(r.stdout)["roadmap_sync"]["cambios"]


def test_disparador_retro_gate_sync_cierra_spec_y_plan(tmp_path):
    roadmap = proyecto(tmp_path, filas_cal="| 2026-01-09 | demo | −1 % | −1 % | 1 | c | a |\n")
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("completado"), retro=RETRO,
                   spec=artefacto("spec", "aprobada"), plan=artefacto("plan", "en-progreso"))
    gate = [sys.executable, str(KIT / "retro-gate.py"), str(c)]
    antes = snapshot(tmp_path)
    assert subprocess.run(gate, capture_output=True, timeout=30).returncode == 0
    assert snapshot(tmp_path) == antes, "sin --sync la puerta solo lee"
    r = subprocess.run(gate + ["--sync"], capture_output=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "estado: implementada" in (c / "spec.md").read_text(encoding="utf-8")
    assert "estado: completado" in (c / "improvement-plan.md").read_text(encoding="utf-8")
    assert "· estado: cerrada" in (roadmap / "README.md").read_text(encoding="utf-8")


def test_disparador_retro_gate_sync_con_puerta_cerrada_no_cierra_la_spec(tmp_path):
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("completado"), spec=artefacto("spec", "aprobada"))
    r = subprocess.run([sys.executable, str(KIT / "retro-gate.py"), str(c), "--sync"],
                       capture_output=True, encoding="utf-8", timeout=30)
    assert r.returncode == 1
    assert "estado: aprobada" in (c / "spec.md").read_text(encoding="utf-8")


def test_disparador_puerta_pm_cycle_go_y_no_go(tmp_path):
    roadmap = proyecto(tmp_path)
    go = iniciativa(roadmap, "2026-01-01-go", spec=artefacto("spec", "borrador"),
                    evaluation=artefacto("evaluacion", "en-revision"))
    code, out = run_json("gate", go, "--decision", "go")
    assert code == 0, out
    assert "estado: aprobada" in (go / "spec.md").read_text(encoding="utf-8")
    assert "estado: completado" in (go / "evaluation.md").read_text(encoding="utf-8")
    assert "go — Spec demo · estado: evaluada" in (roadmap / "README.md").read_text(encoding="utf-8")
    nogo = iniciativa(roadmap, "2026-01-02-nogo", spec=artefacto("spec", "borrador"),
                      evaluation=artefacto("evaluacion", "en-revision"))
    assert run("gate", nogo, "--decision", "no-go", "--descartar")[0] == 0
    assert "estado: obsoleta" in (nogo / "spec.md").read_text(encoding="utf-8")
    assert "estado: cancelado" in (nogo / "evaluation.md").read_text(encoding="utf-8")
    assert "· estado: cancelada" in (roadmap / "README.md").read_text(encoding="utf-8")
    # La puerta no reabre una decisión ya tomada (nunca rebaja).
    assert run("gate", go, "--decision", "no-go")[0] == 1
    assert "estado: completado" in (go / "evaluation.md").read_text(encoding="utf-8")


def test_modulo_importable_para_los_disparadores():
    spec = importlib.util.spec_from_file_location("roadmap_sync", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.sincronizar) and callable(mod.comprobar)


# ---------------------------------------------------------------- fix1 de T-42 (revisión intento 1)

def _mod():
    spec = importlib.util.spec_from_file_location("roadmap_sync_fix1", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_t42_fix1_gap2_verdict_limpio_sin_cierre_deja_el_ledger_en_progreso(tmp_path):
    """Gap 2: tareas al 100 % sin la autorización de la Fase 6 → el ledger sigue `en-progreso` y sale un aviso
    `cierre-pendiente` (no un desfase); solo `--cerrar` lo pasa a `completado`."""
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger())
    code, out = run_json(roadmap)
    assert code == 0 and "estado: en-progreso" in (c / "tasks.md").read_text(encoding="utf-8")
    assert [a["tipo"] for a in out["avisos"]] == ["cierre-pendiente"]
    assert not [d for d in out["desfases"] if d["tipo"] == "ledger"]
    assert run(c, "--cerrar")[0] == 0
    assert "estado: completado" in (c / "tasks.md").read_text(encoding="utf-8")


def test_t42_fix1_gap2_cerrar_exige_todas_las_tareas_cerradas_y_una_iniciativa(tmp_path):
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("en-progreso", ("completado", "en-revision")))
    antes = snapshot(tmp_path)
    code, out = run_json(c, "--cerrar")
    assert code == 1 and out["status"] == "open_tasks" and snapshot(tmp_path) == antes
    assert run_json(roadmap, "--cerrar")[0] == 2, "--cerrar es por iniciativa, nunca sobre todo el roadmap"


def test_t42_fix1_gap2_tarea_reabierta_devuelve_el_ledger_a_en_progreso(tmp_path):
    """Gap 2: qa reabre una tarea tras el cierre → el sync devuelve el ledger a `en-progreso` (excepción
    documentada a «nunca rebaja»: la evidencia es la tarea reabierta) y el bloque de sesión lo avisa."""
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("completado", ("completado", "en-progreso")))
    code, out = run_json(roadmap, "--check")
    assert code == 1
    assert {"iniciativa": "2026-01-01-demo", "tipo": "ledger", "artefacto": "tasks.md", "de": "completado",
            "a": "en-progreso", "motivo": "reabierta"} in out["desfases"]
    pr = KIT / "progress-report.py"
    r = subprocess.run([sys.executable, str(pr), "session", "--root", str(tmp_path)], capture_output=True,
                       encoding="utf-8", errors="replace", timeout=30)
    assert any(l.startswith("Roadmap desfasado:") and "reabierta" in l for l in r.stdout.splitlines()), r.stdout
    assert run(roadmap)[0] == 0
    assert "estado: en-progreso" in (c / "tasks.md").read_text(encoding="utf-8")


ASTRA = Path(__file__).resolve().parents[2] / "docs" / "roadmap" / "2026-11-24-auditoria-astra" / "improvement-plan.md"


def test_t42_fix1_gap3_conserva_el_resto_de_la_celda_y_salta_cabeceras(tmp_path):
    """Gap 3: solo se sustituye el TOKEN de estado (frontmatter con comillas y comentario, celda con prosa y
    emojis); una fila cabecera `| Estado | Significado |` no se toca; una celda sin token es aviso."""
    mod = _mod()
    copia = tmp_path / "improvement-plan.md"
    copia.write_bytes(ASTRA.read_bytes())
    real = copia.read_text(encoding="utf-8")
    nuevo = mod.con_estado(real, "en-progreso")
    assert "estado: en-progreso\n" in nuevo and "| **Estado** | en-progreso |" in nuevo
    assert nuevo.replace("en-progreso", "borrador", 2) == real, "solo cambian los dos tokens"
    texto = ('---\nplan: demo\nestado: "borrador"  # comentario\n---\n\n# Plan\n\n| Estado | Significado |\n'
             '|---|---|\n| x | y |\n\n| Cadena | Enlace |\n|---|---|\n'
             '| Estado | `borrador` 📝. **La ejecución NO está autorizada**: el usuario pidió el plan |\n\n## Fase 1\n')
    salida = mod.con_estado(texto, "en-progreso")
    assert 'estado: "en-progreso"  # comentario' in salida
    assert "| Estado | Significado |" in salida
    assert "| Estado | `en-progreso` 📝. **La ejecución NO está autorizada**: el usuario pidió el plan |" in salida
    assert mod.campos_estado(texto)[0] == "borrador"
    sin_token = "---\nplan: demo\nestado: borrador\n---\n\n# Plan\n\n| | |\n|---|---|\n| **Estado** | ver nota |\n"
    assert "| **Estado** | ver nota |" in mod.con_estado(sin_token, "en-progreso")
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("borrador", ("en-progreso",)).replace(
        "# Demo\n", "# Demo\n\n| | |\n|---|---|\n| **Estado** | ver nota |\n"))
    code, out = run_json(roadmap)
    assert code == 0 and "| **Estado** | ver nota |" in (c / "tasks.md").read_text(encoding="utf-8")
    assert any(a["tipo"] == "sin-estado" and "celda" in a["detalle"] for a in out["avisos"])


def test_t42_fix1_gap4_fila_propia_por_su_enlace_no_por_la_primera_mencion(tmp_path):
    """Gap 4 (caso `ideas-externas`): otra fila cita la carpeta antes que la propia → la marca cae en la propia;
    dos filas candidatas → aviso, sin escribir; `--check` ve la marca de estado en la fila ajena."""
    otra = fila("2026-02-01-otra", "otra — sucede a [x](2026-01-01-tres/spec.md) · estado: solo spec",
                "[spec](2026-02-01-otra/spec.md)")
    propia = fila("2026-01-01-tres", "tres — demo", "[spec](2026-01-01-tres/spec.md)")
    roadmap = proyecto(tmp_path, filas_indice=otra + "\n" + propia)
    iniciativa(roadmap, "2026-01-01-tres", spec=artefacto("spec", "borrador"))
    iniciativa(roadmap, "2026-02-01-otra", spec=artefacto("spec", "borrador"),
               evaluation=artefacto("evaluacion", "en-revision"))
    code, out = run_json(roadmap, "--check")
    assert code == 1
    assert {"iniciativa": "2026-02-01-otra", "tipo": "indice", "artefacto": "README.md",
            "de": "solo spec · faltan eval", "a": "evaluada"} in out["desfases"], out["desfases"]
    assert run(roadmap)[0] == 0
    lineas = (roadmap / "README.md").read_text(encoding="utf-8").splitlines()
    assert any(l.startswith("| 2026-01-01 | tres — demo · estado: solo spec |") for l in lineas)
    assert any(l.startswith("| 2026-02-01 | otra — sucede a [x](2026-01-01-tres/spec.md) · estado: evaluada |")
               for l in lineas)
    doble = propia + "\n" + propia.replace("tres — demo", "tres — copia")
    (tmp_path / "b").mkdir()
    roadmap2 = proyecto(tmp_path / "b", filas_indice=doble)
    iniciativa(roadmap2, "2026-01-01-tres", spec=artefacto("spec", "borrador"))
    antes = (roadmap2 / "README.md").read_bytes()
    code, out = run_json(roadmap2)
    assert code == 0 and (roadmap2 / "README.md").read_bytes() == antes
    assert any(a["tipo"] == "indice" and "2026-01-01-tres" in a["detalle"] for a in out["avisos"])


def test_t42_fix1_gap7_pipe_escapado_en_el_titulo(tmp_path):
    propia = fila("2026-01-01-seis", r"seis — a \| b", "[spec](2026-01-01-seis/spec.md)")
    roadmap = proyecto(tmp_path, filas_indice=propia)
    iniciativa(roadmap, "2026-01-01-seis", spec=artefacto("spec", "borrador"))
    assert run(roadmap)[0] == 0
    texto = (roadmap / "README.md").read_text(encoding="utf-8")
    assert (r"| 2026-01-01 | seis — a \| b · estado: solo spec | No estimado | No medido | "
            "[spec](2026-01-01-seis/spec.md) |") in texto


def test_t42_fix1_gap8_indice_grande_degrada_con_aviso_y_json(tmp_path):
    roadmap = proyecto(tmp_path)
    iniciativa(roadmap, "2026-01-01-cinco", spec=artefacto("spec", "borrador"))
    (roadmap / "README.md").write_text(INDICE.format(filas="") + ("x" * 100 + "\n") * 2700, encoding="utf-8")
    antes = (roadmap / "README.md").read_bytes()
    code, out = run_json(roadmap)
    assert code == 0 and out["status"] == "ok" and (roadmap / "README.md").read_bytes() == antes
    assert any(a["tipo"] == "no-escrito" and "README.md" in a["detalle"] for a in out["avisos"])


def test_t42_fix1_gap9_conserva_el_texto_tras_una_marca_previa(tmp_path):
    propia = fila("2026-01-01-cuatro", "cuatro — demo · estado: ver nota · seguimiento en #12",
                  "[spec](2026-01-01-cuatro/spec.md)")
    roadmap = proyecto(tmp_path, filas_indice=propia)
    iniciativa(roadmap, "2026-01-01-cuatro", spec=artefacto("spec", "borrador"))
    assert run(roadmap)[0] == 0
    assert "cuatro — demo · estado: solo spec · seguimiento en #12 |" in (
        roadmap / "README.md").read_text(encoding="utf-8")


def test_t42_fix1_gap10_gate_escribe_ambos_o_ninguno(tmp_path, monkeypatch, capsys):
    mod = _mod()
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", spec=artefacto("spec", "borrador"),
                   evaluation=artefacto("evaluacion", "en-revision"))
    antes = snapshot(tmp_path)
    original = mod._escribir

    def falla_en_la_evaluacion(doc, texto, deadline, ledger=False):
        if doc["path"].name == "evaluation.md":
            raise mod.SyncError("conflict", 1)
        return original(doc, texto, deadline, ledger)

    monkeypatch.setattr(mod, "_escribir", falla_en_la_evaluacion)
    code = mod.main(["gate", str(c), "--decision", "go", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 1 and out["status"] == "conflict" and snapshot(tmp_path) == antes, "ninguno: la spec se restaura"

    def sin_restaurar(*a, **k):
        raise OSError("sin restaurar")

    monkeypatch.setattr(mod, "_restaurar", sin_restaurar)
    code = mod.main(["gate", str(c), "--decision", "go", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 3 and out["status"] == "partial"
    assert out["escritos"] == ["spec.md"] and out["no_escritos"] == ["evaluation.md"]


def test_t42_fix1_gap11_ledger_grande_sin_cerrar_avisa_no_escrito(tmp_path):
    roadmap = proyecto(tmp_path)
    grande = ledger("en-progreso") + ("relleno " * 40 + "\n") * 900
    c = iniciativa(roadmap, "2026-01-01-grande", tasks=grande)
    assert (c / "tasks.md").stat().st_size > 256 * 1024
    code, out = run_json(roadmap, "--check")
    assert any(a["tipo"] == "no-escrito" and "tasks.md > 256 KiB" in a["detalle"] for a in out["avisos"]), out


# ---------------------------------------------------------------- fix1 gaps 6 y 15: comprobación de sesión acotada

def test_t42_fix1_gap6_cache_por_firma_no_reanaliza_lo_que_no_cambia(tmp_path, monkeypatch):
    roadmap = proyecto(tmp_path)
    (tmp_path / ".claude").mkdir()
    iniciativa(roadmap, "2026-01-01-uno", tasks=ledger("borrador", ("en-progreso",)))
    iniciativa(roadmap, "2026-01-02-dos", spec=artefacto("spec", "borrador"))
    mod = _mod()
    primera = mod.comprobar(tmp_path)
    assert primera["desfases"] and (tmp_path / ".claude" / ".roadmap-sync.cache").is_file()
    llamadas = []
    real = mod.analizar
    monkeypatch.setattr(mod, "analizar", lambda c, *a, **k: llamadas.append(c.name) or real(c, *a, **k))
    segunda = mod.comprobar(tmp_path)
    assert llamadas == [] and segunda["desfases"] == primera["desfases"]
    (roadmap / "2026-01-02-dos" / "spec.md").write_text(artefacto("spec", "aprobada") + "\n", encoding="utf-8")
    mod.comprobar(tmp_path)
    assert llamadas == ["2026-01-02-dos"], "solo se reanaliza la iniciativa cuya firma cambió"
    assert not list((tmp_path / "docs").rglob("*.cache")), "la caché nunca vive dentro de docs/"


def test_t42_fix1_gap6_tope_de_carpetas_y_plazo(tmp_path):
    roadmap = proyecto(tmp_path)
    for n in range(130):
        iniciativa(roadmap, f"2025-{1 + n // 28:02d}-{1 + n % 28:02d}-i{n}", spec=artefacto("spec", "borrador"))
    mod = _mod()
    informe = mod.comprobar(tmp_path)
    assert informe["iniciativas"] == 128 and informe["recortadas"] == 2
    vencido = mod.comprobar(tmp_path, deadline=0)
    assert vencido["omitida"] is True and vencido["status"] == "ok"


def test_t42_fix1_gap15_el_informe_trae_las_retros_abiertas(tmp_path):
    roadmap = proyecto(tmp_path, filas_cal="| 2026-01-09 | demo | −1 % | −1 % | 1 | c | a |\n")
    iniciativa(roadmap, "2026-01-01-demo", tasks=ledger(), retro=RETRO)
    iniciativa(roadmap, "2026-01-02-otra", tasks=ledger())
    assert _mod().comprobar(tmp_path)["retro_abiertas"] == ["2026-01-01-demo"]


# ---------------------------------------------------------------- fix2 de T-42 (revisión intento 2)

CAL_DEMO = "| 2026-01-09 | demo | −1 % | −1 % | 1 | c | a |\n"


def _estado(path):
    return next(l for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("estado:"))


def test_t42_fix2_gap2_retro_gate_sync_cierra_ledger_plan_y_spec(tmp_path):
    """Gap 2 (a): el cierre lo hace el plugin. Con la retro hecha (solo existe tras qa verde) y las tareas al
    100 %, `retro-gate.py --sync` cierra el ledger aunque se olvidara `--cerrar`, el plan y la spec."""
    roadmap = proyecto(tmp_path, filas_cal=CAL_DEMO)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("en-progreso"), retro=RETRO,
                   spec=artefacto("spec", "aprobada"), plan=artefacto("plan", "en-progreso"))
    r = subprocess.run([sys.executable, str(KIT / "retro-gate.py"), str(c), "--sync"],
                       capture_output=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr
    assert _estado(c / "tasks.md") == "estado: completado"
    assert _estado(c / "improvement-plan.md") == "estado: completado"
    assert _estado(c / "spec.md") == "estado: implementada"
    assert "· estado: cerrada" in (roadmap / "README.md").read_text(encoding="utf-8")
    assert run_json(roadmap, "--check")[0] == 0


def test_t42_fix2_gap2_retro_gate_sync_con_tareas_abiertas_no_abre_la_puerta(tmp_path):
    roadmap = proyecto(tmp_path, filas_cal=CAL_DEMO)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("en-progreso", ("completado", "en-revision")),
                   retro=RETRO, spec=artefacto("spec", "aprobada"), plan=artefacto("plan", "en-progreso"))
    antes = snapshot(tmp_path)
    r = subprocess.run([sys.executable, str(KIT / "retro-gate.py"), str(c), "--sync"],
                       capture_output=True, encoding="utf-8", timeout=30)
    assert r.returncode == 1, r.stdout
    assert "tareas abiertas" in r.stdout and "ABIERTA" not in r.stdout, r.stdout
    assert snapshot(tmp_path) == antes


def test_t42_fix2_gap2_check_cuenta_el_cierre_olvidado_como_desfase(tmp_path):
    """Gap 2 (b): tareas al 100 % + retro hecha + ledger/plan/spec sin cerrar = DESFASE (exit 1); sin retro sigue
    siendo el aviso `cierre-pendiente` (exit 0)."""
    roadmap = proyecto(tmp_path, filas_cal=CAL_DEMO)
    iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("en-progreso"), retro=RETRO,
               spec=artefacto("spec", "aprobada"), plan=artefacto("plan", "en-progreso"))
    code, out = run_json(roadmap, "--check")
    assert code == 1
    assert {"iniciativa": "2026-01-01-demo", "tipo": "ledger", "artefacto": "tasks.md", "de": "en-progreso",
            "a": "completado", "motivo": "cierre-olvidado"} in out["desfases"], out["desfases"]
    assert {d["tipo"] for d in out["desfases"]} >= {"ledger", "plan", "spec"}
    (tmp_path / "b").mkdir()
    roadmap2 = proyecto(tmp_path / "b", filas_indice=fila("2026-01-01-demo", "demo · estado: en curso",
                                                          "[tasks](2026-01-01-demo/tasks.md)"))
    iniciativa(roadmap2, "2026-01-01-demo", tasks=ledger("en-progreso"))
    code, out = run_json(roadmap2, "--check")
    assert code == 0 and [a["tipo"] for a in out["avisos"]] == ["cierre-pendiente"]


def test_t42_fix2_gap2_el_bloque_de_sesion_da_el_comando_exacto(tmp_path):
    """Gap 2 (c): para el cierre olvidado, la sesión dice `roadmap-sync.py docs/roadmap/<carpeta> --cerrar`,
    no `/retro` ni un `<carpeta>` por rellenar."""
    roadmap = proyecto(tmp_path, filas_cal=CAL_DEMO)
    iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("en-progreso"), retro=RETRO)
    r = subprocess.run([sys.executable, str(KIT / "progress-report.py"), "session", "--root", str(tmp_path)],
                       capture_output=True, encoding="utf-8", errors="replace", timeout=30)
    assert "roadmap-sync.py docs/roadmap/2026-01-01-demo --cerrar" in r.stdout, r.stdout
    assert "/retro demo" not in r.stdout and "<carpeta>" not in r.stdout, r.stdout
    assert any(l.startswith("Roadmap desfasado:") for l in r.stdout.splitlines()), r.stdout


def test_t42_fix2_gap2_check_cubre_los_tipos_del_criterio_2(tmp_path):
    """Gap 2 (e): el criterio 2 (enmendado en fix2) cita los tipos reales: ledger rancio, ledger reabierto, cierre
    olvidado con retro hecha, plan, spec y fila del índice. `--check` los ve todos; la puesta al día los deja en 0."""
    cal = "".join(f"| 2026-01-09 | {s} | −1 % | −1 % | 1 | c | a |\n" for s in ("plan-rancio", "olvidado"))
    roadmap = proyecto(tmp_path, filas_cal=cal)
    iniciativa(roadmap, "2026-01-01-ledger-rancio", tasks=ledger("borrador", ("completado", "en-progreso")))
    iniciativa(roadmap, "2026-01-02-reabierto", tasks=ledger("completado", ("completado", "en-progreso")))
    iniciativa(roadmap, "2026-01-03-olvidado", tasks=ledger("en-progreso"), retro=RETRO,
               spec=artefacto("spec", "aprobada"))
    iniciativa(roadmap, "2026-01-04-plan-rancio", tasks=ledger("completado"), retro=RETRO,
               plan=artefacto("plan", "en-progreso"))
    code, out = run_json(roadmap, "--check")
    assert code == 1
    vistos = {(d["tipo"], d.get("motivo")) for d in out["desfases"]}
    assert {("ledger", None), ("ledger", "reabierta"), ("ledger", "cierre-olvidado"), ("plan", None),
            ("spec", None), ("indice", None)} <= vistos, vistos
    assert run(roadmap)[0] == 0
    assert run_json(roadmap, "--check")[0] == 0


def test_t42_fix2_gap3_fila_con_el_enlace_en_iniciativa_no_se_duplica(tmp_path):
    """Gap 3: una fila que enlaza a la carpeta en «Iniciativa» con la última columna `—` es la propia: no se
    añade otra; dos filas así → aviso, sin escribir."""
    propia = "| 2026-01-01 | [bee](2026-01-01-bee/spec.md) | a | b | — |"
    roadmap = proyecto(tmp_path, filas_indice=propia)
    iniciativa(roadmap, "2026-01-01-bee", spec=artefacto("spec", "borrador"))
    assert run(roadmap)[0] == 0
    texto = (roadmap / "README.md").read_text(encoding="utf-8")
    filas = [l for l in texto.splitlines() if "2026-01-01-bee/" in l]
    assert filas == ["| 2026-01-01 | [bee](2026-01-01-bee/spec.md) · estado: solo spec | a | b | "
                     "[spec](2026-01-01-bee/spec.md) |"], filas
    assert run_json(roadmap, "--check")[0] == 0
    (tmp_path / "b").mkdir()
    roadmap2 = proyecto(tmp_path / "b", filas_indice=propia + "\n" + propia.replace("| a |", "| c |"))
    iniciativa(roadmap2, "2026-01-01-bee", spec=artefacto("spec", "borrador"))
    antes = (roadmap2 / "README.md").read_bytes()
    code, out = run_json(roadmap2)
    assert code == 0 and (roadmap2 / "README.md").read_bytes() == antes
    assert any(a["tipo"] == "indice" and "2026-01-01-bee" in a["detalle"] for a in out["avisos"])


def test_t42_fix2_gap4_cache_con_entrada_incompleta_se_descarta(tmp_path):
    """Gap 4: una entrada de caché con la firma vigente pero incompleta (o de otra forma) se descarta y se
    recalcula: el aviso de desfases de la sesión sigue apareciendo."""
    roadmap = proyecto(tmp_path)
    (tmp_path / ".claude").mkdir()
    iniciativa(roadmap, "2026-01-01-uno", tasks=ledger("borrador", ("en-progreso",)))
    mod = _mod()
    assert mod.comprobar(tmp_path)["desfases"]
    cache = tmp_path / ".claude" / mod.CACHE_NOMBRE
    for roto in ({"nombre": "x"},
                 {"nombre": "x", "cambios": [{"x": 1}], "avisos": [], "etiqueta": None, "enlaces": [],
                  "titulo": None, "retro": False, "cerrable": False, "vigente": True}):
        datos = json.loads(cache.read_text(encoding="utf-8"))
        datos["inic"]["2026-01-01-uno"]["plan"] = roto
        cache.write_text(json.dumps(datos), encoding="utf-8")
        assert mod.comprobar(tmp_path)["desfases"], roto
        datos["inic"]["2026-01-01-uno"]["plan"] = roto
        cache.write_text(json.dumps(datos), encoding="utf-8")
        r = subprocess.run([sys.executable, str(KIT / "progress-report.py"), "session", "--root", str(tmp_path)],
                           capture_output=True, encoding="utf-8", errors="replace", timeout=30)
        assert any(l.startswith("Roadmap desfasado:") for l in r.stdout.splitlines()), (roto, r.stdout)


def test_t42_fix2_gap5_cerrar_sin_campo_estado_no_es_exito_silencioso(tmp_path):
    roadmap = proyecto(tmp_path)
    texto = ("# Demo\n\n## Fase 1\n\n### T-01 — t\n\n- **Estado**: completado\n\n"
             "**Criterios de aceptación**\n- [x] a\n")
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=texto)
    antes = snapshot(tmp_path)
    code, out = run_json(c, "--cerrar")
    assert code != 0 and out["status"] == "sin_estado", out
    code, _, err = run(c, "--cerrar")
    assert code != 0 and "estado" in err
    assert snapshot(tmp_path) == antes
    code, out = run_json(roadmap, "--check")
    assert code == 1 and any(d["tipo"] == "ledger" and d.get("motivo") == "sin-estado" for d in out["desfases"])


def test_t42_fix2_gap10_tarea_nueva_en_borrador_reabre_el_ledger(tmp_path):
    """Gap 10: una tarea nueva en `borrador` (o reabierta) en un ledger `completado` es trabajo abierto: el ledger
    vuelve a `en-progreso`. Es lo correcto y la documentación lo dice (test de prosa en tests/)."""
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("completado", ("completado", "borrador")))
    code, out = run_json(roadmap, "--check")
    assert code == 1 and any(d.get("motivo") == "reabierta" for d in out["desfases"])
    assert run(roadmap)[0] == 0 and _estado(c / "tasks.md") == "estado: en-progreso"


INDICE_SLUG = """# Roadmap

| Fecha | Slug | Estado | Coste estimado | Spec | Evaluación | Plan |
|---|---|---|---|---|---|---|
{filas}
Texto que no se toca.
"""


def test_t42_fix2_gap11_indice_con_columna_slug(tmp_path):
    """Gap 11 (encontrado por la sesión kairos sobre un índice de otro proyecto): un índice que generó el plugin en
    versiones anteriores, `| Fecha | Slug | Estado | Coste estimado | Spec | Evaluación | Plan |`, se reconoce (no
    «sin tabla»), cada iniciativa encuentra su fila por el enlace a su carpeta (o por el slug y la fecha), el
    estado va a SU columna `Estado` (no una marca en otra celda) sin mover columnas, las celdas de enlace
    vacías se rellenan y una iniciativa sin fila recibe una fila con las mismas columnas."""
    filas = "\n".join((
        "| 2026-01-01 | demo | aprobada | 1.200 € | [spec](2026-01-01-demo/spec.md) | "
        "[evaluación](2026-01-01-demo/evaluation.md) | [plan](2026-01-01-demo/improvement-plan.md) |",
        "| 2026-01-02 | otra | borrador | — | [spec](2026-01-02-otra/spec.md) | — | — |",
        "| 2026-01-03 | sin-enlace | borrador | — | — | — | — |",
    ))
    roadmap = tmp_path / "docs" / "roadmap"
    roadmap.mkdir(parents=True)
    (roadmap / "README.md").write_text(INDICE_SLUG.format(filas=filas), encoding="utf-8")
    (roadmap / "CALIBRATION.md").write_text(CALIBRATION.format(filas=""), encoding="utf-8")
    iniciativa(roadmap, "2026-01-01-demo", spec=artefacto("spec", "aprobada"),
               evaluation=artefacto("evaluacion", "completado"), plan=artefacto("plan", "en-progreso"),
               tasks=ledger("en-progreso", ("completado", "en-progreso")))
    iniciativa(roadmap, "2026-01-02-otra", spec=artefacto("spec", "borrador"),
               evaluation=artefacto("evaluacion", "en-revision"))
    iniciativa(roadmap, "2026-01-03-sin-enlace", spec=artefacto("spec", "borrador"))
    iniciativa(roadmap, "2026-01-04-nueva", spec=artefacto("spec", "borrador"))
    code, out = run_json(roadmap, "--check")
    assert code == 1, out
    assert not [a for a in out["avisos"] if "sin tabla" in a["detalle"]], out["avisos"]
    assert run(roadmap)[0] == 0
    lineas = (roadmap / "README.md").read_text(encoding="utf-8").splitlines()
    assert ("| 2026-01-01 | demo | en curso | 1.200 € | [spec](2026-01-01-demo/spec.md) | "
            "[evaluación](2026-01-01-demo/evaluation.md) | [plan](2026-01-01-demo/improvement-plan.md) |") in lineas
    assert ("| 2026-01-02 | otra | evaluada | — | [spec](2026-01-02-otra/spec.md) | "
            "[eval](2026-01-02-otra/evaluation.md) | — |") in lineas
    assert "| 2026-01-03 | sin-enlace | solo spec | — | [spec](2026-01-03-sin-enlace/spec.md) | — | — |" in lineas
    nuevas = [l for l in lineas if "2026-01-04-nueva/" in l]
    assert nuevas == ["| 2026-01-04 | nueva | solo spec | No estimado | [spec](2026-01-04-nueva/spec.md) | — | — |"], nuevas
    assert all(l.count("|") == 8 for l in lineas if l.startswith("| 2026-")), lineas
    assert not any(" · estado: " in l for l in lineas)
    assert "Texto que no se toca." in lineas
    assert run_json(roadmap, "--check")[0] == 0
