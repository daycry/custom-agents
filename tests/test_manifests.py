#!/usr/bin/env python3
"""Guarda de los MANIFIESTOS del plugin (distribution T-03): `plugin.json` y `marketplace.json`.

- Las descriptions de ambos listan EXACTAMENTE las skills (carpetas de `skills/`) y comandos
  (`commands/*.md`) que existen en el repo — BIDIRECCIONAL: conjunto listado == conjunto real (una
  skill fantasma o borrada también falla) — y mencionan todos los agentes (`agents/*.md`). Mismo
  conteo que `tests/test_readme_badges.py`. Si añades/borras una pieza y olvidas los manifiestos, el
  marketplace miente.
- La description de la entrada del marketplace es la MISMA que la de `plugin.json` (sincronizadas).
- `displayName` presente (clave oficial de plugin.json: «Human-readable name shown in UI», verificada
  2026-09-03 en code.claude.com/docs/en/plugins-reference.md).
- Las `tags` del marketplace ⊆ `keywords` de plugin.json e incluyen las de distribución
  (jira, agile, sdd, budgeting, tdd, code-review, evals).

Ejecutar: python3 tests/test_manifests.py   (o pytest -q tests)
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, ".claude-plugin", "plugin.json")
MARKET = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
KEYWORDS_DISTRIBUCION = {"jira", "agile", "sdd", "budgeting", "tdd", "code-review", "evals"}


def piezas():
    skills = sorted(d for d in os.listdir(os.path.join(ROOT, "skills"))
                    if os.path.isdir(os.path.join(ROOT, "skills", d)))
    commands = sorted(f[:-3] for f in os.listdir(os.path.join(ROOT, "commands")) if f.endswith(".md"))
    agents = sorted(f[:-3] for f in os.listdir(os.path.join(ROOT, "agents")) if f.endswith(".md"))
    return skills, commands, agents


def cargar():
    with open(PLUGIN, encoding="utf-8") as f:
        plugin = json.load(f)
    with open(MARKET, encoding="utf-8") as f:
        market = json.load(f)
    return plugin, market


# `/nombre` que no forma parte de una ruta (`.claude/dev.json` no cuenta)
COMANDO_RE = re.compile(r"(?<![\w./])/([a-z][a-z0-9-]*)(?![\w/-])")
SKILLS_SEG_RE = re.compile(r"Skills:\s*(.+?)\.(?:\s|$)")


def listados(desc):
    """(skills, comandos) que la description LISTA: comandos = todo `/x` fuera de rutas; skills = la
    enumeración que sigue a «Skills:» hasta el punto (sin paréntesis explicativos), separada por
    comas / «y» / «and»."""
    comandos = set(COMANDO_RE.findall(desc))
    m = SKILLS_SEG_RE.search(desc)
    seg = re.sub(r"\([^)]*\)", "", m.group(1)) if m else ""
    skills = {t.strip() for t in re.split(r",|\by\b|\band\b", seg) if t.strip()}
    return skills, comandos


def discrepancias(desc):
    """Lista de problemas: piezas reales que faltan Y piezas listadas que no existen (bidireccional)."""
    skills, commands, agents = piezas()
    l_skills, l_cmds = listados(desc)
    out = []
    out += [f"skill {s} existe y no se lista" for s in skills if s not in l_skills]
    out += [f"skill {s} se lista y NO existe en skills/" for s in sorted(l_skills - set(skills))]
    out += [f"comando /{c} existe y no se lista" for c in commands if c not in l_cmds]
    out += [f"comando /{c} se lista y NO existe en commands/" for c in sorted(l_cmds - set(commands))]
    out += [f"agente {a} no se menciona" for a in agents if a not in desc]
    return out


def faltantes(desc):   # compatibilidad con el nombre anterior
    return discrepancias(desc)


def test_descriptions_listan_exactamente_las_piezas():
    plugin, market = cargar()
    assert discrepancias(plugin["description"]) == [], f"plugin.json: {discrepancias(plugin['description'])}"
    for entry in market["plugins"]:
        assert discrepancias(entry["description"]) == [], f"marketplace.json ({entry['name']}): {discrepancias(entry['description'])}"
    skills, commands, _a = piezas()
    l_skills, l_cmds = listados(plugin["description"])
    assert l_skills == set(skills) and l_cmds == set(commands)      # igualdad de conjuntos, no ⊆


def test_description_sincronizada():
    plugin, market = cargar()
    entry = next(e for e in market["plugins"] if e["name"] == plugin["name"])
    assert entry["description"] == plugin["description"], "la description de marketplace.json difiere de plugin.json"


def test_display_name_y_keywords():
    plugin, market = cargar()
    assert isinstance(plugin.get("displayName"), str) and plugin["displayName"].strip()
    kw = set(plugin["keywords"])
    assert KEYWORDS_DISTRIBUCION <= kw, f"faltan keywords: {KEYWORDS_DISTRIBUCION - kw}"
    entry = next(e for e in market["plugins"] if e["name"] == plugin["name"])
    tags = set(entry["tags"])
    assert tags <= kw, f"tags del marketplace fuera de keywords: {tags - kw}"
    assert KEYWORDS_DISTRIBUCION <= tags, f"faltan tags: {KEYWORDS_DISTRIBUCION - tags}"


def test_discrepancias_detecta_ausente_y_fantasma():
    plugin, _m = cargar()
    skills, commands, _a = piezas()
    # ausente: una skill/comando real borrado de la description
    roto = plugin["description"].replace(skills[0], "xx", 1).replace(f"/{commands[0]}", "/xx", 1)
    f = discrepancias(roto)
    assert f"skill {skills[0]} existe y no se lista" in f and f"comando /{commands[0]} existe y no se lista" in f
    assert "skill xx se lista y NO existe en skills/" in f and "comando /xx se lista y NO existe en commands/" in f
    # fantasma: una skill listada que no existe en skills/ (p. ej. borrada del repo)
    fantasma = plugin["description"].replace("Skills: ", "Skills: ghost-skill, ", 1)
    assert discrepancias(fantasma) == ["skill ghost-skill se lista y NO existe en skills/"]
    fantasma_cmd = plugin["description"].replace("Comandos: ", "Comandos: /ghost-cmd, ", 1)
    assert discrepancias(fantasma_cmd) == ["comando /ghost-cmd se lista y NO existe en commands/"]
    # una ruta con barra no se confunde con un comando
    assert "dev" not in listados("opt-in en .claude/dev.json y docs/roadmap/x")[1]


def main():
    for t in (test_descriptions_listan_exactamente_las_piezas, test_description_sincronizada,
              test_display_name_y_keywords, test_discrepancias_detecta_ausente_y_fantasma):
        t()
    skills, commands, agents = piezas()
    print(f"test_manifests: 4/4 OK ({len(skills)} skills · {len(commands)} comandos · {len(agents)} agentes en ambos manifiestos)")


if __name__ == "__main__":
    main()
