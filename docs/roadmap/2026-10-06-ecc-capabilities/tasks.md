---
tasks: ecc-capabilities
estado: completado
creado: 2026-10-06
actualizado: 2026-10-06
verificacion: obligatoria
changelog: Added
generacion:
  inicio: "2026-10-06T11:27:42Z"
  fin: "2026-10-06T11:53:42Z"
  fuente: estimado
  tokens_reales: null
  horas_ia: null
  eur: null
  ratio_usado: 531798.5
  nota: "Ventana parcial sin respuestas compatibles; no representa consumo ni duración total de la iniciativa."
---

# ECC — ledger de primera integración

> **Ledger canónico de progreso.** Fuente única de verdad de esta iniciativa.

Autorización: el usuario solicita integración selectiva, delega decisiones y
autoriza push de la rama. No solicita PR/merge ni release.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 5 | 5 | 100% |
| **TOTAL** | **5** | **5** | **100%** |

## Fase 1 — Integración

**Estado**: completado

### T-01 — Comparar ECC, Graphify y memoria actual

- **Estado**: completado
- **Descripción**: comparación de catálogo, tools, agentes, comandos, hooks, workflows, dashboards y memoria con fuente fijada y decisiones de adopción.
- **Changelog**: Se documenta la adopción selectiva de ECC y el encaje de Graphify como complemento estructural de la memoria curada.
- **Archivos**: `docs/roadmap/2026-10-06-ecc-capabilities/**`, `docs/roadmap/README.md`
- **Verificación**: lectura de revisión/versión/licencias en clones originales; enlaces a implementaciones y clasificación de evidencia en comparison.md.
**Criterios de aceptación**:
  - [x] Comparación trazable y piloto de memoria con aceptación, sin mejora inventada.

TDD n/a: análisis y documentación.

Evidencia ejecutada: testing/report.md (2026-10-06); interop --check: 52 ficheros al día, exit 0; evals: 167 casos/0 errores; suites de metadatos y panel: 95 passed/1 skipped.

### T-02 — Investigar antes de construir

- **Estado**: completado
- **Descripción**: skill compartida con comparación breve/completa, canal no disponible explícito y uso bajo demanda por analyst/architect.
- **Changelog**: Analyst y architect pueden comparar soluciones existentes antes de diseñar integraciones o herramientas con research-first.
- **Archivos**: `skills/research-first/**`, `agents/analyst.md`, `agents/architect.md`, `docs/agents/analyst.md`, `docs/agents/architect.md`, `tests/test_rationalization_tables.py`, `evals/cases/skill-research-first.json`, `interop/**`
- **Verificación**: linter, evals/check.py, tests/test_rationalization_tables.py y export-interop.py --check.
**Criterios de aceptación**:
  - [x] Decisión y límites explícitos; sin agente adicional, precarga obligatoria ni instalación automática.

TDD n/a: prosa de skill/agentes y configuración de evals.

Evidencia ejecutada: testing/report.md (2026-10-06); interop --check: 52 ficheros al día, exit 0; evals: 167 casos/0 errores; suites de metadatos y panel: 95 passed/1 skipped.

### T-03 — Control panel de capacidades

- **Estado**: completado
- **Descripción**: inventario público de agentes/skills/comandos/tools/hooks; HTML local buscable y JSON; presencia de fuentes sin afirmar ejecución o salud.
- **Changelog**: plugin-catalog genera un panel local buscable del catálogo, con redacción central y presencia de fuentes de runtime y memoria.
- **Archivos**: `skills/plugin-panel/**`, `commands/plugin-catalog.md`, `tests/test_plugin_panel.py`, `tests/test_console_encoding.py`, `evals/cases/skill-plugin-panel.json`, `evals/cases/command-plugin-catalog.json`, `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `interop/**`
- **Verificación**: pytest tests/test_plugin_panel.py; coverage-gate changed-only al 90 %; navegador con búsqueda/filtros y viewport móvil.
**Criterios de aceptación**:
  - [x] Metadatos redactados, cuerpos privados excluidos, symlinks rechazados y salida ajena preservada.
  - [x] HTML autónomo funcional; sin recursos externos ni servidor obligatorio.

RED: test_catalog_metadata_redacted_without_private_bodies falló con counts={} frente a cinco grupos esperados · 2026-10-06 (scratchpad/panel-red.xml).
GREEN inicial: 9 passed/1 skipped (symlinks no disponibles en Windows).
RED: test_opencode_presence_uses_exporter_path y test_yaml_list_tools_are_counted fallaron con absent/lista incompleta · 2026-10-06 (scratchpad/panel-contract-red.xml).
GREEN: 11 passed/1 skipped (scratchpad/panel-green.xml).
RED: test_windows_junction_directory_is_never_read falló al leer OUTSIDE PRIVATE mediante una junction NTFS · 2026-10-06 (scratchpad/panel-junction-red.xml).
GREEN final: 12 passed/1 skipped en Windows y 12 passed/1 skipped en Linux; symlink real validado en Linux y junction real en Windows. Cobertura changed-only: 91,76 %, gate exit 0. Playwright: 4 passed, qa-gate VERDE.

Evidencia ejecutada: testing/report.md (2026-10-06); interop --check: 52 ficheros al día, exit 0; evals: 167 casos/0 errores; suites de metadatos y panel: 95 passed/1 skipped.

### T-04 — Guías específicas de los tres stacks

- **Estado**: completado
- **Descripción**: CodeIgniter 4/PHP, Python y React, con decisiones de implementación/revisión y fuentes oficiales; integración bajo demanda en implementer/reviewer/qa.
- **Changelog**: Los roles de desarrollo disponen de guías específicas para CodeIgniter 4, Python y React, cargadas según el stack de la tarea.
- **Archivos**: `skills/codeigniter-practices/**`, `skills/python-practices/**`, `skills/react-practices/**`, `agents/implementer.md`, `agents/reviewer.md`, `agents/qa.md`, `docs/agents/implementer.md`, `docs/agents/reviewer.md`, `docs/agents/qa.md`, `evals/cases/skill-codeigniter-practices.json`, `evals/cases/skill-python-practices.json`, `evals/cases/skill-react-practices.json`, `interop/**`
- **Verificación**: evals/check.py, linter, tests/test_skill_size.py, export-interop.py --check; fuentes oficiales con fecha y versión del consumidor como referencia.
**Criterios de aceptación**:
  - [x] Tres skills sin mecanismos de instalación alternativos ni dueños duplicados.

TDD n/a: guías y configuración de descubrimiento.

Evidencia ejecutada: testing/report.md (2026-10-06); interop --check: 52 ficheros al día, exit 0; evals: 167 casos/0 errores; suites de metadatos y panel: 95 passed/1 skipped.

### T-05 — Validar, documentar y publicar la rama

- **Estado**: completado
- **Descripción**: documentación bilingüe, fuentes generadas, revisión adversarial, pruebas afectadas, cobertura del script y commit/push; integración a master pendiente.
- **Changelog**: La primera integración de ECC conserva los contratos de los tres runtimes y documenta sus capacidades y límites de memoria.
- **Archivos**: `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `README.md`, `README.es.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/CALIBRATION.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-10-06-ecc-capabilities/**`, `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`
- **Verificación**: scope-check base 0d9ce74; revisión A+B (C/D según selector); linter, evals, export --check, pruebas afectadas y coverage gate; git diff --check y push normal.
**Criterios de aceptación**:
  - [x] Puertas y evidencias registradas; memoria sin migración ni promociones automáticas.

TDD n/a: metadatos y documentación; el código del panel sigue TDD en T-03.

Alcance E3 adicional: README principal y espejo, INTEROP y espejo conservan sus
conteos e índice de comandos sincronizados con las cinco skills y el comando nuevos.

## Revisión de dos lentes — intento 1: Fase 1 (T-01…T-05) — dos gaps reproducidos

Lentes A+B por subagentes genéricos: reviewer por nombre no disponible. Modelo
del reviewer: opus/high por frontmatter, sin override de dev.json. Selector C/D:
false/false. Scope previo: exit 0, sin fuera de alcance, avisos ni exclusiones de
usuario. Jira no configurado para esta iniciativa; no se publican mensajes externos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-01 | Important | Falta matriz de invocación/export y límites por runtime | T-01 | Corregido: matriz Claude/Codex/OpenCode en comparison.md | Requisito spec aceptación 1; export y permisos existentes citados, sin afirmar E2E de runtimes |
| B-01 | Important | Redacción posterior a JSON y truncado permite secreto entrecomillado/PEM largo | T-03 | Corregido: redactor central sobre texto original antes de resumir y serializar | RED: dos casos fallaron con secreto intacto, 2026-10-06; scratchpad/panel-redaction-red.xml. GREEN: 14 passed/1 skipped; cobertura 92,11 %, gate exit 0 |

Veredicto del primer pase: 0 Critical, 2 Important, 0 Minor. Ambos confirmados y
corregidos; falta revalidación independiente de estas correcciones (intento 2).

## Revisión de dos lentes — intento 2: Fase 1 (T-01…T-05) — A+B sin gaps

Contexto fresco, fallback genérico. Se reevalúan A-01/B-01 y el delta E3;
los criterios aprobados del intento 1 se conservan. C/D no activadas.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| T-01 comparación, memoria y piloto | ✓ | Revisiones fijadas y matriz por runtime; distinción Graphify/Graphiti |
| T-02 investigación y dueños | ✓ | Skill y uso bajo demanda, sin precarga ni nuevo agente |
| T-03 privacidad, rutas y HTML | ✓ | Redacción previa al resumen/JSON; regresiones de comillas/PEM; 14 passed/1 skipped en ambos SO |
| T-03 cobertura e interacción | ✓ | Changed-only 92,11 %, gate exit 0; Playwright final 4 passed, qa-gate VERDE |
| T-04 tres stacks | ✓ | Guías, fuentes oficiales y versión mínima del consumidor |
| E2/E3 | ✓ | Lente A ejecutó --check: 52 ficheros al día, exit 0; README/INTEROP y espejos actualizados |
| Alcance, constitución y verificación | ✓ | Scope exit 0; sin principios vulnerados; report.md con ejecuciones |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-01 | Important | Matriz por runtime | T-01 | Validado como corregido | comparison.md: matriz explícita, sin E2E de runtimes inventado |
| B-01 | Important | Etapa de redacción | T-03 | Validado como corregido | Lente B independiente: 14 passed/1 skipped, sin defectos |

Resultado: **0 Critical, 0 Important, 0 Minor pendientes**. Sin entradas nuevas
de conocimiento que promover. Jira no activo para esta iniciativa; no se envían
mensajes externos. T-05 conserva el cierre/publicación pendiente hasta ejecutar
el push de la entrega.

## Cierre técnico de la entrega

T-05 completada: código y comparación publicados con commit `ad7f9d7`;
`git push origin fix/hooks-brief-budget-ecc` ejecutado, exit 0, remoto actualizado
`0d9ce74..ad7f9d7`. El cierre documental se añade después de verificar ese push.
Pruebas finales: panel 14 passed/1 skipped en Windows y Linux, conjunto de
metadatos/panel 97 passed/1 skipped; exports/consola 469 passed; índice 14 passed;
Playwright 4 passed y qa-gate VERDE. Cobertura changed-only 92,11 %. Linter 0
errores/3 avisos previos; evals 167 casos/0 errores; export 52 al día; ledger-lint
0 incoherencias/0 avisos; revisión A+B intento 2 sin gaps pendientes.

Spec implementada, plan y ledger completados: **5/5**. Piloto Graphify y futuras
ampliaciones conservan su estado pendiente en comparison.md, fuera de esta
primera entrega. PR/master y release no solicitados; no se ejecutan.

Comprobación posterior al primer push: al entrar el nuevo script en `git ls-files`,
la suite UTF-8 exige registrar su modo de arranque. RED: cuatro casos fallaron por
MODOS ausente/KeyError (scratchpad/ecc-console-registration-red.xml), con 913 casos aprobados.
Se registra `--json`, que imprime metadatos públicos no ASCII; no cambia producción
ni se admite un skip. La corrección añade tests/test_console_encoding.py a T-03.
GREEN específico: 8 passed, 442 deselected, sin skips. Se repite la puerta completa
de consola/metadatos antes del cierre publicado. No cambia el script aprobado.

## Revisión de dos lentes — intento 3: Fase 1 (T-03/T-05) — registro y cierre

A+B en contexto fresco, fallback genérico; C/D no activadas. Solo delta posterior
a `ad7f9d7`; sin cambios de producción ni reapertura de criterios aprobados.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Registro del arranque real UTF-8 | ✓ | --json emite metadatos no ASCII; Lente B independiente: 8 passed, sin skips |
| RED, alcance y constitución | ✓ | Falta de MODOS reproducida, test declarado en T-03; ledger y changelogs bilingües |
| E2/E3, retro y medición | ✓ | Lente A ejecutó export --check: exit 0, 52 al día; fila sin ratio y mediana preservada |
| Push inicial y cierre honesto | ✓ | Rama remota en ad7f9d7; segundo push documental todavía por ejecutar |

Resultado independiente: **0 Critical, 0 Important, 0 Minor nuevos**. No hay gaps
pendientes ni promociones de memoria. Tras las lentes, puerta completa repetida:
**917 passed, 0 failed, 0 skipped**, un aviso histórico de marcador en el ledger
cerrado de plugin-refactor (sin error). JUnit: scratchpad/ecc-closure-tests.xml.
Changelog --check, ledger-lint, scope y retro-gate en verde. Este cierre documental
se comitea y sube como último paso autorizado; no se ejecuta PR/merge/release.

## Aclaración posterior sobre el catálogo completo — 2026-10-06

Ante la pregunta del usuario por el resto del catálogo, se añade
catalog-inventory.md: 293 skills, 68 agentes y 94 comandos, **455 fuentes únicas**
fijadas al commit original. Extracción de metadatos e inventario completos;
evaluación semántica individual pendiente. Se registran rutas propuestas de
comparación y atribución MIT de los extractos, sin instalar ni importar piezas.
La primera entrega sigue completada; la adopción general de ECC no se declara
completada. No se confunden nuestras guías iniciales con migraciones completas
de python-patterns/react-patterns ni plugin-catalog con un comando ECC importado.
