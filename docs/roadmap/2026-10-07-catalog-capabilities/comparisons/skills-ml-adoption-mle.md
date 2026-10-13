# Adopción de aprendizaje automático y flujo de ingeniería de ML — S175–S176

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Dos cuerpos completos: **26.349 bytes/405 líneas**, sin recursos locales.
[ml-adoption-mle-reading-evidence.json](ml-adoption-mle-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S175 — Introducir ML en un código que no lo tiene

`3.899 bytes/57 líneas`. Cinco fases: encuadre y viabilidad (¿basta una
heurística?, métrica de negocio, presupuesto de errores), datos (fuentes,
contrato de datos, fuga de información en la partición), integración desacoplada
(frontera de API, alternativa por regla si el modelo falla o tarda, flag),
modelo base reproducible con script de evaluación, y traspaso a operación.

## S176 — Flujo de ingeniería de ML en producción

`22.450 bytes/348 líneas`. Contrato de predicción y de datos, entrenamiento
reproducible, puertas de promoción declaradas antes de entrenar, empaquetado para
servir, monitorización y vuelta atrás; además una plantilla de una página
(«Iteration Compact»), un bucle de decisión, economía de errores (qué error
abarata cada métrica y quién lo paga), análisis de errores por grupos y un
registro de observaciones por iteración. Remite a una veintena de piezas del corpus.

## Comparación

No hay consumidor que declare ML y `stack-practices` solo tiene Python genérico.
Como con los stacks sin consumidor (Java en S145, Go en S116–S117), **no se abre
especialidad**; si un consumidor lo declara, S175 y S176 se leen juntas como una
sola referencia (con las piezas de PyTorch y de migraciones que citan; el bloque
de migraciones ya registró a S176 como caller). Gran parte del método ya tiene
dueño en el plugin:

| Idea de la pieza | Pieza propia |
|---|---|
| Empezar por la decisión y preguntar si una regla bastaría | `analyst` (contraejemplos y fuera de alcance) y la puerta go/no-go de `evaluator` |
| Investigar soluciones existentes antes de construir | `research-first` |
| Puertas de promoción fijadas antes de ver resultados | `outcome-evals`: «No cambies el criterio tras ver qué salida produjo el modelo» |
| Comparar contra la línea base en condiciones iguales | `outcome-evals/references/protocol.md` (baseline y variante sobre la misma copia) |
| Registro de observaciones por iteración y lección capturada | Ledger canónico, `/retro` y candidatos de conocimiento curados (ADR-018) |
| Cada error importante se conserva como test de regresión | `debug-root-cause` (fix con test de regresión) |

Defectos concretos de los ejemplos de S176:

| Ejemplo | Problema | Adaptación |
|---|---|---|
| `assert_promotion_ready` compara con `<` y `>` | Un `NaN` no es menor ni mayor que el umbral: la métrica corrupta **pasa** las dos direcciones, aunque la checklist exige puertas que «fallan cerradas» | Rechazar valores no finitos antes de comparar; `report_outcomes.py` del plugin ya exige métricas finitas |
| `artifact_name` concatena a mano cuatro campos del config | Un hiperparámetro nuevo no entra en el hash hasta que alguien edite la clave: dos configuraciones distintas comparten nombre | Serializar el config completo de forma canónica |
| El nombre usa `dataset_uri`, no una versión del dataset | Si la URI apunta a datos mutables, el mismo nombre cubre datos distintos, contra «registrar versión o snapshot del dataset» | Hash del snapshot o su identificador inmutable |
| Umbrales `auc ≥ 0,82`, `p95 ≤ 80 ms` | Cifras de ejemplo sin justificar | Fijarlas desde el coste de cada error, como pide la propia pieza |

En S175, la fase 1 propone empezar por una heurística, pero la fase 4 solo compara
el modelo con «la línea base» del propio modelo; S176 sí pide comparar con la
línea base y con lo que ya está en producción. La comparación con la regla actual
debería ser explícita.

**Destino:** **sin destino** inmediato. Si un consumidor declara ML, una referencia
única con el contrato de predicción y de datos, fuga de información,
equivalencia entre entrenamiento y servicio, y las correcciones anteriores; la
regla general «un valor no finito es ausencia, nunca un pase» ya está en el
protocolo de `outcome-evals`.
