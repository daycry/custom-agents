<!-- GENERADO por scripts/export-interop.py desde commands/plugin-catalog.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a Codex** (fichero generado; la fuente es `commands/plugin-catalog.md`).
> Este comando ORQUESTA agentes. En Codex no hay herramienta Agent: usa `spawn_agent` con `agent_type` igual al ID nativo del rol, si está disponible; las definiciones se copian a `.codex/agents/`.
> En el cuerpo, los roles propios se resuelven con este mapa: analyst → `custom-agents-analyst`; architect → `custom-agents-architect`; documenter → `custom-agents-documenter`; evaluator → `custom-agents-evaluator`; implementer → `custom-agents-implementer`; knowledge-curator → `custom-agents-knowledge-curator`; nemesis → `custom-agents-nemesis`; planner → `custom-agents-planner`; qa → `custom-agents-qa`; reviewer → `custom-agents-reviewer`. Conserva nombres y rutas de agentes del consumidor.
> Las skills se invocan mencionándolas con `$custom-agents:nombre` para las skills de este plugin; conserva el nombre nativo de las skills del consumidor. Todo lo demás (puertas, artefactos, ledger) no cambia.


# /plugin-catalog — consola común y catálogo

Usa la skill **plugin-panel** y sus referencias según el modo solicitado.
Interpreta **$ARGUMENTS** como argumentos estructurados; nunca eval ni shell libre.
Un pedido de inventario produce un artefacto, sin abrir servicios. Un pedido de
trabajar desde el dashboard o `--serve` abre la consola operativa.

## Consola operativa

1. Localiza `skills/plugin-panel/scripts/control_center.py` en el bundle activo.
   Lee `skills/plugin-panel/references/control-center.md` antes del arranque.
2. Usa el registro explícito `--workspaces <registro.json>` elegido por el operador.
   Es un archivo común fuera de Git, con IDs, nombres, raíces absolutas y runtimes
   permitidos. No escanees carpetas personales ni registres proyectos cercanos.
   Un piloto puede usar `--project <raíz>` en lugar del registro.
3. Reutiliza una instancia y enlace previamente abiertos en esta sesión. Si no
   existe, ejecuta Python nativo con el script y el registro. Un proceso escucha
   en 127.0.0.1:8769 por defecto. Un conflicto no autoriza a elegir otro puerto ni
   a parar un proceso ajeno. `--port` se usa sólo cuando el operador lo indica.
4. Entrega la URL privada sólo al usuario; no la persistáis en Git, documentos,
   memoria ni logs. Conserva el handle del proceso propio. En Windows, si se
   lanza en segundo plano con Start-Process, utiliza WindowStyle Hidden.

El selector cambia el contexto; cada proyecto conserva sus sesiones, planes,
notas, memoria, integraciones y eventos. El registro se modifica por el operador
fuera del navegador y se relee al reiniciar. El enlace da acceso a todos los
proyectos de esa consola local; no hay identidad ni permisos de otros usuarios.

La conexión usa interfaces nativas admitidas, autenticación y políticas existentes.
No instala CLI, no amplía permisos ni garantiza control de aplicaciones Desktop.
Crear una sesión no envía trabajo. Continuar un plan presenta el mensaje y exige
una sesión del mismo proyecto. Las aprobaciones nativas son explícitas y de un
solo uso. Nunca confundas envío admitido, ejecución y resultado confirmado.

Las notas son locales y el ledger canónico conserva los estados. La UI no aprueba
QA ni publica automáticamente comentarios externos. La memoria se consulta
localmente; encontrar un backend no acredita conexión. Actividad identifica
fuente y frescura; una tarea en marcha no demuestra un agente vivo.

## Inventario estático

Localiza `skills/plugin-panel/scripts/build_panel.py`. Pasa `--project <raíz>` y
el runtime real (`claude-code`, `codex` u `opencode`) cuando corresponda. Usa
`--export <carpeta>` o `--json`; lee la referencia `static-panel.md` de la skill.
La exportación tiene siete páginas y un manifiesto de propiedad; no reemplaza
archivos ajenos y no incluye chat ni control de sesiones. Entrega su carpeta y
avisos. Para un diagnóstico existente y elegido explícitamente, admite
`--diagnostics-report <informe.json>` del mismo proyecto; no ejecuta doctor.

`build_panel.py --serve` conserva el servidor informativo anterior para sus
consumidores explícitos; este comando usa `control_center.py` para el dashboard
operativo. No pases `--serve` al script nuevo: ejecutarlo ya inicia el servicio.
Si faltan helpers o un runtime, informa de la capacidad indisponible y continúa
con las vistas y el trabajo posibles. Nunca marques comprobado lo que sólo está
declarado. Para diagnosticar hooks y configuración, `/doctor` conserva su función.
