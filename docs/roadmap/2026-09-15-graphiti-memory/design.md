---
design: graphiti-memory
estado: aprobado
opcion_elegida: O1
---

# Diseno - proyeccion Graphiti derivada

**O1 elegida:** `approved/` es la fuente, un sincronizador genera episodios idempotentes SOLO para las categorias cuyo `routing.graphiti` (en `.claude/knowledge-services/taxonomy.json`, definido por `knowledge-services`) sea `true`, y un router consulta Graphiti solo ante relaciones, evidencia o tiempo. **O2 descartada:** guardar memoria de cada turno, por ruido, privacidad e inyeccion. **O3 descartada:** hacer que Graphiti sea el almacen primario. **O4 descartada:** sincronizar TODO `approved/` sin distincion por categoria — el plugin es base de proyectos con dominios distintos y no todos quieren relaciones temporales para todas sus categorias (p. ej. un `TOOL` documentado no necesita grafo).

Cada instalacion configura un `group_id` estable bajo `.claude/knowledge-services/`; nunca acepta uno libre desde el prompt. Las escrituras pasan por Curator/sincronizador. El adaptador conserva `knowledge_id`, `version`, `status`, `evidence_level`, `source_path` y hash. Un `SUPERSEDES` invalida la vigencia sin borrar la version previa.

No hay red desde hooks. El cliente usa timeout, allow-list de loopback por defecto y `GRAPHITI_TELEMETRY_ENABLED=false` cuando el usuario lo elija. La sincronizacion se lanza explicitamente al cerrar la curacion o a demanda, y por categoria: una categoria sin `routing.graphiti` declarado (o `false`) nunca genera episodios (fail-closed, mismo criterio que el exportador Kwipu).