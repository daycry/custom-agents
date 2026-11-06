---
tasks: external-session-discovery
estado: completado
creado: 2026-11-06
verificacion: obligatoria
changelog: Fixed
---
# Descubrimiento de sesiones externas

> Ledger canónico: tasks.md conserva estados, criterios y evidencia.

## Resumen de progreso
| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 4 | 4 | 100.0% |
| **TOTAL** | **4** | **4** | **100.0%** |

## Fase 1
**Estado**: completado

### T-01 — Transporte JSON acotado y propio
- **Estado**: completado
- **Archivos**: `skills/plugin-panel/scripts/console_transport.py`, `tests/test_console_transport.py`
- **Changelog**: Captura JSON nativa con tamaño, plazo y exit0 comprobados; cierre de auxiliares mediante propiedad del transporte existente.
- **Verificación**: pruebas sintéticas de bytes, salida, timeout y terminación propia; resultados ejecutados en testing/validation.md.

**Criterios de aceptación**
- [x] Capturar JSON nativo sin shell ni stdin de trabajo, limitar bytes y tiempo, exigir salida0 y cerrar sólo procesos propios en error/shutdown.

### T-02 — Inventarios de los tres runtimes
- **Estado**: completado
- **Archivos**: `skills/plugin-panel/scripts/console_claude.py`, `skills/plugin-panel/scripts/console_opencode.py`, `skills/plugin-panel/scripts/console_service.py`, `tests/test_console_claude.py`, `tests/test_console_opencode.py`, `tests/test_console_codex.py`, `tests/test_console_service.py`
- **Changelog**: Descubrir metadatos externos de Claude/OpenCode y conservar Codex exact-cwd; sin turnos, adopción ni control de sesiones externas.
- **Verificación**: regresiones de metadatos exact-cwd, límites, errores, sólo GET y cleanup; resultados ejecutados en testing/validation.md.

**Criterios de aceptación**
- [x] Claude agents JSON y OpenCode GET session list muestran metadatos externos sin iniciar sesiones/turnos; Codex conserva su contrato, filtrado exacto y sólo lectura; versiones sin interfaz fallan explícitamente y cierre propio garantizado.

### T-03 — Contadores y guía honesta
- **Estado**: completado
- **Archivos**: `skills/plugin-panel/assets/console-dom.js`, `skills/plugin-panel/assets/console-sessions.js`, `skills/plugin-panel/SKILL.md`, `skills/plugin-panel/references/control-center.md`, `docs/guides/session-visibility.md`, `docs/en/guides/session-visibility.md`, `tests/console-inventory.test.mjs`
- **Changelog**: Distinguir lectura vacía incompleta de cero confirmado y conservar deduplicación; guías ES/EN de alcance local y versiones compatibles.
- **Verificación**: casos propios/externos, vacío completo/incompleto y deduplicación; revisión ES/EN; resultados ejecutados en testing/validation.md.

**Criterios de aceptación**
- [x] Inventario desconocido vacío se muestra como desconocido, no cero; no atribuir procesos vivos ni control externo; guías detallan interfaces, alcance local y límites de cada runtime.

### T-04 — Validación y entrega
- **Estado**: completado
- **Archivos**: `docs/roadmap/2026-11-06-external-session-discovery/**`, `docs/roadmap/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`
- **Changelog**: Regresión completa, revisión independiente y contraste con Claude CLI; evidencia local sin atribuir validación al otro ordenador.
- **Verificación**: gates del proyecto, revisión fresca, CI, commits/push y PR actualizada.

**Criterios de aceptación**
- [x] Evidencia reproducible, sin afirmar prueba en equipo remoto; revisión y regresión completas; commits/push/PR sin publicación ni cambios en servicios externos.

RED: pruebas nuevas transporte/proveedores/dispatch: 11 failed por captura/inventarios ausentes y Claude/OpenCode unsupported; Node contador 1 failed/2 passed (cero incorrecto cuando otro proveedor es desconocido), antes de implementar, 2026-11-06.

RED adicional T-03: contador de inventario vacío antiguo con refresh_failed devolvía cero (1 failed/3 passed); corregido para mostrar desconocido, 2026-11-06.

## Revisión de dos lentes — intento 1: T-01–T-04 — verde A+B+C

Diff 1fd0460..ddf6cf3, 18 archivos. Las tres lentes leen el diff completo; A/C ejecutan 87 pruebas Python y B56 dirigidas; Node4 pasan. Sin gaps de conformidad, corrección o seguridad confirmados. D no aplica por selector. T-04 sigue pendiente de CI.

## Contraste final de contratos

Root detecta un caso válido adicional del contrato Claude: background con ID corto, sin UUID/PID vivo, seguía descartado. RED: test_native_background_without_uuid_or_live_pid_keeps_its_native_job_identity, 1 failed antes del fix (2026-11-06). Se conserva ese ID nativo como identidad observada de sólo lectura, sin control ni adopción. Regresión dedicada y guías ES/EN actualizadas. Se revisará el delta en intento2.

## Revisión de dos lentes — intento 2: T-01–T-04 — verde A+B+C

Head4aa985e, 18 archivos; delta5 leído íntegramente. A/B/C aprueban el ID observado de background, su validación y la documentación ES/EN, conservando criterios previos. Claude10 +Node4 correctos; C además comprueba siete IDs inválidos. No hay gaps de revisión confirmados pendientes; D false. T-04 sigue abierta por CI.

Contraste de Claude CLI: [testing/claude-review-triage.md](testing/claude-review-triage.md) conserva los avisos, rebates con llamantes y límites. No se convierten hipótesis heredadas en arreglos a ciegas.

Cierre T-04: CI42201569592 correcta en4aa985e; revisión A+B+C intento2 sin gaps confirmados y Claude CLI contrastado. Commits/push/PR30 realizados; equipo remoto no accedido.
