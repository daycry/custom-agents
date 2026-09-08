---
retro: memory-retrieval
fecha: 2026-09-08
---

# Retro — memory-retrieval (2026-09-08)

> Iniciativa cerrada: plan `completado`, spec `implementada` — tras esta retro, por la puerta `retro-gate.py`
> que la propia iniciativa introdujo (T-17): fue la primera a la que se le exigió. Cifras del ledger
> (`tasks.md`) y de los bloques `generacion:`, no de memoria. **En este ciclo `usage-meter.py` no midió
> nada** (sesión en Windows sin transcripción legible para el meter): los bloques `generacion:` y las horas
> IA del ledger son `fuente: estimado`, así que la fila de `CALIBRATION.md` deja `tokens/hora` **vacío** —
> no se calibra con humo. Las causas del §Causas se propusieron desde el ledger y se presentaron al usuario,
> que no las corrigió; su única instrucción fue dejar las horas humanas en 0.

## Estimado vs real

| Concepto | Estimado | Real | Desviación |
|---|---|---|---|
| Horas humanas | 34,0 h | **0 h registradas** («déjalo en 0») | −100 % — sin muestra, no calibra (8.ª iniciativa seguida sin horas humanas reales) |
| Horas IA (ejecución) | 2,60 h (+0,54 h de la línea de revisión = 3,14 h) | **4,32 h** (est.) | **+66 %** sobre el plan · +38 % sobre plan + línea de revisión |
| Supervisión | 0,66 h (+0,13 h) | 1,11 h (est.) | +68 % |
| Tokens | 1.248.000 | n/d — sin medición | — |
| Coste | ~2.050 € (34 h humanas + IA) | sin medir; horas humanas 0 | — |
| Tareas | 18 (6 fases) | **21** (18 + T-19/T-20/T-21, cierres de tres revisiones de dos lentes) | +3 fuera del plan |
| Revisión de dos lentes | línea propia: 0,54 h IA (12 % del presupuesto) | **38 gaps** (3 Critical · 13 Important · 22 Minor), 0 rebatidos; corregirlos costó **1,30 h IA** (30 % del real) | revisar estaba presupuestado; corregir, no |

Por fase (horas IA est. → real est.): F1 0,51 → 0,60 (+18 %) · F2 0,31 → 0,46 (+48 %) · F3 0,27 → 0,76 (+181 %, incluye T-19) ·
**F4 0,43 → 1,20 (+179 %, incluye T-20)** · F5 0,24 → 0,35 (+46 %) · **F6 0,30 → 0,95 (+217 %, incluye T-21)**. Las tres fases que
absorben un cierre de gaps son las que se disparan; las otras tres quedan entre +18 % y +48 %.

## Causas

1. **Desviación principal (+66 % IA): la corrección tras la revisión no estaba presupuestada.** Las tres
   revisiones de dos lentes encontraron 38 gaps (F1-3: 12 · F4: 16 con 1 Critical · F5-6: 10 con 2 Critical) y
   cada una abrió una tarea de cierre fuera del plan (T-19/T-20/T-21, 1,30 h). La línea transversal de revisión
   (0,54 h) cubría *revisar*; el plan no tenía línea para *corregir lo revisado*. `LES-001`/`LES-009` («el coste
   está en la revisión») se confirman por tercera vez, con matiz: el coste está en **lo que la revisión saca**.
2. **La incógnita marcada fue barata; las caras no estaban en la spec.** El riesgo señalado (contrato oficial de
   `UserPromptSubmit`) se cerró en cinco minutos con la doc oficial. Lo caro fue (a) la **privacidad de punta a
   punta** — el opt-out `<private>` protegía el log y el turno volvía por la transcripción (Critical de F4) —
   y (b) el **tope CA-08 del brief**, que depende de la ruta absoluta del repo y del tamaño de `docs/knowledge/`:
   cuatro recortes del ledger en un día para mantener T-18/T-19/T-20 bajo 10.000.
3. **F4 (hooks con degradaciones + privacidad) costó ×2,8.** La spec ya la declaraba «la fase más cara y de peor
   confianza», y aun así la estimación se quedó a un tercio.
4. **Entorno no presupuestado (~0,3 h):** Windows sin `python3` real (venv), checkout CRLF (medidas en LF),
   rutas con espacios, suite con 37 fallos de plataforma que hay que separar de los reales en cada pasada.

## Aprendizajes

1. **Presupuestar la corrección post-revisión como línea propia**, del mismo tamaño que la de revisión: aquí
   1,30 h reales frente a 0,54 h presupuestadas para revisar. Es lo que convierte «12 % del presupuesto» en el
   30 % real.
2. **Un control se prueba contra datos reales y de punta a punta** — dos veces en la misma iniciativa: el
   `<private>` que resucitaba por otro camino (F4) y la puerta de retro que exigía un frontmatter que ninguna de
   las 7 retros reales tenía (F6). Recogido en [`LES-015`](../../knowledge/lessons/LES-015-implementer-privacidad-de-punta-a-punta.md)
   (segunda evidencia añadida en esta retro).
3. **La suite de codificación solo ve scripts versionados**: `281 passed` antes de `git add`, 4 rojos en CI
   después. Trampa concreta → [`GOT-007`](../../knowledge/gotchas/GOT-007-suite-de-codificacion-solo-ve-scripts-versionados.md).
4. **El tope CA-08 del brief no es una constante del repo**: cambia con la máquina (ruta absoluta) y con el
   corpus de memoria (hasta su tope). Trampa concreta → [`GOT-008`](../../knowledge/gotchas/GOT-008-tope-ca08-del-brief-depende-de-ruta-y-corpus.md).
5. **Las horas humanas siguen sin muestra.** 34 h estimadas, 0 registradas; `CALIBRATION.md` lleva ocho
   iniciativas sin una fila con horas humanas reales (`LES-003`, aprendizaje 2 de CALIBRATION). Estimarlas sin
   muestra no calibra nada: infla el coste sin información.

## Ajuste sugerido

- **Revisión**: línea de revisión **y** línea de corrección post-revisión, cada una del tamaño de la revisión
  estimada (aquí habría sido 0,54 h + 0,54 h ≈ 1,08 h frente a 1,30 h reales).
- **Fases con hooks, degradaciones o privacidad**: ×2 sobre la estimación base (F4: 0,43 h estimadas, 1,20 h reales).
- **Horas humanas**: sin una muestra real en `CALIBRATION.md`, no presupuestarlas como producción; dejar la celda
  vacía y decirlo, como hace esta fila.
