# Traza del intento 18 (Fase 1)

> Cuerpo movido literal desde [tasks.md](../tasks.md) el 2026-11-20 para dejar el ledger bajo el tope de lectura de 256 KiB; la cabecera sigue en el ledger. Superado por los intentos 19-21 (Fase 1 cerrada).

## Revisión de dos lentes — intento 18: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix17: 4 Important, 13 Minor

Lentes: A+B+C+D sobre `e371259..ae56211` (fix17 y los dos arreglos de test del orquestador tras la suite completa), dos a dos por memoria. Antes de lanzarlas, la suite completa en verde dos veces: Windows (node 579/0, pytest 15.261/0, serie 58/0) y réplica Linux (todos los pasos exit 0). Informes en el scratchpad de la sesión (`lenteA18.md` a `lenteD18.md`, sondas en `la18/`, `lb18/`, `lc18/`, `ld18/`).

**Cerrado del intento 17:**
- Gaps 1, 11, 12, 14, 15 y 16: git que lanza git (`submodule foreach`, `rebase -x`, `bisect run`, alias), `-B`, `update-ref refs/heads/*`, `rebase`/`bisect` con refs, tags, `FETCH_HEAD`, `fork/main` y SHA corto → deny; `checkout HEAD` → allow.
- Gap 17 en lo plausible: `rama_barata` exige un repositorio válido (queda el Minor 8).
- Gaps 3 y 5 con la raíz viva: `taskkill` ya filtra por fecha de creación; la víctima anterior sobrevive en producción (Lente C, 2 pasadas).
- Gaps 6, 13, 21 y 22, y `queryPlan`: Codex, `/doctor` y OpenCode caben en sus topes por construcción (Lente D).
- TDD: el RED `eb8612b` solo trae tests; reejecutado da 445 failed / 92 passed (declarado 447/90). Archivado literal (SHA-256 coincide), horas cuadran, datos personales ausentes.
- Coste del guard: p50 240-280 ms, igual que `e371259`; lineal; la lista blanca lee `.git/HEAD` una vez y no lanza git.
- 89 órdenes normales del implementer: 0 deny.
- Test de statusline reescrito (`b40614d`): sigue probando el requisito.

**Decisiones del usuario (2026-11-17):**
- **LÍMITE conocido: cadenas de programas fuera de la tabla.** El sufijo desenvuelto no se re-ancla otra vez (`uv run env -S 'strace git reset --hard'`, `uv run xargs -a f strace git restore`, shells `ash`/`mksh`/`fish` como programa desconocido). Se aplica la regla de escalado del intento 17: la clase se declara límite, no se persigue forma a forma.
- **D2 se optimiza en el producto**, no se declara límite: 8 hooks de herramienta en ráfaga sobre el anillo lleno deben caber en la espera real de 1 s con carga.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | **Regresión de fix17: rama con nombre de ruta.** Con un directorio `main` (o `master`, `origin/main`) en el cwd, `git checkout main` y `git checkout main --` → allow y git real cambia a `main`; el `--` final se quita antes de analizar y una ref delante de `--` se toma por ruta. Además se mira el cwd del proceso del guard, no el `cwd` del payload. En `e371259` se denegaban | T-06 | corregido en fix18 | A1, B3; `guardrail-check.py:2293-2298`, `:2322` |
| 2 | Important | `git submodule update [--init --recursive] --force` y `git submodule deinit -f` → allow; con git real borran los cambios sin comitear del submódulo | T-06 | corregido en fix18 | B1; `:2398`, `:2175` |
| 3 | Important | **Árbol de procesos de Windows: el barrido de respaldo no actúa en producción.** El PowerShell no `detached` muere con el worker (job de libuv) y ningún llamador pasa `until`; la raíz muerta deja un descendiente huérfano (reproducido, igual que `e371259`). Con la raíz viva, la espera de hasta 1,5 s a ese barrido no aporta (2,39 s frente a 0,65 s de `taskkill` solo). La identidad de la raíz no se comprueba cuando se da por viva (pid reutilizado → ajeno muerto en 4,7 s), y el barrido comprueba la identidad al fotografiar, no al matar. El ledger afirma «confirma hasta 15 s» y que `until` cubre la raíz muerta, cosa que solo ocurre en los tests | T-23 | corregido en fix18 | A3, B5, B6, C4, D18-3; `codex-plugin-state.mjs:29,36,41,46,58,67,79` |
| 4 | Important | **D2: la ráfaga pierde eventos con la espera real.** 2 de 48 con solo la carga ajena, 6 de 32 con 4 bucles; retención p50/p90/máx 122/340/501 ms. Causa medida: abrir para leer un fichero recién reemplazado cuesta 25-55 ms (escaneo síncrono, igual con 1 KB que con 200 KB) y cada escritor lee lo que publicó el anterior; la CPU solo suma 12-15 ms. Validar solo lo nuevo o recortar incrementalmente no lo cierra (8 de 32 perdidos). El test `d2` escalado (`b40614d`) ya no ve la pérdida | T-23 | corregido en fix18 | D18-1, A7, B7; prototipo de cola en `ld18/` (0 de 32, 0,45 s) |
| 5 | Important | Clase de envoltorios encadenados (ver decisión) | T-06 | **límite conocido** (usuario; declarado en `implementer.md` y en fix18) | A2, B2; `:2610-2617` |
| 6 | Minor | Salidas de rama o movimientos de `refs/heads/*` sin cubrir: `rebase -S main other` (el `-S` se come `main`), `bisect good|bad <ref>` tras `start` a secas (el camino que recomienda el propio mensaje de deny), `fetch +x:main` y `fetch . x:main`, `push . HEAD:main`, `push <remoto> HEAD:<rama>`, `worktree add -B main`, `-C <worktree de main> merge`, `filter-branch`, `filter-repo` | T-06 | corregido en fix18 | B4, C2; `:2287`, `:2334`, `:2368` |
| 7 | Minor | Opciones de git que ejecutan una cadena de shell sin cubrir: `difftool -x`/`--extcmd`, `grep -O`/`--open-files-in-pager`, `archive --exec`/`--remote`, `fetch-pack`/`send-pack --upload-pack`/`--receive-pack` | T-06 | corregido en fix18 | C1; `:2168-2175` |
| 8 | Minor | `_es_repositorio` acepta cualquier `commondir` sin mirar adónde apunta: `.git` con `HEAD` de otra rama y `commondir` inválido → git sube al padre y el guard cree estar en la rama de trabajo | T-06 | corregido en fix18 | C3; `:297-303` |
| 9 | Minor | `git gc --prune=now` y `git reflog expire --expire=now --all` → allow; destruyen la recuperación que el guard protege al denegar `branch -D` y `stash drop` | T-06 | corregido en fix18 (decisión del orquestador: deny, ante la duda) | C (fuera de lente) |
| 10 | Minor | Cambios en los tests tras el RED sin trazar (un legítimo retirado, dos formas del corpus, umbral 0,7 → 0,6) | T-06 | corregido en fix18 | A4 |
| 11 | Minor | `Archivos` de T-23 (`tasks.md:681`) sigue con «2 s» y «`TIMEOUT_CAZA` 15 s» | T-23 | corregido en fix18 | A5 |
| 12 | Minor | `docs/agents/implementer.md:70` mantiene la regla `-B` de fix16 junto a la de fix17, que la contradice | T-06 | corregido en fix18 | A6 |
| 13 | Minor | Gap 10 del intento 17: nada comprueba que `uninstall` ejecute `marketplace remove` | T-23 | rebatido con evidencia en fix18 (`uninstall` no ejecuta `marketplace remove`: el registro `daycry` es compartido; ver T-23 fix18) | A8 |
| 14 | Minor | Punto 5: la ruta de `/doctor` solo se midió a mano con +1 s (el diseño pedía +2 s); desviación sin numerar | T-23 | corregido en fix18 | A9 |
| 15 | Minor | `runBounded` añade un arranque de node a cada llamada del instalador a una CLI (1.071 ms frente a 75 ms) | T-23 | corregido en fix18 | D18-2 |
| 16 | Minor | Escáner de la statusline cuadrático en número de tokens por debajo del tope de 8 KB (96/271/1.594 ms con 2/4/8 KB; entrada real 30-40 ms) | T-23 | corregido en fix18 | D18-4, B |
| 17 | Minor | Restos temporales de la Lente A fuera de su carpeta (`$TEMP/sc-err.txt`, `/tmp/la18-td.txt`) | — | lo limpia el orquestador | A |

**Diseño fijado por el orquestador para fix18:** movido literal a [testing/intento18-diseno-fix18.md](intento18-diseno-fix18.md) (2026-11-20, tope de lectura del ledger); aplicado en fix18 y revisado en los intentos 19-21.


