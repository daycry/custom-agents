#!/usr/bin/env python3
"""Tamaño de los `skills/*/SKILL.md` + comprobación de «cero pérdida» de una dieta (plan-and-diet T-01).

Regla (docs/CONVENTIONS.md, «skills cortas»): un `SKILL.md` se inyecta COMPLETO en el contexto cada vez
que la skill se invoca, así que lleva el mapa (propósito, disparadores, pasos en 1-3 líneas, guardrails,
qué NO hace, tabla de referencias) y el detalle vive en `skills/<skill>/references/<tema>.md`, que se lee
solo al llegar al paso que lo cita. Umbrales: `scripts/lint_plugin.py` AVISA a partir de
SKILL_WARN_LINES (200); esta suite FALLA a partir de SKILL_MAX_LINES (250, umbral duro).

Uso:
  python3 tests/test_skill_size.py                          # suite (también la recoge pytest)
  python3 tests/test_skill_size.py --diet-check <skill> <git-ref>
      Cero pérdida: toda línea no vacía de > 80 caracteres del `skills/<skill>/SKILL.md` en <git-ref>
      (normalizada por espacios) debe aparecer LITERAL en el SKILL.md actual o en `references/**/*.md`
      (corpus con los saltos de línea plegados a espacios: re-envolver texto no cuenta como pérdida).
      Exit 0 si «0 párrafos perdidos», 1 si falta alguno (los imprime), 2 si el ref/skill no existe.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
SKILL_MAX_LINES = 250      # umbral DURO (esta suite falla)
MIN_CHARS = 80             # «párrafo» que cuenta para la comprobación de cero pérdida

try:
    import pytest
except ImportError:  # el bucle de la CI ejecuta el fichero como script
    pytest = None


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


def skill_md_paths(root=SKILLS):
    return sorted(os.path.join(root, d, "SKILL.md") for d in os.listdir(root)
                  if os.path.isfile(os.path.join(root, d, "SKILL.md")))


def lineas(path):
    with open(path, encoding="utf-8") as f:
        return sum(1 for _ in f)


def corpus_actual(skill, root=SKILLS):
    """SKILL.md actual + references/**/*.md, plegado a una sola línea normalizada."""
    partes = []
    base = os.path.join(root, skill)
    partes.append(open(os.path.join(base, "SKILL.md"), encoding="utf-8").read())
    refs = os.path.join(base, "references")
    if os.path.isdir(refs):
        for dp, _, fns in os.walk(refs):
            for fn in sorted(fns):
                if fn.endswith(".md"):
                    partes.append(open(os.path.join(dp, fn), encoding="utf-8").read())
    return _norm("\n".join(partes))


def parrafos_perdidos(original_text, corpus, min_chars=MIN_CHARS):
    """Líneas no vacías de > min_chars del original cuya forma normalizada no está en el corpus."""
    perdidos = []
    for ln in original_text.splitlines():
        n = _norm(ln)
        if len(n) > min_chars and n not in corpus:
            perdidos.append(n)
    return perdidos


def diet_check(skill, ref, root=SKILLS):
    rel = f"skills/{skill}/SKILL.md"
    try:
        r = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True,
                           text=True, encoding="utf-8", timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"diet-check: no se pudo leer {ref}:{rel} ({e})")
        return 2
    if r.returncode != 0 or not os.path.isfile(os.path.join(root, skill, "SKILL.md")):
        print(f"diet-check: no existe {ref}:{rel} o skills/{skill}/SKILL.md ({r.stderr.strip()})")
        return 2
    perdidos = parrafos_perdidos(r.stdout, corpus_actual(skill, root))
    total = sum(1 for ln in r.stdout.splitlines() if len(_norm(ln)) > MIN_CHARS)
    for p in perdidos:
        print(f"  PERDIDO: {p[:160]}{'…' if len(p) > 160 else ''}")
    print(f"diet-check {skill} vs {ref}: {total} párrafos (> {MIN_CHARS} chars) · "
          f"{len(perdidos)} párrafos perdidos · SKILL.md {lineas(os.path.join(root, skill, 'SKILL.md'))} líneas")
    return 1 if perdidos else 0


# ------------------------------------------------------------------ suite

def _casos():
    return [(os.path.relpath(p, ROOT), lineas(p)) for p in skill_md_paths()]


if pytest is not None:
    @pytest.mark.parametrize("rel,n", _casos())
    def test_skill_md_bajo_el_umbral_duro(rel, n):
        assert n <= SKILL_MAX_LINES, (f"{rel}: {n} líneas > {SKILL_MAX_LINES} — mueve el detalle a "
                                      f"references/<tema>.md (regla de skills cortas, CONVENTIONS)")

    def test_parrafos_perdidos_detecta_y_tolera_reenvolver():
        original = ("Una frase larga que supera los ochenta caracteres para contar como párrafo de la dieta, sí.\n"
                    "corta\n"
                    "Otra frase igualmente larga que también supera los ochenta caracteres y que se perderá.\n")
        corpus = _norm("Una frase larga que supera los ochenta\ncaracteres para contar como párrafo de la "
                       "dieta, sí. Y más texto.")
        perdidos = parrafos_perdidos(original, corpus)
        assert perdidos == [_norm("Otra frase igualmente larga que también supera los ochenta caracteres y que se perderá.")]

    def test_diet_check_ref_inexistente_exit_2(capsys):
        assert diet_check("jira-sync", "0000000000000000000000000000000000000000") == 2

    def test_diet_check_skill_inexistente_exit_2():
        assert diet_check("no-existe-esta-skill", "HEAD") == 2


def main(argv):
    if len(argv) >= 3 and argv[0] == "--diet-check":
        return diet_check(argv[1], argv[2])
    fallos = 0
    casos = _casos()
    for rel, n in casos:
        ok = n <= SKILL_MAX_LINES
        fallos += not ok
        print(f"{'OK  ' if ok else 'FAIL'}: {rel} — {n} líneas (máx. {SKILL_MAX_LINES})")
    print(f"test_skill_size: {len(casos) - fallos}/{len(casos)} OK")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
