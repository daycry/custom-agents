# Revisión T-05 — intento 1

Incremento nuevo solicitado por el usuario después de cerrar T-01..T-04. No
reabre sus tres intentos previos. Base del incremento: `173556d`, con CI verde
(10.368 pytest aprobados, 39 omitidos; Node 452 aprobados, 16 omitidos).
Dos revisores nativos con contexto fresco; alcance limpio comprobado con exit 0.

| Criterio T-05 | A | B | Resultado fusionado |
|---|---|---|---|
| Estimación y costes condicionales | ✓ | ✓ | Aritmética reproducida para ese snapshot |
| Sin promesa de consumo facturado | ✓ | ✓ | Conforme |
| Protocolo y cinco reglas originales íntegros | ✓ | ✓ | Conforme |
| Obligación de transmitir reglas al delegado | ✗ A-1 | Sin defecto detectado | Important confirmado |
| Cálculo versionado con tests y exit codes | ✗ A-2 | Sin defecto detectado | Important confirmado |
| Cierre portable snapshot→verify | ✓ | ✓ | Conforme, 86 tests focales aprobados |

A-1: el resumen omitía exigir pasar las reglas a quien explora por delegación.
Se restaura la obligación explícita y se conserva el párrafo original completo
en la referencia. Se recalculan los costes, sin inventar una excepción aprobada.

A-2: el cálculo inicial se produjo con un script de trabajo privado. La
Constitución exige script versionado con tests y códigos de salida. Se añade
`audit-token-estimates.py` como evidencia de la iniciativa, sin sumar una
capacidad pública al plugin. Consume snapshots declarados, reproduce JSON y
Markdown, y `--current` detecta cambios sin reescribir evidencia histórica.
RED observado del cálculo ausente; casos inválidos y deriva se prueban.

Ambos gaps confirmados, sin rebates. El baseline original ahora incluye
políticas literales y líneas de referencia extraídas del commit `9c109c5` en
`scenario-before.json`, para revisarlo sin acceso al repo exterior. La segunda
revisión debe reevaluar estas correcciones y el verificador nuevo.
