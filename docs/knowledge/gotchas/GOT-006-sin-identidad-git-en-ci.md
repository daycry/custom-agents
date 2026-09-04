---
id: GOT-006
tipo: gotcha
area: Tests / CI y fixtures
estado: aceptada (validada: usuario, 2026-09-04)
fuente: docs/roadmap/2026-09-04-ci-sin-identidad-git/tasks.md (CI roja en `4a5bdd8` y `3569f5d`, reportada por el usuario)
---

## Una fixture que crea un repo git hereda tu identidad global y verde en local; en el runner no hay ninguna

- **Síntoma:** la suite pasa en local (`1175 passed`) y la misma orden de la CI falla con exit 1 en
  GitHub Actions. Los 11 rojos son todos de `tests/test_release.py`, con la forma
  `assert (1 == 0)` sobre el `returncode` de `release.py`.
- **Causa:** la fixture creaba el repo temporal y comiteaba con
  `git -c user.name=t -c user.email=t@t commit`, que resuelve la identidad **solo para ese proceso
  git**. Pero el test invoca `release.py` como **subproceso**, y `release.py` hace su propio
  `git commit`: ese git no ve el `-c` del test y busca la identidad donde siempre —
  `--local`, luego `--global`, luego `--system`. En una máquina de desarrollo hay identidad global
  y el commit funciona; en un runner de GitHub Actions **no hay ninguna** y git sale con 128
  (`Please tell me who you are`), así que `release.py` degrada con exit 1 y el test cae.
- **Por qué no se vio antes:** `tests/test_release.py` **no entraba en el `pytest` de la CI** hasta
  que la iniciativa `changelog-brief` (T-07) añadió `tests` a las carpetas del paso de pytest. El
  defecto llevaba ahí desde que se escribió el fichero; cerrar el hueco de la puerta fue lo que lo
  sacó a la luz. No es una regresión de T-07: es una latencia que T-07 destapó.
- **Arreglo:** la identidad va **en el repo**, no en los `git` del test — `git config user.name` y
  `git config user.email` justo después del `git init` de la fixture. Así cualquier proceso git que
  corra en ese repo, incluido el subproceso, la encuentra, y la fixture deja de depender del
  `git config --global` de quien ejecute la suite.
- **Cómo se comprueba:** ejecutar la suite con la configuración global neutralizada, que es lo que
  de verdad hace el runner:

  ```bash
  GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null python3 -m pytest -q
  ```

  Medido: antes `11 failed, 1164 passed`; después `1178 passed`. Es la forma barata de reproducir
  «verde en local, rojo en CI» sin esperar al runner, y vale para cualquier fixture futura que
  monte un repo.
- **Regla que queda:** una fixture que crea un repo git y llama a un script que comitea **fija la
  identidad en el repo**. Lo vigila `test_la_fixture_configura_la_identidad_DENTRO_del_repo`, que
  se pone rojo si alguien quita esas dos líneas (medido: la mutación deja `12 failed`).
- **De paso, el contrato del producto quedó fijado:** sin identidad, `release.py` **escribe los
  ficheros**, avisa por stderr («los ficheros quedaron actualizados, pero git falló») y da el
  comando a mano — nunca un traceback. Antes nadie lo probaba; ahora sí
  (`test_sin_identidad_release_degrada_con_mensaje_y_no_revienta`). Es un escenario real: un git
  recién instalado no tiene identidad.
