<!-- ⚠️ COPIA MANUAL: este árbol (github-templates.MANUAL-COPY/) se copia TAL CUAL a .github/
     (ruta protegida para las herramientas remotas). tests/test_ci_manual_copy.py compara ambos. -->
## What · Qué

<!-- One paragraph: what changes and why. Link the issue / initiative ledger (docs/roadmap/<date>-<slug>/tasks.md) if any. -->

## Evidence · Evidencia

<!-- Paste real output, not descriptions (CONTRIBUTING.md §2). -->

```
python3 scripts/lint_plugin.py            → 
python3 -m pytest -q tests agent-kits/shared skills/adversarial-review/scripts evals → 
python3 evals/check.py                    → 
```

## Checklist

- [ ] `lint_plugin.py` 0 errors, no new warnings
- [ ] Suites green (`tests/`, `agent-kits/shared`, `skills/adversarial-review/scripts`, `evals`)
- [ ] `evals/check.py` exit 0 — new/changed piece has literal positive + paraphrase + neighbouring negative in `evals/cases/`
- [ ] Docs updated in **both** languages (`README.md`/`README.es.md`, `docs/` + `docs/en/`)
- [ ] `CHANGELOG.md` `[Unreleased]` + `CHANGELOG.es.md` `[Sin publicar]` (no version section — `release.py` creates it)
- [ ] `.MANUAL-COPY` sources and their `.github/` copies are byte-identical (`tests/test_ci_manual_copy.py`)
- [ ] New `.sh` files are `100755`
- [ ] Commit messages follow `T-XX:` / `feat:` / `fix:` / `docs:` / `chore:`
