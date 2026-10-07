# Comparación de navegación, interacciones, mantenibilidad y datos

Fichas S036–S042 de la revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`. Se leyeron siete cuerpos completos:
61.516 bytes/2.008 líneas. Ninguno tiene recursos locales en su directorio.
[navigation-reading-evidence.json](navigation-reading-evidence.json) registra
21 fuentes, 28 archivos propios y 15 contrastes documentales oficiales. El
enlace antiguo de autenticación devuelve HTTP 404; la documentación actual
se leyó y queda identificada por separado. Los consumidores leídos parcialmente
no cuentan como otras piezas evaluadas. Progreso canónico: [tasks.md](../tasks.md).

Los destinos son **propuestas para T-08**, no altas de producción. No se
ejecutaron servidores, herramientas MCP, código del corpus, SQL, instalaciones,
misiones, recorridos ni modificaciones del proyecto consumidor. Las consultas
HTTP fueron de documentación y metadata pública; no acreditan autenticación,
dispatch o funcionamiento de los proveedores. Tokens y latencia son null.
Las comprobaciones de hashes, enlaces y estructura no demuestran eficacia.

## S036 — Despacho externo de misiones con dependencias

**Identidad y lectura.** SHA-256
`5fe6efbb5663699ba8e348b2a77fbf7c396ed1903bb95fa0c05c1174f81fabfc`;
6.216 bytes/112 líneas. Sin recursos locales; el servidor citado es externo.

**Contrato y valor.** Divide un objetivo en proyecto y misiones con DAG,
dependencias, modelo, límite de turnos, estado y reporte. Aporta una interfaz
de despacho, cancelación y monitorización; el artefacto útil es un resultado
por misión que identifica cambios, pruebas, errores, bloqueos y siguiente paso.
Conservar planificación antes de efectos, aislamiento por worktree, admisión
según capacidad, dependencias explícitas y recuperación tras perder la sesión.

**Correcciones.** El procedimiento propone auto-merge al terminar una misión
y arranque automático de sus dependientes antes de la revisión independiente.
Su [README oficial](https://github.com/LEC-AI/claude-devfleet#readme) confirma ese
comportamiento. El aislamiento por worktree no acredita permisos, restricciones,
validación ni una política de merge compatible con nuestro ciclo. Si el
proveedor no permite validar el resultado antes de ese efecto, no delegar
misiones con escritura mediante ese modo; puede quedar como monitor opcional.

Los ejemplos combinan `auto_dispatch` con un despacho explícito del mismo
trabajo. Resolver un único inicio e idempotencia, no copiar ambos pasos.
El límite de tres agentes y la espera de 600 segundos son afirmaciones del
cuerpo, no parámetros comprobados en el esquema de una sesión. Consultar
tools y firmas reales; usar observación acotada con progreso y cancelación.
No atribuir al servidor externo nuestras guardias por herencia de instrucciones.

**Comparación propia.** `/dev-cycle` ya usa ledger, dependencias, briefs,
resultados de subagente, aislamiento opcional y coordinación de cambios. Su
despacho distingue tareas independientes y conserva revisión/QA/cierre en
la rama de trabajo. El proveedor no debe abrir un segundo ledger ni convertir
su dashboard en la fuente de aprobación. Los contratos nativos y el bloqueo
efectivo de cada runtime siguen pendientes en T-02/T-09.

**Decisión y destinos.** Consolidar admisión, recuperación y reporting en
el método de ejecución prolongada propuesto para `agent-system-quality`,
referencia `persistent-workflows.md` compartida con S010/S020/S021/S035.
Una referencia adicional `external-dispatch.md` describe el adaptador opt-in
de T-12: identidad de servidor, disponibilidad real, esquema/versiones,
presupuesto, proyecto/rama/base SHA, ID de misión, dependencias y resultado
tipado. Mantener la orquestación y el ledger en `/dev-cycle`; sin instalación
global, servidor, cuenta o dashboard alternativo por defecto.

Todo comportamiento útil tiene destino: planificación y aprobación vigente
en planner; DAG/admisión/despacho/cancelación en shared; estado/reportes en el
ledger y panel; revisión y QA antes del avance autorizado. Dependencia fallida,
cancelación parcial y reconexión deben conservar IDs y evidencia, evitando
repetir cambios por perder una respuesta. Un estado externo «completado» no
equivale a aceptación local.

**Activación estática.** Literal «delega estas tareas en mi servidor de
misiones»; paráfrasis «coordina trabajos externos con dependencias». Negativo
«implementa esta tarea local» → `/dev-cycle`, sin arrancar un proveedor.

**Validación e impacto pendientes.** T-12: schemas reales, identidad del
listener, doble inicio, recuperación de respuesta perdida, cancelación,
dependientes bloqueados y proveedor que hace merge prematuro. T-09/T-14:
aislamiento y efectos observados en los tres runtimes. La entrada de instalación
modular y las exclusiones del consumidor alternativo no prueban portabilidad;
actualizar exports/callers y panel sin prometer soporte por presencia de metadata.

## S037 — Auditoría del recorrido de una interacción

**Identidad y lectura.** SHA-256
`662fc5d02483bcd8ff799d6d3109a38da673182341cfc14445e9076fcd920162`;
7.975 bytes/245 líneas. Sin recursos locales ni runner.

**Contrato y valor.** Sigue una acción hasta su resultado observable: handler,
llamadas en orden, lecturas, escrituras, resets, efectos y estado final. Antes
de dividir páginas, identifica stores compartidos y todos los consumidores.
Produce un hallazgo con evento, ruta/línea, secuencia causal, resultado esperado,
resultado actual, impacto y reparación verificable.

Conservar sus seis lentes: escritura anulada por otra posterior; respuesta
asíncrona fuera de orden; closure obsoleta; transición ausente; rama condicional
inalcanzable; interferencia de efectos/suscripciones. Permite inspección de una
página, del cambio de un store o del conjunto de consumidores afectados.
La etiqueta de éxito debe corresponder al estado final y a la persistencia real.

**Correcciones.** El número de defectos que el autor dice haber encontrado no
es una medición del plugin. Una secuencia sospechosa leída estáticamente es una
hipótesis, no un bug reproducido. Tampoco demuestra que el método de depuración
existente no pueda detectarlo. Los ocho subagentes y nombres de páginas del
ejemplo pertenecen a una aplicación concreta; no fijar esa topología en todos
los proyectos. Los comandos de otro plugin no son dependencias propias.

**Comparación propia.** `frontend-quality` ya trata estados, accesibilidad y
comportamiento; `debug-root-cause` exige reproducción e hipótesis probada; qa
comprueba escenarios de aceptación. Falta el mapa explícito evento → store →
efectos → estado final y la inspección de resets cruzados. La referencia React
puede ilustrar actualizaciones funcionales y limpieza, pero el método sirve
también para Vue, JavaScript directo y otros consumidores de estado.

**Decisión y destinos.** Ampliar `frontend-quality` con
`references/state-transition-audit.md`. Un único método comparte tabla de
transiciones, interleavings y plantilla de hallazgo; qa define el resultado
observable, debug-root-cause prueba la hipótesis y TDD configurado fija la
regresión. No crear otro rol de revisión o un ciclo de reparación duplicado.

Conservar carga/error/retry, navegación, foco/teclado y suscripciones en el
contrato de interacción. Distinguir cancelación de respuesta local y efectos
ya persistidos en servidor; abortar una petición no demuestra rollback.
Graduar hallazgos con la escala propia y el efecto concreto, sin equivalencias
automáticas entre nombres de severidad.

**Activación estática.** Literal «al pulsar guardar aparece éxito pero se
vacía el formulario»; paráfrasis «dos respuestas se pisan y queda el estado
anterior». Negativo «cambia el color del botón» → trabajo visual; respuesta API
incorrecta sin transición UI → depuración del backend.

**Validación e impacto pendientes.** T-10/T-14: reproducción, orden de dos
promesas controladas, escritura/reset compartido, doble envío, cierre/reapertura,
suscripción desmontada y teclado. T-13: menú y etapas del panel con selección
y contenido coherentes. Esos escenarios no se ejecutaron en este bloque.
Actualizar trigger, referencia React, QA y manifiestos sin precargar la guía
en todas las tareas de frontend ni exigir el plugin externo.

## S038 — Analítica e ingestión con ClickHouse

**Identidad y lectura.** SHA-256
`9f0f2b632f3feb1bd4ca7bae119fe05454668ab763b7d3c3d304f8740b8fd415`;
10.731 bytes/445 líneas. Sin recursos locales ni fixtures ejecutables.

**Contrato y valor.** Especialidad opcional de OLAP: MergeTree,
ReplacingMergeTree, agregados/materialized views, consultas, SDK JavaScript,
ingestión batch/stream, observación de consultas/partes, retención, cohortes,
funnel y ETL. Produce propuestas de esquema y consultas con grain, precisión,
coste y validación; no instala una base de datos ni despliega pipelines.

**Correcciones de modelo.** El ejemplo usa `ORDER BY (user_id, event_id,
timestamp)` y `PRIMARY KEY (user_id, event_id)` para supuesta deduplicación.
En [ReplacingMergeTree](https://clickhouse.com/docs/guides/replacing-merge-tree),
la identidad de reemplazo depende del ORDER BY completo. Cambiar timestamp
puede conservar dos filas; definir clave estable, versionado y política de
partición según se modelen eventos o actualizaciones. El merge es eventual;
un SELECT simple no prueba unicidad y FINAL puede ser necesario para corrección.
No convertir «evitar FINAL» en regla universal de rendimiento.

El destino de agregados declara un estado `count` parametrizado por UInt32
pero el SELECT produce `countState()` sin argumento. Deben coincidir los tipos
de estado, entrada y merge: este snippet necesita prueba en la versión elegida.
Las tablas fuente y tipos monetarios no están completos. Las
[vistas incrementales](https://clickhouse.com/docs/materialized-view/incremental-materialized-view)
procesan bloques insertados; los cambios de tablas a la derecha de un JOIN no
recalculan automáticamente el destino. Definir backfill, correcciones y
reconciliación antes de atribuirles mantenimiento completo del histórico.

Poner un predicado primero en WHERE no acredita poda por índice. La
[guía de clave primaria](https://clickhouse.com/docs/best-practices/choosing-a-primary-key)
usa índices dispersos y EXPLAIN para contrastar lecturas; elegir orden por
carga real, no «alta cardinalidad primero» indiscriminadamente. El propio
SELECT * de ejemplo contradice su consejo de seleccionar columnas necesarias.

[quantile](https://clickhouse.com/docs/sql-reference/aggregate-functions/reference/quantile)
es aproximado y no determinista; declarar error tolerable y alternativa exacta.
Para varios niveles valorar estados compartidos con quantiles. No afirmar
superioridad frente a otro motor sin carga y benchmark comparables.

**Correcciones de métricas e ingestión.** La retención agrupa por usuario y día
de actividad y obtiene en ese mismo grupo el mínimo timestamp: signup coincide
con actividad y days_since_signup acaba en cero. Calcular primero alta real o
primera actividad por usuario y después cohortes/actividad con denominador
explícito. El funnel cuenta eventos por sesión sin orden ni ventana; repetidos
pueden superar 100 %. Definir entidad, orden, ventana, duplicados y denominador
cero antes de llamar a esos recuentos conversión.

El ETL periódico asíncrono necesita exclusión de ejecuciones, checkpoint,
retries y validación; `parseFloat`/`parseInt` sin contrato pueden perder precisión.
El [cliente JavaScript](https://clickhouse.com/docs/integrations/javascript)
distingue streams Node/web, formatos y representaciones de enteros grandes,
Decimal y fechas. Los objetos Date requieren configuración compatible de
DateTime; no son inválidos por sí mismos. Fijar tipos/formato/zona horaria,
backpressure, abort, cierre y errores. El cliente web no admite los mismos
inserts streaming que Node.

El ejemplo denominado CDC no implementa una conexión supervisada, recuperación
o cursor duradero. [PostgreSQL NOTIFY](https://www.postgresql.org/docs/current/sql-notify.html)
entrega a listeners con semántica transaccional y límites de payload/cola;
no demuestra un feed recuperable tras desconexión. Conectar/esperar/configurar
correctamente el cliente y añadir resync/outbox o replicación adecuada al
contrato. El intervalo y la notificación no prueban entrega exactamente una vez.
Query logs pueden contener SQL y datos sensibles; la observación debe redactar
su contenido y distinguir partes físicas de filas lógicas deduplicadas.

**Comparación, decisión y destinos.** Conservar especialidad opcional en
`stack-practices/references/clickhouse.md`; backend mantiene validación,
idempotencia, jobs y retries compartidos con S024. Preservar motores/DDL,
agregados/MV, claves y EXPLAIN, precisión/grain de métricas, SDK e ingestión,
observación, retención/cohortes/funnel y reconciliación. Kafka, proyecciones y
migraciones solo aparecen como alcance sugerido, sin contrato implementado:
no anunciar colectores o cobertura que el cuerpo no aporta. No añadir un
paquete técnico global ni imponer este motor a otros proyectos.

**Activación estática.** Literal «optimiza estas consultas ClickHouse»;
paráfrasis «revisa los reemplazos y agregados de mi almacén analítico». Negativo
«diseña cualquier persistencia» → arquitectura/backend, sin asumir ClickHouse.

**Validación e impacto pendientes.** T-10/T-12/T-14: fixtures por versión con
actualización de timestamp/partición, estado count, llegada tardía/backfill,
dos días de actividad, duplicados de funnel, denominador cero, precisión grande,
stream cancelado y reconexión sin pérdidas. No se ejecutó SQL ni un cliente.
El caller PostgreSQL y el flujo de ML justifican referencias cruzadas; no
acreditan que sus otros cuerpos estén evaluados o que deban cargar esta guía.

## S039 — Recorridos guiados y anclados en el código

**Identidad y lectura.** SHA-256
`416c7eb9229554a1ef113bbb873ff0b260a2ad9ae6e6075a75c375955d3fcf6f`;
8.030 bytes/254 líneas. Sin recursos locales ni validador.

**Contrato y valor.** Produce `.tours/<persona>-<foco>.tour` con audiencia,
profundidad, título, ref Git y pasos anclados en rutas/líneas/selecciones o
patrones. Conserva reconocimiento inicial, mapa de orientación, flujo real,
caso límite, cierre y narrativa situación/mecanismo/implicación/gotcha.
Una persona lectora ajusta profundidad; no es una persona de dominio del brief.
Los intervalos de pasos sugeridos son ejemplos, no cobertura demostrada.

**Correcciones verificadas.** El ejemplo de selección usa carácter 0. El
[schema oficial](https://github.com/microsoft/codetour/blob/main/schema.json)
declara líneas y caracteres desde 1; el
[player](https://github.com/microsoft/codetour/blob/main/src/player/commands.ts)
resta uno al convertirlos. Validar ambos extremos y el archivo en la ref
elegida, no solo en el working tree. Un tour de PR debe referenciar una revisión
que contenga los archivos nuevos. Resolver rutas, patrones y colisiones de
nombres sin aceptar escapes del proyecto ni interpretar una ref como shell.

Generar solo JSON no hace que su consumo sea de solo lectura. El schema
admite comandos automáticos y condiciones JavaScript. El
[README del visor](https://github.com/microsoft/codetour#readme) describe enlaces
de comandos, terminal, inserción de snippets y edición según ref. Un recorrido
normal debe usar un subconjunto sin `commands`, `when`, enlaces ejecutables
o sintaxis de terminal; no presentar el visor como barrera de escritura.
También comprobar descriptions/URIs, no únicamente las claves superiores.

**Comparación propia.** Read-discipline ya acota lectura; research-first
compara fuentes y documenter escribe documentación bajo `docs/`. Ninguno
valida tours ni sus anclajes. `.tours/` queda fuera del alcance actual de
documenter: T-08 debe definir autor y permisos, sin ampliar ese rol en silencio.

**Decisión y destinos.** Conservar formato opcional bajo una capacidad
`codebase-navigation`, con `references/guided-tours.md`, compartiendo recon con
S040. Proponer un `validate-tour.py` propio para schema/subconjunto, rutas,
ref/blobs, posiciones y patrones acotados. El schema remoto leído no se debe
descargar/evaluar automáticamente durante validación; fijar el contrato propio.
No instalar extensión de editor para una explicación en chat.

Preservar audiencia/profundidad, secuencia narrativa, contenido introductorio,
archivos/directorios, línea/selección/patrón, ref, enlaces documentales y cierre
en destinos concretos. La adaptación del formato no concede ejecución de
comandos ni edición de fuentes del consumidor.

**Activación estática.** Literal «crea un recorrido CodeTour para esta PR»;
paráfrasis «quiero una visita guiada con pasos anclados para nuevos lectores».
Negativo «explícame esta función» → respuesta en chat, sin artefacto tour.

**Validación e impacto pendientes.** T-10/T-12: JSON, campo ejecutable,
Markdown/URI peligrosos, ruta escapada, ref incorrecta, archivo nuevo ausente,
columna cero, Unicode, selección invertida y patrón inexistente/ambiguo.
T-14: apertura de un artefacto propio sin ejecución ni modificación. El flujo
de ML y el mapa de triggers tienen callers; actualizarlos junto a exports,
panel y documentación sin convertir la especialidad en dependencia universal.

## S040 — Reconocimiento y guía de incorporación al repositorio

**Identidad y lectura.** SHA-256
`ef88873a4b0d0fe155c0a196ffecd5c7b5e28edd00fbbdb5c1fd2ca8fd0eb6f0`;
8.235 bytes/234 líneas. Sin recursos locales.

**Contrato y valor.** Reconoce manifiestos, configuración, entradas,
estructura, CI, ejemplos de entorno y tests. Produce mapa de stack/versiones,
arquitectura, request/data flow con rutas reales, convenciones, comandos,
zonas de riesgo y primeros pasos. Diferencia monorepo, servicios, API/CLI y
otros modelos en vez de inventar siempre un flujo HTTP.

**Correcciones.** Las versiones/frameworks del ejemplo no son detecciones.
Muestrear código y contrastar manifiestos; distinguir declaración, lockfile y
observación. Excluir dependencias/generados y leer configuración con límites;
un `.env.example` puede contener valores privados. La ausencia de histórico
en un repo nuevo/shallow no demuestra falta de disciplina. Mostrar comandos
desde fuentes reales no autoriza ejecutarlos ni aplicar migraciones.

El procedimiento pasa de «onboard me» a escribir instrucciones persistentes
en CLAUDE.md. Una guía en chat no equivale a autorización para cambiar las
instrucciones del proyecto. Cuando el usuario solicite ese artefacto, conservar
reglas existentes y su jerarquía, explicar cambios y elegir el formato del
runtime. El límite de 100 líneas y dos minutos de lectura no acredita el coste
real de todas las guías.

**Comparación propia.** Planner ya hace recon con rutas reales; read-discipline
limita carga y research-first exige evidencia. `/setup` configura opciones
del plugin; no describe arquitectura de una base de código. Project-pieces
inventaría metadata de extensiones, no inspecciona por sí solo implementación.
La gobernanza de documentos continuos es una intención distinta del onboarding.

**Decisión y destinos.** Consolidar recon con S039 bajo `codebase-navigation`,
`references/onboarding.md` y una plantilla de guía. Compartir descubrimiento de
entradas/estructura, evidencia de comandos/versiones y convenciones; elegir
salida según intención: conversación, guía bajo docs, instrucciones persistentes
solicitadas o tour. No crear otro agente, base de datos, ledger o paquete de stack.

La guía conserva las seis clases de fuentes, mapa de tecnologías, arquitectura,
recorrido de ejecución, prácticas de código/tests/Git, riesgos y primeros
pasos. La generación de instrucciones por runtime requiere los contratos T-02
y no convierte un archivo Claude en configuración universal.

**Activación estática.** Literal «ayúdame a entender este repositorio»;
paráfrasis «prepara una guía para un desarrollador que acaba de entrar».
Negativo «configura los opt-ins del plugin» → `/setup`; «mantén la documentación
actualizada» → documenter, no repetir onboarding completo en cada turno.

**Validación e impacto pendientes.** T-10/T-14: dos stacks en monorepo,
configuración contradictoria, repo nuevo/shallow, instrucciones existentes,
datos privados de entorno, comando ausente y salida de chat sin escrituras.
El agente de extracción de especificaciones delimita expresamente otra
intención; no contarlo como dependencia por una mención. El flujo ML consume
la guía y requiere rutas actualizadas. Verificar permisos/artefactos con
documenter y actualizar catálogo/exports sin imponer CLAUDE.md a los tres runtimes.

## S041 — Análisis estructural externo antes y después del cambio

**Identidad y lectura.** SHA-256
`c5943c4c353b02dcd87b751de15bb087caae2f11c36e84a74e181fe2eadee394`;
7.463 bytes/167 líneas. Sin recursos locales; configuración MCP en plantilla
compartida, no un servidor incluido en la skill.

**Contrato y valor.** Propone baseline antes de editar, revisión posterior,
guardia precommit y análisis del delta de rama/PR. Conserva identificación
de funciones difíciles, comparación del cambio, sugerencias localizadas y
evidencia de cobertura. El score del proveedor no es una medida de corrección.

**Vigencia y límites.** El enlace antiguo de token devuelve HTTP 404. La
[documentación actual de autenticación](https://github.com/codescene-oss/codescene-mcp-server/blob/main/docs/authentication.md)
describe mecanismos vigentes; no se abrió sesión ni se instaló el servidor.
La [metadata oficial del paquete](https://registry.npmjs.org/@codescene%2Fcodehealth-mcp/latest)
consultada declara versión 1.5.8, bin `cs-mcp`, Node ≥18 y plataformas
Windows/Linux/macOS. El [README](https://github.com/codescene-oss/codescene-mcp-server#readme)
describe descarga/caché del binario en el arranque: npx no es un inventario
sin efectos. El uso opcional requiere versión, cuenta/licencia y tools reales.

Los [contratos documentados de tools](https://github.com/codescene-oss/codescene-mcp-server/blob/main/docs/tools.md)
mantienen las cuatro operaciones de revisión, pero también describen gestión
de autenticación/configuración y otras funciones. Acotar la selección; descubrir
el servidor no autoriza mutar políticas ni cambiar de cuenta. Un reporte
precommit no demuestra que Git esté bloqueado. Separar `no_issues_found` de
`no_files_modified`, archivos elegibles/analizados, datos parciales y error.

La escala 1–10 y límites sugeridos por el cuerpo no deben convertirse en una
política universal; sus rangos y recomendaciones no son coherentes entre sí.
El salto de puntuación del ejemplo es del autor, no un resultado medido aquí.
La descripción de análisis local no prueba ausencia de red para instalación,
actualizaciones, auth o todas las versiones del proveedor.

**Comparación propia.** `code-health` mide duplicados, tamaño/anidamiento,
hotspots y marcadores con antigüedad. Su baseline compara heurísticas y no
produce el score externo 1–10. Evaluator y planner ya convierten esa evidencia
en riesgo/deuda dentro del alcance. QA, pruebas y revisión independiente
siguen siendo necesarias aunque suba cualquier puntuación.

**Decisión y destinos.** Ampliar `code-health` con una referencia opt-in
`references/external-analysis.md`, sin otro agente de salud. T-12 propone un
adaptador por proveedor seleccionado que conserva reporte bruto redactado,
proveedor/versión, raíz, base/head, reglas, lenguajes elegibles, archivos
analizados, desconocidos y baseline comparable. No reescalar nuestras métricas
para fingir equivalencia ni mejorar puntuación suprimiendo reglas sin justificar.

Baselines, revisión del cambio, gate pactado y delta tienen destinos en
code-health/shared y sus consumidores existentes; panel muestra proveedor,
cobertura y estado, sin exponer credenciales. Si es opcional y no está
disponible, avisar y usar controles propios con sus límites. Si es un gate
obligatorio acordado, no declarar cierre verificado sin evidencia compatible;
el trabajo independiente autorizado puede continuar. No añadir un flujo de
permiso rutinario para cada fallo de un proveedor opcional.

**Activación estática.** Literal «compara la mantenibilidad con mi MCP
CodeScene»; paráfrasis «usa el analizador externo configurado para el delta».
Negativo «mide duplicación sin herramientas externas» → code-health local.

**Validación e impacto pendientes.** T-12/T-14: sin auth, cero elegibles,
cobertura parcial, lenguaje no soportado, score ausente, base cambiada,
reglas/versiones distintas y mismo baseline verificable. T-09 comprueba
el bloqueo real si se integra un gate; T-13 muestra cobertura sin falso verde.
Actualizar plantilla MCP, exclusiones de instalación y consumidores sin
instalar/licenciar automáticamente. Ninguna tool del proveedor fue invocada.

## S042 — Convenciones generales y ejemplos TypeScript/React

**Identidad y lectura.** SHA-256
`e80544c3d1eac5b14f22022146bd91a6b0ecc30e099cf5181894853aeb81dee1`;
12.866 bytes/551 líneas. Sin recursos locales. La regla común es una dependencia
separada y leída completa, no un recurso de este directorio.

**Contrato y valor.** Reúne claridad de nombres, funciones cohesionadas,
KISS/DRY/YAGNI, tipos, errores, inmutabilidad, concurrencia, organización,
documentación y pruebas. Sus ejemplos concretos usan TypeScript/JavaScript,
React/Next, validación y acceso a datos; ese alcance no es una norma universal
para todos los lenguajes.

**Correcciones.** «Siempre spread, nunca mutación» contradice su excepción
de rendimiento y no resuelve alias de objetos anidados: spread es superficial.
Definir propiedad y límites del estado compartido; mutar un buffer local
propio no tiene el mismo contrato que mutar estado de UI. No imponer copias
indiscriminadas ni extender convenciones React a otros stacks.

Los ejemplos de error registran objetos completos y reemplazan excepciones
sin preservar causa; separar clasificación, contexto redactado y responsabilidad
de logging. El handler POST deja parsing fuera de su catch y no muestra
respuesta para todos los errores: son ejemplos incompletos, no una API lista.
Promise.all exige independencia, política de fallo/cancelación y límite de
concurrencia; no paralelizar efectos solo porque el snippet sea más corto.

Un botón reutilizable necesita intención explícita dentro de formularios;
una actualización basada en estado anterior necesita su contrato correcto.
Loading/error/data deben producir estados coherentes y testables. La
[documentación React](https://react.dev/reference/react/useMemo) trata memoización
como optimización, no garantía semántica, y contempla el compiler; medir y
respetar la configuración antes de añadir useMemo/useCallback a todo componente.

La forma de envelope API debe seguir contrato/consumidores reales; si se
introduce, usar estados tipados coherentes. No imponer REST wrappers, Zod,
Supabase, Next ni organización por tipos a un proyecto con otras convenciones.
Los tests vacíos son ilustración, no cobertura; límites de líneas/anidamiento
son heurísticas configurables, no defectos de corrección por sí solos.

**Comparación, decisión y destinos.** Consolidar un mínimo agnóstico en
`stack-practices/references/coding-baseline.md` y ejemplos propios en una
referencia TypeScript opcional. La tabla conserva cada grupo con un único dueño:

| Contenido útil | Destino propuesto o método ya existente |
|---|---|
| Nombres, cohesión, simplicidad, comentarios del porqué | Coding baseline; convenciones del proyecto prevalecen |
| Tipos, null/unknown, inmutabilidad y alias | Referencia TypeScript con límites de propiedad |
| Errores, contexto, async y concurrencia | Backend compartido y ejemplos TypeScript |
| Componentes, estado, debounce y accesibilidad | Referencia React y frontend-quality |
| API, validación y acceso a datos | Contratos backend/api-contract; ejemplos por stack |
| Organización y documentación pública | Baseline/onboarding, sin árbol de carpetas obligatorio |
| AAA, nombres y casos significativos | TDD/unit-tests existentes, sin duplicar método |
| Memoización, carga diferida y consultas | Referencias React/backend con evidencia de coste |
| Funciones largas/anidamiento | Code-health como indicador contextual, no prohibición fija |

**Activación estática.** Literal «revisa convenciones TypeScript de este
cambio»; paráfrasis «simplifica nombres y contratos de estas funciones».
Negativo «aplica las convenciones Java de este repo» → especialidad/guía de
ese stack, sin importar ejemplos React o cambiar organización por defecto.

**Validación e impacto pendientes.** T-10/T-11/T-14: alias anidado, estados
de formulario, error inesperado, concurrencia con dependencia, envelope
compatible, ausencia de dependencias ejemplificadas y conservación de normas
del repo. El revisor TypeScript, prompt optimizer, React Native y Vue contienen
referencias pertinentes; comprobar su transferencia antes de consolidar.
Las reglas con nombre parecido pero calificadas para otros lenguajes no se
cuentan como callers de esta skill. Triggers/manifiestos/exports deben apuntar
al contenido nuevo, sin alias vacíos ni duplicación de guías enteras.

## Cierre de este bloque

S036–S042 están **evaluadas, no integradas**. Las fuentes completas,
dependencias/callers acotados y documentación externa tienen alcances distintos
en el JSON. Los siete directorios tienen cero recursos locales; las referencias
compartidas no se contabilizan como recursos propios de las skills.

T-08 resolverá los destinos propuestos junto a las fichas restantes. T-09/T-12
deben probar los mecanismos y versiones; T-10/T-11 integrarán contenido y
consumidores; T-13/T-14 acreditarán panel y escenarios funcionales. No sustituir
esa evidencia por linter verde, metadata de instalación o afirmaciones del autor.
