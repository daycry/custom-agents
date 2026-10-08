# Diagnóstico: acciones derivadas del informe canónico

Comparación pertinente para el Bloque 5, sobre revisión fijada
`ef648e01899ba3e8dc6371642deaaf64b4477775`. C030 aporta un diagnóstico reproducible
con acciones prioritarias. Su cuerpo, motor y callers pertinentes se leyeron
completos, sin ejecutar código del corpus. No cierra la evaluación global de
otros agentes o skills; las nuevas skills siguen aplazadas.

| ID | Lectura completa | Contrato observado |
|---|---|---|
| C030 | 84 líneas / 3.170 bytes | Informe estático por categorías y tres acciones ordenadas |
| R-3d9f69328581 | 1.085 líneas / 35.498 bytes | Inspección de archivos/cadenas y scoring por presencia/cantidad; no ejecuta hooks ni mide latencia |
| A031 | 55 líneas / 4.923 bytes | Caller de optimización; promete una medida de latencia que el motor no produce |
| S052 | 46 líneas / 1.190 bytes | Caller de ciclo; contexto y recomendaciones, sin acreditar calidad por score |

Los hashes/rangos figuran en la [evidencia de lectura](command-diagnostics-reading-evidence.json). La lectura
histórica de 18/94 cuerpos no se convierte en 18 evaluaciones completas: solo
C030 completa su ficha de diagnóstico aquí. Las rutas de origen permanecen
en el mapa privado. Ningún código o prompt del corpus se ejecuta para validar
la implementación propia.

## Contraste y decisión

`commands/doctor.md` y `commands/setup.md` ya usan el diagnóstico compartido.
Las utilidades de filas, registros pertinentes, ensamblado, Markdown y CLI de
`agent-kits/shared/doctor.py` conservan estado, comprobación, detalle y arreglo;
el informe termina con tablas y conteos, sin una selección estructurada de
acciones. Se contrastaron esos consumidores y la exportación de sus cuerpos.
No se afirma lectura completa de todos los checkers del script.

Se consolida la priorización en doctor, fuente única de diagnóstico. El JSON
añade `acciones_prioritarias`: total de filas accionables, límite tres y
selección con referencias al bloque y ordinal originales. Errores preceden
a avisos; el orden canónico desempata. Dos problemas con el mismo remedio
conservan identidad. Las filas informativas, sin arreglo o con arreglo vacío
permanecen en el informe y no originan recomendaciones.

Markdown presenta exactamente esa selección; los bloques completos, sus filas
de cuatro campos, conteos y exit codes continúan. No se calcula una puntuación,
infiere un path desde la prosa ni ejecuta un remedio. Se retiran afirmaciones
de salud global basadas solo en ausencia de errores. El onboarding describe la
excepción de red existente para capacidades opcionales activadas y utiliza
los resultados del mismo diagnóstico.

Se descartan umbrales de población, calidad por presencia de `PreToolUse`,
latencia no medida y rollback automático. Las guardias requieren su evidencia
nativa; la presencia de archivos no la reemplaza. La proyección en el panel
será opt-in y conservará fuente/scope/vigencia, porque ejecutar doctor puede
consultar runtimes y capacidades configuradas.

## Validación del bloque

RED/GREEN y pruebas sobre prioridad, empates, truncamiento, ausencia de remedios,
acciones repetidas en hallazgos distintos, texto con pipes/newlines, selección
JSON/Markdown, filas/exit y ausencia de cambios en fixtures. Suite propia de
doctor en consumidores y homes aislados, cobertura oficial del diff >=90%,
docs ES/EN, exports, revisión y push comprobado; el ledger registra resultados.
Las pruebas de activación no se anuncian como ejecución nativa del comando.
Bloque aceptado en revisión y [QA final](../panel-command-qa-evidence.json): 361 identidades únicas cubiertas junto al panel. T-05/T-11 globales abiertas. La lectura histórica conserva el estado previo a entrega; esta integración consolida un concepto de C030 en doctor, sin añadir comando o skill.
