---
name: training-data-services
description: >
  Captura DETERMINISTA de casos (petición, contexto, trayectoria chat/SFT sin chain-of-thought,
  métricas opacas del proyecto, validación) en un case store versionado FUERA de Git y de
  `docs/knowledge/`, y ensamblado de dataset solo con casos Gold aprobados por un humano. Opt-in
  por proyecto con `.claude/knowledge-services/training.json`; sin él, cero impacto. El plugin
  valida FORMA, nunca dominio: no calcula métricas, no marca Gold solo, no entrena ni sirve
  modelos. `scripts/case_schema.py` valida `training.json` y el esquema del caso (vocabularios
  cerrados de `validation.status` y `outcome`, mapeo declarado desde `useful|dead_end|corrected`).
  Úsala cuando el usuario diga "guarda este intento como caso", "captura casos para entrenar un
  modelo local", "valida el esquema del caso", "prepara un dataset con los casos aprobados",
  "activa training-data-services", o al activar la capacidad `training` desde `/setup`.
---

# training-data-services — casos versionados y dataset Gold, sin saber nada del dominio

Algunos proyectos repiten tareas con una forma objetiva de medir el éxito y quieren conservar cada
intento para entrenar después un modelo local más barato. Esta skill da el **mecanismo genérico**:
esquema del caso, recorder determinista, puerta humana para Gold y ensamblador de dataset. Todo lo
de dominio (métricas, simulación, herramientas) es del proyecto consumidor.

> Regla central: **Gold es siempre una acción humana explícita** y **solo Gold se exporta**. El
> conocimiento aprobado nunca alimenta hacia atrás al case store (anti-leakage).

## Cuándo NO usarla

- Para curar o aprobar conocimiento (`docs/knowledge/candidates/`): eso es `knowledge-curator`. Esta
  skill, como mucho, **propone** un caso Gold como candidato (puente opt-in `bridge_to_curator`).
- Para publicar conocimiento aprobado a un backend (Kwipu): eso es `knowledge-services`.
- Para calcular una métrica, simular o evaluar semánticamente un resultado: código del proyecto.
- Para lanzar un fine-tuning, servir un modelo o correr un benchmark: siempre fuera del plugin.
- Sin `training.json` (o con `enabled: false`) no hay nada que hacer: la capacidad está apagada y
  eso es correcto, no un error.

## Piezas

| Fichero | Qué es |
|---|---|
| `scripts/case_schema.py` | Validador stdlib de `training.json` y del caso (exit 0 válido · 1 errores · 2 uso/JSON ilegible). Fuente única de los vocabularios cerrados y del mapeo de `outcome`. |
| `scripts/case-recorder.py` | Recorder (API importable + CLI `record`). Graba cada intento como versión inmutable `cases/<family>.<variant>/v<NNN>/`. La redacción la delega en `agent-kits/shared/redact.py` (fuente única); sin él se niega a grabar. Un caso `corrected` exige que exista la versión que corrige. |
| `assets/` | Plantillas del case store: `training.example.json`, ejemplo completo `case-store-example/` (caso con par fallo → corrección) y `README.md` con la estructura y cada fichero de versión (`metadata.json`, `validation.json`, `cases_index.jsonl`…). Ubicación: `docs/knowledge/adr/ADR-019-case-store-fuera-de-docs-knowledge.md`. |
| Capacidad `training` | Entrada de `agent-kits/shared/capabilities.py`: `deshabilitado` sin fichero, `error` con fichero y campo si la config es inválida, `declarado`/`ok` según exista `root`. Sin red. |

## Config opt-in — `.claude/knowledge-services/training.json`

| Clave | Obligatoria | Qué es |
|---|---|---|
| `version` | sí | `1` |
| `enabled` | no (`false`) | Activa la capacidad `training` |
| `root` | si `enabled` | Raíz del case store; la elige el proyecto (relativa a su raíz o absoluta, sin `~`); nunca dentro de `<proyecto>/docs/knowledge/` (resuelto con `realpath`, sin distinguir mayúsculas) |
| `id_prefix` | si `enabled` | Slug que prefija el `case_id`: `<id_prefix>-<family>.<variant>` |
| `ids` | no | `family_pattern` / `variant_pattern` (regex, sin puntos por defecto) · `version_width` (dígitos de `v<NNN>`, 3 por defecto) |
| `bridge_to_curator` | no (`false`) | Un caso Gold puede proponerse como candidato a `knowledge-curator` (nunca se aprueba solo) |

Cualquier otra clave se rechaza (salvo `$comment`), para que una errata no pase en silencio.

## Esquema del caso (resumen; el contrato completo vive en el docstring de `case_schema.py`)

- Obligatorios: `case_id`, `version` (entero ≥ 1), `family`, `variant`, `request` (literal),
  `trajectory` (turnos `system|user|assistant|tool` con `content`/`tool_calls`), `validation`,
  `outcome`.
- `validation.status` ∈ `pending · approved · needs_changes · rejected`; `approved` ⇔
  `approved_by_human: true`.
- `outcome` ∈ `success · failure · corrected`; `corrected` exige (y solo él admite)
  `supersedes_case: "<case_id>@v<NNN>"` en forma canónica (dígitos ASCII, relleno a `version_width`,
  ≥ 1) del mismo `case_id` y una versión anterior.
- `family`/`variant` son directorios: sin separadores, `..`, `.` (separa family y variant), `:`,
  controles, espacio final ni nombres reservados de Windows (`con`, `nul`, `com1`…), sea cual sea el patrón.
- La trayectoria **nunca** guarda chain-of-thought. Se rechaza toda clave que empiece por
  `reasoning`, `thinking`, `thought`, `chain_of_thought` o `scratchpad`, sin distinguir mayúsculas y a
  cualquier profundidad del turno (también en `arguments`).
- Excepciones y límite: `reasoning_effort`, `thinking_budget` y `reasoning_level` son parámetros de
  proveedor y se admiten **solo** dentro de `tool_calls[].arguments`. Un turno con más de 50 niveles
  de anidamiento se rechaza.
- Un tipo inesperado es un error `{campo, mensaje}`, nunca un crash.
- `metrics` es un objeto JSON opaco del proyecto; el plugin no lo interpreta.
- `context`: texto u objeto libre; admite `refs: [{"ref": "<fichero:línea|nodo>", "kind": "..."}]`
  opcional para citar procedencia (nadie está obligado a usarla).
- `artifacts`: solo referencias `{path, hash, kind}`; nunca contenido binario inline.

### Mapeo declarado de `outcome` desde fuentes externas

El vocabulario cerrado no se amplía: una fuente externa se **traduce** con `mapear_outcome(valor,
fuente)` según la tabla `OUTCOME_MAPEO`. Lo que no esté en la tabla devuelve `None` (no se inventa).

| Fuente | Valor externo | `outcome` |
|---|---|---|
| `graphify` (`save-result`) | `useful` | `success` |
| `graphify` | `dead_end` | `failure` |
| `graphify` | `corrected` | `corrected` (el caso debe declarar `supersedes_case`) |

## Proceso

1. **Activar**: el proyecto crea `training.json` con `enabled: true`, `root` e `id_prefix` (paso de
   `/setup` de la capacidad `training`).
2. **Validar** antes de escribir nada: `python3 scripts/case_schema.py config <training.json>` y
   `python3 scripts/case_schema.py case <caso.json> --config <training.json>`. `root` se resuelve
   contra la raíz deducida de `<proyecto>/.claude/knowledge-services/training.json` (o el cwd);
   `--project-root <dir>` la fija a mano. Si la ruta no se puede resolver, se rechaza.
3. **Grabar** cada intento: `python3 scripts/case-recorder.py record <caso.json>
   [--project-root <dir>]` (exit 0 ok · 1 rechazo · 2 uso/JSON ilegible). Redacta secretos, valida
   lo ya redactado y solo entonces escribe. Sin `version` toma la siguiente libre; una versión
   existente nunca se sobrescribe (reserva atómica, también en paralelo). No hay borrado.
4. **Aprobar Gold** a mano: `case-recorder.py set-status <case_id> <versión> approved
   --approved-by-human [--note …]`. Sin el flag, rechazo explícito. `needs_changes`, `rejected` y
   `pending` no lo piden. Solo se reescribe `validation.json` (atómico); lo demás es inmutable.
5. **Ensamblar** el dataset (T-07…T-09, pendiente): solo Gold, dedup por shingles, benchmark
   reservado por familia completa.

## Degradación

- Sin `training.json` o con `enabled: false`: la capacidad no existe para el ciclo (CA-01).
- `training.json` inválido: `/doctor` lo informa con fichero y campo; nada del ciclo se bloquea.
- Sin `python3`: la skill no puede validar; el resto del plugin sigue igual.

## Scripts y rutas

Rutas relativas dentro de la skill; desde fuera, `find` sobre las seis raíces de la regla 5 de
`docs/CONVENTIONS.md` (`-path '*skills/training-data-services'`). Los tests viven junto a los
scripts, solo en el repo (no viajan en el paquete portable); sin dependencias externas.
