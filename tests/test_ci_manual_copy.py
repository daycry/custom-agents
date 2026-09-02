#!/usr/bin/env python3
"""Tests de la copia manual de los workflows (debt-cleanup T-04a).

`ci.yml.MANUAL-COPY` (y `release.yml.MANUAL-COPY`) viven en la raíz porque `.github/workflows/` es
una ruta protegida para las herramientas remotas: la copia a `.github/workflows/<x>.yml` es MANUAL
y puede quedarse atrás (pasó con el paso pytest por carpetas de adversarial-review). Regla:
  - si `.github/workflows/<x>.yml` existe → debe ser BYTE-IDÉNTICO a `<x>.yml.MANUAL-COPY`;
  - si no existe → skip con el `cp` a ejecutar (no es un error del repo, es una copia pendiente).
`scripts/lint_plugin.py` avisa con el mismo criterio (`lint_manual_copies`).

Ejecutar: python3 tests/test_ci_manual_copy.py   (o pytest -q tests)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIAS = ("ci.yml", "release.yml")

try:
    import pytest
except ImportError:  # el bucle de la CI ejecuta el fichero como script
    pytest = None


def _comparar(nombre):
    """Devuelve (estado, detalle): 'skip' si falta la copia, 'ok' si idénticas, 'diff' si no."""
    fuente = os.path.join(ROOT, f"{nombre}.MANUAL-COPY")
    destino = os.path.join(ROOT, ".github", "workflows", nombre)
    if not os.path.isfile(fuente):
        return "skip", f"sin {nombre}.MANUAL-COPY en la raíz"
    if not os.path.isfile(destino):
        return "skip", f"copia manual pendiente: cp {nombre}.MANUAL-COPY .github/workflows/{nombre}"
    a = open(fuente, "rb").read()
    b = open(destino, "rb").read()
    if a == b:
        return "ok", f".github/workflows/{nombre} idéntico a {nombre}.MANUAL-COPY ({len(a)} bytes)"
    return "diff", (f".github/workflows/{nombre} difiere de {nombre}.MANUAL-COPY — copia manual pendiente: "
                    f"cp {nombre}.MANUAL-COPY .github/workflows/{nombre}")


if pytest is not None:
    @pytest.mark.parametrize("nombre", COPIAS)
    def test_workflow_copiado_es_byte_identico(nombre):
        estado, detalle = _comparar(nombre)
        if estado == "skip":
            pytest.skip(detalle)
        assert estado == "ok", detalle

    def test_lint_plugin_avisa_con_el_mismo_criterio(tmp_path):
        """`lint_manual_copies` del linter: iguales → sin aviso; distintas → aviso con el `cp`."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("lint_plugin", os.path.join(ROOT, "scripts", "lint_plugin.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        (tmp_path / "ci.yml.MANUAL-COPY").write_text("name: CI\n")
        assert mod.lint_manual_copies(str(tmp_path)) == []               # sin copia → nada
        wf = tmp_path / ".github" / "workflows"
        wf.mkdir(parents=True)
        (wf / "ci.yml").write_text("name: CI\n")
        assert mod.lint_manual_copies(str(tmp_path)) == []               # idénticas → nada
        (wf / "ci.yml").write_text("name: CI\n# atrasada\n")
        avisos = mod.lint_manual_copies(str(tmp_path))
        assert len(avisos) == 1 and "cp ci.yml.MANUAL-COPY .github/workflows/ci.yml" in avisos[0]


def main():
    fallos = 0
    for nombre in COPIAS:
        estado, detalle = _comparar(nombre)
        print(f"{'SKIP' if estado == 'skip' else 'OK' if estado == 'ok' else 'FAIL'}: {detalle}")
        fallos += estado == "diff"
    print(f"test_ci_manual_copy: {len(COPIAS) - fallos}/{len(COPIAS)} OK")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
