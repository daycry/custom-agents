# Gobierno de agentes: documentación viva, diseño de bucles y autoridad financiera — S163, S164, S166

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **25.055 bytes/427 líneas**, sin recursos locales.
[living-docs-loops-trading-reading-evidence.json](living-docs-loops-trading-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S163 — Gobierno de la documentación viva

`8.482 bytes/137 líneas`. Inventariar antes de crear; asignar a los documentos
existentes cuatro papeles sin solape (constitución, mapa, estado, historia);
enlazarlos desde las instrucciones del arnés sin afirmar lecturas automáticas
inexistentes; tratar los documentos enlazados como evidencia, no como
instrucciones; actualizar solo el papel afectado; mantener una «zona de
borrado» para que lo retirado no se recree.

**Comparación.** El plugin ya tiene los cuatro papeles con dueño: constitución
en `CLAUDE.md` (y `docs/CONSTITUTION.md` en el consumidor), mapa en
`docs/README.md`, estado en el ledger y `/spec-drift` (deriva spec↔código,
solo lectura), historia en ADR, journal y CHANGELOG. «Un hecho, un dueño» es la
regla de `ADR-011`; «verificar la memoria contra la fuente vigente antes de
aplicarla» ya está en `agent-kits/shared/knowledge-check.md`. Lo que se inyecta
al arrancar está cableado y es acotado: el índice de piezas (`skill-index.py`) y
la última entrada del journal por `SessionStart`; el mapa `docs/README.md` no se
inyecta.

La zona de borrado también existe, pero con la semántica invertida.
`scripts/lint_plugin.py` mantiene `RUTAS_RETIRADAS` (p. ej. `agents/pdfy.md`,
retirado por `ADR-011`) y, si una de esas rutas vuelve a existir, avisa
«quítala de RUTAS_RETIRADAS»: trata la recreación como una tolerancia caducada,
no como la reaparición de algo retirado por decisión. La pieza aporta el matiz:

| Idea | Encaje |
|---|---|
| Lo retirado lleva motivo, sustituto y condición de revisión; recrearlo exige una decisión nueva | Cambiar el texto del aviso: «`<ruta>` vuelve a existir y `<ADR>` la retiró; si es intencional, registra la decisión y luego quítala de la lista» |
| Correcciones a la historia con fecha explícita, nunca reescritura silenciosa | Ya es la regla de registros fechados del repo |

Defectos menores: disparadores en dos idiomas dentro de la `description` sin
negativos, y la tabla de adopción usa `AGENTS.md` como constitución aunque la
misma pieza pide usar la superficie del arnés que realmente corre.

**Destino:** el texto del aviso de `_tolerancias_caducadas` en
`scripts/lint_plugin.py`. Sin skill nueva.

## S166 — Diseño y revisión de bucles de agente

`11.941 bytes/143 líneas`. Puerta previa de cuatro condiciones; objetivo
decidible por máquina con límites («qué no debe hacer»), tope de reintentos y
conciliación con una referencia externa; tipos servo/regulador; esqueleto
planificar/construir/juzgar con juez independiente y determinista; cinco modos
de fallo y tres líneas rojas.

**Comparación.** `/dev-cycle` es exactamente ese esqueleto: `planner` fija
criterios y `Verificación` por tarea, `implementer` construye, la revisión de
dos lentes con `reviewer` (solo lectura, contexto fresco) y `qa-gate` juzgan, los
bucles se acotan a 3 y al tercer rojo entra `debug-root-cause`; el cierre lo
decide la retro y el usuario. La regla de S166 que más interesa es la del modo
de fallo 3: **«el criterio de hecho va con su límite»**, porque un bucle que solo
exige verde termina borrando o debilitando tests. Dos comprobaciones a verificar
en T-08:

| Riesgo | Estado propio |
|---|---|
| El constructor debilita o borra un test para ponerse en verde | `tdd` prohíbe asserts triviales, pero no consta una comprobación sobre el diff que marque tests eliminados o asserts relajados como gap. Propuesta: fila en la tabla de racionalización del implementer y criterio explícito de la Lente B |
| El constructor edita los criterios de aceptación | `guardrail-check.py` permite al implementer escribir `tasks.md`, donde viven los criterios; `ledger-lint.py` comprueba que estén marcados al completar, no que su texto siga siendo el aprobado. Propuesta: que `ledger-lint.py` o `scope-check.py` detecten cambios en las líneas de criterio de una tarea ya aprobada |

Defectos: el punto 4 del marco de objetivos («el objetivo está estratificado»)
no se explica; la puerta «la tarea se repite al menos semanalmente» es
arbitraria; da por hechos `/goal`, `/loop` y `/schedule` como comandos del
anfitrión; «el estado avanza en un solo sentido y nunca retrocede» impide
corregir un registro erróneo, que la propia historia de S163 sí permite con fecha.

**Destino:** consolidar el método de diseño en la capacidad
`agent-system-quality` propuesta por S002/S004/S010 (referencia
`loop-design.md`), para bucles de los proyectos consumidores; las dos
comprobaciones de la tabla, como propuestas para la cadena propia.

## S164 — Seguridad de agentes con autoridad de transacción

`4.632 bytes/147 líneas`. Inyección como ataque financiero, límites de gasto,
simulación previa al envío, interruptor por pérdidas, cartera aislada y
protección frente a MEV, con checklist previa al despliegue.

**Comparación.** Dominio de trading sin rol en el ciclo. **Fuera del bundle.**
Su principio central —**los límites se aplican fuera de la salida del modelo**—
es el de `ADR-007` (un deny vive en un script determinista con tests, no en la
prosa del agente) y el de la autoridad explícita de S142 y la aprobación ligada
de S096. Defectos:

| Ejemplo | Corrección |
|---|---|
| Lista de regex contra inyección que lanza excepción con el texto | Una lista negra se evade con una paráfrasis y da falsa seguridad; además copia el contenido hostil al log. Separar datos externos del contexto con autoridad |
| `check_and_record` lee el gasto diario y luego registra | No es atómico: dos operaciones concurrentes pasan ambas el límite; reservar de forma atómica |
| Se simula y luego se firma y envía | El estado cambia entre simulación y envío; el mínimo de salida debe ir dentro de la transacción, no solo comprobarse fuera |
| `TradingCircuitBreaker.check` | Tras `halt` por pérdidas consecutivas sigue evaluando; mezcla `float` para dinero con el `Decimal` del límite de gasto |
| Clave privada en una variable de entorno del proceso del agente | El agente no debería poseer la clave: firmante separado con su propia política |
| Bloque de MEV | Solo declara constantes, sin mecanismo |

**Destino:** ninguno nuevo. Slippage y plazos, en la referencia
`oracle-swap-controls.md` de la especialidad Solidity propuesta por S073 si se
adopta; «reservar el límite de forma atómica antes del efecto» como precisión
del criterio de efectos externos de S096.
