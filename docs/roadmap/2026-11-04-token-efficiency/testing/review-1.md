# Revisión de dos lentes — intento 1

Contexto fresco, solo lectura, copia aislada del alcance aprobado. La copia
excluye las preferencias locales; `scope-check.py --base HEAD` salió con 0.
El selector de las dos piezas ejecutables devolvió C=false y D=false.
Agentes nativos `custom-agents-reviewer`, lentes A y B en paralelo.

| Criterio | A | B | Resultado fusionado |
|---|---|---|---|
| T-01: fuentes frescas/obsoletas y ausencia de escritura | ✓ | ✓ | Conforme |
| T-01: recibos completos reutilizables por CLI | ✓ | ✗ B-2 | Important confirmado |
| T-02: procedimientos, activación, permisos y gates | ✓ | ✓ | Conforme |
| T-03: comparación equivalente y estimaciones honestas | ✓ | ✓ | Conforme |
| T-03: errores de baseline explícitos | ✓ | ✗ B-1 | Important confirmado |
| T-04: contratos, documentación y generado | ✓ | Fuera de B | Conforme; QA final pendiente |

| Gap | Grado | Evidencia y escenario | Decisión |
|---|---|---|---|
| B-1 | Important | `context-footprint.py` no capturaba RecursionError con un baseline JSON de profundidad 5000, aun dentro del presupuesto de bytes | Confirmado. `test_cli_rejects_null_or_duplicate_baseline` rojo observado; captura explícita añadida, salida JSON incompleta y exit no cero |
| B-2 | Important | `source-snapshot.py` podía emitir un recibo completo de más de 64 KiB con 32 rutas Unicode válidas; la CLI verify no admitía ese recibo | Confirmado. `test_snapshot_never_emits_a_complete_receipt_its_cli_cannot_read` rojo observado; generación comprueba el tamaño UTF-8 con newline y devuelve `receipt_budget` |

No hay rebates ni gaps descartados. Ningún permiso o umbral se relaja.
Tras corregir: helpers Windows 47 passed, 1 skipped (sin privilegio symlink).
La revisión del diff corregido debe reevaluar B-1/B-2 sin reabrir lo ya aprobado,
salvo evidencia nueva. A ejecutó `export-interop.py --check`: exit 0, 92 ficheros
al día; comparó procedimientos literales, descriptions y las 60 rutas/tamaños.
