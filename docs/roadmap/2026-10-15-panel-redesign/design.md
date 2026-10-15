---
design: panel-redesign
titulo: "Rediseño del panel local: multi-página, kanban y gráficos"
estado: aprobado              # borrador | aprobado | obsoleto
creado: "2026-10-15"
actualizado: "2026-10-15"
spec: spec.md                 # enlace hacia atrás (misma carpeta)
evaluacion: evaluation.md
plan: improvement-plan.md     # creado por el planner el 2026-10-15
adr: docs/knowledge/candidates/pending/2026-10-15-plugin-panel-dueno-unico-de-la-presentacion.md   # sha256 1128a65fcbbf5a31733d5bfa87f9fffb183c006ad88f84c848c64f91a73351f9; lo decide knowledge-curator (ID sugerido custom-agents.ADR-024)
opcion_elegida: "O1+O5"       # D-A1 = O1, D-A2 = O5; fijadas por instrucción del orquestador (estructura aprobada por el usuario); revisables por el usuario
generacion:                   # usage-meter.py close (marcador abierto tras el recon del repo y la doc oficial: cubre la redacción; la ventana puede incluir el transcript del evaluator en paralelo)
  inicio: 2026-10-15T09:29:45Z
  fin: 2026-10-15T09:38:37Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-6ffc6375d334471b9b14d14cca8bace5
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 36, salida: 34732, cache_creacion: 40566, cache_lectura: 4966593 }
  tokens_procedencia: transcript
  tokens_cobertura: completa
  coste_procedencia: estimado_tarifa
  coste_cobertura: completa
  eur: 3.32
  horas_ia: 0.14
  duracion: 8m
  ratio_usado: 531798.5     # CALIBRATION.md (mediana de 6)
  avisos: ["CALIBRATION: 7 filas marcadas (estimado) fuera de la mediana", "tarifa verificada el 2026-08-18", "transcripts_subagente: 1 (posible solape con el evaluator en paralelo)"]
---

# Diseño — Rediseño del panel local: multi-página, kanban y gráficos

> **Spec:** [`spec.md`](spec.md) (aprobada) · **Evaluación:** [`evaluation.md`](evaluation.md) (en redacción en paralelo) · **Plan:** [`improvement-plan.md`](improvement-plan.md) · **Decisión propuesta:** [`candidates/pending/2026-10-15-plugin-panel-dueno-unico-de-la-presentacion.md`](../../knowledge/candidates/pending/2026-10-15-plugin-panel-dueno-unico-de-la-presentacion.md) (pendiente del Curator)

| | |
|---|---|
| **Estado** | aprobado |
| **Opción elegida** | D-A1: **O1** — `plugin-panel` dueño único de la presentación · D-A2: **O5** — captura asíncrona post-herramienta con atribución por ventana declarada |
| **Validada por el usuario** | 2026-10-15, vía orquestador. El usuario aprobó la estructura en la spec; el orquestador pidió fijar la recomendada. **El usuario puede cambiar cualquiera de las dos**: basta con re-invocar al architect con `elegida: O<n>` para esa decisión. |

## 1. Contexto y restricciones

La spec pide un panel local de 7 páginas (Inicio, Iniciativas, Plan, Agentes en vivo, Memoria, Catálogo, Diagnóstico). Tiene menú común, kanban de solo lectura, gráficos con Chart.js incluido y dos modos: servido en `127.0.0.1` y exportado a carpeta. No hace red, cumple WCAG 2.2 AA y marca los datos ausentes como ausentes. Deja abiertas dos decisiones: quién es el dueño de la presentación (D-A1) y cómo se capturan las herramientas para «Agentes en vivo» (D-A2).

**Qué hay hoy (hechos del repo):**

- `skills/plugin-panel/scripts/build_panel.py` (814 líneas) genera **un** HTML. Usa `references/panel.html` y cuatro JS que se incrustan como `<script>` inline (`render_html`, l. 655-738): `panel-live.js`, `panel-memory.js`, `panel-activity.js` y `panel-review.js`. La marca de propiedad es `MARKER` (l. 19) y el generador solo sobrescribe HTML que la lleva (`_write_html`, l. 740).
- `skills/plugin-panel/scripts/serve_panel.py` (507 líneas) sirve **una** página en la ruta `''` y las API `api/progress`, `api/activity`, `api/memory` (POST) y `api/review/<id>/<op>` (l. 381-448). Usa un token de 43 caracteres en la ruta y rechaza `?`, `%`, `\` y `#` (l. 364-371). Valida Host, Origin y Sec-Fetch-Site (l. 347-362). La CSP es `default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-…'; connect-src 'self'` (l. 492-493) y el nonce se inyecta reemplazando el literal `<script>` (l. 470). El id de una iniciativa es `sha256(carpeta)[:16]` (l. 184).
- `skills/roadmap-dashboard/scripts/build_dashboard.py` (1.181 líneas) hace `scan()` (l. 451), `render_html()` (l. 573), `render_markdown()`, `render_metrics_md()` y `--json` con `procedencia` (l. 1157-1170). Su HTML es una página estática de tarjetas, la salida `docs/roadmap/dashboard.html` de `/roadmap-status`.
- Actividad: `agent-kits/shared/agent-activity-store.py` solo acepta `SubagentStart`/`SubagentStop` (Claude, Codex) y eventos de ejecución de sesión (OpenCode) (l. 155-178). El inventario del estado está cerrado a 4 ficheros (l. 119-122). Lee la entrada hasta 64 KiB y, si es mayor, descarta el evento (l. 264-266). Las filas caducan a los 60 s (l. 217).
- El hook `agent-activity` se registra en `hooks/hooks.json` (l. 34-50) y en `interop/codex/hooks.json`. OpenCode lo invoca desde `hooks/opencode-plugin.js` (binding `activity`, l. 19). El launcher `hooks/run-hook.mjs` le da 2.000 ms (l. 26).
- `tests/test_graphiti_security.py` fija con huella el launcher (`_LAUNCHER_NODE_HASH`, l. 122; solo admite `child_process`, `fs`, `path` y `url`, l. 787) y el propio `agent-activity-store.py` con su cierre de módulos (`_CARGAS_LOCALES_REVISADAS`, l. 159-165). Cualquier cambio en estos dos ficheros exige revisión y huella nueva.
- `scripts/export-interop.py` fuerza `matcher: ^apply_patch$` en **todo** grupo `PostToolUse` de Codex (l. 407-408).

**Qué emite cada runtime (verificado en la documentación oficial el 2026-10-15):**

| Runtime | Evento de herramienta | Identidad del run en el evento | Duración | Resultado | Asíncrono |
|---|---|---|---|---|---|
| Claude Code | `PreToolUse`, `PostToolUse`, `PostToolUseFailure` con `tool_name`, `tool_input` y `tool_use_id` | `agent_id` y `agent_type` cuando la herramienta corre dentro de un subagente (doc: «the input carries the `agent_id` and `agent_type`») | `duration_ms` opcional en Post y Failure | Post = ok; Failure = error (`is_interrupt`) | `"async": true` en hooks `command` |
| Codex | `PreToolUse`, `PostToolUse` con `tool_name`, `tool_input`, `tool_use_id` y `turn_id`. Bash, `apply_patch`, MCP y herramientas locales; las alojadas (WebSearch) no pasan | **No documentada** en eventos de herramienta: «Subagent hooks use the parent session id» | no hay | no hay `PostToolUseFailure`; Post también salta con Bash de salida ≠ 0 | `async: true`, hasta 8 a la vez; los MCP siempre síncronos |
| OpenCode V2 | `tool.execute.before` y `tool.execute.after` (`status: completed\|error`) | `sessionID` (el subagente corre en sesión hija) y `agent` (ya lo usa la guardia, l. 163) | no documentada | `completed` / `error` | lo decide el plugin (puede no esperar al hijo) |

**Restricciones que fijan el espacio de soluciones**

- Constitución §2: no hay red desde hooks, solo stdlib de Python, `tasks.md` es el ledger canónico y cada responsabilidad tiene un único dueño (ADR-011).
- Constitución §4: todo texto persistido o exportado pasa por `redact.py`. Nunca se guarda chain-of-thought ni contenido crudo. Una pieza nunca sobrescribe lo que no ha creado.
- ADR-007 y ADR-023: los hooks informan y salen con exit 0; las guardias van por identidad nativa del runtime, nunca por texto del prompt ni por argumentos.
- La spec declara intocables los contratos de `dashboard.md`, `build_dashboard.py --json` y `doctor --panel-json`, además de los topes de `serve_panel.py` (256 KiB por fichero, 1 MiB por petición, 64 iniciativas y 64 KiB por respuesta salvo justificación) y el refresco de 5 s.
- `tests/test_graphiti_security.py`: el launcher solo importa módulos nativos de Node y su huella se revisa; el cierre de `agent-activity-store.py` se declara uno a uno.
- Multi-runtime: la pieza no sabe de runtimes; traduce `export-interop.py`, cuyo `--check` es puerta de CI y de `release.py`.

**Invariantes, propiedad de los datos y estados:**

- Propiedad de los datos:
  - `tasks.md` solo lo escribe su implementador; el panel lo lee.
  - `.claude/agent-activity/` solo lo escribe `agent-activity-store.py`.
  - En la carpeta exportada, el panel solo sobrescribe ficheros que él creó: HTML con `MARKER` y ficheros listados en su `export-manifest.json` con el hash que él escribió.
  - Los datos de cartera solo los calcula `build_dashboard.py`; el panel no los recalcula.
- Estados de un run:
  - `en curso`: señal de hace menos de 60 s.
  - `sin señal reciente`: más de 60 s; la duración se congela en la última señal.
  - `respuesta terminada`: solo si se observó `SubagentStop`.
  - Nunca se muestran «muerto» ni «terminado» inferidos.
- Estados de una ventana de atribución:
  - Transiciones: `abierta` (se vio `usage-meter.py start --artefacto <slug>/T-XX`) → `cerrada` (se vio `close` con la misma clave) | `reemplazada` (nuevo `start` en el mismo ámbito) | `caducada` (24 h).
  - Prohibido: `cerrada → abierta` sin un `start` nuevo.

## 2. Opciones (2-3)

### D-A1 — Dueño de la presentación y comando de entrada

#### O1 — `plugin-panel` absorbe la presentación; `roadmap-dashboard` queda como proveedor de datos

`plugin-panel` pasa a ser el **único** generador HTML del plugin, con 7 páginas en modo servido y en modo exportado. `roadmap-dashboard` conserva `scan()`, `--md`, `--metrics-md` y `--json` sin cambiar su contrato, y **retira** `--html` y `render_html()`. El panel importa `build_dashboard.py` como módulo del bundle (patrón `_load_shared` de `serve_panel.py`) para obtener cifras idénticas a `--json` (CA-01, CA-03). Para ello `build_dashboard.py` extrae a una función pura, `vista_json(inits)`, lo que hoy hace `main()` en l. 1157-1170; la refactorización no cambia bytes.

Comandos:

- `/plugin-catalog` es **el** comando que abre el panel. Por defecto exporta a una carpeta (`--export <dir>`, sustituye a `--html`); con `--serve` lo sirve; `--page <nombre>` elige la página de aterrizaje.
- `/roadmap-status` conserva su nombre y su `dashboard.md`. Su vista HTML pasa a ser la exportación del panel en `docs/roadmap/panel/`, aterrizando en `iniciativas.html`, en lugar de `dashboard.html`.
- La relación queda **documentada** en `docs/agents/ROLES.md` (caso «documentar explícitamente» de ADR-011): `roadmap-dashboard` es dueño de los datos de cartera; `plugin-panel` es dueño de la presentación; `/roadmap-status` es la entrada de cartera y delega en esa presentación.

| Criterio | Valoración |
|---|---|
| Complejidad | Media. 4 de las 7 páginas ya tienen su base en `plugin-panel` (catálogo, diagnóstico, memoria, actividad), igual que el servidor, el token, la CSP, la revisión y los lectores acotados. Lo nuevo es la plantilla multi-página y tres proyecciones (cartera, plan y eventos). |
| Riesgo | Medio. Se rompe el flag `--html` de `build_dashboard.py` y la ruta `docs/roadmap/dashboard.html`: 2 casos de eval, `confluence-pull/SKILL.md`, `commands/roadmap-status.md` y 2 docs README. Mitigación: todos se actualizan en el mismo cambio y `lint_plugin.py` avisa de las citas rotas. |
| Coste relativo | **S** frente a O2 y O3 |
| Reversibilidad | Media. Recuperar `render_html()` del dashboard es un `git revert` acotado: los datos no se tocan y el contrato `--json`/`--md` sigue igual. |

#### O2 — `roadmap-dashboard` absorbe la presentación; `plugin-panel` queda como proveedor del catálogo

`build_dashboard.py` pasa a ser el generador multi-página. Para servir en vivo necesita el servidor, la revisión, la memoria y la actividad, que hoy viven en `plugin-panel`: habría que moverlos (más de 15 aristas de `docs/agents/CONTRACTS.md` E30-E51 nombran rutas de `plugin-panel`) o invertir la dependencia para que el dashboard importe el servidor del panel. `/roadmap-status` abriría el panel completo y `/plugin-catalog` quedaría como alias del catálogo o se retiraría.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: se mueve `serve_panel.py` y sus 7 suites `tests/test_panel_*` cambian de ruta; el nombre «roadmap» no cubre Catálogo, Diagnóstico ni Agentes. |
| Riesgo | Alto: el cierre de seguridad del servidor (token, Host/Origin, nonce) migra de pieza y rompe las referencias de CONTRACTS y de `SKILL.md`; hay riesgo de regresión en CA-34 y CA-43. |
| Coste relativo | **L** |
| Reversibilidad | Baja: deshacerlo es volver a mover el servidor. |

#### O3 — Skill nueva `local-panel`, dueña de la presentación; las dos actuales quedan como proveedoras de datos

Se crea una pieza neutra. `plugin-panel` y `roadmap-dashboard` exponen solo datos, y un comando nuevo (`/panel`) abre el panel.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: es una pieza nueva con doc, evals, interop y fila en ROLES; el servidor se mueve igualmente. |
| Riesgo | Medio-alto: añade una tercera pieza y un comando que se solapa con `/plugin-catalog` y `/roadmap-status`, justo lo que ADR-011 y LES-013 piden evitar. |
| Coste relativo | **L** |
| Reversibilidad | Media. |

### D-A2 — Captura de herramientas para «Agentes en vivo»

Las tres opciones comparten la proyección (§2.3), el almacén (§2.3, `events.json`), la atribución (§2.3) y el resumen redactado (I-07). Lo que cambia es **qué eventos** se registran y **cuándo** corre el hook.

#### O4 — Post-herramienta síncrono

Se registra `agent-activity` en `PostToolUse` (sin matcher, para todas las herramientas) y en `PostToolUseFailure` (solo Claude). Codex usa su `PostToolUse` y OpenCode, `tool.execute.after`, esperando al hijo. Hay un evento por herramienta terminada.

| Criterio | Valoración |
|---|---|
| Complejidad | Baja: se reutiliza el handler y el launcher; solo se amplían `_payload` y el almacén. |
| Riesgo | Alto en latencia: cada herramienta espera a node + Python (dos procesos Python en Windows por `runtime-supervisor.py`) hasta 2.000 ms. Lo pagan **también** los consumidores sin la captura activada. |
| Coste relativo | **S** |
| Reversibilidad | Alta: se quitan los grupos de `hooks.json`. |

#### O5 — Post-herramienta **asíncrono** + atajo del launcher para quien no ha activado la captura

Mismos eventos que O4, pero con `"async": true` en Claude y Codex, y en OpenCode el plugin lanza el hijo **sin esperarlo**: lo registra en `children` para el cierre. En `run-hook.mjs`, para `agent-activity`, Node lee `.claude/dev.json` (≤ 64 KiB, `node:fs`) y **sale antes de lanzar Python** si `sesion.actividad !== true`. El almacén vuelve a comprobarlo (defensa en profundidad, CA-20). La duración sale de `duration_ms` (Claude) y es «sin datos» en Codex y OpenCode. El resultado es `ok`/`error`: en Claude, Post y Failure; en OpenCode, `status`; en Codex, «sin datos» mientras no se valide su `tool_response`.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: hay que cambiar el launcher (huella nueva revisada en `test_graphiti_security.py` y `hook-budget.test.mjs`) y `export-interop.py` (matcher del grupo de actividad). |
| Riesgo | Medio. (a) Un evento puede llegar después del siguiente, por concurrencia de hooks asíncronos (hasta 8 en Codex). (b) Si el bloqueo del almacén está ocupado, el evento se pierde: la captura es informativa y la página lo dice. (c) En `claude -p` los hooks asíncronos pendientes se cancelan al cerrar. |
| Coste relativo | **M** |
| Reversibilidad | Alta: se quita `async` o los grupos; el atajo del launcher es un bloque aislado. |

#### O6 — Pre + Post emparejados por `tool_use_id`

Se registran `PreToolUse` y `PostToolUse`, los dos asíncronos. El par da «herramienta en curso» y una duración calculada en los tres runtimes; en OpenCode el par se hace por `sessionID` + `callID` si V2 lo expone.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: hay estado de pares abiertos, huérfanos (Pre sin Post por denegación o interrupción) y doble validación. |
| Riesgo | Medio-alto: el doble de procesos y de escrituras por herramienta. Además, Codex no garantiza el orden y OpenCode no documenta `callID` en V2, así que el par puede no cerrarse. |
| Coste relativo | **L** |
| Reversibilidad | Alta. |

### 2.3 Subdecisiones comunes a D-A2 (alternativas y descarte)

**Atribución herramienta → run → `T-XX` (sin leer transcripts).**

- **Elegida — ventana declarada del medidor.** Hay que hacer `usage-meter.py start|close --artefacto <slug>/T-XX`, un paso que `/dev-cycle` y `implementer` ya exigen por tarea. El hook lo **reconoce por gramática exacta** en el `tool_input.command` de un evento Bash/shell: regex anclada sobre el argv de `usage-meter.py`, con `-fixN` normalizado a `T-XX`. Abre o cierra una ventana en el ámbito del run (`runtime`, `session`, `agent`).
- Regla de atribución:
  1. Un evento se atribuye a `T-XX` si su run tiene exactamente **una** ventana abierta.
  2. Si su run no tiene ninguna, se mira la sesión padre: con exactamente una ventana abierta, se atribuye. Es el caso de los subagentes, porque el orquestador abre la ventana en la sesión principal antes de despachar.
  3. Cero o más de una ventana → «tarea: sin atribuir».
  4. `<slug>/lote-<n>` nunca atribuye.
- Prueba de no regresión (CA-18): un argumento de texto libre con `T-07` (commit, grep, prompt de Agent) **nunca** atribuye.
- Descartada — enlazar el `description` de la llamada `Agent` con su `agentId`: solo existe en Claude; la propia doc no confirma que `agentId` y `agent_id` coincidan; en primer plano el `agentId` llega al terminar, y la `description` es texto libre (CA-18).
- Descartada — no atribuir nunca: cumple CA-18 de forma trivial, pero vacía el valor de CA-16.
- Descartada — la tarea `en-progreso` única del ledger: es inferencia por proximidad, que CA-18 prohíbe.

**Almacenamiento.**

- **Elegida:** `events.json` en el directorio propio `.claude/agent-activity/`. El inventario pasa de 4 a 5 nombres, más `.lock`. Es un JSON acotado con `runs` (≤ 64), `ventanas` (≤ 64) y `events` (anillo), y se reemplaza de forma atómica con CAS (`StateIO`, `expected=signature`), igual que `snapshot.json`.
- `snapshot.json` y su contrato (60 s, 64 filas, 64 KiB, `api/activity`, `doctor`) **no cambian**.
- Descartado JSONL de solo añadir: líneas parciales al cortarse, validación completa por lectura y rotación con borrado.
- Descartado un fichero por run: número de ficheros sin tope y rompe el inventario cerrado.

**Forma de un evento persistido.** Lleva: `schema_version`, `runtime`, `run_key` (HMAC con `scope_id`, como hoy), `role`, `tool` (≤ 64), `resumen` (I-07), `tarea` (`<slug>/T-XX` o `null`), `duracion_ms` (o `null`), `resultado` (`ok`/`error`/`null`), `observed_at` y `revision`. **Nunca** lleva `tool_response`, contenido de ficheros, salidas, prompts ni rutas absolutas.

### 2.4 Incógnitas técnicas resueltas

**I-01 — Chart.js: versión, licencia y CSP.**

- Versión y origen:
  - Versión: **Chart.js 4.5.1**, la `latest` de npm (publicada el 2025-10-13T08:54:35Z) y marcada «Latest» en GitHub Releases a 2026-10-15.
  - Licencia: MIT («Copyright (c) 2014-2024 Chart.js Contributors», `LICENSE.md` del repo).
  - Fichero: `dist/chart.umd.min.js` (el `unpkg`/`jsdelivr` del paquete), un build UMD clásico que funciona desde `file://`, donde los módulos ES no cargan.
  - Tamaño y hash: 208.522 bytes; SHA-256 publicado por jsDelivr `48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a`. El tarball npm tiene integridad `sha512-GIjfiT9dbmHRiYi6Nl2yFCq7kkwdkp1W/lp2J99rX0yo9tgJGn3lKQATztIjb5tVtevcBtIdICNWqlq5+E8/Pw==`.
  - Se incluye **sin modificar**. El implementer lo extrae del tarball verificando su `sha512` (una sola vez, en desarrollo; nunca en ejecución ni al generar) y debe obtener el mismo SHA-256, que queda en `PROVENANCE.json`.
- Modo servido:
  - `<script nonce="N" src="vendor/chart.umd.min.js">` desde el mismo origen; `serve_panel.py` deja de inyectar el nonce reemplazando el literal `<script>` y lo pone en todas las etiquetas `<script …>` que genera.
  - La CSP queda `script-src 'nonce-N'` (el nonce también autoriza scripts externos), sin `unsafe-eval`.
  - Chart.js 4 dibuja en `<canvas>` y fija estilos por CSSOM, que `style-src` no bloquea.
- Modo exportado:
  - Todos los scripts son ficheros (`assets/*.js` y `vendor/…`); no hay JS inline. Los datos de la página van en `<script type="application/json" id="panel-data">`, que no se ejecuta.
  - La CSP del `<meta>` queda `default-src 'none'; script-src 'self' file:; style-src 'self' 'unsafe-inline'; img-src data:`. **Se elimina el `script-src 'unsafe-inline'` actual** (`panel.html:2`).
  - `file:` se añade porque el origen de `file://` es opaco en Chromium y `'self'` puede no casar.
- Pico (*spike*) de la fase 1 con Playwright en Chromium y Firefox, con la red bloqueada:
  - Criterio: cero eventos `securitypolicyviolation`, en servido y en `file://`.
  - Respaldo si `file:` falla en algún motor: incrustar el texto de Chart.js en cada página con `script-src 'sha256-…'`, el hash del bloque, que es determinista. El fichero sigue en `vendor/` con su `LICENSE` (CA-33, CA-36).

**I-02 — Burndown sin fecha de cierre.**

- Fuente: un campo nuevo **opcional** en la tarea, `- **Cerrada**: AAAA-MM-DD`. Lo escribe quien la marca `completado`, el mismo patrón que `- **Changelog**:` (ADR-012). Lo valida `ledger-lint.py`: solo el formato, y que sea posterior o igual a `creado`. Lo extrae `agent-kits/shared/ledger-view.py` (nuevo).
- Regla de dibujo:
  - Si **todas** las tareas `completado` llevan fecha, se dibuja el burndown.
  - Si no, se muestra «burndown no disponible: N de M tareas completadas sin fecha de cierre», sin gráfico parcial ni interpolado (CA-12, CA-40).
- Los ledgers antiguos muestran el mensaje.
- Descartado `git log -p` de `tasks.md`: exige git en el panel, se rompe con rebase/squash y con `ledger-archive.py`, y es caro.
- Descartado `ultimoCierre` de `.claude/usage-state.json`: es local a una máquina, no versionado, y un *re-close* no equivale a `completado`.

**I-03 — Tope y retención del historial.**

- Topes del anillo: 500 eventos o 256 KiB, lo que llegue antes. Al superarlos se descarta el más antiguo y se guarda `recortado: N` (CA-21).
- Retención: 24 h. Se purga en cada escritura y se filtra al leer.
- Tope de entrada del hook para eventos de herramienta: 2 MiB (hoy es 64 KiB para inicio/fin). Hace falta porque el `tool_response` de un Read puede superar 64 KiB; se parsea en memoria y se descarta. Si la entrada pasa de 2 MiB, se incrementa `descartados_por_tamano` sin identidad.
- Son constantes en `agent-kits/shared/agent-activity.py`, no configurables en esta iteración. Si `sesion.actividad` vuelve a `false` no se escribe nada más; el borrado del directorio lo documenta la guía, ya que el panel no borra.

**I-04 — 64 KiB por respuesta.**

- **Se mantiene** el tope de 64 KiB y se reparten las API en lugar de subirlo.
- Rutas por parámetro de ruta, porque el servidor rechaza `?`:
  - `api/cartera`: Inicio e Iniciativas, ≤ 64 iniciativas, unos 600 B cada una.
  - `api/plan-<id16>`: kanban; por tarea solo ID, título, fase, estado, real/est y nº de gaps.
  - `api/plan-<id16>-<T-XX>`: detalle de una tarea; `Verificación` recortada a `VERIFICACION_MAX` = 2.000 de `ledger-lint.py:65`.
  - `api/actividad-runs` y `api/actividad-run-<key16>`: ≤ 150 últimos eventos del run, con `recortado`.
- `api/progress`, `api/activity`, `api/memory` y `api/review/*` no cambian.
- Las páginas HTML no llevan datos en modo servido. En modo exportado los llevan incrustados, sin tope de respuesta (lo acota la lectura de 256 KiB por ledger).

**I-05 — Coste por evento.**

- Con O5, la latencia síncrona añadida a cada herramienta es **0 ms** en Claude y Codex (`async`) y en OpenCode (no se espera al hijo). Excepción: las herramientas MCP en Codex, que el runtime ejecuta siempre en síncrono.
- Coste en segundo plano: con la captura desactivada, solo el arranque de Node (lectura de `dev.json`); con la captura activa, Node + Python, con el presupuesto existente de 2.000 ms (`run-hook.mjs:26`).
- Se mide en la fase 3 con las líneas `Hooks: PostToolUse:… (Nms)` del log de Claude Code. Si el usuario quiere otra cifra, se ajusta antes de la fase 3.

**I-07 — Resumen del argumento.**

- Formato: **160** puntos de código como máximo, con el precedente de `serve_panel.py:139`. El orden es fijo: redactar, quitar caracteres de control y luego recortar.
- Por herramienta, en lista blanca:

  | Herramienta | Resumen |
  |---|---|
  | Bash, PowerShell, `exec_command` | 1.ª línea del comando |
  | Read, Write, Edit, MultiEdit, NotebookEdit, `apply_patch` | ruta(s) **relativa(s)** al proyecto, o «N ficheros» |
  | Grep, Glob | patrón + ruta relativa |
  | WebFetch | solo el host |
  | WebSearch | consulta redactada |
  | Agent, Task, `spawn_agent` | solo el tipo de subagente |
  | Skill | el nombre |
  | MCP y desconocidas | «—» |

- Después de `redact.redactar`, se aplica `redact.anonimizar(texto, raiz, home, usuario)`, nueva en `redact.py`: raíz del proyecto → `.`, home → `~`, usuario del sistema → `<usuario>` y correos → `<correo>`. Cubre CA-41 para el resumen y para todo HTML o JSON del panel. `redactar` y su copia declarada en `copias.json` no cambian.

**I-08 — Codex.**

- Sí emite `PreToolUse` y `PostToolUse` con `tool_use_id`, pero **sin identificador de subagente** documentado. Sus eventos se agrupan en el run de **sesión**.
- Agentes en vivo lo declara: «Codex no identifica el subagente en eventos de herramienta: se agrupan por sesión».
- Sin duración ni `PostToolUseFailure`: el resultado es «sin datos» hasta que la fase 3 valide un campo de salida de `tool_response` para Bash.
- La herramienta WebSearch no emite eventos.

**I-09 — Qué se publicó en los backends, sin red.**

- Kwipu (`markdown-export`):
  - nº de entradas: `entries` de `<export_dir>/manifest.json` (por defecto `.claude/knowledge-services/kwipu-export/manifest.json`; el manifiesto no trae fecha);
  - fecha: el `completado_en` más reciente de `.claude/knowledge-services/_sync-outbox/<backend>/done/*.manifest.json`; sin él, «sin datos».
- Graphiti:
  - nº de entradas: `entradas` de `.claude/knowledge-services/graphiti-manifest.json`; si existe `graphiti-manifest.pending.json`, se muestra «publicación interrumpida»;
  - fecha: la misma regla de la outbox.
- Nunca se usa el `mtime` como fecha de publicación ni se llama a `health`.
- Enlace a la interfaz: `taxonomy.json` solo declara `health.url`, así que **no hay enlace** salvo que se declare uno (ver §7).

## 3. Criterios de decisión

1. **Un rol, un dueño sin romper contratos intocables**: ADR-011, más `dashboard.md`, `--json` y `doctor --panel-json` iguales byte a byte. Pesa más que el coste, porque es política fija de la spec.
2. **Reutilizar el cierre de seguridad ya revisado** (token, Host/Origin, nonce, lectores acotados, huellas de `test_graphiti_security.py`) antes que moverlo. Cada huella que se toca es una revisión de seguridad.
3. **Cero latencia para quien no activa la captura** y latencia mínima para quien la activa: el registro es opt-in y no puede encarecer las sesiones de todos.
4. **Honestidad del dato**: atribución solo con certeza declarada, ausencias explícitas y nada inferido (CA-18, CA-40).
5. Reversibilidad por fase (4 fases con revisión manual del usuario) y, por último, coste relativo.

## 4. Recomendación · opción elegida y por qué

**Recomendación del arquitecto:** O1 + O5.

**D-A1 = O1 — `plugin-panel` dueño único de la presentación.** Ya contiene el servidor revisado y 4 de las 7 páginas. `roadmap-dashboard` queda como dueño de los datos de cartera (`scan`, `--md`, `--json`, `--metrics-md` intactos) y retira `--html`. `/plugin-catalog` abre el panel (`--export <dir>` | `--serve`, `--page`); `/roadmap-status` mantiene `dashboard.md` y exporta el panel a `docs/roadmap/panel/` aterrizando en Iniciativas. La relación se documenta en ROLES.md.

**D-A2 = O5 — post-herramienta asíncrono.**

- Eventos: `PostToolUse` (+ `PostToolUseFailure` en Claude), `async: true`; OpenCode `execute.after`, sin esperar al hijo.
- Atajo en `run-hook.mjs`: sin `sesion.actividad: true` no se lanza Python.
- Atribución a `T-XX` solo por la ventana declarada `usage-meter.py start|close --artefacto <slug>/T-XX`; ambigüedad → «sin atribuir».
- Almacén `events.json` (500 eventos / 256 KiB / 24 h); resumen ≤ 160 redactado y anonimizado. Codex se agrupa por sesión.

Descartadas:

- O2 y O3: mueven el servidor y su cierre de seguridad, con coste L.
- O4: añade latencia a todas las sesiones.
- O6: dobla el coste y no garantiza los pares.

Decisión propuesta al Curator vía `knowledge-curation.py` (ver §7).

## 5. Impacto en módulos y ficheros

| Módulo / fichero (ruta real) | Cambio | Nuevo / modificado |
|---|---|---|
| `skills/plugin-panel/scripts/build_panel.py` | CLI `--export <dir>` (retira `--html`), `--page`; conserva `--json` (CA-28) y `--serve`; delega en `panel_pages.py` | modificado |
| `skills/plugin-panel/scripts/panel_pages.py` | Plantilla común (menú de 7 entradas, `aria-current`, «Saltar al contenido», cabecera de modo/fecha), render por página; JSON incrustado; escritura con `MARKER` + `export-manifest.json` | nuevo |
| `skills/plugin-panel/scripts/panel_data.py` | Proyecciones de solo lectura: cartera (importa `build_dashboard.py`), plan (`ledger-view.py`), memoria (`knowledge-find`/`knowledge-curation`/`journal`/manifiestos), actividad (`events.json`); ausencias como `null` + etiqueta | nuevo |
| `skills/plugin-panel/scripts/serve_panel.py` | Rutas de página `<token>/<pagina>.html` y `plan-<id16>.html`; activos de lista blanca precargados al arrancar (hash de Chart.js comprobado); nonce en todo `<script …>`; API de I-04 | modificado |
| `skills/plugin-panel/assets/` | `panel.css`, `panel-core.js` (menú, foco, Escape, tabla alternativa, «sin datos»), `panel-charts.js` (adaptador Chart.js + paleta validada), `page-*.js` por página; aquí se mueven `panel-live.js`, `panel-memory.js`, `panel-activity.js`, `panel-review.js` desde `references/` | nuevo / movido |
| `skills/plugin-panel/assets/vendor/chart.js/` | `chart.umd.min.js` 4.5.1 sin modificar + `LICENSE.md` (MIT) + `PROVENANCE.json` (versión, URL del tarball, `sha512` npm, `sha256` del fichero, tamaño, licencia, fecha) | nuevo |
| `skills/plugin-panel/references/panel.html` | Sustituido por la plantilla de `panel_pages.py`; se retira | retirado |
| `skills/plugin-panel/SKILL.md` | Mapa ≤ 200 líneas: 7 páginas, modos, export, descripción absorbe «dashboard del roadmap», «panel del roadmap», «kanban de los planes» | modificado |
| `skills/roadmap-dashboard/scripts/build_dashboard.py` | Extrae `vista_json(inits)` (sin cambio de bytes); retira `--html` y `render_html()` | modificado |
| `skills/roadmap-dashboard/SKILL.md` | Proveedor de datos (MD/JSON/métricas); su `description` deja de prometer HTML y cede esos disparadores | modificado |
| `commands/plugin-catalog.md` | Entrada única del panel: `--export`, `--serve`, `--page` | modificado |
| `commands/roadmap-status.md` | `dashboard.md` + export del panel en `docs/roadmap/panel/` (aterriza en Iniciativas) | modificado |
| `skills/confluence-pull/SKILL.md` | Quita `--html docs/roadmap/dashboard.html` de su regeneración | modificado |
| `agent-kits/shared/ledger-view.py` | Proyección pura de un `tasks.md`: tareas, fase, estado (vocabulario `ledger-lint.ESTADOS`, desconocidos aparte), real/est con procedencia, criterios, `Verificación`, dependencias, `Cerrada`, última revisión y gaps (reusa `ledger-lint.secciones_revision`/`filas_pendientes_de_tarea`; no duplica parsers, ADR-016) | nuevo |
| `agent-kits/shared/ledger-lint.py` | Valida el formato opcional `- **Cerrada**:` | modificado |
| `agent-kits/shared/agent-activity.py` | Constantes del historial (500 / 256 KiB / 24 h / 2 MiB / 160), proyección pura de runs, ventanas y eventos | modificado |
| `agent-kits/shared/agent-activity-store.py` | `_payload` para eventos de herramienta de los 3 runtimes; resumen por lista blanca; ventanas por gramática exacta; `events.json` (inventario 5); lectura `history(project)`; carga `redact.py` | modificado |
| `agent-kits/shared/redact.py` | Nueva `anonimizar(texto, raiz, home, usuario)`; `redactar` sin cambio | modificado |
| `hooks/hooks.json` | Grupos `PostToolUse` (sin matcher) y `PostToolUseFailure` con `agent-activity`, `async: true`, `timeout: 5` | modificado |
| `hooks/run-hook.mjs` | Atajo `agent-activity`: lee `dev.json` con `node:fs` y sale sin Python si no hay opt-in | modificado |
| `hooks/opencode-plugin.js` | Binding de actividad en `execute.after` (herramienta, `status`, `agent`, args → solo para el resumen), sin `await` | modificado |
| `scripts/export-interop.py` | Conserva el matcher del grupo de actividad en `PostToolUse` de Codex; omite `PostToolUseFailure` | modificado |
| `interop/` | Regenerado por `export-interop.py` | modificado (generado) |
| `agents/implementer.md`, `commands/dev-cycle.md` | Escribir `- **Cerrada**:` al marcar `completado` | modificado |
| `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/observability.md`, `docs/en/observability.md`, `docs/INTEROP.md` | Panel multi-página, captura de herramientas y degradación por runtime | modificado |
| `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md` | Filas presentación (`plugin-panel`) / datos (`roadmap-dashboard`) / entrada (`/roadmap-status`); aristas panel→`build_dashboard`, panel→`ledger-view`, hook→`events.json` | modificado |
| `evals/cases/command-roadmap-status.json`, `evals/cases/skill-roadmap-dashboard.json`, `evals/cases/skill-plugin-panel.json`, `evals/cases/command-plugin-catalog.json` | Salida esperada y disparadores tras la absorción | modificado |

### 5.2 Estructura de ficheros del panel (servido = exportado)

```
<export-dir>/  (servido: <token>/…, mismas rutas relativas)
├── index.html            Inicio
├── iniciativas.html      kanban de iniciativas + gráficos de cartera
├── plan-<id16>.html      un Plan por iniciativa con tasks.md (servido: una ruta parametrizada)
├── agentes.html          Agentes en vivo
├── memoria.html
├── catalogo.html
├── diagnostico.html
├── export-manifest.json  (solo exportado) ficheros propios + sha256 + fecha de generación
├── assets/panel.css · panel-core.js · panel-charts.js · panel-live.js · page-*.js · panel-review.js
└── vendor/chart.js/chart.umd.min.js · LICENSE.md · PROVENANCE.json
```

Cada gráfico es un `<figure>` con `<canvas aria-label>` y una `<table>` equivalente accesible por teclado (CA-39). Si falta Chart.js o su hash no coincide, se muestra solo la tabla con un aviso.

### 5.3 Migración de tests

| Suite | Qué cambia |
|---|---|
| `tests/test_plugin_panel.py` | `--html` → `--export <dir>` (l. 247, 364-373); propiedad por `MARKER` **y** por `export-manifest.json`; **golden** de `--json` antes/después (CA-28) sobre un bundle de fixture, no el repo real |
| `tests/test_panel_server.py` | Rutas de página y de activos; exclusión `--serve` + `--export` (l. 232); 403 por token/Host/Origin sin cambio (CA-34); nonce en `<script src>` |
| `tests/test_panel_live_ui.py`, `tests/test_panel_activity_ui.py`, `tests/test_panel_memory_ui.py`, `tests/test_panel_review_ui.py` | El arnés Node lee los JS de `assets/` en vez de extraerlos del HTML inline; IDs DOM por página; sigue prohibido `innerHTML` |
| `tests/test_panel_activity_server.py`, `tests/test_panel_memory_server.py`, `tests/test_panel_review_server.py`, `tests/test_panel_diagnostics.py` | API existentes sin cambio; nuevas rutas I-04 con tope de 64 KiB y `recortado` |
| `tests/test_dashboard.py` | Se retiran las aserciones de `render_html` (l. 378-397, 449-452) y se llevan a las tarjetas de Iniciativas; `--json`/`--md` iguales byte a byte para la fixture |
| `tests/test_agent_activity_store.py`, `tests/test_agent_activity_git.py` | Eventos de herramienta por runtime, ventanas, tope y retención, redacción (corpus de `redact.py`, CA-17), sin escritura con opt-out (CA-20), inventario 5, `.gitignore` |
| `tests/test_graphiti_security.py` | Nueva huella `sha256_lf` de `agent-activity-store.py` y `redact.py` en sus `dependencies` (l. 159-165); nuevo `_LAUNCHER_NODE_HASH` (l. 122) tras revisión; `fs` sigue en la lista de módulos |
| `tests/hook-budget.test.mjs`, `tests/opencode-plugin.test.mjs`, `tests/hook-runtime.test.mjs` | Atajo del launcher; binding de actividad sin `await` |
| `tests/test_export_interop.py` | Matcher del grupo de actividad en Codex; `--check` |

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| `script-src 'self' file:` no autoriza los scripts en algún navegador con `file://` | Media | Alto (CA-33) | Pico (*spike*) Playwright en Chromium y Firefox en la fase 1; respaldo determinista con Chart.js incrustado y `'sha256-…'` (I-01) |
| CA-28 «`--json` igual antes y después» choca con la fase 3, que añade hooks al inventario | Alta | Medio | La golden se fija sobre un bundle de fixture; en la fase 3 se actualiza con un diff limitado a los registros de hook nuevos, revisado |
| La atribución por gramática se lee como «deducir del texto del argumento» (CA-18) | Media | Medio | Se reconoce solo el argv exacto de `usage-meter.py`, un protocolo propio que ya es obligatorio; test negativo con `T-XX` en texto libre; el usuario puede pedir la alternativa «nunca atribuir» |
| Eventos perdidos por bloqueo ocupado o por cancelación de hooks asíncronos (`claude -p`) | Media | Bajo | La página dice «captura informativa: puede tener huecos»; sin reintentos que añadan latencia |
| La huella del launcher y la del almacén cambian: revisión de seguridad obligatoria | Segura | Medio | Cambios acotados a un bloque cada uno; revisión de dos lentes con Lente C; tests de imports Node (`fs` ya admitido) |
| `redact.py` no cubre `Authorization: Basic …` (CA-17 lo nombra) | Media | Alto | Ampliar `_SECRETOS_RE` en el canónico y en su copia declarada (`copias.json`, ADR-016) con caso en el corpus; test CA-17 |
| Payloads de Read/Write grandes superan el tope de entrada | Alta | Bajo | Tope de 2 MiB solo en memoria; por encima, contador `descartados_por_tamano` |
| La ruta `docs/roadmap/dashboard.html` desaparece para quien la usaba | Media | Bajo | `/roadmap-status` avisa una vez de la ruta nueva; nunca borra el `dashboard.html` antiguo (constitución §4) |
| La exportación del panel bajo `docs/roadmap/panel/` mete ruido en git del consumidor | Media | Bajo | El doc recomienda ignorarla; `confluence-publish` solo espeja `.md` |
| El alcance desborda la evaluación (eventos de herramienta + `redact.anonimizar` + `ledger-view.py` + campo `Cerrada`) | Media | Medio | Contrastar con `evaluation.md` al planificar; si desborda, `/dev-cycle` decide re-evaluar |

## 7. Preguntas abiertas

- **Persistencia de la decisión (D-A1).** El encargo pedía escribir el ADR en `docs/knowledge/adr/`. El contrato vigente del rol (`agents/architect.md` P5, `docs/agents/ROLES.md` fila architect: «sin ADR nuevo en legado») exige proponerlo con `knowledge-curation.py propose` como candidato en `candidates/pending/`, y que lo decida `knowledge-curator`. Se ha seguido el contrato vigente: candidato `docs/knowledge/candidates/pending/2026-10-15-plugin-panel-dueno-unico-de-la-presentacion.md` (sha256 `1128a65f…51f9`, `evidencia: observation` hasta que el usuario confirme la opción). El Curator asigna el ID final; se sugiere `custom-agents.ADR-024`.
- **Enlace a la interfaz de Kwipu/Graphiti (CA-26).** ¿Se añade una clave opcional, por ejemplo `ui_url` (solo loopback/privada), a cada backend de `taxonomy.json`? Primero hay que comprobar que el validador de la taxonomía la admite. Sin ella, la página muestra «interfaz: no declarada».
- **Codex `tool_response` de Bash.** La fase 3 debe comprobar si trae un estado de salida documentado; hasta entonces, el resultado en Codex es «sin datos».
- **OpenCode V2 `execute.after`.** La fase 3 debe confirmar en un runtime real que llevan `sessionID` y `agent` (la doc solo muestra `status`/`result`/`error`).
- **I-06** (tiempo de carga y tamaño máximo de la exportación) sigue siendo del usuario. Referencia: unos 210 KB fijos (Chart.js) más las páginas.
- **Nombre del comando.** `/plugin-catalog` queda corto para 7 páginas. Renombrarlo (por ejemplo a `/panel`) es otra decisión, con coste en evals, docs e interop; no entra en esta iteración salvo que el usuario la pida.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-15 | Diseño creado; D-A1 (O1-O3) y D-A2 (O4-O6) con recomendación O1+O5, fijada por instrucción del orquestador sobre la estructura aprobada por el usuario (`aprobado`, revisable) |
