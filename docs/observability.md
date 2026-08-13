# Observabilidad — qué mide este plugin y cómo convive con monitores de sesión

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

- **Este plugin** registra hooks `PostToolUse` **no bloqueantes** (`hooks/hooks.json`): marcar
  `docs/` pendiente de Confluence y el aviso de `ledger-lint` sobre `tasks.md`. No interceptan
  ni modifican nada; solo observan y avisan.
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

## Dónde mirar cada cosa (chuleta)

- Coste de una iniciativa (proceso + implementación): `/roadmap-metrics`.
- Estado del roadmap: `/roadmap-status` (local) · `/roadmap-live` (desde Jira).
- Coste real por artefacto: bloque `generacion:` en el frontmatter de spec/eval/plan/tasks.
- Calibración tokens→hora: `docs/roadmap/CALIBRATION.md` (lo alimenta `/retro`).
- Actividad de sesión en vivo, herramientas, subagentes: el monitor externo.
