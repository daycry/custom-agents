---
design: design.md
test-plan: n/a (sin UI)
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
---

# 2026-09-15-knowledge-services

> Knowledge Gate local y exportacion opcional a Kwipu; Graphiti diferido.

| Metrica | Estimado |
|---|---:|
| Estado | en-progreso |
| Tiempo humano | 56h (enmienda 2026-09-17; antes 48h) |
| Tiempo IA / supervision | 16.8h / 4.2h |
| Coste humano | 2,800 EUR + tokens por verificar |
| Tareas | 13 |

## Fases

1. **Contrato y validacion**: esquema, taxonomia, indice y estructura segura.
2. **Curacion y workflow**: Curator, propuesta desde Documenter y Fase 4-bis.
3. **Backends y Kwipu**: contrato de adaptador, `knowledge-sync.py`, Kwipu como primer adaptador sobre `outbox.py`, registro de capacidades, setup y doctor. **Puerta de entrada**: `session-end-durable-capture` completado.
4. **Regresion y cierre**: aislamiento, contratos, interop, QA sin UI y retro.

## Invariantes

- Markdown/Git es la fuente; el indice y export son derivados.
- Solo `approved/` se exporta; nunca journal, candidatos, rechazos, logs o datos de entrenamiento.
- **Taxonomia y enrutado de destino son configuracion del proyecto** (`.claude/knowledge-services/taxonomy.json`), nunca una lista fija del plugin; sin ese fichero, el plugin usa su propio default minimo.
- Una categoria sin `routing` declarado no exporta a ningun backend (fail-closed); `routing` solo cita ids declarados en `backends` (ADR-018).
- Anadir un backend = un adaptador + una entrada en `backends`; validador, Curator y `knowledge-sync.py` no cambian.
- Staging, manifiesto y dead-letter salen de `agent-kits/shared/outbox.py`; no hay una segunda cola.
- El utility scoring es opt-in, apagado por defecto, y nunca decide un estado por si mismo.
- Sin configuracion o salud Kwipu, todo el ciclo actual funciona sin bloquear.
- Kwipu indexa una vista, no ingiere: el plugin escribe el export en `generated_knowledge` y el reindexado (`build_view` + reinicio) es del stack; `verify` detecta el desfase y nombra el remedio, nunca lo ejecuta (enmienda 2026-09-18, CA-16).
- Graphiti no aparece en codigo, configuracion o writers de esta iniciativa.