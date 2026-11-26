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
  inicio: 2026-11-26T12:50:29Z
  fin: 2026-11-26T13:25:29Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-5857b17b9041433db03fd49765d986be
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 58, salida: 21761, cache_creacion: 429568, cache_lectura: 4743835 }
  eur: 3.25
  horas_ia: 0.85
  duracion: 51m
  ratio_usado: 531798.5
---

# Kairos como memoria opcional de los agentes

> **Evaluación:** pendiente
> **Plan de implementación:** pendiente

> **Terminología:**
> - **Kairos**: servidor de memoria del usuario (repo knowledge-graphs). Habla MCP por *streamable HTTP* en exactamente `<base>/mcp/` (con barra final), con credencial `Authorization: Bearer`. Contrato: repo knowledge-graphs, `docs/contracts/kairos-mcp.json` (MCP 0.4.1, 34 herramientas, contrato estrictamente aditivo).
> - **Adaptador**: fichero `backends/<type>.py` del marco `knowledge-services` con las 6 funciones `health/plan/apply/verify/rebuild/revoke` (+ opcionales `puede_leer`/`consultar`).
> - **Cliente MCP genérico**: módulo Python del plugin que abre sesión MCP por HTTP, envía `Bearer` y llama herramientas por nombre. No sabe nada de Kairos.
> - **Capacidad**: grupo de operaciones del adaptador (lectura, publicación, revocación, reconciliación, captura) que se habilita o degrada por separado. Que exista se ve en `tools/list`; que funcione, solo con una llamada real.
> - **Publicación documental**: envío de `docs/knowledge/approved/` con `publish_document`/`revoke_document`.
> - **Memoria episódica**: eventos con `remember` (resumen de sesión del journal, hitos del ledger).
> - **Generación documental**: sufijo que entra en el UUIDv5 del `document_id`; cambia solo cuando una entrada revocada (lápida) vuelve a `approved/`.
> - **Ocurrencia de hito**: número de veces que un mismo hito (p. ej. «T-07 cerrada») ha sucedido en el ledger; reabrir y volver a cerrar una tarea da la ocurrencia 2.
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
knowledge-graphs) validó este diseño dos veces contra el servidor y el contrato 0.4.1 el
2026-11-26 (rama `feat/access-control`). Este plugin no escribe en ese repo.

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

Decisiones técnicas (análisis y orquestador), validadas por la sesión kairos:

| Decisión | Elección | Motivo |
|---|---|---|
| Identidad documental | **UUIDv5** de (`project_id`, ID local, generación). La generación empieza en 1 y **sube obligatoriamente** cuando una entrada con lápida vuelve a `approved/`. `source.uri` = `custom-agents:<project_id>/<id_local>#g<n>` (sin espacios, ≤ 2.000 caracteres, sin aspecto de secreto) | El servidor no permite republicar un ID borrado. `document_manifest` devuelve `source` sin transformar, así que la generación se reconstruye aunque se pierda el estado local |
| Identidad de hitos | **`item_id` nuevo por ocurrencia** = UUIDv5(`project_id`, slug, tarea, estado, nº de ocurrencia), siempre con **`version: 1`**; `event_id` también estable por ocurrencia | No exige conocer la versión remota; reabrir una tarea no choca con `Conflicting event or version` |
| Estado de validación de eventos | **`validation_status: observed`** en journal e hitos | Con `validated`, `remember` exigiría scope `validate` y evidencia |
| Evidencia de publicación | `validation` = `{status: "validated", evidence: [≥ 1], validated_by}`; la **evidencia sale de la aprobación de `knowledge-curator`** (ID de la decisión del curator y sus fuentes) | El servidor rechaza un documento sin evidencia; la aprobación local es la que da autoridad |
| Salud | **Por capacidad, con una llamada real de solo lectura**; `tools/list` solo dice si la herramienta existe; nunca `serverInfo.version` | `tools/list` es estático (lista las 34 a cualquier `Bearer`) y no valida la clave si la API no responde |
| Errores | **Regex anclada sobre el mensaje entero** de `isError` con `re.fullmatch` (`Error executing tool \S+: <mensaje>`; nunca `$`, que admite un salto de línea final), nunca subcadena; los errores HTTP (400, 401, 403, 406, 413, 421, 429 de proxy y 502/503/504 sin JSON del nginx) son de toda la petición y se clasifican por código de estado | Por MCP no llegan códigos; el texto es el contrato |
| Redacción | **Antes de calcular el hash y antes de encolar**, sustituyendo el **valor completo** (esquema incluido: `Authorization: [REDACTADO]`) por un marcador que el servidor acepte como valor seguro (`[REDACTADO]` o `[REDACTED]` exactos; el marcador concreto es la Pregunta abierta 1); la outbox guarda el evento ya redactado y no se vuelve a redactar | Re-redactar con patrones nuevos cambia el contenido y da `Conflicting event or version` |
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
| Plazo de lectura y diagnóstico | `config.timeout_ms` | 5.000 | Respeta el tope de `/doctor` |
| Plazo de escritura | `config.write_timeout_ms` | 40.000 | Por petición de escritura; siempre **< 45.000** (el nginx de la entrada web corta a 45 s con `proxy_read_timeout`) y por encima de los ~35 s que puede tardar el servidor; un timeout tras enviar es entrega incierta |
| Tope del cuerpo enviado | constante del cliente | 262.144 bytes | Sobre el **cuerpo HTTP completo** (sobre JSON-RPC incluido), serializado **una sola vez** con `ensure_ascii=False`; vale para `publish_document` y `remember` |
| Tope de la respuesta leída | constante del cliente | 1 MiB | Mayor que el recorte del servidor (262.144 bytes con marca) |
| Página del manifiesto | constante del adaptador | 50 | `limit` ≤ 50: con 100 la respuesta puede pasar del recorte y perder `structuredContent` |

## Arquitectura y componentes

| Pieza | Nueva / reutilizada | Papel |
|---|---|---|
| Cliente MCP genérico (Python, sin dependencias) | **Nueva** (reescritura genérica, sin reutilizar nombres retirados) | `initialize`, `tools/list`, `tools/call` contra `<base>/mcp/` con `Authorization: Bearer`, `Content-Type: application/json` y `Accept: application/json, text/event-stream`, **sin** cabecera `Origin`; guardarraíl de host (local/privado por defecto, sin redirecciones, sin proxy del entorno); topes de cuerpo y respuesta; plazos separados de lectura y escritura; clasificación de errores por regex anclada; extrae `code=`/`retry_after=` del texto; acepta `Retry-After` en un HTTP 429 de un proxy; backoff propio cuando no hay plazo; aviso si la respuesta trae `Deprecation: true`; acepta el sobre `untrusted`/`warning` y campos opcionales de más; marca todo resultado como dato no confiable |
| Adaptador `kairos` (`skills/knowledge-services/backends/kairos.py`) | **Nuevo, incluido en el plugin** | Las 6 funciones + `puede_leer`/`consultar`. Salud por capacidad. Mapea a `capture_policy`, `search`, `details`, `context`, `publish_document`, `document_status`, `document_manifest`, `revoke_document` |
| Envío episódico (journal e hitos) | **Nuevo** (script determinista con tests) | `capture_policy` → `remember` → `event_status`; identidad estable por evento y ocurrencia; validación local con `session-summary.v1` y `observation.v1` |
| `skills/knowledge-services/scripts/knowledge-sync.py` | Reutilizado sin cambios de núcleo | Carga por `type`, routing fail-closed, outbox, `--check/--dry-run/--rebuild` |
| `agent-kits/shared/outbox.py` | Reutilizado | Dos colas (documental y episódica) con el envío ya redactado y serializado |
| `agent-kits/shared/knowledge-find.py --intent` | Reutilizado | Router de lectura con respaldo local y motivo |
| `agent-kits/shared/redact.py` | Ampliado | Todo texto enviado pasa por aquí antes de hashear y encolar; cubre los patrones actuales del servidor, su lista de nombres de secreto y los del hito B de Kairos; marcador según la Pregunta abierta 1 |
| `agent-kits/shared/capabilities.py`, `commands/setup.md`, `agent-kits/shared/doctor.py` | Ampliados | Paso guiado de configuración y fila de diagnóstico por capacidad, con remedio |
| `commands/dev-cycle.md` (Fase 6), `commands/retro.md` | Ampliados | Paso explícito de envío episódico (journal e hitos) |
| `hooks/` | **Sin cambios de red** | El journal se sigue escribiendo en local; el envío ocurre fuera de los hooks |

**Capacidades: herramientas que deben existir y llamada real que las comprueba**

| Capacidad | Herramientas en `tools/list` | Comprobación real (solo lectura) | Clave |
|---|---|---|---|
| Lectura | `capture_policy`, `search`, `details`, `context` (`projects` opcional) | `capture_policy(project_id)` responde sin error (más fiable que buscar el proyecto en `projects`, que corta a 100) | lectura |
| Publicación | `publish_document`, `document_status` | `capture_policy(project_id)` con la clave de escritura; `publish`/`validate` **no verificables sin publicar** | escritura |
| Revocación | `revoke_document` | Igual que publicación | escritura |
| Reconciliación | `document_manifest` + `event_status` con propiedad `project_id` en su esquema | `document_manifest(project_id, limit: 1)` | escritura |
| Captura (journal e hitos) | `capture_policy`, `remember`, `event_status` | `capture_policy`: `capture_mode` y `capture_allowed` | escritura con `write` |

La lectura no depende de la escritura: si falta una capacidad de escritura, la lectura sigue sana.

## Flujo (paso a paso)

**Configuración (`/setup`)**
1. El usuario elige activar Kairos. `/setup` pide URL base, `project_id`, rutas de las dos claves, categorías a publicar, journal e hitos.
2. Valida formato (`project_id`, URL, host permitido, ficheros de clave existen y están fuera del proyecto). No conecta.
3. Escribe `backends.<id>` en `taxonomy.json` y propone `/doctor` para la comprobación en vivo.

**Diagnóstico (`/doctor`)**
4. Con la clave de lectura: `initialize` + `tools/list` (existencia) y `capture_policy(project_id)` (funciona). Con la de escritura: `capture_policy` y `document_manifest(limit: 1)`. Veredicto por capacidad. No mira `serverInfo.version`. Nunca escribe.
5. Avisos con remedio:
   - `publish`/`validate` no se verifican sin publicar: «no verificable sin publicar».
   - `capture_mode == "off"` con journal o hitos activos: «la captura del proyecto está apagada; un admin debe activarla en Kairos».
   - `capture_mode != "off"` y `capture_allowed: false`: «a la clave de escritura, o a su usuario en el proyecto, le falta `write`» (el permiso efectivo es la intersección de ambos).
   - HTTP 421: «el servidor no admite este host; el operador añade el origen exacto (esquema, host y puerto si no es el por defecto, p. ej. `https://kairos.example.com`) a `MEMORY_ALLOWED_ORIGINS` en el `.env` del despliegue —Compose lo pasa a `KAIROS_ALLOWED_ORIGINS`— y recrea el servicio MCP; si hay un proxy o terminador TLS propio delante, debe conservar el `Host` original». HTTP 403 por origen: mismo remedio. El cliente envía el `Host` estándar de la URL (nunca lo sobrescribe) y ningún `Origin`.
   - Respuesta con `Deprecation: true`: «`base_url` apunta al MCP interno heredado (se retira en Kairos 0.5.0); usa la entrada `/mcp/` de kairos-mcp».

**Lectura (agentes)**
6. Un agente llama `knowledge-find.py --intent <intent> "<texto>"`. Si el intent está autorizado y `puede_leer` da `true`, el adaptador llama `search`/`context` con la clave de lectura y `project_ids: [<project_id>]` (lista).
7. Cada acierto vuelve marcado como **dato no confiable**, con procedencia. Si Kairos falla o responde parcial, la respuesta incluye el motivo y los aciertos locales.

**Publicación de lo aprobado**
8. `knowledge-sync.py --backend <id> --dry-run` muestra qué se publicará (solo `approved/` con routing).
9. Sin `--dry-run`, drena la outbox documental y construye cada documento así:
   - `content` redactado **antes** de calcular el hash; `source.sha256` = SHA-256 de esos bytes UTF-8 exactos.
   - `document_id` = UUIDv5(`project_id`, ID local, generación); `source.uri` = `custom-agents:<project_id>/<id_local>#g<n>`.
   - `title` obligatorio; `tags` como lista; versión secuencial.
   - `validation` = `{status: "validated", evidence: [1..20 elementos de ≤ 4.000 caracteres], validated_by}`; la evidencia sale de la aprobación de `knowledge-curator`. Sin evidencia no se envía.
   - `source.sha256` es obligatorio en la práctica: sin él el servidor responde `Source SHA-256 must match the exact UTF-8 content`.
   - Serializa con `ensure_ascii=False` y comprueba el tope de 262.144 bytes; si no cabe, fallo permanente de esa entrada.
   - El documento completo queda guardado en la outbox: un reenvío idempotente exige el documento **entero** idéntico (título, categoría, tags, `source`, `validation`) y la **misma clave de escritura** (el servidor fija `validated_by` al actor de la clave).
10. La aceptación no es el fin: `document_status` hasta confirmar versión, hash y trabajos. Un job `failed` es terminal: se reporta su `error_code` y no se reencola (`superseded` no existe en `document_status`; solo en `event_status`).
11. Una entrada que sale de `approved/`: primero `document_status`. `deleted: true` → no hace nada. `Resource not found` → «nada que revocar» **solo** si en la misma ejecución, con la misma clave, otra llamada sobre ese proyecto ya funcionó; si no, es un error de configuración (clave sin el proyecto o sin permisos). En otro caso, `revoke_document` con la versión siguiente.
12. Una entrada con lápida que vuelve a `approved/` se publica con la generación siguiente (ID nuevo) y se avisa en el informe. El ID revocado nunca se republica.
13. `--check`: `document_manifest` con `limit` ≤ 50, pasando `next_cursor` como `cursor` hasta agotar; compara `source_sha256` (nunca `canonical_hash`, que es interno y depende del actor), versión y lápidas (el manifiesto también las devuelve); nombra el remedio sin reenviar a ciegas. Si se perdió el estado local, la generación se reconstruye desde `source.uri`.

**Journal e hitos (memoria episódica)**
14. Momentos de envío: paso explícito en la Fase 6 de `/dev-cycle`, en `/retro` y con una orden manual. Cada envío drena lo que `SessionEnd` dejó en local.
15. Antes de enviar, `capture_policy` con la clave de escritura. Con `capture_allowed: false`, nada nuevo sale: journal e hitos se quedan en local y `/doctor` lo avisa. Los eventos ya encolados de antes sí se pueden conciliar con `event_status` (no depende de la política).
16. Con `capture_allowed: true` y `config.journal: true`: un `remember` por sesión con `event_type: summary`, `generate: false`, `validation_status: observed`, `payload.title` (≤ 500, p. ej. «Sesión <fecha> · <slug>»), `payload.content` (≤ 100.000, el resumen en texto), `session_id` (el `session_id` del journal) y `agent_id` (`custom-agents`), ambos ≤ 200 y sin aspecto de secreto, y `payload.structured` `session-summary.v1`. Sin campo `capture` ni etiquetas `capture:*`.
17. Con `config.hitos: true`, cada hito nuevo del ledger es un `remember` con `validation_status: observed`:

    | Hito | `event_type` | `observation.v1.type` |
    |---|---|---|
    | Tarea cerrada | `note` | `change` |
    | Veredicto de revisión o decisión | `note` | `decision` |
    | Retro | `learning` | `discovery` |

    - Identidad: `item_id` = UUIDv5(`project_id`, slug, tarea, estado, nº de ocurrencia) con `version: 1`; `event_id` estable por ocurrencia.
    - Sin `category: agent-activity` y sin etiquetas `capture:*`.
    - `payload.structured.facts[]` (`observation.v1`: `statement`, `evidence_quote` ≤ 2.000): el plugin comprueba que cada cita aparece literal en `narrative` (el servidor no lo comprueba).
    - Si se usan `payload.facts[]` (máximo 30; `subject` 1-300, `predicate` 1-200, `object` 1-2.000, `evidence_quote` ≤ 4.000; `valid_from`/`valid_until` con zona horaria y en orden): cada cita debe aparecer literal en `content + "
" + problem + "
" + correction` **después** de la redacción del servidor (el servidor lo exige). Como la redacción local va antes, la cita se toma del texto ya redactado.
    - Límites de `structured`: 1.000 nodos como máximo, profundidad ≤ 8, `concepts` y `files_*` sin repetidos.
18. Cada evento se redacta y serializa **una vez**, antes de encolarlo. El reintento reenvía ese mismo evento entero, sin volver a redactar.
19. `event_status` (con `project_id`) hasta `complete`. `failed` o recibo `superseded` son terminales (se reporta `error_code`, no se reencola). Pendiente o incierto → se queda en la outbox episódica. En `event_status`, `Resource not found` significa proyecto no accesible, no evento ausente; la ausencia es solo `{found: false}`.

## Alcance

- **Dentro (esta iteración):**
  - Cliente MCP genérico en Python (HTTP *streamable*, cabeceras requeridas, `Bearer`, guardarraíl de host, topes de cuerpo y respuesta, plazos de lectura y escritura, errores por regex anclada, `retry_after`, backoff propio, aviso de `Deprecation`), sin dependencias externas, con servidor MCP falso para los tests.
  - Adaptador `kairos` incluido en el plugin, con las 6 funciones del contrato, `puede_leer`/`consultar` y salud por capacidad con llamada real.
  - Publicación de `approved/` (con modo `resumen`) con evidencia del curator, revocación con lápida y comprobación previa, generaciones documentales, reconciliación por `document_manifest`, `--rebuild`, jobs terminales.
  - Lectura vía `knowledge-find.py --intent` con respaldo local y marca de dato no confiable.
  - Envío de journal (`session-summary.v1`) e hitos del ledger (`observation.v1`) cuando `capture_allowed: true`.
  - Dos outbox separadas, idempotencia estricta y reconciliación tras entrega incierta.
  - Redacción previa (`redact.py`) con los patrones actuales del servidor y los del hito B de Kairos.
  - `/setup` (paso guiado), `/doctor` (fila por capacidad con veredicto y remedio), `capabilities.py`, paso de envío en `/dev-cycle` Fase 6 y `/retro`.
  - Documentación: `skills/knowledge-services/references/` (cómo activar Kairos y cómo añadir otro MCP de memoria), `backends/README.md` y `SKILL.md` (ya hay un adaptador incluido), CHANGELOG EN/ES, regeneración de `interop/`.
- **Fuera (siguientes specs):**
  - Cambios en el servidor Kairos o en su cliente `kairos` (repo knowledge-graphs).
  - Instalar el cliente `kairos`, crear claves, cambiar la política de captura, añadir orígenes permitidos o reindexar: son acciones del usuario, de un admin o del operador. El plugin las **nombra**, no las ejecuta.
  - REST `/v1` (incluido `GET /v1/auth/me` para leer scopes), sesión del portal, contraseña de admin o `bootstrap_password`.
  - Detectar la instalación del cliente kairos (`.kairos/installation.json` no es contrato).
  - Enviar candidatas, el ledger entero, transcripciones o prompts.
  - Herramientas de corpus, observaciones, equipo y `work_state_*` de Kairos.
  - Red desde hooks; lectura automática de Kairos en `SessionStart`.
  - Un segundo adaptador MCP real (se deja documentado cómo añadirlo y probado con un fixture).
  - Cualquier pieza, nombre, test o fixture con el nombre de los backends retirados.

## Manejo de errores

Dos familias. **Errores HTTP de toda la petición** (no llegan como `isError`): 400, 401, 403, 406,
413, 421, 429 (si hay un proxy) y 502/503/504 del nginx de la entrada web, que llegan **sin cuerpo JSON** (502: kairos-mcp caído; 504: tras 45 s de `proxy_read_timeout`). Se clasifican por **código de estado**, nunca por el cuerpo (el 413 del nginx viene en HTML). **Errores de herramienta**: `isError` con el texto
`Error executing tool <x>: <mensaje>`; el cliente compara con una regex **anclada sobre el mensaje
entero** con `re.fullmatch` (o `\Z`; nunca `$`, que admite un salto de línea final), nunca por subcadena. Los errores de validación de
entrada llegan **sin** ese prefijo, como `Input validation error: …`.

| Caso (texto o señal) | Clase | Comportamiento |
|---|---|---|
| HTTP 401 (clave inválida, revocada, caducada o rotada; no se distinguen) | Configuración | «Clave rechazada» con el remedio (renovar en el portal); nunca imprime la clave; escritura reencola |
| HTTP 400 / 406 (faltan `Content-Type` o `Accept`) | Defecto del cliente | Fallo permanente; no debería ocurrir (CA-03) |
| HTTP 413 (cuerpo > 262.144 bytes; del servidor en JSON o del nginx en HTML) | Permanente | Fallo de esa entrada; no se reintenta igual |
| HTTP 502 / 503 / 504 sin JSON (nginx) | Reintentable / incierto | Backoff propio. Si llega **después de enviar una escritura**, es entrega incierta: se concilia con `document_status`/`event_status`; nunca se descarta |
| HTTP 421 (host no admitido) / 403 (`Origin` no admitido) | Configuración | Remedio al operador en `/doctor` (`MEMORY_ALLOWED_ORIGINS` del `.env` → `KAIROS_ALLOWED_ORIGINS`; recrear el servicio MCP; proxy que conserve el `Host`) |
| HTTP 429 con `Retry-After` (proxy) | Reintentable | Espera el plazo; si supera el de escritura, reencola |
| `Rate limit exceeded [code=rate_limited retry_after=N]` | Reintentable | `re.fullmatch(r"Error executing tool \S+: Rate limit exceeded \[code=rate_limited retry_after=(\d+)\]")`; no reintenta antes de N s; si N supera el plazo, reencola |
| Mensaje que empieza por `Daily write quota exceeded` | Reintentable (escrituras) | Reconoce por prefijo; extrae `code=`/`retry_after=` con regex tolerante si aparecen; sin plazo, backoff largo o hasta el cambio de día UTC. La lectura sigue |
| Mensaje que empieza por `Too many activity streams` | Reintentable | Igual que la cuota (por MCP no debería llegar: ninguna herramienta abre SSE) |
| `Memory service temporarily unavailable`, `The store is busy; retry shortly`, `The store took too long to answer; retry shortly`, `Semantic query exceeded its time budget` | Reintentable | Backoff propio; lectura degrada a local con motivo; escritura reencola. El ciclo nunca se bloquea |
| Conexión rechazada o timeout de red | Reintentable / incierto | Igual que la fila anterior; tras enviar una escritura, es entrega incierta |
| `Conflicting event or version` en `publish_document` | Según estado | `document_status`: `deleted: true` → lápida → generación siguiente; si no, conflicto de contenido → se reporta, se detiene esa entrada, sin subir la versión |
| `Conflicting event or version` en `remember` | Permanente | Conflicto de identidad: se reporta; nunca un UUID nuevo para el mismo evento |
| `Resource not found` | Según contexto | En `document_status`: ausencia del documento solo si otra llamada con la misma clave sobre el proyecto ya funcionó (paso 11); si no, configuración. En `event_status`: proyecto no accesible (configuración) |
| `Operation not permitted` | Configuración | Falta scope o proyecto: se nombra el scope que la operación necesita |
| `Capture is disabled for this project` | Configuración | Journal e hitos se quedan en local; aviso en `/doctor` |
| `Unknown tool: <x>` | Configuración | La capacidad pasa a `degradado` nombrando la herramienta |
| `Input validation error: …`, `Request does not match the API contract`, `Timezone is required` | Permanente | Defecto del cliente: fallo de esa operación con el mensaje |
| `Structured observation does not match its schema: …`, `Fact evidence must quote its source literally`, `Invalid grounded fact`, `At most 30 grounded facts are permitted` | Permanente | Fallo de ese evento con el mensaje; se valida en local antes de enviar para evitarlo |
| `Source SHA-256 must match the exact UTF-8 content`, `Published documents require source hash and validation evidence`, `Published content must be valid UTF-8 text` | Permanente | Fallo de esa entrada; indica un defecto del adaptador |
| Privacidad, lista literal comparada con `re.fullmatch`: `Approved sources require privacy review before publication`, `Validated sources require privacy review before capture`, `Sensitive capture metadata requires privacy review`, `Sensitive source metadata requires privacy review`, `Generated capture metadata requires privacy review`, la forma dinámica `<campo> requires privacy review` (regex `[A-Za-z][A-Za-z0-9 _.-]* requires privacy review`), `Private blocks must use balanced private tags`, `Private key blocks must be complete before redaction`, `Privacy input exceeds its supported bound`, `Secret assignments must have balanced quotes`, `Capture text exceeds its supported bound`, `Serialized privacy input is too deeply nested` | Permanente | Fallo con motivo; se revisa la redacción previa; no se reenvía igual |
| `Fact validity requires timezone-aware timestamps`, `Fact validity interval is reversed` | Permanente | Defecto del cliente en `payload.facts`; se valida en local antes de enviar |
| Recibo de `remember` con `redacted: true` | Aviso | El envío se aceptó, pero la redacción local se quedó corta: aviso con el ID |
| Job `failed` o recibo `superseded` | Terminal | Se reporta `error_code`; no se reencola |
| `isError` con cualquier otro texto | Fallo | Fallo de esa operación, **no** ausencia |
| Respuesta con `Deprecation: true` | Aviso | `/doctor` avisa de endpoint heredado |
| Respuesta recortada (marca de tope) o no-JSON | Fallo | Se descarta con motivo; nunca se inventa contenido |
| Host no permitido o redirección | Configuración | Se rechaza antes de conectar; no se siguen redirecciones |
| Clave de solo lectura | Configuración | No se llama a ninguna herramienta de escritura; «sin clave de escritura» |

## Criterios de aceptación

Cada criterio dice cómo se comprueba. Los `[GWT]` se prueban con el servidor MCP falso salvo
que se indique «integración real».

- [ ] [GWT] CA-01 — Dado un proyecto sin `backends.<id>` de tipo `kairos`, Cuando se ejecutan `/doctor`, `knowledge-find.py` y los hooks, Entonces no se abre ninguna conexión de red y la capacidad sale «desactivada» (no error). *Comprobación:* test con socket espía + `tests/test_hook_network_egress.py` en verde.
- [ ] [GWT] CA-02 — Dado `/setup` con un `project_id` inválido, un host público sin `allow_remote`, un host remoto con `http` o una ruta de clave dentro del proyecto, Cuando se valida la config, Entonces se rechaza con un mensaje que nombra el campo y no se escribe `taxonomy.json`. *Comprobación:* test del validador con los cuatro casos.
- [ ] [GWT] CA-03 — Dado el servidor falso que exige `Bearer`, Cuando el cliente MCP genérico llama `initialize`, `tools/list` y `tools/call`, Entonces todas las peticiones van a `<base>/mcp/` con barra final y llevan `Authorization: Bearer <clave>`, `Content-Type: application/json` y `Accept: application/json, text/event-stream`, ninguna lleva `Origin`, no se exige `Mcp-Session-Id` (el servidor no tiene estado y responde JSON), `MCP-Protocol-Version` es la negociada en `initialize` o no se envía, la clave no aparece en salidas, logs ni outbox, y no se siguen redirecciones. *Comprobación:* test del cliente que inspecciona cabeceras + búsqueda del valor de la clave en todo lo escrito.
- [ ] [GWT] CA-04 — Dado Kairos caído o respondiendo `Memory service temporarily unavailable`, `The store is busy; retry shortly`, `The store took too long to answer; retry shortly` o `Semantic query exceeded its time budget`, o con HTTP 502/503/504 sin JSON del nginx, Cuando se ejecutan `/doctor`, una lectura con `--intent` y `knowledge-sync.py`, Entonces `/doctor` marca ⚠️ con el remedio, la lectura devuelve los aciertos locales con el motivo y el sync reencola con backoff propio sin dead-letter; todos acaban dentro de su plazo y con exit 0 donde el ciclo lo exige. Dado un 502/503/504 recibido **después** de enviar una escritura, Entonces se trata como entrega incierta y se concilia con `document_status`/`event_status`, nunca se descarta. *Comprobación:* test con servidor apagado, uno por mensaje y uno por código HTTP antes y después de enviar.
- [ ] [GWT] CA-05 — Dado `approved/` con 3 entradas (una sin routing) y `candidates/` con 2, Cuando se publica, Entonces solo llegan 2 `publish_document` (las enrutadas) y ninguna candidata. *Comprobación:* registro de llamadas del servidor falso.
- [ ] [GWT] CA-06 — Dada una entrada publicada, Cuando se inspecciona la llamada, Entonces `source.sha256` es el SHA-256 hex minúsculo de los bytes UTF-8 exactos de `content` ya redactado, `tags` es una lista (comas, comillas y acentos intactos), `source.uri` es `custom-agents:<project_id>/<id_local>#g<n>`, y `document_id` = UUIDv5(`project_id`, ID local, generación) es estable entre ejecuciones; tras borrar el estado local, `--check` reconstruye la generación desde `document_manifest` y obtiene el mismo `document_id`. *Comprobación:* test que recalcula hash e ID, borra el estado y reconcilia.
- [ ] [GWT] CA-07 — Dado un timeout tras `publish_document`, Cuando se reintenta, Entonces se consulta `document_status` antes de reenviar (`Resource not found` es la ausencia del documento **solo** con la misma condición de acceso que en CA-08: otra llamada con la misma clave sobre el proyecto ya funcionó en esa ejecución; si no, error de configuración; `found: false` no existe aquí), y el reenvío es el documento **entero** guardado en la outbox (mismo ID, versión, título, categoría, tags, `source` y `validation`) con la misma clave de escritura; el servidor falso registra un solo documento. Dado un cambio de ACTOR (clave emitida por otro usuario de Kairos; la rotación con `replaced_by` conserva el actor), Entonces la entrega incierta se resuelve con `document_status` comparando `version` y `source_sha256`, sin reenviar (el servidor fija `validated_by` al actor y el reenvío daría `Conflicting event or version`). *Comprobación:* test de entrega incierta que compara el cuerpo byte a byte.
- [ ] [GWT] CA-08 — Dada una entrada que sale de `approved/`, Cuando se sincroniza, Entonces se consulta `document_status` primero: con `deleted: true` no se llama a `revoke_document`; con `Resource not found` tampoco, solo si otra llamada con la misma clave sobre el proyecto ya funcionó en esa ejecución; si es la primera llamada, se informa como error de configuración (clave sin el proyecto o sin permisos); en otro caso se llama con la versión siguiente. *Comprobación:* test con los cuatro estados.
- [ ] [GWT] CA-09 — Dado un desfase entre local y remoto (documento ausente, versión distinta, `source_sha256` distinto, lápida inesperada), Cuando se ejecuta `knowledge-sync.py --check`, Entonces pide páginas con `limit` ≤ 50, pasa cada `next_cursor` como `cursor` hasta agotar, compara con `source_sha256` (nunca `canonical_hash`), sale ≠ 0 con un `desfase` que nombra la identidad y el remedio, y no publica nada. *Comprobación:* test con manifiesto de varias páginas que incluye lápidas y un `canonical_hash` distinto que no debe dar desfase.
- [ ] [GWT] CA-10 — Dado un intent autorizado y Kairos sano, Cuando un agente ejecuta `knowledge-find.py --intent <intent>`, Entonces usa solo la clave de lectura, cada acierto trae `id`, `estado`, `evidencia`, `ruta` y la marca de dato no confiable, y un texto recuperado con forma de instrucción no cambia la salida del script (se presenta como dato). *Comprobación:* test con respuesta envenenada del servidor falso.
- [ ] [GWT] CA-11 — Dada solo una clave de lectura, Cuando se intenta publicar, revocar o enviar journal e hitos, Entonces no se llama a ninguna herramienta de escritura, se informa «sin clave de escritura» y la lectura sigue sana. *Comprobación:* test que verifica cero llamadas de escritura.
- [ ] [GWT] CA-12 — Dados `config.journal: true` y `capture_policy` con `capture_allowed: true` (con o sin cliente kairos instalado), Cuando llega un momento de envío, Entonces se envía un único `remember` por sesión con `event_type: summary`, `generate: false`, `validation_status: observed`, `payload.title` (≤ 500), `payload.content` (≤ 100.000), `session_id` y `agent_id` (≤ 200), `payload.structured` válido contra `session-summary.v1` y sin campo `capture` ni etiquetas `capture:*`. Dado `capture_mode: "off"`, Entonces no se llama a `remember`, el resumen queda en local y `/doctor` dice que la captura del proyecto está apagada; dado `capture_mode` distinto de `off` con `capture_allowed: false`, Entonces `/doctor` dice que a la clave, o a su usuario en el proyecto, le falta `write`. *Comprobación:* test de las tres ramas + validación con el esquema; el test no lee `.kairos/`.
- [ ] [GWT] CA-13 — Dado un evento episódico (journal o hito) enviado con timeout, Cuando se reintenta, Entonces reenvía el evento **entero** tal como quedó en la outbox, ya redactado (mismos `event_id`, `item_id`, `version`, `occurred_at` y payload), aunque `redact.py` haya cambiado de patrones; solo repite tras `event_status` con `{found: false}`; `Resource not found` en `event_status` es proyecto no accesible (configuración), y ningún `isError` cuenta como ausencia. *Comprobación:* test de entrega incierta episódica que cambia los patrones de redacción entre el envío y el reintento.
- [ ] [GWT] CA-14 — Dado `config.hitos: true` y un ledger con una tarea cerrada, un veredicto de revisión y una retro, Cuando se envían los hitos, Entonces llegan exactamente 3 eventos con el mapeo `note`+`change`, `note`+`decision` y `learning`+`discovery`, todos con `version: 1` y `validation_status: observed`, nada más del ledger, y repetir el envío no crea eventos nuevos. Dada después la misma tarea reabierta y cerrada otra vez, Entonces llega un evento con otro `item_id` (UUIDv5 con ocurrencia 2), `version: 1`, y ningún `Conflicting event or version`. *Comprobación:* test sobre un ledger de fixture con reapertura; el servidor falso aplica la regla «versión = actual + 1 o conflicto».
- [ ] [GWT] CA-15 — Dado un servidor que responde `isError` con `Rate limit exceeded [code=rate_limited retry_after=2]`, o un HTTP 429 con `Retry-After: 2` de un proxy, Cuando el cliente reintenta, Entonces no vuelve a llamar antes de 2 s y, si 2 s superan su plazo, reencola; un mensaje con texto añadido después del corchete no casa la regex anclada y se trata como fallo. Dado un mensaje que empieza por `Daily write quota exceeded` con o sin `[code=… retry_after=N]`, Entonces reconoce la cuota, usa N si aparece o backoff largo si no, y las lecturas siguen. *Comprobación:* test con reloj inyectado.
- [ ] [GWT] CA-16 — Dado un adaptador de fixture `type: "mcp-fixture"` que reutiliza el cliente MCP genérico con otro mapa de herramientas, Cuando se carga por `--backends-dir`, Entonces publica y lee sin tocar `knowledge-sync.py`, `backends/__init__.py` ni el cliente genérico. *Comprobación:* test de carga y diff vacío del núcleo.
- [ ] CA-17 — Ningún fichero nuevo o modificado nombra los backends retirados (salvo el antecedente histórico de `testing/retirada.md` y los CHANGELOG ya publicados). *Comprobación:* `git diff --name-only master...` filtrado con `grep -il` por los dos nombres retirados que lista `testing/retirada.md` → vacío.
- [ ] CA-18 — Funciona igual en Claude Code, Codex y OpenCode: ninguna pieza nueva tiene lógica por runtime y `python scripts/export-interop.py --check` sale 0. *Comprobación:* comando y `python scripts/lint_plugin.py` en verde.
- [ ] CA-19 — Todo texto enviado (documentos, journal, hitos, incluido `payload.structured`, que el servidor no redacta) pasa por `agent-kits/shared/redact.py` **antes** de calcular el hash y de encolar. Cubre los patrones actuales del servidor (`sk-`, `AKIA`, `Bearer`, `gh*_`, `github_pat_`, `xox*`, `AIza`, JWT, DSN con credenciales, PEM, `<private>`, nombres de secreto) y los del hito B (`mp_`, `sk_live_`, `sk_test_`, `rk_live_`, `glpat-`, `hf_`, `npm_`, `*_KEY`, `*_PASS`, `curl -u`, `curl --user`, `Authorization: Basic`, cadenas de alta entropía). Un recibo con `redacted: true` produce un aviso. El marcador y los nombres de secreto los fija CA-29. Cuando Kairos publique `docs/contracts/redaction-cases.json` (T-43), se usa como batería de casos compartida. *Comprobación:* test con un ejemplo de cada patrón en una entrada aprobada y en un hito, que no aparece en la llamada; el hash enviado es el del texto redactado.
- [ ] CA-20 — Integración real (la ejecuta la sesión kairos o el usuario contra su servidor): la lista de «Criterios de aceptación para el equipo consumidor» del repo knowledge-graphs (`docs/integration.md`) pasa, con versiones, IDs de prueba y resultados adjuntos en `testing/` sin claves. *Comprobación:* informe en `docs/roadmap/2026-11-26-kairos-memory/testing/`.
- [ ] [GWT] CA-21 — Dado un servidor cuyo `tools/list` no anuncia `revoke_document` y cuyo `serverInfo.version` es `0.0.0`, Cuando se ejecuta `/doctor`, Entonces solo la capacidad de revocación sale ⚠️ nombrando la herramienta y la versión no influye. Dado un `tools/list` completo pero `capture_policy(project_id)` con error, Entonces la lectura sale ⚠️ aunque `tools/list` respondiera (la salud exige la llamada real: `tools/list` lista las 34 herramientas a cualquier clave que `/v1` acepte, sin mirar scopes; con la API caída, a cualquier `Bearer`; con la API en pie, una clave inválida da 401). Las herramientas y campos de más (`extraction`, `redacted`, `capture_hash`, sobre `untrusted`/`warning`) se ignoran sin error. *Comprobación:* test con cuatro escenarios (completo, sin una herramienta, con herramientas extra, `tools/list` sano con llamada real fallida).
- [ ] [GWT] CA-22 — Dada una entrada con lápida en Kairos que vuelve a `approved/`, Cuando se publica, Entonces se usa la generación siguiente (nuevo `document_id`), el informe lo avisa y el ID revocado no se envía. Dado un `Conflicting event or version` con `document_status.deleted: false`, Entonces se reporta como conflicto de contenido y no se sube la versión. *Comprobación:* test de las dos ramas del conflicto.
- [ ] [GWT] CA-23 — Dado cada uno de los errores de la tabla «Manejo de errores» (los HTTP 400, 401, 403, 406, 413, 421 y 429, y cada mensaje de herramienta listado, incluidos `Input validation error: …` sin prefijo, `Unknown tool: <x>`, los de hechos, los de publicación, la lista literal de privacidad, los dos de validez de hechos, 502/503/504 sin JSON y un texto desconocido), Cuando el cliente los recibe, Entonces los clasifica como dice la columna «Clase» con `re.fullmatch` sobre el mensaje entero, un mensaje conocido con texto extra antes o después (incluido un salto de línea final) no casa con su clase, los HTTP se clasifican por código aunque el cuerpo sea HTML o esté vacío, y ninguno se trata como éxito. *Comprobación:* test parametrizado con un caso por error, uno con texto añadido por clase y uno con `\n` final.
- [ ] [GWT] CA-24 — Dado un hito con `observation.v1`, Cuando se construye el evento, Entonces valida en local (8 campos, `type` del enum, longitudes, `evidence_quote` ≤ 2.000, máximo 1.000 nodos, profundidad ≤ 8, `concepts` y `files_*` sin repetidos), el plugin comprueba que cada `evidence_quote` aparece literal en `narrative`, y no lleva `category: agent-activity` ni etiquetas `capture:*`. Dados `payload.facts` (máximo 30; `subject` 1-300, `predicate` 1-200, `object` 1-2.000, `evidence_quote` ≤ 4.000; `valid_from`/`valid_until` con zona horaria y no invertidos), Entonces cada cita aparece literal en `content + "\n" + problem + "\n" + correction` ya redactados. Un evento inválido no se envía y queda como fallo permanente con la ruta del error. *Comprobación:* test con los ejemplos válidos e inválidos del esquema y casos de cada límite.
- [ ] [GWT] CA-25 — Dada una entrada aprobada o un evento cuyo **cuerpo HTTP completo** (sobre JSON-RPC incluido, serializado una sola vez con `ensure_ascii=False`) supera 262.144 bytes (por ejemplo, por texto no ASCII), Cuando se publica o se envía con `remember`, Entonces no se envía y se marca fallo permanente de esa entrada; dado un HTTP 413 (en JSON o en HTML del nginx), Entonces se trata igual por el código de estado. Dada una respuesta de más de 1 MiB, Entonces el cliente la corta, la descarta con motivo y no la interpreta. *Comprobación:* test con contenido multibyte justo por encima y por debajo del tope.
- [ ] [GWT] CA-26 — Dado un job `failed` en `document_status`, o un job `failed` o un recibo `superseded` en `event_status` (`superseded` solo existe ahí), Cuando se concilia, Entonces se reporta su `error_code`, la entrada sale de la outbox sin reencolarse y no se espera `complete`. *Comprobación:* test con los dos estados terminales en cada flujo.
- [ ] [GWT] CA-27 — Dado un servidor que responde HTTP 421, HTTP 403 por origen o cualquier respuesta con `Deprecation: true`, Cuando se ejecuta `/doctor`, Entonces la fila sale ⚠️ con el remedio: añadir el origen exacto a `MEMORY_ALLOWED_ORIGINS` del `.env` del despliegue (Compose → `KAIROS_ALLOWED_ORIGINS`), recrear el servicio MCP y, si hay proxy propio, conservar el `Host` original (421/403) o cambiar `base_url` a la entrada `/mcp/` de kairos-mcp (`Deprecation`). *Comprobación:* test con los tres casos en el servidor falso.
- [ ] [GWT] CA-28 — Dada una entrada de `approved/`, Cuando se construye su publicación, Entonces lleva `title` y `validation` = `{status: "validated", evidence: [1..20 elementos de ≤ 4.000 caracteres], validated_by}` con la evidencia tomada de la aprobación de `knowledge-curator`; una entrada sin aprobación trazable, o con evidencia fuera de esos límites, no se envía y se informa. Una escritura usa el plazo de 40 s (siempre < 45 s del nginx); una respuesta que tarda 35 s no es timeout, y un timeout tras enviar es entrega incierta. *Comprobación:* test con una entrada con aprobación, otra sin ella y otra con 21 evidencias; test de plazos con reloj inyectado.
- [ ] [GWT] CA-29 — Dado un texto con secretos detrás de nombres de secreto (`password`, `passwd`, `pwd`, `passphrase`, `secret`, `token`, `credential`, `credentials`, `api_key`/`apikey`, `access_key`, `access_key_id`, `secret_access_key`, `access_token`, `client_secret`, `private_key`, `connection_string`, `authorization`, `cookie`, `dsn` como nombre o sufijo tras `_`, y `pgpassword`; con camelCase separado y `.`/`-` tratados como `_`, p. ej. `dbPassword`, `aws.secret-access-key`; también como claves JSON dentro de cadenas y en `structured`), Cuando se prepara el envío a Kairos, Entonces cada valor completo, esquema incluido, queda como `[REDACTADO]` exacto (`Authorization: [REDACTADO]`, nunca `Bearer [REDACTADO]` ni `[secreto redactado]`), y una asignación con comilla sin cerrar no se envía (evita `Secret assignments must have balanced quotes`). *Comprobación:* test con un caso por nombre y por variante, que pasa el texto resultante por una copia de `_SECRET_NAME` y `_SAFE_VALUE` del servidor (o por `redaction-cases.json` cuando exista) sin detectar nada sensible.

## Pruebas

- Unitarias con TDD (Constitución): cliente MCP genérico, adaptador `kairos`, envío episódico, validador de config, clasificador de errores. Servidor MCP falso en proceso que reproduce `tools/list` variable, cabeceras requeridas (400/406), `Bearer` (401), host/origen (421/403), cuerpo grande (413), `isError` con los mensajes reales, `retry_after` en el texto y en un 429 de proxy, recorte de bytes, `Deprecation`, paginación con lápidas, jobs terminales y la regla de versiones de `remember`.
- Las `[GWT]` (CA-01..CA-16 y CA-21..CA-29) se traducen 1:1 a tests del repo (no E2E de navegador).
- Suites existentes que deben seguir en verde: `tests/test_hook_network_egress.py`, `tests/test_sync_write_gate.py`, suites de `skills/knowledge-services/scripts/`, `evals/check.py`, `scripts/lint_plugin.py`, `export-interop.py --check`.
- CA-20 es una prueba de integración manual contra el servidor real; no la sustituyen `/doctor`, un HTTP 200 ni las unitarias.

## Referencias

- Repo knowledge-graphs, `docs/contracts/kairos-mcp.json` (contrato MCP 0.4.1, 34 herramientas; `$defs/Source` de `publish_document`).
- Repo knowledge-graphs, `docs/integration.md`: «Conectar con kairos-mcp», «Dos flujos de escritura separados», «Capturar memoria con identidad estable», «Observaciones estructuradas con esquema versionado», «Publicar conocimiento aprobado», «Conciliar antes de reenviar», «Criterios de aceptación para el equipo consumidor».
- Repo knowledge-graphs, `docs/contracts/session-summary.v1.schema.json` y `docs/contracts/observation.v1.schema.json` (con ejemplos en `docs/contracts/examples/`).
- Repo knowledge-graphs, `docs/install.md` (captura `--capture off|summary|full`) y `client/lib/lifecycle-config.mjs:7-16` (configuración interna de la captura del cliente; no es contrato).
- Validaciones de la sesión kairos del 2026-11-26 (servidor y contrato 0.4.1, rama `feat/access-control`), en el repo knowledge-graphs:
  - `server/memory_platform/store_auth.py:74-75` y `:84-85` (`Resource not found` también por falta de acceso), `:86` (permiso efectivo = clave ∩ usuario) y `:163-174` (`capture_allowed`).
  - `server/memory_platform/store_ingest.py:146,157-159` (reenvío idéntico), `:164-165` (captura `off` rechaza `remember`) y `:175-176` (versión = actual + 1).
  - `server/memory_platform/store_documents.py:91` (hash en la comprobación de contenido), `:95-96,109-111` (`validated_by` = actor), `:112-113` (sin republicación tras lápida), `:114` y `:295` (`source` sin transformar), `:264-271` (`event_status` sin mirar la política).
  - `server/memory_platform/errors.py:113-114`, `store_vectors.py:341`, `privacy.py:15-27`, `schemas.py:21,25,113-137`.
  - `mcp/kairos_mcp/config.py:7` (tope de cuerpo), `web/nginx.conf:15` (corte del nginx a 256 k) y `:69-74` (502/504 sin JSON, `proxy_read_timeout` 45 s), `server/memory_platform/privacy.py:25` (`_SECRET_NAME`) y `:27` (`_SAFE_VALUE`), `server/memory_platform/models.py:149-152` (límites de `validation.evidence`), `mcp/kairos_mcp/app.py:28-35` (host/origen) y `:51-57` (`tools/list` sin validar clave), `translate.py:165-171` (recorte y pérdida de `structuredContent`).
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
6. **Entrada revocada que vuelve a `approved/`** (cerrada con la validación de kairos): nuevo `document_id` con la generación siguiente (obligatorio: el servidor no permite republicar un ID con lápida), aviso en el informe de sync, y el ID local y la generación en `source.uri` (`custom-agents:<project_id>/<id_local>#g<n>`) para reconstruirla desde `document_manifest`.
7. **Marcador de redacción: se normaliza solo en lo que va a Kairos** (recomendación del orquestador, 2026-11-26; el usuario la confirma o cambia al aprobar la spec). `redact.py` sigue siendo la fuente única de los patrones y gana un parámetro de marcador; el adaptador y el envío episódico lo llaman con `[REDACTADO]` y sustituyen el valor completo tras un nombre de secreto, antes de hashear. El journal local, el ledger, los hooks y sus tests conservan `[secreto redactado]`. Motivo: la regla del marcador es del servidor y el adaptador la absorbe; no reescribe ~36 ficheros ni deja journals nuevos con otro formato, y otro backend podría exigir otro marcador. CA-29 fija lo que llega a Kairos.

## Preguntas abiertas

Ninguna.

## Supuestos

- **Hecho técnico:** el marco carga adaptadores por `type` y valida las 6 funciones; `consultar` es lo que hace enrutable la lectura — `skills/knowledge-services/backends/README.md` (tablas «Las 6 funciones» y «Funciones OPCIONALES»).
- **Hecho técnico:** el plugin no incluye adaptadores desde la 4.0.0; esta iniciativa incluye el primero — `skills/knowledge-services/backends/README.md` («El plugin no incluye adaptadores»).
- **Hecho técnico:** la red está vetada en hooks y toda capacidad con red es opt-in y local/privada por defecto — `docs/CONSTITUTION.md:20` y `:37`.
- **Hecho técnico:** el router de lectura exige `puede_leer` con `puede: true` antes de consultar — `agent-kits/shared/knowledge-find.py:1722`.
- **Hecho técnico (validado por kairos):** los scopes de una clave no se pueden conocer por MCP. `projects` no los devuelve; `capture_policy` exige `read` y da `capture_allowed: true` solo con `write` y política distinta de `off`. `publish`/`validate` no se pueden verificar sin escribir — repo knowledge-graphs, `server/memory_platform/store_auth.py:163-174`.
- **Hecho técnico (validado por kairos):** `tools/list` es estático (lista las 34 herramientas a cualquier `Bearer` sin mirar scopes) e `initialize`/`tools/list` no validan la clave si la API no responde — repo knowledge-graphs, `mcp/kairos_mcp/app.py:51-57`.
- **Hecho técnico (validado por kairos):** con la captura en `off`, `remember` rechaza todo `event_type` salvo `delete` con `Capture is disabled for this project`; `event_status` con `project_id` no mira la política (exige `read`+`write`) — repo knowledge-graphs, `server/memory_platform/store_ingest.py:164-165` y `store_documents.py:264-271`.
- **Hecho técnico (validado por kairos):** tras una lápida no hay versión que permita republicar el mismo ID; se distingue con `document_status.deleted`. El reenvío idempotente exige el documento entero idéntico y el mismo actor (`validated_by` lo fija el servidor) — repo knowledge-graphs, `store_documents.py:95-96,109-113`.
- **Hecho técnico (validado por kairos):** en `remember`, una versión distinta de la actual + 1, o un ítem borrado, da `Conflicting event or version`; un reenvío con contenido distinto (también por redactar con otros patrones) también — repo knowledge-graphs, `store_ingest.py:146,157-159,175-176`.
- **Hecho técnico (validado por kairos):** `source.uri` es obligatorio (≤ 2.000), `label` opcional (≤ 300) y `sha256` (64 hex) **no es opcional en la práctica**: si falta, `publish_document` responde `Source SHA-256 must match the exact UTF-8 content`; `document_manifest` devuelve `source` sin transformar — repo knowledge-graphs, `store_documents.py:91,114,295`.
- **Hecho técnico (validado por kairos):** el servidor acepta cualquier versión de UUID como `document_id` y lo normaliza a minúsculas con guiones; la clave primaria es (`project_id`, `id`).
- **Hecho técnico (validado por kairos):** la captura del cliente kairos nunca envía `session-summary.v1`; en modo `summary` envía metadatos de ciclo de vida con `category: agent-activity` — repo knowledge-graphs, `client/lib/capture.mjs:64-78`. Su configuración (`.kairos/installation.json`, esquema en `client/lib/lifecycle-config.mjs:7-16`) es interna y no forma parte del contrato.
- **Hecho técnico (validado por kairos):** por MCP no llegan códigos ni la cabecera `Retry-After` (kairos-mcp descarta cabeceras); solo el texto del error. Son HTTP de toda la petición: 400/406 (cabeceras), 401 (clave), 403 (origen), 413 (cuerpo > 262.144 bytes, `mcp/kairos_mcp/config.py:7`; el nginx también corta a 256 k con 413 en HTML), 502/503/504 sin JSON (nginx, `web/nginx.conf:69-74`) y 421 (host, `mcp/kairos_mcp/app.py:28-35`).
- **Hecho técnico (validado por kairos):** el servidor no redacta `payload.structured` (un secreto ahí da 422 y rechaza el evento entero) y `publish_document` **rechaza**, no redacta, los secretos — repo knowledge-graphs, `privacy.py:15-27` y `docs/integration.md` («Observaciones estructuradas con esquema versionado»).
- **Hecho técnico:** el cliente MCP retirado no enviaba `Bearer` — `docs/roadmap/2026-11-10-plugin-audit-2/testing/retirada.md`.
- **Supuesto hasta confirmar:** los mensajes de cuota (`Daily write quota exceeded`) y de flujos (`Too many activity streams`) solo tienen fijado el prefijo; el sufijo `[code=quota_exceeded retry_after=N]` / `[code=too_many_streams retry_after=N]` es intención de Kairos, no contrato. Lo confirmaría la sesión kairos al cerrar T-55..T-58.
- **Riesgo / supuesto de calendario:** Kairos tiene en curso tres hitos sin fechas (van por la fase 3 de 18). El contrato MCP no cambia en toda esa iniciativa, pero el comportamiento sí:

  | Hito | Fases | Qué llega | Efecto en esta spec |
  |---|---|---|---|
  | A | 3-6 (rotación en la 4) | `last_used_at`, rotación `replaced_by` (24 h de gracia; luego 401); 429 del login HTTP por IP | El 401 tras rotación debe dar el remedio correcto; el login HTTP no lo usa el plugin |
  | B | 7-12 (redacción 8-9, límites 10-11) | Redacción ampliada (patrones de CA-19); tasa por clave, cuota diaria de escritura, tope de flujos, y su paso por kairos-mcp (T-55, T-61, T-63) | Hoy no hay límite de tasa en herramientas: CA-15, CA-19 y CA-23 se prueban contra el servidor falso hasta que B exista; CA-20 los reconfirmará en real |
  | C | 13 | `capabilities` en `/v1/auth/me` | Fuera de alcance (es `/v1`); una spec futura podría usarlo para verificar scopes |

  También hay un proxy previsto (Iniciativa 5 de Kairos) que puede responder HTTP 429 con `Retry-After`; el cliente ya lo contempla. Lo confirmaría la sesión kairos al cerrar cada hito.
- **Incógnita:** el presupuesto y plazo no se han fijado; los dará `evaluator`.
