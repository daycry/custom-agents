# F3: validación automática cerrada, prueba real pendiente

Código comprobado: `4596eaf1bec3f21b21d364d5493b92d072f71cac`.
T-22..T-25 están implementadas. T-26 sigue en progreso: falta el resultado real
del otro equipo con Ollama, el Knowledge Gate posterior a QA y confirmar la
versión antes de fusionar/publicar. No hay release de F3.

| Puerta | Resultado y evidencia |
|---|---|
| Revisión independiente | A+B+C+D, intento 2/3: cero gaps. Los tres Important de intento1 tienen regresión dedicada y revalidación fresca. [Recibo](t26-review-2-2026-10-30.json). |
| CI Linux del código | [Run 41092581342](https://github.com/daycry/custom-agents/actions/runs/41092581342), verde sobre 4596eaf: Python 9889 pass/38 skip/82 subtests; Node 431 pass/16 skip/0 fail/0 cancel, 447 tests. Lint, evals, interop, bench, sintaxis y coherencia de versiones verdes. |
| Cobertura oficial del diff | Media aritmética 91,08% en 10 archivos Python cambiados, umbral 90, exit0. Corrida dirigida Linux 673 pass/9 skip y linter canónico 29/29. Archivos medidos contrastados byte a byte con el SHA. [Recibo y valores por archivo](t26-coverage-2026-10-30.json). |
| Generados y activación | Interop 88 al día; evals 192 casos sin errores; lint 0 errores y 3 avisos de nombres previos. |
| Alcance UI | `test-plan: n/a (sin UI)` del plan: `coverage-check.py` devuelve applies=false. No equivale a cobertura E2E verde ni se inventa una ejecución Playwright/qa-gate. Las verificaciones de tareas y la prueba nativa real son los oráculos. |
| Modelo/identidad nativos | Spike y reinstalación con CLI Codex0.166 real y Responses simulado, ya registrados en T-22. Prueba bindings/modelo/retirada y terminación; no inferencia o calidad Ollama. |
| Prueba real | [Ficha reproducible](t26-manual-ollama-checklist.md), pendiente del usuario; contexto declarado, observado y efectivo se registran por separado. |

## Límites de la medición

La media de cobertura no es el porcentaje global del repositorio ni exige 90%
por archivo. El informe global de la corrida dirigida es 49,5% y no es la métrica
del gate. JavaScript se valida con las suites Node, fuera de la cobertura Python.

La corrida completa instrumentada anterior sobre 4e5017d **no fue verde**:
9860 pass/57 skip y un fallo en el límite temporal de 1,5 s de un test de redacción
sin cambios desde la base publicada. Un control aislado con el mismo archivo de
fuentes pasa sin instrumentación y falla con coverage. No se cambió el umbral,
se suprimió el test ni se usa esa corrida como puerta superada. La cobertura
aceptada es la corrida dirigida del código corregido; la CI completa sin
instrumentación de 4596eaf está verde.
[Control y procedencia](t26-instrumented-timing-control-2026-10-30.json).

Los conteos de ejecuciones dirigidas se solapan. Tokens, coste y tiempo IA de
las ventanas actuales no tienen medida comparable; los minutos de reloj se
conservan como reloj, sin convertirlos a IA.

## Propuesta de publicación preparada

La propuesta es **v2.3.0**, aún sin aprobar. `release.py 2.3.0 --no-git` se ejecutó
en un clon local aislado y limpio, con checks y copias coherentes. Produjo cambios
en cinco manifiestos y los dos changelogs. El repositorio de trabajo conserva
v2.2.0; no se crearon commit/tag de release ni se publicó.

- [Patch de siete archivos](t26-release-v2.3.0-preview.patch), 12 inserciones y 6 eliminaciones.
- SHA256: `42e2c1125271315ba3bd1dca53bf5d23b05c80dbbd668b743f4cee8827d30788`.
- [Recibo](t26-release-preview-2026-10-30.json): proyección Git sin ruido CRLF,
  blobs previstos y comprobación inversa de aplicación exit0.

Se regenerará si cambian esos archivos o la fecha antes de pedir confirmación
final. Las dos propuestas de conocimiento de F3 siguen asociadas por ruta/SHA
en el ledger y pendientes de Curator tras QA; revisión y aprobación del diseño
no equivalen a aprobación de memoria.
