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
  subagente) y `SessionStart` (contexto de retoma al arrancar/retomar/compactar). No interceptan
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
| Al arrancar, retomar o tras compactar el contexto | hook `SessionStart` → `session-context.sh` | Bloque ≤ 15 líneas inyectado como contexto: iniciativas activas, tareas en curso, marcadores abiertos del usage-meter y «retoma desde la tarea en-progreso». Sin nada activo, no inyecta nada. |
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
2. **Contexto de sesión.** reanuda la sesión (`claude --resume`, o espera a una compactación; `/clear` NO dispara el hook: el matcher es `startup|resume|compact`) → el bloque de
   `progress-report.py session` (iniciativas activas, tarea en curso, «retoma desde…») entra como
   contexto; con nada activo, no entra nada.
3. **Hook de guardia del implementer.** Como `implementer` (p. ej. `@implementer …`), intenta escribir
   `docs/roadmap/<slug>/spec.md` → debe llegar el **deny** con la razón («solo toca tasks.md…»);
   escribir `tasks.md` o `docs/roadmap/README.md` debe pasar.

Si algún paso no ocurre: `python3 scripts/lint_plugin.py` (commands de `hooks.json` existentes y
ejecutables), `python3 -m pytest -q tests/test_hooks_shell.py` (lógica de los hooks) y, si ambos están
en verde, el fallo está en el registro del hook en Claude Code (versión, `${CLAUDE_PLUGIN_ROOT}`), no
en el plugin.

## Dónde mirar cada cosa (chuleta)

- Coste de una iniciativa (proceso + implementación): `/roadmap-metrics`.
- Estado del roadmap: `/roadmap-status` (local) · `/roadmap-live` (desde Jira).
- Coste real por artefacto: bloque `generacion:` en el frontmatter de spec/eval/plan/tasks.
- Calibración tokens→hora: `docs/roadmap/CALIBRATION.md` (lo alimenta `/retro`).
- Progreso de la iniciativa en curso: la línea de progreso del hook, el contexto de sesión y la statusline opt-in (`progress-report.py line|active|session`).
- Actividad de sesión en vivo, herramientas, subagentes: el monitor externo.
