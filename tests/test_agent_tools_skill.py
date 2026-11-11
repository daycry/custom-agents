#!/usr/bin/env python3
"""Un agente que ordena invocar una skill debe poder llegar a ella SIN la herramienta `Skill`.

`Skill` es un concepto de Claude Code: el agente de Codex no declara `tools` y el de OpenCode usa un
`skill: allow` fijo. La vía común a los tres runtimes es leer `skills/<x>/SKILL.md` por su ruta (patrón
de `nemesis`). Este test recorre `agents/*.md`: toda skill del repo nombrada entre comillas invertidas en
una línea que habla de «skill» o «invoca» tiene que aparecer también con su ruta `skills/<x>/SKILL.md`
en el cuerpo del mismo agente.

Ejecutar: python3 tests/test_agent_tools_skill.py   (o pytest -q tests/test_agent_tools_skill.py)
"""
import glob
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = {d for d in os.listdir(os.path.join(ROOT, "skills"))
          if os.path.isfile(os.path.join(ROOT, "skills", d, "SKILL.md"))}
AGENTES = sorted(glob.glob(os.path.join(ROOT, "agents", "*.md")))


def _cuerpo(path):
    texto = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    return texto.split("---", 2)[2]


def skills_ordenadas(cuerpo):
    """Skills del repo nombradas como `x` en una línea con «skill» o «invoca»."""
    out = set()
    for linea in cuerpo.split("\n"):
        if not re.search(r"skill|invoca", linea, re.I):
            continue
        out.update(m for m in re.findall(r"`([a-z0-9-]+)`", linea) if m in SKILLS)
    return out


def test_hay_agentes_que_ordenan_skills():
    assert any(skills_ordenadas(_cuerpo(a)) for a in AGENTES), "el detector no ve ninguna skill: revisa la regla"


@pytest.mark.parametrize("agente", AGENTES, ids=[os.path.basename(a) for a in AGENTES])
def test_toda_skill_que_el_agente_ordena_invocar_lleva_su_ruta(agente):
    cuerpo = _cuerpo(agente)
    sin_ruta = sorted(s for s in skills_ordenadas(cuerpo) if f"skills/{s}/SKILL.md" not in cuerpo)
    assert not sin_ruta, (f"{os.path.basename(agente)} ordena invocar {sin_ruta} sin dar `skills/<x>/SKILL.md`: "
                          "sin la herramienta Skill (Codex, OpenCode) el agente no tiene cómo cargarlas")


def test_el_detector_ve_una_skill_sin_ruta():
    assert skills_ordenadas("Invoca la skill `tdd` y sigue.") == {"tdd"}
    assert "tdd" not in skills_ordenadas("Texto sin la palabra clave `tdd`.")


def main():
    return pytest.main([os.path.abspath(__file__), "-q"])


if __name__ == "__main__":
    sys.exit(main())
