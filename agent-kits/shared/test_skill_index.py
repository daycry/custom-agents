#!/usr/bin/env python3
"""Tests de skill-index.py (índice compacto de piezas inyectado al arrancar; activation-reliability T-02).

Ejecutar:  python3 -m pytest agent-kits/shared/test_skill_index.py -q
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = HERE / "skill-index.py"
REPO = HERE.parent.parent

_SPEC = importlib.util.spec_from_file_location("skill_index", SCRIPT)
si = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(si)


# ------------------------------------------------------------------ helpers ----

def plugin(tmp_path, n_skills=2, n_cmds=1, n_agents=1, desc=None):
    """Plugin sintético con frontmatters válidos."""
    root = tmp_path / "plugin"
    d = desc or "Hace una cosa concreta con mucho cuidado. Segunda frase que no debe salir. Úsala cuando el usuario diga «hazlo»."
    for i in range(n_skills):
        p = root / "skills" / f"skill-{i}"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text(f"---\nname: skill-{i}\ndescription: >\n  {d}\n---\n# cuerpo\n", encoding="utf-8")
    for i in range(n_cmds):
        (root / "commands").mkdir(parents=True, exist_ok=True)
        (root / "commands" / f"cmd-{i}.md").write_text(
            f"---\ndescription: {d}\nargument-hint: \"<objetivo> [rapido | completo]\"\n---\n# cmd\n", encoding="utf-8")
    for i in range(n_agents):
        (root / "agents").mkdir(parents=True, exist_ok=True)
        (root / "agents" / f"agent-{i}.md").write_text(
            f"---\nname: agent-{i}\ndescription: {d}\nmodel: sonnet\ntools: Read\n---\n# agente\n", encoding="utf-8")
    return root


def run(args, env_extra=None, cwd=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_ROOT")}
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, str(SCRIPT)] + args, capture_output=True, text=True, env=env, cwd=cwd)
    return r.returncode, r.stdout, r.stderr


# ------------------------------------------------------------------ tests ----

def test_determinista_y_estructura_sobre_el_repo_real():
    a = si.construir(si.piezas(str(REPO)))
    b = si.construir(si.piezas(str(REPO)))
    assert a["texto"] == b["texto"] and a["hash"] == b["hash"]
    lineas = a["lineas"]
    assert lineas[:3] == si.CABECERA
    assert "Comandos:" in lineas and "Skills:" in lineas and "Agentes:" in lineas
    assert lineas.index("Comandos:") < lineas.index("Skills:") < lineas.index("Agentes:")
    # una línea por pieza salvo recorte por LIMITE_LINEAS (superiority T-05/T-06: el repo real ya
    # roza el tope con 40+ piezas — cada grupo recortado cierra en una línea «… y N piezas más», así
    # que el conteo válido es «líneas de pieza visibles + piezas resumidas en extras == n», no un
    # número fijo de líneas; `test_tope_de_tamano_sobre_el_repo_real` ya cubre que quepa en el tope.
    n = sum(1 for d in ("commands", "agents") for f in os.listdir(REPO / d) if f.endswith(".md"))
    n += sum(1 for d in os.listdir(REPO / "skills") if (REPO / "skills" / d / "SKILL.md").is_file())
    extras = [l for l in lineas if l.startswith("… y ")]
    ocultas = sum(int(l.split()[2]) for l in extras)
    n_lineas_de_pieza = len(lineas) - 3 - 3 - len(extras)   # cabecera(3) + 3 encabezados de grupo
    assert a["piezas"] == n
    assert n_lineas_de_pieza + ocultas == n, (n_lineas_de_pieza, ocultas, n)
    assert len(lineas) <= 3 + 3 + n
    assert any(l.startswith("/dev-cycle ") for l in lineas) and any(l.startswith("quick-implement — ") for l in lineas)


def test_tope_de_tamano_sobre_el_repo_real():
    idx = si.construir(si.piezas(str(REPO)))
    assert idx["n_lineas"] <= si.LIMITE_LINEAS, idx["n_lineas"]
    assert idx["chars"] <= si.LIMITE_CHARS, idx["chars"]
    for l in idx["lineas"]:
        assert len(l) <= si.LIMITE_LINEA, (len(l), l)


def test_tope_se_respeta_aunque_haya_muchas_piezas_con_descriptions_largas(tmp_path):
    root = plugin(tmp_path, n_skills=20, n_cmds=10, n_agents=8, desc="Palabra " * 60 + "final.")
    idx = si.construir(si.piezas(str(root)))
    assert idx["chars"] <= si.LIMITE_CHARS and all(len(l) <= si.LIMITE_LINEA for l in idx["lineas"])
    assert idx["ancho"] < si.LIMITE_LINEA          # el ancho por línea bajó para caber


def test_recorte_de_description_primera_frase_o_gatillo():
    assert si.resumen("Hace X con Y y Z de forma bastante detallada y larga. Segunda frase larga. Úsala cuando digan hola.", 110) == "Hace X con Y y Z de forma bastante detallada y larga"
    assert si.resumen("Convierte a PDF, p. ej. informes largos de la cartera. Otra frase.", 110) == "Convierte a PDF, p. ej. informes largos de la cartera"
    assert si.resumen("Sin punto pero con gatillo largo de verdad para pasar el mínimo. Úsalo cuando X", 110) == "Sin punto pero con gatillo largo de verdad para pasar el mínimo"
    # primera frase-título corta arrastra la siguiente (MIN_FRASE)
    assert si.resumen("Experto en X. Conversa con el humano para convertir ideas. Tercera.", 110) == "Experto en X. Conversa con el humano para convertir ideas"
    # exceso → corte en palabra + «…», nunca más largo que el ancho
    r = si.resumen("palabra " * 40, 50)
    assert r.endswith("…") and len(r) <= 50
    assert si.resumen("", 110) == "(sin description)"
    assert si.resumen("**Negrita** y `código` limpios.", 110) == "Negrita y código limpios"


def test_hint_corto():
    assert si.hint_corto('"<objetivo de la iniciativa> [rapido | completo] [--superpowers]"') == "<objetivo de la iniciativa> [rapido | completo] [--superpowers]"
    assert si.hint_corto('"(opcional) ruta al roadmap; por defecto docs/roadmap"') == "[opcional]"
    assert si.hint_corto('"(sin argumentos)"') == ""
    assert si.hint_corto("prosa cualquiera") == "<args>"
    assert si.hint_corto("") == ""


def test_cache_invalidada_por_cambio_de_frontmatter(tmp_path):
    root = plugin(tmp_path)
    proj = tmp_path / "proj"
    (proj / ".claude").mkdir(parents=True)
    env = {"CLAUDE_PROJECT_DIR": str(proj), "CLAUDE_PLUGIN_ROOT": str(root)}
    rc, out1, _ = run([], env)
    assert rc == 0 and "Comandos:" in out1
    cache = proj / ".claude" / ".skill-index.cache"
    assert cache.is_file()
    h1 = cache.read_text(encoding="utf-8").splitlines()[0]
    assert h1.startswith("# skill-index ") and len(h1.split()[-1]) == 16
    # 2.ª ejecución: mismo hash → se sirve desde la caché (texto idéntico)
    rc, out2, _ = run(["--json"], env)
    d = json.loads(out2)
    assert d["cache"] is True and d["texto"] == out1.rstrip("\n")
    # cambia una description → hash distinto, regeneración y caché reescrita
    sk = root / "skills" / "skill-0" / "SKILL.md"
    sk.write_text(sk.read_text(encoding="utf-8").replace("Hace una cosa concreta", "Hace OTRA cosa distinta"), encoding="utf-8")
    rc, out3, _ = run(["--json"], env)
    d3 = json.loads(out3)
    assert d3["cache"] is False and d3["hash"] != d["hash"] and "OTRA cosa" in d3["texto"]
    assert cache.read_text(encoding="utf-8").splitlines()[0] == f"# skill-index {d3['hash']}"
    # --no-cache: ni lee ni escribe
    cache.write_text("# skill-index 0000000000000000\nbasura\n", encoding="utf-8")
    rc, out4, _ = run(["--no-cache"], env)
    assert "OTRA cosa" in out4 and cache.read_text(encoding="utf-8").startswith("# skill-index 0000000000000000")


def test_cache_corrupta_no_utf8_se_regenera_y_sobrescribe(tmp_path):
    """Gap Important #1 (revisión intento 1): caché con bytes no UTF-8 → antes stdout vacío y la caché
    corrupta se conservaba (el índice desaparecía de todas las sesiones). Ahora se regenera y sobrescribe."""
    root = plugin(tmp_path)
    proj = tmp_path / "proj"
    (proj / ".claude").mkdir(parents=True)
    cache = proj / ".claude" / ".skill-index.cache"
    cache.write_bytes(b"garbage\x00\xff")
    env = {"CLAUDE_PROJECT_DIR": str(proj), "CLAUDE_PLUGIN_ROOT": str(root)}
    rc, out, err = run([], env)
    assert rc == 0 and "Comandos:" in out and err == ""
    assert cache.read_text(encoding="utf-8").startswith("# skill-index ")
    # hash correcto pero cuerpo vacío → también regenera
    cache.write_text(f"# skill-index {json.loads(run(['--json'], env)[1])['hash']}\n", encoding="utf-8")
    rc, out, _ = run([], env)
    assert rc == 0 and "Comandos:" in out


def test_limite_de_lineas_recorta_grupos_proporcionalmente(tmp_path):
    """Gap Minor #3: LIMITE_LINEAS se aplica — 60 skills + 11 comandos + 8 agentes → ≤ 45 líneas, cada
    grupo recortado cierra con «… y N piezas más (ver `<carpeta>/`)» y los tres bloques siguen presentes."""
    root = plugin(tmp_path, n_skills=60, n_cmds=11, n_agents=8)
    idx = si.construir(si.piezas(str(root)))
    assert idx["n_lineas"] <= si.LIMITE_LINEAS and idx["chars"] <= si.LIMITE_CHARS
    extras = [l for l in idx["lineas"] if l.startswith("… y ")]
    assert len(extras) == 3 and any("`skills/`" in l for l in extras)
    n_skill_lineas = sum(1 for l in idx["lineas"] if l.startswith("skill-"))
    n_extra_skills = int([l for l in extras if "`skills/`" in l][0].split()[2])
    assert n_skill_lineas + n_extra_skills == 60                 # nada se pierde: visibles + «N más»
    assert n_skill_lineas > sum(1 for l in idx["lineas"] if l.startswith("agent-"))   # proporcional


def test_plugin_sin_piezas_exit_0_sin_salida(tmp_path):
    vacio = tmp_path / "vacio"
    vacio.mkdir()
    assert run(["--root", str(vacio)]) == (0, "", "")
    # raíz con carpetas pero sin ficheros .md → tampoco
    (vacio / "skills").mkdir()
    (vacio / "commands").mkdir()
    assert run(["--root", str(vacio)]) == (0, "", "")
    # sin CLAUDE_PLUGIN_ROOT ni plugin localizable: el propio kit del repo es el fallback (dirname)
    rc, out, _ = run([], {"HOME": str(tmp_path)}, cwd=str(tmp_path))
    assert rc == 0 and "Comandos:" in out


def test_frontmatter_roto_no_rompe(tmp_path):
    root = plugin(tmp_path)
    (root / "skills" / "rota").mkdir()
    (root / "skills" / "rota" / "SKILL.md").write_text("---\nname: rota\ndescription: sin cierre", encoding="utf-8")
    (root / "agents" / "sinfm.md").write_text("# sin frontmatter\n", encoding="utf-8")
    (root / "commands" / "bin.md").write_bytes(b"---\ndescription: \xff\xfe binario\n---\n")
    rc, out, err = run(["--root", str(root), "--no-cache"])
    assert rc == 0 and err == ""
    assert "rota — (sin description)" in out and "sinfm — (sin description)" in out and "/bin — (sin description)" in out


def test_json(tmp_path):
    root = plugin(tmp_path)
    rc, out, _ = run(["--root", str(root), "--no-cache", "--json"])
    assert rc == 0
    d = json.loads(out)
    assert set(d) >= {"lineas", "texto", "chars", "n_lineas", "hash", "piezas", "cache"}
    assert d["piezas"] == 4 and d["n_lineas"] == len(d["lineas"]) and d["chars"] == len(d["texto"])
    assert d["texto"] == "\n".join(d["lineas"])
    assert "Segunda frase" not in d["texto"]           # recorte en la primera frase
    assert any(l.startswith("/cmd-0 <objetivo> [rapido | completo] — ") for l in d["lineas"])


def test_dev_json_off_y_corrupto(tmp_path):
    root = plugin(tmp_path)
    proj = tmp_path / "proj"
    (proj / ".claude").mkdir(parents=True)
    env = {"CLAUDE_PROJECT_DIR": str(proj), "CLAUDE_PLUGIN_ROOT": str(root)}
    (proj / ".claude" / "dev.json").write_text('{"sesion": {"indice": false}}', encoding="utf-8")
    assert run([], env) == (0, "", "")
    assert not (proj / ".claude" / ".skill-index.cache").exists()
    (proj / ".claude" / "dev.json").write_text('{"sesion": {"indice": true}}', encoding="utf-8")
    assert "Comandos:" in run([], env)[1]
    (proj / ".claude" / "dev.json").write_text('{ roto', encoding="utf-8")          # corrupto → activado
    assert "Comandos:" in run([], env)[1]


def test_exit_0_siempre_con_root_inexistente_y_cache_no_escribible(tmp_path):
    assert run(["--root", str(tmp_path / "no-existe")]) == (0, "", "")
    root = plugin(tmp_path)
    rc, out, _ = run(["--root", str(root), "--cache", str(tmp_path / "fichero-plano" / "x" / "cache")])
    assert rc == 0 and "Comandos:" in out
    # caché apuntando a un fichero como directorio padre → se ignora el fallo de escritura
    (tmp_path / "plano").write_text("x", encoding="utf-8")
    rc, out, _ = run(["--root", str(root), "--cache", str(tmp_path / "plano" / "cache")])
    assert rc == 0 and "Comandos:" in out
