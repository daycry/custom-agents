---
tasks: ci-sin-identidad-git
descripcion: >
  CI roja en `master` desde `4a5bdd8` (y en el release `3569f5d`) — reportado por el usuario con el
  enlace al job. Los 11 fallos son todos de `tests/test_release.py`: la fixture creaba el repo
  temporal comiteando con `git -c user.name/-c user.email`, que solo resuelve la identidad para ESE
  proceso git, mientras el test invoca `release.py` como subproceso y ese git busca la identidad en
  `--local`/`--global`/`--system` y no encuentra ninguna en un runner de GitHub Actions. En local
  hay identidad global y la suite salía verde. El defecto llevaba ahí desde que se escribió el
  fichero; lo destapó `changelog-brief` T-07 al añadir `tests` al paso de pytest de la CI.
  La identidad pasa a fijarse EN el repo, con guardarraíl que se pone rojo si se quita, y queda
  fijado además el contrato del producto sin identidad (escribe, avisa por stderr, no revienta).
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-04
actualizado: 2026-09-04
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva verificación
verificacion: obligatoria # cada `### T-XX` lleva `- **Verificación**:`; ledger-lint lo exige
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud)
---

# Checklist de Tareas — ci-sin-identidad-git (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-04 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio.

> **Bug reportado por el usuario (2026-09-04, con enlace al job).** `chore: release v1.17.0`
> (`3569f5d`) y `feat(changelog-sync): …` (`4a5bdd8`) dejan la CI en rojo en el paso «Tests (pytest
> — tests/ + scripts shared + skills con suite propia + evals)», exit 1. Reproducido **sin esperar
> al runner** neutralizando la configuración global de git, que es la condición real del entorno:
> `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null python3 -m pytest …` → `11 failed,
> 1164 passed`, los 11 de `tests/test_release.py`.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — identidad de git en la fixture | 2 | 2 | 100% | 1,0 / 1,0h | 0,06 / 0,06h | 0,02 / 0,02h | 30k / 30k |
| **TOTAL** | **2** | **2** | **100%** | **1,0 / 1,0h** | **0,06 / 0,06h** | **0,02 / 0,02h** | **30k / 30k** |

---

## Fase única — identidad de git en la fixture

**Estado**: completado · **Estimado**: 1,0h · **Real**: 1,0h (estimado) · **Coste est.**: ≈50 € · **Tokens est.**: 30k

### T-01 — La identidad va EN el repo, no en los `git` del test

- **Descripción**: `tests/test_release.py` monta un repo temporal y comitea con `git -c user.name=t -c user.email=t@t`, que resuelve la identidad **solo para ese proceso git**. El test invoca `release.py` como **subproceso** y ese git la busca donde siempre (`--local` → `--global` → `--system`): en una máquina de desarrollo la encuentra en global y el commit funciona; en un runner de GitHub Actions no hay ninguna, git sale con **128** (`Please tell me who you are`) y `release.py` degrada con exit 1, así que los 11 tests que comprueban el commit y el tag caen. La fixture pasa a fijar `user.name` y `user.email` **en el repo** justo tras el `git init`, con lo que cualquier proceso git que corra ahí —incluido el subproceso— la encuentra, y la suite deja de depender del `git config --global` de quien la ejecute.
- **Estado**: completado
- **Tiempo humano**: est. 0,6h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `tests/test_release.py`
- **Changelog**: La suite del repo deja de depender de que quien la ejecute tenga identidad de git configurada, así que la CI vuelve a verde.
- **Verificación** (ejecutada 2026-09-04): reproducción del fallo sobre el commit publicado — `git clone` de `3569f5d` + `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null python3 -m pytest tests agent-kits/shared skills/*/scripts evals -q` → **`11 failed, 1164 passed`**, los 11 de `tests/test_release.py`, con `AssertionError: assert (1 == 0)` sobre el `returncode` · el mismo comando **con** identidad global → `1175 passed` (por eso salía verde en local) · tras el arreglo, `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null python3 -m pytest -q tests/test_release.py` → **`26 passed`** y la suite completa del paso de pytest de la CI → **`1178 passed`** · con identidad global también `26 passed` (el arreglo no depende del entorno en ningún sentido) · barrido de las otras 5 suites que crean repos (`test_guardrail_check`, `test_journal`, `test_scope_check`, `test_review_lens_select`, `test_coverage_gate`): ninguna invoca un script que comitee, y la suite completa sin identidad global lo confirma en verde

**Criterios de aceptación**
- [x] La fixture fija `user.name` y `user.email` en el repo temporal, tras el `git init`
- [x] `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null` sobre la suite completa del paso de la CI → verde
- [x] La suite sigue verde con identidad global (el arreglo no cambia el comportamiento en local)
- [x] Ninguna otra suite del repo tiene la misma dependencia latente (barrido + suite completa sin identidad)

### T-02 — Guardarraíl y contrato del producto

- **Descripción**: dos tests nuevos. `test_la_fixture_configura_la_identidad_DENTRO_del_repo` afirma con `git config --local --get` que la fixture fija las dos claves, y su mensaje explica el porqué (sin identidad local, el `git commit` del subproceso falla en cualquier entorno sin identidad global), así que quitar las dos líneas vuelve a poner la suite roja **nombrando la causa** en vez de dejar 11 `assert (1 == 0)` sin explicación. Y `test_sin_identidad_release_degrada_con_mensaje_y_no_revienta` fija el contrato del PRODUCTO bajo esa misma condición, que antes nadie probaba y es un escenario real (un git recién instalado no tiene identidad): `release.py` **escribe los ficheros**, avisa por **stderr** («los ficheros quedaron actualizados, pero git falló») dando el `git commit` a mano, sale con 1 y **no** imprime traceback. Más el gotcha `GOT-006` con la receta de reproducción, su fila en el índice de `docs/knowledge/`, y la explicación de por qué no se vio antes: `tests/test_release.py` no entraba en el `pytest` de la CI hasta que `changelog-brief` T-07 añadió `tests` a las carpetas del paso — el defecto era anterior, cerrar el hueco de la puerta fue lo que lo destapó.
- **Estado**: completado
- **Tiempo humano**: est. 0,4h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,02h · real 0,02h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `tests/test_release.py`, `docs/knowledge/gotchas/GOT-006-sin-identidad-git-en-ci.md`, `docs/knowledge/README.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-09-04-ci-sin-identidad-git/tasks.md`
- **Changelog**: Si alguien vuelve a escribir una fixture que crea un repo git sin identidad, la suite se pone roja diciendo por qué, y queda probado que `release.py` sin identidad configurada escribe los ficheros y explica qué hacer en vez de reventar.
- **Verificación** (ejecutada 2026-09-04): `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null python3 -m pytest -q tests/test_release.py` → **`26 passed`** (24 previos + 2 nuevos) · **mutación** que demuestra que el guardarraíl discrimina: borrando las dos líneas `git(r, "config", …)` de la fixture en una copia, el mismo comando da **`12 failed, 14 passed`** con `test_la_fixture_configura_la_identidad_DENTRO_del_repo` entre los rojos · el contrato del producto, medido: `rc: 1`, stderr con `ERROR: los ficheros quedaron actualizados, pero git falló (… exit status 128)` y `Haz a mano: git add … && git commit -m 'chore: release v1.2.3' && git tag v1.2.3`, sin `Traceback`, y `plugin.json`/`marketplace.json` ya en `1.2.3` · `ls docs/knowledge/gotchas/` → `GOT-006` es el siguiente ID libre (existían GOT-001..005) y `grep -c "GOT-006" docs/knowledge/README.md` → 1

**Criterios de aceptación**
- [x] Existe un test que afirma que la fixture fija la identidad en el repo, y su mensaje nombra la causa
- [x] La mutación que quita esas dos líneas pone la suite roja (medido: 12 rojos)
- [x] El contrato de `release.py` sin identidad está probado: ficheros escritos, aviso por stderr con el comando a mano, exit 1, sin traceback
- [x] `GOT-006` existe con el formato de los gotchas previos, con su fila en el índice, y explica por qué el defecto era anterior a T-07
