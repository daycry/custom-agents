# Comparación de selección, evaluación y flujos de agentes

Fichas S006–S012, revisión `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Decisiones y destinos **propuestos**, todavía sin integración de producción.
El progreso canónico está en [tasks.md](../tasks.md), T-03; T-08 decidirá el
diseño conjunto tras la comparación completa. Esta entrega complementa
[skills-foundations.md](skills-foundations.md).

Se leyeron los siete cuerpos completos y los seis recursos locales de S007.
Los otros seis directorios contienen solo su cuerpo. Se inspeccionaron los
consumidores pertinentes en agentes, skills y manifiestos canónicos; los
adaptadores y generadores operativos completos siguen en T-06. La evidencia
de [workflow-reading-evidence.json](workflow-reading-evidence.json) distingue
cuerpos, recursos y secciones de consumidores. Una lectura parcial no equivale
a evaluar semánticamente otra pieza. Ningún código del corpus fue ejecutado.

## S006 — Pagos de APIs por agentes

**Identidad.** SHA-256
`78ac50508665d894f1cbf02fe7d121c6ffc5c72cc66d68174db77ffdb30b6b89`;
10.715 bytes/225 líneas, cuerpo completo; recursos locales: ninguno.

**Contrato y dueño.** Distingue comprar acceso a una API que responde HTTP 402
de cobrar como proveedor. Produce un diseño de negociación, límites y recibos,
o una integración específica autorizada. Architect define política y límites;
implementer desarrolla el cliente o servidor; qa verifica estados y fallos.
La configuración de privilegios permanece en el orquestador autorizado, fuera
de la autonomía del agente que consume el presupuesto.

**Valor y defectos.** Aporta presupuesto por tarea/sesión, destinatarios
permitidos, límites de frecuencia, testnet y separación entre pagador y vendedor.
El ejemplo comprueba coste finito, rechazos del servidor y saldo antes de actuar,
pero no implementa el pago ni una reserva atómica: dos llamadas concurrentes
pueden aprobar el mismo saldo. Tampoco cierra el cliente en un finally, define
unidades monetarias exactas o resuelve la relación dominio/destinatario. No puede
presentarse como protección completa frente al gasto concurrente. La afirmación
de ausencia de riesgo por usar una cartera no custodial es demasiado amplia.

El ejemplo propone arrancar un MCP con `npx agentwallet-sdk@6.0.0`.
La [metadata oficial de esa versión](https://registry.npmjs.org/agentwallet-sdk/6.0.0)
no declara `bin`; HTTP 200 y hash del documento están registrados. npm infiere
el ejecutable mediante ese campo y falla si no obtiene uno, según su
[contrato de npm exec](https://docs.npmjs.com/cli/v11/commands/npm-exec/).
Por tanto ese comando no acredita un servidor MCP ejecutable. No se instaló ni
ejecutó el paquete; tampoco se comprobó el esquema real de las tools enumeradas.
La alternativa del proveedor mantiene un flujo cotización/pago y rutas de
vendedor en su [dispatcher oficial](https://raw.githubusercontent.com/okx/onchainos-skills/main/skills/okx-agent-payments-protocol/SKILL.md),
versión declarada 4.6.3. Los contratos especializados de esas rutas siguen sin
validación ejecutada. El protocolo conserva sus identificadores técnicos;
adaptar la guía no significa renombrar headers ni inventar una API compatible.

**Comparación propia.** `delivery-practices/references/delivery-tools.md`
ya exige esquema MCP real, privilegios mínimos, configuración del runtime,
redacción y distinción entre declaración y conexión. `backend-practices/`
«Contratos y datos» aporta idempotencia, concurrencia y operación durable.
Ninguno desarrolla negociación HTTP 402, pagador/vendedor ni política de gasto
delegado; ese contenido es una especialidad distinta presente en el corpus.

**Dependencias y consumidores.** R-591e7a1672e1 y R-03ffcc8e6e9e distribuyen
la pieza; no acreditan llamadas. Dependencias externas: protocolo, SDK/servidor
real, cartera, red y proveedor. Las guías de vendedor enlazadas son continuaciones
por lenguaje, no seis recursos locales ni implementaciones ya auditadas.

**Decisión y destino.** **Actualizar**, como capacidad opcional propuesta
`skills/agent-payments/`, con método común y referencias de proveedor bajo demanda.
Conservar comprador/vendedor, cotización, presupuesto, destinatarios, testnet,
privilegios separados y recibos. Añadir unidades exactas, reserva/idempotencia,
estados terminales y cleanup antes de ofrecer código operativo. Reutilizar los
contratos MCP y backend existentes. No instalar una cartera ni conectar servicios
por discovery; el dominio no se impone a otros proyectos.

**Activación estática.** Literal: «Integra pagos HTTP 402 en esta API».
Paráfrasis: «Necesito que este agente compre acceso con un límite por tarea».
Negativo vecino: «Calcula el gasto de tokens de la sesión» → observabilidad y
tarifas, sin pagos. No se ejecutó el selector ni una sesión de pago.

**Carga y degradación.** 10.715 bytes/225 líneas, recursos locales 0/0;
cargar solo la ruta comprador/vendedor pertinente. Tokens/latencia: null.
Sin proveedor o contrato validado, entregar diseño y requisitos pendientes,
sin afirmar pago, conexión, custodia segura o protección presupuestaria efectiva.

**Validación e impacto.** Lectura/hash y consultas oficiales el 2026-10-07;
sin instalación, claves, acceso a carteras, transacciones ni modelo externo.
T-08 decidirá el destino; T-12 verificará API/configuración y fixtures aisladas,
T-14 los límites reales y T-15 docs, dependencias y exports ES/EN.

## S007 — Evaluación de la calidad de un entregable

**Identidad.** SHA-256
`96bb21eb37760f596789f84ec0a5dad4ef92fc2255e35cd7b88dc4234062b8c1`;
7.625 bytes/182 líneas. Recursos locales, leídos completos:

| ID | Función | Bytes | Líneas |
|---|---|---:|---:|
| R-dacf97dafeeb | Ejemplo de puntuación alta | 3.545 | 87 |
| R-4a22d54c38f8 | Ejemplo de puntuación baja | 3.702 | 86 |
| R-3146d80e35e9 | Criterios de evaluación | 5.820 | 71 |
| R-27db0a027721 | Ejemplo de recordatorios mediante hooks | 2.500 | 64 |
| R-e4f5a09c931a | Evaluador heurístico Python | 14.975 | 408 |
| R-bf0243814165 | Plantilla de informe | 3.485 | 86 |

Recursos: 34.027 bytes/802 líneas; cuerpo más recursos: 41.652 bytes/984 líneas.
Los hashes completos están en la evidencia enlazada; el script no se ejecutó.

**Contrato y dueño.** Evalúa precisión, completitud, claridad, posibilidad de
actuar y concisión del resultado, con evidencia por dimensión y cambios concretos.
El autor mejora la entrega; reviewer conserva la revisión y qa las pruebas.
La evaluación del resultado no crea un segundo propietario de la implementación.

**Valor y defectos.** La rúbrica de cinco ejes distingue un resultado usable de
una descripción prolija y pide no ampliar alcance por gusto del evaluador.
Sin embargo el script parte de precisión 5 sin verificar hechos; puede otorgar
completitud 5 sin valorar los requisitos de la tarea. La tarea solo participa
en la heurística de concisión. Frases inglesas que afirman pruebas o verificación
se puntúan sin comprobar artefactos; reconocer límites puede bajar una nota.
La relación longitud petición/respuesta y el promedio final no demuestran calidad
semántica. La recomendación automática de entregar sin cambios queda invalidada
por esos supuestos, no por la ausencia de logs de uso.

El ejemplo alto atribuye reintentos de 429/5xx al transporte HTTPX y backoff a
Limits. Los [reintentos documentados del transporte](https://www.python-httpx.org/advanced/transports/)
son para ConnectError/ConnectTimeout; [Limits](https://www.python-httpx.org/advanced/resource-limits/)
configura el pool de conexiones. Las cifras de tests del ejemplo son texto,
no resultados ejecutados. Debe corregirse antes de usarse como ejemplo de calidad.

Los hooks propuestos imprimen un recordatorio en Stop y PostToolUse/Bash.
No ejecutan la evaluación. Además, el stdout plano con exit 0 de esos eventos
no se añade al contexto del modelo según el
[contrato actual de Claude](https://code.claude.com/docs/en/hooks).
No trasladar ese echo como activación efectiva ni añadir un hook global por cada
comando Bash. La configuración nativa y entrega real de mensajes necesitan prueba.

**Comparación propia.** `outcome-evals/references/protocol.md`, «Definir antes
de ejecutar» y «Registrar y comparar», ya separa juicio auxiliar de evidencia
ejecutable y fija criterios antes de observar resultados. No incluye esta rúbrica
de comunicación/entregabilidad. `adversarial-review` revisa defectos y conformidad;
no debe convertirse en un promedio que permita compensar un fallo crítico.

**Dependencias y consumidores.** A002 invoca la rúbrica y produce un informe
de cinco ejes; se leyó su cuerpo completo, pero su ficha semántica de agente
sigue en T-04. R-591e7a1672e1/R-03ffcc8e6e9e son distribución. Los enlaces a
evaluación comparativa, verificación y seguridad son métodos vecinos, no obligación
de ejecutarlos todos para cada respuesta. El hook es un ejemplo de configuración.

**Decisión y destino.** **Consolidar** la rúbrica en la referencia propuesta
`skills/outcome-evals/references/delivery-quality.md`. Conservar los cinco ejes,
anclajes de escala, alcance de la petición, evidencia, limitaciones y correcciones.
La evaluación humana o del modelo queda explícitamente auxiliar; sin información
se registra desconocido, sin asumir precisión máxima. No copiar el scorer
semántico aparente, el ejemplo HTTPX incorrecto ni el promedio como aprobación QA.
Corregir ejemplos y mantener una plantilla de evidencia, sin duplicar los gates.

**Activación estática.** Literal: «Evalúa si esta entrega responde bien a la
petición». Paráfrasis: «El código puede estar bien, pero ¿la explicación permite
utilizarlo?». Negativo vecino: «Ejecuta las pruebas E2E» → qa, sin sustituirlas
por puntuación textual. Selector y entrega nativa de hooks no ejecutados.

**Carga y degradación.** Rúbrica/plantilla solo al evaluar una entrega; no
precargar ejemplos y script. Tokens/latencia: null. Sin juez externo, aplicar
revisión explícita con fuentes disponibles; mantener desconocidos y pruebas
pendientes. No pagar una evaluación externa ni emitir aprobado por defecto.

**Validación e impacto.** Lectura de todos los recursos, hash y contraste
oficial HTTPX/hooks; sin ejecución del scorer, HTTPX ni hook del corpus.
T-08/T-10 deberán conservar todos los criterios útiles; T-11 resolverá A002 y
callers, T-14 escenarios reales y T-15 dependencias, exports y docs ES/EN.

## S008 — Selección de capacidades por evidencia del proyecto

**Identidad.** SHA-256
`5847fc20cf0fd0d00c0c2dbacca03472c5a43af429978cf874dd41ecc144dc53`;
5.922 bytes/216 líneas, cuerpo completo; recursos locales: ninguno.

**Contrato y dueño.** Clasifica capacidades de uso habitual y biblioteca
disponible bajo demanda mediante evidencia del repositorio. Produce inventario,
selección propuesta y comprobaciones de instalación. Planner conserva la selección
por tarea; los propietarios de instalación y especialización conservan sus cambios.
Una clasificación no constituye autorización para instalar o borrar piezas.

**Valor y defectos.** Examina agentes, skills, comandos, reglas, hooks y extras;
usa manifiestos, extensiones, CI, configuración y documentación en lugar de elegir
solo por nombre. Biblioteca no equivale a baja: conserva especialidades accesibles.
Los grupos de referencias y router evitan repetir cuerpos. La distinción habitual/
ocasional aporta valor, pero no permite inferir disponibilidad nativa, permisos,
confianza ni uso medido. El plan de instalación necesita un dueño y acción explícita.
El dominio detectado tampoco justifica excluir del catálogo global capacidades
presentes en el corpus o sobrescribir extensiones de proyecto.

**Comparación propia.** `commands/work-context.md` y
`agent-kits/shared/capability-check.md` ya seleccionan por rol/fase/stack/área,
inventarían piezas propias y conservan IDs/fuentes, colisiones y disponibilidad
sin verificar. `docs/PROJECT-EXTENSIONS.md`, «Cómo entran en una tarea» y
«Propiedad y límites», separa descubrimiento de adopción. `docs/SPECIALIZATION.md`
declara generación/adopción como plan pendiente. Falta una pauta explícita para
justificar habitual/bajo demanda con evidencia y revisar una selección obsoleta.

**Dependencias y consumidores.** S256 enlaza esta clasificación como
continuación de descubrir nuevas capacidades; su sección final fue leída, no
toda su auditoría. R-591e7a1672e1 distribuye la pieza; R-03ffcc8e6e9e la excluye
de un perfil portable específico. Esa exclusión no prueba inutilidad en otros
entornos. Los instaladores y auditorías relacionados son continuaciones, no
scripts locales de esta pieza; su revisión operativa completa sigue en T-06.
La recomendación de paralelismo del cuerpo no se ejecutó durante esta comparación.

**Decisión y destino.** **Ampliar** el método de selección existente con la
referencia propuesta `agent-kits/shared/capability-selection.md`, enlazada desde
capability-check y work-context. Conservar los seis grupos, evidencia de repo,
dos inventarios, revisión de vigencia, plan de instalación y comprobaciones.
Habitual significa selección corta pertinente, no carga completa en cada sesión.
Reutilizar catálogo, doctor y contratos de especialización; no crear un segundo
instalador/registro ni adoptar piezas automáticamente. Los grupos serían opcionales
y su diseño se resolverá con el catálogo completo en T-08.

**Activación estática.** Literal: «Qué capacidades usarías habitualmente en
este proyecto». Paráfrasis: «Tenemos muchas guías; selecciona las que encajan
con este repositorio». Negativo vecino: «Crea mi agente de facturación» → creación
de pieza y contrato de especialización, sin confundirlo con inventario.
No se ejecutaron selecciones nuevas ni instalaciones por estos escenarios.

**Carga y degradación.** 5.922 bytes/216 líneas, recursos locales 0/0;
metadatos primero, referencias pertinentes después. Tokens/latencia: null.
Sin señal suficiente, selección provisional con motivos y pendientes; sin lector
o instalación completa, aviso y continuidad con los criterios disponibles.
No declarar soporte universal de OpenCode V2 antes de adaptar lector y despacho.

**Validación e impacto.** Cuerpo, callers y contratos propios leídos; hash
comprobado, sin instalación ni escritura del consumidor. T-08/T-10 definirán
referencia y mapas; T-11 actualizará handoffs; T-14 probará selección, conflictos
y ausencia de recursos; T-15 docs/exports. El plan de especialización mantiene
su ledger independiente, no se da por implementado por esta ficha.

## S009 — Ingeniería de tareas asistidas por agentes

**Identidad.** SHA-256
`41c32c20ec97469341f5d83d8beb15f03d1b6f1c40fb1bdf534c50cd9a38cb6f`;
1.830 bytes/64 líneas, cuerpo completo; recursos locales: ninguno.

**Contrato y dueño.** Descompone un objetivo verificable, fija baseline y
elige capacidad/modelo según el riesgo y el tipo de fallo. Produce criterios,
unidades de trabajo, evidencia de evaluación y motivos para escalar. Planner
planifica, implementer construye, reviewer revisa y qa verifica; no abre otro ciclo.

**Valor y defectos.** Acceptance-first y eval-first se solapan con los gates
propios; aporta firma del fallo, observación de retries/coste/tiempo y separar
carencia de razonamiento de problema operativo antes de usar un modelo más caro.
Los 15 minutos por tarea no son una duración medida ni adecuada universalmente.
Los tiers con nombres de un proveedor no se pueden imponer a todos los runtimes.
Sesiones nuevas y compactación por hitos requieren conservar contrato y evidencia,
no reiniciar a ciegas mientras se depura un fallo activo.

**Comparación propia.** `agents/planner.md` P3 ya exige tareas verificables y
criterios de aceptación; `commands/dev-cycle.md` comparte briefs, revisión/QA y
estado del ledger. `outcome-evals/references/protocol.md` fija baseline y variantes
comparables. `docs/CONVENTIONS.md` define tiering y límites del override efectivo
en Claude; su contrato no acredita parámetros equivalentes en Codex/OpenCode.
Delta: firma de fallos y decisión explicada de escalar, coordinadas con esos métodos.

**Dependencias y consumidores.** S091 lo enlaza desde diagnóstico de costes
de una aplicación consumidora; se leyó el contrato y la ruta de análisis pertinente,
no se ejecutó esa aplicación. R-591e7a1672e1/R-03ffcc8e6e9e distribuyen la pieza.
No declara script o MCP local. Métricas necesitan runner/meter compatible.

**Decisión y destino.** **Consolidar**, junto con S011, en la referencia
propuesta `skills/delivery-practices/references/agent-assisted-delivery.md`.
Conservar aceptación previa, unidades verificables, riesgo, baseline/firma,
evaluación de deltas, continuidad de contexto y coste por tarea. Reutilizar planner,
outcome-evals y model-tier; adaptar criterios de selección al contrato real de
cada runtime, sin duplicar dev-cycle ni prometer tareas de duración fija.

**Activación estática.** Literal: «Diseña cómo dividir este trabajo entre
agentes». Paráfrasis: «Cuándo conviene escalar el modelo si esta tarea falla».
Negativo vecino: «La API devuelve 500, encuentra su causa» → debug-root-cause;
no escalar por defecto. No se midió una mejora de agentes con estos escenarios.

**Carga y degradación.** 1.830 bytes/64 líneas, recursos locales 0/0;
referencia breve bajo demanda. Tokens/latencia: null. Sin métricas compatibles,
registrar ausencia; sin override nativo, usar la capacidad efectiva disponible,
sin declarar un tier aplicado por una etiqueta informativa.

**Validación e impacto.** Lectura/hash, contraparte y secciones de consumidores
comprobadas. Sin benchmark, prompts, estimación de coste real o despacho nuevo.
T-08/T-10 consolidarán contenidos; T-11 handoffs y T-14/T-15 pruebas/docs/exports.

## S010 — Flujos persistentes y automatización programada

**Identidad.** SHA-256
`e1d1207353652456ac84a821e5522def1d108677318630af4fd7ac16735b5c04`;
12.349 bytes/388 líneas, cuerpo completo; recursos locales: ninguno.

**Contrato y dueño.** Diseña un proyecto de automatización persistente con
instrucción corta, roles, comandos, estado y ejecución programada independiente
de la sesión. Produce arquitectura de persistencia, routing y operación; no
convierte cada sesión de desarrollo en un daemon. Architect define aislamiento;
los roles siguen sus artefactos y el propietario de operaciones gestiona schedules.

**Valor y defectos.** La separación kernel corto/estado/logs y lectura/escritura
por rol aporta una arquitectura útil. LaunchAgent/systemd/pm2 son alternativas
de operación del proyecto, no herramientas instaladas por el plugin. Leer todo
el estado y reflexionar/escribir al cerrar cada sesión aumenta contexto y mezcla
doctrina con episodios. La regla de añadir campos sin renombrar nunca no resuelve
migraciones ni lectores antiguos; se necesita esquema versionado y política de
retención. Las mejoras de tiempo narradas no son mediciones reproducibles.

La CLI instalada devolvió `2.1.287 (Claude Code)`, exit 0; su ayuda terminó con
exit 0 y no documenta `--cwd`/`--command`, usados en el ejemplo de scheduler.
Se conserva el hash de la ayuda. Esto prueba ausencia en la ayuda observada,
no un intento de despacho con esos flags. No se ejecutaron prompts ni schedules.
La ruta MCP y los agentes en una carpeta genérica del ejemplo tampoco acreditan
descubrimiento nativo: deben adaptarse a los formatos del runtime real.

**Comparación propia.** `knowledge-check.md` hace recuperación dirigida,
acotada y con estado/procedencia; `knowledge-write.md` distingue journal,
propuesta y doctrina aceptada. `commands/dev-cycle.md` ya tiene ledger y cierre.
`docs/PROJECT-EXTENSIONS.md` fija formatos, identidad de piezas y declaración
frente a conexión. El delta es el ciclo de vida de una automatización que sobrevive
a la sesión, no sustituir esa memoria ni duplicar sus archivos canónicos.

**Dependencias y consumidores.** R-591e7a1672e1 incluye esta especialidad;
R-03ffcc8e6e9e la excluye de un perfil particular por mecanismos ligados a Claude.
No se halló otro caller en las búsquedas canónicas realizadas, lo que no demuestra
uso cero. Daemon, CLI, fuente de eventos y servicios externos son dependencias
del consumidor; sus ejemplos de correo/outreach no autorizan envíos reales.

**Decisión y destino.** **Consolidar** el diseño persistente en la referencia
propuesta `skills/agent-system-quality/references/persistent-workflows.md`,
compartiendo el dueño propuesto en S002/S004. Conservar routing corto, límites
de lectura/escritura por rol, logs/decisiones/inbox, reinicio y programación
externa. Añadir schema/migración/retención, concurrencia, reintentos/idempotencia
y supervisión. Reutilizar ledger y memoria gobernada; preservar la utilidad de
automatizaciones opcionales sin imponer infraestructura o una base de datos nueva.
T-07/ fase 4 compararán recuperación y utilidad; esta ficha no reemplaza memoria.

**Activación estática.** Literal: «Diseña un agente que ejecute este flujo
programado y conserve estado». Paráfrasis: «Cómo reanuda mañana esta automatización
sin depender de la conversación abierta». Negativo vecino: «Reanuda esta tarea
del roadmap» → dev-cycle/ledger, sin daemon nuevo. No hubo scheduling ejecutado.

**Carga y degradación.** 12.349 bytes/388 líneas, recursos locales 0/0;
kernel corto y referencias de operación solo cuando apliquen. Tokens/latencia:
null. Sin scheduler o CLI validada, conservar arquitectura/operación manual y
marcar ejecución automática pendiente, sin prometer continuidad ni recuperación.

**Validación e impacto.** Hash/lectura y CLI local limitada a versión/ayuda;
sin ejecución del código del corpus, servicios, prompts o publicación de memoria.
T-08 decidirá diseño; T-12 validará cualquier recurso operativo adoptado según
runtime/OS, T-14 fallos/reinicio y T-15 docs/exports. Los ejemplos no son soporte
ya probado en Windows ni instrucciones para instalar un paquete técnico global.

## S011 — Prácticas de equipo para desarrollo asistido

**Identidad.** SHA-256
`114913bdcb6127392df56d96f7f1312f36c74d69c278dece6d377b9bd92123a5`;
1.454 bytes/52 líneas, cuerpo completo; recursos locales: ninguno.

**Contrato y dueño.** Define aceptación, responsabilidades y revisión de
trabajo asistido por agentes dentro de un equipo. Produce acuerdos observables
sobre implementación/revisión, pruebas y escalado. No reemplaza al responsable
humano ni añade otro orquestador al ciclo.

**Valor y defectos.** Aporta criterios de competencia verificable: descomponer
ambigüedad, diseñar evaluaciones, reconocer límites y controlar riesgos. Revisión
de comportamiento, seguridad, integridad, errores y rollout ya tiene dueño en
el plugin. No convertir indicios de competencia en un score automático de
contratación ni repetir un proceso genérico como guía obligatoria para todo proyecto.

**Comparación propia.** Planner P3 conserva aceptación; dev-cycle «Fase 3» y
adversarial-review «Método» conservan implementación, revisión independiente
y QA; unit-tests «Pirámide» distingue niveles y cobertura real. S009 aporta
el detalle técnico complementario de baseline, firma del fallo y modelo.
Delta: responsabilidades del equipo e indicadores concretos para delegación humana,
ligados a ese mismo proceso, en lugar de otro workflow equivalente.

**Dependencias y consumidores.** Solo R-591e7a1672e1/R-03ffcc8e6e9e en la
búsqueda canónica pertinente; son distribución, no uso medido. Sin ejecutor/MCP
local. Evaluación de competencias requiere evidencia del trabajo y juicio humano.

**Decisión y destino.** **Consolidar** con S009 en
`skills/delivery-practices/references/agent-assisted-delivery.md`. Conservar
responsabilidades, aceptación/interfaces, determinismo, riesgo bajo presión,
pruebas de límites y regresiones, revisión de integridad/rollout e indicadores
de competencia. Enlazar los métodos existentes en lugar de copiar sus pasos.

**Activación estática.** Literal: «Define las responsabilidades del equipo
cuando usa agentes». Paráfrasis: «Qué evidencia pedir antes de delegarles trabajo».
Negativo vecino: «Calcula un presupuesto de la iniciativa» → evaluator,
sin estimación por esta guía. No se ejecutó evaluación de personas ni selector.

**Carga y degradación.** 1.454 bytes/52 líneas, recursos locales 0/0; compartir
la referencia con S009. Tokens/latencia: null. Sin evidencia de competencias,
documentar criterios y pendientes; no inferir eficacia del equipo o de un agente.

**Validación e impacto.** Lectura/hash y comparación de secciones; sin estudio
de productividad ni adopción operativa. T-08/T-10 conservarán todos los criterios,
T-11 callers y T-14/T-15 activación, distribución y docs ES/EN.

## S012 — Regresiones de ramas condicionales y contratos

**Identidad.** SHA-256
`83f2f5c4083af5762dd658f742d4a390eb3a6f969d835f69e8f47efba296c127`;
11.659 bytes/386 líneas, cuerpo completo; recursos locales: ninguno.

**Contrato y dueño.** Detecta supuestos erróneos de cambios asistidos y protege
comportamientos con regresiones concretas: sandbox/proveedor, feature flags,
campos de respuesta y consumidores, estado/caché/rollback concurrente. Produce
tests y matriz de rutas; implementer crea la protección, reviewer comprueba
defectos y qa conserva el resultado ejecutado.

**Valor y defectos.** Los ejemplos Vitest/Next.js/Supabase concretan peticiones,
campos obligatorios y tipos generados. Sin embargo la prueba que afirma paridad
sandbox/producción solo llama al camino simulado. Condicionar las aserciones a
que exista alguna fila deja un verde vacío. Proponer SELECT * puede exponer campos
privados y contradice un contrato de respuesta explícito. Restaurar el snapshot
entero tras un rollback puede deshacer mutaciones concurrentes válidas.
Una suite no garantiza que un fallo no pueda reaparecer; el objetivo de menos
de un segundo no es medición ni requisito universal. La recomendación de probar
solo bugs históricos no cubre comportamiento nuevo ni sustituye el TDD configurado.

**Comparación propia.** `backend-practices/references/contracts-data.md`
requiere campos serializados permitidos, idempotencia/concurrencia y motor real.
`api-contract/references/contract-tests.md` distingue mock de contrato frente
a implementación. Sus ejemplos de SDK también necesitan revalidar versiones
antes de ampliarlos: no se dan por vigentes solo por ser propios.
`tdd` exige rojo pertinente cuando está habilitado; `unit-tests` separa cobertura
real de aserciones triviales. `frontend-quality` exige estado coherente tras
mutación optimista y respuesta fuera de orden. Falta una matriz explícita de ramas
que detecte diferencias de selección del proveedor y falsos verdes por datos vacíos.

**Dependencias y consumidores.** S055 relaciona contrato primero con regresión;
S176 lo incorpora a flujos con predicciones y cambios backend. Se leyeron las
secciones pertinentes, sin completar sus fichas. R-591e7a1672e1 lo distribuye;
R-03ffcc8e6e9e excluye un perfil por plantillas de comandos Claude, no por ausencia
de valor técnico. La plantilla de comando del cuerpo es un ejemplo, no un caller
ejecutado. Vitest/Next.js/Supabase dependen del proyecto; no se instalaron.

**Decisión y destino.** **Ampliar** backend-practices con la referencia
propuesta `references/conditional-path-regressions.md`, enlazando api-contract,
tdd, unit-tests y frontend-quality. Conservar matriz flag/entorno/proveedor,
forma/nullabilidad/selección de campos, errores, estado/caché y carrera/rollback.
Exigir fixtures no vacías y recorrer cada rama reclamada; usar campos explícitos
y rollback por operación. Los ejemplos por stack seguirán opcionales porque
están presentes en el corpus, sin generar esos proyectos en todos los consumidores.

**Activación estática.** Literal: «Prueba que sandbox y proveedor devuelven el
mismo contrato». Paráfrasis: «Este flag pasa los tests pero rompe producción».
Negativo vecino: «Valida solo la estructura OpenAPI» → api-contract/linter;
no atribuir ejecución de ramas a una validación de esquema. Sin pruebas nuevas
ejecutadas, SDKs compilados ni servicio de producción contactado.

**Carga y degradación.** 11.659 bytes/386 líneas, recursos locales 0/0;
cargar matriz común y ejemplo del stack afectado. Tokens/latencia: null.
Sin dependencia/credenciales aisladas para una rama, declarar no ejecutada;
mock-only no demuestra paridad real. Mantener tests posibles y los gates existentes.

**Validación e impacto.** Lectura/hash, recursos inexistentes y consumidores
comprobados; las deficiencias de los ejemplos proceden de inspección, no de un
fallo ejecutado en Vitest. T-08/T-10 deberán corregir y verificar ejemplos;
T-11 enlazará roles, T-14 demostrará rutas/fallos y T-15 actualizará docs/exports.

## Estado de este bloque

Siete skills comparadas; ninguna integrada desde estas fichas. Todos los destinos
nuevos están sujetos al diseño T-08, sin aliases vacíos, segundo instalador,
scorer semántico aparente ni sustitución de la memoria. La validación de hashes
y estructura confirma trazabilidad, no eficacia, despacho nativo o mejora medida.
