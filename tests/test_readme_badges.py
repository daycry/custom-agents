#!/usr/bin/env python3
"""Guarda de los badges ESTÁTICOS de los README (agentes · skills · comandos).

Los badges que cuentan piezas del plugin no se actualizan solos: si añades un
agente, una skill o un comando y olvidas el badge, el README miente. Este test
compara el número del badge con lo que hay de verdad en el repo, en los DOS
idiomas (regla bilingüe de CLAUDE.md).

Ejecuta: python tests/test_readme_badges.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# etiqueta del badge en cada idioma → cómo se cuenta la pieza en el repo
PIEZAS = {
    "agents": ("agents", lambda d: [f for f in os.listdir(d) if f.endswith(".md")]),
    "agentes": ("agents", lambda d: [f for f in os.listdir(d) if f.endswith(".md")]),
    "skills": ("skills", lambda d: [x for x in os.listdir(d)
                                    if os.path.isdir(os.path.join(d, x))]),
    "commands": ("commands", lambda d: [f for f in os.listdir(d) if f.endswith(".md")]),
    "comandos": ("commands", lambda d: [f for f in os.listdir(d) if f.endswith(".md")]),
}

READMES = ("README.md", "README.es.md")
# badge estático de shields con contador: [![Label](.../badge/<etiqueta>-<N>-color.svg)](...)
BADGE = re.compile(r"img\.shields\.io/badge/([a-zA-Z]+)-(\d+)-")


def contar(carpeta, listar):
    d = os.path.join(ROOT, carpeta)
    if not os.path.isdir(d):
        return None  # checkout parcial: no podemos afirmar nada
    return len(listar(d))


def main():
    comprobados = 0
    for readme in READMES:
        p = os.path.join(ROOT, readme)
        if not os.path.isfile(p):
            continue
        texto = open(p, encoding="utf-8").read()
        vistos = set()
        for etiqueta, declarado in BADGE.findall(texto):
            clave = etiqueta.lower()
            if clave not in PIEZAS:
                continue  # badges estáticos sin contador de piezas (python, license…)
            carpeta, listar = PIEZAS[clave]
            real = contar(carpeta, listar)
            if real is None:
                print(f"  · {readme}: badge `{clave}` no verificable "
                      f"(falta {carpeta}/ — checkout parcial)")
                continue
            assert int(declarado) == real, (
                f"{readme}: el badge dice {clave}={declarado} pero hay {real} "
                f"en {carpeta}/. Actualiza el badge (y su gemelo del otro idioma)."
            )
            vistos.add(clave)
            comprobados += 1
        # los tres contadores deben existir en cada README
        esperados = {"agents", "skills", "commands"} if readme == "README.md" \
            else {"agentes", "skills", "comandos"}
        faltan = esperados - vistos
        if faltan and contar("agents", PIEZAS["agents"][1]) is not None:
            raise AssertionError(f"{readme}: faltan badges de piezas: {sorted(faltan)}")

    print(f"test_readme_badges: {comprobados} badge(s) verificados OK")


if __name__ == "__main__":
    main()
