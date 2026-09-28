---
spec: project-dashboard
descripcion: Dashboard único y opcional con el estado de todos los proyectos que usan custom-agents — emisor opt-in en el plugin (contrato JSON versionado, sin red en hooks, cola local) y dashboard aparte (API con token por proyecto, SQLite con historial, UI de kanban/detalle/métricas y MCP de consulta de solo lectura)
estado: aprobada          # borrador | aprobada | implementada | obsoleta
creado: 2026-09-28
actualizado: 2026-09-28
evaluacion: evaluation.md
design: n/a               # se espera design.md del agente architect si hay go (stack, repo, contrato, historial)
plan: pendiente
generacion:               # usage-meter.py close degradó (sin transcripciones del worktree C:/tpd): tokens/€ ESTIMADOS a juicio
  inicio: 2026-09-28T11:43:36Z
  fin: 2026-09-28T11:52:04Z
  fuente: estimado
  tokens_reales: { entrada: 30000, salida: 35000, cache_creacion: 120000, cache_lectura: 1500000 }   # estimado
  eur: 2.32               # estimado con precioTokens de rates.json (verificado 2026-08-18) × 0,92
  horas_ia: 0.39          # 185.000 tok facturables ÷ 479326
  duracion: 8m            # reloj medido por el meter (duracion_reloj)
  ratio_usado: 479326     # CALIBRATION.md (mediana de 5)
---

# Dashboard multi-proyecto de custom-agents

> **Evaluación:** [`evaluation.md`](evaluation.md)
> **Plan de implementación:** pendiente (handoff a `planner` tras la puerta go/no-go y, recomendado, `architect`)

> **Terminología:**
> - **Emisor**: la parte que vive en el plugin (`dashboard-sync.py` + config + comando). Solo lee lo que el plugin ya calcula y lo envía.
> - **Dashboard**: el componente aparte (API + almacenamiento + UI + MCP de consulta) que recibe y muestra los datos.
> - **Envío (snapshot)**: un JSON completo del estado de un proyecto en un instante, validado contra el contrato.
> - **`project`**: etiqueta de presentación del dashboard. **No** es un `project_id` de aislamiento ni un tenant del plugin (ver ADR-018 y D-02).
> - **Ronda fixN**: cada ronda de corrección posterior a una revisión (`T-XX-fixN` en el ledger), con su coste medido.

## Contexto y objetivo

Hoy cada proyecto que usa el plugin ve su estado solo desde dentro: `/roadmap-status` y `/roadmap-metrics` (skill `roadmap-dashboard`, `build_dashboard.py`) escanean su propio `docs/roadmap/`, y `/doctor` su propia instalación. No hay forma de ver **a la vez** todos los proyectos: qué iniciativas están abiertas, qué tareas están en revisión o bloqueadas, cuántos gaps Critical/Important siguen abiertos, cuánto se ha gastado este mes o qué instalación está rota.

El objetivo (decidido con el usuario el 2026-09-28) es un **dashboard único y opcional**, desplegable en local o en Docker, accesible desde la misma red o, de forma explícita, desde fuera. **Nada es obligatorio**: el proyecto que quiera aparecer lo configura y entonces envía datos; sin configurar, el plugin funciona exactamente igual que hoy.

Fuentes: conversación con el usuario (2026-09-28, recogida por `/pm-cycle`); lectores existentes del plugin (ver Referencias).

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| D-01 Opt-in | **Emisor apagado por defecto**: solo actúa si existe `.claude/dashboard.json` con `enabled: true` | Regla del plugin «degradación, no bloqueo»; sin config, cero diferencias de comportamiento |
| D-02 Identidad del proyecto | **`project` = etiqueta de presentación**, no identificador de aislamiento | ADR-018 rechazó un `project_id`/control plane multi-proyecto dentro del plugin; aquí el aislamiento del plugin sigue siendo el proyecto consumidor. Requiere un **ADR nuevo** que lo deje escrito |
| D-03 Qué se envía | **JSON estructurado derivado de lo que el plugin ya calcula**, reutilizando sus lectores (sin parsers nuevos donde ya hay uno) | Una sola fuente de verdad por dato; evita divergencias entre `/roadmap-status` y el dashboard |
| D-04 Qué NO se envía nunca | **Ni código, ni prompts, ni conversaciones, ni secretos**; piezas/MCP solo por nombre y tipo, sin `env` de MCP; textos libres pasan por `redact.py` y se truncan | Privacidad; el dashboard puede estar en otra máquina o expuesto |
| D-05 Cuándo se envía | **En las puertas de los orquestadores** (`/dev-cycle`, `/pm-cycle`, `/retro`) y **a demanda** (`/dashboard-sync`); **nunca desde un hook** | Regla del plugin: los hooks no usan red y salen siempre con exit 0 |
| D-06 Fallo de red | **Cola local reutilizando `outbox.py`**; el ciclo nunca se bloquea | `outbox.py` ya resuelve staging, reintentos y dead-letter con tests |
| D-07 Contrato | **JSON versionado (`schema_version`, semver) con JSON Schema y test en el plugin**; el dashboard acepta la versión mayor que conoce y rechaza con 4xx lo que no | Emisor y dashboard evolucionan por separado |
| D-08 Determinismo | **Recolección y envío en un script con tests y exit codes**; el envío NUNCA por MCP | Regla «Determinismo» del plugin; un MCP lo invoca un modelo y no es determinista |
| D-09 Ubicación del dashboard | **Componente aparte (recomendado: repo `custom-agents-dashboard`) con `docker-compose`** — decisión final de `architect` | No se empaqueta con el plugin ni se instala en los consumidores |
| D-10 Seguridad v1 | **Sin login de usuarios**: token de escritura **por proyecto**, token de lectura **compartido**, bind por defecto a `127.0.0.1`/red privada, exposición externa solo explícita y detrás de TLS (proxy inverso) | Mínimo razonable para la v1; el modelo de datos ya particionado por proyecto permite login con permisos por proyecto más adelante |
| D-11 Historial | **SQLite con historial de envíos** que permita reconstruir la evolución de cada tarea | Detalle de tarea con línea de tiempo (E2); la granularidad (snapshot completo vs por entidad) y la retención las fija `architect` |
| D-12 Stack | **Lo decide `architect`** (UI y backend) | Fuera de la competencia de la spec; afecta a coste de E1 |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Activación | `.claude/dashboard.json` → `enabled` | ausente = apagado | **`true` para aparecer** |
| Etiqueta del proyecto | `dashboard.json` → `project` | nombre de la carpeta del repo | **etiqueta legible elegida por el usuario** |
| URL del dashboard | `dashboard.json` → `url` | — | **`http://127.0.0.1:<puerto>` o la URL TLS del proxy** |
| Token de escritura | `dashboard.json` → `token_env` (**nombre** de la variable de entorno) | `CUSTOM_AGENTS_DASHBOARD_TOKEN` | **el token nunca se guarda en el fichero** |
| Versión del contrato | campo `schema_version` del JSON | `1.0.0` | sube minor al añadir campos (E2/E3), major si rompe |
| Bind del dashboard | `docker-compose` / variable del servidor | `127.0.0.1` | red privada o proxy TLS solo si se pide explícitamente |
| Token de lectura | variable del servidor | — | compartido por quien consulta la UI y el MCP |
| Retención del historial | config del servidor | ⚠️ a decidir por `architect` | — |

## Arquitectura y componentes

**Emisor (en el plugin, opt-in)** — nuevo salvo donde se indica:

- `.claude/dashboard.json` y su esquema; paso opcional en `/setup`; comprobación en `/doctor` (configurado · dashboard alcanzable · cola pendiente), registrado como **capacidad** en `capabilities.py` (como `kwipu`/`training`) para que `/setup` y `/doctor` no necesiten código específico.
- `dashboard-sync.py` (nuevo, determinista, con tests): recolecta, valida contra el contrato, redacta, envía por HTTP y, si falla, encola.
- **Reutiliza** (solo lectura, sin reescribirlos): `build_dashboard.py --json` (iniciativas y artefactos), `ledger-lint.py` y su `REVISION_HDR_PATTERN` (tareas y cabeceras de revisión), `progress-report.py --json` (progreso), parser de secciones de revisión de `jira-flow.py` (`secciones_revision`, filas de gaps), `usage-meter.py` (costes medidos), `doctor.py --json` y `capabilities.py` (salud y piezas), `redact.py` (secretos), `outbox.py` (cola).
- Comando `/dashboard-sync` (a demanda) y una línea en las puertas de `/dev-cycle`, `/pm-cycle` y `/retro` que lo invoca si está activo.
- Contrato JSON versionado (`schema_version`) con JSON Schema y test en el plugin; regeneración de interop (`export-interop.py`) para Codex/OpenCode.

**Dashboard (componente aparte)** — todo nuevo:

- API de recepción (`POST` por proyecto con token de escritura) y de consulta (token de lectura).
- Almacenamiento SQLite particionado por proyecto, con historial de envíos.
- UI: portada, kanban de iniciativas, kanban de tareas, detalle de tarea, detalle de iniciativa, salud, métricas globales.
- MCP de consulta de **solo lectura** (proyectos, tareas bloqueadas, costes).
- `docker-compose` con bind por defecto a localhost y ejemplo de proxy inverso TLS para exponerlo fuera.

## Flujo (paso a paso)

1. El usuario activa el dashboard en un proyecto (paso opcional de `/setup` o editando `.claude/dashboard.json`) y exporta el token en la variable de entorno indicada.
2. Al pasar una puerta de `/dev-cycle`, `/pm-cycle` o `/retro` (o al lanzar `/dashboard-sync`), el orquestador invoca `dashboard-sync.py`.
3. `dashboard-sync.py` recolecta con los lectores existentes, construye el JSON, lo valida contra el contrato y pasa los textos libres por `redact.py`.
4. Envía por HTTP con el token de escritura del proyecto. Si el dashboard no responde o da 5xx, lo deja en la cola de `outbox.py` y **sale sin bloquear** (aviso de una línea).
5. En el siguiente envío (o con `/dashboard-sync --drain`), la cola se vacía en orden.
6. El dashboard valida el token y la versión del contrato, guarda el envío en el historial del proyecto y actualiza la vista actual.
7. La UI y el MCP de consulta leen con el token de lectura.

## Alcance

- **Dentro (esta iniciativa, por entregas):**
  - **E1 — emisor + backend + portada + kanbans:** config, `/setup`, `/doctor`, capacidad, `dashboard-sync.py`, `/dashboard-sync`, puertas, cola, contrato v1 con test, interop; datos de iniciativas (spec/evaluación/diseño/plan con estados), tareas `T-XX` (estado con vocabulario cerrado, fase, horas real/estimado, verificación) y resumen de salud; API con token por proyecto, SQLite con historial, seguridad v1, `docker-compose`; **portada** con tarjeta por proyecto (iniciativas abiertas, % de tareas, en revisión/bloqueadas, coste del mes, salud, último envío; filtros y orden «necesita atención»), **kanban de iniciativas** (idea → spec aprobada → evaluada go → en implementación → en revisión → cerrada) y **kanban de tareas** por iniciativa (`borrador` → `en-progreso` → `en-revision` → `completado`, `cancelado` plegado; carriles por fase).
  - **E2 — revisiones y reintentos:** el emisor añade **secciones de revisión por intento** (lentes, gaps con grado/estado/evidencia), **rondas fixN** con coste, veredicto de qa, retro y fila de calibración (contrato v1.1); **detalle de tarea** con línea de tiempo (rondas de revisión con lentes y gaps, fixN con coste, verificación dirigida, cierre) y tabla de gaps filtrable; **detalle de iniciativa** (artefactos enlazados, coste real vs estimado por fase, embudo de gaps por intento, resultado final: qa, retro, calibración). La tarjeta de portada y la del kanban de tareas ganan gaps Critical/Important e intento «2/3» o «fix5».
  - **E3 — métricas, salud y MCP:** el emisor añade salud completa de la instalación y piezas/MCP instalados (solo nombres y tipos); **salud de la instalación** en la UI; **métricas globales** (coste por proyecto/mes, desviación estimado/real, gaps por lente, rondas medias hasta cerrar); **MCP de consulta de solo lectura** (proyectos, tareas bloqueadas, costes).
- **Fuera (siguientes specs):**
  - Login de usuarios y permisos por proyecto (fase futura; el modelo de datos ya queda particionado).
  - Envío desde hooks, envío por MCP, envío de código, prompts o conversaciones.
  - Integración con dashboards de terceros. Headroom solo como referencia: su dashboard es de una instalación; la visión de organización es su oferta de pago.
  - (Opcional, futuro) métricas de ahorro de Headroom como fuente opt-in adicional, con el mismo patrón de capacidad que `kwipu`.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Sin `.claude/dashboard.json` o `enabled: false` | `dashboard-sync.py` sale con exit 0 sin hacer nada; los orquestadores no muestran nada |
| Config inválida (JSON roto, falta `url`/`project`) | Aviso de una línea con el fichero y el arreglo; `/doctor` lo marca ❌; el ciclo continúa |
| Variable del token ausente | Aviso «token no definido en `$<token_env>`», no se envía ni se encola; `/doctor` ⚠️ |
| Dashboard caído, timeout o 5xx | Envío a la cola de `outbox.py`; aviso breve; exit 0 del paso; reintento en el siguiente envío |
| 401/403 (token incorrecto) | No se reintenta en bucle: dead-letter con causa; `/doctor` ⚠️ con el arreglo |
| 4xx por versión de contrato | Dead-letter con causa «contrato vX no soportado»; `/doctor` sugiere actualizar dashboard o plugin |
| Lector del plugin falla o ledger ilegible | Ese bloque sale como `no-verificable` con motivo; el resto del envío sigue |
| Ledger histórico con tablas de gaps en formato antiguo | Se envía lo que se puede parsear; el resto como `no-verificable`, sin inventar grados ni estados |
| Texto con apariencia de secreto | `redact.py` lo sustituye antes de validar y enviar |
| Dashboard recibe un envío de un proyecto desconocido | 401; el alta de proyectos (y su token) es explícita en el servidor |

## Criterios de aceptación

**Emisor (plugin)**

- [ ] [GWT] CA-01 — Dado un proyecto sin `.claude/dashboard.json`, Cuando se completa `/dev-cycle` o se ejecuta `dashboard-sync.py`, Entonces no hay ninguna petición de red, ningún fichero nuevo en la cola y el exit es 0.
- [ ] [GWT] CA-02 — Dado un proyecto configurado y el dashboard caído, Cuando se pasa una puerta de `/dev-cycle`, Entonces el envío queda en la cola de `outbox.py`, el ciclo continúa y `/doctor` informa de «cola pendiente: 1».
- [ ] [GWT] CA-03 — Dado el dashboard de nuevo disponible y una cola con N envíos, Cuando se ejecuta `/dashboard-sync`, Entonces se entregan los N en orden y la cola queda vacía.
- [ ] [GWT] CA-04 — Dado un ledger con un texto que contiene un token con forma de secreto, Cuando se genera el JSON, Entonces el secreto aparece redactado y el JSON valida contra el esquema del contrato.
- [ ] [GWT] CA-05 — Dado un proyecto con MCP configurados con `env`, Cuando se genera el JSON de E3, Entonces solo aparecen nombre y tipo de cada MCP y ninguna clave ni valor de `env`.
- [ ] El contrato JSON tiene `schema_version`, JSON Schema versionado en el plugin y un test que valida un envío real generado sobre ledgers de este repo.
- [ ] Ningún hook del plugin invoca `dashboard-sync.py` ni abre red (lo comprueba un test o el linter).
- [ ] `/setup` ofrece el paso opcional y `/doctor` muestra la fila de la capacidad (configurado · alcanzable · cola).
- [ ] `export-interop.py --check` en verde tras añadir el comando y los cambios de orquestadores.

**Dashboard**

- [ ] [GWT] CA-06 — Dado un envío con el token de otro proyecto, Cuando llega al endpoint de recepción, Entonces responde 401/403 y no se guarda nada.
- [ ] [GWT] CA-07 — Dado el `docker-compose` por defecto, Cuando se arranca, Entonces el servicio solo escucha en `127.0.0.1` (no accesible desde otra máquina de la red sin cambio explícito).
- [ ] [GWT] CA-08 — Dado dos envíos del mismo proyecto con una tarea que pasa de `en-progreso` a `en-revision`, Cuando se consulta el historial de esa tarea, Entonces se ven los dos estados con su fecha de envío.
- [ ] [GWT] CA-09 — Dado tres proyectos, uno con una tarea bloqueada y gaps Critical abiertos, Cuando se abre la portada ordenada por «necesita atención», Entonces ese proyecto aparece primero y su tarjeta muestra las tareas bloqueadas y los gaps.
- [ ] [GWT] CA-10 — Dada una iniciativa con tareas en varias fases, Cuando se abre su kanban de tareas, Entonces cada tarea está en la columna de su estado y en el carril de su fase, y `cancelado` aparece plegado.
- [ ] [GWT] CA-11 — Dada una tarea con 3 intentos de revisión y 2 rondas fixN, Cuando se abre su detalle (E2), Entonces la línea de tiempo muestra los 3 intentos con sus lentes y gaps y las 2 rondas con su coste, y la tabla de gaps se puede filtrar por grado y estado.
- [ ] [GWT] CA-12 — Dado el MCP de consulta (E3), Cuando se pide «tareas bloqueadas», Entonces devuelve la lista por proyecto y cualquier operación de escritura no existe o se rechaza.
- [ ] La exposición externa está documentada solo detrás de un proxy inverso con TLS, con ejemplo.
- [ ] El modelo de datos lleva el proyecto como partición en todas las tablas (preparado para login con permisos por proyecto).

**Transversales**

- [ ] ADR nuevo que registra que `project` es etiqueta de presentación y no reabre el control plane rechazado por ADR-018.
- [ ] Documentación ES/EN del emisor (y del dashboard en su repo) y fila en `docs/README.md` si hay pieza nueva.

## Pruebas

- **Emisor:** tests unitarios de `dashboard-sync.py` (config ausente/inválida, token ausente, red caída → cola, 401 → dead-letter, redacción, truncado, `no-verificable`), test de contrato que valida un envío generado sobre ledgers reales del repo (incluidos los heterogéneos), test de que ningún hook lo invoca, suites de `capabilities`/`doctor`/`setup` ampliadas, `export-interop.py --check`.
- **Dashboard:** tests de API (tokens por proyecto, 401/403, versión de contrato, historial), test de bind por defecto, tests de consultas del MCP (solo lectura), E2E de UI con Playwright en local para los criterios `[GWT]` CA-06 a CA-12 (qa, solo local).
- Los criterios `[GWT]` se traducen 1:1 a bloques del `test-plan.md` (mismo ID `CA-XX`).
- Auditoría de seguridad opcional con `nemesis` contra el dashboard levantado en local.

## Referencias

- `skills/roadmap-dashboard/scripts/build_dashboard.py` (`scan`, `--json`): iniciativas, artefactos, `generacion:`.
- `agent-kits/shared/ledger-lint.py:186` (`REVISION_HDR_PATTERN`): cabeceras «Revisión de dos lentes — intento N».
- `skills/jira-sync/scripts/jira-flow.py:317` (`secciones_revision`), `:479` (`gap_pendiente`), `:489` (`filas_pendientes_de_tarea`): secciones y filas de gaps.
- `agent-kits/shared/progress-report.py` (`--json`), `usage-meter.py`, `doctor.py` (`--json`, tope total de red `CAPACIDADES_PRESUPUESTO_S`), `capabilities.py` (contrato `{id, config_path, enabled, health, doctor, setup_step}`), `redact.py`, `outbox.py`.
- `docs/knowledge/adr/ADR-018-arquitectura-de-memoria-markdown-canonico-backends-declarados.md` (punto 2 y «Control plane multi-proyecto» rechazado).
- `CLAUDE.md` (reglas «Hooks», «Determinismo», «Degradación, no bloqueo», «Interop»).

## Decisiones confirmadas (revisión del usuario · 2026-09-28)

1. Dashboard único y **opcional**; sin configurar, el plugin funciona igual. **Confirmado.**
2. Envío en las puertas de los orquestadores y a demanda, **nunca desde hooks** ni por MCP. **Confirmado.**
3. Nunca se envía código, prompts, conversaciones ni secretos; piezas/MCP solo por nombre y tipo. **Confirmado.**
4. Seguridad v1 sin login, con token de escritura por proyecto y token de lectura compartido; login con permisos por proyecto como fase futura. **Confirmado.**
5. Entregas E1/E2/E3, cada una útil por sí sola; MCP de consulta en E3. **Confirmado (ajustable por la evaluación).**
6. Stack y ubicación final del dashboard: los decide `architect` si hay go. **Confirmado.**

## Supuestos

- **Volumen:** decenas de proyectos y cientos de tareas por proyecto; un envío completo cabe en unos cientos de KB. Lo verifica un envío real generado sobre este repo (el que más iniciativas tiene).
- **Textos de gaps:** se envía el resumen del gap truncado (≤ 200 caracteres, tras `redact.py`) y la evidencia como referencia `fichero:línea`, nunca el fragmento de código citado. Si el usuario prefiere no enviar texto de gaps, queda solo grado/estado/lente/tarea (⚠️ a confirmar en la puerta).
- **Historial:** se guardan los cambios por entidad (tarea, gap, iniciativa) con hash de contenido, no el snapshot completo en cada envío, para que el tamaño crezca con los cambios y no con la frecuencia de envío (decisión final de `architect`).
- **Retención:** ⚠️ sin decidir (propuesta inicial: todo el historial de estados; snapshots completos solo los últimos N).
- **Ledgers históricos:** las tablas de gaps y las líneas `Tiempo IA (fixN)` no tienen hoy un formato canónico validado (hay variantes `Corrección`/`Correccion`, con y sin columna `Lente`); E2 formaliza el formato en `ledger-lint` y lo que no case se envía como `no-verificable`.
- **ADR:** el número del ADR nuevo se asigna al crearlo (la rama `feature/training-data-services`, aún sin mergear, ya cita un ADR-019).
- **Ubicación:** si el dashboard vive en un repo aparte, su cadena de artefactos (`docs/roadmap/`, ledger, revisión) y su CI viven en ese repo, y esta iniciativa cubre en este repo solo el emisor, el contrato y el ADR (a confirmar por `architect`).
