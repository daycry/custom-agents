# Panel de capacidades del plugin

[English](en/PLUGIN-PANEL.md) · **Español**

El comando `/plugin-catalog` usa plugin-panel para mostrar agentes, skills,
comandos, tools declaradas y hooks globales. La búsqueda y los filtros funcionan
en un panel HTML autónomo de siete páginas. El modo servido añade progreso, consulta local de memoria y señales recientes de actividad opt-in. La
cartera (evaluaciones y presupuestos) se presenta en la página Iniciativas; sus datos los calcula roadmap-dashboard.

Los hooks se agrupan por **runtime y evento**, con una tarjeta por grupo.
`PostToolUse` conserva tres handlers en cada runtime. El contador HTML mide
grupos; el JSON conserva una entrada por handler, `counts.hooks` cuenta acciones
y `hook_group_count` cuenta grupos. `--runtime` selecciona las fuentes de hooks
y extensiones; `all` compara los tres entornos. El filtro HTML de runtime afecta
solo a los hooks, sin ocultar otras capacidades del bundle.

Cada acción tiene ID estable, fuente y localizador, canal nativo, función pública,
activación y comportamiento. Claude lee `hooks/hooks.json`; Codex lee
`interop/codex/hooks.json`. OpenCode lee un JSON estricto acotado entre marcadores
en `hooks/opencode-plugin.js`: ese catálogo gobierna el adapter y no se importa
como código JavaScript. `hook_sources` describe cada fuente como declarada,
ausente o inválida; una fuente fallida no se sustituye por otro runtime.

El catálogo OpenCode conserva seis bindings y ocho acciones. `ActivityObserved`
identifica la captura informativa `agent-activity`, con supervisión declarada de
2500 ms; el lector exige sus eventos terminales y inputs de idle exactos. La fila
es una declaración del adapter, no prueba de opt-in, carga o ejecución efectiva.

El timeout de Claude/Codex tiene unidad segundos y procedencia de registro.
OpenCode muestra milisegundos de supervisión del adapter; su captura por stream
de idle/ejecución no es un hook de teardown nativo. Presupuesto declarado,
ausente e inválido son estados distintos; no se inventa un valor predeterminado.
La guardia identifica sus roles mediante el mapa central del bundle; configuración,
carga y ejecución son evidencias distintas. `load_status` y `execution_status`
permanecen `unknown` en este catálogo estático.

Los nombres y funciones informativas se extraen de las cabeceras públicas
`panel-title` y `panel-description` del handler reconocido. El panel excluye los
comandos completos y no ejecuta scripts, hooks ni diagnósticos. Los enlaces de
acción restauran filtros y foco; Fuentes permanece accesible en móvil.

En un checkout:

```powershell
python skills/plugin-panel/scripts/build_panel.py --export panel
python skills/plugin-panel/scripts/build_panel.py --json
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --export panel
```

`--export <carpeta>` sustituye al antiguo `--html`: escribe siete páginas (`index.html`,
`iniciativas.html`, `plan.html`, `agentes.html`, `memoria.html`, `catalogo.html`,
`diagnostico.html`) con un menú común, `assets/`, `vendor/chart.js/` (con su licencia
y su procedencia) y un `export-manifest.json` con cada fichero propio y su SHA-256.
La carpeta se abre con `file://` y no hace peticiones de red. Solo se sobrescribe un
HTML con la marca del panel o un fichero del manifiesto con el hash que se escribió; un
fichero ajeno con el mismo nombre aborta la exportación con código 2 sin escribir nada.
Rutas del proyecto y del home, nombre de usuario y correos salen como `.`, `~`,
`<usuario>` y `<correo>`. Si Chart.js no coincide con su huella, las páginas muestran
solo las tablas. `--json` no cambia.

En una instalación, localiza la skill en las raíces del runtime. El script
identifica el bundle por su propia ubicación. `--root <bundle>` permite inspeccionar
otro catálogo; no importa código del catálogo inspeccionado. Python nativo funciona
en Windows; no necesita WSL, Tkinter o paquetes Python adicionales. La
exportación autónoma no necesita servidor.

## Panel multi-página: siete páginas, dos modos

Un solo comando (`/plugin-catalog`; `/roadmap-status` lo invoca para la cartera) produce
el mismo panel de siete páginas con un menú común, en dos modos:

| Página | Archivo | Qué muestra |
|---|---|---|
| Inicio | `index.html` | Resumen y, en modo servido, progreso del ledger |
| Iniciativas | `iniciativas.html` | Cartera de `docs/roadmap/` (estado, presupuesto); es la página de aterrizaje de `/roadmap-status` |
| Plan | `plan.html` (índice) y `plan-<id16>.html` | Kanban de tareas por iniciativa, gráficos y burndown; en modo servido, la revisión del plan desde el panel |
| Agentes en vivo | `agentes.html` | Señales recientes de actividad (solo servido; opt-in) |
| Memoria | `memoria.html` | Consulta local de memoria (solo servido; bajo demanda) |
| Catálogo | `catalogo.html` | Agentes, skills, comandos, tools y hooks |
| Diagnóstico | `diagnostico.html` | Informe de doctor importado, con fecha y alcance |

- **Exportado** (`--export <carpeta>`): ficheros estáticos que se abren con `file://`; sin
  servidor ni peticiones de red; las páginas con datos vivos lo dicen en lugar de inventarlos.
  CSP por `<meta>`: `default-src 'none'`, `script-src 'self' file:`, `style-src 'self'
  'unsafe-inline'`, `img-src data:`. La revisión de planes nunca se abre desde aquí.
- **Servido** (`--serve`, solo 127.0.0.1): las mismas páginas más los scripts vivos
  (`panel-live.js`, `panel-memory.js`, `panel-activity.js`, `panel-review.js`). CSP por cabecera
  con nonce y `connect-src 'self'`; sin CDN. Las rutas `api/*` mantienen su forma.

Las gráficas usan **Chart.js 4.5.1 (MIT) vendorizado** en `assets/vendor/chart.js/`, sin
modificar: extraído una sola vez del tarball oficial de npm con su integridad verificada;
`PROVENANCE.json` guarda versión, SHA-256 y licencia, y nada lo descarga al generar ni al
abrir. Si el fichero no coincide con su huella, las páginas muestran solo las tablas.
`roadmap-dashboard` ya no genera HTML: calcula los datos de cartera (`dashboard.md`, `--json`,
`--metrics-md`) y el panel los presenta (relación en `agents/ROLES.md`). La instalación copia
`skills/plugin-panel/assets/` entero, `vendor/` incluido.

## Inicio, Iniciativas y Plan (fase 2 del rediseño)

Las tres páginas leen el roadmap con proyecciones de **solo lectura** y no recalculan
cifras que ya tengan dueño: `roadmap-dashboard` (`scan` + `vista_json`) da la cartera,
`progress-report.py` el «N de M tareas» y `agent-kits/shared/ledger-view.py` lo que dice
el ledger de cada tarea. `skills/plugin-panel/scripts/panel_data.py` solo las proyecta.
Un dato ausente es `null` y se dice («sin datos»); nunca se pinta como 0.

| Página | Qué muestra | API servida |
|---|---|---|
| Inicio | Iniciativas por estado de spec (gráfico + tabla), avance global y coste real frente al estimado | `api/cartera` |
| Iniciativas | Kanban de solo lectura, una columna por estado de spec (`borrador`, `aprobada`, `implementada`, `obsoleta`) y una tarjeta por iniciativa con sus alertas en texto; gráficos de horas y coste con su tabla. La tarjeta con plan es un enlace a `plan-<id16>.html` | `api/cartera` |
| Plan (`plan-<id16>.html`) | Kanban de las tareas del ledger con las cinco columnas del vocabulario (`borrador`, `en-progreso`, `en-revision`, `completado`, `cancelado`) y una franja «Estado no reconocido» con el literal; detalle de tarea; gráficos de avance y horas por fase y burndown | `api/plan-<id16>`, `api/plan-<id16>-<T-XX>` |

- **`api/cartera`**: iniciativas de `docs/roadmap/` (máx. 128 carpetas listadas, 64 filas, respuesta
  ≤ 64 KiB). Cada iniciativa cae en UNA categoría de spec: los cuatro estados, `ilegible`,
  `sin_spec` (vía rápida) o `no_reconocido` (con su literal). El coste estimado se muestra
  como lo escribe `evaluation.md`; solo el primer importe en euros se extrae para sumar.
- **Plan por id16**: `<id16>` son 16 hex del inventario de planes que el servidor publica;
  el navegador nunca envía una ruta. Una tarea trae horas IA reales y estimadas con su procedencia
  (`medido`/`estimado`), supervisión y humanas, criterios con su casilla, la `Verificación` y su
  salida, dependencias, la última revisión con sus gaps abiertos y la marca «archivado»
  (solo el enlace a `execution-history.md`; su contenido no se lee). El detalle se abre
  con clic o Enter, se anuncia en una región `aria-live` y Escape lo cierra devolviendo el foco.
- **Gráficos**: avance por fase = completadas/total como las cuenta el ledger; horas por fase =
  suma de lo presente, «sin datos» si ninguna tarea trae el dato, con «(medido)», «(estimado)»
  o «(medido y estimado)». El **burndown** parte de las tareas no canceladas menos las cerradas
  hasta cada fecha, con solo las fechas de cierre reales; sin ninguna completada dice
  «Sin datos: ninguna tarea completada todavía».
- **Actualización viva** (servido): el Plan se relee cada cinco segundos con las reglas del
  sondeo de Progreso (una petición activa, pausa con la pestaña oculta, plazo de cuatro segundos);
  las tarjetas con la misma fila conservan su nodo y el foco. La fecha de lectura va en una
  región no viva para no anunciar cada ciclo. Un fallo conserva la vista con aviso.
- **Exportado**: lo mismo desde el JSON incrustado en `panel-data` (claves `plan` y `detalles`),
  sin peticiones; los datos vivos se declaran ausentes.

### Campo `Cerrada` del ledger

`- **Cerrada**: AAAA-MM-DD` es un campo opcional de cada tarea: la fecha real de cierre. Lo
rellena el implementer al completar la tarea; `ledger-lint.py` exige fecha real (vacío, mal
formada o imposible → incoherencia) y no anterior a `creado:` ni a la fila `| **Fecha** |`.
`ledger-view.py` publica `cerrada` (válida) y `cerrada_invalida` (el texto), y el burndown
solo usa la primera. `task-brief.py` no lo pasa al subagente. Como `Changelog`, es
metadato del ledger, no criterio de aceptación.

### `ledger-view.py`

```powershell
python agent-kits/shared/ledger-view.py docs/roadmap/<fecha>-<slug> --json
```

Proyección pura de un `tasks.md` (carpeta o fichero): fases, tareas, estado (del vocabulario o
`literal` si no casa), horas, criterios, descripción, verificación, dependencias, `archivado`,
`cerrada`, `revision` y `gaps`. No valida (es de `ledger-lint.py`), no resume (es de
`progress-report.py`) y reutiliza sus parsers. `status`: `ok`, `fuera_de_tope` (> 256 KiB, sin
cifras), `ilegible`, `sin_ledger`, `sin_tareas` o `sin_lectura`. Exit 0 con ruta utilizable, 2 por uso incorrecto.

## Dashboard local con actualización

```powershell
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --serve
```

Abre la URL de acceso que entrega el proceso y detén el servidor con Ctrl+C
o su handle de lanzamiento. La URL contiene una capacidad privada: no la
publiques ni la guardes en Git, documentación, memoria o registros. Cada
arranque crea otra. Solo escucha en 127.0.0.1; puerto libre automático o
`--port 8765`. No sirve archivos arbitrarios del proyecto.

Requiere proyecto y excluye HTML/JSON y raíces personales. Las declaraciones
de proyecto se leen para la instantánea inicial. Catálogo y diagnóstico quedan
fijados al arranque; Progreso relee ledgers cada cinco segundos, con botón de
actualización, búsqueda y filtro de estado. Las respuestas comparten una lectura
durante dos segundos. La pestaña oculta suspende peticiones; cada consulta vence
a los cuatro segundos. Un fallo conserva la vista y su fecha anterior con aviso.

El parser canónico calcula conteos y fase desde `tasks.md`. Fecha de lectura y
SHA-256 identifican texto UTF-8 sin BOM, incluyendo saltos de línea; no autentican
al autor ni demuestran ejecución de agentes. La actualización de Progreso no consulta journal, usage-meter, memoria o
backends, ni escribe estados. Memoria se consulta solo por una acción explícita.

La lectura rechaza redirecciones y cambios durante el acceso. Límites: 128
entradas, 256 KiB por ledger, 1 MiB acumulado, 64 iniciativas, ocho tareas visibles
por iniciativa y 64 KiB JSON. Lectura incompleta, ledger ilegible, estado
desconocido o recorte se indican como parciales. Texto redactado y acotado;
sin cuerpos, verificaciones libres o rutas absolutas.

Página/API requieren capacidad y Host exacto; Origin, si aparece, debe ser el
propio. Rechaza cross-site, query y rutas libres; admite POST solo para la
consulta local de memoria y la revisión de planes (la fija de `--review-initiative` o la de
`--review-panel`). Es la única excepción a la solo lectura: la revisión sólo escribe sus
propios recibos y comentarios locales; el navegador nunca abre la puerta `plan-ok`. Sin cookies
ni logs de acceso; CSP con nonce, conexión al mismo origen, no-store, no-referrer
y marcos prohibidos. La capacidad no aísla frente a procesos del mismo usuario.
Consumir una decisión de plan requiere el CLI común y el workflow autorizado.
Publicar/reconstruir memoria conserva sus consumidores y pruebas.

## Señales recientes de actividad

En el modo `--serve`, Actividad está separada de Progreso. Su lectura no inicia
agentes ni convierte estados del ledger en presencia real. El productor común
`agent-kits/shared/agent-activity-store.py` sólo persiste metadatos cerrados; el
lector usa su `snapshot(project)` y la proyección pura `agent-activity.py`.

La captura requiere el opt-in booleano `sesion.actividad: true` en el
`.claude/dev.json` del proyecto. Ausencia o `false` la desactiva. Para activarla
manualmente, combina esta clave con la configuración existente, sin sustituirla:

```json
{"sesion": {"actividad": true}}
```

Abrir el panel o ejecutar setup no crea ni activa esa configuración. El productor
es dueño de `.claude/agent-activity/` y crea primero su `.gitignore` con `*` y salto
de línea para excluir los archivos nuevos de ese estado local de Git. El lector
no crea, bloquea, purga, migra ni recupera estado; un directorio ajeno, parcial o
inválido queda indisponible, sin adoptarlo. La regla de ignore no retira archivos
ya rastreados de Git.

Hay hasta 64 observaciones. El snapshot JSON y la respuesta HTTP tienen cada
uno un límite de 64 KiB. `complete` describe la validación de ese snapshot;
`collection_complete: false` permanece visible: no representa todas las sesiones
o agentes. Las tarjetas muestran runtime/rol declarados, fuente, estado y fecha;
las claves seudónimas quedan internas. No se conservan prompts, transcripciones,
argumentos de herramientas ni rutas crudas del consumidor en este estado.

| Estado | Qué describe |
|---|---|
| `recent_start` | Señal reciente de inicio |
| `recent_response_end` | Fin reciente de una respuesta |
| `recent_execution_end` | Fin reciente de una ejecución |
| `recent_idle` | Señal reciente de inactividad de sesión |
| `unknown` | Señal caducada, reloj futuro o frescura desconocida |

Una señal no demuestra un proceso vivo, destrucción de agente, identidad
autenticada ni cobertura completa. La frescura caduca a los 60 segundos. La UI
acumula edad monotónica desde la recepción y la compara con la edad anunciada;
refrescar el mismo evento/revisión no la rejuvenece. Un fallo HTTP conserva vista
y fecha, pero las señales siguen caducando. Una fecha futura queda desconocida.

`GET api/activity` usa la misma capacidad y guardias Host/Origin del servidor;
es sólo lectura, con respuesta acotada y sin ruta libre. POST conserva el rechazo
405 existente. Hay una petición activa, timeout de cuatro segundos y polling
cada cinco segundos después de resolverla. Ocultar la pestaña aborta y pausa;
al volver, la vista aplica caducidad antes de consultar. El HTML estático explica
que no hay servicio de señales. Si falta el JS de actividad, sólo esa sección
queda indisponible; las otras vistas conservan su comportamiento.

El export «solo skills» necesita referencias explícitas a
`agent-kits/shared/agent-activity-store.py`, `agent-kits/shared/agent-activity.py`,
`agent-kits/shared/local-state.py` y `agent-kits/shared/local-read.py` en la skill.
El productor `capture` también lee el mapa central
`agent-kits/shared/native-roles.json`: se declara explícitamente para que el
paquete incluya el JSON, aunque la lectura `snapshot` no lo usa.
Ese paquete no registra hooks nativos; incluir helpers y mapa no demuestra captura.
La proyección/HTTP/DOM tienen pruebas focales; interacción real de navegador,
carga de hooks y aceptación nativa requieren su propia evidencia.

Referencias oficiales consultadas el **2026-10-10**:

- [Claude Code: SubagentStart/SubagentStop](https://code.claude.com/docs/en/hooks): señales de subagente; el fin de respuesta no acredita destrucción.
- [Codex: hooks](https://developers.openai.com/codex/hooks/): eventos y payload nativo de subagentes; la documentación no acredita su carga en esta sesión.
- [OpenCode V2.0.12: cierre de ejecución](https://github.com/anomalyco/opencode/blob/2670273ff17da96f85c5826ced57aa1b368754fa/packages/core/src/session/execution.ts#L118-L150): emite un terminal `session.execution.succeeded/failed/interrupted`; su [proyector](https://github.com/anomalyco/opencode/blob/2670273ff17da96f85c5826ced57aa1b368754fa/packages/core/src/session/projector.ts#L403-L434) deriva idle/outcome desde ese evento.
  La captura conserva `execution_finished`, sin convertirlo en una observación independiente `session_idle` ni en teardown. `session.idle`/`session.status` siguen como inputs de compatibilidad, sin afirmar emisión por esta versión.
  La aceptación nativa requiere su propia evidencia y correlación exacta; la lectura del contrato no acredita captura completa.

## Revisar planes desde el panel (`--review-panel`)

Además de la revisión de una iniciativa fija (sección siguiente), el panel servido puede abrir
la revisión del plan de **cualquier** iniciativa desde su página Plan:

```powershell
python skills/plugin-panel/scripts/build_panel.py --serve --project . --review-panel --review-state-root ./.claude/plan-review
```

`--review-panel` exige `--serve`, `--project` explícito y `--review-state-root`; se combina con
`--review-initiative` (que conserva su pantalla heredada). Sin `--review-panel`, la página Plan
no muestra botón y explica en una frase cómo activarlo; el HTML exportado nunca lleva controles
de revisión ni `fetch` de escritura.

| Ruta | Método | Qué hace |
|---|---|---|
| `api/review-summary` | GET | Estado de revisión de todas las iniciativas (operación `plan-review.py summary`), por `initiative_id` id16, sin rutas ni `review_id`; caché de 5 s |
| `api/review-current/<id16>` | GET | Registra para el navegador la revisión principal de UNA iniciativa; responde `review_id`, `estado`, `version_ordinal`, `gate_key` y `escritura` |
| `api/review-open/<id16>` | POST | Abre la revisión con la puerta `requested-review`; responde compacto (`review_id`, `escritura`); la vista llega por `api/review/<id64>/view` |

Los id16 salen de listar `docs/roadmap` (carpeta válida con `improvement-plan.md`; una colisión
deja la iniciativa fuera). Un id16 desconocido da 404 antes de leer el cuerpo; el navegador nunca
envía una ruta ni un nombre de fichero. Un proceso registra como máximo 128 revisiones: el
exceso responde 429 con «demasiadas revisiones abiertas en este proceso». Una revisión con otra
puerta (p. ej. `plan-ok` abierta por `/dev-cycle`) se muestra con `escritura: false`.

**`plan-review.py summary`** (solo lectura: sin cerrojo, sin fsync, sin escrituras). Recibe por stdin
una lista de iniciativas y devuelve, por cada una, `estado` (`sin_revision`, `pendiente`,
`cambios_pedidos`, `aprobada`, `obsoleta` o `no_disponible`), `version_ordinal`, `gate_key` y los
contadores de comentarios, con respuesta, que piden aclaración y respuestas sin verificar. Una
revisión cuya versión ya no coincide con el plan es `obsoleta`; la decisión anterior no cuenta
como vigente. Doble inventario con rechazo de cambios observados (no es una instantánea atómica
ni permiso para continuar una puerta); `approval_granted` es siempre `false`. Sin carpeta de
estado todas salen `sin_revision`. Exit 0 con `ok`/`partial`, 3 si no está disponible; un plazo
agotado a mitad deja el resto en `no_disponible`.

La UI de la página Plan muestra el botón «Revisar este plan» y el estado en texto («sin revisión ·
pendiente · cambios pedidos · aprobada vN · obsoleta por cambio de versión») en la tarjeta de
Iniciativas y en la cabecera del Plan, con el mismo texto; permite comentar por sección y decidir
(aprobar o pedir cambios); y muestra bajo cada comentario la respuesta del agente y su disposición,
o «sin respuesta del agente».

**Excepción de escritura.** El panel es de solo lectura, con una excepción acotada: `api/review-open`
(y los POST de comentarios/decisión ya existentes) escriben solo los recibos y comentarios de
`.claude/plan-review/`, con las mismas protecciones (capacidad, Host/Origin, sin cookies, CSP con
nonce). **El navegador nunca abre `plan-ok`**: esa puerta la abre `/dev-cycle`; aprobar aquí
con `requested-review` no autoriza ese gate. Tampoco hay receive/ack/consume/result por HTTP, y
el panel no modifica `improvement-plan.md` ni `tasks.md`.

## Revisar un plan en la puerta existente

La revisión visual es opcional. Sustituye el «OK del plan» pendiente de `/dev-cycle`
cuando se pide expresamente. Un OK conversacional suficiente permite continuar sin
abrir este canal ni confirmar otra vez.

El caller de [`/dev-cycle`](../commands/dev-cycle.md) incluye recetas Bash y
PowerShell. Usa un Python real y dueño/validador/builder del mismo bundle; varias copias
completas sin procedencia activa son ambiguas. Valida `open` antes de iniciar
el servidor con handle separado, y valida ack antes de releer la vista vigente.
Estas recetas no acreditan por sí solas carga del comando por un cliente nativo
ni interacción real del navegador.

```powershell
python skills/plugin-panel/scripts/build_panel.py --serve --project . --review-initiative docs/roadmap/<fecha>-<slug> --review-state-root ./.claude/plan-review --review-gate-key plan-ok
```

Selecciona la ruta exacta de la iniciativa; sólo se revisa `improvement-plan.md`.
`--review-initiative` y `--review-state-root` van juntos. El builder usa
`requested-review` por defecto; `/dev-cycle` debe seleccionar `plan-ok`.
Una decisión de revisión general no autoriza esa puerta. El modo servido excluye
`--export`, `--json`, `--home` y `--user-root`. El HTML autónomo no abre revisión ni escribe estado.

El workflow ejecuta primero `plan-review.py open` para obtener el ID y la versión,
con `gate-key: plan-ok` y su runtime actual. Después abre el servidor, que recupera
el mismo recibo. Conserva el handle y la URL privada; el usuario puede decidir
mientras el consumidor espera sin confundir `waiting` con aprobación.

La vista presenta todo el Markdown como texto, dividido por secciones e identificado
por SHA de bytes originales y SHA de vista. Los títulos repetidos tienen IDs distintos.
Secretos redactados y controles saneados se indican en pantalla. Aprobar la vista
no aprueba los valores ocultos. Texto, enlaces, imágenes y HTML no ejecutan instrucciones
ni cargan recursos externos. Un plan ilegible, vacío, parcial o fuera de límites
deshabilita la decisión; nunca se aprueba un prefijo recortado.

| Acción | Resultado |
|---|---|
| Guardar comentarios | Guarda el borrador redactado por sección antes de decidir |
| Aprobar la vista | Fija `approve` para esa versión; admite cero comentarios |
| Pedir cambios | Fija `request_changes`; exige al menos un comentario no vacío |
| Cargar versión actual | Abre explícitamente la versión actual; no transfiere comentarios |
| Cerrar sin decidir | Cierra la interfaz y conserva borrador/recibo; no crea decisión |
| Volver a la revisión | Recupera la interfaz sin registrar otra decisión |

El workflow usa `plan-review.py consume` con proyecto, state-root, iniciativa,
review_id, puerta y la tupla raw/view. El dueño valida selección/vista antes de
entregar, confirma los IDs reales y relee la versión antes de devolver `consumida`.
No lanza roles ni acredita efectos. `waiting` conserva la ausencia de decisión;
una versión obsoleta no se consume. Un ack fallido conserva la entrega para retry;
un cambio posterior al ack devuelve `version_changed` con el consumo histórico.
El plazo común de tres segundos cubre toda la operación. La vista final no es una
transacción con trabajo posterior ni garantiza detectar ABA.

Una revisión obsoleta conserva la decisión histórica, pero no aprueba el plan
actual. `receive` devuelve `version_changed` y código 2 sin consumirla. Una nueva
revisión se abre con `open` para la versión actual y requiere su propia decisión;
no se actualizan los hashes del recibo antiguo. El consumo válido sigue
`receive → validación → ack → validación → view`, antes de actuar. La autorización
conversacional suficiente sigue su vía existente.

La decisión pasa por `pendiente` → `entregada` → `consumida` bajo el dueño común
`agent-kits/shared/plan-review.py`. Enviar una decisión la mantiene pendiente;
`receive` la entrega y `ack` confirma consumo durable. El panel no inicia agentes,
modifica plan/tasks ni hace receive/ack por HTTP. La inscripción de un consumidor
es histórica: muestra «sin consumidor registrado» o «actividad desconocida».

GET de vista/estado y POST de comentarios/submit/refresh sólo aceptan IDs registrados
por esta instancia. No aceptan raíces, paths, artefactos o comandos libres.
El estado `.claude/plan-review/` pertenece al proyecto y es compartido por los tres
runtimes; no es configuración exclusiva de Claude. Exclúyelo de Git; el dueño no
adopta un directorio ajeno ni elimina decisiones para liberar espacio.

Límites: plan 256 KiB, 128 secciones, 64 recibos, solicitudes 16 KiB y respuesta
JSON 512 KiB. Hasta 20 comentarios, 2.000 caracteres cada uno y 10 KiB UTF-8
acumulados; el exceso se rechaza sin truncar. El plazo acumulado es tres segundos;
lock presupuestado hasta 100 ms. El polling de estado cada cinco segundos admite
una petición activa y se detiene al ocultar/cerrar; aborta la petición a los cuatro segundos.
Los límites propios de Memoria y Progreso permanecen separados.

Cambiar bytes o transformador produce `version_changed`; el recibo anterior se
conserva y los botones quedan deshabilitados hasta la selección explícita vigente.
El workflow valida puerta, versión y decisión, hace ack y relee antes de trabajar.
Un recibo consumido vigente permite retoma sin nueva confirmación. La entrega puede
repetirse; el consumo del recibo es idempotente, los efectos externos no lo son por contrato.
En la retoma, el workflow consulta ledger/plan vigentes: ack no prueba trabajo terminado
tras un crash. Retoma lo pendiente y evita relanzar planner si ya atendió los cambios.
Un recibo obsoleto conserva evidencia histórica, sin repetir su decisión sobre otro plan.
Los hashes/capacidad no autentican a una persona. Relecturas y locks no ofrecen
atomicidad con el workflow, detección ABA ni garantías universales ante pérdida de energía.
El fallback usa la autorización conversacional existente, sin inventar aprobación.

El bundle común necesita `plan-review.py`, `local-state.py`, `local-read.py` y `redact.py`.
La revisión en «solo skills» requiere que el export incluya esas cuatro dependencias
declaradas desde plugin-panel. La comprobación del paquete pertenece a QA;
sin cualquiera de ellas, el canal queda indisponible.
El [comando](../commands/dev-cycle.md) describe receive/ack y la vuelta autorizada al planner.

### Ver qué ocurrió con los comentarios

«Consumo confirmado» significa ack; no significa que se atendió el comentario.
Resultados muestra la respuesta declarada: `addressed` (atención declarada),
`not_applied` (no aplicado con motivo) o `needs_clarification` (aclaración necesaria).
La verificación `confirmed`/`not_confirmed` muestra una observación humana ya
comunicada. No autentica a esa persona ni concede aprobación, QA o permiso nuevo.
Sin respuesta o verificación, el panel indica su ausencia. No abre un chat ni
solicita otra confirmación para continuar trabajo autorizado.

El consumidor registra la respuesta por CLI tras ack de esa decisión; el navegador
lee resultados/historial y no envía result/verify-result/receive/ack por HTTP.
También puede responder comentarios de approve; sin comentarios no crea filas.
La nota se muestra como texto inerte. Al editar el plan, la respuesta sigue ligada
a la revisión consumida antigua; la nueva vista no hereda atención ni aprobación.
Historial de respuestas distingue versiones y mantiene resultados reemplazados.
Polling conserva borradores/foco; un fallo conserva la fecha anterior con aviso.

### Registrar una respuesta desde el workflow

Reutiliza las variables del caller de `/dev-cycle` y el dueño del mismo bundle.
Conserva review_id, version, gate_key, decision_id y delivery_id de la decisión
consumida; CommentId procede de decision.comments. ReviewRevision es el entero
`review.revision` leído de ese registro antes de una operación nueva. Una vista
histórica version_changed/unavailable puede aportar ese registro; nunca autoriza
trabajo sobre el plan nuevo. Genera ResultId una sola vez (64 hex minúsculas) y
conserva ID y payload si pierdes la respuesta. ReviewRuntime es el runtime actual.

```powershell
$OutputEncoding = [Text.UTF8Encoding]::new($false)
$ResultRequest = @{
  version = @{raw_sha256=$RawSha256; view_sha256=$ViewSha256; view_version='plan-text-v1'}
  gate_key = 'plan-ok'; decision_id = $DecisionId; delivery_id = $DeliveryId
  comment_id = $CommentId; result_id = $ResultId; expected_revision = $ReviewRevision
  disposition = 'addressed'; response_text = 'Separé consumo y atención del comentario.'
  supersedes_result_id = $null
  producer = @{caller_id='dev-cycle'; runtime=$ReviewRuntime; actor_id=$null}
}
$ResultRequest | ConvertTo-Json -Depth 4 -Compress | & $ReviewPython @ReviewPythonArgs $PlanReview result @ReviewScope --review-id $ReviewId --json
```

En Bash, selecciona un JSON UTF-8 con esas mismas once claves; RESULT_REQUEST
representa su ruta elegida. La nota se pasa como dato, nunca se evalúa como shell.

```bash
"$REVIEW_PYTHON" "${REVIEW_PYTHON_ARGS[@]}" "$PLANREVIEW" result "${REVIEW_SCOPE[@]}" --review-id "$REVIEW_ID" --json < "$RESULT_REQUEST"
```

`producer` contiene exactamente caller_id (1–128 letras ASCII/dígitos/_/-),
runtime (`claude-code|codex|opencode`) y actor_id (null o 64 hex minúsculas opacos).
No envíes identity_basis, nombres humanos, fechas, flags, section_id u observaciones
de artefacto: los calcula el dueño. No se exige coincidir con el primer consumidor.

Para una observación humana explícita ya recibida, conserva sus vínculos y añade
un VerificationId nuevo elegido una vez. Relee ReviewRevision para esa operación.
No generes una verificación automáticamente desde los cambios o pruebas.

```powershell
$VerifyRequest = @{
  version=$ResultRequest.version; gate_key=$ResultRequest.gate_key
  decision_id=$DecisionId; delivery_id=$DeliveryId; comment_id=$CommentId
  result_id=$ResultId; verification_id=$VerificationId; expected_revision=$ReviewRevision
  assessment='confirmed'; note='Observación humana ya comunicada sobre esta respuesta.'
  producer=@{caller_id='dev-cycle'; runtime=$ReviewRuntime; actor_id=$null}
}
$VerifyRequest | ConvertTo-Json -Depth 4 -Compress | & $ReviewPython @ReviewPythonArgs $PlanReview verify-result @ReviewScope --review-id $ReviewId --json
```

Las once claves de verify-result sustituyen disposition/response_text/supersedes_result_id
por verification_id/assessment/note. Assessment también admite not_confirmed; note
puede estar vacía. En Bash usa el mismo CLI verify-result y su JSON por stdin.
La anotación es opcional; no constituye otra puerta ni requisito de entrega.

Exit 0/status ok confirma persistencia de feedback: review null, approval_granted
false y feedback_receipt con operación/IDs/versión vinculados. No lo pases al
validador de open ni lo uses como autorización. Exit 2 indica conflicto y exit3
indisponibilidad. Retry con los mismos IDs y contenido conserva fecha/observación,
aunque la revisión actual del registro haya avanzado. revision_conflict exige
releer/reconciliar; operation_conflict no permite sobrescribir. Una corrección
usa otro result_id y supersedes_result_id del último resultado (máximo dos por
comentario). Cada resultado admite una verificación; una sustituida sigue histórica.

El campo `feedback_receipt.revision` refleja la revisión actual del registro al
responder. Un reintento posterior a otra operación puede devolver un número
mayor que el primer recibo; los IDs, `recorded_at` y la fila persistida se conservan.


Solicitud 16 KiB; respuesta no vacía hasta 1000 caracteres/2048 bytes UTF-8; nota
hasta 500/1024. Exceso y presupuestos de filas/registro se rechazan sin recorte.
Historial contiene hasta 8 revisiones/64 KiB, sólo filas completas del mismo scope,
iniciativa y puerta. Incompleto no significa vacío. Un bundle antiguo sin extensión
muestra resultados no disponibles; una extensión inválida no se trata como ausencia.
El dueño nuevo lee record schemas 1/2 sin migrar por consultar; la primera mutación
válida de feedback puede actualizar legacy a 2. Usa dueño/server/UI del mismo bundle;
no se promete escritura simultánea de binarios antiguos y nuevos. El envelope sigue 1.
Estas instrucciones no acreditan interacción V01–V08 ni aceptación nativa.

## Consulta local de memoria

Consultar conserva la autoridad de cada entrada: una propuesta o una entrada
heredada no equivale a un aprobado. El [contrato de recuperación local](roadmap/2026-10-07-catalog-capabilities/comparisons/memory-local-recovery-contract.md)
separa la conservación de sesiones y la restauración de las pruebas de consulta.

En modo servido, Memoria permite Buscar, Ver entrada y Relaciones. Cada acción
usa `knowledge-view.py`; abrir el panel o actualizar Progreso no dispara búsquedas.
Las tarjetas conservan ID completo, tipo, estado, versión, evidencia y ruta.
Propuestas y entradas obsoletas conservan su estado. El cuerpo solo se entrega
al pedir Ver; una colisión no selecciona una entrada automáticamente.

La lectura comparte parsers, ranking, relaciones y validación de aprobados con
`knowledge-find.py`. Límites acumulados: 256 entradas de directorio, 128 archivos,
256 KiB por archivo, 2 MiB de lectura y profundidad ocho. Consulta de hasta
1.000 caracteres, ID de hasta 256, 20 resultados/relaciones, cuerpo hasta 12.000
caracteres y respuesta JSON de 64 KiB. Recorte, corpus inválido o lectura
incompleta son parciales; ausencia, ambigüedad y fallo tienen estados explícitos.
El redactor se aplica antes del recorte; ruta/hash no prueban aprobación.

Las versiones mayores que el entero seguro de JavaScript se muestran como
decimal exacto, hasta 4.300 dígitos. Versiones inválidas se declaran desconocidas
con parcialidad. Además de entradas, se acotan 256 llamadas de listado; `scans`
contabiliza ese trabajo incluso si las carpetas están vacías. El byte de sonda
del lector se reserva dentro del acumulado de lectura.

El servidor admite solo JSON UTF-8 en la ruta fija privada `api/memory`, con
solicitud máxima de 4 KiB y plazo acumulado de cuerpo de tres segundos. Rechaza
claves duplicadas, selectores desconocidos y otros métodos. La UI omite cookies,
limita cada consulta a seis segundos y no solapa solicitudes. Ante fallo conserva
la vista/fecha previa con aviso; los resultados, cuerpos y relaciones tienen
frescura propia. No carga adaptadores, candidatos, journal ni cachés o índices.
El HTML autónomo conserva inventario y no incorpora estas consultas.

Desde CLI: `knowledge-find.py --root <proyecto> --view <consulta>`,
`--view --show <ID>` o `--view --related <ID>`. La salida usa versión 1 y fuente
`canonical_knowledge`. La consulta CLI ordinaria también lee el snapshot acotado
y declara `corpus_read`; un corpus parcial no se guarda como índice completo.

## Extensiones en exportación autónoma

Para incluir piezas propias, usa `--project <raíz>` y el runtime real en
`--runtime claude-code|codex|opencode`. `--cwd <paquete>` inspecciona skills de
su cadena de directorios. Las fuentes personales se incluyen por defecto;
`--project-only` las excluye y `--user-root <runtime>=<ruta>` permite otra raíz.
`all` compara declaraciones entre entornos, sin afirmar que una sesión cargue todas.

«Tus extensiones» tiene búsqueda y filtros propios por tipo, origen y runtime.
Sus declaraciones no alteran los conteos del bundle. Cada tarjeta conserva ID,
fuente, estado de propiedad y conflictos. MCP deshabilitados se indican como
configuración declarada; conexión y permisos permanecen sin verificar. Tools
OpenCode son fuentes de definición, sin inferir exports. Personas siguen su
contrato de `Tipo` en los briefs, sin convertirse en agentes.

El generador carga `project-pieces.py` de su propio bundle, nunca del `--root`
inspeccionado. Un fallo del lector conserva el catálogo del bundle e indica
inventario parcial. El JSON añade `extensions` solo cuando se pide proyecto,
manteniendo `schema_version: 1` y los conteos anteriores. Para seleccionar
extensiones en tareas sigue [el método común](PROJECT-EXTENSIONS.md).

El inventario extrae frontmatters públicos, registros de hooks por runtime y los metadatos
de las ocho primeras líneas de scripts reconocidos del launcher empaquetado.
Excluye de la salida cuerpos ejecutables, comandos completos, valores del entorno
y memoria privada. Aplica el redactor
central antes de exportar. Los nombres/modelos/tools se describen tal como se
declaran, sin afirmar disponibilidad de herramientas en la sesión.

Claude/Codex/OpenCode y memoria muestran **presencia de fuentes en el bundle
inspeccionado**, no salud, acceso, configuración del proyecto consumidor ni
ejecución de hooks. La sección de extensiones inventaría aparte las declaraciones
locales del proyecto/usuario; no mide salud ni invoca servidores.

Archivos malformados o no legibles dejan avisos. Sin redactor empaquetado o raíz
válida, exit 2 y diagnóstico, sin emitir metadatos. El flujo del usuario continúa.
Se rechazan symlinks y hay límites de lectura/inventario. El HTML se escribe
atómicamente; solo puede reemplazarse si lleva el marcador de este generador.
Para actualizar la vista, vuelve a generar el archivo.

Las páginas del panel presentan navegación por menú, tarjetas de
inventario, filtros y detalles desplegables de funciones y roles. Se adapta a
móvil, permite operar los controles con teclado y respeta movimiento reducido.
No necesita servidor ni assets de terceros (Chart.js va vendorizado). Si falta
Chart.js o su procedencia, las páginas avisan y muestran tablas; el inventario JSON sigue disponible.

La comparación y decisiones están en
[decisiones de arquitectura y memoria](roadmap/2026-10-06-capability-foundation/comparison.md).
El panel es una implementación propia con stdlib.

## Diagnóstico importado

El panel puede consumir un informe **seleccionado explícitamente**. Primero
solicita a doctor `--panel-json` con la raíz del proyecto y conserva su salida
en un fichero elegido. Después pasa `--diagnostics-report <informe.json>` y
`--project <misma-raíz>` a build_panel. El panel no ejecuta doctor, busca informes
ni comprueba servicios. Doctor conserva las comprobaciones de capacidades
opt-in activas y puede consultar sus backends cuando se solicita el diagnóstico.
Su exit 1 indica errores encontrados y puede acompañar una proyección válida;
exit 2 indica fallo de uso/proyección. No uses el JSON general de doctor: incluye
detalles privados y se rechaza en esta entrada.

Doctor pasa la proyección por el redactor común antes de exportarla. Si falta
el contrato o el redactor empaquetado, devuelve un aviso opaco y exit 2.

La proyección tiene versión 1, productor declarado doctor, fecha UTC, clave SHA-256
de la ruta absoluta normalizada y filas por bloque. Esa clave liga la misma
escritura de ruta según el sistema operativo; no certifica identidad física,
anonimato ni procedencia del proceso. Cambiar de ruta exige otra comprobación.
La fuente visible es SHA-256 del texto UTF-8 decodificado (sin BOM), no de sus
bytes originales. Identifica el contenido importado, sin autenticar el productor.

El formato admite ocho bloques públicos, hasta **512 filas** y **64 KiB** de
entrada. Solo exporta severidad, etiquetas públicas exactas y hasta tres
referencias de acciones prioritarias. Nombres privados/desconocidos usan el
ordinal de fila; detalles, rutas y arreglos libres permanecen en doctor. Las
prioridades enlazan la comprobación y remiten al bloque/fila de doctor para su
detalle y remedio. Ningún enlace ejecuta comandos ni modifica instalaciones.

La fecha pertenece a una instantánea histórica, incluso cuando es reciente.
Más de 24 horas se etiqueta como antigua; una fecha futura se rechaza. Ausencia,
formato incompatible, scope sin ligar/diferente, fallo de lectura y recorte son
estados distintos. Un informe parcial muestra recuentos parciales y omite
prioridades. Sin informe no se inventan ceros, readiness, tasas o salud.

Diagnóstico tiene filtro de severidad, búsqueda, fragmentos y foco de teclado.
El inventario y sus filtros siguen independientes. Una comprobación correcta
no cambia `load_status` o `execution_status` de los hooks. Regenera el panel para
actualizarlo; el exportado no es un servicio vivo.

La sección «Guides by role» lee el registro de capacidades del bundle
inspeccionado y relaciona guías con roles. No suma esas filas a las tarjetas ni
afirma que las guías se hayan aplicado. Un registro ausente/inválido deja el
catálogo utilizable y muestra el límite. `/work-context` consulta ese registro
por rol/fase/stack/área desde el paquete de la tarea.
