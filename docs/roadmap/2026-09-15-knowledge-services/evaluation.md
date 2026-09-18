---
evaluation: knowledge-services
estado: completado
spec: spec.md
plan: improvement-plan.md
creado: 2026-09-15
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
---

# Evaluacion - knowledge-services

| Metrica | Estimado | Confianza |
|---|---:|---|
| Tiempo humano | 56h (46.7h base +20%) — antes 48h | Media |
| Tiempo IA / supervision | 16.8h / 4.2h — antes 14.4h / 3.6h | Media |
| Coste humano (50 EUR/h) | 2,800 EUR — antes 2,400 EUR | Media |
| Tokens | 580k in / 235k out — antes 510k / 205k | Baja |

## Evaluacion por caracteristica

| ID | Alcance | Base | Riesgo |
|---|---|---:|---|
| C-01 | Esquema, taxonomia e indice (+`taxonomy.schema.json`, `backends`) | 11h | Contrato ambiguo o incompatible con memoria actual. |
| C-02 | Curator y Documenter | 9h | Solapar propuesta, aprobacion y escritura. |
| C-03 | Fase 4-bis, roles, contratos, interop | 8h | Romper secuencia de cierre. |
| C-04 | `knowledge-sync.py` + contrato de adaptador + Kwipu como primer adaptador (sobre `outbox.py`) | 11h | Filtrar fuentes excluidas o publicar parcialmente; adaptador que se salte `routing`. |
| C-05 | Setup, doctor y degradacion via `capabilities.py` | 6.7h | Convertir un opt-in en dependencia dura. |
| C-07 | Registro de capacidades (`capabilities.py`) | 3h | Registro que solo sirva a esta iniciativa; se prueba con dos capacidades desde el primer dia. |
| C-06 | Tests, revision y documentacion | 10h | Contratos sin cobertura de regresion. |

**Veredicto: Go condicionado.** Ejecutar O1: fuente Markdown, Curator y export derivado. Kwipu no puede bloquear; Graphiti queda fuera y requiere una spec independiente.

## Enmienda 2026-09-17

Re-estimacion tras la enmienda de la spec (backends declarados, contrato de adaptador, esquema versionado,
registro de capacidades, cola compartida): **+6.7 h base** repartidas en C-01/C-04/C-05/C-07 -> 46.7 h base,
56 h con +20 %, 2,800 EUR. Dependencia nueva: la Fase 3 (Kwipu) espera a `session-end-durable-capture`
`completado` (entrega `outbox.py`, ~14 h, P0). Veredicto **se mantiene Go condicionado**: el sobrecoste (+17 %)
compra que el segundo backend (Graphiti) y cualquier tercero entren sin tocar el nucleo, lo que se verifica con
el adaptador `test` de CA-12.
