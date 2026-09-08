#!/usr/bin/env python3
"""La DOCTRINA del plugin viaja con él y la memoria del proyecto nace vacía (iniciativa `memory-retrieval`,
Fase 5: T-15 assets · T-16 `knowledge-find.py --doctrina` + prompt del `evaluator`; spec CA-21/CA-22).

Doctrina = lo que es cierto para CUALQUIER proyecto que use estos agentes (hoy: las 9 lecciones de
«Estimación / calibración», `LES-001…009`). Vive UNA vez como memoria de este repo (`docs/knowledge/lessons/`)
y viaja como copia byte a byte en `agent-kits/evaluator/assets/doctrina/` — la copia es inevitable porque
`docs/` no llega a una instalación «copiar como `.claude/`»; este test es lo que la mantiene idéntica (mismo
patrón que `tests/test_ci_manual_copy.py` con los `.MANUAL-COPY`). La memoria del PROYECTO consumidor
(`docs/knowledge/`) no se toca: `--doctrina` lee los assets, y sin la bandera un proyecto sin memoria da 0.

Ejecutar: python3 -m pytest -q tests/test_doctrina_viaja.py
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
DOCTRINA = os.path.join(ROOT, "agent-kits", "evaluator", "assets", "doctrina")
LESSONS = os.path.join(ROOT, "docs", "knowledge", "lessons")
KF = os.path.join(ROOT, "agent-kits", "shared", "knowledge-find.py")
EVALUATOR = os.path.join(ROOT, "agents", "evaluator.md")
KIT_README = os.path.join(ROOT, "agent-kits", "evaluator", "README.md")
IDS = [f"LES-00{i}" for i in range(1, 10)]
NO_DOCTRINA = ("LES-010", "LES-011", "LES-012", "LES-013", "LES-014")
TOPE_EVALUATOR = 15513          # bytes (LF) del prompt del evaluator el 2026-09-04 — spec CA-22: no crece


def run(*args, cwd=None, script=KF):
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run([sys.executable, script, *args], cwd=cwd or ROOT, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    return r.returncode, r.stdout, r.stderr


def ficheros_doctrina():
    return sorted(f for f in os.listdir(DOCTRINA) if f.endswith(".md")) if os.path.isdir(DOCTRINA) else []


def diferencias(doctrina_dir, lessons_dir):
    """Ficheros de la doctrina sin original en lessons/ o que no son byte a byte iguales a él."""
    out = []
    for fn in sorted(os.listdir(doctrina_dir)):
        if not fn.endswith(".md"):
            continue
        orig = os.path.join(lessons_dir, fn)
        if not os.path.isfile(orig):
            out.append((fn, "sin original"))
        elif open(os.path.join(doctrina_dir, fn), "rb").read() != open(orig, "rb").read():
            out.append((fn, "difiere"))
    return out


# ------------------------------------------------------------------ T-15: los assets

def test_son_exactamente_las_nueve_lecciones_de_estimacion():
    fs = ficheros_doctrina()
    assert [f[:7] for f in fs] == IDS, fs
    for fn in fs:
        fm = open(os.path.join(DOCTRINA, fn), encoding="utf-8").read().split("---")[1]
        assert "tipo: leccion" in fm and "area: Estimación / calibración" in fm, fn
        assert re.search(r"^estado: aceptada", fm, re.M), fn          # doctrina = aceptada, nunca propuesta


def test_una_sola_fuente_las_copias_son_byte_a_byte_y_el_comprobador_caza_divergencias(tmp_path):
    assert diferencias(DOCTRINA, LESSONS) == []
    d, l = tmp_path / "doctrina", tmp_path / "lessons"
    d.mkdir()
    l.mkdir()
    (l / "LES-001-x.md").write_bytes(b"a\n")
    (d / "LES-001-x.md").write_bytes(b"a\n")
    (d / "LES-002-y.md").write_bytes(b"b\n")
    assert diferencias(str(d), str(l)) == [("LES-002-y.md", "sin original")]
    (d / "LES-001-x.md").write_bytes(b"A\n")
    assert ("LES-001-x.md", "difiere") in diferencias(str(d), str(l))


def test_el_criterio_de_doctrina_esta_escrito_y_aplicado_entrada_por_entrada():
    t = open(KIT_README, encoding="utf-8").read()
    assert "cierta para cualquier proyecto que use estos agentes" in t
    for id_ in IDS + list(NO_DOCTRINA):
        assert id_ in t, id_                                            # las 9 que sí y las 5 que no, con su porqué
    assert "nace vacía" in t                                            # la memoria del consumidor no se siembra


def test_el_paquete_portable_declara_que_la_doctrina_no_viaja_en_el():
    spec = importlib.util.spec_from_file_location("export_skills", os.path.join(ROOT, "scripts", "export-skills.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert any("doctrina" in que for que, _ in m.NO_VIAJA)


# ------------------------------------------------------------------ T-16: --doctrina (CA-21) y el prompt (CA-22)

def test_ca21_doctrina_en_un_proyecto_sin_memoria_y_la_memoria_sigue_naciendo_vacia(tmp_path):
    proj = tmp_path / "consumidor"
    (proj / "src").mkdir(parents=True)
    rc, out, err = run("--doctrina", "--area", "estimacion", "--limit", "0", "--root", str(proj))
    lineas = [l for l in out.splitlines() if l.strip()]
    assert rc == 0 and len(lineas) == 9, (rc, out, err)
    assert all(l.split(" · ")[0] in IDS and "doctrina/" in l for l in lineas)   # cada acierto dice de dónde viene
    rc, out, err = run("--area", "estimacion", "--limit", "0", "--root", str(proj))
    assert (rc, out.strip()) == (0, "")                                            # sin --doctrina: 0 aciertos, exit 0
    assert sorted(os.listdir(proj)) == ["src"]                                     # nada se siembra en el consumidor
    rc, out, _ = run("--doctrina", "--json", "--area", "estimacion", "--limit", "0", "--root", str(proj))
    data = json.loads(out)
    assert data["total"] == 9 and data["corpus"] == "doctrina"
    assert all(a["origen"] == "doctrina" and a["ruta"].startswith("agent-kits/evaluator/assets/doctrina/") for a in data["aciertos"])
    rc, out, _ = run("--doctrina", "--show", "LES-007", "--root", str(proj))
    assert rc == 0 and out.startswith("---") and "id: LES-007" in out
    rc, out, _ = run("--doctrina", "--related", "LES-001", "--root", str(proj))
    assert rc == 0 and out.startswith("LES-001 · aceptada")
    rc, out, _ = run("--doctrina", "ratio tokens por hora", "--root", str(proj))
    assert rc == 0 and out.strip()                                                 # consulta libre sobre la doctrina
    assert sorted(os.listdir(proj)) == ["src"]


def test_doctrina_y_memoria_del_proyecto_no_se_mezclan_en_este_repo():
    rc, out, _ = run("--doctrina", "--area", "estimacion", "--limit", "0")
    lineas = [l for l in out.splitlines() if l.strip()]
    assert rc == 0 and len(lineas) == 9 and all("doctrina/" in l and "lessons/" not in l for l in lineas)
    rc, out2, _ = run("--area", "estimacion", "--tipo", "lesson", "--limit", "0")
    lineas2 = [l for l in out2.splitlines() if l.strip()]
    assert rc == 0 and len(lineas2) >= 9 and all("lessons/" in l and "doctrina/" not in l for l in lineas2)
    rc, out3, _ = run("--doctrina", "--json", "--limit", "0")
    assert json.loads(out3)["corpus"] == "doctrina"
    rc, out4, _ = run("--json", "--area", "estimacion", "--limit", "1")
    d4 = json.loads(out4)
    assert d4["corpus"] == "proyecto" and d4["aciertos"][0]["origen"] == "proyecto"


def test_sin_assets_de_doctrina_degrada_con_aviso_y_exit_0(tmp_path):
    """Instalación parcial: el kit shared sin `agent-kits/evaluator/`. Nunca bloquea; lo dice por stderr."""
    kit = tmp_path / "plugin" / "agent-kits" / "shared"
    kit.mkdir(parents=True)
    shutil.copy(KF, kit / "knowledge-find.py")
    proj = tmp_path / "proj"
    proj.mkdir()
    env = dict(os.environ)
    env.pop("CLAUDE_PLUGIN_ROOT", None)
    env.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run([sys.executable, str(kit / "knowledge-find.py"), "--doctrina", "--area", "estimacion", "--root", str(proj)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
    assert r.returncode == 0 and r.stdout.strip() == "" and "doctrina" in r.stderr
    # con CLAUDE_PLUGIN_ROOT apuntando al repo, la encuentra aunque el kit copiado no tenga el asset al lado
    env["CLAUDE_PLUGIN_ROOT"] = ROOT
    r = subprocess.run([sys.executable, str(kit / "knowledge-find.py"), "--doctrina", "--area", "estimacion", "--limit", "0", "--root", str(proj)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
    assert r.returncode == 0 and len([l for l in r.stdout.splitlines() if l.strip()]) == 9


def test_ca22_el_prompt_del_evaluator_no_engorda_y_cita_la_doctrina_en_vez_de_los_ficheros():
    raw = open(EVALUATOR, "rb").read().replace(b"\r\n", b"\n")   # el checkout de Windows añade CR: la medida es la de git (LF)
    assert len(raw) <= TOPE_EVALUATOR, f"{len(raw)} > {TOPE_EVALUATOR} bytes (spec CA-22)"
    t = raw.decode("utf-8")
    assert "--doctrina" in t
    assert "ahora viven en `docs/knowledge/lessons/LES-007" not in t   # el puntero a ficheros que el consumidor no tiene


if __name__ == "__main__":
    sys.exit(pytest.main(["-q", __file__]))
