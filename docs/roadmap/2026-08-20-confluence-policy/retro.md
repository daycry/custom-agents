# Retro — confluence-policy (2026-08-20)

> Iniciativa cerrada: plan `completado`, spec `implementada`. Cifras del ledger
> (`tasks.md`) y de los bloques `generacion:`, no de memoria. **En este ciclo `usage-meter.py`
> no midió nada** (sandbox cloud sin transcripción local): todos los bloques `generacion:` y las
> horas del ledger son `fuente: estimado`.

## Estimado vs real

| Concepto | Estimado | Real | Desviación |
|---|---|---|---|
| Horas humanas | 21,6 h (18 h base +20 %) | 0 h (no hubo trabajo humano de ejecución) | — no comparable |
| Horas IA de ejecución (tareas) | 0,49 h (+0,16 h supervisión) | 0,57 h (+0,145 h) — **estimado**, no medido | — sin desviación calculable (sin medición) |
| Tokens IA | 426k con margen (355k base; 235k por característica) | parcial, no comparable (ver nota observacional) | — |
| Coste económico | ≈1.085 € | n/d (sin medición de tokens facturables) | — |

**Ratio tokens→hora de esta iniciativa: NO calculable.** Regla del paso 2-bis de `/retro`: el
ratio solo se calcula con datos `fuente: medido`; aquí todo es `estimado`, así que la columna
`tokens/hora` de [`CALIBRATION.md`](../CALIBRATION.md) queda **vacía** para esta fila — no se
calibra con humo. La mediana vigente no cambia.

### Nota observacional — medición externa parcial del orquestador (NO calibra)

Existe una medición externa parcial hecha por el orquestador del ciclo, con una **convención
distinta a la de `usage-meter.py`** (no distingue facturable de lectura de caché ni recorta
ventanas compartidas), así que se registra como observación y **no alimenta la calibración**:

| Ventana | Tokens | Reloj |
|---|---|---|
| planner (plan + tasks) | 156.246 | 9,4 min |
| implementer (pasada inicial, 13 tareas) | 362.593 | 30,1 min |
| revisor lente A | 148.163 | 5,7 min |
| revisor lente B | 81.068 | 5,3 min |
| 3 rondas de corrección y re-revisión | sin medición | — |
| PM (evaluator, primera pasada — compartida con `knowledge-capture`) | 88.206 | 7,9 min |

Conclusión observacional legítima: **la revisión adversarial consumió del orden de lo mismo que
la implementación** — ≈230k tokens medidos solo en las dos lentes del intento 1 frente a 363k de
la pasada inicial del implementer, y las 3 rondas de corrección (sin medir) van encima.

## Causas de la desviación (respuestas literales del usuario)

- **¿Qué explicó la desviación principal?** — «Las specs llegaron muy maduras» (las decisiones
  D1-D5 cerradas en la puerta PM evitaron re-trabajo en plan e implementación).
- **¿Qué se haría distinto?** — «Presupuestar la revisión aparte» (darle línea propia en la
  evaluación; 3 intentos × 2 lentes no es gratis).

## Aprendizajes

- **La revisión de dos lentes cazó lo que las suites no veían.** 3 intentos, 11 hallazgos en
  total: 2 CRÍTICOS (el README staged pisado por la plantilla del marcador, con riesgo de pérdida
  del canónico vía pull; un `rmtree` sin salvaguarda que podía borrar `docs/` entero), 1 fixture
  no versionada por un patrón de `.gitignore` (suite rota en clon limpio, invisible en local), y
  8 gaps más — incluida la enmienda al cierre del literal de CA-10, que era internamente
  contradictorio (el marcador `_STAGING-LEEME.md` quedó sin fecha para preservar la idempotencia
  byte a byte). Ninguna suite en verde habría detectado los dos críticos: solo el ataque
  adversarial los reprodujo. → Las dos trampas concretas quedan registradas como gotchas en
  [`docs/knowledge/gotchas.md`](../../knowledge/gotchas.md) (enlace cruzado, sin duplicar texto).
- **La revisión es la partida grande — confirmado también con medición externa.** Este ciclo
  refuerza la lección ya aceptada en
  [`LESSONS.md#evaluator` — «La revisión es la partida grande, no escribir»](../../knowledge/LESSONS.md#evaluator):
  ≈230k tokens medidos en revisores frente a 363k del implementer inicial, sin contar las 3
  rondas de corrección. No se crea entrada nueva: es la misma idea, se refuerza con este enlace.
- **Una spec madura abarata todo lo de después.** Las 13 tareas se completaron sin recortes ni
  bloqueos, y las desviaciones declaradas fueron de forma (prorrateos, un README de roadmap que
  no toca el implementer), no de fondo — coherente con la causa literal del usuario.

## Ajuste sugerido para las próximas estimaciones

1. **Presupuestar la revisión adversarial como línea propia y con su tamaño real**: los 70k
   estimados como línea transversal se quedaron muy cortos frente a los ≈230k medidos solo en el
   intento 1 (más 3 rondas sin medir). Dimensionarla por nº de intentos × lentes, no como margen.
2. Mientras `usage-meter.py` no pueda medir en el entorno de ejecución (sandbox cloud), asumir
   que la fila de calibración saldrá vacía: si el ratio importa, ejecutar el ciclo donde haya
   transcripción local.
