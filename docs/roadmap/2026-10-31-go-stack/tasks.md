---
tasks: go-stack
estado: completado
creado: 2026-10-31
verificacion: obligatoria
changelog: Changed
---

# Guías de Go en stack-practices

Ledger canónico.

Petición explícita del usuario: añadir capacidades de Go y comprobar si existían
junto con Rust. Ambos tenían referencias de seguridad y entradas TDD; las guías
generales seguían como candidatas. Se admite Go por esta petición concreta.
Rust mantiene su estado; no se incorpora implícitamente otro lenguaje.

Se amplía el dueño existente stack-practices con una referencia bajo demanda.
La selección usa --stack go, igual que otros stacks declarados; no se añade un
parser de go.mod/go.work ni se anuncia autodetección. El catálogo conserva 33 skills.
El historial de admisión de iniciativas cerradas no se reescribe.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Go | 1 | 1 | 100.0% |
| **TOTAL** | **1** | **1** | **100.0%** |

## Fase 1 — Go

### T-01 — Incorporar Go al criterio compartido y al selector

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Guía de Go por versión, selección explícita para los cinco roles de entrega, pruebas, evals y documentación ES/EN. Las tools y dependencias del consumidor siguen bajo su configuración.
- **Changelog**: Guía de Go por versión, con selección explícita, concurrencia, errores y pruebas compartidas entre roles.
- **Archivos**: `skills/stack-practices/**`, `skills/tdd/references/by-stack.md`, `agent-kits/shared/capability-route.py`, `agent-kits/shared/capability-catalog.json`, `agent-kits/shared/capability-check.md`, `evals/cases/skill-stack-practices.json`, `tests/test_capability_route.py`, `CLAUDE.md`, `docs/README.md`, `docs/en/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/2026-10-31-go-stack/**`, `docs/roadmap/README.md`, `docs/roadmap/CALIBRATION.md`
- **Verificación**: suites afectadas y estática; evidencia en testing/report.md.

**Criterios de aceptación**
- [x] Go selecciona stack-practices para architect/planner/implementer/reviewer/qa; procedencia explícita y manifest del consumidor intacto.
- [x] La guía y TDD distinguen semántica de bucles Go 1.22 y benchmarks Go 1.24; no fijan versiones ni umbrales universales.
- [x] Evals, export portable/nativo, tamaño, lint y validaciones de la pieza pasan; changelogs y docs coherentes; cambios revisados literalmente antes de commit.

RED: `python -m pytest -q tests/test_capability_route.py -k go --tb=short`
falló antes del código: 6 failed por invalid choice go/SystemExit 2. Tras ampliar
STACKS y el catálogo: 55 passed, 1 skip de symlink por permisos Windows.

Fuentes primarias Go verificadas el 2026-10-31: módulos/toolchains, Go 1.22,
Go 1.24, testing, context, net/http y race detector. No se copia código de una
skill de terceros. S116/S117 y D-125 aportan antecedentes revisados; el contenido
nuevo conserva al dueño existente y evita las recomendaciones antiguas corregidas.

La ventana de medición de QA comienza después de implementar; no se presenta
como coste completo de la tarea. Sin transcripción compatible, métricas null.

Validación local final:183 passed/1skip en suites afectadas;57passed en índice;
coverage.py94,92%;evals219casos ylint0errores. Revisión literal del patch completo
de26.351caracteres en[0,14000) y[14000,26351), más delta de cierre revisado.
Ventana QA cerrada; sin medida completa de coste/tokens/horas IA. Se conserva
retro sin nueva muestra numérica. CI del commit de entrega se comprueba en la PR22.
