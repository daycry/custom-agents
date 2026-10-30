---
tasks: modular-integrations
estado: completado
creado: 2026-10-30
verificacion: obligatoria
changelog: Changed
test-plan: n/a (sin UI nueva)
---

# Núcleo modular e integraciones por proyecto

Ledger canónico.

El usuario autoriza adoptar el modelo modular de ECC, con criterio de utilidad, evitando incorporar propuestas solo para ampliar el catálogo. Jira/Confluence pasan a ser integraciones opcionales. Cada proyecto puede elegir Redmine, una wiki u otros proveedores mediante herramientas y extensiones propias. Se exige robustez, compatibilidad y separación verificable para múltiples proyectos/usuarios.

Ampliación autorizada: el usuario permite cambios incompatibles en una versión mayor y pide documentación extensa de workflows del core, Atlassian/Redmine, tareas/fases/comentarios/estados y personalización de personas, agentes, skills, tools y MCP. No se exige conservar contratos obsoletos a costa del diseño; cualquier compatibilidad conservada será explícita y comprobada.

Base de esta continuación: `707d4ad67c89dca5f74d564ca7be18b2b8ee2e16`. Se preserva la PR22 existente; esta iniciativa amplía su alcance y reescribirá su presentación al entregar. No se reabren las optimizaciones canceladas ni se añaden automáticamente las 37 propuestas. `.claude/settings.json` personal no se lee, edita ni incluye en commits. Implementación por ROOT, sin delegación; revisores independientes según skill.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Contratos | 3 | 3 | 100.0% |
| Fase 2 — Integración | 3 | 3 | 100.0% |
| Fase 3 — Entrega | 2 | 2 | 100.0% |
| **TOTAL** | **8** | **8** | **100.0%** |

## Fase 1 — Contratos

### T-01 — Arquitectura y criterio de admisión

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Definir núcleo, módulos opcionales, integraciones de proyecto y límites de instalación nativa; revisar las seis skills nuevas y las 37 candidatas sin incorporarlas en bloque.
- **Changelog**: Arquitectura y criterio de admisión.
- **Archivos**: `docs/roadmap/2026-10-30-modular-integrations/**`
- **Verificación**: `lectura de contratos y matriz; ledger-lint exit 0` → exit 0.

**Criterios de aceptación**
- [x] Cada decisión conserva motivo, dueño y evidencia; no se presenta a ECC como DDD ni selección lógica como instalación física.

### T-02 — Catálogo y selección determinista de módulos

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Catálogo versionado de módulos/perfiles y cierre de dependencias, con exclusiones explícitas y origen de cada selección. Jira y Confluence son módulos opcionales.
- **Changelog**: Catálogo y selección determinista de módulos.
- **Archivos**: `agent-kits/shared/modules.json`, `install/modules.mjs`, `agent-kits/shared/module-selection.py`, `tests/module-selection.test.mjs`, `tests/test_module_selection.py`, `docs/roadmap/2026-10-30-modular-integrations/**`
- **Verificación**: `node --test tests/module-selection.test.mjs; python -m pytest -q tests/test_module_selection.py` → exit 0.

**Criterios de aceptación**
- [x] Selección válida, determinista y sin dependencias rotas; entradas inválidas/ciclos/conflictos no producen escrituras; los dos lectores coinciden.


RED: `tests/module-selection.test.mjs + tests/test_module_selection.py` falló con New selection API absent: Node 4 failed, Python 6 failed before implementation; negative test fixed to assert API availability outside assert.throws. · 2026-10-30.

### T-03 — Puertos de integración por proyecto

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Resolver configuración local versionada por función, adaptadores propios o de proyecto, eventos y capacidades declaradas; sin ejecutar código del proyecto ni llamadas remotas. Compatibilidad de lectura con opt-ins Jira/Confluence existentes.
- **Changelog**: Puertos de integración por proyecto.
- **Archivos**: `agent-kits/shared/integration-route.py`, `agent-kits/shared/project-integrations.md`, `agent-kits/shared/README.md`, `tests/test_integration_route.py`, `docs/examples/integrations/**`, `docs/roadmap/2026-10-30-modular-integrations/**`
- **Verificación**: `python -m pytest -q tests/test_integration_route.py` → exit 0.

**Criterios de aceptación**
- [x] Ausente, desactivada, inválida y declarada son distinguibles; aislamiento entre proyectos, lectura acotada, rutas confinadas, sin secretos en salida; declaración no concede disponibilidad ni permiso.


RED: `tests/test_integration_route.py` falló con Project router absent: 11 failed and 1 platform symlink skip before implementation. · 2026-10-30.

## Fase 2 — Integración

### T-04 — Entrega selectiva y perfiles

- **Estado**: completado
- **Tipo**: devops
- **Descripción**: Aplicar selección al export portable y modos de copia compatibles; conservar límites de los plugins nativos sin personalizar su caché. Actualizar/status/uninstall preservan archivos ajenos o modificados.
- **Changelog**: Entrega selectiva y perfiles.
- **Archivos**: `install/install.mjs`, `install/providers.mjs`, `scripts/export-skills.py`, `tests/installer.test.mjs`, `tests/test_export_skills.py`, `tests/test_install_profiles.py`, `tests/profile-delivery.test.mjs`, `docs/roadmap/2026-10-30-modular-integrations/**`
- **Verificación**: `suites dirigidas de instalador/export y fixtures aisladas en Windows/Linux` → exit 0.

**Criterios de aceptación**
- [x] El plan enumera el contenido real; selección inválida falla antes de escribir; reinstalación y cambio de perfil no borran ni adoptan modificaciones ajenas; nativo completo no se anuncia como filtrado.

### T-05 — Núcleo desacoplado de proveedores

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Sustituir instrucciones de proveedor en roles/comandos por el puerto compartido; mantener archivos locales canónicos, puertas QA/TDD y eventos de sincronización opt-in. Setup y doctor muestran integraciones configurables por proyecto.
- **Changelog**: Núcleo desacoplado de proveedores.
- **Archivos**: `agents/**`, `commands/**`, `agent-kits/shared/**`, `agent-kits/planner/**`, `agent-kits/qa/**`, `agent-kits/dev-cycle/references/phase2-planning.md`, `tests/test_integration_decoupling.py`, `tests/test_setup*.py`, `tests/test_review_jira_owner.py`, `tests/test_dev_cycle_split.py`, `tests/fixtures/dev-cycle-modular-replacements.json`, `tests/fixtures/opencode-v2-agent-contract.json`, `tests/test_panel_fix1.py`, `docs/roadmap/2026-10-30-modular-integrations/**`
- **Verificación**: `tests de desacoplamiento y regresiones de flujos; export-interop --check` → exit 0.

**Criterios de aceptación**
- [x] Sin integración se completa el ciclo local; adapters no cambian estado canónico ni relajan guardias; configuración heredada mantiene su alcance y no se migra ni se instala de forma silenciosa.

### T-06 — Adaptadores opcionales y extensiones abiertas

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Adaptar Jira/Confluence al contrato genérico y documentar una extensión Redmine/wiki de proyecto, con selección de herramientas reales y validación de operaciones, recibos y resultados inciertos.
- **Changelog**: Adaptadores opcionales y extensiones abiertas.
- **Archivos**: `skills/jira-sync/**`, `skills/confluence-publish/**`, `skills/confluence-pull/**`, `skills/adversarial-review/**`, `skills/backend-practices/references/pipeline-throughput.md`, `skills/delivery-practices/references/agent-assisted-delivery.md`, `agent-kits/shared/confluence-optin.md`, `agent-kits/shared/jira-optin.md`, `agent-kits/shared/atlassian-transport.md`, `tests/test_integration_adapters.py`, `tests/test_integration_decoupling.py`, `skills/jira-sync/scripts/jira-flow.py`, `docs/examples/integrations/**`, `docs/roadmap/2026-10-30-modular-integrations/**`
- **Verificación**: `fixtures de contratos con proveedor alternativo, adaptadores heredados y permisos/capacidades insuficientes` → exit 0.

**Criterios de aceptación**
- [x] No hay lista cerrada de proveedores; herramientas elegibles por proyecto, sin conexión ni ejecución por estar declaradas; recibos no inventados y sin doble escritura por resultado incierto.

## Fase 3 — Entrega

### T-07 — Documentación, descubrimiento y exports

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Crear manual extenso de personalización y workflows con ejemplos Atlassian/Redmine, roles/personas/agentes/skills/tools/MCP, transiciones/comentarios y migración de versión mayor. Sincronizar contrato público, configuración, mapas, descripciones, evals y exports; distinguir catálogo, instalación, selección y disponibilidad.
- **Changelog**: Documentación, descubrimiento y exports.
- **Archivos**: `README.md`, `README.es.md`, `CLAUDE.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `package.json`, `.gitattributes`, `.claude-plugin/**`, `.codex-plugin/**`, `.agents/plugins/**`, `interop/**`, `evals/**`, `tests/test_console_encoding.py`, `docs/README.md`, `docs/en/README.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/PROJECT-EXTENSIONS.md`, `docs/en/PROJECT-EXTENSIONS.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/CUSTOMIZATION.md`, `docs/en/CUSTOMIZATION.md`, `docs/guides/**`, `docs/en/guides/**`, `output/pdf/**`, `docs/agents/**`, `docs/en/agents/**`, `docs/roadmap/**`
- **Verificación**: `lint_plugin; evals/check; export-interop --check; tests de manifiestos/export/discovery` → exit 0.

**Criterios de aceptación**
- [x] Docs ES/EN y generación coinciden con la implementación; no hay autoactivación de integraciones o 37 altas sin justificar.

### T-08 — Revisión, regresiones y publicación de rama

- **Estado**: completado
- **Tipo**: devops
- **Descripción**: Revisión independiente A/B y C/D condicionales, cobertura oficial y regresiones de selección, aislamiento, compatibilidad y cancelación; commits literales, push/PR y CI verde.
- **Changelog**: Revisión, regresiones y publicación de rama.
- **Archivos**: `docs/roadmap/2026-10-30-modular-integrations/**`, `docs/roadmap/README.md`, `docs/roadmap/CALIBRATION.md`
- **Verificación**: `suites dirigidas y amplia, Node, cobertura mínima 90%; CI del commit final` → exit 0.

**Criterios de aceptación**
- [x] Evidencia sin fallos pendientes; no se alteran cachés/configuración reales; no se publica release nueva sin petición; cierre con retro y mediciones ausentes explícitas.

RED T-02 adicional: catálogo inaccesible desde el kit copiado y selección vacía aceptada (Python 2 failed); identificador constructor colisiona con prototipo y selección vacía aceptada (Node 2 failed/4 passed), antes de corregir. El catálogo canónico se ubica en shared para viajar en los modos copiados, sin duplicarlo en install/.

RED T-03 adicional: dependencias del bundle defectuosas propagaban RuntimeError/AttributeError (2 failed, 15 deselected). Se corrigen después del rojo. Un caso de fixture sobredimensionado necesitó IDs cortos explícitos en pytest para no exceder rutas Windows; ese error de fixture no cuenta como rojo del producto.

RED T-04: exportador de perfiles 5 failed por argumentos/CLI ausentes; plan de copias 3 failed por API ausente, y binarios distintos compartían hash tras decodificar (regresión dedicada roja antes de corregir). El check del portable core detectó 7 referencias obligatorias a módulos opcionales; se sustituyeron por selección explícita bajo demanda y fallback operativo, sin relajar el checker.

RED T-05/T-06: desacoplamiento 8 failed antes de editar roles/comandos; adapters 3 failed tras corregir una clave errónea del fixture. Configuración de ejemplo no cubría review.completed (1 failed) antes de completar eventos/capacidades.

Ampliación de entrega autorizada: PDF moderno con toda la documentación detallada, ejemplos y workflows, para responsables de área. La fuente Markdown y el PDF deben identificar por paso comandos, agentes, skills, herramientas, configuración, artefactos, decisiones/gates y recuperación. Se usa skill pdf para autoría y revisión visual.

Verificación intermedia: Node selección/propiedad 10 passed; CLI selectiva 3 passed; exclusiones persistidas 1 passed tras rojo; Python integración/selección 33 passed + 1 skip inicial. Regresión dirigida doctor/Jira/export/tamaño: 364 passed, 1 skip (antes de los ajustes finales de README/perfiles). README protegido + export: 21 passed. Se repiten checks cuando el contenido final esté fijado.

## Revisión de dos lentes — intento 1: Arquitectura modular, integración y manual (T-01, T-02, T-03, T-04, T-05, T-06, T-07)

Resultado histórico: cinco Important; correcciones con regresión remitidas al intento 2.

Revisión intento 1: lentes genéricas frescas A/B/C/D (este entorno no expone despacho nativo reviewer). A: A-01 mapa Confluence 206>200, A-02 descriptores E3 con proveedor antiguo, A-03 salidas PDF/panel obligatorias con módulos excluidos; B: edición concurrente tras preflight sobrescrita; C: sin hallazgos; D: manifiesto O(N²), full509 archivos/509 escrituras/65.790.680 bytes frente a8 escrituras/350.252 bytes sin perfil. Todos Important, ninguno rebajado.

RED fixes intento 1: tres tests dedicados A-01/02/03 fallaron antes de corregir; test D observó30 checkpoints en un grupo de30 archivos; test B observó ausencia de revalidación. Después se agruparon checkpoints por payload, se guardan hashes previos y se revalida antes de cada reemplazo, sin fallback in-place. Las expectativas de propiedad por intento se trasladan al puerto neutral manteniendo prueba real de comentarios Jira.

Evidencia de revisión: [testing/review-1.md](testing/review-1.md). Regresiones A:11 passed; Node API/propiedad:12 passed; CLI perfiles/exclusiones/race/checkpoints:6 passed. Caso B ahora rechaza la reinstalación y conserva exactamente CONSUMER EDIT DURING REINSTALL. Caso D mantiene ≤8 checkpoints para >400 archivos.

## Revisión de dos lentes — intento 2: Correcciones de los cinco Important del intento 1 (T-01, T-02, T-03, T-04, T-05, T-06, T-07)

Resultado histórico y correcciones documentados en el informe de ese intento.

Adaptación explícita del contrato lossless de F2: el baseline histórico dev-cycle-paragraphs.json permanece intacto. Cinco párrafos afectados por el desacoplamiento aprobado tienen correspondencia SHA antes/después, archivo dueño y motivo en dev-cycle-modular-replacements.json; todos los demás hashes, recetas Bash/PowerShell y gates conservan comprobación exacta. Las rutas lazy nativas exigen las referencias del core y el puerto genérico; phase3-jira queda como referencia opcional, sin ruta obligatoria desde core. Se observaron cuatro fallos de la expectativa antigua antes de esta adaptación, no se rebaja un umbral.

## Revisión de dos lentes — intento 3: Recuperación parcial y contrato final del núcleo (T-01, T-02, T-03, T-04, T-05, T-06, T-07)

Lentes B/C/D sin defectos pendientes. A observó A04 Important de evidencia y A05 Minor antes del delta final; la regresión dedicada y corrección de ambos espejos se verifican por ROOT, conservando el veredicto original en testing/review-3.md.

Revisión intento 2: [testing/review-2.md](testing/review-2.md). A01/A02/A03, B01 yD01 corregidos; C sin hallazgos; residuo A04Minor corregido en ambosFLOWS. B02Important nuevo sobre recuperación de propiedad tras upgrade abortado/SIGTERM: ambas regresionesCLI observadas rojas antes de conservar hashes propios anteriores/planificados y archivos no retirados. Cuatro regresionesCLI B/D/B02/SIGTERM verdes. Pendiente juicio del intento 3, no aprobación por el implementador.

A04/A05: test dedicado `test_gaps_a04_a05_phase3_descriptions_use_the_optional_adapter` nombra ambos residuos y comprueba la explicación general y la tabla Jira opcional en ambos idiomas. A05 observado rojo antes de corregir. A04 era una corrección de prosa ya observada por la lente, ahora con regresión constitucional explícita; no se alega un rojo nuevo de A04 que no ocurrió.

Commit de implementación e6fcac2: selección literal de132 archivos, blobs/modos y HEAD/index/worktree verificados; configuración personal excluida. Lectura total del patch inicial repartida en cinco particiones disjuntas, más lectura ROOT de los seis chunks finales modificados (17.503caracteres). Recibos y hashes en el informe final de revisión. PDF y cierre del roadmap se entregan en commit documental separado.

Cierre del delta documental: README ES/EN de raíz y docs/ conservaban PDF obligatorio.
La regresión dedicada A03 se amplió a las cuatro entradas y falló antes de corregir;
después 16 casos de desacoplamiento/manifiestos/badges pasan. PDF de39páginas revisado
completo, SHA/QA en testing/pdf-manifest.json y testing/pdf-qa.md; commit189b7b9.
.gitattributes marca PDF binario para conservar bytes en Windows; blob publicado
idéntico al artefacto revisado. No se modificaron las fuentes Markdown del PDF tras generarlo.

Ajustes de validación final, sin cambiar runtime: fixture OpenCode del documenter
actualizada al puerto neutro (50 passed); description del marketplace Claude
sincronizada (4 passed); rango descriptivo de imports ampliado hasta importsys;
contrato ASCII JSON del router declarado y medido en la suite de consola;
guarda de panel prueba éxito del dashboard y disponibilidad del renderer.
Se añaden regresiones CLI reales de status/exit/noexecution y paridad de rechazos
Python/Node;50 passed,1 skip. Un NameError del test nuevo se corrigió antes de validar;
no se presenta como rojo del producto. QA/CI continúan en T-08.

QA Linux sobre overlay actual:983 passed,2 skipped en205,49s. Gate oficial de cobertura
changed-only:91,55% (mínimo90%), cinco fuentes Python, sin archivos sin datos.
Node Windows:467 tests,464 passed,2 skip y1 TODO preexistente;0 fallos no esperados,
exit 0. Cobertura de los dos fuentes JS cambiados:96,59% líneas.
La pasada Linux inicial instrumentada y sus17 fallos permanecen trazados en el
informe final; no se reetiquetan como verdes. La comprobación de tiempo de redactor
local sin instrumentar quedó justo fuera del presupuesto(1,501s frente a1,5s);
no se altera ese umbral ni su código y se contrasta con la CI de referencia.

Cierre de T-08: CI7241e0e verde (run41144112195), suite Linux actual983 passed/2 skipped,
Node Linux451 passed/16 skipped, coberturas oficiales91,55% Python y96,59% JS.
El caso de coste del redactor pasó tras terminar el descendiente propio verificado;
los fallos anteriores y las limitaciones Windows quedan en testing/report.md.
Gate determinista VERDE sobre diez comprobaciones, sin simular E2E. Meter QA cerrado:
sin medida compatible, tokens/coste/esfuerzo IA null. Retro y calibración sin nueva muestra.
PDF final39páginas, hashes UTF-8/LF de sus once fuentes cotejados con Git.
Solo cambió el hash de catálogo en página39 respecto a189b7b9; se renderizó/revisó otra vez.
El push del cierre documental se somete además a CI en el HEAD de la PR antes de entregar.
