---
spec: kairos-memory
descripcion: Integración opcional del plugin con Kairos como memoria de los agentes (lectura, publicación de lo aprobado, journal e hitos), como primer adaptador MCP del marco knowledge-services.
estado: borrador          # borrador | aprobada | implementada | obsoleta
creado: 2026-11-26
actualizado: 2026-11-26
evaluacion: pendiente
design: n/a
plan: pendiente
generacion:
  inicio: 2026-11-26T11:56:46Z
  fin: 2026-11-26T11:59:26Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-c1a477eaca734b1e8e8c44819e8b0111
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 18, salida: 21114, cache_creacion: 38691, cache_lectura: 1314721 }
  eur: 0.81
  horas_ia: 0.11
  duracion: 7m
  ratio_usado: 531798.5
---

# Kairos como memoria opcional de los agentes

> **Evaluación:** pendiente
> **Plan de implementación:** pendiente

> **Terminología:**
> - **Kairos**: servidor de memoria del usuario (repo knowledge-graphs). Habla MCP por *streamable HTTP* en exactamente `<base>/mcp/` (con barra final), con credencial `Authorization: Bearer`. Contrato: repo knowledge-graphs, `docs/contracts/kairos-mcp.json` (MCP 0.4.1, 34 herramientas, contrato estrictamente aditivo).
> - **Adaptador**: fichero `backends/<type>.py` del marco `knowledge-services` con las 6 funciones `health/plan/apply/verify/rebuild/revoke` (+ opcionales `puede_leer`/`consultar`).
> - **Cliente MCP genérico**: módulo Python del plugin que abre sesión MCP por HTTP, envía `Bearer` y llama herramientas por nombre. No sabe nada de Kairos.
> - **Capacidad**: grupo de operaciones del adaptador (lectura, publicación, revocación, reconciliación, captura) que se habilita o degrada por separado según las herramientas que anuncie `tools/list`.
> - **Publicación documental**: envío de `docs/knowledge/approved/` con `publish_document`/`revoke_document`.
> - **Memoria episódica**: eventos con `remember` (resumen de sesión del journal, hitos del ledger).
> - **Generación documental**: sufijo que entra en el UUIDv5 del `document_id`; cambia solo cuando una entrada revocada (lápida) vuelve a `approved/`.
> - **Captura del cliente kairos**: hooks que instala `kairos install --capture summary|full` (fuera del plugin). Envía metadatos de ciclo de vida (`category: agent-activity`), **nunca** `session-summary.v1`. El plugin no la detecta ni depende de ella.

## Contexto y objetivo

El plugin ya tiene memoria técnica local (`docs/knowledge/`, journal de sesión, `knowledge-curator`)
y un marco para proyectarla a un servicio externo (`skills/knowledge-services/`), pero desde la
4.0.0 no incluye ningún adaptador. Los dos backends anteriores se retiraron en plugin-audit-2
(T-08/T-09, ver `docs/roadmap/2026-11-10-plugin-audit-2/testing/retirada.md`). El usuario los
sustituye por **Kairos**, su servidor de memoria único.

Objetivo: que un proyecto que lo pida pueda usar Kairos como memoria de sus agentes, de forma
**opcional, correcta y sin errores**:

- **Leer**: los agentes consultan la memoria de Kairos con respaldo local.
- **Escribir**: se publica solo lo aprobado, se revoca lo que sale de `approved/`, se envía el
  resumen de sesión y los hitos del ledger cuando la política de captura del proyecto lo permite.
- **Sin acoplar el plugin**: Kairos es el primer adaptador del marco por `type`. Otro MCP de
  memoria debe poder enchufarse igual.
- **Sin bloquear nunca el ciclo**: si Kairos cae, se degrada con aviso y la outbox reintenta.

Coordinación: la sesión de Claude que mantiene Kairos (sesión «kairos», dueña del repo
knowledge-graphs) validó este diseño contra el servidor y el contrato 0.4.1 el 2026-11-26
(rama `feat/access-control`). Este plugin no escribe en ese repo.

## Decisiones de diseño

Decisiones del usuario (2026-11-17/18 y 2026-11-26). Son requisitos, no se reabren.

| Decisión | Elección | Motivo |
|---|---|---|
| Transporte | **MCP** (*streamable HTTP* en `<base>/mcp/`), no REST `/v1` | Un único contrato; `tools/list` es la fuente del esquema |
| Activación | **Opt-in**: se configura en `/setup`, `/doctor` la comprueba | Constitución: toda capacidad con red es opt-in |
| Journal e hitos | **Siempre que `capture_policy` (con la clave de escritura) dé `capture_allowed: true`**, esté o no instalado el cliente kairos. Con captura `off`, se quedan en local y `/doctor` avisa | La captura del cliente kairos nunca envía resúmenes: no hay duplicado (decisión 5 del 2026-11-26) |
| Qué se publica | **Solo `docs/knowledge/approved/`**; `candidates/` se queda local | Constitución: los backends solo reciben lo aprobado por `knowledge-curator` |
| Proyecto | **Un `project_id`** fijado una vez en `/setup` (`^[a-z0-9][a-z0-9_-]{0,63}$`) | Evita mezclar proyectos |
| Credenciales | **Dos claves separadas**: lectura (`read`) y escritura (`read`+`publish`+`validate`, +`write` si se envían journal o hitos). Nunca `admin` | Mínimo privilegio. La de escritura necesita `read` para `capture_policy`, `document_status`, `document_manifest` y `event_status` |
| Ledger | **Solo hitos**: tarea cerrada, veredicto de revisión, retro, decisiones. `tasks.md` sigue canónico | No duplicar el ledger; ruido mínimo |
| Acoplamiento | **Kairos = primer adaptador por `type`** sobre un cliente MCP genérico; routing fail-closed | Otros MCP de memoria deben poder añadirse |
| Adaptador incluido | **`backends/kairos.py` va en el plugin**, inactivo hasta `/setup` | Una sola implementación probada del contrato fino de Kairos |
| Lectura | **Sin agente nuevo**: `knowledge-find.py --intent` con la clave de lectura y respaldo local | Un rol, un dueño |
| Host | **Local/privado por defecto**; cloud con opt-in `allow_remote` (`https`, sin redirecciones, sin IMDS ni enlace local) | `docs/CONSTITUTION.md:37` |
| Runtimes | **Claude Code, Codex y OpenCode** sin código por runtime; traduce `export-interop.py` | Requisito del proyecto (multi-runtime) |

Decisiones técnicas de este análisis, validadas por la sesión kairos:

| Decisión | Elección | Motivo |
|---|---|---|
| Identidad documental | **UUIDv5** de (`project_id`, ID local, generación). La generación empieza en 1 y **sube obligatoriamente** cuando una entrada con lápida vuelve a `approved/`. El ID local y la generación viajan en `source.uri`/`source.label` | El servidor no permite republicar un ID borrado (`Conflict`). Con el ID local en `source`, la generación se reconstruye desde `document_manifest` aunque se pierda el estado local |
| Salud | **Por capacidad, desde `tools/list`**; nunca por `serverInfo.version` | El contrato es aditivo; el MCP interno en desuso devuelve la versión del SDK |
| Errores | **Por texto del mensaje** de `isError` (lista cerrada abajo); 401 es de toda la petición | Por MCP no llegan códigos ni cabeceras |
| Outbox | **Dos colas separadas** (documental y episódica) sobre `agent-kits/shared/outbox.py` | Lo exige el contrato de Kairos («Dos flujos de escritura separados») |
| Nombres | Nada nuevo se llama como los backends retirados; el cliente MCP se reescribe genérico | Petición del usuario (2026-11-26) |

## Configuración / parámetros

Todo vive en `.claude/knowledge-services/taxonomy.json` (local del proyecto), bajo
`backends.<id>` con `type: "kairos"`. Ningún secreto en ese fichero.

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Activación | `backends.<id>.enabled` | `false` | `true` tras `/setup` |
| Tipo de adaptador | `backends.<id>.type` | — | **`kairos`** |
| URL base | `config.base_url` | ninguno | p. ej. `http://127.0.0.1:5173`; el adaptador llama a exactamente `<base>/mcp/` |
| Hosts permitidos | `config.allow_remote` | `false` | Solo hosts locales/privados salvo opt-in explícito (`https`, sin redirecciones, sin IMDS ni enlace local) |
| Proyecto | `config.project_id` | ninguno | Validado con `^[a-z0-9][a-z0-9_-]{0,63}$` |
| Clave de lectura | `config.read_key_file` | ninguno | Ruta a fichero privado **fuera del proyecto** (scope `read`) |
| Clave de escritura | `config.write_key_file` | ninguno | Ruta a fichero privado fuera del proyecto (`read`+`publish`+`validate`, +`write`); opcional: sin ella, solo lectura |
| Intents de lectura | `backends.<id>.read.intents` | `[]` | Los que el usuario autorice |
| Routing por categoría | `categories.<cat>.routing.<id>` | ausente = no se envía | `true` o `"summary"` por categoría |
| Journal | `config.journal` | `false` | `true`: envía `session-summary.v1` si `capture_allowed: true` |
| Hitos del ledger | `config.hitos` | `false` | `true`: envía hitos si `capture_allowed: true` |
| Plazos | `config.timeout_ms` | 5.000 | Respeta el tope de `/doctor` |

## Arquitectura y componentes

| Pieza | Nueva / reutilizada | Papel |
|---|---|---|
| Cliente MCP genérico (Python, sin dependencias) | **Nueva** (reescritura genérica, sin reutilizar nombres retirados) | `initialize`, `tools/list`, `tools/call` contra `<base>/mcp/`; `Bearer`; guardarraíl de host (local/privado por defecto, sin redirecciones, sin proxy del entorno); clasifica errores por texto; extrae `retry_after=N` del texto de `isError`; backoff propio ante `Memory service temporarily unavailable`; tope de bytes; acepta el sobre `untrusted`/`warning` y campos opcionales de más; marca todo resultado como dato no confiable |
| Adaptador `kairos` (`skills/knowledge-services/backends/kairos.py`) | **Nuevo, incluido en el plugin** | Las 6 funciones + `puede_leer`/`consultar`. Salud por capacidad. Mapea a `projects`, `search`, `details`, `context`, `publish_document`, `document_status`, `document_manifest`, `revoke_document` |
| Envío episódico (journal e hitos) | **Nuevo** (script determinista con tests) | `capture_policy` → `remember` → `event_status`; identidad estable por evento; validación local con los esquemas `session-summary.v1` y `observation.v1` |
| `skills/knowledge-services/scripts/knowledge-sync.py` | Reutilizado sin cambios de núcleo | Carga por `type`, routing fail-closed, outbox, `--check/--dry-run/--rebuild` |
| `agent-kits/shared/outbox.py` | Reutilizado | Dos colas: documental y episódica |
| `agent-kits/shared/knowledge-find.py --intent` | Reutilizado | Router de lectura con respaldo local y motivo |
| `agent-kits/shared/redact.py` | Ampliado | Todo texto enviado pasa por aquí; patrones alineados con los de la redacción del hito B de Kairos |
| `agent-kits/shared/capabilities.py`, `commands/setup.md`, `agent-kits/shared/doctor.py` | Ampliados | Paso guiado de configuración y fila de diagnóstico por capacidad |
| `commands/dev-cycle.md` (Fase 6), `commands/retro.md` | Ampliados | Paso explícito de envío episódico (journal e hitos) |
| `hooks/` | **Sin cambios de red** | El journal se sigue escribiendo en local; el envío ocurre fuera de los hooks |

**Mínimo de herramientas por capacidad** (lo que `health()` busca en `tools/list`):

| Capacidad | Herramientas requeridas | Clave |
|---|---|---|
| Lectura | `projects`, `search`, `details`, `context` | lectura |
| Publicación | `publish_document`, `document_status` | escritura |
| Revocación | `revoke_document` | escritura |
| Reconciliación | `document_manifest` + `event_status` con propiedad `project_id` en su esquema | escritura |
| Captura (journal e hitos) | `capture_policy`, `remember`, `event_status` | escritura con `write` |

La lectura no depende de la escritura: si falta una capacidad de escritura, la lectura sigue sana.

## Flujo (paso a paso)

**Configuración (`/setup`)**
1. El usuario elige activar Kairos. `/setup` pide URL base, `project_id`, rutas de las dos claves, categorías a publicar, journal e hitos.
2. Valida formato (`project_id`, URL, host permitido, ficheros de clave existen y están fuera del proyecto). No conecta.
3. Escribe `backends.<id>` en `taxonomy.json` y propone `/doctor` para la comprobación en vivo.

**Diagnóstico (`/doctor`)**
4. `health()` con la clave de lectura: `initialize` + `tools/list`; veredicto por capacidad según la tabla de mínimos; `projects` debe incluir el `project_id`. Con la clave de escritura: `tools/list` + `capture_policy`. No mira `serverInfo.version`. Nunca escribe.
5. Los scopes `publish`/`validate` no se pueden verificar sin escribir: `/doctor` lo dice («no verificable sin publicar») y no lo da por bueno. Si `capture_allowed: false` y el journal o los hitos están activados, avisa: «la captura del proyecto está en `off` o la clave no tiene `write`; un admin debe activar la captura en Kairos».

**Lectura (agentes)**
6. Un agente llama `knowledge-find.py --intent <intent> "<texto>"`. Si el intent está autorizado y `puede_leer` da `true`, el adaptador llama `search`/`context` con la clave de lectura y el `project_id`.
7. Cada acierto vuelve marcado como **dato no confiable**, con procedencia. Si Kairos falla o responde parcial, la respuesta incluye el motivo y los aciertos locales.

**Publicación de lo aprobado**
8. `knowledge-sync.py --backend <id> --dry-run` muestra qué se publicará (solo `approved/` con routing).
9. Sin `--dry-run`: drena la outbox documental y llama `publish_document` con `document_id` = UUIDv5(`project_id`, ID local, generación), versión secuencial, `source.sha256` de los bytes UTF-8 exactos de `content`, ID local y generación en `source.uri`/`source.label` y tags como lista. La aceptación no es el fin: `document_status` hasta confirmar versión, hash y trabajos.
10. Una entrada que sale de `approved/`: primero `document_status`. Si devuelve `Resource not found` o `deleted: true`, no hace nada. Si no, `revoke_document` con la versión siguiente.
11. Una entrada con lápida que vuelve a `approved/` se publica con la generación siguiente (ID nuevo) y se avisa en el informe. El ID revocado nunca se republica.
12. `--check`: `document_manifest` paginado contra el estado local; nombra el remedio sin reenviar a ciegas. Si se perdió el estado local, la generación se reconstruye desde `source.uri`/`source.label` del manifiesto.

**Journal e hitos (memoria episódica)**
13. Momentos de envío: paso explícito en la Fase 6 de `/dev-cycle`, en `/retro` y con una orden manual. Cada envío drena lo que `SessionEnd` dejó en local.
14. Antes de enviar, `capture_policy` con la clave de escritura. Con `capture_allowed: false`, nada sale: journal e hitos se quedan en local y `/doctor` lo avisa.
15. Con `capture_allowed: true` y `config.journal: true`: un `remember` por sesión con `event_type: summary`, `generate: false` y `payload.structured` `session-summary.v1`. No lleva el campo `capture` ni etiquetas `capture:*`.
16. Con `config.hitos: true`, cada hito nuevo del ledger es un `remember`:

    | Hito | `event_type` | `observation.v1.type` |
    |---|---|---|
    | Tarea cerrada | `note` | `change` |
    | Veredicto de revisión o decisión | `note` | `decision` |
    | Retro | `learning` | `discovery` |

    Sin `category: agent-activity` y sin etiquetas `capture:*`. Cada `facts[].evidence_quote` es una cita literal del contenido enviado. La identidad sale de slug + ID + estado + **número de ocurrencia** (o revisión del ledger), para que reabrir y volver a cerrar una tarea dé un evento nuevo y no un `Conflicting event or version`.
17. `event_status` (con `project_id`) hasta `complete`. Pendiente o incierto → se queda en la outbox episódica.

## Alcance

- **Dentro (esta iteración):**
  - Cliente MCP genérico en Python (HTTP *streamable*, `Bearer`, guardarraíl de host, errores por texto con `retry_after`, backoff propio, tope de bytes), sin dependencias externas, con servidor MCP falso para los tests.
  - Adaptador `kairos` incluido en el plugin, con las 6 funciones del contrato, `puede_leer`/`consultar` y salud por capacidad.
  - Publicación de `approved/` (con modo `resumen`), revocación con lápida y comprobación previa, generaciones documentales, reconciliación por `document_manifest`, `--rebuild`.
  - Lectura vía `knowledge-find.py --intent` con respaldo local y marca de dato no confiable.
  - Envío de journal (`session-summary.v1`) e hitos del ledger (`observation.v1`) cuando `capture_allowed: true`.
  - Dos outbox separadas, idempotencia estricta y reconciliación tras entrega incierta.
  - Redacción previa (`redact.py`) alineada con los patrones del hito B de Kairos.
  - `/setup` (paso guiado), `/doctor` (fila por capacidad con veredicto y remedio), `capabilities.py`, paso de envío en `/dev-cycle` Fase 6 y `/retro`.
  - Documentación: `skills/knowledge-services/references/` (cómo activar Kairos y cómo añadir otro MCP de memoria), `backends/README.md` y `SKILL.md` (ya hay un adaptador incluido), CHANGELOG EN/ES, regeneración de `interop/`.
- **Fuera (siguientes specs):**
  - Cambios en el servidor Kairos o en su cliente `kairos` (repo knowledge-graphs).
  - Instalar el cliente `kairos`, crear claves, cambiar la política de captura o reindexar: son acciones del usuario o de un admin. El plugin las **nombra**, no las ejecuta.
  - REST `/v1` (incluido `GET /v1/auth/me` para leer scopes), sesión del portal, contraseña de admin o `bootstrap_password`.
  - Detectar la instalación del cliente kairos (`.kairos/installation.json` no es contrato).
  - Enviar candidatas, el ledger entero, transcripciones o prompts.
  - Herramientas de corpus, observaciones, equipo y `work_state_*` de Kairos.
  - Red desde hooks; lectura automática de Kairos en `SessionStart`.
  - Un segundo adaptador MCP real (se deja documentado cómo añadirlo y probado con un fixture).
  - Cualquier pieza, nombre, test o fixture con el nombre de los backends retirados.

## Manejo de errores

Por MCP no llegan códigos ni cabeceras (kairos-mcp descarta `Retry-After`): el cliente clasifica
por el texto `Error executing tool <x>: <mensaje>` de `isError`, salvo el 401, que es HTTP.

| Caso (texto o señal) | Comportamiento |
|---|---|
| HTTP 401 de toda la petición MCP (clave inválida, revocada, caducada o rotada; no se distinguen) | `error` «clave rechazada» con el remedio (renovar en el portal); nunca imprime la clave; escritura reencola |
| `Rate limit exceeded [code=rate_limited retry_after=N]` | No reintenta antes de N s; si N excede el plazo, reencola |
| `Daily write quota exceeded …` / `Too many activity streams …` | Escritura reencola con backoff largo y aviso; la lectura sigue (la cuota no afecta a lecturas) |
| `Memory service temporarily unavailable` (5xx, caída o plazo; sin `retry_after`) | Backoff propio; lectura degrada a local con motivo; escritura reencola. El ciclo nunca se bloquea |
| Conexión rechazada o timeout de red | Igual que la fila anterior |
| `Conflicting event or version` en `publish_document` | `document_status`: si `deleted: true`, es una lápida → generación siguiente (paso 11); si no, conflicto real de contenido → se reporta y se detiene esa entrada, sin subir la versión para esquivarlo |
| `Conflicting event or version` en `remember` | Conflicto de identidad: se reporta; nunca se genera un UUID nuevo para el mismo evento |
| `Resource not found` | Ausencia confirmada solo para la consulta de estado de esa identidad (p. ej. `document_status` antes de revocar → nada que revocar) |
| `Operation not permitted` | Falta scope o proyecto: `error` con el scope que la operación necesita |
| `Capture is disabled for this project` | Journal e hitos se quedan en local; aviso en `/doctor` (un admin debe activar la captura) |
| `Structured observation does not match its schema: …` | Fallo permanente de ese evento con la ruta del error; no se reintenta igual (se valida en local antes de enviar para evitarlo) |
| `Sensitive capture metadata requires privacy review` / `Approved sources require privacy review before publication` | Fallo permanente con motivo; se revisa la redacción previa; no se reenvía igual |
| `isError` con cualquier otro texto | Fallo de esa operación, **no** ausencia (un error no confirma que algo no exista) |
| Entrega incierta (timeout tras enviar) | `document_status`/`event_status`; solo una ausencia confirmada (`found: false`) permite repetir el mismo envío, con la misma identidad y contenido |
| Host no permitido o redirección | Se rechaza antes de conectar; no se siguen redirecciones |
| Respuesta recortada por el tope de bytes o no-JSON | Se descarta con motivo; nunca se inventa contenido |
| Herramienta ausente en `tools/list` | Solo esa capacidad pasa a `degradado`, nombrando la herramienta; las demás siguen |
| Clave de solo lectura | No se llama a ninguna herramienta de escritura; «sin clave de escritura» |

## Criterios de aceptación

Cada criterio dice cómo se comprueba. Los `[GWT]` se prueban con el servidor MCP falso salvo
que se indique «integración real».

- [ ] [GWT] CA-01 — Dado un proyecto sin `backends.<id>` de tipo `kairos`, Cuando se ejecutan `/doctor`, `knowledge-find.py` y los hooks, Entonces no se abre ninguna conexión de red y la capacidad sale «desactivada» (no error). *Comprobación:* test con socket espía + `tests/test_hook_network_egress.py` en verde.
- [ ] [GWT] CA-02 — Dado `/setup` con un `project_id` inválido, un host público sin `allow_remote`, un host remoto con `http` o una ruta de clave dentro del proyecto, Cuando se valida la config, Entonces se rechaza con un mensaje que nombra el campo y no se escribe `taxonomy.json`. *Comprobación:* test del validador con los cuatro casos.
- [ ] [GWT] CA-03 — Dado el servidor falso que exige `Bearer`, Cuando el cliente MCP genérico llama `initialize`, `tools/list` y `tools/call`, Entonces todas las peticiones van a `<base>/mcp/` con barra final y llevan `Authorization: Bearer <clave>`, la clave no aparece en salidas, logs ni outbox, y no se siguen redirecciones. *Comprobación:* test del cliente + búsqueda del valor de la clave en todo lo escrito.
- [ ] [GWT] CA-04 — Dado Kairos caído o respondiendo `Memory service temporarily unavailable`, Cuando se ejecutan `/doctor`, una lectura con `--intent` y `knowledge-sync.py`, Entonces `/doctor` marca ⚠️ con el remedio, la lectura devuelve los aciertos locales con el motivo y el sync reencola con backoff propio sin dead-letter; todos acaban dentro del tope de tiempo y con exit 0 donde el ciclo lo exige. *Comprobación:* test con servidor apagado y con el error 5xx.
- [ ] [GWT] CA-05 — Dado `approved/` con 3 entradas (una sin routing) y `candidates/` con 2, Cuando se publica, Entonces solo llegan 2 `publish_document` (las enrutadas) y ninguna candidata. *Comprobación:* registro de llamadas del servidor falso.
- [ ] [GWT] CA-06 — Dada una entrada publicada, Cuando se inspecciona la llamada, Entonces `source.sha256` es el SHA-256 hex minúsculo de los bytes UTF-8 exactos de `content`, `tags` es una lista (comas, comillas y acentos intactos), `source.uri`/`source.label` llevan el ID local y la generación, y `document_id` = UUIDv5(`project_id`, ID local, generación) es estable entre ejecuciones; tras borrar el estado local, `--check` reconstruye la generación desde `document_manifest` y obtiene el mismo `document_id`. *Comprobación:* test que recalcula hash e ID, borra el estado y reconcilia.
- [ ] [GWT] CA-07 — Dado un timeout tras `publish_document`, Cuando se reintenta, Entonces se consulta `document_status` antes de reenviar y el reenvío usa el mismo ID, versión y contenido; el servidor falso registra un solo documento. *Comprobación:* test de entrega incierta.
- [ ] [GWT] CA-08 — Dada una entrada que sale de `approved/`, Cuando se sincroniza, Entonces se consulta `document_status` primero; con `Resource not found` o `deleted: true` no se llama a `revoke_document`; en otro caso se llama con la versión siguiente. *Comprobación:* test con los tres estados remotos.
- [ ] [GWT] CA-09 — Dado un desfase entre local y remoto (documento ausente, versión distinta, hash distinto), Cuando se ejecuta `knowledge-sync.py --check`, Entonces recorre `document_manifest` con cursor hasta `has_more=false`, sale ≠ 0 con un `desfase` que nombra la identidad y el remedio, y no publica nada. *Comprobación:* test con manifiesto de varias páginas.
- [ ] [GWT] CA-10 — Dado un intent autorizado y Kairos sano, Cuando un agente ejecuta `knowledge-find.py --intent <intent>`, Entonces usa solo la clave de lectura, cada acierto trae `id`, `estado`, `evidencia`, `ruta` y la marca de dato no confiable, y un texto recuperado con forma de instrucción no cambia la salida del script (se presenta como dato). *Comprobación:* test con respuesta envenenada del servidor falso.
- [ ] [GWT] CA-11 — Dada solo una clave de lectura, Cuando se intenta publicar, revocar o enviar journal e hitos, Entonces no se llama a ninguna herramienta de escritura, se informa «sin clave de escritura» y la lectura sigue sana. *Comprobación:* test que verifica cero llamadas de escritura.
- [ ] [GWT] CA-12 — Dados `config.journal: true` y `capture_policy` con `capture_allowed: true` (con o sin cliente kairos instalado), Cuando llega un momento de envío, Entonces se envía un único `remember` por sesión con `event_type: summary`, `generate: false`, `payload.structured` válido contra `session-summary.v1` y sin campo `capture` ni etiquetas `capture:*`. Dado `capture_allowed: false`, Entonces no se llama a `remember`, el resumen queda en local y `/doctor` avisa de que un admin debe activar la captura. *Comprobación:* test de las dos ramas + validación con el esquema; el test no lee `.kairos/`.
- [ ] [GWT] CA-13 — Dado un evento episódico (journal o hito) enviado con timeout, Cuando se reintenta, Entonces reusa `event_id`, `item_id`, `version` y `occurred_at`; solo repite tras `event_status` con `found: false`; un `isError` no cuenta como ausencia. *Comprobación:* test de entrega incierta episódica.
- [ ] [GWT] CA-14 — Dado `config.hitos: true` y un ledger con una tarea cerrada, un veredicto de revisión y una retro, Cuando se envían los hitos, Entonces llegan exactamente 3 eventos con el mapeo `note`+`change`, `note`+`decision` y `learning`+`discovery`, nada más del ledger, y repetir el envío no crea eventos nuevos. Dada después la misma tarea reabierta y cerrada otra vez, Entonces llega un evento nuevo con otro `event_id` (número de ocurrencia) y ningún `Conflicting event or version`. *Comprobación:* test sobre un ledger de fixture con reapertura.
- [ ] [GWT] CA-15 — Dado un servidor que responde `isError` con `Rate limit exceeded [code=rate_limited retry_after=2]`, Cuando el cliente reintenta, Entonces no vuelve a llamar antes de 2 s y, si 2 s superan su plazo, reencola. *Comprobación:* test con reloj inyectado.
- [ ] [GWT] CA-16 — Dado un adaptador de fixture `type: "mcp-fixture"` que reutiliza el cliente MCP genérico con otro mapa de herramientas, Cuando se carga por `--backends-dir`, Entonces publica y lee sin tocar `knowledge-sync.py`, `backends/__init__.py` ni el cliente genérico. *Comprobación:* test de carga y diff vacío del núcleo.
- [ ] CA-17 — Ningún fichero nuevo o modificado nombra los backends retirados (salvo el antecedente histórico de `testing/retirada.md` y los CHANGELOG ya publicados). *Comprobación:* `git diff --name-only master...` filtrado con `grep -il` por los dos nombres retirados que lista `testing/retirada.md` → vacío.
- [ ] CA-18 — Funciona igual en Claude Code, Codex y OpenCode: ninguna pieza nueva tiene lógica por runtime y `python scripts/export-interop.py --check` sale 0. *Comprobación:* comando y `python scripts/lint_plugin.py` en verde.
- [ ] CA-19 — Todo texto enviado (documentos, journal, hitos, incluido `payload.structured`, que el servidor no redacta) pasa por `agent-kits/shared/redact.py`, que cubre al menos los patrones del hito B de Kairos (`mp_`, `sk_live_`, `glpat-`, `hf_`, `npm_`, `*_KEY`, `*_PASS`, `curl -u`, `Authorization: Basic`, cadenas de alta entropía). *Comprobación:* test con un ejemplo de cada patrón en una entrada aprobada y en un hito, que no aparece en la llamada.
- [ ] CA-20 — Integración real (la ejecuta la sesión kairos o el usuario contra su servidor): la lista de «Criterios de aceptación para el equipo consumidor» del repo knowledge-graphs (`docs/integration.md`) pasa, con versiones, IDs de prueba y resultados adjuntos en `testing/` sin claves. *Comprobación:* informe en `docs/roadmap/2026-11-26-kairos-memory/testing/`.
- [ ] [GWT] CA-21 — Dado un servidor cuyo `tools/list` no anuncia `revoke_document` y cuyo `serverInfo.version` es `0.0.0`, Cuando se ejecuta `/doctor`, Entonces solo la capacidad de revocación sale ⚠️ nombrando la herramienta; lectura, publicación, reconciliación y captura salen según sus mínimos; la versión no influye; las herramientas y campos de más (`extraction`, `redacted`, `capture_hash`, sobre `untrusted`/`warning`) se ignoran sin error. *Comprobación:* test con tres `tools/list` (completo, sin una herramienta, con herramientas extra).
- [ ] [GWT] CA-22 — Dada una entrada con lápida en Kairos que vuelve a `approved/`, Cuando se publica, Entonces se usa la generación siguiente (nuevo `document_id`), el informe lo avisa y el ID revocado no se envía. Dado un `Conflicting event or version` con `document_status.deleted: false`, Entonces se reporta como conflicto de contenido y no se sube la versión. *Comprobación:* test de las dos ramas del conflicto.
- [ ] [GWT] CA-23 — Dado cada uno de los mensajes de la tabla «Manejo de errores» (401 HTTP, `rate_limited`, `Daily write quota exceeded`, `Too many activity streams`, `Memory service temporarily unavailable`, `Conflicting event or version`, `Resource not found`, `Operation not permitted`, `Capture is disabled for this project`, `Structured observation does not match its schema`, los dos de privacy review y un texto desconocido), Cuando el cliente los recibe, Entonces los clasifica como dice la tabla (reintentable, permanente, ausencia confirmada o fallo) y ninguno se trata como éxito. *Comprobación:* test parametrizado con un caso por mensaje.
- [ ] [GWT] CA-24 — Dado un hito con `facts`, Cuando se construye el evento, Entonces valida en local contra `observation.v1` (8 campos, `type` del enum, límites), cada `evidence_quote` aparece literal en el contenido, no lleva `category: agent-activity` ni etiquetas `capture:*`; un documento inválido no se envía y queda como fallo permanente con la ruta del error. *Comprobación:* test con ejemplos válidos e inválidos del esquema.

## Pruebas

- Unitarias con TDD (Constitución): cliente MCP genérico, adaptador `kairos`, envío episódico, validador de config, clasificador de errores. Servidor MCP falso en proceso que reproduce `tools/list` variable, `Bearer`, 401, `isError` con los mensajes reales, `retry_after` en el texto, recorte de bytes, paginación y lápidas.
- Las `[GWT]` (CA-01..CA-16 y CA-21..CA-24) se traducen 1:1 a tests del repo (no E2E de navegador).
- Suites existentes que deben seguir en verde: `tests/test_hook_network_egress.py`, `tests/test_sync_write_gate.py`, suites de `skills/knowledge-services/scripts/`, `evals/check.py`, `scripts/lint_plugin.py`, `export-interop.py --check`.
- CA-20 es una prueba de integración manual contra el servidor real; no la sustituyen `/doctor`, un HTTP 200 ni las unitarias.

## Referencias

- Repo knowledge-graphs, `docs/contracts/kairos-mcp.json` (contrato MCP 0.4.1, 34 herramientas).
- Repo knowledge-graphs, `docs/integration.md`: «Conectar con kairos-mcp», «Dos flujos de escritura separados», «Capturar memoria con identidad estable», «Observaciones estructuradas con esquema versionado», «Publicar conocimiento aprobado», «Conciliar antes de reenviar», «Criterios de aceptación para el equipo consumidor».
- Repo knowledge-graphs, `docs/contracts/session-summary.v1.schema.json` y `docs/contracts/observation.v1.schema.json` (con ejemplos en `docs/contracts/examples/`).
- Repo knowledge-graphs, `docs/install.md` (captura `--capture off|summary|full`) y `client/lib/lifecycle-config.mjs:7-16` (configuración interna de la captura del cliente; no es contrato).
- Validación de la sesión kairos del 2026-11-26 (servidor y contrato 0.4.1, rama `feat/access-control`): repo knowledge-graphs, `server/memory_platform/store_auth.py:163-174` (`capture_allowed`), `server/memory_platform/store_ingest.py:164-165` (captura `off` rechaza `remember`), `server/memory_platform/store_documents.py:112-113` (sin republicación tras lápida).
- `skills/knowledge-services/backends/README.md` (contrato de 6 funciones y opcionales `puede_leer`/`consultar`).
- `skills/knowledge-services/references/add-backend.md` y `references/project-integration.md`.
- `docs/CONSTITUTION.md`, líneas 20 (sin red en hooks), 34 (`redact.py`, sin secretos) y 37 (red opt-in, local/privada por defecto, solo lo aprobado).
- `docs/roadmap/2026-11-10-plugin-audit-2/testing/retirada.md` (antecedente: commit recuperable del cliente MCP retirado, que no enviaba `Bearer`).
- Iniciativas previas: `docs/roadmap/2026-09-15-knowledge-services/`, `2026-10-31-memory-integrations/`, `2026-11-03-knowledge-verification/`.

## Decisiones confirmadas (revisión del usuario · 2026-11-18)

1. Transporte MCP, no REST. **Confirmado.**
2. Opt-in en `/setup`, comprobado por `/doctor`. **Confirmado.**
3. ~~Journal solo si está configurado y sin duplicar la captura del cliente kairos.~~ **Sustituida** por la decisión 5 del 2026-11-26.
4. Solo se publica lo aprobado. **Confirmado.**
5. Un `project_id` fijado en `/setup`. **Confirmado.**
6. Claves separadas de lectura y escritura. **Confirmado.** (Scopes corregidos tras la validación de kairos: la de escritura incluye `read`.)
7. Del ledger, solo hitos; `tasks.md` sigue canónico. **Confirmado.**
8. Sin acoplar el plugin: Kairos es el primer adaptador por `type`. **Confirmado.**
9. Nada relacionado con los backends retirados se reutiliza por nombre; el cliente MCP se reescribe genérico (2026-11-26). **Confirmado.**

## Decisiones del usuario · 2026-11-26

1. **El adaptador `kairos` va incluido en el plugin** (`backends/kairos.py` + cliente MCP genérico compartido), inactivo hasta `/setup`. Motivo: el contrato de Kairos tiene reglas finas (idempotencia por versión, SHA-256 exacto, lápida sin resurrección, reconciliación por manifiesto, `retry_after`) y una sola implementación probada se actualiza con cada release del plugin. Revierte en parte la política de la 4.0.0 «sin adaptadores incluidos»; el marco y el cliente genérico siguen permitiendo enchufar otros backends.
2. **Sin agente nuevo**: los agentes actuales consultan con la clave de lectura vía `knowledge-find.py --intent`, con respaldo local.
3. **Kairos puede estar en un servidor cloud.** El host remoto se admite con opt-in explícito en `/setup` (`allow_remote: true` + URL): exige `https`, sin redirecciones automáticas y bloqueando direcciones de metadatos (IMDS) y enlaces locales. Sin el opt-in, solo hosts locales/privados (`docs/CONSTITUTION.md:37`).
4. **Momentos de envío del journal y de los hitos**: paso explícito en la Fase 6 de `/dev-cycle` y en `/retro`, y una orden manual en cualquier momento; ambos drenan lo que `SessionEnd` dejó en local. Los hooks siguen sin red. (La frase original «si el cliente kairos captura las sesiones, el plugin no envía el journal» queda **sustituida** por la decisión 5.)
5. **El plugin envía siempre su resumen de sesión y los hitos cuando `capture_policy` (con la clave de escritura) da `capture_allowed: true`**, esté o no instalado el cliente kairos: su captura nunca envía resúmenes, así que no hay duplicado. Resumen: `session-summary.v1`, `event_type: summary`, `generate: false`. Si la captura del proyecto está en `off`, journal e hitos se quedan en local y `/doctor` avisa de que un admin debe activar la captura en Kairos. Sustituye a la decisión 3 del 2026-11-18 y a la parte afectada de la decisión 4 de hoy.
6. **Entrada revocada que vuelve a `approved/`** (cerrada con la validación de kairos): nuevo `document_id` con la generación siguiente (obligatorio: el servidor no permite republicar un ID con lápida), aviso en el informe de sync, y el ID local y la generación en `source.uri`/`source.label` para reconstruirla desde `document_manifest`.

## Preguntas abiertas

Ninguna.

## Supuestos

- **Hecho técnico:** el marco carga adaptadores por `type` y valida las 6 funciones; `consultar` es lo que hace enrutable la lectura — `skills/knowledge-services/backends/README.md` (tablas «Las 6 funciones» y «Funciones OPCIONALES»).
- **Hecho técnico:** el plugin no incluye adaptadores desde la 4.0.0; esta iniciativa incluye el primero — `skills/knowledge-services/backends/README.md` («El plugin no incluye adaptadores»).
- **Hecho técnico:** la red está vetada en hooks y toda capacidad con red es opt-in y local/privada por defecto — `docs/CONSTITUTION.md:20` y `:37`.
- **Hecho técnico:** el router de lectura exige `puede_leer` con `puede: true` antes de consultar — `agent-kits/shared/knowledge-find.py:1722`.
- **Hecho técnico (validado por kairos):** los scopes de una clave no se pueden conocer por MCP. `projects` no los devuelve; `capture_policy` exige `read` y da `capture_allowed: true` solo con `write` y política distinta de `off`. `publish`/`validate` no se pueden verificar sin escribir — repo knowledge-graphs, `server/memory_platform/store_auth.py:163-174`.
- **Hecho técnico (validado por kairos):** con la captura en `off`, `remember` rechaza todo `event_type` salvo `delete` con `Capture is disabled for this project`, sea envío explícito o automático; solo un admin cambia la política por `/v1` — repo knowledge-graphs, `server/memory_platform/store_ingest.py:164-165`.
- **Hecho técnico (validado por kairos):** tras una lápida no hay versión que permita republicar el mismo ID (`Conflicting event or version`); se distingue con `document_status.deleted` — repo knowledge-graphs, `server/memory_platform/store_documents.py:112-113`.
- **Hecho técnico (validado por kairos):** el servidor acepta cualquier versión de UUID como `document_id` y lo normaliza a minúsculas con guiones; la clave primaria es (`project_id`, `id`).
- **Hecho técnico (validado por kairos):** la captura del cliente kairos nunca envía `session-summary.v1`; en modo `summary` envía metadatos de ciclo de vida con `category: agent-activity` — repo knowledge-graphs, `client/lib/capture.mjs:64-78`. Su configuración (`.kairos/installation.json`, esquema en `client/lib/lifecycle-config.mjs:7-16`) es interna y no forma parte del contrato.
- **Hecho técnico (validado por kairos):** por MCP no llegan códigos ni cabecera `Retry-After`; los límites llegan como texto `… [code=rate_limited retry_after=N]` y el 5xx como `Memory service temporarily unavailable` sin plazo. Una clave inválida, revocada o caducada da HTTP 401 a toda la petición.
- **Hecho técnico (validado por kairos):** el contrato MCP es estrictamente aditivo (34 herramientas en el mismo orden; solo se añaden campos opcionales) y `serverInfo.version` no es fiable (el MCP interno en desuso devuelve la del SDK; falta de `mcp/VERSION` → `0.0.0`).
- **Hecho técnico:** el servidor no redacta `payload.structured`: un secreto ahí da 422 y rechaza el evento entero; el resto del evento sí se redacta (`redacted: true` en el recibo) — repo knowledge-graphs, `docs/integration.md` («Observaciones estructuradas con esquema versionado»).
- **Hecho técnico:** el cliente MCP retirado no enviaba `Bearer` — `docs/roadmap/2026-11-10-plugin-audit-2/testing/retirada.md`.
- **Riesgo / supuesto de calendario:** Kairos tiene en curso tres hitos sin fechas (van por la fase 3 de 18). El contrato MCP no cambia en toda esa iniciativa, pero el comportamiento sí:

  | Hito | Qué llega | Efecto en esta spec |
  |---|---|---|
  | A (fases 4-5) | `last_used_at`, rotación `replaced_by` (24 h de gracia; luego 401); 429 del login HTTP por IP | El 401 tras rotación debe dar el remedio correcto; el login HTTP no lo usa el plugin |
  | B (fases 8-11) | Redacción ampliada (patrones de CA-19); tasa por clave, cuota diaria de escritura, tope de flujos, y su paso por kairos-mcp | CA-15, CA-19 y CA-23 se prueban contra el servidor falso hasta que B exista; CA-20 los reconfirmará en real |
  | C (fase 13) | `capabilities` en `/v1/auth/me` | Fuera de alcance (es `/v1`); una spec futura podría usarlo para verificar scopes |

  Lo confirmaría la sesión kairos al cerrar cada hito.
- **Incógnita:** el presupuesto y plazo no se han fijado; los dará `evaluator`.
