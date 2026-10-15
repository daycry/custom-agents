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
opcion_elegida: "O1+O5+O7"    # D-A1 = O1, D-A2 = O5 (instrucción del orquestador, estructura aprobada por el usuario); I-10 = O7 (adenda 2026-10-15, decisión técnica delegada); revisables por el usuario
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
| **Opción elegida** | D-A1: **O1** — `plugin-panel` dueño único de la presentación · D-A2: **O5** — captura asíncrona post-herramienta con atribución por ventana declarada · Adenda 2026-10-15 (I-10): **O7** — resumen de revisiones de solo lectura en `plan-review.py` (§8) |
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

## 8. Adenda 2026-10-15 — revisión del plan desde el panel (enmienda de la spec)

**Origen:** subsección «Enmienda 2026-10-15» de la spec (`spec.md:337-339`), CA-43 reformulado (`spec.md:232`), CA-45 a CA-54 (`spec.md:239-248`) e incógnita I-10 (`spec.md:380`). El usuario aprobó el **qué**; el **cómo** es una decisión técnica que el orquestador delegó en el architect. Esta adenda no cambia D-A1 (O1) ni D-A2 (O5) y el diseño sigue `aprobado`.

### 8.1 Lo que hay hoy (recon con citas)

| Pieza | Hecho comprobado | Consecuencia para la enmienda |
|---|---|---|
| `plan-review.py` `open` | Valida la iniciativa con `INITIATIVE` (`agent-kits/shared/plan-review.py:43`, `:487`), crea el directorio de estado y `owner.json` con `_marker(..., initialize=True)` (`:185-198`, `:495`), crea `.lock` (`agent-kits/shared/local-state.py:104-112`) y escribe el registro nuevo (`:502-508`, `:562`). Sobre un registro existente no cambia bytes, pero hace `fsync` (`:563`) | `open` **escribe**: solo puede llegar por POST con token |
| `plan-review.py` `status` / `view` | Exigen un `review_id` (`:494`) y toman el cerrojo **exclusivo** (`:496`; `local-state.py:115-133`). No escriben contenido (`:558`), pero el `review_id` depende del `scope_id` del estado (`:171-173`) | No sirven para «todas las iniciativas»: el servidor no conoce los ids, y sondear 64 cerrojos cada 5 s compite con el agente que consume la decisión |
| `plan-review.py` `list_reminders` | Lectura sin efectos: no inicializa, no toma cerrojo, inventario doble para detectar cambios (`:575-635`, en concreto `:596-612`). Va **por iniciativa** y expone `decision_recorded`, pero **no** la elección `approve`/`request_changes` (`:620-627`) | Patrón correcto; contrato insuficiente. Lo usa `/work-resume` (`agent-kits/shared/progress-report.py:501-506`): no se toca |
| Internos `_inventory` / `_record` / `_projection` | `_inventory` y `_record` solo listan, hacen `lstat` y leen y validan (`:211-262`); `_projection` es pura (`:264-276`) | Una operación nueva del dueño puede componerlos sin escribir |
| Servidor del panel | Un único `review_selection` fijado al arrancar (`skills/plugin-panel/scripts/serve_panel.py:471-500`); `refresh` reabre SIEMPRE esa iniciativa (`:293-296`); ids registrados en un `set` con tope 64 (`:319-327`); rutas `api/review/<id64>/<op>` solo con id registrado (`:379-385`); GET `view`/`status` (`:403-405`); POST `comments`/`submit`/`refresh` (`:417`, `:451-456`); id de iniciativa = `sha256(carpeta)[:16]` (`:190`); tope de 64 KiB general (`:19`) y de 512 KiB para revisión (`:23`) | Hace falta un registro `id64 → (iniciativa, puerta, escritura)` y una correspondencia `id16 → iniciativa` |
| CLI | `--review-initiative` y `--review-state-root` se exigen mutuamente (`skills/plugin-panel/scripts/build_panel.py:845-847`, `:860-862`), y un test lo fija: `--serve --project … --review-state-root …` sin iniciativa → exit 2 (`tests/test_panel_review_ui.py:52-57`). `/dev-cycle` lanza `--review-gate-key plan-ok` (`tests/test_plan_review_caller.py:120-121`) | CA-54 prohíbe cambiar esa expectativa: el modo nuevo necesita su propio flag |
| UI | `panel-review.js` toma el id de `data-review-id` (`skills/plugin-panel/assets/panel-review.js:59`), ya pinta resultados y verificaciones por comentario (`:106-148`) con el literal «Sin respuesta declarada» (`:106`); sin revisión seleccionada el JS no se sirve (`skills/plugin-panel/scripts/panel_pages.py:146-147`) | CA-51 ya tiene casi todo el render; cambia el texto y el punto de entrada |

### 8.2 Opciones para I-10 (estado de revisión de todas las iniciativas)

#### O7 — Operación nueva de solo lectura en el dueño: `summarize_reviews` (CLI `summary`)

`plan-review.py` añade `summarize_reviews(project, initiatives, *, state_root, deadline=None)`. Sigue el patrón de `list_reminders`: sin `_marker(initialize=True)`, sin `_locked`, inventario doble y `approval_granted: false`. Recorre el inventario **una vez** para todas las iniciativas pedidas (≤ 64) y devuelve una fila cerrada por iniciativa. El servidor solo llama a la función.

| Complejidad | Riesgo | Coste relativo | Reversibilidad |
|---|---|---|---|
| Media | Bajo (patrón ya revisado en `list_reminders`) | M | Alta (función nueva, nada existente cambia) |

#### O8 — Proyección en el servidor

`serve_panel.py` calcula el estado. Hay tres variantes y ninguna se sostiene: (a) leer `.claude/plan-review/r-*.json` o llamar a `_inventory`/`_record` duplica el parser del formato de estado fuera de su dueño (ADR-011) y acopla el servidor a funciones privadas; (b) llamar a `list_reminders` 64 veces cuesta 128 inventarios y aún no distingue «aprobada» de «cambios pedidos»; (c) llamar a `status` por id necesita ids que el servidor no conoce y toma el cerrojo exclusivo.

| Complejidad | Riesgo | Coste relativo | Reversibilidad |
|---|---|---|---|
| Media | Alto (dos lectores del mismo estado; cerrojo en sondeo) | S-M | Media (el formato de estado queda atado al servidor) |

**Elegida (decisión técnica delegada, 2026-10-15): O7.** Criterios: 1) un rol, un dueño — el estado de revisión solo lo interpreta `plan-review.py`; 2) reutilizar el cierre ya revisado — el patrón sin cerrojo de `list_reminders`; 3) honestidad del dato — el dueño ya sabe qué es «vigente» (versión por hash). **Descartadas:** O8 por los motivos anteriores; ampliar `list_reminders` porque cambia el contrato de `/work-resume` (CA-54).

### 8.3 Contrato de `summarize_reviews` (O7)

- **Entrada:** lista de rutas `docs/roadmap/<carpeta>` (cada una debe casar con `INITIATIVE`, sin repetir, ≤ 64), `state_root` = `<proyecto>/.claude/plan-review` (misma comprobación que `:591-592`) y `deadline` (3 s por defecto).
- **Sin efectos:** no inicializa (sin estado → todas `sin_revision`, `complete: true`), no toma `.lock`, no hace `fsync`, no escribe nada. Test: el árbol de `.claude/plan-review/` tiene los mismos nombres, tamaños y hashes antes y después, y la llamada funciona mientras otro proceso tiene el cerrojo.
- **Registro principal por iniciativa:** el más reciente (`created_at`, desempate por `review_id`) cuya versión es la **vigente**; si ninguno es vigente, el más reciente de todos.
- **Vigencia sin redactar de más:** compara primero el `sha256` crudo del plan (`reader.read_bytes(..., include_digest=True)`); si difiere → `obsoleta`. Solo si coincide calcula `_view` para comparar `view_sha256` (cambio del redactor). Un plan ausente o ilegible da `plan: missing|unavailable`.
- **Estado (vocabulario cerrado):**

  | `estado` | Regla | Texto en la UI (CA-49) |
  |---|---|---|
  | `sin_revision` | La iniciativa no tiene registros | «sin revisión» |
  | `pendiente` | Registro principal vigente sin `decision` | «pendiente» |
  | `cambios_pedidos` | Vigente con `decision.choice = request_changes` | «cambios pedidos» |
  | `aprobada` | Vigente con `decision.choice = approve` | «aprobada vN» |
  | `obsoleta` | Hay registros pero ninguno sobre la versión vigente (CA-50) | «obsoleta por cambio de versión» |
  | `no_disponible` | Plazo agotado o plan ilegible; nunca se rellena con otro estado | «sin datos» + motivo |

- **vN:** ordinal (desde 1) de la versión del registro entre las versiones distintas que tienen registros de esa iniciativa, ordenadas por su primer `created_at`. Lo calcula el dueño; el estado no se borra nunca, así que el ordinal es estable.
- **Campos por fila:** `initiative`, `estado`, `version_ordinal` (o `null`), `gate_key` del principal, `review_state` (`pendiente|entregada|consumida`, o `null`), `plan`, `comments`, `comments_with_result`, `needs_clarification`, `results_without_verification`, `other_current_reviews` y `review_id` (este último **solo para el servidor**; ver 8.4).
- **Sobre:** `schema_version`, `status` (`ok|partial|unavailable`), `reason` (`state_changed`, `deadline_expired`, `state_budget`…), `complete`, `observed_at`, `initiatives`, `omitted` y `approval_granted: false`. Unos 350 B por fila: ≈ 22 KiB con 64 filas, por debajo de 64 KiB.
- **CLI:** `plan-review.py summary --project P --state-root S`, con la lista JSON por stdin (≤ 16 KiB, como `comments`). Exit 0 si `ok|partial`, 3 si `unavailable`.

### 8.4 Servidor: rutas nuevas y su enlace con `api/review/<id64>/<op>`

**Correspondencia `id16 → iniciativa`.** La construye el servidor con el mismo escaneo que da los `plan-<id16>` de la Fase 2 (`sha256(carpeta)[:16]`, `serve_panel.py:190`) y la refresca con la caché de cartera. Quedan fuera: las carpetas que no casan con `INITIATIVE`, las que no tienen `improvement-plan.md` (comprobado con `list_names`, sin leer el fichero) y las que colisionan en el id16 (salen las dos). El navegador nunca envía una ruta ni un nombre de fichero.

**Registro de ids.** El `set` (`:319-327`) pasa a ser un diccionario `id64 → {initiative, gate_key, escritura}` con tope 128 (64 iniciativas × vigente + reapertura). Solo se registra desde respuestas del dueño, nunca desde el cuerpo de una petición.

| Ruta | Método | Qué hace | Escribe en disco |
|---|---|---|---|
| `api/review-summary` | GET | `summarize_reviews` sobre la correspondencia; quita `review_id`; caché de 5 s (como `snapshot`, `:252-263`); recorte por filas si pasa de 64 KiB (como `:200-201`) | No |
| `api/review-current/<id16>` | GET | Pide al dueño el resumen de esa iniciativa y registra el `review_id` principal: `requested-review` → con escritura; `plan-ok` → **solo lectura** (salvo que sea el preseleccionado). Devuelve `{initiative_id, review_id, estado, escritura}`. Con eso el cliente usa `api/review/<id64>/view` (CA-51) | No (el registro es memoria del proceso) |
| `api/review-open/<id16>` | POST | Cuerpo exacto `{"initiative_id": "<id16>"}` igual al de la ruta (mismo patrón que `refresh`, `:76-77`); cualquier otra clave, `gate_key` incluida → 400 sin llamar al dueño (CA-48). Llama a `open_review(project, 'docs/roadmap/<carpeta>', gate_key='requested-review', consumer=None)` y registra el id con escritura | Sí, solo a través del dueño |
| `api/review/<id64>/view·status` | GET | Igual que hoy | No |
| `api/review/<id64>/comments·submit·refresh` | POST | Igual que hoy, pero solo si el registro tiene `escritura`. `refresh` reabre la iniciativa y la puerta **del registro**, no de la selección global (hoy, `:293-296`). Un `plan-ok` en solo lectura → 405 | Sí, solo a través del dueño |

Un id16 que no está en la correspondencia → 404 antes de cargar el dueño; el directorio de estado no cambia (test de CA-45). Token en la ruta, `Host`/`Origin`/`Sec-Fetch-Site`, sin cookies, `Content-Type` JSON, 16 KiB de petición, plazo de 3 s y CSP con nonce: **sin cambios** (`:353-368`, `:411-430`; CA-47). `receive`/`ack`/`consume`/`result`/`verify-result` siguen sin ruta HTTP (contrato E51): las respuestas del agente las escribe el agente, no el navegador.

### 8.5 Flags, modos y la puerta `plan-ok`

| Caso | Comportamiento |
|---|---|
| `--serve --project P --review-state-root S --review-panel` (flag **nuevo**, opt-in) | Habilita el botón «Revisar este plan» en todas las páginas Plan con plan legible, el estado en tarjetas y cabeceras y las respuestas del agente. Carga el dueño y el JS de revisión |
| `--review-initiative X --review-state-root S [--review-gate-key G]` | **Se conserva igual** (CA-43, CA-54): abre X al arrancar con su puerta (incl. `plan-ok` para `/dev-cycle`) y la preselecciona en la página Plan de X con escritura. Combinable con `--review-panel` |
| `--review-state-root` sin `--review-initiative` ni `--review-panel` | Sigue saliendo con exit 2 (`tests/test_panel_review_ui.py:52-57` intacto) |
| Servido sin `--review-panel` (o sin `--project`) | Ni botón ni JS de revisión; la página Plan dice en una frase: «La revisión del plan se activa con `--review-panel --review-state-root <proyecto>/.claude/plan-review`» (CA-53). `test_ordinary_server_never_loads_review_owner` sigue igual |
| `--export` | Sin revisión: ni controles, ni `api/review`, ni lectura de `.claude/plan-review/`. La página Plan dice «estado de revisión: solo en modo servido» (CA-52) |

`create_server` recibe el ámbito nuevo en un argumento propio (`review_scope={'state_root': …}`), **no** ampliando `review_selection`, cuya validación fija un test (`tests/test_panel_review_server.py:172-176`).

**`plan-ok` jamás desde el navegador (CA-48):** la puerta la fija el servidor (`'requested-review'` literal en `api/review-open`) o el orquestador (preselección). Un `plan-ok` abierto por otro proceso se ve, pero sin escritura.

**Descartadas en las subdecisiones:**

- Relajar el parser para que `--review-state-root` solo habilite el modo: cambia la expectativa de `test_panel_review_ui.py:54` (incumple CA-54).
- Reutilizar `api/review/<id>/refresh` con un id16: mezcla dos espacios de id en una ruta que hoy exige id registrado.
- Escribir en el exportado el estado de revisión de la instantánea: obligaría a leer `.claude/` al exportar para un dato que caduca; la spec lo permite («si aparece»), pero no lo exige.

### 8.6 Respuestas del agente en el Plan (CA-51)

- **Origen:** `feedback` y `feedback_history` de la proyección del dueño (`plan-review.py:264-276`, `:378-398`), servidos por `api/review/<id64>/view` con su tope actual de 512 KiB (`serve_panel.py:23`) y el historial acotado a 8 revisiones y 64 KiB (`plan-review.py:395`).
- **Render:** el de `panel-review.js:106-148`, en la página Plan. El literal pasa de «Sin respuesta declarada» a «sin respuesta del agente» (ningún test fija el literal antiguo; comprobado con grep en `tests/`).
- **Resumen de la tarjeta:** solo cifras (`comments_with_result` de `comments`, `needs_clarification`), sin texto de respuestas; así `api/review-summary` queda dentro de 64 KiB.

### 8.7 Impacto adicional en módulos y ficheros

| Módulo / fichero (ruta real) | Cambio | Nuevo / modificado |
|---|---|---|
| `agent-kits/shared/plan-review.py` | `summarize_reviews` + CLI `summary` (8.3); el resto, sin cambios | modificado |
| `agent-kits/shared/test_plan_review_summary.py` | Suite nueva de la operación (sin tocar las suites existentes del dueño) | nuevo |
| `skills/plugin-panel/scripts/serve_panel.py` | `review_scope`, correspondencia `id16`, registro con puerta y escritura, rutas de 8.4, `refresh` por registro | modificado |
| `skills/plugin-panel/scripts/build_panel.py` | Flag `--review-panel` y su validación; cuerpo de la página Plan con botón o explicación | modificado |
| `skills/plugin-panel/scripts/panel_pages.py` | Servir `panel-review.js` también con `review_scope` (`:146-147`) | modificado |
| `skills/plugin-panel/assets/panel-review.js` | Entrada por `data-initiative-id`: `review-current` → `view`; botón → `review-open`; cabecera de estado; texto CA-51 | modificado |
| JS de Iniciativas (`page-*.js` de T-19) | Estado de revisión en texto en cada tarjeta, desde `api/review-summary` | modificado |
| `tests/test_panel_review_panel_server.py`, `tests/test_panel_review_panel_ui.py` | Suites nuevas (las de `tests/test_panel_review_*` existentes no cambian sus expectativas) | nuevo |
| `tests/test_panel_export.py` | Sin controles de revisión ni `api/review` en el exportado | modificado |
| `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/agents/CONTRACTS.md` (E49-E51 y una arista nueva «panel resume revisiones»), `agent-kits/shared/README.md` | Modo `--review-panel`, operación `summary`, rutas nuevas | modificado |

No toca agentes, comandos ni hooks: `export-interop.py --check` no cambia por esta adenda.

### 8.8 Tareas sugeridas para el planner (Fase 2)

El planner las numera como `T-XX` de la Fase 2. Dependen de T-12 (JS a `assets/`), T-19 (Iniciativas) y T-23 (`plan-<id16>`).

| # | Tarea | Ficheros | CA |
|---|---|---|---|
| R-1 | `summarize_reviews` + CLI `summary`. Tests: sin escritura (árbol idéntico), sin estado → `sin_revision`, funciona con el cerrojo tomado, los 6 estados, vN, obsoleta por `raw` y por `view`, plazo → `partial`, `state_changed`, 64 registros | `agent-kits/shared/plan-review.py`, `agent-kits/shared/test_plan_review_summary.py` | CA-49, CA-50, CA-54 |
| R-2 | Servidor: `review_scope`, correspondencia `id16`, registro `id64 → {iniciativa, puerta, escritura}` (tope 128), `api/review-summary`, `api/review-current/<id16>`, `api/review-open/<id16>`, `refresh` por registro. Tests: id16 desconocido → 404 y estado intacto; `gate_key` en el cuerpo → 400; sin token u `Origin` ajeno → 403 y estado intacto; `plan-ok` ajeno sin escritura (405); respuesta ≤ 64 KiB | `skills/plugin-panel/scripts/serve_panel.py`, `tests/test_panel_review_panel_server.py` | CA-43, CA-45, CA-47, CA-48 |
| R-3 | CLI `--review-panel` + texto de activación; exportado sin revisión | `skills/plugin-panel/scripts/build_panel.py`, `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_panel_export.py` | CA-52, CA-53, CA-54 |
| R-4 | UI del Plan: botón, cabecera de estado, comentarios y decisión, respuestas del agente; estado en texto en las tarjetas de Iniciativas (misma cifra). Arnés Node sin `innerHTML` | `skills/plugin-panel/assets/panel-review.js`, JS de Iniciativas, `tests/test_panel_review_panel_ui.py` | CA-45, CA-46, CA-49, CA-50, CA-51 |
| R-5 | Documentación y contratos (dentro de T-28) | `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/agents/CONTRACTS.md`, `agent-kits/shared/README.md` | CA-44 |
| R-6 | Cierre de la Fase 2 (T-29) con **lente C obligatoria**, aunque `review-lens-select.py` no la marque; M-02 incluye abrir, comentar y decidir una revisión desde el Plan | ledger | CA-44, CA-47 |

### 8.9 Riesgos de la adenda

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Vía de escritura nueva desde el navegador (abrir `requested-review`) | Segura | Alto | Id de inventario (nunca ruta), cuerpo exacto, puerta literal en el servidor, token/Origin/CSP actuales, `plan-ok` ajeno en solo lectura; lente C obligatoria (R-6) |
| CA-49 nombra `plan-review.py status`, pero la lectura es `summary` | Segura | Bajo | La propiedad que pide el CA (solo lectura del dueño, sin crear ni modificar ficheros) se cumple; qa debe probar `summary`. Ver 8.10 |
| `summary` lee hasta 64 planes de 256 KiB y redacta los que coinciden en `raw` | Media | Medio | `raw` primero, `_view` solo si coincide; plazo de 3 s → `partial` con `no_disponible`, nunca otro estado; caché de 5 s |
| Lectura sin cerrojo mientras el agente escribe | Media | Bajo | Inventario doble → `state_changed`; la UI dice «actualizando» y reintenta en el siguiente sondeo |
| Se agota el registro de ids | Baja | Bajo | Tope 128 y respuesta explícita «demasiadas revisiones abiertas en este proceso»; test |
| Choque con T-11/T-12 en curso (servidor multi-página y JS a `assets/`) | Media | Medio | R-2 a R-4 van después de T-12 y T-23; no se cambia nada de la Fase 1 |
| El contrato E51 («selección fija») queda desfasado | Segura | Bajo | R-5 lo actualiza en el mismo cambio |
| La opción excede la evaluación (≈ 4 tareas más en la Fase 2) | Media | Medio | `/dev-cycle` decide si re-evaluar la Fase 2 |

### 8.10 Preguntas abiertas de la adenda

- **Literal de CA-49.** Dice «calculado solo leyendo `plan-review.py status`». La adenda usa la operación nueva `summary` (`status` exige id y cerrojo; ver 8.1). Si el orquestador lo pide, el analyst puede ajustar el literal a «una operación de solo lectura de `plan-review.py`». El architect no edita la spec.
- **Persistencia de la decisión.** Candidato propuesto al Curator: `docs/knowledge/candidates/pending/2026-10-15-panel-revision-del-plan-resumen-solo-lectura.md` (sha256 `14ca5630c64003b1763065e0b4f68903bec7c525269fb0d1f0ac9c9884135667`, `evidencia: observation`). Lo decide `knowledge-curator`.
- **Medición.** No hay bloque `generacion:` propio para la adenda: `usage-meter.py close` sobrescribiría la medición original del diseño. Si hace falta, se mide a nivel de la tarea del planner.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-15 | Diseño creado; D-A1 (O1-O3) y D-A2 (O4-O6) con recomendación O1+O5, fijada por instrucción del orquestador sobre la estructura aprobada por el usuario (`aprobado`, revisable) |
| 2026-10-15 | Adenda §8 por la enmienda de la spec (CA-43 reformulado, CA-45 a CA-54, I-10): O7 (operación de solo lectura `summarize_reviews` en `plan-review.py`) elegida por decisión técnica delegada; O8 (proyección en el servidor) descartada; rutas `api/review-summary`, `api/review-current/<id16>` y `api/review-open/<id16>`; flag `--review-panel`; candidato de decisión al Curator. Estado sin cambio (`aprobado`) |
