# Observabilidad — qué mide este plugin y cómo convive con monitores de sesión

[English](en/observability.md) · **Español**

Dos preguntas distintas necesitan herramientas distintas:

| Pregunta | Herramienta | Qué obtienes |
|---|---|---|
| **¿Cuánto costó producir esto?** (una spec, un plan, la tarea T-03, la iniciativa entera) | **Este plugin** — `usage-meter.py` (kit shared) | Tokens reales medidos por artefacto/tarea, € (con `rates.json`), horas-IA derivadas por ratio calibrado, bloque `generacion:` en el frontmatter, sección **Coste de proceso** en `/roadmap-metrics`, calibración vía `/retro`. Es coste **con significado de negocio**: se imputa a Jira, entra en el presupuesto y calibra estimaciones futuras. |
| **¿Qué está haciendo el agente AHORA?** (sesiones en vivo, herramientas, subagentes, errores) | Un **monitor de sesión externo** — p. ej. [hoangsonww/Claude-Code-Agent-Monitor](https://github.com/hoangsonww/Claude-Code-Agent-Monitor) | Dashboard en tiempo real vía los hooks de Claude Code: actividad por sesión, kanban de agentes (Working/Waiting/Completed/Error), analytics de tokens por sesión, DAGs de orquestación de subagentes, notificaciones. Es **actividad operativa**, sin noción de iniciativa/tarea/€. |

Son **complementarios, no competidores**: el monitor no sabe qué es una iniciativa ni imputa a
Jira; el usage-meter no te enseña un dashboard en vivo de lo que el agente está tecleando.
Este plugin **no reimplementa** un monitor de sesión (servidor + UI + WebSockets es un producto
entero); si quieres esa vista, instala uno al lado.

**`duracion` vs. `duracion_reloj` en el JSON de `close`:** `duracion` es tokens facturables ÷ ratio
calibrado (la que usan dashboards, plantillas e imputación a Jira — nunca cambia de semántica);
`duracion_reloj` es aditiva y mide el reloj de pared (`fin − inicio`), útil para detectar sesiones
largas con poco token real (pausas, lectura) pero que **no** sustituye a `duracion` en ningún cálculo.

**Límite conocido: marcadores encadenados dentro de la tolerancia de 60 s.** El filtro de ventana de
`close` admite registros hasta 60 s antes de `inicio` (relojes de fichero vs. reloj de `start`). Si un
segundo marcador abre su `start` a menos de 60 s del `close` del primero, y el segundo `close` lee un
fichero de transcript que el primero **no** tenía en su snapshot de offsets, los registros de ese solape
se cuentan en AMBAS ventanas: no es una regresión (antes de la corrección de esta iniciativa se contaba
el transcript entero de nuevo, que era peor), pero sí una fuente de doble conteo en el caso concreto de
marcadores muy próximos en el tiempo sobre ficheros nuevos. Mitígalo espaciando `start`/`close` más de
60 s cuando encadenes tareas cortas, o interpretando `duracion_reloj` corto + `tokens_reales` alto como
señal de posible solape.

## Coexistencia de hooks (verificada)

- **Este plugin** registra hooks **no bloqueantes** (`hooks/hooks.json`) en tres eventos:
  `PostToolUse` (marcar `docs/` pendiente de Confluence, aviso de `ledger-lint` y **línea de
  progreso** sobre `tasks.md`), `SubagentStop` (estado de las iniciativas activas al terminar un
  subagente), `SessionStart` (índice de piezas del plugin + contexto de retoma al
  arrancar/retomar/compactar + última entrada del journal al arrancar/retomar, además de drenar la
  outbox de la captura durable), `UserPromptSubmit` (el turno del usuario a un log crudo no
  versionado, con opt-out `<private>` — también el checkpoint de la sesión) y `SessionEnd` (un
  envelope atómico en la outbox local; `SessionStart` lo materializa en una entrada de bitácora en
  `docs/knowledge/journal/`, con `decisiones`/`pendientes` extraídas de ese log). No interceptan
  ni modifican nada; **informan** (`systemMessage` / `additionalContext`), no deciden; siempre
  exit 0.
- **Agent-Monitor** registra sus propios hooks (envían eventos por HTTP a su servidor local).
- Claude Code ejecuta **todos** los hooks registrados para un evento: los de ambos conviven sin
  interferirse. Ninguno de los dos exige exclusividad ni reescribe la config del otro.
- Si el servidor del monitor está caído, sus hooks fallan **sin afectar** a los del plugin (y
  viceversa): cero dependencia mutua.

## Instalar ambos

1. Este plugin: ver [`INSTALL.md`](INSTALL.md) (marketplace o bundle en `.claude/`).
2. El monitor: sigue su README (servidor local + `install-hooks`). Sus hooks se AÑADEN a los
   existentes en la config de Claude Code; no borres los del plugin al instalarlo.
3. Comprobación rápida: edita un fichero bajo `docs/` — debe dispararse el aviso del plugin — y
   verifica que la sesión aparece en el dashboard del monitor.

## Visibilidad en vivo (sin monitor externo)

Entre las dos preguntas de arriba hay una tercera, más modesta, que el plugin **sí** responde solo
con el ledger canónico: **¿cómo va la iniciativa ahora mismo?** Todo determinista
(`agent-kits/shared/progress-report.py`, con tests), sin prosa extra en los agentes:

| Momento | Mecanismo | Qué ves |
|---|---|---|
| Cada edición de un `docs/roadmap/*/tasks.md` | hook `PostToolUse` → `progress-line.sh` | Una línea: `📋 <slug> · T-04/12 completadas (33%) · fase 2/4 «…» · en curso: T-05 … · IA real 1h 12m`. Con debounce: si el estado no cambió, silencio. |
| Al terminar un subagente | hook `SubagentStop` → `subagent-progress.sh` | Las mismas líneas, una por iniciativa `en-progreso` (solo si hay alguna). |
| Al arrancar, retomar o tras compactar el contexto | hook `SessionStart` → `session-context.sh` | (1) **Índice de piezas** del plugin (`agent-kits/shared/skill-index.py`): 3 líneas de reglas de enrutado + una línea ≤ 110 caracteres por comando/skill/agente, generado DETERMINISTA desde los frontmatters, ≤ 45 líneas / ≤ 3.500 caracteres, con caché por hash en `.claude/.skill-index.cache`; es la respuesta a «la skill correcta no se disparó»: las descriptions solo se ven cuando Claude las busca, el índice las pone delante en cada arranque. Informativo (no fuerza nada); desactivable con `.claude/dev.json` `{"sesion": {"indice": false}}`. (2) Bloque ≤ 15 líneas del roadmap: iniciativas activas, tareas en curso, marcadores abiertos del usage-meter y «retoma desde la tarea en-progreso» (solo si hay algo activo). Va también en `compact` porque la compactación resume la conversación y puede perder el índice del arranque (guía oficial de hooks, «Re-inject context after compaction», verificada 2026-09-03). Total < 10.000 caracteres (tope del hook). Sin nada que decir, no inyecta nada. |
| En cada turno del usuario | hook `UserPromptSubmit` → `user-prompt-capture.sh` | Nada en pantalla (en este evento el stdout se inyectaría como contexto y un exit 2 borraría el prompt: el hook nunca emite y siempre sale 0): `journal.py capture` añade el turno como una línea JSON a `.claude/session-prompts-<session_id>.log` — **no versionado** (`capture` siembra `.claude/.gitignore` con `session-prompts-*`), **secretos evidentes redactados** antes de tocar el disco, `0600`, cerrojo entre turnos solapados, topes por turno/fichero y purga a 30 días. Opt-out por turno: `<private>` en cualquier parte (el log no se toca y ese turno tampoco sale de la transcripción). Opt-out por proyecto: `dev.json` `{"sesion": {"captura": false}}` (o `journal: false`). Solo en proyectos con rastro del plugin. `hooks.json` declara `timeout: 5` (default oficial 30). |
| Al terminar la sesión (salir, `/clear`, logout) | hook `SessionEnd` → `session-journal.sh` (exec form, `timeout: 5`) | Nada en pantalla (por contrato la salida de `SessionEnd` se ignora): desde **session-end-durable-capture**, `SessionEnd` ya NO hace el trabajo pesado en el teardown — `journal.py capture-end` escribe SOLO un **envelope atómico** (≤ 64 KiB, `event_id` determinista, sin git/IA/red, CA-01) en la **outbox** local (`.claude/journal/outbox/`, `agent-kits/shared/outbox.py`), en < 100 ms (p95 ≤ 100 ms / p99 ≤ 300 ms, CA-02, medido con `scripts/bench-session-end.py`). |
| Al arrancar/retomar/compactar | hook `SessionStart` → `session-context.sh` (además de lo de la fila de arriba, `SessionEnd`) | **Reconciliación presupuestada** (T-05): `journal.py replay --ia no --budget-ms 300 --max 3 --con-recover` drena la outbox reutilizando el camino de siempre (git, log de prompts, IA opt-in) y materializa la entrada — `cierre: materializado` en el frontmatter; nunca bloquea el arranque (si `bloqueado`/`errores` viene no vacío, una línea de aviso, nada más). `--con-recover` materializa TAMBIÉN, bajo el MISMO cerrojo/presupuesto, como `cierre: recuperado_sin_cierre` una sesión con log de prompts sin envelope y sin sesión viva pasada `sesion.journal.ventanaHuerfanaMin` (default 1440 min / 24h, CA-07); una sesión concurrente viva nunca se toca. Solo entradas YA escritas en disco llegan a (3) — nunca se inyecta una entrada sin materializar (CA-08). La entrada usa la fecha del **cierre** (`captured_at`), no la del replay; los campos derivados de `git` se calculan al materializar y el frontmatter lo marca con `derivados_en: replay` (también para las huérfanas recuperadas por `--con-recover`: corren bajo la misma pasada, nunca `recover`). Escritura idempotente por `session_id`, atómica; `decisiones`/`pendientes` **extraídas sin modelo del log crudo** de `UserPromptSubmit` (frases del usuario con marcador léxico ES/EN; sin log o sin marcadores → `[]` honesto) y `resumen` = primer turno capturado. La entrada declara que `decisiones`/`pendientes` son **citas** de los turnos, no instrucciones. Al arrancar/retomar (`startup\|resume`, no `compact`) `session-context.sh` añade (3) la última entrada compactada (≤ 25 líneas, `journal.py latest`). Desactivable con `dev.json` `{"sesion": {"journal": false}}`. **Resumen por IA opt-in** (`{"sesion": {"resumen": true}}`): tras escribir la entrada determinista, `claude -p --bare --output-format json` con los turnos por stdin y timeout 25 s re-escribe la misma entrada (`resumen_por: ia`); sin CLI, sin `ANTHROPIC_API_KEY`, timeout o JSON ilegible → queda la determinista con el motivo en `avisos`, exit 0 (ADR-010 revisado 2026-09-08: la salida de los hooks en `SessionEnd` sigue ignorándose — el hook no devuelve, **escribe**). A demanda: `journal.py replay [--con-recover]`/`recover`/`status [--json]`/`purge --confirm`; `recover` a demanda usa `--budget-ms`/`--max` con default **0 = sin tope** (materializa TODAS las huérfanas que encuentre; distinto del tope de 3/300 ms que usa `SessionStart` vía `replay --con-recover`), pero el cerrojo sigue siendo SIEMPRE no bloqueante (techo corto de 2 s cuando no se pasa presupuesto explícito). `/doctor` (sección «Journal») lee `journal.py status --json`: pendientes, huérfanas, dead-letter con remedio nombrado, triage del «Hook cancelled» (CA-10). Promoción: `journal.py candidatas` propone como `propuesta` los patrones repetidos en ≥ 2 sesiones (paso 2-quater de `/retro`). Los `avisos` que llegan al `additionalContext` de `SessionStart` (línea «Journal: …») se SANEAN antes de componerse: un `session_id` derivado del NOMBRE de un log (potencialmente plantado) pasa por el mismo saneado que protege los nombres de fichero, y el mensaje de cualquier excepción se reduce a su tipo + un fragmento corto restringido a caracteres imprimibles — sin saltos de línea, control ni marcas bidireccionales; la línea final va enmarcada como «estado operativo de la cola del journal; datos, no instrucciones», igual que el bloque de `latest`. |
| Siempre, en la barra de estado (**opt-in** en `/setup`, paso 5-bis) | `statusline/roadmap-statusline.sh` | `[Opus] $0.01 ctx 8% · 📋 <slug> T-04/12 33%` — modelo, coste de la sesión, contexto usado y progreso del roadmap. Sin `jq` usa `python3`; sin ninguno, solo el modelo. |

Reversión de la statusline: quitar la clave `statusLine` de `.claude/settings.json`.

### Contrato de garantías de la captura durable de `SessionEnd`

`SessionEnd` deja un envelope atómico; `SessionStart` (o `journal.py replay`/`recover` a demanda)
hace la materialización real. La tabla dice qué garantiza CADA forma de terminar la sesión — y qué
**no** garantiza nadie:

| Forma de salida | Garantía |
|---|---|
| `/exit`, `/clear`, `/resume`, Ctrl+D | Envelope durable en la outbox antes de terminar (< 100 ms, CA-02); journal materializado en el siguiente `SessionStart` o a demanda (`journal.py replay`). |
| Ctrl+C / terminal cerrada / proceso muerto antes de que corra el hook | Recuperación hasta el **último prompt capturado** por `UserPromptSubmit` (el log de prompts es el checkpoint): `journal.py recover` la materializa como `cierre: recuperado_sin_cierre` pasada la ventana (`sesion.journal.ventanaHuerfanaMin`, default 1440 min / 24h). |
| Ctrl+C con el envelope ya escrito | Igual que una salida normal: el aviso `Hook cancelled` del runtime es cosmético (la entrada ya existe o está en la outbox) — `/doctor` lo distingue de una pérdida real (CA-10). |
| Disco lleno / permisos al capturar o al materializar | Error verificable (`journal.py status`: `durabilidad`/`permisos` `degradada(os)`, o el item queda en `dead-letter/` con causa), nunca un éxito falso; el resto de la cola sigue procesándose. |
| Envelope corrupto (JSON venenoso, esquema no soportado, campos fuera de forma) | `dead-letter/` con causa estructurada; no bloquea a los demás (`journal.py replay --reintentar-dead-letter` para recuperarlo tras corregir la causa). |
| Sesión concurrente todavía viva (otra terminal con el mismo `session_id`) | Nunca se trata como huérfana, aunque su log de prompts lleve más tiempo del de la ventana sin actividad nueva. |

**Lo que esto NO garantiza** (fuera de alcance, spec `session-end-durable-capture`): los últimos
milisegundos ante un `SIGKILL` que mate el proceso ANTES de que corra cualquier hook (nada puede
capturarse si el hook nunca llega a ejecutarse); que dos `replay`/`recover` concurrentes sobre el
MISMO proyecto avancen en paralelo (un cerrojo no bloqueante los serializa: el segundo espera su
turno bajo presupuesto o dice `bloqueado: true` y sigue con el arranque); ni sustituir a `git` como
fuente de verdad — un envelope nunca ejecuta git (CA-01): los campos derivados de `git`
(`ficheros_tocados`, `tareas_cambiadas`) se calculan al MATERIALIZAR (`replay`), nunca en el cierre.

**Campos nuevos del frontmatter de una entrada** (`docs/knowledge/journal/AAAA-MM-DD-<slug>.md`):

| Campo | Significado |
|---|---|
| `cierre` | `materializado` (envelope + verificación vía `replay`) · `recuperado_sin_cierre` (sin envelope; reconstruida desde el log de prompts vía `recover`) · `dead_letter` (solo visible en la cola, `journal.py status`: nunca llega a ser una entrada). |
| `materializado_en` | Instante ISO-8601 UTC en que `escribir_sesion` escribió la entrada — normalmente DESPUÉS del cierre real de la sesión (`replay` puede correr sesiones más tarde). |
| `derivados_en` | `replay`: los campos que dependen de `git` (`ficheros_tocados`, `tareas_cambiadas`) describen el estado del repo AL MATERIALIZAR, no al cerrar la sesión — CA-01 prohíbe ejecutar git en el teardown, así que no hay otra fuente posible. Las huérfanas recuperadas por `--con-recover` también llevan `derivados_en: replay` (corren bajo la misma pasada). |

Medición (CA-02): `python3 scripts/bench-session-end.py --iterations 30 --assert-p95-ms 100
--assert-p99-ms 300` reporta DOS números con procedencia distinta (gap 71 de la revisión tramo 2):

- `p50_ms`/`p95_ms`/`p99_ms`/`max_ms`/`mean_ms` — las que se ASSERTEAN — son IN-PROCESS: `journal.py`
  se importa una vez y `capture_end(...)` se cronometra directamente (3 iteraciones de warm-up
  descartadas), sin el coste fijo del arranque del intérprete. Cada iteración medida comprueba
  además que dejó un envelope de verdad (si no, `FALLO: la captura no escribió nada`).
- `e2e_p50_ms` — SOLO informativo, nunca se assertea — es un puñado de subprocesos reales `python3
  journal.py capture-end` (el camino end-to-end que corre `hooks/session-journal.sh` de verdad, con
  el arranque de Python incluido). Un `subprocess.TimeoutExpired` ahí produce un `FALLO`
  estructurado (exit 1), no un traceback.

`ci.yml.MANUAL-COPY` lo ejecuta con los umbrales de CA-02 en cada build, sobre los números
in-process.

### Cómo comprobar los hooks en una sesión real

Los hooks tienen suite automática (`tests/test_hooks_shell.py`: cada `hooks/*.sh` lanzado con `bash`
sobre un proyecto temporal, contrato JSON, debounce, degradación sin `python3`, exit 0). Lo que la
suite **no** puede probar es que Claude Code los registre y muestre; eso se comprueba a mano tras
instalar o actualizar el plugin, en tres pasos (anota el resultado real, no el esperado):

1. **Línea de progreso.** Con una iniciativa `en-progreso`, edita su `docs/roadmap/<slug>/tasks.md`
   (marca un criterio, por ejemplo) → debe aparecer la línea `📋 <slug> · T-XX/N …` como mensaje del
   sistema. Repite la misma edición sin cambiar el estado → silencio (debounce).
2. **Contexto de sesión.** reanuda la sesión (`claude --resume`, o espera a una compactación; `/clear` NO dispara el hook: el matcher es `startup|resume|compact`) → entran como contexto el
   índice de piezas (`Plugin custom-agents — índice de piezas…`, bloques Comandos/Skills/Agentes) y el bloque de
   `progress-report.py session` (iniciativas activas, tarea en curso, «retoma desde…»); con nada activo solo entra el
   índice, y con `dev.json` `sesion.indice: false` solo el roadmap. Prueba de activación: pide algo que case con una
   skill sin nombrarla («revísame este diff») y comprueba que la invoca.
3. **Hook de guardia del implementer.** Como `implementer` (p. ej. `@implementer …`), intenta escribir
   `docs/roadmap/<slug>/spec.md` → debe llegar el **deny** con la razón («solo toca tasks.md…»);
   escribir `tasks.md` o `docs/roadmap/README.md` debe pasar.

Si algún paso no ocurre: `python3 scripts/lint_plugin.py` (commands de `hooks.json` existentes y
ejecutables), `python3 -m pytest -q tests/test_hooks_shell.py` (lógica de los hooks) y, si ambos están
en verde, el fallo está en el registro del hook en Claude Code (versión, `${CLAUDE_PLUGIN_ROOT}`), no
en el plugin.

**En la CI, de forma automática (opcional):** el paso 1 lo cubre el workflow `headless.yml`
(`headless.yml.MANUAL-COPY` → `.github/workflows/headless.yml`; `workflow_dispatch` + lunes 06:00 UTC).
Solo corre si el repo tiene el secret `ANTHROPIC_API_KEY` (los secrets no pueden ir en un `if:` directo:
se pasan a `env` del job y cada paso comprueba `env.ANTHROPIC_API_KEY != ''` — docs.github.com, verificado
2026-09-03); sin secret termina en verde con un aviso. Lanza `claude -p --bare --plugin-dir . --output-format
stream-json` sobre una copia de `evals/fixtures/project/` pidiendo editar el ledger `demo`, y da por
probados los hooks cuando (a) el `system/init` del stream lista el plugin en `plugins` y (b) existe el
**fichero-testigo** `.claude/.progress-last` que escribe `hooks/progress-line.sh` — la evidencia es el
fichero, no un `systemMessage` en la salida, porque la doc de stream-json solo documenta eventos
`hook_started/hook_progress/hook_response` para hooks `SessionStart`/`Setup` y no garantiza que el
`systemMessage` de un `PostToolUse` aparezca. Como la doc tampoco dice si `--bare` ejecuta los hooks de un
plugin cargado con `--plugin-dir`, si con `--bare` el plugin carga pero no hay testigo el job repite SIN
`--bare` y deja constancia (`::warning::`) de en qué modo hubo evidencia. Los pasos 2 y 3 siguen siendo
manuales (una sesión interactiva). Detalle del job: `evals/README.md`.

## Coste del ciclo Jira (por qué lo genera un script)

Con Jira activado, cada tarea produce hasta 6 eventos (`arrancar`, `implementado`, `revision`/`gaps`
por intento, `qa-verde`/`qa-rojo`, `aprobado`). El coste está en **quién redacta el comentario y
compone la llamada**:

| | Antes (prosa en el prompt) | Ahora (`jira-flow.py` + `assets/comment-*.md`) |
|---|---|---|
| Quién redacta el comentario | el modelo, cada vez, leyendo el ledger completo | el script, rellenando una plantilla fija |
| Instrucciones en el prompt del agente | el formato del comentario + reglas de transición + worklog, repetidos en `implementer`, `qa` y la skill de revisión | una línea por agente («dispara el evento X») + la tabla de la Fase 3 de `/dev-cycle`, **una sola vez** |
| Llamadas al conector por evento | improvisadas (a veces una por criterio) | `ops` en orden fijo, agrupadas por tarea (o por fase con `--batch`) |
| Peso de las plantillas | — | **6 plantillas, 1000 bytes en total (`wc -c`) ≈ 245 tokens**, y solo se carga la del evento |

**Medición declarada, no estimada a ojo:** el tamaño de las plantillas y del script está medido
(`wc -c skills/jira-sync/assets/comment-*.md` → **1000 bytes**; `wc -c
skills/jira-sync/scripts/jira-flow.py` → **41 KB** de código que
**no entra en el contexto del modelo**: se ejecuta). **La unidad es la del comando:** `wc -c`
cuenta **bytes**, y con acentos y emojis no coinciden con los caracteres (`wc -m` daría 980, y
encima depende del locale: en `POSIX` cuenta bytes otra vez). Este párrafo decía «727 chars»
citando `wc -c`, que daba 742: la cifra era de caracteres y el comando de bytes (T-fix1).

Lo que **NO** hemos podido medir aquí es el coste en tokens de una sesión real con Jira en vivo (este repo no tiene el conector activado en CI): la
comparación de arriba es estructural (qué entra en el contexto y qué no), no una medición de
sesión. Para medirla en tu proyecto: `usage-meter.py start --artefacto "<slug>/T-XX"` antes del
primer evento y `close` tras `aprobado`.

**Regla de diseño (regla del repo — fila «Determinismo» de `CLAUDE.md` § «Reglas al trabajar
aquí» y regla de cuerpo 1 de la skill `plugin-dev`: «los cálculos y veredictos van en scripts con
tests y exit codes […], no en prosa del agente»; la regla 8 de `CONVENTIONS.md` no la enuncia, es
donde se APLICA al ledger con `ledger-lint`/`qa-gate` —, llevada a la capa de integración):** lo que
puede ser determinista no lo redacta el modelo. Y su corolario en coste de contexto: el patrón de
*un subagente por tarea* lo multiplica, así que el ciclo Jira no lanza ningún subagente — son
llamadas del agente que ya está trabajando.

## Dónde mirar cada cosa (chuleta)

- Coste de una iniciativa (proceso + implementación): `/roadmap-metrics`.
- Estado del roadmap: `/roadmap-status` (local) · `/roadmap-live` (desde Jira).
- Coste real por artefacto: bloque `generacion:` en el frontmatter de spec/eval/plan/tasks.
- Calibración tokens→hora: `docs/roadmap/CALIBRATION.md` (lo alimenta `/retro`).
- Progreso de la iniciativa en curso: la línea de progreso del hook, el contexto de sesión y la statusline opt-in (`progress-report.py line|active|session`).
- Actividad de sesión en vivo, herramientas, subagentes: el monitor externo.

**Cuántos de esos números son de verdad una medida (`fuente: estimado` agregado).** Todo bloque `generacion:` declara `fuente: medido` o `fuente: estimado`, pero suelto no se ve: un `estimado` es una estimación a juicio **con formato de medida**, y en agregado puede ser la mayoría del roadmap sin que nadie lo note (arista E7 de [`docs/agents/CONTRACTS.md`](agents/CONTRACTS.md)). El informe de proceso que produce `build_dashboard.py --metrics-md` —el que consume `/roadmap-metrics`— cierra la tabla con la línea **«N de M bloques `generacion:` con `fuente: estimado`»**, y el `--json` trae las claves aditivas `estimados`, `medidos` y `generacion_total` por iniciativa (el agregado se obtiene sumándolas; el `--json` sigue siendo la misma LISTA de iniciativas de siempre). La cadena sigue en `docs/roadmap/CALIBRATION.md`: una fila cuyo `tokens/hora` no se midió se marca **`(estimado)`** en la celda con su motivo, y `usage-meter.py` la **descarta al calcular la mediana** — sin ese filtro, una fila que heredó el ratio vigente se lo devolvía a la mediana y la calibración se alimentaba de su propia salida.
