---
id: GOT-007
tipo: gotcha
area: Tests / CI y fixtures
estado: aceptada (validada: usuario, 2026-09-08)
fuente: docs/roadmap/2026-09-04-memory-retrieval/retro.md (T-21, gaps A1/B2 de la revisión de F5-F6) · CI roja tras v1.18.0 (commits `d2f93ef`, `50932b4`)
---

## Una verificación solo vale para el estado en que se hizo: re-verifica después del ÚLTIMO cambio (la suite de codificación, además, solo ve scripts VERSIONADOS)

- **Síntoma:** `python3 -m pytest -q tests/test_console_encoding.py` → `281 passed` en local con un script nuevo en el
  árbol; tras comitearlo, la misma suite da **4 failed** (`assert modos` y `KeyError: 'agent-kits/shared/retro-gate.py'`),
  sin nada de Windows en medio: falla igual en CI (Linux). Lo cazaron las Lentes A y B de la revisión, no la pasada
  local «verde» que figuraba en el ledger.
- **Causa:** `descubrir()` recorre `git ls-files` buscando el snippet de reconfiguración de consola (`GOT-005`), así
  que un script **sin seguimiento** no existe para la suite; y la tabla `MODOS` (cómo invocar cada script y qué exit
  codes admite) es **manual**: descubrir un script que no está en ella es el fallo.
- **Arreglo:** al crear un script con el snippet `GOT-005`, añade su entrada en `MODOS` (`tests/test_console_encoding.py`,
  patrón `"agent-kits/shared/<script>.py": [("<modo>", lambda w: [<args>], (<exits>,), <stdin>)]`) y corre la suite
  **después de `git add`**, nunca antes. Regla práctica: `git add -N <script>` (intent-to-add) basta para que `git
  ls-files` lo vea.

### El patrón general (ampliado el 2026-09-08, tras dejar la CI roja en `master` con la v1.18.0 ya publicada)

El caso de arriba es una instancia de algo más amplio, y por eso esta entrada cambió de titular: **una puerta
verde certifica el estado que existía cuando se ejecutó, no el que quedó después.** Aquel día se encadenaron
**tres** fallos por lo mismo, todos con la puerta correspondiente en verde *antes* del último cambio:

1. **Cifras medidas re-medidas demasiado pronto.** `changelog-sync --medicion` dio `bullet_max = 539` y las 11
   marcas `<!--m:…-->` de 5 ficheros se escribieron con ese valor. Después se recortó el campo `- **Changelog**:`
   de una tarea — **que era justamente ese bullet más largo** — y el techo real bajó a **467**: `tests/test_cifras_medidas.py`
   pasó a fallar 11 veces. La medición era correcta; lo que cambió fue el corpus que medía.
2. **Comparar bytes del árbol de trabajo, no del índice.** `tests/test_doctrina_viaja.py` comparaba byte a byte
   las copias de la doctrina contra sus originales. Pasó en la rama y falló tras un `git checkout` de otra rama:
   con `core.autocrlf=true` git re-materializa unos ficheros y no otros, así que la copia quedó en CRLF y el
   original en LF — «difiere» con los **blobs del índice idénticos** (`git rev-parse :<path>`). Lo que la promesa
   dice es que el CONTENIDO es el mismo; el final de línea lo fija git al materializar.
3. **El arreglo del arreglo.** El `subprocess.run` que se añadió para comparar blobs llevaba `text=True` sin
   `encoding=`, y eso lo vigila el propio repo (`GOT-005`,
   `test_console_encoding.py::test_las_suites_tambien_decodifican_a_sus_hijos_como_utf8`): tercer rojo seguido,
   esta vez cazado por una puerta que no se volvió a correr después de tocar el fichero.

- **Regla:** tras el ÚLTIMO cambio de una tanda, vuelve a correr **la puerta que vigila justo eso** (no una
  selección `-k` cercana): cifras medidas → `tests/test_cifras_medidas.py`; script nuevo o tocado con el snippet
  de consola → `tests/test_console_encoding.py` **entero**; tope del brief → `test_ca08_*`; y antes de publicar,
  el `pytest` **completo con la invocación de `ci.yml`**. En esta máquina (Windows) hay ~36 fallos de plataforma
  que no son defectos: la comprobación útil es «¿aparece alguno FUERA de esas familias?», no el número.
- **Y una consecuencia de proceso:** `release.py` **no** corre `pytest` (sus puertas son linter, evals, copias
  `.MANUAL-COPY` y `changelog-sync --check`), así que un release puede salir con la suite roja. La puerta real es
  CI: comprueba el run del push (`gh run list`) **antes** de dar la publicación por buena, no después.
