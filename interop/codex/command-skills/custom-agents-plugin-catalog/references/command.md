<!-- GENERADO por scripts/export-interop.py desde commands/plugin-catalog.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a Codex** (fichero generado; la fuente es `commands/plugin-catalog.md`).
> Este comando ORQUESTA agentes. En Codex no hay herramienta Agent: usa `spawn_agent` con `agent_type` igual al ID nativo del rol, si está disponible; las definiciones se copian a `.codex/agents/`.
> En el cuerpo, los roles propios se resuelven con este mapa: analyst → `custom-agents-analyst`; architect → `custom-agents-architect`; documenter → `custom-agents-documenter`; evaluator → `custom-agents-evaluator`; implementer → `custom-agents-implementer`; knowledge-curator → `custom-agents-knowledge-curator`; nemesis → `custom-agents-nemesis`; planner → `custom-agents-planner`; qa → `custom-agents-qa`; reviewer → `custom-agents-reviewer`. Conserva nombres y rutas de agentes del consumidor.
> Las skills se invocan mencionándolas con `$custom-agents:nombre` para las skills de este plugin; conserva el nombre nativo de las skills del consumidor. Todo lo demás (puertas, artefactos, ledger) no cambia.


# /plugin-catalog — control panel de capacidades

Usa la skill **plugin-panel**. La ruta de salida es **$ARGUMENTS** o una ruta
local acordada para el artefacto. El script no reemplaza archivos ajenos.
Si los argumentos incluyen `--diagnostics-report`, separa esa opción de la ruta
de salida y pásala al generador con la raíz explícita del mismo proyecto. Usa
una lista de argumentos, sin interpolar texto del usuario en shell ni eval.
No ejecutes doctor ni busques informes automáticamente para completar la vista.

Si el usuario solicita el panel con actualización automática, usa `--serve`
en vez de exportar HTML/JSON, con la raíz explícita del proyecto. No abras
servicios por una petición de inventario estático. El servidor solo escucha
en 127.0.0.1 y entrega una URL de acceso propia de ese proceso; no la guardes
en Git, documentación, memoria ni registros. Conserva el handle del proceso
para detenerlo a petición del usuario. En Windows, si lo lanzas en segundo
plano con Start-Process, usa WindowStyle Hidden; no abras otra consola visible.

Puerto efímero por defecto; `--port` permite uno local disponible. Este modo
excluye `--html`, `--json`, `--home` y `--user-root`, y omite fuentes personales.
Entrega la URL solo al usuario. Catálogo y diagnóstico quedan fijados al
arranque; Progreso relee ledgers con límites cada cinco segundos. La UI permite
filtrar y actualizar, e identifica lecturas parciales y datos anteriores tras
un fallo. Una tarea en progreso no demuestra que un agente esté ejecutándose.
Memoria permite Buscar, Ver y Relaciones mediante acciones explícitas. Conserva
ID completo, estado, versión, evidencia y fuente; las lecturas parciales y
colisiones permanecen visibles. No hay consultas de memoria automáticas.
Este modo no escribe tareas ni consulta journal, cachés o backends de memoria.

```bash
PANEL="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/plugin-panel/scripts/build_panel.py' 2>/dev/null | head -1)"
# En el checkout, el script está también en skills/plugin-panel/scripts/.
python3 "$PANEL" --project "<raíz-proyecto>" --runtime <claude-code|codex|opencode> --html "<salida.html>"
```

Una vez localizado PANEL, para el modo servido ejecuta esta alternativa:

```bash
python3 "$PANEL" --project "<raíz-proyecto>" --runtime <claude-code|codex|opencode> --serve
```

En Windows usa el Python nativo disponible. El script identifica el bundle
por su ubicación; `--root` sirve para inspeccionar otro bundle sin importar su
código. Si falta el script o su redactor, informa y sigue la tarea del usuario.
Para un paquete anidado pasa `--cwd`; para excluir piezas personales,
`--project-only`. Raíces personalizadas requieren `--user-root <runtime>=<ruta>`.
Elige el runtime real de la sesión; `all` sirve para comparar declaraciones
entre entornos. El panel separa el bundle y las extensiones. Un fallo del lector
de extensiones conserva el catálogo del bundle con aviso. No modifica, adopta
ni ejecuta las piezas encontradas; contrasta disponibilidad antes de invocarlas.
Entrega el fichero generado y distingue catálogo, presencia de fuente y
ejecución real. Explica los grupos de hooks por runtime/evento, sus handlers,
fuentes y presupuestos; el timeout de registro y la supervisión del adapter
son contratos distintos. Una declaración no acredita carga ni ejecución.
Para cartera, evaluaciones y presupuestos usa roadmap-dashboard; el modo
servido añade una vista local de progreso desde los mismos ledgers canónicos.
El diagnóstico importado es una instantánea histórica: explica fecha, alcance,
formato rechazado, antigüedad o recorte. No cambia los estados de los hooks.
Para el detalle y los arreglos conserva /doctor como dueño de la comprobación.
