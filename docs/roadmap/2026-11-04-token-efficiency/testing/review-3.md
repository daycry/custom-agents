# Revisión de dos lentes — intento 3

Dos revisores nativos con contexto fresco revisaron la corrección pendiente,
con las tablas completas de los [intentos 1](review-1.md) y [2](review-2.md).
No hay rebates ni nuevas lentes C/D seleccionadas.

| Criterio | A | B | Resultado fusionado |
|---|---|---|---|
| B-2 / T-01: recibo válido con newline Windows | ✓ | ✓ | Corregido |
| T-01: frescura, límites y ausencia de escritura | ✓ | Conforme previo | Conforme |
| T-02: procedimientos, activación, permisos y gates | ✓ | Conforme previo | Conforme |
| B-1 / T-03: baseline profundo explícito | ✓ | Conforme previo | Corregido |
| T-03: comparaciones equivalentes y estimación honesta | ✓ | Conforme previo | Conforme |
| T-04: generado | ✓ | Conforme previo | Conforme; QA global sigue pendiente |

A ejecutó ambos módulos: 48 passed, 1 skipped; interop: exit 0, 92 ficheros al día.
B ejecutó las dos regresiones de presupuesto y reprodujo snapshot→verify en
subprocesos Windows: recibos de 65.535 y 65.536 bytes, incluido CRLF, salieron
completos y verify respondió `fresh`. Un candidato de 65.537 bytes produjo
`receipt_budget`, `complete: false`, exit 1. No se modifican los límites.

**Veredicto fusionado: sin gaps Critical/Important pendientes en las correcciones
examinadas.** La revisión no certifica la suite completa ni el consumo real.

## Ajuste posterior de fixture por QA

La regresión completa inicial señaló que el fixture OpenCode aún exigía los
cuatro párrafos de cuerpo previos a la compactación aprobada en T-02. Se
actualizó exclusivamente `description_body` para analyst, architect, documenter
y knowledge-curator. Los campos nativos `description`, `mode`, `permissions`,
versiones y hashes de esquema se conservan. No se eliminan tests ni asserts:
el contrato sigue comparando exactamente los campos nativos y el contenido de
cuerpo esperado. Justificación: spec §3 autoriza deduplicar activación y compactar
instrucciones manteniendo contratos. Antes: test rojo de semántica OpenCode;
después: 50 tests de exportación aprobados en Windows.

`opencode-contract-adjustments.json` registra los hashes viejo/nuevo y el motivo.
Este ajuste de expectativa lo verifica el orquestador con QA, después de las
lentes; no se atribuye a una aprobación de los revisores del intento 3.
