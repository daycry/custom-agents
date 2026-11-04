# Cuántos tokens se podrían ahorrar

Escenario: una pasada de analyst, evaluator, architect y planner, cada uno
con contexto separado. Cuenta el mapa completo y las políticas de lectura/salida
directamente referidas, una vez. No carga referencias nuevas condicionales.

**Estimación: unos 1430 tokens de entrada menos por recorrido PM.**
Método: caracteres UTF-8 normalizados a LF / 4. No es un tokenizer nativo,
consumo real medido ni una garantía de facturación.

| Rol | Tokens de entrada estimados que se eliminan |
|---|---:|
| analyst | 89.50 |
| evaluator | 361.75 |
| architect | 464.75 |
| planner | 515.50 |
| Total del escenario | 1431.50 |

Se excluyen envolturas nativas sin cambios, otros recursos previos, lecturas
del proyecto, herramientas, respuestas y reintentos. La carga del cliente,
el tokenizer y la caché pueden cambiar el resultado. No se estima dinero.

## Costes condicionales

Leer cada archivo completo una vez añade este presupuesto de entrada:

| Referencia | Tokens estimados adicionales |
|---|---:|
| `code-health.md` | 223.25 |
| `plan-maintenance.md` | 402.50 |
| `task-types.md` | 524.25 |
| `source-reuse.md` | 934.00 |
| Todas, una vez | 2084.00 |

Si se cargan todas, antes de contar lecturas evitadas, habría unos 652
tokens adicionales. Una referencia puede necesitarse en varios contextos.
No hay un ahorro universal garantizado.

Evitar releer 20.000 caracteres equivale aproximadamente a 5.000 tokens por
lectura evitada. Es un ejemplo de cálculo, no una observación. Hay que
descontar recibos, interpretación y referencias necesarias.

El consumo real total exige ejecuciones equivalentes con medidas nativas:
mismo modelo, objetivo, calidad y condiciones. No se han lanzado sesiones
de pago para este informe. Consumo observado y ahorro de salida: desconocidos.

## Reproducir y comprobar

`python docs/roadmap/2026-11-04-token-efficiency/testing/audit-token-estimates.py`
reproduce los snapshots versionados y comprueba JSON y Markdown: exit 0
vigentes, 1 cifras distintas, 2 entrada inválida o ausente. `--current` compara
además con las fuentes actuales; no obliga a reescribir evidencia histórica.
`--generate` emite JSON por stdout; `--generate --markdown` emite este texto.
`--capture-current` emite el snapshot actual por stdout. No escribe archivos.

Fuentes: scenario-before.json (commit original y políticas literales),
scenario-after.json y token-estimates.json. No contienen datos privados.
