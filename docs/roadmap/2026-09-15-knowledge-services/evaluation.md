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
| Tiempo humano | 48h (40h base +20%) | Media |
| Tiempo IA / supervision | 14.4h / 3.6h | Media |
| Coste humano (50 EUR/h) | 2,400 EUR | Media |
| Tokens | 510k in / 205k out | Baja |

## Evaluacion por caracteristica

| ID | Alcance | Base | Riesgo |
|---|---|---:|---|
| C-01 | Esquema, taxonomia e indice | 10h | Contrato ambiguo o incompatible con memoria actual. |
| C-02 | Curator y Documenter | 9h | Solapar propuesta, aprobacion y escritura. |
| C-03 | Fase 4-bis, roles, contratos, interop | 8h | Romper secuencia de cierre. |
| C-04 | Exportador Kwipu | 8h | Filtrar fuentes excluidas o publicar parcialmente. |
| C-05 | Setup, doctor y degradacion | 5h | Convertir un opt-in en dependencia dura. |
| C-06 | Tests, revision y documentacion | 10h | Contratos sin cobertura de regresion. |

**Veredicto: Go condicionado.** Ejecutar O1: fuente Markdown, Curator y export derivado. Kwipu no puede bloquear; Graphiti queda fuera y requiere una spec independiente.