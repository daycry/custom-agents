---
tasks: hooks-runtime
estado: completado
creado: 2026-10-06
actualizado: 2026-10-06
verificacion: obligatoria
changelog: Fixed
---

# Hooks portables de Claude Code, Codex y OpenCode

> **Ledger canónico de progreso.** Fuente única de verdad de esta corrección.

Cambio autorizado por el usuario: resolver los hooks en los tres runtimes antes de brief-budget.
Vía rápida, sin presupuesto nuevo. No se publica una versión ni se ejecutan sesiones con un modelo.

## Fase 1 — Arranque y contratos

### T-01 — Resolver intérpretes y respetar los límites de cada runtime

- **Estado**: completado
- **Changelog**: Los tres runtimes usan Python nativo y Git Bash en Windows; Codex respeta SessionEnd de 3 s y los eventos apply_patch/Edit conservan avisos y exclusiones de documentación.
- **Tipo**: backend
- **Archivos**: `docs/roadmap/CALIBRATION.md`, `.gitattributes`, `hooks/**`, `agents/implementer.md`, `agents/architect.md`, `scripts/export-interop.py`, `tests/test_export_interop.py`, `tests/test_hooks_config.py`, `tests/test_hooks_shell.py`, `tests/test_confluence_scope.py`, `tests/hook-runtime.test.mjs`, `interop/**`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-10-06-capability-foundation/analysis.md`
- **Dependencias**: ninguna
- **Verificación**: `node --test tests/hook-runtime.test.mjs` → captura UTF-8, outbox, SessionStart y adaptador OpenCode verdes; `python -m pytest tests/test_export_interop.py tests/test_hooks_config.py -q` → verde; `python scripts/export-interop.py --check` → sin deriva; `python scripts/lint_plugin.py` → 0 errores; `python evals/check.py` → 0 errores.
**Criterios de aceptación**:
  - [x] Codex exporta SessionEnd con timeout 3; Claude Code conserva 5.
  - [x] Los tres runtimes comparten el arranque, sin seleccionar el lanzador WSL como Git Bash.
  - [x] SessionEnd y UserPromptSubmit invocan Python nativo; se comprueba la escritura efectiva, no solo exit 0.
  - [x] Los hooks de shell resuelven Python aunque se llame python y conservan UTF-8.
  - [x] Ningún hook global decide ni bloquea; las guardias siguen limitadas a implementer y architect.
  - [x] Documentación EN/ES, exportación y pruebas actualizadas.
- **RED**: `tests/test_export_interop.py::test_codex_hooks_respetan_limite_session_end_y_runner_windows` falló con `assert 5 == 3` · 2026-10-06.

## Evidencia de diagnóstico

En Windows, PATH resolvía primero el lanzador WSL y no ofrecía python3 nativo. Los hooks de
shell salían silenciosamente cuando no encontraban python3. El warning de Codex se reproduce
por el timeout 5 de la exportación: su contrato limita SessionEnd a 3 segundos.

Contratos consultados el 2026-10-06: [Codex](https://learn.chatgpt.com/docs/hooks),
[Claude Code](https://code.claude.com/docs/en/hooks), [OpenCode](https://opencode.ai/docs/plugins/).
OpenCode usa session.idle para capturar; no ofrece las mismas garantías de inyección de contexto.

- **Archivos** adicionales de T-01: `.gitattributes` (LF para las entradas Bash y el shim tras checkout).

Alcance auxiliar: el análisis catálogo de referencia y su fila del índice ya estaban en el árbol al iniciar este
cambio. Se conservan y se documenta la preferencia posterior por los tres stacks. catálogo de referencia sigue sin
implementación; se declaran aquí para que la puerta de alcance examine el diff completo.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 1 | 1 | 100% |
| **TOTAL** | **1** | **1** | **100%** |


## Revisión de dos lentes — intento 1: Fase 1 (T-01) — fallback de guardias

Lentes A+B+C; D comprobó latencia de captura. A aprobó los criterios del exportador. B y C detectaron pérdida de guardia al copiar agentes sin CLAUDE_PLUGIN_ROOT y B señaló una expectativa de registro obsoleta. Corregido: búsqueda en raíces de proyecto/usuario y expectativa del lanzador Node.

## Revisión de dos lentes — intento 2: Fase 1 (T-01) — cachés anidadas

B y C comprobaron cierre de los hallazgos anteriores. A detectó que una instalación bajo caché anidada quedaba fuera de la búsqueda. Corregido: recorrido recursivo sin seguir enlaces simbólicos.

## Revisión de dos lentes — intento 3: Fase 1 (T-01) — precedencia

A y B detectaron que un kit plano del usuario podía ganar a una caché del proyecto; C no abrió hallazgos nuevos. Al agotarse los tres intentos, el orquestador decidió corregir la precedencia por raíz. Las dos regresiones implementer/architect fallaron con allow en lugar de deny y pasaron tras recorrer cada raíz completa antes de la siguiente. No se atribuye una cuarta aprobación a estos revisores.

## Fase 2 — Compatibilidad actual de Codex

Se descubrió un contrato actualizado durante la validación: Codex ya dispara PostToolUse para apply_patch y SessionStart para compact. Se adapta el payload de parche a rutas de archivos y la salida informativa a systemMessage.

## Revisión de dos lentes — intento 1: Fase 2 (T-01) — payload de parche

Revisión independiente A+B, subagente genérico porque reviewer no está disponible como tipo de herramienta: 0 Critical, 0 Important, 0 Minor. 9 tests de exportación, fixture Update y reproducción Move con avisos de lint/progreso JSON. Add/Delete se cubren en el parser de cabeceras; las rutas inexistentes se omiten en progreso.

Revisión C+D del diff final: 0 hallazgos. Allowlist, argumentos separados y stdin conservados. SessionEnd usa Python nativo con límite interno 2200 ms. `node --test tests/hook-runtime.test.mjs` → 11 passed; junto al adaptador OpenCode → 21 passed. No se ha ejecutado una sesión real con un modelo en los clientes.

## Cierre y aplicación local — 2026-10-06

Cachés activas 1.22.0 de Codex y Claude actualizadas con backup en el perfil local fuera del repositorio. Se modificaron únicamente launcher/registros/adaptador y líneas de guardias; se conservaron los scripts journal propios de cada caché. Captura real en outbox: Codex 927 ms, Claude 959 ms; Add File por apply_patch marca documentación pendiente en ambas. Reiniciar los clientes para que carguen los registros nuevos. Una reinstalación puede reemplazar este hotfix local hasta publicar una versión que lo incluya.

No hay bundle custom-agents instalado en las rutas locales de OpenCode inspeccionadas. Su código fuente y copia generada están corregidos y sus pruebas de integración pasan; no se declara una instalación de OpenCode que no existe.

También se actualizó el generador del brief y la plantilla de diseño en ambas cachés, con backup y sin sustituir otros módulos del kit.

## Consolidación — 2026-10-06

La suite general detectó tres pruebas de Confluence que seguían llamando bash de PATH directamente: RED exit127 en Windows. Se adaptó su helper al launcher Node utilizado en producción, con Python explícito y timeout. Se conservan los mismos casos de staging, documentos normales y security-scan; no se modifica el contrato de publicación.

La suite de shell utiliza Git Bash nativo y el mismo shim Python del launcher. El fixture sin
Python conserva su degradación; el caso de filename hostil usa bidi legal en NTFS, que rechaza
comillas y caracteres de control. La comparación de rutas staged usa `as_posix()`.

RED: `test_progress_line_emite_system_message_json` falló con stdout vacío · 2026-10-06.
La traza Bash mostró `docs//roadmap` tras convertir cada backslash del JSON sin jq. Los tres
PostToolUse convierten primero el par escapado, después el separador nativo de jq. La regresión
del launcher verifica progreso, lint, marca docs y exclusión security-scan con rutas Windows.
`node --test tests/hook-runtime.test.mjs` → 12 passed, 0 failed (2026-10-06).

## Revisión de dos lentes — intento 1: Consolidación — rutas Windows

Lentes A+B por subagentes genéricos, solo sobre las tres normalizaciones y los fixtures.
Exportación comprobada por A: 50 ficheros al día. C+D ya revisaron el launcher/exportador;
esta consolidación no cambia esos archivos ni el camino de SessionEnd.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-1/B-1 | Important | Con jq, se pierde la raíz UNC al desescapar por segunda vez | T-01 | Desescape de pares solo para grep; separador nativo para ambos | RED `test_ledger_lint_jq_preserva_raiz_unc`: `/server` frente a `//server`; 2026-10-06 |
| B-2 | Minor | Git Bash en usr/bin duplica usr al construir PATH del fixture | T-01 | Resolver raíz también desde usr/bin | Reproducción del revisor con Git/usr/bin/bash.exe; entorno sin flock |

## Revisión de dos lentes — intento 2: Consolidación — UNC y fixtures

A+B: 0 Critical, 0 Important, 0 Minor. A verificó la regresión Edit del launcher y
`export-interop --check` → 50 ficheros al día. Ambos comprobaron UNC/sin-flock: 2 passed.
Los dos hallazgos del intento 1 quedan corregidos. Ajustes adicionales del harness:
Git check-ignore se comprueba en el proyecto temporal donde capture siembra su regla;
en NTFS se consulta el modo ejecutable del índice Git, conservando stat en POSIX.
Los cuatro casos afectados (captura, modo, filename hostil y UNC) → 4 passed.

Verificación final de consolidación (2026-10-06): shell + Confluence → **87 passed**;
brief + exportador + config → **110 passed**; contratos coverage-check/copias/manual-copy
→ **41 passed**; cifras vivas + índice + suites standalone → **475 passed, 1 fallo previo**
en el fixture de modo ejecutable NTFS de `test_lint_plugin.py` (linter y test sin cambios).
Linter real: 0 errores, 3 avisos de nombres genéricos; changelog-sync --check: sin pendientes.
La suite general arrancada antes de corregir el harness terminó 3557 passed/96 failed/25 skipped;
no representa el árbol final de los hooks. No se declara verde general en Windows.
El dry-run de release pasa lint/evals/interop/copias; avisa que la publicación real requiere
un árbol limpio. No se ha publicado ni etiquetado una versión.
