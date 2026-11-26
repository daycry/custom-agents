"""Tests de roadmap-sync.py (plugin-audit-2 T-42): el plugin mantiene el roadmap al día por sí mismo.

Estado del ledger, del plan, de la spec y de la evaluación, y la fila del índice `docs/roadmap/README.md`,
derivados de los estados de las tareas y de los artefactos (tabla de transiciones de `phase6-close.md`).
Disparadores: `ledger-write.py verdict`, `retro-gate.py --sync` y la puerta de `/pm-cycle` (`gate`).
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
    code, out = run_json(c)
    assert code == 0
    assert "estado: completado   # comentario" in (c / "tasks.md").read_text(encoding="utf-8")
    assert {"iniciativa": "2026-01-01-demo", "tipo": "ledger", "artefacto": "tasks.md",
            "de": "en-progreso", "a": "completado"} in out["cambios"]
    antes = snapshot(tmp_path)
    code, out = run_json(c)
    assert code == 0 and out["changed"] is False and snapshot(tmp_path) == antes


def test_ledger_tabla_de_cabecera_sin_frontmatter(tmp_path):
    roadmap = proyecto(tmp_path)
    texto = ("# Checklist — demo\n\n| | |\n|---|---|\n| **Estado** | en-progreso |\n\n## Fase 1 — Única\n\n"
             "### T-01 — t\n\n- **Estado**: completado\n\n**Criterios de aceptación**\n- [x] a\n")
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=texto)
    assert run(c)[0] == 0
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
    code, out = run_json(roadmap)
    assert code == 0
    assert "estado: aprobada" in (c / "spec.md").read_text(encoding="utf-8")
    assert "estado: en-progreso" in (c / "improvement-plan.md").read_text(encoding="utf-8")
    assert "estado: completado" in (c / "tasks.md").read_text(encoding="utf-8")
    assert [a["tipo"] for a in out["avisos"] if a["iniciativa"] == "2026-01-01-demo"] == ["retro-pendiente"]


def test_spec_aprobada_completa_la_evaluacion(tmp_path):
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", spec=artefacto("spec", "aprobada"),
                   evaluation=artefacto("evaluacion", "en-revision"))
    assert run(c)[0] == 0
    assert "estado: completado" in (c / "evaluation.md").read_text(encoding="utf-8")


def test_nunca_rebaja_un_estado_y_reporta_el_adelantado(tmp_path):
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger("completado", ("completado", "en-progreso")))
    antes = (c / "tasks.md").read_bytes()
    code, out = run_json(c, "--check")
    assert (c / "tasks.md").read_bytes() == antes
    assert [a["tipo"] for a in out["avisos"]] == ["adelantado"]
    assert not [d for d in out["desfases"] if d["artefacto"] == "tasks.md"]


def test_via_rapida_solo_tasks(tmp_path):
    roadmap = proyecto(tmp_path)
    c = iniciativa(roadmap, "2026-01-01-rapida", tasks=ledger())
    assert run(roadmap)[0] == 0
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
    code, out = run_json(c)
    assert code == 0 and not (roadmap / "README.md").exists()
    assert "estado: completado" in (c / "tasks.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------- índice

def test_indice_regenera_solo_su_fila(tmp_path):
    otra = fila("2026-01-02-otra", "otra — algo `con | pipe`", "[tasks](2026-01-02-otra/tasks.md)")
    propia = fila("2026-01-01-demo", "demo — texto del autor", "[tasks](2026-01-01-demo/tasks.md)")
    roadmap = proyecto(tmp_path, filas_indice=otra + "\n" + propia)
    c = iniciativa(roadmap, "2026-01-01-demo", tasks=ledger(), spec=artefacto("spec", "aprobada"))
    assert run(c)[0] == 0
    lineas = (roadmap / "README.md").read_text(encoding="utf-8").splitlines()
    assert otra in lineas, "la fila de otra iniciativa no se toca"
    nueva = next(l for l in lineas if "2026-01-01-demo/" in l)
    assert "demo — texto del autor · estado: completada, retro pendiente |" in nueva
    assert nueva.endswith("[tasks](2026-01-01-demo/tasks.md) · [spec](2026-01-01-demo/spec.md) |")
    assert "**Calibración:** texto que no se toca." in lineas
    antes = snapshot(tmp_path)
    assert run(c)[0] == 0 and snapshot(tmp_path) == antes


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
    iniciativa(roadmap, "2026-01-01-ledger-rancio", tasks=ledger())
    iniciativa(roadmap, "2026-01-02-plan-rancio", tasks=ledger("completado"), retro=RETRO,
               plan=artefacto("plan", "en-progreso"))
    iniciativa(roadmap, "2026-01-03-spec-rancia", tasks=ledger("completado"), retro=RETRO,
               spec=artefacto("spec", "aprobada"))
    iniciativa(roadmap, "2026-01-04-eval-rancia", spec=artefacto("spec", "aprobada"),
               evaluation=artefacto("evaluacion", "en-revision"))
    code, out = run_json(roadmap, "--check")
    assert code == 1
    tipos = {d["tipo"] for d in out["desfases"]}
    assert tipos == {"ledger", "plan", "spec", "evaluacion", "indice"}
    code, out_text, _ = run(roadmap, "--check")
    assert code == 1 and "desfase ledger" in out_text
    assert run(roadmap)[0] == 0
    code, out = run_json(roadmap, "--check")
    assert code == 0 and out["desfases"] == []
    assert [a["iniciativa"] for a in out["avisos"] if a["tipo"] == "retro-pendiente"] == ["2026-01-01-ledger-rancio"]
    code, out_text, _ = run(roadmap, "--check")
    assert code == 0 and "aviso retro-pendiente: 2026-01-01-ledger-rancio" in out_text


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
    assert "estado: completado" in (c / "tasks.md").read_text(encoding="utf-8")
    assert "· estado: completada, retro pendiente" in (roadmap / "README.md").read_text(encoding="utf-8")
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
