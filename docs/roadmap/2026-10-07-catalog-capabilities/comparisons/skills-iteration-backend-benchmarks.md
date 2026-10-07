# Comparación de ejecución, backend, medición y planificación

Fichas S021–S027 de la revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`. Se leyeron los siete cuerpos
completos, sin recursos adicionales dentro de sus directorios, y los
consumidores pertinentes. [iteration-reading-evidence.json](iteration-reading-evidence.json)
registra hashes, rangos, reutilizaciones comprobadas y contrastes oficiales.
Los cuerpos y fragmentos de otras piezas usados como dependencia no cuentan
como nuevas skills evaluadas. El progreso canónico está en [tasks.md](../tasks.md).

Todas las decisiones y rutas de destino siguientes son **propuestas** para
T-08: no hay integración de producción en este bloque. La evidencia es de
lectura documental y análisis estático. La ejecución de código del corpus,
invocación de modelos, instalación de SDKs, medición de aplicaciones, consulta
de cuentas comerciales y apertura de escenas 3D no se realizaron. Las referencias a
comandos y APIs describen contratos por verificar, no ejecuciones acreditadas.

## S021 — Ejecución prolongada y trabajo por dependencias

**Identidad y lectura.** SHA-256
`c2db797295500b9c2b31d9dd2451ef28727346c739b5d1d3366f0f9ea2e823dc`;
24.851 bytes/611 líneas; cuerpo completo y recursos locales 0/0.
Se leyeron también S052 completo, C044 completo y R-fbe5fb44db00 completo:
el último es un helper de 16.269 bytes/521 líneas situado fuera de la skill.

**Contrato y valor.** Decide cómo continuar una tarea larga y cómo transportar
estado entre ejecuciones. Hay seis patrones distintos que conservar:

1. Secuencia implementar → limpiar → verificar → guardar el cambio, con
   resultados de cada etapa y parada ante fallo.
2. Sesión persistente con historial, búsqueda, exportación y rama de contexto.
3. Generación por tandas con especificación común, direcciones de trabajo
   diferenciadas y asignación de salidas.
4. Worker por iteración con límites de ejecuciones, tiempo y coste, notas,
   revisión y operaciones de rama/PR/CI.
5. Revisión de simplificación posterior que examine tests, comprobaciones,
   logging y comentarios por su utilidad concreta.
6. Unidades cohesionadas con IDs, secciones de requisitos, dependencias,
   aceptación y complejidad; trabajo por capas, aislamiento, revisión por otra
   persona/agente, integración ordenada y recuperación con evidencia de fallo.

Los handoffs incluyen investigación, plan, diferencias, tests fallidos,
hallazgos de revisión y motivo de expulsión/reintento. Evitar contexto sin
límite, reintentos ciegos, autor como único revisor y escrituras solapadas.

**Vigencia y defectos.** La cabecera lo presenta como alias temporal de una
versión antigua, pero el corpus fijado conserva el cuerpo extenso. S052 tiene
46 líneas y remite a patrones; no contiene todos los detalles anteriores.
Eliminar el cuerpo por su etiqueta de obsoleto perdería contenido útil.
S166 aporta comprobaciones del diseño del loop y S217 lo recomienda para
flujos de agentes; esos enlaces no acreditan un runner portable. C044 imprime
comandos y propone un plan separado y un modo fast con gates reducidos.
Conservar preparación y condiciones de parada, pero integrar en el ledger
existente y respetar sus gates; un perfil de hooks declarado tampoco prueba
su carga, identidad o capacidad de bloqueo en cada runtime.

La [referencia CLI oficial](https://code.claude.com/docs/en/cli-reference)
distingue `--allowedTools`, permiso sin pregunta, de `--tools`, que restringe
herramientas integradas. Este último no restringe por sí mismo las MCP. Un
argumento de ejemplo no es una garantía de aislamiento o identidad de rol.
La ayuda instalada 2.1.287 se conserva como evidencia separada: la ausencia
de un flag en help no basta para declararlo inválido.

El [README del worker externo](https://github.com/AnandChowdhary/continuous-claude/blob/main/README.md)
documenta proveedores Claude/Codex, diferencia `--disable-commits` y
`--dry-run`, y limita algunas funciones de worktrees/CI al runner Bash.
Costes Codex requieren eventos de uso y tarifas explícitas. El flag de retry
del ejemplo necesita contrato de versión; su ausencia en el README actual
no prueba por sí sola incompatibilidad. No se instaló ni ejecutó ese worker.
El motor de DAG con almacenamiento SQLite/jj se describe sin implementación
fijada verificable en este bloque; preservar el patrón, no copiar un arranque
externo sin contrato. Tres frases de «terminado» no prueban aceptación cumplida.

**Helper leído.** R-fbe5fb44db00 almacena sesiones por nombre bajo la raíz
personal, no por identidad de proyecto. Carga todo el historial; el límite de
su parser no limita lo cargado ni el prompt final. Los encabezados de texto
no son mensajes con rol system. Las skills se resuelven desde cwd, con nombres
sin confinamiento equivalente al guard propio, y las ausencias se omiten.
La escritura no tiene bloqueo; compactar conserva los últimos turnos sin
resumen y una rama puede sobrescribir un destino existente. El token mostrado
es una estimación por caracteres, no consumo medido.

Tiene timeout de proceso de 300 segundos y validación de modelo/launcher;
no garantiza un resultado tipado por estado. Un exit distinto de cero con
stderr vacío puede presentar stdout como respuesta normal. Los errores y
salidas pasan al historial. Búsqueda/exportación/limpieza necesitan alcance
de proyecto, redacción y controles de escritura si se adaptan. No importar
este helper como una segunda memoria canónica ni ejecutar código del consumidor.

**Comparación propia.** `commands/dev-cycle.md` ya separa implementación,
revisión y QA; su despacho usa briefs de contexto fresco y su vía paralela
integra worktrees de forma secuencial. `planner` conserva dependencias y
aceptación en el ledger. `knowledge-check`/`knowledge-write` separan consulta
y publicación curada. Faltan pautas compartidas para recuperación prolongada,
reserva concurrente de salidas y unidades por capas con handoffs trazables.
El propio método no acredita todavía todo el despacho nativo: T-02/T-09
mantienen explícitamente esa verificación pendiente.

**Decisión y destinos.** **Consolidar** con S010/S020/S052 en el destino ya
propuesto `skills/agent-system-quality/references/persistent-workflows.md` y
la referencia propuesta
`skills/delivery-practices/references/parallel-delivery.md`. Conservar los seis
patrones, selección por riesgo, presupuestos, recuperación y evidencias; usar
el ledger, briefs y gates existentes. La reserva de salida necesita atomicidad:
leer el mayor contador y sumar uno no evita carreras entre orquestadores.
Las ramas sin archivos compartidos pueden competir por servicios o recursos;
comprobar también el resultado combinado en el HEAD de integración.
La limpieza adicional debe justificar utilidad, no imponer siempre otra
llamada de modelo ni retirar tests por cantidad. Las afirmaciones universales
sobre mejor rendimiento de dos agentes no tienen medición en esta pieza.

**Activación estática.** Literal: «Organiza este trabajo largo por unidades
dependientes». Paráfrasis: «Cómo retomamos el proceso tras un fallo sin perder
resultados». Negativo vecino: «Corrige este typo» → vía rápida existente.
No se probaron invocación, concurrency, recuperación ni despacho del runner.

**Coste, degradación e impacto.** Cargar únicamente el patrón pertinente y
estado acotado; tokens/latencia null. Sin launcher o medición compatibles,
explicar el límite y usar la ejecución disponible; no declarar gasto controlado
sin datos. T-10/T-11 deben armonizar S021/S052/C044 y sus callers, sin alias
vacíos. T-09/T-12/T-14 verificarán permisos, exit, cancelación, aislamiento,
reservas y recuperación antes de publicar. T-15 actualizará docs/exports ES/EN.

## S022 — Backend por servicios, contratos, caché y trabajos

**Identidad y lectura.** SHA-256
`9b983d0297a983110fdfda8dce55d19b750ca3e53ef155d75a3eff740d3874b8`;
13.349 bytes/562 líneas; cuerpo completo, recursos locales 0/0.

**Contrato y valor.** Architect delimita repositorio, servicio, middleware y
transporte; implementer desarrolla operaciones y qa verifica contratos/fallos.
Conservar URLs y consultas REST, interfaces, inyección de dependencias,
selección de columnas, batching para N+1, transacciones, caché e invalidación,
validación/errores, retries, autenticación y autorización, rate limits,
trabajos asíncronos y logs estructurados con correlación.
El rate limit usa un store compartido, gateway o mecanismo de plataforma;
conservar la separación entre integración backend, contrato HTTP y revisión
de abuso. Los contadores por proceso no acreditan un límite global entre
réplicas y despliegues.

**Defectos concretos.** El servicio usa findByIds sin declararlo en la interfaz;
las operaciones incompletas no forman una fixture compilable. Ordenar scores
necesita declarar su sentido y tratar candidatos ausentes; buscar cada score
linealmente dentro del comparator añade trabajo evitable. El repositorio usa
select('*') aunque la guía posterior pide columnas explícitas.

El SQL recibe JSON y hace INSERT sin columnas: depende de una estructura de
tabla no declarada. No es una receta universal de inserción. La función captura
una excepción y devuelve success:false, mientras el caller solo comprueba el
error RPC. Puede tratar un fallo de negocio como dato exitoso. PostgreSQL
explica el [rollback del bloque con EXCEPTION](https://www.postgresql.org/docs/current/plpgsql-control-structures.html#PLPGSQL-ERROR-TRAPPING)
y Supabase distingue [data/error en RPC](https://supabase.com/docs/reference/javascript/rpc):
verificar también el contrato del resultado, no solo el transporte.

El try de withAuth contiene verificación y llamada al handler: un fallo
síncrono del negocio puede clasificarse como 401. Devolver su promesa sin
await tampoco captura allí su rechazo. Separar autenticación de errores de
negocio; cambiar solo a await dentro del mismo catch no resuelve la
clasificación. Es análisis estático del fragmento, no una fixture ejecutada.
El cast del payload JWT no valida campos en ejecución. La
[documentación de jsonwebtoken](https://github.com/auth0/node-jsonwebtoken/blob/master/README.md)
pide tratar el payload verificado como entrada y documenta opciones de
issuer/audience/algorithms. El consumidor fija versión, claves y claims;
validar configuración y autorización de recurso/tenant además del rol.

La caché omite identidad/tenant, validación del dato e integración de
invalidaciones con escrituras. Faltan tratamiento de outage, stampede y
política de datos obsoletos; el nombre setex depende del cliente elegido.
El retry reintenta errores sin clasificación, jitter, timeout o cancelación;
su parámetro cuenta intentos y el caso cero puede lanzar un valor indefinido.
Definir idempotencia, límites y errores recuperables antes de reutilizarlo.
La cola en memoria retira el trabajo antes de completar y solo registra el
fallo: no aporta durabilidad, recuperación, backpressure ni cierre ordenado.
Los logs aceptan contexto que puede sobrescribir campos de control; acotar y
redactar contenido, conservar correlación y no copiar emails/stacks sin criterio.

**Comparación propia.** `backend-practices/references/contracts-data.md`
cubre recursos/tenant, autenticación, idempotencia, timeouts, batching,
transacciones, outbox y migración. `api-contract` mantiene contrato primero.
No detallan middleware Node ni lifecycle de caché y workers. Los ejemplos
de Next Pages y App Router no comparten firma: escoger el transporte real
del consumidor y su versión, sin imponer Next, Redis, Supabase o JWT.

**Dependencias y consumidores.** S015 conecta wiring de APIs; los fragmentos
de estándares, contratos, revisores TypeScript y guías Laravel/Rails/SQL/
Prisma/Redis enlazan criterios backend. R-591e7a1672e1/R-03ffcc8e6e9e distribuyen
la pieza; los mapas de stack y triggers seleccionan contexto, no prueban
ejecución. Bases de datos, clientes y frameworks pertenecen al consumidor.

**Decisión y destinos.** **Ampliar** `skills/backend-practices/SKILL.md` y
`references/contracts-data.md` con referencias propuestas
`skills/backend-practices/references/service-boundaries.md` y
`skills/backend-practices/references/cache-jobs.md`. Conservar todos los
criterios enumerados, con ejemplos opcionales por SDK/versionado y las
correcciones anteriores. No crear otro rol backend ni un paquete obligatorio.

**Activación estática.** Literal: «Diseña servicio y repositorio de esta API».
Paráfrasis: «Evita consultas repetidas y define cómo invalidar la caché».
Negativo: «Compara posicionamiento comercial» → análisis competitivo, S024.
No se compilaron TypeScript, SQL/RPC, JWT, Redis ni workers.

**Coste, degradación e impacto.** Cargar la referencia pertinente, no 562
líneas siempre; tokens/latencia null. Sin SDK/servicio, dejar pruebas pendientes
y mantener contrato genérico. T-10/T-11 actualizarán selección/callers;
T-14 deberá comprobar éxito/fallos, rechazo async, payload, tenants, caché,
retries y recuperación de jobs en fixtures relevantes. T-15 docs/exports ES/EN.

## S023 — Baselines de rendimiento de aplicación

**Identidad y lectura.** SHA-256
`58e34c3ccf60ee5155e3db74357b73770015a7aad3594649b6758ba8375ab6ff`;
2.630 bytes/95 líneas; cuerpo completo, recursos locales 0/0.

**Contrato y valor.** Define mediciones frontend, API, build y comparación
antes/después. Frontend: LCP/CLS/INP, FCP/TTFB, peso y red. API: latencias,
distribución, carga, status y respuestas. Build: frío, HMR, tests,
tipos/lint e imagen de contenedor. Conservar condiciones, baseline persistente,
delta, comparación en CI y relación con QA/observación posterior al despliegue.
QA conserva el gate; la medición no acredita corrección por sí sola.

**Vigencia y límites.** No incluye collector, esquema ejecutable ni comando
en commands; una invocación slash puede ser una skill del host y no un comando
portable. Los límites de peso y latencia son referencias, no políticas válidas
para todos los productos. Definir unidades, compresión, muestras, estado de
caché, dispositivo, red, versiones y carga antes de imponer un gate.
La [guía oficial Web Vitals](https://web.dev/articles/vitals) usa percentil 75
de datos de campo separado por móvil/escritorio. Un smoke de laboratorio
no acredita ese cumplimiento; INP requiere interacciones medidas.
Con 100 muestras el p99 depende de muy pocas observaciones: declarar método,
repeticiones e incertidumbre adecuados al cambio. Las llamadas de carga
necesitan alcance de prueba, identidad, límites y limpieza si mutan datos.

**Comparación propia.** `frontend-quality/references/interaction-performance.md`
exige interacción y medición de presupuestos. `outcome-evals/references/protocol.md`
ya exige baseline, condiciones repetibles, validez y comparación. Su reporter
actual mide resultados de tareas, duración/tokens/coste y checks; no es un
collector universal de LCP, latencia HTTP o tiempos de build. Conservar esas
semánticas y añadir un artefacto de rendimiento compatible y versionado.

**Dependencias, decisión y destinos.** S176 enlaza benchmarking de ingeniería;
S030/S032 remiten a QA y observación de despliegue, con cabeceras leídas aquí,
no evaluación completa. **Ampliar** outcome-evals con la referencia propuesta
`skills/outcome-evals/references/performance-baselines.md` y contrato futuro
para resultados en `evals/performance/`. Reutilizar frontend-quality, qa y gates.
No rellenar métricas no obtenidas con cero; usar null y motivo. Separar datos
de campo/laboratorio y URLs privadas redactadas, sin un segundo ledger.

**Activación estática.** Literal: «Mide p95 de esta API antes y después».
Paráfrasis: «Compara tiempo de build con un baseline reproducible».
Negativo: «Puntúa nuestros competidores» → S024; «comprueba aceptación» → qa.
No se midieron navegador, endpoints, builds ni CI.

**Coste, degradación e impacto.** Cargar solo modo y protocolo; tokens/latencia
null. Sin herramienta, dato de campo o ambiente autorizado, reportar pendiente,
sin resultado inventado. T-12 definirá collector/salida opt-in después de T-08;
T-14 comprobará parsing, condiciones, métricas ausentes y comparación real.
T-10/T-15 actualizarán activación, dependencias, panel y docs/exports ES/EN.

## S024 — Rúbrica de análisis competitivo

**Identidad y lectura.** SHA-256
`f24585262b9c3e106dc27d45f75c4b965501680a16ff6dc5a9995a53322549df`;
9.942 bytes/186 líneas; cuerpo completo, recursos locales 0/0.

**Contrato y valor.** Recibe brief, tensión estratégica y conjunto de
competidores. Define nueve dimensiones con pesos que suman 100: posición y
diferenciación (18), voz (15), craft (15), oferta (12), evidencia (12),
preparación empresarial (10), contenido (8), pricing (5) y tensión estratégica
(5). Conserva puntuaciones 1–5 con anclas y justificación por dimensión,
perfiles comparables y clasificación directa/adyacente/aspiracional.
Los pesos guían la síntesis, sin fabricar un score compuesto que oculte
fortalezas distintas. Las dos dimensiones de la tensión del cliente se
puntúan por separado para situar perfiles y objetivo en una matriz 2×2.

**Evidencia y defectos.** Contrastar webs, casos, capturas y señales externas;
distinguir claim de evidencia verificada y guardar fuente/fecha. La afinidad,
espectacularidad visual y supervivencia del conjunto pueden sesgar el análisis.
Calibrar anclas con el contexto del cliente, no imponer pesos de consultoría
enterprise a todo negocio. Una fuente inaccesible no equivale a una puntuación
de ausencia: unknown/null con límite de acceso. Definir umbrales de ejes y
proveniencia; no confundir posición deseada con posición acreditada.
No hay extractor ni ejecución de plataformas en el directorio.

**Comparación propia.** `research-first/references/comparison.md` ya conserva
fuentes, vigencia, compatibilidad y límites; no aporta la rúbrica comercial
ni la tensión estratégica con perfiles uniformes. El baseline técnico de S023
y el protocolo de outcome-evals no son esta capacidad. Analyst conserva el
brief y las decisiones de producto; architect/planner consumen conclusiones
con evidencia sin sustituir esos roles.

**Dependencias, decisión y destino.** S043 prepara plataformas/perfiles y S044
estructura el informe; sus secciones relevantes se leyeron, no se cuentan
evaluadas. **Conservar y actualizar** como referencia propuesta
`skills/competitive-analysis/references/profile-scoring.md`. El mapa y el
informe final se resolverán al comparar S028/S043/S044 en T-08. Preservar
dimensiones, pesos como semilla configurable, anclas, tensión, jerarquía de
pruebas y sesgos. No requerir cuentas, pagos ni contactos externos para activar
la capacidad, ni tratar un score editorial como medición técnica objetiva.

**Activación estática.** Literal: «Compara nuestra oferta con estos competidores».
Paráfrasis: «Qué posición podemos ocupar con evidencia de mercado».
Negativo: «Reduce el p95 del endpoint» → S023/S025. No se ejecutó investigación
de mercado, browser, login, ranking de clientes ni puntuación real.

**Coste, degradación e impacto.** Cargar rúbrica y fuentes relevantes;
tokens/latencia null. Sin brief/evidencia, registrar lo faltante antes de
sintetizar. T-10/T-11 armonizarán mapa, analyst y callers; T-14 debe verificar
anclas, unknown y citas con casos de evaluación pertinentes. T-15 docs/exports.

## S025 — Optimización por variantes medidas

**Identidad y lectura.** SHA-256
`f11208b6a86bc311cfbd9e20688a189238fda6c1e03b6f8000ef9e55487f6f95`;
2.658 bytes/71 líneas; cuerpo completo, recursos locales 0/0.

**Contrato y valor.** Pide operación, gate de corrección, métrica, baseline y
presupuesto de búsqueda. Cada variante cambia una hipótesis, conserva forma
de entrada y mide con comando reproducible; descarta resultados incorrectos,
inseguros o irreproducibles. Conserva tabla de hipótesis/comando/tiempo/
corrección/notas, promoviendo el mejor candidato válido y repitiendo contra
baseline. Detiene ruido, fallos repetidos o coste excesivo; documenta ganador,
rollback, comandos y límites, sin declarar óptimo global.

**Comparación y correcciones.** `outcome-evals` ya tiene baseline, repetición,
condiciones y validez, pero no protocolo explícito de búsqueda/promoción.
La palabra «más rápido» debe adaptarse a la métrica real: minimizar memoria
o coste, maximizar throughput y respetar restricciones adicionales. Declarar
objetivo, empates e incertidumbre; alternar orden/warmup/caché y validar el
ganador con datos de comprobación distintos cuando corresponda, para evitar
selección por ruido. No relajar aceptación o tests para ganar tiempo.
Consumo desconocido no permite declarar aplicado un tope monetario.
Terminar una búsqueda acotada no prueba completado el objetivo de producto.

**Dependencias, decisión y destino.** No hay harness local; comparte medición
con S023 y gates de pruebas existentes. **Ampliar** outcome-evals en la
referencia propuesta `skills/outcome-evals/references/measured-optimization.md`.
Conservar hipótesis, presupuestos, tabla, rechazo, promoción, repetición,
parada y rollback; compartir artefacto de rendimiento con S023. La tabla es
evidencia adjunta del ledger canónico, no otro gestor de tareas.

**Activación estática.** Literal: «Prueba variantes medidas de esta función».
Paráfrasis: «Optimiza este hotspot sin perder corrección dentro de un límite».
Negativo: «Limpia nombres sin problema de rendimiento» → implementación/revisión
habitual; «compara marcas» → S024. No se ejecutaron variantes ni mediciones.

**Coste, degradación e impacto.** Cargar protocolo y operación pertinente;
tokens/latencia null. Sin métrica o gate ejecutable, completar el contrato y
dejar la selección pendiente. T-10/T-12 definirán artefactos y activación tras
T-08; T-14 verificará rechazo, ruido, dirección de mejora y rollback con
medición real. T-15 sincronizará callers y docs/exports ES/EN.

## S026 — Inspección estructurada de movimiento en Blender

**Identidad y lectura.** SHA-256
`97b8aee8822a8603e2fc930f66b4bd18507c11ca756accd1419a2a3526196f5c`;
8.146 bytes/165 líneas; cuerpo completo, recursos locales 0/0.

**Contrato y valor.** Decide si un movimiento cumple antes de renderizar o
reconstruir la escena. Conserva inventario de mallas, rigs, proxies, padres,
modificadores, luces/materiales y objetos ocultos; bounds y escalas; huesos,
rest axes, cadenas y constraints; dirección/up/heading con varias señales;
muestreo de inicio, contacto, despegue, extremos y final, más denso ante
aterrizajes o giros. Diagnostica penetración, deslizamiento, cruce, torsión y
deriva con objeto/hueso/frame, valores y confianza. Mantener mesh/rig/skin/
materiales originales salvo reparación autorizada y registrar el baseline
antes de cualquier bake. Las capturas confirman
hallazgos después de extraer estado, no sustituyen coordenadas y evidencia.

**Recursos y vigencia.** El collector mencionado no aparece en el corpus.
Su CLI de ejemplo no demuestra que exista una herramienta operativa.
Importar bpy en Python común depende de una instalación como módulo; el
contrato de referencia debe partir del intérprete real de Blender.
Las páginas current devolvieron HTTP 403; no se contaron como APIs verificadas.
Se consultó en lectura el código oficial fijado v5.0.0:
[PoseBone](https://github.com/blender/blender/blob/v5.0.0/source/blender/makesrna/intern/rna_pose.cc),
[Object](https://github.com/blender/blender/blob/v5.0.0/source/blender/makesrna/intern/rna_object.cc),
[UnitSettings](https://github.com/blender/blender/blob/v5.0.0/source/blender/makesrna/intern/rna_scene.cc)
y [ejemplo Depsgraph](https://github.com/blender/blender/blob/v5.0.0/doc/python_api/examples/bpy.types.Depsgraph.1.py).
Es evidencia de contrato de esa revisión, no de versión instalada ni ejecución.

La matriz de pose está en espacio del objeto armature; bound_box está en
espacio de objeto y tiene sentinel cuando no existe. Transformar al espacio
de comparación, registrar unidades y usar geometry evaluada tras frame/
modificadores. Las tolerancias de centímetros, escala o grados por frame
requieren unit_scale, FPS, distancia entre muestras, referencia de suelo e
intención del movimiento. El vector cuello→cabeza puede describir up, no
forward: contrastar orientación, pies, axes y root antes de afirmar inversión.
Comparar lados sin considerar pose invertida o estilizada produce falsos
positivos; no borrar helpers ni reparar automáticamente una sospecha.

**Comparación propia.** `debug-root-cause` aporta reproducción, aislamiento y
evidencia, pero no estado geométrico. El contexto AST/grafo de código no extrae
animación; frontend-quality tampoco verifica rigs. Es una especialidad útil
del corpus, activada por tarea, sin imponer Blender al resto de proyectos.

**Decisión y destinos.** **Conservar y actualizar** como skill opcional propuesta
`skills/blender-inspection/SKILL.md` y
`skills/blender-inspection/references/motion-state.md`. El collector futuro de
T-12 debe declarar versión, escena/hash, frame/FPS, espacios/matrices, unidades,
muestreo, geometría evaluada, referencia de suelo, tolerancias y confianza.
Separar medición confirmada de sospecha y exportar resultados acotados sin
modificar assets. La normal/distancia de contacto evita asumir un suelo Z=0.

**Dependencias y activación estática.** Necesita escena y Blender compatible,
no un MCP supuesto. Literal: «Comprueba si este pie desliza en la animación».
Paráfrasis: «Inspecciona dirección y contacto del rig antes de renderizar».
Negativo: «Audita teclado en un formulario web» → frontend-quality/qa.
No se abrió escena, ejecutó bpy/collector, midió pose ni realizó render.

**Coste, degradación e impacto.** Cargar mapa, escena pertinente y muestras
acotadas; tokens/latencia null. Sin escena/herramienta, explicar qué falta y
no acreditar defectos ni corrección. T-10/T-12 definirán skill y collector
opt-in; T-14 necesita fixtures de espacios/unidades/pose/geometry/contactos.
T-13 mostrará disponibilidad declarada; T-15 docs, manifiestos y exports ES/EN.

## S027 — Planes por entregas que sobreviven al cambio de sesión

**Identidad y lectura.** SHA-256
`878eae8ed0ea4d46d21c8f88d471f6ffce7b0815202a43501060a163e7f446f3`;
5.153 bytes/97 líneas; cuerpo completo, recursos locales 0/0.

**Contrato y valor.** Convierte un objetivo grande en entregas y briefs que
pueden ejecutarse sin historial de conversación. Preflight de repo/Git/
herramientas, dependencias, archivos afectados, aceptación y comprobaciones
exactas por entrega; tamaño orientativo de 3–12 pasos, tier según complejidad,
rollback y revisión del plan. Conserva modificación explícita de plan:
insertar, dividir, reordenar, omitir o abandonar con motivo y efecto en
dependencias. El artefacto debe permitir retomar trabajo desde cero contexto.

**Defectos y consumidores.** Son instrucciones Markdown que proponen ejecutar
Git/CLI/modelos y modificar archivos: «riesgo runtime cero» no queda probado
por el formato. El corpus incluye scripts; tampoco es correcto generalizar
que todo el repo es Markdown. No hay detector ni protocolo de mutación
ejecutable detrás de las fases escritas. S217 selecciona esta guía como skill,
no como comando; una invocación slash depende del host y no demuestra un
commands entrypoint portable. La falta de gh no debe impedir planificar;
la alternativa directa necesita conservar trazabilidad y aceptación.

**Comparación propia.** `agents/planner.md` ya produce plan/tasks canónicos,
dependencias, verificación, aceptación y documentación; su plantilla admite
selección explícita. `dev-cycle` transporta tarea y criterios en el brief y
aplica revisión/QA. `knowledge-write` exige curación: registrar un plan no
autoriza volcarlo automáticamente a memoria aceptada. Faltan instrucciones
uniformes para mutar planes entre sesiones y delimitar varias entregas/PR
sin abrir otro árbol plans ni sustituir el ledger.

**Decisión y destinos.** **Ampliar** `agents/planner.md`,
`agent-kits/planner/templates/tasks.md` y el método de briefs existente.
Conservar preflight, contexto mínimo, entregas cohesionadas, tiers, verificación,
rollback y revisión; IDs estables, razón del cambio y dependencias revalidadas.
Distinguir cancelación autorizada, trabajo hecho y nueva previsión, sin borrar
evidencia anterior. No añadir otro agente planner, comando paralelo o memoria
automática; no imponer un número de pasos ni contar tools como estimador de
riesgo. El ciclo existente sigue siendo dueño de gates y publicación.

**Activación estática.** Literal: «Divide esta migración en entregas ejecutables».
Paráfrasis: «Prepara un plan que podamos retomar en otra sesión».
Negativo: «Arregla esta línea con solución conocida» → vía rápida existente.
No se invocó planner, revisión de agentes, GitHub ni ejecución de un plan.

**Coste, degradación e impacto.** Cargar solo contexto y entrega pertinente;
tokens/latencia null. Sin remoto/gh, plan local y límites claros; conservar
verificación y no hacer publicación implícita. T-11 deberá unificar plantilla,
planner, callers y prompts por runtime; T-14 comprobará cambio de dependencias,
reanudación sin historial y briefs con presupuesto. T-15 actualizará docs y
exports ES/EN, retirando instrucciones de flujos sustituidos tras su validación.

## Cobertura y siguiente decisión

Los siete cuerpos tienen todos sus criterios útiles asignados a destinos;
las referencias nuevas siguen siendo diseño propuesto. La inspección del
helper de sesiones es dependencia de S021 y no cierre del inventario operativo
T-06. S030/S032/S043/S044/S052 y callers leídos no se suman a las siete fichas.
La matriz global T-08 decidirá el reparto después de completar T-03/T-04/T-05/
T-06/T-07. Las comprobaciones de hashes, enlaces, ledger e índice acreditan
trazabilidad y coherencia documental; no eficacia, dispatch ni rendimiento.
