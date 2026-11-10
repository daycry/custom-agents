---
description: "Diagnostica instalación, herramientas, hooks, configuración y journal del plugin, con remedios verificables. Solo lectura: no corrige ni instala automáticamente. Úsalo cuando el usuario diga \"¿está bien instalado?\", \"diagnostica el plugin\", \"por qué no funciona el hook\", \"comprueba mi configuración\", \"doctor\"."
---
<!-- GENERADO por scripts/export-interop.py desde commands/doctor.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a OpenCode** (fichero generado; la fuente es `commands/doctor.md`).
> Este comando ORQUESTA agentes. En OpenCode no hay herramienta Agent: usa `subagent` con el campo `agent` igual al ID nativo, definido en `.opencode/agents/`.
> En el cuerpo, los roles propios se resuelven con este mapa: analyst → `custom-agents-analyst`; architect → `custom-agents-architect`; documenter → `custom-agents-documenter`; evaluator → `custom-agents-evaluator`; implementer → `custom-agents-implementer`; knowledge-curator → `custom-agents-knowledge-curator`; nemesis → `custom-agents-nemesis`; planner → `custom-agents-planner`; qa → `custom-agents-qa`; reviewer → `custom-agents-reviewer`. Conserva nombres y rutas de agentes del consumidor.
> Las skills se invocan con la herramienta `skill` (`skill({ id: "nombre" })`). Todo lo demás (puertas, artefactos, ledger) no cambia.

# /doctor — ¿está todo en su sitio?

## Alcance y activación

Diagnóstico de la instalación del plugin en este proyecto — herramientas (python3, git, jq, node, Playwright), plugin y hooks registrados, statusline, configs de .claude (rates, dev, jira, confluence) y estado del trabajo (marcadores de medición huérfanos, iniciativas en progreso, memoria técnica —curadas, índice, FTS5, journal, calibración—, evals), con veredicto ✅/⚠️/❌ y el arreglo concreto de cada línea. Solo lee; no toca nada. Sin red salvo la comprobación en vivo de capacidades opcionales activadas en `taxonomy.json`, acotada a hosts locales/privados y a un tope total de tiempo (p. ej. `kwipu` o la memoria de grafo `graphiti`). Úsalo cuando el usuario diga "¿está bien instalado?", "diagnostica el plugin", "por qué no funciona el hook", "comprueba mi configuración", "doctor".


`--panel-json` solicita una proyección portable para plugin-panel; es excluyente
con `--json`. Conserva fecha UTC, alcance por clave de ruta, estados, títulos
públicos permitidos y referencias de prioridades. Excluye rutas, detalles y
arreglos libres; estos siguen en las salidas habituales. Exit 1 puede acompañar
un JSON válido con errores encontrados; exit 2 indica que no se pudo producir
la proyección. Usa el diagnóstico actual, incluidas las comprobaciones de
capacidades opt-in ya activadas; el panel nunca lo ejecuta por su cuenta.

Si dev.json declara `perfil`, muestra los flags efectivos de `execution-profile.py`: techo del brief, writer disponible y estrategia de revisores. Un lite bloqueado informa del arreglo; no lo presentes como listo para despachar.

En Codex añade `--runtime codex`; en OpenCode, `--runtime opencode`. Claude
conserva el modo predeterminado. Estos flags validan modelos con el resolutor
del runtime y añaden el contexto declarado de los agentes propios del proyecto;
contexto desconocido o menor de 65.536 tokens produce aviso con arreglo. Ese
mínimo de la vía rápida es orientativo y no acredita calidad del modelo.
El contexto efectivo de la sesión y la configuración de usuario no se presuponen.
Codex 0.166 no aplica la ventana desde el TOML del rol; no deduzcas el contexto
del subagente a partir del padre. Una observación del servidor tampoco acredita
el contexto efectivo del cliente.

Solo si el usuario solicita el sondeo, añade `--probe-ollama
http://127.0.0.1:11434` al runtime nativo. Es otra excepción explícita de red:
GET de `/api/ps` sobre HTTP loopback, sin proxy, credenciales ni redirects;
dos segundos y respuesta acotada. Informa contexto de modelos cargados en el
servidor, sin ejecutar inferencias, descargar modelos ni cambiar configuración.
Un fallo del sondeo produce aviso; no lo conviertas en contexto verificado.

Primera parada cuando algo "no salta": el hook que no aparece, la statusline que no se ve, el
coste que sale a 0, la skill que no encuentra su script. Comprueba la instalación **sin tocar
nada**: cada línea lleva su veredicto y, si algo falla, **qué comando lo arregla**.

## Pasos
1. Localiza el script del kit compartido y ejecútalo:

   ```bash
   R="${CLAUDE_PLUGIN_ROOT}"; M=agent-kits/shared/ledger-lint.py; [ -f "$R/$M" ] || R="$(for r in "$PWD"/.{opencode,claude,codex} ~/.config/opencode ~/.{claude,codex}/plugins/cache/daycry ~/.{claude,codex}; do find "$r" -maxdepth 5 -path "*/$M" ! -path "$r/jobs/*" ! -path "$r/worktrees/*" 2>/dev/null | sort -V | tail -1 | grep . && break; done)"; R="${R%/$M}"; DOC="${R:+$R/agent-kits/shared/doctor.py}"
   python3 "$DOC"            # informe Markdown · exit 0 sin ❌, 1 con ❌
   python3 "$DOC" --json     # lo mismo para consumo por script
   python3 "$DOC" --verbose  # incluye las capacidades opt-in sin su fichero de config (alias --all)
   ```

2. Presenta el informe tal cual y **resume en 2-3 líneas** los conteos y las
   `acciones_prioritarias` calculadas por el script. Son hasta tres filas con
   arreglo: errores antes de avisos, con su bloque y ordinal originales; el
   total y las tablas conservan el resto. No inventes un score ni reordenes
   por cantidad de piezas. Sin acciones no se acredita salud o ejecución global.
3. Si el usuario quiere resolver los hallazgos, usa los arreglos de sus propias
   filas. Aplica los ajustes que ya haya autorizado; si falta autorización para
   un cambio, presenta ese cambio concreto antes de pedir aprobación. El
   diagnóstico y su lista de prioridades no ejecutan los remedios.

## Notas
- **Qué es cada símbolo**: ✅ correcto · ⚠️ funciona pero a medias · ❌ roto · ℹ️ informativo (las ℹ️ **no** hay que arreglarlas).
- **Detalle de lectura** (modo plugin frente a copia, estado efectivo, los tres runtimes, cómo se teclea el comando, los ocho bloques, automatizaciones, versión sin red, memoria de grafo `graphiti`): `$R/agent-kits/shared/doctor-reference.md` (la raíz `R` del paso 1); léelo solo si el usuario pregunta por una fila concreta.
- **Límite de los topes**: el tope de tiempo de las comprobaciones vale para sistemas de ficheros locales (una llamada del SO bloqueada en SMB u OneDrive no la acota).
- **No confundir con `/setup`**: `/doctor` diagnostica lo que ya hay (solo lectura); `/setup` configura y escribe (`rates.json`, `dev.json`, opt-ins de Jira/Confluence, statusline).
