---
id: LES-012
tipo: leccion
area: Proceso / desarrollo del plugin (release y distribución)
estado: aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)
fuente: docs/roadmap/2026-09-03-distribution/tasks.md (decisión del usuario tras el release v1.15.0 del 2026-09-02)
---

## plugin-dev

- **`release.py` debe hacer TODO el release (changelog, checks, modos de fichero), no solo el bump:
  cada paso que se deja «a mano» es una trampa que salta en el peor momento.** El release v1.15.0
  (2026-09-02) tropezó dos veces con pasos que el script no cubría y que la doc sí «recordaba»:
  1. **`[Unreleased]` sin mover.** El script avisaba («no tiene entrada para [1.15.0]») pero no
     bloqueaba ni lo hacía; el aviso se leyó como ruido y el tag salió con las notas en
     `[Unreleased]` en los dos CHANGELOG. La Release de GitHub (que lee `## [X.Y.Z]` del
     `CHANGELOG.md`) cayó en el fallback «Ver CHANGELOG». Y había que hacerlo dos veces (ES + EN),
     con dos cabeceras distintas (`[Unreleased]` / `[Sin publicar]`): el doble de ocasiones de
     olvidarlo.
  2. **`.sh` en modo `100644`.** Los hooks y guardrails son shell; desde Windows
     (`core.fileMode=false`) el bit ejecutable no viaja al índice, así que el tag publicó
     `hooks/*.sh` sin `+x` y el linter solo lo detectaba como aviso post-hoc. No hay forma de verlo
     en el diff normal: solo `git ls-files -s`.

  Ambas tenían el mismo patrón: **una regla escrita en la doc en vez de en el script**. La regla del
  repo («cálculos y veredictos en scripts con tests y exit codes, no en prosa») se aplicaba a los
  agentes y no a la propia herramienta de release. Se cerró en `distribution` T-02: `release.py`
  mueve el contenido de `[Unreleased]`/`[Sin publicar]` a `## [X.Y.Z] - fecha` y añade el enlace en
  los DOS ficheros (y **aborta** si están vacíos: un release sin notas es un error, no un aviso),
  corre `lint_plugin.py` y `evals/check.py`, exige que las copias `.MANUAL-COPY` estén al día,
  corrige los `.sh` en `100644` con `git update-index --chmod=+x` avisando, y solo después hace bump
  + commit + tag; `--dry-run` enseña el plan completo sin tocar nada y `--check` comprueba también
  que la versión actual tiene su sección en ambos CHANGELOG. Todo con tests sobre un repo git
  temporal (`tests/test_release.py`), no con un párrafo en `INSTALL.md`.

  Regla derivada para `plugin-dev`: si un paso del release o de la CI se documenta como «recuerda
  hacer X antes de publicar», X va al script (con test y `--dry-run`) y la doc pasa a describir lo
  que el script hace. Corolario: **un aviso que se puede ignorar sin consecuencias inmediatas se
  ignorará** — si el paso es obligatorio, es `exit ≠ 0`, no `⚠️`. — *Fuente:*
  [`2026-09-03-distribution/tasks.md`](../../roadmap/2026-09-03-distribution/tasks.md) (T-02),
  [`scripts/release.py`](../../../scripts/release.py), [`docs/INSTALL.md`](../../INSTALL.md)
  «Al publicar». `estado: propuesta`.
