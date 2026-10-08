---
tasks: catalog-capabilities
estado: en-progreso
creado: 2026-10-07
actualizado: 2026-10-08
verificacion: obligatoria
changelog: Changed
---

# Capacidades del catálogo — ledger

> Ledger canónico. Fuente única de progreso de la fase 3.

Autorización: integración por fases, decisiones técnicas delegadas y push
cuando esté listo. Base 6187b12; rama feat/catalog-capabilities. No PR,
integración en main ni release. Settings ajenos intactos y fuera del índice.
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
- **Verificación**: Contratos iniciales OpenCode 2.0.12 y Codex 0.160.1 conservados en runtime-probes.json/contracts.md; transporte OpenCode V2 validado después, con guardias pendientes. Nuevas fixtures aisladas Claude 2.1.287 (binario fijado): contexto/captura UTF-8 positivos, envelope ausente con presupuesto predeterminado y presente con override propio 5.000 ms; control lento propio y recuperación de checkpoint ejecutados. Codex se actualizó a 0.161.0: nueva copia/fuente fijadas, caché ausente tras instalador, add activa pero cambia enabled global, contexto/captura positivos con bypass de fixture; evento terminal no observado en exec y causa pendiente. claude-hook-evidence.json y codex-activation-evidence.json separan versiones, resultados y límites. Confianza persistida, identidad/allow-deny por rol y cierre efectivo siguen pendientes.
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
- **Verificación**: Triaje operativo iniciado con contratos/probes y valoración de memoria en operational-priorities.md. Comparación funcional completa, implementación y validación de despacho pendientes; la lectura dirigida no acredita eficacia.
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
- **Verificación**: design.md abre el bloque de integridad del checkpoint con defectos comprobados en captura/rotación, alternativas y criterios. Diseño restante de runtime/capacidades pendiente; no se declara consolidación global entregada.
- **Diseño operativo en curso (2026-10-08)**: Panel de catálogo, diagnóstico de consumidor y roadmap conservan responsabilidades separadas. Handoff propuesto reutiliza journal/ledger; observaciones requieren fuente compatible antes de tasas. Codex add habilita globalmente aunque el destino sea proyecto; T-09 debe resolver caché nativa respetando el estado global previo, sin remove como rollback ni confundir installed con enabled. Estos destinos y restricciones no acreditan implementación.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

- **Ajuste de personas para T-08/T-09/T-11/T-13/T-15**: el usuario pidió organización por entorno como los agentes y después contrastar los estándares de Codex/OpenCode. [Contraste documental](contracts.md#personas-e-instrucciones-nativas): las carpetas nuevas `.codex/personas/` y `.opencode/personas/` serían convenciones del plugin, no cargadores nativos documentados; la propuesta anterior queda provisional y no se implementará como supuesto estándar. Priorizar agentes e instrucciones nativos para especialistas invocables; conservar perfiles acotados del brief cuando solo complementan un rol, sin agentes duplicados. Mantener compatibilidad de `.claude/personas/` existente. T-08 debe cerrar almacenamiento y composición, selección con runtime all, duplicados, instalación personal, rutas personalizadas y avisos; inventario y brief deben resolver la misma procedencia y conservar sus límites. Distinguir OpenCode V1 agent/prompt de V2 agents/system; no usar personality de Codex para perfiles de dominio. Actualizar panel, documentación y exports con pruebas de carga y contenido efectivo en T-14. Contraste registrado, implementación pendiente.

### T-09 — Guardias y despacho nativo multi-runtime

- **Estado**: en-progreso
- **Descripción**: Implementar mecanismos reales por contrato y versión para Claude/Codex/OpenCode, incluido soporte V2; probar identidad, concurrencia y degradación.
- **Dependencias**: T-02/T-08.
- **Archivos**: `hooks/**`, `interop/**`, `agent-kits/shared/**`, `scripts/**`, `install/**`, `tests/**`, `agents/**`, `docs/**`
- **Verificación**: Bloque de checkpoint implementado y revisado: opt-out coherente, rotación atómica/lectura acotada, CLI portable y reclamación exclusiva con identidad comprobada y errores de transacción visibles. QA final Windows: 200 passed/12 skipped; Linux: 212 passed. Launcher: 12 passed tras las correcciones. Cobertura ejecutable añadida combinada Windows/Linux: 50/53, 94,34%. Evidencia y límites en el segundo intento de revisión. Guardias por rol y carga/despacho nativos pendientes; no se da T-09 por completada.
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
- **Verificación**: Bloque de checkpoint: Windows/Linux y launcher en verde, diff ejecutable 94,34%, A+B sin gaps pendientes en intento 2; qa-gate VERDE a partir de resultados pytest reales. Detalle al final del ledger. Pendientes para la iniciativa: despacho nativo, demás escenarios/capacidades, UI Edge y aceptación completa.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-15 — Limpieza, distribución y documentación

- **Estado**: en-progreso
- **Descripción**: Retirar recursos y callers sustituidos, refrescar dependencias/manifiestos/exports y docs ES/EN; comprobar referencias y nombres públicos.
- **Dependencias**: Verificación del bloque pertinente de T-14 para docs/exports de cada entrega; aceptación global tras completar T-14.
- **Archivos**: `skills/**`, `agents/**`, `commands/**`, `agent-kits/**`, `scripts/**`, `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `.claude-plugin/**`, `docs/**`, `README.md`, `README.es.md`, `CLAUDE.md`, `tests/**`, `evals/**`
- **Verificación**: Pendiente: linter, exports, evals, manifiestos, tamaño, copias y scan de marca sin hallazgos; cero aliases vacíos o callers obsoletos.
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
