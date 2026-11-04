# Revisión de dos lentes — intento 2

Contexto fresco, agentes nativos reviewer A/B, misma copia saneada actualizada.
Se conserva la tabla completa del [intento 1](review-1.md); sin rebates.

| Criterio | A | B | Resultado fusionado |
|---|---|---|---|
| T-01: fuentes frescas/obsoletas y ausencia de escritura | ✓ | Conforme previo | Conforme |
| B-2 / T-01: recibo completo aceptado por verify | ✓ | ✗ | Important pendiente en este snapshot |
| T-02: procedimientos, activación, permisos y gates | ✓ | Conforme previo | Conforme |
| B-1 / T-03: baseline profundo con error JSON explícito | ✓ | ✓ | Corregido |
| T-03: comparación equivalente y estimaciones honestas | ✓ | Conforme previo | Conforme |
| T-04: documentación, generado y alcance | ✓ | Fuera de B | Conforme; cierre QA aún pendiente |

**B-2, Important, T-01:** el límite consideraba un byte LF, pero `print` escribe
CRLF en Windows. Con 32 rutas Unicode válidas y un recibo calculado de 65.536
bytes, snapshot emitía 65.537 bytes con `complete: true`; verify rechazaba su
salida. B ejecutó esa reproducción con CLI real y `collect` simulado.

Confirmado con RED en `test_receipt_budget_reserves_windows_crlf_at_the_exact_boundary`.
La corrección reserva ambos bytes CRLF en todas las plataformas. Windows actual:
48 passed, 1 skipped. No se cambia el límite de 64 KiB ni se recortan fuentes.
El siguiente intento revisa esta corrección y conserva lo aprobado salvo nueva
evidencia. A ejecutó interop, alcance y handbook con exit 0 y contrastó las
mediciones. Aprobación A no sustituye la corrección pendiente que señaló B.
