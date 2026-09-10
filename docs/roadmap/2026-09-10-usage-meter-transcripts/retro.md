---
retro: usage-meter-transcripts
fecha: 2026-09-10
---

# Retro — usage-meter-transcripts (2026-09-10)

> Vía rápida cerrada: ledger `completado` (3/3), tres commits por tarea en `feature/plugin-refactor`
> (`cf88f35` T-01/T-03 · `791f43f` T-02 · `0ebcc1c` ledger + CHANGELOG + cifras). Cifras del ledger
> (`tasks.md`) y de los marcadores de `usage-meter`, no de memoria. **Es la primera iniciativa del
> proyecto en Windows con coste IA medido de verdad**: la propia iniciativa arregló el meter a mitad de
> ciclo, así que la parte anterior al arreglo va `(estimado)` y la posterior `(medido)`, y se dice cuál es cuál.
> Las causas del §Causas las propone el orquestador desde el ledger (él orquestó las desviaciones); el usuario
> las valida o corrige al leer esta retro.

## Estimado vs real

| Concepto | Estimado | Real | Desviación |
|---|---|---|---|
| Horas humanas | 1,6 h | **1,65 h** (estimado: sin supervisión humana registrada, «adelante con todo») | +3 % — sin muestra real, no calibra |
| Horas IA (ejecución) | 0,16 h | **0,82 h** (T-01 0,07 est. + 0,34 medido · T-02 0,03 est. + 0,04 medido · T-03 0,34 medido) | **+410 %** |
| Revisión (línea propia) | no presupuestada | **0,55 h IA medidas** desde la sesión principal: intento 1 (marcador `revision`, 1,13 €) + intento 2 con evidencia (marcador `evidencia-c4`, 3,16 €, 40 respuestas) | fuera del presupuesto: la vía rápida no la contaba |
| Tokens | 90k | **medidos por primera vez**: ventanas del orquestador 13.232 in · 33.904 out · 190.403 caché creación · 2.656.935 caché lectura (solo la ventana `evidencia-c4`); los marcadores del implementer están en el ledger en horas | — (la cifra estimada no distinguía facturables de lectura de caché: no es comparable) |
| Coste | ≈50 € | ≈4,3 € de IA medidos en las ventanas del orquestador + los marcadores del implementer (0,72 h IA medidas) + 1,65 h humanas estimadas | — |
| Tareas | 2 | **3** (T-03 añadida por la revisión: Critical fuera del diff que invalidaba el objetivo) | +1 |
| Intentos de revisión | 1 (vía rápida) | 2: intento 1 con lentes A+B (1 Critical, 6 Important, 7 Minor); intento 2 verificado de forma determinista por el orquestador tras morir las dos lentes por `Connection refused` | +1 |

## Causas

1. **El alcance real era doble y el análisis solo vio la mitad.** La clave de carpeta mal codificada era
   una causa; el `glob("*.jsonl")` plano que ignora `<session-id>/subagents/` era la otra (43,6 % de
   tokens sin contar). El Critical lo encontró la **Lente B midiendo** (5 vs 41 ficheros), no el análisis
   previo ni el implementer. Coste: T-03 entera, más los tests de recursión y dedupe.
2. **Dos hipótesis de causa raíz se dieron por buenas sin una segunda medición.** La del orquestador
   («los once artefactos `estimado` = solo la clave») y la del implementer («el JSONL del subagente no se
   vuelca hasta acabar el turno»). Las dos eran incompletas o falsas; `GOT-010` tuvo que reescribirse.
3. **Tests que no mordían.** 6 de los 7 tests nuevos pasaban con el código viejo: dos usaban **oráculo
   copiado del código bajo prueba** y uno comparaba dos literales. Obligó a la segunda ronda de corrección.
   El mutante final: regex vieja → 5 failed; glob plano → 2 failed.
4. **Una «medición» que parecía evidencia y era subconteo.** El primer `close` post-arreglo (06:47Z) dio
   `medido` con 6.407 tokens de salida en una ventana en la que dos lentes consumieron ~185.000: el glob
   plano no las veía. Y el marcador `correccion`, abierto con el código viejo y cerrado con el nuevo, contó
   **1.552 respuestas / 143 € de ayer** en 25 minutos (ficheros sin offset → enteros; el parser no filtra
   por `timestamp`). Ninguna de las dos se usó como evidencia final, pero costaron una ventana cada una.
5. **Las lentes del intento 2 murieron por conexión** y el usuario paró los agentes. El orquestador ejecutó
   los mismos oráculos deterministas (mutantes, diff, puertas) en vez de relanzar: más barato, pero sin
   segunda opinión de contexto fresco sobre la calidad de los oráculos y la prosa de `GOT-010`.
6. **Cerrar el ledger rompió `test_cifras_medidas` (29 fallos)** y un parche mecánico corrompió tres líneas
   (un «15» convertido en «116», una cita histórica alterada) que hubo que restaurar desde `HEAD`. Cuarta vez en
   dos días que abrir o cerrar una iniciativa mueve las cifras vivas de `changelog-brief` (ancladas en `ADR-012`,
   `medicion-escalera.md`, su ledger y el índice de la memoria). ≈0,3 h de orquestación no previstas.

## Aprendizajes

- **Una medición no es evidencia hasta que se compara con una segunda fuente.** Dos «medido» de hoy eran
  falsos por motivos opuestos (subconteo y sobreconteo). Candidata a lección para `/retro` (`journal.py candidatas`).
- **Cuando TODOS los tests de un script inyectan su dependencia de entorno, el código que la resuelve queda
  sin probar y su fallo es silencioso porque el script degrada «como debe».** Ya es `GOT-010` (`propuesta`).
- **Un test que construye su oráculo llamando al código bajo prueba no cubre nada**: el oráculo debe ser un
  literal externo (aquí, nombres de carpeta reales). Vale para todo el repo.
- **Los marcadores de `usage-meter` abiertos con el código anterior deben descartarse, nunca cerrarse.** Y un
  filtro `timestamp >= inicio` haría el meter robusto a ficheros con historial previo → `plugin-refactor` (E7-ii).
- **Cifras vivas en documentos históricos (un ADR aceptado, un ledger cerrado) son una alarma en cada cierre,
  no documentación.** Hueco de encadenamiento para `plugin-refactor` (E11): o las cifras se generan (y la doc
  cita la fecha de la medición), o el test vigila solo el documento que quiere ser vivo (`medicion-escalera.md`).
- **La vía rápida no presupuesta la revisión** y aquí fue la partida que lo cambió todo (`LES-009` otra vez).

## Ajuste sugerido

- **Vías rápidas sobre scripts de infraestructura de medición o puertas** (`usage-meter`, `ledger-lint`,
  `scope-check`, `qa-gate`): presupuestar la revisión de dos lentes **desde el inicio** y multiplicar la IA
  por **×3** respecto a la estimación «de una línea». La línea no era el trabajo: lo eran los tests que faltaban
  y la segunda causa que nadie había medido.
- **Regla para el orquestador**: ante una hipótesis de causa raíz, exigir una segunda medición antes de
  escribirla en un gotcha o en un ledger. `debug-root-cause` ya lo dice para los bugs; aplica igual a las causas.
- **`CALIBRATION.md`**: la fila deja `tokens/hora` **sin valor**: los tokens están medidos, pero las horas IA
  las deriva el propio meter con el ratio 479.326 — no hay medida independiente de horas, así que un ratio
  calculado sería circular. Cuando `usage-meter` mida horas de reloj (o el implementer anote reloj real), la
  columna tendrá dato.
