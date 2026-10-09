---
name: plugin-panel
description: >
  Genera un control panel local del catálogo de custom-agents: agentes, skills,
  comandos, herramientas declaradas, hooks globales y presencia de fuentes de
  runtime y memoria; incluye extensiones propias de proyecto y usuario,
  personas y MCP con origen y conflictos; admite un diagnóstico portable de
  doctor indicado explícitamente, con fecha y alcance. HTML autónomo con búsqueda y filtros, JSON determinista,
  con modo --serve explícito para progreso actualizado del ledger y consulta
  local de memoria bajo demanda y revisión visual opcional de un plan, sin cambios
  de configuración. Úsala cuando el usuario diga
  "panel de capacidades", "control panel del plugin" o "explora el catálogo del plugin".
---

# Plugin panel

Presenta el bundle y las extensiones del proyecto seleccionado. El estado de las iniciativas lo muestra
la skill roadmap-dashboard; este panel muestra capacidades y, en modo servido,
una vista acotada del ledger local y de memoria canónica.

1. Localiza esta skill en las raíces del bundle del runtime actual.
2. Ejecuta scripts/build_panel.py con Python nativo, `--root <bundle>` y
   `--html <salida>`. Para el proyecto actual añade `--project <raíz>` y
   `--cwd <paquete>` si está anidado; fija `--runtime` según la sesión.
   Añade `--json` si necesitas inventario estructurado.
   Para un informe ya generado y seleccionado explícitamente, añade
   `--diagnostics-report <informe.json>` junto a `--project <misma-raíz>`.
   Para actualización automática solicitada, sustituye HTML/JSON por `--serve`,
   con proyecto obligatorio; `--port` es opcional. Lee el contrato de servidor
   en la referencia de uso antes de lanzarlo. No se inicia en un inventario estático.
   Para una revisión solicitada, añade `--review-initiative <ruta-relativa-exacta>`
   y `--review-state-root <proyecto/.claude/plan-review>` en modo servido.
   Lee la puerta de revisión en la misma referencia antes de abrirla.
3. Entrega el HTML y resume sus avisos. Un archivo presente no acredita que
   el hook se haya ejecutado ni que un servicio esté sano.
   En modo servido entrega la URL privada de ese proceso y conserva su handle;
   no persistas la URL ni presentes los estados del ledger como agentes vivos.

El inventario extrae frontmatters públicos y declaraciones de hooks por runtime.
Claude/Codex leen sus registros; OpenCode aporta un JSON acotado que gobierna el
adapter. El panel lo lee como datos sin importar JavaScript inspeccionado.
Agrupa runtime y evento, conserva handlers y fuente, y distingue timeout de
registro y supervisión del adapter. Carga y ejecución quedan sin verificar.
Las funciones informativas provienen de cabeceras de handlers reconocidos.
Muestra herramientas declaradas por los agentes, sin afirmar acceso a ellas
en esta sesión. El inventario de memoria muestra presencia de directorio aprobado
y artefacto Graphify. En modo servido, Buscar, Ver y Relaciones leen entradas
locales explícitamente mediante `knowledge-view.py`, sin caché o backends.
No consulta grafos, transcripciones ni credenciales.
Usa el redactor del bundle. Sin él, avisa y no emite metadatos; continúa la tarea.
No sigue enlaces simbólicos. Solo reemplaza HTML reconocido como suyo.

Diagnóstico consume exclusivamente la proyección `doctor --panel-json`, no su
JSON general. No ejecuta doctor ni descubre informes. Conserva fuente, fecha,
alcance y estados históricos; rechaza formatos privados/incompatibles y otro
proyecto. Carga y ejecución de hooks continúan sin verificar. Detalles y arreglos
libres permanecen en doctor; el panel solo ofrece referencias y recomendaciones.

El lector compartido `agent-kits/shared/project-pieces.py` inventaría declaraciones
sin ejecutar piezas ni conectar MCP. Usa `--project-only` para excluir fuentes
personales o `--user-root <runtime>=<ruta>` para una raíz personalizada explícita.
El panel separa los conteos del bundle de las declaraciones propias y filtra
estas últimas por tipo, origen y runtime. Encontrar un archivo no prueba su carga,
conexión ni permiso. Un lector ausente deja el bundle visible con aviso.
La selección para tareas sigue `agent-kits/shared/capability-check.md`; este panel
no escribe el ledger ni adopta componentes. Los datos de conexión y cuerpos
privados se omiten; propiedad por hash y disponibilidad son estados distintos.

La revisión visual delega recibos en `agent-kits/shared/plan-review.py`, con
`local-read.py` y `redact.py` del mismo kit. El navegador anota y envía una decisión;
el consumidor CLI recibe y confirma su consumo para la versión exacta del plan.
Una autorización previa válida permite continuar sin otra confirmación.
Cerrar la vista conserva el borrador y no decide.

| Recurso | Cuándo leerlo |
|---|---|
| [Uso y límites](../../docs/PLUGIN-PANEL.md) | Al explicar inventario, exportación y diferencias con el roadmap |
| [Extensiones propias](../../docs/PROJECT-EXTENSIONS.md) | Carpetas nativas, selección por ID, personas y disponibilidad |
| [Plantilla local](references/panel.html) | Presentación HTML empaquetada; el generador la usa sin cargar recursos de red |
