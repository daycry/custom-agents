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
  inicio: 2026-11-26T11:30:38Z
  fin: 2026-11-26T11:35:09Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-3279701ae97e4220b23067a5b2769bb2
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 56, salida: 33666, cache_creacion: 87137, cache_lectura: 2909701 }
  eur: 1.56
  horas_ia: 0.23
  duracion: 14m
  ratio_usado: 531798.5
---

# Kairos como memoria opcional de los agentes

> **Evaluación:** pendiente
> **Plan de implementación:** pendiente

> **Terminología:**
> - **Kairos**: servidor de memoria del usuario (repo knowledge-graphs). Habla MCP por *streamable HTTP* en `<base>/mcp/`, con credencial `Authorization: Bearer`. Contrato: repo knowledge-graphs, `docs/contracts/kairos-mcp.json` (MCP 0.4.1, 34 herramientas).
> - **Adaptador**: fichero `backends/<type>.py` del marco `knowledge-services` con las 6 funciones `health/plan/apply/verify/rebuild/revoke` (+ opcionales `puede_leer`/`consultar`).
> - **Cliente MCP genérico**: módulo Python del plugin que abre sesión MCP por HTTP, envía `Bearer` y llama herramientas por nombre. No sabe nada de Kairos.
> - **Publicación documental**: envío de `docs/knowledge/approved/` con `publish_document`/`revoke_document`.
> - **Memoria episódica**: eventos con `remember` (resumen de sesión del journal, hitos del ledger).
> - **Captura del cliente kairos**: hooks que instala `kairos install --capture summary|full` (fuera del plugin). Se detecta por `.kairos/installation.json` (`automation.capture`).

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
  resumen de sesión (si nadie más lo envía) y los hitos del ledger.
- **Sin acoplar el plugin**: Kairos es el primer adaptador del marco por `type`. Otro MCP de
  memoria debe poder enchufarse igual.
- **Sin bloquear nunca el ciclo**: si Kairos cae, se degrada con aviso y la outbox reintenta.

Coordinación: la sesión de Claude que mantiene Kairos (sesión «kairos», dueña del repo
knowledge-graphs) validará el diseño contra el servidor real. Este plugin no escribe en ese repo.

## Decisiones de diseño

Decisiones del usuario (2026-11-17/18). Son requisitos, no se reabren.

| Decisión | Elección | Motivo |
|---|---|---|
| Transporte | **MCP** (*streamable HTTP* en `<base>/mcp/`), no REST `/v1` | Un único contrato; `tools/list` es la fuente del esquema |
| Activación | **Opt-in**: se configura en `/setup`, `/doctor` la comprueba | Constitución: toda capacidad con red es opt-in |
| Journal | **Solo si está configurado**. Si la captura del cliente kairos está instalada y `capture_policy` la permite, el plugin **no** envía el journal. Si no, envía `session-summary.v1` con `remember` en los puntos de cierre | Sin duplicados; los hooks del plugin siguen sin red |
| Qué se publica | **Solo `docs/knowledge/approved/`**; `candidates/` se queda local | Constitución: los backends solo reciben lo aprobado por `knowledge-curator` |
| Proyecto | **Un `project_id`** fijado una vez en `/setup` (`^[a-z0-9][a-z0-9_-]{0,63}$`) | Evita mezclar proyectos |
| Credenciales | **Dos claves separadas**: lectura (`read`) y escritura (`publish`+`validate`, +`write` solo si se envía journal/hitos). Nunca `admin` | Mínimo privilegio; la de lectura permite consultar sin poder escribir |
| Ledger | **Solo hitos**: tarea cerrada, veredicto de revisión, retro, decisiones. `tasks.md` sigue canónico | No duplicar el ledger; ruido mínimo |
| Acoplamiento | **Kairos = primer adaptador por `type`** sobre un cliente MCP genérico; routing fail-closed | Otros MCP de memoria deben poder añadirse |
| Runtimes | **Claude Code, Codex y OpenCode** sin código por runtime; traduce `export-interop.py` | Requisito del proyecto (multi-runtime) |

Decisiones de este análisis (propuestas; se confirman en la puerta de aprobación):

| Decisión | Elección propuesta | Motivo |
|---|---|---|
| Identidad documental | **UUIDv5** derivado de (`project_id`, ID local de la entrada) + mapa local de versiones | Reintento con la misma identidad aunque se pierda el estado; reconciliable con `document_manifest` |
| Outbox | **Dos colas separadas** (documental y episódica) sobre `agent-kits/shared/outbox.py` | Lo exige el contrato de Kairos («Dos flujos de escritura separados») |
| Lectura | **`knowledge-find.py --intent`** (router existente) con respaldo local | Ya existe la autorización por intent y el respaldo con motivo |
| Nombres | Nada nuevo se llama como los backends retirados; el cliente MCP se reescribe genérico | Petición del usuario (2026-11-26) |

## Configuración / parámetros

Todo vive en `.claude/knowledge-services/taxonomy.json` (local del proyecto), bajo
`backends.<id>` con `type: "kairos"`. Ningún secreto en ese fichero.

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Activación | `backends.<id>.enabled` | `false` | `true` tras `/setup` |
| Tipo de adaptador | `backends.<id>.type` | — | **`kairos`** |
| URL base | `config.base_url` | ninguno | p. ej. `http://127.0.0.1:5173`; el adaptador añade `/mcp/` |
| Hosts permitidos | `config.allow_remote` | `false` | Solo hosts locales/privados salvo opt-in explícito (Pregunta 3) |
| Proyecto | `config.project_id` | ninguno | Validado con `^[a-z0-9][a-z0-9_-]{0,63}$` |
| Clave de lectura | `config.read_key_file` | ninguno | Ruta a fichero privado **fuera del proyecto** |
| Clave de escritura | `config.write_key_file` | ninguno | Ruta a fichero privado fuera del proyecto; opcional (sin ella, solo lectura) |
| Intents de lectura | `backends.<id>.read.intents` | `[]` | Los que el usuario autorice |
| Routing por categoría | `categories.<cat>.routing.<id>` | ausente = no se envía | `true` o `"summary"` por categoría |
| Journal | `config.journal` | `auto` | `auto` (no envía si la captura del cliente kairos está activa) · `off` · `send` |
| Hitos del ledger | `config.hitos` | `false` | `true` si el usuario lo pide |
| Plazos | `config.timeout_ms` | 5.000 | Respeta el tope de `/doctor` |

## Arquitectura y componentes

| Pieza | Nueva / reutilizada | Papel |
|---|---|---|
| Cliente MCP genérico (Python, sin dependencias) | **Nueva** (reescritura genérica; se puede inspirar en el cliente retirado en plugin-audit-2, sin reutilizar nombres) | `initialize`, `tools/list`, `tools/call`; `Bearer`; guardarraíl de host (local/privado por defecto, sin redirecciones automáticas, sin proxy del entorno); `Retry-After` en 429/503; tope de bytes; marca todo resultado como dato no confiable |
| Adaptador `kairos` (`backends/kairos.py` o equivalente, ver Pregunta 1) | **Nuevo** | Las 6 funciones + `puede_leer`/`consultar`. Mapea a `publish_document`, `document_status`, `document_manifest`, `revoke_document`, `search`, `details`, `context` |
| Envío episódico (journal e hitos) | **Nuevo** (script determinista con tests) | `capture_policy` → `remember` → `event_status`; identidad estable por evento |
| `skills/knowledge-services/scripts/knowledge-sync.py` | Reutilizado sin cambios de núcleo | Carga por `type`, routing fail-closed, outbox, `--check/--dry-run/--rebuild` |
| `agent-kits/shared/outbox.py` | Reutilizado | Dos colas: documental y episódica |
| `agent-kits/shared/knowledge-find.py --intent` | Reutilizado | Router de lectura con respaldo local y motivo |
| `agent-kits/shared/redact.py` | Reutilizado | Todo texto enviado pasa por aquí (Constitución) |
| `agent-kits/shared/capabilities.py`, `commands/setup.md`, `agent-kits/shared/doctor.py` | Ampliados | Paso guiado de configuración y fila de diagnóstico |
| `hooks/` | **Sin cambios de red** | El journal se sigue escribiendo en local; el envío ocurre fuera de los hooks |

## Flujo (paso a paso)

**Configuración (`/setup`)**
1. El usuario elige activar Kairos. `/setup` pide URL base, `project_id`, rutas de las dos claves, categorías a publicar, modo de journal e hitos.
2. Valida formato (`project_id`, URL, host permitido, ficheros de clave existen y están fuera del proyecto). No conecta.
3. Escribe `backends.<id>` en `taxonomy.json` y propone `/doctor` para la comprobación en vivo.

**Diagnóstico (`/doctor`)**
4. `health()`: `initialize` + `tools/list` con la clave de lectura; comprueba que están las herramientas que usa el adaptador y que `projects` incluye el `project_id`. Con clave de escritura, `capture_policy`. Respeta el tope de tiempo. Nunca escribe.

**Lectura (agentes)**
5. Un agente llama `knowledge-find.py --intent <intent> "<texto>"`. Si el intent está autorizado y `puede_leer` da `true`, el adaptador llama `search`/`context` con la clave de lectura y el `project_id`.
6. Cada acierto vuelve marcado como **dato no confiable**, con procedencia. Si Kairos falla o responde parcial, la respuesta incluye el motivo y los aciertos locales.

**Publicación de lo aprobado**
7. `knowledge-sync.py --backend <id> --dry-run` muestra qué se publicará (solo `approved/` con routing).
8. Sin `--dry-run`: drena la outbox documental, luego `publish_document` (UUID estable, versión secuencial, SHA-256 de los bytes UTF-8 exactos de `content`, tags como lista). La aceptación no es el fin: `document_status` hasta confirmar versión, hash y trabajos.
9. Una entrada que sale de `approved/` → `revoke_document` con la versión siguiente. El ID revocado no se republica.
10. `--check`: `document_manifest` paginado contra el estado local; nombra el remedio sin reenviar a ciegas.

**Journal e hitos (memoria episódica)**
11. En los puntos de cierre (Pregunta 4) y solo si `config.journal` lo permite: si `.kairos/installation.json` declara captura activa **y** `capture_policy` devuelve `capture_allowed=true`, no envía nada (lo hace el cliente kairos). En otro caso, envía `session-summary.v1` con `remember`.
12. Si `config.hitos: true`, cada hito nuevo del ledger (tarea cerrada, veredicto de revisión, retro, decisión) se envía como un evento con identidad derivada de slug + ID + estado. Reintento = mismo evento.
13. `event_status` hasta `complete`. Pendiente o incierto → se queda en la outbox episódica.

## Alcance

- **Dentro (esta iteración):**
  - Cliente MCP genérico en Python (HTTP *streamable*, `Bearer`, guardarraíl de host, `Retry-After`, tope de bytes), sin dependencias externas, con servidor MCP falso para los tests.
  - Adaptador `kairos` con las 6 funciones del contrato y `puede_leer`/`consultar`.
  - Publicación de `approved/` (con modo `resumen`), revocación con lápida, reconciliación por `document_manifest`, `--rebuild`.
  - Lectura vía `knowledge-find.py --intent` con respaldo local y marca de dato no confiable.
  - Envío de journal (`session-summary.v1` vía `remember`) con la regla de no-duplicado frente a la captura del cliente kairos.
  - Envío de hitos del ledger como eventos episódicos (opt-in).
  - Dos outbox separadas, idempotencia estricta y reconciliación tras entrega incierta.
  - `/setup` (paso guiado), `/doctor` (fila con veredicto y remedio), `capabilities.py`.
  - Documentación: `skills/knowledge-services/references/` (cómo activar Kairos y cómo añadir otro MCP de memoria), CHANGELOG EN/ES, regeneración de `interop/`.
- **Fuera (siguientes specs):**
  - Cambios en el servidor Kairos o en su cliente `kairos` (repo knowledge-graphs).
  - Instalar el cliente `kairos`, crear claves, cambiar la política de captura o reindexar: son acciones del usuario. El plugin las **nombra**, no las ejecuta.
  - REST `/v1`, sesión del portal, contraseña de admin o `bootstrap_password`.
  - Enviar candidatas, el ledger entero, transcripciones o prompts.
  - Herramientas de corpus, observaciones, equipo y `work_state_*` de Kairos.
  - Red desde hooks; lectura automática de Kairos en `SessionStart`.
  - Un segundo adaptador MCP real (se deja documentado cómo añadirlo y probado con un fixture).
  - Cualquier pieza, nombre, test o fixture con el nombre de los backends retirados.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Kairos apagado, plazo agotado o `Memory service temporarily unavailable` | `health` → `degradado`/`error` con motivo; lectura degrada a local con motivo; escritura reencola en la outbox con backoff. El ciclo nunca se bloquea (exit 0 en hooks y orquestadores) |
| 401 (clave ausente, inválida o rotada) | `error` con «clave rechazada» y el remedio (renovar en el portal); nunca imprime la clave |
| 429 / 503 con `Retry-After` | Respeta la espera; no reintenta antes; si excede el plazo, reencola |
| `isError` de una herramienta | Se trata como fallo de esa operación, **no** como ausencia (un error no confirma que un evento no exista) |
| Entrega incierta (timeout tras enviar) | Consulta `document_status`/`event_status`; solo una ausencia confirmada (`found: false`) permite repetir el mismo envío, con la misma identidad y contenido |
| Mismo ID y versión con otro contenido | Conflicto: se reporta y se detiene esa entrada; no se sube la versión para esquivarlo |
| Entrada revocada que vuelve a `approved/` | No se resucita el ID: se reporta y se aplica la política de la Pregunta 5 |
| Host no permitido o redirección | Se rechaza antes de conectar; no se siguen redirecciones |
| Respuesta recortada por el tope de bytes o no-JSON | Se descarta con motivo; nunca se inventa contenido |
| `capture_allowed=false` o clave de solo lectura | No se envía journal ni hitos; aviso en `/doctor` |
| `structured` rechazado con 422 (`invalid_observation`, `sensitive_source_requires_review`) | Se marca como fallido permanente con el motivo (no se reintenta igual); se redacta antes de enviar para evitarlo |
| `tools/list` sin alguna herramienta necesaria | `health` → `degradado` nombrando la herramienta que falta y la versión esperada |

## Criterios de aceptación

Cada criterio dice cómo se comprueba. Los `[GWT]` se prueban con el servidor MCP falso salvo
que se indique «integración real».

- [ ] [GWT] CA-01 — Dado un proyecto sin `backends.<id>` de tipo `kairos`, Cuando se ejecutan `/doctor`, `knowledge-find.py` y los hooks, Entonces no se abre ninguna conexión de red y la capacidad sale «desactivada» (no error). *Comprobación:* test con socket espía + `tests/test_hook_network_egress.py` en verde.
- [ ] [GWT] CA-02 — Dado `/setup` con un `project_id` inválido, un host público sin `allow_remote` o una ruta de clave dentro del proyecto, Cuando se valida la config, Entonces se rechaza con un mensaje que nombra el campo y no se escribe `taxonomy.json`. *Comprobación:* test del validador con los tres casos.
- [ ] [GWT] CA-03 — Dado el servidor falso que exige `Bearer`, Cuando el cliente MCP genérico llama `initialize`, `tools/list` y `tools/call`, Entonces todas las peticiones llevan `Authorization: Bearer <clave>`, la clave no aparece en salidas, logs ni outbox, y no se siguen redirecciones. *Comprobación:* test del cliente + búsqueda del valor de la clave en todo lo escrito.
- [ ] [GWT] CA-04 — Dado Kairos caído, Cuando se ejecutan `/doctor`, una lectura con `--intent` y `knowledge-sync.py`, Entonces `/doctor` marca ⚠️ con el remedio, la lectura devuelve los aciertos locales con el motivo y el sync reencola sin dead-letter; todos acaban dentro del tope de tiempo y con exit 0 donde el ciclo lo exige. *Comprobación:* test con servidor apagado.
- [ ] [GWT] CA-05 — Dado `approved/` con 3 entradas (una sin routing) y `candidates/` con 2, Cuando se publica, Entonces solo llegan 2 `publish_document` (las enrutadas) y ninguna candidata. *Comprobación:* registro de llamadas del servidor falso.
- [ ] [GWT] CA-06 — Dada una entrada publicada, Cuando se inspecciona la llamada, Entonces `source.sha256` es el SHA-256 hex minúsculo de los bytes UTF-8 exactos de `content`, `tags` es una lista (comas, comillas y acentos intactos) y `document_id` es estable entre ejecuciones y tras borrar el estado local. *Comprobación:* test que recalcula el hash y repite el plan.
- [ ] [GWT] CA-07 — Dado un timeout tras `publish_document`, Cuando se reintenta, Entonces se consulta `document_status` antes de reenviar y el reenvío usa el mismo ID, versión y contenido; el servidor falso registra un solo documento. *Comprobación:* test de entrega incierta.
- [ ] [GWT] CA-08 — Dada una entrada que sale de `approved/`, Cuando se sincroniza, Entonces se llama `revoke_document` con la versión siguiente y una publicación posterior del mismo ID no se envía (se reporta). *Comprobación:* test de revocación + intento de resurrección.
- [ ] [GWT] CA-09 — Dado un desfase entre local y remoto (documento ausente, versión distinta, hash distinto), Cuando se ejecuta `knowledge-sync.py --check`, Entonces recorre `document_manifest` con cursor hasta `has_more=false`, sale ≠ 0 con un `desfase` que nombra la identidad y el remedio, y no publica nada. *Comprobación:* test con manifiesto de varias páginas.
- [ ] [GWT] CA-10 — Dado un intent autorizado y Kairos sano, Cuando un agente ejecuta `knowledge-find.py --intent <intent>`, Entonces usa solo la clave de lectura, cada acierto trae `id`, `estado`, `evidencia`, `ruta` y la marca de dato no confiable, y un texto recuperado con forma de instrucción no cambia la salida del script (se presenta como dato). *Comprobación:* test con respuesta envenenada del servidor falso.
- [ ] [GWT] CA-11 — Dada una clave de solo lectura, Cuando se intenta publicar, revocar o enviar journal, Entonces no se llama a ninguna herramienta de escritura y se informa «sin clave de escritura». *Comprobación:* test que verifica cero llamadas de escritura.
- [ ] [GWT] CA-12 — Dado `.kairos/installation.json` con captura activa y `capture_policy` con `capture_allowed=true`, Cuando llega un punto de cierre, Entonces el plugin no llama a `remember` para el journal. Dado lo contrario (sin captura o `capture_allowed=false` con clave de escritura válida y política que permite el envío explícito), Entonces envía un único `session-summary.v1` válido contra el esquema. *Comprobación:* test de las dos ramas + validación con el esquema de ejemplo.
- [ ] [GWT] CA-13 — Dado un evento episódico (journal o hito) enviado con timeout, Cuando se reintenta, Entonces reusa `event_id`, `item_id`, `version` y `occurred_at`; solo repite tras `event_status` con `found: false`; un `isError` no cuenta como ausencia. *Comprobación:* test de entrega incierta episódica.
- [ ] [GWT] CA-14 — Dado `config.hitos: true` y un ledger con una tarea cerrada, un veredicto de revisión y una retro, Cuando se envían los hitos, Entonces llegan exactamente esos 3 eventos y nada más del ledger; repetir el envío no crea eventos nuevos. *Comprobación:* test sobre un ledger de fixture.
- [ ] [GWT] CA-15 — Dado un servidor que responde 429 con `Retry-After: 2`, Cuando el cliente reintenta, Entonces no vuelve a llamar antes de 2 s y, si supera su plazo, reencola. *Comprobación:* test con reloj inyectado.
- [ ] [GWT] CA-16 — Dado un adaptador de fixture `type: "mcp-fixture"` que reutiliza el cliente MCP genérico con otro mapa de herramientas, Cuando se carga por `--backends-dir`, Entonces publica y lee sin tocar `knowledge-sync.py`, `backends/__init__.py` ni el cliente genérico. *Comprobación:* test de carga y diff vacío del núcleo.
- [ ] CA-17 — Ningún fichero nuevo o modificado nombra los backends retirados (salvo el antecedente histórico de `testing/retirada.md` y los CHANGELOG ya publicados). *Comprobación:* `git diff --name-only master...` filtrado con `grep -il` por los dos nombres retirados que lista `testing/retirada.md` → vacío.
- [ ] CA-18 — Funciona igual en Claude Code, Codex y OpenCode: ninguna pieza nueva tiene lógica por runtime y `python scripts/export-interop.py --check` sale 0. *Comprobación:* comando y `python scripts/lint_plugin.py` en verde.
- [ ] CA-19 — Todo texto enviado (documentos, journal, hitos) pasa por `agent-kits/shared/redact.py`. *Comprobación:* test con un secreto de prueba en una entrada aprobada que no aparece en la llamada.
- [ ] CA-20 — Integración real (la ejecuta la sesión kairos o el usuario contra su servidor local): la lista de «Criterios de aceptación para el equipo consumidor» del repo knowledge-graphs (`docs/integration.md`) pasa, con versiones, IDs de prueba y resultados adjuntos en `testing/` sin claves. *Comprobación:* informe en `docs/roadmap/2026-11-26-kairos-memory/testing/`.

## Pruebas

- Unitarias con TDD (Constitución): cliente MCP genérico, adaptador `kairos`, envío episódico, validador de config. Servidor MCP falso en proceso que reproduce `tools/list`, `Bearer`, `isError`, 401/429/503, recorte de bytes y paginación.
- Las `[GWT]` CA-01..CA-16 se traducen 1:1 a tests del repo (no E2E de navegador).
- Suites existentes que deben seguir en verde: `tests/test_hook_network_egress.py`, `tests/test_sync_write_gate.py`, suites de `skills/knowledge-services/scripts/`, `evals/check.py`, `scripts/lint_plugin.py`, `export-interop.py --check`.
- CA-20 es una prueba de integración manual contra el servidor real; no la sustituyen `/doctor`, un HTTP 200 ni las unitarias.

## Referencias

- Repo knowledge-graphs, `docs/contracts/kairos-mcp.json` (contrato MCP 0.4.1, 34 herramientas).
- Repo knowledge-graphs, `docs/integration.md`: «Conectar con kairos-mcp», «Dos flujos de escritura separados», «Capturar memoria con identidad estable», «Publicar conocimiento aprobado», «Conciliar antes de reenviar», «Criterios de aceptación para el equipo consumidor».
- Repo knowledge-graphs, `docs/install.md` (captura `--capture off|summary|full`, `.kairos/installation.json`) y `docs/contracts/session-summary.v1.schema.json`.
- `skills/knowledge-services/backends/README.md` (contrato de 6 funciones y opcionales `puede_leer`/`consultar`).
- `skills/knowledge-services/references/add-backend.md` y `references/project-integration.md`.
- `docs/CONSTITUTION.md`, líneas 20 (sin red en hooks), 34 (`redact.py`, sin secretos) y 37 (red opt-in, local/privada por defecto, solo lo aprobado).
- `docs/roadmap/2026-11-10-plugin-audit-2/testing/retirada.md` (antecedente: commit recuperable del cliente MCP retirado, que no enviaba `Bearer`).
- Iniciativas previas: `docs/roadmap/2026-09-15-knowledge-services/`, `2026-10-31-memory-integrations/`, `2026-11-03-knowledge-verification/`.

## Decisiones confirmadas (revisión del usuario · 2026-11-18)

1. Transporte MCP, no REST. **Confirmado.**
2. Opt-in en `/setup`, comprobado por `/doctor`. **Confirmado.**
3. Journal solo si está configurado y sin duplicar la captura del cliente kairos. **Confirmado.**
4. Solo se publica lo aprobado. **Confirmado.**
5. Un `project_id` fijado en `/setup`. **Confirmado.**
6. Claves separadas de lectura y escritura. **Confirmado.**
7. Del ledger, solo hitos; `tasks.md` sigue canónico. **Confirmado.**
8. Sin acoplar el plugin: Kairos es el primer adaptador por `type`. **Confirmado.**
9. Nada relacionado con los backends retirados se reutiliza por nombre; el cliente MCP se reescribe genérico (2026-11-26). **Confirmado.**

## Preguntas abiertas

1. **¿Dónde vive el adaptador `kairos`?** La 4.0.0 dejó `backends/` sin adaptadores, y la decisión 8 pide que Kairos sea «el primer adaptador». Opciones: (a) incluirlo en el plugin (`backends/kairos.py` + cliente MCP genérico compartido), inactivo hasta `/setup`; (b) plantilla que `/setup` copia al proyecto. **Recomendación: (a).** Revierte en parte la política de la 4.0.0, pero una plantilla copiada se queda sin actualizaciones de seguridad. **Impacto:** alto en alcance y en docs (`backends/README.md`, `SKILL.md`, CHANGELOG).
2. **¿Qué es «un agente independiente que consulta sin escribir»?** (a) Los agentes actuales leen vía `knowledge-find --intent` con la clave de lectura; (b) un agente nuevo `memory-reader`. **Recomendación: (a)**, sin agente nuevo (un rol, un dueño; LES-013). La clave de lectura garantiza que esa vía no puede escribir. **Impacto:** medio (un agente nuevo exige doc, evals, interop).
3. **¿Se permiten hosts remotos?** La Constitución limita la red a hosts locales/privados por defecto. **Recomendación:** local/privado por defecto; `allow_remote: true` explícito en `/setup` exige `https` y nunca permite IMDS. **Impacto:** medio (guardarraíl y tests de host).
4. **¿Cuáles son los «puntos de cierre» del journal y los hitos?** Los hooks no pueden hacer red. **Recomendación:** el envío lo dispara un paso explícito en `/dev-cycle` Fase 6 y en `/retro` (más un comando manual `knowledge-sync`), que drena lo que `SessionEnd` dejó en local. Las sesiones sin ciclo quedan pendientes hasta el siguiente cierre. **Impacto:** alto en diseño (qué orquestadores cambian).
5. **¿Qué pasa si una entrada revocada vuelve a `approved/`?** Kairos no resucita un ID revocado. **Recomendación:** nuevo `document_id` (UUIDv5 con sufijo de generación guardado en el estado local) y aviso en el informe de sync. **Impacto:** medio (estado local y reconciliación).

## Supuestos

- **Hecho técnico:** el marco carga adaptadores por `type` y valida las 6 funciones; `consultar` es lo que hace enrutable la lectura — `skills/knowledge-services/backends/README.md` (tablas «Las 6 funciones» y «Funciones OPCIONALES»).
- **Hecho técnico:** el plugin no incluye adaptadores desde la 4.0.0 — `skills/knowledge-services/backends/README.md` («El plugin no incluye adaptadores»).
- **Hecho técnico:** la red está vetada en hooks y toda capacidad con red es opt-in y local/privada por defecto — `docs/CONSTITUTION.md:20` y `:37`.
- **Hecho técnico:** el router de lectura exige `puede_leer` con `puede: true` antes de consultar — `agent-kits/shared/knowledge-find.py:1722`.
- **Hecho técnico:** la captura del cliente kairos se declara en `.kairos/installation.json` (`automation.capture`) — repo knowledge-graphs, `client/lib/install.mjs:74-89`.
- **Hecho técnico:** kairos-mcp 0.4.1 acepta solo `Bearer`, marca las lecturas con `untrusted: true` y recorta respuestas a 32 KiB/256 KiB — repo knowledge-graphs, `docs/integration.md` («Conectar con kairos-mcp»).
- **Hecho técnico:** el cliente MCP retirado no enviaba `Bearer` — `docs/roadmap/2026-11-10-plugin-audit-2/testing/retirada.md`.
- **Restricción de negocio (supuesto hasta confirmar):** los límites por clave (cuotas diarias de escritura, 429 uniformes, rotación `replaced_by`) llegarán después; el cliente se diseña para tolerarlos ya — la confirmaría la sesión kairos.
- **Restricción de negocio (supuesto hasta confirmar):** el plugin puede saber, por MCP y sin `/v1`, qué scopes tiene una clave (vía `projects`/`capture_policy`) — la confirmaría la sesión kairos.
- **Restricción de negocio (supuesto hasta confirmar):** un envío explícito del plugin con `remember` está permitido aunque la política de captura automática del proyecto esté en `off` (si no, el journal explícito solo funcionaría con captura habilitada) — la confirmaría la sesión kairos.
- **Restricción de negocio (supuesto hasta confirmar):** los hitos del ledger encajan como `event_type` `note` o `learning` con `payload.structured` `observation.v1` (`type: decision|change`) — la confirmaría la sesión kairos.
- **Incógnita:** el presupuesto y plazo no se han fijado; los dará `evaluator`.
