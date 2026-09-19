---
design: design.md
test-plan: n/a (sin UI)
---

# 2026-09-15-graphiti-memory

> Proyeccion temporal opcional de conocimiento aprobado; depende de `knowledge-services` completado.

| Metrica | Estimado |
|---|---:|
| Estado | en-progreso |
| Tiempo humano | 50h (enmienda 2026-09-17; antes 44h) |
| Tokens | 545k |
| Coste humano | 2,500 EUR + tokens por verificar |
| Tareas | 10 |

Fases: (1) contrato del adaptador y ontologia desde `taxonomy.json`, (2) adaptador `graphiti.py` sobre `outbox.py` con proveedor configurable, shadow mode, rebuild y revocacion, (3) router por configuracion + capacidad registrada, (4) pruebas, interop y cierre. Invariantes: fuente Markdown, solo approved, escritura centralizada, fallback local, ninguna llamada desde hooks, **ningun modelo ni endpoint cableado**, y Graphiti es un adaptador mas — el nucleo de `knowledge-sync.py` no lo nombra (`ADR-018`). Enmienda 2026-09-18 (validacion en vivo): el transporte es solo MCP streamable HTTP (`/mcp`, cliente minimo con stdlib), los tipos de entidad los fija el servidor y se mapean por configuracion, y `revoke` nunca borra episodios.