# Selección común de capacidades

Antes de diseñar, planificar, implementar, revisar o probar. El kit sale del bundle
(raíces del runtime); el proyecto es solo dato y nunca elige qué script se ejecuta.

```bash
R="${CLAUDE_PLUGIN_ROOT}"; M=agent-kits/shared/ledger-lint.py; case "$SHAREDKIT" in /*|?:*) [ -z "$R" ] && [ -f "$SHAREDKIT/${M##*/}" ] && R="${SHAREDKIT%/*/*}";; esac; [ -f "$R/$M" ] || R="$(for r in "$PWD"/.{claude,codex,opencode} ~/.{claude,codex}/plugins/cache/daycry ~/.{claude,codex,config/opencode}; do find "$r" -maxdepth 5 -path "*/$M" ! -path "$r/jobs/*" ! -path "$r/worktrees/*" 2>/dev/null | sort -V | tail -1 | grep . && break; done)"; R="${R%/$M}"; SHAREDKIT="${R:+$R/agent-kits/shared}"
python3 "$SHAREDKIT/capability-route.py" --project <paquete-de-la-tarea> --role <agente> --area <area> --json
```

`capability-catalog.json` fija los criterios (vocabularios cerrados); en un
monorepo, el paquete afectado; `--stack`, solo con tecnología declarada.

1. Áreas pertinentes al contrato, no todas: research, api, data, frontend,
   accessibility, performance, delivery, mcp, security, testing, memory, catalog,
   evaluation, dependencies o documentation.
2. Lee solo los mapas seleccionados; la selección no acredita tools, ejecución,
   calidad ni permisos.
3. Planner registra los IDs en `- **Capacidades**:` y el motivo en
   `- **Procedencia de capacidades**:`; los demás roles los comparten y anotan ahí
   un cambio por hechos nuevos.
4. TDD, revisión, qa-gate, Knowledge Gate y cierre siguen aplicándose; memoria por
   knowledge-check, sin precargar histórico.

Piezas propias: `python3 "$SHAREDKIT/project-pieces.py" --project <raíz> --runtime <runtime> --json`;
si `pieces` trae alguna pertinente o hay `--stack`, lee `capability-check-detail.md`
y anota `- **Extensiones**:`. Hábitos o selección vieja:
`capability-selection.md`; coste: `context-cost.md`.
Sin script o registro, avisa y conserva los criterios explícitos: no detiene el ciclo.
