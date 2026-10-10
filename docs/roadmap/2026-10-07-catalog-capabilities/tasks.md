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
- **Archivos**: `tests/**`, `evals/**`, `docs/roadmap/2026-10-07-catalog-capabilities/**`
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

La integración global sigue abierta. Las skills permanecen aplazadas en 79/293 evaluadas.
La siguiente prioridad es la revisión visual de planes en el panel y su consumo desde la puerta «OK del plan».
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


## Bloque18 — QA final aceptada y cierre de implementación

Tras el tercer pase independiente sin gaps nuevos o reabiertos, ambas ejecuciones finales terminaron con exit 0, conservando los mismos handles y sin reinicios. La raíz comprobó 172 artefactos sellados y 1.422 filas E43–E47 contra identidad, índice, estado y SHA de seis JUnit reales. Los 21 artefactos originales NO-PASS permanecen intactos.

| Plataforma/cohorte | Passed | Failed | Skipped | Subtests raw |
|---|---:|---:|---:|---:|
| windows/local-state | 956 | 0 | 19 | 0 |
| windows/router-code | 1023 | 0 | 21 | 39 |
| windows/documental-panel | 539 | 0 | 3 | 6 |
| linux/local-state | 974 | 0 | 1 | 0 |
| linux/router-code | 1023 | 0 | 21 | 39 |
| linux/documental-panel | 541 | 0 | 1 | 6 |

Totales JUnit: Windows 2.518 passed/0 failed/43 skipped; Linux 2.538/0/23. CLI auxiliares: 6 Windows y 8 Linux; los qa-gates incluyen esas CLI y son VERDE. Subtests, plataformas y cohortes históricas no se suman como casos únicos.

| Plataforma | Media de los diez archivos cambiados | Ejecutables añadidas/cambiadas | Gates |
|---|---:|---:|---|
| windows | 91.127209834166% | 1255/1333 = 94.14853713428357% | PASS ambos ≥90% |
| linux | 91.37956456318409% | 1255/1333 = 94.14853713428357% | PASS ambos ≥90% |

Coverage.py oficial y diff OWN del snapshot revisado; sin redondeo para aceptar, sin cambiar selección/umbrales ni asumir cobertura de hijos. Es media por archivo, no afirmación de que cada archivo individual supere el 90%. Lint/evals/export/ledger pasan. coverage-check auxilia solo: defined/referenced vacíos no acreditan cobertura del test-plan macro ni cierran tareas.

Las regresiones de servidor/controles del panel están incluidas. No hubo nueva navegación ni Playwright; Chrome7 anterior sigue siendo checkpoint histórico. Las aceptaciones nativas documental de diez módulos y AST portátil de cinco módulos son evidencia separada vinculada al código actual; no se repitieron modelos durante QA. Los 970 hashes de fuente y copias se conservaron. El contenedor propio Linux fue retirado por ID tras comprobar identidad, con ausencia final confirmada.

- Manifest de revisión y QA: `0ebbb8313c63897d549d015590c22e4047a74e2293946f104412a5ed3e61334e`.
- Informe final: `086a0ebda26896cdbdc6bbcdd61b076a8ab710efb285aee1b0603d0be7ccda5f`.
- Evidencia final: `a81d9c399df7f5f0209f974aebaa1ad61a156151775f4172d61974bd20f9541e`.
- Handoff sellado: `94f985dd8bfd661b4d5bc6503053d0c7829e3421732c118735f3dcfc6d133d46`.

Aceptada la implementación parcial del bloque: lectura documental explícita, selección pura, contexto canónico/deadline, selectores AST, recibos y productor sobre destinos nuevos. La memoria local conserva su disponibilidad sin servicios externos. Publicada la entrega de implementación en la rama; T-07/T-11/T-13/T-14/T-15 siguen abiertas por restore, corpus grandes, continuidad/aprendizaje y demás capacidades. No se declara superioridad experimental, autenticación del productor, atomicidad del par ni prevención de ABA.

## Bloque18 — publicación comprobada

Entrega publicada en `feat/catalog-capabilities`, commit `ded934a70e56508601006a06d52550cbfb7da019`; el SHA remoto observado coincide. Se comprobaron los 43 blobs publicados. Git normalizó CRLF a LF en 13 archivos; los hashes de bytes de la fuente probada se conservan y la evidencia distingue los hashes de blobs publicados. La única diferencia de esos archivos es el fin de línea; los AST de Python y los valores JSON coinciden.

El cierre público conservó 971 archivos, 43 cambios, 214 enlaces locales válidos y 32 destinos del consumidor excluidos antes de leer. La revisión independiente de documentación no dejó gaps; informe SHA `2df7ed67848727ef8e278688f43772bae3e4f1f1a520e79888bfbc18500e5d20`. El historial archivado permanece intacto. El lector real del panel reconoce nuevamente la iniciativa y sus 16 tareas: muestra hasta ocho activas y declara `task_budget` cuando corresponde.

Esta publicación cierra el bloque de implementación, no las tareas macro ni la integración global. Restauración, corpus grandes, continuidad, aprendizaje y las capacidades restantes del panel y comandos siguen pendientes.

## Bloque19 — integración de revisión visual en curso

El [contrato](comparisons/plan-review-integration-contract.md) concreta el diseño elegido de revisión de planes. Alcance: dueño compartido, transporte/UI opt-in y consumo desde la puerta «OK del plan». Las skills y la ampliación de hooks permanecen aplazadas.

La implementación se prepara en fuentes propias aisladas. El candidato del dueño conserva 35 assertions RED previas a sus comportamientos y 46 pruebas GREEN en Windows. Coverage.py mide 384/398 líneas ejecutables, 96.48241206030151%, sin atribuir cobertura de subprocesos. Dos errores del harness por nombres de parámetros demasiado grandes no cuentan como RED. Los tres fallos intermedios de fsync en Windows permanecen en la evidencia y motivaron la corrección del descriptor.

El candidato del panel y la actualización de comandos/documentación avanzan en paralelo. Ningún resultado individual acepta todavía el bloque. Quedan unión real de UI/CLI/puerta, Linux, interacción en navegador, callers de los tres runtimes, revisión independiente y QA del código integrado. No se cierra ninguna tarea macro.

La consolidación aplica fuentes exactas del dueño, transporte/UI y doce archivos de comando/documentación. La comprobación previa a la integración detectó un envío POST en curso que podía acompañarse de un banner incorrecto; cinco RED reales preceden la corrección. La UI corregida pasa 40 casos, incluidos 29 escenarios Node, y conserva el handoff anterior. Estos checkpoints se solapan y no son QA del conjunto.

El comando obtiene ID/versión con `open` antes de iniciar el servidor y registra el runtime actual. Codex y OpenCode regeneran sus proyecciones comunes. La [evidencia de candidatos](testing/plan-review-implementation-evidence.json) conserva límites, fuentes y resultados por componente; revisión independiente, plataformas, navegador y publicación permanecen pendientes.

## Bloque19 — regresiones de normalización antes de corregir

RED: `agent-kits/shared/test_plan_review.py::test_gap_b1_c1_sanitized_plan_is_redacted_before_display` falló porque la vista mostraba un token sintético ensamblado al retirar controles; dos casos · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_gap_b1_c1_comment_roundtrip_keeps_receipts_readable` falló con `unavailable/invalid_state` después de guardar o sellar comentarios aceptados; cuatro casos · 2026-10-09.

RED: `tests/test_panel_review_server.py::test_gap_b1_c1_http_comments_do_not_reveal_tokens_or_poison_state` falló porque la respuesta HTTP contenía el token sintético saneado sin redactar; cuatro casos · 2026-10-09.

Los diez fallos son assertions de regresión en una copia propia, sin errores de colección ni skips. El dueño mantenía su SHA previo `536931b06e6ce0689d7434c0392e4f1517bdcf2ad7281d379d4f3d9ddbaefaff`; stdout RED SHA `731bfd7f9734ac7c475686ec013b03e061661ded001ab2aee20af4029ac27c06`. Esta evidencia precede la corrección y no acepta QA del conjunto.

## Revisión de dos lentes — intento 1: Bloque19 (T-11/T-13/T-14/T-15) — correcciones pendientes de validación

Lentes A+B+C+D sobre 28 archivos y 978 hashes de fuente. C usa el informe estático independiente de reemplazo; su primer informe fue interrumpido por un filtro automático. B conserva un addendum del error de serialización. Tres gaps Important tras fusionar la misma raíz B/C; no hay Critical ni Minor. Ningún resultado de revisión acepta QA.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Faltaba traza RED canónica | T-11/T-13/T-14 | Registrar las observaciones previas existentes, con procedencia | RED por criterio abajo; 35 assertions del dueño, dos errores de harness excluidos; pendiente de validar |
| A2 | Important | Faltaba salida del check de interop | T-11/T-15 | Registrar exit y stdout del check real | `export-interop --check: 58 ficheros al día`, exit 0; pendiente de validar |
| BC1 | Important | El saneado posterior a redacción exponía texto y volvía inválido el recibo | T-11/T-13/T-14 | Sanear controles antes de redactar vista y comentarios | Diez RED/GREEN dedicados y 156 vecinos GREEN en Windows; pendiente de validar |

### Observaciones RED previas a la creación y endurecimiento del dueño

RED: `agent-kits/shared/test_plan_review.py::test_raw_view_and_sections_bind_exact_full_redacted_content` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_plan_failures_never_create_authorizing_state` falló con unavailable/missing_owner antes de existir el dueño; 3 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_selection_scope_rejected_before_state` falló con unavailable/missing_owner antes de existir el dueño; 4 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_comments_cas_and_sealed_decision` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_invalid_comments_never_freeze_decision` falló con unavailable/missing_owner antes de existir el dueño; 3 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_receive_keeps_delivery_until_revalidated_idempotent_ack_and_restart` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_changed_plan_blocks_each_decision_boundary_and_retains_old_record` falló con unavailable/missing_owner antes de existir el dueño; 3 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_gate_and_ack_identity_are_not_interchangeable` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_poll_is_read_only_and_unknown_id_has_no_state_effect` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_existing_unowned_state_and_foreign_record_are_preserved` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_state_scope_deadline_and_link_rejections` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_deadline_at_commit_and_fsync_failure_do_not_claim_success` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_record_and_response_budgets_do_not_truncate_or_drop_prior_receipt` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_common_cli_pipeline_and_registration_are_runtime_independent` falló con unavailable/missing_owner antes de existir el dueño; 3 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_corrupted_nested_state_cannot_be_served_or_consumed` falló con aceptó estado anidado inválido; 5 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_directory_creation_race_never_adopts_foreign_state` falló con creó marker en un directorio aparecido durante la carrera; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_foreign_record_in_owned_namespace_is_not_adopted_by_new_open` falló con no rechazó el recibo ajeno del namespace; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_unavailable_plan_serves_history_readonly_and_never_consumes` falló con devolvió review nulo en lugar de conservar hechos históricos; 3 caso(s) · 2026-10-09.

### Observaciones RED del panel y cierre

Los ocho registros siguientes conservan el resumen del autor de sus salidas de herramientas; no se presentan como un stream stdout capturado.

RED: tests/test_panel_review_server.py::test_review_open_and_get_delegate_without_browser_paths failed TypeError create_server() unexpected keyword review_selection · 2026-10-09. Test expresses missing opt-in transport API, production still exact base.

RED: tests/test_panel_review_ui.py::test_review_is_explicit_live_only failed TypeError render_html() unexpected keyword review_enabled · 2026-10-09. Product unchanged before test.

RED: tests/test_panel_review_ui.py::test_review_controller[missing_canonical_history] failed generic unavailable discarded historic consumed receipt · 2026-10-09. Owner contract refinement notified before product adaptation.

RED: tests/test_panel_review_ui.py::test_cli_explicit_gate_selection (None/requested-review/plan-ok) failed missing gate_key and argparse unknownflag · 2026-10-09. Parent authorized minimal --review-gate-key extension.

RED: tests/test_panel_review_server.py::test_comment_budget_maps_to_413_without_owner 2 cases failed 400 != 413 · 2026-10-09. Budget HTTP mapping correction before product fix.

RED: tests/test_panel_review_ui.py::test_review_controller[multiple_comments_same_section_preserved] failed dropping existing-two on save · 2026-10-09. Sharedowner permits unique IDs on one section; transport/UI must preserve rows.

RED: tests/test_panel_review_ui.py::test_review_controller[poll_keeps_comment_editing] failed textarea.disabled true during GETstatus · 2026-10-09. Poll would blur focused editable comment every5s; keep editing while readpoll in-flight, mutatingbuttons disabled.

RED: tests/test_panel_review_ui.py::test_review_controller[unavailable_cannot_enable_current_view] failed enabling approval for contradictory unavailable/current envelope · 2026-10-09. UI must reject incoherent display projection, no receipt-state implementation.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_blocked_during_submit]` falló con `close.disabled false != true` · 2026-10-09.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_blocked_during_comments]` falló con `close.disabled false != true` · 2026-10-09.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_blocked_during_refresh_post]` falló con `close.disabled false != true` · 2026-10-09.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_preserves_sealed_changes_consumed]` falló porque el banner «cerrada sin decidir» descartaba hechos de la decisión sellada · 2026-10-09.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_during_get_preserves_later_known_decision]` falló porque el banner «cerrada sin decidir» descartaba hechos de la decisión sellada · 2026-10-09.

El stdout capturado de estos cinco casos tiene SHA `6561d7793dfe264c9a11ff5e352194df75f82c3b0ddd02187b66c02d5dc886dd`. Los GREEN de componente se solapan y no se suman como QA final.

### Check real y siguiente puerta

`python3 scripts/export-interop.py --check` se ejecutó en la fuente integrada congelada del intento 1: exit 0, stdout `export-interop --check: 58 ficheros al día`, stderr vacío. ROOT y la lente A lo ejecutaron por separado; los 978 hashes permanecieron intactos. Los hashes y límites de los informes figuran en la [evidencia del bloque](testing/plan-review-implementation-evidence.json).

TDD n/a: incorporación de trazas/documentación de A1/A2. La corrección de BC1 tiene sus diez RED antes del cambio y diez GREEN después; la suite vecina pasa 156 casos sin fallos. Falta el segundo pase independiente y QA Windows/Linux, navegador, callers y paquete portable. Todas las tareas macro conservan su estado.

## Revisión de dos lentes — intento 2: Bloque19 (T-11/T-13/T-14/T-15) — implementación aceptada

2026-10-10. Lentes A/B/C/D independientes de contexto fresco, fallback genérico porque el revisor nativo no está disponible. Los informes conservan los criterios aprobados del primer pase y revisan los cinco archivos corregidos; no hay rebatidos. Fuente sellada: 978 archivos públicos, 28 en el diff; manifest SHA `1764fcaa55ddfd015419fa1a74a4c78a7cb8a10f1b48a35b725a3d286bbf84ce`, diff SHA `84d89fed1281c2f9d849a402f847d3d6be89a48a854d592e310109c3d4068ffc`. Los hashes antes/después coinciden. Los tres Important anteriores quedan corregidos y validados; 0 Critical, 0 Important y 0 Minor pendientes.

| Hallazgo anterior | Validación independiente |
|---|---|
| A1: trazas RED canónicas | A valida identidades, errores, fecha y procedencia individual; conserva la distinción entre capturas y resumen atribuido del autor. |
| A2: evidencia interop | A ejecuta un check propio: exit 0, stdout `export-interop --check: 58 ficheros al día`, stderr vacío; 978 hashes intactos. |
| BC1: saneado antes de redacción | B valida la corrección con 14 pruebas del dueño y 12 probes independientes; C la valida estáticamente con CWE-180/200. No se suma este checkpoint a QA. D conserva su aprobación de rendimiento sin repetir por rutina el benchmark. |

Los SHA de los cuatro informes están en la [evidencia del bloque](testing/plan-review-implementation-evidence.json). El evento de revisión se comprobó en configuración Jira OWN desactivada: exit 0, ops vacías y cero escrituras externas; el error anterior de harness sin `--batch` se conserva. No se leyó configuración consumidora.

QA Windows/Linux está en ejecución sobre la misma fuente revisada: 42 módulos en tres cohortes, dueño/servidor/builder completos, dos gates Coverage.py ≥90% sin redondear y qa-gate oficial desde JUnit real. Esto no declara su resultado. La prueba de navegador abrió la URL loopback sintética, pero Edge mostró «Microsoft Edge ha bloqueado esta página», `ERR_BLOCKED_BY_CLIENT`; cero escenarios UI ejecutados. Se cerraron la pestaña propia y el servidor registrado sin cambiar protecciones. La interacción real y los callers nativos siguen pendientes; todas las tareas macro conservan su estado.

TDD n/a: registro de revisión y resultados de infraestructura, sin cambio de código de producto.

### QA: registro de consola pendiente

La cohorte router/code de Linux terminó con 4 fallos, 1027 passes, 21 skips y 39 subtests reportados por separado. Los cuatro fallos detectan la ausencia del modo del nuevo CLI en la batería de codificación; no se eliminan ni excluyen. Stdout capturado SHA `3ae32f6fa41748d5d593d04cd691df559633342720d128f354c996692ffbd4aa`. La ejecución completa sigue en curso y no tiene aceptación QA.

RED: `tests/test_console_encoding.py::test_arranca_sin_reventar_en_consola_no_utf8[agent-kits/shared/plan-review.py-cp1252]` falló con AssertionError: el nuevo CLI no declara modo en MODOS · 2026-10-10.

RED: `tests/test_console_encoding.py::test_arranca_sin_reventar_en_consola_no_utf8[agent-kits/shared/plan-review.py-ascii]` falló con AssertionError: el nuevo CLI no declara modo en MODOS · 2026-10-10.

RED: `tests/test_console_encoding.py::test_la_salida_sigue_siendo_utf8_no_interrogantes[agent-kits/shared/plan-review.py-cp1252]` falló con KeyError: 'agent-kits/shared/plan-review.py' · 2026-10-10.

RED: `tests/test_console_encoding.py::test_la_salida_sigue_siendo_utf8_no_interrogantes[agent-kits/shared/plan-review.py-ascii]` falló con KeyError: 'agent-kits/shared/plan-review.py' · 2026-10-10.


### Corrección del registro de consola

Se integra únicamente `tests/test_console_encoding.py`: añade el modo operacional `open` sobre un plan sintético Unicode y su state-root propio. La ayuda del CLI es ASCII, por eso no sustituye la prueba. No se cambia el dueño ni se excluye ningún caso. Antes del cambio, el autor reproduce los cuatro RED sobre la misma fuente; después, los cuatro casos pasan y la batería completa de consola pasa 530 casos en Windows. Es un checkpoint del autor, sin aceptación QA global ni suma con los casos anteriores. Stdout de la batería SHA `cd221e07f1f1e4f7f2db47140105f122b9f91ac6c68d33d906279186eda29724`; informe SHA `83764b23d2dfb0384c3c7b62f843195e73484ffdb9827680607f0233170c7a68`.

La primera ejecución Linux conserva sus fallos y el cleanup del contenedor OWN confirmado. El auxiliar de comando falla por el alias privado `utf8-sig`; el recolector se detiene porque `test_mermaid_blocks.py` es una guarda CLI sin casos pytest. Se preparan correcciones privadas y una ejecución explícita de esa guarda, manteniendo las otras 41 selecciones pytest y los 29 escenarios Node obligatorios. No se borran ni convierten los resultados anteriores en verdes. Falta el tercer pase sobre este delta y QA reparada; navegador y callers siguen pendientes.

## Revisión de dos lentes — intento 3: Bloque19 (T-11/T-13/T-14/T-15) — sin gaps pendientes

2026-10-10. Lentes A+B+C+D de contexto fresco, fallback genérico por revisor nativo no disponible, sin override de modelo. Se conservan todos los criterios y aprobaciones anteriores; el delta revisado contiene registro de consola y dos archivos de evidencia. Los otros 975 archivos, incluida toda producción, conservan sus bytes. Fuente sellada: 978 archivos, 29 en el diff; manifest `834bb1e2050939a9ca6336cd9923e65fe58d0ced1209169e9b2ba2491b7d3d62`, diff `5259c025108e39b807fb3f8b3d90d682cc19d3efe18c97623258d759cfb011a7`. ROOT verifica informes, artefactos declarados y coincidencia de fuente con el árbol. Resultado: 0 Critical, 0 Important, 0 Minor pendientes; ningún gap rebatido o convertido en deuda.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important histórico | Trazas RED canónicas | T-11/T-13/T-14 | Corregida en R2, conservada | A mantiene IDs, errores, fechas y procedencias individuales. |
| A2 | Important histórico | Prueba de exports en ledger | T-11/T-15 | Corregida en R2, conservada | A3 ejecuta check propio: exit 0, stdout `export-interop --check: 58 ficheros al día`, stderr vacío; 978 hashes intactos. |
| BC1 | Important histórico | Normalización después de redacción | T-11/T-13 | Corregida en R2, conservada | Dueño y regresiones mantienen bytes aprobados; B/C no encuentran evidencia de reapertura. |
| Consola | Fallo QA de registro | Cuatro casos cp1252/ascii sin modo para el dueño | T-11/T-14/T-15 | Registro operacional con fixture Unicode propia | A valida traza RED previa y límites; B verifica cuatro casos y dos probes de pipes, sin sustituir QA. C/D no encuentran vulnerabilidad o carga nueva. |

Los SHA de A/B/C/D están en la [evidencia del bloque](testing/plan-review-implementation-evidence.json). Los siete gates previos pasan; no son aceptación de QA, navegador ni callers nativos. Ninguna tarea macro cambia de estado. TDD n/a para este registro de resultados; el RED/GREEN del registro de consola permanece separado.

### QA original terminada — resultados conservados como NO-PASS

| Plataforma | Passed | Failed | Skipped | Subtests separados |
|---|---:|---:|---:|---:|
| Windows | 2678 | 4 | 43 | 45 |
| Linux | 2698 | 4 | 23 | 45 |

Las dos ejecuciones originales terminaron con exit 1. Los cuatro fallos de consola son reales y preceden la corrección revisada. Además, el checker privado usó un alias de codec inválido y la selección incluyó Mermaid, script standalone sin casos pytest: falta su ejecución CLI, no se omite su guard. Windows detectó seis consultas de registro de Codex que el stub OWN bloqueó con exit 97; Linux no tuvo intentos. No se ejecutó el CLI real ni se accedió al registro consumidor. La causa estática liga tres modos de doctor por dos codecs y diferente materialización del CODEX_HOME temporal; los logs originales no permiten atribución individual por PID.

Los runners se detuvieron antes de qa-gate, los gates finales de cobertura y los hashes posteriores. Existen CoverageJSON y JUnit reales, pero no se atribuye al primer intento verificación que no ejecutó. Los checks portable pasaron con seis casos por plataforma sobre CLI común y etiquetas de runtime; no prueban tres hosts nativos. El contenedor Linux propio fue retirado por ID con ausencia confirmada. Los seis XML, logs, fallos y pruebas auxiliares permanecen intactos.

La siguiente ejecución repara sólo consola y auxiliares defectuosos/faltantes, con agregación explícita de procedencias y conservación de resultados originales. La producción no ha cambiado. La aceptación de navegador y de callers nativos permanece pendiente; no se convierten Node/HTTP o etiquetas de runtime en evidencia equivalente.

Evento revisión3 sobre fixture Jira OWN desactivada: exit 0, ops vacías, cero escrituras externas. Stdout SHA `6a946c3fa6a690ce2f112293593f78e69ac1329c2078d0764af8ee13bc9f5f35`; ledger propio SHA `08cb5e81daebd124ddb58c5e8adfaa30b6c091ae51ec293eb9627f4207a2a8ad`.

### Bloque19 — referencia documental de los comandos

La comprobación independiente del puente documental detectó un Minor: el enlace relativo al panel era válido en el comando canónico, pero apuntaba a carpetas inexistentes en las dos proyecciones generadas. Se conserva el resultado original 70/72. La política de exports conserva el cuerpo canónico sin transformar rutas; por eso se sustituyó una única línea de documentación por la referencia explícita a `docs/PLUGIN-PANEL.md` en la documentación del plugin, y se regeneraron las dos copias. No se modificó el exporter ni ninguna instrucción del workflow.

La comparación de bytes verifica una única sustitución por archivo y el contrato funcional de revisión visual idéntico. Generación y check de exports: exit 0; enlaces restantes 69/69, más tres referencias explícitas al documento existente. El recuento baja en tres porque se retiraron el enlace canónico válido y las dos copias inválidas. El informe inicial y sus fallos permanecen intactos. Esta corrección de prosa no reabre la implementación aceptada ni acredita QA, navegador, callers nativos o cierre macro. TDD n/a: prosa y proyecciones generadas.

QA incremental iniciada Windows/Linux sobre fuente834 aceptada, en destinos OWN nuevos. Se ejecutan consola completa de 530 IDs y auxiliares defectuosos/faltantes; se retienen JUnit/coverage/portable válidos con cierre de dependencias y sustitución explícita por IDs. Stub de registro Codex cerrado y sintético, con manifest real/argv/cwd/hash/PID; no hay CLI nativo real. Runner SHA `d91d1ae2da7e250ce5e69d52e93bbfbff31c9eeaeb036fbfbc018ad7782924f1`; receta SHA `1225502c57d4d4cb9e1ce9ef7b856b19fee29daa9c2b76c84fcfbe71d4ac71e0`. La ejecución está en curso y todavía no se declara verde. El puente documental posterior de cinco archivos queda separado de la fuente QA sellada.

La primera repetición incremental terminó con exit 1 en ambas plataformas antes de tests o creación de contenedor: el PATH necesario de Node contiene también un CLI OpenCode real y el preflight estricto lo rechazó. Cero pruebas ejecutadas y cero CLI nativos lanzados. Se conservan los resultados terminales y las copias/hashes previos; al ocurrir antes del try/finally del runner, la traza se atribuye al tool y no a un log generado por el runner. Se prepara un OWN nuevo con Node existente copiado y ligado por hash a un bin aislado; no se amplía PATH ni se elimina el guard. No es un fallo nuevo del producto ni aceptación QA.

Nueva QA incremental iniciada Windows/Linux con copia OWN byte exacta del Node existente en directorio aislado; el rechazo previo del PATH y los fallos originales quedan conservados. Se mantiene la misma selección, fuente834, receta y guard estricto. Runner SHA `349014078051da28600152686c36022cb820aa242f5157d382940dec7a03dda8`; receta SHA `1225502c57d4d4cb9e1ce9ef7b856b19fee29daa9c2b76c84fcfbe71d4ac71e0`. Handles reales observados; ninguna aceptación QA se declara mientras están en curso. El puente documental posterior sigue separado.

La QA Node aislada termina Windows exit 0 (veredicto del runner, pendiente de comprobación ROOT) y Linux exit 1 tras consola completa exit 0 y auxiliares exit 0. El assert de fixture cerrada detecta cero llamadas: el stub Linux escrito desde Windows conserva shebang CRLF y no puede ejecutar `/bin/sh`; no se retira ese assert. Se conserva el fallo, los hashes y la retirada por identidad del contenedor propio. Se prepara únicamente corrección LF del harness para Linux, con candidata Windows retenida bajo puente explícito del cambio de rama; aún no hay aceptación QA global.

Corrección auxiliar LF adoptada en OWN nuevo y QA Linux iniciada con handle real1422. La comparación reversible demuestra que sólo cambian escritor/assert del stub Linux y nombre del contenedor propio; cuerpo Windows, fuente834, receta y proofs siguen exactos. Se retiene la candidata Windows terminal0 sin repetición rutinaria, pendiente de verificador completo por plataforma. Runner Linux SHA `b5dbcbedb5db0edc94d88d583806cd22c8904949133dd41c7ddba0d68f20d76e`; pointer SHA `51cdf42e13161bd3a159be9a2ab27d3e464bcb5b32952358f2dee81c408eedb7`. Se conserva el assert de llamadas CLOSED y toda evidencia NO-PASS previa.

QA de implementación del Bloque19 aceptada por ROOT tras comprobar íntegramente artefactos, procedencia y gate oficial de ambos OS sobre fuente834: Windows2682 passed/0 failed/43 skipped y Linux2702 passed/0 failed/23 skipped;2725 casos JUnit únicos por OS. Los530 casos de consola sustituyen sus mismos IDs anteriores;45 subtests crudos van aparte y29 casos Node ya están incluidos. El gate oficial incluye10/14 auxiliares adicionales y sale VERDE. Coverage oficial retenida bajo hashes/diff idénticos: media3 Windows96.31596814342258% y Linux96.62560154100005%;líneas ejecutables cambiadas515/532 y518/532, con umbral calculado sin redondeo. Seis llamadas mock cerradas por OS y cero CLI nativos reales. Windows se retiene con puente de harness que sólo modifica LF/nombre de contenedor en rama Linux; original NO-PASS, preflight y fallo shebang quedan intactos. Cleanup Linux por ID/imagen/label/network y ausencia verificados. Recibo QA SHA `8168de7023e9fc6685d61ca9a56e525a4c6b6966ac2f005e3ab572facd5489fc`; verificador SHA `020fd4370de91804c0cc81ee1905387f2a3ab8ad791de1a147f73635bac93c5c`. Navegador real, tres hosts nativos, cobertura macro y cierre global siguen pendientes; el puente final documental/metadatos se valida por separado antes de publicación.


## BLOQUE20 — conservación y recuperación de memoria local

Contrato propuesto: [memoria local y recuperación](comparisons/memory-local-recovery-contract.md). Define doce oráculos N01–N09: conservación canónica y colas, caché ausente/corrupta, cuatro fronteras de corte, reintento de manifiesto, restauración quiescente, autoridad, lectura offline y scope/redacción. Añade la regresión del parser para enlaces inline entrecomillados, sin sustituir la fixture por bloques.

Evidencia de aceptación: `UNKNOWN`. Preservar cada ejecución fallida y su clasificación, fuente/Gold/recipe/harness, JUnit y auditorías. El RED/GREEN del autor acredita la regresión específica; ROOT requiere ejecución congelada Windows/Linux y puertas pertinentes antes de aceptar el bloque. Ningún resultado anterior se reutiliza como PASS de recuperación.

| Macro existente | Trabajo del bloque |
|---|---|
| T-07 | Documentar límites de persistencia y recuperación frente a eficacia de consulta ya medida. |
| T-08 | Mantener corpus y colas locales como autoridad; caché reconstruible y contrato de publicación/idempotencia. |
| T-09 | Verificar captura confirmada, barreras y cleanup por identidad, sin añadir hooks o hosts. |
| T-11 | Conservar handoffs y aprobación actuales; legacy, propuesta y aprobado mantienen estados distintos. |
| T-13 | Vincular la guía de consulta a conservación/recuperación y estados parciales; consultar no restaura. |
| T-14 | Revisar regresión y doce casos obligatorios, cobertura oficial del diff y qa-gate; guardar fallos de infraestructura aparte. |
| T-15 | Integrar contrato y enlaces breves en guías propietarias; verificar enlaces y exportaciones afectadas. |
| T-16 | Incorporar evidencia sólo tras aceptación real del bloque; mantener pendiente el cierre de la iniciativa. |

Esta inserción no crea una tarea macro ni modifica los dieciséis campos `Estado`, dependencias o porcentajes. Mantener sólo T-01 completado y conservar todos los pendientes nativos, de escala y aprendizaje restantes.

### Corrección del lector y preparación reproducible

2026-10-10. Se integra la normalización compartida de listas YAML simples: retira una sola pareja de comillas coincidentes y conserva valores mal formados para su rechazo. No añade un parser YAML completo. La fixture entrecomillada original se conserva.

El autor observó 6 failed/7 passed antes del cambio y 13 passed después sobre los mismos IDs. El pase final de documentación volvió a ejecutar esos 13 IDs; no se suma como 26 pruebas distintas ni acepta QA global. JUnit RED SHA `bec970d45bab216aebe71e025ce9dd0f3430b587883a810f96987ed9c2fe9a78`; JUnit final GREEN SHA `eef0f24d7551ad3f9d58ac479c0ec31330b6acdf3ee0d21ed154aa295bd18d45`. ROOT verificó artefactos y adoptó los dos archivos exactos del autor.

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_same_identity_related_and_readonly[double]` falló con AssertionError: show devolvió partial en lugar de ok · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_same_identity_related_and_readonly[single]` falló con AssertionError: show devolvió partial en lugar de ok · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_same_identity_related_and_readonly[mixed-whitespace]` falló con AssertionError: show devolvió partial en lugar de ok · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_unknown_or_malformed_fail_closed[unmatched-block]` falló con AssertionError: show aceptó comillas mal formadas y devolvió ok en lugar de partial · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_unknown_or_malformed_fail_closed[mismatched-block]` falló con AssertionError: show aceptó comillas mal formadas y devolvió ok en lugar de partial · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_unknown_or_malformed_fail_closed[extra-quote-block]` falló con AssertionError: show aceptó comillas mal formadas y devolvió ok en lugar de partial · 2026-10-10 (ejecución del autor, JUnit conservado).

El primer drill Windows terminó 12 failed antes de ejecutar producto por identidad del launcher venv. La corrección usa el intérprete base y mantiene PID/ppid/nonce estrictos. El segundo terminó 2 passed/10 failed: siete por clasificación del argv Git auditado en Windows y tres por corpus aprobado parcial causado por enlaces entrecomillados. Ambos resultados NO-PASS permanecen conservados. El probe stdlib bloqueó las cuatro llamadas antes de crear procesos y distinguió las dos consultas Git exactas de las dos ajenas.

La batería pública copia sólo quince inputs de producto declarados a un directorio pytest propio, sin configuración o memoria del consumidor. Conserva doce IDs, nueve grupos, Gold, barreras y límites; registra el argv auditado y exige corpus completo al reconstruir la caché. Está preparada, todavía sin ejecución ni aceptación Windows/Linux. Revisión independiente, cobertura oficial, qa-gate y documentación humana final siguen pendientes. No se reabre QA19 ni cambia ningún estado macro.


## Revisión de dos lentes — intento 1: Bloque20 (T-08/T-09/T-14/T-15) — dos gaps pendientes

2026-10-10. Lentes A+B de contexto fresco, fallback genérico por revisor nativo no disponible, sin override. Selector sobre el diff real: C=false/D=false, sin avisos. Scope oficial exit0:16 archivos en alcance, cero fuera/exclusiones del usuario/avisos. Ledger-lint:0 incoherencias/0 avisos. Fuente983 y diff sellados; ambos revisores comprobaron983 hashes antes/después. No ejecutaron pruebas ni producto. Se conservan QA19 y todos los criterios aprobados anteriores; no se cierra ninguna macro.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | El contrato no distingue el plazo de admisión de420s de una duración total | T-09/T-14/T-15 | Se aclaran admisión, barrera25s, finalización30s y recogida5s; pendiente validación independiente | Contrato:50 y harness:257/290/312/419 en fuente revisada. |
| AB1 (A2/B1) | Important | Resolver antes de rechazar oculta raíces/ancestros enlazados y destinos colgantes dentro de OWN | T-08/T-09/T-14 | Corrección y regresión del soporte sintético en curso; no se afirma fallo de backup de producto | protocol.py:34/132/184; ningún caso nuevo ejecutado aún. |

Fusión ROOT tras leer ambos informes completos y verificar sus hashes:0 Critical,2 Important,0 Minor; no hay rebatidos ni deuda aceptada. Los informes y límites quedan en la [evidencia del bloque](testing/memory-local-recovery-review-evidence.json). El fallo del auxiliar ROOT que esperaba una lista de exclusiones, en lugar del objeto vacío oficial, se conserva: scope había salido0; no fue un gap del producto ni una prueba ejecutada. Su finalizador verificó nuevamente fuente, diff y salidas oficiales. El intento de registro del revisor A dejó un directorio vacío; se conserva y no se usó para evidencia ni producto.

La revisión sigue acotada a tres intentos para este bloque. La corrección del parser mantiene su GREEN de autor separado; las doce pruebas integradas y los gates de cobertura/QA continúan pendientes. TDD n/a: registro de revisión y precisión documental del plazo; la regresión del protocolo debe observar RED antes de corregirlo.

Evento `gaps`, intento1, actor reviewer, sobre copia de ledger y configuración Jira sintética desactivada: exit0, ops vacías y cero escrituras externas. Stdout SHA `4670c8e70e35284c0d4d764edd464ad73279c3f0d9f2885623a3e6e7976fcdae`. No se leyó configuración consumidora.

### Correcciones preparadas para revisión 2

2026-10-10. ROOT adoptó el rechazo léxico de enlaces/reparse points antes de resolver raíces, hojas y ancestros en el soporte de backup/restauración sintético. No se añade un CLI de backup de producto. Se conserva la contención posterior y todos los oráculos/budgets. La precisión documental distingue el plazo de admisión de420s de la duración total. Ambos gaps esperan revisión independiente; la tabla anterior conserva el estado observado en intento1.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[source-leaf]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[source-ancestor]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[snapshot-leaf]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[snapshot-ancestor]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[target-dangling-leaf]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[target-ancestor]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

Autor:6 failed antes/6 passed después, mismos IDs y bytes; doce junctions nativas creadas con exit0. Cada GREEN rechaza antes de mutar y mantiene idéntico el árbol completo de fixture. ROOT verificó124 artefactos y fuente983 intacta, JUnit, registros/argv/PID y árboles de ambos pases. JUnit RED SHA `b30090d9c71dfdccf03989975a059a925d9f254bf7a5fb85e124cdd81836d68f`; GREEN SHA `03f7822f233c60e8b3ae61eb61d43a173d7ba82a2edd9be48b5f78462aee9c59`. Este checkpoint no acepta las doce pruebas de recuperación ni QA global. POSIX sigue sin ejecutar; macros y QA19 intactos.


## Revisión de dos lentes — intento 2: Bloque20 (T-08/T-09/T-14/T-15) — sin gaps pendientes

2026-10-10. A+B frescos, fallback genérico sin override. Ambos informes completos y sus verificaciones se contrastaron por ROOT; fuente985 idéntica antes/después, FULL18 diff, scope/selector/ledger oficiales exit0 y cero avisos/exclusiones. C=false/D=false. Se conserva el traspaso R1 íntegro, sin reabrir aprobados, sin rebatidos ni deuda.

| # | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Plazo de admisión ambiguo | T-09/T-14/T-15 | Corregido: contrato precisa420s de admisión y25/30/5 propios; no promete duración total | A2 contrato:50–55, harness:257/290/312/377/405/419. |
| AB1 (A2/B1) | Important | Alias oculto por resolve anterior al rechazo | T-08/T-09/T-14 | Corregido: lstat léxico de hojas y ancestros antes de resolve; seis regresiones dedicadas preservan árbol completo | A2/B2 protocol:34–49; test_protocol:102–156; RED/GREEN de autor conservados. |

Fusión actual:0 Critical/0 Important/0 Minor. Recibo de revisión SHA `5138f50080b1692824607fb4cb3639b23d656820f2f590c8164728a71b428608`. La aceptación integrada sigue UNKNOWN: faltan Windows/Linux, cobertura oficial y qa-gate. No se ejecutaron pruebas de producto durante revisión. Los estados macro y QA19 permanecen intactos. TDD n/a: esta traza de revisión.

Evento revision/intento2/reviewer en ledger OWN y configuración Jira sintética desactivada: exit0, ops vacías, cero escrituras externas; stdout SHA `1fe31f91295d3d44feca55cd302ee205d555208176ae133ce7bfb0d1095568c2`. Ninguna configuración consumidora leída.

### QA Windows aceptada; diagnóstico Linux abierto

2026-10-10. ROOT verificó la cohorte Windows congelada R2:528 IDs únicos,514 passed/0 failed/14 skipped. Los doce casos de recuperación y seis guardias de rutas pasaron sin skips. Se contrastaron fuente985, receta, revisión, JUnit, colección, setenta hijos, cinco cortes observados, fallo de manifiesto y auditorías contra los artefactos reales. Cobertura oficial del lector cambiado:212/235 líneas ejecutables y7/7 cambiadas, ambas por encima del umbral90% sin redondeo. El qa-gate oficial salió VERDE, exit0. Recibo Windows SHA `1926ac57e71cb1a25e8a9927dfc1b37c8e5d2bc6469bea0204256fed6a30f6b7`; no acredita Linux ni aceptación integrada.

La ejecución Linux con captura FD terminó antes de recoger casos por ENOENT al truncar el temporal de pytest; sus tres cohortes vacías y cleanup verificado se conservan. Una nueva ejecución con captura sys mantiene fuente, Gold y oráculos intactos. Su cohorte de recuperación terminó4 passed/8 failed: los ocho fallos ocurrieron al verificar la copia, antes de restaurar; las otras cohortes aún estaban en curso al registrar este checkpoint.

Un probe ROOT de sólo lectura dentro del contenedor propio confirmó124 archivos con bytes/SHA256/modos iguales y fuentes estables durante la observación, pero fechas de copia truncadas a segundos enteros. Recibo diagnóstico SHA `76c59b8757a411a24d5c08c939f74a3dcfda3b8a9a10f9117ab7c9cf4739eb1b`. Es una observación posterior de fixtures, no el inventario histórico ni una reproducción sobre filesystem nativo. Se conserva cada fallo y se prepara esa reproducción mínima antes de otra batería Linux. No se redondean expectativas ni se cambia el producto para ocultar diferencias de infraestructura. La aceptación integrada sigue UNKNOWN; QA19 y los dieciséis estados macro permanecen intactos. TDD n/a: registro de evidencia observada.

La ejecución sys terminó con528 IDs:516 passed/12 failed/0 skipped. Los510 vecinos pasaron; fallaron ocho casos de recuperación y cuatro guardias al preparar su copia, todos en el mismo oráculo de metadatos. Cobertura212/235 y7/7 cambió correctamente, pero no convierte los fallos en aceptación. Fuente985/proofs permanecieron idénticos y el contenedor propio fue retirado por identidad con ausencia verificada. El índice final del harness host falló después de esos recibos al acceder a un symlink nativo desde Windows; se conservan XML, logs, fixtures y fallo original sin afirmar un índice completo.

La reproducción mínima ROOT conserva exactamente bytes y modos: cuatro copias con fecha natural pierden su fracción de segundo en el bind Windows; doce copias en tmpfs nativo conservan el inventario exacto, incluidas ocho solicitudes de fecha controlada y doce de modo. No ejecuta producto ni sustituye pruebas de recuperación. Recibo SHA `d896c198e8a09fe7fc420b07337db1c69b52efabbaecf02b80f387192e3a7ddd`; cleanup exacto y ausencia verificados. Un primer guard del auxiliar exigió tmpfs en `Mounts`, aunque Docker lo declara en `HostConfig.Tmpfs`; se conserva el fallo previo a start y se reanudó el mismo contenedor OWN registrado tras verificar ambas representaciones. No hubo ejecución previa del probe ni reinicio de pytest.

La nueva receta privada conserva los oráculos y separa runtime Linux nativo de outputs durables del host. Requiere revisión independiente, precondición de filesystem y archivo completo verificado antes del cleanup. Su preparación no acepta el bloque ni modifica producto, Gold, QA19 o estados macro.

La receta privada V5 fue aceptada estáticamente por A+B y ROOT selló su adopción y la precondición real de filesystem. La ejecución nativa terminó con528 passed/0 failed/0 skipped: doce de recuperación, seis guardias y510 vecinos. El gate original salió1 por el recolector privado: su glob contó tanto el directorio real `memory-local-recovery0` como el alias symlink `memory-local-recoverycurrent` de pytest. El manifiesto archivado confirma ambas rutas. Este resultado original permanece NO-PASS; no se corrigen retrospectivamente su gate ni su verdict.

Antes del cleanup se verificó independientemente el archivo completo:8820 entradas,3999 archivos regulares y12031578 bytes, sin extracción y con grafo de enlaces/framing validados. Archivo SHA `1e2b9fee3fbbc3bd6315af5e3ef5cc4188da45fead2234ec90e0c1bbbb47346b`; manifiesto SHA `e7320fc98c4239fb3f65465f7170e0d332b58cbdcef5ee36d7b287742d9ad833`. Cleanup por identidad y ausencia verificados; fuente985 y pruebas de cierre intactas. Se prepara una verificación ROOT correctiva sobre esos mismos artefactos, con selección del directorio real y comprobación completa de hijos, antes de aplicar un nuevo gate oficial. No se repiten tests, no se cambia producto/Gold y la aceptación integrada sigue UNKNOWN.

### QA correctiva Linux y aceptación ROOT únicamente del Bloque20

2026-10-10. La verificación ROOT correctiva terminó exit 0 sobre los mismos artefactos terminales archivados, sin repetir producto ni tests: 528 IDs únicos, 528 passed/0 failed/0 skipped; doce casos de recuperación, seis guardias y 510 vecinos. Comprueba 70 hijos, cinco cortes, un fallo de manifiesto, diez ACK y nueve snapshots (ocho íntegros y uno alterado de forma controlada), además de seis symlinks POSIX de las guardias. Fuente 985 y proofs antes/después siguen exactos. Coverage oficial conserva 212/235 líneas ejecutables y 7/7 cambiadas, con umbral 90% calculado sin redondeo y sin inferir cobertura de hijos aislados.

El NUEVO qa-gate oficial usa input SHA `11ea4c501210e41ad1504e72100c8cd433656afa253369f1810e022b9fb287d4` y termina VERDE/exit 0; stdout SHA `7f6a9b5cac5255a9481fd8d3cb72ce8801b7106339ea632406950dfde4be1acc`. Recibo correctivo SHA `924702a0e036de50387c78720f8a539d074268eaf8ac98fd6a5addbfab08b072`. No cambia el gate 1, el verdict NO-PASS ni los UNKNOWN históricos del recolector original; tampoco los dos primeros fallos Linux o sus probes.

ROOT acepta únicamente el Bloque20 mediante recibo de publicación SHA `2908cafc8e0cc6be599b0b0ffe01d304f514f8dc172d598358a3de9bfd545761`, ligado a la aceptación detallada SHA `3ddeb5bf89562e3fced0e7edd6e9f66761822d1a118883870d364f9508a07e95`, R2/fuente 985 y los receipts Windows/Linux reales. Windows se retiene514 passed/0 failed/14 skipped; los 18 casos obligatorios pasaron sin skips en ambos OS, sin sumar cohortes ni repetir Windows. Los dieciséis estados macro y QA19 permanecen intactos; cierre global, tres hosts nativos, escala y eficacia comparativa conservan sus pendientes. La validación documental/metadatos final y commit/push de la rama siguen pendientes. TDD n/a: puente documental de resultados y aceptación, sin algoritmo público nuevo.

### Puente documental de publicación: enlaces históricos

El primer preflight de publicación terminó exit 1 antes de ejecutar los cinco gates estáticos. Detectó 28 enlaces históricos del changelog a directorios de conocimiento no versionados en la distribución (14 por idioma). Se conservan el fallo y su informe; no se leyó configuración ni corpus. Los IDs ADR/LES/GOT permanecen como referencias textuales, con una nota de distribución. Esta corrección documental conserva los siete archivos de código/test/Gold de R2 y no reabre QA19/QA20. La siguiente validación usa un OWN nuevo y el mismo auxiliar sellado; no se convierte el primer resultado en verde.

El segundo preflight terminó exit 1 en la preparación Git aislada, antes de los cinco gates oficiales. El escritor privado de alternates generó CRLF y Git conservó el carriage return como parte de la ruta de objects: los bytes terminan en 0d0a; recortar sólo LF no encuentra la ruta, recortar CRLF sí. Se conserva la salida terminal y el OWN completo. La corrección privada escribe bytes UTF-8 con LF literal y ruta POSIX, sin cambiar checks, producto, tests, Gold o receipts de QA. El gate de publicación aún requiere una ejecución nueva real sobre la fuente actual.

El tercer preflight terminó exit 1 antes de los cinco gates: el índice Git nuevo del OWN comparó archivos CRLF sin la conversión de texto. Una comprobación de status en ese mismo OWN, con core.autocrlf=true y configuración global/system NUL, devuelve exactamente los 18 archivos esperados; no modifica la fuente pública. La corrección privada configura la conversión exclusivamente en el Git local del OWN, conservando hashes crudos, filtros, exact18 y ROOT intactos. Los tres preflights originales siguen como fallos históricos, distintos de la QA de recuperación ya aceptada.

### Publicación observada de la implementación del Bloque20

2026-10-10. El cuarto preflight termina exit 0: lint de plugin, interop, evals estáticas, scope exacto de 18 archivos y ledger pasan sus cinco gates. Conserva 985 fuentes antes/después, siete archivos de código/test/Gold iguales a R2, prefijo de las dieciséis macros intacto y cero referencias de origen en los 18 archivos examinados. Lint conserva cuatro avisos existentes; no se ocultan ni se convierten en errores. Recibo estático SHA `6487a748212e007e205d814e9e0b631df269135b098e7947bb88fbca0e7688d1`; manifiesto actual SHA `d828550347c7947f6ecbcf0c88a930b6767c0531d4c1b73949d884f28c11596d`.

Commit de implementación `1f47fbf61261f4bb62282d0e9a8252a80d7bb6c2` publicado en `feat/catalog-capabilities`: push real seguido de comprobación remota devuelve ese mismo HEAD. Este cierre documental registra la primera publicación ya observada; su propio push se verifica posteriormente. Bloque20 aceptado y entregado; no declara cierre global, cambia estados macro, reabre QA19 ni acredita los tres clientes nativos, escala o eficacia comparativa. Las skills siguen aplazadas. TDD n/a: documentación de evidencia observada.

### BLOQUE21 — Caller portable de revisión visual y aceptación nativa

2026-10-10. Publicación del cierre documental del Bloque20 verificada en el remoto mediante HEAD `bd0ffb0a59f117cca30e968da4ceb0e4411a3783`. Es la base de esta entrega T-05/T-11/T-13/T-14/T-15, sin modificar las dieciséis macros ni reabrir QA19/20. Sigue el [contrato de caller portable](comparisons/plan-review-portable-caller-contract.md), conservando owner, estado y puerta plan-ok existentes.

El caller anterior sólo mostraba Bash y buscaba dueño/builder por separado. Las recetas nuevas permiten Bash/PowerShell con Python explícito real, seis raíces con precedencia, bundle común y rechazo de ambigüedad. Open precede su validación; el servidor conserva un handle separado. Receive, ack y view mantienen las validaciones de puerta, versión y consumo anteriores; no se interpretan comentarios como shell ni se inicia trabajo porque un proceso sale0.

RED: los diez casos iniciales fallaron por falta de recetas ejecutables únicas en el comando canónico, exit1/JUnit SHA `221fb016ab393890ca996e1413de52b41d77f9db8cca3378516a5ea5f321efb0` · 2026-10-10. GREEN: esos diez pasan tras el cambio, exit0/JUnit SHA `d327a0b5df17f42ed83ff5b68b63ac998c1f44ca73c37453b76b8e30e34197f6`. La ampliación a seis raíces y fallo de open termina24 passed/0 failed/0 skipped en Windows: doce Bash real y doce PowerShell, sin hosts nativos, navegador o modelos. JUnit SHA `beff581c108f8a291b0a0d39d87898c85ec5e534a7317a0b9a4e3c1200560e11`; el auxiliar conservó metadata expected10 del piloto, pero colección/JUnit reales tienen24, declarado sin alterar el intent original.

La [evidencia del caller](testing/plan-review-portable-caller-evidence.json) separa esta prueba con recorder sintético de owner/servidor/UI reales, carga/expansión por cliente y continuidad de agentes. Faltan congelación/revisión independiente, checks integrados y escenarios reales pendientes; no se suman etiquetas runtime a pruebas de shell para declararlos hechos. Scope previsto: comando canónico y sus dos proyecciones, test de recetas, documentación del panel/flujo y changelogs EN/ES, contrato/evidencia y esta traza. Las skills siguen aplazadas; T-16 y aceptación global permanecen abiertos.

## Revisión de dos lentes — intento 1: Bloque21 (T-11/T-13/T-14/T-15) — corregir retoma entre runtimes

Lentes A+B de contexto fresco, fallback genérico sin override de modelo; selector C/D false por diff real de14 archivos, sin avisos. Scope0/interop0 (58 archivos al día)/ledger0 previos; fuente988 y diff completos estables. A:0 gaps; B:1 Important. Report A SHA `54d558e1581b6f415972b8d9e68bda1332089c179fc333e63de1a4559c94d12c`, receipt `d086b732df62d8260377f48b1189c5c76c6419571271401d0afa7f1d83dfd11c`; report B SHA `2f6aeb6e7428c409cc97d39e979e73f5afde5c1d087de5bf60a1f894577c2a01`, receipt `d8f1909453f47627da5c4b67635407d1c5e47f8d6ffc95ba72ec9807c0f0dc8a`.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Caller exige consumidor actual al reabrir recibo histórico | T-11/T-13/T-14 | Validar selección/puerta/versión; tratar registro de consumidor como histórico, sin exigir coincidencia en retoma | Reproducción ROOT: codex→claude-code y panel sin registro→caller mantienen mismo ID, versión completa/current y consumidor anterior/null. SHA `d48e5f7f607b7af74ce1a1fb40a32f8e30e85aa1a2c8ca4d7692e2f4365730ae`; owner intacto. |

La corrección cambia sólo la regla de validación del caller y su contrato/proyecciones, no actualiza el consumidor guardado ni crea otro registro de estado. La siguiente revisión verificará esta corrección; máximo3 intentos. La aprobación de QA, UI y clientes nativos no se deduce de esta revisión.

### Comprobación real de navegador del Bloque21

El dueño real abre una revisión sintética propia con vista completa/current y el builder real inicia servidor loopback con PID/handle propio. Un primer launcher privado termina antes de navegar porque stdin era EOF en pipes; conserva ese fallo y cierre de su servidor por handle. La nueva ejecución con PTY conserva handle vivo. Edge rechaza la navegación a ese servidor con `net::ERR_BLOCKED_BY_CLIENT`; el árbol visible dice «Microsoft Edge ha bloqueado esta página». Cero escenarios UI ejecutados, ninguna decisión emitida. Se conserva el bloqueo sin cambiar Host/Origin/CSP/capacidad ni protecciones. El servidor propio se detuvo por su handle y se verificó ausencia del PID; su exit1 por terminación explícita no se presenta como salida natural0. La pestaña de prueba fue cerrada; no se tocaron pestañas del usuario, servicios Docker ni corpus/configuraciones consumidoras.


## Revisión de dos lentes — intento 2: Bloque21 (T-11/T-13/T-14/T-15) — prueba dedicada pendiente

2026-10-10. A+B frescos, fallback genérico sin override; scope0/exact14, selectorC/D false, interop0/58 y ledger0. Fuente988 y diff completos idénticos antes/después. A2:0 Critical/1 Important/0 Minor; B2:sin defectos. El comportamiento de B1 concuerda con el dueño, pero la constitución:13 exige una prueba dedicada que nombre y compruebe cada gap corregido. No hay rebatidos ni deuda; las aceptaciones anteriores y macros se conservan.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A2-1 | Important | B1 figura corregido sin regresión dedicada de la regla actual | T-11/T-13/T-14 | Validador de apertura ejecutable sin estado; pruebas B1 sobre dueño real y transporte shell | Informes A2/B2 y hashes completos en la evidencia; pendiente revisión3. |

Fusión ROOT tras leer informes completos y contrastar hashes:1 Important pendiente. Se mantiene máximo3 intentos. La fuente R2 no se modifica; no se aprueban QA, UI, clientes nativos ni publicación.

### Regresión dedicada y validación ejecutable preparadas

RED: `tests/test_plan_review_open.py::test_B1_resume_validates_real_owner_historical_consumer[codex]` y `[None]` fallaron con «B1 requires executable opening validation», dentro de23 failed/0 errors/exit1 · 2026-10-10. JUnit SHA `d0f2af3a476de23200c01d3241cb38ebc679df697f39412c616fe39f2ed1a155`. Un primer intento conservado produjo22 failed/2 errors por IDs pytest de tamaño excesivo para rutas Windows; se acotaron los IDs del test, sin cambiar producto ni oráculos.

El nuevo `agent-kits/shared/plan-review-open.py` valida JSON acotado, envelope, selección, puerta, hashes/vista/current y devuelve sólo IDs/versión con approval_granted=false. No escribe estado ni cambia el dueño. Las dos recetas lo ejecutan antes de servir; PowerShell conserva/restaura OutputEncoding al transportar Unicode por stdin. La búsqueda exige dueño/validador/builder co-locales; no completa una instalación parcial desde otra fuente.

GREEN de autor:49 passed/0 failed/0 skipped Windows,23 de validador y26 shell (13 Bash/13 PowerShell). Los dos B1 ejecutan cuatro aperturas reales en fixtures propias: Codex→Claude y panelnull→Claude; conservan ID/versión/primerconsumidor y bytes del estado durante validación. Dos negativos shell impiden serve ante exit0 del dueño con otra puerta. JUnit SHA `726a0359cde74df563e06cef932a4e20aa69f6b085c0cb05121cdccff09bc2a9`. Fuente/receta/IDs conservados antes/después; cero modelos/hosts/UI. No sustituye QA integrada ni prueba obediencia de agente.

El preflight Linux R2 no ejecutó pytest ni creó contenedores: se detuvo antes del arranque porque cambió la fuente para corregir A2-1. Imagen QA20 exacta disponible, diagnóstico retenido sin afirmar PASS/SKIP Linux. El siguiente ensayo debe corresponder al bundle nuevo. Contrato/evidencia/descriptores se actualizan juntos; exports, revisión3, checks integrados, UI/carga/continuidad nativa y push continúan pendientes.


## Revisión de dos lentes — intento 3: Bloque21 (T-11/T-13/T-14/T-15) — límites JSON pendientes

2026-10-10. A+B+D frescos, fallback genérico sin override; scope0/exact16, interop0/58, ledger0 y fuente990/diff íntegros. C=false; D=true por heurística regex-en-bucle, descartada por D con evidencia de compilaciones fuera del bucle. A3 acepta A2-1 y conserva B1; B3 introduce1 Important/1 Minor, D0. ROOT leyó los tres informes completos, verificó hashes y reprodujo ambos casos. No hay rebatidos ni deuda.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B3-1 | Important | 1e999 llega como infinito en metadata ignorada y valida ok | T-11/T-14 | parse_float comprueba finitud antes de aceptar el número | Probe real:782 bytes/exit0/statusok; pendiente validación correctiva. |
| B3-2 | Minor | JSON muy profundo termina sin envelope | T-11/T-14 | RecursionError devuelve unavailable/exit2, conservando rechazo | Probe real:12000 niveles/24001 bytes/exit1/RecursionError, sin aprobación ni serve. |

La reproducción ROOT sobre R3 intacto y los informes quedan ligados por SHA en la evidencia. El primer probe de2000 niveles devolvió unavailable; se conserva el fallo de su assert privado, sin convertir esa entrada en una reproducción positiva. La reserva siguiente falló por sintaxis del auxiliar antes de ejecutarse; un OWN nuevo conservó intenciones/terminales de los dos probes reales. No hubo mutación de estado, modelos, hosts ni UI.

### Decisión del orquestador tras el límite del ciclo inicial

El ciclo inicial concluye sus tres intentos con B3-1 pendiente y no se declara aprobado. Bajo la delegación del usuario para decisiones técnicas y revisión independiente, ROOT decide continuar con un ciclo correctivo acotado a un solo pase A+B+D sobre estos dos casos reproducidos. Será ciclo2/intento1, cuarto pase acumulado explícito; no reinicia ni oculta los tres resultados anteriores. No reabre criterios aprobados, QA19/20, macros ni catálogo de skills.

RED: `tests/test_plan_review_open.py::test_B3_json_boundaries_fail_closed[overflow_positive]`, `[overflow_negative]` y `[depth]` fallaron en la implementación R3,3 failed/23 deselected/exit1 · 2026-10-10. JUnit SHA `3b84c5758629a3a61f37149f3414dfee932fc4d72df8a7b8c33a7f11761bf77e`. GREEN de autor tras parse_float finito y captura RecursionError:52 passed/0 failed/0 skipped Windows (26 validador/26 shell), JUnit SHA `87f4f2f00852a1a37dc95fa6ba7bd14b64365c575efffa032b09c105e8ae23ab`; mismos IDs/fuente/fixtures y cero modelos/hosts/UI. La revisión correctiva y los checks finales siguen pendientes; no se publicará como aceptado con un Important abierto.


## Revisión de dos lentes — ciclo correctivo 2, intento 1 de 1: Bloque21

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

## Transporte nativo de comandos — Bloque22 en preparación

2026-10-10. T-08/T-09/T-11/T-14/T-15 conservan sus estados. El catálogo de nuevas skills permanece aplazado; los adaptadores generados sólo transportan los workflows de `commands/`. El [contrato](comparisons/codex-command-transport-contract.md) conserva dueño, puertas y argumentos del mensaje invocante.

RED: `tests/test_codex_command_transport.py` falló en sus cinco casos iniciales contra el exporter sin modificar: manifiesto con una sola raíz, adaptador ausente (dos variantes), generación de prompts personales y retirada ausente. Resultado5 failed/0 errors/exit1 · 2026-10-10. JUnit SHA `7b4e9b10233e4793c84416dc51be0d5d28e1369695d54f389af56bb7da8c6d5e`; fuente992 antes/después idéntica, SHA de manifiesto `3bc7de62bd95649c7e73bae0c1029c4dd876c0ab2de33cb94937c086a3fe2b35`. Cero modelos/clientes nativos en este RED. Se añaden negativos de nombres, colisión por nombre declarado y retirada precisa antes de implementar.

La prueba nativa aislada de Codex0.161.0 descubre ambas raíces del plugin desde su caché, con pluginId propio no nulo y SHA iguales a la fuente. El primer filtro privado esperaba nombres sin namespace y dio falso negativo; el reanálisis conserva los mismos frames sin repetir Codex. El nombre real incluye namespace del plugin. Esta observación no acredita inyección, lectura de la referencia ni ejecución del workflow; la verificación ROOT y evidencia pública completa siguen pendientes.

RED ampliado:12 failed/0 errors/1 skipped/exit1,13 casos totales · 2026-10-10. Los negativos de nombres, colisión por `name` declarado y retirada de adaptadores fallan en la fuente previa; el caso de symlink se omite por permiso Windows y no acredita ese guard. JUnit SHA `77df7b04df03eae9ccf99ee11fdc6fdb3867b5c5f8d5c488a36bbd935260c4ce`; fuente992 idéntica antes/después, SHA `0129c6235f5de849a3f60d05c15d2271de55035922d7cba3616d101dfe889165`. ROOT verifica por bytes los cinco pares fuente/caché y los tres frames de entrada/salida de discovery nativo. No ejecuta otro Codex para reanalizar. Implementación y GREEN pendientes.

GREEN inicial de exporter/transporte:47 passed/0 failed/1 skipped Windows; JUnit SHA `1c9290e6f4ad7c073006cd4f6d1687e7e29ea2d174805b78b87f6dfce99c3511`. Generación/check aislados exit0; se adoptan88 outputs,45 archivos de adaptador nuevos y15 prompts antiguos propios retirados con bytes/hash/cabecera verificados. La documentación ES/EN corrige invocación con namespace. Un ajuste posterior cualifica también las skills canónicas en los preámbulos; requiere GREEN final y regeneración antes de revisar.

RED del instalador:3 failed/0 passed/exit1, antes de modificar providers/install; JUnit SHA `898f9ec7a31293f0f65aaa6124646546d0ee6450687e480fce09699a212a13f1`. La primera GREEN falla porque faltaba el árbol generado aún no adoptado; se conserva sin cambiar el oráculo. Tras adoptarlo pasan3/3, más11 regresiones seleccionadas. La migración conserva bytes de prompts globales anteriores y retira sólo su propiedad del manifiesto, sin barrer el home; no existe hash antiguo fiable para eliminarlos. La verificación ROOT y revisión fresca siguen pendientes.

Inyección nativa de fixture observada y verificada por ROOT: una petición incorpora el cuerpo literal completo y Unicode/dólares, ausentes del stdin. Cinco frames enviados,14 recibidos, un POST al proveedor pasivo propio400, cero inferencias/toolcalls, turno failed y recursos propios terminados. El primer ensayo se detuvo por un warning de metadata de modelo sintético; el segundo admite sólo ese warning exacto en OWN nuevo. Se conservan además dos fallos del verificador privado ROOT (Unicode por stdin y ruta de instructionSources), corregidos sólo en el oráculo sin repetir Codex. [Evidencia acotada](testing/codex-command-transport-evidence.json): no acredita carga del adaptador real, lectura de referencias, obediencia, workflow, UI o QA global. Las16 macros y skills aplazadas se conservan.


## Revisión de dos lentes — intento 1: Bloque22 (T-09/T-11/T-14/T-15)

2026-10-10. A+B+D de contexto fresco, fallback genérico sin override; C=false/D=true. Fuente1023 y diff73 conservados por los revisores, exports88 idénticos. ROOT leyó los informes completos y verificó sus SHA y recibos:1 Critical/1 Important/0 Minor. No hay rebatidos ni aceptación.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | B-01: cambio de CODEX_HOME conserva claims externos y uninstall borra bytes personales | T-09/T-15 | Corregido y aceptado en intento2: liberar claims externos con límite del bundle explícito | RED1/GREEN1 y regresiones12; conserva históricos editados y ownership interno |
| 2 | Important | A22-1: índices ES/EN muestran invocación antigua no instalada | T-11/T-15 | Corregido y aceptado en intento2: invocación nativa cualificada en ambos índices | RED6P2F/GREEN8P de los ocho documentos con nombres resolubles |

RED dedicado B-01: `Codex command adapters: B01 ...` falla en la implementación revisada:1 failed/exit1, JUnit SHA `ead5bbd5408e4d202550f1ec1b0a9223925f870268cc9593fc33386b7735d22a`. Prueba con upgrade/uninstall reales, homes propios A/B y CLI simulado; cero modelos/consumers reales. Producción permanece idéntica tras el RED.

Informes A/B/D SHA: `4f3754e2726240f7a37926cc11c531717a3f0b5beef4e7dc8336e216c841961b`, `f23389791daf6b4addfc93ccbf0068bb76a8db25214542afd48a70154c80340e`, `6ec6b19fef5283764adf1f4cd69f1f52970f6b6e49077695b19b03d7a805d8ec`. Fusión ROOT SHA `5980e7e457d6bece289fcf4f905568eeaf80ebac856e1d6d75c84dfd489daa7f`. La siguiente revisión será intento2 de3; no se publica con Critical/Important abiertos ni se cambian las16 macros.


RED dedicado A22-1: las ocho páginas se comprueban contra adaptadores realmente generados;6 passed/2 failed/exit1 en la fuente revisada. Fallan exclusivamente docs/README.md y docs/en/README.md antes de corregirlos. JUnit SHA `5fd16259ba62f92fb7a6ae26473fd1e141f07569ed37d29bf629d51fdb70b006`. Las correcciones ES/EN sustituyen los ejemplos antiguos por invocación con namespace nativo; GREEN y revisión correctiva pendientes.


GREEN dedicado A22-1:8 passed/0 failed/exit0, mismos ocho documentos/IDs y adaptadores generados; JUnit SHA `8204900710d109246c01c74da5a3101386b6c3880e07e42d36b2f7c00558c67d`. Ambos índices ES/EN corregidos. Esta prueba de documentación no sustituye la revisión fresca ni prueba ejecución nativa del comando.


GREEN dedicado B-01:1 passed/0 failed/exit0; JUnit SHA `7fac2f3687f93361b8c5fc0c1e8806a2d59e13c9efccba77437765fb97bd4da5`. Regresiones pertinentes del instalador:12 passed/0 skipped/exit0, JUnit SHA `14a4d2f6ce84435b80a58de7f5bcb85c1cd88f8f04401c8eb8c4c3def92b8288`. ROOT verifica todos los hashes de artefactos y los tres inputs contra producción, recibo SHA `c65876705608025786591df932737e41d3834eb1db3e7bba15d74acc341cb9a1`. El límite del bundle es explícito y los registros externos ambiguos se liberan sin leer ni borrar sus bytes; la prueba conserva prompts históricos editados y la desinstalación interna. La revisión2 y QA congelada siguen pendientes.


## Revisión de dos lentes — intento 2: Bloque22 (T-09/T-11/T-14/T-15)

2026-10-10. Segundo pase de un máximo de3; A+B+D frescos, fallback genérico sin override. C=false/D=true. ROOT lee tres informes completos y verifica hashes/recibos/fuente1023/diff75 y probe directo:1 Critical/1 Important/0 Minor. B-01/A22-1 corregidos y conservados; no hay rebatidos ni aceptación.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | B22-2: uninstall directo legado elimina prompts externos editados | T-09/T-15 | Corregido y aceptado en intento3: liberar claims antes de contar/borrar/podar | Probe real exit0/legacy_exists=false y fuente intacta |
| 2 | Important | A22-2: cabecera y tabla nuevas no las leen brief/Jira | T-11/T-14/T-15 | Corregido y aceptado en intento3: cabecera canónica, seis columnas y # numérico | Header no casa; tabla4 columnas/ID no numérico omite ambas filas |

El borrado directo era previo al diff; B22-2 incumple la nueva garantía contractual sin precondición de upgrade. A22-2 se limita a la nueva sección Bloque22; aviso histórico Bloque21 conservado. Informes A/B/D SHA `9c905b549e4e7cbaa56462a3dc65ce5dd5e19591d6766daa22054dc46abd3a85`, `0eacf79739b78a83091e04168d1a0448fc2d62980aae469b96a4c4234a19f16e`, `8e48460ac420b2a653a68f0353c378ec96bc965814499513912e0d6b3ee3a809`; fusión ROOT SHA `4a53d226fef1b64e52aa5385c699c25a679e02a906f951d59e6bacdedaa4b0ca`. Se conservan dos fallos del verificador privado: ruta relativa de recibo y conteo del padre Node frente a hojas JUnit; corregidos sin repetir pruebas ni alterar producto.

RED dedicado B22-2: project y user fallan al conservar bytes externos tras uninstall directo. JUnit:2 hojas fallidas; Node:3 fallos contando padre+dos subtests; exit1, JUnit SHA `4afdeacbcb9c29dfea18fa8cdac6b8313906fe02b9795f5b8fcad8dfabc66800`. Dry-run previo conserva bytes/manifiesto. Producción intacta; GREEN y revisión3 pendientes. QA final no iniciada; publicación pendiente.


RED dedicado A22-2:2 failed/exit1, JUnit SHA `fe13d69cae6a8968b0bdcf7f784f91e54cbd274f030b63cc60c74ba38a6b6f4d`. Primer caso demuestra cabecera invisible; segundo corrige sólo la cabecera en memoria y demuestra las filas omitidas. Ambos usan el parser canónico real y la sección nueva del ledger, sin reabrir avisos históricos. Corrección: cabecera canónica, seis columnas y # numérico con tarea/evidencia; estados previos aceptados en intento2 conservados. GREEN pendiente.


GREEN dedicado A22-2:2 passed/exit0 sobre el mismo parser canónico, JUnit SHA `0ea9896810368729c7cd12070673a0ab4f4cab3a60d65eaa12afe62b2940ac1b`. La cabecera y las dos filas con tarea/grado/gap vuelven a ser consumibles; el contador máximo3 y veredictos previos permanecen. GREEN dedicado B22-2:2 hojas JUnit/3 contando padre Node,0 failed/exit0, SHA `47d6601824d49dc60e3bc271f9c0a6df09a693a834363ad0af4527cfb9b07b27`; regresiones seleccionadas:14 hojas JUnit/15 Node,0 failed/exit0, SHA `a7ea7ed816ec702ec66be1d0c19e0f1d96804c2afd0d16e62db6b0abe0e49954`. ROOT verifica hashes de todos los artefactos y tres inputs, recibo SHA `dc277409e329e459fac1a97bc10a1f3ee0bf364b671760d6cc36db106cb8f216`. El filtro se aplica antes de contar dry-run/borrar/podar y no lee ni borra bytes externos. Revisión3 y QA congelada pendientes.


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
