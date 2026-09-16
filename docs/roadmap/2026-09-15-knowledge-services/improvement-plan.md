---
design: design.md
test-plan: n/a (sin UI)
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
---

# 2026-09-15-knowledge-services

> Knowledge Gate local y exportacion opcional a Kwipu; Graphiti diferido.

| Metrica | Estimado |
|---|---:|
| Estado | borrador |
| Tiempo humano | 48h |
| Tiempo IA / supervision | 14.4h / 3.6h |
| Coste humano | 2,400 EUR + tokens por verificar |
| Tareas | 12 |

## Fases

1. **Contrato y validacion**: esquema, taxonomia, indice y estructura segura.
2. **Curacion y workflow**: Curator, propuesta desde Documenter y Fase 4-bis.
3. **Kwipu**: export atomico, skill, setup y doctor opcionales.
4. **Regresion y cierre**: aislamiento, contratos, interop, QA sin UI y retro.

## Invariantes

- Markdown/Git es la fuente; el indice y export son derivados.
- Solo `approved/` se exporta; nunca journal, candidatos, rechazos, logs o datos de entrenamiento.
- **Taxonomia y enrutado de destino son configuracion del proyecto** (`.claude/knowledge-services/taxonomy.json`), nunca una lista fija del plugin; sin ese fichero, el plugin usa su propio default minimo.
- Una categoria sin `routing` declarado no exporta a ningun backend (fail-closed).
- El utility scoring es opt-in, apagado por defecto, y nunca decide un estado por si mismo.
- Sin configuracion o salud Kwipu, todo el ciclo actual funciona sin bloquear.
- Graphiti no aparece en codigo, configuracion o writers de esta iniciativa.