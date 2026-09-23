---
design: design.md
test-plan: n/a (sin UI)
---

# 2026-09-16-training-data-services

> Captura determinista de casos y ensamblado de dataset para entrenamiento local; depende de `knowledge-services`, no de `graphiti-memory`.

| Metrica | Estimado |
|---|---:|
| Estado | en-progreso |
| Tiempo humano | 39.5h (enmienda 2026-09-17; antes 41h) |
| Tokens | 575k |
| Coste humano | 1,975 EUR + tokens por verificar |
| Tareas | 11 |

## Fases

1. **Config, esquema, redaccion compartida y capacidad**: `training.json`, esquema de caso, consumo de `redact.py` (lo extrae `session-end-durable-capture`) y registro en `capabilities.py` (`ADR-018`).
2. **Recorder y puerta humana**: recorder determinista, transiciones de estado, flag `--approved-by-human` obligatorio para Gold.
3. **Dedup, particion y ensamblador**: shingles anti-duplicado, particion por familia, ensamblador `train.jsonl`/`benchmark.jsonl`, puente a `knowledge-curator`.
4. **Setup, doctor, regresion y cierre**: opt-in, diagnostico, aislamiento/seguridad, interop, QA sin UI, retro.

## Invariantes

- El plugin nunca calcula ni interpreta metricas de dominio; solo valida forma.
- Ningun caso se exporta sin `validation.status == approved` y `approved_by_human == true`.
- La particion train/benchmark es por familia completa, nunca por version suelta.
- Sin `training.json` o desactivado, el ciclo actual funciona identico.
- Ningun adaptador de dominio (Blender, geometria) vive en este plugin.
