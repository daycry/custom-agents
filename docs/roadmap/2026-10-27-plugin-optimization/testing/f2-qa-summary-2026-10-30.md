# F2: QA y propuesta de entrega

F2 pasa la revisión independiente en dos intentos, el gate oficial de cobertura y la CI completa Linux sobre `e8a59ee8`. T-08..T-15 están completadas; T-16/T-17/T-18 son cancelaciones condicionales documentadas. T-19 sigue abierta para confirmar la versión y publicar.

| Comprobación | Evidencia |
|---|---|
| Revisión A/B/C/D | 28 criterios P/R; tres gaps corregidos; 0 Critical / 0 Important / 0 Minor pendientes |
| Linux normal | 9.764 Python pass, 38 skip y 82 subtests; 423 Node pass, cero fallos y 16 skip |
| Cobertura Python | Media oficial 92,25 % en los ocho ficheros productivos cambiados, mínimo 90 |
| Linux instrumentado dirigido | 1.125 pass / 16 skip, más 426 pass anexados con coverage oficial; suites existentes |
| Lint / evals / interop | Cero errores; 3 avisos genéricos previos; 192 casos; 88 ficheros vigentes |
| UI | Exención canónica del plan sin rutas UI; no se presenta como Playwright ejecutado |

El primer gate dirigido daba 87,49 %. Se amplía la ejecución con suites existentes de retoma, panel y exportación, sin modificar código ni tests. El export estricto encontró un filename virtual de tests sin fuente; la reexportación oficial con `--ignore-errors` conserva exactamente los 101 resúmenes existentes y exige los ocho ficheros productivos presentes y sin cambios. El porcentaje evalúa la media por fichero Python, no cobertura de líneas nuevas ni JavaScript.

Los controles finales observan reducciones T-10 de 70,087 % Claude, 72,022 % Codex y 73,912 % OpenCode; T-14 de 52,397 % en files, 36,694 % en untracked y 26,196 % en tracked. Son fixtures temporales con control intercalado, diez muestras por variante y calentamiento descartado; no representan entrega nativa ni OneDrive. T-12 tiene su propio recibo y contexto de muestra. T-13 estima 6.327 tokens menos en el quick path por chars/4; la carga de referencias adicionales reduce el ahorro. No equivale a consumo API.

Se preservan los tres gaps del intento 1 y sus RED antes del arreglo, las comparaciones históricas inconclusas y los timeouts exploratorios de Windows. La repetición aislada del marcador pasa, pero no prueba una causa única de los timeouts anteriores. No se amplían presupuestos para obtener verde.

Los cambios del supervisor Windows, la consolidación de shared y el recorte del índice no se implementan: sus condiciones de adopción no se cumplen. No hay promoción de memoria ni cierre de la iniciativa completa. F3 queda pendiente de publicación F2, revalidación y diseño aprobado. La propuesta de versión es **2.2.0**; la preview no autoriza crear tag ni publicar.

La preview aislada de **2.2.0** pasa dry-run, preparación sin Git, `release.py --check`, interop y exportación portable validada. Solo cambian cinco manifiestos y ambos changelogs. No crea commit, tag ni release. Recibo: `f2-release-preview-2.2.0-2026-10-30.json`.
