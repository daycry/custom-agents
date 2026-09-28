# Esquema del caso y mapeo de `outcome` (training-data-services)

> Lee esto solo al llegar al paso 2 de `SKILL.md` («Validar») o al preparar un caso a mano. El
> contrato completo y ejecutable vive en el docstring de `scripts/case_schema.py`.

## Esquema del caso (resumen; el contrato completo vive en el docstring de `case_schema.py`)

- Obligatorios: `case_id`, `version` (entero ≥ 1), `family`, `variant`, `request` (literal),
  `trajectory` (turnos `system|user|assistant|tool` con `content`/`tool_calls`), `validation`,
  `outcome`. Para `record`, `version`, `case_id` y `validation` son opcionales: se asignan la
  siguiente versión libre, `<id_prefix>-<family>.<variant>` y `pending`.
- `validation.status` ∈ `pending · approved · needs_changes · rejected` (`approved` ⇔
  `approved_by_human: true`); `outcome` ∈ `success · failure · corrected`; `corrected` exige (y solo él admite)
  `supersedes_case: "<case_id>@v<NNN>"` en forma canónica (dígitos ASCII, relleno a `version_width`,
  ≥ 1) del mismo `case_id` y una versión anterior.
- `family`/`variant` son directorios: sin separadores, `..`, `.` (separa family y variant), `:`,
  controles, espacio final ni nombres reservados de Windows (`con`, `nul`, `com1`…), sea cual sea el patrón.
- La trayectoria **nunca** guarda chain-of-thought: se rechaza toda clave que empiece por `reasoning`,
  `thinking`, `thought`, `chain_of_thought` o `scratchpad` (sin distinguir mayúsculas, a cualquier
  profundidad del turno, también en `arguments`).
- Excepciones y límite: `reasoning_effort`, `thinking_budget` y `reasoning_level` son parámetros de
  proveedor y se admiten **solo** dentro de `tool_calls[].arguments`. Un turno con más de 50 niveles
  de anidamiento se rechaza.
- Un tipo inesperado es un error `{campo, mensaje}`, nunca un crash. `metrics` es un objeto JSON
  opaco del proyecto (el plugin no lo interpreta); `artifacts`, solo referencias `{path, hash, kind}`.
- `context`: texto u objeto libre; admite `refs: [{"ref": "<fichero:línea|nodo>", "kind": "..."}]`
  opcional para citar procedencia (nadie está obligado a usarla).

## Mapeo declarado de `outcome` desde fuentes externas

El vocabulario cerrado no se amplía: una fuente externa se **traduce** con `mapear_outcome(valor,
fuente)` (`OUTCOME_MAPEO`); lo que no esté en la tabla devuelve `None` (no se inventa).

| Fuente | Valor externo | `outcome` |
|---|---|---|
| `graphify` (`save-result`) | `useful` | `success` |
| `graphify` | `dead_end` | `failure` |
| `graphify` | `corrected` | `corrected` (el caso debe declarar `supersedes_case`) |
