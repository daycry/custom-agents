#!/usr/bin/env python3
"""Tests de journal.py (memory-health T-01). Ejecutar: python3 -m pytest -q agent-kits/shared/test_journal.py

Proyecto temporal con git real (si `git` está en PATH), un ledger de fixture en-progreso y una
tarea cuyo estado cambia sin comitear → `draft` detecta la iniciativa activa, los ficheros tocados
y la tarea cambiada; `write` es idempotente por session_id; `latest` respeta n/max-lines; `index`
regenera el README; sin git degrada con aviso; el CLI nunca sale con exit ≠ 0 salvo uso."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(HERE, "journal.py")
LEDGER_FUENTE = os.path.join(ROOT, "docs", "roadmap", "2026-09-02-adversarial-review", "tasks.md")
GIT = shutil.which("git")

spec = importlib.util.spec_from_file_location("journal", SCRIPT)
journal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(journal)


def _git(root, *args):
    return subprocess.run([GIT, "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
                          env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x",
                               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"})


def proyecto(tmp_path, con_git=True, activa=True):
    proj = tmp_path / "proj"
    led = proj / "docs" / "roadmap" / "2026-01-01-demo" / "tasks.md"
    led.parent.mkdir(parents=True)
    text = open(LEDGER_FUENTE, encoding="utf-8").read()
    if activa:
        text = text.replace("estado: completado", "estado: en-progreso", 1)
        text = text.replace("| **Estado** | completado |", "| **Estado** | en-progreso |", 1)
    led.write_text(text, encoding="utf-8")
    (proj / ".claude").mkdir()
    (proj / "src").mkdir()
    (proj / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    if con_git and GIT:
        _git(proj, "init", "-q")
        _git(proj, "add", "-A")
        _git(proj, "commit", "-q", "-m", "base")
    return proj, led


def cambia_tarea(led):
    """Pone la primera tarea completada en en-progreso (cambio SIN comitear)."""
    t = led.read_text(encoding="utf-8")
    t = t.replace("- **Estado**: completado", "- **Estado**: en-progreso", 1)
    led.write_text(t, encoding="utf-8")


def run(*args, root=None, stdin=None):
    cmd = [sys.executable, SCRIPT, *args]
    if root is not None:
        cmd += ["--root", str(root)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", input=stdin, timeout=60)
    return r.returncode, r.stdout, r.stderr


# ------------------------------------------------------------------ draft

@pytest.mark.skipif(GIT is None, reason="sin git")
def test_draft_detecta_iniciativa_ficheros_y_tarea_cambiada(tmp_path):
    proj, led = proyecto(tmp_path)
    cambia_tarea(led)
    (proj / "src" / "nuevo.py").write_text("x=1\n", encoding="utf-8")
    rc, out, _ = run("draft", "--session-id", "s1", "--reason", "other", root=proj)
    assert rc == 0
    d = json.loads(out)
    assert d["iniciativa"] == "demo" and d["session_id"] == "s1" and d["reason"] == "other"
    paths = [f["path"] for f in d["ficheros_tocados"]]
    assert "docs/roadmap/2026-01-01-demo/tasks.md" in paths and "src/nuevo.py" in paths
    assert len(d["ficheros_tocados"]) <= 10
    assert d["tareas_cambiadas"] and d["tareas_cambiadas"][0]["ahora"] == "en-progreso"
    assert d["tareas_cambiadas"][0]["antes"] == "completado" and d["tareas_cambiadas"][0]["iniciativa"] == "demo"
    assert d["resumen"] == "Sesión sobre demo" and d["decisiones"] == [] and d["pendientes"] == []


@pytest.mark.skipif(GIT is None, reason="sin git")
def test_draft_top_10_ficheros_y_excluye_la_propia_bitacora(tmp_path):
    proj, _ = proyecto(tmp_path)
    for i in range(14):
        (proj / "src" / f"f{i:02d}.py").write_text("x\n", encoding="utf-8")
    d = journal.draft(str(proj), "s")
    assert len(d["ficheros_tocados"]) == 10
    journal.write(str(proj), d)                       # crea docs/knowledge/journal/* sin comitear
    d2 = journal.draft(str(proj), "s")
    assert not any(f["path"].startswith("docs/knowledge/journal/") for f in d2["ficheros_tocados"])


def test_draft_sin_git_listas_vacias_con_aviso(tmp_path):
    proj, led = proyecto(tmp_path, con_git=False)
    cambia_tarea(led)
    rc, out, _ = run("draft", "--session-id", "s1", root=proj)
    assert rc == 0
    d = json.loads(out)
    assert d["ficheros_tocados"] == [] and d["tareas_cambiadas"] == []
    assert any("git" in a for a in d["avisos"])
    assert d["iniciativa"] == "demo"          # la iniciativa activa no depende de git


def test_draft_sin_roadmap_iniciativa_na(tmp_path):
    proj = tmp_path / "vacio"
    proj.mkdir()
    d = journal.draft(str(proj), "s")
    assert d["iniciativa"] == "n/a" and d["resumen"] == "Sesión sobre n/a"


def test_write_sin_rastro_del_plugin_no_escribe_nada(tmp_path):
    """T-fix1 (I1): un repo cualquiera con el plugin instalado NO recibe docs/knowledge/journal/."""
    proj = tmp_path / "ajeno"
    proj.mkdir()
    (proj / "a.txt").write_text("x", encoding="utf-8")
    assert journal.proyecto_con_plugin(str(proj)) is False
    assert journal.write(str(proj), journal.draft(str(proj), "s")) is None
    assert run("write", "--session-id", "s", root=proj) == (0, "", "")
    assert sorted(os.listdir(proj)) == ["a.txt"]
    # basta UNO de los tres rastros: docs/roadmap · docs/knowledge · .claude/dev.json
    for rastro in (("docs", "roadmap"), ("docs", "knowledge"), (".claude", "dev.json")):
        p = tmp_path / ("con-" + "-".join(rastro))
        (p / rastro[0]).mkdir(parents=True)
        (p / rastro[0] / rastro[1]).mkdir() if rastro[1] != "dev.json" else (p / rastro[0] / rastro[1]).write_text("{}", encoding="utf-8")
        assert journal.proyecto_con_plugin(str(p)) is True
        rc, out, _ = run("write", "--session-id", "s", root=p)
        assert rc == 0 and out.strip() == f"docs/knowledge/journal/{journal.hoy()}-sesion.md", rastro


def test_slug_sin_iniciativa_es_sesion_no_n_a(tmp_path):
    """T-fix1 (M2): sin iniciativa activa el fichero se llama <fecha>-sesion.md, nunca -n-a.md."""
    assert journal.slugify("n/a") == "sesion" and journal.slugify("") == "sesion" and journal.slugify(None) == "sesion"
    assert journal.slugify("Memory Health") == "memory-health"
    proj = tmp_path / "p"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "dev.json").write_text("{}", encoding="utf-8")
    rel = run("write", "--session-id", "s", root=proj)[1].strip()
    assert rel.endswith("-sesion.md") and "n-a" not in rel
    assert "iniciativa: n/a" in (proj / rel).read_text(encoding="utf-8")   # el frontmatter sí dice n/a


def test_draft_resumen_desde_transcripcion_y_enrich(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    tr = tmp_path / "t.jsonl"
    tr.write_text("\n".join([
        json.dumps({"type": "user", "isMeta": True, "message": {"role": "user", "content": "meta"}}),
        json.dumps({"type": "user", "message": {"role": "user", "content": "<system-reminder>x</system-reminder>"}}),
        "esto no es json",
        json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "hola"}]}}),
        json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "  Implementa   la T-03 del plan  "}]}}),
    ]), encoding="utf-8")
    d = journal.draft(str(proj), "s", transcript=str(tr))
    assert d["resumen"] == "Implementa la T-03 del plan"
    # --enrich manda sobre la transcripción y rellena decisiones/pendientes
    enr = tmp_path / "e.json"
    enr.write_text(json.dumps({"resumen": "Cerrada la fase 2", "decisiones": ["usar flock"], "pendientes": "revisar CI"}), encoding="utf-8")
    d2 = journal.draft(str(proj), "s", transcript=str(tr), enrich=str(enr))
    assert d2["resumen"] == "Cerrada la fase 2" and d2["decisiones"] == ["usar flock"] and d2["pendientes"] == ["revisar CI"]
    # transcripción inexistente → fallback, sin excepción
    assert journal.draft(str(proj), "s", transcript=str(tmp_path / "no.jsonl"))["resumen"] == "Sesión sobre demo"


def test_draft_marcadores_cerrados_hoy(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    hoy = journal.hoy()
    (proj / ".claude" / "usage-state.json").write_text(json.dumps({
        "docs/roadmap/x/tasks.md#T-01": {"inicio": "2020-01-01T00:00:00Z", "ultimoCierre": f"{hoy}T10:00:00Z"},
        "abierto": {"inicio": "2020-01-01T00:00:00Z"},
        "viejo": {"inicio": "2020-01-01T00:00:00Z", "ultimoCierre": "2020-01-02T00:00:00Z"},
    }), encoding="utf-8")
    d = journal.draft(str(proj), "s")
    assert d["marcadores_cerrados"] == ["docs/roadmap/x/tasks.md#T-01"]
    (proj / ".claude" / "usage-state.json").write_text("{ roto", encoding="utf-8")
    assert journal.draft(str(proj), "s")["marcadores_cerrados"] == []


# ------------------------------------------------------------------ write

def test_write_crea_entrada_con_frontmatter_e_indice(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    rc, out, _ = run("write", "--session-id", "abc", "--reason", "clear", root=proj)
    assert rc == 0
    rel = out.strip()
    assert rel == f"docs/knowledge/journal/{journal.hoy()}-demo.md"
    text = (proj / rel).read_text(encoding="utf-8")
    assert text.startswith("---\n") and 'session_id: "abc"' in text and "reason: clear" in text
    assert "iniciativa: demo" in text and "fuente: hook" in text and "## Decisiones" in text
    idx = (proj / "docs" / "knowledge" / "journal" / "README.md").read_text(encoding="utf-8")
    assert f"[{journal.hoy()}]({journal.hoy()}-demo.md) | demo |" in idx


def test_write_idempotente_por_session_id_y_sufijo_para_otra_sesion(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    d = proj / "docs" / "knowledge" / "journal"
    run("write", "--session-id", "abc", root=proj)
    enr = tmp_path / "e.json"
    enr.write_text(json.dumps({"decisiones": ["D1"]}), encoding="utf-8")
    rc, out, _ = run("write", "--session-id", "abc", "--enrich", str(enr), root=proj)
    assert rc == 0
    ficheros = sorted(f for f in os.listdir(d) if f != "README.md")
    assert ficheros == [f"{journal.hoy()}-demo.md"]                 # actualizada, no duplicada
    texto = (d / ficheros[0]).read_text(encoding="utf-8")
    assert "- D1" in texto and "docs/knowledge/journal" not in texto.split("# Journal")[0].split("ficheros_tocados")[1]
    run("write", "--session-id", "otra", root=proj)
    ficheros = sorted(f for f in os.listdir(d) if f != "README.md")
    assert ficheros == [f"{journal.hoy()}-demo-2.md", f"{journal.hoy()}-demo.md"]
    idx = (d / "README.md").read_text(encoding="utf-8")
    assert idx.count("| demo |") == 2


def test_write_desde_draft_json_y_fuente_manual(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    e = journal.draft(str(proj), "s9")
    e["resumen"] = "Resumen manual"
    dj = tmp_path / "d.json"
    dj.write_text(json.dumps(e), encoding="utf-8")
    rc, out, _ = run("write", "--session-id", "s9", "--fuente", "manual", "--draft", str(dj), root=proj)
    assert rc == 0
    text = (proj / out.strip()).read_text(encoding="utf-8")
    assert 'resumen: "Resumen manual"' in text and "fuente: manual" in text
    # draft ilegible → error de uso (2), sin escribir nada
    rc2, _, err = run("write", "--session-id", "s9", "--draft", str(tmp_path / "no.json"), root=proj)
    assert rc2 == 2 and "ilegible" in err


# ------------------------------------------------------------------ latest / index

def test_latest_vacio_sin_carpeta_y_con_una_entrada(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    assert run("latest", root=proj) == (0, "", "")
    run("write", "--session-id", "a", root=proj)
    rc, out, _ = run("latest", "--n", "2", "--max-lines", "25", root=proj)
    assert rc == 0
    assert out.startswith("Journal de sesión") and "1 última(s)" in out and "· demo ·" in out
    assert len(out.splitlines()) <= 25


def test_latest_mismo_dia_solo_ultima_y_dias_distintos_ambas(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    d = proj / "docs" / "knowledge" / "journal"
    d.mkdir(parents=True)
    hoy = journal.hoy()

    def entrada(fecha, sid, resumen):
        e = journal.draft(str(proj), sid)
        e["fecha"], e["resumen"] = fecha, resumen
        journal.write(str(proj), e)

    entrada(hoy, "s1", "primera de hoy")
    entrada(hoy, "s2", "segunda de hoy")
    out = journal.latest(str(proj), n=2)
    assert "segunda de hoy" in out and "primera de hoy" not in out       # mismo día → solo la última
    entrada("2020-05-05", "s0", "sesión antigua")
    out = journal.latest(str(proj), n=2)
    assert "segunda de hoy" in out and "sesión antigua" in out and "primera de hoy" not in out
    assert out.splitlines()[1].startswith(f"- {hoy}")                      # la más reciente primero


def test_latest_respeta_max_lines(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    e = journal.draft(str(proj), "s")
    e["decisiones"] = [f"d{i}" for i in range(5)]
    e["pendientes"] = [f"p{i}" for i in range(5)]
    e["ficheros_tocados"] = [{"path": f"f{i}.py", "cambio": "M"} for i in range(9)]
    e["tareas_cambiadas"] = [{"iniciativa": "demo", "id": f"T-0{i}", "titulo": "t", "antes": "borrador", "ahora": "completado"} for i in range(6)]
    journal.write(str(proj), e)
    out = journal.latest(str(proj), n=2, max_lines=3)
    assert len(out.splitlines()) == 3 and out.splitlines()[-1].strip() == "…"
    full = journal.latest(str(proj))
    assert "(+2)" in full and "f0.py" in full and "(+4)" in full


def test_index_regenera_y_no_lista_readme(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    run("write", "--session-id", "a", root=proj)
    d = proj / "docs" / "knowledge" / "journal"
    (d / "README.md").write_text("basura", encoding="utf-8")
    (d / "suelto.md").write_text("# sin frontmatter\n", encoding="utf-8")
    rc, out, _ = run("index", root=proj)
    assert rc == 0 and out.strip() == "docs/knowledge/journal/README.md"
    idx = (d / "README.md").read_text(encoding="utf-8")
    assert idx.startswith("# `docs/knowledge/journal/`") and "suelto" not in idx and "| demo |" in idx
    # sin carpeta → nada, exit 0
    assert run("index", root=tmp_path / "nada") == (0, "", "")


def test_parse_entry_roundtrip_listas(tmp_path):
    proj, _ = proyecto(tmp_path, con_git=False)
    e = journal.draft(str(proj), "rt")
    e["decisiones"] = ['con "comillas" y | barra']
    e["ficheros_tocados"] = [{"path": "a b.py", "cambio": "??"}]
    p = journal.write(str(proj), e)
    back = journal.parse_entry(p)
    assert back["session_id"] == "rt" and back["decisiones"] == ['con "comillas" y | barra']
    assert back["ficheros_tocados"] == ["a b.py (??)"] and back["pendientes"] == []


def test_cli_sin_subcomando_es_error_de_uso():
    rc, _, _ = run()
    assert rc == 2
