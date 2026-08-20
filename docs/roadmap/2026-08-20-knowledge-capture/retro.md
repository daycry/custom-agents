# Retro — knowledge-capture (2026-08-20)

> Iniciativa cerrada: plan `completado`, spec `implementada`. Cifras del ledger
> (`tasks.md`) y de los bloques `generacion:`, no de memoria. **En este ciclo `usage-meter.py`
> no midió nada** (sandbox cloud sin transcripción local): todos los bloques `generacion:` y las
> horas del ledger son `fuente: estimado`.

## Estimado vs real

| Concepto | Estimado | Real | Desviación |
|---|---|---|---|
| Horas humanas | 24,0 h (20 h base +20 %) | 0 h (no hubo trabajo humano de ejecución) | — no comparable |
| Horas IA de ejecución (tareas) | 0,56 h (+0,14 h supervisión) | 0,575 h (+0,147 h) — **estimado**, no medido | — sin desviación calculable (sin medición) |
| Tokens IA | 456k con margen (380k base; 255k por característica) | parcial, no comparable (ver nota observacional) | — |
| Coste económico | ≈1.205 € | n/d (sin medición de tokens facturables) | — |

**Ratio tokens→hora de esta iniciativa: NO calculable.** Regla del paso 2-bis de `/retro`: el
ratio solo se calcula con datos `fuente: medido`; aquí todo es `estimado`, así que la columna
`tokens/hora` de [`CALIBRATION.md`](../CALIBRATION.md) queda **vacía** para esta fila — no se
calibra con humo. La mediana vigente no cambia.

### Nota observacional — medición externa parcial del orquestador (NO calibra)

Medición externa parcial del orquestador del ciclo, con una **convención distinta a la de
`usage-meter.py`** (no distingue facturable de lectura de caché ni recorta ventanas compartidas):
se registra como observación y **no alimenta la calibración**:

| Ventana | Tokens | Reloj |
|---|---|---|
| revisor lente A (intento 1) | 144.022 | 7,5 min |
| revisor lente B (intento 1) | 138.036 | 9,3 min |
| verificador (intento 2) | 84.148 | 7,3 min |
| planner / implementer | sin medición (reanudaciones) | — |
| PM (evaluator, primera pasada — compartida con `confluence-policy`) | 88.206 | 7,9 min |

Conclusión observacional legítima: **la revisión adversarial consumió del orden de lo mismo que
la implementación** — ≈370k tokens medidos en revisores y verificador frente a una implementación
sin medir (16 tareas de prosa, comparable por tamaño a la de `confluence-policy`, 363k).

## Causas de la desviación (respuestas literales del usuario)

- **¿Qué explicó la desviación principal?** — «Las specs llegaron muy maduras» (las decisiones
  D1-D3 cerradas en la puerta PM evitaron re-trabajo en plan e implementación).
- **¿Qué se haría distinto?** — «Presupuestar la revisión aparte» (darle línea propia en la
  evaluación; 3 intentos × 2 lentes no es gratis).

## Aprendizajes

- **La revisión cazó un hueco de DISEÑO, no solo de código.** 16 tareas / 5 fases, revisión en 3
  intentos (12 gaps el 1.º, 5 residuales el 3.º). El hallazgo mayor: las entradas `propuesta` de
  `docs/knowledge/` se estaban aplicando como doctrina sin validación — un hueco del circuito de
  promoción que ninguna suite podía ver, cerrado con **dos promotores** explícitos (revisión de
  dos lentes en `/dev-cycle`; validación del usuario en `/retro`).
- **La trazabilidad a la fuente no es burocracia: detectó una invención.** El backfill traía una
  cifra («×15-30») que no estaba en su `retro.md` de origen — violación de CA-09 detectada
  cotejando la fuente, sustituida por las desviaciones literales. Sin la regla de "toda entrada
  enlaza a su fuente verificable", habría entrado doctrina inventada en la memoria del proyecto.
- **Contradicciones de alcance de escritura en planner/qa.** Añadir un permiso de escritura nuevo
  (`docs/knowledge/`) a agentes con reglas de "solo escribes en X" exige tocar la regla vieja en
  el mismo cambio — dos lentes lo encontraron en `planner.md` y `qa.md` (y el intento 3 amplió la
  excepción de `qa.md` que había quedado más estrecha que la regla).
- **Pérdida silenciosa de las lecciones en proyectos consumidores.** Un consumidor nuevo no tiene
  `docs/knowledge/` poblado: el texto que prometía «mismo contenido, misma prioridad»
  incondicional era falso allí. Resuelto con honestidad en el prompt (condicionado a memoria
  poblada) + aviso en `docs/INSTALL.md`.
- **«Presupuestar la revisión aparte» refuerza una lección ya aceptada** —
  [`LESSONS.md#evaluator` — «La revisión es la partida grande, no escribir»](../../knowledge/LESSONS.md#evaluator):
  ≈370k tokens medidos solo en revisores/verificador de este ciclo. No se crea entrada nueva: es
  la misma idea, se refuerza con este enlace cruzado.

## Ajuste sugerido para las próximas estimaciones

1. **Presupuestar la revisión adversarial como línea propia y dimensionada por intentos × lentes**:
   los 70k transversales estimados («la línea más alta evaluada hasta hoy») se quedaron ~5× cortos
   frente a los ≈370k medidos en revisores/verificador.
2. Mientras `usage-meter.py` no pueda medir en el entorno de ejecución (sandbox cloud), asumir que
   la fila de calibración saldrá vacía: si el ratio importa, ejecutar el ciclo donde haya
   transcripción local.
