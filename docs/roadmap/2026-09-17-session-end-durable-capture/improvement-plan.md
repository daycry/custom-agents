---
design: design.md
test-plan: n/a (sin UI)
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
---

# 2026-09-17-session-end-durable-capture

> `SessionEnd` captura en < 100 ms; el journal se materializa después, de forma recuperable; cola compartida para toda la memoria.

| Métrica | Estimado |
|---|---:|
| Estado | en-progreso |
| Tiempo humano | 14h |
| Tiempo IA / supervisión | 4.2h / 1.1h |
| Coste humano | 700 EUR + tokens por verificar |
| Tareas | 8 |

## Fases

1. **Módulos compartidos**: `outbox.py` y `redact.py` con tests; `journal.py` los importa sin cambiar comportamiento.
2. **Captura y materialización**: `capture-end`, `replay`, estados, exec form en `hooks.json`.
3. **Reconciliación y diagnóstico**: `SessionStart` con presupuesto, huérfanas, `status`, `/doctor`.
4. **Pruebas, medición y cierre**: suite de shell, bench, matriz de garantías, GOT, changelog.

## Invariantes

- `SessionEnd` no ejecuta git, IA ni red; solo escribe un envelope atómico.
- El journal final conserva ruta, formato e idempotencia por `session_id`.
- Nada se inventa: sin transcript ni log de prompts, la entrada declara la carencia.
- Un fallo de la cola nunca bloquea el arranque ni el cierre de Claude Code.
- El estado vive en `<proyecto>/.claude/journal/` (ignorado por git) y sobrevive a upgrade/uninstall.
- `outbox.py` es la única implementación de cola/staging de la cadena de memoria (la reutilizan Kwipu y Graphiti).
