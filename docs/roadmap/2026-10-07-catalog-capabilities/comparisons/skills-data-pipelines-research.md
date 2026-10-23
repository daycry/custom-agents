# Datos, rendimiento, migraciones e investigación — S069–S072

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Los cuatro cuerpos suman **46.443 bytes y 1.450 líneas**; ninguno tiene recursos
locales en su directorio. Los ejemplos de archivos no equivalen a archivos
entregados. [data-research-reading-evidence.json](data-research-reading-evidence.json)
registra hashes y rangos de cuerpos, consumidores y contrapartes, reutilizaciones
con hash idéntico y contrastes oficiales. Los nombres originales permanecen en
el mapa privado. El ledger canónico sigue siendo [tasks.md](../tasks.md), T-03.

Los destinos son **propuestas para T-08**, sin integración de producción en este
bloque. Se leyeron fuentes y ejemplos; no se ejecutaron scripts, tests o CLI del
corpus, migraciones, colectores ni operaciones autenticadas de MCP. Los casos
de activación y regresión siguientes son checks estáticos preparados, no runs.

## S069 — Recolección y enriquecimiento de datos

**Identidad y lectura.** SHA-256
`662e884d58f4089bd8e090ef8d32042b85a5d9b4715906a89072002704451c0a`,
25.520 bytes, 776 líneas, cuerpo completo y cero recursos locales. La búsqueda
en agentes, comandos, skills y reglas canónicos no encontró referencias por
su nombre; eso no demuestra uso cero. Se comparó S022 como dependencia de
backend con lectura completa reutilizada. No se atribuye ejecución a plantillas.

**Contrato y valor.** Orienta la construcción de una aplicación que recolecta
fuentes públicas, normaliza registros, los enriquece opcionalmente y los guarda.
La separación colectar → enriquecer → almacenar facilita adaptadores, filtros,
deduplicación y programación. Su feedback permite proponer preferencias para
otra ejecución; no demuestra entrenamiento ni mejora medida de un modelo.
La salida pertenece al proyecto consumidor, no al almacén de memoria del plugin.

**Comparación propia.** `backend-practices` y `contracts-data.md` ya cubren
idempotencia, paginación, errores remotos y coexistencia de versiones. No dan
el recorrido de fuentes HTML/RSS/JSON ni el contrato de enriquecimiento por
registros. `delivery-practices` conserva operación y autorización. La lectura
de `training-data-services` se limita a líneas 1–90: opt-in, store externo,
redacción y aprobación humana de Gold; no se revalidaron aquí sus scripts.
Knowledge Gate conserva la aprobación del conocimiento. Ninguno de esos
mecanismos convierte preferencias externas en doctrina aceptada automáticamente.

**Defectos y límites observados.**

| Observación del ejemplo | Contrato que debe conservar la integración |
|---|---|
| El árbol describe setup, backfill y sincronización de feedback que no entrega; main solo implementa el destino Notion | Diferenciar ejemplos, adaptadores implementados y funciones pendientes; no anunciar soporte operativo de Sheets/Supabase/SQLite por nombrarlos |
| HTTP no exitoso puede producir lista vacía; selectors ausentes o JSON de otra forma fallan sin el mismo tratamiento | Separar vacío válido, extracción parcial y error; validar estructura y reportar cada fuente |
| Requests tiene timeout por petición, pero no límite total de descarga; paginación y cuerpo no tienen presupuesto global | Acotar bytes, registros, páginas, redirects y deadline; progreso reanudable y cancelación |
| Construye URLs con prefijos de string y sigue redirects; HTML y contenido del modelo son datos externos | Resolver URLs y validar origen/esquema por salto; una página no concede acceso, envío ni autoridad sobre el workflow |
| `ai_enabled()` solo comprueba una clave y no respeta `ai.enabled`; respuesta ausente permite guardar registros sin score | Distinguir desactivado, no disponible, fallo y resultado válido; definir qué permite el dominio sin enriquecimiento |
| Arrays vacíos, tipos de score inválidos o respuestas reordenadas rompen el parsing o la asociación por posición | Validar cardinalidad, tipos y valores; vincular resultados por ID estable, sin atribuir texto a otro registro |
| El timestamp de rate limit no cubre cada request del fallback; espera fija y modelos predefinidos | Cuotas por proveedor/proyecto, retry acotado, modelo/configuración vigente y reserva de coste antes de llamar |
| Dedup carga todas las URLs y mantiene un set local; fallos de escritura se cuentan como saltos existentes | Identidad durable y concurrencia, estado de checkpoint y evidencia por escritura; duplicado no equivale a error |
| El feedback no se sincroniza desde main; JSON corrupto se reinicia y el workflow intenta guardarlo en Git | Persistencia acotada, recuperación visible y privacidad elegida por el proyecto; no publicar historial o contexto personal por defecto |

**Dependencias por versión.** La plantilla fija librerías Python, usa Gemini,
Notion y GitHub Actions; no son dependencias globales del plugin. La fuente del
SDK Notion **2.2.1** fija `Notion-Version: 2022-06-28`, por lo que no se declara
inválida toda llamada antigua a databases. El contrato actual distingue data
sources y advierte fallos de versiones previas con bases de múltiples fuentes.
La lectura fallida del tag con prefijo `v` y su sustituto válido están separados.
[SDK 2.2.1](https://github.com/ramnes/notion-sdk-py/blob/2.2.1/notion_client/client.py),
[migración Notion](https://developers.notion.com/guides/get-started/upgrade-guide-2025-09-03).

Los modelos Gemini 2.0 Flash/Lite del fallback tienen cierre documentado el
1 de junio de 2026. Las cuotas dependen del proyecto/modelo/tier y el JSON
estructurado requiere validación semántica de la aplicación. El tier gratuito
tiene condiciones de uso de contenido distintas del pagado; no se conserva
la promesa universal de producción gratuita.
[Deprecaciones](https://ai.google.dev/gemini-api/docs/deprecations),
[límites](https://ai.google.dev/gemini-api/docs/rate-limits),
[outputs](https://ai.google.dev/gemini-api/docs/structured-output),
[precios](https://ai.google.dev/gemini-api/docs/pricing).

Notion documenta presupuestos por conexión y workspace con `Retry-After`;
no se fija un número universal en la guía.
[Request limits](https://developers.notion.com/reference/request-limits).
Un timeout Requests no limita toda la descarga.
[Requests](https://requests.readthedocs.io/en/latest/user/quickstart/).
Los schedules de Actions pueden retrasarse o perderse y dependen de la rama
por defecto; en repos públicos se desactivan por inactividad. La gratuidad de
runners estándar públicos no cubre toda configuración ni almacenamiento.
[Schedules](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
[facturación](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

**Decisión y destino.** Adaptar como guía opcional
`skills/data-collection/SKILL.md`, con `references/source-contracts.md`,
`references/enrichment-storage.md` y `references/feedback-operations.md`.
Compartir retries, presupuesto y cache con la propuesta de pipeline LLM de
S056; no crear otro agente permanente ni otro backend de memoria. El proyecto
elige fuentes, destino y proveedor. T-12 resolverá adaptadores concretos después
del diseño, sin instalar paquetes ni servicios a todos los consumidores.

**Activación preparada.** Literal «Crea un colector diario de estas fuentes»;
paráfrasis «Extrae y normaliza las oportunidades y guárdalas». Negativo
«Compara qué mercado conviene» → investigación/criterios de negocio, sin
inventar un colector. «Mi importador va lento» → S070. Main, archivos y destino
de una aplicación se asignan a implementer; qa verifica sus efectos.

**Casos pendientes T-14.** Respuesta vacía frente a 500; redirect fuera del
origen; paginación repetida; bytes/deadline agotados; AI apagada pese a tener
clave; lista vacía/reordenada/score inválido; 429 durante fallback; escritura
aceptada con timeout; dos workers con misma identidad; feedback corrupto;
fuente caída y otras válidas; cambio de API y reanudación tras cancelación.

**Coste e impacto.** Cuerpo y referencias bajo demanda; tokens/latencia null.
El número de requests, filas o modelos depende del presupuesto autorizado.
T-08/T-10 actualizarán routing y contenidos; T-11 sus consumidores futuros;
T-12 herramientas y T-14/T-15 casos, docs y exports. No se guarda automáticamente
el output en conocimiento ni en training; cada puerta conserva su autoridad.

## S070 — Rendimiento de pipelines con contabilidad de datos

**Identidad y lectura.** SHA-256
`59e98c2c2871627ee42984a1509da0d2c3e92d80b10b04d4f93338e5e0c9b0d6`,
2.832 bytes, 74 líneas, cuerpo completo, cero recursos locales. No se encontraron
callers por nombre en las áreas canónicas inspeccionadas. El frontmatter lista
tools, pero no constituye disponibilidad o autorización en otro runtime.

**Contrato y contenido único.** Diagnostica movimiento de datos con backlog
y destino explícitos. Separa extracción, red, carga, transformación, frescura
de serving y crecimiento del tail mientras corre el job. Contrasta batching,
workers, agrupación de archivos, SQL cercano al dato, staging, partición y
actualización de manifest; vuelve a comprobar contabilidad después de codificar
la variante en el job real. El bloque de 294 archivos y 38,7 segundos es un
ejemplo ilustrativo, no una medición del plugin o de este repositorio.

**Comparación propia.** `backend-practices/references/contracts-data.md`
aporta idempotencia, transacciones y backfill reanudable, pero no localiza
cuellos de botella por etapa ni diferencia tail de histórico.
`outcome-evals/SKILL.md` y `references/protocol.md` ya fijan corpus, baseline,
condiciones/repeticiones, resultados ausentes y autoridad de qa. Su agregador
JUnit no valida filas de una base ni calcula métricas de dominio. La referencia
propuesta añade criterios de datos sin crear otro método de benchmarks.

**Correcciones necesarias.** Igual número de filas y timestamps máximos no
prueba corrección: pérdidas y duplicados pueden compensarse; updates o valores
erróneos conservan ambos contadores. Un filtro/agregado legítimo tampoco tiene
por qué conservar cardinalidad. Definir por dominio identidad, transformación,
aceptados/rechazados/fallos, invariantes y reconciliación, con evidencia de replay.
Manifests necesitan identidad/versiones y coherencia de commit con la escritura;
tener un archivo con ese nombre no proporciona atomicidad.

La comparación necesita snapshot o high-watermark explícito por partición,
late arrivals y zona horaria. Registrar instante de readback y separar backlog
de la ventana histórica del tail vivo. Un muestreo rápido no acredita el job
completo bajo otra carga, cache o concurrencia. Conservar fallos de archivos,
coste, recursos y calidad al promover una variante; no borrar raw para mejorar
los números. Aprobaciones concretas dependen del proyecto y trabajo autorizado.

**Decisión y destinos.** Consolidar en
`skills/backend-practices/references/pipeline-throughput.md`, enlazada solo para
ingestión, exportación, ETL o backfill. Reutilizar `outcome-evals` para condiciones
y informe comparable; añadir métricas opacas o evidencia de dominio sin inventar
un runner de warehouse ni duplicar case store. El proyecto implementa su job;
qa conserva el resultado y delivery-practices prepara la operación posterior.

**Activación preparada.** «Acelera este backfill manteniendo los datos»;
«El destino se queda atrasado aunque procesamos muchos archivos». Negativo
«Optimiza una pantalla Flutter» → guía frontend pertinente. «Añade un campo
obligatorio a producción» → S071. «Construye un colector nuevo» → S069 y después
la comparación de rendimiento cuando exista baseline.

**Casos pendientes T-14.** Dos variantes con distinta ventana; pérdida y
duplicado con mismos contadores; rechazo legítimo; actualización sin cambio
de max timestamp; llegada tardía; checkpoint adelantado al commit; reintento
de partición; fallo parcial; worker rápido con coste mayor; sample versus job
completo. No se ejecutaron benchmarks, queries ni conciliaciones aquí.

**Carga e impacto.** Método sin imports ni dependencias ejecutables entregadas;
2.832 bytes bajo demanda, tokens/latencia null. T-08/T-10 ajustarán triggers y
referencias compartidas sin añadir un agente; T-11 mapeará consumidores y
T-14/T-15 verificará casos, routing, documentación y exports.

## S071 — Migraciones y despliegues de datos compatibles

**Identidad y lectura.** SHA-256
`dad2f1964295eee14a96e06213ce3f60992bbcdc1f37a50c828bbc2e1abd79dd`,
12.034 bytes, 430 líneas, cuerpo completo y cero recursos locales. Callers
pertinentes leídos: A016, S176, S180, S211, S217 y S234; el JSON delimita rangos.
Son referencias de revisión, persistencia, selección de guías y tooling. No se
consideran evaluados los cuerpos completos de esas piezas por leer su caller.

**Contrato y contenido útil.** Versiona evolución de esquema/datos, conserva
migraciones ya desplegadas y prepara cambios compatibles con lectores y
escritores coexistentes. Aporta ejemplos PostgreSQL y recorridos particulares
de Prisma, Drizzle, Kysely, Django y golang-migrate; backfill, orden de despliegue,
verificación y recuperación requieren evidencia del motor/runner del proyecto.
El consumidor conserva la base y sus migraciones; no se modifica desde un hook.

**Comparación propia.** `backend-practices` ya activa con «revisa una migración»
y su referencia cubre expandir → desplegar compatibilidad → backfill verificable
→ adopción → contraer, ensayo representativo y diferencia down/restauración.
`delivery-practices` conserva readiness/operación; planner, revisión y qa siguen
siendo dueños del plan, defectos y veredicto. El delta son herramientas concretas,
locks, defaults, estado dirty y contratos de backfill, no otro ciclo de despliegue.

**Correcciones verificadas.** PostgreSQL 18 documenta `ACCESS EXCLUSIVE` por
defecto para ALTER TABLE; un nullable o default no volátil puede evitar rewrite
sin eliminar ese lock. Concurrent index exige fuera de transaction block, espera
transacciones y puede dejar índice inválido. `IF NOT EXISTS` solo comprueba
nombre, no equivalencia del índice. No conservar «sin lock» o «siempre instantáneo».
[ALTER TABLE](https://www.postgresql.org/docs/18/sql-altertable.html),
[CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html).

| Ejemplo o regla a adaptar | Cambio requerido |
|---|---|
| Primer ejemplo de rename hace backfill antes de introducir dual writing | Desplegar compatibilidad antes; reconciliar escritores antiguos, jobs y registros creados durante el backfill antes de cambiar lectura/contraer |
| DO por lotes incluye COMMIT | Verificar ejecución top-level y límites del runner; dentro de otra transacción no asumir que puede confirmar cada lote |
| `SKIP LOCKED` con cero filas se interpreta como final | Distinguir filas ocupadas de trabajo terminado; reintentar/verificar ventana y conservar cursor/checkpoint |
| Normalización de email NULL mantiene el predicado de pendiente | Definir entradas inválidas, progreso y terminación; no reejecutar para siempre filas que no pueden normalizarse |
| Django usa batches dentro de Migration sin desactivar atomicidad; calcula alias pero usa manager por defecto | Acotar transacciones realmente, usar alias/modelos históricos y comprobar NULL/cadena vacía con entradas que no cambian |
| Reverse vacío o down que elimina datos se trata como rollback seguro | Declarar pérdida/irreversibilidad y plan de recuperación real; un retorno sin error no restaura datos |
| Archivo golang-migrate mezcla ALTER y CREATE INDEX CONCURRENTLY | Separar la operación concurrente o comprobar multi-statement mode y límites; el modo por defecto ejecuta el archivo completo en un Exec |
| `force VERSION` se propone ante dirty | Solo cambia metadata de versión: investigar efecto aplicado, reparar/reconciliar y después decidir la versión; no usar como reparación de datos |

Control transaccional DO requiere condiciones documentadas; múltiples statements
de un Query simple se ejecutan en transacción implícita salvo control explícito.
[PL/pgSQL](https://www.postgresql.org/docs/18/plpgsql-transactions.html),
[protocolo](https://www.postgresql.org/docs/18/protocol-flow.html).
Django 6.0 documenta `atomic=False` para lotes fuera de la transacción global y
alias de conexión; eso no acredita el ejemplo con todas las bases.
[Migraciones Django](https://docs.djangoproject.com/en/6.0/howto/writing-migrations/).
El README y el driver PostgreSQL leídos de golang-migrate confirman la diferencia
entre split y archivo completo. Son snapshots actuales, no prueba de la versión
instalada en un consumidor.
[Driver](https://github.com/golang-migrate/migrate/blob/master/database/postgres/README.md),
[Run](https://github.com/golang-migrate/migrate/blob/master/database/postgres/postgres.go),
[CLI](https://github.com/golang-migrate/migrate/blob/master/cmd/migrate/README.md).

**Versiones y herramientas.** No se copian comandos como universales. La
documentación actual de Prisma contrasta `migration plan`/`db migrate` con
los `migrate` de ORM 7 que usa el ejemplo; mantener la guía de la versión real,
sin imponer upgrade. Drizzle distingue generate/migrate y otras estrategias,
pero su overview no demuestra atomicidad de cada runner. Kysely-ctl requiere
configuración y documenta provider, cleanup y límites de rollback. Consultar
motor, runner, versión y código generado antes de aplicar SQL.
[Prisma](https://www.prisma.io/docs/orm/migrations/how-migrations-work),
[Drizzle](https://orm.drizzle.team/docs/migrations),
[Kysely-ctl](https://github.com/kysely-org/kysely-ctl/blob/main/README.md).

**Decisión y destinos.** Ampliar
`skills/backend-practices/references/database-migrations.md` y
`references/migration-tools.md`, manteniendo `contracts-data.md` como contrato
compartido. S070 aporta reconciliación del backfill, no autoridad para ejecutarlo.
Delivery enlaza preparación/adopción/restauración sin duplicar el método.
Los ejemplos de los cinco toolchains son opcionales y bajo demanda; no se
añaden ORM ni paquetes obligatorios al proyecto o al plugin.

**Activación preparada.** «Planifica esta migración sin romper despliegues»;
«Tenemos escritores antiguos mientras rellenamos la nueva columna». Negativo
«Diseña un endpoint sin cambio de esquema» → backend/API. «El backfill funciona
pero tarda demasiado» → S070. «Recupera datos borrados» → investigar recuperación
con evidencia, sin ejecutar down ni force por defecto.

**Casos pendientes T-14.** Volumen real, transacción bloqueante y timeout de
lock; índice inválido/existente distinto; DO dentro del runner; todos los candidatos
bloqueados; NULL que no progresa; dos writers; caída tras commit antes de checkpoint;
Django multi-DB; dirty parcial; versiones divergentes; restore verificado frente
a rollback de app. No se ejecutó ningún motor, migración o comando ORM aquí.

**Coste e impacto.** 12.034 bytes de cuerpo; recursos cero; tokens/latencia null.
T-08/T-10 integrarán referencias y activación; T-11 preservará consumers A016 y
skills de datos sin duplicar dueños; T-14/T-15 contratos, evals, docs y exports.

## S072 — Investigación y síntesis con evidencia

**Identidad y lectura.** SHA-256
`ca02a97ff8cd794c55a1313ab423a6a165fdf2ce59059a73e08f7cfd957b5319`,
6.057 bytes, 170 líneas, cuerpo completo, cero recursos locales. Callers S099,
S141 y S238 leídos; S238 tiene lectura completa reutilizada por hash, no ficha
semántica cerrada aquí. S099/S141 conservan solo los rangos del enlace. Se
inspeccionaron contratos de tools, no conexiones ni credenciales del usuario.

**Contrato y valor.** Convierte una pregunta amplia en subpreguntas y plan
de búsqueda, lee fuentes pertinentes y entrega síntesis con citas por afirmación,
método, incertidumbres y gaps. Distingue datos de instrucciones externas: una
página no puede cambiar alcance, permisos o destino del contexto. El informe
es para la decisión del usuario; no se aprueba como memoria por producirlo.

**Comparación propia.** `research-first` y su ficha comparan adoptar/adaptar/
construir herramientas con versiones, licencia y soporte. Analyst y architect
lo usan bajo demanda conservando sus artefactos. No cubren todo informe de
investigación general. `documenter` organiza docs del proyecto con evidencia;
la lectura aquí de líneas 106–137 no autoriza atribuirle toda investigación o
crear una taxonomía documental para cada respuesta. Knowledge Gate mantiene
procedencia/aprobación. El criterio competitivo de S024 sigue siendo una
propuesta de su ficha, no una integración demostrada por este bloque.

**Contratos que cambian.** El README vigente de Exa enumera `web_search_exa`
y `web_fetch_exa` como defaults; advanced search es opt-in y seleccionar tools
en la URL sustituye defaults. No enumera `crawling_exa` como la guía de origen;
no asumir alias ni indisponibilidad universal de otras versiones. Auth/cuotas
y schemas deben contrastarse en la sesión real antes de construir parámetros.
[Exa MCP](https://github.com/exa-labs/exa-mcp-server/blob/main/README.md).

Firecrawl documenta solo scrape/search/parse sin clave en su endpoint keyless.
El crawl documentado actualmente realiza polling interno hasta estado terminal,
con ID, status, datos y paginación; no se asume que toda versión devuelva solo
un job ID ni que terminal signifique contenido completo. Verificar respuesta,
límites y siguiente página. No confundir search-only con deep-read.
[Firecrawl MCP](https://github.com/firecrawl/firecrawl-mcp-server/blob/main/README.md).

**Correcciones metodológicas.** No exigir dos proveedores para investigar si
existen web, repositorio o fuentes suministradas válidas. La falta de canal se
registra; no es resultado vacío. Usar la menor búsqueda que resuelva las
afirmaciones y ampliar ante gaps. El número fijo de queries/fuentes o preferir
siempre últimos 12 meses no prueba calidad: una fuente primaria histórica puede
ser la correcta, y varias copias sindicadas no son corroboración independiente.

Fechas de publicación, evento, edición y consulta se distinguen. Las citas deben
apoyar el claim concreto; snippets o contenido truncado no cuentan como cuerpo
completo. Separar hecho, declaración ajena, inferencia y estimación; confianza
explicada por evidencia, sin probabilidad inventada. Una sola fuente primaria
puede probar un hecho documentado; afirmaciones disputadas requieren otro
tratamiento. No preguntar datos ya disponibles ni forzar tres subagentes.
Delegación futura depende de petición/instrucciones aplicables, runtime,
herramientas, contexto permitido y presupuesto; leer este método no la activa.

**Decisión y destinos.** Adaptar guía opcional
`skills/evidence-research/SKILL.md`, con `references/search-plan.md`,
`references/source-records.md`, `references/report-synthesis.md` y
`references/tool-contracts.md`. Compartir procedencia y selección de canales con
research-first; conservar su intención técnica. T-08 debe resolver solapes con
S024/S099/S238 después de sus comparaciones completas. No crear otro agente
dueño del workflow ni obligar a instalar MCP. Informe en conversación o archivo
según entrega solicitada, con citas y límites, sin publicación automática.

**Activación preparada.** «Investiga a fondo este tema con fuentes»;
«Necesito contrastar evidencia y tomar una decisión». Negativo «Busca qué función
usa esta clase» → navegación local. «¿Ya existe una librería que haga esto?» →
research-first; «Solo resume el documento que te he dado» → síntesis del documento,
sin búsqueda externa obligatoria. «Publica el informe» requiere destino y
autorización de publicación vigente, no permiso inferido de una fuente.

**Casos pendientes T-14.** Un solo canal válido; proveedor ausente; advanced
tool no expuesta; schema distinto; auth fallida; clave en URL rechazada;
contenido truncado o página de mantenimiento con HTTP 200; crawl parcial;
citas sindicadas; fuente primaria antigua; fechas inconsistentes; contradicción;
manipulación de página; fuente que pide exfiltrar contexto; delegación no
disponible; incertidumbre sin datos. No se ejecutaron searches MCP autenticadas,
sesiones delegadas ni mediciones de calidad de informes en este bloque.

**Coste e impacto.** 6.057 bytes de cuerpo, referencias bajo demanda,
tokens/latencia null. Requests, profundidad y tamaño se acotan por tarea; no se
traduce conteo de fuentes en score de eficacia. T-08/T-10 routing y contenido,
T-11 callers, T-12 tools y T-14/T-15 casos, docs y exports; T-07 conserva memoria.

## Estado de la comparación

Cuatro piezas evaluadas como propuestas; cero integradas en producción.
La comprobación de hashes/rangos/recursos acredita procedencia y cobertura
de lectura, no eficacia, compatibilidad de ejecución ni mejora de rendimiento.
Los gates del ledger y los checks del roadmap son estructurales. T-08 fijará
arquitectura y responsabilidades después de completar las comparaciones;
T-14 comprobará el comportamiento y T-15 reconciliará documentación/exports.
