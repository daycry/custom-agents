# Observabilidad — qué mide este plugin y cómo convive con monitores de sesión

[English](en/observability.md) · **Español**

El launcher de `SessionStart` conserva la identidad `session-context.sh`, pero
ejecuta `session-context.py` sin Bash. Importa los servicios de journal, índice,
progreso y memoria en el mismo intérprete, conserva el orden y los topes del
contexto y fuerza `--ia no` durante replay. En Windows sigue usando el supervisor
y su cierre de procesos. La invocación directa del shell anterior permanece
disponible. El timeout se mantiene hasta completar su validación medida.

El marcador de documentación pendiente (`.claude/.confluence-pending`) se crea
directamente en el launcher Node para los tres runtimes, sin Python ni shell.
Conserva los filtros de `docs/` y excluye `docs/security-scan/` y `docs/confluence/`.
El marcador es un fichero vacío; entradas inválidas, enlaces observados y fallos
de escritura producen un diagnóstico sin bloquear la edición. Un fichero existente
con contenido se conserva y se avisa. La invocación directa del wrapper shell
antiguo sigue disponible como compatibilidad.

Los edits de un ledger usan un solo hook de validación y progreso. Lee y analiza
el ledger una vez y ejecuta un Python de negocio (más el supervisor en Windows).
Lint informa en cada llamada; el progreso idéntico se emite una sola vez bajo
cerrojo sobre `.claude/.progress-last.lock`, con actualización atómica de
`.claude/.progress-last`. Los wrappers separados siguen disponibles. El hook
solo consulta ledgers del proyecto y rechaza enlaces observados; si no puede
guardar el debounce, avisa y emite el progreso, que puede repetirse.
Los mensajes emitidos y la línea de progreso guardada pasan por el redactor
canónico, también cuando un título del ledger contiene una credencial.

El lector de memoria carga su detalle gobernado cuando el proyecto consumidor
tiene `docs/knowledge/`; la condición incluye tanto legado como approved y no
depende de un backend remoto. El journal, el contexto de código y la doctrina
de estimación del plugin conservan sus reglas propias. Sin esa carpeta se lee
solo el núcleo; con ella se leen núcleo y referencia, por lo que no se atribuye
ahorro de texto a ese segundo caso.

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

SessionStart declara `timeout: 30` en `hooks/hooks.json` y en el manifiesto
regenerado de Codex. Cuando C-06 unifique el arranque en un solo Python se
revisará su bajada a 10 s. El launcher compartido conserva su presupuesto
interno de 20 s para contexto; el adaptador nativo de OpenCode también tiene
su propio límite de 20 s. El timeout de registro no amplía esos límites.
`UserPromptSubmit` invoca `journal.py capture` con `-I -S`: mantiene el log,
la redacción y los opt-outs sin cargar paquetes del consumidor.

Al reconstruir el índice de conocimiento se barren solo sus temporales
`knowledge-index.sqlite.<pid>.tmp` y `-journal`: ambos deben tener al menos
una hora y el PID debe estar confirmado como muerto. PIDs vivos, dudosos o
ficheros recientes se conservan. Se rechazan enlaces, junctions y nombres
ajenos; la limpieza es local al directorio del índice y un fallo de E/S avisa
sin impedir reconstruirlo. El `finally` limpia el temporal y el journal propios.

La barra de estado usa como máximo un Python aislado por refresco. Con la
misma entrada y metadatos de ledgers sin cambios, sirve los campos desde
`.claude/statusline-cache` sin Python. Cambios de coste/contexto, ledgers,
usage-state o scripts invalidan la caché; no guarda la entrada JSON cruda.
Se respeta `CUSTOM_AGENTS_PYTHON`, se excluyen alias de WindowsApps y, sin
intérprete o ante un error, queda el modelo y exit 0. El formato y redondeo
siguen en Bash; no se necesita `jq`. El comando de `/setup` no cambia.

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
| Cuando el runtime emite el cierre | hook `SessionEnd` → `session-journal.sh` (exec form, `timeout: 5`) | El launcher invoca `journal-capture.py`: escribe solo un **envelope atómico** (≤ 64 KiB, identidad determinista, sin materializador/git/IA/red) en la outbox local. El benchmark in-process mide la operación, excluyendo arranque y presupuesto nativo; no demuestra la latencia total del hook. |
| Al arrancar/retomar/compactar | hook `SessionStart` → `session-context.sh` (además de lo de la fila de arriba, `SessionEnd`) | **Reconciliación presupuestada** (T-05): `journal.py replay --ia no --budget-ms 300 --max 3 --con-recover` drena la outbox reutilizando el camino de siempre (git, log de prompts, IA opt-in) y materializa la entrada — `cierre: materializado` en el frontmatter; nunca bloquea el arranque (si `bloqueado`/`errores` viene no vacío, una línea de aviso, nada más). `--con-recover` materializa TAMBIÉN, bajo el MISMO cerrojo/presupuesto, como `cierre: recuperado_sin_cierre` una sesión con log de prompts sin envelope y sin sesión viva pasada `sesion.journal.ventanaHuerfanaMin` (default 1440 min / 24h, CA-07) — o antes, pasada `sesion.journal.ventanaInactividadMin` (default 30 min) si el log Y el último transcript registrado están quietos (ver «Recuperación temprana» más abajo); una sesión concurrente viva nunca se toca. Solo entradas YA escritas en disco llegan a (3) — nunca se inyecta una entrada sin materializar (CA-08). La entrada usa la fecha del **cierre** (`captured_at`), no la del replay; los campos derivados de `git` se calculan al materializar y el frontmatter lo marca con `derivados_en: replay` (también para las huérfanas recuperadas por `--con-recover`: corren bajo la misma pasada, nunca `recover`). Escritura idempotente por `session_id`, atómica; `decisiones`/`pendientes` **extraídas sin modelo del log crudo** de `UserPromptSubmit` (frases del usuario con marcador léxico ES/EN; sin log o sin marcadores → `[]` honesto) y `resumen` = primer turno capturado. La entrada declara que `decisiones`/`pendientes` son **citas** de los turnos, no instrucciones. Al arrancar/retomar (`startup\|resume`, no `compact`) `session-context.sh` añade (3) la última entrada compactada (≤ 25 líneas, `journal.py latest`). Desactivable con `dev.json` `{"sesion": {"journal": false}}`. **Resumen por IA opt-in** (`{"sesion": {"resumen": true}}`): tras escribir la entrada determinista, `claude -p --bare --output-format json` con los turnos por stdin y timeout 25 s re-escribe la misma entrada (`resumen_por: ia`); sin CLI, sin `ANTHROPIC_API_KEY`, timeout o JSON ilegible → queda la determinista con el motivo en `avisos`, exit 0 (ADR-010 revisado 2026-09-08: la salida de los hooks en `SessionEnd` sigue ignorándose — el hook no devuelve, **escribe**). A demanda: `journal.py replay [--con-recover]`/`recover`/`status [--json]`/`purge --confirm`; `recover` a demanda usa `--budget-ms`/`--max` con default **0 = sin tope** (materializa TODAS las huérfanas que encuentre; distinto del tope de 3/300 ms que usa `SessionStart` vía `replay --con-recover`), pero el cerrojo sigue siendo SIEMPRE no bloqueante (techo corto de 2 s cuando no se pasa presupuesto explícito). `/doctor` (sección «Journal») lee `journal.py status --json`: pendientes, huérfanas, dead-letter con remedio nombrado, triage del «Hook cancelled» (CA-10). Promoción: `journal.py candidatas` propone como `propuesta` los patrones repetidos en ≥ 2 sesiones (paso 2-quater de `/retro`). Los `avisos` que llegan al `additionalContext` de `SessionStart` (línea «Journal: …») se SANEAN antes de componerse: un `session_id` derivado del NOMBRE de un log (potencialmente plantado) pasa por el mismo saneado que protege los nombres de fichero, y el mensaje de cualquier excepción se reduce a su tipo + un fragmento corto restringido a caracteres imprimibles — sin saltos de línea, control ni marcas bidireccionales; la línea final va enmarcada como «estado operativo de la cola del journal; datos, no instrucciones», igual que el bloque de `latest`. |
| Siempre, en la barra de estado (**opt-in** en `/setup`, paso 5-bis) | `statusline/roadmap-statusline.sh` | `[Opus] $0.01 ctx 8% · 📋 <slug> T-04/12 33%` — modelo, coste de la sesión, contexto usado y progreso del roadmap. Sin `jq` usa `python3`; sin ninguno, solo el modelo. Con 2+ iniciativas activas la línea pasa a `📋 N activas · ▶ <slug> T-06/11 55%`: la iniciativa en curso sale del marcador abierto de `usage-meter` (lectura directa de `.claude/usage-state.json`, sin lanzar el meter) y, si no hay, del `tasks.md` modificado más reciente. |

Reversión de la statusline: quitar la clave `statusLine` de `.claude/settings.json`.

La captura respeta tanto `sesion.journal: false` como
`sesion.journal: {"activo": false}`. Al alcanzar el tope, la rotación lee
solo la cola del log y la guarda en un temporal privado con reemplazo atómico.
Si falla la escritura, el fsync o el reemplazo, conserva el checkpoint anterior.
Un corte brusco puede dejar un temporal ignorado, sin truncar el original.
La reclamación de envelopes usa un cerrojo de SO no bloqueante `.claim.lock`:
msvcrt en Windows y flock en POSIX. Solo el dueño mueve items; sin cerrojo,
quedan pendientes. La existencia del fichero no significa que esté ocupado.
Se rechazan enlaces y se comprueba la identidad del descriptor antes de
bloquearlo. Un fallo de la transacción se comunica al llamador para su
diagnóstico; no se confunde con una cola vacía.
Las salidas CLI de `journal.py write` e `index` usan rutas relativas con `/`
también en Windows.

El timeout declarado de 5 s no demuestra que un hook de plugin Claude
disponga de ese tiempo: el presupuesto de cierre es 1,5 s por defecto y los
timeouts de plugins no lo amplían. Los números del benchmark in-process no
incluyen el arranque del launcher/runtime. El despacho y tiempo total deben
comprobarse por runtime antes de atribuir una garantía nativa de captura.
[Contrato oficial de SessionEnd](https://code.claude.com/docs/en/hooks#sessionend-input).

El launcher ejecuta la captura con Python aislado (`-I -S`) y el helper
canónico `journal-capture.py`; `journal.py capture-end` reutiliza ese escritor.
Así, el cierre no carga el materializador ni depende de paquetes de Python
del consumidor. El trabajo hijo dispone de 800 ms en Claude y 2.200 ms en
Codex/OpenCode, seleccionados por un argumento literal del adaptador. Al
agotar el tiempo, el launcher termina su árbol de procesos y espera el cierre;
el log de prompts retenido permite `recover`.

En Windows, `runtime-supervisor.py` incorpora el intérprete a un Job Object
antes de ejecutar el negocio. El handle no heredable pertenece a Node:
terminar solo el launcher cierra el job y alcanza los descendientes aunque
Python ya haya salido. Un fallo de contención omite el hook con aviso.
En POSIX, el adaptador posee el grupo del launcher; la limpieza comprueba
esa propiedad, detiene y termina sus miembros hijos y conserva vivo al dueño.
Los demás lanzamientos usan su propio grupo. La confirmación de cierre tiene
un límite adicional de 500 ms y no garantiza planificación inmediata del SO.
El helper `close` carga solo lo necesario para confirmar el Job Object. Los
ejecutores `runpy` y `subprocess`, y el serializador `json`, se cargan en las
operaciones que los usan, para no gastar el plazo de limpieza en inicializarlos.
[Contrato de Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

La prueba headless del payload supervisado de Claude 2.1.287 conservó contexto,
UTF-8 y envelope sin aumentar su presupuesto, comprobado al observar la
salida del proceso padre. Su log nativo confirma `SessionEnd` con status 0;
el stream no emite respuesta para ese evento. El arranque del SO queda fuera del
deadline interno: no se garantiza menos de 1,5 s en todos los equipos.
[Evidencia y límites](roadmap/2026-10-07-catalog-capabilities/claude-hook-evidence.json).

**Recuperación temprana por inactividad.** En Windows la captura de `SessionEnd`
no cabe en ese presupuesto (arrancar el launcher ya lo supera), así que la
sesión suele quedar huérfana: hay log de prompts, pero ni envelope ni entrada.
Con la ventana de 24 h, el arranque siguiente no la veía hasta un día después.
Por eso `journal.py capture` guarda en cada turno del log local (no versionado)
la ruta del transcript, solo si pasa `_transcript_seguro`: absoluta,
`<session_id>.jsonl`, sin symlink y bajo `~/.claude/projects` o
`$CLAUDE_CONFIG_DIR/projects`. `recover` lee la cola acotada del log, toma la
última ruta y hace un `stat`. Si el transcript y el log llevan más de
`sesion.journal.ventanaInactividadMin` sin cambiar (default 30, mínimo 1), la
sesión se recupera ya. Sin transcript válido rige la ventana de 24 h. La sesión
que arranca nunca se toca. La entrada recuperada guarda `log_hasta` (mtime UTC
del log usado; nunca la ruta del transcript). Si la sesión sigue y el log cambia
después, la próxima pasada la vuelve a recuperar y sobrescribe esa misma
entrada. Una entrada `materializado` nunca se reabre ni se degrada.

### Contrato de garantías de la captura durable de `SessionEnd`

`SessionEnd` deja un envelope atómico; `SessionStart` (o `journal.py replay`/`recover` a demanda)
hace la materialización real. La tabla dice qué garantiza CADA forma de terminar la sesión — y qué
**no** garantiza nadie:

| Forma de salida | Garantía |
|---|---|
| Runtime emite `SessionEnd` y la captura termina | Envelope durable en la outbox; journal materializado en el siguiente `SessionStart` o a demanda (`journal.py replay`). Cada forma de salida necesita prueba nativa por runtime. |
| Ctrl+C / terminal cerrada / proceso muerto antes de que corra el hook | Recuperación hasta el **último prompt capturado** por `UserPromptSubmit` (el log de prompts es el checkpoint): `journal.py recover` la materializa como `cierre: recuperado_sin_cierre` pasada la ventana (`sesion.journal.ventanaHuerfanaMin`, default 1440 min / 24h), o pasada `sesion.journal.ventanaInactividadMin` (default 30 min) si el log y el último transcript registrado no cambian; si la sesión sigue después, la entrada se rehace. |
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
  journal.py capture-end` (CLI de compatibilidad, con arranque de Python incluido; excluye el
  launcher Node y el presupuesto nativo). Un `subprocess.TimeoutExpired` ahí produce un `FALLO`
  estructurado (exit 1), no un traceback.

`ci.yml.MANUAL-COPY` lo ejecuta con los umbrales de CA-02 en cada build, sobre los números
in-process.

### Prefiltro de la guardia nativa

`run-hook.mjs` comprueba el mapa generado `native-roles.json` antes de buscar
Python. Con un mapa válido y una identidad nativa ausente o no protegida, termina
con el mismo resultado de continuación sin arrancar Python. La comparación es
exacta: `agent_type` en Claude/Codex y `agent` en OpenCode; no acepta prefijos,
normalizaciones ni identidades tomadas de los argumentos de herramientas.

Las identidades protegidas y los mapas, codificaciones o payloads dudosos pasan
al evaluador Python. La entrada se limita a 64 KiB, como el evaluador, y la lectura
y evaluación comparten el presupuesto con reloj monotónico. El prefiltro no emite
denegaciones; las decisiones de política siguen en Python.

El adaptador persistente de OpenCode relee el mapa por invocación. Un mapa
inválido deja llegar al diagnóstico del evaluador; no se conserva una selección
obsoleta de identidades. La validación del mapa está replicada de forma declarada
en `copias.json`, con igualdad de bytes y paridad con los roles protegidos de Python.

La medición del launcher incluye el arranque de Node. Evitar procesos Python no
implica una reducción fija de latencia total. La comparación local de T-02 y el
control de arranque están en la carpeta de pruebas de `plugin-optimization`.

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

## Agentes en vivo: captura de herramientas (opt-in)

El panel servido (`/plugin-catalog --serve`) tiene una página **Agentes en vivo** que responde, de forma
acotada y local, a la pregunta que antes solo cubría un monitor externo: qué herramientas ha usado cada run.
Es **opt-in** y **informativa**: no decide nada ni sustituye a un monitor de sesión.

| Qué | Cómo |
|---|---|
| Activarla | `{"sesion": {"actividad": true}}` en `.claude/dev.json` (sin sustituir el resto de la configuración). Ausente, `false`, ilegible, mayor de 64 KiB o con JSON inválido = desactivada. |
| Qué se registra | Un evento por herramienta terminada: hora, herramienta, resumen del argumento (≤ 160 caracteres, lista blanca por herramienta, redactado y anonimizado), `T-XX` si se pudo atribuir, duración y resultado (`ok`/`error`). Nunca contenido de ficheros, salidas, prompts, chain-of-thought ni rutas absolutas. |
| Atribución a una tarea | Solo por el comando exacto del medidor (`usage-meter.py start\|close --artefacto <slug>/T-XX`) en un evento Bash/shell; un `T-07` en un commit, un grep o un prompt nunca atribuye. Un evento a menos de 5 s de un cambio de ventana queda «sin atribuir». |
| Coste | Los grupos `PostToolUse` y `PostToolUseFailure` de `agent-activity` son `async`: 0 ms síncronos añadidos en Claude Code y Codex (excepción: las herramientas MCP de Codex, que el runtime ejecuta en síncrono; ahí el almacén hace un único intento sin espera). Sin el opt-in, el launcher Node sale antes de arrancar Python: unos 80 ms en segundo plano (medido el 2026-10-20 en Windows, p50 78 ms). En OpenCode el adaptador no espera al proceso hijo. |
| Topes | Historial de 500 eventos o 256 KiB (lo que llegue antes) y 24 h; al superarlo se descarta el más antiguo y se cuenta en `recortado`. Una entrada de más de 2 MiB no se lee: solo suma `descartados_por_tamano`. |
| Esperas | Un evento de herramienta espera el cerrojo hasta 1 s dentro de un plazo de 1,3 s (`TOOL_LOCK_WAIT`/`TOOL_DEADLINE`, `agent-kits/shared/agent-activity-store.py:36-37`), en segundo plano. Las señales de ciclo de vida (`SubagentStart`/`SubagentStop`) esperan 100 ms dentro de 1 s y pasan primero: anuncian su espera en el byte 1 de `.lock` y los eventos de herramienta les ceden el turno. La prioridad impide que entren nuevos escritores, pero no interrumpe uno que ya tiene el cerrojo: si su retención supera los 100 ms, la señal puede devolver `state_busy`. Las herramientas MCP de Codex hacen un único intento sin espera. Decisión y medidas: `design.md` §2.5 de la iniciativa `panel-redesign`. |
| Huecos | Un evento que no se pudo escribir (cerrojo ocupado, escritura cortada) se pierde y no se reintenta (`state_busy`); la página lo avisa siempre («captura informativa: puede tener huecos»). Pérdida medida en una ráfaga con el anillo lleno: 8 escritores en paralelo, 0 perdidos; 12, 0-2; 16, 1-5. Los eventos se listan en orden de recepción, no de ejecución. |
| Cerrojo | `agent-kits/shared/local-state.py` usa dos bytes de `.lock`: el 0 excluye a otros escritores y el 1 es la intención del ciclo de vida. En POSIX ambos son `fcntl.lockf` de un byte (un solo tipo: mezclar `flock` y `lockf` sobre el mismo fichero hace que un proceso se bloquee a sí mismo en macOS/BSD y en NFS); en Windows, `msvcrt.locking`. |
| Redacción | El resumen del argumento pasa por `agent-kits/shared/redact.py` antes de escribirse. Además de claves y tokens, tapa las credenciales de `curl -u/--user/--proxy-user` y de `mysql*`/`mariadb* -p/--password=` cuando el programa aparece antes en el mismo comando: también dentro de comillas (`sh -c "…"`, `ssh host '…'`) y tras `sudo`, `--`, `timeout`, `xargs` o `$(`. Ante la duda, tapa de más. |
| Desactivarla | `sesion.actividad: false` (o quitar la clave): no se escribe nada más (a lo sumo las escrituras que ya estaban en vuelo, ≤ 2 s). Al reactivarla, las ventanas de atribución abiertas caducan. |
| Borrar el historial | El panel **nunca** borra. Para borrarlo, borra a mano el directorio `.claude/agent-activity/` del proyecto (con la captura desactivada o sin sesiones en curso); la siguiente captura lo recrea. Es también el remedio si la página dice «historial no disponible (`invalid_state`)» o `unowned_state`. |

El estado vive en `.claude/agent-activity/` (dueño: `agent-kits/shared/agent-activity-store.py`), con su
propio `.gitignore`. Lo que aporta cada runtime está en [`INTEROP.md`](INTEROP.md) §4; la página la describe
[`PLUGIN-PANEL.md`](PLUGIN-PANEL.md) («Agentes en vivo»).

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
- Actividad de sesión en vivo, herramientas, subagentes: el monitor externo. Una vista acotada y opt-in de las herramientas por run: Agentes en vivo del panel servido (`sesion.actividad: true`).

**Cuántos de esos números son de verdad una medida (`fuente: estimado` agregado).** Todo bloque `generacion:` declara `fuente: medido` o `fuente: estimado`, pero suelto no se ve: un `estimado` es una estimación a juicio **con formato de medida**, y en agregado puede ser la mayoría del roadmap sin que nadie lo note (arista E7 de [`docs/agents/CONTRACTS.md`](agents/CONTRACTS.md)). El informe de proceso que produce `build_dashboard.py --metrics-md` —el que consume `/roadmap-metrics`— cierra la tabla con la línea **«N de M bloques `generacion:` con `fuente: estimado`»**, y el `--json` trae las claves aditivas `estimados`, `medidos` y `generacion_total` por iniciativa (el agregado se obtiene sumándolas; el `--json` sigue siendo la misma LISTA de iniciativas de siempre). La cadena sigue en `docs/roadmap/CALIBRATION.md`: una fila cuyo `tokens/hora` no se midió se marca **`(estimado)`** en la celda con su motivo, y `usage-meter.py` la **descarta al calcular la mediana** — sin ese filtro, una fila que heredó el ratio vigente se lo devolvía a la mediana y la calibración se alimentaba de su propia salida.

**Procedencia y cobertura de cada cierre del meter.** `usage-meter.py close` añade claves planas que separan lo medido de lo estimado: `tokens_procedencia` (`transcript` · `sin_medida`), `tokens_cobertura` (`completa` · `parcial` si un transcript no se pudo leer o un `usage` no era numérico · `sin_medida`), `transcripts_leidos`/`transcripts_subagente`/`transcripts_con_error`, `coste_procedencia` (`estimado_tarifa` · `sin_coste`), `coste_cobertura` (`completa` · `incompleta` si alguna clase de token con tokens no tiene precio y se valoró a 0 · `sin_coste`), `coste_sin_precio` y `tarifa_verificada_el`. `eur` es siempre tokens × `precioTokens`, nunca una factura; `sin_medida` y `sin_coste` no equivalen a cero. Copiadas al bloque `generacion:`, `build_dashboard.py` las agrega: el informe de proceso de `/roadmap-metrics` añade la columna **Procedencia** por iniciativa y la línea **«Procedencia (cartera)»** (tokens medidos por transcript con cobertura completa/parcial · sin medida · procedencia desconocida; coste estimado completo · incompleto con sus clases sin precio · sin coste · desconocido, con cuántos artefactos aporta cada caso), la tarjeta de `/roadmap-status` muestra «Medición», y el `--json` trae la clave aditiva `procedencia` por iniciativa (`tokens`, `coste`, `transcripts`, `tarifas_verificadas_el`; el total de cartera es su suma). Un bloque antiguo sin esas claves cuenta como **procedencia desconocida**, nunca como medido aunque diga `fuente: medido`; lo ausente es `null`, nunca 0. Los tokens por procedencia suman solo las ventanas que ya suma el total de la fila (una ventana compartida cuenta una vez).

**Inventario de automatizaciones en `/doctor`.** La sección «Automatizaciones» (clave `automatizaciones` del `--json`) lista hooks, statusline y workflows de `.github/workflows/` con fuente, alcance, fecha de la configuración, estado (`configurado` · `no_configurado` · `no_cargado` · `roto`) y firma de fallo. `ejecucion` es siempre `no_verificada`: para saber si un hook corre de verdad, mira su efecto (la entrada del journal, la línea de progreso), no esta tabla.

**Continuidad y candidatas del journal.** Con `journal.py write --enrich`, una sesión puede declarar `objetivo`, `punto_actual`, `siguientes_pasos`, `bloqueos` y `descartados` (enfoques que ya fallaron, «enfoque — motivo»); al reescribir la misma sesión, la clave omitida conserva su valor y la vaciada (`""`, `[]`, `null`) se limpia. `latest` y `select` las muestran como citas. `journal.py candidatas` añade a cada candidata un `id` estable y una `categoria` léxica (`correccion_usuario`, `resolucion_error`, `workaround`, `tecnica_depuracion`, `convencion`, `otra`); `--lote` devuelve un cursor e id de lote, `--hasta <cursor>` reproduce ese lote aunque lleguen entradas nuevas (contadas en `posteriores_al_cursor`) y `--confirmar <id>` comprueba que es el mismo, sin marcar nada como procesado.

## Benchmark reproducible de hooks y tokens

`python scripts/bench-hooks.py --runs 10 --warmup 1 --json` genera un informe
estructurado; `--md` presenta el mismo esquema en tabla. Ejecuta cada registro de
`hooks/hooks.json` con fixtures versionadas de Claude, Codex y OpenCode, usando
`hooks/run-hook.mjs --runtime=...` directamente, sin evaluar comandos de shell.
Es una medida end-to-end del launcher compartido, incluido el arranque de sus
procesos, no una prueba de que cada runtime dispare esos eventos. En particular,
los registros canónicos `PostToolUseFailure` se ejercitan también con selector
Codex; eso no significa que Codex ofrezca ese evento.

Cada iteración usa un proyecto temporal nuevo con un ledger mínimo. Su creación y
limpieza quedan fuera del cronómetro; `CLAUDE_PROJECT_DIR`, `cwd` y las rutas del
payload apuntan al temporal. El benchmark no escribe en el proyecto consumidor.
Se mide el guard sin identidad protegida y actividad desactivada, tal como indica
la fixture; no se mide el coste del almacén de actividad opt-in. La captura de
prompts usa texto inventado y no se habilitan resúmenes por IA ni red.

Por registro/runtime se conservan las muestras, mediana, p95 interpolado y máximo.
El calentamiento se ejecuta pero se descarta. Un fallo de proceso, timeout o
aviso de degradación del launcher produce `FALLO`, sin una mediana de éxito, y
exit 1. En captura de prompts y SessionEnd se verifica además el registro persistido
fuera del cronómetro; un no-op silencioso también falla. `linea_base` solo es verdadero para una pasada completa correcta con
al menos diez muestras por caso y una iteración de calentamiento descartada. Exit 2 indica argumentos inválidos.
`--runtime codex --hook native-guardrail` permite comparar una mejora concreta;
`--runs 3` sirve para smoke, y `--tokens-only` calcula solo el inventario textual.
`--fail-fast` detiene la pasada ante el primer caso fallido y conserva sus muestras
y diagnóstico. `casos_ejecutados` y `casos_previstos` hacen visible la cobertura
de la pasada en JSON y Markdown; una pasada incompleta no es línea base.

`tokens_fijos` separa descriptions de agentes/skills/comandos e índice de
SessionStart por runtime, reutilizando el parser y generador de `skill-index.py`
sin escribir caché. `tokens_bajo_demanda` cuenta `dev-cycle.md` y
`knowledge-check.md`. El método es **estimación caracteres/4 con redondeo superior**:
no utiliza un tokenizador, no mide consumo facturado y no representa todo el
prompt del runtime. El inventario de piezas y caracteres acompaña a la estimación.

Para caracterizar la línea base: tres pasadas completas correctas, conservando JSON
y Markdown, muestras y calentamientos descartados. Registrar fuentes, SO, RAM libre
observada, fecha y si el código está en OneDrive; declarar la dispersión entre las tres
medianas por registro/runtime sin afirmar estabilidad uniforme. Para evaluar cada mejora
temporal: control antes/después intercalado del mismo workload, equipo, fixtures e
intérpretes, con fuentes identificadas, control de arranque, dispersión y fallos. Una
comparación inconcluyente no acredita ahorro global; un fallo no es una muestra de éxito.
No atribuir al cambio el ruido de la máquina. Los temporales están en el directorio temporal del sistema, no en
OneDrive. La CI comprueba el contrato con relojes y procesos controlados, sin
umbrales absolutos de latencia. La línea base local no se extrapola a otros equipos.

### Lecturas condicionales y procesos en F2

`tokens_bajo_demanda` es un inventario de los ficheros indicados, no el coste de
una ejecución completa. Los núcleos de dev-cycle y knowledge-check cargan detalle
bajo condiciones: el flujo completo, Jira/subagentes/candidatos o la presencia de
memoria local cambian el readset. Las comparaciones por escenario de T-11/T-13 en
`docs/roadmap/2026-10-27-plugin-optimization/testing/` conservan esos costes,
incluidos los escenarios que añaden texto. No sumes un núcleo y su versión antigua
ni atribuyas el ahorro de la vía rápida a todas las configuraciones.

El hook combinado del ledger comparte lectura/análisis y conserva lint en cada
llamada. MultiEdit admite una ruta superior con ediciones de contenido, o rutas
por edición; el progreso elige el primer ledger que no esté repetido. SessionStart
compone el contexto en un Python de negocio y mantiene su timeout de 30 s.
En Windows sigue habiendo supervisión y confirmación de limpieza mediante un
helper: «un Python de negocio» no significa «un proceso total». El spike de T-15
no acreditó una alternativa equivalente; no se reduce ese margen de limpieza.
