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

