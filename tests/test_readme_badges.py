#!/usr/bin/env python3
"""Guarda de los conteos de piezas de los README: badges ESTÁTICOS **y la prosa**.

Los badges que cuentan piezas del plugin no se actualizan solos: si añades un
agente, una skill o un comando y olvidas el badge, el README miente. Este test
compara el número del badge con lo que hay de verdad en el repo, en los DOS
idiomas (regla bilingüe de CLAUDE.md).

La FRASE de presentación repite ese conteo en palabras («Nine agents, twelve
commands…» / «Nueve agentes, doce comandos…») y también se desincroniza: tras
retirar `pdfy` los badges bajaron a 9 y la frase siguió diciendo «Ten agents» /
«Diez agentes» dos líneas más abajo (T-fix1). Así que aquí se valida igual que un
badge: palabra → número → conteo real del repo.

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

# frase de presentación con el conteo EN PALABRAS. Si la reescribes, actualiza este patrón: que el
# test falle es lo que impide que la prosa vuelva a mentir en silencio.
PROSA = {
    "README.md": re.compile(r"\b([A-Za-z]+) agents, ([A-Za-z]+) commands\b"),
    "README.es.md": re.compile(r"\b([A-Za-zÁÉÍÓÚáéíóú]+) agentes, ([A-Za-zÁÉÍÓÚáéíóú]+) comandos\b"),
}
# solo los numerales que pueden aparecer de verdad en este conteo (5-25), en los dos idiomas
NUMERALES = {
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
    "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciséis": 16, "dieciseis": 16,
    "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20,
}


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

        # --- la PROSA, con el mismo criterio que el badge
        m = PROSA[readme].search(texto)
        assert m, (f"{readme}: no encuentro la frase con el conteo en palabras "
                   f"(patrón {PROSA[readme].pattern!r}). Si la reescribiste, actualiza PROSA en "
                   f"tests/test_readme_badges.py — no la borres: es la guarda de que la prosa "
                   f"no vuelva a contradecir a los badges.")
        for palabra, carpeta in ((m.group(1), "agents"), (m.group(2), "commands")):
            real = contar(carpeta, PIEZAS[carpeta][1])
            if real is None:
                continue
            declarado = NUMERALES.get(palabra.lower())
            assert declarado is not None, (
                f"{readme}: «{palabra}» no es un numeral que este test conozca (frase: "
                f"«{m.group(0)}»). Añádelo a NUMERALES o escribe el conteo con un numeral normal.")
            assert declarado == real, (
                f"{readme}: la frase dice «{m.group(0)}» ({palabra} = {declarado}) pero hay {real} "
                f"en {carpeta}/. Actualiza la frase (y su gemela del otro idioma), no solo el badge.")
            comprobados += 1

    print(f"test_readme_badges: {comprobados} conteo(s) verificados OK (badges + prosa)")


if __name__ == "__main__":
    main()
