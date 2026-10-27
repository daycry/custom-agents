---
verificacion: obligatoria
---

# Correcciones del inventario OpenCode V2

| | |
|---|---|
| **Estado** | en-revision |
| **Origen** | Errores reproducidos y patch revisado en esta conversación; usuario: habría que solucionar estos errores. |

Ledger canónico. No modifica workers, configuración global, el patch externo ni los timeouts de hooks.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---:|---:|---:|
| Fase 1 — Corrección del lector | 1 | 1 | 100% |

## Fase 1 — Compatibilidad y regresiones

### T-01 — Corregir el descubrimiento OpenCode V1/V2

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Descubrir MCP V2 anidados y disabled, conservar overrides V1 y fuentes coexistentes, excluir opciones timeout; descubrir agents/commands V2 e ignorar carpetas auxiliares sin SKILL.md. Preservar privacidad, fuentes, conflictos y avisos de declaraciones realmente inválidas.
- **Archivos**: `agent-kits/shared/project-pieces.py`, `tests/test_project_pieces.py`, `docs/PROJECT-EXTENSIONS.md`, `docs/en/PROJECT-EXTENSIONS.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-10-27-opencode-reader-fixes/testing/**`
- **Changelog**: Corrige el inventario OpenCode V2 y sus avisos, conservando las declaraciones V1 y la privacidad de las configuraciones.
- **Verificación**: `python -m pytest -q tests/test_project_pieces.py`; cobertura directa del lector con Coverage.py ≥ 90 %; `python scripts/lint_plugin.py`; `python scripts/export-interop.py --check`; `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-27-opencode-reader-fixes/tasks.md`.

**Criterios de aceptación**

- [x] MCP V2 y estados disabled booleanos se inventarían sin exportar endpoints ni secretos.
- [x] El override V1 `servers: {enabled: false}` y los hermanos/agentes inline se conservan; timeout global sin servers no inventa un MCP.
- [x] V1/V2 coexistentes conservan ambas fuentes y conflictos sin inventar precedencia nativa.
- [x] Se descubren agents/commands V2 y siguen funcionando las claves V1.
- [x] Los auxiliares sin SKILL.md no generan falsos parciales; las declaraciones inválidas y enlaces siguen avisando.
- [x] Tests de regresión, cobertura y documentos ES/EN verificados.

**Evidencia**

- RED 2026-10-27: `python -m pytest -q tests/test_project_pieces.py -k "v2_nested_mcp or v2_timeout_only or v2_agents_and_commands or auxiliary_skill or flat_skill" --tb=short` → **11 fallos, 121 deseleccionados**, todos por aserciones de comportamiento (sin errores de importación/fixture).
- V1 enabled-only y las declaraciones válidas existentes son controles de caracterización: deben conservar su verde.
- Revisión secuencial, sin subagentes: `.claude/dev.json` declara `subagentes: false`.
- Los cambios previos de benchmark y su roadmap no pertenecen a esta corrección.

- RED adicional 2026-10-27: `test_opencode_invalid_v1_timeout_override_is_not_silently_ignored` → 3 fallos por `partial: false`. La revisión propia detectó que un flag inválido en un servidor V1 llamado timeout se ocultaba; ahora se envía a validación, conservando los servidores V2 llamados enabled/url.

- RED adicional: enabled de tipo objeto en el override timeout → 1 fallo y 3 controles verdes. Se rechaza también ese flag malformado; no se aplica ese rechazo a un servidor V2 llamado enabled.

- GREEN final: **138 passed, 1 skipped** (privilegios de symlink), 29,60 s. Coverage.py: **92,307692 %**, 684/741 sentencias; gate `--fail-under=90` en verde.
- Callers: 8 pruebas de extensiones/briefs y seguridad de declaraciones; 2 pruebas de CLI y privacidad del catálogo, todas en verde.
- `lint_plugin.py`: 0 errores, 3 avisos existentes de nombres genéricos. `export-interop.py --check`: 88 ficheros al día. `git diff --check`: exit 0.
- Revisión propia secuencial A/B: criterios verificados; se corrigió el gap de enabled inválido con sus rojos dedicados. No se declara revisión independiente.
- Patch autocontenido: `testing/opencode-reader-fixes.patch`, solo los seis ficheros de la corrección; no incluye el benchmark. `git apply --check` contra copia limpia de HEAD: exit 0.
- No se ha actualizado la caché instalada ni publicado release. Notificaciones Codex, WorkerRecovery y la línea base pendiente de optimización mantienen sus estados previos.
