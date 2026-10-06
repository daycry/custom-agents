# Protocolo reproducible de comparación

## Definir antes de ejecutar

Fija la revisión de código, fixture inicial, petición y criterio esperado por
caso. Incluye un caso representativo de cada stack afectado y fallos que la guía
pretende evitar: escritura duplicada/rollback, cancelación con cleanup y respuesta
React fuera de orden. No cambies el criterio tras ver qué salida produjo el modelo.

Un check puede ser un test de dominio, un contrato API o una inspección humana
predefinida. Una búsqueda textual de «TaskGroup» no demuestra cancelación; una
captura de pantalla no demuestra persistencia. Clasifica checks automáticos y
humanos por separado. Los juicios de un modelo son evidencia auxiliar con modelo,
prompt y revisión; nunca sustituyen una prueba ejecutable disponible.

## Ejecutar condiciones comparables

Repite baseline y variante sobre la misma copia inicial, modelos/herramientas,
permisos, presupuesto, dependencias y criterios. Ordena o alterna las ejecuciones
para no atribuir ruido temporal a la guía. Guarda la trayectoria permitida y
artefactos redactados, sin razonamiento privado ni secretos. Una tool ausente,
timeout o rechazo es un resultado distinto de un defecto funcional.

## Registrar y comparar

Por ejecución: ID del caso/run, revisión/fixture, variante, resultado de cada
check, comando/artefacto de evidencia y métricas realmente disponibles. Datos
de tokens/coste ausentes quedan null; duración requiere inicio/fin medidos.
Separa pass/fail/error/not-run; no cuentes not-run como aprobado.

Agrega ejecuciones ya realizadas con
`skills/outcome-evals/scripts/report_outcomes.py <runs.json>` (resuelve la skill
en el bundle antes de invocar). El manifiesto tiene `version: 1` y `runs`: cada
run declara id, case, variant, revisión Git de 40 hex, fixture_sha256 de 64 hex,
conditions (ID de condiciones fijadas), result (XML relativo al manifiesto) y
measurements. IDs son ASCII, hasta 64 caracteres. Measurements es null o un
objeto con source (`usage-meter|runner|manual`), tokens, duration_seconds y
cost_eur; las métricas ausentes son null, las presentes finitas y entre 0 y 10¹⁸.
Tokens es entero. La procedencia declarada no constituye verificación de medida.

El script no ejecuta tests, importa código del consumidor ni aprueba QA. Lee
JUnit limitado a 2 MiB, sin DTD/enlaces y con profundidad ≤32; verifica contadores
de suite contra los casos. Si falta evidencia o es inválida, ese run es error.
Skips/corpus vacío no dan pass. Comparabilidad exige al menos dos variantes con
los mismos casos/fixtures/conditions y número de repeticiones; no demuestra por
sí misma que el productor haya mantenido esas condiciones.

Publica denominador, casos y repeticiones, distribución y fallos de cada variante.
La conclusión debe explicar qué cambió y en qué condiciones; no generalices de
tres fixtures a todo el catálogo. Si no hay sesiones comparables, publica el
protocolo y sus checks como preparados, sin anunciar una mejora de agentes.

Usa `evals/` para fixtures y reportes de desarrollo. Si se capturan casos del
consumidor, utiliza training-data-services opt-in y su case store externo; solo
un humano marca Gold. Los resultados no pasan automáticamente a conocimiento
aceptado: conserva Knowledge Gate y procedencia de cada propuesta.
