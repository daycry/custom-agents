---
tasks: external-session-discovery
estado: en-progreso
creado: 2026-11-06
verificacion: obligatoria
changelog: Fixed
---
# Descubrimiento de sesiones externas

> Ledger canónico: tasks.md conserva estados, criterios y evidencia.

## Resumen de progreso
| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 0 | 4 | 0.0% |
| **TOTAL** | **0** | **4** | **0.0%** |

## Fase 1
**Estado**: en-progreso

### T-01 — Transporte JSON acotado y propio
- **Estado**: en-revision
- **Archivos**: `skills/plugin-panel/scripts/console_transport.py`, `tests/test_console_transport.py`
- **Verificación**: pruebas sintéticas de bytes, salida, timeout y terminación propia; resultados ejecutados en testing/validation.md.

**Criterios de aceptación**
- [ ] Capturar JSON nativo sin shell ni stdin de trabajo, limitar bytes y tiempo, exigir salida0 y cerrar sólo procesos propios en error/shutdown.

### T-02 — Inventarios de los tres runtimes
- **Estado**: en-revision
- **Archivos**: `skills/plugin-panel/scripts/console_claude.py`, `skills/plugin-panel/scripts/console_opencode.py`, `skills/plugin-panel/scripts/console_service.py`, `tests/test_console_claude.py`, `tests/test_console_opencode.py`, `tests/test_console_codex.py`, `tests/test_console_service.py`
- **Verificación**: regresiones de metadatos exact-cwd, límites, errores, sólo GET y cleanup; resultados ejecutados en testing/validation.md.

**Criterios de aceptación**
- [ ] Claude agents JSON y OpenCode GET session list muestran metadatos externos sin iniciar sesiones/turnos; Codex conserva su contrato, filtrado exacto y sólo lectura; versiones sin interfaz fallan explícitamente y cierre propio garantizado.

### T-03 — Contadores y guía honesta
- **Estado**: en-revision
- **Archivos**: `skills/plugin-panel/assets/console-dom.js`, `skills/plugin-panel/assets/console-sessions.js`, `skills/plugin-panel/SKILL.md`, `skills/plugin-panel/references/control-center.md`, `docs/guides/session-visibility.md`, `docs/en/guides/session-visibility.md`, `tests/console-inventory.test.mjs`
- **Verificación**: casos propios/externos, vacío completo/incompleto y deduplicación; revisión ES/EN; resultados ejecutados en testing/validation.md.

**Criterios de aceptación**
- [ ] Inventario desconocido vacío se muestra como desconocido, no cero; no atribuir procesos vivos ni control externo; guías detallan interfaces, alcance local y límites de cada runtime.

### T-04 — Validación y entrega
- **Estado**: en-progreso
- **Archivos**: `docs/roadmap/2026-11-06-external-session-discovery/**`, `docs/roadmap/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`
- **Verificación**: gates del proyecto, revisión fresca, CI, commits/push y PR actualizada.

**Criterios de aceptación**
- [ ] Evidencia reproducible, sin afirmar prueba en equipo remoto; revisión y regresión completas; commits/push/PR sin publicación ni cambios en servicios externos.

RED: pruebas nuevas transporte/proveedores/dispatch: 11 failed por captura/inventarios ausentes y Claude/OpenCode unsupported; Node contador 1 failed/2 passed (cero incorrecto cuando otro proveedor es desconocido), antes de implementar, 2026-11-06.

RED adicional T-03: contador de inventario vacío antiguo con refresh_failed devolvía cero (1 failed/3 passed); corregido para mostrar desconocido, 2026-11-06.
