---
design: graphiti-memory
estado: aprobado
opcion_elegida: O1
---

# Diseno - proyeccion Graphiti derivada

**O1 elegida:** `approved/` es la fuente, un sincronizador genera episodios idempotentes SOLO para las categorias cuyo `routing.graphiti` (en `.claude/knowledge-services/taxonomy.json`, definido por `knowledge-services`) sea `true`, y un router consulta Graphiti solo ante relaciones, evidencia o tiempo. **O2 descartada:** guardar memoria de cada turno, por ruido, privacidad e inyeccion. **O3 descartada:** hacer que Graphiti sea el almacen primario. **O4 descartada:** sincronizar TODO `approved/` sin distincion por categoria — el plugin es base de proyectos con dominios distintos y no todos quieren relaciones temporales para todas sus categorias (p. ej. un `TOOL` documentado no necesita grafo).

Cada instalacion configura un `group_id` estable bajo `.claude/knowledge-services/`; nunca acepta uno libre desde el prompt. Las escrituras pasan por Curator/sincronizador. El adaptador conserva `knowledge_id`, `version`, `status`, `evidence_level`, `source_path` y hash. Un `SUPERSEDES` invalida la vigencia sin borrar la version previa.

No hay red desde hooks. El cliente usa timeout, allow-list de loopback por defecto y `GRAPHITI_TELEMETRY_ENABLED=false` cuando el usuario lo elija. La sincronizacion se lanza explicitamente al cerrar la curacion o a demanda, y por categoria: una categoria sin `routing.graphiti` declarado (o `false`) nunca genera episodios (fail-closed, mismo criterio que el exportador Kwipu).

## Enmienda 2026-09-17 — Graphiti como adaptador (`ADR-018`)

```json
"backends": {
  "graphiti": {
    "type": "graphiti", "enabled": true, "mode": "shadow",
    "endpoint": "http://127.0.0.1:8000", "group_id": "<slug-estable>", "allow_remote": false,
    "telemetry": false, "timeout_ms": 3000, "concurrency": 1,
    "provider": {"llm": "ollama", "model": "qwen2.5:7b", "base_url": "http://127.0.0.1:11434",
                 "embedder": "ollama", "embedder_model": "nomic-embed-text"},
    "router": {"intents": {"temporal": true, "relacional": true, "evidencia": true}, "default": "local"},
    "relations": ["MITIGATES", "APPLIES_TO"]
  }
}
```

- **Adaptador** `skills/knowledge-services/backends/graphiti.py` implementa `health · plan · apply · verify ·
  rebuild · revoke`. `plan` traduce entradas `approved` (ya filtradas por `routing`) a episodios idempotentes con
  `knowledge_id`, `version`, `status`, `evidence_level`, `source_path`, hash; `apply` corre sobre `outbox.py`
  (claim, reintento acotado, dead-letter); `verify` compara el manifiesto del grupo con `approved/`; `rebuild`
  vacia el grupo y reproduce el manifiesto; `revoke` escribe la invalidacion (`SUPERSEDES` hacia tombstone) sin
  borrar historial.
- **Proveedor**: `provider.llm` en `ollama | openai | anthropic | none`. Con `none` el adaptador no extrae
  entidades: solo acepta episodios con estructura ya calculada (util para CI y para proyectos sin modelo local).
  Cada proveedor es una funcion pequena con la misma firma; anadir uno no toca el adaptador.
- **Modo**: `off` (registrado, inactivo) → `shadow` (sincroniza, no lee; default) → `read` (el router puede
  leer, solo si `health` sano y `verify` sin desfase). El paso a `read` lo hace el usuario en la config.
- **Router**: `knowledge-find.py --intent <x>` consulta el adaptador solo si `intents.<x>` es `true` y `mode` es
  `read`; en cualquier otro caso responde el camino local/Kwipu. No hay clasificacion por modelo.
- **Ontologia**: nucleo `Knowledge`, `Evidence`; un `entity_type` por categoria de `taxonomy.json`
  (`categories[].entity_type`, default la clave); relaciones nucleo `SUPPORTED_BY`, `SUPERSEDES`, `CONTRADICTS`
  + `relations` declaradas. El plugin no conoce `Constraint`, `Failure` ni ningun tipo de dominio.
- **Seguridad**: `allow_remote: false` limita a loopback; `telemetry: false` fija `GRAPHITI_TELEMETRY_ENABLED`;
  ninguna credencial en `taxonomy.json` (variables de entorno referenciadas por nombre).
- Se registra en `capabilities.py` (`graphiti`) para `/setup` y `/doctor` sin tocar `doctor.py`.