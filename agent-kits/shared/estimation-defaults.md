<!--
  FRAGMENTO COMPARTIDO: parámetros de estimación (fuente única).
  Lo leen `evaluator` y `planner` (y la lógica de horas de `jira-sync`).
  Si cambias un valor aquí, cambia para todos — no dupliques esta tabla en prompts.
-->

# Parámetros de estimación — defaults compartidos

> **Fuente única de config: `.claude/rates.json`.** Si existe (plantilla en `agent-kits/evaluator/templates/rates.example.json`), lee de ahí tarifa, precio de tokens, tipo de cambio, ratio de supervisión, margen y jornada — así `evaluator`, `planner` y `jira-sync` usan los mismos números. Localízala con `find "$PWD/.claude" "$HOME/.claude" -type f -path '*rates.json'`. La tabla siguiente es solo el **fallback** si no existe; si la creas o cambias, esos valores mandan.

| Parámetro | Default | Uso |
|-----------|---------|-----|
| Tarifa de desarrollo | `50 €/h` | Coste humano = horas × tarifa |
| Modelo IA asumido | `claude-opus-4-8` | Base de la previsión de tokens |
| Precio tokens input/output | (a confirmar) | Coste IA; **verifica la tarifa vigente**, no la inventes |
| Tipo de cambio USD→EUR | `1 USD = 0.92 €` | Si el proveedor factura en USD |
| Ratio de supervisión | `~25 % de las horas IA` | Tiempo de revisión/validación humana del trabajo del agente |
| Horas por empleado-mes (FTE) | `160 h` | Base para el cálculo de FTE equivalentes |
| Margen de contingencia | `20 %` | Colchón por imprevistos; se aplica sobre las horas **base** (humanas e IA) |
| Ratio tokens→hora-IA | `300.000 tok/h` ⚠️ no calibrado | Deriva horas-IA de tokens **facturables** (entrada + creación de caché + salida; la lectura de caché no cuenta). **Precedencia:** mediana de la columna `tokens/hora` de `docs/roadmap/CALIBRATION.md` (lo alimenta `/retro` con datos medidos) > este default. Lo aplican `usage-meter.py` y `evaluator`. Ejecuta `/retro` en cuanto cierres iniciativas medidas para calibrarlo |

Registra los valores usados en el bloque de **Supuestos** del artefacto que generes. Si no conoces el precio de tokens vigente, márcalo `⚠️ verificar` y deja el cálculo parametrizado en lugar de dar una cifra falsa.

**Precio de tokens fiable:** considera `precioTokens` de `.claude/rates.json` fiable solo si `input`/`output` > 0 **y** `verificadoEl` es reciente (< ~90 días). Si falta, es 0 o es antiguo, sigue mostrando `⚠️ verificar` y sugiere ejecutar la skill **`rates-verify`** (consulta la doc oficial de precios y lo actualiza con fecha; nunca inventa). No aproximes el precio a mano.
