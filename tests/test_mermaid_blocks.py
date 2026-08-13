#!/usr/bin/env python3
"""Guarda de los diagramas Mermaid de la documentación.

GitHub renderiza Mermaid con su propia versión, más estricta que la de muchos
editores locales: un salto de línea escrito como `\\n` dentro de una etiqueta
puede tumbar el diagrama entero con «Unable to render rich display / Cannot
read properties of undefined (reading 'render')». El salto portable —y el que
recomienda la documentación de Mermaid— es `<br/>`.

Comprueba, en TODOS los `.md` del repo:
  1. Ningún bloque ```mermaid usa `\\n` como salto de línea (usa `<br/>`).
  2. Los bloques ```mermaid están bien cerrados (fences pareadas).
  3. Cada bloque declara un tipo de diagrama en su primera línea útil.

No renderiza (eso necesitaría Chromium): es una comprobación estática, rápida
y sin dependencias, apta para CI.

Ejecuta: python tests/test_mermaid_blocks.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOQUE = re.compile(r"```mermaid\n(.*?)```", re.S)
# tipos de diagrama que usamos (amplía la lista si añades otro)
TIPOS = ("flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
         "erDiagram", "journey", "gantt", "pie", "mindmap", "timeline", "gitGraph")


def ficheros_md():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(base, f)


def main():
    errores, bloques = [], 0
    for ruta in sorted(ficheros_md()):
        rel = os.path.relpath(ruta, ROOT)
        texto = open(ruta, encoding="utf-8", errors="replace").read()
        if "```mermaid" not in texto:
            continue
        # 2) fences pareadas: tantos cierres como aperturas dentro del documento
        if texto.count("```mermaid") != len(BLOQUE.findall(texto)):
            errores.append(f"{rel}: hay un bloque ```mermaid sin cerrar")
            continue
        for i, cuerpo in enumerate(BLOQUE.findall(texto), 1):
            bloques += 1
            if "\\n" in cuerpo:
                muestra = next((l.strip() for l in cuerpo.splitlines() if "\\n" in l), "")
                errores.append(
                    f"{rel} (bloque {i}): usa `\\n` como salto de línea — GitHub puede "
                    f"no renderizarlo. Sustitúyelo por `<br/>`.\n      → {muestra[:100]}")
            primera = next((l.strip() for l in cuerpo.splitlines() if l.strip()
                            and not l.strip().startswith("%%")), "")
            if not primera.startswith(TIPOS):
                errores.append(f"{rel} (bloque {i}): primera línea sin tipo de diagrama "
                               f"reconocido → {primera[:60]!r}")

    if errores:
        print("test_mermaid_blocks: FALLA\n  - " + "\n  - ".join(errores))
        sys.exit(1)
    print(f"test_mermaid_blocks: {bloques} diagrama(s) OK")


if __name__ == "__main__":
    main()
