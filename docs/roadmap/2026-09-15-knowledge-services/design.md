---
design: knowledge-services
estado: aprobado
opcion_elegida: O1
spec: spec.md
evaluation: evaluation.md
plan: improvement-plan.md
---

# Diseno - Knowledge Gate y Kwipu

| Opcion | Decision |
|---|---|
| O1 | Markdown canonico + Curator + export Kwipu derivado, taxonomia/enrutado configurables por proyecto. **Elegida.** |
| O2 | Kwipu como almacen primario. Descartada: no hay curacion ni revision Git. |
| O3 | Graphiti primero. Descartada: aumenta operacion y no resuelve primero la documentacion. |
| O4 | Taxonomia de categorias fija en el plugin (una lista Python compartida por todo consumidor). Descartada: el plugin es base de proyectos con dominios distintos (ver ejemplo Marble Run); una lista fija obliga a tocar codigo del plugin para adaptar categorias a cada dominio. |

## Configuracion por proyecto: `.claude/knowledge-services/taxonomy.json`

El plugin **no** declara una taxonomia propia de categorias de conocimiento. Declara el MECANISMO (Gate, Curator, esquema, exportador) y cada proyecto declara SU taxonomia en un fichero de configuracion versionado en el propio proyecto:

```json
{
  "version": 1,
  "id_prefix": "mr",
  "utility_scoring": false,
  "categories": [
    {"key": "PATTERN", "folder": "patterns", "min_evidence": "multiple_validated_cases",
     "routing": {"kwipu": true, "graphiti": true}},
    {"key": "CONSTRAINT", "folder": "constraints", "min_evidence": "human_confirmed_rule",
     "routing": {"kwipu": true, "graphiti": true}},
    {"key": "FAILURE", "folder": "failures", "min_evidence": "observation",
     "routing": {"kwipu": false, "graphiti": true}},
    {"key": "CORRECTION", "folder": "corrections", "min_evidence": "validated_case",
     "routing": {"kwipu": "summary", "graphiti": true}}
  ]
}
```

- **`categories`** sustituye la lista fija: clave, carpeta bajo `approved/`, evidencia minima exigida y enrutado de destino (`kwipu`/`graphiti`: `true` | `false` | `"summary"`).
- **Sin `taxonomy.json`**, el plugin usa un default MINIMO propio, alineado con lo que `docs/knowledge/` ya usa hoy (`DECISION` -> `adr/`, `PATTERN`/`GOTCHA` -> `gotchas/`, `LESSON` -> `lessons/`), para que custom-agents siga funcionando sin configurar nada.
- **Una categoria sin `routing` declarado no exporta a ningun backend** (fail-closed): evita que una categoria nueva se filtre a Kwipu/Graphiti por omision.
- **`id_prefix`** es el prefijo de `knowledge_id` del proyecto (p. ej. `mr.pattern.fast-curve-derailment` para Marble Run); sin `taxonomy.json`, el prefijo default es el slug del propio directorio del proyecto.
- **`utility_scoring`** (opt-in, default `false`): si es `true`, el candidato lleva un desglose 0-10 (relevancia/reutilizacion/evidencia/novedad, 0-2 cada uno) que el Curator puede usar SOLO para ordenar la cola de revision. El validador y el Curator **nunca** cambian un estado (`approved`/`rejected`) por el valor de `utility`; es puramente informativo. Sin este campo activo, el ciclo es cualitativo: `pending -> approved | needs_changes | rejected` por evidencia y categoria.
- **Lista negra de memoria activa (default del plugin, ampliable en `taxonomy.json` -> `"denylist"`)**: chain-of-thought, conversacion cruda, TODOs, planes/progreso, logs completos, salidas enormes, codigo duplicado, errores triviales, intentos sin aprendizaje, hipotesis como hechos, opiniones, redundancias. Nunca se convierten en candidato.

## Modelo

```text
docs/knowledge/{candidates/{pending,needs_changes,rejected},approved/<categorias de taxonomy.json>}
  -> schema/index validator (lee taxonomy.json) -> kwipu exporter (respeta routing.kwipu) -> .claude/knowledge-services/kwipu-export
```

`approved/` es versionado y canonico; sus subcarpetas nacen de `taxonomy.json`, no de una constante del plugin. El export contiene Markdown autocontenido, enlaces, frontmatter y `manifest.json`; se publica desde staging de forma atomica y se puede borrar. Kwipu indexa solo ese directorio, y solo las categorias con `routing.kwipu` distinto de `false`.

`documenter` retorna propuestas con categoria (validada contra `taxonomy.json`), fuentes y evidencia. `knowledge-curator` es el unico escritor de candidatos y aprobados; contradicciones, cambios de taxonomia y reglas de alto impacto requieren confirmacion humana. Los hooks no hacen red.

## Convivencia con datasets propios de proyecto

Fuera de alcance de esta iniciativa (se trata aparte): un proyecto puede mantener su propio dataset (p. ej. `training_data/` de un pipeline de entrenamiento) en cualquier ruta fuera de `docs/knowledge/`; el plugin no lo lee, no lo valida ni lo exporta.