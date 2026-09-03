#!/usr/bin/env python3
"""Tests de la copia manual de los workflows (debt-cleanup T-04a) y de las plantillas de GitHub
(distribution T-03).

`ci.yml.MANUAL-COPY` (y `release.yml.MANUAL-COPY`, `headless.yml.MANUAL-COPY`) viven en la raíz porque `.github/workflows/` es
una ruta protegida para las herramientas remotas: la copia a `.github/workflows/<x>.yml` es MANUAL
y puede quedarse atrás (pasó con el paso pytest por carpetas de adversarial-review). Regla:
  - si `.github/workflows/<x>.yml` existe → debe ser BYTE-IDÉNTICO a `<x>.yml.MANUAL-COPY`;
  - si no existe → skip con el `cp` a ejecutar (no es un error del repo, es una copia pendiente).
Mismo mecanismo para el ÁRBOL `github-templates.MANUAL-COPY/` (issue forms YAML + PR template) →
`.github/`: cada fichero del árbol se compara con `.github/<misma ruta relativa>`.
`scripts/lint_plugin.py` avisa con el mismo criterio (`lint_manual_copies`); `scripts/release.py`
se niega a publicar con una copia atrasada.

Ejecutar: python3 tests/test_ci_manual_copy.py   (o pytest -q tests)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIAS = ("ci.yml", "release.yml", "headless.yml")   # headless.yml: job opcional (plan-and-diet T-03)
ARBOL = "github-templates.MANUAL-COPY"                 # → .github/ (issue forms + PR template; distribution T-03)

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


def _ficheros_arbol():
    """Rutas relativas dentro de github-templates.MANUAL-COPY/ (orden fijo); [] si no existe."""
    base = os.path.join(ROOT, ARBOL)
    if not os.path.isdir(base):
        return []
    out = []
    for dirpath, _dirs, files in os.walk(base):
        for f in files:
            out.append(os.path.relpath(os.path.join(dirpath, f), base).replace(os.sep, "/"))
    return sorted(out)


def _comparar_arbol(rel):
    fuente = os.path.join(ROOT, ARBOL, rel)
    destino = os.path.join(ROOT, ".github", rel)
    if not os.path.isfile(destino):
        return "skip", f"copia manual pendiente: cp {ARBOL}/{rel} .github/{rel}"
    if open(fuente, "rb").read() == open(destino, "rb").read():
        return "ok", f".github/{rel} idéntico a {ARBOL}/{rel}"
    return "diff", f".github/{rel} difiere de {ARBOL}/{rel} — copia manual pendiente: cp {ARBOL}/{rel} .github/{rel}"


if pytest is not None:
    @pytest.mark.parametrize("rel", _ficheros_arbol())
    def test_plantilla_github_copiada_es_byte_identica(rel):
        estado, detalle = _comparar_arbol(rel)
        if estado == "skip":
            pytest.skip(detalle)
        assert estado == "ok", detalle

    def test_arbol_de_plantillas_tiene_issue_forms_y_pr_template():
        rels = _ficheros_arbol()
        assert "PULL_REQUEST_TEMPLATE.md" in rels
        forms = [r for r in rels if r.startswith("ISSUE_TEMPLATE/") and r.endswith(".yml")]
        assert len(forms) >= 3, forms
        for r in forms:                                   # claves obligatorias de un issue form
            texto = open(os.path.join(ROOT, ARBOL, r), encoding="utf-8").read()
            assert all(f"\n{k}:" in texto for k in ("name", "description", "body")), r

    def test_lint_plugin_avisa_tambien_del_arbol(tmp_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location("lint_plugin", os.path.join(ROOT, "scripts", "lint_plugin.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        (tmp_path / ARBOL / "ISSUE_TEMPLATE").mkdir(parents=True)
        (tmp_path / ARBOL / "ISSUE_TEMPLATE" / "bug.yml").write_text("name: Bug\n")
        assert mod.lint_manual_copies(str(tmp_path)) == []               # sin copia → nada
        (tmp_path / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
        (tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug.yml").write_text("name: Bug\n")
        assert mod.lint_manual_copies(str(tmp_path)) == []               # idénticas → nada
        (tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug.yml").write_text("name: Bug\n# atrasada\n")
        avisos = mod.lint_manual_copies(str(tmp_path))
        assert len(avisos) == 1 and f"cp {ARBOL}/ISSUE_TEMPLATE/bug.yml .github/ISSUE_TEMPLATE/bug.yml" in avisos[0]

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
    fallos, total = 0, 0
    for nombre in COPIAS:
        estado, detalle = _comparar(nombre)
        print(f"{'SKIP' if estado == 'skip' else 'OK' if estado == 'ok' else 'FAIL'}: {detalle}")
        fallos += estado == "diff"
        total += 1
    for rel in _ficheros_arbol():
        estado, detalle = _comparar_arbol(rel)
        print(f"{'SKIP' if estado == 'skip' else 'OK' if estado == 'ok' else 'FAIL'}: {detalle}")
        fallos += estado == "diff"
        total += 1
    print(f"test_ci_manual_copy: {total - fallos}/{total} OK")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
