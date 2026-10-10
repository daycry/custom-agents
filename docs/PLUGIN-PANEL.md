# Panel de capacidades del plugin

[English](en/PLUGIN-PANEL.md) · **Español**

El comando `/plugin-catalog` usa plugin-panel para mostrar agentes, skills,
comandos, tools declaradas y hooks globales. La búsqueda y los filtros funcionan
en un HTML autónomo. El modo servido añade progreso y consulta local de memoria; cartera detallada,
evaluaciones y presupuestos siguen en roadmap-dashboard.

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
python skills/plugin-panel/scripts/build_panel.py --html panel.html
python skills/plugin-panel/scripts/build_panel.py --json
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --html panel.html
```

En una instalación, localiza la skill en las raíces del runtime. El script
identifica el bundle por su propia ubicación. `--root <bundle>` permite inspeccionar
otro catálogo; no importa código del catálogo inspeccionado. Python nativo funciona
en Windows; no necesita WSL, Tkinter o paquetes Python adicionales. La
exportación autónoma no necesita servidor.

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
consulta local de memoria y la revisión de planes seleccionada explícitamente.
La revisión sólo escribe sus propios recibos y comentarios locales. Sin cookies
ni logs de acceso; CSP con nonce, conexión al mismo origen, no-store, no-referrer
y marcos prohibidos. La capacidad no aísla frente a procesos del mismo usuario.
Consumir una decisión de plan requiere el CLI común y el workflow autorizado.
Publicar/reconstruir memoria conserva sus consumidores y pruebas.

## Revisar un plan en la puerta existente

La revisión visual es opcional. Sustituye el «OK del plan» pendiente de `/dev-cycle`
cuando se pide expresamente. Un OK conversacional suficiente permite continuar sin
abrir este canal ni confirmar otra vez.

```powershell
python skills/plugin-panel/scripts/build_panel.py --serve --project . --review-initiative docs/roadmap/<fecha>-<slug> --review-state-root ./.claude/plan-review --review-gate-key plan-ok
```

Selecciona la ruta exacta de la iniciativa; sólo se revisa `improvement-plan.md`.
`--review-initiative` y `--review-state-root` van juntos. El builder usa
`requested-review` por defecto; `/dev-cycle` debe seleccionar `plan-ok`.
Una decisión de revisión general no autoriza esa puerta. El modo servido excluye
`--html`, `--json`, `--home` y `--user-root`. El HTML autónomo no abre revisión ni escribe estado.

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

El bundle común necesita `plan-review.py`, `local-read.py` y `redact.py`.
La revisión en «solo skills» requiere que el export incluya esas tres dependencias
declaradas desde plugin-panel. La comprobación del paquete pertenece a QA;
sin cualquiera de ellas, el canal queda indisponible.
El [comando](../commands/dev-cycle.md) describe receive/ack y la vuelta autorizada al planner.

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

La plantilla local empaquetada presenta navegación por secciones, tarjetas de
inventario, filtros y detalles desplegables de funciones y roles. Se adapta a
móvil, permite operar los controles con teclado y respeta movimiento reducido.
No necesita servidor ni assets de terceros. Si falta la plantilla, el HTML avisa
y el inventario JSON sigue disponible.

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
no cambia `load_status` o `execution_status` de los hooks. Regenera el HTML para
actualizarlo; no es un servicio vivo. En el checkout, /panel.html es un artefacto
local excluido de Git; la plantilla empaquetada sigue versionada.

La sección «Guides by role» lee el registro de capacidades del bundle
inspeccionado y relaciona guías con roles. No suma esas filas a las tarjetas ni
afirma que las guías se hayan aplicado. Un registro ausente/inválido deja el
catálogo utilizable y muestra el límite. `/work-context` consulta ese registro
por rol/fase/stack/área desde el paquete de la tarea.
