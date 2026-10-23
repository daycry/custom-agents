---
tasks: project-extensions
estado: completado
creado: 2026-10-06
actualizado: 2026-10-07
verificacion: obligatoria
changelog: Added
generacion:
  inicio: 2026-10-06T15:27:09Z
  fin: 2026-10-07T09:22:58Z
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  duracion: null
  duracion_reloj: 17h 56m
  ratio_usado: 531798.5
  ratio_origen: CALIBRATION.md (mediana de 6)
---

# Extensiones de proyecto — ledger

> **Ledger canónico de progreso.** Fuente única de esta iniciativa.

Autorización: fases de integración y decisiones técnicas delegadas por el usuario;
push cuando esté listo. Sin PR, merge ni release. Base b067099. Rama propia
feat/project-extensions; settings preexistentes no se modifican ni versionan.
Meter cerrado en estado privado, ventana parcial declarada; sin consumo
compatible no se inventan cifras.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 10 | 10 | 100% |
| **TOTAL** | **10** | **10** | **100%** |

## Fase 1 — Reconocimiento e integración

**Estado**: completado

### T-01 — Contratos y arquitectura de extensiones

- **Estado**: completado
- **Descripción**: Contratos y arquitectura de extensiones.
- **Changelog**: Define contratos nativos y límites del reconocimiento de extensiones en los tres runtimes.
- **Dependencias**: Primera fase publicada.
- **Archivos**: `docs/roadmap/2026-10-06-project-extensions/**`, `docs/roadmap/README.md`, `docs/INTEGRATION-ROADMAP.md`, `docs/en/INTEGRATION-ROADMAP.md`
- **Verificación**: Contratos oficiales enlazados y contraste nativo documentado en contracts.md; revisión A, intento 3, sin gaps pendientes de esta tarea.
**Criterios de aceptación**:
  - [x] Contrato de spec.md comprobado para esta tarea; límites y errores cubiertos, sin gaps pendientes.


### T-02 — Descubrimiento multi-runtime acotado

- **Estado**: completado
- **Descripción**: Descubrimiento multi-runtime acotado.
- **Changelog**: Reconoce agentes, skills, personas, fuentes de tools y MCP locales sin ejecutarlos ni exponer su configuración privada.
- **Dependencias**: T-01.
- **Archivos**: `agent-kits/shared/project-pieces.py`, `tests/test_project_pieces.py`, `tests/test_console_encoding.py`
- **Verificación**: Baseline incluido en Windows 698 passed/2 skipped; delta YAML 239 passed/2 skipped y Linux 702 passed/1 skipped. A/B del ciclo QA revalidan siete casos cada uno sin gaps; detalle y evidencia en testing/report.md.
**Criterios de aceptación**:
  - [x] Contrato de spec.md y caso YAML sin sangría revalidados; límites y errores cubiertos, sin gaps pendientes.


### T-03 — Propiedad, identidad y colisiones verificables

- **Estado**: completado
- **Descripción**: Propiedad, identidad y colisiones verificables.
- **Changelog**: Distingue propiedad e identidad y muestra conflictos de origen e invocación sin sobrescribir piezas propias.
- **Dependencias**: T-02.
- **Archivos**: `agent-kits/shared/project-pieces.py`, `tests/test_project_pieces.py`
- **Verificación**: O1 completo, hashes LF, huérfanos, identidad y colisiones cubiertos en el lector; pruebas dirigidas A/B del intento 3 y fixtures independientes de aliases, selección y redacción verdes.
**Criterios de aceptación**:
  - [x] Contrato de spec.md comprobado para esta tarea; límites y errores cubiertos, sin gaps pendientes.


### T-04 — Selección explícita compartida de extensiones

- **Estado**: completado
- **Descripción**: Selección explícita compartida de extensiones.
- **Changelog**: Comparte la selección explícita de extensiones entre los roles y la tarea mediante IDs y procedencia.
- **Dependencias**: T-03.
- **Archivos**: `agent-kits/shared/capability-check.md`, `agent-kits/shared/project-pieces.py`, `commands/work-context.md`, `tests/test_project_pieces.py`
- **Verificación**: Selección por ID, runtime y raíces, hasta 20 referencias, cubierta en lector/briefs; revalidación del contrato común por A/B sin gaps.
**Criterios de aceptación**:
  - [x] Contrato de spec.md comprobado para esta tarea; límites y errores cubiertos, sin gaps pendientes.


### T-05 — Briefs y personas de proyecto

- **Estado**: completado
- **Descripción**: Briefs y personas de proyecto.
- **Changelog**: Transfiere referencias acotadas al brief y conserva la prioridad de personas del proyecto.
- **Dependencias**: T-04.
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/shared/project-pieces.py`
- **Verificación**: 89 tests de task-brief incluidos en Windows final; transferencia real, fences, bajas, persona, instalación parcial y presupuesto verificados; revisión sin gaps.
**Criterios de aceptación**:
  - [x] Contrato de spec.md comprobado para esta tarea; límites y errores cubiertos, sin gaps pendientes.


### T-06 — Extensiones en panel con fuentes y conflictos

- **Estado**: completado
- **Descripción**: Extensiones en panel con fuentes y conflictos.
- **Changelog**: Muestra las extensiones propias en el panel con búsqueda, filtros, fuentes y conflictos identificables.
- **Dependencias**: T-03/T-04.
- **Archivos**: `skills/plugin-panel/**`, `tests/test_plugin_panel.py`, `evals/cases/skill-plugin-panel.json`, `evals/cases/command-plugin-catalog.json`
- **Verificación**: Edge extensiones 4 passed/0 failed/0 skipped (22,5 s), más bundle previo 7 passed (15,1 s). Tests Python del panel incluidos en los 132 passed/2 skipped; capturas inspeccionadas.
**Criterios de aceptación**:
  - [x] Contrato de spec.md comprobado para esta tarea; límites y errores cubiertos, sin gaps pendientes.


### T-07 — Workflow, distribución y documentos bilingües

- **Estado**: completado
- **Descripción**: Workflow, distribución y documentos bilingües.
- **Changelog**: Integra el método compartido, exports y documentación bilingüe con distribución portable comprobada.
- **Dependencias**: T-05/T-06.
- **Archivos**: `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `agents/**`, `commands/**`, `docs/**`, `agent-kits/shared/README.md`, `skills/plugin-dev/**`, `evals/cases/command-work-context.json`, `CLAUDE.md`, `README.md`, `README.es.md`
- **Verificación**: Export --check, 54 ficheros al día; evals 182 casos/0 errores; linter 0 errores/3 avisos históricos. Distribución portable y documentos ES/EN revisados por A, intento 3.
**Criterios de aceptación**:
  - [x] Contrato de spec.md comprobado para esta tarea; límites y errores cubiertos, sin gaps pendientes.


### T-08 — Revisión, cobertura y QA multi-runtime

- **Estado**: completado
- **Descripción**: Revisión, cobertura y QA multi-runtime.
- **Changelog**: Verifica parsing, privacidad, selección, briefs y panel en Windows, Linux y Edge con revisión independiente y hace portables las pruebas de release.
- **Dependencias**: T-07.
- **Archivos**: `tests/**`, `docs/roadmap/2026-10-06-project-extensions/testing/**`
- **Verificación**: Gates técnicos de testing/report.md ejecutados; cobertura de producción 92,16% (741/804). Cierre adicional: release Windows 27 passed/62,39 s, Linux 27 passed/3,86 s; docs Windows 557 passed/25,96 s. Ciclos inicial, YAML y fixtures terminan sin gaps ni deuda.
**Criterios de aceptación**:
  - [x] Contrato verificado con evidencia ejecutada y sin gaps pendientes.


### T-09 — Retro, estados y changelogs

- **Estado**: completado
- **Descripción**: Retro, estados y changelogs.
- **Changelog**: Registra resultados, límites y retrospectiva de la integración y sincroniza las notas de cambios.
- **Dependencias**: T-08.
- **Archivos**: `docs/**`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificación**: Retro e informe QA finales, meter compatible nulo, estados consistentes y changelogs ES/EN sincronizados. Changelog --check sin pendientes y ledger-lint 0 incoherencias/0 avisos; publicación técnica observada y cierre documental comprobado.
**Criterios de aceptación**:
  - [x] Contrato verificado con evidencia ejecutada y sin gaps pendientes.


### T-10 — Push y comprobación remota

- **Estado**: completado
- **Descripción**: Push y comprobación remota.
- **Changelog**: Publica la rama de extensiones y contrasta su SHA con el remoto sin merge ni release.
- **Dependencias**: T-08 y entrega documental de T-09; las notas y estados finales se confirman después del primer push verificado.
- **Archivos**: `docs/roadmap/2026-10-06-project-extensions/tasks.md`
- **Verificación**: Push observado de 9f591ac707f96a0a191db2f9d62efdec3418819d; git ls-remote coincide exactamente con HEAD el 2026-10-07. El commit documental final conserva este delivery como ancestro y se publica después de sus gates.
**Criterios de aceptación**:
  - [x] Contrato de spec.md comprobado; límites y errores cubiertos, sin gaps pendientes.

## Evidencia

TDD n/a: prosa y planificación. Los tests de parsing/descubrimiento preceden
al código; RED se registra con resultado y fecha. No se anticipa disponibilidad
de sesión, adopción de piezas, gates finales ni publicación.

RED: T-02 test_discovers_native_agents_skills_personas_and_tools_without_execution
falló por módulo ausente; después, la API mínima sin lector produjo 15 failed /
1 skipped (privilegio symlink) en los escenarios de declaración, scopes, MCP,
JSONC, colisiones, límites, redacción, propiedad y confinamiento; 2026-10-06.
Evidencia privada: scratchpad/.venv/project-pieces-contract-red.xml.

GREEN inicial: 15 passed/1 skipped (privilegio symlink). La fixture de hash se
corrige para escribir LF explícito; Windows había convertido LF a CRLF antes
de crear la variante, duplicando CR. Producción no cambia para ese caso.
RED ampliado: 7 failed/16 passed/1 skipped para roles declarados en config,
confinamiento de config_file, raíz personalizada, comandos OpenCode, MCP de
agente, tools declaradas y caracteres de control; 2026-10-06.
Evidencia privada: scratchpad/.venv/project-pieces-expanded-red.xml.

GREEN ampliado: 23 passed/1 skipped; XML privado
scratchpad/.venv/project-pieces-expanded-green.xml.

RED propiedad: 6 failed/25 passed/1 skipped; el lector aceptaba cinco formas
inválidas del registro como gestionadas y no informaba destinos huérfanos;
2026-10-06. XML privado: scratchpad/.venv/project-pieces-registry-red.xml.

GREEN propiedad: 31 passed/1 skipped (privilegio symlink); validación completa
de las filas O1 antes de atribuir propiedad y aviso de destinos huérfanos.
XML privado: scratchpad/.venv/project-pieces-registry-green.xml.
El lector sigue sin conexión al selector, briefs o panel; no hay cierre de
T-02/T-03, revisión final, QA multi-plataforma ni push de esta fase todavía.

RED selección: 8 failed/31 passed/1 skipped; faltaban colisiones con el bundle,
selección por ID, límites y filtro de runtime; dos raíces personales distintas
producían la misma identidad. XML privado: project-pieces-selection-red.xml;
2026-10-06.

GREEN selección: 39 passed/1 skipped; XML privado
scratchpad/.venv/project-pieces-selection-green.xml.
RED briefs: 6 failed/83 deselected; no existía la sección de extensiones ni los
argumentos de runtime/raíces. Casos: transferencia real, fences, destino borrado,
campos ambiguos, instalación parcial y veinte referencias extensas; 2026-10-06.
XML privado: scratchpad/.venv/brief-extensions-red.xml.

GREEN lector + briefs: 128 passed/1 skipped; selección compartida y referencias
de extensiones incorporadas al brief sin cuerpos y con límite de 1000 caracteres.
XML privado: scratchpad/.venv/project-extensions-brief-green.xml.
RED hardening: 7 failed/39 passed/1 skipped para presupuesto total, instalación
parcial, tools/permission de OpenCode y MCP por agente Claude; 2026-10-06.
GREEN hardening: 135 passed/1 skipped (lector + briefs). XML privado:
scratchpad/.venv/project-extensions-hardening-green.xml.
RED límites: 3 failed/46 passed/1 skipped; las lecturas rechazadas no consumían
presupuesto, la indentación de cuatro espacios se rechazaba y un campo MCP
vacío duplicado se combinaba en silencio. XML privado:
scratchpad/.venv/project-pieces-budget-red.xml; 2026-10-06.

GREEN límites: XML final comprobado tras retomar la sesión: 138 passed/1 skipped,
0 errores/fallos, 19,598 s; scratchpad/.venv/project-extensions-budget-green.xml.
RED panel: 6 failed/26 passed/1 skipped, faltaba recibir raíces/runtime,
representar extensiones y conservar el bundle ante fallo del lector; 2026-10-07.
GREEN panel: 32 passed/1 skipped; XML privado panel-extensions-green.xml.
Edge: P-01…P-04, 4 passed/0 failed/0 skipped, 19,1 s; fixtures de los tres
runtimes, filtros independientes, secretos/cuerpos omitidos, configuración
intacta, cero red/ejecución del consumidor, navegación y teclado móvil sin
desborde. JSON privado scratchpad/.venv/panel-preview/extensions-results.json.
Estos resultados no cierran revisión adversarial, cobertura del diff o Linux.

RED contratos MCP: 4 failed/74 deselected; el estado Claude se atribuía a un
campo enabled ajeno a su contrato, faltaban ws/streamable-http y una URL sin
type se infería como HTTP. XML privado extensions-native-mcp-red.xml;
2026-10-07, reproducido al retomar el trabajo. Se amplían casos de definiciones
inválidas, preferencias corruptas y representación en panel antes de corregir.

RED MCP ampliado: 8 failed/111 deselected en definiciones locales SDK,
transportes sin endpoint, preferencias corruptas y badge del panel; XML privado
extensions-native-mcp-expanded-red.xml; 2026-10-07.

GREEN MCP: lector, briefs y panel, 206 passed/2 skipped, 31,97 s; XML privado
extensions-native-mcp-green.xml. Preferencias del proyecto seleccionado,
transportes Claude, definiciones inválidas y panel corregidos; las fixtures
usan el contrato nativo y mantienen configuración intacta.

Verificación previa a revisión: lint_plugin, 10 agentes/0 errores/3 avisos
históricos por nombres genéricos; evals/check, 51 ficheros/182 casos
(112 positivos/70 negativos)/0 errores; export-interop --check, 54 ficheros al
día. Consolas ASCII/cp1252 de los lectores: 8 passed; XML privado
extensions-console-targeted.xml. Edge P-01…P-04: 4 passed/0 failed/0 skipped,
11,3 s, con preferencias Claude nativas; JSON privado extensions-results.json.

Puerta de alcance con base b067099: 55 cambiados, 54 en alcance, 0 fuera, 0 avisos;
solo settings del usuario excluido por el default, intacto y sin versionar.
Selector de revisión: A+B+D; C=false sin motivos; D=true por ruta export en
tests/test_export_skills.py. No se anticipa el resultado de la revisión ni QA.

Windows previo al fix de revisión: 682 passed/2 skipped, 128,75 s; XML privado
extensions-gates-v3.xml. Cobertura ejecutable del diff de los tres scripts:
92,01 % (714/776); project-pieces 91,15 % global, task-brief 96,99 %, panel
93,37 %. JSON privado extensions-coverage-v3.json; medición a actualizar tras fix.
Capturas Edge escritorio/móvil inspeccionadas: filtros, conflictos y fuentes
legibles, teclado visible y sin desborde. Linux no arrancó porque el daemon
Docker estaba apagado; CLI desktop start lo inició y docker info confirmó
29.8.2. No se reutiliza el fallo como evidencia de suite ejecutada.

## Revisión de dos lentes — intento 1: Fase 1 (T-01…T-08) — gaps reproducidos

Lentes A+B+D por subagentes genéricos con contexto fresco y solo lectura;
reviewer no está expuesto como tipo de Agent en esta sesión. Tier de referencia:
opus/high del frontmatter, sin override de dev.json. C no aplica por selector.
Cinco gaps Important y uno Minor, sin deuda aceptada ni rebate. A+B coinciden
en la omisión de formatos Claude y se fusionan. Los criterios 1, 2, 6 y 7 de
spec requieren corrección; 3, 4 y 5 conservan la evidencia previa; 8 sigue abierto.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R1 | Important | El límite de directorio depende del orden de iterdir | T-02 | Rechazar directorio excedido completo, con aviso; pendiente de verde/revisión | Reproducción A: dos órdenes de las mismas 1001 entradas producen subconjuntos distintos |
| R2 | Important | Skills sin name y comandos sin frontmatter nativos Claude se omiten | T-02/T-07 | Nombre derivado y metadata opcional sin extraer cuerpos; pendiente | Reproducciones A/B: piezas válidas ausentes; contrato oficial skills verificado |
| R3 | Important | Las listas MCP args anidadas se exportan como servidores | T-02 | Respetar indentación de la lista de servidores; pendiente | B: private-customer-argument aparece como name/locator sin avisos |
| R4 | Important | Comandos/skills Claude comparten invocación pero no conflicto | T-03 | Agrupar namespace y contrastar ambos tipos contra bundle; pendiente | B: dos /deploy producen conflicts vacío |
| R5 | Important | Descripción multilineal tiene coste cuadrático | T-02 | Reunir fragmentos y unir una vez, antes de redacción; pendiente | D: 512KiB/174666 líneas tarda 5,552–13,244s; 16 archivos caben en 8MiB |
| R6 | Minor | Prosa nueva separa /doctor de la tabla README ES/EN | T-07 | Restaurar fila dentro de ambas tablas; corregido | Lectura del diff A y comprobación de ambas tablas |

Revisores ejecutaron además 221 passed/2 skipped (A), 132 passed/2 skipped (D)
y export-interop --check, 54 al día (A). No acreditan QA final. TDD fix1:
10 failed/85 deselected, 18,60 s; XML privado extensions-review-red.xml.
Incluye listas privadas, formatos sin metadata, conflictos cruzados, orden del
filesystem y timeout de 15s con 16 descripciones dentro del presupuesto 8MiB.
Los cambios de indentación de la fixture ajustan el YAML al contrato real.

Fix1 aplicado y verificado: 127 passed/2 skipped, 17,64 s; XML privado
extensions-review-fix1-green.xml. R1…R5 corregidos, pendiente la revalidación
independiente del intento 2. El directorio excedido se rechaza completo con
aviso; la fixture antigua que esperaba un subconjunto se actualiza al contrato
determinista. No se extraen cuerpos como descripciones de skills sin metadata.
Las descripciones se unen una sola vez y se redactan completas antes de acotar;
no se truncan secretos previamente a redacción. El namespace Claude contrasta
command y skill entre sí y con ambos tipos del bundle. R6 también corregido.

Medición fix1: parsing 524032 bytes/174666 líneas, 0,18 s; CLI completo de
16 archivos: 6,941 s, sin fallo/timeout. Helper privado solo importa el lector
del bundle y usa datos sintéticos. Windows v4 previo al fix2: 693 passed/2 skipped,
188,62 s; XML privado extensions-gates-v4.xml, cobertura aún no medida tras fix2.

## Revisión de dos lentes — intento 2: Fase 1 (T-01…T-08) — R4 incompleto

Lentes A+B+D con contexto fresco; selector sin cambios, C=false/D=true.
A conserva R1/R2/R3/R5/R6 aprobados y reproduce evidencia nueva dentro de R4.
B no encuentra defectos y revalida 94 passed/1 skipped + cinco comprobaciones
independientes; D sin hallazgos, crecimiento lineal 131/262/524KiB:
0,084/0,173/0,355 s y 10 tests dirigidos verdes. A ejecuta export --check,
54 al día, y 10 tests verdes; su fixture nueva demuestra el caso no cubierto.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R4 | Important | Comando Claude conserva name de frontmatter que el runtime ignora | T-03 | Usar filename; contrastar alias de directorio de skill; nombre nativo OpenCode equivalente; pendiente de verde/revisión | A: commands/tdd.md name misleading + skill tdd deja command fuera de conflicto; contrato oficial confirmado |

No se reabre lo aprobado ni se acepta deuda. El mismo contraste oficial muestra
que agentes/comandos Markdown OpenCode usan filename y que una skill Claude
con name distinto conserva alias de directorio; se cubren como el mismo contrato
de identidad/colisiones. El panel muestra el nombre que colisiona para poder
interpretar el alias. RED fix2: 5 failed/129 deselected, 3,14 s; XML privado
extensions-review-fix2-red.xml; 2026-10-07. Tareas siguen en progreso.

GREEN fix2: lector + panel, 132 passed/2 skipped, 16,40 s; XML privado
extensions-review-fix2-green.xml. Rechaza name como autoridad para comandos
Claude y agentes/comandos Markdown OpenCode; conserva los dos nombres de
invocación de skills Claude y el panel identifica cuál está repetido.
Puerta previa al intento 3: 54 en alcance/0 fuera/0 avisos, settings excluido.
Selector A+B+D sin cambios. El último pase se limita a R4 y las correcciones
de identidad/aliases relacionadas, manteniendo lo aprobado salvo evidencia nueva.

## Revisión de dos lentes — intento 3: Fase 1 (T-01…T-08) — sin gaps

Lentes A+B+D, contexto fresco y solo lectura. R4 revalidado; se conserva lo
aprobado en intentos 1/2 sin evidencia nueva que lo contradiga. C no aplica por
selector. Cero Critical/Important/Minor pendientes o aceptados como deuda.

| Criterio corregido | Veredicto | Evidencia independiente |
|---|---|---|
| Nombre nativo de comandos Claude y agentes/comandos OpenCode | ✓ | A: 8 tests dirigidos verdes y contratos oficiales; B: name complejo/duplicado/privado ignorado |
| Alias Claude, namespace compartido y contraste con ambos tipos bundle | ✓ | A/B: tests y fixtures independientes, deduplicación y redacción; B: 17 tests dirigidos verdes |
| Panel identifica y escapa el nombre que colisiona | ✓ | A/B: test de alias en tarjeta, controles y secretos redactados |
| Trabajo de aliases/conflictos acotado | ✓ | D: 250/500/1000 skills, result 0,0173/0,0292/0,0588s; HTML 0,0059/0,0137/0,0390s, cinco repeticiones |
| Exports y documentos ES/EN vigentes | ✓ | A: export --check propio, 54 ficheros al día; docs leídas |
| R1/R2/R3/R5/R6 | ✓ conservado | A/B/D: sin evidencia nueva ni regresiones atribuibles a fix2 |

El ciclo inicial concluye en tres pases, sin deuda aceptada. QA/cobertura final,
retro, estados y push siguen pendientes y no se afirman con este resultado.

QA posterior a revisión: Windows 698 passed/2 skipped, 210,58 s; XML privado
extensions-gates-v5.xml. Panel previo del bundle, 7 passed/0 failed (15,1 s).
Panel extensiones inicialmente 3 passed/1 failed: P-01 buscaba el primer code de
la tarjeta, que ahora contiene el alias repetido en el aviso de conflicto.
Se acota el selector a details code para comprobar la fuente que el escenario
exige; sin modificar producto, requisito ni fixture. Se repite el escenario.

Resultados baseline final: Edge 4 passed/0 failed/0 skipped, 22,5 s, qa-gate
VERDE; Windows Node 134 passed/0 failed/0 skipped, 248,28 s; Linux 4023
passed/29 skipped/8 subtests passed, 432,17 s; Node Linux 131 passed/3 skipped.
Linter/evals/export/release check verdes en Linux. No publicación todavía.

QA de límites nativos revela evidencia nueva tras el ciclo aprobado: un agente
con mcpServers seguido de una lista YAML sin sangría es válido para YAML, pero
_agent_servers devuelve [] sin aviso. Probe privado en memoria compara el
extractor con PyYAML usando datos sintéticos: [] frente a ['ledger'].
T-02 se reabre, sin rebajar ni ocultar el defecto. Arbitraje del orquestador bajo
la delegación técnica existente: conservar el baseline revisado en un commit
local, corregir el caso como delta de QA y aplicar un nuevo ciclo acotado de
revisión solo a ese delta. El ciclo anterior no se relanza ni reinicia; mantiene
sus tres intentos y todos los veredictos. Sin push antes del fix y sus gates.

Baseline local revisado: 87772c1, todavía sin push. RED QA YAML: 3 failed/4
passed/95 deselected; XML privado extensions-indentless-red.xml, 2026-10-07.
Casos nuevos: referencia, definición inline y args privados con lista exterior
sin sangría. La corrección conserva la detección de límites de indentación y
salida de la sección; identifica la entrada antes de cerrar el campo activo.

GREEN QA YAML: 239 passed/2 skipped, 77,09 s; XML privado
extensions-indentless-green.xml. Incluye lector, panel, briefs y distribución
portable. Cobertura ejecutable del diff completo contra b067099: 92,16%
(741/804); informe privado extensions-coverage-v6.json. Puerta del nuevo delta
contra 87772c1: tres ficheros en alcance, cero fuera y cero avisos; settings
preexistente excluido. Selector C=false/D=false: revisión A+B, intento 1 del
ciclo de QA separado. No se reinicia el ciclo inicial aprobado.

## Revisión de dos lentes — intento 1: Fase 1 (T-02/T-08) — delta QA sin gaps

Nuevo ciclo acotado contra 87772c1, solo la corrección YAML posterior al
baseline aprobado. A+B por subagentes genéricos, contexto fresco y solo lectura;
reviewer no está expuesto como tipo de Agent. Tier de referencia opus/high del
frontmatter, sin override. Selector C=false/D=false. Ambos ejecutan siete tests
dirigidos verdes; no modifican código ni leen los settings ajenos.

| Criterio | Veredicto | Evidencia independiente |
|---|---|---|
| Referencias y definiciones MCP sin sangría | ✓ | A/B: siete casos dirigidos; project-pieces.py identifica entrada antes del límite raíz |
| Listas privadas anidadas y salida de sección | ✓ | A/B: indentaciones 0/2/4; campo tools posterior no produce servidores |
| TDD y verificación declarada | ✓ | A: XML RED con tres fallos reales; GREEN 239 passed/2 skipped |
| Cobertura del diff completo | ✓ | A: recálculo independiente 741/804=92,16%, sin contar archivos de tests |
| Alcance, constitución y estados | ✓ | A: tres ficheros declarados; TDD, stdlib y privacidad; tareas abiertas al revisar, sin publicación anticipada |
| Criterios del ciclo inicial | ✓ conservado | Sin evidencia nueva del delta que contradiga lo aprobado; generados/OpenAPI no afectados |

Gaps: cero Critical/Important/Minor, sin deuda aceptada. El ciclo inicial
conserva sus tres intentos. Jira-flow --batch devuelve ops vacío: Jira
desactivado, sin issue asociado; no se publica ningún mensaje externo.

Linux posterior al delta: 702 passed/1 skipped, 33,03 s; export --check 54 al
día. XML privado extensions-linux-v3/linux-pytest.xml. La suite completa del
baseline no se presenta como posterior al fix. No cambian fuentes Node ni UI.

Meter cerrado: ventana parcial 17h 56m de reloj, incluyendo esperas; fuente
estimado sin respuestas compatibles, tokens/horas IA/eur nulos. No es esfuerzo
IA ni una nueva muestra de calibración. La retro delimita lo no medido.

Protocolo de publicación: primer commit de delta QA, informe y retro; push y
contraste del SHA remoto. Después se cierran T-09/T-10, se generan changelogs
y se publica el commit documental final. Esto permite registrar evidencia real
sin afirmar un push futuro como hecho. Sin PR, merge ni release.

## Publicación observada

Primer push de feat/project-extensions confirmado el 2026-10-07: HEAD y
refs/heads/feat/project-extensions devuelven ambos
9f591ac707f96a0a191db2f9d62efdec3418819d. Incluye 87772c1 y el delta QA.
El cierre documental se publica en un commit descendiente, sin modificar
settings, crear PR, merge o release. Las fases 3 y 4 siguen pendientes.

## QA del cierre documental — fixtures Windows de release

La comprobación adicional da 3 failed/580 passed/1 aviso histórico en 82,61 s;
XML privado extensions-closure-green.xml (el nombre no determina su resultado).
Tres fallos en test_release.py: mensaje con separador POSIX esperado en Windows,
commit CRLF sin cambios y caso sin identidad que cambia la conversión de Git
al excluir su config global. Tests y scripts/release.py no habían cambiado
frente a b067099: son límites preexistentes de la fixture, no una regresión
de producción. No se omiten ni se presentan como verdes.

Corrección solo del oráculo: escribir fixture inicial en LF explícito, fijar
core.autocrlf=false dentro de su repo temporal, esperar la ruta nativa y escribir
la variante final LF en bytes. Se conservan asserts de CRLF sin LF suelto,
comandos manuales y degradación sin identidad. El release de producción no cambia.
T-08/T-09 se reabren; publicación técnica observada y demás gates se conservan.

Primera revalidación de release: 1 failed/25 passed, 68,89 s. El caso sin
identidad llega ahora al commit y Git Windows infiere una identidad aunque
la config global/sistema esté excluida. El oráculo necesita prohibir inferencia
(user.useConfigOnly=true en el repo temporal) y excluir variables de identidad
heredadas en ese caso. No se toca Git del consumidor ni scripts/release.py.
Se conserva el fallo en extensions-release-portable-green.xml y se revalida.

## Revisión de dos lentes — intento 1: Fase 1 (T-08/T-09) — cierre documental R7

Revalidación normal: release 26 passed, 64,16 s. Revisión del cierre documental
A+B, intento 1 contra 9f591ac, limitada al delta de tests: A sin gaps; B detecta
un Important en la protección de identidad (R7). El entorno puede configurar
user.name/user.email con GIT_CONFIG_COUNT y KEY_n/VALUE_n aunque se retiren
variables directas y archivos de config. Root reproduce exit 0 frente a 1:
extensions-release-config-env-red.xml, 1 failed, 3,71 s.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R7 | Important | El test sin identidad hereda config Git por variables | T-08 | Excluir GIT_CONFIG* del entorno del subprocess; regresión parametrizada real antes del fix | Nuevo caso True: 1 failed, 3,18 s, extensions-release-config-param-red.xml |

Se conserva lo aprobado (LF/CRLF, ruta nativa, aislamiento de repo y asserts).
El nuevo caso configura Git mediante monkeypatch antes de construir el entorno;
el fix retira las variables de configuración y vuelve a fijar global/sistema a
devnull. No cambia producción ni configuración real del usuario. Pendiente de
GREEN y revisión intento 2 del ciclo del cierre documental, máximo tres.

## Revisión de dos lentes — intento 2: Fase 1 (T-08/T-09) — cierre documental sin gaps

A+B, contexto fresco y solo lectura; scope 10 en alcance/0 fuera/0 avisos,
settings excluido, C=false/D=false. Mismo ciclo de fixtures contra 9f591ac,
sin reiniciar lo aprobado. Subagentes genéricos, tier de referencia sin override.

| Criterio | Veredicto | Evidencia independiente |
|---|---|---|
| R7, identidad por config de Git en entorno | ✓ corregido | A/B: filtro GIT_CONFIG* anterior a GLOBAL/SYSTEM=devnull; incluye COUNT/KEY/VALUE y PARAMETERS |
| Regresión dedicada antes del fix | ✓ | A: XML RED contiene assert 0==1 del caso True; dos casos dirigidos verdes en 5,00 s |
| Aislamiento y asserts de degradación | ✓ conservado | Repo temporal y entorno subprocess; monkeypatch restaura variables; asserts de mensaje, exit, versiones y traceback intactos |
| LF/CRLF y comando de reparación | ✓ conservado | Sin evidencia nueva que contradiga el intento 1 |
| Alcance y estado al revisar | ✓ | A: tests declarados y tareas abiertas; no anticipa cierre ni revalidación Linux |

Cero Critical/Important/Minor pendientes o aceptados como deuda. Jira-flow del
intento 1 devuelve ops vacío (desactivado); se comprueba igualmente el intento 2.
QA final posterior: release Windows 27 passed, 62,39 s; release Linux 27 passed,
3,86 s. Documentos Windows 557 passed, 25,96 s; cierre público Linux previo al
último ajuste de identidad 552 passed, 17,23 s, con un aviso histórico.
No se suma el solape ni se presenta la ejecución Linux previa como posterior.
Changelogs ES/EN comprobados; settings del consumidor permanecen sin tocar.
