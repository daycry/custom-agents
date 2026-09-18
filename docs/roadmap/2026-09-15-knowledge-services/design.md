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
  ],
  "backends": {
    "kwipu":    {"type": "markdown-export", "enabled": true,
                 "config": {"export_dir": ".claude/knowledge-services/kwipu-export",
                            "health": {"url": "http://127.0.0.1:8765/health", "timeout_ms": 800}}},
    "graphiti": {"type": "graphiti", "enabled": false,
                 "config": {"mode": "shadow", "endpoint": "http://127.0.0.1:8001/mcp", "group_id": "mr-local",
                            "provider": {"llm": "ollama", "model": "qwen2.5:7b", "embedder": "ollama", "embedder_model": "nomic-embed-text"}}}
  }
}
```

- **`backends`** (enmienda 2026-09-17, `ADR-018`): cada destino se declara con `id` (la clave), `type` (el adaptador
  que lo implementa) y su configuracion. `routing` solo puede citar ids declarados aqui; un id desconocido es
  error de validacion y la categoria no exporta (fail-closed, CA-11). Sin `backends`, el default del plugin
  declara solo `kwipu` desactivado. La configuracion de `graphiti` la define `graphiti-memory`; aqui solo se
  muestra la forma.

- **`categories`** sustituye la lista fija: clave, carpeta bajo `approved/`, evidencia minima exigida y enrutado de destino (`kwipu`/`graphiti`: `true` | `false` | `"summary"`).
- **Sin `taxonomy.json`**, el plugin usa un default MINIMO propio, alineado con lo que `docs/knowledge/` ya usa hoy (`DECISION` -> `adr/`, `PATTERN`/`GOTCHA` -> `gotchas/`, `LESSON` -> `lessons/`), para que custom-agents siga funcionando sin configurar nada.
- **Una categoria sin `routing` declarado no exporta a ningun backend** (fail-closed): evita que una categoria nueva se filtre a Kwipu/Graphiti por omision.
- **`id_prefix`** es el prefijo de `knowledge_id` del proyecto (p. ej. `mr.pattern.fast-curve-derailment` para Marble Run); sin `taxonomy.json`, el prefijo default es el slug del propio directorio del proyecto.
- **`utility_scoring`** (opt-in, default `false`): si es `true`, el candidato lleva un desglose 0-10 (relevancia/reutilizacion/evidencia/novedad, 0-2 cada uno) que el Curator puede usar SOLO para ordenar la cola de revision. El validador y el Curator **nunca** cambian un estado (`approved`/`rejected`) por el valor de `utility`; es puramente informativo. Sin este campo activo, el ciclo es cualitativo: `pending -> approved | needs_changes | rejected` por evidencia y categoria.
- **Lista negra de memoria activa (default del plugin, ampliable en `taxonomy.json` -> `"denylist"`)**: chain-of-thought, conversacion cruda, TODOs, planes/progreso, logs completos, salidas enormes, codigo duplicado, errores triviales, intentos sin aprendizaje, hipotesis como hechos, opiniones, redundancias. Nunca se convierten en candidato.

## Modelo

```text
docs/knowledge/{candidates/{pending,needs_changes,rejected},approved/<categorias de taxonomy.json>}
  -> schema/index validator (taxonomy.schema.json, lee taxonomy.json)
  -> knowledge-sync.py --backend <id>  ->  backends/<type>.py (plan -> outbox.py staging -> apply -> verify)
       kwipu (markdown-export)  -> .claude/knowledge-services/kwipu-export + manifest.json
       graphiti (graphiti)      -> episodios (graphiti-memory, iniciativa aparte)
       <type nuevo>             -> un fichero de adaptador + una entrada en `backends`; el nucleo no cambia
```

### Contrato de adaptador (`skills/knowledge-services/backends/<type>.py`)

| Funcion | Que hace | Obligatoria |
|---|---|---|
| `health(cfg) -> {estado, detalle}` | salud/desfase sin efectos; `estado` en `off · sano · degradado · error` | si |
| `plan(entries, cfg) -> ops` | calcula operaciones idempotentes a partir de las entradas `approved` YA filtradas por `routing` | si |
| `apply(ops, cfg) -> result` | ejecuta sobre un staging de `outbox.py`; publica de forma atomica | si |
| `verify(cfg) -> {ok, desfase}` | compara manifiesto vs fuente | si |
| `rebuild(cfg)` | reconstruye la proyeccion entera desde `approved/` | si |
| `revoke(knowledge_id, cfg)` | invalida/tombstone una entrada retirada de `approved/` | si (puede ser no-op declarado) |

`knowledge-sync.py` carga el adaptador por `type`, aplica `routing` **antes** de llamar a `plan` (el adaptador
nunca ve una entrada no enrutada), registra cada corrida en `outbox.py` y expone `--dry-run`, `--check` y
`--rebuild`. Un adaptador `type: "test"` en fixtures demuestra que anadir un backend no toca el nucleo (CA-12).

### Registro de capacidades (`agent-kits/shared/capabilities.py`)

Cada capacidad opcional declara `{id, config_path, enabled(root), health(root), doctor(root), setup_step}`.
`/doctor` y `/setup` iteran el registro: esta iniciativa registra `knowledge-gate` y `kwipu`; `graphiti-memory`
y `training-data-services` anaden las suyas sin tocar `doctor.py` (CA-14).

`approved/` es versionado y canonico; sus subcarpetas nacen de `taxonomy.json`, no de una constante del plugin. El export contiene Markdown autocontenido, enlaces, frontmatter y `manifest.json`; se publica desde staging de forma atomica y se puede borrar. Kwipu indexa solo ese directorio, y solo las categorias con `routing.kwipu` distinto de `false`.

`documenter` retorna propuestas con categoria (validada contra `taxonomy.json`), fuentes y evidencia. `knowledge-curator` es el unico escritor de candidatos y aprobados; contradicciones, cambios de taxonomia y reglas de alto impacto requieren confirmacion humana. Los hooks no hacen red.

## Convivencia con datasets propios de proyecto

Fuera de alcance de esta iniciativa (se trata aparte): un proyecto puede mantener su propio dataset (p. ej. `training_data/` de un pipeline de entrenamiento) en cualquier ruta fuera de `docs/knowledge/`; el plugin no lo lee, no lo valida ni lo exporta.

> **Nota 2026-09-18 (revisión de la Fase 2, gap 55).** La línea «`documenter` retorna propuestas con categoría (validada contra `taxonomy.json`)» queda matizada por la implementación de T-05: `documenter` propone la categoría como mejor estimación y NO la valida (sin puerta mecánica, arista E13 de `CONTRACTS.md`); la validación contra la taxonomía la hace `curator-gate.py` cuando `knowledge-curator` decide. Un rol, un dueño (ADR-011): el buzón no valida, el curador sí.

> **Nota 2026-09-18 (revisión de la Fase 2, gap 41).** Lista negra por defecto: `TODO:` (marcador) en vez de `TODOs`; coincidencia por frontera de palabra sobre el cuerpo, no por subcadena.
