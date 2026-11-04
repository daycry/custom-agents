# Revisión T-05 — intento 2

Se conserva la [tabla completa del intento 1](quantity-review-1.md), sin rebates.
Dos revisores frescos examinan solo las correcciones y el verificador nuevo.

| Criterio T-05 | A | B | Resultado |
|---|---|---|---|
| Delegación explícita y párrafo original, A-1 | ✓ | ✓ | Contenido corregido |
| Verificador versionado y reproducible, A-2 | ✓ | ✓ | Corregido |
| Aritmética, costes y límites | ✓ | ✓ | 1.431,50 estimados; referencias 2.084,00 |
| Snapshots fijos, deriva e inventario | ✓ | ✓ | Comandos audit verdes |
| Cierre portable | ✓ | ✓ | snapshot→verify fresco |
| Test dedicado de la obligación restaurada | ✗ A-1.1 | Sin defecto detectado | Important confirmado |

Constitución §1 exige una regresión dedicada para cerrar el gap A-1. Se añade
`test_A1_delegation_transmits_read_rules_and_returns_findings`: comprueba que el
core obliga a transmitir las reglas y devolver hallazgos sin volcados, y que el
párrafo original completo permanece en la referencia. RED observado al reproducir
la omisión original; GREEN tras restaurarla. No se relaja ningún assert.

A ejecutó 99 tests; B ejecutó 14 tests del verificador y distribución, todos
aprobados. Cobertura Linux del verificador: 97,39 %, gate mínimo 90, ambos exit 0.
Se registra además el modo Unicode del verificador en la suite de consola:
8 tests aprobados sobre consolas cp1252/ASCII con salida UTF-8.

No cambia código del verificador, helpers, modelos, permisos o límites después
del intento 2. El intento 3 comprueba el test dedicado y su evidencia.
