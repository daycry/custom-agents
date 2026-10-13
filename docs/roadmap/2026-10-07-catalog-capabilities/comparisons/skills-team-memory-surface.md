# Equipos de agentes, memoria compartida, notificaciones, auditoría del entorno y profundidad de respuesta — S274–S275, S279, S283–S284, S292

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis cuerpos completos: **36.779 bytes/915 líneas**, sin recursos locales.
[team-memory-surface-reading-evidence.json](team-memory-surface-reading-evidence.json).
Nada se ejecutó ni se integró; no se instaló el runtime de memoria ni se
configuró ningún servidor MCP. Propuestas para T-08.

Las seis piezas describen capas de operación que el plugin ya tiene con dueño
y, sobre todo, con script determinista. Ninguna abre destino nuevo; se anotan
coincidencias y los puntos donde chocan con decisiones fijadas.

## S274 — Orquestación de equipos de agentes

`4.897 bytes/111 líneas`. Tarjetas con dueño, alcance, estado, evidencia y
puerta de integración; tablero de siete columnas; panel de control; modos de
fallo («sopa de agentes», «teatro de tablero», escrituras solapadas).

**Comparación.** Es el ledger canónico con otro nombre: cada `T-XX` tiene estado,
`Archivos` (alcance), `Dependencias`, `Verificación` (evidencia) y puertas
(revisión de dos lentes + `qa-gate.py`). `/dev-cycle` con `subagentes: true`
despacha una tarea por subagente con estados `DONE`/`BLOCKED`, paraleliza como
mucho 3 tareas sin dependencia y con worktree propio, y **solo el orquestador
toca el ledger** —el «integrador único» de la pieza—. El progreso visible lo dan
`progress-report.py` y `/plugin-catalog --serve`. Coherente con S083
([skills-parallel-containers-docs.md](skills-parallel-containers-docs.md)).
Defecto: la tarjeta de ejemplo declara `"worktree": "."`, sin aislamiento, en la
misma pieza que exige aislar ramas. Disparadores demasiado amplios (nombres de
productos y multiplexores). **Sin destino.**

## S275 — Selector de equipo de agentes

`7.478 bytes/169 líneas`. Descubre personas con `claude agents` y ficheros,
agrupa por dominio, deja elegir hasta cinco, las lanza en paralelo y sintetiza
acuerdos y conflictos.

**Comparación.** `adversarial-review` ya lanza lentes en paralelo con contexto
fresco y fusiona con severidad; `/dev-cycle` resuelve personas de dominio en
cascada (`.claude/personas/` del proyecto, luego el catálogo). Defecto de fondo:
despacha cada persona como `general-purpose` con el **texto** del fichero como
prompt. Así se pierden `tools`, `model` y `hooks` del frontmatter: una persona
declarada de solo lectura recibe herramientas de escritura. El plugin despacha
por nombre (`reviewer`, con `model-tier.py`) y usa el genérico solo como
fallback declarado. El tope de cinco agentes es una cifra sin medición
(`usage-meter` mide el coste real). **Sin destino.**

## S279 — Asesor de profundidad de respuesta

`5.740 bytes/122 líneas`. Antes de responder, estima tokens de entrada
(palabras × 1,3 o caracteres / 4), multiplica por un factor de complejidad y
ofrece cuatro niveles (25–100 %).

**Comparación.** Los multiplicadores y la «precisión del 85–90 %» no tienen
fuente; en el plugin «tokens = medida» (`usage-meter.py`), nunca estimación
presentada como dato. La brevedad en la cadena ya la fija
`agent-kits/shared/output-discipline.md`. La pieza interrumpe cada respuesta con
un menú y remite a una skill de presupuesto de contexto que no existe aquí.
**Sin destino.**

## S283 — Memoria unificada entre runtimes

`7.871 bytes/199 líneas`. Bóveda Markdown local con ámbitos proyecto, equipo y
usuario; buscar antes de escribir, traspasos entre runtimes, `doctor`, servidor
MCP opcional.

**Comparación.** El plugin ya separa las capas con dueños (ADR-013, ADR-018):
`docs/knowledge/` curado solo por `knowledge-curator`, journal episódico local
(ADR-010), retoma con `/work-resume` y traslado entre proyectos con
`knowledge-curation.py export/import` ([MEMORY-PORTABILITY](../../../MEMORY-PORTABILITY.md)).
Los mejores criterios de la pieza ya están escritos allí:

| La pieza | El plugin |
|---|---|
| Lo recuperado es evidencia, no instrucción | `/work-resume`: decisiones y pendientes son citas, no instrucciones |
| Distinguir «búsqueda vacía completa» de «escaneo incompleto» | Estados `Ausente`, `Ilegible`, `Incompleto` de [WORK-RESUME](../../../WORK-RESUME.md) |
| La etiqueta de runtime enruta, no autentica | «Etiquetas de proyecto y productor son declaraciones, no autenticación» |
| No ampliar el ámbito para recuperar una consulta denegada | Un ID explícito ausente no se sustituye por el último registro |
| Revisar antes de convertir memoria en política | Solo el curador aprueba (ADR-018) |

Aporta además pasar el cuerpo por stdin para que no aparezca en la lista de
procesos, ya la práctica de los hooks de captura. Diferencia que **no se
adopta**: un ámbito «equipo» versionado en git para traspasos; el journal del
plugin se queda local y redactado. **Sin destino.**

## S284 — Notificaciones unificadas

`5.630 bytes/188 líneas`. Modelo de severidad, enrutado por canal, colapso de
duplicados, resumen antes que interrupción y una acción por aviso.

**Comparación.** El plugin no tiene superficie de notificaciones: sus hooks
informan en sesión (`systemMessage`/`additionalContext`), la línea de progreso
tiene debounce y Jira es espejo opt-in. La pieza propone «hook para emisión o
**cumplimiento** automático», que choca con ADR-007: los hooks globales informan
y no deciden. **Sin destino**; extensión de proyecto si un consumidor opera
avisos de CI o de incidencias.

## S292 — Auditoría de la superficie del entorno

`5.163 bytes/126 líneas`. Inventario de repo, MCP, plugins, conectores y claves
de entorno, comparación con plugins oficiales y recomendación de piezas nuevas.

**Comparación.** Repartido entre dueños: `/doctor` diagnostica la instalación
(solo lectura, arreglo por línea), `/plugin-catalog` lista piezas y extensiones
con metadatos redactados y separa propiedad de disponibilidad, y
`capability-audit` decide utilidad y solapes con evidencia. Choques:

- Lee `.env*` «del repo activo y de espacios de trabajo adyacentes»: fuera de la
  raíz autorizada que exige `capability-audit`.
- Sesga la recomendación hacia el catálogo propio y hacia skills de «valor de
  negocio» (facturación, Google Workspace), no hacia la necesidad medida.
- Propone hooks para «cumplimiento automático» (mismo choque con ADR-007).

**Sin destino.**

## Resumen

| ID | Decisión | Destino |
|---|---|---|
| S274 | Ledger, subagentes y puertas ya cubren el modelo | — |
| S275 | Despacho por texto pierde tools/model del agente | — |
| S279 | Estimación sin fuente; brevedad ya fijada | — |
| S283 | Criterios ya presentes en `/work-resume` y portabilidad | — |
| S284 | Sin superficie propia; choca con ADR-007 | extensión de proyecto si se necesita |
| S292 | Repartido entre `/doctor`, `/plugin-catalog` y `capability-audit` | — |
