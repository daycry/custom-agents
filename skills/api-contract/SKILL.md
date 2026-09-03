---
name: api-contract
description: >
  Flujo CONTRACT-FIRST para APIs con `scripts/openapi-lint.py` (SIN dependencias externas): valida
  la estructura MÍNIMA de una spec OpenAPI 3.x (versión 3.x, `paths` no vacío, `operationId`
  único, `responses` con 2xx y 4xx/5xx, `$ref` internos resueltos, parámetros con schema/content) y,
  con `--diff <old> <new>`, detecta cambios ROMPEDORES — path u operación eliminada, parámetro
  obligatorio nuevo, campo de respuesta eliminado, tipo cambiado, enum que pierde valores — frente a
  cambios compatibles informativos (path o campo opcional nuevo). Regla: el CONTRATO manda, el
  código se adapta. `planner` abre tareas de contrato cuando la spec toca una API; la Lente A de
  `adversarial-review` ejecuta `--diff` si el diff toca la spec. Sugiere plantillas de tests de
  contrato por stack (schemathesis, dredd, prism) sin instalarlas. NO documenta la API para humanos
  (`documenter`) ni audita su seguridad (`nemesis`). Úsala cuando el usuario diga "valida este
  OpenAPI", "¿esta spec es válida?", "¿qué cambios rompen el contrato de la API?", "compara estas
  dos versiones del OpenAPI", o antes de implementar un endpoint con spec.
---

# api-contract — el contrato manda; el código se adapta

Resolución de rutas (regla 5 de CONVENTIONS — nunca rutas fijas):
```bash
SKILL="$(find "$PWD/.claude" "$PWD/skills" "$HOME/.claude" -type d -path '*skills/api-contract' 2>/dev/null | head -1)"
```

## Cuándo NO usarla

- Para documentar la API para humanos o consumidores externos (guías, ejemplos de uso): eso es `documenter`.
- Para auditar la seguridad de la API (auth, rate limiting, OWASP API Security Top 10): eso es `nemesis` con la skill `cybersecurity`. Esta skill solo mira la ESTRUCTURA del contrato.
- Para ejecutar tests de contrato de verdad contra un servidor real (`schemathesis run`, `dredd`): la skill ofrece la PLANTILLA (más abajo); ejecutarla contra un entorno vivo es cosa de `qa` o del propio pipeline del proyecto.
- Sobre una API sin spec OpenAPI (GraphQL, gRPC, RPC ad-hoc): fuera de alcance; si no existe spec, sugiere escribirla primero — no se puede validar un contrato que no está escrito.

## Flujo contract-first

1. **La spec nace ANTES que el código.** Un endpoint nuevo o modificado empieza por la spec OpenAPI (si hay `architect`, su `design.md` referencia la spec; si no, quien implemente la escribe primero).
2. **Valida la spec** con `openapi-lint.py` antes de implementar — un `operationId` que falta o una `responses` sin 4xx se detectan en segundos, no en la revisión.
3. **Implementa contra la spec validada.** El código se adapta al contrato, nunca al revés: si el código necesita algo que la spec no dice, se cambia la spec primero (y se vuelve a validar), no se improvisa en el handler.
4. **`--diff` antes de tocar una spec existente.** Compara la versión base con la propuesta: un cambio ROMPEDOR sin versionar la API (`/v2/...`) o sin avisar a los consumidores es un gap, no un detalle de implementación.
5. **Tests de contrato como plantilla** (sección de abajo) — verifican que la IMPLEMENTACIÓN cumple lo que la spec promete; no sustituyen al linter (estructura) ni a `qa` (comportamiento end-to-end).

## Uso del script

```bash
python3 "$SKILL/scripts/openapi-lint.py" <spec.yaml|json> [--json]           # validar
python3 "$SKILL/scripts/openapi-lint.py" --diff <old.yaml> <new.yaml> [--json]  # cambios rompedores
```

- **Sin dependencias externas.** JSON con la stdlib; YAML con `yaml` (PyYAML) si el proyecto lo
  tiene instalado, y si no, un parser YAML mínimo propio para el subconjunto habitual de las specs
  (mapas y listas por indentación, escalares, cadenas entrecomilladas, colecciones `[...]`/`{...}`,
  `$ref`). YAML fuera de ese subconjunto (bloques `|`/`>`, anclas, multi-documento) → **exit 2** con
  el aviso «instala PyYAML para specs más complejas» — nunca intenta adivinar.
- **Validación** (un fichero): `openapi: 3.x` presente; `paths` no vacío; cada operación
  (get/put/post/delete/options/head/patch/trace) con `operationId` ÚNICO en todo el documento;
  `responses` con al menos una 2xx y una 4xx/5xx; cada `$ref` interno (`#/components/...`) resuelve
  dentro del propio documento (las referencias a ficheros externos se ignoran, no son error);
  parámetros con `schema` o `content`. Aviso, no error: `requestBody` de tipo `object` sin
  `additionalProperties: false` (informativo — no toda API necesita cerrar el esquema).
- **`--diff old new`** (cambios rompedores): path eliminado, operación (método) eliminada de un
  path que sigue existiendo, parámetro eliminado, parámetro obligatorio nuevo o que pasa de
  opcional a obligatorio, campo de una respuesta 2xx (`application/json`) eliminado, tipo (`type`)
  distinto en un parámetro o un campo de respuesta, `enum` que pierde valores. Informativos, NO
  bloquean: path nuevo, parámetro opcional nuevo, campo de respuesta nuevo.
- **Exit 0** spec válida / diff sin rompedores · **1** errores encontrados / diff con rompedores ·
  **2** fichero ilegible, extensión no soportada, o uso incorrecto. Salida MD legible o `--json`
  (mismos datos); cada hallazgo lleva una `ruta` estilo JSON-pointer (`/paths/~1pets/get/...`) para
  saltar directo al punto de la spec. El contrato exacto son las funciones `validar`/`diff_specs`
  del script, con sus tests (`pytest -q skills/api-contract/scripts`).

## Integración con la cadena

- **`planner`** (P3, Descomposición): cuando el alcance crea o cambia endpoints con spec OpenAPI,
  añade una tarea de verificación de contrato con `Verificación` = ejecutar `openapi-lint.py` (y
  `--diff` contra la versión previa si ya existía) — antes de implementar, no como gap que encuentre
  la revisión.
- **Lente A de `adversarial-review`** (`references/lens-prompts.md`): si el diff toca una spec
  OpenAPI, ejecuta `--diff` contra la versión en la base de la revisión; un cambio ROMPEDOR que el
  plan no justifica es gap Important.
- Ninguna integración es obligatoria: sin spec OpenAPI en el proyecto, ninguna de las dos se activa.

## Plantillas de tests de contrato (sugerencia, NO se instalan)

La skill NO instala nada por su cuenta — son plantillas para copiar y adaptar, detalladas en
`references/contract-tests.md`: **`pytest` + `schemathesis`** (Python; genera casos desde la spec y
los ejecuta contra un servidor real o un `TestClient`), **`dredd`** (Node; contratos declarativos
por endpoint contra ejemplos de la spec), **`prism`** (Node; mock server desde la spec + modo
`proxy` que valida request/response reales contra el contrato). Elige UNA según el stack del
proyecto; instalarla y engancharla al CI es decisión del equipo, no de esta skill.

## Qué NO hace

- No implementa el endpoint ni corrige la spec por su cuenta: reporta errores/cambios; corrige quien
  pidió la validación.
- No ejecuta tests de contrato contra un servidor real (eso son las plantillas de arriba, a mano o
  vía `qa`) ni sustituye los tests E2E de `qa-gate.py`.
- No documenta la API para humanos (`documenter`) ni valida seguridad (`nemesis`/`cybersecurity`).
- No resuelve `$ref` a ficheros externos (`otro-fichero.yaml#/...`): solo referencias internas al
  propio documento (`#/components/...`).
- No es un parser YAML de propósito general: fuera del subconjunto habitual de una spec OpenAPI
  (bloques `|`/`>`, anclas `&`/`*`, multi-documento), degrada a exit 2 en vez de arriesgar un parseo
  incorrecto — instala PyYAML para esos casos.

## Degradación

Sin PyYAML instalado, el parser propio cubre el subconjunto habitual de las specs (ver arriba); si
la spec usa algo fuera de ese subconjunto, exit 2 con el aviso «instala PyYAML», nunca inventa una
estructura. Sin `api-contract` instalada, `planner` no abre tareas de contrato y la Lente A omite su
criterio adicional (lo dice en la salida) — ninguna de las dos cadenas se bloquea por su ausencia.

## Referencias

| Fichero | Cuándo leerlo |
|---|---|
| `scripts/openapi-lint.py` | Nunca hace falta leerlo para usar la skill — el contrato son sus funciones + tests. Ábrelo solo para extender la validación o el diff. |
| `references/contract-tests.md` | Al elegir o adaptar una plantilla de tests de contrato para el stack del proyecto. |
