# Comandos de sesión y de documentación — C079, C085, C087, C092, C093

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco definiciones completas: **38.250 bytes/959 líneas**. [commands-c4-session-docs-reading-evidence.json](commands-c4-session-docs-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Sesión: C079, C085, C087

Los tres ya tienen comparación propia en
[commands-session-continuity.md](commands-session-continuity.md) y fila en
[operational-panel-commands.md](operational-panel-commands.md) (línea 64). Allí
se fijó la prioridad P1, «retoma dirigida bajo demanda» sobre journal y ledger,
sin otro almacén ni aliases globales. Esa decisión **ya está entregada**:
`/work-resume` (`commands/work-resume.md`, contrato en `docs/WORK-RESUME.md`)
compone ledger actual + journal con identidad exacta y sin sustitución
(`WORK-RESUME.md:29-41`), y D-085 dio esquema a la continuidad
(`agent-kits/shared/journal.py:239-247`: `objetivo`, `punto_actual`,
`siguientes_pasos`, `bloqueos`). Esta ficha no repite el análisis; añade
artefactos, dueños y escenarios, y señala el único campo que sigue sin dueño.

| Artefacto de la fuente | Dueño propio |
|---|---|
| `~/.claude/session-data/<fecha>-<id>-session.tmp`, global y escrito por el modelo a petición (C085:29-37) | Entrada de `docs/knowledge/journal/` escrita por el hook `SessionEnd` con `journal.py`, determinista e idempotente por `session_id` (ADR-010) |
| `~/.claude/session-aliases.json` (C087:337) | Ninguno: los aliases globales se rechazaron (escritura que borra el destino antes del rename en Windows) |
| Briefing de C079 en conversación | Vista de `/work-resume` (`progress-report.py resume`), solo lectura |

## C079 — resume-session

`8.105 bytes/181 líneas` · tools: no declara · model: no declara. Carga el fichero
de sesión más reciente (o el indicado) y da un briefing fijo con «WHAT NOT TO
RETRY»; espera instrucciones.

- **Despacho:** ninguno; lectura del fichero.
- **Disparador:** «retoma la sesión de ayer».

**Comparación.** Cubierto por `/work-resume`: selección explícita sin sustitución
(C079:48-49 ↔ `WORK-RESUME.md:36`), ledger primero y citas después
(`WORK-RESUME.md:44-52`), y el usuario decide (`commands/work-resume.md`, último
párrafo). Lo que `/work-resume` no puede mostrar es «WHAT NOT TO RETRY»
(C079:92-93, :180), porque el journal no tiene ese campo (ver C085).

Escenarios: **positivo** «retoma esta iniciativa donde quedó» → `/work-resume`;
**negativo** «aprueba esta decisión como doctrina» → `knowledge-curator`.

**Destino:** **Sin destino.** Ya integrado en `/work-resume`.

## C085 — save-session

`9.702 bytes/275 líneas` · tools: no declara · model: no declara. Escribe a mano un
fichero de sesión con lo que funcionó (con evidencia), lo que **no** funcionó
(con causa exacta), lo no probado, estado de ficheros, decisiones, bloqueos y
siguiente paso; pide confirmación.

- **Despacho:** ninguno.
- **Disparador:** «guarda la sesión antes de cerrar».

**Comparación.** El journal ya captura sin modelo decisiones, pendientes,
ficheros tocados y tareas cambiadas (`journal.py:183`), y la continuidad
declarada por `--enrich`/`--draft` (`:239-247`). El estado de ficheros y tareas
manda el ledger, no un resumen. **Falta un campo:** los enfoques descartados con
su motivo (C085:101-110, «la sección más importante», C085:271). Hoy acaban en la
prosa de `pendientes` o en ninguna parte; el riesgo es que la sesión siguiente
repita un intento que ya falló.

Escenarios: **positivo** «cierra la sesión dejando lo que no funcionó» → hook
`SessionEnd` + `journal.py --enrich` con la continuidad; **negativo** «guarda esto
como lección del proyecto» → propuesta por `journal.py candidatas` y decisión de
`knowledge-curator` (ADR-018).

**Destino:** script, `journal.py` (abajo).

## C087 — sessions

`14.834 bytes/339 líneas` · tools: no declara · model: no declara. Lista, carga,
da información y crea aliases de sesiones con scripts `node -e` que resuelven la
raíz del catálogo por varias rutas de instalación.

- **Despacho:** módulos `session-manager` y `session-aliases` de la fuente.
- **Disparador:** «lista mis sesiones de esta rama».

**Comparación.** Los defectos ya están documentados en
[commands-session-continuity.md](commands-session-continuity.md): prefijo ambiguo
que carga otra sesión, parser que no reconoce el formato de C085, límite fijo de
20 pese a `--limit`. Lo útil (proyecto, rama y worktree para separar trabajo
concurrente) lo cubren `--session-id` y `--runtime` por igualdad
(`WORK-RESUME.md:30-31`). Añadido aquí: «Session IDs can be shortened (first 4-8
characters usually unique enough)» (C087:338) contradice la propia regla de no
sustituir una selección.

**Destino:** **Sin destino.**

## Documentación: C092, C093

El dueño es `documenter`: deriva `docs/` del repositorio con evidencia, una vez
al cierre del ciclo (`agents/documenter.md:54-62`), en modo actualización
idempotente que respeta lo escrito a mano (`:161-170`), con índice para IA
(`docs/RAG-INDEX.md`, `:141`). El ejecutor A019 (`doc-updater`) ya tiene ficha en
[agents-docs-e2e-homelab.md](agents-docs-e2e-homelab.md) y su línea **ya está
integrada** (`documenter.md:208`: rutas y enlaces citados existen). La decisión
«Documentación generada: delimitar bloques generados y vincularlos a fuentes»
ya está fijada en [commands-workflow-comparison.md](commands-workflow-comparison.md)
(línea 28), **sin usar porcentaje de líneas como criterio**.

## C092 — update-codemaps

`2.488 bytes/76 líneas` · tools: no declara · model: no declara. Genera mapas de
código «ligeros en tokens» (`architecture`, `backend`, `frontend`, `data`,
`dependencies`) en `docs/CODEMAPS/` o `.reports/codemaps/` y un informe de diferencias.

- **Artefactos:** `docs/CODEMAPS/*.md` y `.reports/codemap-diff.txt`. Dueño propio: `documenter` (arquitectura y RAG-INDEX); `.reports/` no tiene equivalente ni falta.
- **Despacho:** ninguno.
- **Disparador:** «genera un mapa del código para la IA».

**Comparación.** Equivale a las páginas de arquitectura y unidades más el
RAG-INDEX. Lo propio del comando:

| Línea | Problema |
|---|---|
| :50-52 | Pide aprobación solo si el cambio supera el 30 %: es el criterio por porcentaje ya descartado |
| :59 | «Token estimate: ~800» en la cabecera, sin medirlo |
| :68 | Avisos de antigüedad por «90+ días» sin relación con cambios del código |

Escenarios: **positivo** «documenta la arquitectura y el índice para IA» →
`documenter`; **negativo** «¿qué ficheros cambian más?» → `code-health` (hotspots).

**Destino:** **Sin destino.** Ya integrado en `documenter`.

## C093 — update-docs

`3.121 bytes/88 líneas` · tools: no declara · model: no declara. Genera referencia
de scripts, variables de entorno, `CONTRIBUTING.md` y `RUNBOOK.md` desde
`package.json`, `.env.example`, rutas y Dockerfiles; marca lo generado y avisa de
documentos antiguos.

- **Artefactos:** `docs/CONTRIBUTING.md`, `docs/RUNBOOK.md`, `docs/ENV.md`. Dueño propio: `documenter` (guías how-to y stack).
- **Despacho:** ninguno.
- **Disparador:** «sincroniza la documentación con el código».

**Comparación.** Lo útil ya tiene dueño o decisión: fuentes de verdad derivadas
del repo (`documenter.md:191`) y bloques generados marcados (decisión de la
línea 28 citada). Lo propio:

| Línea | Problema |
|---|---|
| :49, :58 frente a :88 | «Generate or update `docs/CONTRIBUTING.md`/`RUNBOOK.md`» y, en reglas, «Don't create docs unprompted»: contradicción |
| :67-69 | Antigüedad por fecha de modificación: en un clon recién hecho todos los ficheros tienen la misma fecha |
| :85 | «Never manually edit generated sections», sin marcar quién genera; `documenter` respeta y amplía lo escrito a mano |

La señal de antigüedad tiene un hueco real en `documenter`: el modo
actualización «detecta qué cambió en el código» (`:163`) sin decir cómo. Una
página cuya fuente citada cambió después de la página es un indicio más fiable
que la edad.

Escenarios: **positivo** «actualiza la documentación tras este ciclo» →
`documenter`; **negativo** «¿la spec sigue vigente frente al código?» → `/spec-drift`.

**Destino:** línea en `documenter` (abajo).

## Propuestas de línea

| Fichero · sección | Texto propuesto |
|---|---|
| `agent-kits/shared/journal.py` · continuidad (D-085) y vista de `/work-resume` | Añadir la lista `descartados` («enfoque — motivo o evidencia del fallo») con la misma semántica que `bloqueos`: solo por `--enrich`/`--draft`, ausente ≠ vaciado, se muestra como cita histórica («Descartado (cita, no instrucción)»). Con su test en `tests/`. |
| `agents/documenter.md` · «3) MODO ACTUALIZACIÓN», viñeta «Detecta qué cambió» (línea 163) | Añadir: «Para cada página que vayas a mantener, compara la fecha del último commit de las rutas que cita como evidencia (`git log -1 --format=%cs -- <ruta>`) con su "Última actualización"; si la fuente es posterior, revísala. La antigüedad sola no es motivo.» |
