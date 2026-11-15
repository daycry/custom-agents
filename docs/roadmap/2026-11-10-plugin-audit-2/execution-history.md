# Historial de ejecución — plugin-audit-2

## Archivado 2026-11-14 — Revisión de dos lentes — intento 4: Fase 1 (T-06, T-07, T-23) — verificación dirigida del ciclo final: 2 Important, 4 Minor (bytes sin cambios)

SHA-256 del bloque: `13284352f35a7954f4c505a3072e865f7f2a99a402bb511f6d8b4f5f42c576be`.

## Revisión de dos lentes — intento 4: Fase 1 (T-06, T-07, T-23) — verificación dirigida del ciclo final: 2 Important, 4 Minor

Verificación dirigida sobre el ciclo final (`8488b00..84ec8ba`), dos revisores de contexto fresco: B+C sobre el guardarraíl y A+B+D sobre code-health y `redact`. Los gaps 1-4 y 6-9 del intento 3 quedan corregidos según el diseño fijado. Lo que sigue son hallazgos nuevos, reproducidos con git real y con sondas. El usuario exige que no quede nada en rojo ni a medias («no puede quedar nada en rojo»), así que el orquestador abre un último ciclo con diseño estructural, no caso a caso.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Un apóstrofo dentro del cuerpo de un heredoc abre una «comilla» que se traga lo que sigue: `cat <<EOF⏎it's⏎EOF⏎git restore .` y `git commit -F - <<'EOF'⏎don't⏎EOF⏎git checkout .` pasan sin deny, también por el hook | T-06 | corregido (fix4: el tokenizador salta el cuerpo de los heredocs; sin cierre = orden incompleta; el de una shell se analiza) | `agent-kits/shared/guardrail-check.py:293-297,941-945`; repo de prueba: 0 de 2 ficheros modificados |
| 2 | Important | Bajo el suelo de 50 ms del caso pequeño, la puerta de `redact` no compara razones y da verde falso a un cuadrático (`re.compile(r"x*y").search("x"*25000)`: `tc=0.0000 tg=0.4062` → pasa); 15 de las 23 entradas quedan bajo el suelo. Con la máquina saturada sigue habiendo rojo (16,27) | T-23 | corregido (fix4: puerta autocalibrada con referencia lineal, tamaño adaptativo y razón relativa; demostraciones con un cuadrático y un n^1,5 reales) | `tests/test_redact_fix3.py:247,250-253`; sonda `vf2/probe2.py` |
| 3 | Minor | El cambio de base solo se detecta si el segmento empieza por `cd`/`pushd`/`env`: se escapan `A=1 env -C ..`, `command cd ..`, `builtin cd ..`, `{ cd ..; … }`, `if …; then cd ..; fi`, `time cd ..`, `! cd ..`, `cd .. && bash -c 'git restore proj'`, `cd .. && eval '…'` | T-06 | corregido (fix4: el cambio de base se detecta en cualquier token y lo heredan `bash -c`/`sh -c`/`eval`) | `guardrail-check.py:462,957,1027`; monorepo de prueba `vf/m` |
| 4 | Minor | Falso positivo frecuente: `cd "<ruta del propio proyecto>" && git checkout feature/x` o `… && git restore src/a.py` se deniegan como cambio de base | T-06 | corregido (fix4: un `cd` al propio directorio no cuenta como cambio de base) | `guardrail-check.py:914,1027-1028` |
| 5 | Minor | Un `\x0c` desplaza la numeración de Python (`splitlines`) frente a la de git: un TODO recibe la edad de otra línea, con `fichero:línea` errónea y sin aviso | T-07 | corregido (fix4: `leer()` separa solo por LF, como git) | `skills/code-health/scripts/code-health.py:266,676-705`; repo `vf2/ff2` |
| 6 | Minor | La medida con carga ajena en Windows se hizo en reposo | T-23 | corregido (fix4: 10 pasadas en Windows con carga ajena real; razones máximas en la tabla de T-23) | `tasks.md` T-23 |

**Diseño fijado por el orquestador para este último ciclo:**

- Gap 1: el tokenizador reconoce los heredocs (`<<DELIM`, `<<-DELIM`, `<<'DELIM'`, `<<"DELIM"`) y salta su cuerpo hasta la línea del delimitador: el cuerpo es datos, no órdenes. Un heredoc sin delimitador de cierre cuenta como orden incompleta (falla cerrado, como el gap 1 del intento 3).
- Gaps 3 y 4: el cambio de base se detecta en cualquier punto de la orden, no solo al inicio del segmento. Un `cd`/`pushd`/`popd` (también tras `command`, `builtin`, `time`, `!`, asignaciones, `{`, `if/then/do`), un `env -C`/`--chdir` o un `git -C`/`--work-tree`/`--git-dir` en la orden, junto con una restauración del árbol, deniegan. La recursión en `bash -c`, `sh -c` y `eval` hereda ese estado. Única excepción: un `cd` cuyo destino, resuelto, es el propio directorio de trabajo del hook, no cuenta.
- Gap 2: la puerta se autocalibra. En la misma pasada mide una función de referencia lineal sobre la misma entrada y compara `razón_redact / razón_referencia`, porque la carga afecta igual a las dos. El tamaño se adapta: crece hasta que el caso pequeño supere el suelo de CPU (con tope de tamaño y de tiempo declarados); sin suelo alcanzado, el test falla con un motivo claro en vez de aprobar. Lineal ≈ 1, n^1,5 ≈ 2,8 y cuadrático ≈ 8 con entrada ×8; el tope es 2,5. Las demostraciones cubren un cuadrático real que antes quedaba bajo el suelo. 10 pasadas seguidas sin rojo en Linux con 12 bucles de CPU (saturación) y en Windows con carga ajena.
- Gap 5: la numeración de líneas de code-health sigue a git (separa solo por `\n`).

Tras este ciclo, una verificación dirigida más. Si aparecen solo Minor sin pérdida de datos, el orquestador cierra la fase y los anota como deuda.


## Archivado 2026-11-14 — Revisión de dos lentes — intento 7: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix6: 4 Important, 15 Minor (bytes sin cambios)

SHA-256 del bloque: `d43914a5378d3f10b2d552fc27ff99621f17d1cddcabee8b5ee140a02c3d442f`.

## Revisión de dos lentes — intento 7: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix6: 4 Important, 15 Minor

Lentes: A+B+C+D sobre `3512526..be61509`. Motivos de C y de D: `hooks/run-hook.mjs:161` (`exec`) y las rutas del guard.

**Cerrado del intento 6:**
- Fallo cerrado del rol protegido en el lanzador, `native-guardrail` y el puente de OpenCode: el plazo agotado, la entrada de más de 64 KiB con el rol delante, el evaluador caído y el JSON inválido deniegan.
- Gap 5: cambio de base dentro de `eval`, funciones y `. <(…)`.
- Gaps 9, 11, 13, 14 y 16.
- `_aritmetica` lineal.
- La puerta de redact con mediana y umbral 6.
- El modelo de amenaza documentado.

Las interpretaciones i1, i2 e i4 del implementer se aceptan. La i3 (rol sacado del prefijo) no es verificable y pasa al punto 6 del diseño.

La fase **no** cierra: siguen 4 Important con pérdida de datos. Todos vienen de la lista blanca de commits o de envoltorios que se desenvuelven a medias, y bash real los ejecuta con el centinela perdido.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Forma exacta con un heredoc que bash cierra antes. Dentro de `$(…)`, bash 5.2 acepta `D)` como cierre del heredoc; `_CUERPO` solo cierra con `D` sola en la línea y se traga lo que bash ejecuta entre dos commits: `git commit --allow-empty -m "$(cat <<'D'⏎msg⏎D)"⏎git restore .⏎D⏎)"` → allow | T-06 | corregido en fix7 | Lente C: `guardrail-check.py:567-570`, `:311`; Git Bash 5.2.37 y lanzador de punta a punta |
| 2 | Important | Forma exacta detrás de un comentario: `true # ok; git commit -m "$(cat <<'EOF'⏎git restore .⏎EOF⏎)"` → allow. Para bash todo es comentario, no abre el heredoc y ejecuta el cuerpo. Lo mismo con `-F -` y con `&&` | T-06 | corregido en fix7 | Lente B: `guardrail-check.py:601-607` |
| 3 | Important | `env -S` solo se desenvuelve en `_literal_invocation`; `_posicion_programa` no busca dentro el cambio de base. Desde `main/wt`, `env -S 'git -C .. restore a.txt'` → allow, y se pierde el cambio sin comitear | T-06 | corregido en fix7 | Lente A: `guardrail-check.py:689` frente a `:725-735`, `:898`, `:1436`; sonda `la7/envs` |
| 4 | Important | `xargs` con las rutas por la entrada estándar: `git diff --name-only \| xargs git checkout --` → allow. Igual `xargs git restore --`, `xargs -r git checkout HEAD --` y `xargs -I{} git checkout -- {}`. Es el mismo caso que `--pathspec-from-file`, que sí se deniega | T-06 | corregido en fix7 | Lente B: `guardrail-check.py:649,697-720,1369-1396` |
| 5 | Minor | Regresión: `$$'` se toma como comilla ANSI-C. `echo $$'\'; git reset --hard #'` → allow (deny en 3512526) | T-06 | corregido en fix7 | Lente C: `guardrail-check.py:447,418` |
| 6 | Minor | Regresión: `&` como redirección sin mirar si `>`/`<` está escapado. `echo \>& git reset --hard` → allow (deny en 3512526) | T-06 | corregido en fix7 | Lente C: `guardrail-check.py:511` |
| 7 | Minor | Envoltorios con el valor de la opción separado: `timeout --kill-after 5 30 git restore .`, `--signal KILL`, `nice --adjustment 5`, `stdbuf -o 0`/`-o L`, `sudo --user root`; `flock` no está en `_ENVOLTORIOS` → allow | T-06 | corregido en fix7 | Lentes B y C: `guardrail-check.py:651-652,666-691` |
| 8 | Minor | Rama protegida: `git checkout @{-2}`, `git checkout origin/HEAD` y `git switch --detach origin/HEAD` → allow. Sin pérdida de datos | T-06 | corregido en fix7 | Lente C: `guardrail-check.py:925` |
| 9 | Minor | `bash -c -- 'git reset --hard'` → allow: `--` se toma por la orden. Ya ocurría en 3512526 | T-06 | corregido en fix7 | Lente C (fuera de diff): `guardrail-check.py:1038` |
| 10 | Minor | Fallo cerrado incompleto en tres puntos, ninguno reproducido con un runtime real: (a) con más de 64 KiB y la clave del rol detrás de `tool_input`, el implementer sigue sin deny (probado con `{tool_name, tool_input, agent_type}`); el orden real de Claude Code y Codex no consta; (b) un `ValueError`/`TypeError`/`KeyError` lanzado dentro de `evaluator.decide` sale como `input-unrecognized` y sigue; (c) en OpenCode, `project()` nulo hace `return` sin guard en vez de lanzar | T-06 | corregido en fix7 | Lentes A, B y C: `native-guardrail.py:60-63,317`; `opencode-plugin.js:281` |
| 11 | Minor | `_quitar_mensajes_de_commit` es superlineal: `finditer` con backtracking de `_OPCIONES` y `_cerrado_sin_heredoc(previo)` por coincidencia. 15 KB de formas → 6-14 s y deny falso por plazo. Los comentarios «el guard nunca agota el plazo» son falsos | T-06 | corregido en fix7 | Lentes B y D: `guardrail-check.py:565-608,975,1420` |
| 12 | Minor | Falso deny: `source .venv/bin/activate && git restore src/a.py`. El mensaje de deny tampoco nombra `source` | T-06 | corregido en fix7 | Lente B: `guardrail-check.py:917-918,1388-1390` |
| 13 | Minor | Documentación contradictoria. El mermaid y la cita de FLOWS §6c ES/EN e INTEROP ES/EN siguen diciendo «sin Python / timeout → permisos normales». En `implementer.md:70` `git checkout -` sale como denegado y como permitido. El texto de deny de Write con más de 64 KiB dice «write files with the edit tool». La docstring de la demo de redact dice «razón ≈ 8» | T-06, T-23 | corregido en fix7 | Lentes A y B: `docs/FLOWS.md:596-603`, `docs/en/FLOWS.md:597,603`, `docs/INTEROP.md:492-494`, `docs/en/INTEROP.md:484-486`, `native-guardrail.py:55-56` |
| 14 | Minor | Assert relajado sin anotar en el ledger: `razon and "descarta" in razon` → `razon` | T-06 | corregido en fix7 | Lente A: `test_guardrail_check.py:962` |
| 15 | Minor | En Windows, la demostración con reloj real del cuadrático nunca pasa por la mediana: la resuelve siempre la sonda ×4 con `inf` sacado de una sola muestra. Ese `inf` no tiene segunda ronda: un lineal sale rojo si una sola medida ×4 se infla unas 3,5 veces | T-23 | corregido en fix7 | Lente B: `test_redact_fix3.py:334-339,418-424`; 5/5 `inf` |
| 16 | Minor | Coste evitable en el paso serie. Las dos pruebas de plazo esperan con `sleep` (≥ 4,5 s cada una) y la cota `dt < 12` aguanta la carga. Los 3 hostiles por el lanzador no tienen aserción de tiempo. Juntos suman ≈13-15 s de los +40 s | T-23 | corregido en fix7 | Lente D: `test_native_guard_failclosed.py:132-141`; `test_guardrail_differential.py:601-621` |

Fuera de gap: `test_ca08` no lo toca la iniciativa (Lente D: sin commits en `57fb054..be61509`).

**Diseño fijado por el orquestador para fix7.** Dentro del modelo de amenaza que decidió el usuario; ante la duda, deny.

1. **Lista blanca a prueba de bash** (gaps 1, 2 y 11).
   - (a) Una forma deja de estar en la lista blanca si alguna línea del cuerpo, quitando tabuladores al principio, EMPIEZA por el delimitador sin ser la línea de cierre exacta. Así entran `D)`, `D;` y `D x`.
   - (b) La forma solo vale si empieza al principio de una sentencia según el tokenizador real, es decir, fuera de comentario, comilla o heredoc. En el caso conservador: no vale si la última línea de `previo` tiene un `#` sin comillas.
   - (c) Coste lineal. Las posiciones de `git commit` las da una sola pasada del tokenizador con el estado de cierre acumulado, y las opciones se acotan a la línea, sin `finditer` con backtracking.
   - Test: los hostiles de las lentes B y D (16 KB) en menos de 0,3 s y sin deny por plazo. Se corrigen los comentarios «nunca agota el plazo».
2. **Envoltorios con una sola implementación** (gaps 3, 7 y 9). `_literal_invocation` y `_posicion_programa` llaman a la MISMA función.
   - El valor de `env -S` se analiza entero, incluido el cambio de base.
   - Se consumen las opciones largas con el valor separado (`timeout --kill-after/--signal`, `nice --adjustment/-n`, `sudo -u/--user/-g/…`, `stdbuf -o/-i/-e`). Se añade `flock [opts] <fichero> <orden>`.
   - Una opción DESCONOCIDA de un envoltorio, en una orden con `git`, se deniega.
   - En `bash -c --`, se salta el `--`.
3. **`xargs` y rutas desconocidas** (gap 4): `xargs … git <subcomando destructivo de ficheros>` (restore, checkout con o sin `--`, reset, clean, rm, checkout-index…) se deniega siempre, incluido con `-I{}`. Se trata igual que `--pathspec-from-file`.
4. **Regresiones del tokenizador** (gaps 5 y 6): `$$` es el PID y no abre ANSI-C, y un `>`/`<` escapado no forma redirección con `&`.
5. **Rama protegida** (gap 8): `checkout`/`switch` a `@{-N}`, a una ref remota o con `--detach` se deniega.
6. **Fallo cerrado completo** (gap 10).
   - (a) Si la entrada pasa de 64 KiB, la clave del rol (`agent_type`/`agent`) se busca en TODO el flujo con un escáner lineal acotado (p. ej. 16 MiB), sin parsear el JSON entero. Test con la clave al final → deny para el implementer y continue para qa.
   - (b) Solo la validación del esquema ANTES de evaluar produce `input-unrecognized`. Cualquier excepción dentro de `evaluator.decide` es `evaluator-unavailable`, y por tanto deny para el rol protegido.
   - (c) En OpenCode, si `project()` es nulo con un rol protegido, el adaptador lanza (deny), con test del adaptador.
   - Se regenera interop.
7. **`source`/`.`** (gap 12). Con un fichero normal no cuenta como cambio de base: es un límite conocido y va al modelo de amenaza. Con `/dev/stdin`, `<(…)` o un heredoc se sigue analizando. El mensaje de deny nombra la causa real.
8. **Documentación y ledger** (gaps 13 y 14):
   - FLOWS §6c (cita y mermaid) e INTEROP, en ES y EN, dicen fallo cerrado para el rol protegido.
   - Se corrigen `implementer.md:70`, el texto de deny de Write y la docstring de la demo.
   - El assert relajado queda anotado en el ledger.
9. **Puerta de redact** (gap 15).
   - La demostración con reloj real usa un tamaño con el que el cuadrático da muestras medibles (no `inf`) en Linux y en Windows, y la que se comprueba es la mediana.
   - Un `inf` de la sonda ×4 necesita confirmación (una segunda muestra) antes del rojo.
   - Otra vez 10 pasadas en Linux y 10 en Windows con carga.
10. **Paso serie** (gap 16): las pruebas de plazo con `sleep` y los hostiles por el lanzador pasan al paso paralelo, salvo que una aserción de tiempo lo impida (entonces se justifica en el ledger).
11. **Corpus:** todas las sondas del intento 7 (scratchpad `la7/`, `lb7/`, `lc7/`, `ld7/`) entran en el corpus diferencial como BAD, LEGIT o LIMITE.

Tras este ciclo: réplica Linux completa sin rojo, medida emparejada de T-23 (la hace el orquestador) y verificación dirigida de las cuatro lentes. Si solo quedan Minor sin pérdida de datos, la fase cierra.


## Archivado 2026-11-14 — Revisión de dos lentes — intento 8: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix7: 3 Important, 12 Minor (bytes sin cambios)

SHA-256 del bloque: `8f99caa7cbfcd4b2ea9c4de898ddab83ea09a2499e2d7a7fb05aa5fcb6a953b2`.

## Revisión de dos lentes — intento 8: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix7: 3 Important, 12 Minor

Lentes: A+B+C+D sobre `00bdf50..5d99de6`. La memoria libre era menor de 1 GB, así que las lentes corrieron dos a dos y con un proceso cada vez.

**Cerrado del intento 7:**
- Gaps 1, 2, 5, 6, 8, 9, 11, 12, 13, 14 y 16.
- Gap 10 (a) y (b): el rol se busca en todo el flujo, sin falsificación por una clave dentro de una cadena, y cualquier excepción del evaluador es `evaluator-unavailable`.
- Gap 3 en sus formas sin comillas.
- Gap 4 en unas 35 variantes directas.
- Lista blanca lineal: los hostiles del intento 7 tardan menos de 0,08 s.
- Escáner del rol lineal: 16 MiB en 145 ms y 90 MB.

**Rebates e interpretaciones:**
- El rebate i1 del implementer (punto 6(c) de OpenCode) se acepta. `native-guard-adapter.test.mjs:66-68` fija que una sesión de otra ubicación no se guarda, y `locate()` cumple las dos condiciones.
- La i4 (comentario detectado con el tokenizador real) se acepta.
- Falso deny aceptado por el diseño 1(a): un mensaje de commit con una línea que empieza por el delimitador.

**Causa del rojo no reproducido de `test_journal.py`** (Lente B, reproducida de forma determinista):
- La E/S acotada del journal tiene un plazo de pared fijo de 5 s (`journal-io.py:69`, `local-state.py:81,97`).
- Si el fsync se atasca más, salta `journal_io_deadline`, `outbox.py:331-333` lo convierte en `OSError` y `capture_end` lo traga.
- Resultado: 2 envelopes en vez de 3 (`test_journal.py:2429`).
- No viene de esta iniciativa.
- En producción, un atasco de E/S de más de 5 s en SessionEnd pierde la captura sin aviso visible. Es un hallazgo de producto y va al gap 15.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | `xargs -I{} sh -c 'git restore {}'` → allow. Al recursar en `sh -c`/`bash -c` no se hereda que «las rutas llegan por stdin», así que `{}`/`%` pasan como ruta literal. Igual con `xargs -I % bash -c 'git checkout -- %'` y `xargs -I{} sh -c 'echo {}; git restore -- {}'`. Es la forma habitual de un agente honesto | T-06 | corregido en fix8 | Lentes B y C: `guardrail-check.py:1591-1614`, `_subcomandos_shell:1169`; Git Bash, centinela perdido |
| 2 | Important | `--replace`, `--eof` y `--max-lines` de GNU xargs llevan valor OPCIONAL, solo pegado con `=`. La tabla los trata como opciones con valor separado y se traga `git`. `xargs --replace git restore {}` → allow. Contradice `implementer.md:92` («se deniega siempre») | T-06 | corregido en fix8 | Lentes B y C: `guardrail-check.py:733-734,772`; xargs 4.10.0, centinela perdido |
| 3 | Important | Assert de tiempo relajado para sacar el test del paso serie: `dt < 12` → `dt < 100`, con el hijo durmiendo 120 s. El hook tiene `timeout: 10` en `hooks.json`. Si una regresión hace que el lanzador espere unos 60 s, el runtime lo corta sin deny y el test sigue verde. Contradice el punto 10 del diseño (si la aserción lo impide, se queda en serie) | T-06, T-23 | corregido en fix8 | Lente A: `tests/test_native_guard_failclosed.py:139-142`, `hooks/hooks.json:10`, `tasks.md:301` |
| 4 | Minor | `env -S` trocea el valor con `str.split()`, pero env quita comillas y procesa `\`. `env -S 'git reset "--hard"'`, `env -S 'git "reset" --hard'`, `env -S 'git restore "."'` y `env -S 'env -S "git -C .. restore a.txt"'` → allow, con pérdida de datos. Además el troceo repetido es cuadrático: 11,7 KB de `-S` → 1,06 s | T-06 | corregido en fix8 | Lentes B y D: `guardrail-check.py:846,878` |
| 5 | Minor | Fallo abierto por encima de 16 MiB: el escáner deja de leer en `GUARD_SCAN_MAX` y, si la clave del rol va detrás, el resultado es continue | T-06 | corregido en fix8 | Lentes C y D: `run-hook.mjs:105,120-122,319`, `native-guardrail.py:64,362`; 17 MiB → continue |
| 6 | Minor | OpenCode compara ubicaciones como texto: solo pasa a minúsculas en win32 y exige `workspaceID` estricto. El mismo proyecto con otra forma de ruta (enlace simbólico, nombre 8.3, mayúsculas en macOS) sale como ajeno y se salta el guard. No verificable sin runtime | T-06 | corregido en fix8 | Lente C: `opencode-plugin.js:61-63,224,288` y su espejo |
| 7 | Minor | `docs/INTEROP.md:364` y `docs/en/INTEROP.md:359` siguen diciendo que la entrada de más de 64 KiB continúa | T-06 | corregido en fix8 | Lente A |
| 8 | Minor | Punto 11 incompleto. (a) Faltan sondas en el corpus: `lc7` b51-b79, k84-k103, w23, w25-w28, w32, w35-w39, los 24 de `lb7/legit2.py` y los falsos deny previos `<<"EOF"`, `<<EOF` y `<<'EOF-1'`. (b) `trap 'cd ../main' DEBUG; git restore src` → allow y no está en LIMITE7. (c) `nice {D}` en `SIN_PARIDAD_7` contradice BAD6 (`test_guardrail_differential.py:220`) | T-06 | corregido en fix8 | Lente A: `test_guardrail_differential7.py:19-103` |
| 9 | Minor | `Archivos` no recoge `agent-kits/shared/test_ledger_view.py` ni `tests/test_graphiti_security.py`, y T-23 dice «sin ficheros nuevos» | T-06, T-23 | corregido en fix8 | Lente A: `tasks.md:935` |
| 10 | Minor | La demo de redact con reloj real tiene poco margen: `TOPE_CPU_DEMO` = 30 s frente a unos 12 s por muestra en Windows. La rama `tg > tope → inf` no se confirma, y la confirmación ×4 se toma sin pausa entre rondas | T-23 | corregido en fix8 | Lente B: `test_redact_fix3.py:350-354,366-367,443` |
| 11 | Minor | La demo de redact cuesta 53 s en Windows sin carga y unos 88 s con carga, en el paso serie. Es evitable: la razón esperada es ≈16 frente a un umbral de 6, medida en CPU | T-23 | corregido en fix8 | Lente D: `test_redact_fix3.py:263,442-443` |
| 12 | Minor | Coste evitable en el corpus: `_estado(copia)` lanza 2 procesos git en cada caso, aunque la copia es idéntica a la plantilla. `_tiene(programa)` no guarda el resultado. Son 40-80 s de CPU en Windows | T-06 | corregido en fix8 | Lente D: `test_guardrail_differential.py:355`, `test_guardrail_differential7.py:106` |
| 13 | Minor | Test frágil: `test_journal.py::test_replay_con_recover_max_n…` depende del plazo de pared de 5 s de la E/S del journal. Con un fsync lento falla `2 == 3` | T-23 | corregido en fix8 | Lente B: reproducción `lb8/jexp.py` |
| 14 | Minor | Rama: `git checkout FETCH_HEAD` → allow. Es la misma clase que `HEAD~1`, que ya se decidió permitir (ledger, línea 230): sin cambio, anotado | T-06 | descartado (rebatido) | Lente C |
| 15 | Minor | Hallazgo de producto fuera de alcance: un atasco de E/S de más de 5 s en SessionEnd pierde la captura del journal con solo un aviso en stderr | — | deuda aceptada → tarea nueva en fase 6 | Lente B: `journal-capture.py:316-321` |

**Diseño fijado por el orquestador para fix8:**

1. **`xargs` heredado** (gaps 1 y 2). El análisis guarda un indicador «rutas por stdin» que se hereda al recursar en `sh -c`/`bash -c`/`env -S`/`eval` lanzados por `xargs`. Con el indicador activo, cualquier subcomando destructivo de ficheros se deniega, con `{}`/`%` o sin ellos.
   - En la tabla de xargs, `--replace`, `--eof` y `--max-lines` solo consumen valor con `=`.
   - Una opción larga desconocida de xargs en una orden con `git` se deniega.
2. **Prueba de plazo de punta a punta** (gap 3).
   - La aserción vuelve a quedar por debajo del timeout del hook: `dt <` (timeout de `hooks/hooks.json` − 1 s), leído del propio `hooks.json`. Así la prueba falla si el lanzador agota el plazo del runtime.
   - Si la cota no aguanta en el paso paralelo, la prueba vuelve a serie y se justifica en el ledger. No se relaja.
3. **`env -S` con `shlex`** (gap 4). El valor se trocea como lo hace env, con `shlex.split(posix=True)` y sus escapes. Si el troceo falla, se deniega cuando la orden contiene git.
   - Coste lineal: un solo troceo por `-S` y nada de rebanar la lista entera.
   - Test con las 4 formas del gap y con el hostil de 11,7 KB por debajo de 0,2 s.
4. **Escáner sin tope** (gap 5). La búsqueda del rol recorre TODO el flujo con memoria constante: una ventana deslizante sobre los fragmentos, sin retener el cuerpo pasados los 64 KiB que necesita el hijo. Así no queda corte en 16 MiB. Test con 17 MiB y la clave al final → deny para el implementer y continue para qa.
5. **OpenCode** (gap 6). Las dos ubicaciones se comparan tras `realpath` (`fs.realpathSync.native`), con minúsculas en win32 y darwin. Un `workspaceID` presente solo en un lado no hace la sesión ajena. Test del adaptador. Interop regenerado.
6. **Corpus y documentación** (gaps 7, 8 y 9).
   - Corregir INTEROP ES/EN.
   - Meter en el corpus todas las sondas listadas en el gap 8(a) como LEGIT, BAD, LIMITE o FALSO_DENY_ACEPTADO.
   - Llevar `trap … DEBUG` a LIMITE7 y añadirlo al modelo de amenaza.
   - Resolver la incoherencia de `nice`.
   - Completar `Archivos`.
7. **Puerta de redact** (gaps 10 y 11).
   - La demo con reloj real usa un tamaño menor y menos muestras: objetivo menor de 15 s en Windows sin carga.
   - Un `inf` por tope también se confirma con una segunda muestra tras `PAUSA_RONDAS`.
   - El margen entre la muestra típica y el tope es al menos 5×.
   - Otra vez 10 pasadas en Linux y 10 en Windows con carga.
8. **Coste del corpus** (gap 12): `_estado` de la plantilla se calcula una vez por módulo y `_tiene` se guarda en caché.
9. **Journal** (gap 13). El plazo de 5 s de `journal-io` se puede inyectar en tests, igual que la escala de plazos de `agent-activity-store`: solo actúa bajo `PYTEST_CURRENT_TEST`. El test del replay lo usa.
   - Test de regresión que fija el comportamiento con un fsync retrasado más allá del plazo por defecto. Usa el plazo inyectado y no depende del reloj de la máquina.
   - La producción NO cambia en este ciclo.
10. **Deuda** (gap 15): se añade al ledger una tarea nueva en la fase 6, «captura de SessionEnd que no se pierde sin aviso ante un atasco de E/S», con su Verificación.

Tras este ciclo: réplica Linux completa sin rojo, medida emparejada de T-23 con el equipo libre (la hace el orquestador) y verificación dirigida de las cuatro lentes. Si solo quedan Minor sin pérdida de datos, la fase cierra.


## Archivado 2026-11-14 — Revisión de dos lentes — intento 9: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix8: 2 Important, 6 Minor (bytes sin cambios)

SHA-256 del bloque: `1b1b64ce4682195575ef02b8c5d3959a52d6ef75f1414f85145000fd4b88c9d7`.

## Revisión de dos lentes — intento 9: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix8: 2 Important, 6 Minor

Lentes: A+B+C+D sobre `c3c7989..1ba8714`, dos a dos por memoria (≈ 2 GB libres).

**Cerrado del intento 8:**
- Gaps 1-13 y 15. Las sondas de xargs heredado (unas 60 por lente) dan deny.
- La prueba de plazo lee la cota de `hooks.json`: 6,0-6,7 s frente a 9 s.
- El escáner del rol no tiene tope y su memoria es constante: 256 MiB en 1,9 s y 62 MB.
- OpenCode compara por `realpath` y no hay fallo abierto: `canonical` vuelve a `resolve()` si el `realpath` lanza.
- T-39 está en la fase 6.
- Cifras del ledger y orden RED → código: correctos.
- Puertas en verde, verificadas por el orquestador.

**Desviaciones aceptadas:**
- Punto 3, `env -S` acotado a 4 troceos y 2.048 caracteres. Se acepta para git, porque deniega; el caso sin git es el gap 4.
- Punto 7, demo de redact ×4. Se acepta en coste (3,7-11 s), con el gap 6.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | `xargs -a <(git diff --name-only) git restore` → allow. `_segmentos` corta en `<(`/`)` y el resto sale como un segmento nuevo sin el `xargs` delante. Igual con `--arg-file=<(…)`, `-a<(…)` y `-a <(…) -I{} sh -c '…'`. Bash real: centinela perdido. No es regresión, porque `c3c7989` da lo mismo, pero contradice `implementer.md:92` | T-06 | corregido (fix9) | Lente B: `guardrail-check.py:1614-1631`; `lb9/r1` |
| 2 | Important | Test intermitente: `test_journal.py::test_replay_con_recover_max_limita…` asserta `recuperadas == 3` y `dur_ms < 5000` con reloj de pared, sin la escala inyectable del fix8. Lo ejecuté 7 veces seguidas en serie y falló 5 (`2 == 3`). Contradice el criterio 2 de T-23 y la regla «nada en rojo, tampoco flaky» | T-23 | corregido (fix9) | Lentes A y B: `agent-kits/shared/test_journal.py:2267-2277` |
| 3 | Minor | Regresión de paridad: en `native-guardrail.py:81` la alternativa de escape pasó de `\\.` a `\.`. Con más de 64 KiB y la identidad escapada (`custom-agents:implementer`), el adaptador Python da continue. Sin efecto de punta a punta: `run-hook.mjs:116` conserva `\\.` y deniega antes. `test_native_guard_scan8.py` no prueba escapes | T-06 | corregido (fix9) | Lentes A, B, C y D: `lc9/p1.py` |
| 4 | Minor | `env -S` fuera del tope (5.º troceo o más de 2.048 caracteres): `_trocea_s` devuelve `None` y solo se deniega si aparece `git` literal. (a) Órdenes externas que se denegaban en `c3c7989` pasan a allow: `env -S 'kubectl delete ns prod A=<2.100 x>'`, `docker system prune`, `npm publish`. (b) `g""it` fuera del tope → allow, con pérdida de datos. (c) shlex no aplica los escapes propios de env: `\_` es un espacio y `\c` corta; `env -S 'git restore\_.'` y `env -S 'git restore .\c'` → allow, con pérdida de datos. Son formas deliberadas | T-06 | corregido (fix9) | Lentes A, B y C: `guardrail-check.py:818-828,866-869,901-904`; GNU env 8.32 |
| 5 | Minor | Las dos pruebas del panel pasaron a serie en vez de inyectar `BODY_TIMEOUT`. Es una línea (`monkeypatch.setattr(service, 'BODY_TIMEOUT', …)`, como en `test_panel_review_server.py:227`). Doctrina de fix5, punto 7: los plazos se inyectan | T-23 | corregido (fix9) | Lentes A y B: `tests/test_panel_review_panel_server.py:263,459` |
| 6 | Minor | La demo de redact a ×4 asserta `relativa > 2` en vez de la decisión real de la puerta (`not _es_lineal`, umbral 6). En una de 3 medidas un cuadrático dio una razón de 3,84 y `_es_lineal` = True: la puerta lo dejaría pasar y la demo sale verde. El margen de 5× se comprueba con constantes | T-23 | corregido (fix9) | Lentes A y B: `tests/test_redact_fix3.py:390,463,677`; `lb9/redemo.py` |
| 7 | Minor | OpenCode: `canonical()` llama a `realpathSync.native` síncrono y sin caché en los dos lados de cada comparación, incluido `location.directory`, que es constante. En SMB o VPN bloquea el bucle de eventos en cada herramienta y cada evento | T-06 | corregido (fix9) | Lente D: `hooks/opencode-plugin.js:66-73,233,437` y su espejo; 265 µs frente a 6,9 µs por llamada |
| 8 | Minor | Límite: un payload hostil de claves densas de 128 MiB o más pasa del plazo de lectura de 4,5 s antes de llegar al rol, y sale continue. No es realista. Antes del fix8 ocurría ya por encima de 16 MiB | T-06 | corregido (fix9): límite documentado en el modelo de amenaza | Lente D: `ld9/probe2.mjs` |

**Diseño fijado por el orquestador para fix9:**

1. **Sustitución de proceso con xargs** (gap 1). Un `<(…)`/`>(…)`/`$(…)` dentro de una palabra NO parte el segmento de la orden que lo contiene. El interior se analiza aparte, como segmento propio, y la orden exterior se analiza entera, con sus argumentos. Con `xargs`, cualquier `-a`/`--arg-file` (con o sin `=`, pegado o separado, con sustitución o fichero) cuenta como «rutas por stdin». Todas las formas del gap van al corpus diferencial como BAD, con bash real.
2. **Journal** (gap 2). El test del replay no depende del reloj de pared. Usa la escala inyectada del fix8 o el reloj simulado, y la aserción de duración desaparece o pasa a usar el reloj inyectado. Cualquier otra aserción de pared de menos de unos segundos en `test_journal.py` que pueda fallar bajo carga recibe el mismo trato; el inventario de esas aserciones va en el informe. Verificación: `-k replay` 20 veces seguidas con carga, 0 rojos.
3. **Escáner Python** (gap 3). Vuelve a `\\.`. Un test de paridad pasa el mismo corpus (identidades escapadas, clave partida, blancos) por el escáner de `native-guardrail.py` y por el de `run-hook.mjs`, y exige el mismo rol.
4. **`env -S`** (gap 4). Un valor que no se puede trocear (fuera del tope o con comilla abierta) se deniega SIEMPRE para el rol protegido: el guard solo actúa sobre ese rol. Antes del troceo se aplican los escapes de GNU env (`\_` → espacio, `\c` → corte, `\t`, `\n`, `\v`, `\f`, `\r`, `\\`, `\'`, `\"`, `\#`, `\$`). Un escape desconocido se deniega si la orden contiene git. Tests con las formas del gap y con el ejemplo sin git.
5. **Panel** (gap 5). Las dos pruebas inyectan `BODY_TIMEOUT` y vuelven al paso paralelo.
6. **Demo de redact** (gap 6). La aserción vuelve a ser la decisión real de la puerta (`not _es_lineal`, con el umbral 6). El tamaño y el número de muestras se eligen para que la razón medida de un cuadrático supere 6 con margen (≥ 1,5× sobre el umbral en el peor de 10 ensayos), y el coste se mantiene por debajo de 15 s en Windows. Si no hay combinación posible, se vuelve a ×8 con menos muestras. El margen se demuestra con medidas, no con constantes. Otra vez 10+10 pasadas.
7. **OpenCode** (gap 7). `location.directory` se canoniza una vez, al cargar. Las demás rutas se canonizan con una caché por cadena (acotada), y el fallo sigue volviendo a `resolve()`. Test del adaptador e interop regenerado.
8. **Límite** (gap 8). Se añade al modelo de amenaza de `implementer.md` y de INTEROP ES/EN.

Tras este ciclo: réplica Linux completa sin rojo, medida emparejada de T-23 con el equipo libre (la hace el orquestador) y verificación dirigida de las cuatro lentes. Si solo quedan Minor sin pérdida de datos, la fase cierra.


## Archivado 2026-11-15 — Revisión de dos lentes — intento 6: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix5: 7 Important, 9 Minor; cambio de modelo decidido por el usuario (bytes sin cambios)

SHA-256 del bloque: `6715d672c9310ff6f6f2982c80fde254dfc9f379b7a5f14ad09e38735c8d7c5c`.

## Revisión de dos lentes — intento 6: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix5: 7 Important, 9 Minor; cambio de modelo decidido por el usuario

Lentes: A+B+C+D sobre `0fd3de2..HEAD` (`82d6922`). C se disparó por `.github/workflows/ci.yml`; D se forzó por el orquestador (guard y puerta).

**Cerrado del intento 5:** gaps 1-10 conforme al diseño y al rebate aceptado del punto 2. Evidencia:
- corpus diferencial: `281 passed` + `87 passed`;
- guard: O(N·K) pasa de 43,4 s a 0,28 s (`echo cd .`×32000);
- paso serie: de 586 s a 65 s, con 55 tests serie igual a `--collect-only`;
- `ci.yml.MANUAL-COPY` idéntico;
- code-health CR.

**No cierra:** el análisis de bash sigue abriendo huecos nuevos en cada intento. Tras seis intentos, el usuario decide cambiar de modelo (2026-11-13). Ver el diseño al final.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | **Regresión fix5.** `_aritmetica` es O(n²): recorre hasta el final en cada `((`/`$((` sin memoria. Además, el tope de entrada se comprueba DESPUÉS de tokenizar. Con 7,8 KB (`"("*8000 + "; git push --force origin master"`) el hook agota el plazo y sale `role guard unavailable; normal permissions continue` sin deny | T-06 | superado (re-evaluado en el intento 7) | Lentes A, B, C y D: `guardrail-check.py:338-355,400,443-445,1261,1275`; Linux 4,6 s y Windows 5,65 s por el hook, frente a 0,004 s en `0fd3de2` |
| 2 | Important | **Regresión.** El guard ve heredoc donde bash no lo ve: `$[1<<2]`, `$(( "1" << 2 ))`, `$(( $(echo 1) << 2 ))`, `for ((i=0;i<1<<1;i++))`, `${x:-<<'E'}`. Las líneas siguientes se tratan como datos. `cdcda09` daba DENY | T-06 | superado (re-evaluado en el intento 7) | Lente B: `guardrail-check.py:335,429,443,517-525`; Git Bash ejecuta el `git restore .` |
| 3 | Important | **Regresión.** Con delimitador sin comillas, bash une `\⏎` antes de comparar con el delimitador, así que cierra el heredoc antes que el guard (`cat <<EOF⏎EO\⏎F⏎git restore .⏎EOF`) | T-06 | superado (re-evaluado en el intento 7) | Lente B: `guardrail-check.py:314-330` |
| 4 | Important | **Regresión.** La lista blanca (c) solo reconoce intérpretes por su nombre literal: `$BASH <<'EOF'`, `"$SHELL" <<'EOF'`, `s=bash; $s <<'EOF'`, `while read -r l; do $l; done <<'EOF'` | T-06 | superado (re-evaluado en el intento 7) | Lente B: `guardrail-check.py:270,725-730` |
| 5 | Important | **Regresión.** El cambio de base solo se mira en posición de programa y no sale de `eval`, de funciones ni de `. <(…)`. `eval cd ../main; git restore src`, lanzado desde un worktree hermano, borró cambios sin comitear del checkout del usuario | T-06 | superado (re-evaluado en el intento 7) | Lente C: `guardrail-check.py:677,685-720,771-787,1292`; repo real `lc6/wt` |
| 6 | Important | **Residual.** Envoltorios que no se desenvuelven para detectar git: `timeout 30`, `nice`, `stdbuf -o0`, `time -p`, `setsid`, `sudo`, `env -S`, `xargs git`. Además, plazo agotado con `export GIT_0…`×3000 + `"g"it` (44 KB) | T-06 | superado (re-evaluado en el intento 7) | Lentes B y C: `guardrail-check.py:563-620,678,830,1283-1287`; Git Bash ejecuta el `git restore .` |
| 7 | Important | La puerta de redact da VERDE a un n^1,5 genuino con el reloj real (relativa 1,21 en Windows sin carga) y a un cuadrático que pesa un 5 %. Causa: `min(corregida, cruda)` + `min(vrc)`. La demostración solo usa el reloj simulado | T-23 | superado (re-evaluado en el intento 7) | Lente B: `test_redact_fix3.py:342-365`; `scratchpad/lb6/gate2.out` |
| 8 | Minor | Residual: código por stdin, variables u otros intérpretes (`echo '…' \| bash`, `g=git; $g reset`, `bash <<< '…'`, `find -exec git`, heredoc entrecomillado a `python3`/`perl`) | T-06 | límite documentado (decisión del usuario) | Lentes A y C |
| 9 | Minor | El CR se trata como espacio y como fin de delimitador; bash lo trata como carácter normal | T-06 | superado (re-evaluado en el intento 7) | Lente C: `guardrail-check.py:292,447,455` |
| 10 | Minor | Entrada > 64 KB → `input-too-large` y la orden continúa sin pasar por el guard | T-06 | corregido en fix6 (verificado en el intento 7) | Lente C: `native-guardrail.py:308-311`, `run-hook.mjs:283` |
| 11 | Minor | Subcomandos destructivos fuera de la lista: `reset --keep/--merge`, `checkout-index -f`, `read-tree -u --reset`, `rm -rf .` de git, `worktree remove --force`, `checkout -`/`@{-1}`/`refs/heads/master` | T-06 | superado (re-evaluado en el intento 7) | Lente C: `guardrail-check.py:666` |
| 12 | Minor | Falso deny: commit con `<<'EOF'` y apóstrofo cuando otro segmento lleva `time`/`env`/`xargs` (`time pytest && git commit -m "$(cat <<'EOF'…)"`), con un mensaje engañoso | T-06 | corregido en fix6 (re-verificado por el orquestador en el intento 11: allow) | Lente B: `guardrail-check.py:514,730` |
| 13 | Minor | `CUSTOM_AGENTS_ACTIVITY_DEADLINE_SCALE` también se aplica en producción: con escala ≥ 1,6 el lanzador mata el proceso hijo antes de su cierre limpio | T-23 | superado (re-evaluado en el intento 7) | Lente B: `agent-activity-store.py:38-52,689`, `run-hook.mjs:26,366` |
| 14 | Minor | `\r(?!\n)` marca ficheros `\r\r\n` y CR sueltos dentro de una línea como «separador CR» (falso `parcial: true`) | T-07 | superado (re-evaluado en el intento 7) | Lente B: `code-health.py:263-271` |
| 15 | Minor | Aserción que no puede fallar (`relativa is None and t < SUELO_CPU`); coste evitable de la demostración cuadrática (sin tope previo) y pausas de 5 s | T-23 | superado (re-evaluado en el intento 7) | Lentes A y D: `test_redact_fix3.py:264,338,438-453` |
| 16 | Minor | Ledger: fila «Total» de la réplica con columnas de otra tabla y una suma que no cuadra (1.025 frente a 1.032); T-23 `en-progreso` con `Cerrada: 2026-11-11`; RED de `77d7ec9` comiteado después; tope de 30 KB rebatido sin aceptación (`max(1,5 s, 2×base+1 s)`) | T-23, T-06 | superado (re-evaluado en el intento 7) | Lente A: `tasks.md:669-670,804`; `test_guardrail_differential.py:365` |

**T-23, «< 50 %».** No se puede juzgar con la medida actual. Hay 11.867 tests frente a 11.190, y la carga del host era distinta: el paralelo pasa de 615 s en reposo a 734 s con carga. Según cómo se normalice, el resultado cae a los dos lados del umbral (44-52 %). Lente D: lo introducido por la iniciativa solo suma ~5 s al paralelo y ~30 s al serie, y no hay coste evitable de tamaño. **Decisión del usuario:** medida emparejada local. Árbol HEAD y un contenedor `-m 1g --cpuset-cpus 0-3`, con el host en reposo y orden A-B-A-B, dos veces por brazo. A = CI vieja (bucle de scripts + `pytest` sin xdist sobre las mismas rutas); B = CI nueva. Se anota la mediana de B/A en `testing/perf.md`; pasa si es < 0,5. La ejecuta el orquestador cuando el usuario haya parado sus contenedores.

**Diseño fijado (decisión del usuario, 2026-11-13: «cambiar de modelo» y «solo cuadrático o peor»).**

1. **Falla cerrado para el rol protegido.** Si el guard no puede decidir, el lanzador DENIEGA cuando el rol es protegido (`implementer`/`architect`, la política de ADR-023), y conserva `continue` para el resto. Casos: plazo agotado, entrada > 64 KB, error o intérprete ausente. Esto lo cierran juntos los gaps 1, 6 (plazo) y 10, y queda como garantía de diseño. Aparte:
   - el guard hace un recorte barato y lineal ANTES de tokenizar: con > 16 KB o > 4.000 palabras, deny si el texto contiene `git` o un cambio de base;
   - `_aritmetica` pasa a ser lineal o memoizada;
   - test de punta a punta por `run-hook.mjs`: plazo agotado simulado y entrada > 64 KB → deny para el implementer y `continue` para un rol no protegido.
2. **El cuerpo del heredoc se analiza SIEMPRE**, como en `cdcda09`, con el invariante de cierre del intento 5. La única excepción es una lista blanca de FORMAS EXACTAS de orden completa (no de reglas de análisis):
   - `git commit [opciones] -m "$(cat <<'DELIM' ⏎ … ⏎ DELIM ⏎ )"`
   - `git commit [opciones] -F - <<'DELIM' ⏎ … ⏎ DELIM`

   Cada una puede ir precedida de `git add …` / `cd <propio directorio>` y unida con `&&`. Delimitador entrecomillado. En esas formas el cuerpo es el mensaje y no se analiza.

   Se retiran: el salto general de cuerpo, la lista de intérpretes como condición de salto y la detección de `<<` aritmético para el salto. Eso cierra los gaps 2, 3, 4 y 12. El precio aceptado es un falso deny de heredocs fuera de las formas exactas cuyo cuerpo tenga comillas impares; la salida es escribir el fichero con la herramienta de edición o usar `-F <fichero>`. El mensaje de deny lo dice.
3. **Envoltorios.** `_literal_invocation` desenvuelve los mismos envoltorios que `_posicion_programa`: `timeout [opts] N`, `nice [-n N]`, `stdbuf …`, `time [-p]`, `setsid`, `sudo [opts]`, `env [-S …]`, `xargs [opts]`, `nohup`, `command`, `exec`, `builtin`. Cierra el gap 6. Los subcomandos del gap 11 se añaden a la lista de destructivos o de cambio de rama.
4. **Cambio de base dentro de `eval`, funciones y `. <(…)`.** Si la orden define una función o usa `eval`/`source`/`.` con contenido, el cambio de base se busca también en ese contenido, y el resultado sube a la orden que lo contiene. Cierra el gap 5.
5. **Modelo de amenaza documentado** en `docs/agents/implementer.md` y en CONVENTIONS ES/EN si procede. El guard frena los errores de un agente honesto. Las indirecciones deliberadas (variables como programa, código por stdin hacia intérpretes, `find -exec`) son un límite conocido: gap 8, sin corrección.
6. **Corpus diferencial.** Todas las sondas de las lentes A, B y C del intento 6 entran como BAD (las de `lb6`, `lc6`, `la6` e `i6` del scratchpad) o como límite documentado (gap 8, marcadas como tal). Los LEGIT incluyen las 14 órdenes típicas de la Lente B.
7. **Puerta de redact: solo cuadrático o peor** (gap 7). Mediana en lugar de mínimo y umbral ~6 frente a la razón 16 del cuadrático con ×16. La demostración con reloj REAL debe rechazar un cuadrático puro y aceptar uno lineal, con 10 pasadas sin rojo en Linux con carga y en Windows con carga. El docstring documenta que n^1,5 queda fuera del alcance. Se cierra también el gap 15: tope de CPU antes de medir la entrada grande de la demostración y aserción tautológica fuera.
8. **Minor 9, 13, 14 y 16:**
   - 9: el CR fuera de comillas cuenta como carácter normal, igual que en bash; un CR en una orden con `git` → deny.
   - 13: la escala solo actúa si además está activa una marca de test explícita, o se documenta y se acota a ≤ 1,5.
   - 14: el aviso se da solo cuando hay `\r` y NINGÚN `\n` en el fichero.
   - 16: se corrige la fila Total, se quita el `Cerrada` de T-23 y se anota la deuda de orden.

Tras este ciclo: réplica Linux completa sin rojo, medida emparejada de T-23 (orquestador) y verificación dirigida de las cuatro lentes. Si solo quedan Minor sin pérdida de datos, la fase cierra.


## Archivado 2026-11-15 — Revisión de dos lentes — intento 10: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix9: 2 Important, 7 Minor (bytes sin cambios)

SHA-256 del bloque: `84599c0fd709810da0c69dacc4dc44dd1ed2779cbd3b43a53b2af6925d439153`.

## Revisión de dos lentes — intento 10: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix9: 2 Important, 7 Minor

Lentes: A+B+C+D sobre `93df37e..ae382f7`, dos a dos por memoria.

**Cerrado del intento 9:** los 8 gaps.
- `xargs -a`/`--arg-file` con `<(…)` → deny en sus 15 formas. El fuzz de la Lente B (5.208 órdenes, 93df37e frente a HEAD) da 0 regresiones fuera de `case`.
- `test_journal` sin reloj de pared: `-k replay` ×10 con 16 bucles de CPU, 10/10.
- Escáner Python con `\\.` y test de paridad.
- `env -S` con troceo propio: 47-48 valores comparados con GNU env 8.32 real.
- Panel con `BODY_TIMEOUT` inyectado y en paralelo.
- Demo de redact con `not _es_lineal`: razones medidas de 9,66 a 15,23 con umbral 6; coste de 3,4 a 10,4 s.
- OpenCode con caché.
- Límite de 128 MiB documentado.

**Interpretaciones aceptadas del implementer:**
- i1: troceo propio en vez de shlex.
- i3: `env -S 'echo "hola'` pasa a deny.
- i4: `\#` y `\$` se permiten.
- i5: `${VAR}` dentro de `-S` es indirección y entra en el modelo de amenaza.

`source <(echo git restore .)`/`bash <(…)` → allow es indirección (el texto lo genera `echo`). Las órdenes escritas dentro de `<(…)` sí se analizan (Lente C). Queda como límite.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Regresión del fix9: dentro de `<(…)`/`>(…)` el `)` de un patrón de `case` cierra la sustitución, y el resto se queda como argumentos de la orden exterior, que ya no se parte. `cat <(case x in x) git reset --hard;; esac)` → allow (deny en 93df37e). Igual con `tee >(case x in x) git stash drop;; esac)` y `diff <(case "$f" in *.py) git checkout master;; esac) b`. `$(case x in x) …)` ya daba allow en 93df37e. Bash 5.2.37 real: centinela perdido. Verificado por el orquestador | T-06 | corregido en fix10 (`a4ba641`) | Lente C: `guardrail-check.py:511-521,530`; `lc10/p1.py`, `lc10/r1` |
| 2 | Important | Fallo abierto en OpenCode, silencioso y permanente. Si `realpathSync.native` falla una vez durante `setup` (EIO pasajero en unidad de red, junction o enlace), `locationReal` se queda en `resolve()`. Las llamadas posteriores sí resuelven y se cachean, así que `sameLocation` da falso y la sesión del propio proyecto sale `foreign`: sin guard durante toda la vida del plugin. En 93df37e se deniega | T-06 | corregido en fix10 (`a4ba641`) | Lente C: `hooks/opencode-plugin.js:73-84,94,250,311-315` y su espejo; `lc10/p3.mjs` |
| 3 | Minor | La caché de rutas reales no caduca y `locationReal` se fija en `setup`. Si el enlace del proyecto se re-apunta con OpenCode abierto, la sesión sale `foreign`. Requiere re-apuntar el enlace. El impacto de punta a punta no es verificable sin runtime | T-06 | corregido en fix10 (`a4ba641`) | Lentes B y C: `opencode-plugin.js:73-82,94`; `lb10/oc.mjs` |
| 4 | Minor | Un fallo de `realpath` no se cachea y se repite de forma síncrona en cada herramienta y cada evento. En UNC caído son 8 s la primera vez y de 5,6 a 8 ms después, con el bucle de eventos bloqueado. No es regresión | T-06 | corregido en fix10 (`a4ba641`) | Lente D: `opencode-plugin.js:77-82,249,453`; `ld10/rp.mjs` |
| 5 | Minor | `_BLANCOS_ENV` incluye `\n\v\f\r`, pero GNU env 8.32 solo separa por espacio y tabulador. Tras un LF el guard abre palabra nueva y toma `#` como comentario: `env -S 'git -c user.name=c⏎#y restore .'` → allow, con el centinela perdido en bash real. En 93df37e también daba allow. Es una forma deliberada | T-06 | corregido en fix10 (`a4ba641`, `926a8ef`) | Lente B: `guardrail-check.py:829,899,901`; `lb10/envcmp.py` |
| 6 | Minor | Paridad de blancos: el `\s` de Python casa `\x1c`-`\x1f` y `\x85`; el de JS no. Solo ocurre con JSON inválido y el lado más estricto es Python. Sin efecto de punta a punta | T-06 | corregido en fix10 (`a4ba641`) | Lente C: `native-guardrail.py:83` frente a `run-hook.mjs:116`; `lc10/p4.py` |
| 7 | Minor | Dos aserciones con presupuesto corto (`replay(budget_ms=100)` y `recover(budget_ms=300)` esperan 1) no recibieron el trato del punto 2. Margen sin carga de unas 3×. La Lente B no las reproduce en 60 iteraciones con carga | T-23 | corregido en fix10 (`a4ba641`) | Lente A: `test_journal.py:1631-1632,2716-2717`; `la10/jb2.py` |
| 8 | Minor | Los comentarios de la demo de redact contradicen el ledger y la configuración: dicen 11,8 frente a 10,90, «1 muestra» frente a `MUESTRAS_DEMO = 3`, y ×14 frente a ×12 | T-23 | corregido en fix10 (`a4ba641`) | Lente A: `tests/test_redact_fix3.py:262,469,705` |
| 9 | Minor | Fuera del diff. En 2 de 10 pasadas, `test_replay_con_recover_dos_procesos_concurrentes_no_duplican` emite un warning de hilo en Windows: `FileExistsError [WinError 183]` al renombrar `.tmp-*` → `.custom-agents-journal`, seguido de `ValueError: unsafe_state`. El test pasa. Puede ser una carrera de escritura del journal en Windows | T-23 | corregido en fix10 (`a4ba641`): defecto real, causa raíz y test de regresión en T-23 | Lente B: `journal-io.py:108-121` |

**Diseño fijado por el orquestador para fix10:**

1. **`case` dentro de una sustitución** (gap 1). Dentro de `$(…)`, `<(…)`, `>(…)` y backticks, el lector reconoce la gramática de `case`: tras `case <palabra> in`, un `)` cierra un patrón y no la sustitución, hasta `;;`, `;&`, `;;&` o `esac`. También vale el `(` opcional delante del patrón. Si el lector no puede seguir la gramática con certeza (anidamiento, `esac` ausente), la orden se deniega cuando contiene git o un cambio de base. Ante la duda, deny. Las formas del gap, con `$(case …)` incluido, van al corpus diferencial como BAD con bash real. Se amplía el fuzz de la Lente B con `case` en todos los contextos.
2. **OpenCode, comparación sin fallo abierto** (gaps 2, 3 y 4).
   - Dos rutas son la misma ubicación si coinciden tras `resolve()` (con minúsculas en win32 y darwin) **o** tras `realpath`. La unión solo amplía qué sesiones se guardan.
   - La ruta real de `location.directory` no se fija en `setup`. Pasa por la misma caché que el resto.
   - La caché guarda éxitos y fallos con caducidad corta (unos 5 s), está acotada y no bloquea más de una resolución por ruta y ventana.
   - Tests del adaptador: fallo en el primer `realpath` y éxito después → la sesión propia se guarda; enlace re-apuntado → guardada al caducar la entrada; ruta caída → una sola llamada por ventana. Se regenera interop.
3. **`env -S`** (gap 5). Se separa solo por espacio y tabulador, como GNU env. `\n`, `\v`, `\f` y `\r` literales son parte de la palabra y no abren comentario. Se comprueba también contra el coreutils de la imagen Linux de CI (9.x) en la réplica: si difiere de 8.32, se deniega la forma ambigua.
4. **Paridad** (gap 6). Los dos escáneres usan la misma clase explícita de blancos JSON (`[ \t\n\r]`), sin `\s`. Se añaden casos al test de paridad.
5. **Journal** (gap 7). Los dos presupuestos cortos pasan a un reloj inyectado, o a un presupuesto que no dependa de la carga, con la misma semántica (1 elemento). El test vigía de fix9 los incluye.
6. **Comentarios de la demo** (gap 8). Se corrigen con las cifras de la configuración final y del ledger.
7. **Carrera del journal en Windows** (gap 9). Se aplica `debug-root-cause`:
   - Reproducir, aislar y probar la hipótesis.
   - Si hay un defecto real (captura perdida, duplicada o un estado inseguro que no se recupera): fix con test de regresión.
   - Si el warning es ruido de un camino ya manejado (reintento): eliminar el warning, con evidencia en el ledger.
   - Si el arreglo excede la fase: se anota en T-39 con la evidencia.

Tras este ciclo: réplica Linux completa sin rojo, medida emparejada de T-23 con el equipo libre (la hace el orquestador) y verificación dirigida de las cuatro lentes. Si solo quedan Minor sin pérdida de datos, la fase cierra.


## Archivado 2026-11-15 — Revisión de dos lentes — intento 11: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix10: 4 Important, 8 Minor (bytes sin cambios)

SHA-256 del bloque: `86e07fb16541591b6bbbe0316308e2176077dd1cff1e5d0b1ed5eb68a0609cd7`.

## Revisión de dos lentes — intento 11: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix10: 4 Important, 8 Minor

Lentes: A+B+C+D sobre `d938cab..8e7c0a0`, dos a dos por memoria.

**Cerrado del intento 10:**
- Gaps 2-9. OpenCode compara por `resolve()` ∪ `realpath`, la caché de 5 s guarda fallos y no fija la ruta en `setup`; tests 4/4.
- `env -S` solo por espacio y tabulador, con LF/VT/FF/CR sueltos denegados (8.x y 9.x difieren).
- Paridad `[ \t\n\r]`, presupuestos del journal con reloj congelado y comentarios de la demo.
- Carrera `nlink == 2` del journal en la rama de lectura: 0 errores en 60 rondas.
- Las formas del gap 1 dan deny. Réplica Linux de fix10: 13.001 + 58 passed, node 528, 0 rojos.

**Interpretaciones del implementer:** i2 (test de fix9 reescrito), i3 (`case` anidado → deny) e i4 (las dos condiciones de `env -S`) se aceptan. La i1 (fallo de `realpath` cacheado ⇒ sesión propia `foreign` 5 s) **no** se acepta: choca con el fallo cerrado (gap 9).

**El lector de `case` no converge.** Cada lente encuentra una forma nueva que bash ejecuta y el lector no sigue. El fuzz de fix10 solo ponía el git destructivo FUERA del `case`; con git dentro del cuerpo da 144 regresiones en 1.560 órdenes.

Incidente de la Lente C, sin efecto: su primera pasada usó el bash de WSL y ejecutó un `git reset --hard` real en el scratchpad, que no es un repositorio (fatal). Repetido con el bash de Git for Windows y un `git` falso.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Regresión del fix10: un `case` dentro de un subshell `( … )` en una sustitución. Con `par>0` el `)` del patrón cae al separador, el estado sigue en patrones, el cuerpo se descarta y `esac` cierra sin `incompleta`. `cat <( (case x in x) git restore .;; esac) )` → allow (deny en d938cab), con el centinela perdido en bash 5.2.37. También con `;`, `&&`, `if`, funciones y anidado. Verificado por el orquestador | T-06 | fix11 p1: `case` por lista blanca (subshell → incompleta) | Lentes A y B: `guardrail-check.py:571,575,586,603,606,613`; `la11/p1.py`, `lb11/fuzz11b.py` |
| 2 | Important | Regresión del fix10: `in(` sin espacio. `echo $(case x in(x) git reset --hard;; esac)` → allow (deny en d938cab). Verificado por el orquestador | T-06 | fix11 p1: `in(` → incompleta | Lente B: `guardrail-check.py:568,597,603,606` |
| 3 | Important | No es regresión. Tras `time -p`, `time --`, `coproc` o `function f`, bash reconoce `case` como reservada y el lector no: el primer `)` cierra `<(…)`. `cat <(time -p case x in x) git reset --hard;; esac)` → allow, git ejecutado | T-06 | fix11 p1: tras `time`/`coproc`/`function`/`!` → incompleta | Lente C: `guardrail-check.py:395-400,411-414` (`_PREFIJOS_ORDEN`); `lc11/c1.txt` |
| 4 | Important | `_empieza_orden` recorre todo `cur` por cada palabra de una sustitución: O(n²) con palabras de prefijo. `echo $(! ! … )` de 32 KB → 12 s y de 64 KB → 47 s (d938cab: 0,09 s). Pasa el plazo de 10 s del hook: deny falso tras 9 s de bloqueo. Con git, 0,35 s. Rompe la garantía lineal documentada | T-06 | fix11 p2: `_empieza_orden` retirado, O(1) por palabra (64 KB: 0,1 s) | Lente D: `guardrail-check.py:398-399,411,597,1295-1299`; `ld11/b1.py` |
| 5 | Minor | Palabras de cabecera citadas o escapadas cuentan como reservadas (`"case"`, `"esac"`, `"then"`, `\then`). `cat <("case" x in; git reset --hard; "esac")` y `cat <("then" case x in ; git reset --hard; "esac")` → allow (deny en d938cab). Son formas deliberadas | T-06 | fix11 p1: palabra «plana» (citada o escapada → incompleta) | Lentes B y C: `guardrail-check.py:395-400,577,587,597,603` |
| 6 | Minor | `esac` como patrón (`case esac in "esac")`, `\esac)`, `x\|esac)`) cierra la sustitución. Ya en d938cab | T-06 | fix11 p1: `esac` como patrón o argumento → incompleta | Lente C: `guardrail-check.py:571-572,586-588` |
| 7 | Minor | `$'…'` toma el carácter crudo tras la barra: `env -S $'git\trestore .'` y `$'git\x20restore\x20.'` → allow, bash ejecuta git restore. Ya en d938cab; codificación deliberada | T-06 | fix11 p3: `$'…'` se decodifica como bash | Lente B: `guardrail-check.py:462-467` |
| 8 | Minor | Carrera del gap 9 del intento 10 en la rama de escritura: si el ganador hace `os.link` entre el `lexists` de `_asegurar_gitignore_local` y el de `write`, `IO.read` lanza `unsafe_state` sin esperar. Excepción, sin pérdida | T-23 | fix11 p4: rama write con la misma espera | Lente B: `journal-capture.py:297-299`, `journal-io.py:110-111`; `lb11/jr.py` |
| 9 | Minor | i1 no aceptada: si falla el primer `realpath` y la sesión llega con otra forma de ruta, la sesión propia sale `foreign` durante 5 s, sin guard para el rol protegido. La Lente C confirma que guardar de más solo ejecuta el guard con el cwd de la sesión | T-06 | fix11 p5: fallo de `realpath` → indeterminada → guardada | Lentes B y C: `opencode-plugin.js:79-81,248-249,312-314` y espejo; `lb11/oc11.test.mjs` |
| 10 | Minor | Con un enlace duro persistente (plantado, o un inicializador muerto entre `os.link` y el `unlink` del `.tmp-`), cada `JIO.queue`/`read_settled` paga 0,75-0,87 s antes del mismo `unsafe_state`. En SessionEnd consume el presupuesto de 800 ms del hijo y lo matan en vez de salir con error limpio | T-23 | fix11 p4: espera solo con `.tmp-` hermano del mismo inodo | Lente D: `journal-io.py:82-100,203`, `run-hook.mjs:13-16`; `ld11/j1.py` |
| 11 | Minor | El deny de LF/VT/FF/CR sueltos en `env -S` (`926a8ef`) entró sin RED previo; sus tests llegan en `fcd182e` y el ledger no lo declara | T-06 | declarado: sin RED previo (bloque fix11 de T-06) | Lente A: `guardrail-check.py:963-966`, `test_guardrail_fix10.py:56-71` |
| 12 | Minor | `docs/agents/implementer.md:92` dice que LF/VT/FF/CR son parte de la palabra; el código los deniega como forma ambigua | T-06 | fix11 p6: `implementer.md:92` | Lente A |

Fuera de gap (límite, indirección): `$(true) git reset --hard` y `` `true` git … `` → allow en d938cab y HEAD.

**Diseño fijado por el orquestador para fix11:**

1. **`case` por lista blanca, no por gramática completa** (gaps 1, 2, 3, 5 y 6). Dentro de `$(…)`, `<(…)`, `>(…)` y backticks, el lector solo sigue la forma simple: `case` sin comillas ni escape, como primera palabra de una orden a profundidad 0 de la sustitución y sin prefijos (`time`, `coproc`, `function`, `!`…); `in` como palabra propia sin comillas; patrones sin comillas, sin escapes y sin `esac`, con `(` opcional separado. Cualquier otra aparición de `case` o `esac` (citada, escapada, tras un prefijo, en un subshell, `in(`, `esac` en patrón) marca la lectura como **incompleta** → deny si la orden contiene git o un cambio de base. Corpus diferencial con bash real: TODAS las formas de `la11/`, `lb11/` y `lc11/` como BAD. Fuzz con el git destructivo DENTRO del cuerpo, en subshells, tras prefijos y con cabeceras citadas: 0 regresiones frente a d938cab y frente a 8e7c0a0.
2. **Coste lineal** (gap 4). Saber si una palabra empieza orden es O(1) por palabra (estado incremental, sin recorrer `cur`). Test con `$(! ! …)`, `$({ { …)` y patrones/cuerpos de prefijos de 64 KB, con y sin git: < 0,3 s.
3. **`$'…'` en `env -S`** (gap 7). Un valor de `-S` que viene de `$'…'` con una barra invertida se deniega si la orden contiene git (forma ambigua), salvo que se decodifique con la semántica de bash y haya test con las dos formas del gap.
4. **Journal** (gaps 8 y 10). La espera de `settled` solo se aplica si existe un `.tmp-*` hermano con el mismo inodo (inicialización en curso) y reciente; en otro caso, `unsafe_state` al instante. La rama de escritura recibe la misma espera acotada. Tests: carrera en la rama write; enlace duro plantado sin `.tmp-` → fallo en < 50 ms.
5. **OpenCode** (gap 9). Si `realpath` falló (fallo cacheado) para cualquiera de los dos lados, la comparación es **indeterminada** y la sesión se guarda. Test: primer `realpath` fallido + forma de ruta distinta → guardada. Interop regenerado.
6. **Ledger y docs** (gaps 11 y 12). Se declara en el ledger que el deny de LF/VT/FF/CR no tuvo RED previo. Se corrige `implementer.md:92` (y INTEROP ES/EN si repiten la frase).

Tras este ciclo: réplica Linux completa sin rojo, medida emparejada de T-23 con el equipo libre (la hace el orquestador) y verificación dirigida de las cuatro lentes. Si solo quedan Minor sin pérdida de datos, la fase cierra.

