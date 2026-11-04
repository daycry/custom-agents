# Fuentes y comprobaciones documentales

Consulta: 2026-11-04. Los enlaces oficiales aparecen junto a las afirmaciones correspondientes del manual. Las recomendaciones y ejemplos propios no son garantías de los proveedores. No se han lanzado sesiones de modelo de pago ni inspeccionado conversaciones privadas.

| Fuente primaria | Afirmación comprobada |
|---|---|
| [Claude pricing](https://claude.com/pricing) | Pro mensual 20 USD, Claude Code incluido y condiciones de precios |
| [Límites de Claude](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work) | Cuota temporal distinta de longitud; uso compartido entre superficies |
| [Buenas prácticas de uso de Claude](https://support.claude.com/en/articles/9797557-usage-limit-best-practices) | Contexto, archivos, herramientas y modelo influyen en consumo |
| [Costes de Claude Code](https://code.claude.com/docs/en/costs) | `/usage`, `/context`, `/mcp`, `/compact`, `/clear`; diferencia entre estimación de sesión y facturación |
| [Modelo y esfuerzo de Claude Code](https://code.claude.com/docs/en/model-config) | `/model`, `/effort` y posibles overrides de skills/subagentes |
| [Memoria de Claude Code](https://code.claude.com/docs/en/memory) | Instrucciones persistentes de proyecto |
| [Skills de Claude Code](https://code.claude.com/docs/en/skills) | Descubrimiento y carga del contenido según invocación |
| [Planes y uso de Codex](https://learn.chatgpt.com/docs/pricing) | Plus mensual 20 USD; API separada; cuota variable; modo acelerado |
| [Comandos de Codex](https://learn.chatgpt.com/docs/developer-commands?surface=cli) | Comandos CLI, `/model --reasoning=high`, estado, compactación, fork y toggle Fast |
| [Selección de modelo de Codex](https://learn.chatgpt.com/docs/model-selection) | Elección según dificultad, capacidad y eficiencia |

## Fuentes canónicas del plugin

- `commands/pm-cycle.md`: termina en spec/evaluación; diseño y salidas extra opt-in; no planifica ni implementa.
- `commands/dev-cycle.md`, `skills/quick-implement/SKILL.md`: recorridos de desarrollo y puertas.
- `commands/setup.md`: perfil lite, preferencias conservadas y límites efectivos.
- `docs/INTEROP.md`, `agent-kits/shared/native-roles.json`: invocaciones y roles por runtime.
- `skills/api-contract/SKILL.md`: valida/compara specs; pruebas de respuesta pertenecen a QA/pipeline.
- `skills/adversarial-review/SKILL.md`: lentes independientes y selección condicional C/D.
- `docs/guides/atlassian.md`, `redmine.md`, `memory.md`, `knowledge-categories.md`, `customization.md`: integraciones y personalización.
- `docs/roadmap/2026-11-04-token-efficiency/testing/token-estimates.md`: escenario y aritmética estimada, no facturación real.

## Regresiones de documentación

**DOC-B1:** comprobar que la columna Codex CLI recomienda el selector `/model` y su opción documentada `--reasoning`. La lista `/reasoning` al final de la página oficial puede pertenecer a otra superficie; no se usa como receta CLI. Test dedicado: `test_B1_codex_cli_effort_uses_documented_model_command`.

**DOC-B2:** comprobar que la tabla atribuye a `api-contract` validación y comparación de specs. Una respuesta incompatible puede existir con una spec válida; la skill no prueba automáticamente esa respuesta. Test dedicado: `test_B2_api_contract_is_not_presented_as_response_validation`.

RED observado restaurando únicamente las dos afirmaciones originales revisadas: `python -m pytest tests/test_user_handbooks.py -q --tb=short` → 2 failed. Tras restaurar los textos corregidos: 2 passed. No se altera el runtime para corregir documentación. Los tests preservan estos dos casos conocidos; no certifican semánticamente todo el manual ni hacen peticiones de red.
