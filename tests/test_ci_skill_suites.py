#!/usr/bin/env python3
"""Toda carpeta `skills/*/scripts` con `test_*.py` corre en la CI (training-data-services #94).

La CI no recorre `skills/` por glob: su paso `pytest` enumera las carpetas de skills a mano
(`ci.yml.MANUAL-COPY`, copiado tal cual a `.github/workflows/ci.yml`). Una skill nueva con su suite
junto a los scripts se quedaba FUERA sin que nadie lo viera: `training-data-services` y
`knowledge-services` no se ejecutaban en Linux y un rojo POSIX suyo no saltaba nunca en la CI.
Regla: cada `skills/<skill>/scripts` que contenga algun `test_*.py` aparece como argumento de la
linea `python -m pytest` del workflow (en la copia manual y, si existe, en `.github/workflows/`; que
sean identicos lo vigila `tests/test_ci_manual_copy.py`).

Ejecutar: python3 tests/test_ci_skill_suites.py   (o pytest -q tests/test_ci_skill_suites.py)
"""
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS = ("ci.yml.MANUAL-COPY", os.path.join(".github", "workflows", "ci.yml"))


def carpetas_con_suite(root=ROOT):
    """`skills/<skill>/scripts` (con `/`) que contienen al menos un `test_*.py`, ordenadas."""
    out = []
    for d in sorted(glob.glob(os.path.join(root, "skills", "*", "scripts"))):
        if os.path.isdir(d) and glob.glob(os.path.join(d, "test_*.py")):
            out.append(os.path.relpath(d, root).replace(os.sep, "/"))
    return out


def argumentos_pytest(texto):
    """Argumentos de TODAS las lineas `python -m pytest ...` del workflow (tokens separados por
    espacios, sin la orden ni las opciones)."""
    args = set()
    for linea in texto.splitlines():
        cuerpo = linea.strip()
        if cuerpo.startswith("run:"):
            cuerpo = cuerpo[len("run:"):].strip()
        if cuerpo.startswith("python -m pytest "):
            args.update(t.rstrip("/") for t in cuerpo.split()[3:] if not t.startswith("-"))
    return args


def faltan(ruta_workflow, root=ROOT):
    """Carpetas con suite que la linea `pytest` de `ruta_workflow` no ejecuta."""
    with open(ruta_workflow, encoding="utf-8") as f:
        args = argumentos_pytest(f.read())
    return [c for c in carpetas_con_suite(root) if c not in args and "skills" not in args]


def _workflows(root=ROOT):
    return [os.path.join(root, w) for w in WORKFLOWS if os.path.isfile(os.path.join(root, w))]


def test_hay_suites_de_skills_y_workflow_que_mirar():
    assert "skills/training-data-services/scripts" in carpetas_con_suite()
    assert "skills/knowledge-services/scripts" in carpetas_con_suite()
    assert _workflows(), "sin ci.yml.MANUAL-COPY en la raiz"


def test_toda_suite_de_skill_esta_en_la_linea_pytest_de_la_ci():
    for w in _workflows():
        assert faltan(w) == [], f"{os.path.relpath(w, ROOT)}: la CI no ejecuta {faltan(w)}; anadelas a su linea `python -m pytest`"


def test_el_detector_ve_una_carpeta_nueva_que_falta(tmp_path):
    """Guarda del propio detector: una skill nueva con `test_*.py` y un workflow que no la nombra."""
    (tmp_path / "skills" / "nueva" / "scripts").mkdir(parents=True)
    (tmp_path / "skills" / "nueva" / "scripts" / "test_algo.py").write_text("", encoding="utf-8")
    (tmp_path / "skills" / "sin-tests" / "scripts").mkdir(parents=True)
    wf = tmp_path / "ci.yml.MANUAL-COPY"
    wf.write_text("      - name: Tests\n        run: python -m pytest tests skills/otra/scripts evals -q\n", encoding="utf-8")
    assert faltan(str(wf), str(tmp_path)) == ["skills/nueva/scripts"]
    wf.write_text("        run: python -m pytest tests skills/nueva/scripts/ -q\n", encoding="utf-8")
    assert faltan(str(wf), str(tmp_path)) == []


if __name__ == "__main__":
    fallos = []
    for w in _workflows():
        f = faltan(w)
        if f:
            fallos.append(f"{os.path.relpath(w, ROOT)}: la CI no ejecuta {f}")
    for x in fallos:
        print(f"FALLA {x}")
    print("OK: toda suite de skills/*/scripts corre en la CI" if not fallos else f"{len(fallos)} workflow(s) incompletos")
    sys.exit(1 if fallos else 0)
