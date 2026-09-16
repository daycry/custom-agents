---
design: design.md
test-plan: n/a (sin UI)
---

# 2026-09-16-dev-cycle-dataset

> Adaptador de dogfooding: traduce tareas cerradas de `/dev-cycle` a casos de `training-data-services`, sin diff de codigo por defecto y sin juicio nuevo del LLM.

| Metrica | Estimado |
|---|---:|
| Estado | borrador |
| Tiempo humano | 26h |
| Tokens | 360k |
| Coste humano | 1,300 EUR + tokens por verificar |
| Tareas | 8 |

## Fases

1. **Opt-in y mapeo (modo metadata)**: `dev.json`, extraccion de campos con lista blanca.
2. **Derivacion deterministica**: outcome/validation desde ledger-lint/qa-gate/revision/usage-meter.
3. **Hook en Fase 6 y modo full-diff**: punto de aprobacion humana, doble opt-in para el diff completo.
4. **Regresion, interop y cierre**.

## Invariantes

- Sin `datasetCapture` activo, `/dev-cycle` funciona identico a hoy.
- El modo `metadata` (default) nunca incluye el diff de codigo fuente.
- `outcome`/`validation` se derivan de scripts existentes, nunca de un juicio nuevo del LLM.
- Familia = iniciativa completa, nunca tarea suelta.
- Gold solo se marca en el paso de integracion del ritual de cierre, con confirmacion humana.
