---
spec: plugin-audit-remediation
estado: aprobada
creado: 2026-11-09
plan: improvement-plan.md
tasks: tasks.md
---

# Corrección de la auditoría completa de v3.2.2

## Problema

El 2026-11-09 se auditó el plugin completo por áreas: piezas del ciclo, hooks y sesión, scripts deterministas, dashboards y consola, y distribución e integraciones. La auditoría dio 1 hallazgo crítico, 40 importantes y 59 menores, con fichero:línea y evidencia. Los más graves los verificó el orquestador en el código.

## Objetivo

Corregir lo hallado sin perder contratos ni puertas:

1. Que ningún estado se pierda en silencio y que ninguna puerta falle en abierto.
2. Que las funciones documentadas funcionen con roadmaps grandes.
3. Bajar la latencia de los hooks, de la consola y de los scripts de las puertas.
4. Bajar los tokens que se cargan por defecto en cada despacho.

## Alcance

Incluido: los hallazgos H-1…H-49 de la auditoría y los menores listados en T-21.

No incluido:
- funciones nuevas;
- cambios de contrato con Jira, Confluence, Kwipu o Graphiti más allá de lo citado;
- reescribir los dashboards.

## Criterios de aceptación

- CA-01: Ningún script de estado (worklog, usage-meter, qa-gate) trata un fichero ilegible o con BOM como vacío ni lo sobrescribe.
- CA-02: Ninguna puerta de seguridad se apaga por un error de entrada: lentes C y D, guardarraíl del implementer en todos los modos e instalador en Windows.
- CA-03: El journal se reinyecta y los dashboards no pierden las iniciativas más nuevas con más de 1 MiB de ledgers.
- CA-04: La vía rápida de `/dev-cycle` tiene un camino de QA ejecutable y la evidencia TDD se comprueba.
- CA-05: Las mejoras de rendimiento se miden antes y después en `testing/perf.md`, con la misma salida funcional.
- CA-06: La carga por defecto baja y se mide con `context-footprint.py`; la vía rápida sigue ahorrando ≥ 6000 tokens estimados.
- CA-07: Lint, evals e interop sin errores, y la CI completa en Linux en verde.

## Restricciones

- TDD real (`docs/CONSTITUTION.md` §1): el rojo se observa antes del código y se registra en el ledger.
- Multi-runtime: Claude Code, Codex y OpenCode. Lo generado se regenera con `export-interop.py`.
- Sin datos personales en ficheros versionados.
