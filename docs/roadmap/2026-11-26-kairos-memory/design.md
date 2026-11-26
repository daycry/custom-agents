---
design: "kairos-memory"
titulo: "Kairos como memoria opcional de los agentes"
estado: borrador              # borrador | aprobado | obsoleto
creado: "2026-11-26"
actualizado: "2026-11-26"
spec: spec.md                 # enlace hacia atrás (misma carpeta)
evaluacion: "evaluation.md"
plan: pendiente               # improvement-plan.md cuando el planner lo cree
adr: "pendiente"              # se propone en la pasada 2, con la opción elegida
opcion_elegida: "pendiente"   # pendiente | O1 | O2 | O3 — se fija SOLO tras la validación del usuario
generacion:
  inicio: 2026-11-26T13:44:44Z
  fin: 2026-11-26T13:56:17Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-391a0d47660a4700ad3ec3f4755459b6
  revision_medicion: 3
  medicion_persistida: true
  tokens_reales: { entrada: 98, salida: 46087, cache_creacion: 145111, cache_lectura: 8162078 }
  eur: 3.02
  horas_ia: 0.36
  duracion: 22m
  ratio_usado: 531798.5
---

# Diseño — Kairos como memoria opcional de los agentes

> **Spec:** [`spec.md`](spec.md) (`aprobada`, 29 criterios) · **Evaluación:** [`evaluation.md`](evaluation.md) (`completado`, go del usuario 2026-11-26) · **Plan:** pendiente · **ADR:** pendiente (pasada 2)

| | |
|---|---|
| **Estado** | borrador |
| **Opción elegida** | pendiente — se fija con la elección del usuario |
| **Validada por el usuario** | pendiente |

## 1. Contexto y restricciones

La spec pide un cliente MCP genérico sin dependencias, el adaptador `kairos` incluido y apagado hasta
`/setup`, publicación idempotente de `approved/`, envío de journal e hitos con dos colas separadas,
redacción previa con marcador `[REDACTADO]` solo para Kairos y diagnóstico por capacidad. Los criterios
que más condicionan el diseño son CA-04 (reencolar sin dead-letter), CA-07 y CA-13 (entrega incierta:
conciliar antes de reenviar el cuerpo entero guardado), CA-14 (ocurrencias de hitos), CA-16 (otro MCP sin
tocar el núcleo) y CA-19/CA-29 (redacción).

Lo que hay hoy en el repo (recon del 2026-11-26):

- `agent-kits/shared/outbox.py` (982 líneas): cola por *envelope* con `outbox/ processing/ done/ dead-letter/`,
  `escribir` idempotente por clave, `reencolar_o_dead_letter` (dead-letter tras `MAX_INTENTOS = 3`, backoff
  `BACKOFF_S × intento`) y **`ceder_paso(item, cortesia_s)`**, que reencola **sin tocar `.intentos`** y con
  plazo explícito (acotado al leer por `BACKOFF_MAX_S = 3600`). Consumidores: `journal.py` (captura de
  `SessionEnd` y `replay`) y `knowledge-sync.py`.
- `skills/knowledge-services/scripts/knowledge-sync.py`: escribe **un envelope por corrida** con `ops`; al drenar
  **re-planifica** con las entradas actuales («la cola es señal de reintento, no consentimiento de
  publicación»); llama `apply(ops)` siempre en la corrida fresca; si `apply` lanza, usa
  `reencolar_o_dead_letter`. El contrato de `backends/README.md` exige que el **adaptador lleve su propio
  diario** para completar lo pendiente.
- `agent-kits/shared/redact.py`: `redactar()` conserva el prefijo (`Bearer `, `token=`) y usa
  `[secreto redactado]`. El bloque `--8<-- redact` está **replicado literal** en `journal.py` como copia
  declarada (`copias.json`, unidad `redact_redactar`, ADR-016 `aceptada`, test byte a byte): es el
  «duplicado de 239 líneas» que señala la evaluación. `anonimizar()` ya vive **fuera** del bloque.
- Aprobación del curator: `agent-kits/shared/knowledge-curation.py` deja un recibo por decisión en
  `docs/knowledge/candidates/.curation/receipts/<operation_id>.json` con `operation_id` (SHA-256),
  `source`, `target` (ruta en `approved/`) y `target_sha256`. Ese es el «ID de decisión» que pide la spec.
- Hitos: `agent-kits/shared/ledger-write.py` es quien mueve los estados del ledger (también desde
  `usage-meter close`); su `_emit` solo alimenta `agent-activity-store.py`, que es opt-in y un anillo con
  poda (no sirve como fuente durable). Las revisiones antiguas se archivan fuera de `tasks.md`
  (`execution-history.md`).
- Esquemas de Kairos (`session-summary.v1`, `observation.v1`): solo usan `type`, `const`, `enum`,
  `required`, `properties`, `additionalProperties`, `minLength`, `maxLength`, `maxItems`, `items` y
  `uniqueItems`.

**Restricciones que fijan el espacio de soluciones**

- Constitución: solo stdlib (`docs/CONSTITUTION.md:21`), hooks sin red (`:20`), todo texto enviado pasa por
  `redact.py` (`:34`), red opt-in y local/privada por defecto, solo lo aprobado (`:37`). No se edita.
- Spec: el adaptador va en el plugin, el núcleo no nombra Kairos, `knowledge-sync.py` «sin cambios de
  núcleo», dos colas «sobre `outbox.py`», ningún nombre de los backends retirados (CA-17), multi-runtime
  sin lógica por runtime (CA-18).
- ADR-016 (`aceptada`): cualquier cambio dentro del bloque replicado de `redact.py` obliga a cambiar la
  copia de `journal.py`. ADR-018 (`aceptada`) punto 2 dice «no hay `project_id`» como frontera del plugin;
  el `project_id` de Kairos es configuración del backend, como el `group_id` que el mismo ADR permite. No se
  reabre.
- Evaluación: arrancar tras fusionar plugin-audit-2; `doctor.py` y `knowledge-find.py` son hotspots
  (cambios acotados a una función).

**Invariantes, propiedad de los datos y estados:** (1) El Markdown local y `tasks.md` son la autoridad;
Kairos es una proyección. (2) Cada cuerpo enviado se redacta y serializa **una vez**, antes de encolar, y
no cambia después (dueño: quien lo encola). (3) Kairos es el dueño del estado remoto: ante cualquier duda
local se pregunta (`document_status`/`event_status`) antes de reenviar. (4) Una identidad
(`document_id`+versión o `event_id`) nunca se reenvía con otro cuerpo. (5) Las transiciones de un registro
son `pendiente → enviado → {completo | pendiente de trabajos → completo | terminal}`, con `transitorio →
pendiente (aplazado, sin tope)` y `permanente → dead-letter con causa`; `terminal → pendiente` y
`dead-letter → pendiente` solo por orden explícita del usuario (`reintentar_dead_letter`).

## 2. Opciones (2-3)

Las tres opciones comparten siete piezas que no admiten una alternativa razonable distinta (se explican
en el apartado 4): cliente en `agent-kits/shared/mcp-client.py` con la tabla de errores de Kairos fuera
del cliente, redacción por destino fuera del bloque replicado, validador de esquemas propio, evidencia
desde los recibos del curator y orden manual sin comando nuevo. Lo que cambia entre opciones es **dónde
vive la máquina de estados de entrega**, cuánto se toca el núcleo y de dónde salen los hitos.

### O1 — Máquina de entrega genérica en el núcleo

`outbox.py` gana estados de entrega persistidos (`enviado`, `incierto`, `aceptado`, `terminal`) con un
sidecar mutable por registro y una clase «transitorio sin tope». `knowledge-sync.py` pasa de un envelope
por corrida a **un registro por operación** y gana un modo `--episodic`. El contrato de adaptador añade
funciones opcionales `enviar(registro, cfg)` y `estado_remoto(registro, cfg)`; el núcleo conduce la
conciliación para cualquier backend. Hitos: `ledger-write.py` añade cada transición a un registro local
append-only. Orden manual: `knowledge-sync.py --episodic`.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: rediseña la cola compartida y el bucle de `knowledge-sync.py`, que hoy re-planifica a propósito en vez de reenviar cuerpos |
| Riesgo | Alto: cambia el contrato de `outbox.py` con dos consumidores vivos (`journal.py` en `SessionEnd`, `knowledge-sync.py`); es la familia de defectos de LES-016 (5 de 6 Critical en `session-end-durable-capture`); contradice «sin cambios de núcleo» de la spec |
| Coste relativo | L |
| Reversibilidad | Baja: deshacerla exige revertir el contrato de la cola y del núcleo de sync con sus suites |

### O2 — Colas propias del adaptador sobre `outbox.py`, conciliación remota primero

`outbox.py` y `knowledge-sync.py` **no cambian de semántica**. El adaptador `kairos` mantiene sus dos colas
con las primitivas existentes en `.claude/knowledge-services/_delivery/<backend>/{documental,episodica}/`:
una entrada por identidad (`document_id@versión`, `event_id`), con el cuerpo completo ya redactado e
inmutable. No hay fase local mutable: **cada vez que reclama un registro, consulta primero** el estado
remoto y decide (`ausente` → enviar; versión y hash iguales con trabajos pendientes → aplazar; `complete`
→ `completar` con recibo; `failed`/`superseded` → `completar` con recibo terminal). Transitorio y
`retry_after` → `ceder_paso` con el plazo (sin tocar intentos: nunca dead-letter); permanente →
`dead_letter` con causa. `apply(ops)` encola y drena, no lanza por fallos transitorios (el envelope de
`knowledge-sync.py` se completa); lanza solo por error de configuración, ya persistidos los registros.
Envío episódico: script genérico nuevo `skills/knowledge-services/scripts/episodic-sync.py` que reúne
episodios neutros (sesiones del journal y hitos) y llama a la función opcional nueva
`capturar(episodios, cfg)` del adaptador. Hitos: registro append-only que escribe `ledger-write.py` en su
carpeta de estado ya ignorada por git.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: la lógica fina vive en el adaptador; las colas y el núcleo se reutilizan tal cual |
| Riesgo | Medio: un `document_status`/`event_status` extra por registro reclamado; `ceder_paso` se usa con un sentido más amplio que su docstring; `ledger-write.py` es compartido |
| Coste relativo | M |
| Reversibilidad | Alta: todo lo nuevo está aislado (adaptador, script, cliente, assets); quitarlo deja intactos cola y núcleo |

### O3 — Almacén de entregas nuevo con estado local explícito

Un módulo nuevo `agent-kits/shared/delivery-store.py`, sin `outbox.py`, guarda un registro JSON por
identidad con todos los campos que pide `docs/integration.md` de Kairos (operación, proyecto, identidad,
versión, hash, fase de entrega, recibo remoto), con escritura por CAS y los cierres de `local-state.py`. La
fase local decide si hay que conciliar. Hitos: se derivan **en el momento del envío** del `tasks.md`
actual, comparando con el último estado visto guardado en el almacén. Mismo script episódico y misma
función `capturar` que O2.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: reimplementa la durabilidad (atomicidad, fsync, reclamación, huérfanos) que `outbox.py` ya cerró en más de 50 gaps |
| Riesgo | Alto: reabre la decisión técnica «dos colas sobre `outbox.py`»; los hitos por instantánea pierden una reapertura y cierre ocurridos entre dos envíos y los veredictos ya archivados |
| Coste relativo | L |
| Reversibilidad | Media: el almacén es nuevo y aislado, pero su formato queda en disco de los proyectos consumidores |

## 3. Criterios de decisión

1. **No romper contratos compartidos** (pesa más): `outbox.py` y `knowledge-sync.py` tienen consumidores
   vivos y un historial de Critical en colas durables (LES-016). La spec ya fija «sin cambios de núcleo».
2. **Corrección de la entrega incierta** (CA-07, CA-13, CA-26): el estado que decide un reenvío debe ser el
   del servidor, no una fase local que se puede perder o desincronizar.
3. **Reversibilidad**: Kairos está a mitad de tres hitos sin fecha; lo que se construya debe poder
   cambiarse sin tocar el núcleo.
4. **Coste** frente a la evaluación (C-03 y C-04 son la mitad del esfuerzo).
5. **Extensibilidad a otro MCP** (CA-16): necesaria, pero basta con que el cliente y el contrato sean
   genéricos; no exige que el núcleo conduzca la entrega.

## 4. Recomendación · opción elegida y por qué

**Recomendación del arquitecto:** O2 — cumple «sin cambios de núcleo» y «dos colas sobre `outbox.py`» sin
ampliar el contrato de la cola, y conciliar con el servidor antes de cada envío resuelve la entrega
incierta con la fuente de verdad remota (criterios 1 y 2) con el menor coste y la mayor reversibilidad
(criterios 3 y 4).

**Opción elegida:** pendiente de la validación del usuario.

Descartadas (motivo provisional, se confirma en la pasada 2): O1 por romper el criterio 1 y la spec; O3 por
reabrir una decisión técnica de la spec, reimplementar la durabilidad y perder ocurrencias de hitos.

**Respuestas a los puntos que la evaluación pidió cerrar** (comunes salvo donde se indica):

| Punto | Decisión de diseño |
|---|---|
| Estados de las dos outbox frente a `outbox.py` | O2: sin ampliar el contrato. Transitorio (incluidos `retry_after=N`, HTTP 429 `Retry-After`, cuota y 502/503/504) → `ceder_paso(item, cortesia_s=plazo)` (no incrementa intentos, nunca dead-letter; un plazo mayor de 3.600 s se reintenta y se vuelve a aplazar). Permanente → `dead_letter` con causa. Terminal remoto → `completar` con recibo. Entrega incierta → sin estado local: conciliación remota al reclamar. El adaptador nunca llama `reencolar_o_dead_letter`. Un alias aditivo `aplazar` en `outbox.py` es opcional y solo de legibilidad |
| `redact.py` y el marcador por destino | Funciones públicas nuevas **fuera del bloque replicado** (como `anonimizar`): `redactar_para(texto, marcador)` y `redactar_estructura_para(obj, marcador)`, con los patrones del hito B, los nombres de secreto de CA-29 (camelCase, `.`/`-`), claves JSON y valor completo con esquema; una asignación con comilla sin cerrar lanza una excepción propia y el registro no se encola. `redactar()`, `REDACTADO` y la copia de `journal.py` no cambian: ADR-016 y las suites del journal siguen igual |
| Cliente MCP genérico | `agent-kits/shared/mcp-client.py` (junto a `outbox.py` y `redact.py`; el adaptador lo resuelve con la misma ruta relativa que `knowledge-sync.py` usa para `SHARED`). Solo sabe de HTTP y JSON-RPC: cabeceras, `Bearer`, guardarraíl de host, topes, plazos, clasificación por código HTTP, `Retry-After`, `Deprecation`. La tabla de mensajes de Kairos (regex con `re.fullmatch`, clase, extracción de `retry_after`) es **dato del adaptador** en `skills/knowledge-services/backends/kairos_assets/errores.json`, que el adaptador pasa al clasificador del cliente |
| Fuente de los hitos | O1/O2: `ledger-write.py` añade una línea por transición a `docs/roadmap/<carpeta>/.ledger-write/hitos.jsonl` (carpeta que ya crea con `.gitignore` `*`), bajo el mismo cierre con el que escribe el ledger; la ocurrencia es el número de líneas previas con la misma tarea y estado. Cubre `usage-meter close`. Retro: `retro.md` (ocurrencia 1). O3: instantánea del ledger |
| Validador de esquemas sin dependencias | `agent-kits/shared/schema-subset.py`: implementa solo las 11 palabras clave que usan los esquemas y **falla cerrado** ante cualquier otra (así una versión nueva del esquema con otra palabra clave se detecta, no se ignora); límites de 1.000 nodos y profundidad 8. Esquemas copiados en `backends/kairos_assets/` con origen y fecha; los ejemplos de Kairos entran como fixtures de test |
| «Orden manual» | Sin comando nuevo (ni evals, ni interop, ni espejo EN): O2/O3 → `python3 skills/knowledge-services/scripts/episodic-sync.py --backend <id> [--dry-run\|--status]`, el mismo que llaman la Fase 6 de `/dev-cycle` y `/retro`; O1 → `knowledge-sync.py --episodic` |
| Evidencia e ID de decisión del curator | El adaptador busca el recibo de `.curation/receipts/` cuyo `target` es la ruta de la entrada y cuyo `target_sha256` coincide con el fichero actual. `evidence` = `curator:operation:<operation_id>` + las `fuentes` del frontmatter + el nivel `evidencia` (1..20 elementos, ≤ 4.000 caracteres). Sin recibo, o con el fichero editado tras la aprobación, no se envía y se informa con el remedio (volver a aprobar con `knowledge-curator`) |

## 5. Impacto en módulos y ficheros

Tabla de la opción recomendada (O2). Con O1 se añaden cambios de contrato en `outbox.py` y
`knowledge-sync.py`; con O3, `agent-kits/shared/delivery-store.py` sustituye a las colas sobre `outbox.py`
y `ledger-write.py` no cambia.

| Módulo / fichero (ruta real) | Cambio | Nuevo / modificado |
|---|---|---|
| `agent-kits/shared/mcp-client.py` | Cliente MCP genérico *streamable HTTP* (C-01) | Nuevo |
| `agent-kits/shared/schema-subset.py` | Validador de esquemas por subconjunto, falla cerrado | Nuevo |
| `agent-kits/shared/redact.py` | `redactar_para` y `redactar_estructura_para` fuera del bloque replicado (C-05) | Modificado |
| `agent-kits/shared/outbox.py` | Sin cambio de semántica; alias aditivo `aplazar` opcional | Sin cambios / modificado |
| `agent-kits/shared/ledger-write.py` | Registro append-only de transiciones en `.ledger-write/hitos.jsonl` | Modificado |
| `skills/knowledge-services/backends/kairos.py` | Adaptador: 6 funciones, `puede_leer`, `consultar`, `capturar`, salud por capacidad, dos colas, conciliación | Nuevo |
| `skills/knowledge-services/backends/kairos_assets/` | `errores.json`, esquemas `*.v1` copiados con origen | Nuevo |
| `skills/knowledge-services/scripts/episodic-sync.py` | Reúne episodios neutros (journal e hitos) y llama `capturar`; orden manual | Nuevo |
| `skills/knowledge-services/scripts/fixtures/` | Servidor MCP falso en proceso y adaptador `mcp-fixture` (CA-16) | Nuevo |
| `skills/knowledge-services/scripts/knowledge-sync.py` | Sin cambios | Sin cambios |
| `skills/knowledge-services/backends/README.md` | Función opcional `capturar`, forma de los episodios neutros, «el plugin incluye un adaptador» | Modificado |
| `skills/knowledge-services/SKILL.md` | Adaptador incluido y orden manual | Modificado |
| `skills/knowledge-services/references/` | Activar Kairos; añadir otro MCP de memoria | Modificado / nuevo |
| `agent-kits/shared/doctor.py` | Una función: fila por capacidad con remedio | Modificado |
| `agent-kits/shared/capabilities.py` | Capacidad de memoria Kairos | Modificado |
| `commands/setup.md` | Paso guiado; validación sin red en el adaptador | Modificado |
| `commands/dev-cycle.md` | Fase 6: llamada a `episodic-sync.py` si hay backend con captura | Modificado |
| `commands/retro.md` | Llamada a `episodic-sync.py` tras escribir `retro.md` | Modificado |
| `interop/` | Regenerado con `scripts/export-interop.py` | Modificado (generado) |
| `CHANGELOG.md` | Entrada `[Unreleased]` | Modificado |
| `CHANGELOG.es.md` | Entrada `[Sin publicar]` | Modificado |

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Purgar `done/` y volver a encolar la misma identidad con otra redacción produce `Conflicting event or version` | Media | Alto | La conciliación remota previa al envío lo evita (el servidor dice `complete`); test que purga `done/`, cambia patrones y reintenta (extiende CA-13) |
| Una corrida larga: cada registro puede sumar consulta, envío y consulta con plazo de 40 s | Media | Medio | Drenaje acotado por número de registros y por tiempo total (como `_MAX_DRENAJE`); lo que no cabe queda en cola |
| `ceder_paso` se usa para plazos del servidor, no solo para envelopes ajenos | Media | Bajo | Documentarlo en su docstring o añadir el alias `aplazar` con test; sin cambio de comportamiento |
| El registro de hitos no ve ediciones manuales de `tasks.md` | Baja | Medio | Regla 8: los estados los mueven los scripts; `episodic-sync.py --status` lista tareas cerradas en el ledger sin hito registrado |
| `ledger-write.py` falla al escribir `hitos.jsonl` | Baja | Bajo | Degrada con aviso `ledger:` como hoy con la actividad; nunca bloquea la transición |
| Entradas de `approved/` sin recibo (aprobadas antes del servicio de curación o editadas a mano) no se publican | Media | Medio | Informe con el remedio; pregunta abierta 1 |
| Deriva entre las copias de esquemas y errores y el repo de Kairos | Media | Medio | Origen y fecha en `kairos_assets/`; el validador falla cerrado; CA-20 en real; `redaction-cases.json` cuando exista |
| El envelope de `knowledge-sync.py` acaba en dead-letter tras tres errores de configuración seguidos | Media | Bajo | Es solo una señal de reintento; los registros siguen en la cola del adaptador; `/doctor` nombra el remedio de configuración |
| La opción elegida desborda la evaluación (O1 u O3) | Media | Medio | Con O1 u O3, `/dev-cycle` debería re-evaluar C-03 y C-04 antes del plan |

## 7. Preguntas abiertas

- Entradas de `approved/` editadas tras su aprobación, o aprobadas antes del servicio de curación: ¿se exige
  volver a aprobarlas con `knowledge-curator` para publicarlas (propuesta), o se acepta otra evidencia?
- Hito «decisión»: ¿qué cuenta como decisión además de los veredictos de revisión? Propuesta: la puerta
  go/no-go de `evaluation.md` y la aprobación de `design.md`, leídas de su frontmatter (ocurrencia 1).
- Validación sin red de `/setup` (CA-02): ¿vía la función opcional `proponer_config` y
  `knowledge-sync.py --propose-config`, o con un subcomando del adaptador? Lo decide `planner` al ver el
  contrato actual de `--propose-config`.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-11-26 | Diseño creado (`borrador`); tres opciones presentadas al usuario, recomendada O2 |
