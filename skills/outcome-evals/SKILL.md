---
name: outcome-evals
description: >
  Evaluación de resultados de tareas con corpus versionado, checks deterministas,
  ejecuciones comparables y mediciones compatibles. Separa éxito de activación.
  Úsala cuando el usuario diga "evalúa resultados", "compara dos workflows"
  o "mide si las nuevas skills mejoran las tareas".
---

# Resultados medidos del workflow

Lee [protocolo](references/protocol.md) **solo** al preparar una comparación.
Define corpus/fixtures y checks antes de ejecutar; usa herramientas del proyecto
en copias aisladas autorizadas. qa conserva el veredicto de pruebas. El checker
de activación y el inventario no miden resolución de tareas.

## Antes del veredicto

Formato: `agent-kits/shared/rationalization-table.md`.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Activó la skill» | La activación no demuestra resolver la tarea. | Compruebo el resultado contra checks del caso. |
| «El modelo dice que funciona» | Su juicio no sustituye una prueba disponible. | Ejecuto el check o registro juicio humano separado. |
| «El corpus es fácil» | Casos triviales no validan límites relevantes. | Incluyo errores, límites y negativos pertinentes. |
| «La media mejoró» | La media oculta fallos y condiciones distintas. | Publico casos, repeticiones, fallos y condiciones. |
| «No hay tokens disponibles» | Una cifra inventada no es una medición real. | Dejo la métrica ausente y registro ese límite. |
| «Todos los casos son Gold» | El plugin no tiene autoridad para aprobarlos. | Mantengo la aprobación humana del case store. |

## Salida y evidencia

Salida: informe con corpus/revisiones, resultados por caso, faltantes y límites.
No aprueba memoria, no entrena, no instala runners ni lanza sesiones que generen
coste externo sin autorización vigente. training-data-services conserva su
contrato opt-in y la promoción humana; no dupliques su almacenamiento.

| Referencia | Cuándo leerla |
|---|---|
| [Protocolo](references/protocol.md) | Corpus, comprobaciones y comparación de resultados |
| `scripts/report_outcomes.py` | Agregar JUnit existente con runs/condiciones y métricas declaradas; no ejecutar ni aprobar QA |
