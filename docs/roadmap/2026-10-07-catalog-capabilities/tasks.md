---
tasks: catalog-capabilities
estado: en-progreso
creado: 2026-10-07
actualizado: 2026-10-09
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
T-03/T-10 aplazadas en 79/293 skills evaluadas; quedan 214. S080–S082 tienen
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

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 1 | 7 | 14% |
| Fase 2 | 0 | 6 | 0% |
| Fase 3 | 0 | 3 | 0% |
| **TOTAL** | **1** | **16** | **6%** |

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
- **Verificación**: 79/293 skills evaluadas semánticamente (S001–S079), cuerpos completos, recursos locales y consumidores pertinentes comprobados. comparisons/skills-foundations.md conserva el primer bloque, con hashes/rangos de 18 fuentes y 13 archivos propios en reading-evidence.json. comparisons/skills-workflows.md añade S006–S012 y los seis recursos de S007; workflow-reading-evidence.json registra 20 fuentes y 18 propios. comparisons/skills-architecture-operations.md añade S013/S015–S020; architecture-reading-evidence.json registra 32 fuentes y 16 propios y conserva la lectura pendiente histórica de S014. comparisons/skills-angular.md completa S014; angular-reading-evidence.json registra 39 fuentes y 15 propios, los 35 recursos completos y 21 contrastes documentales oficiales. comparisons/skills-iteration-backend-benchmarks.md añade S021–S027; iteration-reading-evidence.json registra 35 fuentes y 26 propios, siete cuerpos completos sin recursos locales y 10 contrastes oficiales, con cuatro lecturas documentales rechazadas diferenciadas. comparisons/skills-brand-browser-runtime.md añade S028–S032; brand-ui-reading-evidence.json registra 36 fuentes y 22 propios, los nueve recursos completos y siete contrastes oficiales. comparisons/skills-operations-session-context.md añade S033–S035; operations-reading-evidence.json registra 21 fuentes y 18 propios, nueve recursos completos y cuatro contrastes oficiales, con tres rechazos HTTP directos separados de la lectura documental disponible. comparisons/skills-navigation-quality-data.md añade S036–S042; navigation-reading-evidence.json registra 21 fuentes y 28 propios, siete cuerpos completos sin recursos locales y 15 contrastes oficiales, con un enlace antiguo HTTP 404 y su sustituto vigente diferenciados. comparisons/skills-strategy-configuration-context.md añade S043–S052; business-reading-evidence.json registra 40 fuentes y 30 propios, diez cuerpos completos sin recursos locales y nueve contrastes oficiales; entrypoints leídos y verificación operativa pendiente diferenciados. comparisons/skills-session-learning-memory.md añade S053–S054; learning-reading-evidence.json registra 32 fuentes y 22 propios, dos cuerpos completos, 13 recursos completos y cuatro contrastes oficiales; tests y código del corpus leídos sin ejecución, dispatch/arquitectura/eficacia pendientes diferenciados. Helpers privados de cada bloque, Python 3.13, exit 0. Las fichas separan destinos propuestos, escenarios estáticos y validaciones no ejecutadas. comparisons/skills-contracts-costs-decisions.md añade S055–S060; contract-cost-reading-evidence.json registra 22 fuentes y 20 propios, seis cuerpos completos, tres recursos completos, siete contrastes oficiales y dos consultas CLI de versión/ayuda; estimación, facturación e integración operativa diferenciadas. comparisons/skills-cpp-dotnet-distribution-billing.md añade S061–S065; cpp-dotnet-reading-evidence.json registra 24 fuentes y 20 propios, cinco cuerpos completos sin recursos locales, 14 contrastes oficiales y un HTTP 404 con sustituto vigente diferenciado; compilación/cobertura/envíos/operaciones financieras no ejecutados. comparisons/skills-trade-flutter-observability.md añade S066–S068; trade-flutter-reading-evidence.json registra 25 fuentes y 27 propios, tres cuerpos completos sin recursos locales, diez reglas externas completas (30.350 bytes/1.080 líneas), 24 contrastes oficiales y tres respuestas sin documento válido diferenciadas; normativa por caso, compilación, hooks y dashboards operativos no ejecutados. comparisons/skills-data-pipelines-research.md añade S069–S072; data-research-reading-evidence.json registra 14 fuentes y 24 propios, cuatro cuerpos completos (46.443 bytes/1.450 líneas) sin recursos locales, 23 contrastes oficiales y un HTTP 404 con sustituto válido diferenciado; extracción, enriquecimiento, benchmark, migraciones y conexiones MCP no ejecutados. comparisons/skills-contract-security-delivery.md añade S073–S074; security-delivery-reading-evidence.json registra ocho fuentes y 19 propios, dos cuerpos completos (10.530 bytes/293 líneas), un recurso completo (7.826 bytes/220 líneas), 12 contrastes oficiales, un HTTP 404 y dos errores del lector web diferenciados; herramientas Solidity y dispatch de cierre no ejecutados. comparisons/skills-deployment-design-collaboration.md añade S075–S077; deploy-design-team-reading-evidence.json registra 20 fuentes y 19 propios, tres cuerpos completos (22.246 bytes/714 líneas), cero recursos locales, 13 contrastes oficiales y un error de lector web con lectura HTTP válida posterior diferenciados; despliegue, preview visual y sesiones de agentes no ejecutados. comparisons/skills-django-queues-architecture.md añade S078–S079; django-core-reading-evidence.json registra 11 fuentes y 14 propios, dos cuerpos completos (34.250 bytes/1.193 líneas), cero recursos locales y 14 contrastes oficiales; código, migraciones, workers, brokers y pagos no ejecutados. Integradas desde esta comparación: 0; quedan 214 skills y la revisión operativa de adaptadores/generadores en T-06. T-03 no está cerrada.
- **Notas**: TDD n/a: prosa/config de comparación, sin modificación de producción. Los consumidores leídos parcialmente no se cuentan como otras piezas evaluadas; las validaciones de activación son estáticas y no acreditan invocación nativa.
- **Comprobaciones del primer bloque**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; lint_plugin 0 errores/3 avisos históricos; scope-check 9 archivos propios en alcance/0 fuera, settings ajenos excluidos. check_skill_comparison_docs.py: 18 hashes de origen/13 propios coincidentes, enlaces locales válidos, JSON válido, diff limpio y 0 referencias públicas prohibidas en los 9 documentos de ese checkpoint. Estas puertas validan estructura/trazabilidad, no integración funcional.
- **Hallazgos del segundo bloque**: la metadata oficial del SDK de pagos 6.0.0 no declara bin, por lo que el arranque MCP propuesto necesita corrección y esquema real de tools; la rúbrica textual asume precisión máxima sin verificarla y su ejemplo HTTPX es incorrecto; los recordatorios echo de Stop/PostToolUse no prueban entrega de contexto al modelo; la ayuda de Claude 2.1.287 no documenta los flags del scheduler de ejemplo; la prueba de paridad solo cubre mock y puede pasar sin filas. Contraste documental y CLI limitado a versión/ayuda, sin instalar SDKs, usar carteras, prompts ni schedules. Todos los criterios útiles tienen destino propuesto; integración y pruebas de eficacia pendientes.
- **Comprobaciones del segundo bloque**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; scope-check sobre 299df4b: tres documentos propios en alcance/0 fuera, settings ajenos excluidos. check_workflow_comparison_docs.py: 20 hashes de origen/18 propios coincidentes, seis recursos completos (34.027 bytes/802 líneas), ayuda CLI comprobada como texto UTF-8/LF, JSON y enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas en los tres documentos. TDD n/a: solo documentación/evidencia, sin altas ni código de producción; las comprobaciones estructurales no prueban integración funcional.
- **Hallazgos del tercer bloque**: conservar especialidad Kotlin/KMP corrigiendo cancelación, tipos y mappers; ampliar contratos REST/conectores sobre backend/delivery existentes; consolidar ADR en la memoria canónica; redacción larga opcional con perfil único; auditoría operativa distingue configuración/autenticación/verificación y efectos autorizados. La metadata oficial del servidor MCP de memoria 2026.8.31 tiene bin, sin instalarlo ni probar sus tools. Documentación actual distingue índice de memoria acotado, detalles bajo demanda y scheduling por sesión frente a Cloud/Desktop; estas capacidades no se atribuyen a todos los runtimes. En ese checkpoint S014 tenía cuerpo leído y 35 recursos inventariados/0 leídos; no contó entre las 19 evaluadas. La lectura y su ficha se completaron en el bloque Angular posterior, sin excluirla por stack o tamaño.
- **Comprobaciones del tercer bloque**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; scope-check sobre 788660c: tres documentos propios en alcance/0 fuera, settings ajenos excluidos. check_architecture_comparison_docs.py: 32 hashes de origen/16 propios coincidentes, reutilizaciones verificadas, siete fichas y S014 pendiente diferenciadas, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas en los tres documentos. Fuente privada sin cambios de worktree. TDD n/a: prosa/evidencia; sin altas, código de producción o validación funcional nueva.
- **Hallazgos Angular**: conservar especialidad opcional con nueve referencias y métodos transversales únicos. Corregir API de RouterTestingHarness, resultado Signal entre fases, URL por segmentos, validación de fechas y contratos por versión de formularios/ARIA/Tailwind/MCP; el contraste oficial no acredita compilación ni dispatch. build_angular_read_evidence.py: 39 hashes de origen/15 propios coincidentes, 35 recursos completos (120.171 bytes/3.845 líneas), 21 observaciones oficiales, exit 0. Cero integración de producción y tokens/latencia null.
- **Comprobaciones Angular**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; scope-check sobre aec85f8: cuatro documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_angular_comparison_docs.py: 39 hashes de origen/15 propios coincidentes, reutilizaciones verificadas, 35 recursos completos con destino documentado, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas. El documento anterior enlaza la resolución de S014 y conserva su evidencia histórica. TDD n/a: prosa/evidencia, sin código de producción o pruebas funcionales Angular.
- **Hallazgos de ejecución, backend y medición**: consolidar patrones prolongados con recuperación y presupuestos verificables; no confundir allowedTools con restricciones ni disable-commits con dry-run. El helper de sesiones leído tiene historial sin límite de prompt, aislamiento por proyecto insuficiente y resultados de proceso no tipados. Ampliar backend corrigiendo errores RPC/auth async, validación JWT, caché, retries y recuperación de jobs. Separar baselines técnicos de rúbricas competitivas, compartir optimización con outcome-evals y ampliar planner sin otro ledger. Conservar inspección Blender opcional con espacios, geometría evaluada y unidades; collector citado ausente, fuentes oficiales v5.0.0 leídas como alternativa a cuatro HTTP 403. build_iteration_read_evidence.py: 35 hashes de origen/26 propios coincidentes, siete cuerpos (66.729 bytes/1.787 líneas), 10 contrastes oficiales, Python 3.13 exit 0; sin código de origen ejecutado, integración de producción ni mediciones nuevas.
- **Comprobaciones de ejecución, backend y medición**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; scope-check sobre 038942c: tres documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_iteration_comparison_docs.py: 35 hashes de origen/26 propios coincidentes, reutilizaciones verificadas, siete fichas, JSON/enlaces locales válidos, 10 contrastes y cuatro accesos rechazados separados, diff limpio y 0 referencias públicas prohibidas. Fuente privada sin cambios de worktree. TDD n/a: prosa/evidencia, sin altas ni modificación de código de producción; las comprobaciones no prueban ejecución nativa ni rendimiento.
- **Hallazgos de identidad, navegador y runtime**: conservar entrevista reanudable con ocho plantillas y checkpoint parcial por respuesta, resolviendo escritura y dueño de artefactos sin ampliar analyst silenciosamente. Perfil de voz compartido desde muestras, sin defaults de autor ni persistencia personal automática. Ampliar QA con baseline visual, cobertura manual y reporter compatible; el filtro de hosts nativo por patrones no acredita parsing/IP/DNS o redirects seguros. Bun es opcional y por versión: compatibilidad parcial Node, ejecución TS distinta de typecheck, lockfile y bunVersion; documentación oficial 1.4 describe Zig→Rust. Observación postdeploy requiere deploy/artefacto real, ventanas, estado de proceso y métricas parciales, no solo git push. build_brand_ui_read_evidence.py: 36 hashes de origen/22 propios, cinco cuerpos (21.038 bytes/536 líneas), nueve recursos (15.051 bytes/539 líneas), siete contrastes oficiales, Python 3.13 exit 0. Cero integración de producción, recursos de origen ejecutados o mediciones nuevas.
- **Comprobaciones de identidad, navegador y runtime**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; scope-check sobre 2cfb607: tres documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_brand_ui_comparison_docs.py: 36 hashes de origen/22 propios coincidentes, reutilizaciones verificadas, cinco fichas y nueve recursos con destino explícito, siete contrastes oficiales, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas. Fuente privada sin cambios de worktree. TDD n/a: prosa/evidencia, sin código de producción, entrevistas, perfiles, QA de navegador, Bun ni monitor ejecutados; validación estructural distinta de eficacia.
- **Hallazgos de operaciones y continuidad**: conservar transporte y revisión IOS como especialidades opcionales; corregir clasificación del seguro, separar SMS de rating federal, normalizar pesos/categorías y resolver límites de concentración contradictorios. IOS requiere plataforma/versiones, secuencia de ACL, gestión y verificación de comportamiento; los snippets no prueban ejecución. Consolidar retoma sobre ledger/journal, conservando objetivo, punto de trabajo, siguientes pasos, decisiones y bloqueos. Los nueve recursos de persistencia presentan estado global entre proyectos, escrituras parciales, lectura sin límite, rutas de retirada sin confinamiento y migración sin backup íntegro. La vista reanudable y la proyección opt-in siguen propuestas; el tiempo agregado y dispatch de hooks propios se resolverán en T-09/T-14. build_operations_read_evidence.py: 21 hashes de origen/18 propios, tres cuerpos (33.961 bytes/518 líneas), nueve recursos (49.233 bytes/1.310 líneas), cuatro contrastes oficiales y tres rechazos HTTP directos separados, Python 3.13 exit 0. Cero integración de producción, recursos externos ejecutados o mediciones nuevas.
- **Comprobaciones de operaciones y continuidad**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; scope-check sobre 068e1b9: tres documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_operations_comparison_docs.py: 21 hashes de origen/18 propios coincidentes, reutilizaciones verificadas, tres fichas y nueve recursos con destino explícito, cuatro contrastes oficiales y tres accesos HTTP directos rechazados diferenciados, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas. Fuente privada sin cambios de worktree. TDD n/a: prosa/evidencia, sin código de producción, dispositivos, guardados, migraciones, borrados ni hooks de origen ejecutados; validación documental distinta de integración y eficacia.
- **Hallazgos de navegación, interacciones, mantenibilidad y datos**: consolidar despacho externo sobre el ciclo propio, sin auto-merge previo a validación ni doble arranque. Ampliar auditoría UI con evento/store/efectos/estado final y regresiones reproducibles. Conservar ClickHouse opcional corrigiendo identidad de reemplazo, estados agregados, retención, funnel y recuperación de ingestión. Tours y onboarding comparten recon; el formato usa posiciones desde 1 y admite campos/enlaces ejecutables, por lo que necesita subconjunto propio y validación de ref/rutas. La generación de instrucciones persistentes requiere intención expresa y formato del runtime. Mantener separadas las heurísticas propias y la escala del proveedor externo; reporte vacío o score alto no prueban cobertura ni corrección. Convenciones generales cortas con ejemplos por stack, sin imponer mutación/copia, memoización, carpetas o dependencias universales. build_navigation_read_evidence.py: 21 hashes de origen/28 propios, siete cuerpos (61.516 bytes/2.008 líneas), cero recursos locales, 15 contrastes oficiales y un enlace HTTP 404 con sustituto vigente diferenciado, Python 3.13 exit 0. Cero integración de producción, tools externas ejecutadas o mediciones nuevas.
- **Comprobaciones de navegación, interacciones, mantenibilidad y datos**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; scope-check sobre 6c76eb9: tres documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_navigation_comparison_docs.py: 21 hashes de origen/28 propios coincidentes, reutilizaciones verificadas, siete fichas, 15 contrastes y un acceso rechazado con sustituto vigente, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas. Fuente privada sin cambios de worktree. TDD n/a: prosa/evidencia, sin código de producción, misiones, instalaciones, SQL, tours, cuentas o invocaciones MCP ejecutados; validación documental distinta de integración y eficacia.
- **Hallazgos de estrategia, configuración, contenido y contexto**: consolidar shortlist/rúbrica/informe competitivo con fuentes independientes, desconocidos y decisiones; no probar demanda o moat por cuadrante vacío. Conservar Compose opcional por target/versiones, corrigiendo respuestas fuera de orden, orden de modifiers, estabilidad y controlador retirado. Mantenimiento de configuración separa scan/apply, propiedad, backup/undo y autorización existente; edad o rename no acreditan retirada efectiva. Wizard nativo se consolida sobre instalador/setup/doctor, sin traducir scopes/perfiles entre runtimes ni anunciar éxito solo con enabled=true. Red social y contenido comparten perfil de voz y conservan borradores separados de efectos externos. Caché por contenido requiere versión/config, snapshot, ruta actual y escritura atómica; dataclasses congeladas no justifican prohibir asdict. Inventario/estimaciones/bytes persistidos no demuestran contexto activo; los schemas MCP pueden diferirse por contrato. Consolidar selección/recuperación de loops sobre el ciclo y ledger propios. build_business_read_evidence.py: 40 hashes de origen/30 propios, diez cuerpos (69.493 bytes/1.708 líneas), cero recursos locales y nueve contrastes oficiales, Python 3.13 exit 0. Bibliotecas de instalación/migración y ejecución siguen pendientes en T-06/T-09/T-12; cero integración de producción o mediciones nuevas.
- **Comprobaciones de estrategia, configuración, contenido y contexto**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; scope-check sobre e102fea: tres documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_business_comparison_docs.py: 40 hashes de origen/30 propios coincidentes, reutilizaciones verificadas, diez fichas, nueve contrastes oficiales, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas. Fuente privada sin cambios de worktree. TDD n/a: prosa/evidencia, sin código de producción, estudios comerciales, Compose, limpieza, configuración, cuentas, publicaciones, cachés o loops ejecutados; validación documental distinta de integración y eficacia.
- **Hallazgos de aprendizaje y memoria**: el evaluador de sesión solo emite avisos, no extrae ni escribe skills; el observador sí invoca un modelo y escribe reglas, pero archiva datos no leídos y puede perder otras entradas en import/merge/GC. Conservar candidatos atómicos con evidencia y captura opt-in, integrados con journal/outbox y curación propia. Score heurístico no concede aprobación; promover exige compatibilidad semántica y ámbito explícito. Identidad, privacidad, concurrencia, permisos, jobs Windows y tres runtimes necesitan contrato y pruebas propios. Precisar escritores/estados de los dos contratos de memoria existentes en T-07. build_learning_read_evidence.py: 32 hashes de origen/22 propios, dos cuerpos (18.685 bytes/509 líneas), 13 recursos (229.641 bytes/6.055 líneas), cuatro contrastes oficiales, Python 3.13 exit 0. Cero integración de producción o mediciones nuevas.
- **Comprobaciones de aprendizaje y memoria**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed; scope-check sobre bc9d0a2: tres documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_learning_comparison_docs.py: 32 hashes de origen/22 propios coincidentes, reutilizaciones verificadas, dos fichas y 13 recursos completos con destino explícito, cuatro contrastes oficiales, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas. Fuente privada sin cambios de worktree. TDD n/a: prosa/evidencia, sin código de producción, tests/hooks/modelos/imports/promociones/generadores/migraciones/borrados del corpus ejecutados; validación documental distinta de integración y eficacia.
- **Hallazgos de contratos, costes y decisiones**: ampliar api-contract con fronteras compartidas y payload serializado, conservando el alcance mínimo del linter. Routing/reserva/cache/retries LLM es una especialidad opcional de aplicaciones. Consolidar informes sobre usage-meter con modelo, proyecto, deltas, cobertura y procedencia; snapshots acumulados no son gasto diario ni factura. El productor aplica la tarifa del último modelo al total y el coste de statusline es estimado, no facturado. Conservar deliberación con desacuerdo y una crítica externa opcional compartida; el adaptador exige 0.146.0 frente a Codex instalado 0.160.1 y sus mocks no prueban aislamiento. Separar audiencia, participación y entrega con guards del transport propietario, sin motor competidor ni política universal. build_contract_cost_read_evidence.py: 22 hashes de origen/20 propios, seis cuerpos (42.223 bytes/1.123 líneas), tres recursos (12.909 bytes/374 líneas), siete contrastes oficiales y dos consultas CLI sin prompt/modelo, Python 3.13 exit 0. Cero integración de producción o mediciones nuevas.
- **Comprobaciones de contratos, costes y decisiones**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed (0,54 s); scope-check sobre f0869e1: tres documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_contract_cost_comparison_docs.py: 22 hashes de origen/20 propios coincidentes, reutilizaciones verificadas, seis fichas y tres recursos con destino explícito, siete contrastes documentales y dos consultas CLI sin prompt/modelo, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas. Fuente privada sin cambios de worktree. TDD n/a: prosa/evidencia, sin código de producción, scripts/tests del corpus, APIs, modelos, collectors o entregas externas ejecutados; validación documental distinta de integración y eficacia.
- **Hallazgos de C++, pruebas .NET, distribución y soporte de facturación**: conservar guías C++/.NET opcionales con versión/toolchain/runner, corrigiendo invariantes después de move, aliasing de mutex, discovery vacío, instrumentación de librerías/perfiles, sanitizers y fixtures async/BD. TDD y cobertura siguen compartidos; el gate propio no tiene parsers C++/.NET. Consolidar distribución en content-production con perfil único y resultado por canal, sin confundir borrador con envío. Conservar soporte de cliente sobre herramientas del proveedor, con identidad, alcance, estado de refund/cancelación/portal y efecto autorizado comprobados; no crear otro motor de facturación. build_cpp_dotnet_read_evidence.py: 24 hashes de origen/20 propios, cinco cuerpos (48.826 bytes/1.635 líneas), cero recursos locales, 14 contrastes oficiales y un HTTP 404 con sustituto vigente, Python 3.13 exit 0. Cero integración de producción o mediciones nuevas.
- **Hallazgos de comercio exterior, Flutter y dashboards operativos**: conservar especialidades opcionales con normativa/fecha, pubspec/target y schema/plataforma reales. Corregir reglas de clasificación/valoración, lista británica, ejemplo de minimis y clearing por score; respuestas HTTP 200 de mantenimiento/error no se cuentan como normativa leída. Corregir const/super, APIs Freezed/GoRouter/Riverpod, carreras de auth, refresh concurrente y hooks Dart; métodos y cobertura siguen compartidos. Conservar preguntas operativas y estados de datos sin confundir catálogo/roadmap con observabilidad ni presencia con salud. build_trade_flutter_read_evidence.py: 25 hashes de origen/27 propios, tres cuerpos (47.421 bytes/929 líneas), diez reglas externas completas, 24 contrastes oficiales y tres rechazos documentales, Python 3.13 exit 0. Cero integración de producción o mediciones nuevas.
- **Hallazgos de datos, migraciones e investigación**: conservar colectar→enriquecer→almacenar con contratos de fuentes/destino, sin prometer archivos ausentes, autoaprendizaje o coste gratuito universal; distinguir AI apagada/fallida, identidad de resultados, error frente a duplicado y privacidad del feedback. Consolidar rendimiento en backend con outcome-evals, añadiendo reconciliación de dominio, snapshot/high-watermark y tail separado; contadores/timestamps no bastan. Ampliar migraciones con locks, transacciones reales, backfill reanudable, alias Django, estado dirty y recuperación, respetando versiones ORM. Investigación conserva claims/citas/fechas y presupuestos, herramientas disponibles y contenido no confiable, sin dos MCP ni delegación obligatorios. build_data_research_read_evidence.py: 14 hashes de origen/24 propios, cuatro cuerpos completos, 23 contrastes oficiales y un rechazo HTTP diferenciado, Python 3.13 exit 0. Cero integración de producción y tokens/latencia null.
- **Verificación del bloque de datos, pipelines e investigación**: 50 tests de test_roadmap_index pasaron (0,36 s); ledger-lint cero incoherencias/cero avisos; scope-check contra 0f23fb8, tres archivos propios en alcance/cero fuera/cero avisos, settings ajenos excluidos. Checker privado: 14 hashes de origen/24 propios, rangos/recursos/JSON/enlaces/nombres públicos válidos y fuente fijada limpia, exit 0. Son gates documentales, no validación funcional de las propuestas. TDD n/a: documentación e investigación.
- **Hallazgos de seguridad de contratos y cierre**: conservar Solidity opcional con contabilidad, oráculos, límites y toolchain por versión; ejemplos de guard OpenZeppelin 5.x y math V3 requieren compiladores incompatibles, y la división TWAP omite floor negativo. Consolidar readiness sobre delivery/qa/ciclo, retirando bloqueo universal por mtime y memoria paralela; regex en historial no acredita cambios ni aprendizaje. Distinguir Stop de SessionEnd y transporte informativo de bloqueo. Claude no eleva presupuesto de teardown por timeout de plugin; resolver margen real/captura durable en T-09/T-14. build_security_delivery_read_evidence.py: ocho hashes de origen/19 propios, 12 contrastes oficiales, un recurso completo, exit 0; fuente no ejecutada y cero integración de producción.
- **Sincronización de rama**: push autorizado de feat/catalog-capabilities hasta 726cb48868034f2c342a5893205c14c1fb77f583; git ls-remote confirmó coincidencia con HEAD. Es publicación del progreso validado, sin cerrar T-16 ni anunciar la integración terminada. El usuario pidió seguir subiendo bloques validados.
- **Verificación de seguridad de contratos y cierre**: test_roadmap_index, 50 passed (0,79 s); ledger-lint cero incoherencias/cero avisos; scope-check contra 726cb48, tres archivos propios en alcance/cero fuera/cero avisos, settings ajenos excluidos. Checker privado: ocho hashes de origen/19 propios, rangos, recurso completo, JSON, enlaces y nombres públicos válidos; 12 contrastes oficiales y tres lecturas rechazadas diferenciadas; fuente fijada limpia, exit 0. TDD n/a: solo prosa/evidencia. Estas puertas prueban estructura/trazabilidad, no compilación Solidity, dispatch de hooks o integración funcional.
- **Hallazgos de despliegue, sistema visual y perspectivas**: ampliar delivery-practices con estrategia de rollout/recuperación y CI/artefactos, conservando límites de permisos, migraciones y proveedores; el YAML de deploy solo hace echo y no acredita una entrega. Ampliar frontend-quality con sistema visual derivado, procedencia de tokens y preview verificable, sin usar puntuación editorial como conformidad. Consolidar feedback de producto/arquitectura/dev/QA con la propuesta opcional decision-review; coincidencia no prueba severidad, ni prompt analysis-only acredita permisos efectivos. S084/S107/S154/S275 quedan para comparación completa antes del diseño final. Builder privado: 20 hashes de origen/19 propios, 13 documentos oficiales, exit 0; ninguna integración de producción. TDD n/a: documentación e investigación.
- **Verificación de despliegue, sistema visual y perspectivas**: 50 tests de test_roadmap_index pasaron (0,35 s); ledger-lint cero incoherencias/cero avisos; scope-check contra 08ec913, tres archivos propios en alcance/cero fuera/cero avisos, settings ajenos excluidos. Checker privado: 20 hashes de origen/19 propios, rangos, recursos, JSON, enlaces y nombres públicos válidos; 13 contrastes oficiales y un error de lector con sustituto válido diferenciados; fuente fijada limpia, exit 0. Estas puertas prueban trazabilidad/estructura documental, no despliegues, previews, dispatch de agentes ni integración funcional.
- **Hallazgos de Django, colas y APIs**: conservar especialidad opcional django-practices con tres referencias propuestas (arquitectura/ORM, API/cache, tareas distribuidas), sin otros métodos de TDD/revisión/QA. Corregir despacho antes de commit, acknowledgements, política de retries, pago remoto y estado durable; modo eager no acredita worker real y Celery no declara soporte Windows nativo. Diferenciar auth, permisos de objeto, ámbito de listas y creación; resolver paginación desactivada, modelos incompletos, bulk sin save/signals, usuario custom, cache y concurrencia. S080–S082 y A017/A018 quedan para fichas completas; no copiar migrate --fake como reparación verificada. Builder: 11 hashes de origen/14 propios/14 documentos oficiales, exit 0; cero integración de producción. TDD n/a: documentación e investigación.
- **Verificación de Django, colas y APIs**: test_roadmap_index, 50 passed (0,13 s); ledger-lint cero incoherencias/cero avisos; scope-check contra 3d183b9, tres archivos propios en alcance/cero fuera/cero avisos, settings ajenos excluidos. Checker privado: 11 hashes de origen/14 propios, rangos, recursos, JSON, enlaces y nombres públicos válidos; 14 contrastes oficiales, cero lecturas rechazadas y fuente fijada limpia, exit 0. Son gates documentales, sin ejecución de Django, worker, broker, pago ni integración funcional.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

- **Comprobaciones de C++, pruebas .NET, distribución y soporte de facturación**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed (0,32 s); scope-check sobre 5856039: tres documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_cpp_dotnet_comparison_docs.py: 24 hashes de origen/20 propios coincidentes, reutilizaciones verificadas, cinco fichas sin recursos locales, 14 contrastes oficiales y un HTTP 404 con sustituto vigente separados, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas. TDD n/a: prosa/evidencia, sin código de producción, compiladores, tests del corpus, APIs, publicaciones u operaciones financieras ejecutados; validación documental distinta de integración y eficacia.

- **Comprobaciones de comercio exterior, Flutter y dashboards operativos**: ledger-lint 0 incoherencias/0 avisos; test_roadmap_index 50 passed (0,53 s); scope-check sobre ba71c6a: tres documentos propios en alcance/0 fuera/0 avisos, settings ajenos excluidos. check_trade_flutter_comparison_docs.py: 25 hashes de origen/27 propios coincidentes, reutilizaciones verificadas, tres fichas sin recursos locales y diez reglas externas completas, 24 contrastes oficiales y tres respuestas sin documento válido diferenciadas, JSON/enlaces locales válidos, diff limpio y 0 referencias públicas prohibidas. Fuente privada sin cambios de worktree. TDD n/a: prosa/evidencia, sin código de producción, scripts/tests del corpus, compiladores, screening, trámites, dashboards, MCP ni servicios externos ejecutados; validación documental distinta de integración y eficacia. El ajuste de carpetas de personas está trazado en T-08 como requisito pendiente, sin cambiar todavía lectores ni briefs.

### T-04 — Comparación de los 68 agentes

- **Estado**: borrador
- **Descripción**: Evaluar responsabilidades, procedimientos, permisos y resultados frente a roles propios; distinguir especialidad útil de duplicación de fase.
- **Dependencias**: T-01/T-02.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Pendiente: fichas por ID con contratos y destinos; ninguna equivalencia basada solo en nombres.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-05 — Comparación de los 94 comandos

- **Estado**: en-progreso
- **Descripción**: Revisar intención, artefactos y despacho de comandos frente a los ciclos propios; identificar operaciones útiles y callers que cambiarían.
- **Dependencias**: T-01/T-02.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Pendiente: fichas por ID, disparadores y escenarios positivos/negativos, con dueño por artefacto.
- **Comparación operativa parcial (2026-10-08)**: 18/94 cuerpos de comandos leídos, recursos concretos y límites en comparisons/command-reading-evidence.json; quedan 76 cuerpos y closures pendientes. comparisons/operational-panel-commands.md propone consolidar contexto, diagnóstico, coste y criterios de workflow sobre dueños existentes. Cero fichas globales cerradas, cero integraciones y cero routing nativo probado por esta comparación; no se añaden skills.
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
- **Archivos**: `hooks/**`, `interop/**`, `agent-kits/shared/**`, `scripts/**`, `install/**`, `tests/**`, `agents/**`, `docs/**`
- **Verificación**: Dispatcher, IDs exactos, transporte de decisiones y correcciones de rama/preflight verificados en los bloques 3–10; `2a010a2` publicado. QA Windows/Linux y ocho ejecuciones nativas en hook-reliability-qa-evidence.json y hook-native-acceptance-evidence.json. Bloque 11 contrasta publicación canónica OpenCode con siete casos y recuperación de una copia del checkpoint; hook-canonical-capture-evidence.json conserva hashes y límites. Pendientes: bypass de verificación Git, demás reglas/capacidades y aceptación ampliada de carga/TUI. T-09 sigue abierta.
- **RED del bloque de checkpoint (2026-10-08)**: `test_journal.py -k 'capture_respeta_journal_en_forma_objeto or rotar_fallo_conserva_checkpoint or rotar_lee_solo_cola'`: 4 failed/1 passed, 150 deselected. `{activo: false}` creó un log; los fallos simulados de fsync/replace no conservaron el original; la rotación leyó el archivo completo (`read(-1)`). Evidencia obtenida antes de modificar producción.
- **RED de compatibilidad Windows (2026-10-08)**: `test_journal.py -x -q`: 1 failed/4 passed; `test_write_sin_rastro_del_plugin_no_escribe_nada` recibió `docs\knowledge\journal\2026-10-08-sesion.md` en vez de la ruta relativa con `/`. Se amplía el bloque para normalizar la salida CLI, sin cambiar rutas internas.
- **RED de reclamación exclusiva (2026-10-08)**: probe propio con trazas de `os.replace` reprodujo dos movimientos exitosos del mismo origen en Windows (iteración 2); el test de 100 reclamaciones concurrentes falló en la iteración 1 con dos ganadores. El test de cerrojo no disponible también falló: entregó el item en vez de mantenerlo pendiente. Se serializa la transacción de reclamación con cerrojo de SO no bloqueante; pendientes intactos si no se obtiene.
- **RED nativo de instalación/cierre (2026-10-08)**: Instalador real Codex deja marketplace/enabled pero plugin list lo muestra sin instalar; tras add hay contexto/captura, con efecto global comprobado incluso desde false previo. Claude fijado captura UTF-8/contexto pero no deja envelope con presupuesto predeterminado; misma definición con override propio 5.000 ms sí lo deja. Control SessionEnd propio 2.200 ms/timeout 5 cancela por defecto y completa con override. recover sobre checkpoint de sesión nativa terminada conserva el turno como recuperado_sin_cierre, exit 0. Producción intacta; no se aplica workaround chmod con causa no aislada. Evidencia y límites en contracts.md y JSONs nativos.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-10 — Skills opcionales y consolidación de contenido

- **Estado**: borrador
- **Descripción**: Integrar contenido útil de las fichas con referencias y recursos propios; dominios existentes en el corpus, sin paquetes inventados ni carga indiscriminada.
- **Dependencias**: T-08/T-09.
- **Archivos**: `skills/**`, `agent-kits/shared/**`, `evals/**`, `tests/**`, `docs/**`
- **Verificación**: Pendiente: escenarios reales por alta/consolidación, recursos vigentes, tamaño y degradación; mapas sin duplicación ni pérdida.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-11 — Agentes, comandos y handoffs coherentes

- **Estado**: borrador
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

- **Estado**: borrador
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
- **Archivos**: `tests/**`, `evals/**`, `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Cada bloque conserva su QA por snapshot al final del ledger. Bloque 10: Windows Node 166/Python 287 y Linux Node 154 + 12 skips/Python 287, cuatro qa-gates GREEN y cobertura de diff con método explícito. Bloque 11: 16 controles del observador estricto, siete capturas canónicas nativas y recuperación sobre copia aislada. Las ejecuciones nativas y los casos por plataforma no se suman como unit tests. Pendientes: nuevos escenarios/capacidades de T-09/T-11/T-13, UI Edge y aceptación global.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-15 — Limpieza, distribución y documentación

- **Estado**: en-progreso
- **Descripción**: Retirar recursos y callers sustituidos, refrescar dependencias/manifiestos/exports y docs ES/EN; comprobar referencias y nombres públicos.
- **Dependencias**: Verificación del bloque pertinente de T-14 para docs/exports de cada entrega; aceptación global tras completar T-14.
- **Archivos**: `skills/**`, `agents/**`, `commands/**`, `agent-kits/**`, `scripts/**`, `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `.claude-plugin/**`, `docs/**`, `README.md`, `README.es.md`, `CLAUDE.md`, `tests/**`, `evals/**`
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

## Evidencia inicial

TDD n/a: planificación y documentación. Reconciliación de hashes mediante
helper privado y lectura de corpus fijado; ningún script externo ejecutado.
455 hashes verificados: 293 skills/68 agentes/94 comandos. Cero piezas
evaluadas semánticamente en esta fase; decisiones anteriores no se promueven
a revisión completa. Recursos auxiliares reconciliados en corpus.json; sus
dependencias y utilidad todavía requieren lectura semántica.

Versiones obtenidas con --version: Codex CLI 0.160.1, Claude Code 2.1.287,
OpenCode 2.0.12. Fuentes oficiales abiertas en contracts.md. La prueba aislada
reproduce el rechazo del export V1 actual en OpenCode V2; el control positivo
carga y registra hooks, y se observa normalización de configuración V1/V2.
No acredita despacho ni bloqueo. Guardias y formatos se resolverán en T-02/T-09.

Comprobaciones de apertura ejecutadas: scope-check contra 6187b12, nueve
ficheros en alcance/cero fuera/cero avisos, settings ajenos excluidos;
ledger-lint cero incoherencias/cero avisos; linter cero errores/tres avisos
históricos; test_roadmap_index 50 passed; scan de nombres/contenido público sin
hallazgos y diff --check limpio. Son gates del plan, no de la implementación.

Comprobaciones del cierre de T-01 ejecutadas: ledger-lint cero incoherencias y
cero avisos; test_roadmap_index 50 passed (0,09 s); linter cero errores y tres
avisos históricos; scope-check 13 ficheros en alcance y cero fuera/avisos,
settings ajenos excluidos; scan público sin hallazgos. TDD n/a: documentación
e inventario de investigación; ningún cambio de producción en este hito.

Al añadir la evidencia nativa de OpenCode, scope-check conserva 13 ficheros
propios en alcance/cero fuera/cero avisos (14 cambiados contando settings
excluidos). El scan público sigue sin hallazgos. Los digests y agregados del
manifiesto y el enlace al método se contrastaron con el mapa privado: exit 0.

## Revisión de dos lentes — intento 1: Fase 2 (T-08, T-09, T-14, T-15) — bloque de checkpoint

Lentes A+B mediante subagentes de contexto fresco; no se dispone de la herramienta
Agent del plugin en esta sesión. Selector contra 47e9ddc: C=false/D=false, sin
avisos. Alcance: diez archivos propios/cero fuera; settings ajenos excluidos.
No se ha revisado ni cerrado el resto de las tareas multi-runtime.

| Criterio | Veredicto inicial | Evidencia |
|---|---|---|
| T-08: diseño previo, alternativas, bloque acotado | ✓ | design.md, criterios del primer bloque y pendientes explícitos |
| T-09: opt-out booleano/objeto, privacidad, rotación acotada y atómica | ✓ | test_journal.py, casos capture/rotar y fallos fsync/replace |
| T-09: CLI portable y reclamación exclusiva | ✓ | aserciones de rutas y cien contenciones en test_outbox.py |
| Constitución: cerrojo sin seguir enlaces ajenos | ✗ | A-1, outbox.py reclamar abría .claim.lock sin validar |
| Corrección: errores de transacción visibles | ✗ | B-1, excepción de processing/ dañado absorbida como None |
| T-14: evidencia de pruebas y TDD | ✓ parcial | rojos registrados; Windows 198 passed/11 skipped y Linux 209 passed antes de estos fixes; cobertura final pendiente |
| T-15: docs ES/EN, sin marca nueva, alcance declarado | ✓ | observability y changelogs bilingües; scope-check |
| No cerrar tareas globales sin aceptación completa | ✓ | T-08/T-09/T-14/T-15 siguen en-progreso |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-1 | Important | .claim.lock seguía symlink externo | T-09 | Corregido: lstat previo, O_NOFOLLOW donde existe y contraste descriptor/ruta antes del cerrojo; pendiente revalidación independiente | RED Linux: test_reclamar_rechaza_cerrojo_enlace_sin_abrirlo falla al abrir enlace; test_reclamar_rechaza_cerrojo_sustituido_antes_de_abrir falla Windows/Linux. GREEN dirigido: Linux 5 passed; Windows 4 passed/1 skipped (symlinks sin privilegio), 2026-10-08 |
| B-1 | Important | except absorbía errores de _reclamar | T-09 | Corregido: captura solo errores de adquisición; transacción fuera del except y liberación en finally; pendiente revalidación independiente | RED test_reclamar_error_de_transaccion_no_parece_cola_vacia: DID NOT RAISE OSError en Windows/Linux; GREEN dirigido anterior incluye fallo observable y posterior recuperación, 2026-10-08 |

Rojo de revisión antes de modificar producción: Windows 2 failed/1 skipped;
Linux 3 failed, todos los casos dirigidos a los gaps. No hay deuda aceptada ni
gaps rebatidos. Segundo intento y QA final del bloque pendientes. No se promueve
conocimiento de otras tareas en progreso.

Jira: planner local de evento gaps/actor reviewer/intento 1 devuelve ops=[];
enabled no es true. No se publica nada externo.

## Revisión de dos lentes — intento 2: Fase 2 (T-08, T-09, T-14, T-15) — checkpoint sin gaps pendientes

A+B de contexto fresco revalidan solo las correcciones con la tabla completa del
intento anterior. C/D siguen false según selector, sin avisos. No se reabre lo
aprobado sin evidencia nueva. A-1/B-1 corregidos y verificados por ambas lentes;
cero Critical, Important o Minor pendientes en este bloque.

| Criterio corregido | Veredicto | Evidencia independiente |
|---|---|---|
| A-1: enlace rechazado e identidad contrastada antes de bloquear | ✓ | outbox.py:592–602; test_outbox.py:130,149. Lente A ejecuta Windows 4 passed/1 skipped y Linux 5 passed; el enlace sin privilegios de Windows se verifica en Linux |
| B-1: errores de la transacción llegan al llamador y el cerrojo se libera | ✓ | outbox.py:611–620; test_outbox.py:119 verifica excepción, pendiente y recuperación. Lente B ejecuta Windows 4 passed/1 skipped |
| Docs ES/EN y ámbito del bloque | ✓ | observability ES/EN explican enlaces, identidad y diagnóstico; tareas globales siguen en-progreso |

QA final después de esas correcciones, 2026-10-08:

- Python nativo Windows 3.13: journal/outbox completos, 200 passed/12 skipped,
  141,05 s. Los skips corresponden a POSIX/permisos/enlaces no disponibles allí;
  no acreditan ACL de NTFS. Python nativo Linux 3.14.4 en WSL Ubuntu: 212 passed,
  135,23 s, sin skips; mismos pytest 9.1.1 y coverage 7.16.2, dependencias de
  prueba aisladas en /tmp, sin instalación global.
- coverage.py oficial mide ambos módulos; unión de líneas ejecutadas en ambos
  sistemas intersectada con líneas añadidas ejecutables contra 47e9ddc:
  journal 16/19, outbox 34/34, total 50/53 = 94,34% (umbral ≥90%). Las dos
  líneas CLI ejecutadas en subprocess no se instrumentan y cuentan como ausentes;
  no se extrapola cobertura a runtime nativo ni al resto del proyecto.
- qa-gate VERDE: 412 passed, 0 failed/flaky/interrupted, 12 skipped. Entrada
  normalizada desde los casos JUnit reales de esas dos ejecuciones pytest;
  no se presenta como una ejecución de Playwright.
- node --test tests/hook-runtime.test.mjs: 12 passed/0 failed, 33,05 s. Prueba
  launchers/fixtures propios, incluida captura UTF-8 y cierre dentro de 3 s;
  el adaptador OpenCode V1 invocado por fixture no acredita carga nativa V2,
  ni este tiempo acredita el presupuesto de cierre por defecto de Claude.
- tests/test_console_encoding.py + tests/test_roadmap_index.py: 512 passed
  antes del registro final de revisión, 235,26 s.
- Linter: cero errores/tres avisos históricos; export-interop --check: 54
  archivos al día. Scope-check: diez propios/cero fuera/cero avisos; settings
  ajenos excluidos. No se ejecutan scripts del corpus ni se activan backends.

Evidencias brutas locales ignoradas: scratchpad/.venv/memory-{win,linux}.xml,
coverage-memory-{win,linux}.json, memory-diff-coverage.json y memory-qa-gate.json.
Son respaldos de este bloque, no distribución del plugin. La aceptación global
de T-08/T-09/T-14/T-15 permanece abierta por los criterios restantes.

Comprobación del registro final: test_roadmap_index 50 passed (0,97 s),
ledger-lint cero incoherencias/cero avisos, diff --check limpio y scan de
contenido/nombres de los diez archivos públicos sin marca de origen.
Jira evento revision/actor reviewer/intento 2: ops=[], disabled; sin envíos.
Este checkpoint se publica en feat/catalog-capabilities; el SHA final se
contrasta con origin después del push, sin merge ni release.

## Bloque de transporte OpenCode V2 — T-02, T-06, T-08, T-09, T-14, T-15

Implementación acotada al adaptador informativo y su distribución; las guardias
nativas y el resto del catálogo permanecen en-progreso. Diseño previo en design.md.
La comparación dirigida del adaptador del corpus descubre el mismo contrato V1
incompatible; no se ejecuta ni incorpora su código. Commands/dashboard siguen
pendientes de comparación detallada; las skills continúan aplazadas.

Evidencia RED anterior a producción, 2026-10-08:

- tests/opencode-plugin.test.mjs: seis fallos por ausencia de default id/setup.
- Instalador: dos fallos por registro sin plugins nativo y dos por ausencia de
  retirarArtefacto; export: un fallo por ausencia del paquete V2 generado.
- Doctor: tres fallos (estado info/aviso frente a registro V2 esperado) al cambiar
  únicamente las fixtures antes del lector.
- Diagnóstico stderr: falla la expectativa de aviso; el adaptador absorbía el error.
- Cierre nativo: el modelo local termina correctamente, pero no aparece envelope.
  Fixture session.execution.succeeded falla dos veces con «Adapter effect was not
  observed», con ubicación explícita y sin ella, antes de modificar producción.
  El stream local observado entrega eventos terminales sin location. La corrección
  usa session.get para verificar siempre la ubicación y mantiene rechazo de eventos
  explícitamente ajenos; no reutiliza el directorio de instancia a ciegas.

Verificación parcial antes de revisión: Python Windows 241 passed/2 skipped;
launchers/adaptador 20 passed; instalador dirigido 9 passed y casos de retirada
3 passed. La primera ejecución Node completa tuvo tres fallos por arrancar antes
de regenerar el nuevo paquete; los tres pasan después de generar. No se oculta
ese fallo ni se presenta como una suite completa verde. Linter: cero errores/tres
avisos históricos. Export-interop: 55 archivos generados. Alcance contra 057e26e:
cero fuera/cero avisos; settings ajenos excluidos y conservados.

Prueba nativa en OpenCode 2.0.12: paquete instalado active, prompt UTF-8 y exclusión
private observados, contexto y herramienta write despachados por el runtime,
cierre terminal con envelope. Dos respuestas SSE del modelo simulado propio en
loopback; cero solicitudes a proveedores externos, sin credenciales heredadas.
Replay nativo en una nueva sesión, cobertura final y revisión independiente en curso.

## Revisión de dos lentes — intento 1: transporte OpenCode V2

Scope-check contra 057e26e: cero fuera/cero avisos; configuración ajena excluida.
Selector: C=false, D=true por callbacks esperados en el camino del modelo.
A/B/D independientes; fallback de herramienta genérica porque Agent(reviewer)
no está disponible. No se ejecutó código del corpus ni se enviaron mensajes externos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-1 | Minor | Docstring del índice describe transporte V1 | T-15 | Corregido; pendiente revalidación | Docstring V2 actualizado; prosa/config, TDD n/a |
| B-1 | Important | Cleanup resuelve antes de close con stdout excesivo/timeout | T-09 | Corregido; pendiente revalidación | Se espera close y terminación del árbol propio; test verde Windows |
| B-2 | Important | Patches indentados válidos pierden post-hooks | T-09 | Corregido; pendiente revalidación | Targets del resultado nativo; fallback trim; patch indentado y write normalizado verdes |
| D-1 | Important | Composición completa en cada continuación | T-09 | Corregido; pendiente revalidación | Caché efímera acotada; 50 iniciativas: 7890/5915/64/38/32/31 ms, medianas calientes 7506 → 38 ms |

RED adicional antes de corregir: native applied falla para patch indentado;
unchanged context falla por devolver context 2 en la segunda llamada. La garantía
de cleanup ya tiene rojo reproducido. Diseño ampliado antes de producción;
correcciones y revalidación independientes pendientes, sin deuda aceptada.

GREEN dirigido tras las correcciones: adaptador Windows 11 passed/0 failed.
Prueba nativa 2.0.12 posterior: active, dos loops y cuatro requests al modelo
propio en loopback, replay en segunda sesión observado, cero proveedores externos,
servidor terminado exit 0. La prueba propia de caché se amplía con TTL, cambios
concurrentes y colas personalizadas antes de QA final. Segunda revisión y cobertura
siguen pendientes; ningún criterio global se marca completado.

## Revisión de dos lentes — intento 2: transporte OpenCode V2

A/B/D frescas revalidan las correcciones con la tabla completa del intento 1.
A: cero gaps. B: B-1/B-2 corregidos, un Important nuevo. D: D-1 corregido,
sin hallazgos nuevos; fixture independiente 50 iniciativas × 8 archivos produce
5986/5978/151/175/158/193 ms, mediana caliente 166,5 ms (~45× menos que 7506 ms).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-1 | Minor | Docstring V1 | T-15 | Verificado por A | export-interop --check 55 al día |
| B-1 | Important | Cleanup anterior a close | T-09 | Verificado por A/B | Windows cinco dirigidos verdes; Linux cinco dirigidos verdes |
| B-2 | Important | Patches indentados pierden avisos | T-09 | Verificado por A/B | Patch indentado y input write distinto de target nativo verdes |
| D-1 | Important | Contexto completo repetido | T-09 | Verificado por A/D | Caché/invalidez/TTL/concurrencia probados y benchmark independiente |
| B-3 | Important | Move desde docs pierde origen eliminado | T-09 | Pendiente | B contrasta native output=false frente a fallback=true; RED native move out falla antes de modificar producción |

Se conserva el destino normalizado y se añade el origen absoluto del diff
nativo FileDiff.Info.patch: el runtime lo compone con la ruta original incluso
cuando files[].file y applied[].target describen el destino. No se usa el cuerpo
de la herramienta como una decisión nueva ni se publica documentación. Diseño
ampliado antes de esta corrección; intento 3 será solo sobre B-3 y criterios afectados.

B-3 corregido con la ruta del origen desde el diff nativo; GREEN native move out.
El contraste de generación de caché se hace después de esperar su firma final,
manteniendo la garantía frente a invalidaciones durante esa espera; GREEN de
mutación concurrente. Suite Node completa previa a estas últimas líneas: 139
passed/0 failed; QA de adaptador final y nueva prueba nativa en curso. No se
reanuda el catálogo de skills ni se consideran comparados commands/dashboard.

## Revisión de dos lentes — intento 3: transporte OpenCode V2

A/B/D de contexto fresco, tabla anterior completa y solo B-3/criterios afectados.
C sigue false según selector; D conserva la revisión de las últimas líneas.
Cero Critical/Important/Minor pendientes en este bloque, sin deuda aceptada.

| Criterio corregido | Veredicto | Evidencia independiente |
|---|---|---|
| B-3: move conserva origen y destino | ✓ | A Windows 2 passed; B Linux 2 passed; fuente oficial patchFile/fileDiff compone header con absolute original; test dedicado verde |
| Invalidación durante la firma final | ✓ | A/B verifican contraste de generation posterior al await; mutación concurrente verde |
| Coste de extracción y caché | ✓ | D: tres dirigidos verdes; extracción en 400 diffs/26,3 MB mediana 1,010 ms; no se añade recorrido a la firma |
| Docs y fuente única | ✓ | A: ES/EN/diseño coherentes; export-interop --check, 55 al día |

QA final del bloque, 2026-10-08:

- Python Windows 3.13: doctor/export/panel, 241 passed/2 skipped, 166,59 s;
  skips por bit ejecutable y symlinks no disponibles en Windows. Node 23.8:
  suite completa de adaptador/launcher/instalador, 139 passed/0 failed antes
  de las últimas líneas del move y guardado de caché; adaptador/launcher
  completos después de ellas, 25 passed/0 failed/0 skipped. Los módulos del
  instalador no cambiaron entre esas dos ejecuciones.
- Python encoding/índice de roadmap: 512 passed/0 failed, 128,56 s, antes del
  registro final. qa-gate VERDE: 917 ejecuciones passed, cero failed/flaky/
  interrupted, dos skipped; normalización de casos JUnit reales, incluidas
  las repeticiones dirigidas del adaptador, no una ejecución de Playwright.
- Cobertura del diff contra 057e26e: 299/306 = 97,71% (umbral ≥90%). c8 10.1.3
  mide líneas V8 de JS; coverage.py, líneas ejecutables Python. Cinco módulos
  de fixture son copias byte a byte del adaptador: se unen sus rangos V8
  manteniendo offsets y contrastando el SHA, sin atribuir cobertura al probe
  nativo Bun. Export index.js idéntico a la fuente, comprobado, no contado
  por duplicado. Líneas ausentes se conservan, incluida terminación POSIX
  no instrumentada en Windows.
- Pruebas dirigidas propias Linux/WSL con Node 23.8.0 aislado, checksum de
  SHASUMS256 oficial: cuatro passed (cleanup de árbol, stdout excesivo,
  caché/concurrencia), más dos finales independientes de B para move y
  concurrencia. No instalación global ni ejecución del corpus.
- Native OpenCode 2.0.12 después de la última corrección: active, dos loops,
  cuatro requests al modelo propio en loopback y dos prompts retenidos;
  captura UTF-8/private, contexto, write, cierre y replay de segunda sesión
  observados. Cero proveedores externos, sin credenciales heredadas, servidor
  terminado exit 0. runtime-probes.json separa la evidencia nueva del baseline.
- Migración CLI real en proyecto temporal propio: copia V1 conocida retirada,
  entrada antigua del manifiesto eliminada, contenido/config/permissions ajenos
  preservados, paquete V2 idéntico, segunda instalación idempotente. La primera
  fixture usó «./.opencode» para instructions, distinto del valor histórico
  «.opencode»; su conservación fue correcta. Fixture corregida al registro real.
- Linter: cero errores/tres avisos históricos. Skills permanecen aplazadas.
  Guardias/presupuestos nativos Claude/Codex y comparación detallada de
  commands/dashboard siguen abiertos; ningún task global se cierra por este
  bloque. No se activan backends ni se publica conocimiento de tareas abiertas.

Evidencias brutas locales ignoradas: opencode-v2-{python,node,adapter-final,docs}.xml,
opencode-v2-{qa-input,test-summary,diff-coverage,coverage-identity}.json,
opencode-v2-transport-probe.json y opencode-v2-migration-probe.json en
scratchpad/.venv. La cobertura deriva de c8/coverage.py oficiales; las fichas
públicas no incluyen rutas/credenciales de consumidores. Publicación en la
rama autorizada después de los últimos checks; sin merge ni release.

Checks del registro final: ledger-lint cero incoherencias/cero avisos;
test_roadmap_index 50 passed; export-interop --check 55 al día; diff --check
limpio. Scope-check: 28 archivos propios/cero fuera/cero avisos, settings ajenos
excluidos y conservados. Scan de esos contenidos/nombres sin marca del corpus.
El SHA publicado se contrasta con origin después del push a feat/catalog-capabilities.

## Revisión de dos lentes — intento 1: Fase 1 (T-02, T-05, T-06, T-08, T-09, T-14, T-15) — evidencia operativa

Lentes A+B por subagentes genéricos de contexto fresco: reviewer no disponible
como herramienta nativa. Scope-check contra 90a41f8: diez archivos propios
en alcance, cero fuera/cero avisos; settings ajenos excluidos y sin cambios.
Selector C/D false: solo documentación/evidencia, sin producción modificada.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Estados y alcance | ✓ | T-02/T-05/T-06/T-08/T-09/T-14/T-15 abiertas; aceptación global sin marcar |
| Comparación semántica | ✗ inicial | C004 tenía destino de conversación incorrecto; gap deduplicado A/B-1 |
| Constitución y dueños | ✓ | Sin segundo ledger, dependencias nuevas, escrituras ajenas ni acciones externas |
| Evidencia y límites | ✓ | Fixtures Claude fijadas, recovery y 12 hashes Codex; versiones, bypass y ausencia de evento separados |
| Exports y OpenAPI | n/a | No cambian hooks/agents/commands de producción ni spec API |
| Prosa, privacidad y trazabilidad | ✓ | Enlaces válidos, sin nombres públicos prohibidos y dependencias pendientes explícitas |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A/B-1 | Important | C004 se consolidaba como conversación y perdía su contrato de checkpoints Git | T-05/T-08 | Separar C001 y C004; conservar SHA, diferencias de archivos y artefactos tests/cobertura en ledger/QA, sin stash/commit automático ni confundir con checkpoint de prompts. Corregido, pendiente de revisión independiente | Fuente C004:13–53 y propuesta privada coinciden; fila pública corregida |

Comprobaciones documentales ejecutadas: pytest test_roadmap_index, 50 passed
(0,10 s); ledger-lint cero incoherencias/cero avisos. Helper privado
check_operational_evidence.py: 60 registros de origen y 18 propios con
hash/bytes/líneas LF/rangos comprobados, 12 hashes privados Codex, cuatro
fixtures Claude coincidentes, recovery positivo, 56 enlaces locales válidos,
JSON/nombres públicos válidos y fuente fijada sin cambios; exit 0.
Son pruebas de trazabilidad y estructura, no eficacia ni entrega funcional.
TDD n/a: prosa/evidencia; los rojos nativos se conservaron en T-09. Sin
producción modificada, la cobertura ejecutable del diff no aplica.

## Revisión de dos lentes — intento 2: Fase 1 (T-02, T-05, T-06, T-08, T-09, T-14, T-15) — evidencia operativa sin gaps pendientes

A+B por nuevos subagentes genéricos de contexto fresco, con tabla completa
del intento anterior. Re-evaluación de la corrección y su traza; criterios
aprobados conservados salvo evidencia nueva. C/D no aplican en este diff
documental. Sin defectos restantes: cero Critical, Important o Minor.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A/B-1 | Important | Destino incorrecto de C004 | T-05/T-08 | Corregido y verificado independientemente: C001 conversación; C004 anclas Git/evidencia en ledger/QA, límites y recursos pendientes | A2 y B2 contrastan fuente C004:13–53, propuesta privada y filas públicas 52–53 |

Ambas lentes validan conservación de SHA, diferencias y artefactos tests/
cobertura, ausencia de stash/commit automático, sin log duplicado y sin
confundir journal con Git. No se promueven entradas de knowledge porque
este bloque no crea ninguna. Jira-flow del intento 1: ops vacías, Jira
desactivado; nada publicado. El intento 2 conserva la misma degradación.

Los gates documentales del intento anterior siguen aplicando; la corrección
solo cambia una fila de prosa. Comprobación final de ledger, correspondencia,
JSON, enlaces, nombres y alcance antes del commit; no se atribuye a esta
revisión QA funcional del plugin. Las tareas globales y el objetivo continúan
en progreso. Próxima implementación: activar caché Codex conservando scope
y preferencias, corregir cierre por defecto y probar el lifecycle terminal
real antes de anunciar guardias o paridad entre runtimes.

## Implementación de cierre e instalación — T-02/T-09/T-14/T-15

Trabajo paralelo autorizado por el usuario: captura y lifetime de procesos,
instalación/caché Codex y revisión independiente. Doctor, documentación y
traza coordinados por el orquestador. Las skills siguen aplazadas; ninguna
tarea global se cierra por este bloque. Base del diff: b5a611a.

La captura terminal se extrae a `journal-capture.py`: un solo writer durable,
sin importar la materialización del journal, con snapshot físico compartido
por identidad y secuencia. El launcher recibe el runtime por argumento fijo,
no por texto del consumidor. El export de Codex declara tres segundos y
añade `--runtime=codex`; OpenCode declara `--runtime=opencode` al lanzarlo.
La instalación Codex valida la caché nativa antes de activar el scope local.
Doctor y status distinguen declaración, listado nativo, confianza y ejecución.

Rojos observados antes de implementar, 2026-10-08:

- RED: `SessionEnd capture is independent of slow materialization startup`
  falló: sin envelope con arranque de materializador de dos segundos.
- RED: `test_capture_end_hash_y_sequence_comparten_snapshot_fisico` falló:
  sequence 2 combinada con hash del snapshot anterior de una línea.
- RED: `SessionEnd timeout terminates its child tree before returning` falló:
  un descendiente escribió después de retornar el launcher.
- RED: `test_capture_version_uses_packaged_runtime_manifest` falló: manifests
  Codex y package-only devolvían 0.0.0.
- RED: `test_partial_journal_bundle_reports_missing_capture_without_blocking`
  falló: exit 1 y traceback al faltar el helper canónico.
- RED: `test_native_capture_rejects_oversized_payload_without_partial_envelope`
  falló: payload excesivo producía envelope.
- RED: export `test_codex_hooks_respetan_limite_session_end_y_runner_windows`
  falló: SessionEnd sin argumento literal de runtime.
- RED: `native adapter identifies its runtime independently of consumer
  payload` falló: argv sin runtime declarado por el adaptador.
- RED: cinco casos de doctor para estado nativo fallaron por ausencia del
  lector; después, el caso relativo de B-I4 falló porque se resolvía dos veces.
  GREEN de los quince casos actuales, sin CLI del consumidor.

## Revisiones parciales de corrección — cierre e instalación

B por revisores genéricos de contexto fresco, porque Agent(reviewer) no está
disponible. Estos pases parciales no constituyen la puerta completa A+B+D.
Scope-check: 34 archivos propios, cero fuera/cero avisos; únicamente settings
ajenos excluidos. Selector: C false; D true por espera del supervisor, lectura
de configuración y export. Falta cerrar QA y revisión completa del payload final.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B-T1 | Important | Padre Python termina pero nieto conserva pipes y evita deadline | T-09 | En corrección: ownership del árbol independiente de exitCode | Fixture Windows: nieto mantuvo pipes 3163 ms tras salida del padre |
| B-T2 | Important | Grupo Python separado sobrevive al cleanup del adaptador POSIX | T-09 | En corrección: lifecycle del grupo y ownership del adaptador | Contraste de código; reproducción Linux del revisor no ejecutada por falta de binario local |
| B-I1 | Important | Claves TOML quoted/bare duplicaban tabla equivalente | T-09 | Normalizar segmentos decodificados y rechazar cabeceras inválidas; revisión 2 en curso | RED previo y tests dedicados del instalador |
| B-I2 | Important | Ruta relativa nativa entrecomillada eludía validación | T-09 | Clasificar clave decodificada y scope nativo; revisión 2 en curso | RED previo y fixtures typed paths |
| B-I3 | Important | MCP env.config_file se trataba como ruta nativa | T-09 | Clasificar por scope, no solo nombre final; revisión 2 en curso | RED previo y fixture MCP preservada |
| B-I4 | Important | Doctor duplicaba raíz relativa en cwd y argv | T-09 | Absolutizar una sola vez | RED dedicado, GREEN quince casos de wrapper/estado |
| B-I5 | Important | CLI tests heredaban PATH real | T-14 | HOME/configdirs/PATH propios con stubs y credenciales filtradas; revisión 2 en curso | RED de aislamiento y pruebas propias |

Hipótesis de upsert de marketplace descartada con evidencia: el binario
oficial fijado 0.161.0 rechaza un origen diferente ya registrado. Esto no
recupera una preimagen inexistente de la configuración del consumidor.

Incidente de aislamiento: un test antiguo llegó al registro real de Codex y
dejó `marketplaces.daycry` apuntando a una carpeta temporal. La creación del
backup de caché falló con AccessDenied antes de activar el plugin. No se
dispone de preimagen de esa entrada; su reparación requiere el origen
anterior consultado al usuario. No se restaura el config completo, no se
ejecuta chmod ni se afirma que todos sus bytes permanecieron intactos.
Los probes posteriores usan solo homes, PATH, proyectos y proveedores propios.
El audit privado de este incidente queda fuera de Git y no publica rutas del usuario.

La revisión automática rechazó limpiar directorios auxiliares vacíos creados
fuera del workspace con el motivo `blocked by policy`. Esa limpieza no se
reintenta; no impide continuar las correcciones del plugin. Sigue pendiente.

QA previa a la corrección de lifetime: journal 150 passed/10 skipped;
export 28 passed; adaptador OpenCode 14 passed; doctor 184 passed/1 skipped.
La ejecución instrumentada conjunta dio 357 passed/11 skipped/14 deselected;
los catorce casos excluidos son capacidades ajenas a este diff. No se usa
esta medición como cobertura final de fuentes que cambiaron después.
Pruebas nativas previas conservadas por hash en las fichas: Claude headless,
Codex app-server con archive del hilo activo y OpenCode V2 con replay.
La nueva supervisión obliga a contrastar otra vez el payload final antes del push.

Segundo pase B parcial del instalador: B-I1–B-I4 verificados corregidos;
B-I5 corregido en tests del instalador, reabierto con evidencia nueva en
`test_doctor.py:_status`, cuyo subprocess heredaba PATH y credenciales.
Nuevo Important B-I6: `execFileSync` con SIGTERM espera una CLI no cooperativa;
fixture Linux propia con timeout 200 ms retornó a los 1292 ms. Sin una salida
posterior, el catch de cleanup no se alcanzaba. Cero Critical/Minor.

- RED: `test_status_subprocess_no_hereda_cli_ni_credenciales_del_host` falló
  porque el PATH del subprocess contenía el directorio host simulado y una
  credencial sentinel. Corregido con entorno permitido y stubs propios para
  los tres runtimes; el subprocess no depende del mock inprocess de doctor.
- B-I6 en corrección: worker Node con watchdog asíncrono y pipes internos,
  que limpia el árbol antes de retornar; outer wait también acotado. El rojo
  propio Windows dejó un descendiente vivo y bloqueo de cwd al limpiar.
- La ejecución Python instrumentada posterior se interrumpió deliberadamente
  al detectar B-I5 en doctor. No cuenta como QA verde ni cobertura final;
  mostró además un fallo sin resumen final que debe resolverse al repetir.

Rojos dedicados de lifetime preservados, 2026-10-08:

- RED: `SessionEnd cleans descendants after its direct child has already exited`
  falló: marker del nieto presente tras la salida del padre Windows.
- RED: `cleanup of the real launcher reaches its Python process` falló:
  marker posterior al cleanup en POSIX con grupo Python separado.
- RED: `test_group_cleanup_keeps_owner_running_and_kills_children` falló:
  SIGSTOP al grupo owner y ausencia de SIGSTOP individual del hijo.
  Los tres escenarios tienen GREEN dedicado en las fuentes congeladas.

A completa sin gaps confirmados; D sin hallazgos de rendimiento atribuibles.
B intento 3 verifica T1/T2/I1–I4/I6 corregidos y devuelve un Important I5:
PATHEXT `.EXE` omitía nuestros stubs `.cmd` y podía ejecutar un codex.exe
vecino al Node incluido en PATH. Fixture independiente propia reprodujo
`hostSiblingRuntimeExecuted: true`, sin CLI del consumidor.
El bucle automático de tres pases se detiene. El orquestador decide continuar
únicamente con esta corrección de aislamiento de tests y su verificación
dirigida independiente; no acepta deuda ni reinicia el contador de revisión.

- RED: `test_status_stubs_no_dependen_de_pathext_del_host` falló porque el
  subprocess conservaba PATHEXT `.EXE`. Se fija el selector Windows del
  entorno de tests para incluir los stubs propios; GREEN de los dos casos
  dedicados de aislamiento. No cambia producción.
- QA Python de fuentes finales: 357 passed/11 skipped/14 deselected, más dos
  fallos de export viejo detectados mientras se terminaba de regenerar la
  distribución. Corrección por exportador canónico: --check exit 0, 55 al día;
  suite export completa posterior: 28 passed. No son fallos intermitentes de
  la misma fuente; la distribución generada cambió entre ambas ejecuciones.

Verificación independiente dirigida de I5 sobre el intento 3: misma fixture
Windows con Node/codex.exe propios y PATHEXT `.EXE`, ahora
`hostSiblingRuntimeExecuted: false`. B confirma cero gaps pendientes de su
tabla, sin ampliar el pase. El cambio solo afecta el entorno de tests.

## Revisión de dos lentes — intento 3: Fase 1 (T-02, T-09, T-14, T-15) — cierre e instalación

Fusión final A+B+D por subagentes genéricos: Agent(reviewer) no está disponible.
Los pases B parciales y sus correcciones se conservan arriba; A revisa el diff
completo y los contratos, plan y constitución; D revisa el diff completo y
fixtures de rendimiento. C no aplica según selector automático; D sí por
esperas del supervisor y lecturas síncronas de instalación/exportación.
Esta sección cierra el bloque de captura/lifetime, instalación y diagnóstico,
sin dar por terminadas las guardias ni las tareas globales de la iniciativa.

| Criterio A | Veredicto | Evidencia y límite |
|---|---|---|
| Scope y contratos por runtime | ✓ | Diff propio contrastado con Archivos; settings ajenos preservados; instalación ≥0.161.0 y límites de cada runtime documentados |
| Captura canónica y ownership del cierre | ✓ | Writer único; Job Object Windows y grupo POSIX; pruebas de descendientes, pipes y muerte del padre; evidencia nativa final en tres runtimes |
| Scope Codex y preferencias del consumidor | ✓ | Config temporal privada, caché compartida, validación antes de activar; restauración de source por clave; colisión con origen ajeno explícita |
| Doctor/estado y límites de observabilidad | ✓ | Consulta nativa compartida, estado desconocido cuando no hay evidencia; no equipara enabled con confianza o ejecución |
| TDD, QA y distribución | ✓ | REDs trazados arriba; baseline nativo y cinco REDs del lector; cobertura oficial del diff y export canónico. El RED inicial del helper no se recupera de su consola y no se inventa |
| Documentación y tareas abiertas | ✓ | ES/EN, changelog, evidencia fechada y hashes; T-01 sigue siendo la única tarea global completada |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B-T1 | Important | Padre terminado y nieto conservando pipes evitaban deadline | T-09 | Corregido: ownership del árbol independiente de exitCode | RED de nieto Windows; GREEN runtime 34/34 y supervisor; cierre nativo final |
| B-T2 | Important | Grupo Python separado sobrevivía al cleanup del adaptador | T-09 | Corregido: ownership del grupo POSIX y cleanup sin detener owner | Dos REDs POSIX dedicados; cuatro casos Linux GREEN |
| B-I1 | Important | Claves TOML quoted/bare duplicaban tabla equivalente | T-09 | Corregido: segmentos decodificados y cabeceras válidas | RED de tabla comentada: 2 !== 1; tests instalador GREEN |
| B-I2 | Important | Ruta relativa quoted eludía validación nativa | T-09 | Corregido: clasificación por scope y clave decodificada | RED skills.config sin excepción; fixture relativa GREEN |
| B-I3 | Important | MCP env.config_file se confundía con ruta nativa | T-09 | Corregido: scope exacto de rutas tipadas | Fixture conserva env ordinario; revisión B sin gap |
| B-I4 | Important | Doctor duplicaba raíz relativa | T-09 | Corregido: raíz absoluta una sola vez | RED relativo; suite doctor y 18 casos finales de status/aislamiento GREEN |
| B-I5 | Important | PATH/PATHEXT permitían CLI del host en tests | T-14 | Corregido: entorno permitido y stubs seleccionados por PATHEXT propio | REDs sentinel y PATHEXT; verificación independiente dirigida hostSiblingRuntimeExecuted false |
| B-I6 | Important | CLI no cooperativa bloqueaba execFileSync tras deadline | T-09 | Corregido: worker con watchdog y cleanup, outer wait acotado | Reproducción Linux 200 ms → 1292 ms anterior; helper final 5/5 y cobertura 6/6 GREEN |

Cero Critical/Important/Minor pendientes en el bloque. La continuación
dirigida de B-I5 fue decisión explícita del orquestador tras detener el bucle
de tres intentos; no se contabiliza como cuarto pase global ni deuda aceptada.
La hipótesis de upsert sigue descartada con evidencia del binario fijado.
No se promueven entradas de knowledge: este bloque no creó ninguna.

D: cero hallazgos atribuibles al diff. 36 fixtures finales de cierre y seis
pares baseline/final; arranque externo domina las medidas y el baseline ya
supera 1,5 s en cinco de seis pares. Dos avisos de cleanup en 42 fixtures
conservaron envelope y status 0. No se promete latencia universal por debajo
del presupuesto nativo en cualquier equipo.

QA final: `qa-gate.py` VERDE, 1091 ejecuciones passed, 11 skipped, cero failed,
flaky o interrupted en la selección final. Son ejecuciones con repeticiones
dirigidas, no 1091 tests únicos. La clase export anterior completa (28 casos,
dos fallos) se sustituye por sus 28 casos GREEN tras regenerar; su XML rojo
permanece privado. La ejecución interrumpida no participa. Los 14 casos de
capacidades ajenas se excluyeron expresamente de pytest. Cobertura oficial
coverage.py/c8 de líneas añadidas ejecutables: **869/946 = 91,86%**, mínimo
90%; se conservan líneas sin cubrir. Los probes nativos no se usan como
cobertura instrumentada. [Resumen verificable](terminal-qa-evidence.json).

Payload del bloque anterior (snapshot 18f58e3) verificado nativamente:

- Claude 2.1.287: cierre headless, envelope antes de salida, debug SessionEnd
  completed status 0; el stream no emite respuesta SessionEnd.
- Codex 0.161.0: un app-server y archive del hilo activo; SessionEnd 1745 ms
  con timeout 3 s sin modificar, envelope antes de salida natural.
- OpenCode 2.0.12: dos loops activos, UTF-8, write/post, cierre y replay;
  43,829 s es duración de fixture completa, no latencia individual del hook.

Fichas públicas: [Claude](claude-hook-evidence.json),
[Codex](codex-lifecycle-evidence.json), [OpenCode](opencode-lifecycle-evidence.json),
[supervisión](terminal-capture-evidence.json) e
[instalación](codex-installation-evidence.json). Conservan hashes y resultados
anteriores sin atribuirlos al payload final. Homes, proyectos, proveedores
y credenciales de pruebas son propios; no se prueba TUI, todas las formas
de salida, confianza persistida, guardias por rol ni activación del consumidor.

Resolución del incidente de registro: el usuario eligió el repositorio
oficial `daycry/custom-agents`. Se cambian únicamente source_type y source
de marketplaces.daycry a git y https://github.com/daycry/custom-agents.git.
Se comprueba igualdad de toda la configuración parseada salvo esas dos
claves y de los tres payloads de caché conocidos. No se recupera la preimagen
desconocida, no se refresca ni activa la caché real. Audit privado sin
credenciales, fuera de Git. La limpieza rechazada por política sigue pendiente.

T-02/T-09/T-14/T-15 permanecen en-progreso por su aceptación global pendiente.
Siguiente bloque: identidad efectiva y allow/deny por rol; después comandos,
dashboard y recuperación de memoria. Skills siguen aplazadas: 79/293 evaluadas,
214 pendientes, cero altas de esa comparación en este bloque.

Jira-flow de esta fusión: `plan --event revision --actor reviewer --batch
--task T-02,T-09,T-14,T-15 --intento 3 --json`, ops vacías porque Jira está
desactivado; no se publica nada. La primera llamada sin --batch devolvió
error de argumentos y ops vacías; se corrigió la invocación, sin mutación.

Cierre documental independiente A: cero gaps confirmados y condiciones
previas resueltas. Verifica hashes de las doce fuentes finales, los diez
registros de QA, siete XML, cobertura y fichas nativas de los tres runtimes.
No certifica TDD histórico completo del helper cuyo RED inicial no se recupera.
Repite export --check exit 0/55; no cambia producción ni amplía la revisión B.

Verificaciones finales del bloque: linter 0 errores/3 avisos históricos de
nombres genéricos, ledger-lint 0 incoherencias/0 avisos, roadmap index 50 passed,
export 55 al día, git diff --check sin errores. Scope: 41 archivos propios,
cero fuera/cero avisos; settings ajenos excluidos y preservados. Correspondencia
histórica: 60 registros de fuente, 18 propios y 12 hashes nativos privados,
corpus sin cambios ni ejecución. Correspondencia final: hashes de producción,
fichas públicas/privadas y 100 enlaces locales comprobados; nombres públicos
limpios. Los hashes de doctor/journal en la lectura operativa son históricos,
conservados y contrastados con sus snapshots, no con el payload final.

## Siguiente bloque operativo — identidad y guardias nativas

El turno anterior fue progreso: commit/push 18f58e3 verificado remoto, cierre
nativo en tres runtimes y configuración source reparada por elección del usuario.
Se retoma T-02/T-08/T-09/T-14/T-15 sobre HEAD 18f58e3, sin tocar settings ajenos.
Tres investigaciones independientes en paralelo contrastan metadata y bloqueo
nativo por rol en Claude, Codex y OpenCode; solo fixtures propias y proveedores
loopback, sin ejecutar código del corpus. Diseño y criterios en design.md,
«Bloque 3». La lectura y los controles nativos positivos y negativos confirman
identidad en los tres runtimes. Nombre e
ID scoped no acreditan procedencia del prompt: se decide usar IDs propios
con semántica de rol protegido y una migración que preserve personalizaciones.
Las pruebas de mecanismo no se declaran implementación entregada.

Resultados paralelos preservados en native-role-contract-evidence.json:
Claude 14 casos, Codex 12 comprobaciones y OpenCode tres experimentos, incluidos
dos hijos reales. Los controles nativos demuestran ID efectivo, bloqueo previo,
sesión principal sin rol, rol ajeno permitido y límites de procedencia. Claude
usa política simplificada de fixture; Codex/OpenCode llaman al evaluador actual.
No se certifica normalización de todas las herramientas, instalación de la
guardia ni confianza persistida por estas pruebas.

Hallazgo reproducido del export Codex: sandbox_mode="read-only" en dos TOMLs
se acepta, pero ambos subagentes escriben sentinels vía Set-Content cuando el
padre tiene permiso. La proyección nativa no aplica ese campo ni hooks por rol.
Se corrige el export y la documentación activa ES/EN sin cambiar permisos del
consumidor. Los nombres canónicos/bare actuales aún no migran: el namespace y
su retirada segura pertenecen al siguiente bloque de integración.

- RED: test_reviewer_no_declara_sandbox_independiente_inexistente falló el
  2026-10-08 porque reviewer.toml exportaba sandbox_mode. Se corrige el productor,
  se regenera interop y el mismo caso queda GREEN.
- QA del bloque: export + roadmap, 78 passed. La primera cobertura no recopiló
  datos por usar un fichero como --source; no se usa como medición. Se repite
  export con --source=scripts, 28 passed y datos oficiales coverage.py válidos.
  El XML y la colección vacía anteriores se conservan privados.

Las descripciones activas de reviewer ya no prometen solo lectura por
construcción: su responsabilidad de no modificar código y las restricciones
reales por runtime quedan explícitas. Bash conserva permisos del runtime;
Write/Edit ausentes o permission.edit deny no cubren toda escritura indirecta.
No se incorpora ninguna skill ni se cambia el writer/lifetime del bloque previo.

La comparación de política previa queda en
[hooks-role-policy.md](comparisons/hooks-role-policy.md): 19 cuerpos completos,
un helper parcial y lecturas pendientes explícitas. Se prioriza protección
frente a bypass de verificación Git después de conectar el dispatcher; la
protección de configuración de calidad es candidata opt-in. Se descartan
retries como autorización. Ninguna de estas políticas nuevas se distribuye
en este bloque; no hay ejecución del corpus ni alta de paquetes técnicos.

## Revisión de dos lentes — intento 1: Fase 1 (T-02, T-06, T-08, T-09, T-14, T-15) — identidad nativa y permisos de reviewer

Nuevo bloque sobre base 18f58e3; no reinicia el bucle de cierre/instalación
anterior. Lentes A+B+D independientes y paralelas, con prompts literales;
fallback por subagentes genéricos porque reviewer no está disponible en esta
sesión. Selector actual: C false, D true por rutas del exporter y su suite;
no código de guardia añadido. Todas las lentes leen el diff completo y las
fichas nuevas; A/B contrastan las fuentes privadas sin ejecutarlas.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Identidad y bloqueo nativos, T-02 | ✓ | 14 casos Claude, 12 checks Codex, tres experimentos OpenCode; hashes privados/públicos coincidentes, dos hijos OpenCode contrastados |
| Comparación acotada, T-06 | ✓ | 19 cuerpos completos, uno parcial, 24 inmediatos y 16 descendientes pendientes; 44 hashes/rangos comprobados |
| Diseño y entrega separados, T-08/T-09 | ✓ | IDs y migración previstos; dispatcher privado; campo Codex ignorado retirado, sin promesa de integración |
| RED/GREEN, QA y cobertura, T-14 | ✓ | Test rojo previo al productor, mismo test verde; QA 78 passed; coverage.py y diff ejecutable 5/5 |
| Export canónico y formato | ✓ | A/B/D ejecutan --check, exit 0, 55 ficheros al día; B ejecuta 28 tests, todos passed |
| Límites activos de reviewer, T-15 | ✗ | A-E3: productor y método conservaban garantía por construcción, replicada en los cuerpos generados |
| Corrección y rendimiento del código añadido | ✓ | B y D sin hallazgos; dos callsites coherentes, selección O(1), sin E/S ni recorridos adicionales |
| Alcance y estados globales | ✓ | Solo T-01 completada; settings ajenos excluidos, integración y confianza real pendientes |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-E3 | Important | Instrucciones activas prometen solo lectura por construcción | T-15 | Pendiente en intento 1; corregido y revalidado en intento 2 | agents/reviewer.md y skills/adversarial-review/SKILL.md conservaban el claim, copiado a ambos exports; contradicción con el límite nativo medido |

Fusión: cero Critical, un Important, cero Minor en intento 1. No se rebaja
el gap ni se declara deuda. Se corrige el productor canónico, se regenera
interop y se actualiza el método; no se altera el estado del consumidor.
TDD n/a para estos deltas de prompt/documentación. El RED/GREEN del cambio
ejecutable del exporter queda preservado arriba y en sus XML privados.

## Revisión de dos lentes — intento 2: Fase 1 (T-02, T-06, T-08, T-09, T-14, T-15) — instrucciones y exports coherentes

A reevalúa solo A-E3 y sus deltas, sin reabrir lo aprobado. Verifica
agents/reviewer.md, la instrucción del método y ambos cuerpos regenerados;
responsabilidad de no modificar y permisos reales de Bash quedan explícitos.
Ejecuta --check: exit 0, 55 ficheros al día. Comprueba XML actual: 78 tests,
cero fallos/errores/skipped. B/D del intento 1 se conservan: no hay nuevo
cambio ejecutable desde sus dictámenes. A-E3: **corregido**. Cero gaps
Critical/Important/Minor pendientes; no hay entrada de memoria propuesta
nueva en este bloque para promover.

QA actual: [role-contract-qa-evidence.json](role-contract-qa-evidence.json),
qa-gate VERDE exit 0, **78 tests únicos passed**, cero failed, flaky,
skipped o interrupted. El input deriva de JUnit pytest, no de Playwright.
Cobertura oficial coverage.py 7.16.2: **5/5 líneas ejecutables añadidas,
100%**, mínimo 90%, solo el exporter; no se cuentan copias generadas como
código adicional. La primera colección sin datos no participa; XML/datos
anteriores permanecen privados. Los probes nativos no se suman al conteo.

La corrección y la evidencia del mecanismo quedan entregables. T-02/T-06/
T-08/T-09/T-14/T-15 permanecen abiertas por su aceptación global. Siguiente
paso concreto: conectar política central con metadata nativa, normalizar
todos los targets soportados y migrar IDs propios preservando agentes de
usuario. Después comandos, dashboard y recuperación de memoria; skills
siguen aplazadas en 79/293 evaluadas, 214 pendientes.

B contrasta por separado la derivación de la ficha QA final: 78 identidades
únicas, XML sin fallos, hashes oficiales coincidentes y diff recalculado
5/5, sin volver a ejecutar el publicador ni abrir otra revisión global.

Jira-flow de ambos intentos: gaps/revision, actor reviewer, batch, tareas
T-02/T-06/T-08/T-09/T-14/T-15; exit 0 y ops vacías porque Jira está desactivado.
No se publica ningún mensaje externo.

Gates finales: export --check 55 al día; linter 0 errores/3 avisos históricos
de nombres genéricos; ledger-lint 0 incoherencias/0 avisos; roadmap index
50 passed tras actualizar la traza. No se suman esas repeticiones a los
78 tests únicos de QA. Scope contra 18f58e3: 25 archivos propios en alcance,
cero fuera/cero avisos, settings ajenos excluidos. Checker final: 199 enlaces
locales, 22 hashes de procedencia nativa y 44 hashes/rangos del corpus
coincidentes, fuente fijada limpia, JSON y nombres públicos válidos, cero
referencias prohibidas. El exporter y las fuentes finales quedan fijados
en role-contract-qa-evidence.json; los hashes previos en terminal-qa-evidence.json
pertenecen al snapshot 18f58e3. Sin ejecución del corpus ni activación de la
caché real. La limpieza rechazada por política sigue pendiente.

## Bloque en progreso: guardias con identidad nativa y migración de agentes

Base: `8b51edd9ae1af020e0eb96bf92933e1f55edbaed`. T-02/T-08/T-09/T-14/T-15
siguen abiertas. Implementación local todavía sin revisión final, commit ni push.
Skills aplazadas: 79/293 evaluadas, 214 pendientes; sin ampliar el catálogo.

El dispatcher selecciona IDs propios de un mapa generado por runtime y consulta
la política central existente. No acepta el rol declarado dentro del input de la
herramienta. Codex y OpenCode exportan nombres con prefijo del plugin. La migración
usa manifiesto y hashes, conserva archivos ajenos/modificados y declara estado
incompleto ante conflictos. El contexto expone IDs del runtime. OpenCode evalúa
antes de ejecutar, sin reutilizar decisiones entre llamadas.

Evidencia TDD privada conservada, 2026-10-08:

- RED: entrada nativa del launcher falló por `unknown hook` antes del destino
  directo Python; mismo test GREEN para los tres runtimes.
- RED: entrada de contexto recibió `missing` antes de propagar el runtime fijo;
  mismo test GREEN.
- RED: timeout de branch y lectura limitada de config fallaron por `TypeError`
  antes de extender las APIs centrales; mismos tests GREEN, defaults conservados.
- RED: adapter OpenCode permitió escrituras protegidas antes de `execute.before`;
  mismos tests GREEN con política real. Diagnóstico de opt-out: RED y mismo GREEN.
- RED: MultiEdit incompleto perdió el diagnóstico; mismo test GREEN. El stand-in
  inicial descartado no cuenta como evidencia TDD.
- RED: installer sobrescribía un agente del consumidor; GREEN de conflictos,
  junction exterior, estado incompleto e ID propio desde otro nombre de archivo.
- RED: descripción del export no compartía el ID del mapa; mismo caso GREEN.

QA parcial: núcleo Python **140 passed**, normalizador **82 passed** y cobertura
oficial de su diff **202/206 = 98,06%**; installer dirigido **9/9**, V8 oficial del
diff **188/194 = 96,91%**. No se suman estos conjuntos como tests únicos ni se
presentan como QA final. Exporter: **56 archivos al día**. La suite amplia del
installer conserva un fallo de fixture: consultas a la CLI simulada rozan 3 s;
se reproduce `cli-timeout` sin cambio funcional en config/cache. Se corrige el
shim de prueba antes de dar por válida la suite; no se cambia producción.

La distribución real detectó un defecto pendiente: Claude recibe JSON `deny`,
pero el proceso no termina dentro de 5 s; el runtime descarta la decisión y
permite escribir. El control aislado sin suites concurrentes reproduce el fallo
(callback total 6.261 ms). Codex también registró un callback cancelado de 5.115 ms.
Se conservan protocolos y archivos fallidos y se investiga cierre/cleanup antes
de declarar eficaz la protección. OpenCode observa bloqueo anterior a escritura
en su primer caso real; matriz completa e hijos siguen en ejecución. No se afirma
paridad completa ni sandbox para herramientas arbitrarias.

El marketplace local Codex se reparó con autorización: origen Git oficial
`daycry/custom-agents`. Solo cambian dos campos; el resto de config y tres hashes
de payloads cacheados coinciden. No se refresca ni activa la caché real.

Registro posterior: PreToolUse Claude/Codex **10 s**, adapter OpenCode **10,5 s**,
presupuesto interno **4,5 s**, contención conservada. El diagnóstico privado de
una copia instrumentada midió 802 ms y no reprodujo hang; se conserva separado
de las pruebas de eficacia. La distribución final Codex 0.161.0 alcanza **14/14
checks de guardia** reales: deny de spec implementer, src architect y force Git;
allow de tasks/design/planner/agente bare/chat principal; metadata de los hijos
correlacionada y hashes de cache/fuente coincidentes. Los callbacks previos tardan
3.350–8.032 ms y no agotan los 10 s. La fixture usa catálogo de modelo compatible
del cliente y proveedor loopback propio, sin credenciales ni cambios del usuario.

El mismo experimento conserva **dos checks SessionEnd fallidos**: timeout nativo
de 3.041 ms y sin envelope en outbox antes del exit. Un experimento anterior sí
capturó envelope antes de un aviso de timeout. No se publica 16/16 verde, no se
amplían los 3 s ni se confunde captura con materialización. Se investiga el coste
de arranque/cierre y la recuperación del prompt retenido por separado. La matriz
Claude de 10 s ya acredita bloqueos y permisos, pero sigue en ejecución. OpenCode
verificó efectos correctos; una fixture anterior omitía cargar los prompts de
agente al desactivar discovery de proyecto, por lo que no cuenta como aceptación
de la distribución completa; la fixture final debe acreditar el prompt cargado.

Claude final: **13/13 casos nativos passed**, cinco deny aceptados antes de escribir
y ocho allow; todos con salida natural 0. Incluye cuatro hijos reales, controles
bare/principal y override explícito del mismo ID. Las fuentes ejecutables de
guardia coinciden en todos los casos; los primeros prompts preceden correcciones
de prosa, con hashes por caso preservados. La proyección pública en
[native-role-integration-evidence.json](native-role-integration-evidence.json)
excluye rutas privadas, prompts y payloads; no afirma todavía OpenCode completo.

Diagnóstico separado de memoria: dos copias instrumentadas, sin cambio de
producción, midieron escritura del envelope en 45/63 ms. El mínimo venv completó
SessionEnd en 2.704 ms; el mínimo base escribió antes de un timeout de 3.077 ms
durante cierre. El coste previo a Node fue 1.623/2.498 ms. No se confunden esos
diagnósticos con pruebas de eficacia de la distribución intacta. En el fixture
original cerrado sin envelope, `journal.py recover` recuperó **1 de 1 candidata**
desde el prompt UTF-8 retenido, sin avisos y con `recuperado_sin_cierre`. Es prueba
de recuperación a demanda; no acredita retoma automática por TTL. Se mantiene
el fallo de cierre original visible y la aceptación global de memoria abierta.

## Revisión de dos lentes — intento 1: guardias nativas y migración sobre 8b51edd

Scope previo: 101 archivos propios en alcance, cero fuera/cero avisos;
`.claude/settings.json` ajeno excluido. Selector: C true por ruta de sesión;
D true por lectura síncrona del instalador y exporter. Fallback de reviewer por
subagentes genéricos con prompts literales y contexto fresco. B/C independientes
ya finalizaron; A/D pendientes. No es todavía una revisión final aprobada.

| # | Grado | Gap | Tarea | Estado y evidencia |
|---|---|---|---|---|
| B-1 | Important | `splitlines()` divide caracteres Unicode/CR dentro de contenido patch válido y degrada a allow | T-09 | Corregido en productor, pendiente revalidación independiente. RED 24 fallos + 2 CRLF válidos; mismos 26 GREEN y suite 108 passed. Delta nativo Codex Unicode: deny de spec y tasks permitido con 29 bytes UTF-8 exactos, salida natural 0; snapshot conservado |
| B-2 | Important | Preflight ignora `agents` V2 y puede retirar un bare referenciado | T-09 | Corregido en productor, pendiente revalidación independiente. Test dedicado RED/GREEN; se inspeccionan ambos mapas `agent`/`agents`, con IDs y referencias `{file:…}` |
| C-1 | Important | Contexto válido ` *** Add File: …` se confunde con header, permitiendo Update protegido | T-09 | Corregido en productor; pendiente revalidación independiente. RED seis fallos y ocho controles válidos; mismos catorce GREEN, suite 122 passed. Deltas nativos Codex y OpenCode: Update protegido intacto y Update permitido con contenido UTF-8 exacto; snapshot 9827f5fd preservado |
| R-1 | Important | `Environment ID:own` válido sin espacio no se reconoce y degrada la guardia a allow | T-09 | Corregido en productor, pendiente revisión final y delta nativo. Se conserva RED contra gramática pinned OpenCode y GREEN en mismos casos; parser final 3347254b |
| R-2 | Important | Heredoc con delimitador válido distinto de EOF, con o sin `cat`, degrada la guardia a allow | T-09 | Corregido en productor según `stripHeredoc` nativo: delimitador ASCII, comillas emparejadas y whitespace ECMAScript. RED 17 fallos reales, 34 dirigidos GREEN y suite 156 passed; cobertura 211/215 = 98,14%. Revisión final y delta nativo pendientes |
| B-3 | Important | Una referencia `{file:…}` fuera de `agent`/`agents` puede perder su agente bare durante migración | T-09 | Corregido en productor; referencias en valores/claves de toda config, sin reclamar IDs desde comandos. `~/` y variables de entorno no resueltas conservan archivos con diagnóstico. RED/GREEN dedicados; tests actuales 16/16, cobertura 231/235 = 98,30%. Revisión final pendiente |

No se rebajan hallazgos ni se aceptan como deuda. Los tests dedicados y deltas
nativos deben conservarse con hashes de cada snapshot. La matriz ASCII previa
no se anuncia ejecutada contra el parser corregido; sirve como baseline junto
a las regresiones y los deltas posteriores. Los fallos SessionEnd no pasan a
verde por haber aprobado las guardias.

La lente A no encontró nuevos gaps de requisito o constitución en el bloque;
la aceptación de sus criterios de publicación y QA sigue pendiente. La lente D
no encontró regresiones de rendimiento medibles. OpenCode final acredita ocho
casos baseline (seis de matriz y dos hijos reales), más cuatro casos de regresión
Unicode/contexto sobre el parser 9827f5fd, con prompts de agente verificados y
salida natural cero. Los experimentos fallidos de modelo/seed de fixture se
conservan separados; no cuentan como pruebas verdes.

QA de raíz sobre ese snapshot: **180 tests Python passed**. Node: **36/37**
pasaron; SessionStart emitió `child cleanup confirmation timed out` en el primer
pase y pasó sin cambios de fuente en el reintento dirigido (**1/1**). La evidencia
mantiene ambos resultados y el test se registra como flaky, sin afirmar una
causa raíz demostrada. Cobertura oficial del diff del launcher, adapter y APIs
centrales: **69/71 = 97,18%**. Quedan las correcciones de gramática/referencias,
su revalidación independiente y la consolidación de QA del bloque.

Jira por intento 1: `jira-flow.py plan --event gaps --actor reviewer --task T-09
--intento 1 --json`, exit 0, `ops: []`; configuración desactivada, sin publicación.

## Revisión de dos lentes — intento 2: guardias nativas — límites de patches

La comprobación técnica dirigida B verificó las correcciones B-1/B-2/B-3/R-1/R-2
contra tests RED/GREEN y hashes actuales. La lente C de contexto fresco confirmó
de forma independiente un nuevo gap R-3; es la misma causa señalada por B, no dos
defectos distintos. No se declara revisión aprobada ni cierre de T-09. La tabla
completa del intento 1 se conserva arriba; no hay rebates ni deuda aceptada.

| # | Grado | Gap | Tarea | Corrección y evidencia |
|---|---|---|---|---|
| R-3 | Important | Los límites entre archivos después de Add/Delete requieren trim nativo, pero el normalizador preserva indentación como en Update y permite el patch protegido por degradación | T-09 | Corregido en parser 43f6c5ce: Add/Delete usan trim ECMAScript; Update conserva contexto con trimEnd estructural. RED/GREEN, C-1 retenido; revisión 3 y delta nativo pendientes |
| R-4 | Important | `strip()`/`rstrip()` Python no retiran BOM donde `trim()`/`trimEnd()` nativos sí lo hacen, y un patch protegido válido degrada a allow | T-09 | Corregido en parser 43f6c5ce: whitespace ECMAScript en headers/rutas/marcadores; EOF no convierte whitespace posterior en contenido. RED 40 fallos reales + tres controles, mismos 43 GREEN y suite 199 passed; cobertura oficial 227/231 = 98,27%. Revisión 3 y delta nativo pendientes |

El pase final usará revisores nuevos y revaluará las correcciones, con el estado
de esta tabla. La evidencia nativa iniciada antes de R-3 conserva su snapshot
3347254b; se añade un delta propio para la última corrección. No se reescriben
resultados previos como si hubieran ejecutado la fuente final.

Jira por intento 2: `jira-flow.py plan --event gaps --actor reviewer --task T-09
--intento 2 --json`, exit 0, `ops: []`; desactivado, sin publicación.

El normalizador extrae mutaciones de los esquemas soportados; no reimplementa
el validador ni la aplicación de patches del runtime. Conserva la tolerancia
previa para move-only y chunks vacíos, sin afirmar que el runtime los acepte.
Las decisiones por targets y la exención de enlaces de diseño siguen evaluadas
por el script central, con contenido/contexto UTF-8 original preservado.

## Revisión de dos lentes — intento 3: guardias nativas — validación de rutas

La lente C de contexto fresco finalizó sobre parser 43f6c5ce: **un Important
pendiente, cero Critical/Minor**. Su nueva evidencia impide aprobar el bloque.
El pase final conjunto A/B/D y el push no se completan: se alcanza el límite de
tres intentos y se devuelve la decisión de continuación. Las correcciones previas
no se promueven a aceptación global ni se marca completada ninguna tarea abierta.

| # | Grado | Gap | Tarea | Corrección y evidencia |
|---|---|---|---|---|
| R-5 | Important | Validar la ruta con `path.strip()` Python rechaza un nombre U+0085 válido y omite la guardia de otro archivo protegido del mismo patch | T-09 | Pendiente, CWE-863. Repro propio de C: primer Add con ruta NEL y segundo Delete de spec devuelve continue/input-unrecognized; primer Add src/a y mismo Delete devuelve deny. Fuente native-guardrail.py:58, hash 43f6c5ce. Contrato ECMAScript conserva NEL; resolución/aplicación pinned no elimina el carácter. Sin ejecutar upstream |

Propuesta de continuación: alinear la comprobación de ruta vacía con el conjunto
de whitespace ya definido, conservar NEL como parte del nombre y verificar todos
los targets. Exigir RED/GREEN del mismo payload, control permitido, prueba nativa
aislada e independiente revisión final antes del commit/push. No se ha aplicado
esta corrección tras alcanzar el límite; no se acepta el gap como deuda.

QA de raíz final del snapshot: **257 tests Python passed**, incluido el parser
199/199. OpenCode conserva 24 casos nativos entre baseline y deltas: ocho baseline,
cuatro Unicode/contexto, seis Environment/heredoc y seis sangría/BOM. Cada cohorte
conserva sus hashes; los seis últimos prueban R-3/R-4 con la fuente 43f6c5ce, no
R-5. Salidas naturales cero y controles permitidos con bytes exactos. La ficha
pública declara revisión no aprobada; unit tests verdes no resuelven este gap.

Las protecciones adicionales de migración conservan bindings de
`command`/`commands.*.agent` y las definiciones legacy `mode`, según contrato
pinned. La presencia de comandos Markdown en las capas conocidas impide retirar
exports bare, sin intentar interpretar YAML: las copias nuevas siguen su
preflight. Se conserva diagnóstico; el estado puede quedar incompleto aunque no
haya bare que retirar, porque cualquier aviso afecta al estado del instalador.
Esta limitación se registra, sin anunciar una migración plenamente verificada.

Consolidación QA del bloque (sin aprobar la revisión): **374 identidades únicas**,
373 passed y un flaky justificado; cero failed/skipped/interrupted. Los XML se
unen por identidad y se conservan el fallo inicial y reintento de SessionStart.
Installer final 19/19 y cobertura 272/276 = 98,55%; hash LF 2edeab74.
Cobertura oficial agregada del diff ejecutable: **663/677 = 97,93%**. Excluye
generados, JSON, prosa y tests. [native-role-qa-evidence.json](native-role-qa-evidence.json)
declara `review_approved: false` y R-5 pendiente; el verde de unit tests no
autoriza publicación. Jira por intento 3: exit 0, `ops: []`, desactivado.

Decisión de continuación solicitada al usuario el 2026-10-08: autorizar otro
ciclo acotado para corregir R-5 y completar revisión, o replanificar. El usuario
autorizó explícitamente corregir y completar la revisión. No se hace commit/push
de esta implementación sin resolver el gap.
La última entrega remota comprobada continúa en 8b51edd.

## Revisión de dos lentes — intento 4: ciclo adicional autorizado — R-5

Autorización expresa del usuario tras el límite de tres intentos; nuevo ciclo
acotado de hasta tres pases (intentos 4–6) para corregir y completar la revisión.
La plataforma rechaza crear revisores nuevos con
`agent thread limit reached`. Se revalidan las correcciones con los revisores
anteriores, independientes de quienes las implementaron. Se declara la pérdida
de contexto fresco; no se presenta esta degradación como un pase de agentes nuevos.

R-5 corregido en productor bbd3608c: validación de ruta vacía con whitespace
ECMAScript, conservando NEL. RED real de 17 regresiones, mismos 17 GREEN;
suite 216 passed y cobertura oficial 227/231 = 98,27%. Sin cambio de API/política.
La auditoría del normalizador no encuentra trims sin charset. La lente C verifica
la corrección de forma independiente. Delta OpenCode real: dos casos con parser
bbd3608c; el Delete protegido se bloquea antes de ambos efectos, el Delete
permitido y Add NEL conservan bytes exactos. Salida natural cero. Las cohortes
anteriores mantienen sus hashes originales.

La limitación de diagnóstico Markdown sin legacy se corrige en este ciclo:
se conserva el discovery acotado y el impedimento de retirar bare no verificable,
pero el aviso se emite solo cuando hay una copia antigua real. Test dedicado RED
por warnings inesperados; GREEN del mismo caso y dos controles de preservación
(3/3). Installer final LF cbcd7d50: 20 casos dirigidos, 19 pasan y el A/B falla
por consulta nativa de fixture no disponible. Primer reintento A/B vuelve a
fallar; una consulta mínima y una copia diagnóstica pasan, sin acreditar el test
canónico. Un posterior reintento del mismo test canónico pasa sin cambios en
fuente, límites ni assertions. Se conserva como flaky con los tres XML; no se
atribuye una causa demostrada. Cobertura oficial del diff installer: 276/280 =
98,57%. Fuentes y limitaciones históricas permanecen en los registros.

La lente D encuentra R-6 Important: un heredoc sin cierre con 16.000 LF y JSON
de 32.187 bytes excede 5.002 ms después de READY, por encima del presupuesto
interno de 4.500 ms. La expresión regular reintenta la apertura con coste
cuadrático. No se acepta como deuda ni se cambia el presupuesto para ocultarlo.
Jira por intento 4: exit 0, `ops: []`; desactivado, sin publicación.

## Revisión de dos lentes — intento 5: scanner lineal y evidencia final

R-6 corregido en normalizador 17fcd2ba: scanner lineal de heredoc, conservando
delimiter ASCII-word, quotes coincidentes, `cat` opcional, whitespace ECMAScript,
cierre literal y cuerpo exacto. TDD: dos fallos RED acotados tras READY y tres
controles preválidos; mismos cinco GREEN. Suite 221 passed, cobertura oficial
255/261 = 97,70%. No cambia la API, política central ni los permisos nativos.

La lente B independiente compara 20.000 casos pequeños con la gramática previa:
cero diferencias. La lente D compara 4.608 casos, 576 wrappers reconocidos y cero
discrepancias. Sus cinco evaluaciones por caso tras READY miden máximos de
2,565 ms para cierre ausente/mixto y 24,473 ms para casos válidos protegidos o
permitidos; todos por debajo de 4.500 ms y 64 KiB JSON. Corpus acotados, sin
afirmar equivalencia universal. Revisores reutilizados por límite de plataforma,
independientes de la implementación; no se declara contexto fresco.

Delta OpenCode real sobre el parser final: dos casos heredoc, deny protegido y
patch permitido con bytes exactos, prompts nativos cargados y salida natural
cero. La ficha [native-role-integration-evidence.json](native-role-integration-evidence.json)
conserva 28 casos OpenCode por cohortes, 13 Claude y 14 checks Codex baseline
más su delta; cada snapshot identifica su fuente. No anuncia toda la matriz
ejecutada contra el parser final ni transforma SessionEnd en verde.

QA final: 282 tests Python de raíz passed, 221 del parser incluidos. Se unen
reportes por identidad con exports, installer y Node: **397 identidades únicas**,
395 passed, dos flaky justificados, cero failed/skipped/interrupted; qa-gate
exit 0. Los fallos de SessionStart y A/B siguen visibles y sus reintentos no
suman pruebas únicas. Cobertura oficial agregada del diff: **695/711 = 97,75%**.
[native-role-qa-evidence.json](native-role-qa-evidence.json) recoge fuentes,
instrumentos y límites. La lente A acepta el bloque con todos los criterios
conformes: alcance, R-5/R-6, eficacia/trazabilidad de cohortes nativas, migración,
QA/flaky, cobertura, generado/documentación y constitución. Lentes A+B+C+D:
**0 Critical, 0 Important, 0 Minor pendientes**. Los hallazgos de los intentos
anteriores quedan corregidos y revalidados, sin rebates ni deuda aceptada.

| # | Grado original | Gap | Tarea | Corrección y evidencia |
|---|---|---|---|---|
| R-5 | Important | Ruta NEL omitía otro target protegido | T-09 | Corregido; RED/GREEN, delta OpenCode bbd3608c y revalidación C/A |
| R-6 | Important | Heredoc incompleto excedía presupuesto interno | T-09 | Corregido; scanner 17fcd2ba, dos RED/cinco GREEN, 221 tests, equivalencia B/C/D, medición D tras READY y delta nativo final |

Se acepta y autoriza publicar **este bloque**, con contexto reutilizado declarado.
Ninguna tarea global abierta ni la memoria se marca completada. ADR-023 se
promueve en memoria local; sustituye la ubicación exclusiva de ADR-007 y
mantiene su alcance por rol. Esos documentos locales están fuera de Git.
Jira por intento 5: `revision`, exit 0, `ops: []`; desactivado, sin publicación.
Puertas finales: lint_plugin cero errores/tres avisos históricos de nombres;
56 exports al día; ledger-lint cero incoherencias/cero avisos; scope-check
104 archivos propios en alcance/cero fuera y un settings ajeno excluido entre
105 cambios detectados. Scan de 881
archivos públicos: cero referencias o nombres prohibidos. Diff sin errores.
Publicación comprobada el 2026-10-08: commit
`54e8b3f8e117bfc1f9f4a83951f77631541b1549`, push de
`feat/catalog-capabilities` exit 0 y `git ls-remote --heads` coincide con HEAD.
Después del push, 56 exports siguen al día y el único archivo sin seguimiento
es `.claude/settings.json` ajeno, intacto y nunca incluido en el commit. La
memoria local ADR-023/ADR-007 también permanece fuera de Git. Este registro
documenta la entrega verificada del bloque; T-02/T-08/T-09/T-14/T-15 conservan
sus pendientes globales. Las skills siguen aplazadas en 79/293 evaluadas.

## Bloque operativo 5 — diagnóstico con acciones prioritarias

Base comprobada: `d3a2490a798485f5b0f982b6e04f2b55bd9c633b`. El turno anterior
fue progreso: corrigió y publicó guardias/IDs/migración con SHA remoto verificado.
Se continúa T-05/T-08/T-11, conservando skills aplazadas y aceptación global abierta.

Comparación pertinente completa: C030 (84 líneas), motor R-3d9f69328581
(1.085 líneas) y callers A031 (55) / S052 (46), contra revisión fijada y hashes
coincidentes. Lectura estática, sin ejecutar el corpus. No cierra globalmente
esos callers ni integra skills. El contraste propio cubre filas, registros,
ensamblado, rendering y CLI de doctor, ambos comandos doctor/setup y exportación
de sus cuerpos; no se afirma lectura de todos los checkers de doctor.

Diseño registrado en design.md antes de producir código. Dueño: doctor;
añadir acciones derivadas a JSON/Markdown y actualizar consumidores/docs.
Se conserva el contrato de filas y se descartan scores de inventario. El panel
se investiga en paralelo; su selector hoy no cambia la fuente de hooks y no
reconoce los handlers Codex con argumento runtime. Ese gap alimentará el siguiente
bloque, sin convertir la presencia de archivos en carga o ejecución probadas.

TDD/QA en progreso. Un test histórico diagnostica el repo real; se trasladará
a proyecto temporal con fuentes propias antes de correr la suite, para conservar
la comprobación del linter sin leer `.claude/settings.json` ajeno. No hay push
de este bloque hasta verificar implementación y revisión.

## Bloque operativo 6 — hooks por runtime en el panel

Investigación paralela completada: 29 lecturas propias/de origen con hashes y
rangos privados, diez hashes de origen coincidentes. Siete recursos releídos
completos y tres entrypoints parcialmente; se conservan sus lecturas completas
históricas sin cerrar dependencias globales. No se ejecuta código del corpus.

Repro propio del reader actual: los tres selectores presentan ocho handlers
Claude y SessionEnd 5 s; Codex declara 3 s. Regex de metadata no reconoce guardia
ni argumentos runtime. Footer conserva ubicación anterior de guardias y móvil
oculta Fuentes. Navegación y seis etapas ya tienen solución y tests históricos;
no se atribuye su bug antiguo al estado actual.

Diseño Bloque 6 registrado antes de producir código. Dueños: build_panel,
plantilla y contrato de bindings consumido por adapter OpenCode. T-06/T-08/T-13
y sus gates se aplican en paralelo al Bloque 5. Mantener estados de carga y
ejecución desconocidos, fuentes/runtime y presupuestos exactos; sin nuevo
servidor, escritor de memoria ni conexión de servicios. TDD, QA y delta nativo
propio pendientes; no se publica este bloque hasta su revisión independiente.

### Implementación y QA de los Bloques 5/6

Doctor incorpora `acciones_prioritarias` sin cambiar filas, conteos o exit:
errores antes de avisos, desempate canónico, total completo y hasta tres acciones
con bloque/ordinal. Markdown presenta esa selección antes de las tablas. El
test de linter utiliza consumidor temporal y la suite aísla homes/registro;
el settings ajeno no se lee. TDD: diez RED iniciales, diez GREEN; un RED de
orden Markdown y once GREEN finales. Suite Windows final **207 passed/1 skipped**
(chmod); Linux **207 passed/1 skipped** (PATHEXT). Cada caso omitido por plataforma
pasa en la otra. Cobertura oficial del diff **19/19 = 100%**. La primera
invocación de cobertura por filepath no produjo datos válidos; se conserva
como diagnóstico rechazado y se utiliza el informe final por módulo/directorio.

Panel incorpora fuentes independientes, 23 handlers y **17 grupos** declarados:
Claude 8/6, Codex 8/6, OpenCode 7/5. Muestra fuente/localizador, función, activación,
guardia por ID y procedencia/unidad del presupuesto. Booleanos, no finitos e
integer de 400 dígitos degradan a inválido; handlers no identificados permanecen
desconocidos. El JSON estricto consumido por OpenCode gobierna registros,
handlers, filtros y supervisión, sin importar JavaScript desde el catálogo.
No se modifica el normalizador, launcher, mapa de roles ni installer.

TDD panel: 17 RED iniciales → GREEN; dos RED de número/mapa booleano → nueve
GREEN; cinco RED de comportamiento/bindings incompatibles → cinco GREEN.
Adapter: tres RED de catálogo inexistente → GREEN; suite Windows **19/19**.
Cobertura oficial del diff Python **167/168 = 99,40%**, adapter **33/34 = 97,06%**.
Suite panel tras B1: Windows **84 passed/2 skipped** por symlinks; Linux final
**85 passed/1 skipped** por junction Windows. Las omisiones de plataforma quedan
cubiertas por los controles de la otra plataforma. La plantilla se ejercita
mediante DOM real y navegador, fuera de esos denominadores de statements.

Navegador Edge: nueve casos finales pasan, sin retries automáticos. Inventario,
filtro de los tres runtimes, presupuestos e identidades, enlaces, foco/historial,
destino ausente, seis etapas, Fuentes móvil, movimiento reducido, skip link y
extensiones independientes. Dos ejecuciones previas se conservan rechazadas:
arranque Edge con directorios de perfil falsos/largos, y selectors del runner
que incluían extensiones al contar catálogo. Se corrigen entorno y selectores,
conservando las assertions; no se presentan como passes ni como fallos del panel.
La generación inspecciona solo fixtures/homes propios; Edge usa perfil temporal
nuevo y conserva los known folders del sistema necesarios para arrancar.

El [delta nativo OpenCode](panel-native-delta-evidence.json) verifica dos casos
con el adapter modificado: deny previo al observer, patch permitido con bytes
exactos, cuerpos de agentes nativos cargados, notificación documental observada
y salida natural cero. Proveedor loopback y homes/config/proyecto propios; no
activa caché del consumidor. No acredita todos los handlers informativos ni
captura durable de memoria. Los snapshots anteriores permanecen inmutables.

QA adicional: export-interop regenera 56 archivos y `--check` confirma los 56
al día; tests del exportador **35 passed**. `evals/check`: 51 piezas, 182 casos,
cero errores. Linter cero errores y tres avisos históricos; ledger cero/ cero.
Gates finales, contraste de entorno Linux, revisión A y publicación aún pendientes.

## Revisión de dos lentes — intento 1: Bloques 5/6 (T-05/T-13) — filtro de extensiones

Nuevo ciclo acotado para este diff desde `d3a2490`, separado del bloque de
guardias aceptado en intento 5. Contexto fresco: lentes B y D genéricas porque
el tool `reviewer` no está disponible. Selector automático: C false; D true
por await en los bucles del adapter. D no encuentra degradación introducida:
tres handlers secuenciales y cuatro registros ya existían; doctor añade dos
pasadas lineales y panel tiene fuentes/inventario acotados. A queda para el
diff y evidencias finales; este pase no acepta ni publica el bloque.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Excepción de runtime de catálogo aplicada también a extensiones | T-13 | Corregido tras el pase; condición limitada a `sectionId === 'catalog'` | Tres RED reales Node/DOM (agent/skill/mcp) → tres GREEN, suite 84/2, Linux 85/1, navegador H-09 |

Sin rebates ni deuda aceptada. Cero Critical/Minor; el único Important se
traspasa a intento 2 para revalidación independiente. Jira del pase: `gaps`,
exit 0 con `--batch`, `ops: []`, desactivado; sin publicación. La primera llamada
sin `--batch` fue rechazada antes de generar operaciones y se corrigió.

## Revisión de dos lentes — intento 2: Bloques 5/6 (T-05/T-13) — revalidación de B1

Lente B nueva, contexto fresco, recibe la tabla completa del intento 1:
reevalúa solo la corrección y no reabre áreas aprobadas sin evidencia nueva.
Confirma B1 corregido, hashes congelados y regresión 3/3; su control independiente
recorre 2.592 combinaciones de runtime/tipo/origen/búsqueda, sin discrepancias.
Cero Critical/Important/Minor en B. Se conserva el veredicto D sin cambio de
productores que altere su análisis; A y QA final todavía no autorizan entrega.

Jira del intento 2: `revision`, exit 0 con `--batch`, `ops: []`, desactivado;
sin publicación. Cuatro casos históricos de navegador de extensiones también
pasan después de actualizar su contador a grupos runtime/evento. La generación
y ejecución usan consumidores propios y conservan sin cambios sus fixtures.

### Puerta QA final de los Bloques 5/6

[panel-command-qa-evidence.json](panel-command-qa-evidence.json) une reportes
canónicos por módulo/título: **361 identidades únicas**, todas con ejecución
positiva, cero failed/flaky/interrupted y ninguna omisión sin cubrir. Los skips
por plataforma conservan identidad/motivo en cada reporter y su pass en el
otro sistema; no se convierten en tests nuevos. `qa-gate.py` exit 0, VERDE.
Cobertura oficial agregada del diff **219/221 = 99,10%**; cada script supera 90%.
No se suma dos veces la copia generada del adapter ni se incluye HTML en el
denominador de statements Python/Node.

Linux adapter final **19/19**, exit 0. Se conservan preparaciones rechazadas:
imagen sin `ps` y sin reaper, y snapshot crudo del checkout Windows con CRLF.
A/B con adapter/tests originales `d3a2490` reproduce las mismas tres identidades
de fallo; `/proc` comprueba hijos zombie con PPID 1. Imagen QA privada derivada
del pin existente incorpora procps de fuentes oficiales Debian; las pruebas
corren offline con `--init`, tar/runner propios readonly y salida propia,
sin montar workspace, home ni socket. Con procps pasan las dos limpiezas;
queda un fallo de contexto. `bash -n` reproduce `in\r` en el shell crudo y pasa
con LF. Las ocho normalizaciones en la copia QA obedecen `.gitattributes` y
coinciden byte/hash con los blobs canónicos de HEAD y `d3a2490`. La suite final
canónica pasa sin cambiar fuentes, tests, assertions ni plazos. No se borra ni
presenta como verde ninguna preparación rechazada.

Las rutas, hashes y conteos de XML RED/GREEN, oficiales de cobertura, reportes
de navegador y QA Linux figuran en la ficha pública. Evidencia privada de
doctor en `scratchpad/.venv/doctor-priorities-*`; panel/adapter Windows en
`scratchpad/.venv/dashboard-comparison/`; Linux doctor en
`scratchpad/.venv/doctor-linux-ba9b7f4a15f0/`; panel final en
`scratchpad/.venv/panel-adapter-linux-final-8fb8dc5c4423/`; adapter LF final y
prueba de checkout canónico en `scratchpad/.venv/panel-adapter-linux-procps-image/`.
Estos artefactos no se versionan; la ficha exporta exclusivamente datos propios
acotados y hashes, sin prompts, memoria privada ni credenciales.

### Aceptación acotada y parada solicitada

La lente A fresca contrasta fuentes, diff, tests, docs, las fichas y todos los
hashes/reporters privados del QA público; cuenta de forma independiente las
361 identidades. Conformidad por criterio: comparación C030/destinos, diseño
previo y alcance, prioridades/empates/límite/filas/exit/CLI, fuentes/grupos/
handlers/identidades/presupuestos/desconocidos, lectura acotada/catálogo consumido,
UI y delta nativo, TDD/ejecución/cobertura, documentación ES/EN/constitución.
Todos ✓. Su propio `export-interop.py --check`: exit 0, 56 archivos al día.
Lentes **A+B+D**, contexto fresco mediante subagentes genéricos; C no seleccionada
por el selector automático. **0 Critical, 0 Important, 0 Minor pendientes**.
B1 queda corregido y revalidado, sin rebates ni deuda. Los Bloques 5/6 se
aceptan para publicar; el intento 2 cierra este ciclo acotado.

No se crearon entradas nuevas de conocimiento que promocionar en estos bloques;
las anteriores aceptadas se conservan fuera de Git. Las fichas de lectura
históricas mantienen el estado anterior a entrega. Se consolida un concepto
de comando (C030) en doctor; no se suman nuevas skills ni se cierran los callers
globales. Tampoco se cierran T-02/T-05/T-06/T-08/T-09/T-11/T-13/T-14/T-15 globales
o la eficacia de memoria. El 2026-10-08 el usuario solicita explícitamente
hacer los commits, push de la rama y **parar al acabar este bloque**. No se
inicia la siguiente fase ni se reanudan las 214 skills pendientes.

### Publicación verificada de los Bloques 5/6

Implementación y documentación: commit
`363d0c95ca4069ec1a51af8c4dc6a944197b67cc`, 41 archivos propios.
Push a `feat/catalog-capabilities` exit 0; `git ls-remote --heads origin`
confirma exactamente ese SHA. Tras el push, `export-interop.py --check` sigue
en exit 0 con 56 archivos al día. Solo permanece sin seguimiento el
`.claude/settings.json` ajeno; no se leyó, modificó ni incluyó en el commit.
Scan de 869 archivos públicos: cero nombres/referencias prohibidos. Scope:
41 propios en alcance, settings ajeno excluido, cero fuera y cero avisos.
Linter cero errores/tres avisos históricos; ledger cero incoherencias/cero avisos.

Este registro se incorpora en un commit documental separado. Se conserva la
instrucción de detener el objetivo tras publicar, con pendientes globales
documentados, sin iniciar otra fase. El panel local actualizado está generado
fuera de Git; no contiene fixtures de extensiones ni configura el consumidor.

## Bloque operativo 7 — diagnóstico de cierre y contrato de memoria

El usuario pide continuar después de la parada anterior. Base `470e92e`,
T-02/T-07/T-09/T-14/T-15; nuevas skills todavía aplazadas. Se aplica
`debug-root-cause`: no modificar el cierre sin hipótesis probada. La evidencia
histórica de timeout nativo y falta de envelope se conserva, sin extrapolar
el tiempo del negocio a toda la ejecución. Contrato Codex reconsultado en
`https://learn.chatgpt.com/docs/hooks`: SessionEnd síncrono, default 1 s,
máximo 3 s; `async` no amplía el presupuesto. Fuente oficial local
`d27764b82f7118f674371e6d6e76271d9d606edb`,
`codex-rs/hooks/src/events/session_end.rs`, constantes 20–23.

La auditoría de T-07 confirma documentación obsoleta en la skill existente:
Graphiti presentado como futuro y toda consulta atribuida al stack externo,
pese a las funciones de lectura/router presentes. Se reconcilian mapa,
contrato y docs ES/EN; no se incorpora otra skill ni se activa un servicio.
Las referencias de proveedores son instrucciones al servidor, sin acreditar
modelo efectivo o coste. Se elimina la promesa genérica de captura <100 ms.
FLOWS distingue presupuestos/eventos por runtime y actualiza el claim antiguo
de guardias solo por frontmatter con el dispatcher ya entregado.

Archivos del bloque documental: skill y README del adaptador existentes,
README raíz ES/EN, docs/README ES/EN, FLOWS ES/EN, changelogs ES/EN y roadmap.
TDD n/a: prosa; producción del cierre intacta hasta prueba de causa. Se
validarán contratos existentes, lint/evals/exports/ledger y revisión A+B.
No se cierran tareas globales ni se atribuye utilidad medida a un backend.

### Diagnóstico y corrección del entorno de QA del Bloque 7

La primera tanda produjo 405 elementos JUnit: cuatro fallos; pytest declara
399 tests y dos subtests pasados. Se conserva íntegra, sin convertirla en verde.
El runner directo del exportador falla al recibir tests con fixtures; pytest
es la invocación compatible y pasa los 35 tests en base y cambio actual.

Contraste A/B con las mismas fuentes y memoria curada en copias privadas:
base `470e92e` y actual reproducen los tres fallos de knowledge-find; el
scanner de hooks pasa en ambas copias sin bytecode. No se modifica el scanner.
La caché `.pyc` local hizo fallar su lectura UTF-8 estricta en el workspace.

RED: `test_show_imprime_la_entrada_completa_tal_cual` y
`test_show_json_envuelve_el_contenido_con_su_ficha`: la fixture escribe CRLF
en Windows aunque los assertions requieren el contenido LF original.
Solo fijar `newline="\n"` en la escritura privada hace pasar ambos tests.
La corrección pública aplica esa misma escritura, sin alterar el lector.

RED: `test_ca03_related_adr010_grafo_curado_en_menos_de_1600_caracteres`
exige ADR-007 en una vista humana topada a seis entradas por grupo. Al
crecer el corpus puede quedar fuera de la vista. El test ahora exige
ADR-006/ADR-007 en la relación JSON completa, conserva el tope de 1600
caracteres y exige el marcador si ADR-007 no cabe en la vista compacta.
Fuentes/tests ejecutables de producción intactos; cobertura del diff n/a
porque el único código modificado es de prueba.

## Revisión de dos lentes — intento 1: Fase 2 (T-07, T-15) — contrato y diagnóstico parcial

Lentes A+B por subagentes genéricos frescos, sin agente reviewer nativo
disponible; tier declarado opus/high, sin override de proyecto. Scope exit 0;
selector C/D false, sin motivos. Ninguna lente implementó los cambios.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Contratos de memoria y proveedores vigentes | ✓ | A1/B1 contrastan router, `puede_leer`, adaptadores y proveedores |
| Diagnóstico sin promesa de fix ni cierre global | ✓ | Tres cohortes separadas; hashes instrumentados/originales; histórico abierto |
| Alcance, espejos y generación | ✓ | Scope cero fuera; A1 ejecuta export --check: 56 al día, exit 0 |
| No activar backends ni añadir skills | ✓ | Solo mapa/docs/evidencia; estados globales preservados |
| Verificación final no inventada | ✓ | QA aún pendiente al revisar; ninguna T global cerrada |

Gaps: cero Critical/Important/Minor. B1 verifica 12 hashes de evidencia y 15
snapshots de cohortes. La tanda QA posterior expone problemas de fixture/
invocación ya registrados arriba; los cambios de tests requieren el intento 2.

Jira del intento 1: `jira-flow.py plan --event revision --actor reviewer
--task T-07,T-15 --batch --intento 1 --json`, exit 0; desactivado, `ops: []`.

## Revisión de dos lentes — intento 2: Fase 2 (T-07, T-14, T-15) — fixtures de memoria

Lentes A+B por nuevos subagentes genéricos frescos; C/D false, sin motivos.
Traspaso íntegro de aprobación A1/B1, sin reabrirla al no existir evidencia nueva.
Scope exit 0: tests bajo T-14/T-15, resto del bloque bajo su alcance previo.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Fixture LF sin cambiar assertions ni lector | ✓ | A2/B2 leen línea 122; A/B y variante LF verificadas |
| Relaciones completas y salida humana acotada | ✓ | JSON exige ambos IDs; ≤1600 y aviso de truncado conservados |
| RED/GREEN con procedencia explícita | ✓ | A2/B2 verifican hashes XML/logs; GREEN privado equivalente, no byte idéntico al test público |
| Generados y contratos mantenidos | ✓ | A2 ejecuta --check: exit 0, 56 archivos al día |
| QA y aceptación global no inventadas | ✓ | Suite final aún en marcha al revisar; ninguna T global cerrada |

Gaps: cero Critical/Important/Minor. La QA final debe validar el test público
exacto en el snapshot con overlay, no atribuirle por identidad el GREEN privado.

Jira del intento 2: `jira-flow.py plan --event revision --actor reviewer
--task T-07,T-14,T-15 --batch --intento 2 --json`, exit 0; desactivado, `ops: []`.

### Resultado del diagnóstico nativo y QA final del Bloque 7

[SessionEnd reducido](session-closure-diagnosis-evidence.json): Codex 0.161.0,
dos cierres instrumentados completan captura antes de salir en 1251/1492 ms.
El segundo usa cero turnos y cero peticiones al proveedor; el primero una
petición a un stub local propio. Un override con shell anidado falla en 864 ms
por comillas y se rechaza. Hashes originales e instrumentados diferenciados.
El mínimo no reproduce el timeout histórico bajo carga de subagentes;
no hay causa probada ni cambio de producción. La fiabilidad sigue abierta.

La primera copia final produjo 402/403 pruebas de memoria verdes: el único
rojo hereda el Git del workspace y su exclusión de scratchpad en vez de un
`.gitignore` propio. Se conserva el resultado. Inicializar Git únicamente en
la copia de QA corrige esa fixture: el delta dedicado pasa 1/1. La repetición
completa posterior tiene artefactos separados, sin sobrescribir ningún rojo.

[QA final](memory-contract-qa-evidence.json): **403 pruebas de memoria + 35
de exportación = 438 identidades únicas**, cero fallos, errores, skips o flaky;
qa-gate VERDE. Memoria: 246,78 s; exportación: 1,74 s. Es una tanda dirigida,
no toda la suite del repositorio. Entorno Python 3.13.0/pytest 8.4.2, homes y
Git propios, sin `.pyc`; servicios simulados locales. El entorno inicial
reporta 403 casos padre y dos subtests separados; el final ejecuta los
subtests dentro de su caso padre. No se han eliminado pruebas por ese conteo.

[Contraste causal y procedencia](memory-contract-test-diagnosis-evidence.json):
917 hashes de la copia siguen intactos tras ejecutar (865 fuentes + 52 archivos
de memoria curada). El test público coincide exactamente con el snapshot:
SHA256 `9bbf23e962b92a4e15aadd98c740189f28a861b6d45bef5ed4fe26a94ed2864e`.
Los dos RED de `--show` y el RED de relación compacta quedan verdes con los
cambios registrados; no cambia el lector, el scanner ni código de producción.
Cobertura del diff n/a: solo prosa y código de fixtures de prueba.

Dos checks independientes adicionales verifican GOT-017, sus cuatro campos,
unicidad, fuente e índice. Detectan una frase Minor en la ficha causal que
atribuía LF explícito también al README: se corrige a entradas sintéticas;
ambos revalidan el delta y aprueban con cero gaps. GOT-017 se promociona con
traza `aceptada (validada: revisión de dos lentes, 2026-10-08, intento 2)` en
su entrada e índice locales, ignorados por Git. No se promociona ninguna
otra propuesta. Esta entrada nueva es posterior a la fixture congelada de
52 archivos de QA; no se atribuye su validación a esa tanda.

Aceptación acotada: documentación, diagnóstico parcial y fixtures corregidas.
Sin nuevas skills, activación de backend, configuración del consumidor ni
cierre global de T-02/T-07/T-09/T-14/T-15. La auditoría completa de memoria,
el benchmark de Graphiti y la reproducción causal del cierre siguen abiertos.

### Puertas finales y límite del verificador de revisión

Lint final: cero errores, tres avisos históricos de nombres. La promoción de
GOT-017 requería entrecomillar `estado` por sus dos puntos internos; se corrige
solo esa serialización YAML y el lint vuelve a verde. Evals: 51 piezas,
182 casos, cero errores. Export --check: 56 archivos al día. Ledger: cero
incoherencias/cero avisos. Diff --check: exit 0. Scope contra `470e92e`:
18 archivos propios en alcance, cero fuera, settings ajeno excluido, cero avisos.
Scan público: 872 archivos, cero nombres/referencias prohibidos; excluye el
settings ajeno antes de leer. No se publica memoria local ignorada por Git.

Incidente acotado del selector: su invocación `--base 470e92e` incluye todos
los archivos sin seguimiento y lee indirectamente `.claude/settings.json`.
No se mostró su contenido ni se modificó o añadió al índice. Se detecta al
inspeccionar el verificador y se registra la lectura; no se afirma aislamiento
de ese comando inicial. La repetición usa `--files` con los 18 archivos propios
explícitos: C/D false, sin motivos ni avisos, excluyendo settings antes de
cualquier lectura. El aislamiento de las copias de QA sigue acreditado por
sus manifiestos; no se extiende esa afirmación al primer selector del workspace.

### Publicación verificada del Bloque 7

Commit de cambios y evidencia:
`80689b79e166415e19ebcf88b4039e27eae44546`, 18 archivos propios.
Push a `feat/catalog-capabilities` exit 0; `git ls-remote --heads origin`
confirma exactamente ese SHA. Tras el push, export --check sigue en exit 0
con 56 archivos al día. Solo permanece sin seguimiento `.claude/settings.json`;
no se modificó ni incluyó en los commits. GOT-017 e índice de memoria local
siguen fuera de Git; el incidente de lectura del selector consta arriba.

Este registro de entrega se incorpora en un commit documental separado.
No se declara cerrada la iniciativa ni se inicia otra fase en esta entrega.

## Bloque operativo 8 — cierre bajo carga y recuperación canónica

El usuario reactiva el objetivo completo tras la entrega `b8e6192`. El turno
anterior produjo progreso verificable: dos commits publicados y 438 tests verdes.
Skills aplazadas; foco hooks/comandos/panel/memoria. Tres auditorías independientes
en paralelo: causalidad del cierre, continuidad por comandos y gobierno local.
No leen settings ajenos, conversaciones o journals ni ejecutan código del corpus.

El contraste de cierre fija dos fixtures frescas y hooks completos iguales,
variando solo actividad de dos hijos nativos frente a raíz. La instrumentación
no corta el despacho del stub. Producción y límite de 3 s intactos hasta prueba
causal. Es diagnóstico privado, TDD n/a; resultados y límites pendientes.

Auditoría local identifica dos huecos funcionales: el corpus recuperado omite
`approved/` y el router pierde `version`. Diseño de extracción y contrato
aprobado en design.md. RED antes de producción: ocho fallos en
`tests/test_knowledge_approved_retrieval.py` (1,45 s), approved-only ausente,
show/related exit 1, fallback vacío, caché sin entradas y `KeyError: version`.
Segundo RED: nueve fallos de corpus inválido, ambigüedad, independencia de
config de servicio y traversal. Logs propios separados bajo
`scratchpad/.venv/memory-approved-retrieval/audit-red-20261008-01/` y `-02/`.
El diseño preserva legacy, estados y políticas de promoción; no activa backend.

RED adicional `-03`: dos fallos demuestran que configuración/enabled de backend
inválidos eliminaban la lectura local. RED `-04`: nueve fallos cubren categoría
con carpeta propia, prioridad de aprobado, enlaces explícitos fuera del área,
versiones remotas bool/list/dict/controladas y junction hacia candidatos.
Estos casos preceden sus correcciones; los logs anteriores quedan intactos.

### Contraste nativo bajo carga: resultado parcial

[Evidencia de carga](session-closure-load-evidence.json): cuatro fixtures propias
con Codex 0.161.0 y hooks completos. Los cuatro manifiestos contienen 326 archivos
idénticos, comprobados en distribución y caché. SessionEnd del plugin informa
`completed` en 1308/2338/1807/3075 ms; todos capturan un envelope de raíz correcto
antes de salir naturalmente con código 0. Se conserva el 3075 tal como lo devuelve
el runtime: no se declara cumplimiento estricto de tres segundos.

La primera muestra con dos hijos permite crear `src/architect.txt` protegido:
su guardia termina con entradas vacías después de expirar el presupuesto hijo,
sin job header registrado. El mismo payload evaluado directamente devuelve
deny. Hay líneas de trace intercaladas inválidas, preservadas con línea/hash;
la ausencia de un stage no se trata como prueba absoluta. Los controles
posteriores bloquean, pero varían turnos/tiempos y no prueban que cambiar de
intérprete resuelva el fallo. No hay cambio de launcher, supervisor o guardia.
La eficacia de guardias y la fiabilidad de cierre permanecen abiertas.

### Comparación de continuidad sin otro almacén

[Ficha de continuidad](comparisons/commands-session-continuity.md) y su evidencia
registran lecturas de cuerpos, recursos y contratos propios. Proponen una
fachada de retoma de solo lectura sobre journal/progress/ledger, con selección
exacta y pruebas históricas distinguidas del estado vigente. No está implementada,
no aumenta el conteo global de fichas ni crea aliases, servicios o fases nuevas.
Las lecturas parciales y la cadena secundaria pendiente quedan explícitas.

### Validación inicial conservada, sin aceptación prematura

La primera cobertura Windows del snapshot de fuentes propio mide 460/499 líneas
ejecutables añadidas (92,18 %). Ejecuta 407 passed/1 skipped/4 failed: tres fallos
son dependencias ausentes de la copia (`evals/check.py` para copias declaradas),
y uno hereda el Git ancestral de scratchpad. Esos resultados se conservan;
el harness siguiente necesita dependencias completas y un Git propio antes
de atribuir verde. El skip es una fixture symlink de Windows, por justificar
con su identidad exacta en la evidencia final. Linux, sin memoria real, pasa
las pruebas sintéticas de symlinks; los skips de corpus real no cuentan como
validaciones ejecutadas de ese corpus.

Lint del workspace detecta un alias `_TAXONOMY_FALLBACK` de compatibilidad sin
fila de registro en schema. Evals: 51 piezas/182 casos, exit 0. Export interop
--check: 56 archivos al día, exit 0. Portable privado: 189 archivos, check 0.
Ledger: cero incoherencias/avisos. Estas comprobaciones no sustituyen la QA
ni cierran la revisión del código; el lint rojo requiere corrección validada.

## Revisión de dos lentes — intento 1: Fase 2 (T-07, T-08, T-14, T-15) — Bloque 8

Lentes A+B+C por subagentes genéricos frescos: reviewer nativo no disponible;
tier frontmatter opus/high, sin override. Scope contra `b8e6192`: exit 0,
cero fuera/avisos; settings ajeno excluido. Selector con ocho archivos propios
explícitos, excluyendo settings antes de leer: C true por SQL f-string con
columnas constantes; D false. C verifica parametrización y contención sin
hallazgos. A ejecuta export --check (56 archivos, exit 0). QA final pendiente.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Recuperación, ID/version, categorías, enlaces, caché y respaldo local | ✓ | A/B leen diff completo y tests sintéticos; B ejecuta 36 passed |
| TDD y límites de evidencia/estado global | ✓ | RED previos conservados; ningún T global cerrado |
| Documentación bilingüe y generados | ✓ | Contrato/índices/FLOWS/changelogs; export --check 0 |
| Registro de alias de compatibilidad | ✗ | A reproduce lint rojo en schema |
| Nuevas aristas con puerta declarada | ✗ | A cita CONTRACTS regla de alta |
| Datos opcionales incompatibles degradan sin perder legado | ✗ | B reproduce TypeError en query con/sin índice |
| Helpers ausentes degradan sin traceback | ✗ | B contrasta CLI nuevo y base en kits propios |
| Seguridad introducida | ✓ | C: SQL parametrizado, rutas contenidas, lector sin red; 11 tests propios passed |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1-01 | Important | Alias `_TAXONOMY_FALLBACK` sin registro, schema:188 | T-07/T-15 | pendiente: binding declarado y test de identidad, sin copiar literal | lint dirigido y lint workspace rojo |
| A1-02 | Important | find/index/schema → helpers no están en CONTRACTS | T-08/T-15 | pendiente: filas de contrato con puerta | CONTRACTS:11–12 y diff |
| B1 | Important | `area: [test]` admitida en approved aborta también legado | T-07/T-14 | pendiente: validar campos usados por recuperación y degradar con motivo | reproducciones propias query/--no-index, find:549–552 |
| B2 | Important | Kit parcial sin nuevos helpers aborta al importar | T-07/T-14 | pendiente: carga y API/CLI con diagnóstico | index:90/schema:54; contraste exacto con base |

Fusión: cero Critical, cuatro Important, cero Minor. No se rebate ni rebaja
ninguno. Producción congelada durante revisión; la siguiente corrección exige
RED dedicado y otro intento antes de QA/entrega. Detalles privados A1/B1/C1
preservados, sin publicar payloads ni contenido del consumidor.

Jira del intento 1: plan `--event gaps --actor reviewer --task T-07,T-08,T-14,T-15
--intento 1 --batch --json`, exit 0; desactivado, `ops: []`. Nada publicado.
Corrección A1-02: CONTRACTS declara E25–E28 con firmas/resultados y suites
ejecutables; incluye la arista interna local → taxonomy además de las tres
aristas de consumidor. TDD n/a: documentación, pendiente revalidación A2.

### Corrección del intento 1 con RED dedicado

RED `-05`: trece fallos reproducen metadatos opcionales incompatibles en caché/
recorrido plano y imports de helpers ausentes. RED `-06`: el test A1 demuestra
la definición adicional del respaldo en schema. RED `-07`: cinco fallos de
evidencia y tags incompatibles completan la frontera de metadatos consumidos.
Logs originales separados y conservados. GREEN `-06`: 55 passed, 13,64 s.

A1-01 se corrige mediante reexportación estándar `__getattr__`: el wrapper
devuelve el mismo objeto del helper y no define otro respaldo. No se debilita
el registro ni se fabrica una segunda copia; template/helper siguen siendo
los únicos cuerpos comparados. El test dedicado verifica identidad y lint.
B1 valida forma de etiquetas consumidas solo al recuperar; el índice completo
conserva su política anterior. B2 captura carga fallida y devuelve diagnóstico
en API/CLI; sin helper no finge validación ni copia el parser.

Fuentes finales congeladas en `frozen-20261008-03`, con Git/HOME propios,
dependencias de copias declaradas y sin memoria real/bytecode. QA Windows con
JUnit y cobertura, QA Linux equivalente y revisión 2 siguen pendientes al
escribir esta nota. No se altera la evidencia de snapshots rechazados.

## Revisión de dos lentes — intento 2: Fase 2 (T-07, T-08, T-14, T-15) — Bloque 8 corregido

Lentes A+B+C por subagentes genéricos frescos; traspaso completo del intento 1,
sin reabrir aprobados ni hallazgos rebatidos (no hubo rebates). Scope exit 0;
C aplica por el SQL de columnas constantes, D false. A ejecuta export --check:
56 archivos al día, exit 0. Revisión anterior a la aceptación final de QA.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| A1-01: respaldo único y reexportación de compatibilidad | ✓ | A verifica identidad, ausencia de definición adicional y test de lint |
| A1-02: contratos nuevos declarados y vigilados | ✓ | E25–E28, nueve columnas, puertas y docs correspondientes |
| B1: metadatos inválidos conservan legado | ✓ | A/B: tipos solo include_source; B reproduce seis campos con/sin caché |
| B2: kit parcial sin traceback | ✓ | B: helpers ausentes, SyntaxError y RuntimeError, API/CLI con diagnóstico |
| TDD, docs bilingües, generados y límites globales | ✓ | A: RED -05/-06/-07, estados abiertos, --check 0 |
| Seguridad introducida | ✓ | C: rutas fijas, delegación limitada, schema completo intacto, SQL parametrizado |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1-01 | Important | Definición de respaldo adicional | T-07/T-15 | corregido | test A1; A2/B2 verifican forwarding al mismo objeto |
| A1-02 | Important | Nuevas aristas ausentes | T-08/T-15 | corregido | CONTRACTS E25–E28, A2 verifica formato/puertas |
| B1 | Important | Listas opcionales abortan recuperación | T-07/T-14 | corregido | tests B1; 21 escenarios B2, 19 tests dirigidos A2/B2 |
| B2 | Important | Imports parciales abortan CLI | T-07/T-14 | corregido | tests B2 y fixtures independientes ausente/roto |

Fusión: cero Critical/Important/Minor pendientes. C2 ejecuta 30 passed/25
deselected en HOME propio; no confunde esa selección con la QA completa.
No se promueve memoria ni se cierra ningún T global de esta iniciativa.

### QA final del Bloque 8

[Evidencia de recuperación](memory-approved-retrieval-evidence.json): Windows
**430 passed/1 skipped**, 431 casos parametrizados y 377 identidades padre;
Linux **405 passed/20 skipped**, 425 parametrizados y 384 identidades padre;
paquete portable **15 passed**, cero skips. Cada cohorte tiene qa-gate VERDE,
cero fallos/errores/flaky. Son suites dirigidas que se solapan entre plataformas;
no se suman como tests únicos ni se presentan como toda la CI.

Windows: Python 3.13.0/pytest 9.1.1/coverage 7.16.2, 220,73 s. Su único skip es
`test_gap6_symlink_fuera_de_la_carpeta_aprobada_falla`, por permisos de symlink;
las junctions propias y los symlinks Linux sí pasan. Los skips Linux requieren
memoria real deliberadamente ausente: no acreditan validación de ese corpus.
Linux: Python 3.11.16/pytest 9.1.1, 29,30 s, imagen propia fijada y red `none`.
Ambas copias contienen exactamente las mismas 477 fuentes del manifiesto final;
los ocho archivos implementados coinciden con sus fuentes actuales. Homes, TMP,
Git y datos de memoria son propios; no settings o servicios del consumidor.

Cobertura oficial del diff: **473/524 líneas ejecutables añadidas = 90,27 %**,
supera el gate global ≥90 %. Las métricas por módulo se conservan sin inflarlas:
los tests de wrappers parciales ejecutan copias byte idénticas fuera del filtro
de fuente canónica, por lo que sus ramas no se atribuyen a esos módulos. No se
afirma ≥90 % por archivo. Los rojos y resultados rechazados anteriores siguen
identificados con hashes; los nuevos artefactos no los sobrescriben.

Comprobaciones de entrega: lint workspace cero errores/tres avisos históricos,
evals 51 piezas/182 casos y cero errores, interop 56 archivos al día, ledger cero
incoherencias/avisos. Portable: 189 archivos/check 0 y ambos helpers byte idénticos.
La copia de entrega tiene un cuarto aviso de modo ejecutable de hooks.json
por metadatos de su Git vacío/NTFS; se conserva el log. El Git real declara su
modo correcto y el lint real da los tres avisos anteriores, sin cambiar modos.
Scan inicial de 874 fuentes públicas propias: cero referencias/nombres vetados;
settings y memoria local se excluyen antes de leer. Evidencia final añadida
después de esa copia; su scan y revisión de consistencia quedan para la entrega.

Aceptación acotada: recuperación aprobada corregida, distribución validada,
documentación y comparación/diagnóstico con límites explícitos. El fallo de
guardia bajo carga, la eficacia nativa de memoria, benchmark Graphiti, propuesta
de retoma y comparación general siguen abiertos. Nuevas skills aplazadas.
Publicación pendiente al escribir este bloque; no se inicia otra fase.

Jira del intento 2: `--event revision --actor reviewer --task T-07,T-08,T-14,T-15
--intento 2 --batch --json`, exit 0; desactivado, `ops: []`. Nada publicado.

### Consistencia y puertas antes de publicar

Dos controles independientes frescos de la evidencia final verifican hashes,
477 fuentes, mapas Windows/Linux, ocho fuentes actuales, XML/padres/skips,
gates derivados de resultados reales y portable. Recalculan cobertura desde
diff y JSON oficial: 473/524, 90,27 %, sin discrepancias ni gaps nuevos.
No repiten suites ni ejecutan builders que reescriban evidencia.

Scan final de 875 archivos públicos propios: cero referencias/nombres vetados;
settings ajeno y memoria local excluidos antes de cualquier lectura. Los ocho
hashes implementados siguen iguales al snapshot validado. Git declara
hooks.json `100644`. Scope final: 26 archivos propios en alcance, settings
excluido, cero fuera/avisos. Selector solo con ocho paths propios: C true por
SQL de columnas constantes, D false, cero avisos. Ledger y diff --check: exit 0.
La rama remota sigue en la base `b8e6192` antes de publicar; no hay cambios
ajenos staged. Tras entregar los commits y verificar el remoto, se detiene
este bloque conforme a la instrucción del usuario. El objetivo global no se
declara completado y esta entrega no inicia otra fase.

El check del índice al añadir helpers nuevos detecta dos líneas vacías al EOF,
sin espacios finales ni defecto funcional. Se conserva ese diagnóstico y se
comprueba con `git -c core.whitespace=-blank-at-eof diff --cached --check`:
exit 0. La excepción es solo para esa preferencia de estilo y solo por llamada;
no cambia configuración, fuentes validadas, gates del plugin ni sus hashes.

### Publicación verificada del Bloque 8

Commit de implementación/documentación/evidencia:
`e6fc5ff2a37a854ee0a2ccfcd5c7cb56abeb7640`, 26 archivos propios.
Push a `feat/catalog-capabilities` exit 0; `git ls-remote --heads origin`
confirma exactamente ese SHA. Solo queda sin seguimiento el settings ajeno;
no se modifica ni añade. Memoria local, fuentes de investigación, fixtures y
artefactos privados permanecen fuera de Git.

Este registro de entrega se incorpora en un segundo commit documental.
Al verificar su push, se detiene el trabajo a petición del usuario. No se
declara completa la iniciativa: quedan los pendientes y límites registrados
arriba, sin comenzar otra fase ni añadir skills nuevas.

## Bloque 9 — Entrega de guardia y diagnóstico acotado (2026-10-09)

El usuario reanudó el trabajo pendiente. Base `f3e594a`; T-02/T-09/T-14/T-15
siguen abiertas y nuevas skills aplazadas. El diseño de este bloque separa
entrega explícita de decisiones y eficacia bajo carga.

**RED real antes del código:**
`node --test --test-name-pattern='spawn failure|empty successful evaluator|evaluated denial' tests/hook-guard-delivery.test.mjs`
terminó con 8 failed/1 passed. Python ausente/spawn fallido y respuesta vacía
produjeron `Unexpected end of JSON input` en los tres runtimes; Claude/Codex
no convirtieron el resultado estructurado al deny nativo esperado. Los fixtures
solo contienen payloads propios. Primer verde de desarrollo: 39/39 casos de
entrega; ampliación de casos adversos y QA final en progreso.

El launcher pide `--output structured`, acota stdout a 16 KiB, valida un único
objeto y entrega como máximo una respuesta. Una decisión de bloqueo completa
se conserva incluso ante timeout o salida fallida posterior; una continuación
necesita terminar normalmente. Supervisión inválida invalida ambas. Errores,
ausencia o resultado incompleto degradan con aviso estable, sin revelar payload
ni diagnóstico libre del proceso y sin conceder permisos adicionales.

Scope-check inicial base f3e594a: 8 archivos propios en alcance, cero fuera/cero avisos;
settings ajenos excluidos por defecto. Selector con `--files` explícitos: A+B,
C/D false, cero avisos; no inspecciona settings ajenos. Exportador comprobado:
56 archivos al día. Tier reviewer frontmatter opus/high; el runtime ofrece
subagentes genéricos como fallback de revisión, sin override de modelo.

Comparación privada acotada: cuatro pares, dos de arranque Python y dos del
launcher real instrumentado. Venv 116,8/102,8 ms frente a base 83,1/66,2 ms;
launcher venv 854,2/819,6 frente a base 740,8/708,9 ms. Los cuatro guards
produjeron deny/exit 0. El snapshot de ascendencia sólo ocurrió en venv y
tardó aproximadamente 10–11 ms. No hubo carga impuesta ni despacho nativo
Codex, y no se reprodujo el fallo de 4.500 ms: no justifica cambiar intérprete
o presupuesto. `analysis-v2.json` sustituye un campo derivado incorrecto del
análisis inicial; se conservan ambos y no se usa el inicial como evidencia.

## Revisión de dos lentes — intento 1: bloque 9

A+B en paralelo, contexto fresco; C/D no activadas por selector explícito.
A: nueve criterios conformes, export --check exit 0/56 archivos al día.
B encontró un Important reproducible; no otros defectos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Razón deny válida con caracteres suplementarios rechazada por límite UTF-16 | T-09 | Contar puntos de código como el evaluador Python; pendiente segunda revisión | RED: 3 failed/0 passed en `supplementary Unicode` antes del fix; evaluador real del revisor deny con 1.189 puntos/2.189 unidades |

Jira deshabilitado: no se publican operaciones externas. Desarrollo ampliado
antes de este fix: 72 passed (69 nuevos + 3 adaptador), cero fallos, 115,86 s.
Estos resultados no constituyen QA de la corrección Unicode.

## Revisión de dos lentes — intento 2: bloque 9

A+B frescas revalidaron el delta Unicode y conservaron los criterios aprobados:
cero Critical/Important/Minor. Ambas ejecutaron independientemente seis casos
de frontera Unicode, todos verdes; A comprobó export --check exit 0/56 archivos.
El Important del intento 1 queda corregido. Jira `revision`, intento 2: exit 0,
`jira: desactivado`, `ops: []`. No se cierra ninguna tarea global.

### QA final del bloque 9

Fuentes congeladas: 876 archivos, manifest
`614ea558238b5131fe1f0f055b4786ccad124e9822d58363fcf3f8e780b614bf`.
Launcher `0b6b2f8a16721ef742e2c4bf3d6bb4bef9e4868e1e38f9f8b420c98b85bd0077`;
test de entrega `3454698bc9a0ea5051327362af94f80e775cc1f0e2f6ea6d454c28d8baffd49c`.
El gate de alcance antes de QA comprendía diez archivos propios, cero fuera,
sin avisos y settings ajenos excluidos. Evidencia y prioridades amplían sólo docs.

| Plataforma | Runner | Resultado final |
|---|---|---|
| Windows, Node 23.8.0 / Python 3.13 | Node, cuatro suites | 115 passed, cero fallos/skips |
| Windows | pytest, cinco suites | 276 passed, cero fallos/skips |
| Linux, imagen propia Python 3.11.16 / Node 22.23.3 | Node, cuatro suites | 103 passed, 12 skips de casos exclusivos de Windows |
| Linux | pytest, cinco suites | 276 passed, cero fallos/skips |

JUnit real convertido al formato del qa-gate: VERDE en las cuatro cohortes.
Las identidades de casos no se suman entre plataformas como casos únicos.
Cobertura V8: 51/55 líneas añadidas significativas, 92,73 %. Proyección de
rangos oficiales al primer offset UTF-16 de cada línea, no cobertura de
sentencias/ramas Istanbul; denominador/método/líneas descubiertas preservados.
No se repite para inflar el resultado tras superar el gate del diff ≥90 %.

La primera tanda Linux no ejecutó tests por el entrypoint heredado del helper.
La segunda conservó 92 passed/11 failed/12 skipped con checkout shell Windows;
la tercera, con LF canónico, 102 passed/1 failed/12 skipped. El único fallo
restante estaba en el oráculo de existencia de PID de limpieza, línea 271,
sin init en el contenedor. La cuarta usó init y pasó ambos runners, pero falló
la copia de symlinks de fixtures a Windows. La quinta conserva los informes
JUnit finales, exportando sólo artefactos necesarios. Todas permanecen privadas.
Los ocho shell normalizados coinciden exactamente con los blobs Git de la base
y con `.gitattributes`; los demás bytes, incluido launcher, coinciden con
Windows. Linux usa red none, HOME/Git propios y verifica los 876 hashes antes
de ejecutar. No se oculta un fallo del runner como test omitido.

Lint del snapshot: cero errores/cuatro avisos (tres nombres históricos y uno
por Git vacío/mode NTFS del JSON). Lint del árbol real: cero errores/tres avisos
históricos. Evals: 51 piezas, 182 casos, cero errores. Interop: 56 al día;
ledger-lint: cero incoherencias/cero avisos.

Prueba nativa Codex 0.161.0: una cohorte raíz propia con los seis eventos,
proveedor loopback sin Authorization y un guard privado retrasado ocho segundos.
PreToolUse plugin completed, 5.719 ms; entrada `warning` con el aviso exacto
del launcher; parche permitido bajo permisos normales. 328 archivos de
distribución/cache verificados, una sustitución explícita del negocio y ningún
instrumento en producción. Salida natural 0, sin cleanup forzado. Esta prueba
acredita entregar el aviso, no eficacia del evaluador/hijos ni cierre bajo carga.

Evidencia pública: [guard-delivery-evidence.json](guard-delivery-evidence.json)
y [guard-warning-native-evidence.json](guard-warning-native-evidence.json).
El gotcha Unicode GOT-018 y su fila del índice nacieron localmente como
propuesta. Dos auditorías independientes finales validaron los cuatro campos,
fuentes, RED/GREEN, casos finales y correspondencia del índice, sin hallazgos;
se acepta sólo esta entrada propia con la traza de revisión del intento 2.
`docs/knowledge/` sigue fuera de Git por la política del repositorio.
No se promociona memoria anterior ni se publica a un backend.

Auditorías documentales A/B finales: cero discrepancias. Verificados los cuatro
JUnit/gates, manifests, ocho excepciones LF, 146 muestras V8, denominador y
hashes públicos/privados de la prueba nativa y comparación de arranque. No
ejecutaron suites ni leyeron payloads/protocolos crudos, settings o memoria ajena.
Scan final: 878 archivos públicos, cero referencias/nombres prohibidos; fuentes
de launcher/test siguen idénticas al snapshot. Scope final: trece archivos
propios, cero fuera/cero avisos, settings excluidos antes de leer. Diff limpio.

Publicación: los dos JSON públicos se escriben con LF para que sus hashes
coincidan con los blobs Git. La proyección nativa privada conserva CRLF y
hash propio; su copia pública sólo normaliza finales de línea, con datos JSON
idénticos. La evidencia separa ambos hashes y no afirma igualdad de bytes.

### Checkpoint de entrega del bloque 9

Commit funcional/documental `e488f23f03eef1f3fc84bc0e5183a279310f4863`:
trece archivos, decisiones explícitas, 75 casos nuevos, evidencia de QA y
aviso nativo. Los JSON publicados conservan LF y sus hashes coinciden con
Git; código/tests siguen idénticos a las fuentes verificadas. Este segundo
commit registra el checkpoint antes de publicar ambos en la rama autorizada.
No PR, merge, release ni modificación de settings del consumidor.

Pendiente de la iniciativa: fiabilidad del arranque de guardia y cierre bajo
carga nativa, retoma de comandos, controles de panel y medición de memoria
opcional. Las nuevas skills permanecen aplazadas. El bloque de entrega de
decisiones queda validado; la iniciativa y T-02/T-09/T-14/T-15 siguen abiertas.

## Bloque 10 — Aislamiento causal de latencia de hooks (2026-10-09)

El usuario autoriza el punto 1: hooks bajo carga. Base `e7160f4`, alcance inicial
de investigación: fixtures privadas y este diseño/ledger. Nuevas skills y otras
fases aplazadas. No se tocan settings del consumidor, instalaciones reales,
credenciales ni memoria anterior. Durante el diagnóstico inicial, producción
conserva sus bytes y presupuestos; las correcciones posteriores se detallan abajo.

Dos comprobaciones independientes en paralelo: réplica nativa Codex completa y
auditoría de fuentes del launcher/supervisor/captura y contrato nativo pinned.
Las trazas se separan por proceso y módulo para eliminar corrupción por escrituras
concurrentes; el coste de escribir la propia traza permanece como hipótesis.
Límite de contraste inicial: dos cohortes, con los datos de la primera antes
de elegir la segunda. Los resultados y los errores del reducer se conservan;
una proyección corregida recibe versión nueva, sin sustituir la original.

La aceptación exige efecto de guardia por rol, control permitido y envelope
correcto antes de salida natural. `completed` no basta para acreditar captura;
la duración nativa y su timeout tienen instantes iniciales diferentes.
No se cierra T-02/T-09/T-14/T-15 ni la iniciativa por este diagnóstico.

**RED: antes de modificar el lector de rama**, `pytest` sobre
`test_guardrail_check.py` y `test_native_guardrail.py` con `-k unborn`:
8 failed, 254 deselected, 7,57 s, 2026-10-09. En main y feature sin commits,
`current_branch` devolvió None y los tres evaluadores entregaron
`branch-unavailable`. Esto omite protección de main aunque el HEAD simbólico
sea válido. Scope añadido: `agent-kits/shared/guardrail-check.py` y los dos
tests citados; consulta alternativa dentro del mismo presupuesto, sin cambiar
timeouts ni selección de Python.

GREEN de desarrollo del detector: 12 passed, 253 deselected, 8,58 s. Incluye
los ocho casos RED, timeout original, presupuesto restante/exhausto, HEAD
detached y ausencia de repositorio. No constituye todavía QA del bundle.

**RED antes del preflight:** `node --test tests/hook-post-preflight.test.mjs`
exit 1, 2026-10-09. Los casos de edición no aplicable fallaron al exigir stderr
vacío: el launcher intentó arrancar Python ausente y emitió `ENOENT`, por ejemplo
al editar `src/app.py` para `mark-docs-pending.sh`. Los controles aplicables y de
entrada desconocida conservaron el intento de ejecución. Scope añadido:
`hooks/run-hook.mjs`, `tests/hook-post-preflight.test.mjs`, documentación de
hooks ES/EN y changelogs; la forma exportada de registros no cambia.

Primer GREEN de desarrollo preflight: 42 passed, cero fallos, 38,35 s.
RED adicional de ruta multilínea: tres fallos reales en Claude/Codex/OpenCode,
`tasks.md\nsrc/app.py` se saltó como no aplicable pese a que el shell descompone
líneas. Esas rutas pasan a entrada desconocida y mantienen el camino anterior.

GREEN de ruta multilínea: tres passed, cero fallos, 2,47 s. Puerta previa a
revisión: scope-check base e7160f4 exit 0, once archivos propios en alcance,
cero fuera/cero avisos; settings ajenos excluidos por defecto antes de leer.
Selector con once `--files` propios explícitos: C/D false, cero avisos. Export
--check exit 0, 56 archivos al día. Registros generados sin delta: los scripts
compartidos se distribuyen directamente. T-09 declara `interop/**`.

## Revisión de dos lentes — intento 1: bloque 10

A+B en paralelo, contexto fresco, subagentes genéricos por disponibilidad del
runtime; reviewer frontmatter opus/high, sin override. A aprobó los ocho criterios
de conformidad y ejecutó export --check exit 0/56 archivos. C/D no activadas por
selector explícito. B encontró un Important reproducible, ningún otro defecto.
QA/cobertura/aceptación nativa del nuevo diff siguen pendientes.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B-1 | Important | Regex JS omite ledger/progreso en carpeta con U+2028/U+2029 que acepta el glob shell | T-09 | Corregido por comparación literal; pendiente segunda revisión | Reproducción B y RED seis failed/cero passed; mismos seis GREEN en los tres runtimes |

Jira gaps intento 1: exit 0, desactivado, `ops: []`. RED dedicado B-1:
`node --test --test-name-pattern='[\u2028\u2029]' tests/hook-post-preflight.test.mjs`
seis failed/cero passed, antes de cambiar producción. Una selección previa con
`.*` seleccionó otros nueve casos ASCII/multilínea verdes, sin seleccionar los
Unicode: no se usa como evidencia del gap. La fixture del test ahora deja PATH
propio sin Bash además de Python ausente para que el oráculo de intento de
dependencias sea portable a Linux, sin ejecutar negocio ni modificar su contrato.

GREEN B-1: seis passed/cero fallos, 3,53 s. Se conservan presupuestos, separación
de handlers y fuente shell de negocio. La segunda revisión fresca está en curso.

## Revisión de dos lentes — intento 2: bloque 10

A+B frescas conservaron los ocho criterios aprobados y verificaron B-1 corregido;
cero Critical/Important/Minor. A ejecutó export --check exit 0/56 al día y
selección Unicode exacta seis passed/cero fallos. Una selección inicial propia
de A ejecutó el archivo completo (51/0); no se presenta como selección Unicode
ni QA. B ejecutó 51/51 y nueve controles adicionales Unicode no aplicable/CR
desconocido en los tres runtimes, todos verdes. Sin reapertura de lo aprobado.
Se permite pasar a QA del snapshot y aceptación nativa; ninguna tarea global
se cierra en este pase. Jira por intento 2 se verifica antes de QA.

Jira revisión intento 2: exit 0, desactivado, `ops: []`. Snapshot inicial QA:
879 archivos, manifest `c5991285c0ca83e4e7d22f0fda45d77e06c0efb89edc0d50899614e741917d8d`.
Node Windows terminó exit 0 en 261.407 ms. Python conservó 286 passed/1 failed:
el test nuevo de ausencia de repo encontró el Git del workspace padre al usar
basetemp dentro de él. Es un defecto de aislamiento de fixture, no una regresión
del lector. La prueba acota descubrimiento con GIT_CEILING_DIRECTORIES propio;
la primera cohorte se conserva. Producción y tests Node no cambian. Se repite
Python y se valida Linux con esa fixture, sin repetir Node Windows ya verde.

### Resultado del diagnóstico y límites

La [proyección del diagnóstico](hook-load-diagnosis-evidence.json) conserva las
dos cohortes instrumentadas y sus límites. Al mover únicamente las escrituras
de trazas/observador a TEMP propio, la guardia raíz pasó de 9.221 ms con aviso a
2.936 ms sin aviso. El evaluador había entregado stdout completo a los 381 ms
en la primera cohorte; ese instante no acredita la salida del proceso. Los
PostToolUse que alcanzaron el deadline de limpieza bajaron de 8/9 a 4/9.
Persisten latencias y confusores: una observación por variante no demuestra
una causa única ni un arreglo universal. El probe aislado de limpieza no
reprodujo la hipótesis de proceso huérfano. No se aumenta ningún timeout ni
se cambia el intérprete por estas mediciones. SessionEnd dejó envelope raíz
válido antes de salida natural en ambas cohortes instrumentadas.

SHA-256 de la proyección del diagnóstico:
`0fb7cb439efb1aaefbc33e70a3c003672c09f6095ddc8fdc9193adeec48ae491`.
Las proyecciones privadas anteriores con colisión de etiquetas/asociación de
PID quedan conservadas y rechazadas; la aceptada delimita cada ciclo de proceso.

### QA del diff final

La [evidencia de QA](hook-reliability-qa-evidence.json) identifica el snapshot
final de 879 archivos, manifest
`d928d1af878e029832ec2595f9634a2972c3b2a03c8ad4c0e488564c7d5f7490`.
Windows: Node 166 passed/cero fallos/cero skips; Python 287 passed/cero fallos.
Linux: Node 154 passed/cero fallos/12 skips exclusivos de Windows; Python
287 passed/cero fallos. Cuatro JUnit reales dan qa-gate GREEN. Los casos no
se suman entre plataformas. Node Windows se reutiliza sólo tras comprobar
identidad de todos los bytes de producción y tests Node; el único delta del
segundo snapshot es la fixture Python y este ledger. Linux usa los ocho shell
con LF canónico de Git, sin otras diferencias respecto al snapshot Windows.

Cobertura de líneas añadidas: V8 37/37 (100 %, unión de 197 muestras), una
proyección de rangos nativos que no representa statements/branches de Istanbul;
Coverage.py 7/7 statements ejecutables añadidos (100 %). Ambos gates de diff
superan 90 %. Lint/evals/export/ledger exit 0; 51 piezas/182 casos de activación,
56 archivos interop al día. El snapshot congelado añade un aviso de modo JSON
por su Git vacío/NTFS a los tres nombres genéricos previos; no se cambia chmod.

SHA-256 de la proyección de QA:
`a2c03816127d74dd1871829f6af1884cabf1fbc14b9c1bb505b3c49c6b5a31f5`.

### Aceptación nativa del bundle sin instrumentar

La [evidencia nativa](hook-native-acceptance-evidence.json) usa ese snapshot,
binarios Windows pinned y proveedor sintético loopback sin Authorization.
Ocho ejecuciones seriales finalizaron exit 0, sin limpieza forzada, cambios
de fuentes ni hooks observadores adicionales. Las versiones son Codex 0.161.0,
Claude 2.1.287 y OpenCode 2.0.12; hashes de binarios/helpers/resultados en JSON.

- Codex: una raíz con implementer y architect reales, cuerpos TOML completos
  reconocidos e identidades nativas distintas. Cinco decisiones de guardia
  coinciden con el efecto esperado (dos bloqueos, tres permitidas). SessionEnd
  nativo al archivar deja envelope schema 1, secuencia entera positiva e ID raíz
  correcto, observado antes de la salida natural del app-server.
- Claude: cinco procesos propios separados (raíz y deny/allow de cada rol),
  cuerpos exportados completos y deny nativo en los dos casos protegidos.
  Cada caso deja captura raíz válida antes de la salida natural. Esta matriz
  no demuestra ejecución simultánea de ambos roles.
- OpenCode: siete casos directos y cuatro raíces con un hijo real cada una;
  parentID/agente/outcome correctos, cuerpos completos, escrituras protegidas
  impedidas y controles permitidos. La captura se observa durante execution/idle,
  con servidor vivo: no equivale a un evento nativo SessionEnd en teardown.
  Una captura aún tenía nombre temporal al observarse; no se acredita publicación
  canónica ni replay completado de ese caso.

La ausencia de Authorization del proveedor es una comprobación medida; no se
afirma captura global de tráfico saliente. Estos casos reproducibles acreditan
el contrato ejercitado, no un soak test de TUI en producción ni una garantía
de latencia bajo cualquier carga. T-02/T-09/T-14/T-15 y la iniciativa siguen
abiertas; las siguientes fases y skills permanecen aplazadas.

### Contraste factual final y estado de entrega

Dos auditorías independientes finales verificaron hashes, JUnit, reutilización
de Node, EOL Linux, método de cobertura y límites del diagnóstico/nativos;
cero hallazgos pendientes en el diff. El contraste OpenCode de sólo lectura
añade cuatro registros nativos de guardia `executed:false`/error con alcance
correcto. Diez capturas conservan nombre canónico y una, temporal completo;
el JSON explicita la frontera de publicación/replay. SHA-256 nativo final:
`3cdab6f57c4af3458ee52a796a94128640ca46996158f715d0af39f590b41e67`.
La corrección de aislamiento de fixture y la nota GOT-019 propia también
fueron contrastadas; sólo esa nueva nota/fila local pasa a aceptada, sin
publicación de memoria ni incorporación a Git.

El lint por defecto del workspace devolvió exit 1 por un escalar YAML con
`: ` en una nota local anterior GOT-018, ignorada por Git y ajena al diff;
no se modifica esa memoria. Esto no se presenta como lint local verde.
El bundle público congelado excluye memoria local/config/fixtures antes de
leer y conserva lint exit 0. El ledger actualizado da cero incoherencias/cero
avisos y export --check conserva 56 archivos al día.

Se entrega este diff acotado de hooks con sus evidencias. Quedan abiertas
la extrapolación de carga/TUI y publicación canónica del caso temporal de
OpenCode; no se atribuye cierre completo de fiabilidad ni de T-09. Comandos,
dashboard, memoria opcional y las nuevas skills no avanzan en este bloque.

Puerta final del código público: lint del snapshot con documentación actualizada
exit 0/cero errores/cuatro avisos descritos, scope-check base e7160f4 exit 0:
catorce archivos propios en alcance, cero fuera/cero avisos; settings ajenos
excluidos antes de leer. Escaneo de 882 archivos públicos: cero referencias o
nombres prohibidos. Producción y tests conservan los hashes del QA final.
Destino autorizado: commit y push a `feat/catalog-capabilities`, sin integración
en main ni publicación de versión. La nota local GOT-019 queda fuera de Git.

## Bloque 11 — Publicación canónica de la captura (2026-10-09)

Retoma del objetivo activo tras entregar `2a010a2`; prioridad de hooks y skills
aplazadas conservadas. El caso temporal de OpenCode se investiga antes de
cambiar producción. El bundle y sus presupuestos mantienen sus bytes.

La auditoría de sólo lectura confirma: el observador privado abría también
`.tmp-*` mediante `glob('*.json')`. La matriz anterior acredita seis capturas
canónicas y una temporal completa, no siete publicaciones atómicas. El JSON
anterior conserva ese límite; sus resultados históricos no se sobrescriben.

Hipótesis competidoras: terminación del hook durante flush/fsync/close/rename;
o fallo de rename y limpieza por un lector Windows sin permiso de borrado.
El observador incorrecto podría interferir con el escritor. El temporal por
sí solo no distingue estas causas; la salida natural del servidor tampoco
acredita salida natural de todos sus hooks hijos. Un OSError de fsync aislado
no explica falta de rename, porque el escritor degrada y sigue publicando.

Dos trabajos independientes en paralelo, sólo en fixtures privadas propias:
criterio canónico estricto con RED previo, y probes atómicos de las dos
hipótesis con controles. El criterio excluye temporales antes de abrirlos,
exige `<event_id>.json`, schema/secuencia/raíz correctos y observación con
servidor vivo; contempla outbox/processing/done. Una matriz nativa corregida
se permite sólo tras preparar y auditar ese criterio. No se incrementan
timeouts, se retira fsync ni se promocionan temporales arbitrarios por su JSON.

### Resultado medido

[Evidencia de publicación canónica](hook-canonical-capture-evidence.json),
SHA-256 `effb1eac12de8b778e0cd7259e3a979e0599189b3987cfb7e7628f0ce111840b`.
Caracterización del observador anterior: 16 controles, ocho fallos y un error;
incluye aceptación indebida de temporal completo y lectura de nombre no
publicado. Observador estricto: los mismos 16 controles pasan, sin lanzar
runtime; su función coincide por AST con la embebida en el helper nuevo.

Probe de lector Windows: un handle propio sin FILE_SHARE_DELETE provoca error
32 en rename y limpieza, dejando un temporal completo. Control de fallo de
rename con limpieza disponible: ningún temporal; control de OSError en fsync:
publicación canónica y marcador degradado. Probe independiente de hard stop:
worker propio bloqueado tras flush, terminado por su handle Popen y confirmado
terminal; temporal completo sin publicación. Liberar la barrera publica.
El worker usa el intérprete base fijado para evitar matar sólo el redirector
venv; no cambia la selección de producción ni mide el launcher. El probe de
launcher queda preparado, no ejecutado. Ambos mecanismos son reproducibles;
ninguno queda demostrado como causa histórica del caso anterior.

La única cohorte nativa nueva usa OpenCode 2.0.12 y la misma fuente congelada
de 879 archivos del QA previo. Siete casos exit 0 en 135.055 ms, siete nombres
canónicos en outbox observados con servidor vivo, schema 1, secuencia entera
positiva y sesión raíz correcta. Cuerpos exportados completos y 94 hashes de
fuente actual/congelada/instalada coinciden. Deny/allow por rol, control raíz,
planner y agente homónimo del consumidor conservan sus efectos. Salida natural
del servidor, sin limpieza forzada ni Authorization del proveedor; sin hooks
observadores adicionales. No se repiten Codex/Claude ni se cambian sus evidencias.

Una copia aislada del checkpoint sintético del planner anterior permite
`journal.py recover --session-id <id propio> --budget-ms 3000 --max 1`:
exit 0, una candidata/una recuperada en 511 ms. Entrada `fuente: recover`,
`cierre: recuperado_sin_cierre`, sesión coincidente; originales y checkpoint
de copia conservan su hash. No se renombra/promociona el temporal anterior ni
se convierte recuperación en cierre observado. Se usa recuperación explícita
de una sesión conocida como terminada, sin saltar la guarda de sesiones vivas
en la recuperación implícita.

No hay fix de producción en este bloque: el defecto probado era del criterio
de aceptación privado y queda corregido en una fixture nueva, conservando la
anterior. TDD de producción y alta de memoria técnica no aplican. Cambios
públicos: evidencia, diseño y estado verificable del ledger; ninguna skill,
agente, comando, backend, instalación del usuario o configuración ajena cambia.
La iniciativa permanece abierta. Siguiente integración de hooks: preservar
verificación de commit frente a bypass, bajo `guardrails.git` e IDs protegidos.

## Revisión de dos lentes — intento 1: bloque 11

A+B frescas en paralelo, fallback a reviewer genérico por disponibilidad;
tiering del frontmatter opus/high, sin override. A verifica conformidad y
evidencia por criterio; B contrasta hashes/AST, siete capturas físicas y dos
errores nativos de guardia en SQLite propio de sólo lectura. Ambas: cero
Critical/Important/Minor. C/D no activadas por selector de tres archivos
documentales explícitos, cero avisos. Jira revisión: exit 0, desactivado,
`ops: []`; no publicación externa.

Lint del bundle público con documentación actualizada: exit 0/cero errores,
los cuatro avisos ya descritos; no se afirma lint local por defecto verde.
Ledger: cero incoherencias/cero avisos. Export --check: 56 al día. Alcance
base 2a010a2: tres archivos propios, cero fuera/cero avisos; settings ajenos
excluidos antes de leer. Escaneo de 883 archivos públicos: cero referencias
o nombres prohibidos. No se repiten suites de producción para este diff
documental: los 94 archivos nativos y la fuente del QA conservan su hash,
con excepción esperada del propio diseño/ledger que describen este bloque.
Se permite commit/push acotado a la rama autorizada; la iniciativa queda abierta.
