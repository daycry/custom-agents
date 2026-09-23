# Plantillas del case store (`training-data-services`)

Plantillas y ejemplo completo del **case store**: donde el proyecto guarda cada intento
(«caso») y de donde sale el dataset. La estructura es la de `design.md` (opción O1) de la
iniciativa `2026-09-16-training-data-services`. `scripts/test_assets.py` comprueba que el
ejemplo valida con `scripts/case_schema.py` y que el índice cuadra con las versiones.

> El case store vive en el `root` que declara `training.json`, **fuera de Git y de
> `docs/knowledge/`** (ADR-019). Esta carpeta es solo el ejemplo que viaja con el plugin.

## Estructura

```text
<root>/                                  # training.json -> root (lo elige el proyecto)
├── cases_index.jsonl                    # índice append-only (caché: se reconstruye desde cases/)
├── cases/<family>.<variant>/            # un directorio por caso; case_id = <id_prefix>-<family>.<variant>
│   └── v<NNN>/                          # una versión por intento; NUNCA se sobrescribe
│       ├── metadata.json
│       ├── request.json
│       ├── context.json
│       ├── constraints.json
│       ├── trajectory.jsonl
│       ├── metrics.json
│       ├── validation.json
│       └── final/artifacts.json         # solo referencias a los artefactos finales
└── exports/<export_id>/                 # lo escribe el ensamblador (T-08/T-09), nunca a mano
    ├── manifest.json
    ├── train.jsonl
    └── benchmark.jsonl
```

`v<NNN>` usa `ids.version_width` dígitos (3 por defecto). El ejemplo de esta carpeta
(`case-store-example/`) trae un caso con dos versiones: `v001` falla (`outcome: failure`, rechazada
y **conservada**) y `v002` la corrige (`outcome: corrected`, `supersedes_case` apuntando a `v001`,
aprobada como Gold por un humano).

## `training.json` (config del proyecto)

Plantilla: `training.example.json` → cópiala a `.claude/knowledge-services/training.json`. Claves y
reglas: tabla de la skill (`SKILL.md`) y docstring de `scripts/case_schema.py`.

## Ficheros de cada versión

| Fichero | Contenido | Quién lo define |
|---|---|---|
| `metadata.json` | `case_id`, `family`, `variant`, `version` (entero ≥ 1), `created_at` (ISO-8601), `outcome` (`success`·`failure`·`corrected`) y, si `corrected`, `supersedes_case: "<case_id>@v<NNN>"` | Plugin (forma cerrada) |
| `request.json` | `{"request": ...}`: la petición **literal**, sin normalizar (texto u objeto) | Proyecto (contenido) |
| `context.json` | Contexto normalizado, esquema libre; opcional `refs: [{"ref": "<fichero:línea\|nodo>", "kind": "..."}]` para citar procedencia | Proyecto |
| `constraints.json` | Restricciones del intento, esquema libre | Proyecto |
| `trajectory.jsonl` | Un turno por línea: `role` (`system`·`user`·`assistant`·`tool`), `content`, `tool_calls` (`[{name, arguments}]`, solo `assistant`), `name` (en `tool`), `ts`. **Nunca** chain-of-thought | Plugin (forma) / proyecto (turnos) |
| `metrics.json` | Objeto JSON **ya calculado** por el proyecto; opaco para el plugin | Proyecto |
| `validation.json` | `status` (`pending`·`approved`·`needs_changes`·`rejected`), `approved_by_human` (`true` solo con `approved`), `approved_at`, `reviewer_note` | Plugin (forma) / humano (Gold) |
| `final/artifacts.json` | Lista de `{path, hash: "<algoritmo>:<hex>", kind}`; nunca contenido binario inline | Proyecto |

`request.json`, `context.json` y `trajectory.jsonl` pasan por la redacción de secretos compartida
(`agent-kits/shared/redact.py`) **antes** de escribirse (el recorder, T-04).

### Ejemplo de `metadata.json` (versión corregida)

```json
{"case_id": "geo-ramp.steep", "family": "ramp", "variant": "steep", "version": 2,
 "created_at": "2026-09-23T10:10:00Z", "outcome": "corrected", "supersedes_case": "geo-ramp.steep@v001"}
```

### Ejemplo de `validation.json` (Gold)

```json
{"status": "approved", "approved_by_human": true, "approved_at": "2026-09-23T10:20:00Z",
 "reviewer_note": "Correccion del fallo de v001 (anchura). Gold."}
```

## `cases_index.jsonl`

Una línea por **cambio** (alta de versión o cambio de estado), nunca se reescribe: para cada
`(case_id, version)` vale la última línea. Claves exactas: `case_id`, `version`, `family`,
`variant`, `status`, `outcome`, `updated_at`. Es una **caché**: si se corrompe, se reconstruye
recorriendo `cases/` (T-06).

```json
{"case_id": "geo-ramp.steep", "version": 1, "family": "ramp", "variant": "steep", "status": "pending", "outcome": "failure", "updated_at": "2026-09-23T10:00:08Z"}
{"case_id": "geo-ramp.steep", "version": 1, "family": "ramp", "variant": "steep", "status": "rejected", "outcome": "failure", "updated_at": "2026-09-23T10:05:00Z"}
```

## `exports/`

Lo escribe el ensamblador (T-07…T-09): `manifest.json` (qué `case_id@version` entraron, hash de
cada uno, asignación train/benchmark por familia completa), `train.jsonl` y `benchmark.jsonl` en
formato chat (`messages`). Solo casos `approved` con `approved_by_human: true`.
