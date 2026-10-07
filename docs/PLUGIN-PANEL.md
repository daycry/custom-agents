# Panel de capacidades del plugin

[English](en/PLUGIN-PANEL.md) · **Español**

El comando `/plugin-catalog` usa plugin-panel para mostrar agentes, skills,
comandos, tools declaradas y hooks globales. La búsqueda y los filtros funcionan
en un HTML autónomo. El progreso de iniciativas sigue en roadmap-dashboard.

Los hooks se agrupan en una tarjeta por evento. `PostToolUse` muestra sus tres
handlers dentro de esa tarjeta; el contador HTML mide eventos distintos. El JSON
conserva una entrada por handler y `counts.hooks` cuenta esos handlers. El panel
no muestra comandos completos. Cada acción identificada muestra su nombre,
función y activación; el timeout aparece cuando está configurado en la fuente.
Los nombres y funciones se extraen de las cabeceras públicas `panel-title` y
`panel-description` del script registrado. No se ejecutan esos scripts.

En un checkout:

```powershell
python skills/plugin-panel/scripts/build_panel.py --html panel.html
python skills/plugin-panel/scripts/build_panel.py --json
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --html panel.html
```

En una instalación, localiza la skill en las raíces del runtime. El script
identifica el bundle por su propia ubicación. `--root <bundle>` permite inspeccionar
otro catálogo; no importa código del catálogo inspeccionado. Python nativo funciona
en Windows; no necesita WSL, Tkinter, paquetes Python adicionales ni servidor.

Para incluir piezas propias, usa `--project <raíz>` y el runtime real en
`--runtime claude-code|codex|opencode`. `--cwd <paquete>` inspecciona skills de
su cadena de directorios. Las fuentes personales se incluyen por defecto;
`--project-only` las excluye y `--user-root <runtime>=<ruta>` permite otra raíz.
`all` compara declaraciones entre entornos, sin afirmar que una sesión cargue todas.

«Tus extensiones» tiene búsqueda y filtros propios por tipo, origen y runtime.
Sus declaraciones no alteran los conteos del bundle. Cada tarjeta conserva ID,
fuente, estado de propiedad y conflictos. MCP deshabilitados se indican como
configuración declarada; conexión y permisos permanecen sin verificar. Tools
OpenCode son fuentes de definición, sin inferir exports. Personas siguen su
contrato de `Tipo` en los briefs, sin convertirse en agentes.

El generador carga `project-pieces.py` de su propio bundle, nunca del `--root`
inspeccionado. Un fallo del lector conserva el catálogo del bundle e indica
inventario parcial. El JSON añade `extensions` solo cuando se pide proyecto,
manteniendo `schema_version: 1` y los conteos anteriores. Para seleccionar
extensiones en tareas sigue [el método común](PROJECT-EXTENSIONS.md).

El inventario extrae frontmatters públicos, hooks/hooks.json y los metadatos
de las ocho primeras líneas de scripts reconocidos del launcher empaquetado.
Excluye de la salida cuerpos ejecutables, comandos completos, valores del entorno
y memoria privada. Aplica el redactor
central antes de exportar. Los nombres/modelos/tools se describen tal como se
declaran, sin afirmar disponibilidad de herramientas en la sesión.

Claude/Codex/OpenCode y memoria muestran **presencia de fuentes en el bundle
inspeccionado**, no salud, acceso, configuración del proyecto consumidor ni
ejecución de hooks. La sección de extensiones inventaría aparte las declaraciones
locales del proyecto/usuario; no mide salud ni invoca servidores.

Archivos malformados o no legibles dejan avisos. Sin redactor empaquetado o raíz
válida, exit 2 y diagnóstico, sin emitir metadatos. El flujo del usuario continúa.
Se rechazan symlinks y hay límites de lectura/inventario. El HTML se escribe
atómicamente; solo puede reemplazarse si lleva el marcador de este generador.
Para actualizar la vista, vuelve a generar el archivo.

La plantilla local empaquetada presenta navegación por secciones, tarjetas de
inventario, filtros y detalles desplegables de funciones y roles. Se adapta a
móvil, permite operar los controles con teclado y respeta movimiento reducido.
No necesita servidor ni assets de terceros. Si falta la plantilla, el HTML avisa
y el inventario JSON sigue disponible.

La comparación y decisiones están en
[decisiones de arquitectura y memoria](roadmap/2026-10-06-capability-foundation/comparison.md).
El panel es una implementación propia con stdlib.

La sección «Guides by role» lee el registro de capacidades del bundle
inspeccionado y relaciona guías con roles. No suma esas filas a las tarjetas ni
afirma que las guías se hayan aplicado. Un registro ausente/inválido deja el
catálogo utilizable y muestra el límite. `/work-context` consulta ese registro
por rol/fase/stack/área desde el paquete de la tarea.
