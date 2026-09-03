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

## Coexistencia de hooks (verificada)

- **Este plugin** registra hooks **no bloqueantes** (`hooks/hooks.json`) en tres eventos:
  `PostToolUse` (marcar `docs/` pendiente de Confluence, aviso de `ledger-lint` y **línea de
  progreso** sobre `tasks.md`), `SubagentStop` (estado de las iniciativas activas al terminar un
  subagente), `SessionStart` (índice de piezas del plugin + contexto de retoma al
  arrancar/retomar/compactar + última entrada del journal al arrancar/retomar) y `SessionEnd`
  (entrada de bitácora de la sesión en `docs/knowledge/journal/`). No interceptan
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
| Al terminar la sesión (salir, `/clear`, logout) | hook `SessionEnd` → `session-journal.sh` | Nada en pantalla (por contrato la salida de `SessionEnd` se ignora): escribe `docs/knowledge/journal/AAAA-MM-DD-<slug>.md` con `agent-kits/shared/journal.py write` — **borrador determinista** (fecha, iniciativa activa, ficheros tocados por git, tareas del ledger que cambiaron de estado, marcadores del meter cerrados, primer prompt como resumen) e idempotente por `session_id`. Al arrancar/retomar (`startup\|resume`, no `compact`) `session-context.sh` añade (3) la última entrada compactada (≤ 25 líneas, `journal.py latest`). Desactivable con `dev.json` `{"sesion": {"journal": false}}`. **Sin resumen por IA**: la doc oficial (hooks.md, 2026-09-03) solo deja a los hooks `prompt`/`agent` devolver una decisión `ok/reason`, y en `SessionEnd` toda salida se ignora; `journal.py write --enrich` queda para uso manual. Presupuesto: los hooks de `SessionEnd` comparten 1,5 s → `hooks.json` declara `timeout: 20`. |
| Siempre, en la barra de estado (**opt-in** en `/setup`, paso 5-bis) | `statusline/roadmap-statusline.sh` | `[Opus] $0.01 ctx 8% · 📋 <slug> T-04/12 33%` — modelo, coste de la sesión, contexto usado y progreso del roadmap. Sin `jq` usa `python3`; sin ninguno, solo el modelo. |

Reversión de la statusline: quitar la clave `statusLine` de `.claude/settings.json`.

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

**Regla de diseño (la misma que superpowers aplica a sus skills, llevada a la integración):** lo que
puede ser determinista no lo redacta el modelo. Superpowers no tiene integración con herramientas de
gestión, así que aquí no hay nada que copiar — sí hay algo que no repetir: su patrón de *un subagente
por tarea* multiplica el contexto; el ciclo Jira no lanza ningún subagente, son llamadas del agente
que ya está trabajando.

## Dónde mirar cada cosa (chuleta)

- Coste de una iniciativa (proceso + implementación): `/roadmap-metrics`.
- Estado del roadmap: `/roadmap-status` (local) · `/roadmap-live` (desde Jira).
- Coste real por artefacto: bloque `generacion:` en el frontmatter de spec/eval/plan/tasks.
- Calibración tokens→hora: `docs/roadmap/CALIBRATION.md` (lo alimenta `/retro`).
- Progreso de la iniciativa en curso: la línea de progreso del hook, el contexto de sesión y la statusline opt-in (`progress-report.py line|active|session`).
- Actividad de sesión en vivo, herramientas, subagentes: el monitor externo.
