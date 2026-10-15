---
tasks: catalog-capabilities
estado: en-progreso
creado: 2026-10-07
actualizado: 2026-10-12
verificacion: obligatoria
changelog: Changed
---

# Capacidades del catálogo — ledger

> Ledger canónico. Fuente única de progreso de la fase 3.

Autorización: integración por fases, decisiones técnicas delegadas y push
cuando esté listo. Base 6187b12; rama feat/catalog-capabilities. No PR,
integración en main ni release. `.claude/settings.json` ajeno intacto y fuera del índice.
Meter privado abierto; sin respuestas compatibles no se inventa consumo.

Prioridad del usuario del 2026-10-08: hooks, comandos, dashboard y memoria.
Actualización 2026-10-14: T-03 con las 293 skills leídas y T-10 en curso con los 110 destinos P1/P2/P3 integrados (47 aparcados); falta la validación con escenarios reales. S080–S082 tienen
lectura privada parcial, no evaluación completada. Dependencias por bloque
y valoración inicial de memoria en
[operational-priorities.md](operational-priorities.md). No se cierra el
objetivo ni se convierte la comparación restante en una entrega realizada.

Comprobación de la repriorización: TDD n/a, solo documentación. 50 tests de
test_roadmap_index pasaron (0,13 s); ledger-lint cero incoherencias/cero avisos;
scope-check contra f8828f9, cuatro documentos en alcance/cero fuera, settings
ajenos excluidos; 13 enlaces locales válidos y scan de nombres/contenido sin
referencias prohibidas. Diff limpio. Estas puertas no prueban despacho de
hooks, conexiones de backend ni utilidad de recuperación.

## Resumen de progreso

Retoma nativa JSON: dos casos reales OpenCode 2.0.12 pasan con el modelo configurado, selección explícita/ambigua, invocación efectiva del compositor, JSON semánticamente completo y ledgers intactos. Se corrigen dos desviaciones source55: status omitido y selección manual sin compositor. [Evidencia y límites](testing/native-work-resume140-status.md). Regresión focal: 118 passed/1 skipped; cambios sólo de prompt/doc y exports. No acredita Claude/Codex, aprobación de planes, UI, revisión independiente ni cierre global; skills aplazadas.

Actualización 2026-10-12: la QA completa del core source54 pasa los 7.296 casos por plataforma: Windows 7.197 passed/99 skipped y Linux 7.235 passed/61 skipped, sin fallos/error. Cobertura parental de 33 fuentes Python: 91,1558%/91,2668%; inventario actual incluye task-brief. Node: 330 passed; DOM: 76 passed/61 escenarios, incluidos en el total Python. [Resultados y límites](testing/global-source54-status.md). Cinco implementaciones JavaScript tienen 205/205 líneas cambiadas evaluadas ejecutadas; el mirror generado se excluye del porcentaje y conserva prueba nativa separada. [Medición](testing/javascript-source54-status.md). Recorridos reales de comandos, UI humana y revisión independiente siguen pendientes; sin cierre de macros, commit o push por esta QA.

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 1 | 7 | 14% |
| Fase 2 | 0 | 6 | 0% |
| Fase 3 | 0 | 3 | 0% |
| **TOTAL** | **1** | **16** | **6%** |
El porcentaje anterior corresponde a las tareas macro de todo el catálogo,
incluidas las skills aplazadas. No mide el progreso de este lote operativo.
La copia revisada mantiene las siguientes entregas y pendientes:

| Prioridad | Implementación en la copia revisada | Trabajo pendiente |
|---|---|---|
| Memoria | Base local canónica, curación única, retoma y traslado explícito de aprobados a candidatos; Kwipu/Graphify opcionales; captura y replay locales comprobados en una sesión Claude aislada | Workflows nativos, despliegue compatible, utilidad comparativa de recuperación y QA conjunta de la versión integrada |
| Comandos | Diagnóstico, retoma, revisión de planes, curación y selección exacta de commits con staging ajeno conservado | QA conjunta y aceptación de workflows nativos; recursos restantes |
| Hooks | Contratos por runtime, captura acotada y productores opt-in de actividad; señales verificadas en sesiones aisladas Claude, Codex y OpenCode | Cobertura nativa restante sobre la versión integrada; causas históricas de errores no demostradas |
| Dashboard | Navegación, fases, handlers, revisión de planes y señales recientes de actividad con vencimiento | QA conjunta e interacción visual real en Edge |

La QA conjunta full02 terminó sobre 6.951 casos por plataforma: Windows 6.848 aprobadas, cinco fallidas y 98 omitidas; Linux 6.906 aprobadas, una fallida y 44 omitidas; cero errores en ambas. Los dos gates de cobertura superan el 90 %, pero la QA no está aceptada. Se conserva el fallo textual corregido en la candidata y los cuatro fallos Windows pendientes de diagnóstico o comprobación focal. El detalle y los límites están en [testing/final-qa25-status.md](testing/final-qa25-status.md). Este lote aún no tiene commit ni push.
Estas entregas no cierran las tareas macro ni la integración global.

La prueba real posterior al código final pasó: versión 2 recuperada por consulta
ordinaria, hechos y entidades; tres creaciones únicas, dos identidades históricas
verificadas y recursos propios retirados. El servicio original permanece sin actualizar.
[Detalle y límites](testing/graphiti-final-live67-status.md). QA global, utilidad
comparativa, workflows nativos, interacción visual y revisión final siguen pendientes.


Los quince fallos residuales quedaron resueltos. El código final pasó 375 casos ampliados
y 288 del publicador en Windows, con una omisión y sin fallos; Linux pasó los 664 sin
omisiones. La procedencia moderna no se decide por nombres coincidentes, las versiones
previas inválidas se rechazan y las identidades largas se validan completas sin recorte.
Se conservan los RED y los pases fallidos intermedios. Detalle en
[testing/graphiti-contract66-status.md](testing/graphiti-contract66-status.md).
Siguen pendientes recorrido real posterior, utilidad comparativa, workflows nativos y QA global.


La actualización de contratos y fixtures redujo el diagnóstico ampliado de 68 a 19
fallos. El foco posterior de esos 19 deja 15 pendientes. El recibo de envío incierto
conserva ahora la causa original saneada sin reenviar; pasan 280 casos del publicador
por plataforma y las tres pruebas de seguridad afectadas. Se conserva el historial
de fallos; no se acepta una nueva suite ampliada ni la QA global. Detalle en
[testing/graphiti-contract65-status.md](testing/graphiti-contract65-status.md).


El lector común conserva procedencia derivada, UUID e identidades exactas en JSON,
y antepone la falta de autoridad en CLI/briefs. La regresión de búsqueda/router/brief
pasa en Windows y Linux con omisiones declaradas; Git se comprobó por separado.
El diagnóstico ampliado de Graphiti conserva 68 fallos pendientes, 307 casos correctos
y una omisión. No se acepta esa batería ni la QA global. El detalle queda en
[testing/memory-source-surface64-status.md](testing/memory-source-surface64-status.md).


La candidata incorpora el vínculo de UUID nativos y pertenencia de entidades con
fuentes vigentes confirmadas. La regresión posterior tiene 275 casos aprobados por
plataforma; la prueba real en servidor compatible recuperó versión 2 por consulta
ordinaria, hechos y entidades, con tres creaciones únicas y retiro de recursos propios.
Respuestas parciales no atribuyen una fuente inequívoca. El detalle y los límites están
en [testing/graphiti-provenance63-status.md](testing/graphiti-provenance63-status.md).
No se acepta utilidad comparativa, despliegue permanente, workflow nativo ni QA global.


La prueba real de reconstrucción pasó en una instancia compatible del servidor oficial;
el servicio instalado tiene un defecto de enrutado de lecturas por grupo. También se
reprodujo el descarte de cuatro aciertos semánticos por falta de vínculo entre UUID y
procedencia. El detalle y los límites quedan en [testing/graphiti-live61-status.md](testing/graphiti-live61-status.md).

La candidata incorpora creación con UUID del servidor, recibos/intenciones recuperables,
verificación histórica y reconstrucción por generaciones con snapshot y cambio final.
La batería focal conjunta tiene 256 casos aprobados por plataforma; no acepta la suite
global ni la reconstrucción con el servicio real. El timeout Linux inicial y su aislamiento
de E/S se conservan en [testing/graphiti-generation59-status.md](testing/graphiti-generation59-status.md).

La comprobación focal posterior ejecutó una vez los cuatro casos Windows con fuente y soporte originales: tres pasaron y N05 volvió a fallar con WinError 5, esta vez al publicar la restauración sintética, antes del replay posterior. Recibo SHA d0833a0f787ed30cdf47255db581c22d95b37c84b2792a02635514de62883f25. Se verificaron antes y después los 1.071 inputs congelados y las 86 dependencias; el job propio terminó con cero procesos activos y sin fuga. Este foco no explica las causas históricas ni acepta full02.

El coste de proceso conserva un gap reproducido con fixtures sintéticas y los CLIs actuales: el primer cierre de una ventana informa 150 tokens y el segundo, acumulativo, 200; conservar ambos snapshots en plan y tasks hace que el dashboard sume 350. El resultado esperado para esa misma ventana es 200. RED PID 21648/exit 1, recibo SHA 6c78148e0d055566c1cbcffa8dc33cdb59cd6d4a6ede1ded60cbebb39b56a4c7. No se usaron transcripciones privadas, precios ni calibración medida. Este RED histórico se conserva; la corrección candidata y las comprobaciones focales posteriores están en testing/final-qa25-status.md. La aceptación conjunta sigue pendiente.

La candidata conserva el encargo de desarrollo en ambas vías: resultado, requisitos y fuentes, restricciones, patrones con rutas y pendientes pasan al evaluator y al ledger creado por planner o por el orquestador. Usa Descripción, Notas, criterios y Verificación existentes; no añade artefactos ni puertas. Las dos traducciones del comando se regeneraron con el exportador oficial, PID 25568/exit 0, conservando frontmatter, wrapper y cuerpo canónico. La generación no prueba atención del modelo ni aceptación del workflow nativo. TDD n/a: prosa y traducciones de prosa; revisión independiente y validación operativa pendientes.

## Fase 1 — Comparación

**Estado**: en-progreso

### T-01 — Corpus y trazabilidad de la comparación

- **Estado**: completado
- **Descripción**: Reconciliar piezas principales, recursos y soporte del control panel; fijar IDs/hashes y distinguir inventario de evaluación.
- **Dependencias**: Primera y segunda fases publicadas.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`, `docs/roadmap/README.md`, `docs/INTEGRATION-ROADMAP.md`, `docs/en/INTEGRATION-ROADMAP.md`
- **Verificación**: build_catalog_corpus.py terminó con exit 0: 4.212 archivos reconciliados, 455 hashes principales coincidentes, 455 bundles estructurales, tres entradas y 30 archivos relacionados con paneles. corpus.json/corpus.md y audit-contract.md fijan evidencia y fichas; cero evaluadas semánticamente.
**Criterios de aceptación**:
  - [x] Los 455 hashes principales coinciden con revisión y registro privado/público de fase 1.
  - [x] Recursos y control panel reconciliados y vinculados al corpus, con fuentes privadas y nombres propios públicos.
  - [x] Alcance completo y fichas de comparación definidos sin simular revisión semántica.

### T-02 — Contratos por runtime y modo de instalación

- **Estado**: en-progreso
- **Descripción**: Contrastar esquemas y código de las versiones instaladas; resolver identidad, confianza, hooks y configuración OpenCode V2 antes de elegir mecanismos.
- **Dependencias**: T-01.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Los contratos iniciales y sus fallos quedan preservados en runtime-probes.json/contracts.md. Después se verificaron contexto, captura UTF-8 y cierre natural en Claude 2.1.287, Codex 0.161.0 y OpenCode 2.0.12: evidencia de cierre e instalación en terminal-qa-evidence.json y fichas nativas enlazadas. native-role-contract-evidence.json añade 14 casos Claude, 12 comprobaciones Codex y tres experimentos OpenCode con identidad efectiva, bloqueo previo y controles permitidos en fixtures propias. La identidad nativa no certifica procedencia del prompt. Persisten pendientes la confianza de instalación real, normalización completa e integración de guardias por rol; no se cierra T-02 por las pruebas del mecanismo.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-03 — Comparación semántica de las 293 skills

- **Estado**: en-progreso
- **Descripción**: Leer cuerpos, recursos y callers de todas las skills; registrar contenido único y comparación concreta, incluyendo dominios técnicos y memoria.
- **Dependencias**: T-01.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: 293/293 skills evaluadas semánticamente (S001–S293), cuerpos completos, recursos locales y consumidores pertinentes comprobados. comparisons/skills-foundations.md conserva el primer bloque, con hashes/rangos de 18 fuentes y 13 archivos propios en reading-evidence.json. comparisons/skills-workflows.md añade S006–S012 y los seis recursos de S007; workflow-reading-evidence.json registra 20 fuentes y 18 propios. comparisons/skills-architecture-operations.md añade S013/S015–S020; architecture-reading-evidence.json registra 32 fuentes y 16 propios y conserva la lectura pendiente histórica de S014. comparisons/skills-angular.md completa S014; angular-reading-evidence.json registra 39 fuentes y 15 propios, los 35 recursos completos y 21 contrastes documentales oficiales. comparisons/skills-iteration-backend-benchmarks.md añade S021–S027; iteration-reading-evidence.json registra 35 fuentes y 26 propios, siete cuerpos completos sin recursos locales y 10 contrastes oficiales, con cuatro lecturas documentales rechazadas diferenciadas. comparisons/skills-brand-browser-runtime.md añade S028–S032; brand-ui-reading-evidence.json registra 36 fuentes y 22 propios, los nueve recursos completos y siete contrastes oficiales. comparisons/skills-operations-session-context.md añade S033–S035; operations-reading-evidence.json registra 21 fuentes y 18 propios, nueve recursos completos y cuatro contrastes oficiales, con tres rechazos HTTP directos separados de la lectura documental disponible. comparisons/skills-navigation-quality-data.md añade S036–S042; navigation-reading-evidence.json registra 21 fuentes y 28 propios, siete cuerpos completos sin recursos locales y 15 contrastes oficiales, con un enlace antiguo HTTP 404 y su sustituto vigente diferenciados. comparisons/skills-strategy-configuration-context.md añade S043–S052; business-reading-evidence.json registra 40 fuentes y 30 propios, diez cuerpos completos sin recursos locales y nueve contrastes oficiales; entrypoints leídos y verificación operativa pendiente diferenciados. comparisons/skills-session-learning-memory.md añade S053–S054; learning-reading-evidence.json registra 32 fuentes y 22 propios, dos cuerpos completos, 13 recursos completos y cuatro contrastes oficiales; tests y código del corpus leídos sin ejecución, dispatch/arquitectura/eficacia pendientes diferenciados. Helpers privados de cada bloque, Python 3.13, exit 0. Las fichas separan destinos propuestos, escenarios estáticos y validaciones no ejecutadas. comparisons/skills-contracts-costs-decisions.md añade S055–S060; contract-cost-reading-evidence.json registra 22 fuentes y 20 propios, seis cuerpos completos, tres recursos completos, siete contrastes oficiales y dos consultas CLI de versión/ayuda; estimación, facturación e integración operativa diferenciadas. comparisons/skills-cpp-dotnet-distribution-billing.md añade S061–S065; cpp-dotnet-reading-evidence.json registra 24 fuentes y 20 propios, cinco cuerpos completos sin recursos locales, 14 contrastes oficiales y un HTTP 404 con sustituto vigente diferenciado; compilación/cobertura/envíos/operaciones financieras no ejecutados. comparisons/skills-trade-flutter-observability.md añade S066–S068; trade-flutter-reading-evidence.json registra 25 fuentes y 27 propios, tres cuerpos completos sin recursos locales, diez reglas externas completas (30.350 bytes/1.080 líneas), 24 contrastes oficiales y tres respuestas sin documento válido diferenciadas; normativa por caso, compilación, hooks y dashboards operativos no ejecutados. comparisons/skills-data-pipelines-research.md añade S069–S072; data-research-reading-evidence.json registra 14 fuentes y 24 propios, cuatro cuerpos completos (46.443 bytes/1.450 líneas) sin recursos locales, 23 contrastes oficiales y un HTTP 404 con sustituto válido diferenciado; extracción, enriquecimiento, benchmark, migraciones y conexiones MCP no ejecutados. comparisons/skills-contract-security-delivery.md añade S073–S074; security-delivery-reading-evidence.json registra ocho fuentes y 19 propios, dos cuerpos completos (10.530 bytes/293 líneas), un recurso completo (7.826 bytes/220 líneas), 12 contrastes oficiales, un HTTP 404 y dos errores del lector web diferenciados; herramientas Solidity y dispatch de cierre no ejecutados. comparisons/skills-deployment-design-collaboration.md añade S075–S077; deploy-design-team-reading-evidence.json registra 20 fuentes y 19 propios, tres cuerpos completos (22.246 bytes/714 líneas), cero recursos locales, 13 contrastes oficiales y un error de lector web con lectura HTTP válida posterior diferenciados; despliegue, preview visual y sesiones de agentes no ejecutados. comparisons/skills-django-queues-architecture.md añade S078–S079; django-core-reading-evidence.json registra 11 fuentes y 14 propios, dos cuerpos completos (34.250 bytes/1.193 líneas), cero recursos locales y 14 contrastes oficiales; código, migraciones, workers, brokers y pagos no ejecutados. comparisons/skills-django-security-testing-verification.md añade S080–S082 (2026-10-13); django-security-testing-reading-evidence.json registra tres cuerpos completos (50.033 bytes/1.844 líneas), cero recursos locales, callers A017/A018 por líneas y dos contrastes oficiales (Django 6.1, pytest-django); sin skill nueva: especialidad django-practices propuesta. comparisons/skills-parallel-containers-docs.md añade S083–S085 (2026-10-13): parallel-containers-docs-reading-evidence.json registra tres cuerpos completos (26.185 bytes/803 líneas), cero recursos locales y dos scripts citados sin leer; decisiones: no adoptar dmux, ampliar delivery-practices con el arnés aislado, Context7 como canal opcional de research-first. comparisons/skills-dotnet-harness-e2e.md añade S086–S088 (2026-10-13): tres cuerpos completos (22.875 bytes/773 líneas) sin recursos locales; .NET de diseño a dotnet-practices, criterio de extracción a plugin-dev y estabilidad de specs a qa/frontend-quality; contraste oficial pendiente. comparisons/skills-catalog-self-ops-domains.md añade S089–S094 (2026-10-13): seis cuerpos completos (54.512 bytes/906 líneas); tres describen el catálogo de origen y quedan cubiertas por dueños propios, S091 aporta cuatro patrones de coste a backend-practices, S092/S093 van a extensiones/personas de proyecto. comparisons/skills-errors-evals-providers.md añade S095–S100 (2026-10-13): seis cuerpos y un recurso completos (45.983 + 4.651 bytes); errores a stack/backend-practices, patrón de aprobación ligada de S096 a delivery-practices, pass@k a outcome-evals, Exa a research-first, fal.ai fuera del bundle. comparisons/skills-fastapi-billing-flox.md añade S101–S103 (2026-10-13): FastAPI a stack-practices/python con 10 adaptaciones, facturación sin destino nuevo, Flox como manifiesto de dependency-upgrade. comparisons/skills-flutter-ondevice-a11y.md añade S104–S106 (2026-10-13): revisión Flutter a la especialidad de S067, FoundationModels fuera del bundle, accesibilidad React a frontend-quality con 7 correcciones. comparisons/skills-frontend-direction-patterns-slides.md añade S107–S109 (2026-10-13; S109 cerrada tras leer sus seis recursos): dirección visual a frontend-quality, carga de datos con cancelación a stack-practices/react. comparisons/skills-fsharp-gan-gateguard.md añade S110–S112 (2026-10-13): F# a dotnet-practices, arnés generador-evaluador y puerta de hechos sin adoptar (contradicen alcance aprobado y hooks que informan). comparisons/skills-git-github-workspace.md añade S114, S115 y S118 (2026-10-13): flujo Git cubierto por guardrails y release.py, sección de contenido no confiable de GitHub a delivery-practices, Workspace fuera del bundle. comparisons/skills-installer-golang.md añade S113, S116 y S117: instalador Windows fuera del bundle, Go sin especialidad hasta que un consumidor declare el stack. comparisons/skills-growthlog-healthcare-imports.md añade S119–S124: registro de aprendizaje a la plantilla de knowledge-write, dominio sanitario fuera del bundle, checklist de saneado a plugin-dev. comparisons/skills-hexagonal-hipaa-homelab.md añade S125–S130: arquitectura hexagonal como opción del architect, HIPAA y red doméstica fuera del bundle. comparisons/skills-vpn-hookify-i18n-legacy.md añade S131–S134: VPN doméstica fuera del bundle, reglas de hookify sin destino (hooks que informan), traducciones a frontend-quality, umbral de señal para la constitución de /setup. comparisons/skills-intent-inventory.md añade S135–S136: tres reglas de criterios (hechos frente a restricciones de negocio, efecto prohibido, palabras vagas) para analyst/spec; inventario fuera del bundle. comparisons/skills-investor-icons-retrieval.md añade S137–S140: inversores e iconos iOS fuera del bundle, búsqueda de sinónimos del dominio en el brief de task-brief.py. comparisons/skills-ito-family.md añade S141–S144: familia Itô fuera del bundle; procedencia (fecha de fuente frente a recuperación) y digest sobre descriptor abierto como referencias. comparisons/skills-java-jira-knowledge.md añade S145–S148: Java/JPA sin especialidad hasta que un consumidor declare el stack, contenido de ticket no confiable para jira-sync, /roadmap-live y confluence-pull, operación del conocimiento sin destino. comparisons/skills-kotlin-family.md añade S149–S153: sin especialidad Kotlin sin consumidor (T-08 resuelve la tensión con kotlin-practices de S013/S045); correcciones por pieza; coverage-gate no detecta Gradle/Kover. comparisons/skills-k8s-latency-mailtrap.md añade S154, S160 y S167: tres líneas agnósticas en delivery-practices (PDB/réplicas, HPA/manifiesto, token de cuenta de servicio); frescura y segmentos a performance-baselines (S023); Mailtrap fuera del bundle. comparisons/skills-laravel-family.md añade S155–S159: sin especialidad Laravel (el consumidor PHP es CodeIgniter 4); 12 errores anotados en S157 y mezcla de versiones; nada nuevo en php-codeigniter.md. comparisons/skills-leads-logistics-research-agreements.md añade S161, S165 y S170–S172: dominios de negocio fuera del bundle; S170 cubierta por S072; escritura atómica propuesta para to-pdf (no dejar un PDF viejo tras un fallo). comparisons/skills-glass-polish-manim.md añade S162, S168 y S169: S162 y S169 fuera del bundle; S168 aporta cuatro criterios a la dirección visual de frontend-quality y área de pulsación con WCAG 2.5.8. comparisons/skills-living-docs-loops-trading.md añade S163, S164 y S166: revisar el aviso de RUTAS_RETIRADAS de lint_plugin.py; S166 aporta dos comprobaciones (tests debilitados, criterios editados en tasks.md); S164 fuera del bundle. comparisons/skills-mysql-nestjs-mcp-keccak.md añade S173, S180, S183 y S189: dos reglas de construcción MCP en delivery-practices; réplica tras escritura e interbloqueo en contracts-data; NestJS sin especialidad; Keccak fuera del bundle. comparisons/skills-messages-nasiko-nutrient-persona.md añade S174, S181, S182, S190 y S192: las cinco fuera del bundle; «cada línea del prompt debe cambiar el comportamiento» a los anti-patrones de plugin-dev. comparisons/skills-ml-adoption-mle.md añade S175–S176: sin especialidad ML hasta que un consumidor la declare; el método ya tiene dueños (analyst, research-first, outcome-evals, retro); defectos anotados. comparisons/skills-motion-next-nuxt.md añade S177–S179, S188 y S191: fila «Animación» en frontend-quality; convención de ficheros por versión de Next.js y render inicial determinista en react.md; Nuxt sin especialidad. comparisons/skills-network-netmiko-bgp.md añade S184–S187: mantiene la especialidad opcional network-operations de S034 con tres referencias y corrige parsers que descartan vecinos Idle, solapes sin VRF y ausencias leídas como 0. comparisons/skills-orch-opensource-approval.md añade S193–S196: orch-* sin destino salvo rebanadas verticales en planner; open source sin destino; estado incierto a delivery-practices y recibo de envío para jira-sync/outbox (jira-flow.py marca publicado al planificar). comparisons/skills-orch-parallel-plan.md añade S197–S201 y S206: dueño /dev-cycle (ADR-011); dos filas para tdd (cambio de comportamiento y refactor puro); migraciones o mismo almacén en secuencia en el despacho paralelo; S206 sin destino. comparisons/skills-perl-family.md añade S202–S204: sin especialidad Perl hasta que un consumidor la declare; correcciones anotadas; entonces, fila prove en tdd/by-stack y parser en coverage-gate. comparisons/skills-product-canvas-flow-prompts.md añade S205, S212, S213, S216 y S217: S205 al destino de panel-plan-review.md sin hook que bloquee; política/preferencia/abierta en analyst e invariantes en design.md; S213 y S217 sin destino. comparisons/skills-plankton-postgres-prisma-audit.md añade S207, S208, S211 y S214: hooks de S207 no se adoptan (ADR-007); relajación de lint como gap de la lente A y trinquete con --baseline en code-health; S211 sin especialidad. comparisons/skills-prediction-markets-scheduling.md añade S209, S210 y S215: fuera del bundle; S209–S210 de la familia de S141–S144; S215 fabricación con defectos anotados. comparisons/skills-python-pytorch.md añade S218–S220: python.md de stack-practices ya cubre S218–S219, con defectos anotados; SQLAlchemy queda candidata; S220 sin especialidad ML. comparisons/skills-nonconformance-remotion-returns.md añade S221, S236 y S239: fabricación regulada, devoluciones y vídeo Remotion fuera del bundle; causas conjuntas en la fase 3 de debug-root-cause. comparisons/skills-quarkus-family.md añade S222–S225: sin especialidad Java/Quarkus hasta que un consumidor declare el stack (java.md con S145/S147/S260–S263); huecos JaCoCo en coverage-gate y pom.xml en deps-inventory. comparisons/skills-rails-redis-rust.md añade S226, S234, S241 y S242: Rails y Rust sin especialidad; Redis cierra el pendiente de S078 con una tabla «Caché, cerrojos y límites» en contracts-data.md. comparisons/skills-rfc-dag-ledger-santa.md añade S227, S233 y S244: repetir la Verificación de lo ya integrado tras cada reintegración del lote paralelo en /dev-cycle; S233 y S244 sin destino (adversarial-review ya lo supera). comparisons/skills-react-rn-perf-testing.md añade S228–S231: sin especialidad React Native; «use server» como disparador de la lente C, estado de módulo en servidor y MSW/caché por test en react.md. comparisons/skills-recsys-regex-llm.md añade S232 y S235: recomendación fuera del bundle; en outcome-evals, el silencio del extractor no es éxito (contar lo esperado por vía independiente). comparisons/skills-reposcan-research-rules-safety.md añade S237, S238, S240 y S243: aviso de versionados excluidos en code-health; S238 absorbida en S072; «elevar a convención» en capability-audit; patrones destructivos a evaluar en guardrail-check. comparisons/skills-scientific-literature-patents.md añade S245–S249: fuera del bundle; registro reproducible de consultas, separación oficial/secundaria y «la fuente lo dice» a research-first. comparisons/skills-search-compliance-stocktake-compact.md añade S250, S255–S257 y S264: componer y vetar skills externas en research-first, buscar dueño antes de crear en plugin-dev, casos en contra en outcome-evals; stocktake y compactación sin destino. comparisons/skills-security-bounty-review-agentshield.md añade S251–S253: recompensas fuera del bundle; subidas a backend-practices, OIDC a delivery-practices y configuración de agente como superficie en cybersecurity (incoherencia de large-codebase.md). comparisons/skills-seo-social-graph-publisher.md añade S254, S258 y S259: fuera del bundle; Core Web Vitals ya en frontend-quality; contenido no confiable refuerza S115/S146. comparisons/skills-springboot-patterns-security-testing.md añade S260–S263: Spring Boot sin especialidad hasta que un consumidor declare Java (java.md); la verificación duplicaría a qa; JaCoCo en coverage-gate como tarea aparte. comparisons/skills-swift-swiftui.md añade S265–S268: Swift/SwiftUI sin especialidad hasta que un consumidor declare iOS/macOS; correcciones para un futuro swift.md. comparisons/skills-taste-video.md añade S269–S272, S286 y S287: producción de vídeo fuera del bundle (recursos de S270–S271 leídos de forma selectiva); un juez que recibe la medida no la contrasta, a outcome-evals. comparisons/skills-tdd-verification-ops.md añade S273, S277 y S285: sin skill nueva; Verificación de plan externo en implementer y filas de rojo de compilación y Bun en tdd/by-stack; S285 duplica qa. comparisons/skills-team-memory-surface.md añade S274, S275, S279, S283, S284 y S292: sin destino; ledger, /work-resume, /doctor, /plugin-catalog y capability-audit ya cubren; S284/S292 chocan con ADR-007. comparisons/skills-terminal-uncloud-x-visa.md añade S276, S282, S288 y S293: S276 sin destino; Uncloud, visados y X fuera del bundle, con defectos anotados. comparisons/skills-vue-vite-tinystruct.md añade S278, S281, S289 y S290: sin especialidad Vue ni tinystruct hasta consumidor; dos líneas de Vite a react.md. comparisons/skills-ui-demo-desktop-e2e.md añade S280 y S291: localizar por rol antes de generar el test en qa; E2E de escritorio Windows sin consumidor, defectos anotados. Integradas desde esta comparación: 0; la lectura de las 293 está completa y quedan la revisión operativa de adaptadores/generadores en T-06 y la integración de destinos en T-08. T-03 no está cerrada.
- **Notas**: TDD n/a: prosa/config de comparación, sin modificación de producción. Los consumidores leídos parcialmente no se cuentan como otras piezas evaluadas; las validaciones de activación son estáticas y no acreditan invocación nativa.
- **Historial de bloques**: hallazgos y comprobaciones de S001–S079 (34 viñetas) trasladados sin cambios a [execution-history.md](execution-history.md) («Traslado 2026-10-13 — T-03», SHA-256 `56676ee3f03ac3c677a4caba28286396771aaa3a806c122d61ca56d309768121`).
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.



### T-04 — Comparación de los 68 agentes

- **Estado**: en-progreso
- **Descripción**: Evaluar responsabilidades, procedimientos, permisos y resultados frente a roles propios; distinguir especialidad útil de duplicación de fase.
- **Dependencias**: T-01/T-02.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: 68/68 agentes leídos completos (A001–A068, orden alfabético de `agents/` de la fuente), 17 fichas `comparisons/agents-*.md` con evidencia JSON (hash, bytes, líneas, rangos); comparación por responsabilidad, procedimiento, permisos y salida frente a roles propios citados, sin equivalencias por nombre. comparisons/agents-a11y-architect-explorer.md añade A001, A003, A006, A007: a11y sin destino (web ya en frontend-quality); architect aporta una línea de requisitos no funcionales al analyst; code-architect y code-explorer cubiertos por architect/planner. comparisons/agents-review-cpp-csharp-db.md añade A008, A013, A014, A016: code-reviewer aporta «sigue un llamante» a la Lente B; C++ y C# sin especialidad; database-reviewer aporta EXPLAIN ANALYZE seguro (persona db) y sin credenciales del entorno al reviewer. comparisons/agents-build-resolvers-core.md añade A004, A012, A015, A017: resolutores serían un segundo dueño del código (ADR-011); una línea común en implementer P3 y otra en debug-root-cause; Dart y Django sin especialidad. comparisons/agents-evaluator-simplifier-comms.md añade A002, A005, A009, A010, A011: agent-evaluator ya en outcome-evals; chief-of-staff fuera del bundle; code-simplifier y comment-analyzer sin destino; conversation-analyzer ya en journal.py candidatas. comparisons/agents-java-kotlin.md añade A035–A037: java-reviewer y kotlin-reviewer sin destino (stacks aparcados; lo transversal ya en reviewer, Lente C y backend-practices); kotlin-build-resolver duplica implementer y debug-root-cause. comparisons/agents-php-python-tests-mle.md añade A040, A048, A050–A051: subidas en php-codeigniter.md y argumento por defecto mutable en python.md; pr-test-analyzer cubierto por Lentes A/B, coverage-check y unit-tests; mle-reviewer aparcado. comparisons/agents-network-ops.md añade A041–A043: red aparcada (especialidad de proyecto); del troubleshooter, la hipótesis debe explicar todos los síntomas en la Fase 3 de debug-root-cause. comparisons/agents-opensource-release.md añade A044–A046: fuera del bundle como S193; rotación de secretos ya en cybersecurity; defectos de los cuerpos anotados. comparisons/agents-loop-marketing-perf-planner.md añade A038–A039, A047, A049: loop-operator, planner y performance-optimizer ya integrados (D-110, D-095/D-096, Lente D y D-050); marketing-agent fuera del bundle; el `name: planner` ajeno chocaría con el nuestro. comparisons/agents-stack-domain-reviewers.md añade A018, A022–A024, A029, A032: revisores por stack cubiertos por reviewer, lentes A–D, stack-practices y backend-practices; Django, FastAPI, Flutter, F# y Go aparcados; healthcare-reviewer como persona de proyecto. comparisons/agents-build-resolvers.md añade A028, A030, A034: duplican la fase de implementer y el bucle con debug-root-cause; harmonyos revisa y edita a la vez (ADR-011); dos líneas generales: supresiones y diagnóstico que no escribe. comparisons/agents-gan-harness.md añade A025–A027, A031: arnés GAN ya decidido en S111; planner amplía alcance, generator acepta todo, evaluator decide por nota del modelo; harness-optimizer aporta un antipatrón a plugin-dev. comparisons/agents-docs-e2e-homelab.md añade A019–A021, A033: doc-updater cubierto por documenter (línea de DoD de rutas y enlaces); docs-lookup ya en research-first; e2e-runner ya en qa; homelab fuera del bundle. comparisons/agents-pytorch-react-rust-swift-build.md añade A052, A054, A057, A063: resolutores repiten implementer con el método de debug-root-cause; Rust, Swift y PyTorch aparcados; línea de build para debug-root-cause y de React duplicado para react.md. comparisons/agents-react-rust-swift-ts-vue-review.md añade A055, A058, A064, A067, A068: revisión por lentes, no por lenguaje; Rust, Swift y Vue aparcados; `key` estable a react.md y «promesa sin esperar» a coding-baseline. comparisons/agents-refactor-security-silent-tdd-types.md añade A056, A059, A061, A065, A066: cubiertos por Lente C con nemesis, Lente B, tdd y coding-baseline; borrado seguro en planner P3 y precisión de fallback en la Lente B. comparisons/agents-rag-seo-specminer.md añade A053, A060, A062: RAG especialidad de proyecto; SEO fuera del bundle; de spec-miner, comportamiento actual frente a deseado en analyst. Ningún agente ajeno entra como agente propio (ADR-011): revisores por lenguaje y resolutores de build duplican fases con dueño. Propuestas de línea en integración (T-11). Pendiente: validación funcional de lo integrado.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-05 — Comparación de los 94 comandos

- **Estado**: en-progreso
- **Descripción**: Revisar intención, artefactos y despacho de comandos frente a los ciclos propios; identificar operaciones útiles y callers que cambiarían.
- **Dependencias**: T-01/T-02.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: 94/94 comandos con ficha propia (C001–C094, orden alfabético de `commands/` de la fuente) en 17 fichas `comparisons/commands-c1…c4-*.md` con evidencia JSON; cada comando con intención, artefactos y su dueño propio (ROLES.md), despacho, disparador y un escenario positivo y otro negativo. comparisons/commands-c1-session-tools.md añade C001, C002, C004, C006, C010, C018: aside y auto-update cubiertos por /btw, /plugin update e instalador; checkpoint sin destino (choca con el alias nativo); cost-report y evolve ya integrados (D-086, D-084); ecc-guide como S089. comparisons/commands-c1-cycle-review.md añade C003, C005, C020, C024: build-fix ya integrado; code-review aporta PR remoto y publicación con OK en adversarial-review; feature-dev duplica /dev-cycle; gan-build sin destino (nota del modelo como veredicto). comparisons/commands-c1-stack-wrappers.md añade C007–C009, C019, C021–C023: C++, FastAPI y Flutter sin especialidad; dos líneas neutrales: tuberías que ocultan el exit y goldens/snapshots regenerados. comparisons/commands-c1-epic-coordination.md añade C011–C017: fuera del bundle; usan el issue de GitHub como fuente (al revés que la regla 8); claim/review pueden autoaprobar; lo transversal ya está en delivery-tools. comparisons/commands-c2-stack-build-review-test.md añade C026–C029, C039–C041: build/review/TDD de Go y Gradle/Kotlin sin destino; código a implementer y debug-root-cause, revisión a adversarial-review, TDD a tdd y unit-tests; una fila de stub como rojo válido en by-stack. comparisons/commands-c2-hooks-memory-learning.md añade C031–C037, C042–C043: hookify cubierto por /doctor Automatizaciones, guardrails y ADR-007; instinct-* por knowledge-curation export/import; learn por journal candidatas y el curador; una línea de duplicados en el curador. comparisons/commands-c2-loops-orchestration-misc.md añade C025, C030, C038, C044–C048: harness-audit en /doctor, loops en persistent-workflows y /work-resume; marketing fuera; model-route y multi-backend sin destino; jira aporta la entrada por clave de Jira al analyst. comparisons/commands-c4-review.md añade C073, C076, C080, C082, C084, C094: revisores por lenguaje sin destino (Python y React ya en stack-practices; Rust y Vue sin especialidad); review-pr aporta base/head del PR a adversarial-review; santa-loop sin destino (push automático, código a otro proveedor). comparisons/commands-c4-build-test.md añade C074, C075, C077, C078, C081, C083, C091: quality-gate sin destino (un hook que reescribe choca con ADR-007); build/TDD/cobertura ya integrados; Rust sin especialidad; refactor-clean aporta deshacer solo los cambios propios al implementer. comparisons/commands-c4-session-docs.md añade C079, C085, C087, C092, C093: sesión cubierta por /work-resume y la continuidad; falta `descartados` en el journal; codemaps ya en documenter; update-docs aporta vigencia por git log al documenter. comparisons/commands-c4-catalog-ops.md añade C086, C088, C089, C090: security-scan ya integrado; setup-pm fuera del bundle; skill-create y skill-health sin destino (guardas de escritura propuestas para F2 de /specialize). comparisons/commands-c3-multi-model.md añade C049–C052: el flujo multimodelo duplica /dev-cycle; despacho externo aparcado (D-118/D-119); sin destino; defectos anotados (Y/N contradictorio, bucle sin tope). comparisons/commands-c3-orch.md añade C053–C058: orch-* ya integrados (tdd, D-095); entrada por intención en la Fase 0 de /dev-cycle y lente sin salida = intento incompleto en adversarial-review. comparisons/commands-c3-prd-plan.md añade C059–C061, C069, C071: lienzo del plan ya integrado; evidencia del problema en analyst y patrón real por tarea en planner; el resto sin destino. comparisons/commands-c3-implement-delivery.md añade C063, C067, C068, C070: prp-implement y prp-commit ya integrados; plantilla de PR, base/head y PR existente en la Fase 6 de /dev-cycle; pr/prp-pr rebasan y fuerzan push (sin destino). comparisons/commands-c3-env-instincts.md añade C062, C064–C066, C072: pm2 fuera del bundle; project-init ya integrado; projects, promote y prune sin destino (solo el curador aprueba, nada se borra por edad). Ningún comando ajeno entra como comando propio. 16 propuestas integradas el 2026-10-14 (adversarial-review con PR remoto y lente sin salida = incompleto, Lente B snapshots, tdd stub, implementer pipefail y deshacer solo lo propio, planner patrón por tarea, analyst evidencia del problema y Jira como dato, documenter vigencia por git log, curador duplicados, /dev-cycle clasificación del cambio y plantilla de PR, `descartados` en el journal y /work-resume). Pendiente: validación funcional.
- **Comparación operativa parcial (2026-10-08)**: 18/94 cuerpos de comandos leídos, recursos concretos y límites en comparisons/command-reading-evidence.json; quedan 76 cuerpos y closures pendientes. comparisons/operational-panel-commands.md propone consolidar contexto, diagnóstico, coste y criterios de workflow sobre dueños existentes. Cero fichas globales cerradas, cero integraciones y cero routing nativo probado por esta comparación; no se añaden skills.
- **Ampliación verificada (2026-10-10, bloque24)**: 76 cuerpos nuevos y dos relecturas en cuatro grupos; total94/94. Ocho decisiones estáticas suficientes en planificación y seis en el último grupo, sin aceptación nativa ni integración por analogía; demás fichas conservan recursos/callers pendientes. Las correcciones propias de handoff/estados se documentan en el bloque24, con revisión estática y exports separados de la QA congelada6. No se amplían skills.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-06 — Tools, MCP, hooks, reglas y workflows

- **Estado**: en-progreso
- **Descripción**: Comparar configuración y scripts realmente usados, dependencias y API, ejecución, permisos y aislamiento; evaluar soporte del control panel.
- **Dependencias**: T-01/T-02.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Triaje operativo y valoración de memoria en operational-priorities.md. comparisons/hooks-role-policy.md y role-hook-reading-evidence.json comparan 19 cuerpos completos y un helper parcial, con diferencias y destinos concretos de política previa; quedan 24 cuerpos inmediatos y 16 descendientes de metadata pendientes. No se ejecutó código del corpus. Comparación global, implementación y validación funcional de esos destinos pendientes; la lectura dirigida no acredita eficacia.
- **Paneles/comandos en paralelo (2026-10-08)**: Tres entradas de dashboard y recursos relacionados contrastados por lectura; IDs, hashes, rangos y fuentes propias en comparisons/panel-reading-evidence.json. Propuestas de proyección read-only, procedencia y desconocidos en comparisons/operational-panel-commands.md. Plataforma de readiness, servicios/almacenamiento del control operativo y fuente de observación compatible pendientes; cero fichas globales cerradas o integraciones nuevas.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-07 — Arquitectura y candidatos de memoria

- **Estado**: en-progreso
- **Descripción**: Comparar recuperación, aprendizaje, persistencia y gobierno frente a memoria propia; delimitar los experimentos que exige la fase 4.
- **Dependencias**: Comparación pertinente de T-03 (S053–S054 ya disponible) y recursos de memoria de T-06; no espera a las skills aplazadas.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Decisión del usuario (2026-10-08)**: Aceptada la dirección de memoria en operational-priorities.md: base local canónica, captura/recuperación primero, propuestas con evidencia y revisión, Kwipu como proyección y Graphiti condicionado a medición. No implica backend activado ni tarea completada.
- **Verificación**: Valoración inicial en operational-priorities.md: Kwipu publica/verifica sin consulta enrutada; Graphiti expone consulta con puerta de salud/verificación y respaldo local. Lectura dirigida de adaptadores/router y comparación S053–S054, sin conexiones ni mediciones nuevas. Auditoría completa de mecanismos/casos y benchmark pendientes.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

## Fase 2 — Integración

**Estado**: en-progreso

### T-08 — Diseño nativo de capacidades y workflow

- **Estado**: en-progreso
- **Descripción**: Convertir diferencias verificadas en destinos propios, opcionales y compartidos; cerrar diseño y acotar archivos antes de modificar producción.
- **Dependencias**: Contratos T-02 y comparación pertinente T-03/T-04/T-05/T-06/T-07 por bloque; aceptación global tras completar esas tareas. Hooks/comandos/panel/memoria no esperan al contenido opcional aplazado.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: design.md fija integridad del checkpoint, cierre e instalación y, en el bloque 3, identidad nativa, IDs propios, políticas por rol y migración que preserve personalizaciones. Los mecanismos se prueban en fixtures propias; dispatcher y migración del bloque 3 siguen sin distribuir. Diseño restante de capacidades pendiente; no se declara consolidación global entregada.
- **Diseño operativo en curso (2026-10-08)**: Panel de catálogo, diagnóstico de consumidor y roadmap conservan responsabilidades separadas. Handoff propuesto reutiliza journal/ledger; observaciones requieren fuente compatible antes de tasas. Codex add habilita globalmente aunque el destino sea proyecto; T-09 debe resolver caché nativa respetando el estado global previo, sin remove como rollback ni confundir installed con enabled. Estos destinos y restricciones no acreditan implementación.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

- **Ajuste de personas para T-08/T-09/T-11/T-13/T-15**: el usuario pidió organización por entorno como los agentes y después contrastar los estándares de Codex/OpenCode. [Contraste documental](contracts.md#personas-e-instrucciones-nativas): las carpetas nuevas `.codex/personas/` y `.opencode/personas/` serían convenciones del plugin, no cargadores nativos documentados; la propuesta anterior queda provisional y no se implementará como supuesto estándar. Priorizar agentes e instrucciones nativos para especialistas invocables; conservar perfiles acotados del brief cuando solo complementan un rol, sin agentes duplicados. Mantener compatibilidad de `.claude/personas/` existente. T-08 debe cerrar almacenamiento y composición, selección con runtime all, duplicados, instalación personal, rutas personalizadas y avisos; inventario y brief deben resolver la misma procedencia y conservar sus límites. Distinguir OpenCode V1 agent/prompt de V2 agents/system; no usar personality de Codex para perfiles de dominio. Actualizar panel, documentación y exports con pruebas de carga y contenido efectivo en T-14. Contraste registrado, implementación pendiente.

### T-09 — Guardias y despacho nativo multi-runtime

- **Estado**: en-progreso
- **Descripción**: Implementar mecanismos reales por contrato y versión para Claude/Codex/OpenCode, incluido soporte V2; probar identidad, concurrencia y degradación.
- **Dependencias**: T-02/T-08.
- **Archivos**: `hooks/**`, `interop/**`, `agent-kits/shared/**`, `scripts/**`, `install/**`, `tests/**`, `agents/**`, `docs/**`, `statusline/roadmap-statusline.sh` (comprobación LF/CRLF en el cierre; formato original conservado, sin cambio semántico ni selección de publicación)
- **Verificación**: Dispatcher, IDs exactos, transporte de decisiones y correcciones de rama/preflight verificados en los bloques 3–10; `2a010a2` publicado. QA Windows/Linux y ocho ejecuciones nativas en hook-reliability-qa-evidence.json y hook-native-acceptance-evidence.json. Bloque 11 contrasta publicación canónica OpenCode con siete casos y recuperación de una copia del checkpoint; hook-canonical-capture-evidence.json conserva hashes y límites. Pendientes: bypass de verificación Git, demás reglas/capacidades y aceptación ampliada de carga/TUI. T-09 sigue abierta.
- **RED del bloque de checkpoint (2026-10-08)**: `test_journal.py -k 'capture_respeta_journal_en_forma_objeto or rotar_fallo_conserva_checkpoint or rotar_lee_solo_cola'`: 4 failed/1 passed, 150 deselected. `{activo: false}` creó un log; los fallos simulados de fsync/replace no conservaron el original; la rotación leyó el archivo completo (`read(-1)`). Evidencia obtenida antes de modificar producción.
- **RED de compatibilidad Windows (2026-10-08)**: `test_journal.py -x -q`: 1 failed/4 passed; `test_write_sin_rastro_del_plugin_no_escribe_nada` recibió `docs\knowledge\journal\2026-10-08-sesion.md` en vez de la ruta relativa con `/`. Se amplía el bloque para normalizar la salida CLI, sin cambiar rutas internas.
- **RED de reclamación exclusiva (2026-10-08)**: probe propio con trazas de `os.replace` reprodujo dos movimientos exitosos del mismo origen en Windows (iteración 2); el test de 100 reclamaciones concurrentes falló en la iteración 1 con dos ganadores. El test de cerrojo no disponible también falló: entregó el item en vez de mantenerlo pendiente. Se serializa la transacción de reclamación con cerrojo de SO no bloqueante; pendientes intactos si no se obtiene.
- **RED nativo de instalación/cierre (2026-10-08)**: Instalador real Codex deja marketplace/enabled pero plugin list lo muestra sin instalar; tras add hay contexto/captura, con efecto global comprobado incluso desde false previo. Claude fijado captura UTF-8/contexto pero no deja envelope con presupuesto predeterminado; misma definición con override propio 5.000 ms sí lo deja. Control SessionEnd propio 2.200 ms/timeout 5 cancela por defecto y completa con override. recover sobre checkpoint de sesión nativa terminada conserva el turno como recuperado_sin_cierre, exit 0. Producción intacta; no se aplica workaround chmod con causa no aislada. Evidencia y límites en contracts.md y JSONs nativos.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-10 — Skills opcionales y consolidación de contenido

- **Estado**: en-progreso
- **Prioridad acordada (2026-10-10)**: Retomar la ampliación gradual de skills después de implementar y validar comandos, dashboard, hooks y memoria. La ampliación sigue prevista; no se cancela.
- **Descripción**: Integrar contenido útil de las fichas con referencias y recursos propios; dominios existentes en el corpus, sin paquetes inventados ni carga indiscriminada.
- **Dependencias**: T-08/T-09.
- **Archivos**: `skills/**`, `agent-kits/shared/**`, `evals/**`, `tests/**`, `docs/**`
- **Verificación**: Pendiente: escenarios reales por alta/consolidación, recursos vigentes, tamaño y degradación; mapas sin duplicación ni pérdida. Avance 2026-10-13: [comparisons/skills-destinations.md](comparisons/skills-destinations.md) consolida 157 destinos (13 P1, 59 P2, 38 P3, 47 aparcados por la regla única de stacks sin consumidor). Integrados los 72 P1/P2 en siete paquetes con tests de los scripts tocados (guardrail-check, scope-check, task-brief, review-lens-select, jira-flow, lint_plugin, coverage-gate, to-pdf), lint 0 errores, evals 0 errores, interop al día. P3 integrado el 2026-10-14 (38 destinos: 33 referencias nuevas y 5 scripts con TDD — journal.py candidatas/continuidad, usage-meter.py procedencia, doctor.py automatizaciones, code-health.py excluidos_versionados, evals/check.py casos en-contra); D-109/D-110 sin skill nueva (plugin-dev es dueño). S114 al implementer (git por nombre, merge/rebase, conflictos) y S163 al documenter (inventario y «Retirados») tras la revisión de consumidores operativos. 2026-10-14 (tarde): `continuidad` visible en /work-resume, procedencia del meter agregada en build_dashboard.py, `expect.contains` y primer caso en contra ejecutable (tdd), limpieza de evals en Windows corregida. SessionEnd medido en Windows sin carga: arrancar node cuesta 1-3,3 s (mediana 2,3 s), fuera de 1,5 s; el launcher respeta `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` (hook-budget.mjs, 7 tests) y /doctor lo informa; el usuario lo autorizó el 2026-10-14 (`env` de su `~/.claude/settings.json`, 5000 ms; el cierre real queda por verificar en la próxima sesión). Recuperación temprana de huérfanas por inactividad del log y del transcript (`ventanaInactividadMin`, 30 min) con `log_hasta` para rehacer una recuperación si la sesión siguió; 19 tests. Validación real 2026-10-14/15 con el plugin de la rama (instalado desactivado con `--settings`): (1) deterministas sobre el repo y fixtures — /doctor (presupuesto SessionEnd 5 s, automatizaciones), dashboard (procedencia en 48/48 iniciativas), guardrail (deniega publish/prune/kubectl delete/DROP vía psql; permite dry-run, grep y mensaje de commit), scope-check (criterio reescrito → exit 1 citándolo; marcar casilla → 0), jira-flow (pendiente → reintento con aviso → confirmar → yaRealizado), coverage-gate (Gradle nombrado); (2) activación con `claude -p`: tdd, adversarial-review, debug-root-cause, plugin-dev, jira-sync y research-first activan en sus positivos y no en sus negativos; dos fallos reales corregidos (tdd con «prisa, sin test» y adversarial-review con rendimiento del diff) y tres del arnés (`--add-dir`, `python` en Windows, plugin instalado); ~12 USD; (3) extremo a extremo `quick-implement` sobre una fixture Python (slugify): Skill quick-implement → ledger nuevo → RED `ImportError` → verde → adversarial-review con `review-lens-select` (A+B; C/D no aplican) → gap Important real (separadores no ASCII) corregido con nuevo RED → intento 2 sin gaps bloqueantes → qa (suite + ledger-lint; qa-gate n/a sin test-plan) → ledger `completado`, ledger-lint 0, scope-check 0, 7 passed; sin commit (no pedido). Límites: en `-p` el agente qa recibió Bash denegado y el orquestador ejecutó la QA; usage-meter no usado (horas estimadas). Pendiente: escenario con /dev-cycle completo y con Jira real.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-11 — Agentes, comandos y handoffs coherentes

- **Estado**: en-progreso
- **Descripción**: Integrar procedimientos útiles y despacho en roles/ciclos propios; compartir selección y conservar puertas, artefactos y extensiones del proyecto.
- **Dependencias**: Diseño y despacho pertinentes de T-08/T-09; comandos requieren su comparación T-05. T-10 solo para consumidores de skills concretas; no bloquea el resto de comandos.
- **Archivos**: `agents/**`, `commands/**`, `agent-kits/**`, `interop/**`, `evals/**`, `tests/**`, `docs/**`
- **Verificación**: Pendiente: pruebas de transferencia entre fases, roles y briefs; exports al día y destinos de contenido comprobados.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-12 — Tools e integraciones bajo demanda

- **Estado**: borrador
- **Descripción**: Adaptar recursos ejecutables útiles y configuración MCP documentada al contrato propio, con opt-in y disponibilidad real, sin conectar cuentas por inventario.
- **Dependencias**: T-06/T-08/T-09.
- **Archivos**: `skills/**`, `agent-kits/**`, `scripts/**`, `interop/**`, `tests/**`, `docs/**`
- **Verificación**: Pendiente: fixtures propias, flags/APIs oficiales, permisos y ausencia de efectos del consumidor; instalación parcial comprensible.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-13 — Funciones operativas del panel nativo

- **Estado**: en-progreso
- **Descripción**: Incorporar funciones útiles del control panel comparado al panel propio, con fuentes, métricas observadas y guardias declaradas/contrastadas diferenciadas.
- **Dependencias**: Comparación/diseño T-06/T-08 y contratos de los componentes mostrados de T-09/T-11/T-12; T-10 solo para altas concretas. No espera a todas las piezas opcionales.
- **Archivos**: `skills/plugin-panel/**`, `commands/plugin-catalog.md`, `interop/**`, `evals/**`, `tests/**`, `docs/**`
- **Verificación**: Pendiente: Edge escritorio/móvil/teclado, filtros y navegación, privacidad y ausencia de datos, sin anunciar un snapshot como servicio vivo.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

## Fase 3 — Verificación y cierre

**Estado**: en-progreso

### T-14 — QA funcional, cobertura y revisión

- **Estado**: en-progreso
- **Descripción**: Verificar aceptación completa y eficacia observable por escenario, carga nativa, regresiones, cobertura y revisión independiente por fase.
- **Dependencias**: Verificar cada bloque entregado de T-09/T-11/T-12/T-13; aceptación global tras T-09/T-10/T-11/T-12/T-13, sin cerrar por una entrega parcial.
- **Archivos**: `tests/**`, `evals/**`, `.github/workflows/ci.yml`, `ci.yml.MANUAL-COPY`, `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Ajuste de alcance 2026-10-10**: la QA de curación detectó que la nueva suite de Confluence no estaba enumerada en CI. Se incorporan el workflow y su copia canónica idéntica para que la regresión ejecute en CI; no cambia activación ni servicios externos.
- **Verificación**: Cada bloque conserva su QA por snapshot al final del ledger. Bloque 10: Windows Node 166/Python 287 y Linux Node 154 + 12 skips/Python 287, cuatro qa-gates GREEN y cobertura de diff con método explícito. Bloque 11: 16 controles del observador estricto, siete capturas canónicas nativas y recuperación sobre copia aislada. Las ejecuciones nativas y los casos por plataforma no se suman como unit tests. Pendientes: nuevos escenarios/capacidades de T-09/T-11/T-13, UI Edge y aceptación global.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-15 — Limpieza, distribución y documentación

- **Estado**: en-progreso
- **Descripción**: Retirar recursos y callers sustituidos, refrescar dependencias/manifiestos/exports y docs ES/EN; comprobar referencias y nombres públicos.
- **Dependencias**: Verificación del bloque pertinente de T-14 para docs/exports de cada entrega; aceptación global tras completar T-14.
- **Archivos**: `skills/**`, `agents/**`, `commands/**`, `agent-kits/**`, `scripts/**`, `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `.claude-plugin/**`, `.gitignore`, `package.json`, `docs/**`, `README.md`, `README.es.md`, `CLAUDE.md`, `tests/**`, `evals/**`
- **Verificación**: Cada bloque conserva gates de lint del bundle público, exports, alcance y referencias. `2a010a2`: catorce archivos propios, fuentes/tests/JSON idénticos a sus blobs publicados, export 56 al día y cero referencias públicas prohibidas. El lint local por defecto distingue el error YAML de una nota anterior ignorada, ajena al bundle. Bloque 11 actualiza verificación y evidencias sin cambiar producción. Siguen pendientes recursos restantes y aceptación global de limpieza/distribución.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-16 — Retro, changelogs y publicación comprobada

- **Estado**: borrador
- **Descripción**: Cerrar consumo y resultados sin inventar métricas; sincronizar changelogs ES/EN y publicar la rama con contraste remoto, conservando fase 4 pendiente.
- **Dependencias**: T-15.
- **Archivos**: `docs/**`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificación**: Pendiente: retro/report/ledger, changelog --check y SHA remoto observado; cierre documental publicado después de comprobar la entrega.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

## Qué está entregado y qué falta

Los bloques operativos 1–18 conservan sus pruebas y decisiones en [execution-history.md](execution-history.md).
La entrega más reciente acepta lectura documental opt-in, selectores AST, recibos y productor explícito.
La memoria local sigue siendo canónica y funciona sin servicios externos.

La integración global sigue abierta. La comparación de skills se retomó el 2026-10-13: 293/293 evaluadas. Lecturas parciales completadas ([skills-taste-comply-complete-reading.md](comparisons/skills-taste-comply-complete-reading.md)), 37 afirmaciones contrastadas con fuentes oficiales ([skills-official-contrasts.md](comparisons/skills-official-contrasts.md): 31 confirmadas, 3 corregidas, 3 sin concluir) y consumidores operativos revisados ([skills-operational-consumers.md](comparisons/skills-operational-consumers.md): S114 y S163 a revisar). Destinos P1/P2 y P3 integrados (los 47 aparcados esperan consumidor).
La revisión de planes y los resultados por comentario están implementados en la copia revisada. La QA conjunta, el diagnóstico de instalación Codex y la interacción real del panel conservan su validación pendiente.
Restore, corpus grandes, continuidad, aprendizaje y demás capacidades siguen pendientes.

## Dónde se conserva la evidencia

El historial anterior se trasladó sin cambiar un byte de su contenido.
El ledger conserva íntegros sus dieciséis bloques de tarea, estados, criterios y resumen de progreso.
Las trazas detalladas y tablas de los primeros pases están en el historial; el resultado vigente queda debajo.
Ninguna aprobación se reabrió ni se cerró una tarea por reducir el archivo.

| Gap anterior | Grado | Estado comprobado |
|---|---|---|
| A2: outputs preexistentes | Critical | Corregido y aprobado en revisión2; conservado en revisión3 |
| A1: normalización después del deadline | Important | Corregido y aprobado; guard final y regresiones |
| B1: helper opcional incompatible | Important | Corregido y aprobado; fallo dentro del envelope |
| D1: nuevas lecturas después del deadline | Important | Corregido y aprobado; plazo absoluto compartido |
| A3: contrato negaba RED observados | Minor | Documentación corregida y aprobada |
| B2: score documental perdido | Minor | Alias numérico finito conservado y aprobado |

## Revisión de dos lentes — intento 3: Bloque18 (T-07/T-11/T-13/T-14/T-15) — sin gaps nuevos o reabiertos

Cuatro lentes A+B+C+D de contexto fresco revisaron íntegro el delta de14 archivos/2411 líneas. Se conservaron la tabla completa de20 criterios y las aprobaciones anteriores; ningún gap de producto fue rebatido. Resultado fusionado:0 Critical,0 Important,0 Minor pendientes. Fuente pública congelada:970 archivos,42 cambios; manifest `0ebbb8313c63897d549d015590c22e4047a74e2293946f104412a5ed3e61334e`. Los hashes de producción y pruebas actuales coinciden con esa fuente.

A:34 pruebas/18 subtests y dos payloads UTF-8 exactos; B:76 pruebas/18 subtests; C y D revisión estática. Son cohortes separadas y no se suman. D conserva D1 corregido porque seis módulos pertinentes siguen idénticos. Q1–Q4 conformes; las adiciones Q5 son pertinentes, pero la cobertura final sigue pendiente.

- A: `928b11c378de87c970b5222ba6cb0810bff4a091a2a547b60109b94cf592c973`.
- B: `0a282ae3c290c4862bb42d39247b791dfb75bf716861942b4676606a0c99737b`.
- C: `70ab48dee42d341117e239500890488d345dbb982bacccb671cb888354ac079e`.
- D: `0ab37da41c2702f1fde3133607bd1bdadc21f9206eea8c011b98671c96d56c03`.

Aceptación de revisión, no verde QA. Se preservan los fallos Windows/Linux y los dos gates originales inferiores al90%. Los checkpoints nativos actuales documental y AST siguen siendo pruebas funcionales separadas. Quedan QA completa en ambas plataformas, las dos métricas oficiales>=90% y publicación. Ninguna tarea macro se cierra por esta revisión.


Evento de revisión3 ejecutado sobre fixture propia Jira desactivada: exit0,0 operaciones; no se consultó configuración del consumidor ni se publicaron mensajes. Stdout SHA `637579da152352acacb582fde8ae1032ab614bf5ddec25a32b0133caeef6c50f`; ledger propio SHA `ffe1859b2444e8d8757703a76ad94b4337858ecd7288a5a86e56b0badd50ebfa`.

| Detalle | Fuente |
|---|---|
| Registro íntegro | [Historial](execution-history.md) |

## Bloque18 — QA final aceptada y cierre de implementación

Registro histórico: [detalle original](execution-history.md).

## Bloque18 — publicación comprobada

Registro histórico: [detalle original](execution-history.md).

## Bloque19 — integración de revisión visual en curso

Registro histórico: [detalle original](execution-history.md).

## Bloque19 — regresiones de normalización antes de corregir

Registro histórico: [detalle original](execution-history.md).

## Revisión de dos lentes — intento 1: Bloque19 (T-11/T-13/T-14/T-15) — correcciones pendientes de validación

Lentes A+B+C+D sobre 28 archivos y 978 hashes de fuente. C usa el informe estático independiente de reemplazo; su primer informe fue interrumpido por un filtro automático. B conserva un addendum del error de serialización. Tres gaps Important tras fusionar la misma raíz B/C; no hay Critical ni Minor. Ningún resultado de revisión acepta QA.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Faltaba traza RED canónica | T-11/T-13/T-14 | Registrar las observaciones previas existentes, con procedencia | RED por criterio abajo; 35 assertions del dueño, dos errores de harness excluidos; pendiente de validar |
| A2 | Important | Faltaba salida del check de interop | T-11/T-15 | Registrar exit y stdout del check real | `export-interop --check: 58 ficheros al día`, exit 0; pendiente de validar |
| BC1 | Important | El saneado posterior a redacción exponía texto y volvía inválido el recibo | T-11/T-13/T-14 | Sanear controles antes de redactar vista y comentarios | Diez RED/GREEN dedicados y 156 vecinos GREEN en Windows; pendiente de validar |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 2: Bloque19 (T-11/T-13/T-14/T-15) — implementación aceptada

2026-10-10. Lentes A/B/C/D independientes de contexto fresco, fallback genérico porque el revisor nativo no está disponible. Los informes conservan los criterios aprobados del primer pase y revisan los cinco archivos corregidos; no hay rebatidos. Fuente sellada: 978 archivos públicos, 28 en el diff; manifest SHA `1764fcaa55ddfd015419fa1a74a4c78a7cb8a10f1b48a35b725a3d286bbf84ce`, diff SHA `84d89fed1281c2f9d849a402f847d3d6be89a48a854d592e310109c3d4068ffc`. Los hashes antes/después coinciden. Los tres Important anteriores quedan corregidos y validados; 0 Critical, 0 Important y 0 Minor pendientes.

| Hallazgo anterior | Validación independiente |
|---|---|
| A1: trazas RED canónicas | A valida identidades, errores, fecha y procedencia individual; conserva la distinción entre capturas y resumen atribuido del autor. |
| A2: evidencia interop | A ejecuta un check propio: exit 0, stdout `export-interop --check: 58 ficheros al día`, stderr vacío; 978 hashes intactos. |
| BC1: saneado antes de redacción | B valida la corrección con 14 pruebas del dueño y 12 probes independientes; C la valida estáticamente con CWE-180/200. No se suma este checkpoint a QA. D conserva su aprobación de rendimiento sin repetir por rutina el benchmark. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 3: Bloque19 (T-11/T-13/T-14/T-15) — sin gaps pendientes

2026-10-10. Lentes A+B+C+D de contexto fresco, fallback genérico por revisor nativo no disponible, sin override de modelo. Se conservan todos los criterios y aprobaciones anteriores; el delta revisado contiene registro de consola y dos archivos de evidencia. Los otros 975 archivos, incluida toda producción, conservan sus bytes. Fuente sellada: 978 archivos, 29 en el diff; manifest `834bb1e2050939a9ca6336cd9923e65fe58d0ced1209169e9b2ba2491b7d3d62`, diff `5259c025108e39b807fb3f8b3d90d682cc19d3efe18c97623258d759cfb011a7`. ROOT verifica informes, artefactos declarados y coincidencia de fuente con el árbol. Resultado: 0 Critical, 0 Important, 0 Minor pendientes; ningún gap rebatido o convertido en deuda.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important histórico | Trazas RED canónicas | T-11/T-13/T-14 | Corregida en R2, conservada | A mantiene IDs, errores, fechas y procedencias individuales. |
| A2 | Important histórico | Prueba de exports en ledger | T-11/T-15 | Corregida en R2, conservada | A3 ejecuta check propio: exit 0, stdout `export-interop --check: 58 ficheros al día`, stderr vacío; 978 hashes intactos. |
| BC1 | Important histórico | Normalización después de redacción | T-11/T-13 | Corregida en R2, conservada | Dueño y regresiones mantienen bytes aprobados; B/C no encuentran evidencia de reapertura. |
| Consola | Fallo QA de registro | Cuatro casos cp1252/ascii sin modo para el dueño | T-11/T-14/T-15 | Registro operacional con fixture Unicode propia | A valida traza RED previa y límites; B verifica cuatro casos y dos probes de pipes, sin sustituir QA. C/D no encuentran vulnerabilidad o carga nueva. |

| Plataforma | Passed | Failed | Skipped | Subtests separados |
|---|---:|---:|---:|---:|
| Windows | 2678 | 4 | 43 | 45 |
| Linux | 2698 | 4 | 23 | 45 |


Detalle y pruebas originales: [historial](execution-history.md).

## BLOQUE20 — conservación y recuperación de memoria local

Registro histórico: [detalle original](execution-history.md).

## Revisión de dos lentes — intento 1: Bloque20 (T-08/T-09/T-14/T-15) — dos gaps pendientes

2026-10-10. Lentes A+B de contexto fresco, fallback genérico por revisor nativo no disponible, sin override. Selector sobre el diff real: C=false/D=false, sin avisos. Scope oficial exit0:16 archivos en alcance, cero fuera/exclusiones del usuario/avisos. Ledger-lint:0 incoherencias/0 avisos. Fuente983 y diff sellados; ambos revisores comprobaron983 hashes antes/después. No ejecutaron pruebas ni producto. Se conservan QA19 y todos los criterios aprobados anteriores; no se cierra ninguna macro.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | El contrato no distingue el plazo de admisión de420s de una duración total | T-09/T-14/T-15 | Se aclaran admisión, barrera25s, finalización30s y recogida5s; pendiente validación independiente | Contrato:50 y harness:257/290/312/419 en fuente revisada. |
| AB1 (A2/B1) | Important | Resolver antes de rechazar oculta raíces/ancestros enlazados y destinos colgantes dentro de OWN | T-08/T-09/T-14 | Corrección y regresión del soporte sintético en curso; no se afirma fallo de backup de producto | protocol.py:34/132/184; ningún caso nuevo ejecutado aún. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 2: Bloque20 (T-08/T-09/T-14/T-15) — sin gaps pendientes

2026-10-10. A+B frescos, fallback genérico sin override. Ambos informes completos y sus verificaciones se contrastaron por ROOT; fuente985 idéntica antes/después, FULL18 diff, scope/selector/ledger oficiales exit0 y cero avisos/exclusiones. C=false/D=false. Se conserva el traspaso R1 íntegro, sin reabrir aprobados, sin rebatidos ni deuda.

| # | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Plazo de admisión ambiguo | T-09/T-14/T-15 | Corregido: contrato precisa420s de admisión y25/30/5 propios; no promete duración total | A2 contrato:50–55, harness:257/290/312/377/405/419. |
| AB1 (A2/B1) | Important | Alias oculto por resolve anterior al rechazo | T-08/T-09/T-14 | Corregido: lstat léxico de hojas y ancestros antes de resolve; seis regresiones dedicadas preservan árbol completo | A2/B2 protocol:34–49; test_protocol:102–156; RED/GREEN de autor conservados. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 1: Bloque21 (T-11/T-13/T-14/T-15) — corregir retoma entre runtimes

Lentes A+B de contexto fresco, fallback genérico sin override de modelo; selector C/D false por diff real de14 archivos, sin avisos. Scope0/interop0 (58 archivos al día)/ledger0 previos; fuente988 y diff completos estables. A:0 gaps; B:1 Important. Report A SHA `54d558e1581b6f415972b8d9e68bda1332089c179fc333e63de1a4559c94d12c`, receipt `d086b732df62d8260377f48b1189c5c76c6419571271401d0afa7f1d83dfd11c`; report B SHA `2f6aeb6e7428c409cc97d39e979e73f5afde5c1d087de5bf60a1f894577c2a01`, receipt `d8f1909453f47627da5c4b67635407d1c5e47f8d6ffc95ba72ec9807c0f0dc8a`.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Caller exige consumidor actual al reabrir recibo histórico | T-11/T-13/T-14 | Validar selección/puerta/versión; tratar registro de consumidor como histórico, sin exigir coincidencia en retoma | Reproducción ROOT: codex→claude-code y panel sin registro→caller mantienen mismo ID, versión completa/current y consumidor anterior/null. SHA `d48e5f7f607b7af74ce1a1fb40a32f8e30e85aa1a2c8ca4d7692e2f4365730ae`; owner intacto. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 2: Bloque21 (T-11/T-13/T-14/T-15) — prueba dedicada pendiente

2026-10-10. A+B frescos, fallback genérico sin override; scope0/exact14, selectorC/D false, interop0/58 y ledger0. Fuente988 y diff completos idénticos antes/después. A2:0 Critical/1 Important/0 Minor; B2:sin defectos. El comportamiento de B1 concuerda con el dueño, pero la constitución:13 exige una prueba dedicada que nombre y compruebe cada gap corregido. No hay rebatidos ni deuda; las aceptaciones anteriores y macros se conservan.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A2-1 | Important | B1 figura corregido sin regresión dedicada de la regla actual | T-11/T-13/T-14 | Validador de apertura ejecutable sin estado; pruebas B1 sobre dueño real y transporte shell | Informes A2/B2 y hashes completos en la evidencia; pendiente revisión3. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 3: Bloque21 (T-11/T-13/T-14/T-15) — límites JSON pendientes

2026-10-10. A+B+D frescos, fallback genérico sin override; scope0/exact16, interop0/58, ledger0 y fuente990/diff íntegros. C=false; D=true por heurística regex-en-bucle, descartada por D con evidencia de compilaciones fuera del bucle. A3 acepta A2-1 y conserva B1; B3 introduce1 Important/1 Minor, D0. ROOT leyó los tres informes completos, verificó hashes y reprodujo ambos casos. No hay rebatidos ni deuda.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B3-1 | Important | 1e999 llega como infinito en metadata ignorada y valida ok | T-11/T-14 | parse_float comprueba finitud antes de aceptar el número | Probe real:782 bytes/exit0/statusok; pendiente validación correctiva. |
| B3-2 | Minor | JSON muy profundo termina sin envelope | T-11/T-14 | RecursionError devuelve unavailable/exit2, conservando rechazo | Probe real:12000 niveles/24001 bytes/exit1/RecursionError, sin aprobación ni serve. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 1: Bloque21 · ciclo correctivo 2 (1 de 1; cuarto pase acumulado)

2026-10-10. Cuarto pase acumulado explícito después de los tres intentos iniciales, cuyo historial permanece intacto. A+B+D de contexto fresco, fallback genérico sin override; C=false y D=true por la misma señal heurística, descartada con evidencia estática. ROOT leyó los tres informes íntegros y verificó sus SHA, recibos y fuente990 antes/después:0 Critical/0 Important/0 Minor. B3-1 y B3-2 corregidos y aceptados; B1/A2-1 conservados. Sin rebatidos ni deuda.

Lente A: informe SHA `2d691b32cdfb5d0054d501cc8c10c947948f2866280dfb3f4f85f61222dce848`, recibo `f9c7a3f15055df87bcffb11895eab3eafafdca024ae961cfdfe8ec7153b0e5ca`.

Lente B: informe SHA `b5e2fab162dadb03f6a353f6cdc4b1903f04c00f180bfd1000584703ad85dde3`, recibo `9aec586ac7c1a472744cff67247823a8df2616127fb16fa232cf99ca5f031361`.

Lente D: informe SHA `7d518b2502adef0862adbc6472037640569174e7309c0434c7e751cf57f77f82`, recibo `3f99402314f52a9959e36450f7295d500acb87c6ab23aaabf98b8e7f08e46033`.

Fusión ROOT SHA `8ead037e75b9bc9e4ec74557a6e17d47c1fb0bd89415ccbc97379a83a4d58b4b`; fuente de revisión `edfef7a43df7d19115bd935e804455f9333964df7506c16b7f07391c49401bd9`. Esta aceptación corresponde a revisión del código congelado; no acredita QA visual, clientes nativos ni cierre global.

### Aceptación acotada de Windows

ROOT verificó los siete inputs del GREEN final contra la fuente revisada y los52 casos únicos de JUnit, más una colección independiente sin ejecutar de nuevo las pruebas. Resultado52 passed/0 failed/0 skipped;26 del validador,13 Bash y13 PowerShell. El qa-gate oficial aplicado a esos resultados reales convertidos terminó exit0/VERDE, SHA `a2b547b43ddf08c5879ee0361450fe77ad940fda64ba98e77a728a63a32d6c4e`. Recibo de aceptación SHA `f999c30eb5aa789a2df726b0740180e31caed6ed8ba82ea2dee7f9dc6166ffd2`. La conversión es de pruebas unitarias/shell y no se presenta como Playwright o aceptación de navegador.

El ensayo Linux del bundle final está en preparación; no se acredita todavía PASS ni SKIP. Los checks estáticos previos pasan con fuente990, exports58 y53 enlaces válidos; el lint de aquella copia aislada emitió5 avisos, uno por no resolver Git en PATH y recurrir a os.access para hooks/hooks.json. El índice ROOT confirma modo100644; los checks finales expondrán Git en el entorno propio para medir ese criterio correctamente. No cambia producto para ocultar el aviso. UI real de Edge, carga/continuidad nativa, comprobaciones finales y publicación permanecen pendientes. No cambia ninguna de las16 macros ni QA19/20, y el catálogo de skills permanece aplazado.


### Aceptación acotada de Linux y comprobaciones finales del Bloque21

Linux final:39 passed/13 skipped/0 failed/0 errors, pytest exit0. Los26 casos del validador y13 Bash pasan; los13 PowerShell se omiten por ejecutable ausente y no acreditan aceptación de ese shell en Linux. ROOT contrastó190 artefactos por bytes/SHA, los52 IDs de colección/JUnit, siete inputs ligados a GREEN/revisión y43 hijos registrados terminados. Sólo el contenedor propio fue retirado y su ausencia exacta se verificó. JUnit SHA `2520a688498ce712cb21ad6307905473b0cebefa9fe1039a564d0f9a814da38f`; recibo ROOT `108959646c1948a1ef1481392454555f1bd36d46d2f9748db725c65982537035`; qa-gate oficial exit0/VERDE, SHA `bb9859f3985b0465d212264c4d05bb2d2de3b8c1c77129a0b7bbd242a39cac62`. No se ejecutaron de nuevo las pruebas ni contenedores al verificar.

Se conservan dos fallos de auxiliares privados: el primer check estático intentó crear un directorio de entorno ya existente; el primer verificador Linux esperaba la frase Docker No such object y el artefacto real decía No such container para el CID exacto. Correcciones sólo del transporte/verificador, sin cambios en producto/oráculos ni repetición de pruebas. Los checks estáticos recuperados pasan:scope0/exact16, exports0/58, ledger0, evals0 y lint0 errores/4 avisos,53 enlaces válidos y16 estados macro sin cambios. La diferencia respecto a los5 avisos iniciales es la resolución real de Git para comprobar el modo100644 de hooks/hooks.json.

Checkpoint estático fuente SHA `1002b0c7c74b3ee83d636f65fffa1f5c4b8957a3e2717fef4ecd193fddd764bb`; recibo `f475a5c14b39222918b809afd818b5099c2aace4a1e495c0db23cce03a16b164`. Código, recetas, tests y proyecciones idénticos a la revisión correctiva; sólo tasks/evidence añaden resultados observados. Se acepta esta entrega portable, sin aceptar UI de Edge, carga/continuidad real en tres clientes, QA global o tareas macro. Se verificará el cierre documental y el push en la rama autorizada antes de registrarlos como observados.


### Publicación observada de la implementación portable del Bloque21

ROOT observó y verificó el push normal del commit `b5932849649db8294bdbe9053c64ae53d496dd2a` a feat/catalog-capabilities; HEAD remoto coincide. Recibo SHA `b7829dce6afb8f0f8d6a3bb99897da5aa177bbcebd1803fbb0bae3a034cb5c33`. Antes de publicar, los cinco gates estáticos pasaron sobre fuente990 y los16 archivos explícitos:scope, exports, ledger, lint y evals;53 enlaces válidos, código/proyecciones idénticos a revisión y estados macro conservados. Fuente final SHA `aa1826dc6a5ca833a405908b6037aa4aa5e9cc2367c4e568ed729aea2e7cd131`; recibo estático `37799fca2384e1b8dbcb4f19c1007cf549ef3e9a0a38514e65e51830cc137d9a`.

Esta publicación entrega la validación de apertura y las recetas portables aceptadas en Windows/Linux; no cierra UI real, carga/continuidad de agentes en tres clientes ni el objetivo global. El navegador Edge conserva su bloqueo sin escenarios aceptados. El cierre documental toca sólo tasks/evidence, pasa sus comprobaciones propias y se publica después de observar la implementación; su propio push se verificará tras ejecutarlo. QA19/20 y16 tareas macro permanecen iguales; skills aplazadas.

| Detalle | Fuente |
|---|---|
| Registro íntegro | [Historial](execution-history.md) |

## Transporte nativo de comandos — Bloque22 en preparación

Registro histórico: [detalle original](execution-history.md).

## Revisión de dos lentes — intento 1: Bloque22 (T-09/T-11/T-14/T-15)

2026-10-10. A+B+D de contexto fresco, fallback genérico sin override; C=false/D=true. Fuente1023 y diff73 conservados por los revisores, exports88 idénticos. ROOT leyó los informes completos y verificó sus SHA y recibos:1 Critical/1 Important/0 Minor. No hay rebatidos ni aceptación.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | B-01: cambio de CODEX_HOME conserva claims externos y uninstall borra bytes personales | T-09/T-15 | Corregido y aceptado en intento2: liberar claims externos con límite del bundle explícito | RED1/GREEN1 y regresiones12; conserva históricos editados y ownership interno |
| 2 | Important | A22-1: índices ES/EN muestran invocación antigua no instalada | T-11/T-15 | Corregido y aceptado en intento2: invocación nativa cualificada en ambos índices | RED6P2F/GREEN8P de los ocho documentos con nombres resolubles |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 2: Bloque22 (T-09/T-11/T-14/T-15)

2026-10-10. Segundo pase de un máximo de3; A+B+D frescos, fallback genérico sin override. C=false/D=true. ROOT lee tres informes completos y verifica hashes/recibos/fuente1023/diff75 y probe directo:1 Critical/1 Important/0 Minor. B-01/A22-1 corregidos y conservados; no hay rebatidos ni aceptación.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | B22-2: uninstall directo legado elimina prompts externos editados | T-09/T-15 | Corregido y aceptado en intento3: liberar claims antes de contar/borrar/podar | Probe real exit0/legacy_exists=false y fuente intacta |
| 2 | Important | A22-2: cabecera y tabla nuevas no las leen brief/Jira | T-11/T-14/T-15 | Corregido y aceptado en intento3: cabecera canónica, seis columnas y # numérico | Header no casa; tabla4 columnas/ID no numérico omite ambas filas |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 3: Bloque22 (T-09/T-11/T-14/T-15)

2026-10-10. Tercer pase de un máximo de3; A+B+D de contexto fresco, fallback genérico sin override; C=false/D=true. ROOT leyó íntegros los tres informes y verificó sus recibos, todos los hashes declarados y fuente1023 intacta:0 Critical/0 Important/0 Minor. B22-2/A22-2 corregidos y aceptados; B-01/A22-1 conservados. Sin rebatidos ni deuda. Se acepta exclusivamente el diff75 del código/documentos congelados, no la continuidad nativa, UI, integración global o tareas macro.

Informes A/B/D SHA `68105e3944d3d34489c522fd7da9852c807881d98299d770c1d1c23199a33e9f`, `89b2e64ebf9d39bc99d6c11a608c9302bf8127b365200465ac57df1abc502fe0`, `38f65fa8295b85368bff1fb958bd02cfcfe1c8854333608e0171e990f82897f5`; recibos `ffa913cf796507a6fb8a849f161ef1dc31c7f4a0aa0bcace3e8b78c79857f8eb`, `16bb8e8cae451b3ab2f906cf76b55fd0b423a7422efb6ad4788d75d7328eb3f8`, `433c9d1d12e7868c1646990708ed503d8d70b03e90dd0efc2d9dfe986dc1d620`. Fusión ROOT SHA `a74bd1c4543d815857f85e8d02d0ad36345b4e54f6f07a958c7ec24d709d050a`; fuente `d0b95ef1f9166a71e509db77ac95efdf63094af9e098b464782d257460d49539`, diff `b762855ccefdf09db2da0e337c1b6f9cff3c77f4aa532c8b70c1455761354914`. Export propio A exit0/88; probe independiente B project/user conserva bytes externos históricos/actuales/personales y limita dry-run/retiro al bundle. Los fallos privados de conteo rename/path, import aislado e inventario por cwd se conservan; se corrigieron sólo auxiliares propios, sin repetir probes ni cambiar producto.

### QA congelada acotada del Bloque22

Windows:57 passed/1 skipped Python y14 hojas passed/0 skipped Node;0 failed/errors, ambos procesos exit0. JUnit SHA `cc9dbcfb05d8ee3dbd4d783394c78c1708b659584d7df97403c8b8a8e5761338` y `d6fa184f329dbe00244a5da3e27b58e4e4ea62f158cf5eb41160064c11d906ba`. El skip de enlace simbólico por permisos no acredita ese guard en Windows. Linux:58 passed/0 skipped/failed/errors, exit0; JUnit SHA `c8463b73636961b92f17a13ac41408cb1d351b1c67ef53b5b1a73678c834993d`. Incluye el caso de symlink; no se ejecutó el instalador Node en Linux. ROOT verificó los58 IDs Python iguales entre plataformas, colección real y reportes por caso Linux, fuente1023 intacta y procesos registrados terminados. El contenedor exclusivamente propio, sin red, se retiró y su ausencia exacta se observó; no se tocaron servicios del usuario.

qa-gate oficial sobre resultados reales convertidos:Windows VERDE/exit0 con71 passed/1 skipped, SHA `b35b3e5ba6f4481dc0b240f53654c35e0db4e0bff599107a2614c5041c3d114d`; Linux VERDE/exit0 con58 passed/0 skipped, SHA `f56efab6c9168c38397da371da99ac516ae7461d77b701f2668fb7b9b743eac5`. La conversión JUnit es de pruebas unitarias/instalador y no se presenta como Playwright ni aceptación de navegador. Recibo de verificación ROOT SHA `4149b37ddbd52a921cb47ad50da5756683c1cce8b60f58d107fffc6c0c7a0259`. Se conserva el fallo inicial del verificador que exigía un log de subprocess opcional: no hubo eventos de subprocess en las dos pruebas Linux; se corrigió únicamente el lector, sin repetir QA.

Código, tests, recetas y proyecciones quedan ligados a revisión3. Se preparan comprobaciones documentales finales y push en la rama autorizada. Carga del adaptador real, lectura completa de referencia, workflow/plan UI y continuidad en tres clientes siguen pendientes; no se inventa cobertura ni aceptación global. Las16 macros, QA19/20/21 y catálogo de skills aplazado se conservan.


### Publicación observada del transporte de comandos del Bloque22

ROOT observó el commit `c03f5ff34aa65881998758546ccbabb46921f7b3` y su push normal a feat/catalog-capabilities; HEAD remoto coincide. Recibo SHA `de8363ac00e57aa01195b3f5247e04b595ae49696e9d1529424ed972d2344520`. El índice incluyó sólo las90 identidades de ruta del diff75 revisado; el índice quedó vacío y los1023 hashes públicos permanecieron iguales. Código/tests/proyecciones son idénticos a revisión3; sólo tres documentos registraron revisión/QA posteriores. Fuente final SHA `e34c9b5ee649c256374b90464eeefbc07a939950a63fda359754294f95610cde`, recibo estático `e49eacd9e43901e985afb7d1acfb70207e0f48251d34909e5e76d408b8dd7f40`:scope exact75 sin avisos/exclusiones, exports88, ledger0 incoherencias/1 aviso histórico, lint0 errores/8 avisos conocidos y evals0 (52 archivos/188 casos de validación).

Checkpoint documental independiente conforme:18 enlaces nuevos/cambiados válidos,16 estados y prefijo histórico QA19/20/21 intactos; recibo SHA `b6c5cd3f806b3a6739140dc0dc25079e2e675d13ffd9f0693bb35eb436210441`. Se conservan fallos privados de regex/reparación y comparación de modo: la copia de sólo archivos había perdido100755 de install.mjs, pero ROOT conserva el modo anterior verificado y todos los blobs coinciden. Dos pushes iniciales exit128 por autenticación no disponible en el entorno aislado permanecen registrados; el push normal final usó el helper de credenciales GitHub CLI ya configurado, sin leer/imprimir tokens ni cambiar configuración/iniciar sesión. No se cambió producto ni se repitió QA.

Esta publicación entrega los15 adaptadores generados de comandos Codex y preserva prompts externos durante actualización/desinstalación, incluidos homes históricos. No incorpora nuevas skills del catálogo. El cierre documental de tasks/evidence registra únicamente hechos ya observados y se publica con comprobaciones propias; su push se verifica después. Carga real del adaptador, lectura de referencia, workflow/UI y tres clientes siguen pendientes. No cambian las16 macros ni QA19/20/21 y no se concede aceptación global.

| Detalle | Fuente |
|---|---|
| Registro íntegro | [Historial](execution-history.md) |

## Bloque23 — Curación única de memoria (T-07/T-08/T-11/T-14/T-15)

Registro histórico: [detalle original](execution-history.md).

## Revisión de dos lentes — intento 1: Bloque23 (T-07/T-08/T-11/T-14/T-15) — corregir cinco Important

Lentes frescas A+B por subagentes genéricos; reviewer nativo no disponible.
Selector oficial C=false/D=false, sin avisos. ROOT leyó ambos informes completos,
contrastó los cinco hallazgos con fuente/reproducciones y los aceptó sin rebate.
0 Critical/5 Important/0 Minor. A aporta conformidad; sus ✓ no anulan los
defectos concretos reproducidos por B. Ninguna macro se cierra.

Tabla completa de criterios A sobre la fuente de revisión1:

| Criterio | Veredicto A | Evidencia / límite |
|---|---|---|
| Tareas hechas y criterios | ✓ | Sólo T-01 completada; no cambia su verificación. |
| Alcance del plan | ✓ | 65 rutas declaradas; scope sin exclusiones, avisos ni fuera. |
| Tests y oráculos reales | ✗ | IO real; falta consola obligatoria A23-1. |
| Constitución explícita | ✓ | Ownership/stdlib/redacción y límites declarados. |
| Verificaciones de tareas cerradas | ✓ | Ninguna macro nueva completada. |
| Generado / E2 | ✓ | Check propio A PID32344, exit0, 88 al día; sin cliente nativo. |
| Descriptores / E3 | ✓ | ROLES/CONTRACTS/E13/E14/E22/E53/E54 y espejos actualizados. |
| OpenAPI | n/a | No spec OpenAPI modificada. |
| Docs-style como gate de prosa | n/a | Bloque de persistencia con pruebas; no prosa exclusiva. |
| Corte prospectivo/legado | ✓ | Sin migración, reaprobación ni borrado. |
| Persistencia compartida/juicio Curator | ✓ | Productores proponen; Curator decide; servicio persiste. |
| Propuesta redactada/portable/exclusiva | ✓ | Límites, SHA y reserva; B3 detecta compatibilidad larga. |
| SHA/metadatos finales | ✓ | Índice/ID/versión/taxonomía; B4 detecta secreto en diagnóstico. |
| needs_changes/reject/replacement | ✓ | Original ligado a SHA y rechazado terminal. |
| Gate puro/reglas comunes | ✓ | Sin mutación; gate0 no es transición. |
| Intención/recibo/recover | ✓ | Cortes de checkpoint; B1 detecta corte interno de enlaces. |
| Concurrencia/IO/OS | ✓ | Cooperantes y límites; skips Windows no acreditan guards. |
| Productores/fallback/retro tardía | ✓ | Handoff o pendiente visible, sin autoaprobación. |
| Bridge Gold/store | ✓ | Gold/config/hash; B3 prueba ID válido máximo no cubierto. |
| Journal episódico | ✓ | Estado/fuentes y ausencia de promoción automática. |
| Confluence y staging | ✓ | Exclusión antes de include; sin publicación real. |
| Honestidad RED/GREEN/QA | ✓ | Fallos/skips preservados; aceptación final pendiente. |
| Consola de piezas nuevas | ✗ | Snippet y MODOS ausentes A23-1. |
| Rama/publicación/macros | ✓ | Sin PR/release/main ni cierre global declarado. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A23-1 | Important | Consola: snippet rules y MODOS ausentes | T-11/T-14/T-15 | Snippet literal, módulo puro medido y stdin/JSON/emoji reales cp1252/ascii; pendiente revisión2 | RED11 fallos; GREEN20 sin skips. |
| B23-1 | Important | recover bloqueado con nlink2 de intención/recibo tras enlace antes de limpieza | T-08/T-14 | Registro liga staging e identidad; sólo limpia el enlace exacto validado, rechaza ajenos; pendiente revisión2 | RED dos cortes internos; GREEN con recuperación doble y contraejemplos ajenos. |
| B23-2 | Important | Curator generado ordena no escribir y derivar al implementador | T-11/T-15 | Exportador declara persistencia por servicio/Bash y límites reales; edición directa denegada; pendiente revisión2 | RED Codex/OpenCode; GREEN y 88 exports al día. |
| B23-3 | Important | Gold válido de nombre histórico157 excede destino128 | T-08/T-14 | Slug acotado/hash completo, aliases sólo comparación en cuatro árboles; ruta/SHA real en handoff; pendiente revisión2 | RED seis bridge y contrato aliases; GREEN nombres ordinarios/Gold/store intactos. |
| B23-4 | Important | Categoría/ID inválidos muestran secreto en errores | T-08/T-14 | Redactor compartido en diagnóstico; sin él nunca emite bytes crudos; pendiente revisión2 | RED categoría/ID; GREEN mismos códigos y corpus intacto. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 2: Bloque23 (T-07/T-08/T-11/T-14/T-15) — corregir un Important de rendimiento

Contexto fresco A+B+D, selector C=false/D=true. Revisor genérico; tier
opus/high comunicado desde frontmatter, sin override ni configuración consumidora.
Fuente inmutable1029, diff68/6577; ROOT leyó informes completos y verificó
23/88/119 artefactos, recibos, entradas y todos los hashes de la fuente.
El primer verificador auxiliar ROOT falló al tratar SHA null de archivos
nuevos como hashes de baseline; corregido a comprobar ausencia exacta. No
ejecutó producto ni altera dictámenes. A y B:0/0/0; D:0 Critical/1 Important/0 Minor.
ROOT acepta D23-1: el coste está reproducido y nace de recargar contenidos
históricos completos bajo el cerrojo. Los cinco Important previos quedan
corregidos; no se reabren conformidades aprobadas ni hay hallazgos rebatidos.
Ninguna macro se cierra y QA no comienza con un Important pendiente.

Tabla completa A del intento2 (referencias relativas a su fuente congelada,
sin convertir pruebas comunicadas en QA propia del revisor):

| Criterio | ✓/✗ | Evidencia y límite |
|---|---|---|
| T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: sólo T-01 completada, tres criterios y verificación corpus preservados. T-02…T-16 abiertas/borrador; no se reacepta comparación global. |
| Alcance del plan | ✓ | `tasks.md:204,248,281,292`: Archivos cubre servicio/kits/callers/docs/tests/interop. ROOT comunica scope oficial68/0fuera/0avisos/0excluidos. Las68 rutas verificadas implementan o describen curación; la aclaración F2 sólo retira falsa entrega de memoria/especialización. |
| Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:106–194,195–702`: IO real, cortes/contraejemplos, redacción, aliases y estado legado. Bridge `skills/training-data-services/scripts/test_propose_from_case.py:603–701`; consola `tests/test_console_encoding.py:730–770`; export `tests/test_export_interop.py:51–62`. A23-1 subsanado sin fake writer ni exclusión genérica. |
| Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: scripts/tests/RED, regresiones dedicadas, fuente generada, stdlib, propietario del juicio, redactor compartido y no mutación ajena. `tasks.md:1024` en adelante preserva RED correctivo y GREEN; no exige PR/main/release excluidos por autorización vigente. |
| Verificación declarada de tareas cerradas | ✓ | `tasks.md:52` conserva ejecución T-01; no macro nueva completada. `tasks.md:846` en adelante conserva estado B23 en progreso, evidencias y pendientes; no ejecuté verificaciones faltantes para tapar cierre. |
| Generado al día / E2 | ✓ | Comprobación A propia en copia OWN exacta: PID30224, Python absoluto `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `interop/**` declarado en T-11/T-15; ROOT conserva evidencia previa. Falta traza final del intento2 por revisión en curso, sin macro cerrada. |
| Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119`: E13/E14/E22/E53/E54 describen servicio, juicio, SHA y fronteras. `docs/agents/ROLES.md:30–43,89`; docs de seis agentes, CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits y comando retro actualizados en el mismo diff. |
| API OpenAPI | ✓ (n/a) | Ninguna spec OpenAPI en las68 rutas. No se ejecutó openapi-lint. |
| Docs-style | ✓ (n/a como gate de prosa) | Bloque de servicio/persistencia con pruebas y descriptores, no iniciativa exclusivamente de prosa. Espejos preservan sentido y tokens; no se reporta estilo. |
| T-07 corte prospectivo / legacy | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`, contrato `comparisons/memory-curation-contract.md:98–114` bajo roadmap. No migración/reaprobación/borrado ni accepted=approved. `test_knowledge_curation.py:597–610` conserva bytes/IDs/estados/journal/README. |
| T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,551,611`; `agents/knowledge-curator.md:37–46,79–141`: propose productores, Curator semántica, servicio bytes. Gate/design/QA/revisión/Gold/repetición no aprueban por sí solos. Sin agente/skill nuevo. |
| Propuesta redactada, portable y exclusiva | ✓ | `knowledge-curation.py:78–85,153–164,195–204,450–475`: 128 destino, aliases<=8/255 sólo comparación, cuatro estados/approved casefold y reserva bajo cerrojo. `test_knowledge_curation.py:170–194,195–266` reserva históricos sin escritura por alias y preserva redacción/SHA. |
| SHA original y metadata final | ✓ | `knowledge-curation.py:404–443,551–571`: ID/prefijo, categoría exacta, versión1, índice/colisión y SHA fuente. `_caught:66–76` redacta diagnóstico antes de devolución, fallback sin bytes crudos. Tests dedicados `test_knowledge_curation.py:157–167` cubren categoría e ID sensibles con mismo status/código y árbol intacto. |
| needs_changes/reject/replacement | ✓ | Servicio `:560–576,589–607`; tests `:364–429`: original/contenido/motivo y SHA conservados, rechazo terminal, sólo approve corrección final, nunca edición de approved. |
| Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega mismas reglas usadas por servicio `:421–435`. `test_knowledge_curation.py:613–619` comprueba gate sin mutación; gate0 no significa transición. |
| Intención / recibo / recover | ✓ | Servicio `:299–340,477–496,499–548`: staging/identidad exactos ligados al registro, hash de intención, lectura links controlada y limpieza sólo verificable. Tests `:106–153` cortan el enlace real operations/receipts, recover doble y rechazo de hardlink ajeno sin mutación; `:456–524` conserva cortes/reintentos/cambios/ajenos. No garantiza corte eléctrico. |
| Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:526–595,633–702`: cerrojo cooperante de proceso, redirected/hardlinks/scan incompleto, fuente ajena conservada. Los dos skips Windows de symlink no prueban esos guards; POSIX/native pendientes. |
| T-11 productores / fallback / retro tardía | ✓ | Architect/planner/implementer/qa/documenter/debug-root-cause/retro/bridge delegan sin writer fallback. `commands/dev-cycle.md:400–428`; `commands/retro.md:24–34`: handoff tardío o pendiente/ruta/ID visible, cierre retro no aprueba memoria. |
| Bridge Gold / nombres / SHA / store | ✓ | `propose-from-case.py:172–187,210–267,307–309`: nombre histórico ordinario igual, sólo truncado slug largo conservando hash/ref íntegros; aliases reservan históricos157, sin ampliar destino128. API/CLI conserva SHA real; `test_propose_from_case.py:603–701` prueba dos Gold máximos, cuatro estados, duplicado/store/config intactos y handoff SHA. Hash ausente/cambiado conserva tratamiento `:239–243` y pruebas `:417–438`. |
| Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: sólo cambia orientación generada, conserva fuentes/estado y no escribe candidates/approved. RED/GREEN histórico se conserva, no nueva aceptación QA. |
| Confluence excluye journal/candidates y staging | ✓ | `confluence-scope.py:83–85,268–275`; defaults/skill/policy y `test_memory_curation_scope.py:21–58`: exclusión antes de include, casing y staging, approved/originales intactos. Sin conexión/publicación externa. |
| T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:863` en adelante conserva fallos, REDs y GREEN205/2skips, journal173/10skips, nuevos RED11/6/16 y GREEN264/2symlinkskips + consola20sin skips. Evidencia comunicada/ledger, no tests propios A ni QA completa, eficacia/escala/UX/native/global. |
| T-15 consola obligatoria nueva | ✓ | A23-1 corregido: rules `:6–8` incorpora snippet literal al arrancar; service `:20–22` conserva suyo. `test_console_encoding.py:305–306,383–392` declara pureza nominal medible/MODOS para ambos; `:730–770` oráculos reales cp1252/ascii, error noASCII JSON y stdin UTF8/emoji/bytes/SHA éxito. El criterio canónico `:169–179,269–292,639–722` se conserva. |
| Rama / publicación / macros | ✓ | `tasks.md:14–24,1035–1046`: no PR/main/release ni B23 publicado/aceptado, sólo T-01 cerrada. Autorización normal commit/push rama no obliga PR/release. Comparación restante, skills aplazadas y objetivo global activos. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A23-1 | Important | Consola de nuevas piezas | T-11/T-14/T-15 | Corregido, confirmado A2; criterio conservado | Snippet/MODOS y oráculos reales, check88 propio. |
| B23-1 | Important | Corte entre enlace y limpieza de registros | T-08/T-14 | Corregido, confirmado B2 | Dos cortes reales y recover doble; enlaces ajenos rechazados. |
| B23-2 | Important | Curator generado incompatible con su persistencia | T-11/T-15 | Corregido, confirmado B2 | Dos proyecciones completas y otras14 equivalencias verificadas. |
| B23-3 | Important | Nombre Gold largo y SHA en handoff | T-08/T-14 | Corregido, confirmado B2 | Gold máximo real, aliases cuatro estados y store intacto. |
| B23-4 | Important | Secreto en diagnóstico de metadatos | T-08/T-14 | Corregido, confirmado B2 | Mismos códigos, secreto omitido y dependencia ausente segura. |
| D23-1 | Important | Cada apply recarga todos los payloads de intenciones cerradas | T-08/T-14/T-15 | Directorios ligados a la ruta del candidato; recover enumera nombres y valida único registro; pendiente GREEN y revisión3 | D:1/201/801 históricos,2/202/802 lecturas y0,139/0,703/2,031s. RED ROOT abajo. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 3: Bloque23 (T-07/T-08/T-11/T-14/T-15) — sin gaps pendientes

Lentes A+B+D, C=false/D=true; contexto fresco, fallback genérico reviewer
con tier opus/high frontmatter y sin override consumidor. Scope oficial68,
0 fuera/avisos/excluidos; fuente inmutable1029, diff68/6740 líneas. ROOT leyó
completos los tres informes, verificó recibos/90+362+112 artefactos, entradas
y hashes1029. Los seis Important están corregidos; 0 Critical/Important/Minor.
No rebatidos ni criterios reabiertos. B3 conserva23 sondas, sin sumar la
cohorte anterior de21; A ejecutó check88 propio PID17500 exit0.
Revisión aceptada como puerta previa de este bloque, no QA ni cierre macro.

Tabla completa A3 (referencias relativas a la fuente congelada revisión3):

| Criterio | ✓/✗ | Evidencia y límite |
|---|---|---|
| T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. |
| Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. |
| Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. |
| Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. |
| Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. |
| Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. |
| Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. |
| API OpenAPI | ✓ (n/a) | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. |
| Docs-style | ✓ (n/a como gate exclusivo de prosa) | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. |
| T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. |
| T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. |
| Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. |
| SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. |
| needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. |
| Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. |
| Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. |
| Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. |
| T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. |
| Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. |
| Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. |
| Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. |
| T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. |
| T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. |
| Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A23-1 | Important | Consola | T-11/T-14/T-15 | Corregido; aprobado2 y conservado3 | Snippet/MODOS, oráculos Unicode y criterios intactos. |
| B23-1 | Important | Corte enlace/limpieza de registros | T-08/T-14 | Corregido; confirmado B3 en layout actual | Cortes reales operations/receipts y staging vivo, recover doble y enlaces ajenos. |
| B23-2 | Important | Curator generado incompatible | T-11/T-15 | Corregido; aprobado2 y conservado3 |16 proyecciones individualmente verificadas; check88 propio A3. |
| B23-3 | Important | Gold largo y handoff SHA | T-08/T-14 | Corregido; aprobado2 y conservado3 | Nombre128/hash completo/aliases y store conservados. |
| B23-4 | Important | Secreto en diagnóstico | T-08/T-14 | Corregido; aprobado2 y conservado3 | Redactor/fallback y códigos sin datos crudos. |
| D23-1 | Important | Recarga global de payloads históricos bajo lock | T-08/T-14/T-15 | Corregido, confirmado D3 y sin defecto B3 |801 históricos:802→1 lecturas,62.627.193→78.137B,0 ajenas; cuatro transiciones reales conservadas. |


Detalle y pruebas originales: [historial](execution-history.md).

## Validación Windows/Linux interrumpida y corrección posterior — Bloque23

Registro histórico: [detalle original](execution-history.md).

## Revisión de dos lentes — intento 1: Remediación post-QA Bloque23 (T-14/T-15) — sin gaps pendientes

Ciclo nuevo acotado1 de3, separado de revisión original1–3 aceptada.
Lentes A+B+C independientes en paralelo, D=false. C=true sólo por workflow.
Scope PID35296 exit0:6 rutas,0 fuera/avisos/exclusiones. Export check88
PID10000 exit0. Ledger PID23512 exit0, aviso histórico de cabecera729.
ROOT leyó íntegros los tres informes y verificó recibos,26 hashes de A,
artefactos/hijos B y las1029 fuentes congeladas. Se conservan24 criterios
y seis gaps originales; Q23-1/Q23-2 corregidos,0 Critical/Important/Minor.
Sin rebatidos, reaperturas, nueva aprobación de memoria ni cierre macro.

| Criterio | ✓/✗ heredado | Evidencia aceptada del ciclo original3 (referencias históricas) | Revisión del delta remediación1 |
|---|---|---|---|
| T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. | ✓ Conservado; tasks.md:48 única macro completada. |
| Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. | ✓ Revalidado: tasks.md:238–239 y259; scope PID35296 exit0 seis rutas, 0 fuera/avisos/excluidos. Changelogs pertenecen al alcance T-16, sin cerrar esa macro. |
| Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. | ✓ Revalidado: tests/test_ci_skill_suites.py:61–63; test_console_encoding.py:303–304,380–387,687–699,783–796. Ejecución real subprocess :632–634. RED5 y GREEN570/6skips comprobados; no acreditan QA global. |
| Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. | ✓ Revalidado: CONSTITUTION.md:11–13,26. RED previo conserva tests que identifican el gap, stdlib json y espejo ES/EN en el delta. Sin cambios generados manuales ni cierre global. |
| Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. | ✓ Conservado; ninguna nueva tarea completada. Tasks.md:1216–1222 registra evidencia correctiva limitada, no cierre. |
| Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. | ✓ No aplica al delta6: no cambia commands/, agents/ ni hooks/. No ejecutado export por esta lente. Check88/PID17500 sigue como evidencia histórica aceptada3, sin atribuir ejecución nueva. |
| Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. | ✓ Revalidado para delta: tasks.md:239,1193–1230 y CHANGELOG.md:14–16/CHANGELOG.es.md:14–16 describen exactamente CI y consola. Contratos/callers del producto sin delta. |
| API OpenAPI | ✓ (n/a) | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. | ✓ n/a: sin spec OpenAPI en seis rutas; no ejecutado lint. |
| Docs-style | ✓ (n/a como gate exclusivo de prosa) | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. | ✓ Conservado n/a del ciclo anterior; no hallazgos de requisitos introducidos por la prosa acotada. |
| T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. | ✓ Conservado producto; Q23-1 revalidado: workflow y copia :52 incluyen skills/confluence-publish/scripts y son byte-idénticos SHA d8378db84a799058564c69ad12f7e1331ad54c0f191f0bd91366bc3beb810844. No publicación real. |
| T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. | ✓ Revalidado: tasks.md:1195–1201 QA interrumpida no aceptada; :1216–1222 RED5/GREEN570/6skips exactos. XML y recibos coinciden. Sin suma de cohortes, cobertura/gate completo no acreditados. |
| T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. | ✓ Revalidado Q23-2: MODOS :380–387 exige exit0 para envelope UTF8 con emoji; excepción ASCII :303–304 medida :783–796 y no oculta arranque/snippet. Validador :69–79 usa bytes UTF8 y approval_granted=False :60–61. |
| Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. | ✓ Revalidado: tasks.md:1224–1230 ciclo nuevo1/max3 separado, objetivo activo/skills aplazadas, sin QA verde/cierre macro/commit/push. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A23-1 | Important | Consola | T-11/T-14/T-15 | Corregido; aprobado2 y conservado3 | Snippet/MODOS, oráculos Unicode y criterios intactos. |
| B23-1 | Important | Corte enlace/limpieza de registros | T-08/T-14 | Corregido; confirmado B3 en layout actual | Cortes reales operations/receipts y staging vivo, recover doble y enlaces ajenos. |
| B23-2 | Important | Curator generado incompatible | T-11/T-15 | Corregido; aprobado2 y conservado3 |16 proyecciones individualmente verificadas; check88 propio A3. |
| B23-3 | Important | Gold largo y handoff SHA | T-08/T-14 | Corregido; aprobado2 y conservado3 | Nombre128/hash completo/aliases y store conservados. |
| B23-4 | Important | Secreto en diagnóstico | T-08/T-14 | Corregido; aprobado2 y conservado3 | Redactor/fallback y códigos sin datos crudos. |
| D23-1 | Important | Recarga global de payloads históricos bajo lock | T-08/T-14/T-15 | Corregido, confirmado D3 y sin defecto B3 |801 históricos:802→1 lecturas,62.627.193→78.137B,0 ajenas; cuatro transiciones reales conservadas. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| Q23-1 | Important | Suite Confluence omitida en CI | T-14 | Corregido; confirmado A/B/C | Ruta literal en copias idénticas, detector real sin carpetas omitidas; sin permisos/triggers/secrets nuevos. |
| Q23-2 | Important | Metadata consola de plan-review-open | T-14/T-15 | Corregido; confirmado A/B/C | Envelope UTF8 válido y exit0, exención ASCII individual medida; snippet/arranque/negativos preservados, approval_granted=false. |


Detalle y pruebas originales: [historial](execution-history.md).

## Continuación técnica — regresiones de hooks (2026-10-10)

Registro histórico: [detalle original](execution-history.md).

## Revisión de dos lentes — intento 2: Remediación post-QA Bloque23 (T-14/T-15) — un Important corregido pendiente de revisión3

Lentes A+B frescas por subagentes genéricos; reviewer nativo no disponible.
Selector PID23076 exit0: C=false/D=false. Scope real PID14652 exit0:
11 en alcance,0 fuera/avisos/excluidos. El despacho mencionaba PID13620;
se usa el terminal real y se conserva el artefacto original. Fuente congelada
1030 archivos, manifest SHA256
`a1fc147808cf757f0fcdb12b9748d73b9d80ebf534a57b146db6157f09e2b9bd`,
diff SHA256 `138fa204f56c565c61f335015cfa773a4a134ab2ed270c82afd70b9fb4db814d`.

A conserva los24 criterios y ocho gaps corregidos del intento1 post-QA.
B reproduce un Important nuevo: el cambio de método del parser desde una
función o mediante alias mantenía indebidamente la exención de datos runtime.
ROOT leyó ambos informes íntegros, comprobó sus hashes y17 artefactos B,
reprodujo el defecto con cinco regresiones dedicadas y lo acepta sin rebate.
Los ✓ de A no anulan el defecto de B; no hay aceptación global del intento2.
Informes A SHA256 `0e164b90a66fbe2258259654c62f8e497f4850a6bb26c330722f3f21e87745a1`,
B SHA256 `9b251e7739102295076489b1911f5870670121ab6bd410fe6221c431794aad95`.

Tabla de continuidad: las referencias al intento1 son evidencia canónica
heredada; no representan una nueva ejecución de esas cohortes.

| # | Criterio | A2 | Continuidad y delta |
|---|---|---|---|
| 1 | T-XX hechas y criterios | ✓ | Intento1 fila1; sólo T-01 completada, sin macro nueva. |
| 2 | Alcance del plan | ✓ | Intento1 fila2; scope11 sin fuera ni exclusiones. |
| 3 | Tests y oráculos reales | ✓ | Intento1 fila3; fixtures y spies reales; B23-QA2-1 acepta un defecto nuevo del scanner. |
| 4 | Constitución explícita | ✓ | Intento1 fila4; stdlib, RED previo, delegación y fuentes generadas conservadas. |
| 5 | Verificación de tareas cerradas | ✓ | Intento1 fila5; T-01 intacta, ninguna verificación faltante se inventa. |
| 6 | Generado al día / E2 | ✓ | Intento1 fila6; delta sin commands/agents/hooks; check autor PID5800 exit0,88 al día. |
| 7 | Descriptores / E3 | ✓ | Intento1 fila7; CONTRACTS E22 incorpora puertas reales manteniendo QA pendiente. |
| 8 | API OpenAPI | n/a | Intento1 fila8; no spec OpenAPI modificada. |
| 9 | Docs-style | n/a | Intento1 fila9; no gate exclusivo de prosa ni reapertura por estilo. |
| 10 | Corte prospectivo / legado | ✓ | Intento1 fila10; sin delta ni migración. |
| 11 | Persistencia compartida / juicio Curator | ✓ | Intento1 fila11; Gold sólo propone, QA no aprueba. |
| 12 | Propuesta redactada / portable / exclusiva | ✓ | Intento1 fila12; propose, aliases y reserva intactos. |
| 13 | SHA original / metadatos finales | ✓ | Intento1 fila13; binding y redactor intactos. |
| 14 | needs_changes / reject / replacement | ✓ | Intento1 fila14; transiciones y original ligado a SHA intactos. |
| 15 | Gate puro / reglas compartidas | ✓ | Intento1 fila15; E22 sólo enumera ejecución, sin transición nueva. |
| 16 | Intención / recibo / recover | ✓ | Intento1 fila16; operación y cortes internos intactos. |
| 17 | Concurrencia / IO / OS | ✓ | Intento1 fila17; fixtures Windows conservan assertions/POSIX; límites explícitos. |
| 18 | Productores / fallback / retro tardía | ✓ | Intento1 fila18; sin delta ni autoaprobación. |
| 19 | Bridge Gold / nombre / SHA / store | ✓ | Intento1 fila19; E22 gate real, store y juicio intactos. |
| 20 | Journal episódico sin promoción | ✓ | Intento1 fila20; nueva clasificación sólo en scanner de tests. |
| 21 | Confluence / staging | ✓ | Intento1 fila21 y Q23-1 conservados; ninguna publicación real. |
| 22 | Honestidad RED / GREEN / QA | ✓ | Intento1 fila22; cohortes separadas, fallos/skips preservados, sin cobertura nueva aceptada. |
| 23 | Consola obligatoria nueva | ✓ | Intento1 fila23 y A23-1/Q23-2 conservados; no CLI nueva del helper. |
| 24 | Rama / publicación / macros | ✓ | Intento1 fila24; QA/gates/push pendientes, skills aplazadas, objetivo activo. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | Mutación de parser entre scopes o aliases oculta argv claude | T-14/T-15 | Invalidación conservadora transitiva de aliases y nombres mutados; corregido, pendiente revisión3 | RED5, GREEN130/0skips; no producto modificado. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 3: Fase QA (T-14/T-15) — residual verificado y decisión del orquestador

Lentes A+B+D sobre la fuente de1030 archivos, manifest
`0524e67de8eddac84d2d0a1777a366a1531b3bb9dd9bef2440a8904e7ac6bfee`.
A conserva sus24 criterios y los9 gaps de continuidad; D sin hallazgos.
B confirma el mismo Important B23-QA2-1: `alias = second = p` y
`alias: object = p` ocultan el argv tras mutar `alias.add_argument`.
ROOT verificó informes, recibos, artefactos y fuente; acepta el residual.
La sonda con mock PID9288 exit0 observa argv real y detectores vacíos;
no ejecuta comandos ni red. La corrección previa no cubre esas asignaciones.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | Alias encadenado/anotado no invalida el parser | T-14/T-15 | pendiente; no se acepta intento3 | test_graphiti_security.py:313–339; informe B SHA6727e60b351cc1d398ac1f6be1e9938f431aff50a2e163d6806c367ee447529a |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 4: Fase QA (T-14/T-15) — dos Important verificados y replan acotado

ROOT fusiona A+B sobre el manifest de1030 archivos SHA256
`94aec1d3b603bc6185f33e5ee5726f8abd9f2de9320c31df8ae57b2d226dd45f`.
Selector autor C=false/D=false; reviewer nativo ausente, lentes genéricas con
modelo heredado sin override. Informes, recibos, artefactos y fuente cotejados
por SHA. A conserva24 criterios y tres criterios T-01; criterio4 ahora ✗.
B confirma el mismo B23-QA2-1 en `alias, *rest = p, None, None`: la mutación
no invalida p y los dos detectores omiten el argv observado por el mock.
La sonda PID10956 exit0 no ejecuta hosts, comandos de producto ni red.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | Desempaquetado con estrella conserva el falso negativo | T-14/T-15 | pendiente | tests/test_graphiti_security.py:335–339; informe B SHA d17c90225d71e9cd9aa35f20b137b522b73b900851c0bfa6d75c2518907a59c5 |
| A23-QA4-1 | Important | Nuevo diagnóstico persistido sin redactor compartido | T-14/T-15 | pendiente | evals/run.py:324–325,397; CONSTITUTION.md:34; informe A SHA 1f647b6ceec03f22553088033ca2a99f3a85928299aa6d0c59b6ea71cf1c3172 |

| # | Tarea | Criterio | ✓/✗ | Evidencia heredada completa | Estado y evidencia delta2 heredados | Juicio y evidencia delta3 | Juicio y evidencia adicional 4/MAX4 |
|---|---|---|---|---|---|---|---|
| 1 | T-01 | T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. Referencia de traspaso: tasks.md:1246. | ✓ Conservado. tasks.md:48,54–56 y33–40 mantiene única macro T-01 completa, tres criterios y1/16; ninguna nueva macro se cierra. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada,1/16. Sus tres criterios se desglosan abajo; ninguna macro se cierra en este delta. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada, 1/16; se conservan sus tres criterios ejecutados. Ninguna macro se cierra. |
| 2 | T-14/T-15/T-16 | Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. Referencia de traspaso: tasks.md:1247. | ✓ Revalidado. tasks.md:239 tests/** y ledger, :250 docs/** y tests/**, :260 ambos changelogs; corresponde QA/documentación del plan:19–21,45–48. Scope terminal PID14652 exit0:11 en alcance,0 fuera/avisos/excluidos. PID13620 del despacho no coincide con terminal y no se usa. | ✓ Revalidado. tasks.md:239,250,260 declara tests/kit/skills/docs y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID6176 exit0,6 en alcance,0 fuera/avisos/info/excluidos (terminal y hashes propios comprobados). | ✓ Revalidado. tasks.md:239,250,260 declara evals/**, tests/**, skills/**, ledger y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID 28776 exit 0: ocho rutas dentro, cero fuera/avisos/info/excluidos. Limpieza del fixture y serialización del runner son reparación de QA, no ampliación de skills. |
| 3 | T-14 | Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. Referencia de traspaso: tasks.md:1248. | ✓ Revalidado línea a línea: test_graphiti_security.py:2250–2348 prueba datos/argv, parseo/red, rutas y lector local real; test_knowledge_services.py:1379–1404 prueba ambos recorridos; test_lint_plugin.py:497–516 controla noexec/otro/missing. test_training_data_services.py:572–601 separa resolución/timeout y mantiene los asserts; test_memory_path.py:185–284 mantiene payload/contexto/área/topes. test_knowledge_router_read.py:366–371 sólo añade diagnóstico info. No existe % oficial nuevo del diff aceptado: pendiente, sin usar cohortes como cobertura. | ✓ Revalidado. tests/test_graphiti_security.py:308–339,2369–2385 conserva detector real y cinco negativos de mutación/alias/delete; RED5 y GREEN130/0skip ejecutados. test_task_brief.py:1802–1823 copia cuatro dependencias reales, preserves assertions/topes y GREEN7. test_backend_markdown_export.py:278,528–530 mantiene condiciones,100ms y añade sólo dict/presencia. Último archivo diagnóstico sin rerun todavía; tests existentes no equivalen a QA completa. Sin % oficial nuevo aceptado del diff. | ✓ Revalidado línea a línea. test_graphiti_security.py:332–347,2405–2422 recoge Assign/AnnAssign/NamedExpr y exige argv + ofensor real para seis variantes; RED 6/GREEN 136. evals/test_evals.py:402–458 comprueba Git readonly/ausencia real y denegación visible/conservación del sentinel; RED 2/GREEN 2 y cohorte 45. test_coverage_gate.py:160,262 cambia sólo shlex.join; conserva mínimos/diff/exit/asserts. No % oficial nuevo válido del diff. |
| 4 | T-14/T-15 | Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. Referencia de traspaso: tasks.md:1249. | ✓ Revalidado contra CONSTITUTION.md:10–13,17–21,26,29,33–38. Tests/soporte stdlib, RED real conservado en tasks.md:1321–1330,1360–1366,1393–1394,1409–1412; controles dedicados y espejos CHANGELOG.md/CHANGELOG.es.md:17–18. No nueva llamada de red hook ni edición manual generada; no aprobación de memoria ni cierre/publicación. | ✓ Revalidado. CONSTITUTION.md:10–13,17–21,26,29,33–38: helper usa stdlib, RED válido precede corrección y cinco regresiones nombradas; mirrors EN/ES actualizados; fuente generada y juicio Curator conservados. Pytest es infraestructura de test existente, no dependencia nueva del producto. El error import PID1480 no cuenta como RED. | ✗ Nuevo A23-QA4-1 Important. CONSTITUTION.md:34 exige que todo texto persistido pase por redact.py. evals/run.py:324–325 crea detalle.cleanup como texto y :397 lo persiste por json.dump sin cargar/invocar ese redactor. El resto conserva stdlib, TDD (tasks.md:1598–1610,1629–1642), fuentes y espejos; no se reabren violaciones previas ajenas al delta. |
| 5 | T-01 | Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. Referencia de traspaso: tasks.md:1250. | ✓ Conservado. Verificación ejecutada T-01 heredada tasks.md:52 y fila aceptada :1250. El delta no altera Estado ni sus tres criterios; otras15 macros abiertas. No ejecuté ninguna verificación para cubrir falta de evidencia. | ✓ Conservado. tasks.md:52 contiene verificación ejecutada T-01 y :54–56 sus tres checks. Ninguna otra macro cerrada; no ejecuté una verificación para ocultar ausencia. | ✓ Conservado. tasks.md:52 conserva la verificación ejecutada de la única macro cerrada; :54–56 sus tres checks. No ejecuto verificaciones para cubrir evidencia faltante. T-14/T-15 abiertas, T-16 borrador. |
| 6 | T-11/T-15 | Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. Referencia de traspaso: tasks.md:1251. | ✓ n/a al delta11: sólo tests, CONTRACTS, changelogs y ledger; no commands/, agents/ ni hooks/. No ejecuté export. Evidencia autor adicional qa-rem-review2-final-exports/terminal.json PID5800 exit0 y stdout exacto export-interop --check: 88 ficheros al día; hashes stdout/stderr comprobados, separado del check heredado PID17500. | ✓ n/a al delta6: no commands/, agents/ ni hooks/. Prompt A no requiere ejecución propia de export aquí. Autor PID6488 exit0,88 ficheros al día, terminal/streams verificados; separar del check histórico17500. | ✓ n/a al delta ocho: no commands/, agents/ ni hooks/. No ejecuté export-interop; evidencia autor PID 30612 exit 0 y stdout «export-interop --check: 88 ficheros al día», streams cotejados. interop/** declarado en tasks.md:250. No se atribuye como ejecución propia nueva. |
| 7 | T-15 | Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. Referencia de traspaso: tasks.md:1252. | ✓ Revalidado E3. CONTRACTS.md:85 cambia sólo Puerta E22 por dos rutas existentes del bridge/servicio y conserva QA pendiente/Gold nunca aprueba. test_training_data_services.py:386–407 exige ruta real. CHANGELOG.md/CHANGELOG.es.md:17–18 y tasks.md:1303–1432 describen scanner/espía/fixtures, sin promesa global. Producto/callers sin delta. | ✓ Revalidado. CONTRACTS.md:85,118–119,140–142 conserva E22/E53/E54 y condición E3. Sólo tests/scanner/fixture cambian, sin arista/caller o flujo de producto nuevo; CHANGELOG.md/CHANGELOG.es.md:18,20 y tasks.md:1433–1561 describen exactamente esos cambios y límites en esta tarea. | ✓ Revalidado. CONTRACTS.md:66,140–142 exige E3/espejos. Ninguna arista de productor/caller cambia. evals/README.md:79–85,157–163 describe limpieza/cleanup_error en ES/EN en esta misma tarea; CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1596–1657 describen scanner/fixtures/runner y límites. No obligación de modificar FLOWS por un flujo del ciclo inexistente en el delta. |
| 8 | T-08/T-11 | API OpenAPI | ✓ | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. Referencia de traspaso: tasks.md:1253. | ✓ n/a; las11 rutas no incluyen spec OpenAPI. No ejecutado lint. | ✓ n/a: seis rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: ocho rutas sin spec OpenAPI. No ejecutado openapi-lint. |
| 9 | T-15 | Docs-style | ✓ | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. Referencia de traspaso: tasks.md:1254. | ✓ n/a conservado como gate exclusivo de prosa; sin hallazgo de requisitos ni reapertura por estilo. | ✓ Aplicado a este delta mayoritariamente prosa por líneas; docs-style.md:14–25. tasks.md:1433–1561 y changelogs:18,20 usan evidencia y comparaciones concretas, sin promesa global/nativa. Tabla única de gap :1482–1484 responde al formato obligatorio SKILL §6, no se elimina por preferencia; no hallazgo citable nuevo. | ✓ n/a al criterio adicional de iniciativa mayoritariamente prosa: semántica de código/tests y documentación de QA. docs-style.md:15–22 leído; no se reporta estilo. Tabla de una fila en ledger responde al formato obligatorio SKILL §6. |
| 10 | T-07 | T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. Referencia de traspaso: tasks.md:1255. | ✓ Conservado. Sin delta al servicio, knowledge-write/check ni contrato de corte prospectivo; evidencia heredada :1255 sigue vigente. | ✓ Conservado. tasks.md:1255,1466; ningún delta a knowledge-write/check/contrato o producto. Legado sin migración/reaprobación. | ✓ Conservado. tasks.md:1255,1466; sin delta a knowledge-write/check/contrato de corte prospectivo. No migración ni reaprobación del legado. |
| 11 | T-08 | T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. Referencia de traspaso: tasks.md:1256. | ✓ Conservado. Sin delta al servicio/Curator. CONTRACTS.md:85 conserva explícitamente Gold no aprueba, sólo pending; juicio no delegado a QA. | ✓ Conservado. tasks.md:1256,1467; persistencia/Curator sin delta. QA/Gold no aprueban memoria. | ✓ Conservado. tasks.md:1256,1467; servicio/Curator sin delta. QA/Gold/revisión no aprueban memoria. |
| 12 | T-08 | Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. Referencia de traspaso: tasks.md:1257. | ✓ Conservado. Sin delta a propose/redactor/alias/reserva; evidencia heredada :1257 intacta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases/reserva/redactor sin delta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases de candidatos/reserva/redactor de memoria sin delta. Aliases del scanner son otro dominio. |
| 13 | T-08 | SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. Referencia de traspaso: tasks.md:1258. | ✓ Conservado. Sin delta a SHA/metadatos/_caught ni test B4; evidencia heredada :1258 intacta. | ✓ Conservado. tasks.md:1258,1469; SHA original/metadatos y test B23-4 sin delta. | ✓ Conservado. tasks.md:1258,1469; SHA/metadatos/_caught y test B23-4 sin delta. |
| 14 | T-08 | needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. Referencia de traspaso: tasks.md:1259. | ✓ Conservado. Sin delta a transiciones/replacement/terminal rejected; evidencia heredada :1259 intacta. | ✓ Conservado. tasks.md:1259,1470; transiciones y replacement ligados a SHA original sin delta. | ✓ Conservado. tasks.md:1259,1470; transiciones/replacement y rejected terminal sin delta. |
| 15 | T-08 | Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. Referencia de traspaso: tasks.md:1260. | ✓ Conservado. Sin delta al gate/validadores; E22 sólo enumera su puerta de ejecución, no añade mutación ni transición. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate puro y validadores compartidos sin delta. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate y validadores compartidos sin delta. |
| 16 | T-08/T-14 | Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. Referencia de traspaso: tasks.md:1261. | ✓ Conservado. Sin delta a operaciones/recibos/recover ni oráculos de interrupción; evidencia heredada :1261 intacta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y fronteras reales sin delta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y cortes reales sin delta. |
| 17 | T-08/T-14 | Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. Referencia de traspaso: tasks.md:1262. | ✓ Conservado producto. Fixture Windows test_memory_path.py:151–169 ahora aporta shim/SYSTEMROOT/Python coherentes con shell, sin relajar aserciones. test_lint_plugin.py:41–60 simula X_OK sólo del path exacto y :497–516 comprueba delegado/missing. tasks.md:1375–1376,1400–1407,1418–1421 conserva límites, intento fallido y skips; no acredita POSIX/nativo. | ✓ Conservado. tasks.md:1262,1473; ningún cambio producto/OS/permisos. Fixture Linux lector real RED trescohortes6/1 y GREEN7/0skip son selección acotada, no aceptación Windows/POSIX completa ni nativa. | ✓ Conservado producto de curación. tasks.md:1262,1473; no cambio servicio/locks/guards. evals/run.py:134–164 limpia sólo cwd recibido de preparar_cwd, limita retry a unlink regular readonly Windows dentro del cwd y sin reparse; pruebas :402–458 verifican Windows, no aceptación POSIX/nativa completa. |
| 18 | T-11 | T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. Referencia de traspaso: tasks.md:1263. | ✓ Conservado. Sin delta a productores/commands/retro; evidencia heredada :1263 intacta. | ✓ Conservado. tasks.md:1263,1474; productores/retro/commands sin delta. No autoaprobación. | ✓ Conservado. tasks.md:1263,1474; productores, comandos y retro sin delta, sin autoaprobación. |
| 19 | T-08/T-11/T-14 | Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. Referencia de traspaso: tasks.md:1264. | ✓ Conservado implementación. E22 CONTRACTS.md:85 incorpora gate real y conserva pending/no aprobación; suites bridge/curation ejecutadas PID3364 exit0:161 pases y2 skips. No cambia nombre/SHA/Gold/store; evidencia heredada :1264. | ✓ Conservado. tasks.md:1264,1475,CONTRACTS.md:85; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado. tasks.md:1264,1475; puente Gold/nombre/SHA/store sin delta. |
| 20 | T-07/T-11 | Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. Referencia de traspaso: tasks.md:1265. | ✓ Conservado. Sin delta journal/handoff y sin promoción por repetición. Nueva clasificación de runtime en test_graphiti_security.py:292–397 se limita al scanner de tests y no cambia autoridad. | ✓ Conservado. tasks.md:1265,1476; scanner de tests cambia clasificación conservadora, no journal ni autoridad. Journal sigue episódico. | ✓ Conservado. tasks.md:1265,1476; journal/handoff sin delta. Scanner AST sólo modifica una puerta de tests, no autoridad de memoria. |
| 21 | T-07/T-15 | Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. Referencia de traspaso: tasks.md:1266. | ✓ Conservado Q23-1 y producto. No delta workflow/copia/confluence-scope ni tests Confluence; evidencia heredada :1266 y gap :1282. | ✓ Conservado. tasks.md:1266,1282,1477; sin cambios a Confluence/staging/CI en delta3. Q23-1 conservado; ninguna conexión o publicación real. | ✓ Conservado. tasks.md:1266,1282,1477; Confluence/staging/CI sin delta. Q23-1 conservado; no conexión/publicación real. |
| 22 | T-14 | T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. Referencia de traspaso: tasks.md:1267. | ✓ Revalidado. tasks.md:1321–1340,1360–1376,1393–1425 coincide con recibos terminal/JUnit por cohortes; se conservan70 pases/1 fallo y correctivo1 pase separado,161/2skips y598/12skips. QA2 anterior permanece pendiente/fallida; no % ni gate/QA completa nuevos aceptados. | ✓ Revalidado. tasks.md:1490–1548 conserva error preparación, RED5/GREEN130, tres RED6/1 y GREEN7; mismos7 repetidos. Dos verify históricos no reproducidos, causa pendiente y100ms intactos; diagnóstico final sin JUnit nuevo. QA2Linux6209/78/44,6331 no se transforma en verde; PyTracer/trace-changed y gates históricos insuficientes. tasks.md:1550–1561 distingue preparación QA3 de ejecución/aceptación. | ✓ Revalidado. tasks.md:1598–1610 conserva RED 6/GREEN 136; :1622–1642 conserva 20/7, RED 2 y verdes 2,45,45 + noop 1 separado. XML/terminales cotejados. :1644–1649 conserva HTTP no reproducido y deadlines, sin causa inventada. :1587–1591 mantiene QA2 Windows 6215/24/92 y Linux 6209/78/44, ambos 6331 FAIL. Sin QA3 ni cobertura válida. |
| 23 | T-15 | T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. Referencia de traspaso: tasks.md:1268. | ✓ Conservado A23-1/Q23-2. Sin delta a rules/MODOS/snippet/validador/oráculos Unicode; evidencia heredada :1268 y :1283. Helper de tests sin CLI nueva; no cambia promesa de consola. | ✓ Conservado. tasks.md:1268,1283,1479; A23-1/Q23-2 sin delta a snippet/MODOS/Unicode. Helper no añade CLI de producto. | ✓ Conservado. tasks.md:1268,1283,1479; snippet/MODOS/Unicode sin delta. evals/run.py:65–69 conserva consola UTF-8; no CLI de producto nueva. A23-1/Q23-2 no se reabren. |
| 24 | T-01..T-16 | Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. Referencia de traspaso: tasks.md:1269. | ✓ Revalidado. tasks.md:192,1305–1308,1339–1340,1350–1354,1427–1432 conserva intento2 pendiente, QA2 intacta, macros/publicación/gates pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria; objetivo no cancelado. | ✓ Conservado. tasks.md:14–24,192,1486–1488,1513–1515,1560–1561: ciclo post-QA3/MAX3 sin reset original1–3/post1–2; sólo1/16, skills aplazadas después comandos/dashboard/hooks/memoria; QA/gates/commit/push/cierre global pendientes. | ✓ Conservado. tasks.md:1564–1593 preserva rechazo de intento 3, decisión ROOT de una única revisión adicional global 4/MAX4 y original 1–3/post 1–3 sin reset. :1655–1657 mantiene QA completa/gates/macros/push/cierre pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 5: Fase QA (T-14/T-15) — redacción corregida y regresión de clase pendiente

ROOT fusiona A+B sobre 1030 rutas públicas, manifest SHA256
`f87527e0739ff7aa9bef32d657debdbfa4694119c676c17baa34ae7af4241300`.
Selector C=false/D=false, lentes genéricas con modelo heredado sin override.
Informes, recibos, artefactos y fuente cotejados; anexos A4/B4 byte-equivalentes
tras lectura de texto conservan íntegro el traspaso. A conserva 24 criterios
y tres de T-01, sin gaps nuevos. A23-QA4-1 corregido: redactor compartido real,
fallback fijo y cinco regresiones RED antes de la reparación, GREEN30 después.
B no identifica otro defecto en evals. ROOT acepta su corrección; QA no cerrada.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | alias.__class__ cambia add_argument sin invalidar p | T-14/T-15 | pendiente; regresión verificada | tests/test_graphiti_security.py:330–340,357–370; mock observa argv, detectores vacíos; PID14436 exit0 |
| A23-QA4-1 | Important | Diagnóstico nuevo persistido sin redactor | T-14/T-15 | corregido, aceptado por ROOT5 | evals/run.py:299–313,342–344; test_evals.py:462–561; RED5/GREEN30, A5/B5 |

| # | Tarea | Criterio | ✓/✗ histórico | Evidencia heredada completa | Estado y evidencia delta2 heredados | Juicio y evidencia delta3 | Juicio y evidencia adicional 4/MAX4 | Juicio y evidencia global5/MAX5 |
|---|---|---|---|---|---|---|---|---|
| 1 | T-01 | T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. Referencia de traspaso: tasks.md:1246. | ✓ Conservado. tasks.md:48,54–56 y33–40 mantiene única macro T-01 completa, tres criterios y1/16; ninguna nueva macro se cierra. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada,1/16. Sus tres criterios se desglosan abajo; ninguna macro se cierra en este delta. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada, 1/16; se conservan sus tres criterios ejecutados. Ninguna macro se cierra. | ✓ Conservado. tasks.md:33–56: sólo T-01 completada,1/16; tres criterios y evidencia ejecutada sin delta. |
| 2 | T-14/T-15/T-16 | Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. Referencia de traspaso: tasks.md:1247. | ✓ Revalidado. tasks.md:239 tests/** y ledger, :250 docs/** y tests/**, :260 ambos changelogs; corresponde QA/documentación del plan:19–21,45–48. Scope terminal PID14652 exit0:11 en alcance,0 fuera/avisos/excluidos. PID13620 del despacho no coincide con terminal y no se usa. | ✓ Revalidado. tasks.md:239,250,260 declara tests/kit/skills/docs y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID6176 exit0,6 en alcance,0 fuera/avisos/info/excluidos (terminal y hashes propios comprobados). | ✓ Revalidado. tasks.md:239,250,260 declara evals/**, tests/**, skills/**, ledger y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID 28776 exit 0: ocho rutas dentro, cero fuera/avisos/info/excluidos. Limpieza del fixture y serialización del runner son reparación de QA, no ampliación de skills. | ✓ Revalidado. tasks.md:239,250,260 declara tests/**,evals/**,docs/** y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope autor PID9148 exit0,7 dentro,0 fuera/avisos/info/excluidos; reparación acotada QA y replan ROOT4:1714–1726. |
| 3 | T-14 | Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. Referencia de traspaso: tasks.md:1248. | ✓ Revalidado línea a línea: test_graphiti_security.py:2250–2348 prueba datos/argv, parseo/red, rutas y lector local real; test_knowledge_services.py:1379–1404 prueba ambos recorridos; test_lint_plugin.py:497–516 controla noexec/otro/missing. test_training_data_services.py:572–601 separa resolución/timeout y mantiene los asserts; test_memory_path.py:185–284 mantiene payload/contexto/área/topes. test_knowledge_router_read.py:366–371 sólo añade diagnóstico info. No existe % oficial nuevo del diff aceptado: pendiente, sin usar cohortes como cobertura. | ✓ Revalidado. tests/test_graphiti_security.py:308–339,2369–2385 conserva detector real y cinco negativos de mutación/alias/delete; RED5 y GREEN130/0skip ejecutados. test_task_brief.py:1802–1823 copia cuatro dependencias reales, preserves assertions/topes y GREEN7. test_backend_markdown_export.py:278,528–530 mantiene condiciones,100ms y añade sólo dict/presencia. Último archivo diagnóstico sin rerun todavía; tests existentes no equivalen a QA completa. Sin % oficial nuevo aceptado del diff. | ✓ Revalidado línea a línea. test_graphiti_security.py:332–347,2405–2422 recoge Assign/AnnAssign/NamedExpr y exige argv + ofensor real para seis variantes; RED 6/GREEN 136. evals/test_evals.py:402–458 comprueba Git readonly/ausencia real y denegación visible/conservación del sentinel; RED 2/GREEN 2 y cohorte 45. test_coverage_gate.py:160,262 cambia sólo shlex.join; conserva mínimos/diff/exit/asserts. No % oficial nuevo válido del diff. | ✓ Revalidado línea a línea. tests/test_graphiti_security.py:330–340,357–359,2413–2431: guardia conservadora de métodos y siete regresiones argv + detector real; RED7 PID21444/GREEN143 PID35096. evals/test_evals.py:462–561 persiste JSON, espía y delega redactor real, comprueba marcadores ausentes y cuatro fallbacks; RED5 PID22624/GREEN30 PID13396. Sin porcentaje oficial válido para este diff7; cohortes no son cobertura. |
| 4 | T-14/T-15 | Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. Referencia de traspaso: tasks.md:1249. | ✓ Revalidado contra CONSTITUTION.md:10–13,17–21,26,29,33–38. Tests/soporte stdlib, RED real conservado en tasks.md:1321–1330,1360–1366,1393–1394,1409–1412; controles dedicados y espejos CHANGELOG.md/CHANGELOG.es.md:17–18. No nueva llamada de red hook ni edición manual generada; no aprobación de memoria ni cierre/publicación. | ✓ Revalidado. CONSTITUTION.md:10–13,17–21,26,29,33–38: helper usa stdlib, RED válido precede corrección y cinco regresiones nombradas; mirrors EN/ES actualizados; fuente generada y juicio Curator conservados. Pytest es infraestructura de test existente, no dependencia nueva del producto. El error import PID1480 no cuenta como RED. | ✗ Nuevo A23-QA4-1 Important. CONSTITUTION.md:34 exige que todo texto persistido pase por redact.py. evals/run.py:324–325 crea detalle.cleanup como texto y :397 lo persiste por json.dump sin cargar/invocar ese redactor. El resto conserva stdlib, TDD (tasks.md:1598–1610,1629–1642), fuentes y espejos; no se reabren violaciones previas ajenas al delta. | ✓ A23-QA4-1 corregido conforme en A5: evals/run.py:299–313,342–344 carga por ruta propia y llama module.redactar antes de json.dump:416; fallback fijo seguro para redactor ausente/fallido/no-texto. CONSTITUTION.md:34 satisfecho; :11–13 evidencia dedicada RED5/GREEN30 tasks.md:1745–1758, stdlib y espejos intactos. |
| 5 | T-01 | Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. Referencia de traspaso: tasks.md:1250. | ✓ Conservado. Verificación ejecutada T-01 heredada tasks.md:52 y fila aceptada :1250. El delta no altera Estado ni sus tres criterios; otras15 macros abiertas. No ejecuté ninguna verificación para cubrir falta de evidencia. | ✓ Conservado. tasks.md:52 contiene verificación ejecutada T-01 y :54–56 sus tres checks. Ninguna otra macro cerrada; no ejecuté una verificación para ocultar ausencia. | ✓ Conservado. tasks.md:52 conserva la verificación ejecutada de la única macro cerrada; :54–56 sus tres checks. No ejecuto verificaciones para cubrir evidencia faltante. T-14/T-15 abiertas, T-16 borrador. | ✓ Conservado. tasks.md:48,52,54–56: única tarea cerrada y Verificación ejecutada. T-14/T-15 abiertas; T-16 borrador. No ejecuté una verificación faltante para cubrir evidencia. |
| 6 | T-11/T-15 | Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. Referencia de traspaso: tasks.md:1251. | ✓ n/a al delta11: sólo tests, CONTRACTS, changelogs y ledger; no commands/, agents/ ni hooks/. No ejecuté export. Evidencia autor adicional qa-rem-review2-final-exports/terminal.json PID5800 exit0 y stdout exacto export-interop --check: 88 ficheros al día; hashes stdout/stderr comprobados, separado del check heredado PID17500. | ✓ n/a al delta6: no commands/, agents/ ni hooks/. Prompt A no requiere ejecución propia de export aquí. Autor PID6488 exit0,88 ficheros al día, terminal/streams verificados; separar del check histórico17500. | ✓ n/a al delta ocho: no commands/, agents/ ni hooks/. No ejecuté export-interop; evidencia autor PID 30612 exit 0 y stdout «export-interop --check: 88 ficheros al día», streams cotejados. interop/** declarado en tasks.md:250. No se atribuye como ejecución propia nueva. | ✓ n/a: diff7 no toca commands/,agents/ ni hooks/. No ejecuté exportador. Evidencia autor PID27252 exit0, stdout export-interop --check: 88 ficheros al día; hashes de terminal y streams cotejados. tasks.md:250 declara interop/**; separar de check propio históricoPID17500. |
| 7 | T-15 | Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. Referencia de traspaso: tasks.md:1252. | ✓ Revalidado E3. CONTRACTS.md:85 cambia sólo Puerta E22 por dos rutas existentes del bridge/servicio y conserva QA pendiente/Gold nunca aprueba. test_training_data_services.py:386–407 exige ruta real. CHANGELOG.md/CHANGELOG.es.md:17–18 y tasks.md:1303–1432 describen scanner/espía/fixtures, sin promesa global. Producto/callers sin delta. | ✓ Revalidado. CONTRACTS.md:85,118–119,140–142 conserva E22/E53/E54 y condición E3. Sólo tests/scanner/fixture cambian, sin arista/caller o flujo de producto nuevo; CHANGELOG.md/CHANGELOG.es.md:18,20 y tasks.md:1433–1561 describen exactamente esos cambios y límites en esta tarea. | ✓ Revalidado. CONTRACTS.md:66,140–142 exige E3/espejos. Ninguna arista de productor/caller cambia. evals/README.md:79–85,157–163 describe limpieza/cleanup_error en ES/EN en esta misma tarea; CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1596–1657 describen scanner/fixtures/runner y límites. No obligación de modificar FLOWS por un flujo del ciclo inexistente en el delta. | ✓ E3 revalidado. CONTRACTS.md:140–142: sin cambio de cadena del ciclo; README evals:84–88,167–171 describe redactor/fallback/ruta retenida ES/EN en esta tarea. CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1729–1771 describen scanner/redactor y límites; sin nueva autoridad/flujo de memoria. |
| 8 | T-08/T-11 | API OpenAPI | ✓ | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. Referencia de traspaso: tasks.md:1253. | ✓ n/a; las11 rutas no incluyen spec OpenAPI. No ejecutado lint. | ✓ n/a: seis rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: ocho rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: siete rutas sin spec OpenAPI; no ejecutado openapi-lint. |
| 9 | T-15 | Docs-style | ✓ | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. Referencia de traspaso: tasks.md:1254. | ✓ n/a conservado como gate exclusivo de prosa; sin hallazgo de requisitos ni reapertura por estilo. | ✓ Aplicado a este delta mayoritariamente prosa por líneas; docs-style.md:14–25. tasks.md:1433–1561 y changelogs:18,20 usan evidencia y comparaciones concretas, sin promesa global/nativa. Tabla única de gap :1482–1484 responde al formato obligatorio SKILL §6, no se elimina por preferencia; no hallazgo citable nuevo. | ✓ n/a al criterio adicional de iniciativa mayoritariamente prosa: semántica de código/tests y documentación de QA. docs-style.md:15–22 leído; no se reporta estilo. Tabla de una fila en ledger responde al formato obligatorio SKILL §6. | ✓ n/a: iniciativa de corrección de código/tests con evidencia documental; docs-style.md:15–22 leído. Sin nueva violación citable de requisitos ni hallazgo de estilo. |
| 10 | T-07 | T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. Referencia de traspaso: tasks.md:1255. | ✓ Conservado. Sin delta al servicio, knowledge-write/check ni contrato de corte prospectivo; evidencia heredada :1255 sigue vigente. | ✓ Conservado. tasks.md:1255,1466; ningún delta a knowledge-write/check/contrato o producto. Legado sin migración/reaprobación. | ✓ Conservado. tasks.md:1255,1466; sin delta a knowledge-write/check/contrato de corte prospectivo. No migración ni reaprobación del legado. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 11 | T-08 | T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. Referencia de traspaso: tasks.md:1256. | ✓ Conservado. Sin delta al servicio/Curator. CONTRACTS.md:85 conserva explícitamente Gold no aprueba, sólo pending; juicio no delegado a QA. | ✓ Conservado. tasks.md:1256,1467; persistencia/Curator sin delta. QA/Gold no aprueban memoria. | ✓ Conservado. tasks.md:1256,1467; servicio/Curator sin delta. QA/Gold/revisión no aprueban memoria. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 12 | T-08 | Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. Referencia de traspaso: tasks.md:1257. | ✓ Conservado. Sin delta a propose/redactor/alias/reserva; evidencia heredada :1257 intacta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases/reserva/redactor sin delta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases de candidatos/reserva/redactor de memoria sin delta. Aliases del scanner son otro dominio. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 13 | T-08 | SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. Referencia de traspaso: tasks.md:1258. | ✓ Conservado. Sin delta a SHA/metadatos/_caught ni test B4; evidencia heredada :1258 intacta. | ✓ Conservado. tasks.md:1258,1469; SHA original/metadatos y test B23-4 sin delta. | ✓ Conservado. tasks.md:1258,1469; SHA/metadatos/_caught y test B23-4 sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 14 | T-08 | needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. Referencia de traspaso: tasks.md:1259. | ✓ Conservado. Sin delta a transiciones/replacement/terminal rejected; evidencia heredada :1259 intacta. | ✓ Conservado. tasks.md:1259,1470; transiciones y replacement ligados a SHA original sin delta. | ✓ Conservado. tasks.md:1259,1470; transiciones/replacement y rejected terminal sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 15 | T-08 | Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. Referencia de traspaso: tasks.md:1260. | ✓ Conservado. Sin delta al gate/validadores; E22 sólo enumera su puerta de ejecución, no añade mutación ni transición. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate puro y validadores compartidos sin delta. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate y validadores compartidos sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 16 | T-08/T-14 | Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. Referencia de traspaso: tasks.md:1261. | ✓ Conservado. Sin delta a operaciones/recibos/recover ni oráculos de interrupción; evidencia heredada :1261 intacta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y fronteras reales sin delta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y cortes reales sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 17 | T-08/T-14 | Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. Referencia de traspaso: tasks.md:1262. | ✓ Conservado producto. Fixture Windows test_memory_path.py:151–169 ahora aporta shim/SYSTEMROOT/Python coherentes con shell, sin relajar aserciones. test_lint_plugin.py:41–60 simula X_OK sólo del path exacto y :497–516 comprueba delegado/missing. tasks.md:1375–1376,1400–1407,1418–1421 conserva límites, intento fallido y skips; no acredita POSIX/nativo. | ✓ Conservado. tasks.md:1262,1473; ningún cambio producto/OS/permisos. Fixture Linux lector real RED trescohortes6/1 y GREEN7/0skip son selección acotada, no aceptación Windows/POSIX completa ni nativa. | ✓ Conservado producto de curación. tasks.md:1262,1473; no cambio servicio/locks/guards. evals/run.py:134–164 limpia sólo cwd recibido de preparar_cwd, limita retry a unlink regular readonly Windows dentro del cwd y sin reparse; pruebas :402–458 verifican Windows, no aceptación POSIX/nativa completa. | ✓ Conservado producto curación. Scanner sólo cambia puerta de tests. evals/run.py:335–346 conserva limpieza/caso fallido/retención real; redacción no borra ni mueve ruta. test_evals.py:490,525–529,560–561 observa sentinel y JSON. Sin aceptación nueva POSIX/nativa. |
| 18 | T-11 | T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. Referencia de traspaso: tasks.md:1263. | ✓ Conservado. Sin delta a productores/commands/retro; evidencia heredada :1263 intacta. | ✓ Conservado. tasks.md:1263,1474; productores/retro/commands sin delta. No autoaprobación. | ✓ Conservado. tasks.md:1263,1474; productores, comandos y retro sin delta, sin autoaprobación. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 19 | T-08/T-11/T-14 | Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. Referencia de traspaso: tasks.md:1264. | ✓ Conservado implementación. E22 CONTRACTS.md:85 incorpora gate real y conserva pending/no aprobación; suites bridge/curation ejecutadas PID3364 exit0:161 pases y2 skips. No cambia nombre/SHA/Gold/store; evidencia heredada :1264. | ✓ Conservado. tasks.md:1264,1475,CONTRACTS.md:85; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado. tasks.md:1264,1475; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 20 | T-07/T-11 | Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. Referencia de traspaso: tasks.md:1265. | ✓ Conservado. Sin delta journal/handoff y sin promoción por repetición. Nueva clasificación de runtime en test_graphiti_security.py:292–397 se limita al scanner de tests y no cambia autoridad. | ✓ Conservado. tasks.md:1265,1476; scanner de tests cambia clasificación conservadora, no journal ni autoridad. Journal sigue episódico. | ✓ Conservado. tasks.md:1265,1476; journal/handoff sin delta. Scanner AST sólo modifica una puerta de tests, no autoridad de memoria. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 21 | T-07/T-15 | Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. Referencia de traspaso: tasks.md:1266. | ✓ Conservado Q23-1 y producto. No delta workflow/copia/confluence-scope ni tests Confluence; evidencia heredada :1266 y gap :1282. | ✓ Conservado. tasks.md:1266,1282,1477; sin cambios a Confluence/staging/CI en delta3. Q23-1 conservado; ninguna conexión o publicación real. | ✓ Conservado. tasks.md:1266,1282,1477; Confluence/staging/CI sin delta. Q23-1 conservado; no conexión/publicación real. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 22 | T-14 | T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. Referencia de traspaso: tasks.md:1267. | ✓ Revalidado. tasks.md:1321–1340,1360–1376,1393–1425 coincide con recibos terminal/JUnit por cohortes; se conservan70 pases/1 fallo y correctivo1 pase separado,161/2skips y598/12skips. QA2 anterior permanece pendiente/fallida; no % ni gate/QA completa nuevos aceptados. | ✓ Revalidado. tasks.md:1490–1548 conserva error preparación, RED5/GREEN130, tres RED6/1 y GREEN7; mismos7 repetidos. Dos verify históricos no reproducidos, causa pendiente y100ms intactos; diagnóstico final sin JUnit nuevo. QA2Linux6209/78/44,6331 no se transforma en verde; PyTracer/trace-changed y gates históricos insuficientes. tasks.md:1550–1561 distingue preparación QA3 de ejecución/aceptación. | ✓ Revalidado. tasks.md:1598–1610 conserva RED 6/GREEN 136; :1622–1642 conserva 20/7, RED 2 y verdes 2,45,45 + noop 1 separado. XML/terminales cotejados. :1644–1649 conserva HTTP no reproducido y deadlines, sin causa inventada. :1587–1591 mantiene QA2 Windows 6215/24/92 y Linux 6209/78/44, ambos 6331 FAIL. Sin QA3 ni cobertura válida. | ✓ Revalidado. tasks.md:1731–1759 conserva RED7/GREEN143 y RED5/GREEN dedicado5/GREEN30 separados, PIDs/XML cotejados; no suma como cobertura/suite única. :1761–1771 y recibo QA2 mantienen FAIL Windows6215/24/92 y Linux6209/78/44, auditorías inutilizable/corrupta, procesos aceptados null, sin QA3. |
| 23 | T-15 | T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. Referencia de traspaso: tasks.md:1268. | ✓ Conservado A23-1/Q23-2. Sin delta a rules/MODOS/snippet/validador/oráculos Unicode; evidencia heredada :1268 y :1283. Helper de tests sin CLI nueva; no cambia promesa de consola. | ✓ Conservado. tasks.md:1268,1283,1479; A23-1/Q23-2 sin delta a snippet/MODOS/Unicode. Helper no añade CLI de producto. | ✓ Conservado. tasks.md:1268,1283,1479; snippet/MODOS/Unicode sin delta. evals/run.py:65–69 conserva consola UTF-8; no CLI de producto nueva. A23-1/Q23-2 no se reabren. | ✓ Conservado A23-1/Q23-2. No delta a consola/MODOS/Unicode; importlib es stdlib y no añade CLI. Evidencia histórica intacta. |
| 24 | T-01..T-16 | Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. Referencia de traspaso: tasks.md:1269. | ✓ Revalidado. tasks.md:192,1305–1308,1339–1340,1350–1354,1427–1432 conserva intento2 pendiente, QA2 intacta, macros/publicación/gates pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria; objetivo no cancelado. | ✓ Conservado. tasks.md:14–24,192,1486–1488,1513–1515,1560–1561: ciclo post-QA3/MAX3 sin reset original1–3/post1–2; sólo1/16, skills aplazadas después comandos/dashboard/hooks/memoria; QA/gates/commit/push/cierre global pendientes. | ✓ Conservado. tasks.md:1564–1593 preserva rechazo de intento 3, decisión ROOT de una única revisión adicional global 4/MAX4 y original 1–3/post 1–3 sin reset. :1655–1657 mantiene QA completa/gates/macros/push/cierre pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria. | ✓ Conservado. tasks.md:1714–1726 y ROOT4 preservan rechazo3/MAX3 y4/MAX4; global5/MAX5 único pase explícito replan, sin reset ni deuda. :1759,1769–1771 mantiene revisión5,QA3,gates,cobertura,publicación/macros pendientes; sólo1/16 y skills aplazadas. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 6: Fase QA (T-14/T-15) — correcciones aceptadas; QA completa pendiente

ROOT fusiona A+B, genéricos con contexto fresco/modelo heredado. Selector C=false/D=false.
1030 hashes de fuente coinciden antes/después; informes, recibos e índices íntegros
cotejados: A6 21 artefactos y B6 62. Los anexos A5/B5 son byte exactos;
la tabla conserva las 24 filas y todas sus evidencias anteriores, añadiendo sólo6.
El primer cotejo ROOT falló antes de escribir recibos: el formatter A6 anexó el
juicio6 dentro de la última celda5. ROOT cotejó íntegros todos los campos previos
y el prefijo literal de esa celda; aquí separa el juicio añadido, sin modificar
el informe sellado ni sus veredictos. No fue fallo de producto o nuevo intento.
Tres criterios cerrados T-01 y diez warnings preservados. Rechazos3/4/5
siguen intactos; el pase6/MAX6 procede de la decisión ROOT5 explícita, sin reset.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | Mutación de identidad parser oculta argv | T-14/T-15 | corregido, aceptado ROOT6 | test_graphiti_security.py:326–336,353–355,2431–2454; RED3 PID38164/GREEN146 PID19260; B6 24 sondas OWN PID2396 exit0,14 cuerpos con subprocess mock y cinco controles limpios |
| A23-QA4-1 | Important | Diagnóstico nuevo persistido sin redactor | T-14/T-15 | aceptación ROOT5 conservada | evals/run.py:299–313,342–344; RED5/GREEN30, A5/B5; sin delta6 |

| # | Tarea | Criterio | ✓/✗ histórico | Evidencia heredada completa | Estado y evidencia delta2 heredados | Juicio y evidencia delta3 | Juicio y evidencia adicional 4/MAX4 | Juicio y evidencia global5/MAX5 | Juicio y evidencia global6/MAX6 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | T-01 | T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. Referencia de traspaso: tasks.md:1246. | ✓ Conservado. tasks.md:48,54–56 y33–40 mantiene única macro T-01 completa, tres criterios y1/16; ninguna nueva macro se cierra. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada,1/16. Sus tres criterios se desglosan abajo; ninguna macro se cierra en este delta. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada, 1/16; se conservan sus tres criterios ejecutados. Ninguna macro se cierra. | ✓ Conservado. tasks.md:33–56: sólo T-01 completada,1/16; tres criterios y evidencia ejecutada sin delta. | ✓ Conservado. tasks.md:33–56: sólo T-01 completada, 1/16; tres checks y Verificación ejecutada sin delta. |
| 2 | T-14/T-15/T-16 | Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. Referencia de traspaso: tasks.md:1247. | ✓ Revalidado. tasks.md:239 tests/** y ledger, :250 docs/** y tests/**, :260 ambos changelogs; corresponde QA/documentación del plan:19–21,45–48. Scope terminal PID14652 exit0:11 en alcance,0 fuera/avisos/excluidos. PID13620 del despacho no coincide con terminal y no se usa. | ✓ Revalidado. tasks.md:239,250,260 declara tests/kit/skills/docs y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID6176 exit0,6 en alcance,0 fuera/avisos/info/excluidos (terminal y hashes propios comprobados). | ✓ Revalidado. tasks.md:239,250,260 declara evals/**, tests/**, skills/**, ledger y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID 28776 exit 0: ocho rutas dentro, cero fuera/avisos/info/excluidos. Limpieza del fixture y serialización del runner son reparación de QA, no ampliación de skills. | ✓ Revalidado. tasks.md:239,250,260 declara tests/**,evals/**,docs/** y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope autor PID9148 exit0,7 dentro,0 fuera/avisos/info/excluidos; reparación acotada QA y replan ROOT4:1714–1726. | ✓ Revalidado. tasks.md:239,250,260 declara tests/**, ledger y ambos changelogs; plan:19–21,45–48 y replan ROOT5/tasks.md:1826–1831 acotan esta reparación. Scope autor PID35272 exit0: cuatro dentro, cero fuera/avisos/info/excluidos. |
| 3 | T-14 | Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. Referencia de traspaso: tasks.md:1248. | ✓ Revalidado línea a línea: test_graphiti_security.py:2250–2348 prueba datos/argv, parseo/red, rutas y lector local real; test_knowledge_services.py:1379–1404 prueba ambos recorridos; test_lint_plugin.py:497–516 controla noexec/otro/missing. test_training_data_services.py:572–601 separa resolución/timeout y mantiene los asserts; test_memory_path.py:185–284 mantiene payload/contexto/área/topes. test_knowledge_router_read.py:366–371 sólo añade diagnóstico info. No existe % oficial nuevo del diff aceptado: pendiente, sin usar cohortes como cobertura. | ✓ Revalidado. tests/test_graphiti_security.py:308–339,2369–2385 conserva detector real y cinco negativos de mutación/alias/delete; RED5 y GREEN130/0skip ejecutados. test_task_brief.py:1802–1823 copia cuatro dependencias reales, preserves assertions/topes y GREEN7. test_backend_markdown_export.py:278,528–530 mantiene condiciones,100ms y añade sólo dict/presencia. Último archivo diagnóstico sin rerun todavía; tests existentes no equivalen a QA completa. Sin % oficial nuevo aceptado del diff. | ✓ Revalidado línea a línea. test_graphiti_security.py:332–347,2405–2422 recoge Assign/AnnAssign/NamedExpr y exige argv + ofensor real para seis variantes; RED 6/GREEN 136. evals/test_evals.py:402–458 comprueba Git readonly/ausencia real y denegación visible/conservación del sentinel; RED 2/GREEN 2 y cohorte 45. test_coverage_gate.py:160,262 cambia sólo shlex.join; conserva mínimos/diff/exit/asserts. No % oficial nuevo válido del diff. | ✓ Revalidado línea a línea. tests/test_graphiti_security.py:330–340,357–359,2413–2431: guardia conservadora de métodos y siete regresiones argv + detector real; RED7 PID21444/GREEN143 PID35096. evals/test_evals.py:462–561 persiste JSON, espía y delega redactor real, comprueba marcadores ausentes y cuatro fallbacks; RED5 PID22624/GREEN30 PID13396. Sin porcentaje oficial válido para este diff7; cohortes no son cobertura. | ✓ Revalidado línea a línea. tests/test_graphiti_security.py:2431–2454 nombra B23_QA2_1, observa argv bajo mock antes de exigir argv claude y ofensor en detectores reales. Tres variantes class-alias/class-setter/internal-method-alias. RED3 PID38164/GREEN146 PID19260 cotejados. No porcentaje oficial válido del diff actual; cobertura pendiente, cohortes no equivalen a cobertura. |
| 4 | T-14/T-15 | Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. Referencia de traspaso: tasks.md:1249. | ✓ Revalidado contra CONSTITUTION.md:10–13,17–21,26,29,33–38. Tests/soporte stdlib, RED real conservado en tasks.md:1321–1330,1360–1366,1393–1394,1409–1412; controles dedicados y espejos CHANGELOG.md/CHANGELOG.es.md:17–18. No nueva llamada de red hook ni edición manual generada; no aprobación de memoria ni cierre/publicación. | ✓ Revalidado. CONSTITUTION.md:10–13,17–21,26,29,33–38: helper usa stdlib, RED válido precede corrección y cinco regresiones nombradas; mirrors EN/ES actualizados; fuente generada y juicio Curator conservados. Pytest es infraestructura de test existente, no dependencia nueva del producto. El error import PID1480 no cuenta como RED. | ✗ Nuevo A23-QA4-1 Important. CONSTITUTION.md:34 exige que todo texto persistido pase por redact.py. evals/run.py:324–325 crea detalle.cleanup como texto y :397 lo persiste por json.dump sin cargar/invocar ese redactor. El resto conserva stdlib, TDD (tasks.md:1598–1610,1629–1642), fuentes y espejos; no se reabren violaciones previas ajenas al delta. | ✓ A23-QA4-1 corregido conforme en A5: evals/run.py:299–313,342–344 carga por ruta propia y llama module.redactar antes de json.dump:416; fallback fijo seguro para redactor ausente/fallido/no-texto. CONSTITUTION.md:34 satisfecho; :11–13 evidencia dedicada RED5/GREEN30 tasks.md:1745–1758, stdlib y espejos intactos. | ✓ Revalidado. CONSTITUTION.md:11,13 satisfechos por RED válido y test dedicado B23_QA2_1; tasks.md:1850–1856 conserva NameError inválido y descarte/re-escritura. :17–21,26,34–37 sin violación nueva: fuente de pruebas, stdlib, espejos EN/ES, sin cambio de autoridad/red/persistencia de producto. A23-QA4-1 corregido/aceptado ROOT5:1783,1788. |
| 5 | T-01 | Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. Referencia de traspaso: tasks.md:1250. | ✓ Conservado. Verificación ejecutada T-01 heredada tasks.md:52 y fila aceptada :1250. El delta no altera Estado ni sus tres criterios; otras15 macros abiertas. No ejecuté ninguna verificación para cubrir falta de evidencia. | ✓ Conservado. tasks.md:52 contiene verificación ejecutada T-01 y :54–56 sus tres checks. Ninguna otra macro cerrada; no ejecuté una verificación para ocultar ausencia. | ✓ Conservado. tasks.md:52 conserva la verificación ejecutada de la única macro cerrada; :54–56 sus tres checks. No ejecuto verificaciones para cubrir evidencia faltante. T-14/T-15 abiertas, T-16 borrador. | ✓ Conservado. tasks.md:48,52,54–56: única tarea cerrada y Verificación ejecutada. T-14/T-15 abiertas; T-16 borrador. No ejecuté una verificación faltante para cubrir evidencia. | ✓ Conservado. tasks.md:48,52,54–56 contiene ejecución de Verificación T-01; demás macros abiertas/borrador. Ninguna verificación faltante ejecutada por A6. |
| 6 | T-11/T-15 | Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. Referencia de traspaso: tasks.md:1251. | ✓ n/a al delta11: sólo tests, CONTRACTS, changelogs y ledger; no commands/, agents/ ni hooks/. No ejecuté export. Evidencia autor adicional qa-rem-review2-final-exports/terminal.json PID5800 exit0 y stdout exacto export-interop --check: 88 ficheros al día; hashes stdout/stderr comprobados, separado del check heredado PID17500. | ✓ n/a al delta6: no commands/, agents/ ni hooks/. Prompt A no requiere ejecución propia de export aquí. Autor PID6488 exit0,88 ficheros al día, terminal/streams verificados; separar del check histórico17500. | ✓ n/a al delta ocho: no commands/, agents/ ni hooks/. No ejecuté export-interop; evidencia autor PID 30612 exit 0 y stdout «export-interop --check: 88 ficheros al día», streams cotejados. interop/** declarado en tasks.md:250. No se atribuye como ejecución propia nueva. | ✓ n/a: diff7 no toca commands/,agents/ ni hooks/. No ejecuté exportador. Evidencia autor PID27252 exit0, stdout export-interop --check: 88 ficheros al día; hashes de terminal y streams cotejados. tasks.md:250 declara interop/**; separar de check propio históricoPID17500. | ✓ n/a al delta4: no commands/, agents/ ni hooks/. No ejecuté exportador. Evidencia autor PID20444 exit0, stdout exacto export-interop --check: 88 ficheros al día; terminal/streams cotejados. interop/** declarado tasks.md:250; no nueva obligación de ledger --check de tarea cerrada. |
| 7 | T-15 | Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. Referencia de traspaso: tasks.md:1252. | ✓ Revalidado E3. CONTRACTS.md:85 cambia sólo Puerta E22 por dos rutas existentes del bridge/servicio y conserva QA pendiente/Gold nunca aprueba. test_training_data_services.py:386–407 exige ruta real. CHANGELOG.md/CHANGELOG.es.md:17–18 y tasks.md:1303–1432 describen scanner/espía/fixtures, sin promesa global. Producto/callers sin delta. | ✓ Revalidado. CONTRACTS.md:85,118–119,140–142 conserva E22/E53/E54 y condición E3. Sólo tests/scanner/fixture cambian, sin arista/caller o flujo de producto nuevo; CHANGELOG.md/CHANGELOG.es.md:18,20 y tasks.md:1433–1561 describen exactamente esos cambios y límites en esta tarea. | ✓ Revalidado. CONTRACTS.md:66,140–142 exige E3/espejos. Ninguna arista de productor/caller cambia. evals/README.md:79–85,157–163 describe limpieza/cleanup_error en ES/EN en esta misma tarea; CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1596–1657 describen scanner/fixtures/runner y límites. No obligación de modificar FLOWS por un flujo del ciclo inexistente en el delta. | ✓ E3 revalidado. CONTRACTS.md:140–142: sin cambio de cadena del ciclo; README evals:84–88,167–171 describe redactor/fallback/ruta retenida ES/EN en esta tarea. CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1729–1771 describen scanner/redactor y límites; sin nueva autoridad/flujo de memoria. | ✓ Revalidado. CONTRACTS.md:140–142 no introduce E2/flujo E3 nuevo. CHANGELOG.md/CHANGELOG.es.md:18 describen class/internal/setters en ESTA tarea; tasks.md:1844–1869 documenta guardia/pruebas/límites actuales. No cambio de productor/caller/autoridad de memoria. |
| 8 | T-08/T-11 | API OpenAPI | ✓ | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. Referencia de traspaso: tasks.md:1253. | ✓ n/a; las11 rutas no incluyen spec OpenAPI. No ejecutado lint. | ✓ n/a: seis rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: ocho rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: siete rutas sin spec OpenAPI; no ejecutado openapi-lint. | ✓ n/a: cuatro rutas sin spec OpenAPI; no ejecutado openapi-lint. |
| 9 | T-15 | Docs-style | ✓ | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. Referencia de traspaso: tasks.md:1254. | ✓ n/a conservado como gate exclusivo de prosa; sin hallazgo de requisitos ni reapertura por estilo. | ✓ Aplicado a este delta mayoritariamente prosa por líneas; docs-style.md:14–25. tasks.md:1433–1561 y changelogs:18,20 usan evidencia y comparaciones concretas, sin promesa global/nativa. Tabla única de gap :1482–1484 responde al formato obligatorio SKILL §6, no se elimina por preferencia; no hallazgo citable nuevo. | ✓ n/a al criterio adicional de iniciativa mayoritariamente prosa: semántica de código/tests y documentación de QA. docs-style.md:15–22 leído; no se reporta estilo. Tabla de una fila en ledger responde al formato obligatorio SKILL §6. | ✓ n/a: iniciativa de corrección de código/tests con evidencia documental; docs-style.md:15–22 leído. Sin nueva violación citable de requisitos ni hallazgo de estilo. | ✓ Conservado; docs-style.md:15–22 leído para la evidencia documental del delta. No gap de requisito/constitución ni reapertura por estilo. |
| 10 | T-07 | T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. Referencia de traspaso: tasks.md:1255. | ✓ Conservado. Sin delta al servicio, knowledge-write/check ni contrato de corte prospectivo; evidencia heredada :1255 sigue vigente. | ✓ Conservado. tasks.md:1255,1466; ningún delta a knowledge-write/check/contrato o producto. Legado sin migración/reaprobación. | ✓ Conservado. tasks.md:1255,1466; sin delta a knowledge-write/check/contrato de corte prospectivo. No migración ni reaprobación del legado. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 11 | T-08 | T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. Referencia de traspaso: tasks.md:1256. | ✓ Conservado. Sin delta al servicio/Curator. CONTRACTS.md:85 conserva explícitamente Gold no aprueba, sólo pending; juicio no delegado a QA. | ✓ Conservado. tasks.md:1256,1467; persistencia/Curator sin delta. QA/Gold no aprueban memoria. | ✓ Conservado. tasks.md:1256,1467; servicio/Curator sin delta. QA/Gold/revisión no aprueban memoria. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 12 | T-08 | Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. Referencia de traspaso: tasks.md:1257. | ✓ Conservado. Sin delta a propose/redactor/alias/reserva; evidencia heredada :1257 intacta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases/reserva/redactor sin delta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases de candidatos/reserva/redactor de memoria sin delta. Aliases del scanner son otro dominio. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 13 | T-08 | SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. Referencia de traspaso: tasks.md:1258. | ✓ Conservado. Sin delta a SHA/metadatos/_caught ni test B4; evidencia heredada :1258 intacta. | ✓ Conservado. tasks.md:1258,1469; SHA original/metadatos y test B23-4 sin delta. | ✓ Conservado. tasks.md:1258,1469; SHA/metadatos/_caught y test B23-4 sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 14 | T-08 | needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. Referencia de traspaso: tasks.md:1259. | ✓ Conservado. Sin delta a transiciones/replacement/terminal rejected; evidencia heredada :1259 intacta. | ✓ Conservado. tasks.md:1259,1470; transiciones y replacement ligados a SHA original sin delta. | ✓ Conservado. tasks.md:1259,1470; transiciones/replacement y rejected terminal sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 15 | T-08 | Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. Referencia de traspaso: tasks.md:1260. | ✓ Conservado. Sin delta al gate/validadores; E22 sólo enumera su puerta de ejecución, no añade mutación ni transición. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate puro y validadores compartidos sin delta. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate y validadores compartidos sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 16 | T-08/T-14 | Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. Referencia de traspaso: tasks.md:1261. | ✓ Conservado. Sin delta a operaciones/recibos/recover ni oráculos de interrupción; evidencia heredada :1261 intacta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y fronteras reales sin delta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y cortes reales sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 17 | T-08/T-14 | Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. Referencia de traspaso: tasks.md:1262. | ✓ Conservado producto. Fixture Windows test_memory_path.py:151–169 ahora aporta shim/SYSTEMROOT/Python coherentes con shell, sin relajar aserciones. test_lint_plugin.py:41–60 simula X_OK sólo del path exacto y :497–516 comprueba delegado/missing. tasks.md:1375–1376,1400–1407,1418–1421 conserva límites, intento fallido y skips; no acredita POSIX/nativo. | ✓ Conservado. tasks.md:1262,1473; ningún cambio producto/OS/permisos. Fixture Linux lector real RED trescohortes6/1 y GREEN7/0skip son selección acotada, no aceptación Windows/POSIX completa ni nativa. | ✓ Conservado producto de curación. tasks.md:1262,1473; no cambio servicio/locks/guards. evals/run.py:134–164 limpia sólo cwd recibido de preparar_cwd, limita retry a unlink regular readonly Windows dentro del cwd y sin reparse; pruebas :402–458 verifican Windows, no aceptación POSIX/nativa completa. | ✓ Conservado producto curación. Scanner sólo cambia puerta de tests. evals/run.py:335–346 conserva limpieza/caso fallido/retención real; redacción no borra ni mueve ruta. test_evals.py:490,525–529,560–561 observa sentinel y JSON. Sin aceptación nueva POSIX/nativa. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 18 | T-11 | T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. Referencia de traspaso: tasks.md:1263. | ✓ Conservado. Sin delta a productores/commands/retro; evidencia heredada :1263 intacta. | ✓ Conservado. tasks.md:1263,1474; productores/retro/commands sin delta. No autoaprobación. | ✓ Conservado. tasks.md:1263,1474; productores, comandos y retro sin delta, sin autoaprobación. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 19 | T-08/T-11/T-14 | Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. Referencia de traspaso: tasks.md:1264. | ✓ Conservado implementación. E22 CONTRACTS.md:85 incorpora gate real y conserva pending/no aprobación; suites bridge/curation ejecutadas PID3364 exit0:161 pases y2 skips. No cambia nombre/SHA/Gold/store; evidencia heredada :1264. | ✓ Conservado. tasks.md:1264,1475,CONTRACTS.md:85; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado. tasks.md:1264,1475; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 20 | T-07/T-11 | Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. Referencia de traspaso: tasks.md:1265. | ✓ Conservado. Sin delta journal/handoff y sin promoción por repetición. Nueva clasificación de runtime en test_graphiti_security.py:292–397 se limita al scanner de tests y no cambia autoridad. | ✓ Conservado. tasks.md:1265,1476; scanner de tests cambia clasificación conservadora, no journal ni autoridad. Journal sigue episódico. | ✓ Conservado. tasks.md:1265,1476; journal/handoff sin delta. Scanner AST sólo modifica una puerta de tests, no autoridad de memoria. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 21 | T-07/T-15 | Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. Referencia de traspaso: tasks.md:1266. | ✓ Conservado Q23-1 y producto. No delta workflow/copia/confluence-scope ni tests Confluence; evidencia heredada :1266 y gap :1282. | ✓ Conservado. tasks.md:1266,1282,1477; sin cambios a Confluence/staging/CI en delta3. Q23-1 conservado; ninguna conexión o publicación real. | ✓ Conservado. tasks.md:1266,1282,1477; Confluence/staging/CI sin delta. Q23-1 conservado; no conexión/publicación real. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 22 | T-14 | T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. Referencia de traspaso: tasks.md:1267. | ✓ Revalidado. tasks.md:1321–1340,1360–1376,1393–1425 coincide con recibos terminal/JUnit por cohortes; se conservan70 pases/1 fallo y correctivo1 pase separado,161/2skips y598/12skips. QA2 anterior permanece pendiente/fallida; no % ni gate/QA completa nuevos aceptados. | ✓ Revalidado. tasks.md:1490–1548 conserva error preparación, RED5/GREEN130, tres RED6/1 y GREEN7; mismos7 repetidos. Dos verify históricos no reproducidos, causa pendiente y100ms intactos; diagnóstico final sin JUnit nuevo. QA2Linux6209/78/44,6331 no se transforma en verde; PyTracer/trace-changed y gates históricos insuficientes. tasks.md:1550–1561 distingue preparación QA3 de ejecución/aceptación. | ✓ Revalidado. tasks.md:1598–1610 conserva RED 6/GREEN 136; :1622–1642 conserva 20/7, RED 2 y verdes 2,45,45 + noop 1 separado. XML/terminales cotejados. :1644–1649 conserva HTTP no reproducido y deadlines, sin causa inventada. :1587–1591 mantiene QA2 Windows 6215/24/92 y Linux 6209/78/44, ambos 6331 FAIL. Sin QA3 ni cobertura válida. | ✓ Revalidado. tasks.md:1731–1759 conserva RED7/GREEN143 y RED5/GREEN dedicado5/GREEN30 separados, PIDs/XML cotejados; no suma como cobertura/suite única. :1761–1771 y recibo QA2 mantienen FAIL Windows6215/24/92 y Linux6209/78/44, auditorías inutilizable/corrupta, procesos aceptados null, sin QA3. | ✓ Revalidado. tasks.md:1850–1856 separa NameError PID39108/6996 de RED válido3 PID38164; :1864–1869 conserva GREEN146/0skip/48.44s, SHAs XML y revisión6/QA3/cobertura pendientes. Terminales, streams y casos JUnit cotejados; no suma como QA global. |
| 23 | T-15 | T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. Referencia de traspaso: tasks.md:1268. | ✓ Conservado A23-1/Q23-2. Sin delta a rules/MODOS/snippet/validador/oráculos Unicode; evidencia heredada :1268 y :1283. Helper de tests sin CLI nueva; no cambia promesa de consola. | ✓ Conservado. tasks.md:1268,1283,1479; A23-1/Q23-2 sin delta a snippet/MODOS/Unicode. Helper no añade CLI de producto. | ✓ Conservado. tasks.md:1268,1283,1479; snippet/MODOS/Unicode sin delta. evals/run.py:65–69 conserva consola UTF-8; no CLI de producto nueva. A23-1/Q23-2 no se reabren. | ✓ Conservado A23-1/Q23-2. No delta a consola/MODOS/Unicode; importlib es stdlib y no añade CLI. Evidencia histórica intacta. | ✓ Conservado. tasks.md:1268,1283 y tests/test_graphiti_security.py:2437 import subprocess local: no CLI nueva ni delta a consola/MODOS/oráculos Unicode; A23-1/Q23-2 intactos. |
| 24 | T-01..T-16 | Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. Referencia de traspaso: tasks.md:1269. | ✓ Revalidado. tasks.md:192,1305–1308,1339–1340,1350–1354,1427–1432 conserva intento2 pendiente, QA2 intacta, macros/publicación/gates pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria; objetivo no cancelado. | ✓ Conservado. tasks.md:14–24,192,1486–1488,1513–1515,1560–1561: ciclo post-QA3/MAX3 sin reset original1–3/post1–2; sólo1/16, skills aplazadas después comandos/dashboard/hooks/memoria; QA/gates/commit/push/cierre global pendientes. | ✓ Conservado. tasks.md:1564–1593 preserva rechazo de intento 3, decisión ROOT de una única revisión adicional global 4/MAX4 y original 1–3/post 1–3 sin reset. :1655–1657 mantiene QA completa/gates/macros/push/cierre pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria. | ✓ Conservado. tasks.md:1714–1726 y ROOT4 preservan rechazo3/MAX3 y4/MAX4; global5/MAX5 único pase explícito replan, sin reset ni deuda. :1759,1769–1771 mantiene revisión5,QA3,gates,cobertura,publicación/macros pendientes; sólo1/16 y skills aplazadas. | ✓ Conservado. tasks.md:1830–1841,1868–1869 mantiene rechazos3/4/5 sin reset, una revisión6/MAX6 explícita y QA2 FAIL/QA3/cobertura/macros/push/cierre pendientes. :192 conserva skills aplazadas; T-01 sigue 1/16. |


Detalle y pruebas originales: [historial](execution-history.md).

## Revisión de dos lentes — intento 1: Bloque24 (T-14) — pruebas adicionales de memoria

Bloque nuevo de tres pruebas, separado de la revisión aceptada6 del producto:
intento1 de3, lentes A+B. Selector PID14604 exit0, C=false/D=false, sin avisos.
Contexto fresco por revisores genéricos con modelo heredado; API de reviewer por
nombre no disponible. Alcance sin Git: selección explícita de los tres archivos,
scope-gate saltado con aviso, sin simular exit0. No cambia el veredicto ni el
historial de intentos3/4/5/6 de la fuente anterior.

| Criterio del bloque | A | B | Evidencia |
|---|---|---|---|
| CLI y handoff reales | ✓ | ✓ | Confluence main, servicio propose/apply/recover y recorder Gold real |
| Errores e inputs corruptos observables | ✓ | ✓ | Códigos, snapshots y fronteras IO específicas |
| Bytes, identidades y estado preservados | ✓ | ✓ | SHA de bytes persistidos, fuente/store/policy conservados |
| Recuperación, idempotencia y lock cooperante | ✓ | ✓ | Servicio real, operación durable y hilo dueño liberado en finally |
| Gold exclusivamente candidato | ✓ | ✓ | Sin approved, trayectoria ni writer alternativo |
| Fixtures locales sin servicios externos | ✓ | ✓ | tmp_path, sin red ni subprocess en la cohorte acotada |
| Originales/umbrales intactos | ✓ | ✓ | Tres archivos nuevos; fuente1030 y dependencias86 verificadas |
| Evidencia y límites de54 casos | ✓ | ✓ | JUnit real, Windows acotado; Linux/global/multiproceso no aceptados |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin defectos ni gaps abiertos en este bloque | T-14 | No necesaria | A+B leyeron los tres tests completos y contratos/transitivos pertinentes |


Detalle y pruebas originales: [historial](execution-history.md).

## Bloque24 — integración revisada y validación conjunta pendiente

Registro histórico: [detalle original](execution-history.md).

## Bloque25 — traslado de memoria, commits y actividad integrada

Registro histórico: [detalle original](execution-history.md).

## Consulta de revisiones al retomar — candidata, verificación incompleta

Registro histórico: [detalle original](execution-history.md).

## Lectura estable — comprobación focal completada, cierre conjunto pendiente

Registro histórico: [detalle original](execution-history.md).

## Estado actual de validación

La integración sigue en curso; ninguna tarea macro se cierra con esta reorganización.
Las revisiones estructuradas mantienen los mismos encabezados, intentos, resúmenes,
filas y fronteras de selección. Toda la narrativa original posterior a las tareas
se conserva íntegra en [execution-history.md](execution-history.md).

La candidata incorpora lectura estable Windows y consultas CLI sin cachés:
392 pruebas correctas y seis omitidas en la regresión ampliada; 187 correctas y
seis omitidas en el control posterior, con 23/23 líneas nuevas cubiertas.
Los workloads separados completaron 100 y 250 ciclos sin reintentos.
[Evidencia](testing/stable-read25-evidence.json). Se conservan los resultados rojos
históricos; no se han identificado todas sus causas.

La QA completa de working24 pasa en Windows y Linux. Pendientes: aceptación
de workflows nativos, UI real, comparación restante de recursos y revisión independiente.
Las skills siguen aplazadas. Este lote no tiene commit ni push.

La retoma del ledger reorganizado se ejecutó con el CLI común: estado `ok`,
16 tareas, sin escrituras ni nuevos directorios en el proyecto. La selección de
revisiones, gaps del brief y puerta Jira coincide con la fuente anterior.
[Evidencia](testing/ledger-readability25-evidence.json).

## Corrección de límites históricos y QA completa

Se conservan los encabezados no pertenecientes a revisiones que usan los
consumidores del ledger. La retoma funciona y no altera las decisiones previas.
La QA full03 histórica permanece en rojo; sus resultados y siguientes pasos constan en
[la evidencia](testing/full03-and-ledger-boundaries25-evidence.json) y el
[estado de validación](testing/final-qa25-status.md). Ninguna tarea macro se cierra.

## Publicación de estado propio — corrección acotada

Se reprodujo un rechazo real de Windows con un lector que no comparte borrado.
La corrección conserva la generación y el plazo entre intentos. Regresión Windows:
221 correctas y dos omisiones; comprobación local Linux: 18 correctas y seis
omisiones específicas de Windows. [Evidencia](testing/state-publication26-evidence.json).
No explica los fallos históricos ni cierra tareas macro, QA, UI o revisión final.

## Cierre OpenCode y aislamiento de captura — corrección acotada

La búsqueda de taskkill por PATH bloqueaba el cierre Windows. La ruta del
sistema resuelve el caso real, con una regresión permanente RED/GREEN y las
20 pruebas del módulo aprobadas. Se sincronizó el adaptador generado.
El registro de captura deja de recibir resultados de actividad ajenos.
[Evidencia](testing/opencode-lifecycle27-evidence.json). Las suites completas
anteriores siguen fallidas o incompletas; no se cierran tareas macro.

## QA conjunta Windows/Linux — fuente working24 aceptada

La suite Python completó 7.020 casos por plataforma, conservando las colecciones
anteriores: Windows 6.921 correctos y 99 omitidos; Linux 6.962 correctos y 58
omitidos. No hubo fallos ni errores. Ambos gates de cobertura pasan sin redondeo;
el dashboard original se ejecutó directamente en los dos padres y pasa.
Node: Windows 328 correctos; Linux 312 correctos y 16 casos exclusivos de Windows
omitidos. Código y dependencias preservados, contenedores propios retirados.
[Evidencia](testing/dual-platform-qa29-evidence.json).

Esta entrada acepta la QA de esa fuente; no cierra las tareas macro, workflows,
UI, comparación de dependencias, revisión independiente ni publicación.
La actualización documental conserva el código probado y el historial de revisiones.

## Narrativa operativa del 2026-10-10/11 — trasladada

Las secciones de dependencias, memoria aprendida, hooks, transporte nativo, OpenCode V2, consumidor de plan, memoria pendiente, feedback, curación/portabilidad, publicador, conectividad y Graphiti real están íntegras en [execution-history.md](execution-history.md) («Traslado 2026-10-13», SHA-256 `\7a5394b52bb997ef6ae88800ca6e60ec02b61ecd6b84f7b45ed62f069fa8c07`). Ninguna revisión ni asociación de curación se movió.

## Validación OWN68–OWN70: plazo nativo y cobertura del panel

El arranque síncrono de Codex debe consumir el deadline original. RED Windows
y Linux: un proceso real devuelve exit 0 después de vencido el plazo, donde
la regresión exige 124 sin salida. GREEN de la corrección: seis casos en cada
plataforma, sin skips. El código conserva el deadline absoluto y comprueba
la fecha al aceptar éxito. Fixtures Windows preparan el ejecutable copiado;
Linux enlaza el Node instalado y el contenedor de prueba usa init para recoger
descendientes terminados. Todos los contenedores focales propios se retiraron.

Windows global: 7.126/2/99 sobre 7.227, fallo original preservado. Los dos casos
fallidos pasan juntos tras corregir los modos del Git privado y aclarar la
firma de consulta en documentación, sin cambiar el oracle. Cobertura oficial
CTracer 7.16.2 de los 31 archivos Python modificados: 90,95 %. El runner falló
al interpretar rutas del informe; la auditoría terminal verifica la base de
rutas, todos los archivos y los mismos bytes.

Panel: 61 escenarios DOM originales pasan con fuente renderizada comprobada
y cobertura oficial V8: actividad 100 % / revisión 98,79 % de líneas. No es
aceptación visual ni interacción en navegador. Node global de nueve archivos
conserva 327/329 y dos fallos temporales; concurrencia 2 sin cambiar producto ni
cuerpos agotó 390 s antes de completar. El nuevo recorrido permite 900 s al
cohort completo, con todos los deadlines individuales intactos. Linux global,
revisión independiente, aceptación nativa/visual, utilidad comparativa y
publicación siguen pendientes; no cambia el estado de las macrotareas.

Evidencia: `testing/native-deadline69-evidence.json`,
`testing/native-deadline69-status.md`. Se conservan fallos originales y
recibos privados de cada recorrido; ningún pase focal acepta la suite global.


### Resultado terminal Node OWN69 — mismo código, todos los casos

El recorrido completo con concurrencia de archivos 2 pasa 329/329, sin fallos,
skips o cancelaciones; terminal y limpieza del propietario exit 0. Source1139
permanece idéntica al recorrido fallido por defecto; ningún test ni plazo del
producto cambió entre esas ejecuciones. El presupuesto de cohorte fue 900 s.
CI y copia manual usan el mismo límite 2 y mantienen el glob de todos los tests.
Cobertura V8 oficial: lector Codex 97,73 %, adaptador OpenCode 96,52 % y launcher
85,24 % de líneas; conjunto de esos tres 92,32 %. No es cobertura de todo el
diff JavaScript ni aceptación del dispatcher generado. Los 61 contratos DOM
del panel conservan su medición aparte. Fallos y timeout históricos permanecen
en la evidencia; Linux global y los gates de aceptación pendientes no se cierran.


### Linux OWN68 terminal y causa verificada OWN71

Linux global terminó con 7.160 pases, 8 fallos y 59 skips sobre 7.227 casos;
colección conservada, dashboard directo correcto y cobertura de los 31 archivos
Python modificados de 91,07 %. El contenedor propio se retiró. Siete fallos
proceden de la copia de prueba: archivos bind desde Windows expuestos como
ejecutables y tmpfs sin ejecución pese al chmod de las fixtures. El octavo
corresponde a la firma documental. Con fuente de entrada en solo lectura,
copia nativa con modos exactos del manifiesto y tmpfs ejecutable para las
fixtures, pasan los ocho casos, sin editar tests o producto. Fuente y
dependencias permanecen intactas y el contenedor focal se retiró. La suite
completa bajo esa topología todavía debe ejecutarse; el focal no la acepta.


### Linux global OWN72 y entrypoint generado OWN73

La suite Linux completa en copia nativa pasó: 7.168 casos, 59 skips y cero
fallos sobre los mismos 7.227 IDs; cobertura CTracer de los 31 archivos Python
modificados de 91,07 %, dashboard directo correcto, fuente/dependencias
conservadas y contenedor propio eliminado. La anterior suite fallida se conserva.

El módulo OpenCode generado pasa 23 casos con el instalador real de proyecto
y guardias por rol, sin cambiar aserciones. Cobertura V8 del entrypoint:
93,03 % de líneas / 64,67 % de ramas. La primera fixture parcial conserva
17/20: dos fuentes mal resueltas al mover el test y un bundle incompleto.
Ninguno requirió editar producción. No prueba carga del servidor nativo.

Los seis destinos JavaScript del diff tienen informes V8 reales; contra
HEAD 3be4821 hay 214 líneas de fuente modificadas, dos no cubiertas: 99,07 %.
Este conteo incluye comentarios y líneas vacías; no es una métrica de
statements o ramas ni se suma a cobertura Python. Windows vuelve a ejecutar
la suite completa del source1141 con los modos Git corregidos; sigue pendiente.


### OpenCode nativo OWN75 — contexto, captura, replay y actividad

OpenCode 2.0.12 carga el adaptador d65c59fa actual por el instalador de
proyecto. Dos prompts retenidos verifican UTF-8/private; dos loops con
proveedor local verifican contexto, write/post-tool, capture y replay de
journal en la siguiente sesión. La opción actividad guarda registros
execution_finished del stream nativo; no acredita liveness o colección
completa. Servidor natural exit 0, parent/cleanup exit 0, job activo 0/sin
fuga y todos los hashes Source1141 intactos. Sin credenciales heredadas,
navegador, preferencias personales alteradas o inferencia externa.
El intento previo no arrancó la CLI por una sustitución incorrecta de su
ruta en el helper; se conserva y sólo se corrige esa ruta en otro recibo.
Guardias por rol nativas, aprobación humana por UI y workflows globales
siguen pendientes; no cambia estados de macrotareas. Evidencia propia:
`testing/native-opencode75-evidence.json`, `testing/native-opencode75-status.md`.


### Validación de límites y contención de Windows — 2026-10-12

La suite global de Windows quedó en rojo: 7.126 passed, 2 failed, 99 skipped. Se aisló el salto final no contabilizado por el aviso de brief y la publicación de carpeta del protocolo sintético. Un bloqueo real de carpeta reproduce WinError 32; un lector de auditoría sin delete-sharing reproduce WinError 5. No se identificó el dueño del handle del fallo global original. RED: 17 casos, 12 failed y 5 passed, antes de corregir el CLI y el protocolo de pruebas. Se conserva también el primer verde fallido por una fixture de límite que permitía reducir una sección opcional y dos errores de publicación de auditoría.

GREEN de las suites afectadas: Windows 118 passed; Linux 116 passed, 2 skipped específicos de Windows; fuente preservada y procesos/contenedor propios cerrados. El helper de pruebas reintenta sólo errores 5/32 durante 20/40/80 ms, verifica destino nuevo antes de cada rename y conserva errores persistentes. No modifica la semántica de memoria del producto. [Evidencia y límites](testing/windows-boundary80-status.md). QA global de la fuente actual y puertas nativas/humanas/independientes siguen pendientes.


Las dos causas se propusieron con el servicio canónico como gotchas pendientes; Curator aún no las ha aprobado. Configuración personal preservada. Asociación explícita para retoma:

```curation-refs-v1
[
  {
    "candidate": "docs/knowledge/candidates/pending/2026-10-12-brief-final-newline.md",
    "sha256": "e9cb77fd0c60155f99af39cef2b2792a6eddad70dcf36ed8910bb67d8c940f46",
    "operation_id": "683904c801e08378e656906fe7db12d9d93e54324f244223d6bad7dafc522a35"
  },
  {
    "candidate": "docs/knowledge/candidates/pending/2026-10-12-windows-test-publication.md",
    "sha256": "53cf5e630b780f90a11e7583ff0bbc50a18b0c2a754a13809334c0ac70c54152",
    "operation_id": "6c84b6188c1addcb27081d901dd5d253e92b15b4a8a4e4bfd74e7892d265af86"
  },
  {
    "candidate": "docs/knowledge/candidates/pending/2026-10-12-memory-producer-guard-scope.md",
    "sha256": "63dcee7510b2506d9fbec27ee91f4adeb9f6c156313e44f11c7a34ba4ac287d8",
    "operation_id": "dcfb2b98139ad5861d144d0b7c5305ce192a633587fb79a549d4d59e393234f8"
  },
  {
    "candidate": "docs/knowledge/candidates/pending/2026-10-12-native-activity-start-and-capture.md",
    "sha256": "a847338d5ad29a227fc1ef6eedd5e435ebb376d6202b97d1bdca6b5339ac6087",
    "operation_id": "2c24336cb34e405d25facce40f0659fcbb8b2514be0bd94c00e16e47bb3bb6f2"
  },
  {
    "candidate": "docs/knowledge/candidates/pending/2026-10-12-windows-barrier-ready-read.md",
    "sha256": "97dc7a8f2bdb796e1439000877e21c07558313cdc6b4f972f6b29cf667bfba1f",
    "operation_id": "9899e8ec4b5dd69f60a0d266d259f640a83c475650ac3916744a4dfcd2766011"
  }
]
```


### Alcance nativo de memoria de productores — 2026-10-12

El probe nativo observó un ADR sintético escrito por architect contra su contrato actual. RED unitario: 51 casos, 48 failed y 3 passed; allowlist legacy conservada tras migrar los productores a propuestas. Fix compartido: denegar herramientas de escritura directa en docs/knowledge para implementer/architect, retirar permiso ADR/README antiguo y conservar opt-out explícito e IDs propios exactos. GREEN: 316 casos de guardias/dispatcher en Windows y 316 en Linux. OpenCode instalado: cuatro denegaciones de memoria y dos escrituras permitidas; dos subagentes reales conservan rol/parentID y sólo se restringe al propio. Proveedor controlado, sin juicio externo/humano; source hashes y cierre de procesos verificados. Se conserva el fallo previo del literal de ruta de la fixture. [Evidencia y límites](testing/native-memory-guard90-status.md). Gotcha propuesto por servicio canónico y asociado en curation-refs-v1; no aprobado. QA global actual, aceptación nativa actualizada de Claude/Codex y revisión independiente pendientes.


### QA global source52 y observación durante ejecución — 2026-10-12

La colección fijada de 7.295 casos pasa completa sin fallos/error: Windows 7.196 passed/99 skipped, Linux 7.234 passed/61 skipped. Cobertura oficial parental de 32 fuentes Python: 90,8531% y 90,9698%; dashboard directo, hashes y limpieza propios verificados. [Resultados source52](testing/global-source52-status.md); no se atribuyen a la siguiente fuente.

El probe nativo observó execution.started sin registro. RED Python/Node válido tras corregir el temp propio de la fixture. Fix: separar bindings de actividad/captura, aceptar el inicio nativo en el dueño opt-in y conservar end/idle para SessionEnd. GREEN: Windows 126 passed/1 skip, Linux 127 passed, Node 21 passed. OpenCode instalado observa inicio con proveedor detenido, prompt vivo y cero envelopes prematuros; después registra fin. Fallos de preparación LF/anchor preservados; fuente y cierre propios verificados. [Evidencia](testing/native-activity103-status.md). Gotcha propuesto, asociado y pendiente de Curator.

Se completan catorce cuerpos y dependencias runtime directas de revisión visual; no los callers globales ni aceptación humana. [Comparación](comparisons/plan-review-direct-closure98.md). No se amplían skills. La QA de la fuente actual, recorridos restantes y revisión independiente siguen pendientes.


### Catálogo de actividad y comparación medida — 2026-10-12

QA completa source53 conserva los mismos seis fallos en Windows/Linux, sin aceptarla como verde. RED Windows acotado: seis fallos, 220 passed/2 skips. Causa: vocabulario de actividad terminal y pin del dueño anterior al inicio nativo. Tras revisar el cuerpo completo y sus cargas, GREEN Windows 226 passed/2 skips; Linux pytest exit0, 227 passed/1 skip Windows-junction. El driver Linux conserva exit1 por esperar cero skips; JUnit y limpieza verifican la diferencia, sin repetir ni alterar tests. [Evidencia](testing/activity-catalog-closure114-status.md). QA source54 y revisión siguen pendientes.

Los lectores comparados ejecutan 42 consultas por motor: todas las fuentes top5 en 36/36 frente a 33/36 positivas, sin cruce de proyecto. Doce consultas de contexto conservan vigencia/cobertura desconocidas. [Límites](comparisons/memory-comparison115-status.md). No se acredita generación, UI humana o utilidad externa nueva; se mantiene el origen local y Kwipu/Graphify opcionales. Sin nuevas skills ni cierre de macros.

### Consumo de decisiones de plan — 2026-10-12

RED real: CLI sin consume; contrato ampliado con 16 fallos. Fix en el dueño existente: selección/vista → receive → ack → vista vigente, deadline compartido, sin efectos workflow. GREEN: dueño 68; recetas 34 sin skips; regresión actual 150/1 skip de privilegio. Cuatro sesiones OpenCode ejecutan consume y conservan el JSON real; dos añaden texto/valla y no pasan formato JSON estricto. Fallos originales y cierres propios preservados. [Evidencia y pendientes](testing/plan-consume-runtime-status.md). Colección actual: 7.320 casos; QA completa/cobertura, Linux y revisión pendientes. Cierre solicitado: commits y push de la corrección validada, después parar; sin ampliar catálogo.


### QA final de consumo y fixture de barrera — 2026-10-12

Se conserva Windows164 rojo: N06 no pudo leer ready.json. RED real de sharing: dos fallos; fix acotado sin relajar identidad/deadline y 14 pruebas verdes. Suite actual de 7.322 casos: Windows 7.249 passed/73 skipped; Linux 7.255 passed/67 skipped, sin fallos/error. Cobertura parental de 33 fuentes: 91,1718%/91,2824%; colección, fuentes, dashboard directo y cleanup comprobados. [Recibos y límites](testing/plan-consume-final-qa-evidence.json). Gotcha propuesto por servicio canónico y asociado; no aprobado. La revisión posterior consta debajo; no se cierran macros ni catálogo.

## Revisión de dos lentes — intento 1: cierre de consumo (2026-10-12)

Subagentes independientes de contexto fresco: A+B+C+D, fallback genérico disponible. Scope exit0 sin avisos; delta de consumo/fixture y contratos conforme, sin Critical/Important/Minor nuevos ni reapertura de veredictos históricos. Export comprobado por A: exit0,88 archivos al día. [Cobertura, resultados y límites](testing/publication-review-status.md). Ledger-lint exit0 y CA08 real de todos los ledgers: 1 passed tras incorporar la fuente al checkout. Se conservan propuestas sin aprobar y configuración privada; este cierre no implica aceptación global.

### Curación de los cinco gotchas propuestos — 2026-10-13

Knowledge Curator (rol aplicado por el orquestador con el contrato de la rama) aprueba los cinco candidatos asociados en `curation-refs-v1` como GOTCHA `validated_case`: `custom-agents.GOT-020` (salto final del brief), `GOT-021` (guardias de productores de memoria), `GOT-022` (actividad de inicio frente a captura), `GOT-023` (publicación sintética en Windows) y `GOT-024` (lectura de barrera en Windows). `curator-gate.py --json`: 5 × `errores: []`, `avisos: []`; SHA originales iguales a la asociación. Cada aprobación usa representación corregida por stdin: se retiran frases de QA/revisión pendientes ya cumplidas el 2026-10-12 y se enlazan GOT-008/009/016/017. GOT-021 es de alto impacto (dos guardias); resolución humana: el usuario ordenó curar los cinco. Servicio `apply`: 5 × `status: complete`, operation-id en la asociación; `knowledge-index.py` 16 entradas sin errores; `pending/` vacío. Aparte, el YAML local de GOT-018 se entrecomilla (sin cambio de contenido): `lint_plugin` 0 errores. TDD n/a: memoria local no versionada y ledger.

### Mezcla de master y aceptación nativa Claude/Codex — 2026-10-13

Mezclado `origin/master` (`d553d0c`, PR #15/#16): 12 conflictos resueltos conservando ambas partes; la arista Kwipu de master pasa a **E55** en `docs/agents/CONTRACTS.md` porque esta rama ya usaba E25–E54. Suites afectadas: 1.114 passed/5 skipped; lint 0 errores, export 88 al día, evals 0 errores. Para no superar el tope de 256 KiB del lector de retoma, las secciones operativas del 10–11/10 se trasladaron sin cambios a `execution-history.md` (SHA en el puntero); `resume --initiative` vuelve a `ok`.

Aceptación nativa con modelos reales y proyectos sintéticos ([detalle](testing/native-claude-codex-2026-10-13-status.md)): `/work-resume` exacto y ambiguo pasan en Claude y Codex con JSON igual al compositor. Consumo del plan: Claude da `ok`/`version_changed` correctos pero envuelve y recorta el JSON (formato pendiente, igual que OpenCode); Codex falla con `invalid_input` porque `mkdir(mode=0o700)` en Python 3.13/Windows sustituye la ACL heredada y excluye el token del sandbox. La corrección afecta a cinco piezas y queda pendiente de decisión del usuario. Hooks Claude: SessionEnd cancelado en 2/5 sesiones, recuperado por `recover`; el aviso falso de «candidatas sin recuperar» se corrige en `journal.py` (RED: `test_recover_no_avisa_de_logs_ya_capturados_ni_en_la_segunda_pasada` falló con el aviso en la primera pasada; GREEN: 171 passed/10 skipped en `test_journal.py`). Panel servido para la revisión humana en Edge; su resultado queda pendiente del usuario. Ninguna macro cambia de estado.

### Comparación de skills retomada — S080–S082 (2026-10-13)

Con los pendientes operativos atendidos (salvo la decisión sobre ACL Windows/Codex y la revisión humana del panel), se retoma T-03 donde quedó. Fuente: el clon fijado `ef648e0` en el directorio de trabajo local de Codex; IDs S verificados por hash contra las fichas previas (S078/S079 = posiciones 78/79 del orden alfabético). [Ficha](comparisons/skills-django-security-testing-verification.md): S080 seguridad (13 adaptaciones; ajustes retirados como `SECURE_BROWSER_XSS_FILTER`, `CSRF_COOKIE_HTTPONLY` sin beneficio, CSP nativa en 6.0, políticas contradictorias en la vista), S081 pruebas (12; `--reuse-db`/`--nomigrations` ocultan cambios de esquema y migraciones, ejemplos no ejecutables) y S082 verificación (10; un segundo bucle duplicaría `qa`, varios pasos escriben). Destino: referencias de la especialidad opcional `django-practices` y una fila Django en `tdd/references/by-stack.md`. TDD n/a: prosa/evidencia. 82/293 evaluadas; quedan 211.

### Comparación de skills — S083–S085 (2026-10-13)

[Ficha](comparisons/skills-parallel-containers-docs.md): S083 (paneles tmux) no se adopta porque `subagentes`, `worktree` y las lentes paralelas ya cubren el caso con ledger y puertas; S084 (Docker) amplía `delivery-practices` con el arnés aislado de instaladores y secretos de Compose, y cierra la ficha pendiente del bloque de despliegue; S085 (Context7) entra como canal opcional de `research-first`, con versión desde el lockfile y redacción previa. Scripts citados por S083/S084 sin leer: declarado. TDD n/a: prosa/evidencia. 85/293 evaluadas; quedan 208.

### Comparación de skills — S086–S088 (2026-10-13)

[Ficha](comparisons/skills-dotnet-harness-e2e.md): S086 (C#/.NET) completa la especialidad opcional `dotnet-practices` iniciada con S064, con 10 adaptaciones (concurrencia de `DbContext`, firmas que no compilan, Problem Details); S087 (arneses por tarea) no crea pieza: aporta a `plugin-dev` un criterio de extracción compatible con ADR-011; S088 (Playwright) propone una guía de specs estables para `qa` y corrige `networkidle`, `data-testid` por defecto, `retries` que ocultan flakies y E2E contra staging, que el guardarraíl prohíbe. Contraste oficial pendiente en este bloque. TDD n/a. 88/293 evaluadas; quedan 205.

### ACL de Windows y revisión del panel — 2026-10-13

Decisión del usuario aplicada: directorios de estado sin `0o700` en Windows y con `0o700` en POSIX, en las cinco piezas afectadas. RED `tests/test_private_state_dirs.py` (6 failed) → GREEN (6 passed, 5 skipped de POSIX); consumo de decisiones de plan aceptado en Codex real con JSON exacto. Panel revisado por el usuario en Edge con respuesta «ok». [Detalle](testing/native-claude-codex-2026-10-13-status.md).
